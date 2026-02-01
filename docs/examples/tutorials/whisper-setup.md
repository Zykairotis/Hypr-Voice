# Tutorial: Whisper STT Setup Guide

Learn how to set up and use Whisper speech-to-text in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Step 1: Choose Transcription Mode](#step-1-choose-transcription-mode)
- [Step 2: Wispr Flow Setup (Cloud)](#step-2-wispr-flow-setup-cloud)
- [Step 3: Local Whisper Setup](#step-3-local-whisper-setup)
- [Step 4: Basic Usage](#step-4-basic-usage)
- [Step 5: Vocabulary Enhancement](#step-5-vocabulary-enhancement)
- [Step 6: Advanced Configuration](#step-6-advanced-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

Hypr-Voice supports two transcription modes:

| Mode | Type | Cost | Quality | Setup Difficulty |
|------|------|------|---------|------------------|
| **FLOW** | Cloud API | Paid | Best | Easy |
| **LOCAL** | Local | Free | Good | Medium |

### Recommendation

- **Use FLOW** for production - Best accuracy, no setup
- **Use LOCAL** for development - Free, privacy-focused

---

## Step 1: Choose Transcription Mode

### Configure Mode

```bash
# In .env file
MODE=FLOW          # Use cloud API (recommended)
# or
MODE=LOCAL         # Use local Whisper server
```

### Flow Mode (Recommended)

```yaml
# .env or environment
MODE=FLOW
WISPR_FLOW_JWT_TOKEN=your_jwt_token
WISPR_FLOW_BASETEN_API_KEY=your_api_key
WISPR_FLOW_USER_UUID=your_uuid
```

### Local Mode

```yaml
# .env or environment
MODE=LOCAL
# Requires local Whisper server running
```

---

## Step 2: Wispr Flow Setup (Cloud)

Wispr Flow provides cloud-based transcription with excellent accuracy.

### Get API Credentials

1. Go to https://wispr-flow.baseten.co
2. Sign up for an account
3. Navigate to API settings
4. Get your:
   - JWT Token
   - Baseten API Key
   - User UUID

### Configure Environment Variables

```bash
# Add to .env file
cat >> .env << EOF
MODE=FLOW
WISPR_FLOW_JWT_TOKEN=your_jwt_token_here
WISPR_FLOW_BASETEN_API_KEY=your_baseten_key_here
WISPR_FLOW_USER_UUID=your_uuid_here
WISPR_FLOW_BASETEN_URL=https://chain-o232k03l.api.baseten.co/environments/production/run_remote
WISPR_FLOW_PORT=9095
WISPR_FLOW_TIMEOUT=600
EOF
```

### Performance Optimization

```bash
# Enable Opus encoding (10x faster uploads)
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_OPUS_BITRATE=24k

# Enable auto-chunking (for long recordings)
WISPR_FLOW_AUTO_CHUNK=1
WISPR_FLOW_CHUNK_SECONDS=30
WISPR_FLOW_CHUNK_OVERLAP=0.5

# Enable streaming mode (for 60s+ recordings)
FLOW_STREAMING_MODE=1
```

### Test Configuration

```python
import asyncio
from hypr_voice.whisper.client import WhisperClient

async def test_wispr():
    client = WhisperClient(mode="FLOW")

    # Test with a sample audio file
    result = await client.transcribe(
        audio_file="test.wav"
    )

    print(f"Transcription: {result['text']}")

if __name__ == "__main__":
    asyncio.run(test_wispr())
```

---

## Step 3: Local Whisper Setup

Local Whisper runs on your machine with no cloud dependency.

### Install Dependencies

```bash
# Install Whisper
pip install openai-whisper

# Install WhisperLive for real-time
pip install whisper-live

# Install faster-whisper (faster inference)
pip install faster-whisper

# Install audio dependencies
sudo apt-get install ffmpeg portaudio19-dev python3-pyaudio
```

### Download Model

```python
# Download Whisper model (runs automatically on first use)
import whisper

# Download small model (recommended)
model = whisper.load_model("small.en")

# Models available: tiny, base, small, medium, large
# English-only: tiny.en, base.en, small.en
print("Model downloaded!")
```

### Start Local Server

```bash
# Start WhisperLive server
cd /home/mewtwo/Zykairotis/Hypr-Voice
python -m hypr_voice.whisper.core.hybrid_server

# Server will start on port 9099
# ws://localhost:9099/ws for WebSocket
# http://localhost:9099 for REST API
```

### Configure Local Mode

```yaml
# config/hypr_voice/whisper/config.yaml

server:
  host: "0.0.0.0"
  port: 9099

backend:
  type: "faster_whisper"
  model_path: "small.en"         # Model size
  device: "cuda"                 # cpu or cuda
  language: "en"
  translate: false
```

### Test Local Server

```bash
# Test REST API
curl -X POST http://localhost:9099/transcribe \
  -F "audio_file=@test.wav"

# Test WebSocket
wscat -c ws://localhost:9099/ws
```

---

## Step 4: Basic Usage

### Simple Transcription

```python
import asyncio
from hypr_voice.whisper.client import WhisperClient

async def transcribe_file():
    # Create client
    client = WhisperClient(mode="FLOW")  # or "LOCAL"

    # Transcribe audio file
    result = await client.transcribe(
        audio_file="recording.wav"
    )

    print(f"Text: {result['text']}")
    print(f"Language: {result['language']}")
    print(f"Duration: {result['duration']}s")

if __name__ == "__main__":
    asyncio.run(transcribe_file())
```

### Real-time Transcription

```python
async def transcribe_stream():
    client = WhisperClient(mode="LOCAL")

    # Stream audio for real-time transcription
    async for transcription in client.transcribe_stream():
        print(f"Live: {transcription['text']}")
```

### With Language Detection

```python
async def detect_language():
    client = WhisperClient()

    result = await client.transcribe(
        audio_file="multilingual.wav",
        language=None  # Auto-detect
    )

    print(f"Detected: {result['language']}")
    print(f"Text: {result['text']}")
```

---

## Step 5: Vocabulary Enhancement

Improve transcription accuracy for technical terms.

### Enable Vocabulary

```yaml
# config/hypr_voice/whisper/vocabulary.yaml

global:
  technical_terms:
    - Kubernetes
    - Docker
    - TypeScript
    - PyTorch
    # Add your terms here

programming:
  keywords:
    - async
    - await
    - callback
    # Add programming terms
```

### Use Domain Vocabularies

```yaml
# config/hypr_voice/whisper/vocabularies/development.yaml

name: "Development"
description: "Software development vocabulary"

keywords:
  languages:
    - "python"
    - "javascript"
    - "rust"

  frameworks:
    - "react"
    - "django"
    - "fastapi"
```

### Transcribe with Vocabulary

```python
async def transcribe_with_vocab():
    client = WhisperClient()

    result = await client.transcribe(
        audio_file="tech_talk.wav",
        vocabulary="development"  # Use development vocabulary
    )

    print(f"Enhanced: {result['text']}")
```

---

## Step 6: Advanced Configuration

### Audio Configuration

```yaml
# config/hypr_voice/whisper/audio-profile.yaml

audio:
  channels: 1
  chunk_size: 2048
  format: int16
  sample_rate: 16000          # Whisper's native rate

pulseaudio:
  default_source: alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor
  device_name: HDMI Monitor
  device_type: monitor
```

### Performance Tuning

```yaml
# For faster transcription
ctranslate2:
  beam_size: 1               # Greedy decoding (fastest)
  inter_threads: 2
  intra_threads: 4

# For better accuracy
ctranslate2:
  beam_size: 5               # Beam search (slower but better)
  patience: 2.0
  inter_threads: 4
  intra_threads: 8
```

### Hybrid Mode

```yaml
hybrid:
  enabled: true
  protocol: "both"           # Both WebSocket and REST

  rest_api:
    enabled: true
    max_upload_size: 500     # MB

  websocket:
    enabled: true
    heartbeat_interval: 30   # seconds

  shared_model: true         # Share model between APIs
```

---

## Troubleshooting

### Flow Mode Issues

#### Issue: Authentication failed

```bash
# Error: Authentication failed

# Solution: Verify credentials
echo $WISPR_FLOW_JWT_TOKEN
echo $WISPR_FLOW_BASETEN_API_KEY

# Re-add to .env
cat >> .env << EOF
WISPR_FLOW_JWT_TOKEN=correct_token
WISPR_FLOW_BASETEN_API_KEY=correct_key
EOF
```

#### Issue: Slow transcription

```bash
# Solution: Enable Opus encoding
export WISPR_FLOW_USE_OPUS=1
export WISPR_FLOW_OPUS_BITRATE=24k

# Enable streaming mode
export FLOW_STREAMING_MODE=1
```

### Local Mode Issues

#### Issue: Model not found

```bash
# Error: Model not found

# Solution: Download model
python -c "import whisper; whisper.load_model('small.en')"

# Or set model path
export WHISPER_MODEL_PATH=/path/to/model
```

#### Issue: CUDA not available

```bash
# Error: CUDA not available

# Solution: Use CPU
export device="cpu"

# Or install CUDA
# See https://developer.nvidia.com/cuda-downloads
```

#### Issue: Server not starting

```bash
# Error: Port already in use

# Solution: Check port usage
lsof -i :9099

# Kill existing process
kill -9 <pid>

# Or use different port
export WHISPER_PORT=9100
```

### Audio Issues

#### Issue: No audio input

```bash
# Solution: Check audio devices
pactl list sources short

# Test microphone
arecord -f cd -d 5 test.wav

# Set default source
pactl set-default-source <source_name>
```

#### Issue: Poor quality

```bash
# Solution: Adjust sample rate
# Whisper works best with 16000 Hz

# Convert audio
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

---

## Performance Comparison

| Mode | Latency | Accuracy | Cost | Bandwidth |
|------|---------|----------|------|-----------|
| **FLOW + Opus** | ~1-2s | 97-99% | Paid | Low |
| **FLOW + WAV** | ~5-10s | 97-99% | Paid | High |
| **LOCAL (small)** | ~2-5s | 92-95% | Free | None |
| **LOCAL (medium)** | ~5-10s | 95-97% | Free | None |

---

## Best Practices

### For Production

```bash
# Use FLOW mode
MODE=FLOW

# Enable Opus for fast uploads
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_OPUS_BITRATE=24k

# Enable streaming for long recordings
FLOW_STREAMING_MODE=1

# Enable chunking
WISPR_FLOW_AUTO_CHUNK=1
WISPR_FLOW_CHUNK_SECONDS=30
```

### For Development

```bash
# Use LOCAL mode (free)
MODE=LOCAL

# Use small model (fast)
MODEL_SIZE=small.en

# Use CPU if no GPU
DEVICE=cpu
```

### For Best Accuracy

```yaml
# Use larger model
model_path: "medium.en"

# Enable vocabulary enhancement
vocabulary:
  enabled: true

# Use beam search
ctranslate2:
  beam_size: 5
  patience: 2.0
```

---

## Next Steps

Now that Whisper is set up:

- [Basic Usage Examples](../basic-usage.md) - More STT examples
- [Whisper Configuration](../../development/whisper-config.md) - Detailed config
- [Vocabulary Configuration](../../development/vocabulary-config.md) - Custom vocabularies
- [TTS Setup Tutorial](tts-setup.md) - Add text-to-speech

---

## See Also

- [Whisper Configuration](../../development/whisper-config.md)
- [Audio Profiles](../../development/audio-profiles.md)
- [Vocabulary Configuration](../../development/vocabulary-config.md)
