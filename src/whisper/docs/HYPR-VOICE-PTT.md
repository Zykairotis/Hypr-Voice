# Hypr-Voice Push-to-Talk System

A seamless push-to-talk voice typing system for Hyprland that records audio while a key is pressed, transcribes it using Whisper, and automatically types the result.

## Features

- **🎤 Push-to-Talk**: Hold F9 to record, release to transcribe and type
- **⚡ Fast Transcription**: Uses local Whisper server for quick processing
- **🎯 Smart Typing**: Instantly types transcribed text using `wtype`
- **💾 Optional Recording Storage**: Save recordings for later review
- **🔧 Multiple Modes**: Daemon, direct, or quick-record modes
- **🎨 Visual Feedback**: Desktop notifications and console output

## Installation

### Quick Install

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/whisper/scripts
chmod +x install-hypr-voice.sh
./install-hypr-voice.sh
```

### Manual Installation

1. **Install Dependencies**:
```bash
sudo apt-get install wtype netcat-openbsd alsa-utils
```

2. **Make Scripts Executable**:
```bash
chmod +x hypr-voice-type.py
chmod +x scripts/hypr-voice-daemon.sh
chmod +x scripts/hypr-voice-record.sh
chmod +x scripts/hypr-voice-quick.sh
```

3. **Configure Hyprland**:
```bash
cp config/hyprvoice.conf ~/.config/hypr/
echo "source = ~/.config/hypr/hyprvoice.conf" >> ~/.config/hypr/hyprland.conf
hyprctl reload
```

## Usage

### Method 1: Daemon Mode (Recommended)

The daemon runs in the background and provides the fastest response time.

1. **Start the Whisper server**:
```bash
./scripts/start_hybrid_server.sh
```

2. **Start the PTT daemon**:
```bash
./scripts/hypr-voice-daemon.sh start
```

3. **Use Push-to-Talk**:
   - Press and hold `F9` to record
   - Release `F9` to stop recording and transcribe
   - Text is automatically typed where your cursor is

### Method 2: Direct Mode

For simpler setups without a daemon.

1. **Enable direct bindings** in `~/.config/hypr/hyprvoice.conf`:
```conf
bind = , F9, exec, /path/to/hypr-voice-record.sh start
bindr = , F9, exec, /path/to/hypr-voice-record.sh stop
```

2. **Reload Hyprland**:
```bash
hyprctl reload
```

### Method 3: Quick Record

For fixed-duration recording (default 5 seconds):

```bash
# Record for 5 seconds
./scripts/hypr-voice-quick.sh

# Record for 10 seconds
./scripts/hypr-voice-quick.sh 10
```

Or bind to a key:
```conf
bind = SUPER_ALT, R, exec, /path/to/hypr-voice-quick.sh
```

## Configuration

### Audio Device

Edit `config/audio-profile.yaml` to specify your microphone:

```yaml
pulseaudio:
  device_name: "Your Microphone Name"
  device_type: "source"
  default_source: "alsa_input.your_device"
```

If using the default microphone, leave it as is or remove the file.

### Keybindings

Edit `~/.config/hypr/hyprvoice.conf` to customize keybindings:

```conf
# Default: F9 for PTT
bind = , F9, exec, echo "start" | nc -N localhost 9876
bindr = , F9, exec, echo "stop" | nc -N localhost 9876

# Alternative: Super+F9
bind = SUPER, F9, exec, echo "start" | nc -N localhost 9876
bindr = SUPER, F9, exec, echo "stop" | nc -N localhost 9876

# Alternative: Pause key
bind = , Pause, exec, echo "start" | nc -N localhost 9876
bindr = , Pause, exec, echo "stop" | nc -N localhost 9876
```

### Recordings Storage

**Recordings are saved by default** to:
```
/home/mewtwo/Zykairotis/Hypr-Voice/src/whisper/recordings/
```

Filenames include timestamp: `recording_YYYYMMDD_HHMMSS.wav`

**To disable saving** (use temp files only):
```bash
# Start daemon without saving
./hypr-voice-type.py daemon --no-save
```

**Manage recordings:**
```bash
# View all recordings
ls -lh recordings/

# Delete old recordings (7+ days)
find recordings/ -name "*.wav" -mtime +7 -delete
```

## Systemd Service

For automatic startup:

1. **Install service**:
```bash
cp config/hypr-voice.service ~/.config/systemd/user/
systemctl --user daemon-reload
```

2. **Enable auto-start**:
```bash
systemctl --user enable hypr-voice.service
systemctl --user start hypr-voice.service
```

3. **Check status**:
```bash
systemctl --user status hypr-voice.service
```

## Command Reference

### Daemon Control

```bash
# Start daemon
./scripts/hypr-voice-daemon.sh start

# Stop daemon
./scripts/hypr-voice-daemon.sh stop

# Restart daemon
./scripts/hypr-voice-daemon.sh restart

# Check status
./scripts/hypr-voice-daemon.sh status
```

### Python Script

```bash
# Daemon mode (reads from stdin)
./hypr-voice-type.py daemon

# Single command
./hypr-voice-type.py start   # Start recording
./hypr-voice-type.py stop    # Stop and transcribe
./hypr-voice-type.py toggle  # Toggle recording

# With options
./hypr-voice-type.py daemon --save-recordings
./hypr-voice-type.py daemon --server http://localhost:9090
```

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Hyprland   │────►│  PTT Daemon  │────►│   Whisper   │
│  Keybind    │     │  (Python)    │     │   Server    │
│  (F9)       │     │              │     │  Port 9090  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌─────────────┐
                    │    wtype    │
                    │ (Auto-type) │
                    └─────────────┘
```

1. **Keybind Trigger**: Hyprland sends start/stop commands via netcat
2. **Recording**: PyAudio captures audio from configured device
3. **Transcription**: Audio sent to Whisper server via REST API
4. **Auto-typing**: Transcribed text typed using wtype

## Troubleshooting

### Daemon not responding

```bash
# Check if daemon is running
./scripts/hypr-voice-daemon.sh status

# Check logs
tail -f /tmp/hypr-voice-daemon.log

# Restart daemon
./scripts/hypr-voice-daemon.sh restart
```

### No audio recorded

1. Check microphone permissions
2. Test microphone:
```bash
arecord -d 5 test.wav
aplay test.wav
```
3. List audio devices:
```bash
arecord -l
```

### Transcription fails

1. Check server is running:
```bash
curl http://localhost:9090/health
```

2. Test transcription manually:
```bash
./scripts/hypr-voice-quick.sh 5
```

### Keybind not working

1. Reload Hyprland:
```bash
hyprctl reload
```

2. Check if binding is registered:
```bash
hyprctl binds | grep F9
```

3. Test command directly:
```bash
echo "start" | nc localhost 9876
sleep 2
echo "stop" | nc localhost 9876
```

## Tips & Tricks

### Multiple Languages

The system auto-detects language. For specific language:

```python
# Edit hypr-voice-type.py
self.client.create_session(language="es")  # Spanish
```

### Faster Typing

Instant typing (entire text at once):
```python
# In hypr-voice-type.py
type_text_instant(text)  # Already default
```

### Custom Hotkeys

For app-specific PTT:
```conf
# Discord PTT (Ctrl+Shift+M)
bind = CTRL_SHIFT, M, exec, echo "start" | nc localhost 9876
bindr = CTRL_SHIFT, M, exec, echo "stop" | nc localhost 9876
```

### Visual Indicator

Add to waybar/eww config:
```json
{
  "custom/recording": {
    "exec": "[ -f /tmp/hypr-voice-recording.state ] && echo '🔴 REC' || echo ''",
    "interval": 1
  }
}
```

## Performance

- **Recording latency**: < 50ms
- **Transcription time**: 1-3 seconds (depends on audio length)
- **Typing speed**: Instant (full text at once)
- **Total PTT latency**: ~2-4 seconds from release to typed text

## Privacy

- **Local processing**: All transcription happens locally
- **No cloud services**: Runs entirely on your machine
- **Optional storage**: Recordings only saved if explicitly enabled
- **Temp file cleanup**: Automatic cleanup of temporary files

## License

Part of the Hypr-Voice project. MIT License.
