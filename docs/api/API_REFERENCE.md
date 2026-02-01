# Hypr-Voice API Reference

Complete API documentation for the Hypr-Voice Orchestrator Server.

**Base URL:** `http://localhost:9091`

**API Version:** `0.2.0`

---

## Table of Contents

- [Health & Status](#health--status)
- [Agent Management](#agent-management)
- [Voice Processing](#voice-processing)
- [Enhanced Context Processing](#enhanced-context-processing)
- [Conversation Management](#conversation-management)
- [WebSocket Interface](#websocket-interface)
- [Data Models](#data-models)
- [Error Responses](#error-responses)

---

## Health & Status

### GET /health

Health check endpoint to verify the server is running.

**Request:**
```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-01-26T10:30:00.000000",
  "version": "0.2.0"
}
```

---

## Agent Management

### GET /agents

List all active agent sessions.

**Request:**
```http
GET /agents
```

**Response (200 OK):**
```json
{
  "agents": [
    {
      "session_id": "abc123",
      "agent_type": "code",
      "task": "Fix the bug in authentication",
      "created_at": "2025-01-26T10:25:00.000000",
      "status": "active"
    }
  ]
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Orchestrator not initialized"
}
```

---

### GET /agent-types

Get available agent types and their configurations.

**Request:**
```http
GET /agent-types
```

**Response (200 OK):**
```json
{
  "types": [
    {
      "name": "code",
      "description": "Specialized agent for code-related tasks including debugging, implementation, and code review",
      "tools": ["bash", "str_replace_editor", "run_tests"],
      "model": "claude-sonnet-4-5"
    },
    {
      "name": "research",
      "description": "Agent for research and information gathering tasks",
      "tools": ["bash", "search", "read_file"],
      "model": "claude-sonnet-4-5"
    },
    {
      "name": "shell",
      "description": "Agent for shell command execution and system operations",
      "tools": ["bash", "command_execution"],
      "model": "claude-sonnet-4-5"
    },
    {
      "name": "voice",
      "description": "Agent specialized for voice interaction and audio processing",
      "tools": ["voice_command", "tts", "stt"],
      "model": "claude-sonnet-4-5"
    }
  ]
}
```

---

### POST /query

Process a query through the orchestrator.

**Request Body:**
```json
{
  "query": "Explain how to implement a binary search tree",
  "session_id": "optional-session-id"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| query | string | Yes | The query text to process |
| session_id | string | No | Optional session ID for context continuity |

**Response (200 OK):**
```json
{
  "results": [
    {
      "type": "routing",
      "agent_type": "research",
      "confidence": 0.95
    },
    {
      "type": "content",
      "content": "A binary search tree is a data structure..."
    },
    {
      "type": "complete",
      "session_id": "abc123"
    }
  ]
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Orchestrator not initialized"
}
```

---

### POST /spawn

Spawn a new agent with a specific task.

**Request Body:**
```json
{
  "agent_type": "code",
  "task": "Implement a REST API endpoint for user authentication",
  "parent_session": "optional-parent-session-id"
}
```

**Parameters:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| agent_type | string | Yes | Type of agent to spawn (code, research, shell, voice) |
| task | string | Yes | The task description for the agent |
| parent_session | string | No | Optional parent session ID for nested agents |

**Response (200 OK):**
```json
{
  "session_id": "xyz789",
  "status": "spawned"
}
```

**Error Response (400 Bad Request):**
```json
{
  "detail": "Invalid agent type: unknown_type"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Orchestrator not initialized"
}
```

---

### DELETE /agents/{session_id}

Destroy an agent session.

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| session_id | string | The session ID to destroy |

**Request:**
```http
DELETE /agents/abc123
```

**Response (200 OK):**
```json
{
  "status": "destroyed",
  "session_id": "abc123"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Session not found"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Orchestrator not initialized"
}
```

---

## Voice Processing

### POST /voice/process

Process text through the voice pipeline with TTS response.

**Request Body:**
```json
{
  "text": "What is the weather like today?",
  "conversation_id": "optional-conversation-id",
  "speak_response": true
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | Yes | - | The text to process |
| conversation_id | string | No | null | Optional conversation ID for context |
| speak_response | boolean | No | true | Whether to speak the response via TTS |

**Response (200 OK):**
```json
{
  "success": true,
  "response_text": "I don't have access to real-time weather data...",
  "conversation_id": "conv123",
  "audio_file": "/path/to/audio.wav",
  "agent_type": "voice",
  "duration_ms": 2450,
  "timestamp": "2025-01-26T10:30:00.000000"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

### POST /voice/process/stream

Stream process text through the voice pipeline using Server-Sent Events (SSE).

**Request Body:**
```json
{
  "text": "Tell me a short story",
  "conversation_id": "optional-conversation-id",
  "speak_response": true
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | Yes | - | The text to process |
| conversation_id | string | No | null | Optional conversation ID for context |
| speak_response | boolean | No | true | Whether to speak the response via TTS |

**Response (200 OK - text/event-stream):**
```
data: {"type":"user_message","message":{"id":"msg1","role":"user","content":"Tell me a short story","timestamp":"2025-01-26T10:30:00.000000"},"conversation_id":"conv123"}

data: {"type":"routing","agent_type":"voice","confidence":0.92}

data: {"type":"content","content":"Once upon a time"}

data: {"type":"content","content":" in a land far away"}

data: {"type":"complete","conversation_id":"conv123","audio_file":"/path/to/audio.wav"}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

### POST /voice/process/streaming

Process text with real-time streaming TTS via WebSocket.

This endpoint provides near-instant voice response (<500ms to first audio) by beginning audio playback as soon as the first LLM tokens arrive.

**Request Body:**
```json
{
  "text": "What is quantum computing?",
  "conversation_id": "optional-conversation-id",
  "auto_play": false
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | Yes | - | The text to process |
| conversation_id | string | No | null | Optional conversation ID for context |
| auto_play | boolean | No | false | Server-side audio playback (usually false for API) |

**Response (200 OK - text/event-stream):**
```
data: {"type":"routing","agent_type":"voice","confidence":0.95}

data: {"type":"token","content":"Quantum"}

data: {"type":"token","content":" computing"}

data: {"type":"token","content":" is"}

data: {"type":"first_token","time_ms":450}

data: {"type":"tts_connected","status":"connected"}

data: {"type":"complete","response_text":"Quantum computing is a type of computation...","conversation_id":"conv123","audio_file":"/path/to/audio.wav","metrics":{"total_tokens":150,"time_to_first_token_ms":450,"time_to_complete_ms":3200}}
```

**SSE Event Types:**
| Event Type | Description |
|------------|-------------|
| token | Individual LLM token as it arrives |
| first_token | Time to first token metric (in milliseconds) |
| routing | Agent routing decision |
| tts_connected | TTS WebSocket connection status |
| complete | Final response with metrics |

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

### POST /voice/transcribe

Transcribe an audio file using Whisper.

**Request:**
```http
POST /voice/transcribe
Content-Type: multipart/form-data
```

**Form Data:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| file | file | Yes | Audio file to transcribe (WAV format) |

**Response (200 OK):**
```json
{
  "text": "Hello, how are you today?",
  "success": true
}
```

**Error Response (500 Internal Server Error):**
```json
{
  "detail": "Transcription failed: Whisper server not responding"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

### POST /voice/speak

Convert text to speech using Deepgram TTS.

**Request Body:**
```json
{
  "text": "This is a test of the text to speech system",
  "voice": "aura-luna-en"
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | Yes | - | The text to convert to speech |
| voice | string | No | null | Optional voice selection (overrides default) |

**Response (200 OK - audio/wav):**
Returns audio file directly with headers:
```
Content-Type: audio/wav
Content-Disposition: inline; filename="response.wav"
Accept-Ranges: bytes
```

**Error Response (503 Service Unavailable):**
```json
{
  "success": false,
  "error": "TTS not available",
  "text": "This is a test of the text to speech system"
}
```

---

## Enhanced Context Processing

### POST /voice/process/enhanced

Process text with enhanced context awareness using Claude Agent SDK and Hyprland integration.

This endpoint provides:
- Full context awareness (active window, clipboard, workspace)
- Claude SDK with custom Hyprland tools
- Session persistence for conversation continuity
- TTS spoken responses
- Intelligent, context-specific assistance

**Request Body:**
```json
{
  "text": "What application am I currently using?",
  "context": {
    "window": {
      "class": "kitty",
      "title": "~/Projects/hypr-voice",
      "workspace": {
        "id": 1,
        "name": "1"
      }
    },
    "clipboard": "some clipboard content",
    "timestamp": "2025-01-26T10:30:00.000000"
  },
  "conversation_id": "optional-conversation-id",
  "speak_response": true
}
```

**Parameters:**
| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | string | Yes | - | The user query text |
| context | object | Yes | - | Context information from Hyprland |
| context.window | object | Yes | - | Active window information |
| context.window.class | string | Yes | - | Window class name |
| context.window.title | string | Yes | - | Window title |
| context.window.workspace | object | Yes | - | Workspace information |
| context.clipboard | string | Yes | - | Clipboard content |
| context.timestamp | string | Yes | - | ISO timestamp of context capture |
| conversation_id | string | No | null | Optional conversation ID for follow-ups |
| speak_response | boolean | No | true | Whether to speak the response via TTS |

**Response (200 OK):**
```json
{
  "success": true,
  "response_text": "You are currently using kitty terminal in the ~/Projects/hypr-voice directory on workspace 1.",
  "conversation_id": "conv456",
  "audio_file": "/path/to/audio.wav",
  "context_used": true,
  "agent_type": "enhanced-context",
  "tools_used": ["get_active_window", "get_workspace_info"],
  "timestamp": "2025-01-26T10:30:00.000000"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Enhanced Context Agent not available. Check server logs for initialization errors."
}
```

---

## Conversation Management

### GET /voice/conversations

List all conversations.

**Request:**
```http
GET /voice/conversations
```

**Response (200 OK):**
```json
{
  "conversations": [
    {
      "id": "conv123",
      "created_at": "2025-01-26T10:00:00.000000",
      "title": "What is the weather like today?",
      "message_count": 2,
      "messages": [
        {
          "id": "msg1",
          "role": "user",
          "content": "What is the weather like today?",
          "timestamp": "2025-01-26T10:00:00.000000",
          "agent_type": null,
          "audio_file": null,
          "duration_ms": null
        },
        {
          "id": "msg2",
          "role": "assistant",
          "content": "I don't have access to real-time weather data...",
          "timestamp": "2025-01-26T10:00:01.000000",
          "agent_type": "voice",
          "audio_file": "/path/to/audio.wav",
          "duration_ms": 2450
        }
      ]
    }
  ]
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

### GET /voice/conversations/{conversation_id}

Get a specific conversation by ID.

**URL Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| conversation_id | string | The conversation ID to retrieve |

**Request:**
```http
GET /voice/conversations/conv123
```

**Response (200 OK):**
```json
{
  "id": "conv123",
  "created_at": "2025-01-26T10:00:00.000000",
  "title": "What is the weather like today?",
  "message_count": 2,
  "messages": [
    {
      "id": "msg1",
      "role": "user",
      "content": "What is the weather like today?",
      "timestamp": "2025-01-26T10:00:00.000000",
      "agent_type": null,
      "audio_file": null,
      "duration_ms": null
    },
    {
      "id": "msg2",
      "role": "assistant",
      "content": "I don't have access to real-time weather data...",
      "timestamp": "2025-01-26T10:00:01.000000",
      "agent_type": "voice",
      "audio_file": "/path/to/audio.wav",
      "duration_ms": 2450
    }
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Conversation not found"
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

### POST /voice/conversations

Create a new conversation.

**Request:**
```http
POST /voice/conversations
```

**Response (200 OK):**
```json
{
  "id": "conv789",
  "created_at": "2025-01-26T10:30:00.000000",
  "title": null,
  "message_count": 0,
  "messages": []
}
```

**Error Response (503 Service Unavailable):**
```json
{
  "detail": "Voice orchestrator not initialized"
}
```

---

## WebSocket Interface

### WebSocket /ws

WebSocket endpoint for real-time bidirectional communication.

**Connection URL:**
```
ws://localhost:9091/ws
```

**Client Messages:**

#### Subscribe to Events
```json
{
  "type": "subscribe",
  "topic": "all",
  "client_id": "client-123"
}
```

#### Send Query
```json
{
  "type": "query",
  "query": "Explain quantum computing",
  "session_id": "optional-session-id"
}
```

#### Ping/Pong
```json
{
  "type": "ping"
}
```

#### List Agents
```json
{
  "type": "list_agents"
}
```

**Server Messages:**

#### Subscription Confirmation
```json
{
  "type": "subscribed",
  "topic": "all",
  "client_id": "client-123"
}
```

#### Pong Response
```json
{
  "type": "pong"
}
```

#### Query Response Chunk
```json
{
  "type": "chunk",
  "content": "Quantum computing is...",
  "agent_type": "research"
}
```

#### Query Complete
```json
{
  "type": "complete"
}
```

#### Agents List
```json
{
  "type": "agents_list",
  "agents": [
    {
      "session_id": "abc123",
      "agent_type": "code",
      "task": "Fix the bug",
      "created_at": "2025-01-26T10:25:00.000000",
      "status": "active"
    }
  ]
}
```

---

## Data Models

### QueryRequest
```typescript
{
  query: string;              // The query text to process
  session_id?: string;        // Optional session ID for context
}
```

### SpawnRequest
```typescript
{
  agent_type: string;         // Type of agent to spawn
  task: string;               // Task description
  parent_session?: string;    // Optional parent session ID
}
```

### VoiceProcessRequest
```typescript
{
  text: string;               // The text to process
  conversation_id?: string;   // Optional conversation ID
  speak_response?: boolean;   // Whether to speak response (default: true)
}
```

### StreamingTTSRequest
```typescript
{
  text: string;               // The text to process
  conversation_id?: string;   // Optional conversation ID
  auto_play?: boolean;        // Server-side audio playback (default: false)
}
```

### EnhancedProcessRequest
```typescript
{
  text: string;               // The user query text
  context: {                  // Context information
    window: {                 // Active window info
      class: string;          // Window class
      title: string;          // Window title
      workspace: {            // Workspace info
        id: number;           // Workspace ID
        name: string;         // Workspace name
      };
    };
    clipboard: string;        // Clipboard content
    timestamp: string;        // ISO timestamp
  };
  conversation_id?: string;   // Optional conversation ID
  speak_response?: boolean;   // Whether to speak response (default: true)
}
```

### TTSSpeakRequest
```typescript
{
  text: string;               // The text to speak
  voice?: string;             // Optional voice selection
}
```

### ConversationMessage
```typescript
{
  id: string;                 // Message ID
  role: "user" | "assistant"; // Message role
  content: string;            // Message content
  timestamp: string;          // ISO timestamp
  agent_type?: string;        // Agent type (for assistant messages)
  audio_file?: string;        // Path to audio file (if TTS was used)
  duration_ms?: number;       // Audio duration in milliseconds
}
```

### Conversation
```typescript
{
  id: string;                 // Conversation ID
  created_at: string;         // ISO timestamp
  title?: string;             // Auto-generated from first message
  message_count: number;      // Number of messages
  messages: ConversationMessage[];  // Array of messages
}
```

---

## Error Responses

All endpoints may return error responses in the following format:

### 400 Bad Request
```json
{
  "detail": "Invalid agent type: unknown_type"
}
```

### 404 Not Found
```json
{
  "detail": "Session not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Transcription failed: Whisper server not responding"
}
```

### 503 Service Unavailable
```json
{
  "detail": "Orchestrator not initialized"
}
```

---

## Environment Variables

The server behavior can be configured via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| HYPR_VOICE_MODEL | claude-sonnet-4-5 | Default model for agents |
| HYPR_VOICE_MAX_TURNS | 20 | Maximum conversation turns |
| HYPR_VOICE_WORKING_DIR | - | Working directory for agents |
| HYPR_VOICE_TTS_PROVIDER | deepgram | TTS provider (deepgram, elevenlabs, kokoro) |
| HYPR_VOICE_TTS_VOICE | aura-luna-en | Default TTS voice |
| WHISPER_URL | http://localhost:9099 | Whisper server URL |
| DEEPGRAM_API_KEY | - | Deepgram API key for TTS |
| HYPR_VOICE_TTS_RANDOM | 0 | Use random TTS voice (0 or 1) |
| HYPR_VOICE_TTS_REST_STREAMING | 0 | Enable REST streaming TTS (0 or 1) |
| ENHANCED_AGENT_MODEL | claude-sonnet-4-5 | Model for enhanced context agent |
| ENHANCED_AGENT_MAX_TURNS | 5 | Max turns for enhanced agent |
| CLAUDE_SDK_WORKING_DIR | cwd | Working directory for Claude SDK |

---

## Streaming Implementation Notes

### SSE (Server-Sent Events) Format

The server uses SSE for streaming responses. Events are formatted as:
```
data: {JSON_DATA}

```

Each event is separated by two newlines.

### Handling SSE Streams

**Example (JavaScript):**
```javascript
const response = await fetch('http://localhost:9091/voice/process/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'Tell me a story',
    speak_response: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split('\n\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      console.log('Event:', data);
    }
  }
}
```

---

## Rate Limiting

Currently, there are no explicit rate limits configured. Clients should implement reasonable throttling to avoid overwhelming the server.

---

## CORS Configuration

The server is configured to allow CORS from all origins (`allow_origins=["*"]`). For production deployments, this should be restricted to specific origins.

---

## Support

For issues, questions, or contributions, please refer to the main project repository.
