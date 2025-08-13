#!/bin/bash
# Hypr-Voice control script for Hyprland keybinds - OPTIMIZED VERSION
SOCKET="/tmp/hypr-voice.sock"
TIMEOUT=0.5  # Reduced from 2 seconds to 0.5 seconds
LOCKFILE="/tmp/hypr-voice-command.lock"

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

# Handle different commands with optimizations
case "$1" in
    start)
        # For START: send command without waiting for response
        run_with_lock "START" &
        ;;
    stop)
        # For STOP: this is critical, ensure it gets through
        cleanup_stuck_recording
        ;;
    status)
        if response=$(run_with_lock "STATUS"); then
            echo "$response"
        fi
        ;;
    force-stop)
        # Emergency stop command: send FORCE_STOP immediately
        force_stop_now || cleanup_stuck_recording
        ;;
    *)
        echo "Usage: $0 {start|stop|status|force-stop}"
        exit 1
        ;;
esac