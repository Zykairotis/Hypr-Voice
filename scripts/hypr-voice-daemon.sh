#!/bin/bash
# Hypr-Voice PTT Daemon
# Runs in background and listens for start/stop commands

set -e

# Get directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Configuration
DAEMON_PORT=9876
PIDFILE="/tmp/hypr-voice-daemon.pid"
LOGFILE="/tmp/hypr-voice-daemon.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if daemon is already running
check_daemon() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0  # Daemon is running
        else
            rm -f "$PIDFILE"
        fi
    fi
    return 1  # Daemon is not running
}

# Start daemon
start_daemon() {
    if check_daemon; then
        echo -e "${YELLOW}[INFO]${NC} Daemon already running with PID $(cat $PIDFILE)"
        return 0
    fi
    
    echo -e "${BLUE}🎤 Starting Hypr-Voice PTT Daemon${NC}"
    
    # Check dependencies
    if ! command -v ydotool &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} ydotool not found!"
        echo -e "${YELLOW}[INFO]${NC} Install with: sudo pacman -S ydotool (Arch) or build from source"
        exit 1
    fi
    
    if ! command -v nc &> /dev/null; then
        echo -e "${RED}[ERROR]${NC} netcat not found!"
        echo -e "${YELLOW}[INFO]${NC} Install with: sudo apt-get install netcat-openbsd"
        exit 1
    fi
    
    # Check if server is running
    if ! curl -s http://localhost:9099/health > /dev/null 2>&1; then
        echo -e "${YELLOW}[WARN]${NC} Whisper server not responding at http://localhost:9099"
        echo -e "${YELLOW}[INFO]${NC} Start server with: ./scripts/start_hybrid_server.sh"
        echo ""
        read -p "Start daemon anyway? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Start the Python daemon in background
    # Python files have moved to src/hypr_voice/whisper/, run from project root
    cd "$PROJECT_ROOT"
    export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

    # Create named pipe for communication
    FIFO="/tmp/hypr-voice-fifo"
    rm -f "$FIFO"
    mkfifo "$FIFO"

    # Start Python script listening to the pipe - run as module
    (
        "$VENV_PATH/bin/python" -m hypr_voice.whisper.integration.hypr_voice_type daemon < "$FIFO" > "$LOGFILE" 2>&1 &
        echo $! > "$PIDFILE"
    )
    
    # Start netcat server listening on port and forwarding to pipe
    (
        while true; do
            nc -l localhost "$DAEMON_PORT" >> "$FIFO"
        done
    ) &
    echo $! > "${PIDFILE}.nc"
    
    echo -e "${GREEN}✓${NC} Daemon started on port ${DAEMON_PORT}"
    echo -e "${GREEN}✓${NC} PID: $(cat $PIDFILE)"
    echo -e "${GREEN}✓${NC} Log: $LOGFILE"
    echo ""
    echo -e "${YELLOW}Push-to-Talk Ready:${NC}"
    echo -e "  • Press ${GREEN}F9${NC} to start recording"
    echo -e "  • Release ${GREEN}F9${NC} to stop and transcribe"
    echo -e "  • Text will be typed automatically"
    echo ""
    echo -e "${BLUE}Test commands:${NC}"
    echo -e "  echo 'start' | nc localhost $DAEMON_PORT"
    echo -e "  echo 'stop' | nc localhost $DAEMON_PORT"
}

# Stop daemon
stop_daemon() {
    if ! check_daemon; then
        echo -e "${YELLOW}[INFO]${NC} Daemon is not running"
        return 0
    fi
    
    echo -e "${BLUE}Stopping Hypr-Voice PTT Daemon${NC}"
    
    # Send exit command
    echo "exit" | nc -N localhost "$DAEMON_PORT" 2>/dev/null || true
    
    # Kill processes
    if [ -f "$PIDFILE" ]; then
        kill $(cat "$PIDFILE") 2>/dev/null || true
        rm -f "$PIDFILE"
    fi
    
    if [ -f "${PIDFILE}.nc" ]; then
        kill $(cat "${PIDFILE}.nc") 2>/dev/null || true
        rm -f "${PIDFILE}.nc"
    fi
    
    # Clean up
    rm -f /tmp/hypr-voice-fifo
    
    echo -e "${GREEN}✓${NC} Daemon stopped"
}

# Restart daemon
restart_daemon() {
    stop_daemon
    sleep 1
    start_daemon
}

# Show status
status_daemon() {
    if check_daemon; then
        echo -e "${GREEN}✓${NC} Daemon is running with PID $(cat $PIDFILE)"
        echo -e "${GREEN}✓${NC} Listening on port $DAEMON_PORT"
        
        if [ -f "$LOGFILE" ]; then
            echo ""
            echo -e "${BLUE}Recent log entries:${NC}"
            tail -n 5 "$LOGFILE"
        fi
    else
        echo -e "${RED}✗${NC} Daemon is not running"
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    restart)
        restart_daemon
        ;;
    status)
        status_daemon
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
