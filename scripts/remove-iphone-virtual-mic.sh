#!/bin/bash
# Remove iPhone Virtual Microphone Setup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}🧹 Removing iPhone Virtual Microphone...${NC}"
echo ""

# Find and unload loopback modules
echo "Removing loopback modules..."
pactl list modules short | grep loopback | grep iphone_virtual_mic | while read -r line; do
    MODULE_ID=$(echo "$line" | awk '{print $1}')
    pactl unload-module "$MODULE_ID" 2>/dev/null && echo -e "${GREEN}✓${NC} Unloaded loopback module $MODULE_ID" || true
done

# Find and unload null-sink modules
echo "Removing virtual sink modules..."
pactl list modules short | grep "module-null-sink" | grep iphone_virtual_mic | while read -r line; do
    MODULE_ID=$(echo "$line" | awk '{print $1}')
    pactl unload-module "$MODULE_ID" 2>/dev/null && echo -e "${GREEN}✓${NC} Unloaded sink module $MODULE_ID" || true
done

echo ""
echo -e "${GREEN}✓ iPhone virtual microphone removed${NC}"
echo ""
echo "To restore original audio configuration, edit:"
echo "  config/hypr_voice/whisper/audio-profile.yaml"
