#!/usr/bin/env python3
"""
Universal Clipboard/Paste System

Automatically detects and uses the best available clipboard mechanism:
- X11 PRIMARY selection (xsel/xclip)
- Wayland primary selection (wl-clipboard)
- Fallback to standard clipboard
"""

import os
import shutil
import subprocess
from typing import Optional, Literal

# Type alias for clipboard backends
ClipboardType = Literal['x11', 'wayland', 'unknown']


class UniversalClipboard:
    """Universal clipboard supporting X11 and Wayland."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.backend = self._detect_backend()

    def _detect_backend(self) -> ClipboardType:
        """Detect clipboard backend."""
        # Check Wayland first
        if os.environ.get('WAYLAND_DISPLAY'):
            if shutil.which('wl-paste'):
                return 'wayland'

        # Check X11
        if os.environ.get('DISPLAY'):
            if shutil.which('xsel') or shutil.which('xclip'):
                return 'x11'

        return 'unknown'

    def is_available(self) -> bool:
        """Check if any clipboard is available."""
        return self.backend != 'unknown'

    def get_backend(self) -> ClipboardType:
        """Get current backend name."""
        return self.backend

    def get_primary(self) -> Optional[str]:
        """
        Get text from primary selection (auto-detect backend).

        Returns:
            Text content or None if unavailable
        """
        if self.backend == 'wayland':
            return self._get_wayland_primary()
        elif self.backend == 'x11':
            return self._get_x11_primary()
        return None

    def set_primary(self, text: str) -> bool:
        """
        Set text to primary selection (auto-detect backend).

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        if self.backend == 'wayland':
            return self._set_wayland_primary(text)
        elif self.backend == 'x11':
            return self._set_x11_primary(text)
        return False

    def _get_x11_primary(self) -> Optional[str]:
        """Get X11 primary selection."""
        # Try xsel first, then xclip
        if shutil.which('xsel'):
            try:
                result = subprocess.run(
                    ['xsel', '-p', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        if shutil.which('xclip'):
            try:
                result = subprocess.run(
                    ['xclip', '-selection', 'primary', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        return None

    def _set_x11_primary(self, text: str) -> bool:
        """Set X11 primary selection."""
        if shutil.which('xsel'):
            try:
                subprocess.run(
                    ['xsel', '-i', '-p'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        if shutil.which('xclip'):
            try:
                subprocess.run(
                    ['xclip', '-selection', 'primary', '-i'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        return False

    def _get_wayland_primary(self) -> Optional[str]:
        """Get Wayland primary selection."""
        try:
            result = subprocess.run(
                ['wl-paste', '--primary'],
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return None

    def _set_wayland_primary(self, text: str) -> bool:
        """Set Wayland primary selection."""
        try:
            subprocess.run(
                ['wl-copy', '--primary'],
                input=text,
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout
            )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False
