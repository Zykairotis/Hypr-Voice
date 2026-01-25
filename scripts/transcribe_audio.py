#!/usr/bin/env python3
import requests
import sys
import time

WHISPER_SERVER = "http://localhost:9099"
AUDIO_FILE = "/home/mewtwo/Downloads/AD-CONAF-2019BC-MID-JPWiser-v2+(1).mp3"

# Check server health
try:
    response = requests.get(f"{WHISPER_SERVER}/", timeout=5)
    if response.status_code != 200:
        sys.stderr.write("Server not responding\n")
        sys.exit(1)
except requests.exceptions.RequestException:
    sys.stderr.write("Server not running\n")
    sys.exit(1)

# Create session
session_response = requests.post(f"{WHISPER_SERVER}/sessions")
session_id = session_response.json()["session_id"]

# Upload and transcribe with explicit file metadata
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

# Wait for processing (3.6MB MP3 ~15 seconds)
time.sleep(15)

# Get final result
status_response = requests.get(f"{WHISPER_SERVER}/sessions/{session_id}")
data = status_response.json()

# Output only the transcript text
result = data.get("text", "")
print(result, end="")
