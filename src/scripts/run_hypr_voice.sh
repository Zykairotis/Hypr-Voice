#!/bin/bash
# Unified launcher for Hypr-Voice (Server + Client)
# Optimized for raw transcription with large-v3-turbo on CUDA GPU (RTX 3080)

set -e

# NVIDIA GPU Optimization (RTX 3080 10GB)
export CUDA_VISIBLE_DEVICES=0                    # Use first GPU
export CUDA_LAUNCH_BLOCKING=0                    # Async kernel launches for speed
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512  # Better memory management

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_ROOT="/home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice"
VENV_PATH="$PROJECT_ROOT/.venv"
SERVER_SCRIPT="$PROJECT_ROOT/whisper_server.py"
CLIENT_SCRIPT="$PROJECT_ROOT/hypr_voice.py"
SERVER_PID_FILE="/tmp/hypr-voice-server.pid"
CLIENT_PID_FILE="/tmp/hypr-voice-client.pid"
SERVER_LOG="/tmp/hypr-voice-server.log"
CLIENT_LOG="/tmp/hypr-voice-client.log"

# Configuration
WHISPER_MODEL="large-v3-turbo"  # Optimized model (~1.5GB VRAM with int8)
WHISPER_DEVICE="cuda"           # Use NVIDIA GPU (RTX 3080) - 10-30x faster than CPU
WHISPER_COMPUTE_TYPE="int8"     # Lower VRAM usage (~1.5GB vs 2.5GB float16)
WHISPER_PORT="9880"
RAW_MODE=true  # Set to false for LLM enhancement

# Function to print colored messages
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to activate virtual environment
activate_venv() {
    if [[ -d "$VENV_PATH" ]]; then
        info "Activating virtual environment..."
        source "$VENV_PATH/bin/activate"
        success "Virtual environment activated"
    else
        warning "No virtual environment found at $VENV_PATH"
        warning "Using system Python"
    fi
}

# Function to check if server is running
is_server_running() {
    if [[ -f "$SERVER_PID_FILE" ]]; then
        PID=$(cat "$SERVER_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi
    
    # Also check by port
    if curl -s http://localhost:$WHISPER_PORT/ &>/dev/null; then
        return 0
    fi
    
    return 1
}

# Function to check if client is running
is_client_running() {
    if [[ -f "$CLIENT_PID_FILE" ]]; then
        PID=$(cat "$CLIENT_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to start Whisper server
start_server() {
    if is_server_running; then
        warning "Whisper server is already running"
        return 0
    fi
    
    info "Starting Whisper server..."
    info "Model: $WHISPER_MODEL | Device: $WHISPER_DEVICE | Port: $WHISPER_PORT"
    
    cd "$PROJECT_ROOT"
    
    # Build server command
    SERVER_CMD="python3 $SERVER_SCRIPT --model $WHISPER_MODEL --device $WHISPER_DEVICE --compute-type $WHISPER_COMPUTE_TYPE --port $WHISPER_PORT"
    
    # Add flags for raw transcription mode
    if [[ "$RAW_MODE" == true ]]; then
        SERVER_CMD="$SERVER_CMD --clean"
    fi
    
    # Start server in background
    nohup $SERVER_CMD > "$SERVER_LOG" 2>&1 &
    SERVER_PID=$!
    echo $SERVER_PID > "$SERVER_PID_FILE"
    
    info "Server PID: $SERVER_PID"
    info "Server log: $SERVER_LOG"
    
    # Wait for server to be ready (max 30 seconds)
    info "Waiting for server to initialize..."
    for i in {1..30}; do
        if curl -s http://localhost:$WHISPER_PORT/ &>/dev/null; then
            success "Whisper server is ready!"
            return 0
        fi
        sleep 1
        echo -n "."
    done
    
    error "Server failed to start within 30 seconds"
    error "Check log: $SERVER_LOG"
    return 1
}

# Function to start client
start_client() {
    if is_client_running; then
        warning "Client is already running"
        return 0
    fi
    
    if ! is_server_running; then
        error "Server is not running. Start server first."
        return 1
    fi
    
    info "Starting Hypr-Voice client..."
    
    cd "$PROJECT_ROOT"
    
    # Build client command
    CLIENT_CMD="python3 $CLIENT_SCRIPT"
    
    # Note: Client runs in foreground, controlled via socket
    
    # Start client in background
    nohup $CLIENT_CMD > "$CLIENT_LOG" 2>&1 &
    CLIENT_PID=$!
    echo $CLIENT_PID > "$CLIENT_PID_FILE"
    
    info "Client PID: $CLIENT_PID"
    info "Client log: $CLIENT_LOG"
    
    # Wait a bit for client to initialize
    sleep 2
    
    if kill -0 "$CLIENT_PID" 2>/dev/null; then
        success "Client is running!"
        success "Use keybinds in Hyprland to control recording"
        return 0
    else
        error "Client failed to start"
        error "Check log: $CLIENT_LOG"
        return 1
    fi
}

# Function to stop server
stop_server() {
    if [[ -f "$SERVER_PID_FILE" ]]; then
        PID=$(cat "$SERVER_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            info "Stopping server (PID: $PID)..."
            kill "$PID"
            rm -f "$SERVER_PID_FILE"
            success "Server stopped"
        else
            warning "Server PID file exists but process not running"
            rm -f "$SERVER_PID_FILE"
        fi
    else
        warning "Server not running (no PID file)"
    fi
}

# Function to stop client
stop_client() {
    if [[ -f "$CLIENT_PID_FILE" ]]; then
        PID=$(cat "$CLIENT_PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            info "Stopping client (PID: $PID)..."
            kill "$PID"
            rm -f "$CLIENT_PID_FILE"
            success "Client stopped"
        else
            warning "Client PID file exists but process not running"
            rm -f "$CLIENT_PID_FILE"
        fi
    else
        warning "Client not running (no PID file)"
    fi
    
    # Clean up socket
    if [[ -S "/tmp/hypr-voice.sock" ]]; then
        rm -f "/tmp/hypr-voice.sock"
    fi
}

# Function to show status
show_status() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}      Hypr-Voice Status Report         ${NC}"
    echo -e "${BLUE}========================================${NC}\n"
    
    # Server status
    if is_server_running; then
        echo -e "Whisper Server: ${GREEN}RUNNING${NC}"
        if [[ -f "$SERVER_PID_FILE" ]]; then
            echo "  PID: $(cat $SERVER_PID_FILE)"
        fi
        echo "  Port: $WHISPER_PORT"
        echo "  Log: $SERVER_LOG"
    else
        echo -e "Whisper Server: ${RED}STOPPED${NC}"
    fi
    
    echo ""
    
    # Client status
    if is_client_running; then
        echo -e "Hypr-Voice Client: ${GREEN}RUNNING${NC}"
        if [[ -f "$CLIENT_PID_FILE" ]]; then
            echo "  PID: $(cat $CLIENT_PID_FILE)"
        fi
        echo "  Log: $CLIENT_LOG"
        
        # Check socket
        if [[ -S "/tmp/hypr-voice.sock" ]]; then
            echo -e "  Socket: ${GREEN}ACTIVE${NC}"
        else
            echo -e "  Socket: ${YELLOW}NOT FOUND${NC}"
        fi
    else
        echo -e "Hypr-Voice Client: ${RED}STOPPED${NC}"
    fi
    
    echo ""
}

# Function to show logs
show_logs() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}      Recent Logs (last 20 lines)      ${NC}"
    echo -e "${BLUE}========================================${NC}\n"
    
    if [[ -f "$SERVER_LOG" ]]; then
        echo -e "${GREEN}[Server Log]${NC}"
        tail -n 20 "$SERVER_LOG"
        echo ""
    fi
    
    if [[ -f "$CLIENT_LOG" ]]; then
        echo -e "${GREEN}[Client Log]${NC}"
        tail -n 20 "$CLIENT_LOG"
    fi
}

# Main command dispatcher
case "${1:-start}" in
    start)
        activate_venv
        start_server
        sleep 2
        start_client
        show_status
        ;;
    
    stop)
        stop_client
        stop_server
        success "All services stopped"
        ;;
    
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    
    server)
        activate_venv
        start_server
        show_status
        ;;
    
    client)
        activate_venv
        start_client
        show_status
        ;;
    
    status)
        show_status
        ;;
    
    logs)
        show_logs
        ;;
    
    foreground|fg)
        echo -e "${BLUE}========================================${NC}"
        echo -e "${BLUE}  Starting Hypr-Voice in Foreground   ${NC}"
        echo -e "${BLUE}  Press Ctrl+C to stop                ${NC}"
        echo -e "${BLUE}========================================${NC}"
        echo ""
        
        activate_venv
        stop_server
        stop_client
        
        # Clean up on exit
        trap "echo ''; info 'Stopping services...'; stop_server; stop_client; exit 0" INT TERM
        
        info "Starting Whisper server..."
        python3 "$SERVER_SCRIPT" \
            --model "$WHISPER_MODEL" \
            --device "$WHISPER_DEVICE" \
            --port "$WHISPER_PORT" &
        SERVER_PID=$!
        echo $SERVER_PID > "$SERVER_PID_FILE"
        
        sleep 3
        
        info "Starting Hypr-Voice client..."
        python3 "$CLIENT_SCRIPT"
        ;;
    
    *)
        echo "Usage: $0 {start|stop|restart|server|client|status|logs|foreground}"
        echo ""
        echo "Commands:"
        echo "  start      - Start both server and client in background"
        echo "  stop       - Stop both server and client"
        echo "  restart    - Restart both services"
        echo "  server     - Start only the server"
        echo "  client     - Start only the client"
        echo "  status     - Show current status"
        echo "  logs       - Show recent logs"
        echo "  foreground - Run with real-time logging (Ctrl+C to stop)"
        exit 1
        ;;
esac
