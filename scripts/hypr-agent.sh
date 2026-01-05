#!/bin/bash
# Hypr-Voice Agent Mode Handler
# Triggered by F10 keybinding in Hyprland
# 
# Usage:
#   hypr-agent.sh start   - Start agent input mode (on F10 press)
#   hypr-agent.sh process - Process input and send to orchestrator (on F10 release)
#   hypr-agent.sh status  - Check orchestrator status
#   hypr-agent.sh stop    - Stop recording/processing

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ORCHESTRATOR_PORT="${HYPR_AGENT_PORT:-9093}"
WHISPER_PORT="${HYPR_WHISPER_PORT:-9099}"
RECORDING_FLAG="/tmp/hypr-agent-recording"
AUDIO_FILE="/tmp/hypr-agent-audio.wav"

# LogGurl: Centralized logging - all logs go to same location
LOG_DIR="${HYPR_VOICE_LOG_DIR:-/tmp/hypr-voice}"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/hypr-voice.log"
# Persist conversation id to maintain context across prompts (e.g., permission follow-ups)
CONV_FILE="/tmp/hypr-agent-conv-id"
# Allow long LLM + TTS streams; override with HYPR_AGENT_TIMEOUT (seconds)
# Increase default to 300s to avoid premature timeout on long multi-agent replies
AGENT_TIMEOUT="${HYPR_AGENT_TIMEOUT:-300}"

# Audio source - use env var or read from config.yaml
WHISPER_CONFIG="$PROJECT_DIR/src/Hypr-Whisper/config/config.yaml"
if [[ -z "${HYPR_AGENT_MIC:-}" ]] && [[ -f "$WHISPER_CONFIG" ]]; then
    # Extract pulseaudio_source value between quotes
    AUDIO_SOURCE=$(grep "pulseaudio_source:" "$WHISPER_CONFIG" | sed 's/.*pulseaudio_source: *"\([^"]*\)".*/\1/')
fi
AUDIO_SOURCE="${HYPR_AGENT_MIC:-${AUDIO_SOURCE:-@DEFAULT_SOURCE@}}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# LogGurl-compatible logging with timestamps
# Format: HH:MM:SS.mmm [       agent] [LEVEL] message
log() {
    local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
    local msg="$ts [       agent] [ INFO] $1"
    echo -e "${GREEN}[agent]${NC} $1"
    echo "$msg" >> "$LOG_FILE"
}

warn() {
    local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
    local msg="$ts [       agent] [ WARN] $1"
    echo -e "${YELLOW}[agent]${NC} $1"
    echo "$msg" >> "$LOG_FILE"
}

error() {
    local ts=$(date '+%H:%M:%S.%3N' 2>/dev/null || date '+%H:%M:%S.000')
    local msg="$ts [       agent] [ERROR] $1"
    echo -e "${RED}[agent]${NC} $1" >&2
    echo "$msg" >> "$LOG_FILE"
}

# Audio feedback sounds
SOUNDS_DIR="$SCRIPT_DIR/sounds"

play_sound() {
    local sound="$1"  # query-in, success, error
    local sound_file="$SOUNDS_DIR/${sound}.mp3"
    
    if [[ -f "$sound_file" ]]; then
        # Try mpv first (best for mp3), then ffplay, then paplay
        if command -v mpv &>/dev/null; then
            mpv --no-terminal --no-video "$sound_file" &>/dev/null &
        elif command -v ffplay &>/dev/null; then
            ffplay -nodisp -autoexit "$sound_file" &>/dev/null &
        elif command -v paplay &>/dev/null; then
            paplay "$sound_file" &>/dev/null &
        fi
    fi
}

# Check if orchestrator is running
check_orchestrator() {
    nc -z localhost "$ORCHESTRATOR_PORT" 2>/dev/null
    return $?
}

# Send message to orchestrator via REST API
send_to_orchestrator() {
    local action="$1"
    local query="$2"
    
    if [[ "$action" == "query" && -n "$query" ]]; then
        # Play query input sound
        play_sound "query-in"
        
        # Use voice/process endpoint for full pipeline with TTS response
        local response

        # Reuse last conversation id to keep context if available
        local conv_id=""
        if [[ -f "$CONV_FILE" ]]; then
            conv_id=$(cat "$CONV_FILE" 2>/dev/null || true)
        fi

        # Build JSON payload safely
        local payload
        if [[ -n "$conv_id" ]]; then
            payload=$(jq -nc --arg text "$query" --arg conv "$conv_id" '{text:$text, speak_response:true, conversation_id:$conv}')
            log ">>> Request: conv_id=${conv_id:0:8}... (continuing)"
        else
            payload=$(jq -nc --arg text "$query" '{text:$text, speak_response:true}')
            log ">>> Request: new conversation"
        fi

        log ">>> Calling /voice/process (timeout=${AGENT_TIMEOUT}s)..."
        local start_time end_time duration
        start_time=$(date +%s%3N 2>/dev/null || echo "0")
        
        response=$(curl -s -X POST "http://localhost:$ORCHESTRATOR_PORT/voice/process" \
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
        
        # Extract all response fields
        local response_text agent_type audio_file input_text routing_info tts_success
        response_text=$(echo "$response" | jq -r '.response_text // empty' 2>/dev/null)
        agent_type=$(echo "$response" | jq -r '.agent_type // "unknown"' 2>/dev/null)
        audio_file=$(echo "$response" | jq -r '.audio_file // empty' 2>/dev/null)
        input_text=$(echo "$response" | jq -r '.input_text // empty' 2>/dev/null)
        
        # Log detailed response breakdown
        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        log "<<< RESPONSE (${duration}ms total)"
        log "    Agent: $agent_type"
        log "    Response: ${#response_text} chars"
        if [[ -n "$audio_file" ]]; then
            log "    TTS: $audio_file"
        else
            log "    TTS: streamed (no file saved)"
        fi
        
        # Show truncated response text
        if [[ ${#response_text} -gt 200 ]]; then
            log "    Text: ${response_text:0:200}..."
        else
            log "    Text: $response_text"
        fi
        log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

        # Persist conversation id for follow-up prompts
        local new_conv_id
        new_conv_id=$(echo "$response" | jq -r '.conversation_id // empty' 2>/dev/null)
        if [[ -n "$new_conv_id" ]]; then
            echo "$new_conv_id" > "$CONV_FILE"
            log "    Conversation: $new_conv_id (saved for context)"
        fi
        
        return 0
    else
        # For other actions, use the regular query endpoint
        local response
        response=$(curl -s -X POST "http://localhost:$ORCHESTRATOR_PORT/query" \
            -H "Content-Type: application/json" \
            -d "{\"query\": \"$query\"}" \
            --max-time 30)
        echo "$response"
        return $?
    fi
}

# Start recording for agent input
start_recording() {
    log "Starting agent input mode..."
    
    # Check if already recording
    if [[ -f "$RECORDING_FLAG" ]]; then
        warn "Already recording, stopping first..."
        stop_recording
    fi
    
    # Create recording flag
    touch "$RECORDING_FLAG"
    
    # Play cue so user knows capture began (reuses query-in sound)
    play_sound "query-in"
    
    # Use configured audio source from config.yaml or env var
    log "Using audio source: $AUDIO_SOURCE"
    
    # Start recording in background using arecord (same as working hypr-voice-record.sh)
    # Use -f cd for CD quality (16-bit stereo 44100Hz) which is widely compatible
    arecord -f cd -t wav "$AUDIO_FILE" 2>/dev/null &
    echo $! > /tmp/hypr-agent-recorder.pid
    
    log "Recording started (PID: $(cat /tmp/hypr-agent-recorder.pid 2>/dev/null || echo 'unknown'))"
}

# Stop recording and process
stop_recording() {
    # Stop the recorder
    if [[ -f /tmp/hypr-agent-recorder.pid ]]; then
        local pid
        pid=$(cat /tmp/hypr-agent-recorder.pid)
        kill "$pid" 2>/dev/null || true
        # Also kill any arecord processes recording to our file
        pkill -f "arecord.*hypr-agent" 2>/dev/null || true
        rm -f /tmp/hypr-agent-recorder.pid
    fi
    
    rm -f "$RECORDING_FLAG"
    log "Recording stopped"
}

# Transcribe audio using Whisper (hybrid-whisper-server API)
# Note: This function outputs ONLY the transcribed text to stdout
# All logging goes to stderr and log file only
transcribe_audio() {
    local audio_path="$1"
    
    # Helper for logging within this function (stderr only to avoid capturing in output)
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
    
    # Check if Whisper server is running
    if ! nc -z localhost "$WHISPER_PORT" 2>/dev/null; then
        _terr "Whisper server not running on port $WHISPER_PORT"
        return 1
    fi
    
    _tlog "Creating Whisper session..."
    
    # Step 1: Create a session (requires JSON body)
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
        _terr "No session_id in response: $session_response"
        return 1
    fi
    
    _tlog "Session created: $session_id"
    
    # Step 2: Upload audio file for transcription
    _tlog "Uploading audio to Whisper..."
    local transcribe_start_ms
    # Milliseconds timestamp (GNU date)
    transcribe_start_ms=$(date +%s%3N 2>/dev/null || date +%s000)
    local upload_response
    upload_response=$(curl -s -X POST "http://localhost:$WHISPER_PORT/sessions/$session_id/transcribe" \
        -F "audio_file=@$audio_path" \
        --max-time 30)
    
    _tlog "Upload response: $upload_response"
    
    # Step 3: Poll for result (with timeout)
    local max_attempts=30
    local attempt=0
    local final_text=""
    local status_response=""
    
    while [[ $attempt -lt $max_attempts ]]; do
        sleep 1
        
        status_response=$(curl -s "http://localhost:$WHISPER_PORT/sessions/$session_id" \
            --max-time 5)
        
        local status
        status=$(echo "$status_response" | jq -r '.status // empty' 2>/dev/null)
        final_text=$(echo "$status_response" | jq -r '.final_text // empty' 2>/dev/null)
        local elapsed_ms=$(( $(date +%s%3N) - transcribe_start_ms ))
        _tlog "Poll attempt $attempt: status=$status, text='$final_text', elapsed=${elapsed_ms}ms"
        
        if [[ "$status" == "completed" ]] || [[ -n "$final_text" ]]; then
            break
        fi
        
        ((attempt++))
    done
    
    if [[ -z "$final_text" ]]; then
        # Try to get any text from the response
        final_text=$(echo "$status_response" | jq -r '.text // .transcription // empty' 2>/dev/null)
    fi
    
    # Output ONLY the transcribed text
    echo "$final_text"
}

# Process recorded audio and send to orchestrator
process_input() {
    log "Processing agent input..."
    
    # Stop recording first
    stop_recording
    
    # Wait for audio file to be written
    sleep 0.3
    
    # Check audio file
    if [[ ! -f "$AUDIO_FILE" ]] || [[ ! -s "$AUDIO_FILE" ]]; then
        warn "No audio recorded or file is empty"
        # TODO: play_sound "error"
        return 1
    fi
    
    # TODO: play_sound "processing"
    local transcribed
    transcribed=$(transcribe_audio "$AUDIO_FILE")
    
    if [[ -z "$transcribed" ]]; then
        error "Transcription failed or empty"
        # TODO: play_sound "error"
        return 1
    fi
    
    log "Transcribed: $transcribed"
    
    # Send to orchestrator voice pipeline
    if check_orchestrator; then
        log "Sending to orchestrator..."
        if send_to_orchestrator "query" "$transcribed"; then
            log "Response received and spoken via TTS"
            # TODO: play_sound "success"
        else
            warn "Failed to get response from orchestrator"
            # TODO: play_sound "error"
        fi
    else
        # Fallback: Output to stdout or clipboard
        warn "Orchestrator not running, copying to clipboard"
        echo "$transcribed" | wl-copy 2>/dev/null || echo "$transcribed"
    fi
    
    # Cleanup
    rm -f "$AUDIO_FILE"
}

# Get orchestrator status
get_status() {
    if check_orchestrator; then
        log "Orchestrator: Running on port $ORCHESTRATOR_PORT"
        send_to_orchestrator "list_agents" | jq '.' 2>/dev/null || echo "Connected"
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
    query)
        # Direct query mode (for testing)
        shift
        query_text="$*"
        if [[ -z "$query_text" ]]; then
            read -r -p "Enter query: " query_text
        fi
        if check_orchestrator; then
            send_to_orchestrator "query" "$query_text"
        else
            error "Orchestrator not running"
            exit 1
        fi
        ;;
    help|--help|-h)
        echo "Usage: hypr-agent.sh <command>"
        echo ""
        echo "Commands:"
        echo "  start    - Start recording for agent input (F10 press)"
        echo "  process  - Stop recording and send to orchestrator (F10 release)"
        echo "  stop     - Stop recording without processing"
        echo "  status   - Show orchestrator and whisper status"
        echo "  query    - Send a direct text query to orchestrator"
        echo ""
        echo "Environment:"
        echo "  HYPR_AGENT_PORT   - Orchestrator port (default: 9093)"
        echo "  HYPR_WHISPER_PORT - Whisper server port (default: 9090)"
        ;;
    *)
        error "Unknown command: ${1:-}"
        echo "Use 'hypr-agent.sh help' for usage"
        exit 1
        ;;
esac
