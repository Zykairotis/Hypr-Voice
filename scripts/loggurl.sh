#!/bin/bash
# LogGurl - Hypr-Voice Log Viewer
#
# Usage:
#   loggurl.sh              - Follow all logs (tail -f)
#   loggurl.sh tail         - Follow all logs
#   loggurl.sh cat          - Show all logs
#   loggurl.sh last [N]     - Show last N lines (default: 100)
#   loggurl.sh grep <pat>   - Search logs for pattern
#   loggurl.sh clear        - Clear log file
#   loggurl.sh filter <component> - Show only specific component
#   loggurl.sh errors       - Show only errors/warnings
#   loggurl.sh today        - Show today's logs
#   loggurl.sh stats        - Show log statistics

set -e

LOG_DIR="${HYPR_VOICE_LOG_DIR:-/tmp/hypr-voice}"
LOG_FILE="$LOG_DIR/hypr-voice.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Create log file if it doesn't exist
touch "$LOG_FILE"

header() {
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BOLD}${CYAN}  LogGurl - Hypr-Voice Unified Logs${NC}"
    echo -e "${DIM}  Log file: $LOG_FILE${NC}"
    echo -e "${BOLD}${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

colorize_output() {
    # Add colors based on log content
    sed -E \
        -e "s/\[ERROR\]/$(printf '\033[31m')[ERROR]$(printf '\033[0m')/g" \
        -e "s/\[WARN[A-Z]*\]/$(printf '\033[33m')&$(printf '\033[0m')/g" \
        -e "s/━━━ START ━━━/$(printf '\033[1;32m')━━━ START ━━━$(printf '\033[0m')/g" \
        -e "s/━━━ COMPLETE[^━]*━━━/$(printf '\033[1;32m')&$(printf '\033[0m')/g" \
        -e "s/ROUTE →/$(printf '\033[35m')ROUTE →$(printf '\033[0m')/g" \
        -e "s/LLM →/$(printf '\033[33m')LLM →$(printf '\033[0m')/g" \
        -e "s/LLM ←/$(printf '\033[33m')LLM ←$(printf '\033[0m')/g" \
        -e "s/TTS →/$(printf '\033[32m')TTS →$(printf '\033[0m')/g" \
        -e "s/TTS ←/$(printf '\033[32m')TTS ←$(printf '\033[0m')/g" \
        -e "s/STT[^:]*:/$(printf '\033[34m')&$(printf '\033[0m')/g" \
        -e "s/REQ [A-Z]+ /$(printf '\033[36m')&$(printf '\033[0m')/g" \
        -e "s/\[orchestrator\]/$(printf '\033[35m')&$(printf '\033[0m')/g" \
        -e "s/\[voice\]/$(printf '\033[33m')&$(printf '\033[0m')/g" \
        -e "s/\[tts\]/$(printf '\033[32m')&$(printf '\033[0m')/g" \
        -e "s/\[whisper\]/$(printf '\033[34m')&$(printf '\033[0m')/g" \
        -e "s/\[agent\]/$(printf '\033[36m')&$(printf '\033[0m')/g" \
        -e "s/\[router\]/$(printf '\033[95m')&$(printf '\033[0m')/g" \
        -e "s/\[llm\]/$(printf '\033[93m')&$(printf '\033[0m')/g" \
        -e "s/\[server\]/$(printf '\033[96m')&$(printf '\033[0m')/g"
}

show_logs() {
    # All logs are now in the same file with unified format
    # Format: HH:MM:SS.mmm [component] [LEVEL] message
    cat "$LOG_FILE" 2>/dev/null
}

case "${1:-tail}" in
    tail|follow|f)
        header
        echo -e "${DIM}Following logs... (Ctrl+C to stop)${NC}"
        echo ""
        tail -f "$LOG_FILE" 2>/dev/null | colorize_output
        ;;
    
    cat|all|a)
        header
        show_logs | colorize_output
        ;;
    
    last|l)
        lines="${2:-100}"
        header
        echo -e "${DIM}Last $lines lines:${NC}"
        echo ""
        show_logs | tail -n "$lines" | colorize_output
        ;;
    
    grep|search|s)
        pattern="$2"
        if [[ -z "$pattern" ]]; then
            echo "Usage: loggurl.sh grep <pattern>"
            exit 1
        fi
        header
        echo -e "${DIM}Searching for: $pattern${NC}"
        echo ""
        show_logs | grep -i --color=always "$pattern" | colorize_output
        ;;
    
    filter|component|c)
        component="$2"
        if [[ -z "$component" ]]; then
            echo "Usage: loggurl.sh filter <component>"
            echo "Components: orchestrator, voice, tts, whisper, agent, router, llm, server"
            exit 1
        fi
        header
        echo -e "${DIM}Filtering by component: $component${NC}"
        echo ""
        show_logs | grep -i "\[$component" | colorize_output
        ;;
    
    errors|err|e)
        header
        echo -e "${DIM}Errors and warnings only:${NC}"
        echo ""
        show_logs | grep -iE "\[ERROR\]|\[ WARN" | colorize_output
        ;;
    
    today|t)
        header
        echo -e "${DIM}Today's logs:${NC}"
        echo ""
        show_logs | colorize_output
        ;;
    
    clear|clean)
        echo -e "${YELLOW}Clearing log file...${NC}"
        > "$LOG_FILE"
        echo -e "${GREEN}Logs cleared!${NC}"
        ;;
    
    stats|info|i)
        header
        echo ""
        echo -e "${BOLD}Log Statistics:${NC}"
        echo ""
        
        if [[ -f "$LOG_FILE" ]] && [[ -s "$LOG_FILE" ]]; then
            total_lines=$(wc -l < "$LOG_FILE" | tr -d ' ')
            total_size=$(du -h "$LOG_FILE" | cut -f1)
            errors=$(grep -c "\[ERROR\]" "$LOG_FILE" 2>/dev/null | tr -d '\n' || echo "0")
            warns=$(grep -c "WARN" "$LOG_FILE" 2>/dev/null | tr -d '\n' || echo "0")
        else
            total_lines=0; total_size="0B"; errors=0; warns=0
        fi
        
        echo -e "  ${CYAN}Total lines:${NC} $total_lines ($total_size)"
        echo -e "  ${RED}Errors:${NC}      $errors"
        echo -e "  ${YELLOW}Warnings:${NC}    $warns"
        echo ""
        
        echo -e "${BOLD}Component breakdown:${NC}"
        echo ""
        for comp in orchestrator voice tts whisper agent router llm server; do
            count=$(grep -ci "\[$comp\]" "$LOG_FILE" 2>/dev/null | tr -d '\n' || echo "0")
            [[ -z "$count" ]] && count=0
            if [[ "$count" -gt 0 ]]; then
                printf "  %-14s %d lines\n" "$comp:" "$count"
            fi
        done
        ;;
    
    help|--help|-h)
        echo "LogGurl - Hypr-Voice Unified Log Viewer"
        echo ""
        echo "Usage: loggurl.sh [command] [args]"
        echo ""
        echo "Commands:"
        echo "  tail, f          Follow logs in real-time (default)"
        echo "  cat, all, a      Show all logs"
        echo "  last, l [N]      Show last N lines (default: 100)"
        echo "  grep, s <pat>    Search for pattern"
        echo "  filter, c <comp> Filter by component"
        echo "  errors, e        Show only errors/warnings"
        echo "  today, t         Show today's logs"
        echo "  clear            Clear all logs"
        echo "  stats, i         Show log statistics"
        echo ""
        echo "Components: orchestrator, voice, tts, whisper, agent, router, llm, server"
        echo ""
        echo "Environment:"
        echo "  HYPR_VOICE_LOG_DIR   Log directory (default: /tmp/hypr-voice)"
        echo "  HYPR_VOICE_LOG_LEVEL Log level (default: INFO)"
        ;;
    
    *)
        echo "Unknown command: $1"
        echo "Use 'loggurl.sh help' for usage"
        exit 1
        ;;
esac
