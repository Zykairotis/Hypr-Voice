#!/usr/bin/env python3
"""
Programmatic Middle-Click Paste

Simulates middle-click paste on X11 and Wayland.
"""

import os
import shutil
import subprocess
import time
from typing import Literal

# Type alias for paste methods
PasteMethod = Literal['xdotool', 'ydotool', 'wtype', 'none']


class ProgrammaticPaster:
    """Programmatically paste via middle-click simulation."""

    def __init__(self, method: PasteMethod = 'auto'):
        self.method = self._detect_method() if method == 'auto' else method

    def _detect_method(self) -> PasteMethod:
        """Detect best available paste method."""
        # Prefer wtype on Wayland
        if os.environ.get('WAYLAND_DISPLAY'):
            if shutil.which('wtype') and shutil.which('wl-paste'):
                # Verify virtual keyboard support
                try:
                    result = subprocess.run(
                        ['wayland-info'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if 'virtual_keyboard' in result.stdout:
                        return 'wtype'
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Fall back to ydotool
            if shutil.which('ydotool'):
                return 'ydotool'

        # Use xdotool on X11
        if os.environ.get('DISPLAY'):
            if shutil.which('xdotool'):
                return 'xdotool'

        return 'none'

    def is_available(self) -> bool:
        """Check if paste method is available."""
        return self.method != 'none'

    def paste(self, delay: float = 0.1) -> bool:
        """
        Simulate middle-click paste.

        Args:
            delay: Delay before paste (for focus)

        Returns:
            True if successful
        """
        if delay > 0:
            time.sleep(delay)

        if self.method == 'xdotool':
            return self._paste_xdotool()
        elif self.method == 'ydotool':
            return self._paste_ydotool()
        elif self.method == 'wtype':
            return self._paste_wtype()
        return False

    def paste_text(self, text: str, delay: float = 0.1) -> bool:
        """
        Type text instead of middle-click paste.

        Args:
            text: Text to type
            delay: Delay before typing (for focus)

        Returns:
            True if successful
        """
        if delay > 0:
            time.sleep(delay)

        if self.method == 'xdotool':
            return self._type_xdotool(text)
        elif self.method == 'ydotool':
            return self._type_ydotool(text)
        elif self.method == 'wtype':
            return self._type_wtype(text)
        return False

    def _paste_xdotool(self) -> bool:
        """Paste using xdotool middle-click."""
        try:
            subprocess.run(
                ['xdotool', 'click', '2'],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _type_xdotool(self, text: str) -> bool:
        """Type text using xdotool."""
        try:
            # xdotool doesn't support stdin, so we need a temp file
            with open('/tmp/xdotool_type.txt', 'w') as f:
                f.write(text)

            subprocess.run(
                ['xdotool', 'type', '--file', '/tmp/xdotool_type.txt'],
                capture_output=True,
                check=True,
                timeout=10  # Longer timeout for typing
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, IOError):
            return False

    def _paste_ydotool(self) -> bool:
        """Paste using ydotool middle-click."""
        try:
            subprocess.run(
                ['ydotool', 'click', '0xC2'],  # Middle button code
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _type_ydotool(self, text: str) -> bool:
        """Type text using ydotool."""
        try:
            subprocess.run(
                ['ydotool', 'type', text],
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _paste_wtype(self) -> bool:
        """Paste using wtype (type primary selection)."""
        try:
            # Get primary selection and type it
            subprocess.run(
                'wl-paste --primary | wtype -d 20 -',
                shell=True,
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _type_wtype(self, text: str) -> bool:
        """Type text using wtype."""
        try:
            subprocess.run(
                ['wtype', '-d', '20', text],
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
