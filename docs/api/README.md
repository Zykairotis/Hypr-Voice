# 🔌 API Documentation

Hypr-Voice API reference and integration guides.

*Note: API documentation is currently under development. This section will be expanded as the API evolves.*

## 🚀 Current API Status

### 📡 Web Interface API
- **Base URL**: `http://localhost:8080`
- **Authentication**: Local (no authentication required)
- **Protocol**: REST API with WebSocket support

### 🎯 Available Endpoints

#### 📊 System Status
```http
GET /api/status
```
Returns current system status, including:
- Service health
- Audio device status
- Active mode (Raw/Enhanced)
- Current application

#### 🎛️ Configuration
```http
GET /api/config
PUT /api/config
```
Retrieve or update system configuration:
- Audio settings
- Application profiles
- Mode preferences
- LLM provider settings

#### 🎤 Audio Control
```http
POST /api/audio/start
POST /api/audio/stop
GET /api/audio/levels
```
Control audio recording and monitoring:
- Start/stop recording
- Get current audio levels
- Device information

#### 📋 Clipboard Operations
```http
POST /api/clipboard/paste
GET /api/clipboard/content
```
Manage clipboard content:
- Paste transcribed text
- Get current clipboard content
- Clear clipboard

## 🔧 WebSocket Events

### 📡 Real-time Updates
Connect to `ws://localhost:8080/ws` for real-time events:

- `audio_level`: Current audio input levels
- `transcription`: Live transcription results
- `mode_change`: Raw/Enhanced mode switches
- `app_change`: Application detection updates
- `status_change`: System status updates

### 🎯 Event Examples
```json
{
  "type": "audio_level",
  "data": {
    "level": 0.75,
    "peak": 0.85,
    "timestamp": "2025-10-26T08:30:00Z"
  }
}

{
  "type": "transcription",
  "data": {
    "text": "Hello, this is a test",
    "confidence": 0.95,
    "mode": "enhanced"
  }
}
```

## 🔌 Integration Examples

### 🐍 Python Client
```python
import requests
import websocket

# Get system status
response = requests.get('http://localhost:8080/api/status')
print(response.json())

# Start WebSocket connection
def on_message(ws, message):
    data = json.loads(message)
    print(f"Event: {data['type']}")

ws = websocket.WebSocketApp(
    "ws://localhost:8080/ws",
    on_message=on_message
)
ws.run_forever()
```

### 📱 JavaScript Client
```javascript
// Fetch system status
const response = await fetch('http://localhost:8080/api/status');
const status = await response.json();

// WebSocket connection
const ws = new WebSocket('ws://localhost:8080/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.data);
};
```

## 🔮 Future API Development

### 📋 Planned Features
- **Authentication**: Secure API access with API keys
- **Rate Limiting**: Prevent abuse and ensure stability
- **Bulk Operations**: Batch processing for efficiency
- **Plugin System**: Extensible architecture
- **Remote Configuration**: Cloud-based configuration sync

### 🎯 API Versioning
- **v1.0**: Current local-only API
- **v1.1**: Authentication and rate limiting
- **v2.0**: Plugin system and remote features

## 🔧 Development Setup

### 🌐 Local Development
```bash
# Clone repository
git clone <repository>
cd hypr-voice

# Start development server
./scripts/dev_server.sh

# API will be available at:
# http://localhost:8080
# ws://localhost:8080/ws
```

### 🧪 Testing API
```bash
# Test endpoints
curl http://localhost:8080/api/status
curl -X PUT http://localhost:8080/api/config -d @config.json

# Test WebSocket
wscat -c ws://localhost:8080/ws
```

## 📚 Documentation Roadmap

### 🔮 Coming Soon
- **Complete API Reference**: Detailed endpoint documentation
- **SDK Documentation**: Language-specific client libraries
- **Integration Guides**: Step-by-step integration tutorials
- **Best Practices**: Performance and security guidelines
- **Examples**: Real-world integration scenarios

### 🎯 Current Focus
- **Web UI API**: Primary interface for configuration
- **WebSocket Events**: Real-time system monitoring
- **Configuration API**: Dynamic system configuration
- **Audio Control**: Direct audio system control

## 🔗 Related Documentation

- **[User Guides](../user/web-ui-guide.md)** - Web interface usage
- **[Technical](../technical/implementation-summary.md)** - System architecture
- **[Troubleshooting](../troubleshooting/)** - Common API issues

## 🤝 Contributing to API

### 📋 API Development
- Follow REST principles
- Use proper HTTP status codes
- Implement comprehensive error handling
- Provide clear documentation
- Add unit tests

### 🔧 Integration Examples
- Provide code examples in multiple languages
- Test integrations thoroughly
- Document edge cases and limitations
- Include troubleshooting guides

---

*This API documentation will be updated as the Hypr-Voice API evolves. Check back regularly for updates.*