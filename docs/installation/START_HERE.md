# 🎤 Hypr-Voice - START HERE

Voice-controlled text input for Hyprland on Arch Linux

## What This Does

Speak into your microphone → Text appears where your cursor is!

Perfect for:
- Dictating code comments
- Writing emails
- Terminal commands
- Any text input in any application

## Installation (One Command)

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice
./scripts/install_deps.sh
```

This installs everything you need and sets up Hyprland keybinds.

## Quick Start (After Installation)

### 1. Test Your Setup
```bash
./scripts/test_audio.sh        # Test microphone
./scripts/debug_setup.sh       # Verify everything
```

### 2. Start Hypr-Voice
```bash
./scripts/run_hypr_voice.sh start
```

Wait for "Server is ready!" and "Client is running!"

### 3. Use It
1. Hold `F9` key
2. Speak
3. Release key
4. Text appears!

## Keybinds

| Key | Action |
|-----|--------|
| `F9` | Hold to record voice, release to transcribe & paste |
| `Super + F9` | Show status |
| `Super + Shift + F9` | Emergency stop |

## Configuration

Your setup is configured for:
- ✅ Raw transcription (fast, no LLM overhead)
- ✅ Whisper medium model on CPU
- ✅ USB Audio Microphone (primary)
- ✅ Parth's iPhone (secondary, when connected)
- ✅ Auto-detects terminals (uses Ctrl+Shift+V)
- ✅ Regular apps (uses Ctrl+V)

## Documentation

Choose your path:

1. **Just want to get started?**  
   → [QUICK_START.md](QUICK_START.md) - 5 minutes

2. **Want to understand everything?**  
   → [SETUP_GUIDE.md](SETUP_GUIDE.md) - Complete guide

3. **Want to see what was configured?**  
   → [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Technical details

## Common Commands

```bash
# Start/stop
./scripts/run_hypr_voice.sh start
./scripts/run_hypr_voice.sh stop
./scripts/run_hypr_voice.sh restart

# Monitor
./scripts/run_hypr_voice.sh status
./scripts/run_hypr_voice.sh logs

# Test
./scripts/test_audio.sh
./scripts/debug_setup.sh
```

## Troubleshooting

**Nothing happens when pressing the key?**
```bash
./scripts/run_hypr_voice.sh status   # Check if running
./scripts/run_hypr_voice.sh logs     # View errors
```

**Audio not working?**
```bash
./scripts/test_audio.sh              # Test microphone
pavucontrol                  # Check audio settings
```

**Text won't paste?**
```bash
which wtype                  # Should show /usr/bin/wtype
sudo pacman -S wtype         # If missing
```

## Project Structure

```
Hypr-Voice-main/
├── START_HERE.md              ← You are here
├── QUICK_START.md             ← 5-minute guide
├── SETUP_GUIDE.md             ← Complete reference
├── IMPLEMENTATION_SUMMARY.md  ← Technical details
└── hypr-voice/
    ├── install_deps.sh        ← Run this first!
    ├── run_hypr_voice.sh      ← Main launcher
    ├── debug_setup.sh         ← Diagnostics
    ├── test_audio.sh          ← Audio test
    └── config/                ← Configuration files
```

## What Makes This Special

✨ **Smart Pasting**: Auto-detects terminals and uses correct keybind  
🎯 **Context-Aware**: Knows which app you're in (future: per-app profiles)  
⚡ **Fast**: Raw transcription mode for instant results  
🔧 **Flexible**: Easy to customize and extend  
🎮 **Push-to-Talk**: Hold key, speak, release - that's it!

## Performance

- **Latency**: 2-5 seconds for short phrases
- **Accuracy**: Excellent (Whisper medium model)
- **CPU Usage**: 30-60% during transcription
- **Works Offline**: No internet needed

## Supported Apps

✅ Terminals: kitty, alacritty, foot, wezterm, etc.  
✅ Browsers: Chrome, Firefox, etc.  
✅ Editors: VS Code, Neovim, etc.  
✅ Chat: Discord, Slack, Telegram, etc.  
✅ Everything else!

## Next Steps

1. **Install**: `./scripts/install_deps.sh`
2. **Test**: `./scripts/test_audio.sh`
3. **Start**: `./scripts/run_hypr_voice.sh start`
4. **Use**: Press `Super + Grave` and speak!

---

**Questions?** Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting.

**Ready?** Run `./scripts/install_deps.sh` to begin! 🚀
