#!/usr/bin/env python3

import subprocess
import time
import sys

def test_wlpaste_pasting():
    """Test if wlpaste can paste to any window regardless of class"""

    print("🧪 Testing wlpaste Universal Paste Capability")
    print("=" * 50)

    # Test text to paste
    test_text = "🧪 TEST PASTE from wlpaste at " + time.strftime("%H:%M:%S")

    print(f"📝 Test text: '{test_text}'")
    print(f"⏰ Starting 4-second countdown...")
    print(f"💡 QUICKLY switch to any window/app (terminal, browser, VS Code, etc.)")
    print("")

    # Copy test text to clipboard
    try:
        result = subprocess.run(['wl-copy'], input=test_text, text=True, capture_output=True)
        if result.returncode != 0:
            print("❌ Failed to copy to clipboard with wl-copy")
            print(f"Error: {result.stderr}")
            return False
        print("✅ Text copied to clipboard successfully")
    except FileNotFoundError:
        print("❌ wl-copy not found. Install with: sudo pacman -S wl-clipboard")
        return False

    # Countdown
    for i in range(4, 0, -1):
        print(f"⏳ {i} seconds - switch to your target window now!")
        time.sleep(1)

    print("")
    print("🎯 PASTING NOW!")
    print("💻 Attempting to paste with wlpaste...")

    # Try different paste methods
    paste_methods = [
        ("wl-paste --primary", ["wl-paste", "--primary"]),
        ("wl-paste", ["wl-paste"]),
        ("wtype -M ctrl v -m ctrl", ["wtype", "-M", "ctrl", "v", "-m", "ctrl"]),
        ("wtype", ["wtype", test_text])  # Direct typing
    ]

    results = {}

    for method_name, cmd in paste_methods:
        print(f"\n🔧 Testing method: {method_name}")
        try:
            if "wtype" in method_name and len(cmd) > 2:
                # Direct typing with wtype
                result = subprocess.run(cmd, capture_output=True, text=True)
                success = result.returncode == 0
            else:
                # Paste from clipboard
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    print(f"📤 Pasted content: '{result.stdout.strip()}'")
                    success = True
                else:
                    print(f"❌ No content returned or error")
                    success = False

            results[method_name] = {
                "success": success,
                "error": result.stderr if result.returncode != 0 else None
            }

            if success:
                print(f"✅ {method_name} - SUCCESS")
            else:
                print(f"❌ {method_name} - FAILED")
                if result.stderr:
                    print(f"   Error: {result.stderr.strip()}")

        except FileNotFoundError as e:
            print(f"❌ {method_name} - Command not found: {e.filename}")
            results[method_name] = {"success": False, "error": f"Command not found: {e.filename}"}
        except Exception as e:
            print(f"❌ {method_name} - Unexpected error: {e}")
            results[method_name] = {"success": False, "error": str(e)}

    # Summary
    print("\n" + "=" * 50)
    print("📊 RESULTS SUMMARY:")
    print("=" * 50)

    successful_methods = []
    failed_methods = []

    for method, result in results.items():
        if result["success"]:
            successful_methods.append(method)
            print(f"✅ {method}")
        else:
            failed_methods.append(method)
            print(f"❌ {method} - {result['error'] or 'Unknown error'}")

    print(f"\n🎯 Successful methods: {len(successful_methods)}")
    print(f"💥 Failed methods: {len(failed_methods)}")

    if successful_methods:
        print(f"\n🏆 WORKING SOLUTIONS:")
        for method in successful_methods:
            print(f"   • {method}")

    if failed_methods:
        print(f"\n🔧 MISSING TOOLS:")
        print(f"   Install with: sudo pacman -S wl-clipboard wtype")

    return len(successful_methods) > 0

if __name__ == "__main__":
    print("🚀 Universal Paste Test Starting...")
    print("💡 Get ready to switch to any window in 4 seconds!")
    print("")

    success = test_wlpaste_pasting()

    if success:
        print(f"\n🎉 AT LEAST ONE METHOD WORKS!")
        print("💡 You may not need complex window detection after all!")
    else:
        print(f"\n😞 NO METHODS WORKED")
        print("💡 You may need window detection or different tools")

    sys.exit(0 if success else 1)