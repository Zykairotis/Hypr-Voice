# Hypr-Voice REST API Documentation

## Overview

Hypr-Voice provides a comprehensive REST API for voice orchestration, agent management, and audio processing. The API is built on FastAPI and provides endpoints for transcription, text-to-speech, agent interactions, and more.

**Base URL:** `http://localhost:9091` (default)

**API Version:** 0.2.0

---

## Table of Contents

- [Health & Status](#health--status)
- [Agent Management](#agent-management)
- [Voice Processing](#voice-processing)
- [Transcription](#transcription)
- [Enhanced Context Processing](#enhanced-context-processing)
- [Conversation Management](#conversation-management)

---

## Health & Status

### GET /health

Health check endpoint to verify the service is running.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T12:00:00.000000",
  "version": "0.2.0"
}
```

**Status Codes:**
- `200 OK`: Service is healthy

---

## Agent Management

### GET /agents

List all active agent sessions.

**Authentication:** Not required

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "uuid",
      "name": "agent-name",
      "status": "running",
      "working_directory": "/path/to/dir",
      "parent_id": null,
      "subagents": []
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `503 Service Unavailable`: Orchestrator not initialized

---

### GET /agent-types

Get available agent types with descriptions and capabilities.

**Authentication:** Not required

**Response:**
```json
{
  "types": [
    {
      "name": "code-worker",
      "description": "Handles programming tasks, debugging, and code analysis",
      "tools": ["Read", "Write", "Bash", "Grep"],
      "model": "claude-sonnet-4-5"
    },
    {
      "name": "research-worker",
      "description": "Information lookup and documentation",
      "tools": ["Search", "Read"],
      "model": "claude-sonnet-4-5"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success

---

### POST /query

Process a query through the orchestrator with streaming response.

**Authentication:** Not required

**Request Body:**
```json
{
  "query": "Your question here",
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "results": [
    {
      "type": "text",
      "content": "Response content"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Query processed successfully
- `503 Service Unavailable`: Orchestrator not initialized

---

### POST /spawn

Spawn a new agent of a specific type.

**Authentication:** Not required

**Request Body:**
```json
{
  "agent_type": "code-worker",
  "task": "Create a Python function",
  "parent_session": "optional-parent-id"
}
```

**Response:**
```json
{
  "session_id": "uuid",
  "status": "spawned"
}
```

**Status Codes:**
- `200 OK`: Agent spawned successfully
- `400 Bad Request`: Invalid agent type or parameters
- `503 Service Unavailable`: Orchestrator not initialized

---

### DELETE /agents/{session_id}

Destroy an agent session.

**Authentication:** Not required

**Path Parameters:**
- `session_id` (string): The ID of the agent session to destroy

**Response:**
```json
{
  "status": "destroyed",
  "session_id": "uuid"
}
```

**Status Codes:**
- `200 OK`: Agent destroyed successfully
- `404 Not Found`: Session not found
- `503 Service Unavailable`: Orchestrator not initialized

---

## Voice Processing

### POST /voice/process

Process text through the voice pipeline with routing, LLM response, and TTS.

**Authentication:** Not required

**Request Body:**
```json
{
  "text": "Your input text",
  "conversation_id": "optional-conversation-id",
  "speak_response": true
}
```

**Fields:**
- `text` (string, required): Input text to process
- `conversation_id` (string, optional): Conversation ID for context
- `speak_response` (boolean, optional): Whether to speak the response (default: true)

**Response:**
```json
{
  "success": true,
  "response_text": "AI response here",
  "routing_decision": {
    "agent_type": "general-conversation",
    "confidence": 0.95,
    "reasoning": "Query is conversational"
  },
  "audio_file": "/path/to/response.wav",
  "conversation_id": "uuid",
  "metrics": {
    "total_time": 2.5,
    "llm_time": 1.8,
    "tts_time": 0.7
  }
}
```

**Status Codes:**
- `200 OK`: Voice processed successfully
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### POST /voice/process/stream

Stream process text through the voice pipeline with Server-Sent Events.

**Authentication:** Not required

**Request Body:**
```json
{
  "text": "Your input text",
  "conversation_id": "optional-conversation-id",
  "speak_response": true
}
```

**Response:** Server-Sent Events stream

**Event Types:**
```json
// Routing event
data: {"type": "routing", "agent_type": "general-conversation", "confidence": 0.95}

// LLM token event
data: {"type": "token", "content": "Hello"}

// First token metric
data: {"type": "first_token", "time_ms": 180}

// TTS connection
data: {"type": "tts_connected", "status": "connected"}

// Complete event
data: {"type": "complete", "response_text": "Full response", "audio_file": "/path/to/audio.wav"}
```

**Status Codes:**
- `200 OK`: Streaming started
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### POST /voice/process/streaming

Process text with real-time streaming TTS via WebSocket for ultra-low latency.

**Authentication:** Not required

**Request Body:**
```json
{
  "text": "Your input text",
  "conversation_id": "optional-conversation-id",
  "auto_play": false
}
```

**Fields:**
- `text` (string, required): Input text to process
- `conversation_id` (string, optional): Conversation ID for context
- `auto_play` (boolean, optional): Server-side audio playback (default: false)

**Response:** Server-Sent Events stream

**Event Types:**
```json
// LLM token arrival
data: {"type": "token", "content": "Hello"}

// Time to first token
data: {"type": "first_token", "time_ms": 150}

// Routing decision
data: {"type": "routing", "agent_type": "code-worker", "confidence": 0.92}

// TTS WebSocket status
data: {"type": "tts_connected", "status": "connected"}

// Complete
data: {"type": "complete", "response_text": "...", "audio_file": "...", "metrics": {...}}
```

**Performance:**
- First audio in <500ms
- Token-by-token streaming
- Parallel LLM + TTS processing

**Status Codes:**
- `200 OK`: Streaming started
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### POST /voice/transcribe

Transcribe an audio file using Whisper.

**Authentication:** Not required

**Request:** Multipart form data
- `file`: Audio file (WAV, MP3, etc.)

**Response:**
```json
{
  "text": "Transcribed text here",
  "success": true
}
```

**Status Codes:**
- `200 OK**: Transcription successful
- `500 Internal Server Error**: Transcription failed
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### POST /voice/speak

Convert text to speech using Deepgram TTS.

**Authentication:** Not required

**Request Body:**
```json
{
  "text": "Text to speak",
  "voice": "aura-luna-en"
}
```

**Fields:**
- `text` (string, required): Text to synthesize
- `voice` (string, optional): Voice name (default: system default)

**Response:** Audio file (audio/wav)

**Headers:**
```
Content-Type: audio/wav
Content-Disposition: inline; filename="response.wav"
Accept-Ranges: bytes
```

**Status Codes:**
- `200 OK`: Audio generated successfully
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### POST /voice/process/enhanced

Process text with enhanced context awareness using Claude Agent SDK.

**Authentication:** Not required

**Request Body:**
```json
{
  "text": "user query",
  "context": {
    "window": {
      "class": "kitty",
      "title": "Terminal - bash",
      "workspace": {"id": 1, "name": "dev"}
    },
    "clipboard": "clipboard content",
    "timestamp": "2026-01-26T12:00:00Z"
  },
  "conversation_id": "optional-for-follow-ups",
  "speak_response": true
}
```

**Fields:**
- `text` (string, required): User query
- `context` (object, required): Enhanced context
  - `window` (object): Active window information
  - `clipboard` (string): Clipboard content
  - `timestamp` (string): ISO timestamp
- `conversation_id` (string, optional): Conversation ID for continuity
- `speak_response` (boolean, optional): Enable TTS (default: true)

**Response:**
```json
{
  "success": true,
  "response_text": "AI response with full context awareness",
  "conversation_id": "uuid",
  "audio_file": "/path/to/audio.wav",
  "context_used": true,
  "agent_type": "enhanced-context",
  "tools_used": ["hyprland_monitor", "clipboard"],
  "timestamp": "2026-01-26T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Enhanced processing successful
- `503 Service Unavailable`: Enhanced Context Agent not available

---

## Conversation Management

### GET /voice/conversations

List all conversations.

**Authentication:** Not required

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "uuid",
      "created_at": "2026-01-26T12:00:00Z",
      "message_count": 5
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### GET /voice/conversations/{conversation_id}

Get a specific conversation with all messages.

**Authentication:** Not required

**Path Parameters:**
- `conversation_id` (string): The conversation ID

**Response:**
```json
{
  "conversation_id": "uuid",
  "created_at": "2026-01-26T12:00:00Z",
  "messages": [
    {
      "role": "user",
      "content": "User message",
      "timestamp": "2026-01-26T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": "2026-01-26T12:00:01Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Success
- `404 Not Found`: Conversation not found
- `503 Service Unavailable`: Voice orchestrator not initialized

---

### POST /voice/conversations

Create a new conversation.

**Authentication:** Not required

**Response:**
```json
{
  "conversation_id": "uuid",
  "created_at": "2026-01-26T12:00:00Z",
  "message_count": 0
}
```

**Status Codes:**
- `200 OK`: Conversation created
- `503 Service Unavailable`: Voice orchestrator not initialized

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request parameters"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error occurred"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Service not initialized or unavailable"
}
```

---

## Rate Limiting

Currently, there are no enforced rate limits on the API endpoints. However, clients should implement reasonable rate limiting to prevent abuse.

---

## CORS

The API has CORS enabled with:
- `allow_origins`: `*` (all origins)
- `allow_credentials`: `true`
- `allow_methods`: `*` (all methods)
- `allow_headers`: `*` (all headers)

---

## SDK/Client Libraries

### Python Client

```python
from hypr_voice.client import HyprVoiceClient

client = HyprVoiceClient(base_url="http://localhost:9091")

# Process voice
result = await client.voice_process(
    text="Hello, how are you?",
    speak_response=True
)

# List agents
agents = await client.list_agents()
```

### JavaScript Client (Fetch)

```javascript
const baseUrl = 'http://localhost:9091';

// Process voice
const response = await fetch(`${baseUrl}/voice/process`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Hello, how are you?',
    speak_response: true
  })
});

const result = await response.json();
```

---

## Interactive Documentation

When the server is running, visit:
- **Swagger UI**: `http://localhost:9091/docs`
- **ReDoc**: `http://localhost:9091/redoc`

These provide interactive API documentation with the ability to test endpoints directly from the browser.
