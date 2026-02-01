#!/bin/bash
# Hypr-Voice Recording Script v2
# Optimized for Wispr Flow Cloud with on-demand keep-alive and direct Opus recording
#
# Key Features:
#   - Direct Opus recording when MODE=FLOW (no conversion overhead)
#   - WAV recording when MODE=LOCAL
#   - On-demand keep-alive: starts on F9 press, stops after transcription
#   - No background keepalive when not recording (avoid detection)
#
# Usage:
#   press   - F9 key pressed: start recording + warmup connection
#   release - F9 key released: stop recording + transcribe

# Note: No 'set -e' to prevent silent failures from killing the script
# set -euo pipefail

# Ensure PATH includes common binary locations (Hyprland may have limited PATH)
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin:$PATH"

# Debug logging (for troubleshooting when run from Hyprland)
DEBUG_LOG="/tmp/hypr-voice-v2-debug.log"
debug_log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$DEBUG_LOG"
}

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
WHISPER_CONFIG_DIR="${HYPR_VOICE_WHISPER_CONFIG_DIR:-$PROJECT_ROOT/config/hypr_voice/whisper}"
WHISPER_STATE_DIR="${HYPR_VOICE_WHISPER_STATE_DIR:-$PROJECT_ROOT/var/hypr_voice/whisper}"

# Load environment variables safely
if [ -f "$PROJECT_ROOT/.env" ]; then
    # Use source with set -a to export all variables
    set -a
    source "$PROJECT_ROOT/.env" 2>/dev/null || true
    set +a
fi

# Check command
COMMAND="${1:-toggle}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# State files
STATE_FILE="/tmp/hypr-voice-recording-v2.state"
TIMESTAMP_FILE="/tmp/hypr-voice-press-v2.timestamp"
WARMUP_PID_FILE="/tmp/hypr-voice-warmup.pid"
TAP_MODE_THRESHOLD=1.0  # seconds
VOLUME_STATE_FILE="/tmp/hypr-voice-volume-v2.state"

# Mic boost settings
BOOST_PERCENTAGE="200%"
NORMAL_PERCENTAGE="100%"

# Determine mode
MODE="${MODE:-FLOW}"
FLOW_MODE=$([ "$MODE" = "FLOW" ] && echo "1" || echo "0")
debug_log "MODE=$MODE, FLOW_MODE=$FLOW_MODE"

# Load audio device name from config
AUDIO_SOURCE=$(grep -A3 "^pulseaudio:" "$WHISPER_CONFIG_DIR/audio-profile.yaml" 2>/dev/null | grep "default_source:" | awk '{print $2}')
AUDIO_SOURCE=${AUDIO_SOURCE:-"@DEFAULT_SOURCE@"}

# Load notification settings
NOTIFY_ENABLED=$(grep -A1 "^notifications:" "$WHISPER_CONFIG_DIR/notifications.yaml" 2>/dev/null | grep "enabled:" | awk '{print $2}')
NOTIFY_ENABLED=${NOTIFY_ENABLED:-false}

# Load recording save settings
SAVE_RECORDINGS=$(grep "save_recordings:" "$WHISPER_CONFIG_DIR/audio-profile.yaml" 2>/dev/null | awk '{print $2}')
SAVE_RECORDINGS=${SAVE_RECORDINGS:-false}

# Determine audio file location and format
if [ "$SAVE_RECORDINGS" = "true" ]; then
    RECORDINGS_DIR="$WHISPER_STATE_DIR/recordings"
    mkdir -p "$RECORDINGS_DIR"
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    if [ "$FLOW_MODE" = "1" ]; then
        AUDIO_FILE="$RECORDINGS_DIR/recording_$TIMESTAMP.opus"
        AUDIO_FORMAT="opus"
    else
        AUDIO_FILE="$RECORDINGS_DIR/recording_$TIMESTAMP.wav"
        AUDIO_FORMAT="wav"
    fi
else
    # Use temp file if not saving
    if [ "$FLOW_MODE" = "1" ]; then
        AUDIO_FILE="/tmp/hypr-voice-recording-$$.opus"
        AUDIO_FORMAT="opus"
    else
        AUDIO_FILE="/tmp/hypr-voice-recording-$$.wav"
        AUDIO_FORMAT="wav"
    fi
fi

# ============================================================================
# KEEP-ALIVE FUNCTIONS (On-demand only during recording)
# ============================================================================

start_warmup_keepalive() {
    debug_log "start_warmup_keepalive called, FLOW_MODE=$FLOW_MODE"
    # Start a background process that pings the Wispr Flow warmup endpoint
    # This keeps the connection warm ONLY during recording
    if [ "$FLOW_MODE" != "1" ]; then
        debug_log "Skipping warmup - not in FLOW mode"
        return 0  # Only for FLOW mode
    fi
    
    # Check if already warming up
    if [ -f "$WARMUP_PID_FILE" ]; then
        local pid=$(cat "$WARMUP_PID_FILE" 2>/dev/null)
        if kill -0 "$pid" 2>/dev/null; then
            debug_log "Warmup already running (PID: $pid)"
            return 0  # Already running
        fi
    fi
    
    debug_log "Starting warmup keepalive..."
    # Start background warmup process
    (
        JWT_TOKEN="${WISPR_FLOW_JWT_TOKEN:-}"
        WARMUP_URL="https://api.wisprflow.ai/warmup"
        INTERVAL=${WISPR_FLOW_KEEPALIVE_INTERVAL:-4}
        
        while true; do
            # Lightweight warmup ping
            curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: $JWT_TOKEN" \
                -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
                "$WARMUP_URL" > /dev/null 2>&1 || true
            
            sleep "$INTERVAL"
        done
    ) &
    
    local warmup_pid=$!
    echo "$warmup_pid" > "$WARMUP_PID_FILE"
    
    # Initial warmup ping (blocking, quick)
    curl -s -o /dev/null \
        -H "Authorization: ${WISPR_FLOW_JWT_TOKEN:-}" \
        -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
        "https://api.wisprflow.ai/warmup" > /dev/null 2>&1 || true
    
    echo "🔥 Warmup started (PID: $warmup_pid)"
}

stop_warmup_keepalive() {
    # Stop the background warmup process
    if [ -f "$WARMUP_PID_FILE" ]; then
        local pid=$(cat "$WARMUP_PID_FILE" 2>/dev/null)
        if [ -n "$pid" ]; then
            kill "$pid" 2>/dev/null || true
            wait "$pid" 2>/dev/null || true
        fi
        rm -f "$WARMUP_PID_FILE"
        echo "🔥 Warmup stopped"
    fi
}

# ============================================================================
# MIC BOOST FUNCTIONS
# ============================================================================

boost_mic_gain() {
    CURRENT_VOLUME=$(pactl get-source-volume "$AUDIO_SOURCE" 2>/dev/null | grep -oP '\d+%' | head -1 || echo "100%")
    echo "$CURRENT_VOLUME" > "$VOLUME_STATE_FILE"
    pactl set-source-volume "$AUDIO_SOURCE" "$BOOST_PERCENTAGE" 2>/dev/null || true
}

restore_mic_gain() {
    if [ -f "$VOLUME_STATE_FILE" ]; then
        SAVED_VOLUME=$(cat "$VOLUME_STATE_FILE")
        pactl set-source-volume "$AUDIO_SOURCE" "$SAVED_VOLUME" 2>/dev/null || true
        rm -f "$VOLUME_STATE_FILE"
    else
        pactl set-source-volume "$AUDIO_SOURCE" "$NORMAL_PERCENTAGE" 2>/dev/null || true
    fi
}

# ============================================================================
# RECORDING FUNCTIONS
# ============================================================================

start_recording() {
    debug_log "start_recording called"
    # Check if already recording
    if [ -f "$STATE_FILE" ]; then
        debug_log "Already recording (state file exists)"
        return 1
    fi

    # Save audio file path to state file
    echo "$AUDIO_FILE" > "$STATE_FILE"
    echo "$AUDIO_FORMAT" > "${STATE_FILE}.format"
    debug_log "Recording to: $AUDIO_FILE (format: $AUDIO_FORMAT)"

    # Boost mic gain
    boost_mic_gain

    # Visual feedback
    if [ "$FLOW_MODE" = "1" ]; then
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "🔴 Recording (Cloud)" "Tap F9 again to stop" -t 2000 2>/dev/null || true
    else
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "🔴 Recording (Local)" "Tap F9 again to stop" -t 2000 2>/dev/null || true
    fi

    # Start connection warmup (on-demand, only during recording)
    if [ "$FLOW_MODE" = "1" ]; then
        start_warmup_keepalive
    fi

    # Start recording based on mode
    if [ "$FLOW_MODE" = "1" ]; then
        # FLOW mode: Record directly to Opus using ffmpeg
        # Benefits: ~10x smaller files, no post-processing needed
        ffmpeg -f pulse -i "$AUDIO_SOURCE" \
            -c:a libopus \
            -b:a 16k \
            -ar 16000 \
            -ac 1 \
            -application voip \
            -frame_duration 20 \
            "$AUDIO_FILE" \
            -y -loglevel error 2>/dev/null &
        echo $! > "${STATE_FILE}.pid"
    else
        # LOCAL mode: Record to WAV for local Whisper processing
        arecord -f S16_LE -c 1 -r 16000 -t wav "$AUDIO_FILE" 2>/dev/null &
        echo $! > "${STATE_FILE}.pid"
    fi
    
    return 0
}

stop_recording() {
    # Check if recording
    if [ ! -f "$STATE_FILE" ]; then
        return 1
    fi

    # Get the audio file path and format from state
    AUDIO_FILE=$(cat "$STATE_FILE")
    AUDIO_FORMAT=$(cat "${STATE_FILE}.format" 2>/dev/null || echo "wav")

    # Stop recording
    if [ -f "${STATE_FILE}.pid" ]; then
        local rec_pid=$(cat "${STATE_FILE}.pid")
        kill "$rec_pid" 2>/dev/null || true
        wait "$rec_pid" 2>/dev/null || true
        rm -f "${STATE_FILE}.pid"
    fi

    # Restore mic gain
    restore_mic_gain

    # Stop warmup keepalive (connection will be used for transcription)
    stop_warmup_keepalive

    # Clean up state files
    rm -f "$STATE_FILE"
    rm -f "${STATE_FILE}.format"
    rm -f "$TIMESTAMP_FILE"

    # Visual feedback
    [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⏹️ Processing..." "Transcribing audio" -t 2000 2>/dev/null || true

    # Check if audio file exists and has content
    if [ ! -f "$AUDIO_FILE" ]; then
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⚠️ Recording Failed" "No audio file created" -t 3000 2>/dev/null || true
        return 1
    fi
    
    local file_size=$(stat -f%z "$AUDIO_FILE" 2>/dev/null || stat -c%s "$AUDIO_FILE" 2>/dev/null || echo "0")
    if [ "$file_size" -lt 1000 ]; then
        [ "$NOTIFY_ENABLED" = "true" ] && notify-send "⚠️ Recording Failed" "Audio file too small (${file_size} bytes)" -t 3000 2>/dev/null || true
        rm -f "$AUDIO_FILE"
        return 1
    fi

    # Transcribe and type
    cd "$PROJECT_ROOT"
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"
    
    TRANSCRIPTION=$("$VENV_PATH/bin/python" -c "
import sys
import time
import subprocess
from hypr_voice.whisper.client.hybrid_client import HybridWhisperClient
from hypr_voice.whisper.backends.input_backends import detect_input_backend
from hypr_voice.whisper.backends.window_backends import detect_backend

client = HybridWhisperClient('http://localhost:9099')
client.create_session()

# Pass the audio format info
try:
    client.transcribe_file('$AUDIO_FILE')
    result = client.get_final_transcription(wait=True, interval=0.2, inactivity_timeout=30)
    
    final_result = result if result else {'text': ''}
    
    if final_result and 'text' in final_result:
        text = final_result['text'].strip()
        if text:
            window_backend = detect_backend()
            backend = detect_input_backend(window_backend=window_backend.name)
            backend.type_text_instant(text)
            print(f'{text}')
        else:
            print('__NO_SPEECH__')
    else:
        print('__ERROR__')
except Exception as e:
    print(f'__ERROR__: {e}')
" 2>&1)

    # Show result notification
    if [ "$NOTIFY_ENABLED" = "true" ]; then
        if [[ "$TRANSCRIPTION" == "__NO_SPEECH__" ]]; then
            notify-send "🔇 No Speech" "No speech detected in recording" -t 3000 2>/dev/null || true
        elif [[ "$TRANSCRIPTION" == "__ERROR__"* ]]; then
            notify-send "❌ Error" "Transcription failed" -t 3000 2>/dev/null || true
        elif [ -n "$TRANSCRIPTION" ]; then
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

# ============================================================================
# MAIN COMMAND HANDLER
# ============================================================================

case "$COMMAND" in
    press)
        debug_log "=== PRESS command received ==="
        # F9 pressed
        if [ -f "$STATE_FILE" ]; then
            # Already recording - this must be a second tap to stop
            debug_log "State file exists, stopping recording (toggle mode)"
            rm -f "$TIMESTAMP_FILE"
            stop_recording
        else
            # Not recording - start recording and save timestamp
            debug_log "Starting new recording"
            date +%s.%N > "$TIMESTAMP_FILE"
            start_recording
        fi
        ;;
    
    release)
        debug_log "=== RELEASE command received ==="
        # F9 released: Check if this was a tap or hold
        if [ ! -f "$TIMESTAMP_FILE" ]; then
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
            exit 0
        fi

        # If held shorter than threshold, this is a TAP - do NOT stop
        # If held longer than threshold, this is a HOLD - stop recording
        if [ "$(echo "$DURATION < $TAP_MODE_THRESHOLD" | bc 2>/dev/null || echo "1")" -eq 1 ]; then
            exit 0
        else
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
        echo "  press   - F9 key pressed (start recording + warmup)"
        echo "  release - F9 key released (stop if held > 1s)"
        echo "  start   - Manually start recording"
        echo "  stop    - Manually stop recording and transcribe"
        echo "  toggle  - Toggle recording state"
        echo ""
        echo "Mode: $MODE (FLOW=$FLOW_MODE)"
        echo "Audio format: $AUDIO_FORMAT"
        exit 1
        ;;
esac
