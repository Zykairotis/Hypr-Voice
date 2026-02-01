# System Requirements - Hypr-Voice

Detailed hardware and software requirements for running Hypr-Voice.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Network Requirements](#network-requirements)
4. [Storage Requirements](#storage-requirements)
5. [Audio Requirements](#audio-requirements)
6. [GPU Requirements](#gpu-requirements)
7. [Environment-Specific Requirements](#environment-specific-requirements)
8. [Compatibility Matrix](#compatibility-matrix)

---

## Hardware Requirements

### Minimum Configuration

**Suitable for: Development, testing, light usage**

| Component | Specification | Notes |
|-----------|---------------|-------|
| **CPU** | 4 cores @ 2.0GHz | Intel i5 / AMD Ryzen 5 or better |
| **RAM** | 8 GB | DDR4 |
| **Storage** | 20 GB SSD | NVMe or SATA SSD |
| **Network** | 100 Mbps | Wired connection recommended |
| **GPU** | Not required | CPU-only mode |

**Estimated Performance:**
- Transcription: ~2-3x real-time
- Concurrency: 1-2 users
- Response latency: 500-1000ms

### Recommended Configuration

**Suitable for: Production, moderate usage**

| Component | Specification | Notes |
|-----------|---------------|-------|
| **CPU** | 8 cores @ 3.0GHz+ | Intel i7 / AMD Ryzen 7 or better |
| **RAM** | 16 GB | DDR4 or DDR5 |
| **Storage** | 50 GB NVMe SSD | Fast I/O for model loading |
| **Network** | 1 Gbps | Low latency connection |
| **GPU** | NVIDIA GTX 1660+ | 6GB+ VRAM |

**Estimated Performance:**
- Transcription: ~0.5-1x real-time
- Concurrency: 5-10 users
- Response latency: 100-300ms

### High-Performance Configuration

**Suitable for: Enterprise, high load**

| Component | Specification | Notes |
|-----------|---------------|-------|
| **CPU** | 16+ cores @ 3.5GHz+ | Intel i9 / AMD Ryzen 9 or Xeon |
| **RAM** | 32 GB+ | DDR5 |
| **Storage** | 100 GB NVMe Gen4 | Enterprise-grade |
| **Network** | 10 Gbps | Datacenter connectivity |
| **GPU** | NVIDIA RTX 3090 / A10 | 24GB+ VRAM |

**Estimated Performance:**
- Transcription: <0.3x real-time
- Concurrency: 20+ users
- Response latency: <100ms

---

## Software Requirements

### Operating System

#### Supported Systems

| OS | Version | Status | Notes |
|----|---------|--------|-------|
| **Ubuntu** | 22.04 LTS | ✅ Fully Supported | Recommended for production |
| **Ubuntu** | 20.04 LTS | ✅ Supported | Stable option |
| **Arch Linux** | Rolling | ✅ Supported | Active development platform |
| **Debian** | 11+ | ✅ Supported | Stable server OS |
| **Fedora** | 37+ | ✅ Supported | Latest packages |
| **macOS** | 13+ (Ventura) | ⚠️ Partial | Some features limited |
| **Windows** | 10/11 | ❌ Not Supported | WSL2 may work |

#### Kernel Requirements (Linux)

```bash
# Minimum kernel version
# 5.10+ for full feature support

# Check kernel version
uname -r

# Required kernel modules
snd-aloop          # Audio loopback
snd-pulseaudio     # PulseAudio support
snd-core           # Core sound support
```

### Python Environment

```bash
# Python version
Python 3.10.x      # Minimum
Python 3.11.x      # Recommended
Python 3.12.x      # Latest tested

# Virtual environment
venv               # Built-in
virtualenv         # Alternative

# Package managers
pip 23.0+          # Package installation
uv (optional)      # Faster package manager
```

### Node.js (Web UI)

```bash
# Node.js version
Node.js 18.x       # Minimum LTS
Node.js 20.x       # Recommended LTS

# Package managers
npm 9.0+           # Default
yarn 1.22+         # Alternative
pnpm 8.0+          # Fast alternative
```

### System Dependencies

#### Linux (Ubuntu/Debian)

```bash
# Core dependencies
sudo apt-get update
sudo apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3-pip \
    git \
    wget \
    curl

# Audio dependencies
sudo apt-get install -y \
    ffmpeg \
    portaudio19-dev \
    libportaudio2 \
    libportaudiocpp0 \
    pulseaudio \
    pulseaudio-utils

# Audio processing
sudo apt-get install -y \
    sox \
    libsox-dev \
    libsox-fmt-all

# System utilities
sudo apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libopencv-dev \
    python3-dev
```

#### Linux (Arch)

```bash
# Core dependencies
sudo pacman -S \
    python python-pip \
    git base-devel \
    ffmpeg pulseaudio \
    portaudio opencv \
    cmake pkgconf

# Audio
sudo pacman -S \
    pulseaudio pulseaudio-alsa \
    alsa-plugins sox
```

#### macOS

```bash
# Install Homebrew if not present
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Core dependencies
brew install python@3.12
brew install git
brew install ffmpeg
brew install portaudio

# Audio utilities
brew install sox
```

---

## Network Requirements

### Bandwidth Requirements

| Usage Level | Bandwidth | Concurrent Users | Latency |
|------------|-----------|------------------|---------|
| **Development** | 10 Mbps | 1-2 | <50ms |
| **Small Production** | 100 Mbps | 5-10 | <30ms |
| **Medium Production** | 1 Gbps | 10-50 | <20ms |
| **Large Scale** | 10 Gbps | 50+ | <10ms |

### Port Requirements

#### Internal Ports (Localhost)

| Port | Service | Direction | Required |
|------|---------|-----------|----------|
| 9099 | Hybrid Whisper Server | Internal | Yes |
| 9093 | Orchestrator | Internal | Yes |
| 9091 | Context WebSocket | Internal | Yes |
| 9095 | Wispr Flow API | Internal | Optional |
| 8934 | Web UI Bridge | Internal | Optional |
| 8933 | Web UI Frontend | External | Optional |

#### External Ports (Public)

| Port | Service | Direction | Required |
|------|---------|-----------|----------|
| 80 | HTTP (proxy) | Inbound | Optional |
| 443 | HTTPS (proxy) | Inbound | Optional |
| 22 | SSH | Inbound | Admin |

#### Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# firewalld (Fedora/RHEL)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --reload

# iptables (raw)
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
```

### DNS Requirements

```
# Required for external access
hypr-voice.example.com      A    <server-ip>
api.hypr-voice.example.com  A    <server-ip>

# Optional subdomains
ws.hypr-voice.example.com   A    <server-ip>
```

---

## Storage Requirements

### Disk Space Breakdown

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **Base Installation** | 2 GB | 5 GB | Code + dependencies |
| **Whisper Models** | 2 GB | 5 GB | small.en model |
| **Large Models** | 5 GB | 15 GB | medium/large models |
| **Audio Cache** | 5 GB | 20 GB | Temporary audio files |
| **Logs** | 1 GB | 10 GB | Rotated logs |
| **Backups** | 10 GB | 50 GB | Config + data backups |
| **Total** | **25 GB** | **105 GB** | All components |

### I/O Performance

| Operation | Minimum | Recommended | Performance Impact |
|-----------|---------|-------------|-------------------|
| **Model Loading** | 100 MB/s | 500 MB/s | Startup time |
| **Audio Processing** | 50 MB/s | 200 MB/s | Real-time transcription |
| **Log Writing** | 10 MB/s | 50 MB/s | Concurrent users |

### Storage Configuration

```bash
# Recommended filesystem
ext4        # Default, stable
xfs         # Better for large files
btrfs       # Snapshots and compression (optional)

# Mount options
defaults,noatime  # Better performance
```

---

## Audio Requirements

### Audio Subsystem

#### Linux Audio Systems

| System | Support | Notes |
|--------|---------|-------|
| **PulseAudio** | ✅ Full | Default for most distros |
| **PipeWire** | ✅ Full | Modern replacement |
| **ALSA** | ⚠️ Direct | Use PulseAudio wrapper |

#### Audio Configuration

```bash
# List audio devices
pactl list short sources
pactl list short sinks

# Test audio recording
arecord -f S16_LE -c 1 -r 16000 -t wav test.wav

# Test audio playback
aplay test.wav
```

### Audio Device Requirements

| Requirement | Specification |
|-------------|---------------|
| **Sample Rate** | 16 kHz (recommended) |
| **Channels** | 1 (mono) or 2 (stereo) |
| **Format** | S16_LE (16-bit little-endian) |
| **Latency** | <100ms for real-time |

### Audio Codecs

**Supported Input Formats:**
- WAV (PCM)
- MP3
 FLAC
- OGG
- M4A
- WebM

**Supported Output Formats:**
- WAV (for TTS)
- Opus (streaming)
- MP3 (optional)

---

## GPU Requirements

### NVIDIA GPUs

#### Supported Models

| GPU Series | VRAM | Performance | Recommended For |
|------------|------|-------------|-----------------|
| **GTX 1650** | 4GB | Entry | Development |
| **GTX 1660** | 6GB | Good | Small production |
| **RTX 3060** | 12GB | Very Good | Medium production |
| **RTX 3070** | 8GB | Excellent | Large production |
| **RTX 3080** | 10GB | Excellent | High load |
| **RTX 3090** | 24GB | Outstanding | Enterprise |
| **RTX 4090** | 24GB | Best | Maximum performance |
| **A10/A100** | 24GB+ | Enterprise | Datacenter |

#### CUDA Requirements

```bash
# CUDA toolkit
CUDA 11.8+    # Minimum
CUDA 12.1+    # Recommended

# cuDNN
cuDNN 8.6+    # For Deep Learning

# Verify CUDA
nvidia-smi
nvcc --version

# Test PyTorch CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

### CPU-Only Mode

**Performance Expectations:**
- Transcription: 2-3x real-time
- Latency: 500-1000ms
- Concurrency: Limited to 1-2 users

**Optimization for CPU:**
```bash
# Use smaller model
backend:
  model_path: "tiny.en"  # or "base.en"

# Increase threads
performance:
  omp_num_threads: 8

# Enable optimizations
model:
  compute_type: "int8"  # Quantization
```

---

## Environment-Specific Requirements

### Development Environment

```bash
# Minimal setup
- 4 CPU cores
- 8 GB RAM
- 20 GB SSD
- No GPU required
- Local deployment only
```

### Production Environment

```bash
# Recommended setup
- 8+ CPU cores
- 16 GB+ RAM
- 50 GB+ NVMe SSD
- GPU recommended
- Load balancer
- Reverse proxy
```

### Cloud Environment

#### AWS EC2

```
Instance Types:
- t3.large (2 vCPU, 8 GB RAM) - Development
- g4dn.xlarge (4 vCPU, 16 GB RAM, GPU) - Production
- g4dn.2xlarge (8 vCPU, 32 GB RAM, GPU) - High load
- p3.2xlarge (8 vCPU, 61 GB RAM, GPU) - Enterprise
```

#### Google Cloud Platform

```
Instance Types:
- e2-standard-4 (4 vCPU, 16 GB RAM) - Development
- n1-standard-4 (4 vCPU, 15 GB RAM) - Production
- n1-highmem-4 (4 vCPU, 26 GB RAM) - Memory intensive
- a2-highgpu-1g (12 vCPU, 85 GB RAM, GPU) - Enterprise
```

#### Azure

```
Instance Types:
- Standard_D4s_v3 (4 vCPU, 16 GB RAM) - Development
- Standard_NC4as_T4_v3 (4 vCPU, 28 GB RAM, GPU) - Production
- Standard_NC6s_v3 (6 vCPU, 112 GB RAM, GPU) - High load
```

---

## Compatibility Matrix

### Component Versions

| Component | Version | Status | Notes |
|-----------|---------|--------|-------|
| **Python** | 3.10+ | ✅ Required | 3.12 recommended |
| **Node.js** | 18+ | ✅ Required (Web UI) | 20 LTS recommended |
| **FastAPI** | 0.100+ | ✅ Required | API framework |
| **Uvicorn** | 0.22+ | ✅ Required | ASGI server |
| **PyTorch** | 2.0+ | ✅ Required | ML framework |
| **Transformers** | 4.30+ | ✅ Required | NLP models |
| **faster-whisper** | 0.10+ | ✅ Required | Transcription |
| **FFmpeg** | 4.0+ | ✅ Required | Audio processing |

### API Compatibility

| Provider | API Version | Status |
|----------|-------------|--------|
| **Cerebras** | v1 | ✅ Supported |
| **Deepgram** | v1 | ✅ Supported |
| **ElevenLabs** | v1 | ✅ Supported |
| **Anthropic** | v1 | ✅ Supported |
| **Gemini** | v1 | ✅ Supported |

### Browser Compatibility (Web UI)

| Browser | Version | Status |
|---------|---------|--------|
| **Chrome** | 100+ | ✅ Full support |
| **Firefox** | 100+ | ✅ Full support |
| **Safari** | 15+ | ⚠️ Some limitations |
| **Edge** | 100+ | ✅ Full support |

---

## Resource Estimation

### User Capacity Planning

| Configuration | Concurrent Users | Hourly Requests | Daily Users |
|---------------|------------------|-----------------|-------------|
| **Minimum** | 1-2 | 60 | 5-10 |
| **Recommended** | 5-10 | 300 | 25-50 |
| **High-Perf** | 20+ | 1200+ | 100+ |

### Memory Usage Per Service

```
Hybrid Whisper Server:   1-2 GB (CPU) / 3-4 GB (GPU)
Orchestrator:            500 MB - 1 GB
Context WebSocket:       200-500 MB
Wispr Flow API:          500 MB - 1 GB
Web UI:                  200-500 MB
Total (without models):  3-6 GB
Whisper Models:          1-5 GB
Total Requirement:       8-16 GB recommended
```

### CPU Usage Patterns

```
Idle (no requests):           <5% 1 core
Light load (1-2 users):       20-40% 2 cores
Moderate load (5-10 users):   50-80% 4 cores
Heavy load (20+ users):       80-100% 8+ cores
```

---

## Verification Checklist

Before deployment, verify:

- [ ] OS version compatible
- [ ] Python 3.10+ installed
- [ ] Virtual environment created
- [ ] Sufficient RAM available
- [ ] Sufficient disk space
- [ ] Audio subsystem working
- [ ] Network ports available
- [ ] GPU drivers installed (if using GPU)
- [ ] CUDA toolkit installed (if using GPU)
- [ ] All dependencies installed
- [ ] Environment variables configured
- [ ] Services can start successfully
- [ ] Health checks passing

---

## Next Steps

1. Deploy using [Deployment Guide](deployment.md)
2. Setup [Service Management](service-management.md)
3. Configure [Monitoring](monitoring.md)
4. Implement [Logging](logging.md)
