# Hypr-Voice Setup Guide for Arch Linux

## Quick Start

### 1. Run Diagnostics
First, check if everything is properly configured:

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice
./scripts/debug_setup.sh
```

This will check:
- System dependencies (wl-clipboard, wtype, python packages)
- Audio devices configuration
- Hyprland integration
- Project configuration files

### 2. Install Missing Dependencies

Based on the debug output, install any missing packages:

```bash
# System packages
sudo pacman -S python python-pip wl-clipboard wtype libnotify ffmpeg pulseaudio

# Python virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Python dependencies
pip install -r requirements.txt
```

### 3. Configure Audio Devices

The audio configuration has been set up for:
- **Primary**: USB Audio Microphone (GA102 related)
- **Secondary**: Parth's iPhone (when connected)

To verify your devices, run:
```bash
pactl list sources | grep -E "Name:|Description:"
```

If you need to change devices, edit:
```bash
nano config/audio_config.yaml
```

### 4. Add Hyprland Keybinds

Add this line to your `~/.config/hypr/hyprland.conf`:

```conf
source = /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice/hyprland-keybinds.conf
```

Then reload Hyprland:
```bash
hyprctl reload
```

### 5. Start the System

Use the unified launcher script:

```bash
./scripts/run_hypr_voice.sh start
```

This will:
- Start Whisper server (medium model on CPU)
- Start Hypr-Voice client in daemon mode
- Show status of both services

### 6. Usage

**Keybinds:**
- `Super + Grave (`)` - Hold to record, release to transcribe and paste
- `Super + Shift + Grave` - Show status
- `Super + Ctrl + Grave` - Emergency force stop

**Commands:**
```bash
./scripts/run_hypr_voice.sh status    # Check if services are running
./scripts/run_hypr_voice.sh logs      # View recent logs
./scripts/run_hypr_voice.sh stop      # Stop all services
./scripts/run_hypr_voice.sh restart   # Restart everything
```

## Configuration Details

### Raw Transcription Mode

The system is configured for **raw transcription** (no LLM enhancement):
- Fast, direct speech-to-text
- No context processing overhead
- Immediate paste after transcription
- Uses Whisper medium model on CPU

To enable LLM enhancement later, edit `run_hypr_voice.sh` and set:
```bash
RAW_MODE=false
```

### Terminal Detection

The system automatically detects terminal applications (kitty, Alacritty, etc.) and uses:
- `Ctrl+Shift+V` for terminals
- `Ctrl+V` for regular applications

Detected terminal apps: kitty, alacritty, foot, wezterm, terminator, konsole, gnome-terminal, xterm

### Audio Quality

Recording at high quality (48kHz) then downsampling to 16kHz for Whisper:
- Better voice capture
- Optimal Whisper performance
- Originals saved in `recordings/originals/` (if enabled)

## Troubleshooting

### No Audio Input

1. Check if device is detected:
   ```bash
   python3 -c "import sounddevice as sd; print(sd.query_devices())"
   ```

2. Test recording manually:
   ```bash
   arecord -l  # List devices
   arecord -d 5 test.wav  # Record 5 seconds
   ```

### Server Won't Start

1. Check logs:
   ```bash
   tail -f /tmp/hypr-voice-server.log
   ```

2. Try starting manually:
   ```bash
   source venv/bin/activate
   python3 whisper_server.py --model medium --device cpu --clean
   ```

3. Check if port is in use:
   ```bash
   lsof -i :9880
   ```

### Client Won't Connect

1. Verify server is running:
   ```bash
   curl http://localhost:9880/
   ```

2. Check client logs:
   ```bash
   tail -f /tmp/hypr-voice-client.log
   ```

### Paste Not Working

1. Verify wtype is installed:
   ```bash
   which wtype
   ```

2. Test wtype manually:
   ```bash
   echo "test" | wl-copy
   wtype -M ctrl -M shift -k v  # In a terminal
   ```

3. Check if current app is detected:
   ```bash
   hyprctl activewindow -j | grep class
   ```

### Performance Issues

If transcription is too slow:

1. Use smaller model:
   ```bash
   # Edit run_hypr_voice.sh
   WHISPER_MODEL="small"  # or "base" for even faster
   ```

2. Check CPU usage:
   ```bash
   htop  # Look for python3 processes
   ```

## Advanced Configuration

### Custom Whisper Model

Edit `run_hypr_voice.sh`:
```bash
WHISPER_MODEL="small"   # Options: tiny, base, small, medium, large
WHISPER_DEVICE="cpu"    # Or "cuda" if you have GPU
```

### Change Keybinds

Edit `hyprland-keybinds.conf` to customize shortcuts.

### Per-Application Profiles

Edit `config/app_profiles.yaml` to customize behavior for specific apps:

```yaml
your_app:
  app_class: your_app_name
  writing_style: casual  # or technical, formal, etc.
  context_rules:
    - Your custom rules
  llm_config:
    model: grok-3-mini
    temperature: 0.3
```

### Enable LLM Enhancement

1. Set `RAW_MODE=false` in `run_hypr_voice.sh`
2. Configure LLM provider in `config/llm_providers.yaml`
3. Add API keys to `.env` file (copy from `.env.example`)

## Files Overview

### Scripts
- `debug_setup.sh` - System diagnostics
- `run_hypr_voice.sh` - Unified launcher
- `scripts/hypr-voice-control.sh` - Keybind handler

### Configuration
- `config/audio_config.yaml` - Audio device settings
- `config/app_profiles.yaml` - Per-app behavior
- `config/llm_providers.yaml` - LLM configuration
- `hyprland-keybinds.conf` - Hyprland shortcuts

### Main Code
- `whisper_server.py` - Whisper transcription server
- `hypr_voice.py` - Main client with Hyprland integration
- `context_engine_cognee.py` - LLM context engine (optional)

## Next Steps

1. Run `./scripts/debug_setup.sh` to verify setup ✓
2. Fix any missing dependencies
3. Start services with `./scripts/run_hypr_voice.sh start`
4. Test recording with `Super + Grave`
5. Check logs if something doesn't work
6. Customize profiles in `config/` as needed

## Support

If you encounter issues:
1. Check logs: `./scripts/run_hypr_voice.sh logs`
2. Run diagnostics: `./scripts/debug_setup.sh`
3. Verify Hyprland integration: `hyprctl activewindow`
4. Test individual components (server, then client)

---

**Configured for:**
- Audio: USB Audio (primary), iPhone (secondary)
- Model: Whisper medium on CPU
- Mode: Raw transcription (no LLM)
- Environment: Arch Linux + Hyprland
- Terminals: Auto-detected (Ctrl+Shift+V)
