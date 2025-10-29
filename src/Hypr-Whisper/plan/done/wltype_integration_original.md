"""
Hybrid Whisper Server - wltype Integration
============================================

Simulates typing transcriptions on screen using wltype.

Two modes:
1. REALTIME: Streams audio via WebSocket, types new content every few seconds
2. API: Uploads file, waits for complete transcription, then types entire result
"""

import asyncio
import subprocess
import sys
import time
import threading
from hybrid_client import HybridWhisperClient

# ============================================================================
# WLTYPE UTILITIES
# ============================================================================

def is_wayland():
    """Check if running on Wayland desktop."""
    return subprocess.run(
        ["echo", "$XDG_SESSION_TYPE"],
        capture_output=True,
        text=True
    ).stdout.strip() == "wayland" or "WAYLAND" in subprocess.run(
        ["env"],
        capture_output=True,
        text=True
    ).stdout

def check_wltype_installed():
    """Check if wltype is installed."""
    try:
        result = subprocess.run(
            ["which", "wltype"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
        print("✗ wltype not found!")
        print("  Install with: sudo apt-get install wltype (Wayland)")
        print("  or use: xdotool type (X11)")
        return False
    except Exception as e:
        print(f"✗ Error checking wltype: {e}")
        return False

def type_text(text, typing_speed=0.05):
    """
    Type text on screen using wltype or xdotool.
    
    Args:
        text: Text to type
        typing_speed: Delay between characters in seconds (0 = instant)
    """
    if not text:
        return
    
    try:
        # Escape special characters for shell
        escaped_text = text.replace("'", "'\"'\"'")
        
        if is_wayland():
            # Use wltype for Wayland
            if typing_speed > 0:
                for char in text:
                    subprocess.run(
                        ["wltype", char],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL
                    )
                    time.sleep(typing_speed)
            else:
                subprocess.run(
                    ["wltype", text],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
        else:
            # Use xdotool for X11
            if typing_speed > 0:
                subprocess.run(
                    ["xdotool", "type", "--delay", str(int(typing_speed * 1000)), text],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.run(
                    ["xdotool", "type", text],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
    
    except FileNotFoundError:
        print("✗ wltype/xdotool not found. Install with:")
        print("  Wayland: sudo apt-get install wltype")
        print("  X11: sudo apt-get install xdotool")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"✗ Error typing text: {e}")

def type_text_gradually(text, chars_per_second=10):
    """Type text gradually, simulating natural typing."""
    typing_speed = 1.0 / chars_per_second
    type_text(text, typing_speed=typing_speed)

# ============================================================================
# MODE 1: REALTIME STREAMING WITH WLTYPE
# ============================================================================

class RealtimeTyper:
    """Stream audio and type incremental transcriptions."""
    
    def __init__(self, server_url="http://localhost:9090", device=None, typing_speed=0.05):
        self.client = HybridWhisperClient(server_url)
        self.device = device
        self.typing_speed = typing_speed
        self.last_typed_text = ""
        self.session_id = None
        self.monitoring = False
    
    async def start_streaming(self):
        """Start microphone streaming and type transcriptions."""
        print("\n" + "="*60)
        print("REALTIME TRANSCRIPTION WITH AUTO-TYPING")
        print("="*60)
        print("\n▶ Starting microphone stream...")
        print("  Click on a text field to start typing")
        print("  Press Ctrl+C to stop\n")
        
        # Create session
        self.session_id = self.client.create_session(language="auto")
        print(f"✓ Session created: {self.session_id}\n")
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self.monitor_and_type())
        
        try:
            # Start streaming
            await self.client.stream_microphone_ws(device=self.device)
        except KeyboardInterrupt:
            print("\n\n✓ Stopped")
        finally:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    async def monitor_and_type(self):
        """Monitor transcription and type new content every few seconds."""
        try:
            while True:
                await asyncio.sleep(3)  # Check every 3 seconds
                
                # Get current transcription
                result = self.client.get_session(self.session_id)
                if result:
                    current_text = result.get("text", "")
                    
                    # Check if there's new content
                    if current_text != self.last_typed_text:
                        # Find the new portion
                        if current_text.startswith(self.last_typed_text):
                            new_text = current_text[len(self.last_typed_text):]
                            
                            if new_text.strip():
                                print(f"\n📝 Typing: {new_text}")
                                type_text(new_text, typing_speed=self.typing_speed)
                                self.last_typed_text = current_text
                        else:
                            # Text was modified, type everything
                            print(f"\n📝 Typing: {current_text}")
                            type_text(current_text, typing_speed=self.typing_speed)
                            self.last_typed_text = current_text
        
        except asyncio.CancelledError:
            pass

# ============================================================================
# MODE 2: FILE UPLOAD WITH WLTYPE
# ============================================================================

class FileTyper:
    """Upload file, wait for transcription, then type result."""
    
    def __init__(self, server_url="http://localhost:9090", typing_speed=0.01):
        self.client = HybridWhisperClient(server_url)
        self.typing_speed = typing_speed
    
    def transcribe_and_type(self, filepath, language="en", timeout=300):
        """
        Upload file and type transcription result.
        
        Args:
            filepath: Path to audio/video file
            language: Language code (default: auto-detect)
            timeout: Maximum wait time in seconds
        """
        print("\n" + "="*60)
        print("FILE TRANSCRIPTION WITH AUTO-TYPING")
        print("="*60)
        
        print(f"\n▶ File: {filepath}")
        print("  Waiting for transcription...")
        
        # Create session
        session_id = self.client.create_session(language=language)
        print(f"✓ Session: {session_id}\n")
        
        # Upload file
        self.client.transcribe_file(filepath, session_id=session_id)
        print("✓ File uploaded\n")
        
        # Wait for transcription
        start_time = time.time()
        last_printed = ""
        
        print("⏳ Transcribing")
        print("-" * 60)
        
        while time.time() - start_time < timeout:
            result = self.client.get_session(session_id)
            
            if result:
                status = result.get("status")
                text = result.get("text", "")
                
                # Show updates
                if text != last_printed:
                    print(f"\r{text}", end="", flush=True)
                    last_printed = text
                
                # Check if done
                if status == "completed":
                    print("\n" + "-" * 60)
                    print("✓ Transcription complete\n")
                    
                    # Type the result
                    if text:
                        print(f"📝 Typing transcription ({len(text)} characters)...")
                        type_text_gradually(text, chars_per_second=10)
                        print("\n✓ Done typing")
                    else:
                        print("⚠ No transcription generated")
                    
                    return text
            
            time.sleep(1)
        
        print(f"\n✗ Timeout after {timeout} seconds")
        return None

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hybrid Whisper with wltype Auto-Typing"
    )
    
    parser.add_argument(
        "--server",
        default="http://localhost:9090",
        help="Server URL (default: http://localhost:9090)"
    )
    
    # Realtime mode
    realtime_group = parser.add_argument_group("Realtime Mode")
    realtime_group.add_argument(
        "--realtime",
        action="store_true",
        help="Stream microphone and auto-type transcriptions"
    )
    realtime_group.add_argument(
        "--device",
        type=int,
        help="Audio device ID (default: system default)"
    )
    realtime_group.add_argument(
        "--typing-speed",
        type=float,
        default=0.05,
        help="Delay between characters (seconds, default: 0.05)"
    )
    realtime_group.add_argument(
        "--refresh-interval",
        type=int,
        default=3,
        help="Check for new text every N seconds (default: 3)"
    )
    
    # File mode
    file_group = parser.add_argument_group("File Mode")
    file_group.add_argument(
        "--file",
        help="Audio/video file to transcribe and auto-type"
    )
    file_group.add_argument(
        "--language",
        default="en",
        help="Language code (default: en)"
    )
    file_group.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Max wait time in seconds (default: 300)"
    )
    file_group.add_argument(
        "--type-speed",
        type=float,
        default=10,
        help="Characters per second for typing (default: 10)"
    )
    
    # Common
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if wltype is installed"
    )
    
    args = parser.parse_args()
    
    # Check wltype installation
    if args.check:
        if check_wltype_installed():
            print("✓ wltype is installed")
        return
    
    # List devices
    if args.list_devices:
        print("\nAvailable audio devices:")
        from hybrid_client import list_audio_devices
        list_audio_devices()
        return
    
    # Realtime mode
    if args.realtime:
        if not check_wltype_installed():
            sys.exit(1)
        
        print("\n⏰ Realtime Mode Configuration:")
        print(f"  Server: {args.server}")
        print(f"  Device: {args.device or 'default'}")
        print(f"  Typing speed: {args.typing_speed}s per char")
        print(f"  Refresh interval: {args.refresh_interval}s\n")
        
        typer = RealtimeTyper(
            server_url=args.server,
            device=args.device,
            typing_speed=args.typing_speed
        )
        
        asyncio.run(typer.start_streaming())
    
    # File mode
    elif args.file:
        if not check_wltype_installed():
            sys.exit(1)
        
        print("\n📁 File Mode Configuration:")
        print(f"  Server: {args.server}")
        print(f"  File: {args.file}")
        print(f"  Language: {args.language}")
        print(f"  Typing speed: {args.type_speed} chars/sec\n")
        
        typer = FileTyper(
            server_url=args.server,
            typing_speed=1.0 / args.type_speed
        )
        
        typer.transcribe_and_type(
            filepath=args.file,
            language=args.language,
            timeout=args.timeout
        )
    
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("EXAMPLES")
        print("="*60)
        print("\n1. Realtime streaming with auto-typing:")
        print("   python wltype_integration.py --realtime --device 0")
        print("\n2. File transcription with auto-typing:")
        print("   python wltype_integration.py --file audio.mp3")
        print("\n3. Check if wltype is installed:")
        print("   python wltype_integration.py --check")
        print("\n4. List audio devices:")
        print("   python wltype_integration.py --list-devices")

if __name__ == "__main__":
    main()








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

#### macOS

```bash
# Install via Homebrew
brew install xdotool

# Or compile from source
# https://github.com/jordansissel/xdotool
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

### Workflow

1. **Start the script**
   ```bash
   python wltype_integration.py --realtime
   ```

2. **Click on a text field** (browser, text editor, chat app, etc.)

3. **Speak into microphone** - transcription will appear and type automatically

4. **Stop with Ctrl+C**

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

### Workflow

1. **Start transcription**
   ```bash
   python wltype_integration.py --file meeting.mp3
   ```

2. **Wait for processing** - server transcribes the entire file

3. **Automatic typing** - once done, text automatically types into focused window

4. **Done!** - transcription is typed completely

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

## Troubleshooting

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

### Typing not appearing

**Checklist:**
- ✓ Text input field is focused (cursor visible)
- ✓ Window is in foreground
- ✓ wltype/xdotool is installed and working
- ✓ Running on correct desktop (Wayland vs X11)

**Test wltype:**
```bash
# This should type "Hello" in the focused window
echo "Hello" | wltype

# Or directly
wltype "Hello world"
```

### Character encoding issues

```bash
# If special characters don't work, try:
python wltype_integration.py --file audio.mp3 --type-speed 5

# Slower typing sometimes helps with encoding
```

### Server connection error

```
Error: Connection refused
```

**Solution:**
```bash
# Make sure server is running in another terminal
python hybrid_server.py

# Then try again
python wltype_integration.py --realtime
```

---

## Advanced Usage

### Batch Multiple Files

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

## Tips & Tricks

### 1. Pause Typing
Press Ctrl+C to pause, then restart with same or new file

### 2. Copy Text Later
Output is also displayed in terminal and can be copied from server logs:
```bash
tail -f logs/hybrid_server.log
```

### 3. Combine with Other Tools
```bash
# Pipe to file while typing
python wltype_integration.py --file audio.mp3 | tee transcription.txt
```

### 4. Keyboard Shortcuts
After typing, use standard shortcuts:
- `Ctrl+A` - Select all
- `Ctrl+C` - Copy
- `Ctrl+Z` - Undo
- `Ctrl+S` - Save

### 5. Test First
Before using with important documents:
```bash
# Test with simple file
python wltype_integration.py --file test_audio.mp3
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



#!/bin/bash
# ============================================================================
# Hybrid Whisper + wltype Integration - Quick Examples
# ============================================================================

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Helper functions
print_section() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ $1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}"
}

print_example() {
    echo -e "\n${YELLOW}▶ Example: $1${NC}"
}

print_command() {
    echo -e "${GREEN}$ $1${NC}"
}

print_note() {
    echo -e "${YELLOW}📌 Note: $1${NC}"
}

# ============================================================================
# SETUP CHECK
# ============================================================================
check_setup() {
    print_section "CHECKING SETUP"
    
    echo ""
    echo "Checking Python..."
    if python3 --version &> /dev/null; then
        echo "✓ Python 3 installed"
    else
        echo "✗ Python 3 not found"
        exit 1
    fi
    
    echo ""
    echo "Checking wltype/xdotool..."
    if which wltype &> /dev/null; then
        echo "✓ wltype installed (Wayland)"
    elif which xdotool &> /dev/null; then



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

## Real-Time vs File Mode

### Flow Diagram

**Real-Time:**
```
Microphone Stream
       ↓
Continuous transcription
       ↓
Check every 3 seconds
       ↓
Type new content (incremental)
       ↓
Keep typing as more arrives
```

**File Mode:**
```
Upload File
    ↓
Wait for processing
    ↓
Complete transcription
    ↓
Type entire result (one go)
```

### Comparison Table

```
┌─────────────────────┬──────────────────────┬──────────────────────┐
│ Aspect              │ Real-Time            │ File Mode            │
├─────────────────────┼──────────────────────┼──────────────────────┤
│ Activation          │ Immediate            │ After upload         │
│ Typing              │ Incremental          │ All at once          │
│ Duration            │ Continuous           │ One-time             │
│ Best for            │ Live dictation       │ Recording conversion │
│ Latency             │ 3-5 seconds          │ Minutes (processing) │
│ Pausing             │ Natural              │ Not possible         │
│ Use case            │ Chat, notes, code    │ Email, documents     │
│ Example command     │ `--realtime`         │ `--file audio.mp3`   │
└─────────────────────┴──────────────────────┴──────────────────────┘
```

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

## Troubleshooting

### Text Not Appearing

**Problem:** Text doesn't type after running the command

**Solutions:**
1. Make sure text input field is **focused** (cursor visible)
2. Try clicking in a simple text field first (like a text editor)
3. Run this to test: `echo "Hello" | wltype`

### Server Connection Error

**Problem:** "Connection refused" error

**Solution:**
```bash
# Start server in another terminal
python hybrid_server.py

# Then try again
python wltype_integration.py --realtime
```

### wltype Not Found

**Problem:** "wltype not found" error

**Solution:**
```bash
# For Wayland
sudo apt-get install wltype

# For X11
sudo apt-get install xdotool
```

### Audio Device Issues

**Problem:** Wrong microphone is being used

**Solution:**
```bash
# List devices
python wltype_integration.py --list-devices

# Use specific device
python wltype_integration.py --realtime --device 2
```

### Typing Too Fast/Slow

**Problem:** Text types too quickly or too slowly

**Solution:**
```bash
# Real-time mode - adjust typing-speed
python wltype_integration.py --realtime --typing-speed 0.1  # Slower

# File mode - adjust type-speed
python wltype_integration.py --file audio.mp3 --type-speed 5  # Slower
```

### Character Encoding Issues

**Problem:** Special characters appear wrong

**Solution:**
```bash
# Try slower typing speed
python wltype_integration.py --file audio.mp3 --type-speed 5
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

### 4. Copy Before Typing
```bash


# Visual Guide: Real-Time vs File Mode with wltype

## Side-by-Side Comparison

### Real-Time Mode: Incremental Typing 🎤

```
COMMAND:
python wltype_integration.py --realtime

TIMELINE:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ 0-3s    │ 3-6s    │ 6-9s    │ 9-12s   │ 12-15s  │
└─────────┴─────────┴─────────┴─────────┴─────────┘
   ↓         ↓         ↓         ↓         ↓
 "Hello"   "Hello"  "Hello"   "Hello    "Hello
           "world"  "world"   "world"   "world"
                    "this"    "this is" "this is
                              "a"       "a test"

YOUR SCREEN SHOWS:
┌────────────────────────────────────────────────┐
│ Hello                                          │
└────────────────────────────────────────────────┘
        ↓ (3 seconds pass)
┌────────────────────────────────────────────────┐
│ Hello world                                    │
└────────────────────────────────────────────────┘
        ↓ (3 seconds pass)
┌────────────────────────────────────────────────┐
│ Hello world this                               │
└────────────────────────────────────────────────┘
        ↓ (3 seconds pass)
┌────────────────────────────────────────────────┐
│ Hello world this is a test                     │
└────────────────────────────────────────────────┘

CHARACTERISTICS:
✓ Types as you speak
✓ Refreshes every 3 seconds (configurable)
✓ Only NEW text gets typed
✓ Incremental appearance
✓ Natural typing effect
```

---

### File Mode: Complete Text at Once 📁

```
COMMAND:
python wltype_integration.py --file audio.mp3

TIMELINE:
┌──────────────────────────────────────────────────────┐
│ 0-30s (or more)                                      │
│ Server processes entire file                        │
└──────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────┐
│ Processing complete                                  │
│ Server has: "Hello world this is a test message"    │
└──────────────────────────────────────────────────────┘
           ↓
┌──────────────────────────────────────────────────────┐
│ Typing starts - types entire text at once           │
└──────────────────────────────────────────────────────┘

YOUR SCREEN SHOWS:
(Nothing for 30 seconds while file processes)

Then suddenly:
┌────────────────────────────────────────────────────┐
│ H                                                  │
└────────────────────────────────────────────────────┘
│ He
│ Hel
│ Hell
│ Hello
│ Hello 
│ Hello w
│ Hello wo
│ Hello wor
│ Hello worl
│ Hello world
│ Hello world 
│ Hello world t
│ Hello world th
│ Hello world thi
│ Hello world this
│ Hello world this 
│ Hello world this i
│ Hello world this is
│ Hello world this is 
│ Hello world this is a
│ Hello world this is a 
│ Hello world this is a t
│ Hello world this is a te
│ Hello world this is a tes
│ Hello world this is a test
│ Hello world this is a test 
│ Hello world this is a test m
│ Hello world this is a test me
│ Hello world this is a test mes
│ Hello world this is a test mess
│ Hello world this is a test messa
│ Hello world this is a test messag
│ Hello world this is a test message
└────────────────────────────────────────────────────┘

CHARACTERISTICS:
✓ Wait for complete transcription first
✓ Then type entire result at once
✓ One continuous typing stream
✓ No waiting during typing
✓ Great for documents/emails
```

---

## Use Case Flowcharts

### Real-Time: Live Dictation to Google Docs

```
Start Script
    ↓
Microphone listens
    ↓
Every 3 seconds:
  Get transcription → Type new content
    ↓
Result: Live typing as you speak
    ↓
Stop (Ctrl+C)
    ↓
All text in Google Docs!

Timeline:
Speak: "Hello world this is a test"
    ↓ 3 seconds
Types: "Hello"
    ↓ 3 seconds (speaking continues)
Types: " world"
    ↓ 3 seconds (speaking continues)
Types: " this"
    ↓ 3 seconds (speaking continues)
Types: " is"
    ↓ 3 seconds (speaking continues)
Types: " a"
    ↓ 3 seconds (speaking continues)
Types: " test"
    ↓ (Done!)
```

---

### File Mode: Voice Message to Email

```
You receive: Voice message (voice.mp3)
    ↓
Save to file
    ↓
python wltype_integration.py --file voice.mp3
    ↓
Wait while file processes (30-60 seconds)
    ↓
ENTIRE message types into email
    ↓
Send email!

Timeline:
Upload: voice.mp3 (5 MB)
    ↓ 30-60 seconds
Server transcribes: "Thanks for the update, I'll review it tomorrow morning"
    ↓ 1-2 seconds (all text types)
Email shows: "Thanks for the update, I'll review it tomorrow morning"
```

---

## Decision Tree: Which Mode to Use?

```
┌─────────────────────────────────────┐
│ What do you want to do?             │
└─────────────────────────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ↓             ↓
"Speak and have  "I have a file
it type live"    to transcribe"
    │             │
    ↓             ↓
REAL-TIME      FILE MODE
    │             │
    ├─→ Chat      ├─→ Email
    ├─→ Docs      ├─→ Document
    ├─→ Code      ├─→ Video
    ├─→ Notes     ├─→ Audio
    └─→ Email     └─→ Message
```

---

## Speed Comparison

### Real-Time Mode - Typing Speed Impact

```
--typing-speed 0.01s (100 chars/sec)
Text appears INSTANTLY

--typing-speed 0.02s (50 chars/sec)
H█████████e█████████l█████████l█████████o

--typing-speed 0.05s (20 chars/sec)
H_________e_________l_________l_________o

--typing-speed 0.1s (10 chars/sec)
H_______________e_______________l_______________l_______________o

Best for watching: 0.05s - 0.1s
Feels natural: 0.02s - 0.05s
Super fast: 0.01s - 0.02s
```

---

### File Mode - Type Speed Impact

```
--type-speed 5 (5 chars/sec)
████████████ SLOW ████████████
1000 chars takes 200 seconds (3+ minutes)
Good for: Demos, watching every letter

--type-speed 10 (10 chars/sec)
████████ MEDIUM ████████
1000 chars takes 100 seconds (1.5+ minutes)
Good for: Normal reading

--type-speed 20 (20 chars/sec)
████ FAST ████
1000 chars takes 50 seconds
Good for: Impatient people, fast typing

--type-speed 50 (50 chars/sec)
█ VERY FAST █
1000 chars takes 20 seconds
Good for: Can barely see it appearing
```

---

## Real Example Scenarios

### Scenario 1: Discord Voice Message 💬

```
YOU RECEIVE:
🎤 Voice message from friend

WORKFLOW:
1. Save voice message as "msg.mp3"

2. Open Discord, click in chat box

3. Run:
   python wltype_integration.py --file msg.mp3 --type-speed 15

4. RESULT:
   [30 seconds of waiting]
   Friend's message transcription appears in your chat!

5. You can edit/modify before sending

DIAGRAM:
Voice Message (msg.mp3)
        ↓
    [PROCESSING]
        ↓
 Server transcribes
        ↓
 Entire message types into Discord
        ↓
   You hit Send!
```

---

### Scenario 2: Live Meeting Notes 📝

```
YOU HAVE:
- A meeting happening RIGHT NOW
- A document open where you want to take notes

WORKFLOW:
1. Open Google Docs / Word / Whatever

2. Click in document where you want notes

3. Run:
   python wltype_integration.py --realtime --typing-speed 0.05

4. Speak or play audio

5. RESULT:
   Meeting is transcribed and typed LIVE into your document!

DIAGRAM:
Meeting Audio (streaming)
        ↓
   [REAL-TIME]
        ↓
 Every 3 seconds:
 New words get typed
        ↓
 Document fills with notes as meeting happens!
        ↓
 When done, you have complete meeting notes
```

---

### Scenario 3: Email Dictation 📧

```
YOU WANT:
To dictate an email instead of typing it

WORKFLOW Option A - REAL-TIME:
1. Open email draft, click in body

2. Run:
   python wltype_integration.py --realtime --typing-speed 0.03

3. Speak your email

4. RESULT:
   Email types as you speak!

WORKFLOW Option B - FILE:
1. Record yourself speaking email (email.mp3)

2. Open email draft, click in body

3. Run:
   python wltype_integration.py --file email.mp3 --type-speed 12

4. RESULT:
   Entire email types into draft!

5. Review and send

Which is better?
→ Real-time: More natural, immediate
→ File: Can re-record if mistakes, then type
```

---

### Scenario 4: Video Transcription 🎥

```
YOU HAVE:
- A video file (video.mp4)
- Want transcription in a document

WORKFLOW:
1. Open Google Docs / Document

2. Click in document

3. Run:
   python wltype_integration.py --file video.mp4 --type-speed 10 --timeout 600

4. WAIT:
   - FFmpeg extracts audio
   - Server transcribes audio
   - Typing begins...

5. RESULT:
   Complete video transcription types into document!

TIMELINE:
video.mp4 (100MB)
    ↓ [5 seconds]
Audio extracted (20MB)
    ↓ [60 seconds]
Transcribed: "video content..."
    ↓ [30 seconds]
Text fully typed
    ↓
Complete transcript in document!
```

---

## Latency Comparison

```
REAL-TIME MODE:
Your voice → Microphone → Network → Server → Processing → Typing
             └─ 0.1s ──┘ └─ 0.1s ──┘ └─ 1-3s ──┘ └─ refresh every 3s ──┘
TOTAL: ~3-5 seconds from speaking to typing

FILE MODE:
Your file → Upload → Processing → Complete → Typing
└─ varies ──┘ └─ 1-300s ──┘ └─ instant ──┘
TOTAL: Depends on file size (5 seconds to 5+ minutes)
```

---

## Quality vs Speed

```
REAL-TIME:
Quality:    Medium (processed in chunks)
Speed:      Fast (types continuously)
Latency:    3-5 seconds
Best for:   Live input, chat, notes

FILE MODE:
Quality:    High (full audio context)
Speed:      Slow (wait for full processing)
Latency:    Minutes (but worth it)
Best for:   Important documents, emails
```

---

## Common Patterns

### Pattern 1: Quick Chat

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

## Summary Matrix

```
┌──────────────────┬────────────────┬────────────────┐
│ Aspect           │ Real-Time      │ File Mode      │
├──────────────────┼────────────────┼────────────────┤
│ Start            │ Immediate      │ After upload   │
│ Latency          │ 3-5 seconds    │ Minutes        │
│ Typing           │ Incremental    │ All at once    │
│ Quality          │ Medium         │ High           │
│ Use              │ Live input     │ Recording      │
│ Perfect for      │ Chat, notes    │ Email, docs    │
│ Example command  │ --realtime     │ --file         │
│ Duration         │ As long as you │ One time       │
│ Pausing          │ Possible       │ Not possible   │
│ Editing          │ During        │ After          │
└──────────────────┴────────────────┴────────────────┘
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