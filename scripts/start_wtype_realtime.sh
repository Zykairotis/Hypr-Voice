#!/bin/bash
# Quick start script for wtype integration - Real-time mode

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}⌨️  Starting ydotool Real-Time Auto-Typing${NC}"
echo ""

# Check if venv exists
if [ ! -d "$VENV_PATH" ] || [ ! -f "$VENV_PATH/bin/python" ]; then
    echo -e "${RED}[ERROR]${NC} Virtual environment not found at $VENV_PATH"
    exit 1
fi

# Check if ydotool is installed
if ! command -v ydotool &> /dev/null; then
    echo -e "${RED}[ERROR]${NC} ydotool not found!"
    echo -e "${YELLOW}[INFO]${NC} Install with: sudo pacman -S ydotool (Arch) or build from source"
    exit 1
fi

# Check if server is running
if ! curl -s http://localhost:9099/health > /dev/null 2>&1; then
    echo -e "${YELLOW}[WARN]${NC} Server not responding at http://localhost:9099"
    echo -e "${YELLOW}[INFO]${NC} Start server with: ./scripts/start_hybrid_server.sh"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Run from project root for module imports
cd "$PROJECT_ROOT"
export PYTHONPATH="$PROJECT_ROOT/src:$PYTHONPATH"

echo -e "${GREEN}[INFO]${NC} Audio device: Auto-detected from audio-profile.yaml"
echo -e "${GREEN}[INFO]${NC} Server: http://localhost:9099"
echo -e "${GREEN}[INFO]${NC} Mode: Real-time auto-typing"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC}"
echo -e "  1. Click in a text field (Google Docs, Discord, etc.)"
echo -e "  2. Keep that window focused"
echo -e "  3. Speak into microphone"
echo -e "  4. Watch text appear automatically!"
echo ""
echo -e "${BLUE}Press Ctrl+C to stop${NC}"
echo ""

# Run with auto-detected device - run as module
"$VENV_PATH/bin/python" -m hypr_voice.whisper.integration.wltype_integration --realtime
