#!/usr/bin/env python3
"""
Application detector for Hypr-Voice vocabulary system.
Detects active applications and updates vocabulary accordingly.
"""

import asyncio
import json
import logging
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Set

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from vocabulary_manager import get_vocabulary_manager

logger = logging.getLogger(__name__)

class ApplicationDetector:
    """Detects active applications for vocabulary switching."""

    def __init__(self):
        self.vocabulary_manager = get_vocabulary_manager()
        self.current_window = None
        self.detection_method = self._detect_detection_method()

    def _detect_detection_method(self) -> str:
        """Detect the available window system and detection method."""
        # Try to detect the window system
        try:
            # Check for Hyprland
            result = subprocess.run(['hyprctl', '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Detected Hyprland window system")
                return "hyprland"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        try:
            # Check for X11
            result = subprocess.run(['xdotool', '--version'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                logger.info("Detected X11 window system")
                return "x11"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        logger.warning("No supported window system detected, using manual mode")
        return "manual"

    def get_active_window_hyprland(self) -> Optional[Dict]:
        """Get active window information using Hyprland."""
        try:
            # Get active window info as JSON
            result = subprocess.run(['hyprctl', 'activewindow', '-j'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {
                    'class': data.get('class', ''),
                    'title': data.get('title', ''),
                    'initialClass': data.get('initialClass', ''),
                    'initialTitle': data.get('initialTitle', '')
                }
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError) as e:
            logger.error(f"Error getting Hyprland active window: {e}")
        return None

    def get_active_window_x11(self) -> Optional[Dict]:
        """Get active window information using X11/xdotool."""
        try:
            # Get active window ID
            result = subprocess.run(['xdotool', 'getactivewindow'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return None

            window_id = result.stdout.strip()

            # Get window class
            result = subprocess.run(['xdotool', 'getwindowclassname', window_id],
                                  capture_output=True, text=True, timeout=5)
            window_class = result.stdout.strip() if result.returncode == 0 else ''

            # Get window title
            result = subprocess.run(['xdotool', 'getwindowname', window_id],
                                  capture_output=True, text=True, timeout=5)
            window_title = result.stdout.strip() if result.returncode == 0 else ''

            return {
                'class': window_class,
                'title': window_title,
                'initialClass': window_class,
                'initialTitle': window_title
            }

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.error(f"Error getting X11 active window: {e}")
        return None

    def get_active_window(self) -> Optional[Dict]:
        """Get active window information using available method."""
        if self.detection_method == "hyprland":
            return self.get_active_window_hyprland()
        elif self.detection_method == "x11":
            return self.get_active_window_x11()
        else:
            return None

    def detect_application_change(self) -> bool:
        """Detect if the active application has changed."""
        window_info = self.get_active_window()

        if not window_info:
            return False

        # Create a signature for the current window
        window_signature = f"{window_info.get('class', '')}:{window_info.get('title', '')}"

        if window_signature != self.current_window:
            self.current_window = window_signature
            return True

        return False

    async def monitor_applications(self, interval: float = 0.5):
        """Monitor applications and update vocabulary accordingly."""
        logger.info(f"Starting application monitoring (interval: {interval}s)")

        while True:
            try:
                if self.detect_application_change():
                    window_info = self.get_active_window()
                    if window_info:
                        app_class = window_info.get('class', '') or window_info.get('initialClass', '')
                        logger.info(f"Application changed to: {app_class}")

                        # Update vocabulary based on new application
                        self.vocabulary_manager.update_vocabulary(app_class)

                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                logger.info("Application monitoring stopped")
                break
            except Exception as e:
                logger.error(f"Error in application monitoring: {e}")
                await asyncio.sleep(interval)

    def list_detected_applications(self) -> Set[str]:
        """List all currently detected applications."""
        # This would need to be implemented based on the window system
        # For now, return common applications
        return {
            "Alacritty", "kitty", "gnome-terminal", "konsole",
            "code", "Code", "sublime_text", "vim", "nvim",
            "firefox", "chrome", "chromium", "brave",
            "discord", "slack", "teams", "zoom"
        }

async def main():
    """Main function for running the application detector."""
    import argparse

    parser = argparse.ArgumentParser(description="Hypr-Voice Application Detector")
    parser.add_argument('--interval', type=float, default=0.5,
                       help='Detection interval in seconds')
    parser.add_argument('--test', action='store_true',
                       help='Test detection and exit')
    parser.add_argument('--list', action='store_true',
                       help='List supported applications')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    detector = ApplicationDetector()

    if args.list:
        apps = detector.list_detected_applications()
        print("Supported applications:")
        for app in sorted(apps):
            print(f"  - {app}")
        return

    if args.test:
        print("Testing application detection...")
        window_info = detector.get_active_window()
        if window_info:
            print(f"Current window: {window_info}")
            app_class = window_info.get('class', '') or window_info.get('initialClass', '')
            print(f"Detected application: {app_class}")

            # Test vocabulary matching
            vm = detector.vocabulary_manager
            vm.update_vocabulary(app_class)
            print(f"Selected vocabulary: {vm.current_vocabulary}")
            print(f"Active keywords: {len(vm.active_keywords)}")
        else:
            print("No active window detected")
        return

    # Run monitoring
    try:
        await detector.monitor_applications(args.interval)
    except KeyboardInterrupt:
        logger.info("Application detector stopped by user")

if __name__ == '__main__':
    asyncio.run(main())