# 🎤 Hypr-Voice

A sophisticated context-aware voice input system for Arch Linux with Hyprland, featuring intelligent transcription and AI-enhanced text processing.

## ✨ Key Features

### 🎯 Core Capabilities
- **Real-time Voice Transcription** using WhisperLive with Voice Activity Detection
- **Context-Aware Processing** with per-application profiles
- **Multi-Provider LLM Support** (xAI/Grok, OpenAI, Anthropic, Ollama)
- **Intelligent Memory System** using Cognee for persistent context
- **Hyprland Integration** with automatic window detection
- **Clipboard & Notification Actions** for seamless workflow

### 🚀 Advanced Features
- **Push-to-Talk & Continuous Modes** for flexible input
- **Application Profiles** for context-specific text improvement
- **Memory Persistence** across sessions using semantic knowledge graphs
- **Multi-Language Support** with Whisper
- **GPU Acceleration** with CUDA support
- **WebSocket Streaming** for low-latency communication
- **Audio Level Visualization** for real-time feedback
- **Smart Paste Detection** for all applications (including Electron apps)

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────────┐
│ Audio Input │────▶│ WhisperLive  │────▶│   Context    │────▶│   Output    │
│   (Mic)     │     │  Server      │     │   Engine     │     │  Handler    │
└─────────────┘     └──────────────┘     └──────────────┘     └─────────────┘
                           │                     │                     │
                           ▼                     ▼                     ▼
                    Transcription          LLM Processing      Clipboard/Notify
```

## 🚀 Quick Start

### Prerequisites
- Arch Linux with Hyprland
- Python 3.10+
- Microphone (USB or Bluetooth)

### Installation (One Command)
```bash
cd hypr-voice
./scripts/install_deps.sh
```

### Basic Usage
```bash
# Start Hypr-Voice
./scripts/run_hypr_voice.sh start

# Use it
 Hold F9 → Speak → Release key → Text appears!

# Check status
./scripts/run_hypr_voice.sh status
```

### Keybinds
- **F9**: Hold to record, release to transcribe & paste
- **SUPER + F9**: Show system status
- **SUPER + SHIFT + F9**: Emergency stop

## 📖 Documentation

### 📚 Getting Started
- **[Installation Guide](installation/START_HERE.md)** - Complete setup instructions
- **[Quick Start](installation/quick-start.md)** - Up and running in 5 minutes
- **[Installation Checklist](installation/installation-checklist.md)** - Step-by-step verification

### 🛠️ Configuration & Usage
- **[Setup Guide](guides/setup-guide.md)** - Comprehensive configuration reference
- **[Troubleshooting](guides/setup-guide.md#troubleshooting)** - Common issues and solutions

### ⚡ Features
- **[Audio Level Visualization](features/audio-level-visualization.md)** - Real-time audio feedback
- **[Clipboard Paste Fix](features/paste-fix.md)** - Universal paste support for all apps

### 🔧 Technical Details
- **[Implementation Summary](technical/implementation-summary.md)** - Technical overview
- **[Architecture](../src/Hypr-Whisper/README.md)** - Detailed system architecture
- **[Scripts Overview](technical/scripts-overview.txt)** - Available utility scripts

### 📁 Project Documentation
- **[Project Documentation](../docs/project/README.md)** - Core project documentation and guides
- **[Web UI Documentation](../web-ui/README.md)** - Modern web interface documentation

## 🎯 Supported Applications

### ✅ Fully Supported
- **Terminals**: Kitty, Alacritty, Foot, Wezterm (auto-detects Ctrl+Shift+V)
- **Editors**: VS Code, Windsurf, Cursor, Neovim (smart paste detection)
- **Browsers**: Firefox, Chrome, Edge
- **Communication**: Discord, Slack, Telegram, Teams
- **Productivity**: LibreOffice, GEdit, Obsidian

### 🎛️ Application Profiles
Hypr-Voice includes intelligent profiles for different applications:

- **Terminal**: Technical command preservation, shell abbreviations
- **VSCode/Windsurf**: Code documentation, syntax preservation
- **Gmail**: Professional email formatting and etiquette
- **Discord/Slack**: Casual conversation maintenance
- **Obsidian**: Markdown formatting and organization

## ⚙️ Configuration

### Audio Configuration
Located in `hypr-voice/config/audio_config.yaml`:
- Primary/secondary audio devices
- Quality settings (48kHz recording, 16kHz for Whisper)
- Auto-fallback support

### Application Profiles
Located in `hypr-voice/config/app_profiles.yaml`:
- Per-app writing styles
- Context rules and terminology
- LLM provider settings

### LLM Providers
Configure in `hypr-voice/config/llm_providers.yaml`:
- **xAI/Grok** (primary, fast and intelligent)
- **OpenAI** (fallback, GPT-4)
- **Anthropic** (fallback, Claude)
- **Ollama** (local, Llama3.1)

## 🔧 Advanced Usage

### Mode Selection
- **Raw Mode**: Fast transcription, no LLM overhead (default)
- **Enhanced Mode**: Context-aware AI improvement

### Memory System
- **Session Memory**: Remembers context during current session
- **Persistent Memory**: Learns from interactions across sessions
- **Knowledge Graphs**: Semantic relationships using Cognee + LanceDB

### Customization
```bash
# Change Whisper model
export WHISPER_MODEL="small"  # Options: tiny, base, small, medium, large

# Enable LLM enhancement
export RAW_MODE=false

# Adjust audio levels
export SHOW_AUDIO_LEVELS=true
```

## 🛠️ Development

### Project Structure
```
Hypr-Voice-main/
├── README.md                    # This file
├── hypr-voice/                  # Main application
│   ├── *.py                     # Python modules
│   ├── scripts/                 # Utility scripts
│   ├── config/                  # Configuration files
│   └── docs/                    # Documentation
└── OLD_MARKDOWN_FILES/          # Backup during reorganization
```

### Core Components
- **`whisper_server.py`** - FastAPI transcription server
- **`hypr_voice.py`** - Main client with Hyprland integration
- **`context_engine_cognee.py`** - AI context and memory management
- **`agent_orchestrator.py`** - Multi-provider LLM orchestration

### Dependencies
- **Audio**: `faster-whisper`, `sounddevice`, `webrtcvad`
- **AI**: `cognee`, `lancedb`, `voyageai`, various LLM SDKs
- **System**: `wtype`, `wl-clipboard`, `libnotify`
- **Web**: `fastapi`, `websockets`

## 🐛 Troubleshooting

### Common Issues
```bash
# Check system status
./scripts/debug_setup.sh

# Test audio devices
./scripts/test_audio.sh

# View logs
./scripts/run_hypr_voice.sh logs

# Restart services
./scripts/run_hypr_voice.sh restart
```

### Performance
- **Latency**: 2-5 seconds for short phrases
- **CPU Usage**: 30-60% during transcription (medium model on CPU)
- **Memory**: ~500MB for Whisper + context engine

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `./scripts/debug_setup.sh`
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](hypr-voice/LICENSE) file for details

## 🙏 Acknowledgments

- **OpenAI Whisper** for exceptional transcription accuracy
- **Ollama** for local LLM inference
- **Cognee** for knowledge graph memory management
- **Hyprland community** for the amazing window manager
- **Wayland ecosystem** contributors

## 📊 Performance

- **Accuracy**: Excellent (Whisper medium model)
- **Speed**: 2-5 second latency for most phrases
- **Reliability**: Multiple fallback mechanisms
- **Compatibility**: Works with virtually all Wayland applications

---

**🎉 Ready to get started?**

1. Run `./scripts/install_deps.sh`
2. Test with `./scripts/test_audio.sh`
3. Start with `./scripts/run_hypr_voice.sh start`
4. Press `F9` and begin dictating!

**Need help?** Check the [Installation Guide](hypr-voice/docs/installation/START_HERE.md) or [Setup Guide](hypr-voice/docs/guides/setup-guide.md).