# Command-Line Interface Guide

Hypr-Voice provides powerful command-line tools for voice interaction, system management, and automation. This guide covers all CLI features.

## Quick Reference

### Main Commands

```bash
# Start all services
./scripts/start_everything.sh start

# Stop all services
./scripts/start_everything.sh stop

# Check service status
./scripts/start_everything.sh status

# Voice recording and transcription
./scripts/hypr-voice-record.sh

# Test microphone
./scripts/utils/test_mic.sh

# Audio configuration
./scripts/utils/audio-setup.sh
```

## Service Management

### Start/Stop All Services

**start_everything.sh** - Main service control script

```bash
# Start all services
./scripts/start_everything.sh start

# Stop all services
./scripts/start_everything.sh stop

# Restart all services
./scripts/start_everything.sh restart

# Check status
./scripts/start_everything.sh status
```

**Services Started:**
1. Hybrid Whisper Server (port 9099)
2. Context WebSocket (port 9091)
3. Orchestrator (port 9093)
4. Web UI (port 8933)
5. Web UI Bridge (port 8934)

### Individual Service Control

**Hybrid Whisper Server**

```bash
./scripts/start_hybrid_server.sh start    # Start
./scripts/start_hybrid_server.sh stop     # Stop
./scripts/start_hybrid_server.sh restart  # Restart
./scripts/start_hybrid_server.sh status   # Status
./scripts/start_hybrid_server.sh test     # Test
```

**Wispr Flow API Server** (if using MODE=FLOW)

```bash
./scripts/start_wispr_flow.sh start
./scripts/start_wispr_flow.sh stop
./scripts/start_wispr_flow.sh restart
./scripts/start_wispr_flow.sh status
```

## Voice Recording

### hypr-voice-record.sh

Main script for voice recording and transcription.

**Basic Usage:**
```bash
./scripts/hypr-voice-record.sh
```

**Options:**
```bash
# Record for specific duration (seconds)
./scripts/hypr-voice-record.sh --duration 30

# Send text query directly (no recording)
./scripts/hypr-voice-record.sh --text "Your query here"

# Specify output file
./scripts/hypr-voice-record.sh --output /path/to/output.txt

# Disable TTS response
./scripts/hypr-voice-record.sh --no-speak

# Use specific agent
./scripts/hypr-voice-record.sh --agent code-worker

# Show help
./scripts/hypr-voice-record.sh --help
```

**Example Sessions:**

```bash
# Simple voice query
./scripts/hypr-voice-record.sh
# Speak your query...
# Transcription appears and is sent to agent

# Direct text query
./scripts/hypr-voice-record.sh --text "What's my current directory?"

# Long recording with specific agent
./scripts/hypr-voice-record.sh --duration 60 --agent research-worker

# Silent mode (no spoken response)
./scripts/hypr-voice-record.sh --no-speak
```

### Push-to-Talk (F10 Keybinding)

**Hyprland Integration:**

Configure in `~/.config/hypr/hyprvoice.conf`:

```bash
# F10 keybinding for push-to-talk
bind = $mainMod, F10, exec, /path/to/Hypr-Voice/scripts/hypr-agent.sh
```

**Usage:**
1. Press **F10** to start recording
2. Speak your query
3. Press **F10** again to stop
4. System processes your voice

**Audio Feedback:**
- Sound plays when recording starts
- Sound plays when recording stops
- Error sound if something fails

**hypr-agent.sh** Script:

```bash
# Check status
./scripts/hypr-agent.sh status

# Send query directly
./scripts/hypr-agent.sh query "Your text query"

# Test configuration
./scripts/hypr-agent.sh test
```

## Audio Configuration

### audio-setup.sh

Audio system configuration helper.

```bash
# List available audio devices
./scripts/utils/audio-setup.sh list

# Test microphone (5 seconds)
./scripts/utils/audio-setup.sh test

# Test with specific device
./scripts/utils/audio-setup.sh test alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor 10

# Show current configuration
./scripts/utils/audio-setup.sh current

# Set default audio source
./scripts/utils/audio-setup.sh set-source <device-name>

# Set default audio sink
./scripts/utils/audio-setup.sh set-sink <device-name>
```

**Device Listing Example:**
```bash
$ ./scripts/utils/audio-setup.sh list

Available Audio Sources:
0: alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor
1: alsa_input.pci-0000_2d_00.1.analog-stereo

Current Audio Source: @DEFAULT_SOURCE@
```

### test_mic.sh

Advanced microphone testing with level analysis.

```bash
./scripts/utils/test_mic.sh
```

**Features:**
- Real-time microphone level display
- Peak level detection
- Clipping indication
- Sample rate and bit depth display
- Recommended settings

**Example Output:**
```
Microphone Test
===============

Device: alsa_input.pci-0000_2d_00.1.analog-stereo
Sample Rate: 16000 Hz
Channels: 1 (Mono)

Recording levels:
[████████████████████░░░░] 75% - Good
Peak: -12.3 dB
Clipping: No

Recommendation: Audio levels are good for speech recognition.
```

## API Interaction

### Direct API Calls

**Voice Processing:**

```bash
# Process text query
curl -X POST http://localhost:9093/voice/process \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What can you help me with?",
    "speak_response": true
  }'
```

**Transcription:**

```bash
# Transcribe audio file
curl -X POST http://localhost:9099/transcribe \
  -F "file=@/path/to/audio.wav"
```

**Agent Management:**

```bash
# List active agents
curl http://localhost:9093/agents

# Spawn new agent
curl -X POST http://localhost:9093/spawn \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "code-worker",
    "task": "Help with Python code"
  }'

# Destroy agent
curl -X DELETE http://localhost:9093/agents/<session-id>
```

**Enhanced Context Processing:**

```bash
# Process with context awareness
curl -X POST http://localhost:9093/voice/process/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What should I do next?",
    "context": {
      "window": {
        "class": "code",
        "title": "my_script.py"
      },
      "clipboard": "def hello():",
      "timestamp": "2024-01-26T12:00:00Z"
    },
    "speak_response": true
  }'
```

### WebSocket Connections

**Context WebSocket:**

```bash
# Connect using wscat
wscat -c ws://localhost:9091/ws

# Subscribe to events
{"type": "subscribe", "topic": "all", "client_id": "my-client"}

# Send query
{"type": "query", "query": "Test message", "session_id": "optional"}

# Ping/pong
{"type": "ping"}
```

**Orchestrator WebSocket:**

```bash
wscat -c ws://localhost:9093/ws
```

## System Monitoring

### Service Status

```bash
# Check all services
./scripts/start_everything.sh status

# Check specific service
./scripts/start_hybrid_server.sh status

# Service health endpoints
curl http://localhost:9099/health     # Whisper
curl http://localhost:9093/health     # Orchestrator
curl http://localhost:9091/health     # Context WS
```

### Log Monitoring

**Log Locations:**
- Hybrid Whisper: `/tmp/hybrid-whisper-server.log`
- Wispr Flow: `logs/wispr_flow.log`
- Context WebSocket: `/tmp/hypr-voice-context-ws.log`
- Orchestrator: `/tmp/hypr-voice-orchestrator.log`
- Web UI: `/tmp/hypr-voice-ui.log`

**View Logs:**
```bash
# Follow logs in real-time
tail -f /tmp/hybrid-whisper-server.log

# View last 50 lines
tail -n 50 /tmp/hypr-voice-orchestrator.log

# Search logs for errors
grep -i error /tmp/hypr-voice-*.log

# View all service logs at once
tail -f /tmp/hypr-voice-*.log
```

### Performance Monitoring

**Check Resource Usage:**
```bash
# CPU and memory
ps aux | grep -E "whisper|orchestrator|context"

# Port usage
lsof -i :9099  # Whisper
lsof -i :9093  # Orchestrator
lsof -i :9091  # Context WS
lsof -i :8933  # Web UI

# Process tree
pstree -p | grep hypr
```

## Configuration Management

### Environment Variables

**View Current Configuration:**
```bash
# Show all Hypr-Voice variables
env | grep HYPR_

# Show Wispr Flow settings
env | grep WISPR_FLOW

# Show TTS settings
env | grep -E "DEEPGRAM|ELEVENLABS"
```

**Test Configuration:**
```bash
# Source .env and test
set -a
source .env
set +a

# Verify required variables
echo $CEREBRAS_API_KEY_ONE
echo $WISPR_FLOW_JWT_TOKEN
echo $DEEPGRAM_API_KEY
```

### Configuration Files

**View Configuration:**
```bash
# Whisper configuration
cat config/hypr_voice/whisper/config.yaml

# Audio profile
cat config/hypr_voice/whisper/audio-profile.yaml

# Claude SDK configuration
cat config/hypr_voice/claude-sdk.yaml
```

**Edit Configuration:**
```bash
# Use your preferred editor
nano config/hypr_voice/whisper/config.yaml
vim config/hypr_voice/whisper/audio-profile.yaml
```

## Automation

### Cron Jobs

**Scheduled Tasks:**

```bash
# Edit crontab
crontab -e

# Example: Daily backup at 2 AM
0 2 * * * /path/to/Hypr-Voice/scripts/hypr_voice/backup.sh

# Example: Weekly cleanup
0 3 * * 0 /path/to/Hypr-Voice/scripts/cleanup.sh
```

### Shell Scripting

**Example: Batch Processing**

```bash
#!/bin/bash
# batch-queries.sh

QUERIES=(
    "Check system status"
    "List running processes"
    "Check disk usage"
)

for query in "${QUERIES[@]}"; do
    echo "Processing: $query"
    ./scripts/hypr-voice-record.sh --text "$query"
    sleep 5
done
```

**Example: Voice Note Taker**

```bash
#!/bin/bash
# voice-note.sh

DATE=$(date +%Y%m%d-%H%M%S)
OUTPUT="/path/to/notes/note-$DATE.txt"

./scripts/hypr-voice-record.sh --duration 60 --output "$OUTPUT"
echo "Note saved to: $OUTPUT"
```

### Integration with Other Tools

**tmux Integration:**

```bash
# Create tmux session with Hypr-Voice
tmux new-session -d -s hypr-voice './scripts/start_everything.sh start'
tmux attach -t hypr-voice
```

**systemd Service:**

Create `/etc/systemd/system/hypr-voice.service`:

```ini
[Unit]
Description=Hypr-Voice Service
After=network.target

[Service]
Type=forking
User=your-user
WorkingDirectory=/path/to/Hypr-Voice
ExecStart=/path/to/Hypr-Voice/scripts/start_everything.sh start
ExecStop=/path/to/Hypr-Voice/scripts/start_everything.sh stop
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hypr-voice
sudo systemctl start hypr-voice
sudo systemctl status hypr-voice
```

## Troubleshooting

### Common Issues

**Port Already in Use:**
```bash
# Find process using port
lsof -i :9099

# Kill process
kill -9 $(lsof -t -i:9099)

# Or use different port in .env
HYPR_WHISPER_PORT=9100
```

**Permission Denied:**
```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/utils/*.sh

# Fix audio permissions
sudo usermod -a -G audio $USER
# Log out and back in
```

**Virtual Environment Issues:**
```bash
# Recreate venv
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Debug Mode

**Enable Detailed Logging:**

In `.env`:
```bash
HYPR_VOICE_TRACE=1
HYPR_VOICE_FLOW_TRACE=1
HYPR_VOICE_TRACE_CONTEXT=1
```

**View Debug Logs:**
```bash
# All traces
tail -f /tmp/hypr-voice-*.log | grep -i trace

# Specific component
tail -f /tmp/hybrid-whisper-server.log | grep -i debug
```

## Tips and Best Practices

### Productivity Tips

**Aliases:**
Add to `~/.bashrc`:
```bash
alias hv-start='./scripts/start_everything.sh start'
alias hv-stop='./scripts/start_everything.sh stop'
alias hv-status='./scripts/start_everything.sh status'
alias hv-record='./scripts/hypr-voice-record.sh'
alias hv-mic='./scripts/utils/test_mic.sh'
```

**Functions:**
```bash
hv-query() {
    ./scripts/hypr-voice-record.sh --text "$*"
}
```

### Performance Optimization

**Reduce Latency:**
```bash
# In .env
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_CHUNK_SECONDS=30
FLOW_STREAMING_MODE=1
```

**Improve Accuracy:**
```bash
# Add custom vocabulary
# Edit config/hypr_voice/whisper/vocabulary.txt
```

## Reference

### Exit Codes

- `0` - Success
- `1` - General error
- `2` - Invalid argument
- `3` - Service not running
- `4` - Configuration error
- `5` - Network error

### Environment Variable Reference

See [Features Overview](./features.md#configuration) for complete list.

For more information:
- [Installation Guide](./installation.md)
- [Quick Start](./quickstart.md)
- [Troubleshooting](./troubleshooting.md)
