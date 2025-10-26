#!/bin/bash

# Universal Paste Script for Hypr-Voice
# Uses wlpaste for reliable pasting across all Wayland applications

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/tmp/hypr-voice-universal-paste.log"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

# Main paste function
universal_paste() {
    local text="$1"

    log "Starting universal paste for text: '${text:0:50}...'"

    # Copy text to clipboard first (as backup)
    if ! echo "$text" | wl-copy; then
        log "ERROR: Failed to copy text to clipboard"
        return 1
    fi

    log "Text copied to clipboard successfully"

    # Small delay to ensure clipboard is ready
    sleep 0.1

    # Type the text directly using wtype (universal paste method)
    # Try regular wtype first (should be instant by default)
    log "Typing ${#text} characters with wtype"
    if ! wtype "$text"; then
        log "ERROR: Failed to type text with wtype"
        log "Text is available in clipboard - paste manually with Ctrl+V"
        return 1
    fi

    log "Text typed successfully with wtype"
    return 0
}

# Check if text is provided as argument or via pipe
if [[ $# -gt 0 ]]; then
    # Text provided as argument
    universal_paste "$1"
elif [[ ! -t 0 ]]; then
    # Text provided via pipe
    text=$(cat)
    universal_paste "$text"
else
    echo "Usage: $0 'text to paste' or echo 'text' | $0"
    echo "Logs: $LOG_FILE"
    exit 1
fi