# Hypr-Voice Installation Checklist

Follow this checklist to get Hypr-Voice running on your system.

## ☐ Step 1: Install Dependencies (5 min)

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice
./scripts/install_deps.sh
```

**What this does:**
- Installs system packages (wl-clipboard, wtype, libnotify, ffmpeg, etc.)
- Creates Python virtual environment
- Installs Python dependencies (sounddevice, faster-whisper, etc.)
- Sets up required directories
- Optionally adds Hyprland keybinds

**Expected result:** "Installation Complete!" message

---

## ☐ Step 2: Test Audio (2 min)

```bash
./scripts/test_audio.sh
```

**What to look for:**
- USB Audio device found ✓
- RMS level > 0.001 ✓
- "Audio detected! Device is working." message

**If no audio detected:**
- Check if microphone is plugged in
- Run `pavucontrol` and check input device
- Verify device is not muted

---

## ☐ Step 3: Run Diagnostics (2 min)

```bash
./scripts/debug_setup.sh
```

**Check for:**
- All dependencies installed (green checkmarks)
- Audio devices listed
- Hyprland integration working
- Config files present

**Fix any red X marks before continuing**

---

## ☐ Step 4: Add Hyprland Keybinds (1 min)

Edit `~/.config/hypr/hyprland.conf` and add:

```conf
# Hypr-Voice keybinds
source = /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice/hyprland-keybinds.conf
```

Then reload:
```bash
hyprctl reload
```

**Verify:** `grep -r "hypr-voice" ~/.config/hypr/` should show the source line

---

## ☐ Step 5: Start Services (1 min)

```bash
./scripts/run_hypr_voice.sh start
```

**Wait for:**
- "Server is ready!" (after ~10-30 seconds)
- "Client is running!"

**Check status:**
```bash
./scripts/run_hypr_voice.sh status
```

Both Server and Client should show **RUNNING** in green.

---

## ☐ Step 6: First Test (30 sec)

1. Open any text editor or terminal
2. Click to place cursor
3. **Hold** `F9` key
4. Say something: "Hello, this is a test"
5. **Release** the key
6. Wait 2-5 seconds

**Expected:** Text appears where your cursor was!

---

## ☐ Step 7: Test Terminal Detection

1. Open kitty or alacritty
2. Hold `F9`
3. Say: "echo hello world"
4. Release key

**Expected:** Command appears in terminal (using Ctrl+Shift+V automatically)

---

## Troubleshooting Checklist

### Services won't start
- [ ] Port 9880 not in use: `lsof -i :9880`
- [ ] Python dependencies installed: `source venv/bin/activate && python -c "import faster_whisper"`
- [ ] Check logs: `./scripts/run_hypr_voice.sh logs`

### No audio input
- [ ] Device connected: `pactl list sources | grep -i "usb audio"`
- [ ] Not muted: `pavucontrol` → Input Devices tab
- [ ] Correct device in config: `cat config/audio_config.yaml | grep primary`

### Text won't paste
- [ ] wtype installed: `which wtype`
- [ ] Clipboard works: `echo test | wl-copy && wl-paste`
- [ ] Active window detected: `hyprctl activewindow | grep class`

### Keybind doesn't work
- [ ] Hyprland config sourced: `grep hypr-voice ~/.config/hypr/hyprland.conf`
- [ ] Hyprland reloaded: `hyprctl reload`
- [ ] Socket exists: `ls -l /tmp/hypr-voice.sock`

---

## Success Criteria

✓ Services running: `./scripts/run_hypr_voice.sh status` shows both green  
✓ Audio working: `./scripts/test_audio.sh` detects audio  
✓ Keybind works: Super+Grave triggers recording  
✓ Text pastes: Transcribed text appears at cursor  
✓ Terminals work: Auto-detects and uses Ctrl+Shift+V  

---

## What to Do After Success

### Daily Usage
```bash
# Start
cd /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice
./scripts/run_hypr_voice.sh start

# Use Super+Grave to dictate

# Stop when done
./scripts/run_hypr_voice.sh stop
```

### Customization
- Edit `config/audio_config.yaml` for audio settings
- Edit `config/app_profiles.yaml` for per-app behavior
- Edit `run_hypr_voice.sh` to change model (medium → small for speed)

### Advanced Features
- Enable LLM enhancement: Set `RAW_MODE=false` in `run_hypr_voice.sh`
- Add API keys in `.env` for context-aware improvements
- Configure per-application profiles in `config/app_profiles.yaml`

---

## Need Help?

1. **Check logs first:**
   ```bash
   ./scripts/run_hypr_voice.sh logs
   ```

2. **Run full diagnostics:**
   ```bash
   ./scripts/debug_setup.sh
   ```

3. **Read documentation:**
   - START_HERE.md - Quick overview
   - QUICK_START.md - Fast setup
   - SETUP_GUIDE.md - Complete reference

4. **Common issues:**
   - See SETUP_GUIDE.md → Troubleshooting section

---

## Time Estimate

Total setup time: **10-15 minutes**

- Install dependencies: 5 min
- Test audio: 2 min  
- Run diagnostics: 2 min
- Add keybinds: 1 min
- Start services: 1 min
- First test: 30 sec
- Terminal test: 30 sec

---

**Ready?** Start with Step 1: `./scripts/install_deps.sh` 🚀
