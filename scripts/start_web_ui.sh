#!/bin/bash

# Hypr-Voice Web UI and API Bridge Startup Script
# This script starts both the API bridge service and web UI

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/src/api"
WEB_UI_DIR="$PROJECT_ROOT/web-ui"
VENV_PATH="$PROJECT_ROOT/hypr-voice/.venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
API_PORT=8435
WEB_UI_PORT=8345

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if ports are available
check_ports() {
    log_info "Checking port availability..."

    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "Port $API_PORT is already in use"
        return 1
    fi

    if lsof -Pi :$WEB_UI_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "Port $WEB_UI_PORT is already in use"
        return 1
    fi

    log_success "Ports are available"
}

# Check dependencies
check_dependencies() {
    log_info "Checking dependencies..."

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        return 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        return 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        return 1
    fi

    log_success "Dependencies are available"
}

# Install API dependencies
install_api_deps() {
    log_info "Installing API dependencies..."

    # Activate virtual environment
    if [[ -f "$VENV_PATH/bin/activate" ]]; then
        log_info "Activating virtual environment: $VENV_PATH"
        source "$VENV_PATH/bin/activate"
    else
        log_warning "Virtual environment not found at $VENV_PATH"
        log_info "Using system Python"
    fi

    cd "$API_DIR"
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "API dependencies installed"
    else
        log_error "API requirements.txt not found"
        return 1
    fi
}

# Install Web UI dependencies
install_webui_deps() {
    log_info "Installing Web UI dependencies..."

    cd "$WEB_UI_DIR"
    if [[ -f "package.json" ]]; then
        # Clear npm cache if needed
        npm cache clean --force 2>/dev/null || true

        # Try different npm installation methods
        if command -v yarn &> /dev/null; then
            log_info "Using yarn for installation"
            yarn install
        else
            log_info "Using npm for installation"
            npm install --legacy-peer-deps || npm install --force
        fi

        log_success "Web UI dependencies installed"
    else
        log_error "Web UI package.json not found"
        return 1
    fi
}

# Start API Bridge service
start_api() {
    log_info "Starting API Bridge service on port $API_PORT..."

    cd "$API_DIR"

    # Use virtual environment Python directly
    if [[ -f "$VENV_PATH/bin/python" ]]; then
        log_info "Using virtual environment Python: $VENV_PATH/bin/python"
        "$VENV_PATH/bin/python" run_bridge.py --port $API_PORT > /tmp/hypr-voice-api.log 2>&1 &
        API_PID=$!
    else
        log_warning "Virtual environment not found at $VENV_PATH/bin/python"
        log_info "Using system Python"
        python3 run_bridge.py --port $API_PORT > /tmp/hypr-voice-api.log 2>&1 &
        API_PID=$!
    fi

    # Wait a moment for startup
    sleep 3

    # Check if service is running
    if kill -0 $API_PID 2>/dev/null; then
        log_success "API Bridge service started (PID: $API_PID)"
        echo $API_PID > /tmp/hypr-voice-api.pid
        log_info "API Documentation: http://localhost:$API_PORT/docs"
    else
        log_error "API Bridge service failed to start"
        return 1
    fi
}

# Start Web UI
start_webui() {
    log_info "Starting Web UI on port $WEB_UI_PORT..."

    cd "$WEB_UI_DIR"

    # Start in background
    npm run dev > /tmp/hypr-voice-webui.log 2>&1 &
    WEB_UI_PID=$!

    # Wait a moment for startup
    sleep 5

    # Check if service is running
    if kill -0 $WEB_UI_PID 2>/dev/null; then
        log_success "Web UI started (PID: $WEB_UI_PID)"
        echo $WEB_UI_PID > /tmp/hypr-voice-webui.pid
        log_info "Web UI: http://localhost:$WEB_UI_PORT"
    else
        log_error "Web UI failed to start"
        return 1
    fi
}

# Stop services
stop_services() {
    log_info "Stopping services..."

    # Stop API
    if [[ -f "/tmp/hypr-voice-api.pid" ]]; then
        API_PID=$(cat /tmp/hypr-voice-api.pid)
        if kill -0 $API_PID 2>/dev/null; then
            kill $API_PID
            log_info "Stopped API Bridge service (PID: $API_PID)"
        fi
        rm -f /tmp/hypr-voice-api.pid
    fi

    # Stop Web UI
    if [[ -f "/tmp/hypr-voice-webui.pid" ]]; then
        WEB_UI_PID=$(cat /tmp/hypr-voice-webui.pid)
        if kill -0 $WEB_UI_PID 2>/dev/null; then
            kill $WEB_UI_PID
            log_info "Stopped Web UI (PID: $WEB_UI_PID)"
        fi
        rm -f /tmp/hypr-voice-webui.pid
    fi

    # Clean up any remaining processes
    pkill -f "run_bridge.py" 2>/dev/null || true
    pkill -f "next dev" 2>/dev/null || true

    log_success "All services stopped"
}

# Show status
show_status() {
    log_info "Checking service status..."

    # Check API
    if [[ -f "/tmp/hypr-voice-api.pid" ]]; then
        API_PID=$(cat /tmp/hypr-voice-api.pid)
        if kill -0 $API_PID 2>/dev/null; then
            log_success "API Bridge service: RUNNING (PID: $API_PID) - http://localhost:$API_PORT"
        else
            log_warning "API Bridge service: STOPPED (stale PID file)"
        fi
    else
        log_warning "API Bridge service: STOPPED"
    fi

    # Check Web UI
    if [[ -f "/tmp/hypr-voice-webui.pid" ]]; then
        WEB_UI_PID=$(cat /tmp/hypr-voice-webui.pid)
        if kill -0 $WEB_UI_PID 2>/dev/null; then
            log_success "Web UI: RUNNING (PID: $WEB_UI_PID) - http://localhost:$WEB_UI_PORT"
        else
            log_warning "Web UI: STOPPED (stale PID file)"
        fi
    else
        log_warning "Web UI: STOPPED"
    fi
}

# Show logs
show_logs() {
    echo "=== API Bridge Logs ==="
    if [[ -f "/tmp/hypr-voice-api.log" ]]; then
        tail -20 /tmp/hypr-voice-api.log
    else
        echo "No API logs found"
    fi

    echo ""
    echo "=== Web UI Logs ==="
    if [[ -f "/tmp/hypr-voice-webui.log" ]]; then
        tail -20 /tmp/hypr-voice-webui.log
    else
        echo "No Web UI logs found"
    fi
}

# Display usage information
show_usage() {
    echo "Hypr-Voice Web UI and API Bridge Startup Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  start       Start both services"
    echo "  stop        Stop both services"
    echo "  restart     Restart both services"
    echo "  status      Show service status"
    echo "  logs        Show recent logs"
    echo "  install     Install dependencies only"
    echo "  --help      Show this help message"
    echo
    echo "Service URLs:"
    echo "  Web UI:        http://localhost:$WEB_UI_PORT"
    echo "  API Bridge:    http://localhost:$API_PORT"
    echo "  API Docs:      http://localhost:$API_PORT/docs"
}

# Main function
main() {
    case "${1:-}" in
        start)
            check_ports || exit 1
            check_dependencies || exit 1
            install_api_deps || exit 1
            install_webui_deps || exit 1
            start_api || exit 1
            start_webui || exit 1
            log_success "All services started successfully!"
            echo ""
            echo "Access URLs:"
            echo "  Web UI:     http://localhost:$WEB_UI_PORT"
            echo "  API Bridge: http://localhost:$API_PORT"
            echo "  API Docs:   http://localhost:$API_PORT/docs"
            ;;
        stop)
            stop_services
            ;;
        restart)
            stop_services
            sleep 2
            main start
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        install)
            check_dependencies || exit 1
            install_api_deps || exit 1
            install_webui_deps || exit 1
            log_success "Dependencies installed successfully!"
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        "")
            show_usage
            exit 1
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Trap signals for graceful shutdown
trap 'log_info "Interrupted. Stopping services..."; stop_services; exit 0' SIGINT SIGTERM

# Run main function
main "$@"