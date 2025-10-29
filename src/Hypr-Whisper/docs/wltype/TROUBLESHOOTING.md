# wltype Integration - Troubleshooting Guide

## Installation Issues

### "wltype not found"

```
✗ wltype not found!
  Install with: sudo apt-get install wltype (Wayland)
  or use: xdotool type (X11)
```

**Solution:**
```bash
# For Wayland
sudo apt-get install wltype

# For X11
sudo apt-get install xdotool
```

**Verify Installation:**
```bash
# Test wltype
which wltype
wltype --version

# Or test xdotool
which xdotool
xdotool --version
```

---

## Typing Issues

### Text Not Appearing

**Problem:** Text doesn't type after running the command

**Solutions:**
1. Make sure text input field is **focused** (cursor visible)
2. Try clicking in a simple text field first (like a text editor)
3. Run this to test: `echo "Hello" | wltype`

**Test wltype manually:**
```bash
# This should type "Hello" in the focused window
echo "Hello" | wltype

# Or directly
wltype "Hello world"
```

**Checklist:**
- ✓ Text input field is focused (cursor visible)
- ✓ Window is in foreground
- ✓ wltype/xdotool is installed and working
- ✓ Running on correct desktop (Wayland vs X11)

---

### "Error typing text"

**Causes:**
- Window is not focused
- No text input field is selected
- Permission issues

**Solutions:**
```bash
# Make sure to click on a text field before running
# Re-run the script after focusing the window
```

---

### Typing Too Fast/Slow

**Problem:** Text types too quickly or too slowly

**Solution:**
```bash
# Real-time mode - adjust typing-speed
python wltype_integration.py --realtime --typing-speed 0.1  # Slower

# File mode - adjust type-speed
python wltype_integration.py --file audio.mp3 --type-speed 5  # Slower
```

**Speed Reference:**
- **Real-time mode:** `--typing-speed 0.05` = 20 chars/sec (good default)
- **File mode:** `--type-speed 10` = 10 chars/sec (good default)

---

### Character Encoding Issues

**Problem:** Special characters appear wrong

**Solution:**
```bash
# Try slower typing speed
python wltype_integration.py --file audio.mp3 --type-speed 5
```

---

## Server Connection Issues

### Server Connection Error

**Problem:** "Connection refused" error

**Solution:**
```bash
# Start server in another terminal
python hybrid_server.py

# Then try again
python wltype_integration.py --realtime
```

**Verify server is running:**
```bash
# Check if server is listening on port 9090
curl http://localhost:9090/health

# Or check with netstat
netstat -tulpn | grep 9090
```

---

## Audio Device Issues

### Wrong Microphone Being Used

**Problem:** Wrong microphone is being used

**Solution:**
```bash
# List devices
python wltype_integration.py --list-devices

# Use specific device
python wltype_integration.py --realtime --device 2
```

**Find your device:**
```bash
# List all audio devices
python wltype_integration.py --list-devices

# Output example:
# Available audio devices:
# ID | Name | Channels | Sample Rate
# ────────────────────────────────────
# 0  | Default Input | 2 | 48000 Hz ✓
# 1  | Microphone    | 2 | 48000 Hz
# 2  | Webcam Audio  | 1 | 44100 Hz
```

---

### No Audio Input

**Problem:** No audio is being captured

**Solutions:**

1. **Check microphone permissions:**
```bash
# Test microphone with arecord
arecord -d 5 test.wav

# Play it back
aplay test.wav
```

2. **Check PulseAudio/PipeWire:**
```bash
# List sources
pactl list sources short

# Set default source
pactl set-default-source <source-name>
```

3. **Verify device in wltype:**
```bash
# Use correct device ID
python wltype_integration.py --realtime --device 0
```

---

## Performance Issues

### High Latency

**Problem:** Delay between speaking and typing

**Solutions:**

1. **Reduce refresh interval (real-time mode):**
```bash
python wltype_integration.py --realtime --refresh-interval 1
```

2. **Check network latency:**
```bash
# Ping server
ping localhost

# Check server logs
tail -f logs/hybrid_server.log
```

3. **Use faster typing speed:**
```bash
python wltype_integration.py --realtime --typing-speed 0.01
```

---

### Slow Transcription

**Problem:** File transcription takes too long

**Solutions:**

1. **Increase timeout:**
```bash
python wltype_integration.py --file audio.mp3 --timeout 1800  # 30 minutes
```

2. **Check file size:**
```bash
# Large files take longer
ls -lh audio.mp3
```

3. **Monitor server processing:**
```bash
# Check server logs
tail -f logs/hybrid_server.log
```

---

## Desktop Environment Issues

### Wayland vs X11 Confusion

**Problem:** Not sure which desktop environment you're using

**Solution:**
```bash
# Check your session type
echo $XDG_SESSION_TYPE

# Output:
# wayland  -> Use wltype
# x11      -> Use xdotool
```

**Install correct tool:**
```bash
# For Wayland
sudo apt-get install wltype

# For X11
sudo apt-get install xdotool
```

---

## Advanced Debugging

### Enable Verbose Mode

Add debugging to the script:

```bash
# Monitor in real-time
python wltype_integration.py --realtime 2>&1 | tee debug.log

# Check output
tail -f debug.log
```

---

### Check System Logs

```bash
# System journal
journalctl -f

# Server logs
tail -f /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper/logs/hybrid_server.log

# Client logs
tail -f /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper/hybrid_client.log
```

---

## Tips & Tricks

### 1. Test First

```bash
# Try with a simple text editor before using in production
# This way you can test without affecting real work
```

### 2. Batch Processing

```bash
#!/bin/bash
for file in *.mp3; do
    python wltype_integration.py --file "$file" --type-speed 12
    # Adds delay between files
    sleep 2
done
```

### 3. Monitor in Background

```bash
# In one terminal
python wltype_integration.py --file audio.mp3 > output.txt 2>&1 &

# In another terminal
tail -f output.txt
```

### 4. Keyboard Shortcuts After Typing

After typing completes, use standard shortcuts:
- `Ctrl+A` - Select all
- `Ctrl+C` - Copy
- `Ctrl+Z` - Undo
- `Ctrl+S` - Save

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `wltype not found` | Not installed | `sudo apt-get install wltype` |
| `Connection refused` | Server not running | `python hybrid_server.py` |
| `No such device` | Wrong audio device | `--list-devices` to find correct ID |
| `Timeout` | File too large | Increase `--timeout 600` |
| `Permission denied` | Audio permissions | Check PulseAudio/PipeWire |

---

## Getting Help

If you're still having issues:

1. **Check server status:**
   ```bash
   curl http://localhost:9090/health
   ```

2. **Review logs:**
   ```bash
   tail -f logs/hybrid_server.log
   ```

3. **Test components individually:**
   ```bash
   # Test wltype
   wltype "test"
   
   # Test server
   curl http://localhost:9090
   
   # Test audio
   python wltype_integration.py --list-devices
   ```

4. **Run with minimal options:**
   ```bash
   # Simplest real-time test
   python wltype_integration.py --realtime
   
   # Simplest file test
   python wltype_integration.py --file test.mp3
   ```
