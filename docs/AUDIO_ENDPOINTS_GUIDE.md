# Audio Transcription & Audio Sense API Guide

Complete guide for transcribing audio files and generating speech (TTS) using Hypr-Voice endpoints.

## Architecture Overview

Hypr-Voice provides two main servers:

1. **Orchestrator Server** (port 9093) - Main API for voice operations
2. **Hypr-Whisper Server** (port 9099) - Whisper transcription backend

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Audio File     │────▶│   Orchestrator   │────▶│   Whisper STT   │
│  or Text        │     │   (port 9093)    │     │  (port 9099)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  Text Response   │
                        └──────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   Deepgram TTS   │
                        │  (Audio Sense)   │
                        └──────────────────┘
```

## Prerequisites

### Environment Setup

```bash
# Required API Keys
export ANTHROPIC_API_KEY="your-key"
export DEEPGRAM_API_KEY="your-key"  # For TTS

# Optional: For advanced features
export OPENAI_API_KEY="your-key"
export HYPR_VOICE_MODEL="claude-sonnet-4-5"
export HYPR_VOICE_TTS_PROVIDER="deepgram"
export HYPR_VOICE_TTS_VOICE="aura-luna-en"
```

### Start Servers

```bash
# Start everything (orchestrator + whisper + web UI)
./scripts/start_everything.sh start

# Or start individually:
# Hypr-Whisper Server (STT)
cd src/Hypr-Whisper && ./scripts/start_hybrid_server.sh start

# Orchestrator Server
uvicorn hypr_voice.server:app --host 0.0.0.0 --port 9093
```

---

## Endpoint 1: Transcribe Audio File

### POST `/voice/transcribe`

Transcribe an audio file using Whisper STT.

#### Request

```bash
curl -X POST http://localhost:9093/voice/transcribe \
  -F "file=@/path/to/audio.wav" \
  -H "Content-Type: multipart/form-data"
```

#### Python Example

```python
import requests

url = "http://localhost:9093/voice/transcribe"
files = {"file": open("recording.wav", "rb")}

response = requests.post(url, files=files)
result = response.json()

print(f"Transcription: {result['text']}")
print(f"Success: {result['success']}")
```

#### Response

```json
{
  "text": "Hello, this is a transcription of the audio file.",
  "success": true
}
```

#### Supported Audio Formats

- **WAV** (recommended, 16kHz sample rate for optimal performance)
- **MP3** (auto-converted)
- **FLAC** (auto-converted)
- **OGG** (auto-converted)

#### Error Handling

```python
response = requests.post(url, files=files)

if response.status_code == 503:
    print("Voice orchestrator not initialized")
elif response.status_code == 500:
    error_detail = response.json()["detail"]
    print(f"Transcription failed: {error_detail}")
```

---

## Endpoint 2: Text-to-Speech (Audio Sense)

### POST `/voice/speak`

Convert text to speech using Deepgram TTS and get audio file.

#### Request

```bash
curl -X POST http://localhost:9093/voice/speak \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, this is a test of the text to speech system."}' \
  --output response.wav
```

#### Python Example

```python
import requests
import json

url = "http://localhost:9093/voice/speak"
payload = {
    "text": "Hello! This is the Hypr-Voice audio sense system.",
    "voice": "aura-luna-en"  # Optional
}

response = requests.post(url, json=payload)

if response.status_code == 200:
    # Save audio file
    with open("output.wav", "wb") as f:
        f.write(response.content)
    print("Audio saved to output.wav")
else:
    result = response.json()
    print(f"Error: {result.get('error')}")
```

#### Response

Returns WAV audio file directly (Content-Type: `audio/wav`)

#### Available Voices

```
aura-luna-en      # Default, female voice
aura-asteria-en   # Female voice
aura-orion-en     # Male voice
aura-zeus-en      # Male voice
```

---

## Endpoint 3: Process Text with Voice Response

### POST `/voice/process`

Process text through AI and optionally speak the response.

#### Request

```bash
curl -X POST http://localhost:9093/voice/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the weather like today?",
    "conversation_id": null,
    "speak_response": true
  }'
```

#### Python Example

```python
import requests

url = "http://localhost:9093/voice/process"
payload = {
    "text": "Explain quantum computing in simple terms",
    "conversation_id": None,  # New conversation
    "speak_response": True    # Generate TTS
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Response: {result['response']}")
print(f"Agent: {result['agent_type']}")
print(f"Audio file: {result.get('audio_file')}")
```

#### Response

```json
{
  "response": "Quantum computing uses quantum mechanics...",
  "agent_type": "general_assistant",
  "audio_file": "/tmp/audio_response_123.wav",
  "conversation_id": "abc123",
  "success": true
}
```

---

## Endpoint 4: Enhanced Context-Aware Processing

### POST `/voice/process/enhanced`

Process text with full context awareness (active window, clipboard, workspace).

#### Request

```bash
curl -X POST http://localhost:9093/voice/process/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Help me understand this code",
    "context": {
      "window": {
        "class": "code",
        "title": "server.py - Visual Studio Code",
        "workspace": {"id": 1, "name": "workspace 1"}
      },
      "clipboard": "def hello(): print('world')",
      "timestamp": "2025-01-15T10:30:00Z"
    },
    "conversation_id": null,
    "speak_response": true
  }'
```

#### Python Example

```python
import requests
from datetime import datetime

url = "http://localhost:9093/voice/process/enhanced"

# Get context from your application
context = {
    "window": {
        "class": "code",
        "title": "my_file.py - VSCode",
        "workspace": {"id": 1}
    },
    "clipboard": "selected text or code",
    "timestamp": datetime.utcnow().isoformat()
}

payload = {
    "text": "Explain this function",
    "context": context,
    "speak_response": True
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Response: {result['response_text']}")
print(f"Context used: {result['context_used']}")
print(f"Audio: {result.get('audio_file')}")
```

#### Response

```json
{
  "success": true,
  "response_text": "This function does...",
  "conversation_id": "xyz789",
  "audio_file": "/path/to/response.wav",
  "context_used": true,
  "agent_type": "context_aware"
}
```

---

## Endpoint 5: Stream Processing with SSE

### POST `/voice/process/stream`

Server-Sent Events streaming for real-time updates.

#### Request

```bash
curl -N -X POST http://localhost:9093/voice/process/stream \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Tell me a story",
    "speak_response": true
  }'
```

#### Python Example

```python
import requests
import json

url = "http://localhost:9093/voice/process/stream"
payload = {
    "text": "Write a haiku about programming",
    "speak_response": False
}

response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line:
        line = line.decode('utf-8')
        if line.startswith('data: '):
            data = json.loads(line[6:])
            print(f"Event: {data.get('type')}")
            if data.get('chunk'):
                print(f"Content: {data['chunk']}", end='', flush=True)
```

#### SSE Events

```json
// User message received
{"type": "user_message", "message": {...}}

// Agent routing decision
{"type": "routing", "agent_type": "creative", "reason": "creative task"}

// Response chunks
{"type": "chunk", "chunk": "Code flows like", "done": false}

// TTS synthesis
{"type": "tts", "status": "synthesizing", "audio_file": null}

// Complete
{"type": "complete", "response": "full response text", "audio_file": "/path/file.wav"}
```

---

## Endpoint 6: Real-Time Streaming TTS

### POST `/voice/process/streaming`

Ultra-low latency streaming TTS (<500ms to first audio).

#### Request

```bash
curl -N -X POST http://localhost:9093/voice/process/streaming \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What is the capital of France?",
    "conversation_id": null,
    "auto_play": false
  }'
```

#### Python Example

```python
import requests
import json

url = "http://localhost:9093/voice/process/streaming"
payload = {
    "text": "Explain machine learning",
    "auto_play": False  # Don't play on server
}

response = requests.post(url, json=payload, stream=True)

for line in response.iter_lines():
    if line and line.startswith(b'data: '):
        data = json.loads(line[6:])
        event_type = data.get('event')

        if event_type == 'token':
            print(data['token'], end='', flush=True)
        elif event_type == 'first_token':
            print(f"\nFirst token in {data['time_ms']}ms")
        elif event_type == 'routing':
            print(f"\nRouted to: {data['agent']}")
        elif event_type == 'tts_connected':
            print(f"\nTTS connected: {data['connected']}")
        elif event_type == 'complete':
            print(f"\n\nAudio: {data.get('audio_file')}")
```

#### SSE Events

```json
// First LLM token
{"event": "first_token", "time_ms": 342, "token": "Machine"}

// Streaming tokens
{"event": "token", "token": " learning"}

// Routing decision
{"event": "routing", "agent": "teacher", "reason": "educational query"}

// TTS WebSocket status
{"event": "tts_connected", "connected": true}

// Complete with metrics
{"event": "complete", "response": "full text", "audio_file": "/path/file.wav", "metrics": {...}}
```

---

## Complete Workflow: Audio File → Transcription → Response → Speech

### Full Python Example

```python
import requests
import time

ORCHESTRATOR_URL = "http://localhost:9093"

def transcribe_and_respond(audio_file_path: str):
    """Complete workflow: transcribe audio, get AI response, generate speech."""

    # Step 1: Transcribe audio
    print("🎤 Transcribing audio...")
    transcribe_url = f"{ORCHESTRATOR_URL}/voice/transcribe"
    with open(audio_file_path, "rb") as f:
        transcribe_response = requests.post(
            transcribe_url,
            files={"file": f}
        )

    if not transcribe_response.json().get("success"):
        print("❌ Transcription failed")
        return

    transcribed_text = transcribe_response.json()["text"]
    print(f"✅ Transcribed: {transcribed_text}")

    # Step 2: Get AI response with TTS
    print("\n🤖 Generating response...")
    process_url = f"{ORCHESTRATOR_URL}/voice/process"
    process_response = requests.post(
        process_url,
        json={
            "text": transcribed_text,
            "speak_response": True
        }
    )

    result = process_response.json()
    print(f"✅ Response: {result['response']}")

    # Step 3: Download audio
    if result.get("audio_file"):
        print(f"\n🔊 Audio generated: {result['audio_file']}")
        # Audio is saved on server, can be downloaded if needed
        print(f"💡 Conversation ID: {result['conversation_id']}")
        print("Use this ID for follow-up messages")

    return result

# Example usage
if __name__ == "__main__":
    result = transcribe_and_respond("my_recording.wav")
```

---

## Conversation Management

### List Conversations

```bash
curl http://localhost:9093/voice/conversations
```

```python
response = requests.get(f"{ORCHESTRATOR_URL}/voice/conversations")
conversations = response.json()["conversations"]

for conv in conversations:
    print(f"ID: {conv['id']}")
    print(f"Title: {conv['title']}")
    print(f"Messages: {conv['message_count']}")
```

### Get Conversation History

```bash
curl http://localhost:9093/voice/conversations/{conversation_id}
```

```python
conv_id = "abc123"
response = requests.get(f"{ORCHESTRATOR_URL}/voice/conversations/{conv_id}")
conversation = response.json()

for msg in conversation["messages"]:
    print(f"{msg['role']}: {msg['content']}")
```

### Follow-up in Conversation

```python
conversation_id = "abc123"  # From previous response
payload = {
    "text": "Can you elaborate on that?",
    "conversation_id": conversation_id,
    "speak_response": True
}

response = requests.post(f"{ORCHESTRATOR_URL}/voice/process", json=payload)
```

---

## Environment Variables

### Configuration

```bash
# Orchestrator
export HYPR_VOICE_MODEL="claude-sonnet-4-5"
export HYPR_VOICE_MAX_TURNS="20"
export HYPR_VOICE_WORKING_DIR="/tmp/hypr-voice"

# TTS Configuration
export HYPR_VOICE_TTS_PROVIDER="deepgram"
export HYPR_VOICE_TTS_VOICE="aura-luna-en"
export HYPR_VOICE_TTS_RANDOM="0"  # Set to 1 for random voice

# Streaming TTS (experimental, may cause stutter)
export HYPR_VOICE_TTS_STREAMING="0"  # Set to 1 to enable
export HYPR_VOICE_TTS_MIN_CHARS="140"
export HYPR_VOICE_TTS_MAX_LATENCY="0.8"

# Whisper URL
export WHISPER_URL="http://localhost:9099"
```

---

## Health Check

```bash
curl http://localhost:9093/health
```

```json
{
  "status": "healthy",
  "timestamp": "2025-01-15T10:30:00.000Z",
  "version": "0.2.0"
}
```

---

## Troubleshooting

### Issue: "Voice orchestrator not initialized"

**Solution**: Check that the orchestrator server is running:

```bash
# Check server status
curl http://localhost:9093/health

# Restart if needed
./scripts/start_everything.sh restart
```

### Issue: "Cannot connect to Whisper"

**Solution**: Ensure Whisper server is running:

```bash
# Check Whisper server
curl http://localhost:9099/

# Start Whisper server
cd src/Hypr-Whisper && ./scripts/start_hybrid_server.sh start
```

### Issue: TTS not working

**Solution**: Verify Deepgram API key:

```bash
# Check if API key is set
echo $DEEPGRAM_API_KEY

# Set API key
export DEEPGRAM_API_KEY="your-key-here"
```

### Issue: Audio file format not supported

**Solution**: Convert to WAV format:

```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

---

## Performance Tips

1. **Use WAV format** for fastest transcription (16kHz sample rate)
2. **Keep audio files under 30 seconds** for best latency
3. **Reuse conversation IDs** for context-aware follow-ups
4. **Use streaming endpoints** for real-time feedback
5. **Disable TTS** (`speak_response: false`) if only text is needed

---

## Advanced: Direct Whisper Server API

You can also use the Hypr-Whisper server directly:

### Create Session

```bash
curl -X POST http://localhost:9099/sessions
```

### Transcribe in Session

```bash
curl -X POST http://localhost:9099/sessions/{session_id}/transcribe \
  -F "file=@audio.wav"
```

### Get Context

```bash
curl http://localhost:9099/api/context
```

---

## Full CLI Script Example

```bash
#!/bin/bash
# transcribe_and_respond.sh

AUDIO_FILE="$1"
SERVER="http://localhost:9093"

if [ -z "$AUDIO_FILE" ]; then
    echo "Usage: $0 <audio_file.wav>"
    exit 1
fi

echo "🎤 Transcribing..."
TRANSCRIPT=$(curl -s -X POST "$SERVER/voice/transcribe" \
  -F "file=@$AUDIO_FILE" | jq -r '.text')

echo "✅ Transcribed: $TRANSCRIPT"

echo ""
echo "🤖 Getting response..."
RESPONSE=$(curl -s -X POST "$SERVER/voice/process" \
  -H "Content-Type: application/json" \
  -d "{\"text\": \"$TRANSCRIPT\", \"speak_response\": true}")

echo "✅ Response: $(echo $RESPONSE | jq -r '.response')"
AUDIO_FILE=$(echo $RESPONSE | jq -r '.audio_file')
echo "🔊 Audio: $AUDIO_FILE"
```

Usage: `./transcribe_and_respond.sh recording.wav`
