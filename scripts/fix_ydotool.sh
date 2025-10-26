#!/bin/bash
# Fix ydotool socket permissions issue

echo "=========================================="
echo "  Fixing ydotool socket permissions"
echo "=========================================="
echo ""

echo "🔍 Current status:"
ps aux | grep ydotoold | grep -v grep
echo ""
ls -la /tmp/.ydotool_socket 2>&1
echo ""

echo "Problem: Multiple ydotoold daemons are running (root + user)"
echo "Solution: Kill all and restart as current user only"
echo ""

read -p "Press Enter to fix this..."

# Kill all ydotoold processes
echo "Killing all ydotoold processes..."
sudo pkill ydotoold
sleep 1

# Remove old socket
if [ -S /tmp/.ydotool_socket ]; then
    echo "Removing old socket..."
    sudo rm -f /tmp/.ydotool_socket
fi

# Start ydotoold as current user
echo "Starting ydotoold as $USER..."
ydotoold > /tmp/ydotoold.log 2>&1 &

sleep 2

# Check status
echo ""
echo "✅ New status:"
ps aux | grep ydotoold | grep -v grep
echo ""
ls -la /tmp/.ydotool_socket 2>&1
echo ""

# Test it
echo "🧪 Testing ydotool..."
if ydotool key 1:0 2>&1; then
    echo "✅ ydotool is working!"
else
    echo "❌ ydotool still not working"
    echo "Check /tmp/ydotoold.log for errors"
fi

echo ""
echo "=========================================="
echo "  Done!"
echo "=========================================="
echo ""
echo "💡 To make this permanent, choose ONE option:"
echo ""
echo "OPTION 1: Add to Hyprland config (RECOMMENDED)"
echo "  Add this line to ~/.config/hypr/hyprland.conf:"
echo "    exec-once = ydotoold"
echo ""
echo "OPTION 2: Add to shell rc file (~/.bashrc or ~/.zshrc):"
echo "    # Start ydotoold if not running"
echo "    if ! pgrep -x ydotoold > /dev/null; then"
echo "        ydotoold > /tmp/ydotoold.log 2>&1 &"
echo "    fi"
echo ""
echo "OPTION 3: Create systemd user service (see setup_ydotool.sh)"
echo ""
echo "⚠️  Also check for system-wide ydotoold services:"
echo "  sudo systemctl list-units | grep ydotool"
echo "  If found, disable with: sudo systemctl disable ydotool"
echo ""
