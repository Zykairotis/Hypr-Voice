# Hypr-Voice User Documentation

Welcome to the Hypr-Voice user documentation! This comprehensive guide will help you install, configure, and use all features of the Hypr-Voice system.

## What is Hypr-Voice?

Hypr-Voice is a powerful multi-agent voice orchestration system with Claude AI integration. It combines advanced speech recognition, intelligent AI agents, and text-to-speech to provide a natural voice interface for your computer.

### Key Features

- **🎤 Voice Transcription** - State-of-the-art speech-to-text with Whisper
- **🗣️ Text-to-Speech** - Natural voice synthesis with multiple providers
- **🤖 Multi-Agent AI** - Specialized agents for different tasks
- **🧠 Context Awareness** - Understands your active window and workspace
- **🌐 Web Interface** - Beautiful, intuitive dashboard
- **⌨️ CLI Tools** - Powerful command-line interface
- **🔧 Push-to-Talk** - F10 keybinding for hands-free operation

## Getting Started

### New Users

If you're new to Hypr-Voice, follow this path:

1. **[Installation Guide](./installation.md)** - Set up Hypr-Voice on your system
2. **[Quick Start](./quickstart.md)** - Get up and running in 5 minutes
3. **[Features Overview](./features.md)** - Learn what's possible
4. **[Common Use Cases](./use-cases.md)** - See real-world examples

### Quick Links

| Want to... | Go to... |
|------------|----------|
| Install Hypr-Voice | [Installation Guide](./installation.md) |
| Start using the system | [Quick Start](./quickstart.md) |
| Learn about features | [Features Overview](./features.md) |
| Use the Web interface | [Web UI Guide](./web-ui-guide.md) |
| Use command-line tools | [CLI Guide](./cli-guide.md) |
| Find example workflows | [Use Cases](./use-cases.md) |
| Fix a problem | [Troubleshooting](./troubleshooting.md) |

## Documentation Structure

### Installation & Setup
- **[Installation Guide](./installation.md)** - Detailed setup instructions
- **[Quick Start](./quickstart.md)** - Fast-track to first use

### Feature Guides
- **[Features Overview](./features.md)** - Complete feature documentation
- **[Web UI Guide](./web-ui-guide.md)** - Dashboard usage
- **[CLI Guide](./cli-guide.md)** - Command-line interface

### Practical Guides
- **[Use Cases](./use-cases.md)** - Real-world workflows and examples
- **[Troubleshooting](./troubleshooting.md)** - Problem-solving guide

## Quick Reference

### Essential Commands

```bash
# Start all services
./scripts/start_everything.sh start

# Stop all services
./scripts/start_everything.sh stop

# Check status
./scripts/start_everything.sh status

# Voice recording
./scripts/hypr-voice-record.sh

# Test microphone
./scripts/utils/test_mic.sh
```

### Web Interface

Open your browser to: **http://localhost:8933**

### Service Ports

| Service | Port |
|---------|------|
| Hybrid Whisper | 9099 |
| Wispr Flow | 9095 |
| Context WebSocket | 9091 |
| Orchestrator | 9093 |
| Web UI Bridge | 8934 |
| Web UI Frontend | 8933 |

## System Requirements

### Minimum
- **OS**: Linux (Ubuntu 22.04+, Arch, or similar)
- **Python**: 3.10+
- **Node.js**: 18+
- **RAM**: 8 GB
- **Disk**: 10 GB free

### Recommended
- **OS**: Linux (Ubuntu 22.04+ or Arch)
- **Python**: 3.11+
- **Node.js**: 20+
- **RAM**: 16 GB
- **Disk**: 20 GB free
- **Microphone**: For voice input

## Core Concepts

### Agents

Hypr-Voice uses specialized AI agents for different tasks:

- **Code Agent** - Programming and code analysis
- **Research Agent** - Information gathering and documentation
- **Shell Agent** - System operations and commands
- **Voice Agent** - Natural conversation
- **Enhanced Context Agent** - Context-aware assistance

### Transcription Modes

- **LOCAL Mode** - Uses local Whisper server (free, offline)
- **FLOW Mode** - Uses Wispr Flow API (faster, requires internet)

### Text-to-Speech Providers

- **Deepgram** - Ultra-low latency (recommended)
- **ElevenLabs** - Highest quality
- **Kokoro-ONNX** - Local synthesis (no API costs)

## Common Tasks

### Record Voice Query

```bash
# Using script
./scripts/hypr-voice-record.sh

# Using push-to-talk (F10)
Press F10 → Speak → Press F10 again
```

### Start Conversation

1. Open Web UI: http://localhost:8933
2. Go to Agent Panel
3. Type or speak your message
4. AI responds with text and voice

### Check System Status

```bash
./scripts/start_everything.sh status
```

### Test Microphone

```bash
./scripts/utils/test_mic.sh
```

## Getting Help

### Self-Service

- **[Troubleshooting Guide](./troubleshooting.md)** - Solutions to common issues
- **[FAQ](./troubleshooting.md#faq)** - Frequently asked questions
- **[Use Cases](./use-cases.md)** - Example workflows

### Debug Information

To get help effectively, collect this information:

```bash
# System info
python3 --version
node --version

# Service status
./scripts/start_everything.sh status

# Recent logs
tail -50 /tmp/hybrid-whisper-server.log
tail -50 /tmp/hypr-voice-orchestrator.log
```

## Configuration

### Environment Variables

Main configuration is in `.env` file:

```bash
# Required
CEREBRAS_API_KEY_ONE=your_key_here
WISPR_FLOW_JWT_TOKEN=your_token_here
WISPR_FLOW_BASETEN_API_KEY=your_key_here
WISPR_FLOW_USER_UUID=your_uuid_here
DEEPGRAM_API_KEY=your_key_here

# Optional settings
MODE=LOCAL  # or FLOW
WISPR_FLOW_USE_OPUS=1
FLOW_STREAMING_MODE=1
```

### Configuration Files

- `config/hypr_voice/whisper/config.yaml` - Whisper settings
- `config/hypr_voice/whisper/audio-profile.yaml` - Audio configuration
- `config/hypr_voice/claude-sdk.yaml` - Claude SDK settings

## Tips for Best Results

### Voice Input

- Speak clearly and at moderate pace
- Minimize background noise
- Use quality microphone
- Add technical terms to vocabulary

### AI Queries

- Be specific about what you want
- Provide context when needed
- Use appropriate agent for task
- Break complex tasks into steps

### Performance

- Enable Opus compression
- Use streaming mode for long recordings
- Increase chunk size for faster processing
- Check network speed for cloud APIs

## Security Notes

### API Keys

- Never commit `.env` file to version control
- Rotate keys regularly
- Use separate keys for dev/prod
- Monitor usage and quotas

### Data Privacy

- **LOCAL mode**: Audio stays on your computer
- **FLOW mode**: Audio sent to cloud API
- Check provider privacy policies
- Review what data is sent

## Next Steps

1. **Install** - Follow the [Installation Guide](./installation.md)
2. **Start** - Use the [Quick Start](./quickstart.md)
3. **Explore** - Read the [Features Overview](./features.md)
4. **Practice** - Try [Use Cases](./use-cases.md)
5. **Customize** - Adjust settings to your needs

## Additional Resources

### For Developers
- [API Documentation](../api/)
- [Development Guide](../development/)
- [Contributing Guidelines](../CONTRIBUTING.md)

### For Operators
- [Operations Guide](../operations/)
- [Deployment Guide](../operations/deployment.md)
- [Monitoring Guide](../operations/monitoring.md)

### Community
- Report Issues: [GitHub Issues](https://github.com/your-repo/issues)
- Discussions: [GitHub Discussions](https://github.com/your-repo/discussions)
- Updates: Follow the project repository

## Version Information

- **Current Version**: 0.2.0
- **Python**: 3.10+
- **Node.js**: 18+

## License

Proprietary - All rights reserved

---

**Need help?** Start with the [Troubleshooting Guide](./troubleshooting.md)

**Ready to begin?** Jump to the [Installation Guide](./installation.md)

**Want to learn more?** Check out the [Features Overview](./features.md)
