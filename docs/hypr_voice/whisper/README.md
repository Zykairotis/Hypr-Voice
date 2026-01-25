# WhisperLive for Hypr-Voice

Real-time speech transcription using WhisperLive with optimized INT8 model support.

## 🗂️ Project Structure

```
src/whisper/
├── README.md                    # This file
├── start_whisper_live.py        # Main server entry point
├── whisper_live/                # WhisperLive library
│
├── config/                      # Configuration files
│   ├── config.yaml             # Main WhisperLive configuration
│   ├── audio-profile.yaml      # Audio device settings
│   └── .asoundrc               # ALSA configuration
│
├── scripts/                     # Executable scripts
│   ├── start_server.sh         # Start WhisperLive server
│   ├── start_client_mic.sh     # Start client with microphone
│   └── audio-setup.sh          # Audio configuration helper
│
├── docs/                        # Documentation
│   ├── README.md               # Detailed documentation
│   ├── QUICK_START.md          # Quick start guide
│   └── AUDIO_SETUP.md          # Audio configuration guide
│
├── examples/                    # Example scripts
│   ├── run_server.py           # Example server runner
│   ├── run_client.py           # Example client
│   └── test_client.py          # Client tests
│
├── data/                        # Data files
│   ├── harvard_resampled_resampled.wav
│   └── output.srt
│
└── logs/                        # Log directory
```

## 🚀 Quick Start

### 1. Start the Server

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/whisper
./scripts/start_server.sh start
```

**Server Details:**
- WebSocket: `ws://localhost:9099`
- Model: `openai/whisper-large-v3-turbo` (INT8 optimized)
- Device: CUDA
- Logs: `/tmp/whisper-live-hypr-voice.log`

### 2. Start the Client

```bash
./scripts/start_client_mic.sh
```

The client automatically uses your configured audio device (GA102 HDMI monitor).

## 📋 Available Commands

### Server Management

```bash
./scripts/start_server.sh start      # Start server
./scripts/start_server.sh stop       # Stop server
./scripts/start_server.sh restart    # Restart server
./scripts/start_server.sh status     # Check status
./scripts/start_server.sh logs       # View logs
./scripts/start_server.sh test       # Test WebSocket connection
```

### Audio Configuration

```bash
./scripts/audio-setup.sh list        # List audio devices
./scripts/audio-setup.sh current     # Show current config
./scripts/audio-setup.sh test        # Test recording (5s)
./scripts/audio-setup.sh apply       # Apply audio profile
```

## ⚙️ Configuration

### Main Configuration (`config/config.yaml`)

```yaml
server:
  host: "localhost"
  port: 9099
  max_clients: 4

backend:
  type: "faster_whisper"
  model_path: "openai/whisper-large-v3-turbo"
  device: "cuda"
  language: "auto"
```

### Audio Configuration (`config/audio-profile.yaml`)

```yaml
pulseaudio:
  default_source: "alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor"
  device_name: "GA102 High Definition Audio Controller"
```

## 📚 Documentation

- **[docs/README.md](docs/README.md)** - Complete documentation
- **[docs/QUICK_START.md](docs/QUICK_START.md)** - Quick start guide
- **[docs/AUDIO_SETUP.md](docs/AUDIO_SETUP.md)** - Audio setup guide

## 🎯 Features

- ✅ Real-time speech transcription
- ✅ INT8 optimized Whisper model
- ✅ CUDA acceleration
- ✅ PulseAudio integration
- ✅ Automatic audio device configuration
- ✅ WebSocket streaming
- ✅ Hypr-Voice integration ready

## 🔧 Requirements

- Python 3.12+ (uses `/home/mewtwo/Zykairotis/Hypr-Voice/.venv`)
- CUDA-capable GPU
- PulseAudio
- Dependencies: `faster-whisper`, `websockets`, `pyyaml`

## 📝 Logs

- Server logs: `/tmp/whisper-live-hypr-voice.log`
- PID file: `/tmp/whisper-live-server.pid`

View live logs:
```bash
tail -f /tmp/whisper-live-hypr-voice.log
```

## 🛠️ Development

### Run Examples

```bash
# Server example
python examples/run_server.py

# Client example
python examples/run_client.py

# Test client
python examples/test_client.py
```

### Project Root
```bash
PROJECT_ROOT=/home/mewtwo/Zykairotis/Hypr-Voice
WHISPER_ROOT=$PROJECT_ROOT/src/whisper
VENV_PATH=$PROJECT_ROOT/.venv
```

## 🐛 Troubleshooting

### Server won't start
```bash
./scripts/start_server.sh status
tail -f /tmp/whisper-live-hypr-voice.log
```

### Audio issues
```bash
./scripts/audio-setup.sh list
./scripts/audio-setup.sh test
pactl list sources short
```

### Check logs
```bash
tail -f /tmp/whisper-live-hypr-voice.log
```

## 📖 Related Documentation

- [WhisperLive Documentation](https://github.com/collabora/WhisperLive)
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper)
- [PulseAudio Documentation](https://www.freedesktop.org/wiki/Software/PulseAudio/)

---

**Part of the Hypr-Voice Project**  
Virtual Environment: `/home/mewtwo/Zykairotis/Hypr-Voice/.venv`
