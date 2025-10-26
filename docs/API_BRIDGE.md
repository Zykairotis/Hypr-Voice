# Hypr-Voice Bridge API

A FastAPI bridge service that converts HTTP requests to Unix socket commands for Hypr-Voice control. This service provides a RESTful API and WebSocket interface for controlling Hypr-Voice remotely.

## Features

- **Recording Control**: Start, stop, and force-stop recording with raw and enhanced modes
- **Server Management**: Start, stop, restart, and monitor the Hypr-Voice server
- **Configuration Management**: View and update configuration with validation
- **Real-time Log Streaming**: WebSocket endpoint for live log monitoring
- **Session Management**: Track active and recent voice processing sessions
- **System Metrics**: Monitor performance and usage statistics
- **CORS Support**: Cross-origin resource sharing for web UI integration
- **Comprehensive Error Handling**: Proper HTTP status codes and error messages

## Installation

1. **Install Dependencies**:
   ```bash
   cd /home/mewtwo/Zykairotis/Hypr-Voice-main/src/api
   pip install -r requirements.txt
   ```

2. **Verify Installation**:
   ```bash
   python run_bridge.py --check
   ```

3. **Start the Service**:
   ```bash
   python run_bridge.py
   ```

The API will be available at `http://localhost:8000`

## Configuration

The bridge service can be configured by editing `config.yaml`:

- **Server Settings**: Host, port, and logging configuration
- **Unix Socket**: Path to Hypr-Voice socket file
- **CORS**: Cross-origin settings for web integration
- **Security**: Rate limiting and authentication options

## API Endpoints

### Recording Control

#### Start Recording (Raw Mode)
```http
POST /api/recording/start
Content-Type: application/json

{
  "mode": "raw",
  "context": {"app": "vscode"}
}
```

#### Start Enhanced Recording
```http
POST /api/recording/enhanced
Content-Type: application/json

{
  "context": {"app": "vscode"}
}
```

#### Stop Recording
```http
POST /api/recording/stop
```

#### Force Stop Recording
```http
POST /api/recording/force-stop
```

#### Get Recording Status
```http
GET /api/recording/status
```

Response:
```json
{
  "status": "recording",
  "is_recording": true,
  "mode": "raw",
  "duration_seconds": 5.2,
  "audio_chunks": 42,
  "total_frames": 86016,
  "device_name": "GA102",
  "app_context": "vscode"
}
```

### Server Management

#### Start Server
```http
POST /api/server/start
```

#### Stop Server
```http
POST /api/server/stop
```

#### Restart Server
```http
POST /api/server/restart
```

#### Get Server Status
```http
GET /api/server/status
```

Response:
```json
{
  "status": "running",
  "uptime_seconds": 3600.5,
  "version": "1.0.0",
  "memory_usage_mb": 45.2,
  "active_connections": 3
}
```

### Configuration Management

#### Get Configuration Section
```http
GET /api/config/audio
```

#### Update Configuration Section
```http
PUT /api/config/audio
Content-Type: application/json

{
  "section": "audio",
  "config_data": {
    "quality": {
      "sample_rate": 48000,
      "channels": 1
    }
  },
  "validate": true
}
```

### Log Streaming

#### WebSocket Log Stream
```javascript
const ws = new WebSocket('ws://localhost:8000/api/logs/stream?type=all&level=info');

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Log entry:', data.log_entry);
};
```

#### Get Recent Logs
```http
GET /api/logs/agent/recent?limit=50
```

### Session Management

#### Get Sessions
```http
GET /api/sessions
```

Response:
```json
[
  {
    "session_id": "session_123",
    "start_time": "2024-01-15T10:30:00Z",
    "status": "COMPLETED",
    "duration_seconds": 8.5,
    "primary_agent": "PRIMARY_CLAUDE_SDK",
    "input_text": "help me debug this code",
    "response_preview": "I'll help you debug your Python code...",
    "tokens_used": 289,
    "cost_usd": 0.0145,
    "tools_used": ["file_read", "bash_execute"]
  }
]
```

### System Metrics

#### Get Metrics
```http
GET /api/metrics
```

Response:
```json
{
  "timestamp": "2024-01-15T10:35:00Z",
  "active_sessions": 1,
  "completed_sessions_today": 15,
  "total_sessions_today": 18,
  "claude_sdk_status": "AVAILABLE",
  "litellm_status": "SGLang+Ollama",
  "last_activity": "2024-01-15T10:34:45Z",
  "error_count": 0,
  "average_response_time": 3.2,
  "total_cost_today": 0.234,
  "memory_usage_mb": 45.2,
  "cpu_usage_percent": 2.1
}
```

### Health Check

#### Health Status
```http
GET /api/health
```

Response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:35:00Z",
  "services": {
    "socket_client": true,
    "log_streamer": true,
    "config_manager": true
  }
}
```

## WebSocket Events

### Log Stream Messages
```json
{
  "type": "log_stream",
  "timestamp": "2024-01-15T10:35:00Z",
  "log_entry": {
    "timestamp": "2024-01-15T10:35:00Z",
    "level": "info",
    "message": "Voice input: help me debug this code...",
    "context": {...},
    "source": "agent"
  }
}
```

### Status Update Messages
```json
{
  "type": "status_update",
  "timestamp": "2024-01-15T10:35:00Z",
  "status": "recording",
  "details": {
    "mode": "raw",
    "duration_seconds": 5.2
  }
}
```

## Error Handling

The API returns appropriate HTTP status codes and detailed error messages:

- **200 OK**: Successful request
- **400 Bad Request**: Invalid request parameters
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource state conflict (e.g., already recording)
- **500 Internal Server Error**: Server error
- **503 Service Unavailable**: Service temporarily unavailable

Error Response Format:
```json
{
  "success": false,
  "error": "Already recording",
  "error_code": "ALREADY_RECORDING",
  "details": {...},
  "timestamp": "2024-01-15T10:35:00Z"
}
```

## Development

### Running in Development Mode
```bash
python run_bridge.py --reload --log-level debug
```

### Running Tests
```bash
# Add test files and run pytest
pytest tests/
```

### Code Structure
```
src/api/
├── main.py              # FastAPI application and endpoints
├── models.py            # Pydantic models for validation
├── unix_client.py       # Unix socket communication
├── config_manager.py    # Configuration management
├── log_streamer.py      # WebSocket log streaming
├── run_bridge.py        # Startup script
├── requirements.txt     # Python dependencies
└── config.yaml          # Service configuration
```

## Integration Examples

### JavaScript/TypeScript Client
```javascript
class HyprVoiceAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async startRecording(mode = 'raw') {
    const response = await fetch(`${this.baseURL}/api/recording/start`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode })
    });
    return response.json();
  }

  async stopRecording() {
    const response = await fetch(`${this.baseURL}/api/recording/stop`, {
      method: 'POST'
    });
    return response.json();
  }

  connectLogStream(callback) {
    const ws = new WebSocket(`${this.baseURL.replace('http', 'ws')}/api/logs/stream`);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback(data.log_entry);
    };
    return ws;
  }
}
```

### Python Client
```python
import asyncio
import aiohttp

class HyprVoiceClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    async def start_recording(self, mode="raw"):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/recording/start",
                json={"mode": mode}
            ) as response:
                return await response.json()

    async def get_recording_status(self):
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/api/recording/status") as response:
                return await response.json()
```

## Security Considerations

1. **CORS Configuration**: Configure appropriate origins for production
2. **Rate Limiting**: Enable rate limiting to prevent abuse
3. **Authentication**: Add API key or token authentication for production
4. **Network Security**: Use HTTPS in production environments
5. **Input Validation**: All inputs are validated using Pydantic models

## Troubleshooting

### Common Issues

1. **Socket Connection Failed**:
   - Ensure Hypr-Voice is running
   - Check socket file permissions: `/tmp/hypr-voice.sock`
   - Verify socket path in configuration

2. **Permission Denied**:
   - Check file permissions for log directories
   - Ensure the service has write access to `/tmp/hypr-voice-logs`

3. **Port Already in Use**:
   - Change port in configuration or startup command
   - Check for other services using the same port

4. **Missing Dependencies**:
   - Install with: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

### Debug Logging

Enable debug logging for troubleshooting:
```bash
python run_bridge.py --log-level debug
```

## License

This bridge service is part of the Hypr-Voice project. Refer to the main project license for details.