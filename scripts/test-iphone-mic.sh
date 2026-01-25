#!/bin/bash
# Test iPhone Microphone via HDMI Monitor
# Stream audio from iPhone to computer, capture via HDMI output monitor

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎤 iPhone Microphone Test (via HDMI Monitor)${NC}"
echo ""

# Ensure HDMI monitor is set as default source
pactl set-default-source alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor

echo -e "${GREEN}Current audio source:${NC}"
pactl get-default-source
echo ""

echo -e "${YELLOW}Instructions:${NC}"
echo "1. On your iPhone, play audio (use a mic app, Bluetooth, or any audio)"
echo "2. Make sure audio is routed to this computer's HDMI output"
echo "3. Recording for 5 seconds..."
echo ""

# Record 5 seconds
echo -e "${GREEN}[Recording...]${NC}"
timeout 5 parecord -d alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor /tmp/test-iphone-mic.wav

# Check audio levels
echo ""
echo -e "${GREEN}[Analyzing...]${NC}"
ffmpeg -i /tmp/test-iphone-mic.wav -af "volumedetect" -vn -sn -dn -f null /dev/null 2>&1 | grep -E "(mean_volume|max_volume|Duration)" | sed 's/^/  /'

echo ""
echo -e "${GREEN}✓ Test complete!${NC}"
echo ""
echo "Play back the recording:"
echo "  paplay /tmp/test-iphone-mic.wav"
echo ""

# Show audio level interpretation
MEAN=$(ffmpeg -i /tmp/test-iphone-mic.wav -af "volumedetect" -vn -sn -dn -f null /dev/null 2>&1 | grep "mean_volume" | grep -oP "[0-9.-]+ dB")
MEAN_NUM=$(echo "$MEAN" | grep -oP "[-0-9.]+")

if (( $(echo "$MEAN_NUM < -60" | bc -l) )); then
    echo -e "${YELLOW}⚠ Audio level is low. Make sure iPhone is sending audio to computer.${NC}"
elif (( $(echo "$MEAN_NUM < -30" | bc -l) )); then
    echo -e "${GREEN}✓ Audio level is good!${NC}"
else
    echo -e "${GREEN}✓ Audio level is excellent!${NC}"
fi
