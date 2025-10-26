#!/bin/bash

# Hypr-Voice Bridge Service Startup Script
# This script starts the FastAPI bridge service for Hypr-Voice control

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/src/api"
PYTHON_CMD="python3"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root (not recommended)
check_root_user() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root is not recommended for development"
        read -p "Do you want to continue? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Check Python installation
check_python() {
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python 3 is not installed or not in PATH"
        log_info "Please install Python 3.8 or higher"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    log_info "Found Python version: $PYTHON_VERSION"
}

# Check if virtual environment exists
check_venv() {
    if [[ -n "$VIRTUAL_ENV" ]]; then
        log_info "Already in virtual environment: $VIRTUAL_ENV"
        return 0
    fi

    # Check for venv in project
    if [[ -d "$PROJECT_ROOT/.venv" ]]; then
        log_info "Activating project virtual environment"
        source "$PROJECT_ROOT/.venv/bin/activate"
        return 0
    fi

    # Check for venv in API directory
    if [[ -d "$API_DIR/.venv" ]]; then
        log_info "Activating API virtual environment"
        source "$API_DIR/.venv/bin/activate"
        return 0
    fi

    log_warning "No virtual environment found"
    log_info "Consider creating one with: python3 -m venv .venv"
    return 1
}

# Install dependencies
install_dependencies() {
    log_info "Checking and installing dependencies..."

    cd "$API_DIR"

    if [[ -f "requirements.txt" ]]; then
        log_info "Installing from requirements.txt..."
        $PYTHON_CMD -m pip install -r requirements.txt
        log_success "Dependencies installed"
    else
        log_error "requirements.txt not found"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    directories=(
        "/tmp/hypr-voice-logs"
        "/tmp/hypr-voice-recordings"
    )

    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log_info "Created directory: $dir"
        fi
    done
}

# Check Hypr-Voice installation
check_hypr_voice() {
    log_info "Checking Hypr-Voice installation..."

    # Check for main script
    hypr_voice_script="$PROJECT_ROOT/hypr-voice/src/core/hypr_voice.py"
    if [[ -f "$hypr_voice_script" ]]; then
        log_success "Found Hypr-Voice script at: $hypr_voice_script"
        return 0
    fi

    # Check system installation
    if command -v hypr-voice &> /dev/null; then
        log_success "Found Hypr-Voice system installation"
        return 0
    fi

    log_warning "Hypr-Voice installation not found"
    log_info "The bridge service can run without Hypr-Voice, but functionality will be limited"
    return 1
}

# Start the bridge service
start_bridge() {
    log_info "Starting Hypr-Voice Bridge API service..."

    cd "$API_DIR"

    # Run the bridge service
    if [[ "$1" == "--check" ]]; then
        log_info "Running dependency check..."
        $PYTHON_CMD run_bridge.py --check
    elif [[ "$1" == "--dev" ]]; then
        log_info "Starting in development mode with auto-reload..."
        $PYTHON_CMD run_bridge.py --reload --log-level debug
    else
        log_info "Starting in production mode..."
        $PYTHON_CMD run_bridge.py
    fi
}

# Display usage information
show_usage() {
    echo "Hypr-Voice Bridge Service Startup Script"
    echo
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  --check     Check dependencies and exit"
    echo "  --dev       Start in development mode with auto-reload"
    echo "  --help      Show this help message"
    echo
    echo "Examples:"
    echo "  $0              # Start in production mode"
    echo "  $0 --dev        # Start in development mode"
    echo "  $0 --check      # Check dependencies only"
}

# Main function
main() {
    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --check)
            check_python
            check_venv || install_dependencies
            check_hypr_voice
            start_bridge --check
            exit 0
            ;;
        --dev)
            check_root_user
            check_python
            check_venv || install_dependencies
            create_directories
            check_hypr_voice
            start_bridge --dev
            ;;
        "")
            check_root_user
            check_python
            check_venv || install_dependencies
            create_directories
            check_hypr_voice
            start_bridge
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Trap signals for graceful shutdown
trap 'log_info "Shutting down..."; exit 0' SIGINT SIGTERM

# Run main function
main "$@"