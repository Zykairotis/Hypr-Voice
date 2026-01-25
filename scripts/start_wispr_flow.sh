#!/bin/bash
# Wispr Flow API Server - Startup Script
# FastAPI service for Wispr Flow transcription

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🎙️  WISPR FLOW API SERVER${NC}"
echo -e "${BLUE}======================================${NC}"

# Default port (used for stop/status even if .env missing)
PORT=${WISPR_FLOW_PORT:-9095}

# Function to stop the server
stop_server() {
    echo -e "${YELLOW}Stopping Wispr Flow API server...${NC}"
    if [ -f "var/wispr_flow.pid" ]; then
        PID=$(cat var/wispr_flow.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            rm -f var/wispr_flow.pid
            echo -e "${GREEN}Server stopped${NC}"
        else
            rm -f var/wispr_flow.pid
            echo -e "${YELLOW}Server was not running${NC}"
        fi
    else
        # Try to find by port
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t 2>/dev/null | head -n 1)
            if [ -n "$PID" ]; then
                kill "$PID" 2>/dev/null || true
                echo -e "${GREEN}Server stopped (PID: $PID)${NC}"
            else
                echo -e "${YELLOW}No PID file found${NC}"
            fi
        else
            echo -e "${YELLOW}No PID file found${NC}"
        fi
    fi
    exit 0
}

# Handle command line arguments
case "${1:-start}" in
    start)
        # Check if .env exists
        if [ ! -f ".env" ]; then
            echo -e "${RED}Error: .env file not found${NC}"
            echo "Please create .env with Wispr Flow configuration"
            exit 1
        fi

        # Source environment variables (filter out comments)
        export $(grep -E '^WISPR_FLOW_[A-Z_]+=' .env | grep -v '#' | xargs)

        # Check required variables
        if [ -z "$WISPR_FLOW_JWT_TOKEN" ] || [ -z "$WISPR_FLOW_BASETEN_API_KEY" ]; then
            echo -e "${RED}Error: Required Wispr Flow environment variables not set${NC}"
            echo "Required: WISPR_FLOW_JWT_TOKEN, WISPR_FLOW_BASETEN_API_KEY, WISPR_FLOW_USER_UUID"
            exit 1
        fi

        # Update port after loading env
        PORT=${WISPR_FLOW_PORT:-9095}

        # Check if server is already running
        if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
            echo -e "${YELLOW}Server already running on port $PORT${NC}"
            echo "Stop it first with: $0 stop"
            exit 0
        fi

        # Create var directory
        mkdir -p var logs

        echo -e "${GREEN}Starting Wispr Flow API server...${NC}"
        echo -e "Port: ${BLUE}$PORT${NC}"
        echo -e "Logs: ${BLUE}logs/wispr_flow.log${NC}"
        echo ""

        # Start server in background
        nohup python3 src/hypr_voice/services/wispr_flow_server.py \
            > logs/wispr_flow.log 2>&1 &

        PID=$!
        echo $PID > var/wispr_flow.pid

        # Wait a moment for startup
        sleep 2

        if kill -0 $PID 2>/dev/null; then
            echo -e "${GREEN}✓ Server started successfully (PID: $PID)${NC}"
            echo ""
            echo -e "${BLUE}API Endpoints:${NC}"
            echo "   - http://localhost:$PORT/"
            echo "   - http://localhost:$PORT/docs (Swagger UI)"
            echo "   - http://localhost:$PORT/health"
            echo "   - http://localhost:$PORT/token"
            echo ""
            echo -e "${BLUE}WebSocket:${NC}"
            echo "   - ws://localhost:$PORT/ws/transcribe"
            echo ""
            echo "View logs: tail -f logs/wispr_flow.log"
            echo "Stop server: $0 stop"
        else
            echo -e "${RED}✗ Server failed to start${NC}"
            echo "Check logs: cat logs/wispr_flow.log"
            rm -f var/wispr_flow.pid
            exit 1
        fi
        ;;

    stop)
        stop_server
        ;;

    restart)
        stop_server
        sleep 1
        exec "$0" start
        ;;

    status)
        if [ -f "var/wispr_flow.pid" ]; then
            PID=$(cat var/wispr_flow.pid)
            if kill -0 $PID 2>/dev/null; then
                echo -e "${GREEN}Server is running (PID: $PID)${NC}"
                echo "Port: $PORT"
            else
                echo -e "${RED}Server is not running (stale PID file)${NC}"
                rm -f var/wispr_flow.pid
            fi
        else
            if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
                PID=$(lsof -Pi :$PORT -sTCP:LISTEN -t 2>/dev/null | head -n 1)
                echo -e "${GREEN}Server is running (PID: $PID)${NC}"
                echo "Port: $PORT"
            else
                echo -e "${YELLOW}Server is not running${NC}"
            fi
        fi
        ;;

    logs)
        if [ -f "logs/wispr_flow.log" ]; then
            tail -f logs/wispr_flow.log
        else
            echo -e "${YELLOW}No log file found${NC}"
        fi
        ;;

    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the Wispr Flow API server"
        echo "  stop    - Stop the server"
        echo "  restart - Restart the server"
        echo "  status  - Show server status"
        echo "  logs    - Tail the log file"
        exit 1
        ;;
esac
