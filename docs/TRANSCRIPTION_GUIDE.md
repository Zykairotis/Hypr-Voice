# Hypr-Voice Audio Transcription Guide

Complete guide to transcribing audio files using the Hypr-Whisper transcription service.

## Overview

The transcription script allows you to convert audio files (MP3, WAV, FLAC, etc.) to text using the Hypr-Whisper server. The script handles:

- **Health checks** - Ensures the server is running before attempting transcription
- **Session management** - Creates and manages transcription sessions automatically
- **File upload** - Properly formats audio files for the Whisper API
- **Async processing** - Waits for transcription to complete before returning results
- **Clean output** - Returns only the transcribed text, suitable for piping or further processing

---

## Prerequisites

### 1. Start the Hypr-Whisper Server

```bash
cd src/Hypr-Whisper
./scripts/start_hybrid_server.sh start
```

Verify it's running:
```bash
curl http://localhost:9099/
```

Expected response: Server status JSON

### 2. Install Dependencies

The script only requires `requests`:

```bash
pip install requests
```

---

## Quick Start

### Basic Usage

```bash
python3 scripts/transcribe_audio.py
```

The script will output only the transcribed text:

```
Hey, this happens all the time. I bet this has happened to you guys...
```

### Saving Output to File

```bash
python3 scripts/transcribe_audio.py > transcript.txt
```

### Using in Pipes

```bash
python3 scripts/transcribe_audio.py | wc -l  # Count lines
python3 scripts/transcribe_audio.py | grep -i "whiskey"  # Search for keywords
```

---

## Script Configuration

The script has two main configurable variables at the top:

```python
WHISPER_SERVER = "http://localhost:9099"  # Whisper server URL
AUDIO_FILE = "/path/to/your/audio.mp3"    # Audio file path
```

### Changing the Audio File

Edit the `AUDIO_FILE` variable to transcribe different files:

```python
AUDIO_FILE = "/home/user/podcast.mp3"
```

Or modify the script to accept command-line arguments (see Advanced section below).

---

## Supported Audio Formats

| Format | Extensions | Notes |
|--------|-----------|-------|
| **MP3** | `.mp3` | ✅ Widely compatible |
| **WAV** | `.wav` | ✅ Best quality |
| **FLAC** | `.flac` | ✅ Lossless |
| **OGG** | `.ogg` | ✅ Open format |
| **M4A** | `.m4a` | ✅ Apple format |
| **Video** | `.mp4`, `.mkv`, `.avi` | ✅ Audio extracted |

---

## How It Works

```
┌──────────────────────────────────────────────────────────────┐
│                    Transcription Flow                         │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. HEALTH CHECK                                              │
│     ├─ GET http://localhost:9099/                            │
│     └─ Verify server responds with 200 OK                    │
│                                                              │
│  2. CREATE SESSION                                            │
│     ├─ POST http://localhost:9099/sessions                   │
│     └─ Receive session_id: "abc-123-def"                     │
│                                                              │
│  3. UPLOAD AUDIO                                              │
│     ├─ POST /sessions/{session_id}/transcribe                │
│     ├─ Content-Type: multipart/form-data                     │
│     └─ Send audio file with proper metadata                  │
│                                                              │
│  4. WAIT FOR PROCESSING                                       │
│     ├─ Sleep for ~15 seconds (adjust based on file size)     │
│     └─ Whisper processes audio asynchronously                │
│                                                              │
│  5. RETRIEVE TRANSCRIPT                                       │
│     ├─ GET /sessions/{session_id}                            │
│     ├─ Status: "completed"                                   │
│     └─ Return transcribed text                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Key Implementation Details

#### File Upload Format

The critical part that makes the upload work correctly:

```python
files = {
    "audio_file": (
        "recording.mp3",  # Filename (required by API)
        f,                # File object (opened in binary mode)
        "audio/mpeg"      # Content type (MIME type)
    )
}
```

**Why this matters:**
- The Whisper API expects a multipart upload with specific field names
- Without the filename and content-type, the upload may succeed but produce empty results
- Different file formats need different MIME types (audio/mpeg, audio/wav, etc.)

#### Wait Time Calculation

```python
time.sleep(15)  # For 3.6MB MP3 file
```

Adjust based on your file size:

| File Size | Recommended Wait |
|-----------|------------------|
| < 1 MB | 5 seconds |
| 1-5 MB | 15 seconds |
| 5-10 MB | 30 seconds |
| > 10 MB | 60+ seconds |

---

## Script Code

Here's the complete working script:

```python
#!/usr/bin/env python3
import requests
import sys
import time

WHISPER_SERVER = "http://localhost:9099"
AUDIO_FILE = "/path/to/your/audio.mp3"

# 1. Check server health
try:
    response = requests.get(f"{WHISPER_SERVER}/", timeout=5)
    if response.status_code != 200:
        sys.stderr.write("Server not responding\n")
        sys.exit(1)
except requests.exceptions.RequestException:
    sys.stderr.write("Server not running\n")
    sys.exit(1)

# 2. Create session
session_response = requests.post(f"{WHISPER_SERVER}/sessions")
session_id = session_response.json()["session_id"]

# 3. Upload and transcribe
with open(AUDIO_FILE, "rb") as f:
    files = {
        "audio_file": (
            "recording.mp3",  # filename
            f,                # file object
            "audio/mpeg"      # content type
        )
    }
    requests.post(
        f"{WHISPER_SERVER}/sessions/{session_id}/transcribe",
        files=files
    )

# 4. Wait for processing
time.sleep(15)

# 5. Get result
status_response = requests.get(f"{WHISPER_SERVER}/sessions/{session_id}")
data = status_response.json()

# Output only the transcript
result = data.get("text", "")
print(result, end="")
```

---

## Advanced Usage

### Command-Line Arguments Version

```python
#!/usr/bin/env python3
import requests
import sys
import time
import argparse
import os

def get_mime_type(filepath):
    """Determine MIME type based on file extension."""
    ext = os.path.splitext(filepath)[1].lower()
    mime_types = {
        '.mp3': 'audio/mpeg',
        '.wav': 'audio/wav',
        '.flac': 'audio/flac',
        '.ogg': 'audio/ogg',
        '.m4a': 'audio/mp4',
        '.mp4': 'audio/mp4',
        '.mkv': 'audio/x-matroska',
    }
    return mime_types.get(ext, 'audio/mpeg')

def transcribe(audio_file, server_url="http://localhost:9099", wait_time=15):
    # Check server health
    try:
        response = requests.get(f"{server_url}/", timeout=5)
        if response.status_code != 200:
            sys.stderr.write("Server not responding\n")
            sys.exit(1)
    except requests.exceptions.RequestException:
        sys.stderr.write("Server not running\n")
        sys.exit(1)

    # Create session
    session_response = requests.post(f"{server_url}/sessions")
    session_id = session_response.json()["session_id"]

    # Upload and transcribe
    mime_type = get_mime_type(audio_file)
    with open(audio_file, "rb") as f:
        files = {
            "audio_file": (
                os.path.basename(audio_file),
                f,
                mime_type
            )
        }
        requests.post(
            f"{server_url}/sessions/{session_id}/transcribe",
            files=files
        )

    # Wait for processing
    time.sleep(wait_time)

    # Get result
    status_response = requests.get(f"{server_url}/sessions/{session_id}")
    data = status_response.json()
    result = data.get("text", "")
    print(result, end="")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transcribe audio using Hypr-Whisper")
    parser.add_argument("audio_file", help="Path to audio file")
    parser.add_argument("--server", default="http://localhost:9099", help="Whisper server URL")
    parser.add_argument("--wait", type=int, default=15, help="Wait time in seconds")
    args = parser.parse_args()
    transcribe(args.audio_file, args.server, args.wait)
```

Usage:
```bash
python3 transcribe_cli.py /path/to/audio.mp3
python3 transcribe_cli.py /path/to/audio.mp3 --wait 30
python3 transcribe_cli.py /path/to/audio.mp3 --server http://192.168.1.100:9099
```

---

## Error Handling

The script handles these error scenarios:

### Server Not Running
```
$ python3 scripts/transcribe_audio.py
Server not running
$ echo $?
1
```

### Server Not Responding
```
$ python3 scripts/transcribe_audio.py
Server not responding
$ echo $?
1
```

### Empty Transcription
If the audio file is silent or corrupted, the script will exit with empty output.

---

## Troubleshooting

### Issue: "Server not running"

**Solution:** Start the Whisper server
```bash
cd src/Hypr-Whisper && ./scripts/start_hybrid_server.sh start
```

### Issue: Empty transcription returned

**Causes:**
1. Wait time too short for large files
2. Audio file is silent or corrupted
3. Incorrect MIME type

**Solutions:**
1. Increase `time.sleep()` value
2. Test with a known good audio file
3. Verify MIME type matches file format

### Issue: Partial transcription

**Cause:** Audio quality too low or background noise too high

**Solution:** Use higher quality audio or preprocess with noise reduction

---

## API Endpoints Reference

### Health Check
```
GET http://localhost:9099/
```

### Create Session
```
POST http://localhost:9099/sessions
Response: {"session_id": "uuid", "status": "running", ...}
```

### Transcribe Audio
```
POST http://localhost:9099/sessions/{session_id}/transcribe
Content-Type: multipart/form-data
Body: audio_file=<binary>
```

### Get Session Status
```
GET http://localhost:9099/sessions/{session_id}
Response: {"status": "completed", "text": "transcript here"}
```

---

## Performance Tips

1. **Use WAV format** for fastest processing
2. **Keep files under 10MB** for optimal performance
3. **Use 16kHz sample rate** - matches Whisper's training data
4. **Mono audio** is sufficient for speech
5. **Batch process** multiple files by running scripts in parallel

---

## Integration Examples

### Bash Script - Batch Processing

```bash
#!/bin/bash
for file in recordings/*.mp3; do
    echo "Processing $file..."
    python3 scripts/transcribe_audio.py > "transcripts/$(basename "$file" .mp3).txt"
done
```

### Python - Programmatic Use

```python
import subprocess

def transcribe_file(audio_path):
    result = subprocess.run(
        ["python3", "scripts/transcribe_audio.py"],
        capture_output=True,
        text=True
    )
    return result.stdout

transcript = transcribe_file("meeting.mp3")
print(transcript)
```

### Node.js - Child Process

```javascript
const { exec } = require('child_process');

exec('python3 scripts/transcribe_audio.py', (error, stdout) => {
    if (error) {
        console.error(`Error: ${error}`);
        return;
    }
    console.log(`Transcript: ${stdout}`);
});
```

---

## Summary

| Feature | Description |
|---------|-------------|
| **Server** | Hypr-Whisper on port 9099 |
| **Formats** | MP3, WAV, FLAC, OGG, M4A, video |
| **Output** | Plain text transcript only |
| **Dependencies** | `requests` library only |
| **Error Handling** | Health check, graceful failures |
| **Use Cases** | Transcription, subtitles, voice commands |

For more information, see the main [AUDIO_ENDPOINTS_GUIDE.md](AUDIO_ENDPOINTS_GUIDE.md).
