# wltype Integration - Auto-Typing Transcriptions

Automatically type transcriptions on screen as they're generated, simulating real keyboard input.

---

## Installation

### Prerequisites

#### For Wayland (Recommended)

```bash
# Install wltype
sudo apt-get update
sudo apt-get install wltype

# Verify installation
which wltype
wltype --version
```

#### For X11 (Alternative)

```bash
# Install xdotool
sudo apt-get update
sudo apt-get install xdotool

# Verify installation
which xdotool
xdotool --version
```

#### Check Your Desktop Environment

```bash
# Check which desktop you're using
echo $XDG_SESSION_TYPE

# Output:
# wayland  -> Use wltype
# x11      -> Use xdotool
```

---

## Quick Start

### Check Installation

```bash
python wltype_integration.py --check

# Output:
# ✓ wltype is installed
```

### List Audio Devices

```bash
python wltype_integration.py --list-devices

# Output:
# Available audio devices:
# ID | Name | Channels | Sample Rate
# ────────────────────────────────────
# 0  | Default Input | 2 | 48000 Hz ✓
# 1  | Microphone    | 2 | 48000 Hz
```

---

## Mode 1: Real-Time Streaming (Refreshes Every Few Seconds)

Stream microphone audio and automatically type new transcriptions every 3 seconds.

### Basic Usage

```bash
python wltype_integration.py --realtime --device 0
```

### What Happens

```
▶ Starting microphone stream...
  Click on a text field to start typing
  Press Ctrl+C to stop

✓ Session created: a1b2c3d4-e5f6-47g8-h9i0...

📝 Typing: Hello
📝 Typing:  world
📝 Typing: , this is
📝 Typing:  a test
```

### Configuration Options

```bash
# Use default audio device
python wltype_integration.py --realtime

# Specify audio device ID
python wltype_integration.py --realtime --device 0

# Adjust typing speed (seconds per character)
# Faster typing:
python wltype_integration.py --realtime --typing-speed 0.01

# Slower typing:
python wltype_integration.py --realtime --typing-speed 0.1

# Change refresh interval (check for new text every N seconds)
python wltype_integration.py --realtime --refresh-interval 5

# Combine options
python wltype_integration.py \
  --realtime \
  --device 0 \
  --typing-speed 0.05 \
  --refresh-interval 3 \
  --server http://localhost:9090
```

### Example Scenarios

#### Typing into Google Docs

```bash
# 1. Open Google Docs
# 2. Click in the document
# 3. Run this
python wltype_integration.py --realtime

# 4. Speak into microphone
# 5. Watch as text appears in Google Docs!
```

#### Live Chat Dictation

```bash
# 1. Open Discord/Telegram/WhatsApp
# 2. Click in the chat box
# 3. Run this
python wltype_integration.py --realtime --typing-speed 0.02

# 4. Dictate your message
# 5. It types in real-time!
```

#### Note-Taking

```bash
# 1. Open Obsidian/Notion/Markdown editor
# 2. Click in the editor
# 3. Run this
python wltype_integration.py \
  --realtime \
  --typing-speed 0.05 \
  --refresh-interval 2

# 4. Start speaking
# 5. Your notes are being typed automatically!
```

---

## Mode 2: File Transcription (API - Waits for Complete Text)

Upload audio/video file, wait for complete transcription, then type entire result.

### Basic Usage

```bash
python wltype_integration.py --file audio.mp3
```

### What Happens

```
▶ File: audio.mp3
  Waiting for transcription...
✓ Session: a1b2c3d4-e5f6...

✓ File uploaded

⏳ Transcribing
────────────────────────────────────────
Hello world, this is a test transcription. This is a longer example.
────────────────────────────────────────
✓ Transcription complete

📝 Typing transcription (85 characters)...
✓ Done typing
```

### Configuration Options

```bash
# Transcribe MP3 file
python wltype_integration.py --file audio.mp3

# Transcribe video file (extracts audio automatically)
python wltype_integration.py --file video.mp4

# Specify language
python wltype_integration.py --file audio.mp3 --language es  # Spanish
python wltype_integration.py --file audio.mp3 --language fr  # French

# Adjust typing speed (characters per second)
# Faster:
python wltype_integration.py --file audio.mp3 --type-speed 20

# Slower:
python wltype_integration.py --file audio.mp3 --type-speed 5

# Set timeout (max wait time)
python wltype_integration.py --file audio.mp3 --timeout 600  # 10 minutes

# Combine options
python wltype_integration.py \
  --file audio.mp3 \
  --language auto \
  --type-speed 15 \
  --timeout 300 \
  --server http://localhost:9090
```

### Example Scenarios

#### Transcribe Meeting Recording

```bash
# 1. Open document where you want meeting notes
# 2. Click to position cursor
# 3. Run this
python wltype_integration.py --file meeting_recording.mp3

# 4. Wait for transcription and typing to complete
# 5. Your meeting notes are now in the document!
```

#### Convert Podcast Episode Notes

```bash
# 1. Open note-taking app
# 2. Create new note
# 3. Run this
python wltype_integration.py \
  --file podcast_episode.mp3 \
  --type-speed 10 \
  --language auto

# 4. Complete transcription types into notes
```

#### Quick Voice Message Transcription

```bash
# 1. Receive voice message (MP3/WAV)
# 2. Open chat/email where you want to read it
# 3. Run this
python wltype_integration.py --file voice_message.wav

# 4. Transcription appears automatically
```

---

## Performance Settings

### Typing Speed Recommendations

| Speed | Chars/Sec | Use Case |
|-------|-----------|----------|
| 0.01s | 100 | Fast typing (natural) |
| 0.02s | 50 | Normal typing |
| 0.05s | 20 | Readable typing |
| 0.1s | 10 | Slow, visible typing |

### Real-Time Refresh Intervals

| Interval | Use Case |
|----------|----------|
| 1-2 sec | Responsive, real-time feel |
| 3-5 sec | Balanced, normal conversation |
| 5-10 sec | High-latency network |

### File Timeout Settings

| Timeout | File Duration |
|---------|---|
| 60 sec | < 5 min audio |
| 300 sec | < 30 min audio |
| 600 sec | < 1 hour audio |
| 1800 sec | < 2 hour audio |

---

## Keyboard & Window Focus

### Important Notes

⚠️ **Window focus matters!** The typing will only work if a text input field is focused.

```bash
# Before running the script:
# 1. Open your target application
# 2. Click in a text field (textbox, chat, document, etc.)
# 3. KEEP THAT WINDOW FOCUSED
# 4. Then run the script
```

### Example Setup

```bash
# Terminal 1: Start the server
python hybrid_server.py

# Terminal 2: Start transcription with typing
python wltype_integration.py --realtime

# Browser/Editor: Keep this window focused
# (Open Google Docs, VS Code, Discord, etc.)
```

---

## Comparison: Real-Time vs File Mode

| Feature | Real-Time | File Mode |
|---------|-----------|-----------|
| **Activation** | Immediate | After upload/processing |
| **Refresh** | Every N seconds | Once at end |
| **Duration** | Continuous | One-time |
| **Use Case** | Live dictation | File conversion |
| **Typing Style** | Incremental | All at once |
| **Perfect For** | Chat, notes | Email, documents |

---

## FAQ

**Q: Can I use this without wltype?**
A: Yes, xdotool works on X11, but wltype is recommended for Wayland.

**Q: Will typing interfere with my work?**
A: Yes, make sure to focus on the right window. The typing simulates actual keyboard input.

**Q: Can I stop typing midway?**
A: Yes, press Ctrl+C to stop the script anytime.

**Q: What if I make a mistake?**
A: Use Ctrl+Z (undo) after typing completes.

**Q: Can I adjust typing speed dynamically?**
A: Stop and restart with different `--typing-speed` parameter.

**Q: Does it work with non-Latin characters?**
A: Yes, but may require slower typing speed. Test with `--type-speed 5`.
