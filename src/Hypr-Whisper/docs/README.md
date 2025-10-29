# Final WhisperLive - Essential Files Only

**Minimal WhisperLive implementation for Hypr-Voice**  
Real-time transcription with faster-whisper INT8 backend

---

## 📦 What's Included (4,659 lines)

### Core Library (`whisper_live/`)
- `client.py` (827 lines) - Audio capture & WebSocket client
- `server.py` (328 lines) - Simplified WebSocket server  
- `vad.py` (157 lines) - Voice Activity Detection
- `utils.py` (83 lines) - Helper functions

### Faster-Whisper Backend (`whisper_live/backend/`)
- `base.py` (379 lines) - Base backend class
- `faster_whisper_backend.py` (237 lines) - INT8 GPU implementation

### Transcriber (`whisper_live/transcriber/`)
- `transcriber_faster_whisper.py` (1,888 lines) - Whisper model wrapper

### Configuration & Scripts
- `config.yaml` - Server & audio configuration
- `start_server.sh` - Server startup script
- `start_client_mic.sh` - Client with audio device config
- `start_whisper_live.py` - Python server launcher
- `test_client.py` - Connection test script
- `run_server.py` - Alternative server launcher
- `run_client.py` - Alternative client launcher

---

## 🚀 Quick Start

### 1. Start Server
```bash
./start_server.sh start
```

### 2. Test with Microphone
```bash
./start_client_mic.sh
```

### 3. Test with Audio File
```bash
python run_client.py -f audio.mp3
```

---

## ⚙️ Configuration

Edit `config.yaml`:

```yaml
# Model
backend:
  model_path: "openai/whisper-large-v3-turbo"
  device: "cuda"

# Audio Input (PulseAudio)
audio:
  pulseaudio_source: "alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor"
  
# Server
server:
  port: 9090
  max_clients: 4
```

---

## 📊 What Was Removed

**From original 5,867 lines → 4,659 lines (21% reduction)**

Removed backends:
- ❌ TensorRT backend (689 lines)
- ❌ OpenVINO backend (171 lines)
- ❌ Translation backend (218 lines)
- ❌ Related transcribers and utilities

---

## 🎯 Tech Stack

- **Model**: openai/whisper-large-v3-turbo (INT8 quantization)
- **Backend**: faster-whisper with CTranslate2
- **GPU**: CUDA with INT8 (~2.7GB VRAM)
- **Audio**: PyAudio + PulseAudio/PipeWire
- **Server**: WebSocket (ws://)

---

## 📝 Requirements

```bash
pip install faster-whisper websockets pyaudio pyyaml numpy
```

Or use project venv:
```bash
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
```

---

## 🔧 Troubleshooting

**No audio input?**
```bash
# Set default audio source
pactl set-default-source alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor
```

**Model not loading?**
- Check CUDA available: `nvidia-smi`
- First connection downloads & converts model (~7 min)
- Subsequent connections are instant

**VAD filtering everything?**
- Set `use_vad=False` in client
- Or lower `vad_threshold` in config.yaml

---

## 📁 File Structure

```
src/Hypr-Whisper/
├── whisper_live/
│   ├── client.py              # Audio capture & streaming
│   ├── server.py              # WebSocket server
│   ├── vad.py                 # Voice activity detection
│   ├── utils.py               # Helpers
│   ├── backend/
│   │   ├── base.py           # Backend base class
│   │   └── faster_whisper_backend.py  # INT8 GPU backend
│   └── transcriber/
│       └── transcriber_faster_whisper.py  # Model wrapper
├── config.yaml                # Configuration
├── start_server.sh            # Server launcher
├── start_client_mic.sh        # Client launcher
└── README.md                  # This file
```

---

**Status**: ✅ Production ready  
**VRAM Usage**: ~2.7GB (INT8)  
**Latency**: Real-time (~100-300ms)
