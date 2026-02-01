# Quick Start Guide

Get started with Hypr-Voice in 5 minutes! This guide will help you launch the system and make your first voice query.

## Quick Start (Simplest Method)

The fastest way to start Hypr-Voice is using the startup script:

```bash
# From the project root directory
./scripts/start_everything.sh start
```

This single command launches:
- ✅ Hybrid Whisper Server (speech-to-text)
- ✅ Context WebSocket (window/clipboard awareness)
- ✅ Orchestrator (AI agent system)
- ✅ Web UI (browser interface)
- ✅ Bridge service (connects all components)

## First Launch

### 1. Start the System

```bash
./scripts/start_everything.sh start
```

You should see output like:
```
[start-all] Starting Hypr-Voice services...
[start-all] Starting hybrid server (9099)...
[start-all] Starting Context WebSocket (9091)...
[start-all] Starting Orchestrator (9093)...
[start-all] Starting Web UI...
[start-all] ✓ All services started successfully
```

### 2. Open the Web Interface

Open your web browser and navigate to:

```
http://localhost:8933
```

The dashboard should appear showing:
- Whisper panel (voice transcription)
- Agent panel (AI assistant)
- Status indicators (all should show "online")

### 3. Make Your First Voice Query

**Option A: Using the Web UI**

1. Click the **"Start Recording"** button in the Whisper panel
2. Speak clearly into your microphone
   - Example: *"What's the weather like today?"*
3. Click **"Stop Recording"**
4. Your speech will be transcribed and sent to the AI agent
5. The AI response will appear in the Agent panel
6. If TTS is enabled, the response will be spoken aloud

**Option B: Using Push-to-Talk (F10 Key)**

If you're using Hyprland with the keybinding configured:

1. Press **F10** to start recording
2. Speak your query
3. Press **F10** again to stop
4. The system will transcribe and process your voice

### 4. Try Text Queries

You can also type queries directly:

1. In the Agent panel, type your message
2. Click **"Send"** or press **Enter**
3. The AI agent will respond

## What's Happening?

When you make a voice query, Hypr-Voice:

1. **Records** your voice via microphone
2. **Transcribes** speech to text using Whisper
3. **Routes** to the appropriate AI agent
4. **Processes** your request with context awareness
5. **Generates** a response using Claude AI
6. **Speaks** the response using text-to-speech

## Basic Controls

### Start/Stop Services

```bash
# Start all services
./scripts/start_everything.sh start

# Stop all services
./scripts/start_everything.sh stop

# Check service status
./scripts/start_everything.sh status

# Restart all services
./scripts/start_everything.sh restart
```

### Individual Service Control

```bash
# Start/stop Whisper server only
./scripts/start_hybrid_server.sh start
./scripts/start_hybrid_server.sh stop

# Start/stop Wispr Flow API (if using MODE=FLOW)
./scripts/start_wispr_flow.sh start
./scripts/start_wispr_flow.sh stop
```

## Common First Tasks

### Test Your Microphone

```bash
# Test microphone recording (5 seconds)
./scripts/utils/audio-setup.sh test

# Advanced test with level analysis
./scripts/utils/test_mic.sh
```

### Test Speech Recognition

1. Open the Web UI: http://localhost:8933
2. Go to the **Whisper Panel**
3. Click **"Start Recording"**
4. Speak: *"Hello, this is a test of the voice recognition system."*
5. Click **"Stop Recording"**
6. Check that your speech appears as text

### Test AI Agent

1. In the **Agent Panel**, type: *"What can you help me with?"*
2. Click **"Send"**
3. Read the agent's response about its capabilities

### Test Text-to-Speech

1. Type a message in the Agent Panel
2. Ensure **"Speak Response"** is enabled
3. Send the message
4. Listen for the spoken response

## Navigation Guide

### Web UI Dashboard

The dashboard has several panels accessible via the dock at the bottom:

- **🎤 Whisper Panel** - Voice transcription and recording
- **🤖 Agent Panel** - AI chat and responses
- **🎛️ Orchestrator Panel** - Manage AI agents and sessions
- **📚 Skills Library** - Browse and manage agent skills
- **📖 Vocabulary** - Manage custom vocabulary for better transcription
- **🔊 TTS Controls** - Configure text-to-speech settings
- **🔌 MCP Dashboard** - Model Context Protocol integrations
- **📊 Analytics** - System performance and usage statistics

### Keyboard Shortcuts

In the Web UI:

- **Enter** - Send message
- **Shift+Enter** - New line in message input
- **Ctrl+C** (in terminal) - Stop services

## Example Queries to Try

### System Information
- *"What's my current directory?"*
- *"What processes are running?"*
- *"How much disk space do I have left?"*

### Coding Help
- *"Write a Python function to calculate fibonacci numbers"*
- *"Explain this error: [paste error message]"*
- *"How do I install a package in Python?"*

### Research
- *"What are the latest features in Python 3.12?"*
- *"Explain the difference between REST and GraphQL"*

### Voice Commands
- *"Record a voice note"*
- *"Transcribe this audio file"*
- *"Read the last 5 lines from the server log"*

## Stopping the System

When you're done:

```bash
# Stop all services gracefully
./scripts/start_everything.sh stop
```

Or press **Ctrl+C** in the terminal where services are running.

## What's Next?

Now that you have Hypr-Voice running:

1. 📖 **Explore Features** - Read the [Features Overview](./features.md)
2. 🎛️ **Configure Settings** - Customize your experience
3. 🎯 **Learn Use Cases** - See [Common Use Cases](./use-cases.md)
4. 🔧 **Advanced Setup** - Read the [Web UI Guide](./web-ui-guide.md)
5. 💬 **Join the Community** - Get help and share your experience

## Troubleshooting

### Services Won't Start

```bash
# Check if ports are already in use
lsof -i :9099  # Whisper
lsof -i :9093  # Orchestrator
lsof -i :8933  # Web UI

# Kill processes using specific ports
kill -9 $(lsof -t -i:9099)
```

### Can't Access Web UI

```bash
# Check if Web UI is running
ps aux | grep next

# Check Web UI logs
tail -f /tmp/hypr-voice-ui.log

# Restart Web UI only
cd web-ui && npm start
```

### Microphone Not Working

```bash
# Test microphone
./scripts/utils/test_mic.sh

# List audio devices
pactl list sources short

# Check audio configuration
./scripts/utils/audio-setup.sh current
```

### Transcription Not Working

```bash
# Check Whisper server status
./scripts/start_hybrid_server.sh status

# View Whisper logs
tail -f /tmp/hybrid-whisper-server.log

# Test Whisper server
curl -X POST http://localhost:9099/transcribe \
  -H "Content-Type: application/json" \
  -d '{"text": "test"}'
```

For more troubleshooting help, see the [Troubleshooting Guide](./troubleshooting.md).

## Service Ports Reference

| Service | Port | URL |
|---------|------|-----|
| Hybrid Whisper | 9099 | http://localhost:9099 |
| Wispr Flow | 9095 | http://localhost:9095 |
| Context WebSocket | 9091 | ws://localhost:9091/ws |
| Orchestrator | 9093 | http://localhost:9093 |
| Web UI Bridge | 8934 | ws://localhost:8934/ws/context |
| Web UI Frontend | 8933 | http://localhost:8933 |

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting Guide](./troubleshooting.md)
2. Review logs in `/tmp/hypr-voice/`
3. Ensure all API keys are configured in `.env`
4. Verify microphone and audio are working
5. Check that all services are running

Enjoy using Hypr-Voice! 🎉
