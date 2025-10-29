#!/bin/bash
# Quick one-shot recording and transcription

set -e

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Load notification settings
NOTIFY_ENABLED=$(grep -A1 "^notifications:" "$WHISPER_ROOT/config/notifications.yaml" | grep "enabled:" | awk '{print $2}')
NOTIFY_ENABLED=${NOTIFY_ENABLED:-false}

# Load recording save settings
SAVE_RECORDINGS=$(grep "save_recordings:" "$WHISPER_ROOT/config/audio-profile.yaml" | awk '{print $2}')
SAVE_RECORDINGS=${SAVE_RECORDINGS:-false}

# Configuration
RECORD_DURATION="${1:-5}"  # Default 5 seconds

# Determine audio file location
if [ "$SAVE_RECORDINGS" = "true" ]; then
    RECORDINGS_DIR="$WHISPER_ROOT/recordings"
    mkdir -p "$RECORDINGS_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    AUDIO_FILE="$RECORDINGS_DIR/quick_$TIMESTAMP.wav"
else
    # Use temp file if not saving
    AUDIO_FILE="/tmp/hypr-voice-quick-$(date +%s).wav"
fi

echo -e "${BLUE}🎤 Recording for ${RECORD_DURATION} seconds...${NC}"

# Visual feedback
if [ "$NOTIFY_ENABLED" = "true" ]; then
    notify-send "🔴 Recording..." "${RECORD_DURATION} seconds" -t 2000 2>/dev/null || true
fi

# Record audio
timeout "${RECORD_DURATION}" arecord -f cd -t wav "$AUDIO_FILE" 2>/dev/null || true

echo -e "${BLUE}⏹️ Processing transcription...${NC}"
[ "$NOTIFY_ENABLED" = "true" ] && notify-send "⏹️ Processing..." "Transcribing audio" -t 2000 2>/dev/null || true

# Transcribe and type
cd "$WHISPER_ROOT"
"$VENV_PATH/bin/python" -c "
import sys
import os
import time
sys.path.insert(0, '.')
from hybrid_client import HybridWhisperClient
import subprocess

audio_file = '$AUDIO_FILE'
notify_enabled = '$NOTIFY_ENABLED' == 'true'

# Check if file has content
if os.path.getsize(audio_file) < 1000:
    print('Audio file too small, no recording')
    sys.exit(1)

client = HybridWhisperClient('http://localhost:9090')

# Use same approach as hybrid_client.py --file but with fast polling
client.create_session()
client.transcribe_file(audio_file)
result = client.get_final_transcription(wait=True, interval=0.2, inactivity_timeout=30)

if not result:
    print('Transcription failed')
    if notify_enabled:
        subprocess.run(['notify-send', '❌ Error', 'Transcription failed'], capture_output=True)
    sys.exit(1)

if result and 'text' in result:
    text = result['text'].strip()
    if text:
        print(f'✅ Transcribed: {text}')
        # Type the text instantly with 1ms delay (fastest possible)
        subprocess.run(['wtype', '-d', '1', text], capture_output=True)
        # Notify
        if notify_enabled:
            subprocess.run(['notify-send', '✅ Typed', text[:100]], capture_output=True)
    else:
        print('No speech detected')
        if notify_enabled:
            subprocess.run(['notify-send', '⚠️ No Speech', 'No speech detected in recording'], capture_output=True)
else:
    print('Transcription failed')
    if notify_enabled:
        subprocess.run(['notify-send', '❌ Error', 'Transcription failed'], capture_output=True)
"

# Clean up or keep recording file based on config
if [ "$SAVE_RECORDINGS" = "true" ]; then
    echo "Recording saved: $AUDIO_FILE"
else
    rm -f "$AUDIO_FILE"
fi

echo -e "${GREEN}✓ Done${NC}"
