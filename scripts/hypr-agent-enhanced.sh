#!/bin/bash
# Hypr-Voice Enhanced Agentic Mode - Smart Context-Aware Voice Input
# Triggered by Right Control + F9 keybinding in Hyprland
#
# This script provides an enhanced, faster agent experience with:
# - Rich context gathering (active app, window title, clipboard)
# - AI-enhanced prompt improvement
# - Context-aware response generation
# - TTS spoken responses
#
# Usage:
#   hypr-agent-enhanced.sh start   - Start enhanced agent input mode (on key press)
#   hypr-agent-enhanced.sh process - Process input with AI enhancement (on key release)
#   hypr-agent-enhanced.sh status  - Check orchestrator status

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ORCHESTRATOR_PORT="${HYPR_AGENT_PORT:-9093}"
WHISPER_PORT="${HYPR_WHISPER_PORT:-9099}"
RECORDING_FLAG="/tmp/hypr-agent-enhanced-recording"
AUDIO_FILE="/tmp/hypr-agent-enhanced-audio.wav"
CONTEXT_FILE="/tmp/hypr-agent-enhanced-context.json"

# Logging
LOG_DIR="${HYPR_VOICE_LOG_DIR:-/tmp/hypr-voice}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/hypr-voice.log"
CONV_FILE="/tmp/hypr-agent-enhanced-conv-id"
AGENT_TIMEOUT="${HYPR_AGENT_TIMEOUT:-300}"

# Audio source from config
WHISPER_CONFIG="$PROJECT_DIR/src/Hypr-Whisper/config/config.yaml"
if [[ -z "${HYPR_AGENT_MIC:-}" ]] && [[ -f "$WHISPER_CONFIG" ]]; then
    AUDIO_SOURCE=$(grep "pulseaudio_source:" "$WHISPER_CONFIG" | sed 's/.*pulseaudio_source: *"\([^"]*\)".*/\1/')
fi
AUDIO_SOURCE="${HYPR_AGENT_MIC:-${AUDIO_SOURCE:-@DEFAULT_SOURCE@}}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# Logging functions
log() {
    local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
    local msg="$ts [    enhanced] [ INFO] $1"
    echo -e "${GREEN}[enhanced]${NC} $1"
    echo "$msg" >> "$LOG_FILE"
}

warn() {
    local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
    local msg="$ts [    enhanced] [ WARN] $1"
    echo -e "${YELLOW}[enhanced]${NC} $1"
    echo "$msg" >> "$LOG_FILE"
}

error() {
    local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
    local msg="$ts [    enhanced] [ERROR] $1"
    echo -e "${RED}[enhanced]${NC} $1" >&2
    echo "$msg" >> "$LOG_FILE"
}

# Audio feedback
SOUNDS_DIR="$SCRIPT_DIR/sounds"

play_sound() {
    local sound="$1"
    local sound_file="$SOUNDS_DIR/${sound}.mp3"

    if [[ -f "$sound_file" ]]; then
        if command -v mpv &>/dev/null; then
            mpv --no-terminal --no-video "$sound_file" &>/dev/null &
        elif command -v ffplay &>/dev/null; then
            ffplay -nodisp -autoexit "$sound_file" &>/dev/null &
        elif command -v paplay &>/dev/null; then
            paplay "$sound_file" &>/dev/null &
        fi
    fi
}

# Gather rich context from current environment
gather_context() {
    log "Gathering context..."
    local context_json=""

    # 1. Get active window info via hyprctl
    local window_info=""
    if command -v hyprctl &>/dev/null; then
        window_info=$(hyprctl activewindow -j 2>/dev/null || echo '{}')
        local window_class=$(echo "$window_info" | jq -r '.class // "unknown"')
        local window_title=$(echo "$window_info" | jq -r '.title // "unknown"')
        local workspace_id=$(echo "$window_info" | jq -r '.workspace.id // -1')
        log "Active window: $window_class - $window_title (workspace: $workspace_id)"
    else
        window_info='{}'
    fi

    # 2. Get clipboard content (first 500 chars for context)
    local clipboard=""
    if command -v wl-paste &>/dev/null; then
        clipboard=$(wl-paste 2>/dev/null | head -c 500 || echo "")
        if [[ -n "$clipboard" ]]; then
            log "Clipboard: ${#clipboard} chars"
        fi
    fi

    # 3. Get timestamp
    local timestamp=$(date -Iseconds)

    # 4. Build context JSON
    context_json=$(jq -nc \
        --argjson window "$window_info" \
        --arg clipboard "$clipboard" \
        --arg timestamp "$timestamp" \
        '{
            window: $window,
            clipboard: $clipboard,
            timestamp: $timestamp
        }')

    # Save context to file for use in processing
    echo "$context_json" > "$CONTEXT_FILE"

    log "Context gathered and saved"
    return 0
}

# Check if orchestrator is running
check_orchestrator() {
    nc -z localhost "$ORCHESTRATOR_PORT" 2>/dev/null
    return $?
}

# Send enhanced query to orchestrator
send_enhanced_query() {
    local transcription="$1"
    local context_json="$2"

    if [[ -z "$transcription" ]]; then
        error "Empty transcription"
        return 1
    fi

    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "ENHANCED AGENT MODE - Context-Aware Processing"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    play_sound "query-in"

    # Extract context details for logging
    local window_class=$(echo "$context_json" | jq -r '.window.class // "unknown"')
    local window_title=$(echo "$context_json" | jq -r '.window.title // "unknown"')

    log "User query: $transcription"
    log "Context: $window_class - $window_title"

    # Get conversation ID if exists
    local conv_id=""
    if [[ -f "$CONV_FILE" ]]; then
        conv_id=$(cat "$CONV_FILE" 2>/dev/null || true)
    fi

    # Build enhanced JSON payload for new /voice/process/enhanced endpoint
    local payload
    if [[ -n "$conv_id" ]]; then
        payload=$(jq -nc \
            --arg text "$transcription" \
            --arg conv "$conv_id" \
            --argjson ctx "$context_json" \
            '{
                text: $text,
                conversation_id: $conv,
                context: $ctx,
                speak_response: true
            }')
        log ">>> Request: conv_id=${conv_id:0:8}... (continuing)"
    else
        payload=$(jq -nc \
            --arg text "$transcription" \
            --argjson ctx "$context_json" \
            '{
                text: $text,
                context: $ctx,
                speak_response: true
            }')
        log ">>> Request: new conversation"
    fi

    log ">>> Calling /voice/process/enhanced (timeout=${AGENT_TIMEOUT}s)..."
    local start_time end_time duration
    start_time=$(date +%s%3N 2>/dev/null || echo "0")

    local response
    response=$(curl -s -X POST "http://localhost:$ORCHESTRATOR_PORT/voice/process/enhanced" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        --max-time "$AGENT_TIMEOUT" 2>&1)

    local curl_exit=$?
    end_time=$(date +%s%3N 2>/dev/null || echo "0")
    duration=$((end_time - start_time))

    if [[ $curl_exit -ne 0 ]]; then
        error ">>> curl failed with exit code $curl_exit after ${duration}ms"
        return 1
    fi

    if [[ -z "$response" ]]; then
        error ">>> Empty response from orchestrator after ${duration}ms"
        return 1
    fi

    # Check for error response
    local error_msg
    error_msg=$(echo "$response" | jq -r '.detail // .error // empty' 2>/dev/null)
    if [[ -n "$error_msg" ]]; then
        error ">>> Orchestrator error: $error_msg"
        return 1
    fi

    # Extract response fields
    local response_text agent_type audio_file tools_used
    response_text=$(echo "$response" | jq -r '.response_text // empty' 2>/dev/null)
    agent_type=$(echo "$response" | jq -r '.agent_type // "unknown"' 2>/dev/null)
    audio_file=$(echo "$response" | jq -r '.audio_file // empty' 2>/dev/null)
    tools_used=$(echo "$response" | jq -r '.tools_used // [] | join(", ")' 2>/dev/null)

    # Log response
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "<<< RESPONSE (${duration}ms total)"
    log "    Agent: $agent_type"
    log "    Response: ${#response_text} chars"
    if [[ -n "$tools_used" ]]; then
        log "    Tools: $tools_used"
    fi
    if [[ -n "$audio_file" ]]; then
        log "    TTS: $audio_file"
    else
        log "    TTS: streamed (no file saved)"
    fi

    # Show truncated response
    if [[ ${#response_text} -gt 200 ]]; then
        log "    Text: ${response_text:0:200}..."
    else
        log "    Text: $response_text"
    fi
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Persist conversation ID
    local new_conv_id
    new_conv_id=$(echo "$response" | jq -r '.conversation_id // empty' 2>/dev/null)
    if [[ -n "$new_conv_id" ]]; then
        echo "$new_conv_id" > "$CONV_FILE"
        log "    Conversation: $new_conv_id (saved for context)"
    fi

    return 0
}

# Start recording with context gathering
start_recording() {
    log "Starting enhanced agent input mode..."

    # Check if already recording
    if [[ -f "$RECORDING_FLAG" ]]; then
        warn "Already recording, stopping first..."
        stop_recording
    fi

    # Gather context BEFORE recording starts
    gather_context

    # Create recording flag
    touch "$RECORDING_FLAG"

    # Play cue sound
    play_sound "query-in"

    # Start recording
    log "Using audio source: $AUDIO_SOURCE"
    arecord -f cd -t wav "$AUDIO_FILE" 2>/dev/null &
    echo $! > /tmp/hypr-agent-enhanced-recorder.pid

    log "Recording started (PID: $(cat /tmp/hypr-agent-enhanced-recorder.pid 2>/dev/null || echo 'unknown'))"
}

# Stop recording
stop_recording() {
    if [[ -f /tmp/hypr-agent-enhanced-recorder.pid ]]; then
        local pid
        pid=$(cat /tmp/hypr-agent-enhanced-recorder.pid)
        kill "$pid" 2>/dev/null || true
        pkill -f "arecord.*hypr-agent-enhanced" 2>/dev/null || true
        rm -f /tmp/hypr-agent-enhanced-recorder.pid
    fi

    rm -f "$RECORDING_FLAG"
    log "Recording stopped"
}

# Transcribe audio using Whisper
transcribe_audio() {
    local audio_path="$1"

    _tlog() {
        local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
        local msg="$ts [     whisper] [ INFO] $1"
        echo "$msg" >> "$LOG_FILE"
        echo -e "${GREEN}[whisper]${NC} $1" >&2
    }
    _terr() {
        local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
        local msg="$ts [     whisper] [ERROR] $1"
        echo "$msg" >> "$LOG_FILE"
        echo -e "${RED}[whisper]${NC} $1" >&2
    }

    if [[ ! -f "$audio_path" ]]; then
        _terr "Audio file not found: $audio_path"
        return 1
    fi

    if ! nc -z localhost "$WHISPER_PORT" 2>/dev/null; then
        _terr "Whisper server not running on port $WHISPER_PORT"
        return 1
    fi

    _tlog "Creating Whisper session..."

    # Create session
    local session_response
    session_response=$(curl -s -X POST "http://localhost:$WHISPER_PORT/sessions" \
        -H "Content-Type: application/json" \
        -d '{"language": "en", "beam_size": 5, "vad_filter": false}' \
        --max-time 10)

    if [[ -z "$session_response" ]]; then
        _terr "Failed to create Whisper session"
        return 1
    fi

    local session_id
    session_id=$(echo "$session_response" | jq -r '.session_id // empty' 2>/dev/null)

    if [[ -z "$session_id" ]]; then
        _terr "No session_id in response"
        return 1
    fi

    _tlog "Session created: $session_id"

    # Upload audio
    _tlog "Uploading audio to Whisper..."
    local upload_response
    upload_response=$(curl -s -X POST "http://localhost:$WHISPER_PORT/sessions/$session_id/transcribe" \
        -F "audio_file=@$audio_path" \
        --max-time 30)

    # Poll for result
    local max_attempts=30
    local attempt=0
    local final_text=""

    while [[ $attempt -lt $max_attempts ]]; do
        sleep 1

        local status_response
        status_response=$(curl -s "http://localhost:$WHISPER_PORT/sessions/$session_id" \
            --max-time 5)

        local status
        status=$(echo "$status_response" | jq -r '.status // empty' 2>/dev/null)
        final_text=$(echo "$status_response" | jq -r '.final_text // empty' 2>/dev/null)

        _tlog "Poll attempt $attempt: status=$status"

        if [[ "$status" == "completed" ]] || [[ -n "$final_text" ]]; then
            break
        fi

        ((attempt++))
    done

    if [[ -z "$final_text" ]]; then
        final_text=$(echo "$status_response" | jq -r '.text // .transcription // empty' 2>/dev/null)
    fi

    echo "$final_text"
}

# Process recorded audio with enhanced AI
process_input() {
    log "Processing enhanced agent input..."

    # Stop recording
    stop_recording

    # Wait for audio file
    sleep 0.3

    # Check audio file
    if [[ ! -f "$AUDIO_FILE" ]] || [[ ! -s "$AUDIO_FILE" ]]; then
        warn "No audio recorded or file is empty"
        return 1
    fi

    # Transcribe
    local transcribed
    transcribed=$(transcribe_audio "$AUDIO_FILE")

    if [[ -z "$transcribed" ]]; then
        error "Transcription failed or empty"
        return 1
    fi

    log "Transcribed: $transcribed"

    # Load context
    local context_json="{}"
    if [[ -f "$CONTEXT_FILE" ]]; then
        context_json=$(cat "$CONTEXT_FILE")
    fi

    # Send to orchestrator with context
    if check_orchestrator; then
        log "Sending to orchestrator with enhanced context..."
        if send_enhanced_query "$transcribed" "$context_json"; then
            log "Enhanced response received and spoken via TTS"
        else
            warn "Failed to get response from orchestrator"
        fi
    else
        warn "Orchestrator not running, copying to clipboard"
        echo "$transcribed" | wl-copy 2>/dev/null || echo "$transcribed"
    fi

    # Cleanup
    rm -f "$AUDIO_FILE"
    rm -f "$CONTEXT_FILE"
}

# Get status
get_status() {
    if check_orchestrator; then
        log "Orchestrator: Running on port $ORCHESTRATOR_PORT"
    else
        warn "Orchestrator: Not running"
    fi

    if nc -z localhost "$WHISPER_PORT" 2>/dev/null; then
        log "Whisper: Running on port $WHISPER_PORT"
    else
        warn "Whisper: Not running"
    fi

    if [[ -f "$RECORDING_FLAG" ]]; then
        log "Recording: Active"
    else
        log "Recording: Inactive"
    fi
}

# Main command handler
case "${1:-}" in
    start)
        start_recording
        ;;
    stop)
        stop_recording
        ;;
    process)
        process_input
        ;;
    status)
        get_status
        ;;
    help|--help|-h)
        echo "Usage: hypr-agent-enhanced.sh <command>"
        echo ""
        echo "Commands:"
        echo "  start    - Start enhanced agent input with context gathering"
        echo "  process  - Stop recording and send to orchestrator with AI enhancement"
        echo "  stop     - Stop recording without processing"
        echo "  status   - Show orchestrator and whisper status"
        echo ""
        echo "Features:"
        echo "  - Rich context gathering (active app, window title, clipboard)"
        echo "  - AI-enhanced prompt processing"
        echo "  - Context-aware responses"
        echo "  - TTS spoken output"
        ;;
    *)
        error "Unknown command: ${1:-}"
        echo "Use 'hypr-agent-enhanced.sh help' for usage"
        exit 1
        ;;
esac
