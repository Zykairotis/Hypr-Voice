#!/bin/bash
# Hybrid WhisperLive Server Startup Script for Hypr-Voice

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WHISPER_ROOT="$(dirname "$SCRIPT_DIR")"

# For hybrid-whisper worktree, we need to go up to the main Hypr-Voice root
# Path: .../Hypr-Voice/src/hybrid-whisper/src/whisper/scripts
# We need to go up 5 levels to reach Hypr-Voice root
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../../../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Configuration
CONFIG_FILE="$WHISPER_ROOT/config/config.yaml"
LOG_FILE="/tmp/hybrid-whisper-server.log"
PID_FILE="/tmp/hybrid-whisper-server.pid"

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

# Function to check dependencies
check_dependencies() {
    # Use venv's python and pip explicitly
    local PYTHON="$VENV_PATH/bin/python"
    local PIP="$VENV_PATH/bin/pip"
    
    # Check if uv is available for faster installs
    if command -v uv &> /dev/null; then
        print_status "Using uv for package installation"
        local INSTALLER="uv pip install --python $PYTHON"
    else
        local INSTALLER="$PIP install"
    fi
    
    # Check required packages
    $PYTHON -c "import fastapi" 2>/dev/null || {
        print_warning "FastAPI not installed. Installing..."
        $INSTALLER fastapi "uvicorn[standard]"
    }
    
    $PYTHON -c "import websockets" 2>/dev/null || {
        print_warning "websockets not installed. Installing..."
        $INSTALLER websockets
    }
    
    $PYTHON -c "import faster_whisper" 2>/dev/null || {
        print_warning "faster-whisper not installed. Installing..."
        $INSTALLER faster-whisper
    }
    
    $PYTHON -c "import soundfile" 2>/dev/null || {
        print_warning "soundfile not installed. Installing..."
        $INSTALLER soundfile
    }
    
    $PYTHON -c "import ffmpeg" 2>/dev/null || {
        print_warning "ffmpeg-python not installed. Installing..."
        $INSTALLER ffmpeg-python
    }
    
    $PYTHON -c "import scipy" 2>/dev/null || {
        print_warning "scipy not installed. Installing..."
        $INSTALLER scipy
    }
}

# Function to start server
start_server() {
    print_header "🚀 Starting Hybrid WhisperLive Server"
    
    check_venv
    check_dependencies
    
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
    
    # Create necessary directories
    mkdir -p /tmp/whisper-live-cache
    mkdir -p /tmp/whisper-models
    mkdir -p "$WHISPER_ROOT/logs"
    
    print_status "Configuration: $CONFIG_FILE"
    print_status "Log file: $LOG_FILE"
    print_status "Virtual Environment: $VENV_PATH"
    print_status "Starting hybrid server..."
    
    # Start the server using venv's python explicitly
    cd "$WHISPER_ROOT"
    nohup "$VENV_PATH/bin/python" hybrid_server.py > "$LOG_FILE" 2>&1 &
    local server_pid=$!
    
    # Save PID
    echo "$server_pid" > "$PID_FILE"
    
    # Wait a moment and check if server started successfully
    sleep 3
    if kill -0 "$server_pid" 2>/dev/null; then
        print_status "✅ Server started successfully (PID: $server_pid)"
        print_status ""
        print_header "📍 Endpoints:"
        print_status "🔗 WebSocket: ws://localhost:9090/ws/{session_id}"
        print_status "🌐 REST API: http://localhost:9090"
        print_status "📚 API Docs: http://localhost:9090/docs"
        print_status ""
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
    print_header "🛑 Stopping Hybrid WhisperLive Server"
    
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
    print_header "📊 Hybrid WhisperLive Server Status"
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "✅ Server is running (PID: $pid)"
            
            # Check if server is listening
            if netstat -ln 2>/dev/null | grep -q ":9090 "; then
                print_status "🔗 Server listening on port 9090"
            else
                print_warning "Server port 9090 not found listening"
            fi
            
            # Show active sessions
            if command -v curl &> /dev/null; then
                print_status ""
                print_header "Active Sessions:"
                curl -s http://localhost:9090/sessions 2>/dev/null | python -m json.tool 2>/dev/null || print_warning "Could not fetch sessions"
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
    print_header "📋 Hybrid WhisperLive Server Logs"
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        print_warning "No log file found at $LOG_FILE"
    fi
}

# Function to test server
test_server() {
    print_header "🧪 Testing Hybrid WhisperLive Server"
    
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
    
    # Test REST API
    print_status "Testing REST API endpoint..."
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9090/)
    if [ "$response" = "200" ]; then
        print_status "✅ REST API is responding"
    else
        print_error "❌ REST API test failed (HTTP $response)"
    fi
    
    # Test WebSocket
    print_status "Testing WebSocket connection..."
    
    cd "$WHISPER_ROOT"
    
    "$VENV_PATH/bin/python" -c "
import asyncio
import websockets
import json
import uuid

async def test_connection():
    try:
        session_id = str(uuid.uuid4())
        uri = f'ws://localhost:9090/ws/{session_id}'
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
        echo "  start   - Start the Hybrid WhisperLive server"
        echo "  stop    - Stop the Hybrid WhisperLive server"
        echo "  restart - Restart the Hybrid WhisperLive server"
        echo "  status  - Check server status and active sessions"
        echo "  logs    - Show server logs"
        echo "  test    - Test REST API and WebSocket connections"
        exit 1
        ;;
esac
