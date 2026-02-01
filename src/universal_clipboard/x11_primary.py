#!/usr/bin/env python3
"""
X11 PRIMARY Selection Utilities

Supports both xsel and xclip with automatic fallback.
"""

import subprocess
import shutil
from typing import Optional


class X11PrimarySelection:
    """Handle X11 PRIMARY selection (middle-click paste)."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.tool = self._detect_tool()

    def _detect_tool(self) -> Optional[str]:
        """Detect available clipboard tool."""
        for tool in ['xsel', 'xclip']:
            if shutil.which(tool):
                return tool
        return None

    def is_available(self) -> bool:
        """Check if X11 primary selection is available."""
        return self.tool is not None

    def get_primary(self) -> Optional[str]:
        """
        Get text from X11 PRIMARY selection.

        Returns:
            Text content or None if unavailable/empty
        """
        if not self.tool:
            raise RuntimeError("No clipboard tool available (install xsel or xclip)")

        try:
            if self.tool == 'xsel':
                result = subprocess.run(
                    ['xsel', '-p', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
            else:  # xclip
                result = subprocess.run(
                    ['xclip', '-selection', 'primary', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )

            return result.stdout.strip()

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return None

    def set_primary(self, text: str) -> bool:
        """
        Set text to X11 PRIMARY selection.

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        if not self.tool:
            raise RuntimeError("No clipboard tool available (install xsel or xclip)")

        try:
            if self.tool == 'xsel':
                subprocess.run(
                    ['xsel', '-i', '-p'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
            else:  # xclip
                subprocess.run(
                    ['xclip', '-selection', 'primary', '-i'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
            return True

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False
