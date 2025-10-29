# wltype Integration - Advanced Usage & Examples

## Advanced Integration

### Custom Callback Integration

```python
from wltype_integration import FileTyper

# Use in your own script
typer = FileTyper(server_url="http://localhost:9090")
result = typer.transcribe_and_type(
    filepath="audio.mp3",
    language="en",
    timeout=300
)

print(f"Typed: {result}")
```

### Real-Time with Custom Interval

```bash
# Check for new text every 1 second
python wltype_integration.py \
  --realtime \
  --device 0 \
  --refresh-interval 1 \
  --typing-speed 0.02
```

---

## Batch Processing

### Process Multiple Files

```bash
#!/bin/bash
# Transcribe and type multiple files

for file in *.mp3; do
    echo "Processing: $file"
    python wltype_integration.py --file "$file" --type-speed 15
    echo "Press Enter to continue to next file..."
    read
done
```

### Automated Workflow

```bash
#!/bin/bash
# Watch directory and auto-process new files

inotifywait -m -e create --format '%f' /path/to/audio/folder | while read file
do
    if [[ $file == *.mp3 ]]; then
        echo "New file detected: $file"
        python wltype_integration.py --file "/path/to/audio/folder/$file" --type-speed 12
    fi
done
```

---

## Integration Examples

### Discord Voice Message Transcription

```bash
# 1. Receive voice message in Discord
# 2. Right-click → Save As → discord_message.mp3
# 3. Open Discord and click in chat box
# 4. Run:
python wltype_integration.py --file discord_message.mp3

# Message appears typed in chat!
```

### Live Meeting Transcription

```bash
# 1. Record meeting audio
# 2. Open document where you want notes
# 3. Run:
python wltype_integration.py --file meeting.mp3 --language auto

# Full meeting notes type into document
```

### Real-Time Dictation to Code Editor

```bash
# 1. Open VS Code
# 2. Click in editor
# 3. Run:
python wltype_integration.py --realtime --typing-speed 0.05

# Write code by talking!
```

---

## Performance Optimization

### Minimize Latency (Real-Time)

```bash
# Ultra-responsive setup
python wltype_integration.py \
  --realtime \
  --device 0 \
  --typing-speed 0.01 \
  --refresh-interval 1
```

### Maximum Quality (File Mode)

```bash
# Best quality with patience
python wltype_integration.py \
  --file important_audio.mp3 \
  --language auto \
  --type-speed 8 \
  --timeout 1800
```

---

## Monitoring & Debugging

### Background Processing with Logs

```bash
# In one terminal
python wltype_integration.py --file audio.mp3 > output.txt 2>&1 &

# In another terminal
tail -f output.txt
```

### Pipe to File While Typing

```bash
# Save transcription to file while typing
python wltype_integration.py --file audio.mp3 | tee transcription.txt
```

---

## Advanced Scenarios

### Scenario 1: Video Content Creation

```bash
# Transcribe video narration
python wltype_integration.py --file video.mp4 --type-speed 10 --timeout 600

# Use case:
# - Extract video transcript for subtitles
# - Create video description
# - Generate blog post from video
```

---

### Scenario 2: Podcast Episode Notes

```bash
# Full podcast transcription
python wltype_integration.py \
  --file podcast_episode.mp3 \
  --language auto \
  --type-speed 15 \
  --timeout 1800

# Use case:
# - Create episode show notes
# - Generate blog post
# - Extract quotes
```

---

### Scenario 3: Interview Transcription

```bash
# Professional interview transcription
python wltype_integration.py \
  --file interview.mp3 \
  --language en \
  --type-speed 10 \
  --timeout 900

# Use case:
# - Create article from interview
# - Extract key quotes
# - Research documentation
```

---

### Scenario 4: Voice Journal

```bash
# Daily voice journal entry
python wltype_integration.py \
  --file journal_2024_01_15.mp3 \
  --type-speed 12

# Use case:
# - Convert voice notes to text
# - Digital journaling
# - Voice memos to documents
```

---

## Common Patterns

### Pattern 1: Quick Chat Messages

```bash
# Real-time: Best for quick messages
python wltype_integration.py --realtime --device 0

User speaks: "Hey, can we reschedule?"
Server hears: "Hey can we reschedule"
3 seconds later: Typed in Discord ✓
```

---

### Pattern 2: Formal Email

```bash
# File mode: Better for formal communication
python wltype_integration.py --file email.mp3 --type-speed 8

User records: Full email with pauses for thinking
10 seconds processing
Result: Professional email typed perfectly ✓
```

---

### Pattern 3: Code Comments

```bash
# Real-time: Natural programming flow
python wltype_integration.py --realtime --typing-speed 0.03

Dev speaks: "This function validates user input"
1 second later: # This function validates user input ✓
Continue coding naturally
```

---

## System Integration

### systemd Service

Create `/etc/systemd/system/wltype-realtime.service`:

```ini
[Unit]
Description=wltype Real-time Transcription Service
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
ExecStart=/home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/python wltype_integration.py --realtime --device 0
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable wltype-realtime
sudo systemctl start wltype-realtime
sudo systemctl status wltype-realtime
```

---

### Keyboard Shortcut Integration

Create a script `~/scripts/quick-dictate.sh`:

```bash
#!/bin/bash
# Quick dictation shortcut

# Check if window is focused
if xdotool getactivewindow; then
    cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
    /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/python \
        wltype_integration.py --realtime --typing-speed 0.05
fi
```

Make executable:
```bash
chmod +x ~/scripts/quick-dictate.sh
```

Bind to keyboard shortcut in your DE settings (e.g., `Super+D`).

---

## Tips & Best Practices

### 1. Test Before Production

```bash
# Always test with a simple text editor first
# Open gedit/kate/notepad
python wltype_integration.py --check
python wltype_integration.py --realtime
```

### 2. Pre-configure Device

```bash
# Find your device once
python wltype_integration.py --list-devices

# Create alias in ~/.bashrc
alias dictate='python /path/to/wltype_integration.py --realtime --device 0 --typing-speed 0.05'

# Then just use:
dictate
```

### 3. Use Configuration Files

Create `~/.config/wltype/config.sh`:

```bash
#!/bin/bash
export WLTYPE_SERVER="http://localhost:9090"
export WLTYPE_DEVICE="0"
export WLTYPE_TYPING_SPEED="0.05"
export WLTYPE_REFRESH_INTERVAL="3"
```

Source in your script:
```bash
source ~/.config/wltype/config.sh
python wltype_integration.py \
  --realtime \
  --server "$WLTYPE_SERVER" \
  --device "$WLTYPE_DEVICE" \
  --typing-speed "$WLTYPE_TYPING_SPEED"
```

---

### 4. Handle Errors Gracefully

```bash
#!/bin/bash
# Robust transcription script

check_server() {
    curl -s http://localhost:9090/health > /dev/null
    return $?
}

if ! check_server; then
    echo "Starting server..."
    python hybrid_server.py &
    sleep 5
fi

python wltype_integration.py --file "$1" --type-speed 12
```

---

### 5. Quality Control

For important transcriptions:

```bash
# 1. Use file mode for better quality
python wltype_integration.py --file important.mp3 --type-speed 8

# 2. Review in text editor
# 3. Make corrections
# 4. Save final version
```

---

## Remote Server Usage

### Connect to Remote Server

```bash
# Use remote server
python wltype_integration.py \
  --realtime \
  --server http://192.168.1.100:9090 \
  --device 0

# Or with file mode
python wltype_integration.py \
  --file audio.mp3 \
  --server http://192.168.1.100:9090
```

### SSH Tunnel for Security

```bash
# Create SSH tunnel
ssh -L 9090:localhost:9090 user@remote-server

# Then use local connection
python wltype_integration.py --realtime --server http://localhost:9090
```

---

## Multi-Language Support

### Auto-detect Language

```bash
python wltype_integration.py --file multilingual.mp3 --language auto
```

### Specific Languages

```bash
# Spanish
python wltype_integration.py --file spanish.mp3 --language es

# French
python wltype_integration.py --file french.mp3 --language fr

# German
python wltype_integration.py --file german.mp3 --language de

# Japanese
python wltype_integration.py --file japanese.mp3 --language ja
```

---

## Performance Tuning

### Speed vs Accuracy

```bash
# Maximum speed (may have errors)
python wltype_integration.py \
  --file audio.mp3 \
  --type-speed 30 \
  --timeout 60

# Maximum accuracy (slower)
python wltype_integration.py \
  --file audio.mp3 \
  --type-speed 5 \
  --timeout 600 \
  --language auto
```

---

## Conclusion

The wltype integration provides powerful automation for transcription workflows. Experiment with different settings to find what works best for your use case!
