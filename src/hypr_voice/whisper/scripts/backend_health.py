#!/usr/bin/env python3
"""Backend health checker for Hypr-Whisper.

Shows which window and input backends are detected and optionally performs a
tiny typing test. Designed to be safe-by-default (no typing unless --type-test
is provided).
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running as a script with PYTHONPATH configured
if __name__ == "__main__" and not __package__:
    project_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(project_root / "src"))
    __package__ = "hypr_voice.whisper.scripts"

from ..backends.window_backends import detect_backend
from ..backends.input_backends import detect_input_backend


def main():
    parser = argparse.ArgumentParser(description="Hypr-Whisper backend health check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    parser.add_argument("--type-test", action="store_true", help="Send a short typing test ('Hello')")
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    wb = detect_backend()
    print(f"Window backend: {wb.name}")

    win = wb.get_active_window()
    if win:
        print("Active window:")
        trimmed_raw = win.get("raw")
        if isinstance(trimmed_raw, dict) and len(json.dumps(trimmed_raw)) > 400:
            trimmed_raw = {k: v for k, v in list(trimmed_raw.items())[:10]}
        print(json.dumps({k: v for k, v in win.items() if k != "raw"}, indent=2))
        if trimmed_raw:
            print("raw (truncated):")
            print(json.dumps(trimmed_raw, indent=2))
    else:
        print("Active window: not detected")

    ib = detect_input_backend(window_backend=wb.name)
    print(f"Input backend: {ib.name}")

    if args.type_test:
        success = ib.type_text_instant("Hello")
        status = "success" if success else "failed"
        print(f"Typing test ({ib.name}): {status}")
    else:
        print("Typing test: skipped (run with --type-test to send 'Hello')")


if __name__ == "__main__":
    main()
