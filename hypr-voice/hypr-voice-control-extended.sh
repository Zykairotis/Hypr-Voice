#!/bin/bash
# Hypr-Voice control script for Hyprland keybinds - EXTENDED VERSION with RAW MODE
SOCKET="/tmp/hypr-voice.sock"
TIMEOUT=0.5  # Reduced from 2 seconds to 0.5 seconds
LOCKFILE="/tmp/hypr-voice-command.lock"
RAW_MODE_STATE_FILE="/tmp/hypr-voice-raw-mode.state"

# Function to send command FAST with minimal overhead
send_command_fast() {
    local msg="$1"
    
    # Check if socket exists (quick check)
    if [ ! -S "$SOCKET" ]; then
        echo "Error: Socket not found" >&2
        return 1
    fi
    
    # Use printf with exec for fastest connection (single process)
    # Try socat first (most reliable), then fallback
    if command -v socat >/dev/null 2>&1; then
        # Use socat with minimal timeout and no retries
        printf "%s" "$msg" | timeout $TIMEOUT socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null
        return $?
    elif command -v ncat >/dev/null 2>&1; then
        printf "%s" "$msg" | timeout $TIMEOUT ncat -U "$SOCKET" 2>/dev/null
        return $?
    else
        # Fallback to nc if available
        printf "%s" "$msg" | timeout $TIMEOUT nc -U "$SOCKET" 2>/dev/null
        return $?
    fi
}

# Prevent multiple simultaneous commands using flock
run_with_lock() {
    local command="$1"
    
    # Use flock for atomic locking (prevents race conditions)
    (
        # Try to get exclusive lock with short timeout
        if flock -x -w 0.1 200; then
            send_command_fast "$command"
        else
            echo "Command in progress, skipping..." >&2
            exit 1
        fi
    ) 200>"$LOCKFILE"
}

# Raw mode state management
get_raw_mode_state() {
    if [ -f "$RAW_MODE_STATE_FILE" ]; then
        cat "$RAW_MODE_STATE_FILE" 2>/dev/null || echo "enhanced"
    else
        echo "enhanced"
    fi
}

set_raw_mode_state() {
    local mode="$1"
    echo "$mode" > "$RAW_MODE_STATE_FILE"
}

toggle_raw_mode() {
    local current_mode=$(get_raw_mode_state)
    if [ "$current_mode" = "raw" ]; then
        set_raw_mode_state "enhanced"
        echo "Switched to enhanced mode"
    else
        set_raw_mode_state "raw"
        echo "Switched to raw mode"
    fi
}

# Emergency cleanup and force-stop helpers
cleanup_stuck_recording() {
    # Try STOP twice quickly, then escalate to FORCE_STOP
    for i in {1..2}; do
        send_command_fast "STOP" && break
        sleep 0.03
    done
    # If still stuck, send FORCE_STOP
    send_command_fast "FORCE_STOP" >/dev/null 2>&1
    # Clean up any stale lock files
    rm -f "$LOCKFILE" 2>/dev/null
}

force_stop_now() {
    # Directly send FORCE_STOP with minimal overhead
    send_command_fast "FORCE_STOP"
}

# Start recording with mode selection
start_recording() {
    local mode="$1"
    local command="START"
    
    if [ "$mode" = "raw" ]; then
        command="START_RAW"
    elif [ "$mode" = "enhanced" ]; then
        command="START_ENHANCED"
    else
        # Use current mode state
        local current_mode=$(get_raw_mode_state)
        if [ "$current_mode" = "raw" ]; then
            command="START_RAW"
        else
            command="START_ENHANCED"
        fi
    fi
    
    # For START: send command without waiting for response
    run_with_lock "$command" &
}

# Enhanced status command with raw mode information
show_status() {
    local current_mode=$(get_raw_mode_state)
    echo "Current mode: $current_mode"
    
    if response=$(run_with_lock "STATUS"); then
        echo "Service status: $response"
    else
        echo "Service status: unavailable"
    fi
}

# Handle different commands with optimizations
case "$1" in
    start)
        # Standard start - use current mode
        start_recording
        ;;
    start-raw)
        # Force raw mode start
        start_recording "raw"
        ;;
    start-enhanced)
        # Force enhanced mode start
        start_recording "enhanced"
        ;;
    stop)
        # For STOP: this is critical, ensure it gets through
        cleanup_stuck_recording
        ;;
    stop-raw)
        # Raw mode specific stop (same as regular stop for now)
        cleanup_stuck_recording
        ;;
    status)
        show_status
        ;;
    toggle-raw-mode)
        # Toggle between raw and enhanced modes
        toggle_raw_mode
        ;;
    set-raw-mode)
        # Set to raw mode
        set_raw_mode_state "raw"
        echo "Set to raw mode"
        ;;
    set-enhanced-mode)
        # Set to enhanced mode
        set_raw_mode_state "enhanced"
        echo "Set to enhanced mode"
        ;;
    get-mode)
        # Get current mode
        get_raw_mode_state
        ;;
    force-stop)
        # Emergency stop command: send FORCE_STOP immediately
        force_stop_now || cleanup_stuck_recording
        ;;
    *)
        echo "Usage: $0 {start|start-raw|start-enhanced|stop|stop-raw|status|toggle-raw-mode|set-raw-mode|set-enhanced-mode|get-mode|force-stop}"
        echo ""
        echo "Commands:"
        echo "  start              - Start recording using current mode"
        echo "  start-raw          - Start recording in raw mode (fast, no enhancement)"
        echo "  start-enhanced     - Start recording in enhanced mode (slower, with AI improvement)"
        echo "  stop               - Stop recording"
        echo "  stop-raw           - Stop raw mode recording"
        echo "  status             - Show service and mode status"
        echo "  toggle-raw-mode    - Toggle between raw and enhanced modes"
        echo "  set-raw-mode       - Set default mode to raw"
        echo "  set-enhanced-mode  - Set default mode to enhanced"
        echo "  get-mode           - Get current default mode"
        echo "  force-stop         - Emergency stop"
        echo ""
        echo "Current mode: $(get_raw_mode_state)"
        exit 1
        ;;
esac