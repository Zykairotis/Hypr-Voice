# API Bridge Specifications

## Overview

The API Bridge serves as the communication layer between the web UI and the existing Hypr-Voice Unix socket interface. It provides HTTP REST endpoints and WebSocket connections for real-time communication.

## Architecture

### Unix Socket Bridge Design

The API Bridge communicates with the Hypr-Voice core system through Unix domain sockets. This approach maintains compatibility with the existing architecture while providing modern web-based access.

```python
# Unix Socket Client Implementation
class UnixSocketClient:
    def __init__(self, socket_path: str):
        self.socket_path = socket_path
        self.timeout = 30

    async def send_command(self, command: dict) -> dict:
        """Send command to Hypr-Voice via Unix socket"""
        try:
            reader, writer = await asyncio.open_unix_connection(
                self.socket_path
            )

            # Send JSON command
            message = json.dumps(command) + '\n'
            writer.write(message.encode())
            await writer.drain()

            # Read response
            response = await reader.readline()
            writer.close()
            await writer.wait_closed()

            return json.loads(response.decode())

        except Exception as e:
            logger.error(f"Unix socket error: {e}")
            raise
```

### FastAPI Application Structure

```python
# main.py
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.socket_client = UnixSocketClient("/tmp/hypr-voice.sock")
    await app.state.socket_client.connect()
    yield
    # Shutdown
    await app.state.socket_client.disconnect()

app = FastAPI(
    title="Hypr-Voice API Bridge",
    description="Web API for Hypr-Voice voice transcription system",
    version="1.0.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API End Specifications

### 1. Authentication Endpoints

#### POST /api/auth/login
Authenticate user and return JWT tokens.

**Request Body:**
```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "id": 1,
    "username": "admin",
    "role": "admin",
    "permissions": ["read", "write", "admin"]
  }
}
```

#### POST /api/auth/refresh
Refresh access token using refresh token.

**Request Headers:**
```
Authorization: Bearer <refresh_token>
```

**Response:**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### DELETE /api/auth/logout
Invalidate current session.

**Response:**
```json
{
  "message": "Successfully logged out"
}
```

### 2. Server Control Endpoints

#### GET /api/server/status
Get current server status and metrics.

**Response:**
```json
{
  "status": "running",
  "uptime": 3600,
  "cpu_usage": 25.5,
  "memory_usage": 512.3,
  "active_sessions": 3,
  "total_sessions": 127,
  "whisper_model": "medium",
  "audio_device": "USB Audio Device",
  "current_mode": "enhanced",
  "last_activity": "2024-01-15T10:30:45Z",
  "errors": []
}
```

#### POST /api/server/start
Start the Hypr-Voice server.

**Request Body:**
```json
{
  "config_overrides": {
    "audio.device.primary.name": "USB Audio Device",
    "whisper.model": "medium"
  }
}
```

**Response:**
```json
{
  "message": "Server start initiated",
  "task_id": "task_123456",
  "estimated_time": 15
}
```

#### POST /api/server/stop
Stop the Hypr-Voice server.

**Response:**
```json
{
  "message": "Server stop initiated",
  "task_id": "task_123457"
}
```

#### POST /api/server/restart
Restart the Hypr-Voice server.

**Response:**
```json
{
  "message": "Server restart initiated",
  "task_id": "task_123458",
  "estimated_time": 20
}
```

#### GET /api/server/metrics
Get detailed performance metrics.

**Response:**
```json
{
  "system": {
    "cpu_usage": 25.5,
    "memory_usage": 512.3,
    "disk_usage": 75.2,
    "network_io": {
      "bytes_sent": 1048576,
      "bytes_received": 2097152
    }
  },
  "transcription": {
    "total_transcriptions": 1250,
    "average_latency": 2.5,
    "success_rate": 98.5,
    "error_rate": 1.5
  },
  "audio": {
    "sample_rate": 48000,
    "channels": 1,
    "buffer_size": 2048,
    "input_level": -12.5
  },
  "sessions": {
    "active_count": 3,
    "total_duration": 7200,
    "average_session_length": 45.2
  }
}
```

### 3. Configuration Management Endpoints

#### GET /api/config/list
List all available configuration files.

**Response:**
```json
{
  "files": [
    {
      "name": "audio_config.yaml",
      "path": "/hypr-voice/config/audio_config.yaml",
      "description": "Audio device and processing settings",
      "last_modified": "2024-01-15T09:15:30Z",
      "size": 3650
    },
    {
      "name": "app_profiles.yaml",
      "path": "/hypr-voice/config/app_profiles.yaml",
      "description": "Application-specific profiles",
      "last_modified": "2024-01-14T16:45:20Z",
      "size": 8750
    }
  ]
}
```

#### GET /api/config/{filename}
Get specific configuration file content.

**Response:**
```json
{
  "filename": "audio_config.yaml",
  "content": "# Audio Configuration\naudio:\n  quality:\n    sample_rate: 48000\n    channels: 1\n  devices:\n    primary:\n      name: \"0\"\n      description: \"USB Audio Device\"",
  "schema": {
    "type": "object",
    "properties": {
      "audio": {
        "type": "object",
        "properties": {
          "quality": {
            "type": "object",
            "properties": {
              "sample_rate": {"type": "integer", "minimum": 8000, "maximum": 96000}
            }
          }
        }
      }
    }
  },
  "metadata": {
    "last_modified": "2024-01-15T09:15:30Z",
    "checksum": "sha256:abc123...",
    "version": "1.2.0"
  }
}
```

#### PUT /api/config/{filename}
Update configuration file.

**Request Body:**
```json
{
  "content": "# Updated Audio Configuration\naudio:\n  quality:\n    sample_rate: 44100\n    channels: 1",
  "backup": true,
  "validate": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully",
  "backup_created": "/hypr-voice/config/backups/audio_config.yaml.20240115",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": ["Sample rate change may affect audio quality"]
  },
  "requires_restart": false
}
```

#### POST /api/config/validate
Validate configuration without saving.

**Request Body:**
```json
{
  "filename": "audio_config.yaml",
  "content": "# Audio Configuration\naudio:\n  quality:\n    sample_rate: 48000"
}
```

**Response:**
```json
{
  "valid": true,
  "errors": [],
  "warnings": [],
  "suggestions": [
    "Consider setting explicit device name for better reliability"
  ]
}
```

### 4. Session Management Endpoints

#### GET /api/sessions
List transcription sessions with pagination.

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `status`: Filter by status (active, completed, error)
- `date_from`: Filter by start date
- `date_to`: Filter by end date

**Response:**
```json
{
  "sessions": [
    {
      "id": "session_123456",
      "status": "completed",
      "start_time": "2024-01-15T10:15:30Z",
      "end_time": "2024-01-15T10:17:45Z",
      "duration": 135,
      "mode": "enhanced",
      "application": "kitty",
      "transcript": "This is the transcribed text...",
      "confidence": 0.95,
      "enhanced_text": "This is the AI-enhanced text...",
      "metadata": {
        "whisper_model": "medium",
        "llm_provider": "xai",
        "audio_device": "USB Audio Device",
        "sample_rate": 48000
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 127,
    "pages": 7
  }
}
```

#### GET /api/sessions/{session_id}
Get detailed session information.

**Response:**
```json
{
  "id": "session_123456",
  "status": "completed",
  "start_time": "2024-01-15T10:15:30Z",
  "end_time": "2024-01-15T10:17:45Z",
  "duration": 135,
  "mode": "enhanced",
  "application": {
    "name": "kitty",
    "class": "terminal",
    "window_title": "zsh"
  },
  "audio": {
    "device": "USB Audio Device",
    "sample_rate": 48000,
    "channels": 1,
    "format": "wav",
    "file_path": "/recordings/session_123456.wav"
  },
  "transcription": {
    "raw_text": "This is the raw transcription",
    "confidence": 0.95,
    "language": "en",
    "processing_time": 2.3
  },
  "enhancement": {
    "provider": "xai",
    "model": "grok-3-mini",
    "enhanced_text": "This is the enhanced text",
    "processing_time": 1.8
  },
  "events": [
    {
      "timestamp": "2024-01-15T10:15:30Z",
      "type": "recording_started",
      "details": {"device": "USB Audio Device"}
    },
    {
      "timestamp": "2024-01-15T10:17:45Z",
      "type": "transcription_completed",
      "details": {"confidence": 0.95}
    }
  ]
}
```

#### DELETE /api/sessions/{session_id}
Delete a session and associated files.

**Response:**
```json
{
  "success": true,
  "message": "Session deleted successfully",
  "files_deleted": [
    "/recordings/session_123456.wav",
    "/transcripts/session_123456.json"
  ]
}
```

#### GET /api/sessions/stats
Get session statistics and analytics.

**Response:**
```json
{
  "total_sessions": 127,
  "total_duration": 7200,
  "average_session_length": 45.2,
  "success_rate": 98.5,
  "modes": {
    "raw": 65,
    "enhanced": 62
  },
  "applications": [
    {"name": "kitty", "count": 45, "percentage": 35.4},
    {"name": "chrome", "count": 38, "percentage": 29.9},
    {"name": "vscode", "count": 28, "percentage": 22.0}
  ],
  "daily_usage": [
    {"date": "2024-01-15", "sessions": 12, "duration": 540},
    {"date": "2024-01-14", "sessions": 8, "duration": 360}
  ],
  "performance": {
    "average_latency": 2.5,
    "average_confidence": 0.92,
    "error_rate": 1.5
  }
}
```

### 5. Log Management Endpoints

#### GET /api/logs
Get log entries with filtering.

**Query Parameters:**
- `level`: Filter by log level (debug, info, warn, error)
- `component`: Filter by component (whisper, audio, context, etc.)
- `limit`: Number of entries (default: 100)
- `offset`: Pagination offset
- `search`: Search term

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T10:30:45Z",
      "level": "info",
      "component": "whisper",
      "message": "Transcription completed successfully",
      "metadata": {
        "session_id": "session_123456",
        "duration": 2.3,
        "confidence": 0.95
      }
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total": 1520
  },
  "filters": {
    "level": "info",
    "component": "whisper",
    "search": null
  }
}
```

#### GET /api/logs/stream
Server-Sent Events for real-time log streaming.

**Response (SSE):**
```
data: {"timestamp": "2024-01-15T10:30:45Z", "level": "info", "component": "whisper", "message": "Transcription completed"}

data: {"timestamp": "2024-01-15T10:31:02Z", "level": "warn", "component": "audio", "message": "Audio device disconnected"}

```

#### GET /api/logs/search
Search logs with advanced filtering.

**Request Body:**
```json
{
  "query": "transcription error",
  "level": ["error", "warn"],
  "components": ["whisper", "audio"],
  "date_from": "2024-01-14T00:00:00Z",
  "date_to": "2024-01-15T23:59:59Z",
  "limit": 50
}
```

**Response:**
```json
{
  "results": [
    {
      "timestamp": "2024-01-15T09:45:12Z",
      "level": "error",
      "component": "whisper",
      "message": "Transcription failed: audio timeout",
      "metadata": {
        "session_id": "session_123450",
        "error_code": "TIMEOUT"
      }
    }
  ],
  "total": 3,
  "search_time": 0.045
}
```

## WebSocket API Specifications

### Connection

**Endpoint:** `ws://localhost:8001/ws`

**Authentication:** JWT token in query parameter or WebSocket subprotocol

```javascript
const ws = new WebSocket(
  `ws://localhost:8001/ws?token=${accessToken}`
);
```

### Message Format

All WebSocket messages follow this structure:

```typescript
interface WebSocketMessage {
  type: string;
  timestamp: string;
  data: any;
  id?: string;
}
```

### Event Types

#### server_status_change
Server status updates.

```typescript
{
  type: "server_status_change",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    status: "running" | "stopped" | "error" | "starting",
    uptime: 3600,
    cpu_usage: 25.5,
    memory_usage: 512.3,
    active_sessions: 3
  }
}
```

#### voice_activity
Real-time voice activity monitoring.

```typescript
{
  type: "voice_activity",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    is_recording: boolean,
    audio_level: number,  // -60 to 0 dB
    duration: number,     // seconds
    mode: "raw" | "enhanced",
    peak_level: number,
    rms_level: number
  }
}
```

#### transcription_progress
Real-time transcription progress.

```typescript
{
  type: "transcription_progress",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    session_id: "session_123456",
    status: "recording" | "processing" | "completed" | "error",
    progress: number,     // 0-100
    partial_text: "Partial transcription...",
    confidence: number,
    estimated_time_remaining: number
  }
}
```

#### log_entry
Real-time log streaming.

```typescript
{
  type: "log_entry",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    level: "info" | "warn" | "error" | "debug",
    component: string,
    message: string,
    metadata?: object
  }
}
```

#### config_change
Configuration update notifications.

```typescript
{
  type: "config_change",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    filename: "audio_config.yaml",
    changes: [
      {
        path: "audio.quality.sample_rate",
        old_value: 48000,
        new_value: 44100
      }
    ],
    requires_restart: false,
    applied_by: "admin"
  }
}
```

#### session_created
New session started.

```typescript
{
  type: "session_created",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    session_id: "session_123456",
    application: "kitty",
    mode: "enhanced",
    audio_device: "USB Audio Device"
  }
}
```

#### session_completed
Session finished with results.

```typescript
{
  type: "session_completed",
  timestamp: "2024-01-15T10:32:15Z",
  data: {
    session_id: "session_123456",
    duration: 90,
    transcript: "Final transcribed text...",
    confidence: 0.95,
    enhanced_text: "AI-enhanced text...",
    processing_time: 3.2
  }
}
```

#### error_notification
System error notifications.

```typescript
{
  type: "error_notification",
  timestamp: "2024-01-15T10:30:45Z",
  data: {
    error_code: "AUDIO_DEVICE_ERROR",
    message: "USB Audio Device disconnected",
    severity: "critical" | "error" | "warning",
    component: "audio",
    recoverable: true,
    suggested_action: "Check audio device connections"
  }
}
```

### Client-Side WebSocket Implementation

```typescript
class HyprVoiceWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private subscriptions: Set<string> = new Set();

  constructor(private token: string) {
    this.connect();
  }

  private connect() {
    const url = `ws://localhost:8001/ws?token=${this.token}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.resubscribe();
    };

    this.ws.onmessage = (event) => {
      const message: WebSocketMessage = JSON.parse(event.data);
      this.handleMessage(message);
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.scheduleReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  private handleMessage(message: WebSocketMessage) {
    // Route messages to appropriate handlers
    switch (message.type) {
      case 'server_status_change':
        this.onServerStatusChange(message.data);
        break;
      case 'voice_activity':
        this.onVoiceActivity(message.data);
        break;
      case 'transcription_progress':
        this.onTranscriptionProgress(message.data);
        break;
      // ... other message types
    }
  }

  private scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
    }
  }

  subscribe(eventType: string) {
    this.subscriptions.add(eventType);
    this.send({ type: 'subscribe', events: Array.from(this.subscriptions) });
  }

  unsubscribe(eventType: string) {
    this.subscriptions.delete(eventType);
    this.send({ type: 'unsubscribe', events: [eventType] });
  }

  private send(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }
}
```

## Error Handling

### HTTP Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid configuration data",
    "details": {
      "field": "audio.quality.sample_rate",
      "value": "invalid_value",
      "expected": "integer between 8000 and 96000"
    },
    "timestamp": "2024-01-15T10:30:45Z",
    "request_id": "req_123456"
  }
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| VALIDATION_ERROR | Request validation failed | 400 |
| UNAUTHORIZED | Authentication required | 401 |
| FORBIDDEN | Insufficient permissions | 403 |
| NOT_FOUND | Resource not found | 404 |
| CONFLICT | Resource conflict | 409 |
| INTERNAL_ERROR | Server internal error | 500 |
| SERVICE_UNAVAILABLE | Service temporarily unavailable | 503 |
| SOCKET_ERROR | Unix socket communication error | 502 |
| CONFIG_ERROR | Configuration error | 422 |

## Rate Limiting

- **Authentication endpoints**: 5 requests per minute per IP
- **Configuration endpoints**: 10 requests per minute per user
- **Server control**: 20 requests per minute per user
- **Session endpoints**: 100 requests per minute per user
- **Log endpoints**: 200 requests per minute per user

## Security Implementation

### JWT Token Structure

```json
{
  "sub": "user_123",
  "username": "admin",
  "role": "admin",
  "permissions": ["read", "write", "admin"],
  "iat": 1642248645,
  "exp": 1642252245,
  "jti": "token_123456"
}
```

### API Key Authentication (Alternative)

For system-to-system communication:

```
Authorization: ApiKey abc123def456...
```

### Request Validation

All requests are validated using Pydantic models:

```python
from pydantic import BaseModel, validator
from typing import Optional

class ServerStartRequest(BaseModel):
    config_overrides: Optional[Dict[str, Any]] = None

    @validator('config_overrides')
    def validate_config_overrides(cls, v):
        if v is None:
            return v
        # Validate override paths and values
        for path, value in v.items():
            if not path.startswith(('audio.', 'whisper.', 'llm.')):
                raise ValueError(f"Invalid config path: {path}")
        return v
```

This API bridge specification provides a comprehensive interface for the Hypr-Voice web UI while maintaining clean integration with the existing Unix socket-based architecture.