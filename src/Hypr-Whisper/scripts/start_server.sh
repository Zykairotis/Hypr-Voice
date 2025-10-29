#!/bin/bash
# WhisperLive Server Startup Script for Hypr-Voice

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$(dirname "$WHISPER_ROOT")")"
VENV_PATH="$PROJECT_ROOT/.venv"

# Configuration
CONFIG_FILE="$WHISPER_ROOT/config/config.yaml"
LOG_FILE="/tmp/whisper-live-hypr-voice.log"
PID_FILE="/tmp/whisper-live-server.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "$VENV_PATH" ]; then
        print_error "Virtual environment not found at $VENV_PATH"
        print_status "Please create it first: python -m venv $VENV_PATH"
        exit 1
    fi

    if [ ! -f "$VENV_PATH/bin/activate" ]; then
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Function to check if WhisperLive is installed
check_whisper_live() {
    source "$VENV_PATH/bin/activate"
    if ! python -c "import whisper_live" 2>/dev/null; then
        print_error "WhisperLive not installed in virtual environment"
        print_status "Installing WhisperLive..."
        pip install whisper-live
    fi
}

# Function to start server
start_server() {
    print_header "🎤 Starting WhisperLive Server for Hypr-Voice"

    check_venv
    check_whisper_live

    # Check if server is already running
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Server is already running (PID: $pid)"
            return 0
        else
            print_warning "Stale PID file found, removing..."
            rm -f "$PID_FILE"
        fi
    fi

    # Activate virtual environment
    source "$VENV_PATH/bin/activate"

    # Create necessary directories
    mkdir -p /tmp/whisper-live-cache
    mkdir -p /tmp/whisper-models

    print_status "Configuration: $CONFIG_FILE"
    print_status "Log file: $LOG_FILE"
    print_status "Starting server..."

    # Start the server
    cd "$WHISPER_ROOT"
    nohup python start_whisper_live.py --config "$CONFIG_FILE" > "$LOG_FILE" 2>&1 &
    local server_pid=$!

    # Save PID
    echo "$server_pid" > "$PID_FILE"

    # Wait a moment and check if server started successfully
    sleep 2
    if kill -0 "$server_pid" 2>/dev/null; then
        print_status "✅ Server started successfully (PID: $server_pid)"
        print_status "🔗 WebSocket server: ws://localhost:9090"
        print_status "📋 Logs: tail -f $LOG_FILE"
    else
        print_error "❌ Failed to start server"
        print_status "Check logs: cat $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Function to stop server
stop_server() {
    print_header "🛑 Stopping WhisperLive Server"

    if [ ! -f "$PID_FILE" ]; then
        print_warning "No PID file found - server may not be running"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    if kill -0 "$pid" 2>/dev/null; then
        print_status "Stopping server (PID: $pid)..."
        kill "$pid"

        # Wait for graceful shutdown
        local count=0
        while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
            sleep 1
            count=$((count + 1))
        done

        # Force kill if still running
        if kill -0 "$pid" 2>/dev/null; then
            print_warning "Force killing server..."
            kill -9 "$pid"
        fi

        print_status "✅ Server stopped"
    else
        print_warning "Server process not found (PID: $pid)"
    fi

    rm -f "$PID_FILE"
}

# Function to check server status
check_status() {
    print_header "📊 WhisperLive Server Status"

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "✅ Server is running (PID: $pid)"

            # Check if WebSocket port is listening
            if netstat -ln 2>/dev/null | grep -q ":9090 "; then
                print_status "🔗 WebSocket server listening on port 9090"
            else
                print_warning "WebSocket port 9090 not found listening"
            fi
        else
            print_error "❌ Server is not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "❌ Server is not running"
    fi
}

# Function to show logs
show_logs() {
    print_header "📋 WhisperLive Server Logs"

    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        print_warning "No log file found at $LOG_FILE"
    fi
}

# Function to test server
test_server() {
    print_header "🧪 Testing WhisperLive Server"

    # Check if server is running
    if [ ! -f "$PID_FILE" ]; then
        print_error "Server is not running. Start it first: $0 start"
        return 1
    fi

    local pid=$(cat "$PID_FILE")
    if ! kill -0 "$pid" 2>/dev/null; then
        print_error "Server process not found. Start it first: $0 start"
        return 1
    fi

    # Test WebSocket connection
    print_status "Testing WebSocket connection..."

    source "$VENV_PATH/bin/activate"
    cd "$WHISPER_ROOT"

    python3 -c "
import asyncio
import websockets
import json

async def test_connection():
    try:
        uri = 'ws://localhost:9090'
        async with websockets.connect(uri) as websocket:
            print('✅ WebSocket connection successful')
            return True
    except Exception as e:
        print(f'❌ WebSocket connection failed: {e}')
        return False

result = asyncio.run(test_connection())
exit(0 if result else 1)
" && print_status "✅ Server test passed" || print_error "❌ Server test failed"
}

# Main script logic
case "${1:-start}" in
    start)
        start_server
        ;;
    stop)
        stop_server
        ;;
    restart)
        stop_server
        sleep 1
        start_server
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    test)
        test_server
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|test}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the WhisperLive server"
        echo "  stop    - Stop the WhisperLive server"
        echo "  restart - Restart the WhisperLive server"
        echo "  status  - Check server status"
        echo "  logs    - Show server logs"
        echo "  test    - Test WebSocket connection"
        exit 1
        ;;
esac