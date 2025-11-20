# Unified TTS System Setup Guide
## For Arch Linux + Hyprland

## System Requirements
- Arch Linux with Hyprland
- Python 3.8+
- PipeWire audio system (standard on modern Arch)
- Internet connection for cloud providers

## Installation

### 1. System Dependencies
```bash
# Core audio libraries
sudo pacman -S python python-pip portaudio ffmpeg pipewire pipewire-pulse

# Optional: For better audio handling
sudo pacman -S pipewire-alsa pipewire-jack
```

### 2. Python Dependencies
```bash
# Core dependencies
pip install --upgrade pip
pip install websockets aiohttp pyyaml sounddevice numpy pydub

# Provider SDKs (optional, for advanced features)
pip install openai anthropic

# Development tools (optional)
pip install pytest pytest-asyncio ipython
```

### 3. Kokoro Server Setup (Local TTS)
```bash
# Clone Kokoro if not already installed
git clone https://github.com/remsky/Kokoro-FastAPI.git
cd Kokoro-FastAPI

# Install Kokoro dependencies
pip install -r requirements.txt

# Start the server
python server.py --host 0.0.0.0 --port 8880
```

### 4. API Keys Configuration
Create a `.env` file in your project root:

```bash
# Cloud provider API keys
export DEEPGRAM_API_KEY="your_deepgram_key_here"
export ELEVENLABS_API_KEY="your_elevenlabs_key_here"

# Optional: For LLM integration
export OPENAI_API_KEY="your_openai_key_here"
export ANTHROPIC_API_KEY="your_anthropic_key_here"
```

Load the environment:
```bash
source .env
```

## Quick Test

### 1. Test Individual Providers
```python
# Test Kokoro (local, no API key needed)
from providers.kokoro.llm_streamer import KokoroLLMStreamer

async def test_kokoro():
    streamer = KokoroLLMStreamer()
    await streamer.connect()
    await streamer.stream_text("Hello world!")
    await streamer.flush()
    await streamer.disconnect()

# Run test
import asyncio
asyncio.run(test_kokoro())
```

### 2. Test Unified System
```python
from core.voice_manager import UnifiedVoiceManager
from core.base_provider import VoiceProvider, UnifiedVoiceConfig

async def test_unified():
    config = UnifiedVoiceConfig(
        default_provider=VoiceProvider.KOKORO
    )
    manager = UnifiedVoiceManager(config)
    
    await manager.connect()
    await manager.stream_text("Testing unified TTS system")
    await manager.disconnect()

asyncio.run(test_unified())
```

## Audio Configuration

### PipeWire Setup (Arch Linux)
```bash
# Check PipeWire status
systemctl --user status pipewire pipewire-pulse

# Restart if needed
systemctl --user restart pipewire pipewire-pulse

# Set default audio device
pactl info | grep "Default Sink"
```

### Troubleshooting Audio

#### No Sound?
```bash
# Check volume
pamixer --get-volume
pamixer --set-volume 75

# List audio devices
pactl list short sinks
```

#### Crackling/Distortion?
```bash
# Adjust buffer size in PipeWire
mkdir -p ~/.config/pipewire
cp /usr/share/pipewire/pipewire.conf ~/.config/pipewire/
# Edit ~/.config/pipewire/pipewire.conf
# Set: default.clock.min-quantum = 1024
```

## Provider-Specific Notes

### Kokoro (Local)
- **Pros**: Free, private, no rate limits
- **Cons**: Requires local server, moderate quality
- **Best for**: Development, testing, privacy-focused apps

### Deepgram
- **Pros**: Fast, good quality, WebSocket streaming
- **Cons**: Costs money, requires API key
- **Best for**: Production apps, real-time streaming

### ElevenLabs
- **Pros**: Best quality, natural voices, emotion control
- **Cons**: Most expensive, API limits
- **Best for**: Premium applications, content creation

## Common Issues & Solutions

### 1. "Connection refused" for Kokoro
```bash
# Ensure Kokoro server is running
cd Kokoro-FastAPI && python server.py --host 0.0.0.0 --port 8880
```

### 2. "Invalid API key" for cloud providers
```bash
# Check your .env file
cat .env | grep API_KEY

# Ensure environment is loaded
source .env
echo $DEEPGRAM_API_KEY
```

### 3. "No audio device found"
```bash
# Install audio libraries
sudo pacman -S portaudio
pip install sounddevice --upgrade
```

### 4. Import errors
```bash
# Fix Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/voice/directory"
```

## Performance Optimization

### For Real-Time Streaming
```python
config = UnifiedVoiceConfig(
    min_buffer_size=5,      # Smaller buffer for lower latency
    max_buffer_size=50,     
    flush_timeout=0.3,      # Faster flushing
    punctuation_flush=True  # Flush on punctuation
)
```

### For Quality
```python
config = UnifiedVoiceConfig(
    min_buffer_size=20,     # Larger buffer for context
    max_buffer_size=200,
    flush_timeout=1.0,      # Wait for more text
    punctuation_flush=False # Don't break on punctuation
)
```

## Next Steps

1. Try the example scripts in `/examples/`
2. Read the architecture documentation in `/docs/ARCHITECTURE.md`
3. Integrate with your application
4. Customize voice settings per provider

## Support

- Kokoro Issues: https://github.com/remsky/Kokoro-FastAPI/issues
- Deepgram Docs: https://developers.deepgram.com/
- ElevenLabs Docs: https://docs.elevenlabs.io/
