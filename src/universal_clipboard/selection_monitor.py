#!/usr/bin/env python3
"""
Monitor Primary Selection Changes

Watches for changes to the primary selection and triggers callbacks.
"""

import subprocess
import threading
import time
from typing import Callable, Optional


class PrimarySelectionMonitor:
    """Monitor primary selection for changes."""

    def __init__(self, poll_interval: float = 0.5):
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content = ""
        self._callback: Optional[Callable[[str], None]] = None

    def _get_primary(self) -> Optional[str]:
        """Get current primary selection content."""
        try:
            # Try wl-paste first (Wayland), then xsel (X11)
            for cmd in [['wl-paste', '--primary'], ['xsel', '-p', '-o']]:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        check=True,
                        text=True,
                        timeout=1
                    )
                    return result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        except subprocess.TimeoutExpired:
            pass
        return None

    def _monitor_loop(self):
        """Monitoring loop."""
        while self._running:
            content = self._get_primary()

            if content is not None and content != self._last_content:
                if self._callback:
                    self._callback(content)
                self._last_content = content

            time.sleep(self.poll_interval)

    def start(self, callback: Callable[[str], None]):
        """
        Start monitoring primary selection.

        Args:
            callback: Function to call when selection changes
        """
        if self._running:
            return

        self._callback = callback
        self._running = True
        self._last_content = self._get_primary() or ""

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
