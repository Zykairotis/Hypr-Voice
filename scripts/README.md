# Hypr-Voice Scripts

This directory contains all scripts for running and managing the Hypr-Voice system.

## Quick Start

```bash
# Start all services (Whisper STT, Context WS, Orchestrator, Web UI)
./scripts/start_everything.sh start

# Stop all services
./scripts/start_everything.sh stop

# Check status of all services
./scripts/start_everything.sh status
```

## Core Scripts

### Main Startup Script

| Script | Description |
|--------|-------------|
| `start_everything.sh` | **DO NOT MODIFY** - Starts all services: Hybrid Whisper, Context WebSocket, Orchestrator, Web UI + Bridge |

### Service Scripts (Dependencies)

| Script | Description | Port |
|--------|-------------|------|
| `start_hybrid_server.sh` | Whisper STT server with vocabulary enhancement | 9099 |
| `start_wispr_flow.sh` | Wispr Flow API transcription server (optional, MODE=FLOW) | 9095 |

### Agent Scripts

| Script | Description |
|--------|-------------|
| `hypr-agent.sh` | F10 keybinding handler for push-to-talk voice input |

### Installation Scripts

| Script | Description |
|--------|-------------|
| `install_claude_sdk.sh` | One-time installation of Claude Agent SDK |

### Utility Scripts

| Script | Location | Description |
|--------|----------|-------------|
| `loggurl.sh` | `scripts/` | Centralized logging utility |
| `audio-setup.sh` | `scripts/utils/` | Audio configuration helper |
| `test_mic.sh` | `scripts/utils/` | Microphone testing with level analysis |

## Directory Structure

```
scripts/
├── start_everything.sh        # Main startup script (DO NOT MODIFY)
├── start_hybrid_server.sh     # Whisper STT server
├── start_wispr_flow.sh        # Wispr Flow API (optional)
├── hypr-agent.sh              # F10 push-to-talk handler
├── install_claude_sdk.sh      # SDK installation
├── loggurl.sh                 # Logging utility
│
├── hypr_voice/                # Hypr Voice system scripts
│   ├── start_system.sh        # Start voice system
│   ├── health_check.sh        # System health check
│   ├── install_voice_services.sh  # Install voice services
│   ├── backup.sh              # Backup utility
│   └── claude-tts             # TTS CLI tool
│
├── sounds/                    # Audio feedback sounds
│   ├── query-in.mp3
│   ├── success.mp3
│   └── error.mp3
│
└── utils/                     # Utility scripts
    ├── audio-setup.sh         # Audio configuration
    └── test_mic.sh            # Microphone testing
```

## Usage Examples

### Starting Services

```bash
# Start all services
./scripts/start_everything.sh start

# Start individual services
./scripts/start_hybrid_server.sh start
./scripts/start_wispr_flow.sh start

# Check service status
./scripts/start_hybrid_server.sh status
./scripts/start_wispr_flow.sh status
```

### Using Push-to-Talk

```bash
# The hypr-agent.sh script is triggered by F10 keybinding in Hyprland
# Configure in: ~/.config/hypr/hyprvoice.conf

# Manual testing:
./scripts/hypr-agent.sh status    # Check orchestrator/whisper status
./scripts/hypr-agent.sh query     # Send direct text query
```

### Audio Configuration

```bash
# List available audio sources
./scripts/utils/audio-setup.sh list

# Test microphone recording (5 seconds)
./scripts/utils/audio-setup.sh test

# Test with specific device
./scripts/utils/audio-setup.sh test alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor 10

# Show current audio configuration
./scripts/utils/audio-setup.sh current

# Advanced microphone test with level analysis
./scripts/utils/test_mic.sh
```

### Service Logs

```bash
# Hybrid server logs
tail -f /tmp/hybrid-whisper-server.log

# Wispr Flow logs
tail -f logs/wispr_flow.log

# Context WebSocket logs
tail -f /tmp/hypr-voice-context-ws.log

# Orchestrator logs
tail -f /tmp/hypr-voice-orchestrator.log

# Web UI logs
tail -f /tmp/hypr-voice-ui.log
```

## Service Ports

| Service | Port | Endpoint |
|---------|------|----------|
| Hybrid Whisper | 9099 | `ws://localhost:9099/ws/{session_id}` |
| Wispr Flow | 9095 | `http://localhost:9095/transcribe` |
| Context WebSocket | 9091 | `ws://localhost:9091/ws` |
| Orchestrator | 9093 | `http://localhost:9093` |
| Web UI Bridge | 8934 | `ws://localhost:8934/ws/context` |
| Web UI Frontend | 8933 | `http://localhost:8933` |

## Configuration

Main configuration files are in `config/hypr_voice/`:

- `config/hypr_voice/whisper/config.yaml` - Whisper STT configuration
- `config/hypr_voice/whisper/audio-profile.yaml` - Audio device configuration
- `config/hypr_voice/claude-sdk.yaml` - Claude SDK configuration
- `config/hypr_voice/config.yaml` - Main system configuration

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MODE` | Operating mode (LOCAL or FLOW) | LOCAL |
| `HYPR_AGENT_PORT` | Orchestrator port | 9093 |
| `HYPR_WHISPER_PORT` | Whisper server port | 9099 |
| `HYPR_AGENT_TIMEOUT` | Agent timeout (seconds) | 300 |
| `HYPR_AGENT_MIC` | Audio source | @DEFAULT_SOURCE@ |
| `HYPR_VOICE_LOG_DIR` | Log directory | /tmp/hypr-voice |

## Troubleshooting

### Services won't start

```bash
# Check if ports are already in use
lsof -i :9099  # Hybrid Whisper
lsof -i :9095  # Wispr Flow
lsof -i :9091  # Context WebSocket
lsof -i :9093  # Orchestrator

# Kill processes using specific ports
kill -9 $(lsof -t -i:9099)
```

### Audio not working

```bash
# Test microphone
./scripts/utils/test_mic.sh

# List audio devices
pactl list sources short

# Check audio configuration
./scripts/utils/audio-setup.sh current
```

### Whisper server issues

```bash
# Check Whisper server status
./scripts/start_hybrid_server.sh status

# Test Whisper server
./scripts/start_hybrid_server.sh test

# View logs
tail -f /tmp/hybrid-whisper-server.log
```

## Development

### Adding new scripts

1. Place core scripts in `scripts/`
2. Place utility scripts in `scripts/utils/`
3. Place Hypr Voice system scripts in `scripts/hypr_voice/`
4. Update this README

### Script conventions

- Use `#!/bin/bash` shebang
- Use `set -e` for error handling
- Use colored output for better UX
- Log to `/tmp/hypr-voice/` directory
- Follow existing script patterns

## Related Documentation

- [Project README](../../README.md)
- [Hypr Voice Documentation](../../docs/hypr_voice/README.md)
- [Audio Configuration Guide](../../docs/hypr_voice/AUDIO_CONFIGURATION.md)
- [Web UI Guide](../../docs/webui/WEB_UI_README.md)
