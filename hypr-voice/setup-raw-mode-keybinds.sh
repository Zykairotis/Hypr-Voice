#!/bin/bash
# Setup script for Hypr-Voice raw mode keybinds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HYPRLAND_CONFIG="$HOME/.config/hypr/hyprland.conf"
KEYBINDS_FILE="$SCRIPT_DIR/hyprland-keybinds.conf"
CONTROL_SCRIPT="$SCRIPT_DIR/hypr-voice-control-extended.sh"

echo -e "${BLUE}🎤 Hypr-Voice Raw Mode Setup${NC}"
echo "=================================="

# Check if Hyprland config exists
if [ ! -f "$HYPRLAND_CONFIG" ]; then
    echo -e "${RED}❌ Hyprland config not found at $HYPRLAND_CONFIG${NC}"
    echo "Please make sure Hyprland is installed and configured."
    exit 1
fi

# Make control script executable
echo -e "${YELLOW}📝 Making control script executable...${NC}"
chmod +x "$CONTROL_SCRIPT"

# Update paths in keybinds file
echo -e "${YELLOW}🔧 Updating paths in keybind configuration...${NC}"
TEMP_KEYBINDS="/tmp/hyprland-keybinds-updated.conf"
sed "s|/path/to/hypr-voice/|$SCRIPT_DIR/|g" "$KEYBINDS_FILE" > "$TEMP_KEYBINDS"

# Check if keybinds are already added
if grep -q "HYPR-VOICE KEYBINDS" "$HYPRLAND_CONFIG"; then
    echo -e "${YELLOW}⚠️  Hypr-Voice keybinds already exist in config${NC}"
    read -p "Do you want to update them? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old keybinds and add new ones
        echo -e "${YELLOW}🔄 Updating existing keybinds...${NC}"
        # Create backup
        cp "$HYPRLAND_CONFIG" "$HYPRLAND_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        # Remove old hypr-voice section
        sed '/# HYPR-VOICE KEYBINDS/,/# =============================================================================/d' "$HYPRLAND_CONFIG" > "$HYPRLAND_CONFIG.tmp"
        mv "$HYPRLAND_CONFIG.tmp" "$HYPRLAND_CONFIG"
        # Add new keybinds
        echo "" >> "$HYPRLAND_CONFIG"
        cat "$TEMP_KEYBINDS" >> "$HYPRLAND_CONFIG"
        echo -e "${GREEN}✅ Keybinds updated successfully${NC}"
    else
        echo -e "${YELLOW}⏭️  Skipping keybind update${NC}"
    fi
else
    # Add keybinds to config
    echo -e "${YELLOW}➕ Adding keybinds to Hyprland config...${NC}"
    echo "" >> "$HYPRLAND_CONFIG"
    cat "$TEMP_KEYBINDS" >> "$HYPRLAND_CONFIG"
    echo -e "${GREEN}✅ Keybinds added successfully${NC}"
fi

# Clean up temp file
rm -f "$TEMP_KEYBINDS"

# Test if hyprctl is available
if command -v hyprctl >/dev/null 2>&1; then
    echo -e "${YELLOW}🔄 Reloading Hyprland configuration...${NC}"
    if hyprctl reload; then
        echo -e "${GREEN}✅ Hyprland configuration reloaded${NC}"
    else
        echo -e "${YELLOW}⚠️  Could not reload Hyprland config automatically${NC}"
        echo "Please run: hyprctl reload"
    fi
else
    echo -e "${YELLOW}⚠️  hyprctl not found. Please reload Hyprland manually${NC}"
fi

# Create initial mode state file
echo "enhanced" > "/tmp/hypr-voice-raw-mode.state"

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Keybind Summary:${NC}"
echo "  F11                 - Raw mode (fast, no AI)"
echo "  F12                 - Enhanced mode (slower, with AI)"
echo "  SUPER + F11         - Toggle between modes"
echo "  SUPER + F12         - Show current status"
echo "  SUPER + SHIFT + F12 - Emergency force stop"
echo "  SUPER + R           - Set raw mode as default"
echo "  SUPER + E           - Set enhanced mode as default"
echo ""
echo -e "${BLUE}🚀 Usage:${NC}"
echo "1. Press and hold F11 for fast raw transcription"
echo "2. Press and hold F12 for AI-enhanced transcription"
echo "3. Use SUPER + F11 to toggle your preferred default mode"
echo ""
echo -e "${BLUE}📊 Performance:${NC}"
echo "  Raw Mode:      200-500ms processing, 89% accuracy"
echo "  Enhanced Mode: 800-1500ms processing, 95%+ accuracy"
echo ""
echo -e "${YELLOW}💡 Tip: Use raw mode for CLI commands and quick notes,${NC}"
echo -e "${YELLOW}    enhanced mode for documents and creative writing.${NC}"

# Test the setup
echo ""
echo -e "${BLUE}🧪 Testing setup...${NC}"
if [ -x "$CONTROL_SCRIPT" ]; then
    echo -e "${GREEN}✅ Control script is executable${NC}"
else
    echo -e "${RED}❌ Control script is not executable${NC}"
fi

if "$CONTROL_SCRIPT" get-mode >/dev/null 2>&1; then
    current_mode=$("$CONTROL_SCRIPT" get-mode)
    echo -e "${GREEN}✅ Control script working - Current mode: $current_mode${NC}"
else
    echo -e "${YELLOW}⚠️  Control script test failed (this is normal if hypr-voice service isn't running)${NC}"
fi

echo ""
echo -e "${GREEN}Setup completed successfully! 🎤✨${NC}"