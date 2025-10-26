#!/bin/bash
# Diagnose clipboard pasting capabilities on the system

echo "========================================"
echo "  Hypr-Voice Paste Diagnostics"
echo "========================================"
echo ""

# Check required tools
echo "📋 Checking required tools..."
echo ""

check_tool() {
    if command -v "$1" &> /dev/null; then
        echo "  ✅ $1 is installed: $(which $1)"
    else
        echo "  ❌ $1 is NOT installed"
        echo "     Install with: $2"
    fi
}

check_tool "wtype" "sudo pacman -S wtype"
check_tool "wl-copy" "sudo pacman -S wl-clipboard"
check_tool "wl-paste" "sudo pacman -S wl-clipboard"
check_tool "hyprctl" "Part of Hyprland"
check_tool "ydotool" "sudo pacman -S ydotool (optional)"

echo ""
echo "📊 System Information..."
echo ""

# Check compositor
if pgrep -x "Hyprland" > /dev/null; then
    echo "  ✅ Hyprland is running"
    HYPRLAND_VERSION=$(hyprctl version | head -n1)
    echo "     Version: $HYPRLAND_VERSION"
else
    echo "  ⚠️  Hyprland is not running"
fi

# Check Wayland
if [ "$XDG_SESSION_TYPE" = "wayland" ]; then
    echo "  ✅ Wayland session detected"
else
    echo "  ⚠️  Not a Wayland session (XDG_SESSION_TYPE=$XDG_SESSION_TYPE)"
fi

echo ""
echo "🧪 Testing clipboard operations..."
echo ""

# Test wl-copy
TEST_TEXT="Test from diagnose_paste.sh"
if echo "$TEST_TEXT" | wl-copy 2>/dev/null; then
    echo "  ✅ wl-copy works"
    
    # Test wl-paste
    PASTED=$(wl-paste 2>/dev/null)
    if [ "$PASTED" = "$TEST_TEXT" ]; then
        echo "  ✅ wl-paste works"
    else
        echo "  ❌ wl-paste failed or returned wrong content"
    fi
else
    echo "  ❌ wl-copy failed"
fi

# Test wtype
echo ""
echo "🎹 Testing wtype..."
if wtype --version &>/dev/null; then
    echo "  ✅ wtype is functional"
else
    echo "  ❌ wtype has issues"
fi

# Check active window
echo ""
echo "🪟 Current active window..."
if command -v hyprctl &> /dev/null; then
    ACTIVE_WIN=$(hyprctl activewindow -j 2>/dev/null)
    if [ $? -eq 0 ]; then
        APP_CLASS=$(echo "$ACTIVE_WIN" | grep -o '"class":"[^"]*"' | cut -d'"' -f4)
        APP_TITLE=$(echo "$ACTIVE_WIN" | grep -o '"title":"[^"]*"' | cut -d'"' -f4)
        echo "  App: $APP_CLASS"
        echo "  Title: $APP_TITLE"
    fi
fi

echo ""
echo "========================================"
echo "  Diagnosis Complete"
echo "========================================"
echo ""
echo "💡 Next steps:"
echo "   1. Ensure all tools are installed"
echo "   2. Run: ./test_paste.py"
echo "   3. Switch to a text field during countdown"
echo "   4. Check if text pastes successfully"
echo ""
