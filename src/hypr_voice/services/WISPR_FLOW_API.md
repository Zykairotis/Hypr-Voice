# Wispr Flow API Server

FastAPI service for Wispr Flow transcription with environment variable configuration.

## Features

- **REST API endpoints** for audio transcription
- **WebSocket support** for real-time transcription
- **File upload** support for audio files
- **Base64 audio** support
- **Full context support** - language, app context, custom dictionary, user names
- **Token validation** - JWT expiration checking
- **Health checks** - monitor token and service status

## Quick Start

### 1. Configure Environment Variables

Add to your `.env` file (already configured):

```bash
# Wispr Flow API Configuration
WISPR_FLOW_JWT_TOKEN=eyJhbGci... (your JWT token)
WISPR_FLOW_BASETEN_API_KEY=aEXAlxkF.cIvt1vq... (your API key)
WISPR_FLOW_USER_UUID=ef8df64e-1f1c-4d11-bed1-96129b0dde07 (your user UUID)
WISPR_FLOW_BASETEN_URL=https://chain-o232k03l.api.baseten.co/environments/production/run_remote
WISPR_FLOW_PORT=9095
WISPR_FLOW_TIMEOUT=30
```

### 2. Start the Server

```bash
# Start the server
./scripts/start_wispr_flow.sh start

# Check status
./scripts/start_wispr_flow.sh status

# View logs
./scripts/start_wispr_flow.sh logs

# Stop the server
./scripts/start_wispr_flow.sh stop
```

### 3. Access the API

- **API Root**: http://localhost:9095/
- **Swagger UI**: http://localhost:9095/docs
- **Health Check**: http://localhost:9095/health
- **Token Info**: http://localhost:9095/token

## API Endpoints

### POST /transcribe

Transcribe audio from base64 string.

**Request:**
```json
{
  "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAA...",
  "language": ["en"],
  "app_type": "ai",
  "app_name": "ChatGPT",
  "dictionary_words": ["Claude", "Anthropic"],
  "user_first_name": "Parth",
  "user_last_name": "Sheth",
  "before_text": "I'm working on ",
  "after_text": " project",
  "content_text": "Project context here..."
}
```

**Response:**
```json
{
  "success": true,
  "status": "formatted",
  "text": "Transcribed text here...",
  "detected_language": "en",
  "total_time": 2.5,
  "generated_tokens": 150,
  "metadata": {
    "session_id": "...",
    "timestamp": "2026-01-24T12:00:00"
  }
}
```

### POST /transcribe/file

Transcribe audio from file upload.

**Parameters:**
- `file`: Audio file (form-data, WAV recommended)
- `language`: Language codes (comma-separated)
- `app_type`: Application type (email, ai, code, messaging, other)
- `app_name`: Application name
- `dictionary`: Comma-separated custom words
- `user_first_name`: User's first name
- `user_last_name`: User's last name
- `before_text`: Text before cursor
- `after_text`: Text after cursor
- `selected_text`: Selected text
- `content_text`: Page content for context

**Example (curl):**
```bash
curl -X POST "http://localhost:9095/transcribe/file" \
  -F "file=@audio.wav" \
  -F "language=en" \
  -F "app_type=ai" \
  -F "dictionary=Claude,Anthropic"
```

### GET /token

Get JWT token information.

**Response:**
```json
{
  "email": "partsheth326@gmail.com",
  "expires_at": "2026-01-31T13:14:44",
  "is_valid": true,
  "days_remaining": 37
}
```

### WebSocket /ws/transcribe

Real-time transcription via WebSocket.

**Connect:**
```javascript
const ws = new WebSocket('ws://localhost:9095/ws/transcribe');

// Send transcription request
ws.send(JSON.stringify({
  type: "transcribe",
  audio_base64: "...",
  language: ["en"],
  app_type: "ai",
  dictionary_words: ["word1", "word2"]
}));

// Receive result
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "result") {
    console.log("Transcription:", data.text);
  }
};
```

## Parameters

### Language

List of ISO 639-1 language codes:
- Single language: Forces that language
- Multiple languages: Auto-detects between them

Supported: `en`, `hi`, `es`, `fr`, `de`, `it`, `pt`, `zh`, `ja`, `ko`, `ru`, `ar`, and 90+ more.

### App Types

- `email`: Email clients (Gmail, Outlook)
- `ai`: AI chat (ChatGPT, Claude, Perplexity)
- `code`: Code editors (VS Code, IntelliJ)
- `messaging`: Chat apps (Slack, Discord)
- `other`: Everything else

### Dictionary Words

Custom words/names for accurate transcription:
```python
dictionary_words = ["Kubernetes", "PostgreSQL", "DevOps", "microservices"]
```

### Text Context

- `before_text`: Text before cursor position (affects spacing/punctuation)
- `after_text`: Text after cursor position
- `selected_text`: Highlighted text (for replacements)
- `content_text`: Page/app content for context

## Example Usage

### Python Client

```python
import requests
import base64

# Read audio file
with open("audio.wav", "rb") as f:
    audio_base64 = base64.b64encode(f.read()).decode()

# Send request
response = requests.post(
    "http://localhost:9095/transcribe",
    json={
        "audio_base64": audio_base64,
        "language": ["en"],
        "app_type": "ai",
        "app_name": "ChatGPT",
        "dictionary_words": ["Claude", "Anthropic"],
        "user_first_name": "Parth",
        "user_last_name": "Sheth"
    }
)

result = response.json()
print(result["text"])
```

### JavaScript/TypeScript Client

```typescript
const audioBase64 = await fileToBase64(audioFile);

const response = await fetch('http://localhost:9095/transcribe', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    audio_base64: audioBase64,
    language: ['en'],
    app_type: 'ai',
    dictionary_words: ['Claude', 'Anthropic']
  })
});

const result = await response.json();
console.log(result.text);
```

### WebSocket Client (Python)

```python
import asyncio
import websockets
import json
import base64

async def transcribe_audio(audio_path: str):
    # Read and encode audio
    with open(audio_path, "rb") as f:
        audio_base64 = base64.b64encode(f.read()).decode()

    # Connect to WebSocket
    async with websockets.connect('ws://localhost:9095/ws/transcribe') as ws:
        # Send request
        await ws.send(json.dumps({
            "type": "transcribe",
            "audio_base64": audio_base64,
            "language": ["en"],
            "app_type": "ai"
        }))

        # Receive result
        response = await ws.recv()
        result = json.loads(response)

        if result["type"] == "result":
            print(f"Transcription: {result['text']}")

asyncio.run(transcribe_audio("audio.wav"))
```

## Direct Python Script Usage

You can also run the server directly:

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice
python3 src/hypr_voice/services/wispr_flow_server.py
```

This will start the server on port 9095 (or the port specified in `.env`).

## JWT Token Management

The server automatically checks JWT token expiration:

1. Check token status:
   ```bash
   curl http://localhost:9095/token
   ```

2. If token expires, capture a fresh token from Wispr Flow desktop app using Fiddler
3. Update `.env` with new `WISPR_FLOW_JWT_TOKEN`
4. Restart the server

## Troubleshooting

### Server fails to start

```bash
# Check if port is already in use
lsof -i :9095

# Check logs
tail -f logs/wispr_flow.log
```

### Token validation errors

```bash
# Check token status
curl http://localhost:9095/token

# Update .env with fresh token if expired
```

### Audio format issues

Wispr Flow prefers:
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Format: WAV

Convert with ffmpeg if needed:
```bash
ffmpeg -i input.mp3 -ar 16000 -ac 1 output.wav
```

## Files

- **Server**: `src/hypr_voice/services/wispr_flow_server.py`
- **Startup Script**: `scripts/start_wispr_flow.sh`
- **Environment**: `.env` (WISPR_FLOW_* variables)
- **Logs**: `logs/wispr_flow.log`
- **PID File**: `var/wispr_flow.pid`
