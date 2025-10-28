# WhisperLive Integration for Hypr-Voice

This directory contains the WhisperLive server integration for Hypr-Voice, providing real-time speech transcription capabilities.

## 📁 Files Overview

- **`config.yaml`** - Configuration file for WhisperLive server settings
- **`start_whisper_live.py`** - Python startup script with configuration loading
- **`start_server.sh`** - Bash script for server management (start/stop/status/logs/test)
- **`run_server.py`** - Original WhisperLive server script
- **`whisper_live/`** - WhisperLive source code

## 🚀 Quick Start

### 1. Start the Server

```bash
# Using the bash script (recommended)
./start_server.sh start

# Or using Python directly
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
python start_whisper_live.py
```

### 2. Check Server Status

```bash
./start_server.sh status
```

### 3. Test the Server

```bash
./start_server.sh test
```

### 4. View Logs

```bash
./start_server.sh logs
```

### 5. Stop the Server

```bash
./start_server.sh stop
```

## ⚙️ Configuration

The server is configured via `config.yaml`. Key settings include:

### Server Settings
- **Host**: localhost (binds to 0.0.0.0 for external access)
- **Port**: 9090 (WebSocket server)
- **Max Clients**: 4 concurrent connections
- **Connection Time**: 600 seconds max per client

### Backend Configuration
- **Backend**: faster_whisper (recommended for CPU)
- **Model**: small (balance of speed and accuracy)
- **Device**: cpu (change to cuda if GPU available)
- **Language**: auto (automatic detection)

### Performance Settings
- **OpenMP Threads**: 4 (CPU optimization)
- **Cache Path**: `/tmp/whisper-live-cache`
- **Audio Chunk Size**: 2048 samples

### Hypr-Voice Integration
- **Socket Path**: `/tmp/hypr-voice-whisper.sock`
- **VAD Enabled**: Yes (Voice Activity Detection)
- **VAD Threshold**: 0.5
- **Min Speech Duration**: 0.5 seconds
- **Max Silence Duration**: 2.0 seconds

## 🎯 Usage with Hypr-Voice

### 1. WebSocket Connection

Connect to `ws://localhost:9090` using the WhisperLive client protocol.

### 2. Client Configuration

```python
from whisper_live.client import TranscriptionClient

client = TranscriptionClient(
    host="localhost",
    port=9090,
    lang="auto",  # Auto-detect language
    translate=False,  # Don't translate to English
    model="small",  # Must match server model
    use_vad=True  # Enable Voice Activity Detection
)

# Start transcribing from microphone
client()
```

### 3. Integration Points

- **Audio Input**: 16kHz, mono, 16-bit PCM
- **Real-time**: Low-latency transcription
- **VAD**: Automatic speech detection
- **Multi-language**: Supports 99 languages

## 🔧 Advanced Configuration

### Model Selection

Edit `config.yaml` to change the model:

```yaml
backend:
  model: "medium"  # Options: tiny, base, small, medium, large-v3
```

### GPU Acceleration

If you have a CUDA-enabled GPU:

```yaml
backend:
  device: "cuda"
```

### Custom Model Path

For locally hosted models:

```yaml
backend:
  model_path: "/path/to/custom/model"
```

### Performance Tuning

Adjust thread count based on your CPU:

```yaml
performance:
  omp_num_threads: 8  # Increase for more CPU cores
```

## 📊 Monitoring

### Server Logs

```bash
tail -f /tmp/whisper-live-hypr-voice.log
```

### Process Status

```bash
ps aux | grep whisper
```

### Network Connections

```bash
netstat -ln | grep 9090
```

### Resource Usage

```bash
htop  # Monitor CPU and memory usage
```

## 🐛 Troubleshooting

### Server Won't Start

1. **Check virtual environment**:
   ```bash
   source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
   python -c "import whisper_live"
   ```

2. **Check port availability**:
   ```bash
   netstat -ln | grep 9090
   ```

3. **Check logs**:
   ```bash
   cat /tmp/whisper-live-hypr-voice.log
   ```

### Connection Issues

1. **Verify server is running**:
   ```bash
   ./start_server.sh status
   ```

2. **Test WebSocket connection**:
   ```bash
   ./start_server.sh test
   ```

3. **Check firewall**:
   ```bash
   sudo ufw status
   ```

### Performance Issues

1. **Reduce model size**:
   ```yaml
   backend:
     model: "base"  # Faster but less accurate
   ```

2. **Adjust thread count**:
   ```yaml
   performance:
     omp_num_threads: 2  # Reduce CPU usage
   ```

3. **Monitor resources**:
   ```bash
   top -p $(pgrep -f whisper)
   ```

## 🔄 Integration with Hypr-Voice

### Systemd Service (Optional)

Create a systemd service for automatic startup:

```ini
[Unit]
Description=WhisperLive Server for Hypr-Voice
After=network.target

[Service]
Type=simple
User=mewtwo
WorkingDirectory=/home/mewtwo/Zykairotis/Hypr-Voice/src/live-whisper
Environment=PATH=/home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin
ExecStart=/home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/python run_server.py --port 9090 --backend faster_whisper --omp_num_threads 4 --max_clients 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Hyprland Integration

The WhisperLive server can be integrated with Hypr-Voice keybinds:

```bash
# Start WhisperLive with Hypr-Voice
./start_server.sh start

# The server will be available for Hypr-Voice clients
# WebSocket: ws://localhost:9090
# Socket: /tmp/hypr-voice-whisper.sock
```

## 📈 Performance Expectations

### CPU Performance (Small Model)
- **Latency**: 1-3 seconds for short phrases
- **CPU Usage**: 20-50% during transcription
- **Memory**: ~500MB
- **Accuracy**: Good for most languages

### Model Comparison
- **Tiny**: Fastest, basic accuracy
- **Base**: Good balance of speed and accuracy
- **Small**: Recommended default, good accuracy
- **Medium**: Better accuracy, slower
- **Large-v3**: Best accuracy, highest resource usage

## 📚 Additional Resources

- [WhisperLive GitHub](https://github.com/collabora/WhisperLive)
- [Hypr-Voice Documentation](../../docs/)
- [OpenAI Whisper Model Card](https://github.com/openai/whisper/blob/main/model-card.md)

---

**Status**: ✅ Ready for use with Hypr-Voice
**Server**: ws://localhost:9090
**Virtual Environment**: `/home/mewtwo/Zykairotis/Hypr-Voice/.venv`
**Configuration**: `config.yaml`