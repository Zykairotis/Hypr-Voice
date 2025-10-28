#!/bin/bash
# WhisperLive Client Startup Script - Reads audio device from config.yaml

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
VENV_PATH="$PROJECT_ROOT/.venv"
CONFIG_FILE="$SCRIPT_DIR/config.yaml"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🎤 Starting WhisperLive Client for Hypr-Voice${NC}"

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Extract PulseAudio source from YAML config
if [ -f "$CONFIG_FILE" ]; then
    PULSE_DEVICE=$(python3 -c "
import yaml
with open('$CONFIG_FILE', 'r') as f:
    config = yaml.safe_load(f)
    print(config['audio'].get('pulseaudio_source', ''))
" 2>/dev/null)
    
    if [ -n "$PULSE_DEVICE" ]; then
        export PULSE_SOURCE="$PULSE_DEVICE"
        echo -e "${GREEN}[INFO]${NC} Audio source: $PULSE_DEVICE"
    else
        echo -e "${YELLOW}[WARN]${NC} No pulseaudio_source in config, using system default"
    fi
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
