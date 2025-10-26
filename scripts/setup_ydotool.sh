#!/bin/bash
# Setup ydotool for better Electron app paste support

echo "=========================================="
echo "  Setting up ydotool for Hypr-Voice"
echo "=========================================="
echo ""

# Check if ydotool is installed
if ! command -v ydotool &> /dev/null; then
    echo "❌ ydotool is not installed"
    echo ""
    echo "Install with:"
    echo "  sudo pacman -S ydotool"
    exit 1
fi

echo "✅ ydotool is installed"
echo ""

# Check if user is in input group
if groups | grep -q input; then
    echo "✅ User is already in 'input' group"
else
    echo "⚠️  User is NOT in 'input' group"
    echo ""
    read -p "Add current user to 'input' group? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo usermod -aG input $USER
        echo "✅ Added user to 'input' group"
        echo "⚠️  You need to log out and back in for this to take effect!"
    fi
fi

echo ""
echo "📝 Setting up ydotool daemon..."
echo ""

# Check if ydotoold is running
if pgrep -x ydotoold > /dev/null; then
    echo "✅ ydotoold daemon is already running"
else
    echo "⚠️  ydotoold daemon is not running"
    echo ""
    echo "Starting ydotoold daemon..."
    
    # Try to start ydotoold in background
    if ydotoold &> /tmp/ydotoold.log & then
        sleep 1
        if pgrep -x ydotoold > /dev/null; then
            echo "✅ ydotoold daemon started successfully"
        else
            echo "❌ Failed to start ydotoold daemon"
            echo "Check /tmp/ydotoold.log for errors"
        fi
    fi
fi

echo ""
echo "🧪 Testing ydotool..."
echo ""

# Test ydotool
if timeout 2 ydotool key 1:0 2>/dev/null; then
    echo "✅ ydotool is working!"
else
    echo "❌ ydotool test failed"
    echo ""
    echo "Possible issues:"
    echo "  1. User not in 'input' group (log out and back in)"
    echo "  2. ydotoold daemon not running"
    echo "  3. Permission issues with /dev/uinput"
    echo ""
    echo "Try running manually:"
    echo "  ydotoold &"
fi

echo ""
echo "=========================================="
echo "  Setup Complete"
echo "=========================================="
echo ""
echo "💡 To make ydotoold start automatically:"
echo ""
echo "Create systemd user service:"
echo "  mkdir -p ~/.config/systemd/user"
echo "  cat > ~/.config/systemd/user/ydotool.service << 'EOF'"
echo "[Unit]"
echo "Description=ydotool daemon"
echo "After=graphical-session.target"
echo ""
echo "[Service]"
echo "Type=simple"
echo "ExecStart=/usr/bin/ydotoold"
echo "Restart=on-failure"
echo ""
echo "[Install]"
echo "WantedBy=default.target"
echo "EOF"
echo ""
echo "Then enable it:"
echo "  systemctl --user enable --now ydotool.service"
echo ""
