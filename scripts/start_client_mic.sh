#!/bin/bash
# WhisperLive Client Startup Script - Reads audio device from audio-profile.yaml

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
WHISPER_CONFIG_DIR="${HYPR_VOICE_WHISPER_CONFIG_DIR:-$PROJECT_ROOT/config/hypr_voice/whisper}"
AUDIO_PROFILE="$WHISPER_CONFIG_DIR/audio-profile.yaml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎤 Starting WhisperLive Client for Hypr-Voice${NC}"
echo -e "${GREEN}[INFO]${NC} Virtual Environment: $VENV_PATH"

# Check if venv exists
if [ ! -d "$VENV_PATH" ] || [ ! -f "$VENV_PATH/bin/python" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Suppress ALSA warnings by using custom config
if [ -f "$WHISPER_CONFIG_DIR/.asoundrc" ]; then
    export ALSA_CONFIG_PATH="$WHISPER_CONFIG_DIR/.asoundrc"
fi
export ALSA_CARD=0
export ALSA_PCM_CARD=0

# Extract PulseAudio source from audio profile using venv's python
if [ -f "$AUDIO_PROFILE" ]; then
    PULSE_DEVICE=$("$VENV_PATH/bin/python" -c "
import yaml
with open('$AUDIO_PROFILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config['pulseaudio']['default_source'])
" 2>/dev/null)
    
    DEVICE_NAME=$("$VENV_PATH/bin/python" -c "
import yaml
with open('$AUDIO_PROFILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config['pulseaudio'].get('device_name', 'Unknown'))
" 2>/dev/null)
    
    if [ -n "$PULSE_DEVICE" ]; then
        # Set as system default source
        pactl set-default-source "$PULSE_DEVICE" 2>/dev/null || true
        export PULSE_SOURCE="$PULSE_DEVICE"
        echo -e "${GREEN}[INFO]${NC} Audio device: $DEVICE_NAME"
        echo -e "${GREEN}[INFO]${NC} Audio source: $PULSE_DEVICE"
    else
        echo -e "${YELLOW}[WARN]${NC} No audio profile found, using system default"
    fi
else
    echo -e "${YELLOW}[WARN]${NC} Audio profile not found at $AUDIO_PROFILE"
fi

# Hybrid client has moved - run as module from project root
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

echo -e "${GREEN}[INFO]${NC} Server: http://localhost:9099"
echo -e "${GREEN}[INFO]${NC} Using Hybrid Client (WebSocket mode)"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo ""

# Use the hybrid client with proper WebSocket support - run as module
"$VENV_PATH/bin/python" -m hypr_voice.whisper.client.hybrid_client --stream --server http://localhost:9099
