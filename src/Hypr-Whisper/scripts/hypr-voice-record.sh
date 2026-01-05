#!/bin/bash
# Simple push-to-talk recording script with tap-to-toggle support
#
# Modes:
#   - Tap F9 (< 1s): Toggle recording (press to start, press again to stop)
#   - Hold F9 (> 1s): Push-to-talk (hold to record, release to stop)
#
# Commands:
#   press   - Called when F9 is pressed
#   release - Called when F9 is released
#   start   - Manually start recording
#   stop    - Manually stop recording and transcribe
#   toggle  - Toggle recording state

set -e

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Check command
COMMAND="${1:-toggle}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

# State files
STATE_FILE="/tmp/hypr-voice-recording.state"
TIMESTAMP_FILE="/tmp/hypr-voice-press.timestamp"
TAP_MODE_THRESHOLD=1.0  # seconds - if held shorter, treat as tap

# Load notification settings
NOTIFY_ENABLED=$(grep -A1 "^notifications:" "$WHISPER_ROOT/config/notifications.yaml" 2>/dev/null | grep "enabled:" | awk '{print $2}')
NOTIFY_ENABLED=${NOTIFY_ENABLED:-false}

# Load recording save settings
SAVE_RECORDINGS=$(grep "save_recordings:" "$WHISPER_ROOT/config/audio-profile.yaml" 2>/dev/null | awk '{print $2}')
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

start_recording() {
    # Check if already recording
    if [ -f "$STATE_FILE" ]; then
        return 1
    fi

    # Save audio file path to state file
    echo "$AUDIO_FILE" > "$STATE_FILE"

    # Visual feedback
    [ "$NOTIFY_ENABLED" = "true" ] && notify-send "🔴 Recording..." "Tap F9 again to stop" -t 2000 2>/dev/null || true

    # Start recording with arecord in background
    arecord -f cd -t wav "$AUDIO_FILE" 2>/dev/null &
    echo $! > "${STATE_FILE}.pid"
    return 0
}

stop_recording() {
    # Check if recording
    if [ ! -f "$STATE_FILE" ]; then
        return 1
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
    rm -f "$TIMESTAMP_FILE"

    # Visual feedback
    [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⏹️ Processing..." "Transcribing audio" -t 2000 2>/dev/null || true

    # Check if audio file exists and has content
    if [ ! -f "$AUDIO_FILE" ] || [ $(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE") -lt 1000 ]; then
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⚠️ Recording Failed" "No audio captured" -t 3000 2>/dev/null || true
        rm -f "$AUDIO_FILE"
        return 1
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
    return 0
}

case "$COMMAND" in
    press)
        # F9 pressed
        if [ -f "$STATE_FILE" ]; then
            # Already recording - this must be a second tap to stop
            # Remove timestamp if exists
            rm -f "$TIMESTAMP_FILE"
            stop_recording
        else
            # Not recording - start recording and save timestamp
            date +%s.%N > "$TIMESTAMP_FILE"
            start_recording
        fi
        ;;

    release)
        # F9 released: Check if this was a tap or hold
        if [ ! -f "$TIMESTAMP_FILE" ]; then
            # No timestamp file - either already handled or wasn't set
            exit 0
        fi

        # Calculate duration
        PRESS_TIME=$(cat "$TIMESTAMP_FILE")
        CURRENT_TIME=$(date +%s.%N)
        DURATION=$(echo "$CURRENT_TIME - $PRESS_TIME" | bc 2>/dev/null || echo "0")

        # Remove timestamp file
        rm -f "$TIMESTAMP_FILE"

        # Check if was recording
        if [ ! -f "$STATE_FILE" ]; then
            # Wasn't recording, nothing to stop
            exit 0
        fi

        # If held shorter than threshold, this is a TAP - do NOT stop
        # If held longer than threshold, this is a HOLD - stop recording
        # Use shell string comparison for floating point
        if [ "$(echo "$DURATION < $TAP_MODE_THRESHOLD" | bc 2>/dev/null || echo "1")" -eq 1 ]; then
            # Tap mode (< 1s): Do NOT stop - let recording continue for second tap
            # Just remove the timestamp and exit
            exit 0
        else
            # Hold mode (> 1s): Stop recording (push-to-talk behavior)
            stop_recording
        fi
        ;;

    start)
        start_recording
        ;;

    stop)
        stop_recording
        ;;

    toggle)
        if [ -f "$STATE_FILE" ]; then
            stop_recording
        else
            start_recording
        fi
        ;;

    *)
        echo "Usage: $0 {press|release|start|stop|toggle}"
        echo ""
        echo "Commands:"
        echo "  press   - F9 key pressed"
        echo "  release - F9 key released (checks duration: tap does nothing, hold stops)"
        echo "  start   - Manually start recording"
        echo "  stop    - Manually stop recording and transcribe"
        echo "  toggle  - Toggle recording state"
        exit 1
        ;;
esac
