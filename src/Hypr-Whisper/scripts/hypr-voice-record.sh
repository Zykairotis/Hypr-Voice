#!/bin/bash
# Simple push-to-talk recording script (non-daemon mode)

set -e

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Check command
COMMAND="${1:-toggle}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# Recording state file
STATE_FILE="/tmp/hypr-voice-recording.state"

# Load notification settings
NOTIFY_ENABLED=$(grep -A1 "^notifications:" "$WHISPER_ROOT/config/notifications.yaml" | grep "enabled:" | awk '{print $2}')
NOTIFY_ENABLED=${NOTIFY_ENABLED:-false}

# Load recording save settings
SAVE_RECORDINGS=$(grep "save_recordings:" "$WHISPER_ROOT/config/audio-profile.yaml" | awk '{print $2}')
SAVE_RECORDINGS=${SAVE_RECORDINGS:-false}

# Determine audio file location
if [ "$SAVE_RECORDINGS" = "true" ]; then
    RECORDINGS_DIR="$WHISPER_ROOT/recordings"
    mkdir -p "$RECORDINGS_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    AUDIO_FILE="$RECORDINGS_DIR/recording_$TIMESTAMP.wav"
else
    # Use temp file if not saving
    AUDIO_FILE="/tmp/hypr-voice-recording-$$.wav"
fi

case "$COMMAND" in
    start)
        # Check if already recording
        if [ -f "$STATE_FILE" ]; then
            [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⚠️ Already Recording" "Release F9 to stop first" -t 2000 2>/dev/null || true
            exit 0
        fi
        
        # Save audio file path to state file
        echo "$AUDIO_FILE" > "$STATE_FILE"
        
        # Visual feedback
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "🔴 Recording..." "Release F9 to stop and transcribe" -t 2000 2>/dev/null || true
        
        # Start recording with arecord in background
        arecord -f cd -t wav "$AUDIO_FILE" 2>/dev/null &
        echo $! > "${STATE_FILE}.pid"
        ;;
    
    stop)
        # Check if recording
        if [ ! -f "$STATE_FILE" ]; then
            [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⚠️ Not Recording" "F9 was not pressed to start" -t 2000 2>/dev/null || true
            exit 0
        fi
        
        # Get the audio file path from state
        AUDIO_FILE=$(cat "$STATE_FILE")
        
        # Stop recording
        if [ -f "${STATE_FILE}.pid" ]; then
            kill $(cat "${STATE_FILE}.pid") 2>/dev/null || true
            rm -f "${STATE_FILE}.pid"
        fi
        
        # Clean up state
        rm -f "$STATE_FILE"
        
        # Visual feedback
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⏹️ Processing..." "Transcribing audio" -t 2000 2>/dev/null || true
        
        # Check if audio file exists and has content
        if [ ! -f "$AUDIO_FILE" ] || [ $(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE") -lt 1000 ]; then
            [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⚠️ Recording Failed" "No audio captured" -t 3000 2>/dev/null || true
            rm -f "$AUDIO_FILE"
            exit 1
        fi
        
        # Transcribe and type
        cd "$WHISPER_ROOT"
        TRANSCRIPTION=$("$VENV_PATH/bin/python" -c "
import sys
import time
sys.path.insert(0, '.')
from hybrid_client import HybridWhisperClient
import subprocess

client = HybridWhisperClient('http://localhost:9099')

# Use same approach as hybrid_client.py --file but with fast polling
client.create_session()
client.transcribe_file('$AUDIO_FILE')
result = client.get_final_transcription(wait=True, interval=0.2, inactivity_timeout=30)

final_result = result if result else {'text': ''}

if final_result and 'text' in final_result:
    text = final_result['text'].strip()
    if text:
        # Type the text instantly using ydotool with 1ms delays (fastest)
        subprocess.run(['ydotool', 'type', '-d', '1', '-H', '1', text], capture_output=True)
        print(f'{text}')
    else:
        print('__NO_SPEECH__')
else:
    print('__ERROR__')
" 2>&1)

        # Show result notification
        if [ "$NOTIFY_ENABLED" = "true" ]; then
            if [[ "$TRANSCRIPTION" == "__NO_SPEECH__" ]]; then
                notify-send "🔇 No Speech" "No speech detected in recording" -t 3000 2>/dev/null || true
            elif [[ "$TRANSCRIPTION" == "__ERROR__" ]]; then
                notify-send "❌ Error" "Transcription failed" -t 3000 2>/dev/null || true
            elif [ -n "$TRANSCRIPTION" ]; then
                # Show what was typed (truncate if too long)
                TEXT_PREVIEW="${TRANSCRIPTION:0:50}"
                [ "${#TRANSCRIPTION}" -gt 50 ] && TEXT_PREVIEW="${TEXT_PREVIEW}..."
                notify-send "✅ Typed" "$TEXT_PREVIEW" -t 3000 2>/dev/null || true
            fi
        fi
        
        # Clean up or keep recording file based on config
        if [ "$SAVE_RECORDINGS" = "true" ]; then
            echo "Recording saved: $AUDIO_FILE"
        else
            rm -f "$AUDIO_FILE"
        fi
        ;;
    
    toggle)
        if [ -f "$STATE_FILE" ]; then
            "$0" stop
        else
            "$0" start
        fi
        ;;
    
    *)
        echo "Usage: $0 {start|stop|toggle}"
        exit 1
        ;;
esac
