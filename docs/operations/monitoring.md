# Monitoring Guide - Hypr-Voice

Comprehensive monitoring setup and health check procedures for Hypr-Voice.

## Table of Contents

1. [Monitoring Overview](#monitoring-overview)
2. [Health Checks](#health-checks)
3. [Metrics Collection](#metrics-collection)
4. [Logging Monitoring](#logging-monitoring)
5. [Performance Monitoring](#performance-monitoring)
6. [Alerting Setup](#alerting-setup)
7. [Dashboard Creation](#dashboard-creation)
8. [Service Availability](#service-availability)
9. [Resource Monitoring](#resource-monitoring)
10. [Integration with Monitoring Tools](#integration-with-monitoring-tools)

---

## Monitoring Overview

### Key Monitoring Areas

| Area | Metrics | Tools |
|------|---------|-------|
| **Service Health** | Uptime, response time, error rate | Health endpoints, curl |
| **Performance** | CPU, memory, disk I/O, network | top, htop, iostat |
| **Application** | Request rate, transcription time, TTS latency | Application logs |
| **Business** | Active users, transcription count | Analytics |

### Monitoring Architecture

```
┌─────────────────────────────────────────────────────┐
│                Monitoring Stack                     │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
│  │  Grafana    │  │ Prometheus  │  │ AlertMgr  │  │
│  │ (Dashboards)│  │ (Metrics)   │  │ (Alerts)  │  │
│  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘  │
│         │                │                │          │
│         └────────────────┼────────────────┘          │
│                          │                           │
│              ┌───────────▼───────────┐               │
│              │   Node Exporter       │               │
│              │   + App Metrics       │               │
│              └───────────────────────┘               │
│                          │                           │
│  ┌───────────────────────┼───────────────────────┐  │
│  │                       │                       │  │
│  ▼                       ▼                       ▼  │
│ ┌───────┐  ┌──────────┐  ┌──────────┐  ┌───────┐ │
│ │Hybrid │  │Orchestr. │  │WisprFlow │  │Context│ │
│ │ 9099  │  │   9093   │  │   9095   │  │ 9091  │ │
│ └───────┘  └──────────┘  └──────────┘  └───────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Health Checks

### Basic Health Endpoints

All services expose health check endpoints:

```bash
# Hybrid Whisper Server
curl http://localhost:9099/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2024-01-26T10:30:00.000000",
  "version": "0.2.0"
}

# Orchestrator
curl http://localhost:9093/health

# Wispr Flow API
curl http://localhost:9095/health

# Context WebSocket
curl http://localhost:9091/health
```

### Advanced Health Check Script

Create `scripts/health_check.sh`:

```bash
#!/bin/bash
# Health check script for all Hypr-Voice services

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Services to check
declare -A services=(
    ["9099"]="Hybrid Whisper"
    ["9093"]="Orchestrator"
    ["9091"]="Context WebSocket"
    ["9095"]="Wispr Flow"
)

all_healthy=true

for port in "${!services[@]}"; do
    service="${services[$port]}"
    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $service (port $port): Healthy"
    else
        echo -e "${RED}✗${NC} $service (port $port): Unhealthy"
        all_healthy=false
    fi
done

# Check if processes are running
echo ""
echo "Process Status:"
for pid_file in \
    "/tmp/hybrid-whisper-server.pid" \
    "/tmp/hypr-voice-orchestrator.pid" \
    "/tmp/hypr-voice-context-ws.pid" \
    "var/wispr_flow.pid"
do
    if [ -f "$pid_file" ]; then
        pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${GREEN}✓${NC} Process $pid (PID: $pid): Running"
        else
            echo -e "${YELLOW}⚠${NC} Stale PID file: $pid_file"
        fi
    fi
done

# Final status
echo ""
if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}All services healthy${NC}"
    exit 0
else
    echo -e "${RED}Some services are unhealthy${NC}"
    exit 1
fi
```

### Deep Health Checks

```bash
#!/bin/bash
# Deep health check with diagnostics

check_service_health() {
    local port=$1
    local service=$2

    # 1. Check if port is listening
    if ! nc -z localhost $port 2>/dev/null; then
        echo "FAIL: $service - Port $port not listening"
        return 1
    fi

    # 2. Check HTTP response
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$port/health" 2>/dev/null)
    if [ "$response" != "200" ]; then
        echo "FAIL: $service - HTTP $response"
        return 1
    fi

    # 3. Check response body
    body=$(curl -s "http://localhost:$port/health" 2>/dev/null)
    status=$(echo "$body" | jq -r '.status' 2>/dev/null)
    if [ "$status" != "healthy" ]; then
        echo "FAIL: $service - Status: $status"
        return 1
    fi

    # 4. Check response time
    start_time=$(date +%s%3N)
    curl -s "http://localhost:$port/health" > /dev/null 2>/dev/null
    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))

    if [ $duration -gt 1000 ]; then
        echo "WARN: $service - Slow response (${duration}ms)"
        return 2
    fi

    echo "OK: $service - Healthy (${duration}ms)"
    return 0
}

# Check all services
check_service_health 9099 "Hybrid Whisper"
check_service_health 9093 "Orchestrator"
check_service_health 9091 "Context WebSocket"
check_service_health 9095 "Wispr Flow"
```

### Health Check Cron Job

```bash
# Add to crontab for automated checks
# Run every 5 minutes

*/5 * * * * /opt/hypr-voice/scripts/health_check.sh >> /var/log/hypr-voice-health.log 2>&1

# Or with alerting
*/5 * * * * /opt/hypr-voice/scripts/health_check.sh || /opt/hypr-voice/scripts/alert.sh "Health check failed"
```

---

## Metrics Collection

### Application Metrics

#### Hybrid Whisper Server Metrics

```python
# Add to hybrid_server.py

from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
transcription_counter = Counter(
    'transcriptions_total',
    'Total number of transcriptions',
    ['status', 'language']
)

transcription_duration = Histogram(
    'transcription_duration_seconds',
    'Transcription duration',
    ['model']
)

active_sessions = Gauge(
    'active_sessions',
    'Number of active sessions'
)

audio_duration = Histogram(
    'audio_duration_seconds',
    'Audio duration processed',
    buckets=[10, 30, 60, 120, 300, 600, 1800]
)

# Expose metrics endpoint
start_http_server(9098)  # Separate port for metrics
```

#### Orchestrator Metrics

```python
# Add to server.py

from prometheus_client import Counter, Histogram, Gauge

request_counter = Counter(
    'orchestrator_requests_total',
    'Total requests to orchestrator',
    ['endpoint', 'status']
)

request_duration = Histogram(
    'orchestrator_request_duration_seconds',
    'Request duration',
    ['endpoint']
)

llm_duration = Histogram(
    'llm_response_duration_seconds',
    'LLM response duration',
    ['model', 'agent']
)

tts_duration = Histogram(
    'tts_generation_duration_seconds',
    'TTS generation duration',
    ['provider']
)

active_conversations = Gauge(
    'active_conversations',
    'Number of active conversations'
)
```

### System Metrics with Node Exporter

```bash
# Install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.7.0/node_exporter-1.7.0.linux-amd64.tar.gz
tar xvfz node_exporter-1.7.0.linux-amd64.tar.gz
sudo cp node_exporter-1.7.0.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter

# Create systemd service
sudo cat > /etc/systemd/system/node_exporter.service <<'EOF'
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl start node_exporter
sudo systemctl enable node_exporter

# Metrics available at http://localhost:9100/metrics
```

### Prometheus Configuration

Create `/etc/prometheus/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus itself
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node Exporter (system metrics)
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  # Hybrid Whisper Server
  - job_name: 'hybrid-whisper'
    static_configs:
      - targets: ['localhost:9098']
    metrics_path: '/metrics'

  # Orchestrator
  - job_name: 'orchestrator'
    static_configs:
      - targets: ['localhost:9093']
    metrics_path: '/metrics'

  # Wispr Flow API
  - job_name: 'wispr-flow'
    static_configs:
      - targets: ['localhost:9095']
    metrics_path: '/metrics'
```

---

## Logging Monitoring

### Log Aggregation with Loki

```bash
# Install Loki
wget https://github.com/grafana/loki/releases/download/v2.9.0/loki-linux-amd64.zip
unzip loki-linux-amd64.zip
sudo mv loki-linux-amd64 /usr/local/bin/loki

# Create config
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

# Start Loki
sudo systemctl start loki
```

### Promtail Configuration

```yaml
# /etc/promtail/config.yml

server:
  http_listen_port: 9080

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  # Hybrid Whisper logs
  - job_name: hybrid-whisper
    static_configs:
      - targets:
          - localhost
        labels:
          job: hybrid-whisper
          __path__: /tmp/hybrid-whisper-server.log

  # Orchestrator logs
  - job_name: orchestrator
    static_configs:
      - targets:
          - localhost
        labels:
          job: orchestrator
          __path__: /tmp/hypr-voice-orchestrator.log

  # Wispr Flow logs
  - job_name: wispr-flow
    static_configs:
      - targets:
          - localhost
        labels:
          job: wispr-flow
          __path__: /opt/hypr-voice/logs/wispr_flow.log
```

---

## Performance Monitoring

### Key Performance Indicators (KPIs)

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| **Transcription Latency** | <500ms | >1000ms |
| **TTS Generation Time** | <300ms | >500ms |
| **Orchestrator Response** | <1s | >2s |
| **Memory Usage** | <70% | >90% |
| **CPU Usage** | <60% | >85% |
| **Error Rate** | <1% | >5% |
| **Active Sessions** | <50 | >45 |

### Performance Monitoring Script

```bash
#!/bin/bash
# monitor_performance.sh

# Measure transcription latency
measure_transcription() {
    local test_audio="/tmp/test.wav"
    local start_time end_time duration

    # Ensure test audio exists
    if [ ! -f "$test_audio" ]; then
        echo "Error: Test audio not found"
        return 1
    fi

    # Start timing
    start_time=$(date +%s%3N)

    # Send transcription request
    curl -s -X POST \
        -F "audio_file=@$test_audio" \
        http://localhost:9099/sessions/$(uuidgen)/transcribe \
        > /dev/null

    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))

    echo "Transcription latency: ${duration}ms"

    if [ $duration -gt 1000 ]; then
        echo "WARNING: High transcription latency"
    fi
}

# Measure memory usage
measure_memory() {
    local pid
    if [ -f "/tmp/hybrid-whisper-server.pid" ]; then
        pid=$(cat /tmp/hybrid-whisper-server.pid)
        mem=$(ps -p "$pid" -o rss= | awk '{print $1/1024}')
        echo "Memory usage: ${mem}MB"

        if [ $(echo "$mem > 4000" | bc) -eq 1 ]; then
            echo "WARNING: High memory usage"
        fi
    fi
}

# Measure CPU usage
measure_cpu() {
    local pid
    if [ -f "/tmp/hybrid-whisper-server.pid" ]; then
        pid=$(cat /tmp/hybrid-whisper-server.pid)
        cpu=$(ps -p "$pid" -o %cpu=)
        echo "CPU usage: ${cpu}%"

        if [ $(echo "$cpu > 80" | bc) -eq 1 ]; then
            echo "WARNING: High CPU usage"
        fi
    fi
}

# Run all checks
echo "=== Performance Check ==="
measure_transcription
measure_memory
measure_cpu
```

### Load Testing

```bash
#!/bin/bash
# load_test.sh

concurrent_users=10
test_audio="/tmp/test.wav"

echo "Starting load test with $concurrent_users concurrent users..."

for i in $(seq 1 $concurrent_users); do
    (
        while true; do
            curl -s -X POST \
                -F "audio_file=@$test_audio" \
                http://localhost:9099/sessions/$(uuidgen)/transcribe \
                > /dev/null
            sleep 1
        done
    ) &
done

echo "Load test running. Monitor with: top, htop"
echo "Stop with: pkill -f load_test"
```

---

## Alerting Setup

### AlertManager Configuration

Create `/etc/alertmanager/alertmanager.yml`:

```yaml
global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alerts@example.com'
  smtp_auth_username: 'alerts@example.com'
  smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

  routes:
    - match:
        severity: critical
      receiver: 'critical'

receivers:
  - name: 'default'
    email_configs:
      - to: 'team@example.com'
        headers:
          Subject: '[Hypr-Voice Alert] {{ .GroupLabels.alertname }}'

  - name: 'critical'
    email_configs:
      - to: 'oncall@example.com'
    webhook_configs:
      - url: 'http://slack-webhook-url'
```

### Prometheus Alert Rules

Create `/etc/prometheus/alerts.yml`:

```yaml
groups:
  - name: hypr_voice_alerts
    interval: 30s
    rules:
      # Service down
      - alert: ServiceDown
        expr: up{job=~"hypr-voice.*"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"
          description: "{{ $labels.job }} on {{ $labels.instance }} has been down for more than 1 minute."

      # High error rate
      - alert: HighErrorRate
        expr: rate(transcriptions_total{status="error"}[5m]) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate on {{ $labels.instance }}"
          description: "Error rate is {{ $value }} errors/sec"

      # High latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, rate(transcription_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High transcription latency"
          description: "95th percentile latency is {{ $value }}s"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.instance }}"
          description: "Memory usage is {{ $value | humanizePercentage }}"

      # High CPU usage
      - alert: HighCPUUsage
        expr: rate(process_cpu_seconds_total{job=~"hypr-voice.*"}[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.instance }}"
          description: "CPU usage is {{ $value | humanizePercentage }}"
```

---

## Dashboard Creation

### Grafana Dashboard JSON

Import this dashboard into Grafana:

```json
{
  "dashboard": {
    "title": "Hypr-Voice Monitoring",
    "panels": [
      {
        "title": "Service Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=~\"hypr-voice.*\"}"
          }
        ]
      },
      {
        "title": "Transcription Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(transcriptions_total[5m])"
          }
        ]
      },
      {
        "title": "Transcription Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(transcription_duration_seconds_bucket[5m]))"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "type": "graph",
        "targets": [
          {
            "expr": "active_sessions"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes"
          }
        ]
      },
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(process_cpu_seconds_total{job=~\"hypr-voice.*\"}[5m])"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(orchestrator_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(orchestrator_requests_total{status=\"error\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

### Quick Grafana Setup

```bash
# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server

# Access at http://localhost:3000
# Default credentials: admin/admin
```

---

## Service Availability

### Uptime Monitoring

```bash
#!/bin/bash
# uptime_monitor.sh

log_file="/var/log/hypr-voice-uptime.log"

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    for port in 9099 9093 9091 9095; do
        if nc -z localhost $port 2>/dev/null; then
            echo "$timestamp,UP,$port" >> "$log_file"
        else
            echo "$timestamp,DOWN,$port" >> "$log_file"
            # Send alert
            ./scripts/alert.sh "Service on port $port is down"
        fi
    done

    sleep 60
done
```

### Uptime Report

```bash
#!/bin/bash
# uptime_report.sh

log_file="/var/log/hypr-voice-uptime.log"

echo "=== Uptime Report (Last 24 Hours) ==="
echo ""

for port in 9099 9093 9091 9095; do
    total=$(grep ",$port$" "$log_file" | wc -l)
    up=$(grep "UP,$port$" "$log_file" | wc -l)
    uptime_percent=$(echo "scale=2; $up * 100 / $total" | bc)

    echo "Port $port: ${uptime_percent}% uptime"
done
```

---

## Resource Monitoring

### Real-Time Monitoring

```bash
#!/bin/bash
# real_time_monitor.sh

watch -n 2 '
echo "=== Hypr-Voice Resource Monitor ==="
echo ""
echo "CPU Usage:"
top -b -n 1 | grep -E "hypr|whisper|orchestrat" | head -5
echo ""
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h | grep -E "Filesystem|/opt|/tmp"
echo ""
echo "Network Connections:"
netstat -an | grep -E "9099|9093|9091|9095" | grep ESTABLISHED | wc -l
echo "active connections"
'
```

### Historical Monitoring

```bash
# Record metrics every minute
*/1 * * * * /opt/hypr-voice/scripts/record_metrics.sh

# record_metrics.sh
#!/bin/bash
timestamp=$(date '+%s')
cpu=$(top -b -n 1 | grep hybrid_server | awk '{print $9}')
mem=$(ps aux | grep hybrid_server | awk '{print $4}')
echo "$timestamp,$cpu,$mem" >> /var/log/hypr-voice-metrics.csv
```

---

## Integration with Monitoring Tools

### Uptime Robot (External)

```bash
# Add monitors via API
curl -X POST "https://uptimerobot.com/api/v2/newMonitor" \
  -d "api_key=YOUR_API_KEY" \
  -d "type=1" \
  -d "url=http://your-server.com:9099/health" \
  -d "friendly_name=Hypr-Voice Hybrid" \
  -d "interval=300"
```

### Datadog Integration

```python
# Install Datadog agent
pip install datadog

# Configure
from datadog import initialize, statsd

options = {
    'statsd_host': '127.0.0.1',
    'statsd_port': 8125
}

initialize(**options)

# Send metrics
statsd.increment('hypr.voice.transcriptions')
statsd.timing('hypr.voice.transcription_time', 500)
statsd.gauge('hypr.voice.active_sessions', 5)
```

### Custom Webhook Alerts

```bash
# alert.sh
#!/bin/bash
message="$1"
webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

curl -X POST -H 'Content-type: application/json' \
  --data "{\"text\":\"🚨 Hypr-Voice Alert: $message\"}" \
  "$webhook_url"
```

---

## Next Steps

1. Configure [Logging](logging.md)
2. Setup [Backups](backup-recovery.md)
3. Review [Security](security.md)
4. Optimize [Performance](performance-tuning.md)
