#!/bin/bash
# WhisperLive Client Startup Script with Audio Device Config

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_PATH="$PROJECT_ROOT/.venv"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🎤 Starting WhisperLive Client${NC}"

# Check if config has audio device specified
if [ -f "$CONFIG_FILE" ]; then
    # Extract PulseAudio device name from config (the monitor source)
    PULSE_DEVICE="alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor"
    
    # Set PulseAudio default source for this session only
    export PULSE_SOURCE="$PULSE_DEVICE"
    
    echo -e "${GREEN}[INFO]${NC} Audio input: $PULSE_DEVICE"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

cd "$SCRIPT_DIR"

# Run the test client with no VAD (or specify your own script)
echo -e "${GREEN}[INFO]${NC} Starting transcription..."
echo -e "${GREEN}[INFO]${NC} Press Ctrl+C to stop"
echo ""

python /tmp/test_no_vad.py
