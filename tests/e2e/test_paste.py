#!/usr/bin/env python3
"""
Test script for clipboard pasting on Wayland/Hyprland
Tests multiple methods to paste text after a 5-second delay
"""

import subprocess
import time
import sys

def get_active_window():
    """Get the currently active window/application"""
    try:
        result = subprocess.run(
            ['hyprctl', 'activewindow', '-j'],
            capture_output=True,
            text=True,
            check=True
        )
        import json
        window_info = json.loads(result.stdout)
        return window_info.get('class', 'unknown')
    except Exception as e:
        print(f"Error getting active window: {e}")
        return 'unknown'

def method_1_wtype_simple(text):
    """Method 1: Simple wtype with Ctrl+V"""
    print("\n=== Method 1: wtype with simple Ctrl+V ===")
    try:
        # Copy to clipboard
        subprocess.run(['wl-copy'], input=text, text=True, check=True)
        time.sleep(0.1)
        
        # Paste with wtype
        subprocess.run(['wtype', '-M', 'ctrl', '-P', 'v', '-p', 'v', '-m', 'ctrl'], check=True)
        print("✓ Method 1 executed successfully")
        return True
    except Exception as e:
        print(f"✗ Method 1 failed: {e}")
        return False

def method_2_wtype_terminal(text):
    """Method 2: wtype with Ctrl+Shift+V for terminals"""
    print("\n=== Method 2: wtype with Ctrl+Shift+V (terminal) ===")
    try:
        # Copy to clipboard
        subprocess.run(['wl-copy'], input=text, text=True, check=True)
        time.sleep(0.1)
        
        # Paste with wtype for terminal
        subprocess.run(
            ['wtype', '-M', 'ctrl', '-M', 'shift', '-P', 'v', '-p', 'v', '-m', 'shift', '-m', 'ctrl'],
            check=True
        )
        print("✓ Method 2 executed successfully")
        return True
    except Exception as e:
        print(f"✗ Method 2 failed: {e}")
        return False

def method_3_wtype_direct_typing(text):
    """Method 3: Direct typing with wtype (no clipboard)"""
    print("\n=== Method 3: wtype direct typing ===")
    try:
        subprocess.run(['wtype', text], check=True)
        print("✓ Method 3 executed successfully")
        return True
    except Exception as e:
        print(f"✗ Method 3 failed: {e}")
        return False

def method_4_wtype_with_delay(text):
    """Method 4: wtype with longer delay before paste"""
    print("\n=== Method 4: wtype with 200ms delay ===")
    try:
        # Copy to clipboard
        subprocess.run(['wl-copy'], input=text, text=True, check=True)
        time.sleep(0.2)
        
        # Paste with wtype
        subprocess.run(['wtype', '-M', 'ctrl', '-P', 'v', '-p', 'v', '-m', 'ctrl'], check=True)
        print("✓ Method 4 executed successfully")
        return True
    except Exception as e:
        print(f"✗ Method 4 failed: {e}")
        return False


def main():
    test_text = "Hello from test_paste.py! This is a test of automated clipboard pasting. 🚀"
    
    print("=" * 70)
    print("CLIPBOARD PASTE TEST SCRIPT FOR HYPR-VOICE")
    print("=" * 70)
    print(f"\nTest text: {test_text}")
    print("\n📝 Usage:")
    print("   ./test_paste.py        - Auto-detect and use best method")
    print("   ./test_paste.py 1      - Method 1: wtype with Ctrl+V (PREFERRED FOR APPS)")
    print("   ./test_paste.py 2      - Method 2: wtype with Ctrl+Shift+V (PREFERRED FOR TERMINALS)")
    print("   ./test_paste.py 3      - Method 3: wtype direct typing (fallback)")
    print("   ./test_paste.py 4      - Method 4: wtype with 200ms delay")
    print("\n💡 Auto-mode uses Method 2 for terminals, Method 1 for other apps")
    print("\nYou have 5 seconds to switch to your target application...")
    print("(Switch to any text field where you want the text to appear)")
    
    # Get initial active window
    initial_app = get_active_window()
    print(f"\nCurrent active app: {initial_app}")
    
    # Countdown
    for i in range(5, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        time.sleep(1)
    print("\n")
    
    # Get final active window
    target_app = get_active_window()
    print(f"🎯 Target app: {target_app}")
    
    # Detect if terminal
    terminal_apps = ['kitty', 'alacritty', 'foot', 'wezterm', 'terminator', 'konsole', 'gnome-terminal', 'xterm']
    is_terminal = any(term in target_app.lower() for term in terminal_apps)
    
    if is_terminal:
        print(f"⚠️  Detected terminal application - will use terminal-specific methods")
    
    # Choose method based on command line argument
    if len(sys.argv) > 1:
        method = sys.argv[1]
        print(f"\n🎯 Running specific method: {method}")
        
        methods = {
            '1': method_1_wtype_simple,
            '2': method_2_wtype_terminal,
            '3': method_3_wtype_direct_typing,
            '4': method_4_wtype_with_delay,
        }

        if method in methods:
            success = methods[method](test_text)
            sys.exit(0 if success else 1)
        else:
            print(f"Unknown method: {method}")
            print("Available methods: 1, 2, 3, 4")
            sys.exit(1)
    else:
        # Run appropriate method automatically
        print("\n🎯 Auto-selecting method based on context...")
        
        if is_terminal:
            print("Using Method 2: Ctrl+Shift+V (terminal paste)")
            success = method_2_wtype_terminal(test_text)
        else:
            print("Using Method 1: Ctrl+V (standard paste)")
            success = method_1_wtype_simple(test_text)
        
        if not success:
            print("\n⚠️  Primary method failed, trying direct typing fallback...")
            # Try method 3 (direct typing) as fallback
            success = method_3_wtype_direct_typing(test_text)
        
        if success:
            print("\n✅ Text should have been pasted!")
        else:
            print("\n❌ All methods failed. Check the error messages above.")
        
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
