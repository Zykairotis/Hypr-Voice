# Whisper Integration Guide

## Overview

Hypr-Voice integrates Whisper STT (Speech-to-Text) through two primary methods:
1. **Wispr Flow API** - Cloud-based transcription service (primary)
2. **Hypr-Whisper Integration** - Local/context-aware transcription

**Note**: The project uses Wispr Flow as the primary transcription service, with additional context-aware features through Hyprland IPC integration.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Transcription Pipeline                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  Audio       │    │  Wispr Flow  │    │  Hypr-       │   │
│  │  Input       │───▶│  API         │───▶│  Whisper     │   │
│  │  (Recording) │    │  (Primary)   │    │  (Context)   │   │
│  └──────────────┘    └──────┬───────┘    └──────┬───────┘   │
│                              │                    │          │
│                              │                    │          │
│                              ▼                    ▼          │
│                       ┌───────────────────────────┐          │
│                       │   Transcription Text      │          │
│                       │   + Application Context   │          │
│                       └───────────┬───────────────┘          │
│                                   │                          │
│                            ┌──────▼───────┐                  │
│                            │    Agent     │                  │
│                            │  Processing  │                  │
│                            └──────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Wispr Flow API (Primary transcription)
WISPR_FLOW_JWT_TOKEN=your_jwt_token_here
WISPR_FLOW_BASETEN_API_KEY=your_baseten_key_here
WISPR_FLOW_USER_UUID=your_uuid_here
WISPR_FLOW_BASETEN_URL=https://chain-o232k03l.api.baseten.co/environments/production/run_remote

# Wispr Flow Settings
WISPR_FLOW_PORT=9095
WISPR_FLOW_TIMEOUT=600
MODE=FLOW  # or LOCAL for hybrid mode

# Performance Optimization
WISPR_FLOW_CHUNK_SECONDS=30
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_OPUS_BITRATE=24k
WISPR_FLOW_AUTO_CHUNK=1
FLOW_STREAMING_MODE=1

# Optional: User Personalization
WISPR_FLOW_USER_FIRST_NAME=YourName
WISPR_FLOW_USER_LAST_NAME=YourLastName
```

### Getting Wispr Flow Credentials

1. Visit https://wispr-flow.baseten.co
2. Sign up for an account
3. Navigate to API settings
4. Copy your:
   - JWT Token
   - Baseten API Key
   - User UUID

## Usage

### Basic Transcription

```python
from hypr_voice.services.wispr_flow_direct import WisprFlowDirect

async def transcribe_audio(audio_path):
    # Initialize Wispr Flow client
    wispr = WisprFlowDirect()

    # Connect to service
    await wispr.connect()

    # Transcribe audio file
    result = await wispr.transcribe(audio_path)

    if result['success']:
        print(f"Transcription: {result['text']}")
        print(f"Duration: {result['duration']}s")
    else:
        print(f"Error: {result['error']}")

    # Close connection
    await wispr.close()
```

### Context-Aware Transcription

```python
from hypr_voice.services.tools.hypr_whisper_integration import (
    HyprWhisperIntegration,
    HyprlandMonitor
)

async def context_aware_transcription(audio_data):
    # Initialize integration
    integration = HyprWhisperIntegration(
        whisper_host="localhost",
        whisper_port=9090,
        agent_host="localhost",
        agent_port=8922
    )

    # Start monitoring Hyprland
    await integration.start()

    # Transcribe with context
    transcription = await integration.transcribe_with_context(audio_data)

    # Get current context
    context = await integration.get_current_context()
    print(f"Application: {context['window_class']}")
    print(f"Window Title: {context['window_title']}")

    # Stop integration
    await integration.stop()
```

### Streaming Transcription

```python
async def streaming_transcription():
    wispr = WisprFlowDirect()
    await wispr.connect()

    # Transcribe with streaming mode
    result = await wispr.transcribe_streaming(
        audio_source="microphone",
        chunk_duration=30,  # seconds
        use_opus=True,
        opus_bitrate=24000
    )

    async for chunk in result:
        if chunk['type'] == 'transcription':
            print(f"Live: {chunk['text']}")
        elif chunk['type'] == 'complete':
            print(f"Final: {chunk['text']}")
```

### Long Recording Optimization

```python
async def transcribe_long_recording(audio_path):
    wispr = WisprFlowDirect()

    # Configure for long recordings
    wispr.config.update({
        'chunk_seconds': 30,
        'auto_chunk': True,
        'streaming_mode': True,
        'use_opus': True,
        'opus_bitrate': 24000
    })

    await wispr.connect()

    # Automatically chunks and processes
    result = await wispr.transcribe(audio_path)

    return result
```

## Hyprland Context Integration

### Application Context Monitoring

```python
from hypr_voice.services.tools.claude_code_integration import (
    HyprlandMonitor,
    ApplicationContext
)

async def monitor_applications():
    monitor = HyprlandMonitor(update_interval=0.15)

    # Define context change callback
    async def on_context_change(context: ApplicationContext):
        print(f"App: {context.window_class}")
        print(f"Title: {context.window_title}")
        print(f"Workspace: {context.workspace_id}")

        # Get vocabulary for this app
        print(f"Vocabulary: {context.vocabulary[:10]}...")

    # Register callback
    monitor.register_callback(on_context_change)

    # Start monitoring
    await monitor.start()

    # Keep running...
    await asyncio.sleep(60)

    # Stop monitoring
    await monitor.stop()
```

### Context-Aware Routing

```python
from hypr_voice.services.tools.hypr_whisper_integration import ContextAwareRouter

async def route_by_context():
    integration = HyprWhisperIntegration()
    await integration.start()

    router = ContextAwareRouter(integration)

    # Register handlers for specific apps
    async def vscode_handler(request, context):
        # Handle VS Code-specific commands
        return {"app": "vscode", "action": "edit_code"}

    async def browser_handler(request, context):
        # Handle browser-specific commands
        return {"app": "browser", "action": "navigate"}

    router.register_route("code", vscode_handler)
    router.register_route("firefox", browser_handler)
    router.register_route("chrome", browser_handler)

    # Route request based on current app
    result = await router.route_request("Open file")
    print(f"Routed to: {result}")
```

## Wispr Flow API Details

### API Endpoints

```python
# Primary transcription endpoint
POST https://chain-o232k03l.api.baseten.co/environments/production/run_remote

Headers:
{
    "Authorization": "Bearer {WISPR_FLOW_JWT_TOKEN}",
    "Content-Type": "application/json"
}

Body:
{
    "audio": "<base64_encoded_audio>",
    "user_uuid": "{WISPR_FLOW_USER_UUID}",
    "api_key": "{WISPR_FLOW_BASETEN_API_KEY}",
    "chunk_seconds": 30,
    "use_opus": true,
    "opus_bitrate": 24000
}
```

### Response Format

```json
{
    "success": true,
    "text": "Transcribed text here...",
    "duration": 45.2,
    "language": "en",
    "confidence": 0.95,
    "segments": [
        {
            "start": 0.0,
            "end": 5.2,
            "text": "First segment",
            "confidence": 0.97
        }
    ]
}
```

## Performance Optimization

### Opus Encoding

```python
# Opus is 10x smaller and faster than WAV
config = {
    'use_opus': True,
    'opus_bitrate': 24000,  # 24k bitrate (good quality)
    'chunk_seconds': 30
}
```

### Automatic Chunking

```python
# Automatically split long recordings
config = {
    'auto_chunk': True,
    'chunk_seconds': 30,
    'chunk_overlap': 0.5,  # 50% overlap
    'auto_chunk': True
}
```

### Streaming Mode

```python
# Process while recording
config = {
    'streaming_mode': True,
    'chunk_seconds': 27,  # Slightly less than recording chunk
    'use_opus': True
}
```

## Hyprland IPC Tools

### Get Application Context

```python
from hypr_voice.services.tools.hyprland_tools import get_application_context

result = await get_application_context({})

if result['data']['detected']:
    app = result['data']['class']
    title = result['data']['title']
    workspace = result['data']['workspace']
```

### Switch to Window

```python
from hypr_voice.services.tools.hyprland_tools import switch_to_window

result = await switch_to_window({
    "window_identifier": "firefox"
})

if result['data']['success']:
    print(f"Switched to: {result['data']['switched_to']}")
```

### List Open Windows

```python
from hypr_voice.services.tools.hyprland_tools import list_open_windows

result = await list_open_windows({})

if result['data']['success']:
    for window in result['data']['windows']:
        print(f"{window['class']} - {window['title']}")
```

### Workspace Management

```python
from hypr_voice.services.tools.hyprland_tools import (
    get_workspaces,
    switch_workspace
)

# Get all workspaces
workspaces = await get_workspaces({})

# Switch to workspace 1
await switch_workspace({"workspace_id": 1})
```

## Troubleshooting

### Wispr Flow Authentication Failed

**Error**: `Authentication failed`

**Solution**:
```bash
# Check credentials
echo $WISPR_FLOW_JWT_TOKEN
echo $WISPR_FLOW_BASETEN_API_KEY
echo $WISPR_FLOW_USER_UUID

# Regenerate from Wispr Flow dashboard
# Visit: https://wispr-flow.baseten.co
```

### Connection Timeout

**Error**: `Request timeout after 600 seconds`

**Solution**:
```python
# Increase timeout
wispr.config['timeout'] = 1200  # 20 minutes

# Or enable auto-chunking
wispr.config['auto_chunk'] = True
wispr.config['chunk_seconds'] = 20  # Smaller chunks
```

### Hyprland IPC Not Working

**Error**: `Failed to get window information`

**Solution**:
```bash
# Check if Hyprland is running
echo $HYPRLAND_INSTANCE_SIGNATURE

# Test hyprctl
hyprctl activewindow -j

# Ensure HYPRLAND_INSTANCE_SIGNATURE is set
export HYPRLAND_INSTANCE_SIGNATURE=$(hyprctl instance)
```

### Opus Encoding Failed

**Error**: `Opus encoding failed`

**Solution**:
```bash
# Install Opus codec
sudo apt-get install opus-tools

# Or disable Opus
export WISPR_FLOW_USE_OPUS=0
```

## Best Practices

### 1. Use Opus Encoding

```python
# 10x faster uploads
config = {
    'use_opus': True,
    'opus_bitrate': 24000  # Balance quality and speed
}
```

### 2. Enable Streaming for Long Recordings

```python
# 85% faster for 60s+ recordings
config = {
    'streaming_mode': True,
    'chunk_seconds': 30
}
```

### 3. Use Context-Aware Transcription

```python
# Better accuracy with app context
integration = HyprWhisperIntegration()
await integration.start()
transcription = await integration.transcribe_with_context(audio)
```

### 4. Handle Errors Gracefully

```python
try:
    result = await wispr.transcribe(audio_path)
    if not result['success']:
        # Retry with different settings
        wispr.config['use_opus'] = False
        result = await wispr.transcribe(audio_path)
except Exception as e:
    logger.error(f"Transcription failed: {e}")
```

### 5. Monitor Performance

```python
import time

start = time.time()
result = await wispr.transcribe(audio_path)
duration = time.time() - start

logger.info(f"Transcription took {duration:.2f}s")
logger.info(f"Audio duration: {result['duration']:.2f}s")
logger.info(f"RTF: {duration/result['duration']:.2f}x")
```

## Integration Examples

### Voice Assistant Pipeline

```python
async def voice_assistant(audio_path):
    from hypr_voice.services.wispr_flow_direct import WisprFlowDirect
    from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

    # Transcribe
    wispr = WisprFlowDirect()
    await wispr.connect()
    transcription = await wispr.transcribe(audio_path)

    # Process with Claude
    claude = ClaudeTTSAgent(
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )
    await claude.connect()
    response = await claude.chat(transcription['text'])

    # TTS response
    from hypr_voice.services.voice import UniversalTTS, TTSConfig, TTSProvider
    tts = UniversalTTS(TTSConfig(provider=TTSProvider.KOKORO))
    result = await tts.speak(response['response'])

    return result['audio_file']
```

### Discord Bot Transcription

```python
from hypr_voice.services.tools.discord_tool import DiscordClient

async def transcribe_discord_audio(channel_id, audio_attachment):
    discord = DiscordClient()
    await discord.initialize()

    # Download audio
    audio_path = await download_discord_audio(audio_attachment)

    # Transcribe
    wispr = WisprFlowDirect()
    await wispr.connect()
    transcription = await wispr.transcribe(audio_path)

    # Send transcription
    await discord.send_message(
        channel_id,
        f"Transcription: {transcription['text']}"
    )
```

### Real-Time Captioning

```python
async def realtime_captioning():
    wispr = WisprFlowDirect()
    await wispr.connect()

    async for audio_chunk in get_audio_stream():
        result = await wispr.transcribe_streaming(audio_chunk)

        if result['type'] == 'transcription':
            # Display caption
            display_caption(result['text'])
```

## API Reference

### WisprFlowDirect

**Constructor**:
- No arguments required

**Methods**:
- `async connect()`: Connect to Wispr Flow API
- `async close()`: Close connection
- `async transcribe(audio_path, **kwargs)`: Transcribe audio file
- `async transcribe_streaming(audio_source, **kwargs)`: Stream transcription

**Configuration**:
- `chunk_seconds`: Audio chunk size in seconds (default: 30)
- `use_opus`: Use Opus encoding (default: True)
- `opus_bitrate`: Opus bitrate (default: 24000)
- `auto_chunk`: Enable automatic chunking (default: True)
- `streaming_mode`: Enable streaming (default: True)
- `timeout`: Request timeout in seconds (default: 600)

### HyprWhisperIntegration

**Constructor Parameters**:
- `whisper_host`: Whisper server host (default: "localhost")
- `whisper_port`: Whisper server port (default: 9090)
- `agent_host`: Agent orchestrator host (default: "localhost")
- `agent_port`: Agent orchestrator port (default: 8922)

**Methods**:
- `async start()`: Start integration
- `async stop()`: Stop integration
- `async get_current_context()`: Get current application context
- `async transcribe_with_context(audio_data)`: Transcribe with context

### HyprlandMonitor

**Constructor Parameters**:
- `update_interval`: Polling interval in seconds (default: 0.15)

**Methods**:
- `async start()`: Start monitoring
- `async stop()`: Stop monitoring
- `register_callback(callback)`: Register context change callback
- `get_current_context()`: Get current context

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [TTS Integration](./tts-integration.md)
- [Hyprland Integration](./hyprland-integration.md)
- [Wispr Flow API](../api/wispr-flow-api.md)
