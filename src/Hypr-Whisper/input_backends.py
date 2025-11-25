"""Input synthesis backends for Hypr-Whisper.

We support multiple compositors by selecting an available tool at runtime:
- ydotool  : uinput-based, fast, works on most Wayland/X11 (default)
- kdotool  : KDE/KWin-native (Wayland/X11) and avoids generic input blocks
- wtype    : wlroots-friendly typer (if present)
- xdotool  : X11 EWMH classic

The selection is conservative: we preserve existing behavior by preferring
ydotool when present, and we never raise on failure—typing simply no-ops and
logs an error so current workflows do not break on unsupported desktops.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import time
from typing import Optional, List

logger = logging.getLogger(__name__)


# ---------- helpers ----------


def _cmd_exists(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def _run_safe(args: List[str], timeout: float = 1.5) -> bool:
    try:
        subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=True)
        return True
    except Exception as e:
        logger.debug("input backend command failed: %s -> %s", args, e)
        return False


# ---------- backend classes ----------


class InputBackend:
    name = "base"

    def is_available(self) -> bool:
        return False

    def type_text_instant(self, text: str) -> bool:
        raise NotImplementedError

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:
        # default: fall back to instant if not overridden
        return self.type_text_instant(text)


class YdotoolBackend(InputBackend):
    name = "ydotool"

    def is_available(self) -> bool:
        return _cmd_exists("ydotool")

    def type_text_instant(self, text: str) -> bool:
        return _run_safe(["ydotool", "type", "-d", "1", "-H", "1", text])

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:
        words = text.split()
        if not words:
            return True
        delay = 1.0 / max(words_per_second, 0.1)
        ok = True
        for i, word in enumerate(words):
            token = word if i == 0 else f" {word}"
            ok = _run_safe(["ydotool", "type", "-d", "1", "-H", "1", token]) and ok
            time.sleep(delay)
        return ok


class KdotoolBackend(InputBackend):
    name = "kdotool"

    def is_available(self) -> bool:
        return _cmd_exists("kdotool")

    def type_text_instant(self, text: str) -> bool:
        # kdotool type automatically sends the string
        return _run_safe(["kdotool", "type", "--delay", "0", "--clearmodifiers", "0", text])

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:
        # kdotool type already handles spaces; use instant
        return self.type_text_instant(text)


class WtypeBackend(InputBackend):
    name = "wtype"

    def is_available(self) -> bool:
        return _cmd_exists("wtype")

    def type_text_instant(self, text: str) -> bool:
        return _run_safe(["wtype", text])

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:
        return self.type_text_instant(text)


class XdotoolBackend(InputBackend):
    name = "xdotool"

    def is_available(self) -> bool:
        return _cmd_exists("xdotool")

    def type_text_instant(self, text: str) -> bool:
        # --clearmodifiers avoids stuck modifiers from PTT keys
        return _run_safe(["xdotool", "type", "--delay", "0", "--clearmodifiers", "--", text])

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:
        delay_ms = max(int(1000 / max(words_per_second, 0.1)), 1)
        return _run_safe([
            "xdotool",
            "type",
            "--delay",
            str(delay_ms),
            "--clearmodifiers",
            "--",
            text,
        ])


class NullBackend(InputBackend):
    name = "manual"

    def is_available(self) -> bool:
        return True

    def type_text_instant(self, text: str) -> bool:
        logger.warning("No input backend available; skipping typing")
        return False


# ---------- selection ----------


BACKENDS = [YdotoolBackend, KdotoolBackend, WtypeBackend, XdotoolBackend]


def detect_input_backend(preferred: Optional[str] = None, window_backend: Optional[str] = None) -> InputBackend:
    """Select the best available input backend.

    Priority (unless a valid preferred backend is provided):
      - KDE window backend → kdotool, then ydotool, wtype, xdotool
      - X11 window backend → xdotool, then ydotool, kdotool
      - wlroots/Hyprland/Sway → ydotool, wtype, kdotool, xdotool
      - GNOME (Wayland) → ydotool, kdotool, wtype, xdotool
      - fallback → ydotool, kdotool, wtype, xdotool
    """

    env_pref = (preferred or "").strip() or (os.getenv("HYPR_VOICE_INPUT_BACKEND") or "")
    if env_pref:
        env_pref = env_pref.lower()
        for cls in BACKENDS:
            if cls.name == env_pref:
                inst = cls()
                if inst.is_available():
                    logger.info("Using requested input backend: %s", cls.name)
                    return inst
                logger.warning("Requested input backend '%s' not available; falling back", env_pref)
                break

    # Build priority list based on window backend hint
    priority: List[type] = []
    wb = (window_backend or "").lower()
    if wb == "kde":
        priority = [KdotoolBackend, YdotoolBackend, WtypeBackend, XdotoolBackend]
    elif wb == "x11":
        priority = [XdotoolBackend, YdotoolBackend, KdotoolBackend, WtypeBackend]
    elif wb in ("hyprland", "sway"):
        priority = [YdotoolBackend, WtypeBackend, KdotoolBackend, XdotoolBackend]
    elif wb == "gnome":
        priority = [YdotoolBackend, KdotoolBackend, WtypeBackend, XdotoolBackend]
    else:
        priority = [YdotoolBackend, KdotoolBackend, WtypeBackend, XdotoolBackend]

    for cls in priority:
        inst = cls()
        if inst.is_available():
            logger.info("Selected input backend: %s", cls.name)
            return inst

    logger.warning("No input backend available; using manual")
    return NullBackend()
