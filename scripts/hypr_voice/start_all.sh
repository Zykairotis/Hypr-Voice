#!/bin/bash

# Start both agent systems

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================${NC}"
echo -e "${BLUE}  Hypr-Voice Agent System Launcher  ${NC}"
echo -e "${BLUE}====================================${NC}"
echo

# Function to start agent in background
start_agent() {
    local name=$1
    local script=$2
    local log_file=$3
    
    echo -e "${YELLOW}Starting $name...${NC}"
    nohup bash "$script" > "$log_file" 2>&1 &
    local pid=$!
    sleep 2
    
    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✓ $name started (PID: $pid)${NC}"
        echo $pid
    else
        echo -e "${RED}✗ Failed to start $name${NC}"
        cat "$log_file"
        echo 0
    fi
}

# Create log directory
LOG_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOG_DIR"

# Start Claude SDK Agent
CLAUDE_PID=$(start_agent "Claude SDK Agent" "$SCRIPT_DIR/start_claude_sdk.sh" "$LOG_DIR/claude-sdk.log")

# Start LiteLLM Agent
LITELLM_PID=$(start_agent "LiteLLM Agent" "$SCRIPT_DIR/start_litellm.sh" "$LOG_DIR/litellm.log")

# Save PIDs for later shutdown
echo "$CLAUDE_PID" > "$LOG_DIR/claude.pid"
echo "$LITELLM_PID" > "$LOG_DIR/litellm.pid"

echo
echo -e "${GREEN}Both agents are starting...${NC}"
echo
echo "Claude SDK Agent: http://localhost:8922"
echo "LiteLLM Agent:    http://localhost:8001"
echo
echo "API Documentation:"
echo "  Claude SDK: http://localhost:8922/docs"
echo "  LiteLLM:    http://localhost:8001/docs"
echo
echo -e "${YELLOW}To stop agents, run: $SCRIPT_DIR/stop_all.sh${NC}"
echo
echo "Logs:"
echo "  Claude SDK: $LOG_DIR/claude-sdk.log"
echo "  LiteLLM:    $LOG_DIR/litellm.log"
