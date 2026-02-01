#!/usr/bin/env python3
"""
Quick universal copy-paste utility CLI.

Usage:
    python cli.py              # Paste primary selection
    python cli.py --copy TEXT  # Copy text to primary
    python cli.py --type TEXT  # Type text instead of paste
    python cli.py --monitor    # Monitor selection changes
"""

import sys
import argparse
import signal
from universal_clipboard import (
    UniversalClipboard,
    ProgrammaticPaster,
    PrimarySelectionMonitor
)


def main():
    parser = argparse.ArgumentParser(
        description='Universal clipboard utility for X11 and Wayland',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Paste primary selection to stdout
  %(prog)s --copy "text"      # Copy text to primary selection
  %(prog)s --type "text"      # Type text programmatically
  %(prog)s --monitor          # Monitor selection changes
        """
    )

    parser.add_argument(
        '--copy',
        metavar='TEXT',
        help='Copy text to primary selection'
    )
    parser.add_argument(
        '--type',
        metavar='TEXT',
        help='Type text programmatically instead of paste'
    )
    parser.add_argument(
        '--monitor',
        action='store_true',
        help='Monitor primary selection for changes'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=0.5,
        help='Delay before paste/type in seconds (default: 0.5)'
    )
    parser.add_argument(
        '--backend',
        choices=['auto', 'x11', 'wayland'],
        default='auto',
        help='Force specific backend (default: auto-detect)'
    )
    parser.add_argument(
        '--paste-method',
        choices=['auto', 'xdotool', 'ydotool', 'wtype'],
        default='auto',
        help='Force specific paste method (default: auto-detect)'
    )

    args = parser.parse_args()

    # Initialize clipboard
    clipboard = UniversalClipboard()

    if not clipboard.is_available():
        print("Error: No clipboard backend available", file=sys.stderr)
        print("Install xsel/xclip for X11 or wl-clipboard for Wayland", file=sys.stderr)
        sys.exit(1)

    # Handle copy operation
    if args.copy:
        if clipboard.set_primary(args.copy):
            print(f"Copied to primary selection: {args.copy}", file=sys.stderr)
            sys.exit(0)
        else:
            print("Error: Failed to copy to primary selection", file=sys.stderr)
            sys.exit(1)

    # Handle type operation
    if args.type:
        paster = ProgrammaticPaster(method=args.paste_method)

        if not paster.is_available():
            print(f"Error: Paste method '{paster.method}' not available", file=sys.stderr)
            print("Install xdotool (X11), ydotool, or wtype (Wayland)", file=sys.stderr)
            sys.exit(1)

        print(f"Typing in {args.delay}s... (focus target window)", file=sys.stderr)
        if paster.paste_text(args.type, delay=args.delay):
            print(f"Typed: {args.type}", file=sys.stderr)
            sys.exit(0)
        else:
            print("Error: Failed to type text", file=sys.stderr)
            sys.exit(1)

    # Handle monitor operation
    if args.monitor:
        def on_selection_change(text: str):
            print(f"Selection changed: {text[:100]}{'...' if len(text) > 100 else ''}")

        monitor = PrimarySelectionMonitor()
        monitor.start(on_selection_change)

        print("Monitoring primary selection (Ctrl+C to stop)...", file=sys.stderr)

        # Handle Ctrl+C gracefully
        def signal_handler(sig, frame):
            monitor.stop()
            print("\nStopped monitoring", file=sys.stderr)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Keep running
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            signal_handler(None, None)

    # Default: paste primary selection
    text = clipboard.get_primary()
    if text:
        print(text)
        sys.exit(0)
    else:
        print("Error: No primary selection content", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
