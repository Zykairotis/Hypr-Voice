# 🚀 Quick Start Guide

## One-Command Start

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper

# Start server
./start_server.sh start

# In another terminal - Start live transcription
./start_client_mic.sh
```

That's it! Speak and see real-time transcription.

---

## What You Have

### ✅ Essential Files Only (4,659 lines)
- **Server**: WebSocket server with faster-whisper INT8
- **Client**: Audio capture with PulseAudio support
- **Model**: openai/whisper-large-v3-turbo (~2.7GB VRAM)
- **Config**: Everything in `config.yaml`

### 📁 Directory Structure
```
src/Hypr-Whisper/
├── whisper_live/          # Core library (3,896 lines)
│   ├── client.py         # WebSocket client + audio
│   ├── server.py         # WebSocket server
│   ├── vad.py            # Voice activity detection
│   ├── backend/          # Faster-whisper INT8
│   └── transcriber/      # Model wrapper
├── config.yaml           # All settings
├── start_server.sh       # Server launcher
├── start_client_mic.sh   # Client launcher  
└── README.md             # Full documentation
```

---

## Common Tasks

### Change Audio Input
Edit `config.yaml` line 42:
```yaml
pulseaudio_source: "your-device-name"
```

Find devices:
```bash
pactl list sources short
```

### Change Model
Edit `config.yaml` line 13:
```yaml
model_path: "openai/whisper-large-v3-turbo"  # or any other model
```

### Disable VAD (transcribe everything)
In your client code:
```python
client = TranscriptionClient(..., use_vad=False)
```

### Check Server Status
```bash
./start_server.sh status
```

### View Logs
```bash
./start_server.sh logs
# or
tail -f /tmp/whisper-live-hypr-voice.log
```

### Stop Server
```bash
./start_server.sh stop
```

---

## Performance

- **First connection**: ~7 minutes (downloads & converts model)
- **Subsequent connections**: ~3 seconds (model cached)
- **Transcription latency**: 100-300ms
- **VRAM usage**: ~2.7GB (INT8) vs ~4GB (float16)

---

## Git History

This is the minimal version extracted from the full WhisperLive codebase:

1. ✅ **Full version**: 5,867 lines (committed)
2. ✅ **Cleaned version**: 3,900 lines - removed TensorRT/OpenVINO (committed)
3. ✅ **Final version**: 4,659 lines - essential files only (you are here)

To go back to any version:
```bash
git log --oneline  # See commits
git checkout <commit-hash>  # Go to specific version
```

---

**Ready to use!** Just run the commands at the top. 🎤
