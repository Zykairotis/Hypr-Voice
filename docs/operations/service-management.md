# Service Management - Hypr-Voice

Complete guide for managing Hypr-Voice services including startup, shutdown, restart, and monitoring.

## Table of Contents

1. [Service Overview](#service-overview)
2. [Starting Services](#starting-services)
3. [Stopping Services](#stopping-services)
4. [Restarting Services](#restarting-services)
5. [Service Status](#service-status)
6. [Systemd Integration](#systemd-integration)
7. [Process Management](#process-management)
8. [Service Dependencies](#service-dependencies)
9. [Auto-Start Configuration](#auto-start-configuration)
10. [Troubleshooting Services](#troubleshooting-services)

---

## Service Overview

### Core Services

| Service | Port | Script | PID File | Log File |
|---------|------|--------|----------|----------|
| **Hybrid Whisper** | 9099 | `start_hybrid_server.sh` | `/tmp/hybrid-whisper-server.pid` | `/tmp/hybrid-whisper-server.log` |
| **Orchestrator** | 9093 | `start_everything.sh` | `/tmp/hypr-voice-orchestrator.pid` | `/tmp/hypr-voice-orchestrator.log` |
| **Context WS** | 9091 | `start_everything.sh` | `/tmp/hypr-voice-context-ws.pid` | `/tmp/hypr-voice-context-ws.log` |
| **Wispr Flow** | 9095 | `start_wispr_flow.sh` | `var/wispr_flow.pid` | `logs/wispr_flow.log` |
| **Web UI** | 8933/8934 | `start_everything.sh` | `/tmp/hypr-voice-ui-wrapper.pid` | `/tmp/hypr-voice-ui.log` |

### Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Hypr-Voice Stack                      │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ Web UI (8933)│──│Bridge (8934) │──│Context (9091)│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                           │                              │
│                  ┌────────┴────────┐                     │
│                  │                 │                     │
│           ┌──────▼──────┐   ┌─────▼──────┐              │
│           │ Orchestrator│   │Hybrid(9099)│              │
│           │   (9093)    │   │            │              │
│           └──────┬──────┘   └─────┬──────┘              │
│                  │                │                      │
│                  └────────┬───────┘                      │
│                           │                              │
│                    ┌──────▼──────┐                      │
│                    │ Wispr Flow  │                      │
│                    │   (9095)    │                      │
│                    └─────────────┘                      │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## Starting Services

### Quick Start - All Services

#### Method 1: Using start_everything.sh (Recommended)

```bash
# Start all services at once
./scripts/start_everything.sh start

# Output:
# [start-all] Loaded .env file (MODE=FLOW)
# [start-all] Starting hybrid server (9099)...
# [start-all] Starting context_websocket_server.py (9091)...
# [start-all] Starting Agent Orchestrator (9093)...
# [start-all] Starting web UI + bridge (8933/8934)...
# [start-all] All services started.
```

**Services Started:**
- ✅ Hybrid Whisper Server (9099)
- ✅ Context WebSocket (9091)
- ✅ Agent Orchestrator (9093)
- ✅ Web UI + Bridge (8933/8934)
- ✅ Wispr Flow API (9095) - if `MODE=FLOW`

#### Method 2: Individual Services

```bash
# 1. Start Hybrid Whisper Server
./scripts/start_hybrid_server.sh start

# 2. Start Orchestrator (includes Context WS)
# (included in start_everything.sh)

# 3. Start Wispr Flow (if using MODE=FLOW)
./scripts/start_wispr_flow.sh start

# 4. Start Web UI (optional)
cd web-ui && npm start
```

### Starting Individual Services

#### Hybrid Whisper Server

```bash
# Start the hybrid server
./scripts/start_hybrid_server.sh start

# Expected output:
# 🚀 Starting Hybrid WhisperLive Server
# Configuration: /path/to/config/hypr_voice/whisper/config.yaml
# Log file: /tmp/hybrid-whisper-server.log
# Virtual Environment: /path/to/.venv
# Starting hybrid server...
# ✅ Server started successfully (PID: 12345)
# 📍 Endpoints:
# 🔗 WebSocket: ws://localhost:9099/ws/{session_id}
# 🌐 REST API: http://localhost:9099
# 📚 API Docs: http://localhost:9099/docs
# 📋 Logs: tail -f /tmp/hybrid-whisper-server.log
```

#### Wispr Flow API Server

```bash
# Start Wispr Flow API
./scripts/start_wispr_flow.sh start

# Expected output:
# 🎙️  WISPR FLOW API SERVER
# ======================================
# Starting Wispr Flow API server...
# Port: 9095
# Logs: logs/wispr_flow.log
# ✓ Server started successfully (PID: 12346)
# API Endpoints:
#    - http://localhost:9095/
#    - http://localhost:9095/docs (Swagger UI)
#    - http://localhost:9095/health
#    - http://localhost:9095/token
# WebSocket:
#    - ws://localhost:9095/ws/transcribe
```

#### Context WebSocket

```bash
# Started automatically by start_everything.sh
# Or manually:

# Ensure venv is activated
source .venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH="/path/to/hypr-voice/src:$PYTHONPATH"

# Start context server
nohup python src/hypr_voice/whisper/context/context_websocket_server.py \
    > /tmp/hypr-voice-context-ws.log 2>&1 &

# Save PID
echo $! > /tmp/hypr-voice-context-ws.pid
```

#### Agent Orchestrator

```bash
# Started automatically by start_everything.sh
# Or manually:

# Load environment
source .env

# Start orchestrator
export PYTHONPATH="/path/to/hypr-voice/src"
nohup /path/to/python -c "
import uvicorn
import sys
sys.path.insert(0, '/path/to/hypr-voice/src')
from hypr_voice.server import app
uvicorn.run(app, host='0.0.0.0', port=9093, log_level='info')
" > /tmp/hypr-voice-orchestrator.log 2>&1 &

# Save PID
echo $! > /tmp/hypr-voice-orchestrator.pid
```

### Verification After Start

```bash
# Check all services
./scripts/start_everything.sh status

# Or check individually
curl http://localhost:9099/health  # Hybrid server
curl http://localhost:9093/health  # Orchestrator
curl http://localhost:9091/health  # Context WS
curl http://localhost:9095/health  # Wispr Flow
```

---

## Stopping Services

### Stop All Services

```bash
# Stop all services at once
./scripts/start_everything.sh stop

# Output:
# [start-all] Stopping services...
# [start-all] Stopped UI wrapper
# [start-all] Stopped orchestrator
# [start-all] Stopped Context WS
# [start-all] Stopped Hybrid server
```

### Stop Individual Services

#### Hybrid Whisper Server

```bash
# Method 1: Using script (recommended)
./scripts/start_hybrid_server.sh stop

# Method 2: Using PID file
if [ -f "/tmp/hybrid-whisper-server.pid" ]; then
    pid=$(cat /tmp/hybrid-whisper-server.pid)
    kill $pid
    rm /tmp/hybrid-whisper-server.pid
fi

# Method 3: Force kill if needed
pkill -f hybrid_server.py

# Method 4: Kill by port
fuser -k 9099/tcp
```

#### Wispr Flow API

```bash
# Using script
./scripts/start_wispr_flow.sh stop

# Or manually
if [ -f "var/wispr_flow.pid" ]; then
    pid=$(cat var/wispr_flow.pid)
    kill $pid
    rm -f var/wispr_flow.pid
fi
```

#### Context WebSocket

```bash
# Using PID file
if [ -f "/tmp/hypr-voice-context-ws.pid" ]; then
    pid=$(cat /tmp/hypr-voice-context-ws.pid)
    kill $pid
    rm -f /tmp/hypr-voice-context-ws.pid
fi

# Or by process name
pkill -f context_websocket_server.py
```

#### Orchestrator

```bash
# Using PID file
if [ -f "/tmp/hypr-voice-orchestrator.pid" ]; then
    pid=$(cat /tmp/hypr-voice-orchestrator.pid)
    kill $pid
    rm -f /tmp/hypr-voice-orchestrator.pid
fi
```

### Graceful vs Force Shutdown

```bash
# Graceful shutdown (allows request completion)
kill -SIGTERM $PID

# Force shutdown (immediate)
kill -SIGKILL $PID
# or
kill -9 $PID
```

---

## Restarting Services

### Restart All Services

```bash
# Restart all services
./scripts/start_everything.sh stop
sleep 2
./scripts/start_everything.sh start

# Or for individual services
./scripts/start_hybrid_server.sh restart
./scripts/start_wispr_flow.sh restart
```

### Rolling Restart (No Downtime)

```bash
# Restart services one by one
# 1. Restart Wispr Flow (if no active sessions)
./scripts/start_wispr_flow.sh restart

# 2. Restart Context WS
kill -SIGTERM $(cat /tmp/hypr-voice-context-ws.pid)
sleep 2
# Start Context WS again...

# 3. Restart Orchestrator
kill -SIGTERM $(cat /tmp/hypr-voice-orchestrator.pid)
sleep 2
# Start Orchestrator again...

# 4. Restart Hybrid Server last
./scripts/start_hybrid_server.sh restart
```

### Zero-Downtime Reload (Orchestrator)

```bash
# Send SIGHUP for config reload (if supported)
kill -HUP $(cat /tmp/hypr-voice-orchestrator.pid)

# Or use systemctl (if using systemd)
sudo systemctl reload hypr-voice
```

---

## Service Status

### Check All Services

```bash
# Using start_everything.sh
./scripts/start_everything.sh status

# Output:
# [start-all] Hybrid server status:
# 📊 Hybrid WhisperLive Server Status
# ✅ Server is running (PID: 12345)
# 🔗 Server listening on port 9099
# [start-all] Wispr Flow server status:
# ✅ Server is running (PID: 12346)
# Port: 9095
# [start-all] Context WS running (pid 12347)
# [start-all] Orchestrator running (pid 12348)
# [start-all] UI wrapper running (pid 12349)
```

### Check Individual Services

#### Hybrid Server Status

```bash
./scripts/start_hybrid_server.sh status

# Output:
# 📊 Hybrid WhisperLive Server Status
# ✅ Server is running (PID: 12345)
# 🔗 Server listening on port 9099
# Active Sessions:
# {
#   "active_sessions": 2,
#   "sessions": ["uuid-1", "uuid-2"]
# }
```

#### Wispr Flow Status

```bash
./scripts/start_wispr_flow.sh status

# Output:
# ✓ Server is running (PID: 12346)
# Port: 9095
```

#### Manual Status Check

```bash
# Check if port is listening
netstat -tlnp | grep 9099
# or
ss -tlnp | grep 9099

# Check process
ps aux | grep hybrid_server.py

# Check PID file
cat /tmp/hybrid-whisper-server.pid

# Check if process is alive
kill -0 $(cat /tmp/hybrid-whisper-server.pid) 2>/dev/null && echo "Running" || echo "Not running"
```

### Health Check Endpoints

```bash
# Hybrid server
curl http://localhost:9099/health
# Response: {"status": "healthy", "timestamp": "...", "version": "..."}

# Orchestrator
curl http://localhost:9093/health

# Wispr Flow
curl http://localhost:9095/health

# Context WS
curl http://localhost:9091/health
```

---

## Systemd Integration

### Systemd Service Files

#### Hybrid Whisper Server

Create `/etc/systemd/system/hypr-voice-hybrid.service`:

```ini
[Unit]
Description=Hypr-Voice Hybrid Whisper Server
Documentation=https://github.com/yourusername/hypr-voice
After=network.target sound.target
Wants=sound.target

[Service]
Type=forking
User=hyprvoice
Group=hyprvoice
WorkingDirectory=/opt/hypr-voice

Environment="PATH=/opt/hypr-voice/.venv/bin"
Environment="PYTHONPATH=/opt/hypr-voice/src"
Environment="HYPR_VOICE_WHISPER_CONFIG_DIR=/opt/hypr-voice/config/hypr_voice/whisper"

ExecStart=/opt/hypr-voice/scripts/start_hybrid_server.sh start
ExecStop=/opt/hypr-voice/scripts/start_hybrid_server.sh stop
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=10
TimeoutStartSec=60
TimeoutStopSec=30

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hypr-voice-hybrid

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/hypr-voice/logs /opt/hypr-voice/var /tmp

[Install]
WantedBy=multi-user.target
```

#### Orchestrator Service

Create `/etc/systemd/system/hypr-voice-orchestrator.service`:

```ini
[Unit]
Description=Hypr-Voice Orchestrator
Documentation=https://github.com/yourusername/hypr-voice
After=network.target
Wants=hypr-voice-hybrid.service

[Service]
Type=simple
User=hyprvoice
Group=hyprvoice
WorkingDirectory=/opt/hypr-voice

Environment="PATH=/opt/hypr-voice/.venv/bin:/usr/bin"
Environment="PYTHONPATH=/opt/hypr-voice/src"
Environment="ORCHESTRATOR_PORT=9093"

ExecStart=/opt/hypr-voice/.venv/bin/python -m uvicorn hypr_voice.server:app \
    --host 0.0.0.0 --port 9093 \
    --log-level info

ExecStop=/bin/kill -SIGTERM $MAINPID
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hypr-voice-orchestrator

[Install]
WantedBy=multi-user.target
```

#### Wispr Flow Service

Create `/etc/systemd/system/hypr-voice-wispr.service`:

```ini
[Unit]
Description=Hypr-Voice Wispr Flow API
Documentation=https://github.com/yourusername/hypr-voice
After=network.target

[Service]
Type=forking
User=hyprvoice
Group=hyprvoice
WorkingDirectory=/opt/hypr-voice

Environment="PATH=/opt/hypr-voice/.venv/bin"
EnvironmentFile=/opt/hypr-voice/.env

ExecStart=/opt/hypr-voice/scripts/start_wispr_flow.sh start
ExecStop=/opt/hypr-voice/scripts/start_wispr_flow.sh stop
Restart=on-failure
RestartSec=10

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=hypr-voice-wispr

[Install]
WantedBy=multi-user.target
```

### Enable and Manage Services

```bash
# Reload systemd configuration
sudo systemctl daemon-reload

# Enable services (auto-start on boot)
sudo systemctl enable hypr-voice-hybrid
sudo systemctl enable hypr-voice-orchestrator
sudo systemctl enable hypr-voice-wispr

# Start services
sudo systemctl start hypr-voice-hybrid
sudo systemctl start hypr-voice-orchestrator
sudo systemctl start hypr-voice-wispr

# Check status
sudo systemctl status hypr-voice-hybrid
sudo systemctl status hypr-voice-orchestrator
sudo systemctl status hypr-voice-wispr

# Stop services
sudo systemctl stop hypr-voice-hybrid
sudo systemctl stop hypr-voice-orchestrator

# Restart services
sudo systemctl restart hypr-voice-hybrid

# View logs
sudo journalctl -u hypr-voice-hybrid -f
sudo journalctl -u hypr-voice-orchestrator -f
```

---

## Process Management

### Monitoring Process Resources

```bash
# Check CPU and memory usage
top -p $(cat /tmp/hybrid-whisper-server.pid)

# Or use htop for better visualization
htp -p $(cat /tmp/hybrid-whisper-server.pid)

# Check all Hypr-Voice processes
ps aux | grep -E "hypr|whisper|orchestrator"

# Detailed process info
ps aux | grep hybrid_server.py
```

### Process Resource Limits

```bash
# Set ulimits for the service user
# Edit /etc/security/limits.conf

hyprvoice soft nofile 65536
hyprvoice hard nofile 65536
hyprvoice soft nproc 4096
hyprvoice hard nproc 8192
hyprvoice soft memlock unlimited
hyprvoice hard memlock unlimited
```

### Nice and Ionice

```bash
# Set process priority (lower priority = higher nice value)
nice -n 10 ./scripts/start_hybrid_server.sh start

# Set I/O priority
ionice -c 2 -n 7 ./scripts/start_hybrid_server.sh start

# Change running process priority
renice +10 -p $(cat /tmp/hybrid-whisper-server.pid)
ionice -c 2 -n 7 -p $(cat /tmp/hybrid-whisper-server.pid)
```

---

## Service Dependencies

### Startup Order

Services must be started in this order:

```
1. Wispr Flow API (9095) - if MODE=FLOW
2. Hybrid Whisper Server (9099)
3. Context WebSocket (9091)
4. Orchestrator (9093)
5. Web UI Bridge (8934)
6. Web UI Frontend (8933)
```

### Dependency Graph

```
Orchestrator (9093)
 ├─► needs Hybrid Whisper (9099) [MODE=LOCAL]
 │     └─► needs Audio subsystem
 │
 ├─► needs Wispr Flow (9095) [MODE=FLOW]
 │     └─► needs External API
 │
 └─► needs Context WebSocket (9091)
       └─► needs Orchestrator

Web UI Bridge (8934)
 ├─► needs Context WebSocket (9091)
 └─► needs Orchestrator (9093)

Web UI (8933)
 └─► needs Bridge (8934)
```

### Dependency Check Script

```bash
#!/bin/bash
# check_dependencies.sh

services=(
    "9095:Wispr Flow"
    "9099:Hybrid Whisper"
    "9091:Context WS"
    "9093:Orchestrator"
)

for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    if nc -z localhost $port 2>/dev/null; then
        echo "✓ $name is available on port $port"
    else
        echo "✗ $name is NOT available on port $port"
    fi
done
```

---

## Auto-Start Configuration

### User-Level Auto-Start (Hyprland)

Add to `~/.config/hypr/hyprland.conf`:

```bash
# Auto-start Hypr-Voice services on login
exec-once = /opt/hypr-voice/scripts/start_everything.sh start
```

### System-Level Auto-Start (Systemd)

```bash
# Enable services for system boot
sudo systemctl enable hypr-voice-hybrid
sudo systemctl enable hypr-voice-orchestrator
sudo systemctl enable hypr-voice-wispr
```

### Cron-Based Auto-Start

```bash
# Add to crontab
@reboot /opt/hypr-voice/scripts/start_everything.sh start >> /var/log/hypr-voice-startup.log 2>&1
```

---

## Troubleshooting Services

### Service Won't Start

```bash
# 1. Check if port is already in use
sudo lsof -i :9099

# 2. Check logs for errors
tail -f /tmp/hybrid-whisper-server.log

# 3. Check Python dependencies
source .venv/bin/activate
pip check

# 4. Verify configuration
cat config/hypr_voice/whisper/config.yaml

# 5. Test with verbose mode
HYPR_VOICE_TRACE=1 ./scripts/start_hybrid_server.sh start
```

### Service Keeps Crashing

```bash
# 1. Check system logs
sudo journalctl -xe

# 2. Check service logs
tail -100 /tmp/hybrid-whisper-server.log

# 3. Check for memory issues
free -h

# 4. Check disk space
df -h

# 5. Test manually (without script)
source .venv/bin/activate
export PYTHONPATH=/path/to/hypr-voice/src
python src/hypr_voice/whisper/core/hybrid_server.py
```

### High CPU Usage

```bash
# 1. Identify the process
top -p $(cat /tmp/hybrid-whisper-server.pid)

# 2. Check for infinite loops
strace -p $(cat /tmp/hybrid-whisper-server.pid)

# 3. Check model size (larger models = more CPU)
# Edit config/hypr_voice/whisper/config.yaml
# Use smaller model: "tiny.en" or "base.en"

# 4. Check for concurrent sessions
curl http://localhost:9099/sessions
```

### High Memory Usage

```bash
# 1. Check memory usage
ps aux | grep hybrid_server

# 2. Monitor over time
watch -n 5 'ps aux | grep hybrid_server'

# 3. Reduce model size or batch size
# Edit config/hypr_voice/whisper/config.yaml
performance:
  audio_chunk_size: 1024  # Reduce from 2048

# 4. Enable memory cleanup
model:
  cache_path: "/tmp/whisper-live-cache"
```

### Port Binding Issues

```bash
# 1. Find what's using the port
sudo lsof -i :9099
sudo netstat -tlnp | grep 9099

# 2. Kill the conflicting process
sudo kill -9 <PID>

# 3. Or change port in config
# Edit config/hypr_voice/whisper/config.yaml
server:
  port: 9100  # Use different port
```

### Log Analysis

```bash
# Real-time log monitoring
tail -f /tmp/hybrid-whisper-server.log

# Search for errors
grep -i "error" /tmp/hybrid-whisper-server.log

# Count errors by type
grep -i "error" /tmp/hybrid-whisper-server.log | cut -d: -f4 | sort | uniq -c

# View last 100 lines
tail -100 /tmp/hybrid-whisper-server.log

# View systemd journal
sudo journalctl -u hypr-voice-hybrid -n 100
```

---

## Quick Reference Commands

```bash
# Quick start all
./scripts/start_everything.sh start

# Quick stop all
./scripts/start_everything.sh stop

# Quick status check
./scripts/start_everything.sh status

# View logs
./scripts/start_hybrid_server.sh logs
tail -f logs/wispr_flow.log

# Restart specific service
./scripts/start_hybrid_server.sh restart

# Test health
curl http://localhost:9099/health

# Systemd commands
sudo systemctl start hypr-voice-hybrid
sudo systemctl stop hypr-voice-hybrid
sudo systemctl restart hypr-voice-hybrid
sudo systemctl status hypr-voice-hybrid
sudo journalctl -u hypr-voice-hybrid -f
```

---

## Next Steps

1. Setup [Monitoring](monitoring.md)
2. Configure [Logging](logging.md)
3. Implement [Backups](backup-recovery.md)
4. Review [Performance Tuning](performance-tuning.md)
