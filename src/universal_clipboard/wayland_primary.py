#!/usr/bin/env python3
"""
Wayland PRIMARY Selection Utilities

Uses wl-clipboard (wl-copy/wl-paste) for Wayland selection support.
"""

import subprocess
import shutil
import os
from typing import Optional


class WaylandPrimarySelection:
    """Handle Wayland primary selection."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self._check_wayland()

    def _check_wayland(self) -> bool:
        """Check if running on Wayland."""
        return os.environ.get('WAYLAND_DISPLAY') is not None

    def is_available(self) -> bool:
        """Check if Wayland primary selection is available."""
        if not self._check_wayland():
            return False
        return shutil.which('wl-paste') is not None

    def get_primary(self) -> Optional[str]:
        """
        Get text from Wayland primary selection.

        Returns:
            Text content or None if unavailable/empty
        """
        if not self.is_available():
            raise RuntimeError("Wayland primary selection not available")

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

    def set_primary(self, text: str) -> bool:
        """
        Set text to Wayland primary selection.

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        if not self.is_available():
            raise RuntimeError("Wayland primary selection not available")

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
