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
WHISPER_PORT="${HYPR_WHISPER_PORT:-9090}"
RECORDING_FLAG="/tmp/hypr-agent-recording"
AUDIO_FILE="/tmp/hypr-agent-audio.wav"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[hypr-agent]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[hypr-agent]${NC} $1"
}

error() {
    echo -e "${RED}[hypr-agent]${NC} $1" >&2
}

# TODO: Add audio feedback sounds
# play_sound() {
#     local sound="$1"  # start, processing, success, error
#     local sound_dir="$PROJECT_DIR/sounds"
#     aplay "$sound_dir/${sound}.wav" 2>/dev/null &
# }

# Check if orchestrator is running
check_orchestrator() {
    nc -z localhost "$ORCHESTRATOR_PORT" 2>/dev/null
    return $?
}

# Send message to orchestrator via WebSocket
send_to_orchestrator() {
    local action="$1"
    local query="$2"
    
    local payload
    if [[ -n "$query" ]]; then
        payload=$(jq -n --arg action "$action" --arg query "$query" \
            '{type: $action, query: $query}')
    else
        payload=$(jq -n --arg action "$action" '{type: $action}')
    fi
    
    # Send via netcat (simple TCP)
    echo "$payload" | nc -N localhost "$ORCHESTRATOR_PORT" 2>/dev/null
    return $?
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
    
    # TODO: play_sound "start"
    
    # Start audio recording using PulseAudio
    # Get default source
    local source
    source=$(pactl get-default-source 2>/dev/null || echo "@DEFAULT_SOURCE@")
    
    # Start recording in background
    parec --format=s16le --rate=16000 --channels=1 -d "$source" 2>/dev/null | \
        ffmpeg -y -f s16le -ar 16000 -ac 1 -i pipe:0 "$AUDIO_FILE" &>/dev/null &
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
        # Also kill any parec processes
        pkill -f "parec.*hypr-agent" 2>/dev/null || true
        rm -f /tmp/hypr-agent-recorder.pid
    fi
    
    rm -f "$RECORDING_FLAG"
    log "Recording stopped"
}

# Transcribe audio using Whisper
transcribe_audio() {
    local audio_path="$1"
    
    if [[ ! -f "$audio_path" ]]; then
        error "Audio file not found: $audio_path"
        return 1
    fi
    
    # Check if Whisper server is running
    if ! nc -z localhost "$WHISPER_PORT" 2>/dev/null; then
        error "Whisper server not running on port $WHISPER_PORT"
        return 1
    fi
    
    # Send to Whisper for transcription
    local response
    response=$(curl -s -X POST "http://localhost:$WHISPER_PORT/transcribe" \
        -H "Content-Type: application/json" \
        -d "{\"audio_path\": \"$audio_path\", \"language\": \"auto\"}" \
        --max-time 30)
    
    if [[ -z "$response" ]]; then
        error "Empty response from Whisper"
        return 1
    fi
    
    # Extract text from response
    echo "$response" | jq -r '.text // .transcription // empty' 2>/dev/null
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
    
    # Send to orchestrator
    if check_orchestrator; then
        send_to_orchestrator "query" "$transcribed"
        log "Sent to orchestrator"
        # TODO: play_sound "success"
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
