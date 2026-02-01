# Installation Guide

This guide will walk you through installing and setting up Hypr-Voice on your system.

## System Requirements

### Minimum Requirements
- **Operating System**: Linux (Ubuntu 22.04+, Arch Linux, or similar)
- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (for Web UI)
- **RAM**: 8 GB minimum, 16 GB recommended
- **Disk Space**: 10 GB free space
- **Microphone**: For voice input features

### Recommended Hardware
- **CPU**: Modern multi-core processor (Intel i5/i7/i9, AMD Ryzen 5/7/9, or Apple M1/M2/M3)
- **GPU**: Optional CUDA-capable GPU for faster Whisper processing
- **Audio**: USB microphone or built-in microphone

## Prerequisites

### 1. System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y nodejs npm
sudo apt install -y ffmpeg portaudio19-dev python3-dev
sudo apt install -y pulseaudio pulseaudio-utils
sudo apt install -y git curl wget
```

**Arch Linux:**
```bash
sudo pacman -S python python-pip python-virtualenv
sudo pacman -S nodejs npm
sudo pacman -S ffmpeg portaudio python
sudo pacman -S pulseaudio pulseaudio-utils
sudo pacman -S git curl wget
```

### 2. Audio System Setup

Ensure your audio system is working:

```bash
# Test PulseAudio
pactl info

# List available microphones
pactl list sources short

# Test microphone recording
parec -d @DEFAULT_SOURCE@ | aplay  # Press Ctrl+C to stop
```

## Installation Steps

### Step 1: Clone the Repository

```bash
git clone <repository-url>
cd Hypr-Voice
```

### Step 2: Install Python Dependencies

Create a virtual environment and install Python packages:

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install Hypr-Voice package in development mode
pip install -e .
```

### Step 3: Install Web UI Dependencies

```bash
cd web-ui
npm install
cd ..
```

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your API keys
nano .env  # or use your preferred editor
```

### Step 5: Obtain API Keys

You'll need API keys for the following services:

#### Required API Keys

1. **Cerebras AI** (Primary LLM)
   - Visit: https://cloud.cerebras.ai
   - Sign up and obtain your API key
   - Add to `.env`: `CEREBRAS_API_KEY_ONE=your_key_here`

2. **Wispr Flow** (Voice Transcription)
   - Visit: https://wispr-flow.baseten.co
   - Sign up and obtain:
     - JWT Token: `WISPR_FLOW_JWT_TOKEN`
     - Baseten API Key: `WISPR_FLOW_BASETEN_API_KEY`
     - User UUID: `WISPR_FLOW_USER_UUID`

3. **Text-to-Speech** (Choose One)
   - **Deepgram** (Recommended):
     - Visit: https://deepgram.com
     - Get API key: `DEEPGRAM_API_KEY`
   - **ElevenLabs**:
     - Visit: https://elevenlabs.io
     - Get API key: `ELEVENLABS_API_KEY`

#### Optional API Keys

- **Anthropic Claude** (via Z.ai proxy): `ANTHROPIC_AUTH_TOKEN`
- **Google Gemini**: `GEMINI_API_KEY`
- **CFS Image Generation**: `CFS_API_KEY`

### Step 6: Configure Audio Settings

Edit `config/hypr_voice/whisper/audio-profile.yaml`:

```yaml
# Find your microphone device name with: pactl list sources short
audio_source: "@DEFAULT_SOURCE@"  # Use default or specify device
sample_rate: 16000
channels: 1
```

### Step 7: Verify Installation

```bash
# Check Python packages
python -c "import hypr_voice; print('Hypr-Voice installed successfully')"

# Check web UI dependencies
cd web-ui
npm list --depth=0

# Test audio system
./scripts/utils/test_mic.sh
```

## Troubleshooting Installation Issues

### Python Issues

**Virtual environment creation fails:**
```bash
# Install python3-venv
sudo apt install python3-venv  # Ubuntu/Debian
sudo pacman -S python-virtualenv  # Arch
```

**Pip install errors:**
```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install with specific versions if needed
pip install --no-cache-dir -r requirements.txt
```

**PyAudio installation fails:**
```bash
# Ubuntu/Debian
sudo apt install portaudio19-dev python3-dev

# Arch Linux
sudo pacman -S portaudio python

# Then reinstall
pip install pyaudio
```

### Node.js Issues

**npm install fails:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and try again
rm -rf node_modules package-lock.json
npm install
```

**Node version too old:**
```bash
# Install nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install latest Node.js
nvm install node
nvm use node
```

### Audio Issues

**No microphone detected:**
```bash
# Check PulseAudio is running
pulseaudio --check

# Restart PulseAudio
pulseaudio --kill
pulseaudio --start

# List available devices
pactl list sources short

# Test recording
arecord -f cd -d 5 test.wav  # Records 5 seconds
aplay test.wav  # Play back
```

**Permission denied accessing microphone:**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER

# Log out and log back in for changes to take effect
```

### API Key Issues

**Authentication errors:**
- Verify API keys are correct in `.env` file
- Check for extra spaces or quotes around keys
- Ensure API keys are active and not expired
- Verify you have sufficient API credits/quota

## Post-Installation Checklist

Verify everything is set up correctly:

- [ ] Python 3.10+ installed
- [ ] Virtual environment created and activated
- [ ] All Python dependencies installed
- [ ] Node.js 18+ installed
- [ ] Web UI dependencies installed
- [ ] `.env` file configured with API keys
- [ ] Microphone working and configured
- [ ] Audio system (PulseAudio) running

## Next Steps

Once installation is complete, proceed to the [Quick Start Guide](./quickstart.md) to start using Hypr-Voice.

## Additional Resources

- [Configuration Guide](./features.md#configuration)
- [Troubleshooting](./troubleshooting.md)
- [Web UI Guide](./web-ui-guide.md)
- [CLI Guide](./cli-guide.md)
