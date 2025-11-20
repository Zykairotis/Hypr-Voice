# Hypr-Whisper Project Structure

## 📁 Directory Organization

```
Hypr-Whisper/
├── 🎯 Core Files
│   ├── hybrid_server.py         # Main server with vocabulary enhancement
│   ├── hybrid_client.py         # Client for server communication
│   ├── hypr-voice-type.py       # Push-to-talk (F9) voice typing
│   ├── vocabulary_manager.py    # Vocabulary enhancement system
│   ├── add_vocabulary.py        # Add custom words interactively
│   └── RENAME_SUMMARY.md        # Project rename documentation
│
├── 📚 Configuration
│   ├── config/
│   │   ├── config.yaml          # Main server configuration
│   │   ├── vocabulary.yaml      # Global vocabulary (89+ words)
│   │   ├── vocabularies/        # Context-specific vocabularies
│   │   │   ├── development.yaml
│   │   │   ├── gaming.yaml
│   │   │   └── productivity.yaml
│   │   ├── audio-profile.yaml   # Audio device configuration
│   │   ├── notifications.yaml   # Notification settings
│   │   ├── hyprvoice.conf       # Hyprland keybind configuration
│   │   └── hypr-voice.service   # Systemd service file
│   │
├── 🔧 Scripts
│   ├── scripts/
│   │   ├── start_hybrid_server.sh  # Start the server
│   │   ├── hypr-voice-record.sh    # F9 recording script
│   │   ├── hypr-voice-daemon.sh    # Background daemon
│   │   ├── hypr-voice-quick.sh     # Fixed-duration recording
│   │   ├── app_detector.py         # Application detection
│   │   └── audio-setup.sh          # Audio device setup
│   │
├── 🧪 Tests
│   ├── tests/
│   │   ├── test_vocabulary.py   # Vocabulary testing
│   │   └── test_hybrid.py       # Server testing
│   │
├── 🛠️ Utilities
│   ├── utils/
│   │   └── wltype_integration.py  # Wayland typing integration
│   │
├── 📝 Documentation
│   ├── docs/
│   │   ├── README.md
│   │   ├── CONFIGURATION.md
│   │   ├── HYPR-VOICE-PTT.md
│   │   └── wltype/              # Wayland typing docs
│   │
├── 📦 Project Files
│   ├── requirements.txt         # Python dependencies
│   └── HYBRID_README.md         # Server documentation
│
└── 📂 Runtime Directories
    ├── logs/                    # Server logs (auto-created)
    └── recordings/              # Audio recordings (if enabled)
```

## 🚀 Quick Start

```bash
# Start server
./scripts/start_hybrid_server.sh start

# Add vocabulary words
./add_vocabulary.py

# Test vocabulary
cd tests && python test_vocabulary.py
```

## 🔑 Key Features

- **Vocabulary Enhancement**: 89+ technical terms with fuzzy matching
- **Push-to-Talk**: F9 keybind for voice typing
- **REST API + WebSocket**: Hybrid server architecture
- **Application-Aware**: Switches vocabulary based on active window

## 📊 Cleanup Summary

### Removed (5.2MB total):
- `.venv/` - Redundant virtual environment
- `__pycache__/` - Python cache files
- `.claude*/` - IDE artifacts
- `plan/` - Old planning documents
- `examples/` - Redundant test files
- Old log files (4.5MB)

### Organized:
- Test files → `tests/`
- Utility files → `utils/`
- Cleaned `logs/` and `recordings/`

## 🔗 Virtual Environment

Using project-wide venv at:
```
/home/mewtwo/Zykairotis/Hypr-Voice/.venv
```

All Python scripts automatically use this venv.
