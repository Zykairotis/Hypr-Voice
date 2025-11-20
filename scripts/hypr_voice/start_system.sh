#!/bin/bash

# =============================================================================
# Multi-Agent Orchestration System - Startup Script (Non-Docker)
# =============================================================================

# Use Hypr-Voice virtual environment
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
STATE_DIR="$PROJECT_ROOT/var/hypr_voice"
LOG_DIR="$STATE_DIR/logs/startup"
SESSION_DIR="$STATE_DIR/sessions"
DATA_DIR="$STATE_DIR/data"
REQUIREMENTS_FILE="$PROJECT_ROOT/requirements/hypr_voice.txt"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}==============================================================================${NC}"
echo -e "${CYAN}    🚀 Agent Orchestration System Startup${NC}"
echo -e "${CYAN}==============================================================================${NC}"
echo

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}Error: Virtual environment not found at $VENV_PATH${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source "$VENV_PATH/bin/activate"

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p "$LOG_DIR"
mkdir -p "$SESSION_DIR"
mkdir -p "$DATA_DIR"

# Check for .env file
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cat > "$SCRIPT_DIR/.env" <<EOF
# API Keys (add your keys here)
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
GITHUB_TOKEN=
BRAVE_API_KEY=

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8922
LOG_LEVEL=INFO

# Features
ENABLE_VOICE=true
ENABLE_MCP=true
MOCK_MODE=false
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit .env to add your API keys${NC}"
fi

# Load environment variables
if [ -f "$SCRIPT_DIR/.env" ]; then
    export $(cat "$SCRIPT_DIR/.env" | grep -v '^#' | xargs)
fi

# Install dependencies if needed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    if [ -f "$REQUIREMENTS_FILE" ]; then
        pip install -r "$REQUIREMENTS_FILE"
    else
        echo -e "${YELLOW}⚠️ Requirements file not found at $REQUIREMENTS_FILE${NC}"
    fi
fi

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Check if services are already running
if check_port 8922; then
    echo -e "${YELLOW}⚠ Port 8922 is already in use${NC}"
    echo -n "Stop existing service? (y/n): "
    read -r response
    if [[ "$response" == "y" ]]; then
        echo -e "${YELLOW}Stopping existing services...${NC}"
        pkill -f "uvicorn orchestrator:app"
        sleep 2
    else
        echo -e "${RED}Cannot start: port 8922 is occupied${NC}"
        exit 1
    fi
fi

# Optional: Check for additional services
# (Add any service checks here if needed)

# Start the orchestrator
echo
echo -e "${CYAN}Starting Multi-Agent Orchestrator...${NC}"

# Create startup command
STARTUP_CMD="python -m uvicorn orchestrator:app \
    --host 0.0.0.0 \
    --port 8922 \
    --reload \
    --log-level info"

# Start in background with logging
echo -e "${YELLOW}Starting orchestrator on port 8922...${NC}"
nohup $STARTUP_CMD > "$LOG_DIR/orchestrator.log" 2>&1 &
ORCHESTRATOR_PID=$!

# Save PID
echo $ORCHESTRATOR_PID > "$LOG_DIR/orchestrator.pid"

# Wait for service to start
echo -n "Waiting for service to start"
for i in {1..10}; do
    sleep 1
    echo -n "."
    if curl -s http://localhost:8922/health >/dev/null 2>&1; then
        echo -e " ${GREEN}✓${NC}"
        break
    fi
done

# Check if service started successfully
if curl -s http://localhost:8922/health >/dev/null 2>&1; then
    echo
    echo -e "${GREEN}==============================================================================${NC}"
    echo -e "${GREEN}    ✓ System Started Successfully!${NC}"
    echo -e "${GREEN}==============================================================================${NC}"
    echo
    echo -e "${CYAN}Service URLs:${NC}"
    echo -e "  API Endpoint: ${YELLOW}http://localhost:8922${NC}"
    echo -e "  API Documentation: ${YELLOW}http://localhost:8922/docs${NC}"
    echo -e "  WebSocket: ${YELLOW}ws://localhost:8922/ws/{client_id}${NC}"
    echo
    echo -e "${CYAN}Quick Test:${NC}"
    echo -e "  ${YELLOW}python examples.py quickstart${NC}"
    echo
    echo -e "${CYAN}Interactive CLI:${NC}"
    echo -e "  ${YELLOW}python client.py${NC}"
    echo
    echo -e "${CYAN}Logs:${NC}"
    echo -e "  Orchestrator: ${YELLOW}$LOG_DIR/orchestrator.log${NC}"
    echo -e "  Redis: ${YELLOW}$LOG_DIR/redis.log${NC}"
    echo
    echo -e "${CYAN}Stop System:${NC}"
    echo -e "  ${YELLOW}$SCRIPT_DIR/scripts/stop_all.sh${NC}"
    echo
    
    # Show health status
    echo -e "${CYAN}System Health:${NC}"
    curl -s http://localhost:8922/health | python -m json.tool
    
else
    echo
    echo -e "${RED}✗ Failed to start orchestrator${NC}"
    echo -e "Check logs at: ${YELLOW}$LOG_DIR/orchestrator.log${NC}"
    tail -20 "$LOG_DIR/orchestrator.log"
    exit 1
fi

# Optional: Start monitoring in new terminal
echo
echo -n "Start real-time monitoring? (y/n): "
read -r response
if [[ "$response" == "y" ]]; then
    echo -e "${YELLOW}Starting monitor...${NC}"
    python client.py &
fi
