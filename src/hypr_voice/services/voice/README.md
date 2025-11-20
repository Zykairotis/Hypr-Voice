# Voice Service

A unified Text-to-Speech (TTS) service supporting multiple providers with streaming capabilities.

## 🚀 Features

- **Multiple Providers**: Deepgram, Kokoro, ElevenLabs
- **Real-time Streaming**: HTTP streaming with audio playback while generating
- **Low Latency**: < 3 seconds perceived latency for all providers
- **Unified Interface**: Simple API for all TTS providers
- **Async Support**: Full async/await support

## 📊 Performance

| Provider | Mode | TTFB | Quality | Cost |
|----------|------|------|---------|------|
| **Deepgram** | Streaming | ~2.4 sec | Premium | Per character |
| **Kokoro** | Streaming | ~2 sec | Good | Free |
| **ElevenLabs** | REST | ~3 sec | Premium | Per character |

## 🛠️ Installation

```bash
# Install dependencies
pip install aiohttp requests websockets pyyaml

# For Deepgram
export DEEPGRAM_API_KEY="your_api_key"

# For ElevenLabs  
export ELEVENLABS_API_KEY="your_api_key"

# Kokoro requires local server running on localhost:8880
```

## 🎯 Quick Start

```python
from services.voice import TTSManager, TTSConfig

# Configure
config = TTSConfig(
    provider="deepgram",  # or "kokoro", "elevenlabs"
    voice="aura-luna-en",
    use_streaming=True,
    stream_and_play=True
)

# Initialize
tts = TTSManager(config)

# Generate speech
result = await tts.speak("Hello! This is a test.")
print(f"Audio saved to: {result['audio_path']}")
```

## 🎮 CLI Usage

```bash
# Deepgram streaming (recommended)
python test_tts.py --provider deepgram --voice aura-luna-en --stream

# Kokoro streaming (free)
python test_tts.py --provider kokoro --voice af_bella --stream

# Quick test
python test_tts.py --provider deepgram --voice aura-luna-en --quick
```

## 📁 Project Structure

```
voice/
├── providers/
│   ├── deepgram/
│   │   ├── deepgram_tts.py      # HTTP streaming TTS
│   │   └── configure_voice.py   # Voice configuration
│   ├── kokoro/
│   │   ├── kokoro_tts.py        # HTTP streaming TTS
│   │   └── kokoro.py            # Core implementation
│   └── elevenlabs/
│       ├── elevenlabs_tts.py    # REST TTS
│       └── elevenlabs.py        # Core implementation
├── tts_manager.py               # Unified TTS interface
├── test_tts.py                  # CLI test tool
└── README.md                    # This file
```

## 🔧 Configuration

### Deepgram
- **Voices**: aura-asteria-en, aura-luna-en, aura-stella-en, etc.
- **Format**: WAV (linear16)
- **Sample Rate**: 24000 Hz (streaming), 48000 Hz (non-streaming)

### Kokoro
- **Voices**: af_bella, af_sarah, am_adam, etc.
- **Format**: MP3
- **Sample Rate**: 24000 Hz
- **Server**: localhost:8880 (required)

### ElevenLabs
- **Voices**: rachel, sarah, adam, antoni, etc.
- **Format**: MP3
- **Sample Rate**: 22050 Hz

## 🌊 Streaming Implementation

All providers use HTTP streaming for real-time audio playback:

1. **HTTP Request**: `stream=True` to enable chunked response
2. **Real-time Playback**: Audio chunks piped to ffplay as they arrive
3. **Low Latency**: Audio starts playing before full generation completes
4. **Error Handling**: Graceful fallback if streaming fails

## 📝 Examples

### Basic Usage
```python
from services.voice import TTSManager, TTSConfig

config = TTSConfig(provider="kokoro", voice="af_bella")
tts = TTSManager(config)

# Generate and save
result = await tts.generate("Hello world!")
```

### Streaming with Playback
```python
config = TTSConfig(
    provider="deepgram",
    voice="aura-luna-en",
    use_streaming=True,
    stream_and_play=True
)
tts = TTSManager(config)

# Audio plays while generating
result = await tts.speak("This will play in real-time!")
```

### Voice Selection
```python
# Deepgram voices
voices = ["aura-asteria-en", "aura-luna-en", "aura-stella-en"]

# Kokoro voices  
voices = ["af_bella", "af_sarah", "am_adam", "am_michael"]

# ElevenLabs voices
voices = ["rachel", "sarah", "adam", "antoni"]
```

## 🐛 Troubleshooting

### Deepgram: No Audio
- Check API key: `export DEEPGRAM_API_KEY="your_key"`
- Verify account has TTS access
- Try non-streaming mode first

### Kokoro: Connection Error
- Start Kokoro server: `kokoro-api --port 8880`
- Check server is running: `curl http://localhost:8880/health`

### ElevenLabs: API Error
- Verify API key: `export ELEVENLABS_API_KEY="your_key"`
- Check character credits in ElevenLabs dashboard

### Audio Playback Issues
- Install ffplay: `sudo pacman -S ffmpeg`
- Check audio device: `aplay -l`

## 📄 License

MIT License - see LICENSE file for details.
