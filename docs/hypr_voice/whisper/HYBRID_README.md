# Hybrid WhisperLive System

A unified transcription server supporting both **WebSocket** (real-time streaming) and **REST API** (file uploads) protocols.

## 🎯 Key Features

### Dual Protocol Support
| Feature | REST API | WebSocket | Use Case |
|---------|----------|-----------|----------|
| **File Uploads** | ✅ | ❌ | Batch processing, video/audio files |
| **Live Streaming** | ❌ | ✅ | Real-time transcription |
| **Latency** | Higher | Lower | REST for accuracy, WS for speed |
| **Format** | Any audio/video | PCM Float32 16kHz | REST flexible, WS optimized |
| **Session** | Manual | Auto-managed | REST explicit, WS automatic |

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/mewtwo/Zykairotis/hybrid-whisper-worktree/src/whisper
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Hybrid Server

```bash
# Make script executable
chmod +x scripts/start_hybrid_server.sh

# Start server
./scripts/start_hybrid_server.sh start

# Check status
./scripts/start_hybrid_server.sh status

# View logs
./scripts/start_hybrid_server.sh logs
```

### 3. Access Endpoints

- **REST API**: http://localhost:9099
- **API Docs**: http://localhost:9099/docs
- **WebSocket**: ws://localhost:9099/ws/{session_id}

## 📡 REST API Usage

### Create Session
```bash
curl -X POST http://localhost:9099/sessions \
  -H "Content-Type: application/json" \
  -d '{"language": "en", "beam_size": 3, "vad_filter": true}'
```

### Upload File for Transcription
```bash
# Upload audio/video file
curl -X POST http://localhost:9099/sessions/{session_id}/transcribe \
  -F "audio_file=@/path/to/file.mp4"
```

### Get Transcription Result
```bash
curl http://localhost:9099/sessions/{session_id}
```

### List All Sessions
```bash
curl http://localhost:9099/sessions
```

### Delete Session
```bash
curl -X DELETE http://localhost:9099/sessions/{session_id}
```

## 🔌 WebSocket Usage

### Python Client Example

```python
from hybrid_client import HybridWhisperClient

# Initialize client
client = HybridWhisperClient("http://localhost:9099")

# Stream from microphone
import asyncio
asyncio.run(client.stream_microphone_ws(device=0))
```

### Command Line Client

```bash
# List audio devices
python hybrid_client.py --list-devices

# Stream from microphone (WebSocket)
python hybrid_client.py --stream --device 0

# Transcribe file (REST API)
python hybrid_client.py --file video.mp4

# List active sessions
python hybrid_client.py --list-sessions
```

## 🛠️ Configuration

Edit `config/config.yaml`:

```yaml
# Server Settings
server:
  host: "0.0.0.0"
  port: 9099
  max_clients: 10

# Hybrid Mode
hybrid:
  enabled: true
  protocol: "both"  # Options: websocket, rest, both
  shared_model: true  # Share model between protocols

# Model Settings
backend:
  model_path: "openai/whisper-large-v3-turbo"
  device: "cuda"
  compute_type: "int8_float16"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│           Hybrid Server                  │
├─────────────┬───────────────────────────┤
│  REST API   │      WebSocket             │
├─────────────┴───────────────────────────┤
│         Shared Model Manager             │
├──────────────────────────────────────────┤
│     Faster-Whisper (CTranslate2)        │
└──────────────────────────────────────────┘
```

### Key Components

1. **TranscriptionSession**: Manages audio queue and transcription state
2. **Shared Model**: Single model instance for both protocols
3. **Background Tasks**: Async file processing for REST API
4. **WebSocket Handler**: Real-time audio streaming
5. **Session Manager**: Tracks active transcription sessions

## 📊 Performance Optimization

### GPU Settings (CUDA)
- Model: `openai/whisper-large-v3-turbo`
- Compute Type: `int8_float16` (reduced VRAM)
- Device: `cuda`

### CPU Settings
- Compute Type: `int8`
- Threads: 4
- Workers: 2

## 🔍 Testing

### Test REST API
```bash
# Create session
SESSION_ID=$(curl -s -X POST http://localhost:9099/sessions | jq -r '.session_id')

# Upload file
curl -X POST http://localhost:9099/sessions/$SESSION_ID/transcribe \
  -F "audio_file=@test.wav"

# Get result
curl http://localhost:9099/sessions/$SESSION_ID
```

### Test WebSocket
```python
# test_ws.py
import asyncio
import websockets
import numpy as np
import uuid

async def test():
    session_id = str(uuid.uuid4())
    uri = f"ws://localhost:9099/ws/{session_id}"
    
    async with websockets.connect(uri) as ws:
        # Send test audio
        audio = np.random.randn(16000).astype(np.float32)
        await ws.send(audio.tobytes())
        
        # Receive transcription
        response = await ws.recv()
        print(f"Received: {response}")

asyncio.run(test())
```

## 🐛 Troubleshooting

### Server won't start
```bash
# Check if port is in use
lsof -i :9099

# Check logs
tail -f /tmp/hybrid-whisper-server.log

# Verify dependencies
python -c "import fastapi, websockets, faster_whisper"
```

### CUDA issues
```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Use CPU fallback
# Edit config.yaml: device: "cpu"
```

### Audio device issues
```bash
# List devices
python hybrid_client.py --list-devices --detailed-devices

# Test specific device
python hybrid_client.py --test-audio 0 --test-duration 3
```

## 📝 API Documentation

When server is running, visit:
- **Interactive Docs**: http://localhost:9099/docs
- **OpenAPI Schema**: http://localhost:9099/openapi.json

## 🔗 Integration with Hypr-Voice

This hybrid server is designed to integrate with the Hypr-Voice system:

1. **Shared Virtual Environment**: Uses `/home/mewtwo/Zykairotis/Hypr-Voice/.venv`
2. **Compatible Port**: Runs on port 9099 (doesn't conflict with Agent on 8922)
3. **Audio Config**: Supports GA102 HDMI monitor input
4. **Model Optimization**: INT8 quantization for faster inference

## 📈 Monitoring

### Check active sessions
```bash
curl http://localhost:9099/sessions | python -m json.tool
```

### Server health
```bash
./scripts/start_hybrid_server.sh status
```

### Resource usage
```bash
# GPU memory (if using CUDA)
nvidia-smi

# CPU/Memory
htop
```

## 🚧 Future Enhancements

- [ ] Authentication & API keys
- [ ] Rate limiting
- [ ] Job queue for large files
- [ ] Translation support
- [ ] Speaker diarization
- [ ] WebRTC support
- [ ] Prometheus metrics
- [ ] Docker deployment

---

**Part of the Hypr-Voice Project**  
Virtual Environment: `/home/mewtwo/Zykairotis/Hypr-Voice/.venv`
