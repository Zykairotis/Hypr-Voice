"""Cross-desktop window backends for Hypr-Whisper.

This module provides small, dependency-light adapters for common Linux
desktops/window managers so we can introspect the focused window and basic
metadata without assuming Hyprland. Each backend shells out to the platform's
native CLI/DBus surface and returns a normalized dictionary with keys the rest
of the codebase already understands (class/title/initialClass/initialTitle,...).

Design goals
------------
- Hyprland remains first-class: if Hyprland is available we keep using it.
- Add safe fallbacks for Sway/wlroots, GNOME (Mutter), KDE (KWin Wayland/X11),
  and generic X11 EWMH (xdotool/wmctrl).
- Do not add new mandatory dependencies; everything is optional and guarded by
  presence checks + short timeouts so existing setups keep working.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)
TRACE_ENABLED = os.getenv("HYPR_VOICE_TRACE", "0") == "1"
TRACE_SLOW_MS = float(os.getenv("HYPR_VOICE_TRACE_SLOW_MS", "0"))

# Cache statistics for monitoring
_cache_stats = {
    "reads": 0,
    "writes": 0,
    "hits": 0,
    "misses": 0,
    "read_time_ms": [],
    "write_time_ms": [],
}


def _trace_duration(label: str, start_time: float, **fields) -> float:
    """Log timing for a span if tracing is enabled or exceeds slow threshold."""
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    should_log = TRACE_ENABLED or (TRACE_SLOW_MS > 0 and elapsed_ms >= TRACE_SLOW_MS)
    if should_log:
        field_str = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
        if field_str:
            logger.info(f"[TRACE] {label} {elapsed_ms:.1f}ms {field_str}")
        else:
            logger.info(f"[TRACE] {label} {elapsed_ms:.1f}ms")
    return elapsed_ms


def get_cache_stats() -> Dict:
    """Get cache statistics for monitoring."""
    stats = dict(_cache_stats)
    read_times = stats.pop("read_time_ms", [])
    write_times = stats.pop("write_time_ms", [])
    if read_times:
        import statistics
        stats["avg_read_ms"] = statistics.mean(read_times)
        stats["total_read_ms"] = sum(read_times)
    if write_times:
        import statistics
        stats["avg_write_ms"] = statistics.mean(write_times)
        stats["total_write_ms"] = sum(write_times)
    return stats


def reset_cache_stats():
    """Reset cache statistics."""
    global _cache_stats
    _cache_stats = {
        "reads": 0,
        "writes": 0,
        "hits": 0,
        "misses": 0,
        "read_time_ms": [],
        "write_time_ms": [],
    }


# ---------- helpers ----------


def _cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _run_cmd(args, timeout: float = 1.5) -> Optional[str]:
    start_time = time.perf_counter()
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if TRACE_ENABLED or (TRACE_SLOW_MS > 0 and elapsed_ms >= TRACE_SLOW_MS):
            logger.info("[TRACE] cmd=%s rc=%s %.1fms", args, result.returncode, elapsed_ms)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        if TRACE_ENABLED or (TRACE_SLOW_MS > 0 and elapsed_ms >= TRACE_SLOW_MS):
            logger.info("[TRACE] cmd=%s rc=error %.1fms", args, elapsed_ms)
        logger.debug("Command failed for %s: %s", args, e)
    return None


def _normalize_window(
    backend: str,
    title: str = "",
    wm_class: str = "",
    app_id: str = "",
    pid: Optional[int] = None,
    workspace: str = "",
    raw: Optional[Dict] = None,
) -> Dict:
    """Return a dict compatible with existing Hypr-Whisper consumers."""

    cls = wm_class or app_id or ""
    return {
        "backend": backend,
        "class": cls,
        "title": title or "",
        "app_id": app_id or cls,
        "wm_class": wm_class or cls,
        "pid": pid,
        "workspace": workspace or "",
        "initialClass": cls,
        "initialTitle": title or "",
        "raw": raw or {},
    }


# ---------- backends ----------


class WindowBackend:
    name = "base"

    def is_available(self) -> bool:
        return False

    def get_active_window(self) -> Optional[Dict]:
        raise NotImplementedError


class HyprlandBackend(WindowBackend):
    name = "hyprland"

    def is_available(self) -> bool:
        if not _cmd_exists("hyprctl"):
            return False

        # Fast path: env var is set when Hyprland is running
        if os.environ.get("HYPRLAND_INSTANCE_SIGNATURE"):
            return True

        # Fallback: try activewindow
        try:
            data = self.get_active_window()
            return data is not None
        except Exception:
            return False

    def get_active_window(self) -> Optional[Dict]:
        output = _run_cmd(["hyprctl", "activewindow", "-j"], timeout=1.2)
        if not output:
            return None
        try:
            data = json.loads(output)
        except json.JSONDecodeError:
            return None

        return _normalize_window(
            backend=self.name,
            title=data.get("title", ""),
            wm_class=data.get("class", "") or data.get("initialClass", ""),
            app_id=data.get("initialClass", "") or data.get("class", ""),
            pid=data.get("pid"),
            workspace=str(data.get("workspace", {}).get("id", ""))
            if isinstance(data.get("workspace"), dict)
            else str(data.get("workspace", "")),
            raw=data,
        )


class SwayBackend(WindowBackend):
    """Works for Sway and many wlroots compositors that ship swaymsg."""

    name = "sway"

    def is_available(self) -> bool:
        if not _cmd_exists("swaymsg"):
            return False
        if os.environ.get("XDG_SESSION_TYPE") and os.environ.get("XDG_SESSION_TYPE") != "wayland":
            return False
        try:
            output = _run_cmd(["swaymsg", "-t", "get_tree"], timeout=1.5)
            return bool(output)
        except Exception:
            return False

    def _find_focused(self, node: Dict, workspace: str = "") -> Optional[Tuple[Dict, str]]:
        current_workspace = workspace
        if node.get("type") == "workspace":
            current_workspace = str(node.get("name", ""))

        if node.get("focused"):
            return node, current_workspace

        for child in node.get("nodes", []) + node.get("floating_nodes", []):
            found = self._find_focused(child, current_workspace)
            if found:
                return found
        return None

    def get_active_window(self) -> Optional[Dict]:
        output = _run_cmd(["swaymsg", "-t", "get_tree"], timeout=1.5)
        if not output:
            return None
        try:
            tree = json.loads(output)
        except json.JSONDecodeError:
            return None

        focused_tuple = self._find_focused(tree)
        if not focused_tuple:
            return None

        focused, workspace = focused_tuple
        props = focused.get("window_properties") or {}

        return _normalize_window(
            backend=self.name,
            title=focused.get("name", ""),
            wm_class=props.get("class") or props.get("instance") or "",
            app_id=focused.get("app_id", ""),
            pid=focused.get("pid"),
            workspace=workspace,
            raw=focused,
        )


class GnomeBackend(WindowBackend):
    name = "gnome"

    def is_available(self) -> bool:
        if not _cmd_exists("gdbus"):
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" not in desktop:
            return False
        # Quick sanity check
        return self.get_active_window() is not None

    def _call_shell(self) -> Optional[str]:
        js = (
            "JSON.stringify(global.get_window_actors()"
            ".map(a=>{const w=a.meta_window;return {"
            "title:w.get_title(),"
            "wm_class:w.get_wm_class(),"
            "app_id:w.get_wm_class(),"
            "pid:w.get_pid(),"
            "focused:w.has_focus()};}))"
        )
        return _run_cmd(
            [
                "gdbus",
                "call",
                "--session",
                "--dest",
                "org.gnome.Shell",
                "--object-path",
                "/org/gnome/Shell",
                "--method",
                "org.gnome.Shell.Eval",
                js,
            ],
            timeout=1.5,
        )

    def get_active_window(self) -> Optional[Dict]:
        output = self._call_shell()
        if not output:
            return None

        # gdbus returns: (true, 'json-string')
        start = output.find("[")
        end = output.rfind("]")
        if start == -1 or end == -1:
            return None
        try:
            windows = json.loads(output[start : end + 1])
        except json.JSONDecodeError:
            return None

        focused = next((w for w in windows if w.get("focused")), None)
        if not focused and windows:
            focused = windows[0]
        if not focused:
            return None

        return _normalize_window(
            backend=self.name,
            title=focused.get("title", ""),
            wm_class=focused.get("wm_class", ""),
            app_id=focused.get("app_id", ""),
            pid=focused.get("pid"),
            raw=focused,
        )


class KDEBackend(WindowBackend):
    name = "kde"

    def is_available(self) -> bool:
        # Prefer kdotool (Wayland-safe)
        if not _cmd_exists("kdotool"):
            return False
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "kde" not in desktop and "plasma" not in desktop:
            return False
        return self.get_active_window() is not None

    def get_active_window(self) -> Optional[Dict]:
        win_id = _run_cmd(["kdotool", "getactivewindow"], timeout=1)
        if not win_id:
            return None

        title = _run_cmd(["kdotool", "getwindowname", win_id], timeout=1) or ""
        wm_class = _run_cmd(["kdotool", "getwindowclassname", win_id], timeout=1) or ""
        pid_raw = _run_cmd(["kdotool", "getwindowpid", win_id], timeout=1) or ""
        pid = int(pid_raw) if pid_raw.isdigit() else None

        return _normalize_window(
            backend=self.name,
            title=title,
            wm_class=wm_class,
            app_id=wm_class,
            pid=pid,
            raw={"window_id": win_id},
        )


class X11Backend(WindowBackend):
    name = "x11"

    def is_available(self) -> bool:
        if not _cmd_exists("xdotool"):
            return False
        if not os.environ.get("DISPLAY"):
            return False
        try:
            return self.get_active_window() is not None
        except Exception:
            return False

    def get_active_window(self) -> Optional[Dict]:
        win_id = _run_cmd(["xdotool", "getactivewindow"], timeout=1)
        if not win_id:
            return None

        wm_class = _run_cmd(["xdotool", "getwindowclassname", win_id], timeout=1) or ""
        title = _run_cmd(["xdotool", "getwindowname", win_id], timeout=1) or ""
        pid_raw = _run_cmd(["xdotool", "getwindowpid", win_id], timeout=1) or ""
        pid = int(pid_raw) if pid_raw.isdigit() else None

        return _normalize_window(
            backend=self.name,
            title=title,
            wm_class=wm_class,
            app_id=wm_class,
            pid=pid,
            raw={"window_id": win_id},
        )


class NullBackend(WindowBackend):
    name = "manual"

    def is_available(self) -> bool:
        return True

    def get_active_window(self) -> Optional[Dict]:
        return None


# ---------- selection ----------


BACKEND_MAP = {
    "hyprland": HyprlandBackend,
    "sway": SwayBackend,
    "gnome": GnomeBackend,
    "kde": KDEBackend,
    "x11": X11Backend,
    "manual": NullBackend,
}


def detect_backend(preferred: Optional[str] = None) -> WindowBackend:
    """Pick the best available backend, caching the first successful choice.

    Order of preference when no explicit choice is given:
    1. Hyprland (current behavior)
    2. Sway/wlroots
    3. GNOME Shell
    4. KDE Plasma
    5. X11 (generic EWMH)
    6. manual (no window data)

    Caching: the first successful auto-detection is written to
    ~/.cache/hypr-voice/backend.json. Future runs reuse it if still available.
    Set HYPR_VOICE_WINDOW_BACKEND to override, or delete the cache file.
    """

    cache_dir = Path.home() / ".cache" / "hypr-voice"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "backend.json"

    preference = preferred or os.environ.get("HYPR_VOICE_WINDOW_BACKEND")
    if preference:
        preference = preference.lower()
        if preference in BACKEND_MAP:
            backend = BACKEND_MAP[preference]()
            if backend.is_available():
                logger.info("Using requested window backend: %s", backend.name)
                _write_cache(cache_file, backend.name)
                return backend
            logger.warning("Requested backend '%s' not available; falling back to auto", preference)

    cached = _read_cache(cache_file)
    _cache_stats["reads"] += 1
    if cached:
        _cache_stats["hits"] += 1
        cls = BACKEND_MAP.get(cached)
        if cls:
            candidate = cls()
            if candidate.is_available():
                logger.info("Using cached window backend: %s", cached)
                return candidate
            else:
                logger.info("Cached backend '%s' not available anymore; re-detecting", cached)
    else:
        _cache_stats["misses"] += 1

    for backend_cls in [
        HyprlandBackend,
        SwayBackend,
        GnomeBackend,
        KDEBackend,
        X11Backend,
    ]:
        backend = backend_cls()
        if backend.is_available():
            logger.info("Detected window backend: %s", backend.name)
            _write_cache(cache_file, backend.name)
            return backend

    logger.warning("No window backend available; running in manual mode")
    return NullBackend()


def _write_cache(path: Path, backend_name: str) -> None:
    start = time.perf_counter()
    try:
        data = {"window_backend": backend_name, "detected_at": int(time.time())}
        path.write_text(json.dumps(data))
        elapsed_ms = (time.perf_counter() - start) * 1000
        _cache_stats["writes"] += 1
        _cache_stats["write_time_ms"].append(elapsed_ms)
        _trace_duration("window_backend_cache_write", start, backend=backend_name)
    except Exception as e:
        _trace_duration("window_backend_cache_write", start, backend=backend_name, error=str(e))
        logger.debug("Failed to write backend cache: %s", e)


def _read_cache(path: Path) -> Optional[str]:
    start = time.perf_counter()
    try:
        if not path.exists():
            _trace_duration("window_backend_cache_read", start, hit=False, reason="not_found")
            return None
        data = json.loads(path.read_text())
        backend_name = data.get("window_backend")
        elapsed_ms = (time.perf_counter() - start) * 1000
        _cache_stats["read_time_ms"].append(elapsed_ms)
        _trace_duration("window_backend_cache_read", start, hit=bool(backend_name), backend=backend_name)
        return backend_name
    except Exception:
        return None
