# Logging Guide - Hypr-Voice

Comprehensive logging configuration and management for Hypr-Voice.

## Table of Contents

1. [Logging Overview](#logging-overview)
2. [Log Configuration](#log-configuration)
3. [Log Locations](#log-locations)
4. [Log Formats](#log-formats)
5. [Log Rotation](#log-rotation)
6. [Log Analysis](#log-analysis)
7. [Centralized Logging](#centralized-logging)
8. [Log Retention](#log-retention)
9. [Debug Logging](#debug-logging)
10. [Performance Logging](#performance-logging)

---

## Logging Overview

### Log Sources

| Service | Log Location | Type | Format |
|---------|--------------|------|--------|
| **Hybrid Whisper** | `/tmp/hybrid-whisper-server.log` | Application | Text |
| **Orchestrator** | `/tmp/hypr-voice-orchestrator.log` | Application | Text |
| **Context WS** | `/tmp/hypr-voice-context-ws.log` | Application | Text |
| **Wispr Flow** | `logs/wispr_flow.log` | Application | Text |
| **Web UI** | `/tmp/hypr-voice-ui.log` | Application | Text |
| **Systemd** | Journal | System | Journal |
| **Agent** | `/tmp/hypr-voice/hypr-voice.log` | Application | LogGurl |

### Log Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **DEBUG** | Detailed diagnostic information | Development |
| **INFO** | General informational messages | Normal operation |
| **WARNING** | Warning messages for potential issues | Production (default) |
| **ERROR** | Error events that might allow continuation | Production |
| **CRITICAL** | Critical issues that require immediate attention | Production |

---

## Log Configuration

### Environment Variables

```bash
# Enable detailed tracing
export HYPR_VOICE_TRACE=1
export HYPR_VOICE_FLOW_TRACE=1
export HYPR_VOICE_TRACE_CONTEXT=1
export HYPR_VOICE_TRACE_TCPGEN=1
export HYPR_VOICE_TRACE_QUEUE=1

# Disable tracing (production)
export HYPR_VOICE_TRACE=0
export HYPR_VOICE_FLOW_TRACE=0
```

### Python Logging Configuration

Create `config/logging.yaml`:

```yaml
version: 1
disable_existing_loggers: false

formatters:
  standard:
    format: '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

  detailed:
    format: '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d]: %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S.%f'

  json:
    class: pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(levelname)s %(name)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: detailed
    filename: /opt/hypr-voice/logs/hypr-voice.log
    maxBytes: 10485760  # 10MB
    backupCount: 10

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: detailed
    filename: /opt/hypr-voice/logs/error.log
    maxBytes: 10485760
    backupCount: 10

loggers:
  hypr_voice:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false

  uvicorn:
    level: INFO
    handlers: [console, file]
    propagate: false

  websockets:
    level: INFO
    handlers: [console, file]
    propagate: false

root:
  level: WARNING
  handlers: [console]
```

### Application Usage

```python
# In your Python code

import logging
import logging.config
import yaml

# Load logging config
with open('config/logging.yaml', 'r') as f:
    config = yaml.safe_load(f)
    logging.config.dictConfig(config)

# Get logger
logger = logging.getLogger('hypr_voice')

# Use logger
logger.debug("Detailed debug information")
logger.info("Service started successfully")
logger.warning("High memory usage detected")
logger.error("Failed to process request")
logger.critical("Service unavailable")
```

---

## Log Locations

### Directory Structure

```
/opt/hypr-voice/
├── logs/                          # Application logs
│   ├── hypr-voice.log            # Main application log
│   ├── error.log                 # Error-only log
│   ├── transcription.log         # Transcription events
│   └── performance.log           # Performance metrics
│
├── var/                           # Runtime files
│   └── wispr_flow.pid            # Process IDs
│
└── /tmp/                          # Temporary logs
    ├── hybrid-whisper-server.log  # Hybrid server
    ├── hypr-voice-orchestrator.log # Orchestrator
    ├── hypr-voice-context-ws.log   # Context WebSocket
    └── hypr-voice-ui.log           # Web UI
```

### Log Files by Service

#### Hybrid Whisper Server

```bash
# Location
/tmp/hybrid-whisper-server.log

# View in real-time
tail -f /tmp/hybrid-whisper-server.log

# Search for errors
grep -i error /tmp/hybrid-whisper-server.log

# Count errors by type
grep -i error /tmp/hybrid-whisper-server.log | cut -d: -f4 | sort | uniq -c
```

#### Orchestrator

```bash
# Location
/tmp/hypr-voice-orchestrator.log

# View
tail -f /tmp/hypr-voice-orchestrator.log

# Follow specific patterns
tail -f /tmp/hypr-voice-orchestrator.log | grep --line-buffered "ERROR\|WARNING"
```

#### Wispr Flow API

```bash
# Location
logs/wispr_flow.log

# View
tail -f logs/wispr_flow.log

# Search for API calls
grep "POST /transcribe" logs/wispr_flow.log
```

---

## Log Formats

### Standard Text Format

```
2024-01-26 10:30:45,123 [INFO] hypr_voice.whisper.core.hybrid_server: Starting server on port 9099
2024-01-26 10:30:46,456 [DEBUG] hypr_voice.whisper.core.hybrid_server: Model loaded: small.en
2024-01-26 10:30:50,789 [INFO] hypr_voice.whisper.core.hybrid_server: New session created: abc-123
2024-01-26 10:31:00,012 [WARNING] hypr_voice.whisper.core.hybrid_server: High memory usage: 85%
2024-01-26 10:31:05,345 [ERROR] hypr_voice.whisper.core.hybrid_server: Transcription failed for session abc-123
```

### JSON Format

```json
{
  "timestamp": "2024-01-26T10:30:45.123456",
  "level": "INFO",
  "logger": "hypr_voice.whisper.core.hybrid_server",
  "message": "Starting server on port 9099",
  "context": {
    "port": 9099,
    "host": "0.0.0.0"
  }
}
```

### LogGurl Format (Standardized)

```bash
# Format: HH:MM:SS.mmm [service] [LEVEL] message

10:30:45.123 [  hybrid-whisper] [ INFO] Server started on port 9099
10:30:46.456 [  hybrid-whisper] [DEBUG] Model loaded: small.en
10:30:50.789 [orchestrator] [ INFO] Processing query: "Hello"
10:31:00.012 [  hybrid-whisper] [ WARN] High memory usage: 85%
10:31:05.345 [orchestrator] [ERROR] LLM request failed: timeout
```

### Request/Response Logging

```bash
# Request log
10:30:45.123 [     api-server] [ INFO] POST /voice/process
10:30:45.124 [     api-server] [DEBUG] Request: {"text": "Hello world", "speak_response": true}
10:30:45.500 [     api-server] [ INFO] Response: 200 OK (376ms)

# Error log
10:31:00.000 [     api-server] [ERROR] POST /voice/process
10:31:00.001 [     api-server] [ERROR] Error: Transcription timeout
10:31:00.002 [     api-server] [ERROR] Traceback: File "xxx.py", line 123
```

---

## Log Rotation

### Logrotate Configuration

Create `/etc/logrotate.d/hypr-voice`:

```
# Application logs
/opt/hypr-voice/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 hyprvoice hyprvoice
    sharedscripts
    postrotate
        # Send SIGHUP to reload logs
        systemctl reload hypr-voice-hybrid > /dev/null 2>&1 || true
        systemctl reload hypr-voice-orchestrator > /dev/null 2>&1 || true
    endscript
}

# Temporary logs
/tmp/hybrid-whisper-server.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 hyprvoice hyprvoice
}

/tmp/hypr-voice-*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 hyprvoice hyprvoice
}

# Wispr Flow logs
/opt/hypr-voice/logs/wispr_flow.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 hyprvoice hyprvoice
}
```

### Manual Log Rotation

```bash
#!/bin/bash
# rotate_logs.sh

log_dir="/opt/hypr-voice/logs"
timestamp=$(date +%Y%m%d)

# Rotate logs
for log_file in "$log_dir"/*.log; do
    if [ -f "$log_file" ]; then
        mv "$log_file" "${log_file}.${timestamp}"
        touch "$log_file"
        chmod 640 "$log_file"
        gzip "${log_file}.${timestamp}"
    fi
done

# Reload services
systemctl reload hypr-voice-hybrid
systemctl reload hypr-voice-orchestrator

echo "Log rotation completed: $(date)"
```

### Test Log Rotation

```bash
# Test logrotate configuration
sudo logrotate -d /etc/logrotate.d/hypr-voice

# Force rotation
sudo logrotate -f /etc/logrotate.d/hypr-voice
```

---

## Log Analysis

### Common Analysis Commands

```bash
# Count requests per hour
awk '{print $1}' /opt/hypr-voice/logs/hypr-voice.log | cut -d: -f1-2 | sort | uniq -c

# Find top errors
grep ERROR /opt/hypr-voice/logs/hypr-voice.log | awk '{print $5}' | sort | uniq -c | sort -rn | head -10

# Calculate average response time
grep "Response:" /opt/hypr-voice/logs/api.log | grep -oP '\(\K[0-9]+(?=ms\))' | awk '{sum+=$1; count++} END {print sum/count}'

# Find slow requests
grep "Response:" /opt/hypr-voice/logs/api.log | grep -P '\(\K[0-9]+(?=ms\))' | awk -F'[(ms)]' '$2>1000' | tee slow-requests.log

# Check for exceptions
grep -i "exception\|traceback" /opt/hypr-voice/logs/*.log
```

### Log Analysis Scripts

#### Error Summary Script

```bash
#!/bin/bash
# error_summary.sh

log_file="/opt/hypr-voice/logs/hypr-voice.log"
since_date="${1:-2024-01-01}"

echo "=== Error Summary ==="
echo "Since: $since_date"
echo ""

# Count errors by level
echo "By Level:"
grep -i "error\|warning\|critical" "$log_file" | grep -v "DEBUG" | awk '{print $3}' | sort | uniq -c | sort -rn

# Count errors by logger
echo ""
echo "By Logger:"
grep ERROR "$log_file" | awk -F'[][]' '{print $4}' | sort | uniq -c | sort -rn | head -10

# Recent errors
echo ""
echo "Recent Errors (last 10):"
grep ERROR "$log_file" | tail -10
```

#### Performance Analysis Script

```bash
#!/bin/bash
# performance_analysis.sh

log_file="/opt/hypr-voice/logs/performance.log"

echo "=== Performance Analysis ==="
echo ""

# Average transcription time
avg_trans=$(grep "transcription_time" "$log_file" | grep -oP '[0-9]+(?=ms)' | awk '{sum+=$1; count++} END {print sum/count}')
echo "Average transcription time: ${avg_trans}ms"

# Average TTS time
avg_tts=$(grep "tts_time" "$log_file" | grep -oP '[0-9]+(?=ms)' | awk '{sum+=$1; count++} END {print sum/count}')
echo "Average TTS time: ${avg_tts}ms"

# 95th percentile
p95=$(grep "transcription_time" "$log_file" | grep -oP '[0-9]+(?=ms)' | sort -n | awk 'BEGIN{i=0} {a[i++]=$1} END {x=int(i*0.95); print a[x]}')
echo "95th percentile transcription time: ${p95}ms"
```

---

## Centralized Logging

### ELK Stack Setup

#### Elasticsearch

```bash
# Install Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" | sudo tee /etc/apt/sources.list.d/elastic-7.x.list
sudo apt-get update && sudo apt-get install elasticsearch

# Configure
sudo cat > /etc/elasticsearch/elasticsearch.yml <<'EOF'
cluster.name: hypr-voice
node.name: node-1
network.host: localhost
http.port: 9200
discovery.type: single-node
EOF

# Start
sudo systemctl start elasticsearch
sudo systemctl enable elasticsearch
```

#### Logstash

```bash
# Install Logstash
sudo apt-get install logstash

# Configure pipeline
sudo cat > /etc/logstash/conf.d/hypr-voice.conf <<'EOF'
input {
  file {
    path => "/opt/hypr-voice/logs/*.log"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    codec => multiline {
      pattern => "^%{TIMESTAMP_ISO8601}"
      negate => true
      what => "previous"
    }
  }
}

filter {
  grok {
    match => {
      "message" => "%{TIMESTAMP_ISO8601:timestamp} \[%{LOGLEVEL:level}\] %{DATA:logger}: %{GREEDYDATA:message}"
    }
  }
  date {
    match => ["timestamp", "ISO8601"]
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "hypr-voice-%{+YYYY.MM.dd}"
  }
}
EOF

# Start
sudo systemctl start logstash
```

#### Kibana

```bash
# Install Kibana
sudo apt-get install kibana

# Configure
sudo cat > /etc/kibana/kibana.yml <<'EOF'
server.host: "localhost"
server.port: 5601
elasticsearch.hosts: ["http://localhost:9200"]
EOF

# Start
sudo systemctl start kibana
sudo systemctl enable kibana

# Access at http://localhost:5601
```

### Loki + Promtail (Lightweight)

#### Loki Installation

```bash
# Download Loki
wget https://github.com/grafana/loki/releases/download/v2.9.0/loki-linux-amd64.zip
unzip loki-linux-amd64.zip
sudo mv loki-linux-amd64 /usr/local/bin/loki

# Configuration
sudo cat > /etc/loki/local-config.yaml <<'EOF'
auth_enabled: false
server:
  http_listen_port: 3100
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://localhost:3100/loki/api/v1/push
scrape_configs:
  - job_name: hypr-voice
    static_configs:
      - targets:
          - localhost
        labels:
          job: hypr-voice
          __path__: /opt/hypr-voice/logs/*.log
EOF

# Start
sudo systemctl start loki
```

#### Promtail Installation

```bash
# Download Promtail
wget https://github.com/grafana/loki/releases/download/v2.9.0/promtail-linux-amd64.zip
unzip promtail-linux-amd64.zip
sudo mv promtail-linux-amd64 /usr/local/bin/promtail

# Configuration
sudo cat > /etc/promtail/config.yml <<'EOF'
server:
  http_listen_port: 9080
positions:
  filename: /tmp/positions.yaml
clients:
  - url: http://localhost:3100/loki/api/v1/push
scrape_configs:
  - job_name: hybrid-whisper
    static_configs:
      - targets:
          - localhost
        labels:
          job: hybrid-whisper
          __path__: /tmp/hybrid-whisper-server.log
  - job_name: orchestrator
    static_configs:
      - targets:
          - localhost
        labels:
          job: orchestrator
          __path__: /tmp/hypr-voice-orchestrator.log
EOF

# Start
sudo systemctl start promtail
```

---

## Log Retention

### Retention Policy

| Log Type | Retention | Reason |
|----------|-----------|--------|
| **Application logs** | 30 days | Debugging, auditing |
| **Error logs** | 90 days | Compliance, analysis |
| **Audit logs** | 365 days | Legal requirements |
| **Performance logs** | 7 days | Capacity planning |
| **Debug logs** | 3 days | Troubleshooting |

### Automated Cleanup

```bash
#!/bin/bash
# cleanup_old_logs.sh

log_dir="/opt/hypr-voice/logs"
days_to_keep=30

# Compress logs older than 1 day
find "$log_dir" -name "*.log" -mtime +1 ! -name "*.gz" -exec gzip {} \;

# Remove compressed logs older than retention period
find "$log_dir" -name "*.gz" -mtime +$days_to_keep -delete

# Clear temp logs older than 3 days
find /tmp -name "hypr-voice*.log*" -mtime +3 -delete

echo "Log cleanup completed: $(date)"
```

### Cron Job

```bash
# Add to crontab
0 2 * * * /opt/hypr-voice/scripts/cleanup_old_logs.sh >> /var/log/hypr-voice-cleanup.log 2>&1
```

---

## Debug Logging

### Enable Debug Mode

```bash
# Set environment variables
export HYPR_VOICE_TRACE=1
export HYPR_VOICE_FLOW_TRACE=1
export HYPR_VOICE_TRACE_CONTEXT=1
export HYPR_VOICE_TRACE_TCPGEN=1
export HYPR_VOICE_TRACE_QUEUE=1

# Or add to .env
echo "HYPR_VOICE_TRACE=1" >> .env
echo "HYPR_VOICE_FLOW_TRACE=1" >> .env
```

### Selective Debug Logging

```python
# Enable debug for specific modules

import logging

# Get specific logger
logger = logging.getLogger('hypr_voice.whisper.core')

# Set to DEBUG level
logger.setLevel(logging.DEBUG)

# Add handler
handler = logging.FileHandler('/tmp/debug.log')
handler.setLevel(logging.DEBUG)
logger.addHandler(handler)
```

### Debug Commands

```bash
# Start service with debug output
HYPR_VOICE_TRACE=1 ./scripts/start_hybrid_server.sh start

# View debug logs
tail -f /tmp/hybrid-whisper-server.log | grep DEBUG

# Debug specific component
tail -f /tmp/hybrid-whisper-server.log | grep "tcpgen\|queue"
```

---

## Performance Logging

### Application Performance Logging

```python
# Add performance logging

import time
import logging
from functools import wraps

logger = logging.getLogger('hypr_voice.performance')

def log_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = (end_time - start_time) * 1000  # ms

        logger.info(
            f"{func.__name__} completed",
            extra={
                'function': func.__name__,
                'duration_ms': duration,
                'args': str(args),
                'kwargs': str(kwargs)
            }
        )

        return result
    return wrapper

# Usage
@log_performance
def transcribe_audio(audio_file):
    # Transcription logic
    pass
```

### Performance Metrics

```bash
# Log performance metrics
echo "$(date '+%Y-%m-%d %H:%M:%S'),transcription,${duration}ms" >> /opt/hypr-voice/logs/performance.log

# Analyze performance
awk -F',' '$2=="transcription" {sum+=$3; count++} END {print "Average:", sum/count, "ms"}' \
    /opt/hypr-voice/logs/performance.log
```

---

## Next Steps

1. Setup [Monitoring](monitoring.md)
2. Configure [Backups](backup-recovery.md)
3. Review [Security](security.md)
4. Optimize [Performance](performance-tuning.md)
