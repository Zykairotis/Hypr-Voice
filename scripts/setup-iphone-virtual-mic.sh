#!/bin/bash
# Setup iPhone as Virtual Microphone for Hypr-Whisper
# This creates a virtual audio device that routes iPhone Bluetooth audio to Whisper

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🎤 iPhone Virtual Microphone Setup for Hypr-Whisper${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WHISPER_CONFIG_DIR="${HYPR_VOICE_WHISPER_CONFIG_DIR:-$PROJECT_ROOT/config/hypr_voice/whisper}"

# Find the iPhone Bluetooth source
echo -e "${GREEN}[1/4]${NC} Finding iPhone Bluetooth source..."
IPHONE_SOURCE=$(pactl list sources short | grep -i "AC_86_A3_46_E1_8B" | grep -v monitor | awk '{print $1}' | head -1)

if [ -z "$IPHONE_SOURCE" ]; then
    echo -e "${RED}✗ iPhone Bluetooth source not found!${NC}"
    echo ""
    echo "Please make sure:"
    echo "1. iPhone is paired via Bluetooth"
    echo "2. iPhone is connected"
    echo "3. Microphone app on iPhone is streaming audio"
    echo ""
    echo "Available sources:"
    pactl list sources short
    exit 1
fi

IPHONE_SOURCE_NAME=$(pactl list sources short | grep "^$IPHONE_SOURCE " | awk '{print $2}')
echo -e "${GREEN}✓${NC} Found iPhone source: $IPHONE_SOURCE_NAME"
echo ""

# Create virtual sink
echo -e "${GREEN}[2/4]${NC} Creating virtual microphone sink..."
SINK_ID=$(pactl load-module module-null-sink \
    sink_name=iphone_virtual_mic \
    sink_properties="device.description=iPhone-Virtual-Mic device.icon_name=phone-microphone" \
    channels=1 \
    rate=16000 \
    format=s16le)

if [ -n "$SINK_ID" ]; then
    echo -e "${GREEN}✓${NC} Created virtual sink with ID: $SINK_ID"
else
    echo -e "${YELLOW}⚠${NC} Virtual sink may already exist"
    SINK_ID="existing"
fi
echo ""

# Create loopback from iPhone to virtual sink
echo -e "${GREEN}[3/4]${NC} Creating audio route from iPhone to virtual mic..."
LOOPBACK_ID=$(pactl load-module module-loopback \
    source="$IPHONE_SOURCE_NAME" \
    sink=iphone_virtual_mic \
    channels=1 \
    rate=16000 \
    format=s16le)

if [ -n "$LOOPBACK_ID" ]; then
    echo -e "${GREEN}✓${NC} Created loopback with ID: $LOOPBACK_ID"
else
    echo -e "${YELLOW}⚠${NC} Loopback may already exist"
    LOOPBACK_ID="existing"
fi
echo ""

# Update audio-profile.yaml
echo -e "${GREEN}[4/4]${NC} Updating Hypr-Whisper audio configuration..."
AUDIO_PROFILE="$WHISPER_CONFIG_DIR/audio-profile.yaml"

# Create backup
if [ -f "$AUDIO_PROFILE" ]; then
    cp "$AUDIO_PROFILE" "$AUDIO_PROFILE.bak"
fi

cat > "$AUDIO_PROFILE" << EOF
# iPhone Virtual Microphone Configuration
alsa:
  suppress_warnings: true
  use_pulseaudio_only: true

audio:
  channels: 1
  chunk_size: 2048
  format: int16
  sample_rate: 16000

pulseaudio:
  default_source: iphone_virtual_mic.monitor
  device_name: iPhone Virtual Microphone
  device_type: virtual_microphone

recording:
  auto_cleanup:
    days_to_keep: 7
    enabled: false
  channels: 1
  format: wav
  sample_rate: 16000
  save_recordings: true
EOF

echo -e "${GREEN}✓${NC} Updated audio configuration"
echo ""

# Set as default source
pactl set-default-source iphone_virtual_mic.monitor

# Summary
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ iPhone Virtual Microphone Setup Complete!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Virtual microphone: ${GREEN}iphone_virtual_mic.monitor${NC}"
echo ""
echo "To test recording:"
echo "  parecord -d iphone_virtual_mic.monitor /tmp/test-iphone.wav"
echo ""
echo "To play back test:"
echo "  paplay /tmp/test-iphone.wav"
echo ""
echo "To start Whisper with iPhone mic:"
echo "  cd $PROJECT_ROOT"
echo "  ./scripts/start_hybrid_server.sh start"
echo ""
echo "${YELLOW}To remove this setup, run:${NC}"
echo "  pactl unload-module $LOOPBACK_ID 2>/dev/null || true"
echo "  pactl unload-module $SINK_ID 2>/dev/null || true"
echo ""
