# Deployment Guide - Hypr-Voice

Complete deployment guide for Hypr-Voice in various environments.

## Table of Contents

1. [Deployment Overview](#deployment-overview)
2. [Local Development Deployment](#local-development-deployment)
3. [Containerized Deployment](#containerized-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Production Deployment](#production-deployment)
6. [Environment Configuration](#environment-configuration)
7. [Service Dependencies](#service-dependencies)
8. [Health Verification](#health-verification)
9. [Troubleshooting Deployment](#troubleshooting-deployment)

---

## Deployment Overview

Hypr-Voice is a multi-service voice AI platform with the following components:

### Core Services

| Service | Port | Description |
|---------|------|-------------|
| **Hybrid Whisper Server** | 9099 | Real-time transcription (WebSocket + REST) |
| **Orchestrator** | 9093 | Agent routing and coordination |
| **Context WebSocket** | 9091 | Context management service |
| **Wispr Flow API** | 9095 | Optional cloud transcription backend |
| **Web UI Bridge** | 8934 | WebSocket proxy service |
| **Frontend** | 8933 | Web UI |

### Service Architecture

```
┌─────────────────┐
│   Web UI (8933) │
└────────┬────────┘
         │
┌────────▼────────┐
│  Bridge (8934)  │
└────────┬────────┘
         │
    ┌────┴────┬──────────┬─────────────┐
    │         │          │             │
┌───▼───┐ ┌──▼───┐  ┌───▼────┐  ┌────▼─────┐
│Hybrid│ │Orch. │  │Context │  │WisprFlow │
│9099  │ │9093  │  │  9091  │  │  9095    │
└───────┘ └──────┘  └────────┘  └──────────┘
```

---

## Local Development Deployment

### Prerequisites

```bash
# System requirements
- Linux (Arch/Ubuntu) or macOS
- Python 3.10+
- Node.js 18+ (for web UI)
- 8GB+ RAM (16GB recommended)
- 20GB+ disk space
- GPU with CUDA support (optional, for faster transcription)

# Audio subsystem
- PulseAudio (Linux)
- or PipeWire (Linux)
```

### Installation Steps

#### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/hypr-voice.git
cd hypr-voice

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 2. Configure Environment

```bash
# Copy example environment
cp .env.example .env

# Edit with your API keys
nano .env
```

**Minimum required variables:**

```bash
# Transcription
CEREBRAS_API_KEY_ONE=your_key_here
WISPR_FLOW_JWT_TOKEN=your_jwt_token
WISPR_FLOW_BASETEN_API_KEY=your_baseten_key
WISPR_FLOW_USER_UUID=your_uuid

# TTS (at least one)
DEEPGRAM_API_KEY=your_deepgram_key
# OR
ELEVENLABS_API_KEY=your_elevenlabs_key
```

#### 3. Start Services

**Option A: Start All Services**

```bash
./scripts/start_everything.sh start
```

**Option B: Start Individual Services**

```bash
# Hybrid Whisper Server
./scripts/start_hybrid_server.sh start

# Orchestrator
./scripts/start_everything.sh start  # Includes orchestrator

# Wispr Flow (if using MODE=FLOW)
./scripts/start_wispr_flow.sh start

# Context WebSocket
# Started automatically by start_everything.sh
```

#### 4. Verify Deployment

```bash
# Check all services
./scripts/start_everything.sh status

# Test health endpoints
curl http://localhost:9099/health   # Hybrid server
curl http://localhost:9093/health   # Orchestrator
curl http://localhost:9095/health   # Wispr Flow (if enabled)
```

---

## Containerized Deployment

### Docker Deployment

#### Prerequisites

```bash
# Install Docker
curl -fsSL https://get.docker.com | sh

# Install Docker Compose
sudo apt-get install docker-compose
```

#### Dockerfile Example

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    pulseaudio \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose ports
EXPOSE 9099 9093 9091 9095 8934 8933

# Set PYTHONPATH
ENV PYTHONPATH=/app/src

# Start hybrid server by default
CMD ["python", "src/hypr_voice/whisper/core/hybrid_server.py"]
```

#### Docker Compose Example

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  hybrid-whisper:
    build: .
    container_name: hypr-voice-hybrid
    ports:
      - "9099:9099"
    environment:
      - PYTHONPATH=/app/src
      - HYPR_VOICE_WHISPER_CONFIG_DIR=/app/config/hypr_voice/whisper
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - /tmp/whisper-models:/tmp/whisper-models
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  orchestrator:
    build: .
    container_name: hypr-voice-orchestrator
    ports:
      - "9093:9093"
    environment:
      - PYTHONPATH=/app/src
      - ORCHESTRATOR_PORT=9093
    volumes:
      - ./config:/app/config
      - ./.env:/app/.env
    restart: unless-stopped
    command: >
      bash -c "
        export PYTHONPATH=/app/src &&
        uvicorn hypr_voice.server:app
        --host 0.0.0.0 --port 9093
      "

  context-ws:
    build: .
    container_name: hypr-voice-context
    ports:
      - "9091:9091"
    environment:
      - PYTHONPATH=/app/src
    volumes:
      - ./config:/app/config
    restart: unless-stopped
    command: >
      python src/hypr_voice/whisper/context/context_websocket_server.py

volumes:
  whisper-models:
```

#### Build and Run

```bash
# Build images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## Cloud Deployment

### AWS Deployment

#### EC2 Instance Setup

```bash
# Launch EC2 instance
# - Instance type: g4dn.xlarge (GPU) or t3.large (CPU)
# - AMI: Ubuntu 22.04 LTS
# - Storage: 50GB GP3

# SSH into instance
ssh -i your-key.pem ubuntu@ec2-xxx.amazonaws.com

# Install dependencies
sudo apt-get update
sudo apt-get install -y python3.12 python3-venv git ffmpeg

# Clone repository
git clone https://github.com/yourusername/hypr-voice.git
cd hypr-voice

# Setup environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure .env
nano .env

# Start services
./scripts/start_everything.sh start
```

#### Security Group Rules

```
| Type    | Protocol | Port Range | Source       |
|---------|----------|------------|--------------|
| HTTP    | TCP      | 80         | 0.0.0.0/0    |
| HTTPS   | TCP      | 443        | 0.0.0.0/0    |
| Custom  | TCP      | 9099       | 0.0.0.0/0    |
| Custom  | TCP      | 9093       | 0.0.0.0/0    |
| Custom  | TCP      | 9091       | 0.0.0.0/0    |
| SSH     | TCP      | 22         | Your IP      |
```

#### Using NGINX Reverse Proxy

```nginx
# /etc/nginx/sites-available/hypr-voice
upstream hybrid_backend {
    server localhost:9099;
}

upstream orchestrator_backend {
    server localhost:9093;
}

server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 500M;

    location /api/hybrid/ {
        proxy_pass http://hybrid_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }

    location /api/orchestrator/ {
        proxy_pass http://orchestrator_backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://hybrid_backend/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Google Cloud Platform

#### Cloud Run Deployment

```bash
# Build and push container
gcloud builds submit --tag gcr.io/PROJECT_ID/hypr-voice

# Deploy to Cloud Run
gcloud run deploy hypr-voice \
  --image gcr.io/PROJECT_ID/hypr-voice \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 9099 \
  --memory 4Gi \
  --timeout 3600
```

#### Compute Engine

```bash
# Create instance
gcloud compute instances create hypr-voice-server \
  --zone=us-central1-a \
  --machine-type=n1-standard-4 \
  --image-family=ubuntu-2204-lts \
  --image-project=ubuntu-os-cloud \
  --boot-disk-size=50GB \
  --accelerator=type=nvidia-tesla-t4,count=1
```

---

## Production Deployment

### System Requirements

#### Minimum Specifications

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 8GB | 16GB+ |
| Storage | 20GB SSD | 50GB+ SSD |
| Network | 100 Mbps | 1 Gbps |
| GPU | None | NVIDIA GTX 1660+ |

#### Software Requirements

```
- OS: Ubuntu 22.04 LTS / Arch Linux / macOS 13+
- Python: 3.10+
- Node.js: 18+ (for web UI)
- FFmpeg: 4.0+
- PulseAudio or PipeWire
- CUDA: 11.8+ (for GPU acceleration)
```

### Production Setup

#### 1. User and Directory Setup

```bash
# Create dedicated user
sudo useradd -r -s /bin/bash hyprvoice
sudo mkdir -p /opt/hypr-voice
sudo chown hyprvoice:hyprvoice /opt/hypr-voice

# Setup directory structure
cd /opt/hypr-voice
mkdir -p {logs,var,config,backups}
```

#### 2. Systemd Services

Create `/etc/systemd/system/hypr-voice.service`:

```ini
[Unit]
Description=Hypr-Voice Orchestrator
After=network.target

[Service]
Type=simple
User=hyprvoice
WorkingDirectory=/opt/hypr-voice
Environment="PATH=/opt/hypr-voice/.venv/bin"
Environment="PYTHONPATH=/opt/hypr-voice/src"
ExecStart=/opt/hypr-voice/.venv/bin/python \
    -m uvicorn hypr_voice.server:app \
    --host 0.0.0.0 --port 9093
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hypr-voice
sudo systemctl start hypr-voice
sudo systemctl status hypr-voice
```

#### 3. Log Rotation

Create `/etc/logrotate.d/hypr-voice`:

```
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
        systemctl reload hypr-voice > /dev/null 2>&1 || true
    endscript
}
```

---

## Environment Configuration

### Configuration Files

```bash
/opt/hypr-voice/
├── .env                    # Environment variables
├── config/
│   └── hypr_voice/
│       └── whisper/
│           ├── config.yaml         # Whisper config
│           ├── audio-profile.yaml  # Audio settings
│           └── vocabulary.yaml     # Custom vocab
└── logs/                    # Application logs
```

### Key Environment Variables

```bash
# Service Ports
ORCHESTRATOR_PORT=9093
WISPR_FLOW_PORT=9095

# API Keys
CEREBRAS_API_KEY_ONE=sk-xxx
DEEPGRAM_API_KEY=xxx
ELEVENLABS_API_KEY=xxx

# Transcription Settings
MODE=FLOW  # or LOCAL
WISPR_FLOW_USE_OPUS=1
FLOW_STREAMING_MODE=1

# TTS Settings
HYPR_VOICE_TTS_STREAMING=1
HYPR_VOICE_TTS_PROVIDER=deepgram

# Logging
HYPR_VOICE_TRACE=0  # Disable in production
```

---

## Service Dependencies

### External APIs

| Service | Purpose | Required |
|---------|---------|----------|
| Cerebras | LLM inference | Yes |
| Wispr Flow | Transcription (MODE=FLOW) | Yes* |
| Deepgram | Text-to-speech | Yes* |
| ElevenLabs | Alternative TTS | Optional |

*At least one TTS provider required

### Internal Dependencies

```
Orchestrator (9093)
  ├─► Hybrid Whisper (9099) [MODE=LOCAL]
  ├─► Wispr Flow API (9095) [MODE=FLOW]
  ├─► Context WebSocket (9091)
  └─► TTS Provider (Deepgram/ElevenLabs)
```

---

## Health Verification

### Health Check Endpoints

```bash
# Hybrid Whisper Server
curl http://localhost:9099/health

# Orchestrator
curl http://localhost:9093/health

# Wispr Flow API
curl http://localhost:9095/health

# Context WebSocket
curl http://localhost:9091/health
```

### Expected Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-26T10:30:00.000000",
  "version": "0.2.0"
}
```

### Service Status Script

```bash
#!/bin/bash
# check_services.sh

services=(
    "9099:Hybrid Whisper"
    "9093:Orchestrator"
    "9091:Context WebSocket"
    "9095:Wispr Flow"
)

for service in "${services[@]}"; do
    IFS=':' read -r port name <<< "$service"
    if curl -s "http://localhost:$port/health" > /dev/null; then
        echo "✓ $name (port $port): Healthy"
    else
        echo "✗ $name (port $port): Unhealthy"
    fi
done
```

---

## Troubleshooting Deployment

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
sudo lsof -i :9099

# Kill process
sudo kill -9 <PID>

# Or change port in .env
WISPR_FLOW_PORT=9096
```

#### 2. Permission Denied

```bash
# Fix directory permissions
sudo chown -R $USER:$USER /opt/hypr-voice
chmod +x scripts/*.sh
```

#### 3. Module Not Found

```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/hypr-voice/src:$PYTHONPATH

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### 4. GPU Not Detected

```bash
# Check CUDA installation
nvidia-smi

# Verify PyTorch CUDA support
python -c "import torch; print(torch.cuda.is_available())"

# Install CUDA toolkit
sudo apt-get install nvidia-cuda-toolkit
```

#### 5. Audio Device Not Found

```bash
# List PulseAudio sources
pactl list short sources

# Update config
# Edit config/hypr_voice/whisper/audio-profile.yaml
# Set correct pulseaudio_source
```

### Debug Mode

```bash
# Enable detailed logging
export HYPR_VOICE_TRACE=1
export HYPR_VOICE_FLOW_TRACE=1

# Check logs
tail -f /opt/hypr-voice/logs/hybrid-whisper.log
tail -f /opt/hypr-voice/logs/orchestrator.log

# Systemd logs
sudo journalctl -u hypr-voice -f
```

---

## Deployment Checklist

- [ ] System requirements met (CPU, RAM, storage)
- [ ] Dependencies installed (Python, FFmpeg, audio)
- [ ] Virtual environment created
- [ ] Required packages installed
- [ ] .env file configured with API keys
- [ ] Audio device configured
- [ ] Firewall ports opened
- [ ] Services started and verified
- [ ] Health checks passing
- [ ] Log rotation configured
- [ ] Backups configured
- [ ] Monitoring setup
- [ ] Documentation reviewed

---

## Next Steps

After deployment:

1. Review [System Requirements](system-requirements.md)
2. Setup [Service Management](service-management.md)
3. Configure [Monitoring](monitoring.md)
4. Implement [Logging](logging.md)
5. Setup [Backups](backup-recovery.md)
6. Review [Security](security.md)
7. Optimize [Performance](performance-tuning.md)
