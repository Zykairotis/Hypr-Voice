# Hypr-Voice Quick Start

Get up and running in 5 minutes!

## Step 1: Check System (2 min)

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice
./scripts/debug_setup.sh
```

This checks all dependencies and configuration. Fix anything marked with ✗.

## Step 2: Install Dependencies (if needed)

```bash
# System packages (if missing)
sudo pacman -S wl-clipboard wtype libnotify python

# Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Step 3: Test Audio (1 min)

```bash
./scripts/test_audio.sh
```

Should show "Audio detected! Device is working."

## Step 4: Add Keybinds

Edit `~/.config/hypr/hyprland.conf` and add:

```conf
source = /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice/hyprland-keybinds.conf
```

Reload Hyprland:
```bash
hyprctl reload
```

## Step 5: Start Hypr-Voice

```bash
./scripts/run_hypr_voice.sh start
```

Wait for "Server is ready!" and "Client is running!"

## Step 6: Use It!

1. Press and hold `F9` key
2. Speak into microphone
3. Release key
4. Text appears where your cursor is!

### Keybinds:
- `F9` - Record voice (hold to record, release to transcribe)
- `Super + F9` - Show status
- `Super + Shift + F9` - Emergency stop

## Troubleshooting

**Nothing happens when I press the key?**
- Check status: `./scripts/run_hypr_voice.sh status`
- View logs: `./scripts/run_hypr_voice.sh logs`

**No audio detected?**
- Run: `./scripts/test_audio.sh`
- Check microphone is not muted in `pavucontrol`

**Server won't start?**
- Check port: `lsof -i :9880`
- Kill if needed: `killall python3`
- Try again: `./scripts/run_hypr_voice.sh restart`

**Text won't paste in terminal?**
- Make sure `wtype` is installed: `sudo pacman -S wtype`
- System auto-detects terminals (kitty, alacritty, etc.)

## What's Configured

✓ Audio: USB Audio (primary), iPhone (secondary fallback)  
✓ Model: Whisper medium on CPU (raw transcription mode)  
✓ Paste: Auto-detects terminals (Ctrl+Shift+V vs Ctrl+V)  
✓ Keybind: Push-to-talk with Super+Grave  

## Next Steps

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for:
- Advanced configuration
- Per-app profiles
- LLM enhancement
- Performance tuning

---

**Need help?** Check logs with `./scripts/run_hypr_voice.sh logs`
