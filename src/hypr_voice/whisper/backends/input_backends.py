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


def _run_safe(args: List[str], timeout: float = 1.5, stdin_input: Optional[bytes] = None) -> bool:
    try:
        if stdin_input is not None:
            subprocess.run(args, input=stdin_input, capture_output=True, timeout=timeout, check=True)
        else:
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
        """Type text instantly with minimal delays for lightning-fast input."""
        # Lightning mode: zero delays for instant typing
        # -d 0: no delay between keystrokes
        # -H 0: minimal key hold duration
        # Note: Long text (>1000 chars) is chunked to prevent input buffer issues
        if len(text) <= 1000:
            return _run_safe(["ydotool", "type", "-d", "0", "-H", "0", text])

        # Chunk very long text to avoid UI/input buffer issues
        chunk_size = 500
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i + chunk_size]
            if not _run_safe(["ydotool", "type", "-d", "0", "-H", "0", chunk], timeout=5.0):
                return False
            # Tiny pause between chunks to let UI breathe
            time.sleep(0.01)
        return True

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:  # noqa: ARG002
        # Instant mode is preferred; word-by-word is deprecated
        return self.type_text_instant(text)


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


class PasteBackend(InputBackend):
    """
    Fast paste backend using clipboard + wtype.

    Copies text to clipboard using wl-copy, then sends both Ctrl+V and Ctrl+Shift+V
    using wtype. Works universally on all applications without app detection:

    - Ctrl+V works for GUI apps (Electron, GTK, Qt, browsers)
    - Ctrl+Shift+V works for terminals (Alacritty, Kitty, etc.)
    - Sending both is harmless - one will always work
    """
    name = "paste"

    def is_available(self) -> bool:
        # Need both wl-copy (clipboard) and wtype (paste shortcuts)
        return _cmd_exists("wl-copy") and _cmd_exists("wtype")

    def type_text_instant(self, text: str) -> bool:
        """Paste text using clipboard - works on any application."""
        # Step 1: Copy to clipboard
        if not _run_safe(["wl-copy"], stdin_input=text.encode('utf-8')):
            return False

        # Small delay for clipboard to update
        time.sleep(0.05)

        # Step 2: Send Ctrl+V (works for 90% of apps: Electron, GTK, Qt, browsers)
        _run_safe(["wtype", "-M", "ctrl", "-k", "v", "-m", "ctrl"])

        # Step 3: Send Ctrl+Shift+V (works for terminals)
        # This is harmless in GUI apps (either ignored or types "V")
        time.sleep(0.05)
        try:
            subprocess.run(
                ["wtype", "-M", "ctrl", "-M", "shift", "-k", "v", "-m", "shift", "-m", "ctrl"],
                capture_output=True,
                timeout=1
            )
        except Exception:
            pass  # Ignore failures, Ctrl+V likely worked

        return True

    def type_text_words(self, text: str, words_per_second: float = 10) -> bool:
        return self.type_text_instant(text)


class NullBackend(InputBackend):
    name = "manual"

    def is_available(self) -> bool:
        return True

    def type_text_instant(self, text: str) -> bool:
        logger.warning("No input backend available; skipping typing")
        return False


# ---------- selection ----------


BACKENDS = [YdotoolBackend, KdotoolBackend, WtypeBackend, XdotoolBackend, PasteBackend]


def detect_input_backend(preferred: Optional[str] = None, window_backend: Optional[str] = None) -> InputBackend:
    """Select the best available input backend.

    Priority (unless a valid preferred backend is provided):
      - Hyprland/Sway → ydotool, wtype, kdotool, xdotool, paste
      - KDE window backend → kdotool, ydotool, wtype, xdotool, paste
      - X11 window backend → xdotool, ydotool, kdotool, paste
      - GNOME (Wayland) → ydotool, kdotool, wtype, xdotool, paste
      - fallback → ydotool, kdotool, wtype, xdotool, paste
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
    # Ydotool is default (fastest uinput-based), paste available as fallback
    priority: List[type] = []
    wb = (window_backend or "").lower()
    if wb == "kde":
        priority = [KdotoolBackend, YdotoolBackend, WtypeBackend, XdotoolBackend, PasteBackend]
    elif wb == "x11":
        priority = [XdotoolBackend, YdotoolBackend, KdotoolBackend, WtypeBackend, PasteBackend]
    elif wb in ("hyprland", "sway"):
        priority = [YdotoolBackend, WtypeBackend, KdotoolBackend, XdotoolBackend, PasteBackend]
    elif wb == "gnome":
        priority = [YdotoolBackend, KdotoolBackend, WtypeBackend, XdotoolBackend, PasteBackend]
    else:
        priority = [YdotoolBackend, KdotoolBackend, WtypeBackend, XdotoolBackend, PasteBackend]

    for cls in priority:
        inst = cls()
        if inst.is_available():
            logger.info("Selected input backend: %s", cls.name)
            return inst

    logger.warning("No input backend available; using manual")
    return NullBackend()
