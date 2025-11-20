# 🔧 Troubleshooting Guide

## Common Issues and Solutions

### 🔴 Service Won't Start

#### Problem: Port already in use
```bash
Error: [Errno 98] Address already in use
```

**Solution:**
```bash
# Find process using port 8922
lsof -i:8922

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn orchestrator:app --port 8001
```

#### Problem: Virtual environment not found
```bash
Error: Virtual environment not found at /home/mewtwo/Zykairotis/Hypr-Voice/.venv
```

**Solution:**
```bash
# Create virtual environment
python -m venv /home/mewtwo/Zykairotis/Hypr-Voice/.venv

# Activate and install dependencies
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
pip install -r requirements.txt
```

#### Problem: Module not found
```bash
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate

# Install missing module
pip install fastapi uvicorn
```

### 🔴 WebSocket Connection Issues

#### Problem: WebSocket connection refused
```javascript
WebSocket connection to 'ws://localhost:8922/ws/client-id' failed
```

**Solution:**
1. Check if service is running: `curl http://localhost:8922/health`
2. Check CORS settings in orchestrator.py
3. Ensure firewall allows WebSocket connections
4. Try using `127.0.0.1` instead of `localhost`

#### Problem: WebSocket disconnects frequently

**Solution:**
```python
# Increase ping interval in config
websocket:
  ping_interval: 60  # Increase from 30
  ping_timeout: 20   # Increase from 10
```

### 🔴 Agent Execution Errors

#### Problem: Agent crashes with "API key not found"
```
Error: ANTHROPIC_API_KEY not set
```

**Solution:**
```bash
# Set in .env file
echo "ANTHROPIC_API_KEY=your-key-here" >> .env

# Or export directly
export ANTHROPIC_API_KEY="your-key-here"

# Or use mock mode
MOCK_MODE=true python orchestrator.py
```

#### Problem: Agent can't write files
```
PermissionError: [Errno 13] Permission denied: '/tmp/agents/file.txt'
```

**Solution:**
```bash
# Fix permissions
chmod 755 /tmp/agents
chown -R $(whoami) /tmp/agents

# Or use different directory
config.working_directory = "/home/user/agents"
```

#### Problem: Subprocess execution fails
```
subprocess.CalledProcessError: Command 'ls' returned non-zero exit status 1
```

**Solution:**
```python
# Add error handling
try:
    result = await subprocess.run(cmd, check=True)
except subprocess.CalledProcessError as e:
    print(f"Command failed: {e.stderr}")
```

### 🔴 MCP Server Issues

#### Problem: MCP server not found
```
Error: MCP server 'filesystem' not found
```

**Solution:**
```bash
# Install MCP server
npm install -g @modelcontextprotocol/server-filesystem

# Check installation
npm list -g @modelcontextprotocol/server-filesystem
```

#### Problem: MCP server timeout
```
TimeoutError: MCP server initialization timeout
```

**Solution:**
```python
# Increase timeout in config
mcp_servers:
  filesystem:
    timeout: 60  # Increase from 30
```

### 🔴 Database Issues

#### Problem: Cannot connect to PostgreSQL
```
psycopg2.OperationalError: could not connect to server
```

**Solution:**
```bash
# Check if PostgreSQL is running
systemctl status postgresql

# Start PostgreSQL
systemctl start postgresql

# Check connection
psql -U agent -d agent_db -h localhost
```

#### Problem: Redis connection refused
```
redis.exceptions.ConnectionError: Connection refused
```

**Solution:**
```bash
# Start Redis
redis-server --daemonize yes

# Check if running
redis-cli ping
```

### 🔴 Voice Synthesis Issues

#### Problem: Kokoro TTS not available
```
ImportError: No module named 'kokoro_onnx'
```

**Solution:**
```bash
# Voice synthesis will work in mock mode
# To enable real synthesis, install Kokoro:
pip install kokoro-onnx

# Or disable voice in config
config.enable_voice = False
```

#### Problem: Audio file not created
```
FileNotFoundError: [Errno 2] No such file or directory: 'audio.wav'
```

**Solution:**
```bash
# Check directory permissions
ls -la /tmp/kokoro_cache

# Create directory if missing
mkdir -p /tmp/kokoro_cache
chmod 755 /tmp/kokoro_cache
```

### 🔴 Performance Issues

#### Problem: Slow response times

**Solution:**
1. Check system resources: `htop`
2. Increase workers: `--workers 4`
3. Enable caching in config
4. Check database queries
5. Profile code: `python -m cProfile orchestrator.py`

#### Problem: High memory usage

**Solution:**
```python
# Limit agent count
limits:
  max_agents: 10
  max_conversation_length: 50

# Clear old agents periodically
async def cleanup_agents():
    for agent_id in list(orchestrator.agents.keys()):
        if agent_is_old(agent_id):
            orchestrator.delete_agent(agent_id)
```

### 🔴 Docker Issues

#### Problem: Container won't start
```
docker: Error response from daemon: Conflict
```

**Solution:**
```bash
# Remove old container
docker rm -f agent-orchestrator

# Rebuild image
docker-compose build --no-cache

# Start fresh
docker-compose up -d
```

#### Problem: Can't access service from host
```
curl: (7) Failed to connect to localhost port 8922
```

**Solution:**
```yaml
# Check docker-compose.yml ports
ports:
  - "8922:8922"  # host:container

# Check container is running
docker ps

# Check logs
docker logs agent-orchestrator
```

## Debug Commands

### Check Service Status
```bash
# System service
systemctl status agent-orchestrator

# Docker
docker ps
docker logs agent-orchestrator

# Process
ps aux | grep orchestrator
```

### View Logs
```bash
# Tail logs
tail -f logs/orchestrator.log

# Search for errors
grep ERROR logs/orchestrator.log

# Docker logs
docker logs -f agent-orchestrator
```

### Test Endpoints
```bash
# Health check
curl http://localhost:8922/health

# Create agent
curl -X POST http://localhost:8922/agents/create \
  -H "Content-Type: application/json" \
  -d '{"name":"test","working_directory":"/tmp/test"}'

# WebSocket test
websocat ws://localhost:8922/ws/test-client
```

### Resource Monitoring
```bash
# CPU and memory
htop

# Disk usage
df -h

# Network connections
netstat -tulpn | grep 8922

# Process details
lsof -p $(pgrep -f orchestrator)
```

## Getting Help

### Log Files
- Orchestrator: `logs/orchestrator.log`
- Redis: `logs/redis.log`
- System: `journalctl -u agent-orchestrator`

### Debug Mode
```bash
# Enable debug logging
LOG_LEVEL=DEBUG python orchestrator.py

# Verbose output
python orchestrator.py --verbose
```

### Community Support
- GitHub Issues: [Report bugs](https://github.com/yourusername/agent-system)
- Discord: [Join community](https://discord.gg/yourinvite)
- Documentation: [Read the docs](https://docs.yoursite.com)

## Emergency Recovery

### Full System Reset
```bash
#!/bin/bash
# Stop all services
systemctl stop agent-orchestrator
pkill -f orchestrator

# Clear data
rm -rf /tmp/agents/*
redis-cli FLUSHALL

# Restart
systemctl start agent-orchestrator
```

### Backup Restore
```bash
# Restore from backup
./scripts/restore_backup.sh /backup/agent_backup_20240101_120000

# Verify
curl http://localhost:8922/health
```
