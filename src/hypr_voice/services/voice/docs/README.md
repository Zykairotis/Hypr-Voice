# Voice Services

Comprehensive text-to-speech system supporting multiple providers with unified management.

## 📁 Structure
```
voice/
├── voice_manager.py      # Unified voice management
├── kokoro/              # Local TTS (no API needed)
├── elevenlabs/          # Premium cloud TTS
└── deepgram/            # Fast cloud TTS with WebSocket
```

## 🎤 Quick Start

### Using Voice Manager (Recommended)
```python
from voice_manager import VoiceManager, VoiceProvider

# Initialize manager
manager = VoiceManager()

# Use default provider (Kokoro)
audio = await manager.synthesize("Hello world!")

# Use specific provider
audio = await manager.synthesize(
    "Hello from ElevenLabs!",
    provider=VoiceProvider.ELEVENLABS,
    voice="rachel"
)
```

## 🚀 Providers

### 1. **Kokoro** (Local, Free)
- No API key required
- Runs completely offline
- Multiple voices & accents
- [Documentation](./kokoro/README.md)

### 2. **ElevenLabs** (Premium Quality)
- Industry-leading voice quality
- 30+ natural voices
- Voice cloning support
- Requires API key
- [Documentation](./elevenlabs/README.md)

### 3. **Deepgram** (Fast & Efficient)
- WebSocket real-time synthesis
- Ultra-low latency
- Aura voices collection
- Requires API key
- [Documentation](./deepgram/README.md)

## 🛠️ Installation

### 1. **Install Dependencies**
```bash
# Core dependencies (already in requirements.txt)
pip install fastapi uvicorn websockets

# Provider-specific
pip install elevenlabs        # For ElevenLabs
pip install deepgram-sdk      # For Deepgram
# Kokoro deps included in main requirements
```

### 2. **Set API Keys**
```bash
# Add to your .env file
echo "ELEVENLABS_API_KEY=your_key" >> .env
echo "DEEPGRAM_API_KEY=your_key" >> .env
```

### 3. **Quick Test**
```bash
# No code needed, just run the app
```

## 📁 Directory Structure

```
voice/
├── deepgram/                    # Deepgram WebSocket implementation
│   ├── deepgram_websocket.py  # Main WebSocket service
│   ├── examples/              # Usage examples
│   └── __init__.py            # Module exports
├── docs/                       # Documentation
│   ├── DEEPGRAM_CLI.md        # CLI tool documentation
│   ├── DEEPGRAM_WEBSOCKET.md  # WebSocket implementation
│   └── IMPLEMENTATION_SUMMARY.md
├── deepgram_clp.py             # Command-line interface
├── voice_manager.py            # Unified voice provider interface
├── kokoro.py                   # Kokoro TTS provider
├── elevenlabs.py               # ElevenLabs TTS provider
└── README.md                   # This file
```

## 🚀 Usage Examples

### Command Line
```bash
# Basic usage
python deepgram_clp.py "Hello world"

# Different voices
python deepgram_clp.py "This is Asteria" --voice asteria
python deepgram_clp.py "This is Orion" --voice orion

# Spanish
python deepgram_clp.py "Hola mundo" --voice nestor

# Custom output
python deepgram_clp.py "Save this" --output custom.wav
```

### Python Integration
```python
from voice_manager import VoiceManager, VoiceProvider

manager = VoiceManager()

# File synthesis
result = await manager.synthesize(
    "Hello from voice manager!",
    provider=VoiceProvider.DEEPGRAM_WEBSOCKET,
    voice="luna"
)

# Real-time streaming
await manager.connect_websocket(VoiceProvider.DEEPGRAM_WEBSOCKET)
await manager.send_text_websocket("Real-time synthesis!")
```

## 📚 Documentation

- [Deepgram CLI Tool](docs/DEEPGRAM_CLI.md) - Command-line usage guide
- [Deepgram WebSocket](docs/DEEPGRAM_WEBSOCKET.md) - Implementation details
- [Implementation Summary](docs/IMPLEMENTATION_SUMMARY.md) - Complete project overview

## 🔧 Configuration

### Deepgram Configuration
```python
from deepgram import DeepgramWebSocketConfig

config = DeepgramWebSocketConfig(
    api_key="your_api_key",
    default_voice="asteria",
    auto_play=True,
    sample_rate=24000,
    speaking_rate=1.0,
    pitch=0.0,
    volume=1.0
)
```

### Voice Manager Configuration
```python
from voice_manager import VoiceManagerConfig, VoiceProvider

config = VoiceManagerConfig(
    default_provider=VoiceProvider.DEEPGRAM_WEBSOCKET,
    fallback_provider=VoiceProvider.KOKORO,
    auto_fallback=True
)

manager = VoiceManager(config)
```

## 🎯 Use Cases

- **Real-time assistants**: Low-latency voice responses
- **Interactive chatbots**: Immediate audio feedback
- **Accessibility tools**: Screen reading applications
- **Content creation**: Automated voiceovers
- **Educational tools**: Language learning applications
- **Customer service**: IVR and automated responses

## 🔊 Audio Playback

### Automatic Playback
```python
config = DeepgramWebSocketConfig(auto_play=True)
```

### Manual Playback
```python
import sounddevice as sd
import numpy as np

# Load audio file
audio_data = np.fromfile('output.wav', dtype=np.int16)
sd.play(audio_data, 24000)
sd.wait()
```

### Command Line Playback
```bash
play /tmp/audio_file.wav
aplay /tmp/audio_file.wav
ffplay /tmp/audio_file.wav
```

## ⚠️ Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   ❌ DEEPGRAM_API_KEY not found!
   ```
   - Set in `/home/mewtwo/Zykairotis/Hypr-Voice/.env`
   - Check file permissions

2. **Audio Playback Not Available**
   ```
   ⚠️ sounddevice not available
   ```
   - Install: `pip install sounddevice numpy`
   - Or use `auto_play=False` for file output

3. **Connection Issues**
   ```
   ⚠️ WebSocket failed, trying HTTP...
   ```
   - Normal fallback behavior
   - HTTP API produces same quality

4. **Import Errors**
   ```
   ImportError: attempted relative import
   ```
   - Ensure you're in the correct directory
   - Use absolute imports when running scripts

## 📊 Performance

- **Deepgram WebSocket**: < 500ms latency
- **File synthesis**: 1-3 seconds
- **Audio quality**: 16-48kHz
- **Voice variety**: 16+ professional voices

## 🔗 External References

- [Deepgram API Documentation](https://developers.deepgram.com/)
- [Aura Voice Models](https://developers.deepgram.com/docs/tts-voices)
- [WebSocket Streaming](https://developers.deepgram.com/docs/tts-websocket-streaming)