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
            # Check for Hyprland using 'version' command
            # Note: hyprctl --version returns exit code 1, so we check for 'version' command instead
            result = subprocess.run(['hyprctl', 'version'],
                                  capture_output=True, text=True, timeout=5)
            # Check if output contains "Hyprland" (works even if returncode != 0)
            if 'Hyprland' in result.stdout or 'Hyprland' in result.stderr:
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
        """Get active window information using Hyprland with full metadata."""
        try:
            # Get active window info as JSON with all details
            result = subprocess.run(['hyprctl', 'activewindow', '-j'],
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                data = json.loads(result.stdout)
                # Return full Hyprland data for comprehensive context
                return data
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

    async def monitor_applications(self, interval: float = 0.2):
        """Monitor applications and update vocabulary accordingly."""
        logger.info(f"Starting application monitoring (interval: {interval}s)")

        while True:
            try:
                if self.detect_application_change():
                    window_info = self.get_active_window()
                    if window_info:
                        app_class = window_info.get('class', '') or window_info.get('initialClass', '')
                        app_title = window_info.get('title', '') or window_info.get('initialTitle', '')
                        logger.info(f"Application changed to: {app_class} - {app_title}")

                        # Update vocabulary based on new application
                        self.vocabulary_manager.update_vocabulary(app_class, app_title)

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
            print(f"\n{'='*60}")
            print(f"WINDOW INFO:")
            print(f"{'='*60}")
            print(f"  Class: {window_info.get('class', '')}")
            print(f"  Title: {window_info.get('title', '')}")
            print(f"  Initial Class: {window_info.get('initialClass', '')}")
            
            app_class = window_info.get('class', '') or window_info.get('initialClass', '')
            app_title = window_info.get('title', '') or window_info.get('initialTitle', '')
            
            # Test vocabulary matching
            vm = detector.vocabulary_manager
            vm.update_vocabulary(app_class, app_title)
            
            print(f"\n{'='*60}")
            print(f"VOCABULARY:")
            print(f"{'='*60}")
            print(f"  Selected vocabulary: {vm.current_vocabulary}")
            print(f"  Total active keywords: {len(vm.active_keywords)}")
            
            # Show context extraction details
            if vm.context_manager:
                print(f"\n{'='*60}")
                print(f"CONTEXT EXTRACTION:")
                print(f"{'='*60}")
                
                # Get comprehensive context
                context = vm.context_manager.get_comprehensive_context(window_info)
                
                # Shell history
                print(f"\n  📜 Shell History (last 10 of {len(context['context']['shell']['recent_commands'])}):")
                for i, cmd in enumerate(context['context']['shell']['recent_commands'][-10:], 1):
                    print(f"    {i}. {cmd[:80]}")
                
                # Clipboard
                print(f"\n  📋 Clipboard History ({len(context['context']['clipboard']['recent_entries'])} entries):")
                for i, entry in enumerate(context['context']['clipboard']['recent_entries'], 1):
                    preview = entry[:60].replace('\n', ' ')
                    print(f"    {i}. {preview}...")
                
                # Window context
                if 'window' in context['context']:
                    print(f"\n  🪟 Window Context:")
                    print(f"    Application: {context['context']['window']['application']}")
                    print(f"    Title: {context['context']['window']['title']}")
                
                # Extracted vocabulary
                print(f"\n  🔤 Extracted Vocabulary ({len(context['vocabulary'])} words):")
                # Display as clean list
                vocab_list = sorted(context['vocabulary'])
                print(f"    {vocab_list}")
                
                # Test initial_prompt generation
                print(f"\n  🎯 Initial Prompt Test:")
                initial_prompt = vm.get_initial_prompt(max_tokens=200)
                print(f"    Length: {len(initial_prompt)} chars (~{len(initial_prompt)//4} tokens)")
                print(f"    Preview: {initial_prompt[:150]}...")
                if len(initial_prompt) > 150:
                    print(f"    ...{initial_prompt[-50:]}")
                
                # Verify format
                checks = [
                    ("✓" if "," in initial_prompt else "✗", "Comma-separated format"),
                    ("✓" if len(initial_prompt) <= 800 else "✗", f"Under 800 chars limit ({len(initial_prompt)}/800)"),
                    ("✓" if initial_prompt.endswith(".") else "✗", "Ends with period"),
                    ("✓" if len(initial_prompt.split(", ")) >= 5 else "✗", f"Contains multiple terms ({len(initial_prompt.split(', '))} terms)")
                ]
                print(f"\n  ✅ Format Checks:")
                for status, check in checks:
                    print(f"    {status} {check}")
            
            print(f"\n{'='*60}\n")
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