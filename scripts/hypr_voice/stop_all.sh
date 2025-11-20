#!/bin/bash

# Stop all agent systems

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping all agents...${NC}"

# Function to stop agent
stop_agent() {
    local name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        PID=$(cat "$pid_file")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            echo -e "${GREEN}✓ Stopped $name (PID: $PID)${NC}"
        else
            echo -e "${YELLOW}$name was not running${NC}"
        fi
        rm "$pid_file"
    else
        echo -e "${YELLOW}No PID file for $name${NC}"
    fi
}

# Stop Claude SDK Agent
stop_agent "Claude SDK Agent" "$LOG_DIR/claude.pid"

# Stop LiteLLM Agent
stop_agent "LiteLLM Agent" "$LOG_DIR/litellm.pid"

# Also try to stop by port if PIDs not found
echo -e "${YELLOW}Checking for processes on ports...${NC}"

# Kill process on port 8922 (Claude SDK)
PID=$(lsof -ti:8922)
if [ ! -z "$PID" ]; then
    kill $PID
    echo -e "${GREEN}✓ Stopped process on port 8922${NC}"
fi

# Kill process on port 8001 (LiteLLM)
PID=$(lsof -ti:8001)
if [ ! -z "$PID" ]; then
    kill $PID
    echo -e "${GREEN}✓ Stopped process on port 8001${NC}"
fi

echo -e "${GREEN}All agents stopped${NC}"
