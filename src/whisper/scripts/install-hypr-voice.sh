#!/bin/bash
# Installation script for Hypr-Voice Push-to-Talk

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}     Hypr-Voice Push-to-Talk Installation${NC}"
echo -e "${BLUE}===============================================${NC}"
echo ""

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"
HYPRLAND_CONFIG="$HOME/.config/hypr"

# Step 1: Make scripts executable
echo -e "${BLUE}[1/5]${NC} Making scripts executable..."
chmod +x "$WHISPER_ROOT/hypr-voice-type.py"
chmod +x "$SCRIPT_DIR/hypr-voice-daemon.sh"
chmod +x "$SCRIPT_DIR/hypr-voice-record.sh"
chmod +x "$SCRIPT_DIR/hypr-voice-quick.sh"
echo -e "${GREEN}✓${NC} Scripts are executable"

# Step 2: Check dependencies
echo -e "\n${BLUE}[2/5]${NC} Checking dependencies..."
MISSING_DEPS=""

if ! command -v wtype &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS wtype"
fi

if ! command -v nc &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS netcat-openbsd"
fi

if ! command -v arecord &> /dev/null; then
    MISSING_DEPS="$MISSING_DEPS alsa-utils"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo -e "${YELLOW}[WARN]${NC} Missing dependencies:$MISSING_DEPS"
    echo -e "${YELLOW}[INFO]${NC} Install with: sudo apt-get install$MISSING_DEPS"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓${NC} All dependencies installed"
fi

# Step 3: Install systemd service (optional)
echo -e "\n${BLUE}[3/5]${NC} Install systemd user service?"
read -p "This will allow auto-start on login (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/.config/systemd/user"
    cp "$WHISPER_ROOT/config/hypr-voice.service" "$HOME/.config/systemd/user/"
    
    # Update paths in service file
    sed -i "s|/home/mewtwo|$HOME|g" "$HOME/.config/systemd/user/hypr-voice.service"
    
    systemctl --user daemon-reload
    echo -e "${GREEN}✓${NC} Systemd service installed"
    echo -e "${YELLOW}[INFO]${NC} Enable with: systemctl --user enable hypr-voice.service"
    echo -e "${YELLOW}[INFO]${NC} Start with: systemctl --user start hypr-voice.service"
else
    echo -e "${YELLOW}[SKIP]${NC} Systemd service not installed"
fi

# Step 4: Configure Hyprland keybinds
echo -e "\n${BLUE}[4/5]${NC} Configure Hyprland keybinds?"
echo -e "${YELLOW}[INFO]${NC} This will add F9 push-to-talk bindings"
read -p "Add to hyprland.conf? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Check if hyprland config exists
    if [ ! -d "$HYPRLAND_CONFIG" ]; then
        echo -e "${YELLOW}[WARN]${NC} Hyprland config not found at $HYPRLAND_CONFIG"
        echo -e "${YELLOW}[INFO]${NC} Creating directory..."
        mkdir -p "$HYPRLAND_CONFIG"
    fi
    
    # Copy hyprvoice.conf
    cp "$WHISPER_ROOT/config/hyprvoice.conf" "$HYPRLAND_CONFIG/"
    
    # Update paths in config
    sed -i "s|/home/mewtwo|$HOME|g" "$HYPRLAND_CONFIG/hyprvoice.conf"
    
    # Check if already sourced
    if [ -f "$HYPRLAND_CONFIG/hyprland.conf" ]; then
        if ! grep -q "hyprvoice.conf" "$HYPRLAND_CONFIG/hyprland.conf"; then
            echo "" >> "$HYPRLAND_CONFIG/hyprland.conf"
            echo "# Hypr-Voice Push-to-Talk" >> "$HYPRLAND_CONFIG/hyprland.conf"
            echo "source = ~/.config/hypr/hyprvoice.conf" >> "$HYPRLAND_CONFIG/hyprland.conf"
            echo -e "${GREEN}✓${NC} Added source line to hyprland.conf"
        else
            echo -e "${YELLOW}[INFO]${NC} hyprvoice.conf already sourced"
        fi
    else
        echo -e "${YELLOW}[WARN]${NC} hyprland.conf not found"
        echo -e "${YELLOW}[INFO]${NC} Add this line to your hyprland.conf:"
        echo -e "       source = ~/.config/hypr/hyprvoice.conf"
    fi
    
    echo -e "${GREEN}✓${NC} Keybinds configured"
else
    echo -e "${YELLOW}[SKIP]${NC} Keybinds not configured"
    echo -e "${YELLOW}[INFO]${NC} Manual setup:"
    echo -e "       1. Copy: cp $WHISPER_ROOT/config/hyprvoice.conf ~/.config/hypr/"
    echo -e "       2. Add to hyprland.conf: source = ~/.config/hypr/hyprvoice.conf"
fi

# Step 5: Test the setup
echo -e "\n${BLUE}[5/5]${NC} Installation complete!"
echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}          Installation Successful!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""
echo -e "${YELLOW}Quick Start:${NC}"
echo -e "  1. Start the Whisper server:"
echo -e "     ${BLUE}$SCRIPT_DIR/start_hybrid_server.sh${NC}"
echo ""
echo -e "  2. Start the PTT daemon:"
echo -e "     ${BLUE}$SCRIPT_DIR/hypr-voice-daemon.sh start${NC}"
echo ""
echo -e "  3. Reload Hyprland config:"
echo -e "     ${BLUE}hyprctl reload${NC}"
echo ""
echo -e "${YELLOW}Usage:${NC}"
echo -e "  • Press ${GREEN}F9${NC} to start recording"
echo -e "  • Release ${GREEN}F9${NC} to stop and transcribe"
echo -e "  • Text will be typed automatically"
echo ""
echo -e "${YELLOW}Alternative Methods:${NC}"
echo -e "  • Quick record (5 seconds): ${BLUE}$SCRIPT_DIR/hypr-voice-quick.sh${NC}"
echo -e "  • Direct mode (no daemon): Use alternative bindings in hyprvoice.conf"
echo ""
echo -e "${YELLOW}Test command:${NC}"
echo -e "  ${BLUE}echo 'test' | $WHISPER_ROOT/hypr-voice-type.py start${NC}"
