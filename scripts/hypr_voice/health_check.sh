#!/bin/bash

# Health check script for Multi-Agent Orchestration System

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "===================================="
echo "  Agent System Health Check"
echo "===================================="
echo

# Check API
echo -n "API Endpoint: "
if curl -s http://localhost:8922/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Healthy${NC}"
    HEALTH_DATA=$(curl -s http://localhost:8922/health)
    echo "  Agents: $(echo $HEALTH_DATA | jq -r '.agents_count')"
    echo "  Status: $(echo $HEALTH_DATA | jq -r '.status')"
else
    echo -e "${RED}✗ Unreachable${NC}"
fi

# Check WebSocket
echo -n "WebSocket: "
if timeout 2 bash -c '</dev/tcp/localhost/8922' 2>/dev/null; then
    echo -e "${GREEN}✓ Available${NC}"
else
    echo -e "${RED}✗ Unavailable${NC}"
fi

# Check PostgreSQL
echo -n "PostgreSQL: "
if pg_isready -h localhost -U agent > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check Redis
echo -n "Redis: "
if redis-cli ping > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Running${NC}"
    echo "  Keys: $(redis-cli dbsize | cut -d' ' -f2)"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check MCP Servers
echo -n "MCP Servers: "
MCP_COUNT=$(curl -s http://localhost:8922/mcp/presets | jq '.presets | length' 2>/dev/null || echo 0)
echo -e "${GREEN}$MCP_COUNT available${NC}"

# Check disk space
echo -n "Disk Space: "
DISK_USAGE=$(df -h /var/lib/agent-system | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ ${DISK_USAGE}% used${NC}"
elif [ "$DISK_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠ ${DISK_USAGE}% used${NC}"
else
    echo -e "${RED}✗ ${DISK_USAGE}% used${NC}"
fi

# Check memory
echo -n "Memory: "
MEM_USAGE=$(free | grep Mem | awk '{print int($3/$2 * 100)}')
if [ "$MEM_USAGE" -lt 80 ]; then
    echo -e "${GREEN}✓ ${MEM_USAGE}% used${NC}"
elif [ "$MEM_USAGE" -lt 90 ]; then
    echo -e "${YELLOW}⚠ ${MEM_USAGE}% used${NC}"
else
    echo -e "${RED}✗ ${MEM_USAGE}% used${NC}"
fi

echo
echo "===================================="
