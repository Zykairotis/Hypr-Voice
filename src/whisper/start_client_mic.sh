#!/bin/bash
# WhisperLive Client Startup Script - Reads audio device from audio-profile.yaml

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_PATH="$PROJECT_ROOT/.venv"
AUDIO_PROFILE="$SCRIPT_DIR/audio-profile.yaml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎤 Starting WhisperLive Client for Hypr-Voice${NC}"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Suppress ALSA warnings by using custom config
if [ -f "$SCRIPT_DIR/.asoundrc" ]; then
    export ALSA_CONFIG_PATH="$SCRIPT_DIR/.asoundrc"
fi
export ALSA_CARD=0
export ALSA_PCM_CARD=0

# Extract PulseAudio source from audio profile
if [ -f "$AUDIO_PROFILE" ]; then
    PULSE_DEVICE=$(python3 -c "
import yaml
with open('$AUDIO_PROFILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config['pulseaudio']['default_source'])
" 2>/dev/null)
    
    DEVICE_NAME=$(python3 -c "
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

cd "$SCRIPT_DIR"

echo -e "${GREEN}[INFO]${NC} Server: localhost:9090"
echo -e "${GREEN}[INFO]${NC} Model: openai/whisper-large-v3-turbo (INT8)"
echo -e "${GREEN}[INFO]${NC} VAD: Disabled (will transcribe all audio)"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo ""

# Start the client
python3 << 'PYTHON_EOF'
import sys
sys.path.insert(0, '/home/mewtwo/Zykairotis/Hypr-Voice/src/live-whisper')

from whisper_live.client import TranscriptionClient

print("🎤 Listening for audio...")
print("=" * 60)

client = TranscriptionClient(
    host="localhost",
    port=9090,
    lang="en",
    translate=False,
    model="openai/whisper-large-v3-turbo",
    use_vad=False,  # Disable VAD - transcribe everything
    log_transcription=True,
)

try:
    client()
except KeyboardInterrupt:
    print("\n\n✅ Transcription stopped")
PYTHON_EOF
