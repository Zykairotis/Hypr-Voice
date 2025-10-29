# wltype Integration - Complete Quick Reference

## Installation

```bash
# Wayland (Recommended)
sudo apt-get install wltype

# X11 (Alternative)
sudo apt-get install xdotool

# Verify
python wltype_integration.py --check
```

---

## Mode 1: Real-Time Streaming 🎤

**What it does:** Streams microphone audio, checks every N seconds for new transcription, types incrementally into focused window.

### Basic Command

```bash
python wltype_integration.py --realtime
```

### Setup
1. **Open** target app (Google Docs, Discord, chat, etc.)
2. **Click** in a text field (cursor must be visible)
3. **Run** the command above
4. **Speak** into microphone
5. **Watch** text appear and type automatically

### Common Configurations

```bash
# Use specific audio device
python wltype_integration.py --realtime --device 0

# Faster typing (more characters per second)
python wltype_integration.py --realtime --typing-speed 0.02

# Slower typing (more visible)
python wltype_integration.py --realtime --typing-speed 0.1

# Check for new text every 2 seconds
python wltype_integration.py --realtime --refresh-interval 2

# All together
python wltype_integration.py \
  --realtime \
  --device 0 \
  --typing-speed 0.05 \
  --refresh-interval 3
```

### Real-Time Use Cases

| Use Case | Command |
|----------|---------|
| Live chat dictation | `--realtime --typing-speed 0.02` |
| Google Docs | `--realtime --typing-speed 0.05` |
| Code editor | `--realtime --device 0 --typing-speed 0.03` |
| Email composition | `--realtime --typing-speed 0.05` |
| Note-taking | `--realtime --refresh-interval 2` |

---

## Mode 2: File Transcription 📁

**What it does:** Uploads file, waits for complete transcription, types entire result in one go.

### Basic Command

```bash
python wltype_integration.py --file audio.mp3
```

### Setup
1. **Click** in target text field
2. **Run** the command with your file
3. **Wait** for transcription to complete
4. **Text types** automatically into focused window

### Common Configurations

```bash
# Audio file
python wltype_integration.py --file meeting.mp3

# Video file (auto-extracts audio)
python wltype_integration.py --file video.mp4

# Specify language
python wltype_integration.py --file audio.mp3 --language es

# Fast typing (20 chars/sec)
python wltype_integration.py --file audio.mp3 --type-speed 20

# Slow typing (5 chars/sec)
python wltype_integration.py --file audio.mp3 --type-speed 5

# Longer wait time (10 minutes)
python wltype_integration.py --file audio.mp3 --timeout 600

# All together
python wltype_integration.py \
  --file meeting.mp3 \
  --language auto \
  --type-speed 12 \
  --timeout 300
```

### File Mode Use Cases

| Use Case | Command |
|----------|---------|
| Discord message | `--file msg.mp3 --type-speed 15` |
| Meeting notes | `--file meeting.mp3 --type-speed 10` |
| Email transcription | `--file voice.mp3 --type-speed 12` |
| Long audio (1hr) | `--file podcast.mp3 --timeout 600` |
| Video transcript | `--file video.mp4 --type-speed 10` |

---

## Speed Settings

### Typing Speed (Real-Time Mode)

`--typing-speed X` = X seconds per character

| Speed | Chars/Sec | Feel | Use Case |
|-------|-----------|------|----------|
| 0.01s | 100 | Instant | Text appears fast |
| 0.02s | 50 | Fast | Natural typing |
| 0.05s | 20 | Normal | Readable |
| 0.1s | 10 | Slow | Very visible |
| 0.2s | 5 | Very slow | Demos |

### Type Speed (File Mode)

`--type-speed X` = X characters per second

| Speed | Duration for 1000 chars | Use Case |
|-------|------------------------|----------|
| 5 | 3:20 | Very readable |
| 10 | 1:40 | Normal |
| 15 | 1:06 | Fast |
| 20 | 0:50 | Very fast |

### Refresh Interval (Real-Time Mode)

`--refresh-interval X` = Check every X seconds

| Interval | Responsiveness | Use Case |
|----------|---|----------|
| 1s | Very responsive | Live feel |
| 2s | Responsive | Balanced |
| 3s | Normal | Default |
| 5s | Delayed | Slow network |

---

## Complete Command Reference

### Information Commands

```bash
# Check if wltype installed
python wltype_integration.py --check

# List available audio devices
python wltype_integration.py --list-devices

# Show help
python wltype_integration.py --help
```

### Real-Time Commands

```bash
# Default (system default microphone)
python wltype_integration.py --realtime

# Specific device
python wltype_integration.py --realtime --device 1

# Custom typing speed
python wltype_integration.py --realtime --typing-speed 0.03

# Custom refresh interval
python wltype_integration.py --realtime --refresh-interval 5

# Custom server
python wltype_integration.py --realtime --server http://192.168.1.100:9090

# All options
python wltype_integration.py \
  --realtime \
  --device 0 \
  --typing-speed 0.05 \
  --refresh-interval 3 \
  --server http://localhost:9090
```

### File Commands

```bash
# Default (10 chars/sec, 60s timeout)
python wltype_integration.py --file audio.mp3

# Custom typing speed
python wltype_integration.py --file audio.mp3 --type-speed 15

# Custom timeout
python wltype_integration.py --file audio.mp3 --timeout 600

# Specific language
python wltype_integration.py --file audio.mp3 --language es

# Auto-detect language
python wltype_integration.py --file audio.mp3 --language auto

# Custom server
python wltype_integration.py --file audio.mp3 --server http://192.168.1.100:9090

# All options
python wltype_integration.py \
  --file meeting.mp3 \
  --language auto \
  --type-speed 12 \
  --timeout 300 \
  --server http://localhost:9090
```

---

## Real-World Examples

### Example 1: Discord Voice Message

```bash
# 1. Save voice message as message.mp3
# 2. Open Discord chat
# 3. Click in message box
# 4. Run:
python wltype_integration.py --file message.mp3 --type-speed 15
```

### Example 2: Live Google Docs Dictation

```bash
# 1. Open Google Docs
# 2. Click in document
# 3. Run:
python wltype_integration.py --realtime --typing-speed 0.05
# 4. Speak and watch it appear in Google Docs!
```

### Example 3: Meeting Notes from Recording

```bash
# 1. Record meeting (creates meeting.mp3)
# 2. Open document where you want notes
# 3. Click in document
# 4. Run:
python wltype_integration.py --file meeting.mp3 --type-speed 10 --timeout 600
# 5. Wait and entire meeting transcription types in!
```

### Example 4: Code Comments via Voice

```bash
# 1. Open IDE/editor
# 2. Click where you want comment
# 3. Run:
python wltype_integration.py --realtime --device 0 --typing-speed 0.03
# 4. Dictate comment
# 5. Comment types automatically!
```

### Example 5: Email Dictation

```bash
# Record voice note first
# Then open email draft, click in body
python wltype_integration.py --file voice_note.mp3 --type-speed 12
# Entire email is typed for you!
```

---

## Quick Decision Guide

**Choose REAL-TIME if:**
- ✅ You're dictating live
- ✅ Need it to appear immediately
- ✅ Using chat or messaging
- ✅ Writing notes in real-time
- ✅ Want natural typing effect

**Choose FILE MODE if:**
- ✅ You have a recording
- ✅ Need highest quality
- ✅ Writing formal documents
- ✅ Don't mind waiting
- ✅ Want to type entire document at once

---

**Need help deciding?** Use this:

```
Do you have audio RIGHT NOW?
  → YES: Real-time mode (--realtime)
  → NO: File mode (--file <recording>)
```
