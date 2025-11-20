#!/usr/bin/env python3
"""
Test Runner for Helper Agent

This script runs all tests for the helper agent service.
"""

import sys
import os
import subprocess
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_tests():
    """Run all tests."""
    print("Running Helper Agent Tests...")
    print("=" * 50)

    # Test files to run
    test_files = [
        "test_client.py",
        "test_integration.py"
    ]

    all_passed = True

    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        print("-" * 30)

        try:
            # Run the test file
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )

            if result.returncode == 0:
                print(f"✅ {test_file} passed")
                if result.stdout:
                    print("Output:", result.stdout)
            else:
                print(f"❌ {test_file} failed")
                print("Error:", result.stderr)
                all_passed = False

        except Exception as e:
            print(f"❌ Error running {test_file}: {e}")
            all_passed = False

    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(run_tests())