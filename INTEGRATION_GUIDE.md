# Context Manager Integration Guide

## Overview

This guide explains how to integrate the Context Manager Controls with the Hypr-Whisper transcription system, including backend setup, WebSocket configuration, and real-time data flow.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI (Next.js)                       │
│  ┌─────────────────┐  ┌──────────────────┐  ┌────────────┐ │
│  │  Context        │  │  WebSocket       │  │  Context   │ │
│  │  Dashboard      │  │  Client          │  │  Widgets   │ │
│  └─────────────────┘  └──────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                       │                       │
         │ HTTP/WebSocket         │ Real-time            │
         │                       │ Updates              │
         ▼                       ▼                       │
┌─────────────────────────────────────────────────────────────┐
│              Backend Services (Python)                     │
│  ┌──────────────────┐  ┌─────────────────┐  ┌────────────┐ │
│  │  Context         │  │  Context        │  │  Context   │ │
│  │  Manager         │  │  WebSocket      │  │  Processor │ │
│  │  (context.py)    │  │  Server         │  │  (script)  │ │
│  └──────────────────┘  └─────────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌────────────────┐  ┌──────────────┐  ┌──────────────────────┐
│  Shell         │  │  Clipboard   │  │  Application         │
│  History       │  │  (cliphist)  │  │  Detector            │
│  (.zsh/.bash)  │  │              │  │  (hyprctl)           │
└────────────────┘  └──────────────┘  └──────────────────────┘
```

## Backend Setup

### 1. Python Context Manager

The `context_manager.py` already exists and provides:
- Shell history extraction
- Clipboard access
- Window information from Hyprland
- Vocabulary extraction

```python
from context_manager import get_context_manager

context_manager = get_context_manager()
context_data = context_manager.get_comprehensive_context()
```

### 2. WebSocket Server Setup

Start the WebSocket server for real-time updates:

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
python context_websocket_server.py
```

Or run as a background service:

```bash
nohup python context_websocket_server.py > websocket.log 2>&1 &
```

### 3. Background Processor

Run the context processor for continuous monitoring:

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
python scripts/context_processor.py
```

Or run as a systemd service:

```bash
sudo tee /etc/systemd/system/context-processor.service > /dev/null <<EOF
[Unit]
Description=Context Processor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
ExecStart=/usr/bin/python scripts/context_processor.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable context-processor
sudo systemctl start context-processor
```

## Frontend Configuration

### Environment Variables

Create `.env.local` in the web-ui directory:

```env
# Context Manager API
NEXT_PUBLIC_CONTEXT_API_URL=http://localhost:9090
NEXT_PUBLIC_CONTEXT_WS_URL=ws://localhost:9091

# Context Configuration
CONTEXT_UPDATE_INTERVAL=5000
CONTEXT_MAX_COMMANDS=100
CONTEXT_MAX_CLIPBOARD=50
CONTEXT_RETENTION_HOURS=24

# Privacy Settings
CONTEXT_ENABLE_PRIVACY_MODE=true
CONTEXT_MASK_SENSITIVE_DATA=true
```

### WebSocket Client Setup

The `useContextData` hook automatically connects to the WebSocket:

```typescript
const { data, loading, error } = useContextData();

// Real-time updates are automatically received
useEffect(() => {
  if (data) {
    // Handle context updates
    console.log('Context updated:', data);
  }
}, [data]);
```

## Integration with Hybrid Server

### Add Context Endpoints

Modify `hybrid_server.py` to include context endpoints:

```python
@app.get("/context/data")
async def get_context_data():
    """Get comprehensive context data."""
    global context_manager
    if context_manager:
        return context_manager.get_comprehensive_context()
    return {"error": "Context manager not available"}

@app.websocket("/ws/context")
async def context_websocket(websocket: WebSocket):
    """WebSocket for context updates."""
    await websocket.accept()
    # Implementation in context_websocket_server.py
```

### Vocabulary Integration

Context data automatically updates vocabulary:

```python
# In hybrid_server.py
if application_detector and vocabulary_manager:
    window_info = application_detector.get_active_window()
    if window_info:
        app_class = window_info.get('class', '')
        app_title = window_info.get('title', '')
        vocabulary_manager.update_vocabulary(app_class, app_title)
```

## Real-Time Data Flow

### 1. Shell History Updates

```
Shell Command → .bash_history/.zsh_history
             ↓
         context_manager.get_shell_history()
             ↓
         WebSocket Broadcast
             ↓
         Frontend Update
```

### 2. Clipboard Updates

```
Clipboard Change → cliphist/wl-paste
                ↓
          context_manager.get_clipboard_history()
                ↓
          WebSocket Broadcast
                ↓
          Frontend Update
```

### 3. Window Changes

```
Window Switch → hyprctl activewindow
             ↓
       context_manager.extract_context_from_hyprland()
             ↓
       vocabulary_manager.update_vocabulary()
             ↓
       WebSocket Broadcast
             ↓
       Frontend Update
```

## API Endpoints

### GET /api/context/data

Fetch context data with optional filters:

```typescript
const response = await fetch('/api/context/data?timeRange=24h&categories=git,node');
const data = await response.json();
```

**Response:**
```json
{
  "shell": {
    "commands": [...],
    "statistics": {...}
  },
  "clipboard": {
    "entries": [...],
    "statistics": {...}
  },
  "applications": {
    "activeWindow": {...},
    "usageStats": [...],
    "history": [...]
  }
}
```

### GET /api/context/analytics

Fetch analytics data:

```typescript
const response = await fetch('/api/context/analytics');
const analytics = await response.json();
```

### POST /api/context/clear

Clear context data:

```typescript
const response = await fetch('/api/context/clear', {
  method: 'POST',
  body: JSON.stringify({ type: 'all' })
});
```

### WebSocket /ws/context

Real-time context updates:

```typescript
const ws = new WebSocket('ws://localhost:9090/ws/context');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'context_update') {
    // Handle context update
    setContext(data.data);
  }
};
```

## Configuration Options

### Context Strength Thresholds

Configure when context is considered "strong":

```typescript
// In useContextData.ts
const CONTEXT_THRESHOLDS = {
  weak: 30,
  moderate: 60,
  strong: 80,
  excellent: 90
};
```

### Update Intervals

Adjust update frequencies:

```typescript
// In useContextData.ts
const UPDATE_INTERVALS = {
  realtime: 2000,    // 2 seconds
  normal: 5000,      // 5 seconds
  background: 30000  // 30 seconds
};
```

### Data Retention

Configure how long to keep context data:

```python
# In context_processor.py
RETENTION_HOURS = 24
CLEANUP_INTERVAL = 3600  # 1 hour
```

## Privacy & Security

### Sensitive Data Detection

Automatic detection of:
- Passwords
- API keys
- Tokens
- Credit cards
- Emails

```typescript
const isLikelySensitive = (content: string): boolean => {
  const patterns = [
    /password/i,
    /api[_-]?key/i,
    /\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}/
  ];
  return patterns.some(pattern => pattern.test(content));
};
```

### Privacy Controls

Users can toggle privacy mode:

```typescript
const [showSensitive, setShowSensitive] = useState(false);

// Mask sensitive data
const maskedContent = isSensitive && !showSensitive
  ? '•'.repeat(content.length)
  : content;
```

## Monitoring & Debugging

### Check Backend Status

```bash
# Check if context processor is running
ps aux | grep context_processor

# Check WebSocket server
netstat -tuln | grep 9091

# View logs
tail -f /tmp/context-processor.log
```

### Debug Mode

Enable debug logging:

```typescript
// In browser console
localStorage.setItem('context-debug', 'true');
```

### Health Checks

```bash
# Test API endpoint
curl http://localhost:9090/context/data

# Test WebSocket
wscat -c ws://localhost:9090/ws/context
```

## Performance Optimization

### 1. Data Compression

Enable gzip compression for API responses:

```typescript
// next.config.ts
module.exports = {
  compress: true,
  experimental: {
    gzipSize: true,
  },
};
```

### 2. Client-Side Caching

Cache context data in memory:

```typescript
const CACHE_TTL = 5000; // 5 seconds
const cache = new Map();

const getCachedData = (key: string) => {
  const cached = cache.get(key);
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  return null;
};
```

### 3. Debounced Updates

Debounce frequent updates:

```typescript
const debouncedUpdate = useMemo(
  () => debounce((data) => {
    setContext(data);
  }, 1000),
  []
);
```

## Troubleshooting

### Common Issues

**Issue**: WebSocket connection fails
- Check if WebSocket server is running: `netstat -tuln | grep 9091`
- Verify firewall settings
- Check browser console for errors

**Issue**: No context data
- Ensure context_manager.py is imported
- Check if shell history file exists
- Verify cliphist is installed (Wayland)

**Issue**: Privacy mode not working
- Clear browser cache
- Check localStorage settings

### Debug Commands

```bash
# Check context manager
python -c "from context_manager import get_context_manager; print('OK')"

# Test shell history
python -c "from context_manager import get_context_manager; cm = get_context_manager(); print(cm.get_shell_history(5))"

# Test clipboard
python -c "from context_manager import get_context_manager; cm = get_context_manager(); print(cm.get_clipboard_history(5))"
```

## Security Considerations

1. **Local Processing**: All context data is processed locally
2. **No Cloud Upload**: Data never leaves the machine
3. **Privacy Masking**: Sensitive data is automatically masked
4. **Access Control**: WebSocket only accepts local connections
5. **Data Retention**: Automatic cleanup of old data

## Future Enhancements

1. **ML Integration**: Use ML to predict context needs
2. **Multi-User Support**: Support for team context sharing
3. **Plugin System**: Allow custom context sources
4. **Advanced Analytics**: Deeper pattern analysis
5. **Context Templates**: Predefined context configurations

## Support

For issues and questions:
- Check logs: `/tmp/context-processor.log`
- Review WebSocket logs
- Open GitHub issue
- Contact: [support email]
