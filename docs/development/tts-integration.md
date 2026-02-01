# TTS Integration Guide

## Overview

Hypr-Voice supports multiple Text-to-Speech (TTS) providers through a unified interface:
- **Kokoro** - Local/open-source TTS server
- **Deepgram** - Cloud-based Aura voices
- **ElevenLabs** - Premium cloud TTS

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   UniversalTTS Manager                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Kokoro     │  │  Deepgram    │  │  ElevenLabs      │  │
│  │   (Local)    │  │  (Cloud)     │  │  (Cloud)         │  │
│  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘  │
│         │                 │                   │              │
│         └─────────────────┴───────────────────┘              │
│                           │                                  │
│                    ┌──────▼───────┐                          │
│                    │ Voice Library│                          │
│                    │ & Config     │                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│                    ┌──────▼───────┐                          │
│                    │ TTS Manager  │                          │
│                    └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Deepgram (https://deepgram.com)
DEEPGRAM_API_KEY=your_deepgram_key_here

# ElevenLabs (https://elevenlabs.io)
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Kokoro (local server)
KOKORO_URL=http://localhost:8880
```

### Python Installation

```bash
# Core TTS support (included)
pip install aiohttp requests

# Optional: For audio playback
pip install pygame

# System requirements for audio playback
# Ubuntu/Debian: sudo apt-get install ffmpeg
```

### Kokoro Local Server Setup

```bash
# Using Docker (recommended)
docker run -d \
  -p 8880:8880 \
  --name kokoro-tts \
  ghcr.io/remsky/Kokoro-FastAPI:latest

# Or using local installation
git clone https://github.com/remsky/Kokoro-FastAPI
cd Kokoro-FastAPI
python -m pip install -r requirements.txt
python -m kokoro_fastapi.server --port 8880
```

## Usage

### Basic TTS

```python
from hypr_voice.services.voice import UniversalTTS, TTSConfig, TTSProvider

async def basic_tts():
    # Create config
    config = TTSConfig(
        provider=TTSProvider.KOKORO,
        voice="af_bella",
        speed=1.0
    )

    # Initialize TTS
    tts = UniversalTTS(config)

    # Generate speech
    result = await tts.speak("Hello, world!")

    if result['success']:
        print(f"Audio saved to: {result['audio_file']}")
        print(f"Duration: {result.get('duration')}s")
```

### Using Convenience Function

```python
from hypr_voice.services.voice import text_to_speech

result = await text_to_speech(
    text="Hello from Hypr-Voice!",
    provider="kokoro",
    voice="af_bella"
)
```

### Provider-Specific Examples

#### Kokoro (Local)

```python
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    voice="af_bella",  # Female voice
    speed=1.0,
    sample_rate=24000,
    use_streaming=True,
    stream_and_play=True  # Play while generating
)

tts = UniversalTTS(config)
result = await tts.speak("This is Kokoro TTS")
```

#### Deepgram (Cloud)

```python
config = TTSConfig(
    provider=TTSProvider.DEEPGRAM,
    voice="aura-asteria-en",  # Aura voice
    deepgram_api_key=os.getenv("DEEPGRAM_API_KEY"),
    use_streaming=True,
    stream_and_play=False
)

tts = UniversalTTS(config)
result = await tts.speak("This is Deepgram Aura")
```

#### ElevenLabs (Cloud)

```python
config = TTSConfig(
    provider=TTSProvider.ELEVENLABS,
    voice="rachel",
    model="eleven_turbo_v2_5",
    elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY"),
    sample_rate=44100
)

tts = UniversalTTS(config)
result = await tts.speak("This is ElevenLabs")
```

### Streaming with Auto-Play

```python
# Fastest perceived latency
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    voice="af_bella",
    use_streaming=True,
    stream_and_play=True  # Play while streaming
)

tts = UniversalTTS(config)
result = await tts.speak("This will play almost immediately!")
```

### Random Voice Selection

```python
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    use_random_voice=True,
    voice_gender="female",  # "male", "female", or None
    voice_accent="american"  # "american", "british", or None
)

tts = UniversalTTS(config)
result = await tts.speak("Random voice selected!")
```

## Available Voices

### Kokoro Voices

**Female**:
- `af_bella` - Bella (American female)
- `af_sarah` - Sarah (American female)
- `af_sky` - Sky (American female)
- `af_nicole` - Nicole (American female)
- `af_heart` - Heart (American female)
- `af_nova` - Nova (American female)

**Male**:
- `am_adam` - Adam (American male)
- `am_michael` - Michael (American male)
- `am_echo` - Echo (American male)

**British**:
- `bf_emma` - Emma (British female)
- `bf_alice` - Alice (British female)
- `bm_george` - George (British male)
- `bm_lewis` - Lewis (British male)

**Special**:
- `am_santa` - Santa Claus
- `pm_santa` - Santa Claus (pitch-modified)

### Deepgram Aura Voices

**Female** (Aura-2):
- `aura-asteria-en` - Asteria
- `aura-athena-en` - Athena
- `aura-aurora-en` - Aurora
- `aura-cora-en` - Cora
- `aura-luna-en` - Luna
- `aura-stella-en` - Stella

**Male** (Aura-2):
- `apollo-en` - Apollo
- `arcas-en` - Arcas
- `orion-en` - Orion
- `perseus-en` - Perseus
- `zeus-en` - Zeus

**Full List**:
```python
from hypr_voice.services.voice.tts_manager import VoiceLibrary

# All 44 Aura-2 voices
voices = VoiceLibrary.DEEPGRAM_VOICES['all']
print(voices)
```

### ElevenLabs Voices

**Female**:
- `rachel` - Rachel (default)
- `sarah` - Sarah
- `emily` - Emily
- `lily` - Lily
- `jessica` - Jessica
- `freya` - Freya
- `alice` - Alice
- `charlotte` - Charlotte

**Male**:
- `adam` - Adam
- `antoni` - Antoni
- `arnold` - Arnold
- `bill` - Bill
- `brian` - Brian
- `callum` - Callum
- `charlie` - Charlie
- `daniel` - Daniel

## TTSConfig Options

### Configuration Parameters

```python
from hypr_voice.services.voice import TTSConfig, TTSProvider

config = TTSConfig(
    # Provider settings
    provider=TTSProvider.KOKORO,

    # Voice settings
    voice="af_bella",
    model=None,  # Provider-specific model
    use_random_voice=False,
    voice_gender=None,  # "male", "female", or None
    voice_accent=None,  # "american", "british", or None

    # Audio parameters
    speed=1.0,  # 0.5 to 2.0
    pitch=0.0,  # -20.0 to 20.0
    volume=1.0,  # 0.0 to 2.0
    sample_rate=48000,  # Hz
    output_format="mp3",  # "mp3", "wav", "pcm"

    # API settings
    kokoro_url="http://localhost:8880",
    deepgram_api_key=None,  # Loads from DEEPGRAM_API_KEY env
    elevenlabs_api_key=None,  # Loads from ELEVENLABS_API_KEY env

    # Output settings
    save_to_file=True,
    output_dir="./audio_output",
    filename=None,  # Auto-generate if None

    # Streaming settings
    use_streaming=True,
    stream_and_play=False  # Play while streaming
)
```

## Advanced Usage

### Dynamic Voice Switching

```python
tts = UniversalTTS(TTSConfig(provider=TTSProvider.KOKORO))

# Use different voices
voices = ["af_bella", "af_sarah", "am_adam"]
for voice in voices:
    result = await tts.speak(
        f"Hello from {voice}",
        voice=voice
    )
```

### Provider Comparison

```python
async def compare_providers(text):
    providers = [
        TTSProvider.KOKORO,
        TTSProvider.DEEPGRAM,
        TTSProvider.ELEVENLABS
    ]

    results = {}
    for provider in providers:
        config = TTSConfig(provider=provider)
        tts = UniversalTTS(config)
        result = await tts.speak(text)
        results[provider.value] = result

    return results
```

### Batch Processing

```python
async def batch_tts(texts):
    config = TTSConfig(
        provider=TTSProvider.KOKORO,
        use_streaming=False  # Better for batch
    )

    tts = UniversalTTS(config)

    results = []
    for i, text in enumerate(texts):
        result = await tts.speak(
            text,
            filename=f"batch_{i:03d}.mp3"
        )
        results.append(result)

    return results
```

### Voice Library Queries

```python
from hypr_voice.services.voice.tts_manager import (
    VoiceLibrary,
    list_all_voices,
    list_all_models
)

# List all voices
all_voices = list_all_voices()
print("Kokoro:", all_voices['kokoro'])
print("Deepgram:", all_voices['deepgram'])
print("ElevenLabs:", all_voices['elevenlabs'])

# List all models
all_models = list_all_models()
print("Deepgram models:", all_models['deepgram'])
print("ElevenLabs models:", all_models['elevenlabs'])

# Get random voice
voice = VoiceLibrary.get_random_voice(
    TTSProvider.KOKORO,
    gender="female",
    accent="british"
)
```

## Troubleshooting

### Kokoro Server Not Running

**Error**: `Cannot connect to Kokoro server`

**Solution**:
```bash
# Start Kokoro server
docker run -d -p 8880:8880 ghcr.io/remsky/Kokoro-FastAPI:latest

# Or check if running
curl http://localhost:8880/health
```

### Deepgram API Key Invalid

**Error**: `Deepgram API error: 401`

**Solution**:
```bash
# Set valid API key
export DEEPGRAM_API_KEY=your_valid_key

# Or pass directly
config = TTSConfig(
    provider=TTSProvider.DEEPGRAM,
    deepgram_api_key="your_valid_key"
)
```

### ElevenLabs Quota Exceeded

**Error**: `ElevenLabs API error: 429`

**Solution**:
- Check your quota at https://elevenlabs.io/app/settings/account
- Reduce usage or upgrade plan
- Implement rate limiting

### Audio Playback Issues

**Error**: `ffplay not found`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Or disable auto-play
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    stream_and_play=False
)
```

### Streaming Not Working

**Error**: `Streaming failed`

**Solution**:
```python
# Disable streaming for debugging
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    use_streaming=False,
    stream_and_play=False
)
```

## Performance Optimization

### For Low Latency

```python
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    use_streaming=True,
    stream_and_play=True,  # Play while generating
    sample_rate=24000,  # Lower sample rate
    output_format="mp3"  # Faster encoding
)
```

### For High Quality

```python
config = TTSConfig(
    provider=TTSProvider.ELEVENLABS,
    voice="rachel",
    model="eleven_multilingual_v2",
    sample_rate=48000,
    speed=1.0,
    output_format="wav"  # Lossless
)
```

### For Batch Processing

```python
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    use_streaming=False,  # Disable streaming
    save_to_file=True,
    output_dir="./batch_output"
)
```

## Best Practices

### 1. Choose the Right Provider

- **Kokoro**: Low latency, no API costs, requires local server
- **Deepgram**: Fast cloud API, good quality, reasonable pricing
- **ElevenLabs**: Best quality, higher latency, more expensive

### 2. Handle Errors Gracefully

```python
result = await tts.speak("...")

if not result['success']:
    error = result.get('error', 'Unknown error')
    logger.error(f"TTS failed: {error}")

    # Fallback to different provider
    if 'Kokoro' in error:
        fallback_tts = UniversalTTS(
            TTSConfig(provider=TTSProvider.DEEPGRAM)
        )
        result = await fallback_tts.speak("...")
```

### 3. Monitor Resource Usage

```python
import psutil
import os

def check_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.2f} MB")
```

### 4. Use Streaming for Long Text

```python
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    use_streaming=True,
    stream_and_play=True
)

# Better for long texts
long_text = "..." * 1000
result = await tts.speak(long_text)
```

### 5. Implement Caching

```python
import hashlib
from pathlib import Path

async def cached_tts(tts, text):
    # Create cache key from text
    cache_key = hashlib.md5(text.encode()).hexdigest()
    cache_file = Path(f"./tts_cache/{cache_key}.mp3")

    # Return cached if exists
    if cache_file.exists():
        return {
            'success': True,
            'audio_file': str(cache_file)
        }

    # Generate and cache
    result = await tts.speak(text)
    if result['success'] and result.get('audio_file'):
        cache_file.parent.mkdir(exist_ok=True)
        Path(result['audio_file']).rename(cache_file)
        result['audio_file'] = str(cache_file)

    return result
```

## Integration Examples

### With Claude AI

```python
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

async def claude_with_tts():
    agent = ClaudeTTSAgent(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        enable_tts=True,
        tts_provider="kokoro",
        tts_voice="af_bella"
    )

    await agent.connect()

    result = await agent.chat(
        "Tell me a short story",
        synthesize_response=True
    )

    if result['tts_synthesized']:
        print(f"Audio: {result['audio_file']}")
```

### With Wispr Flow

```python
async def voice_assistant_pipeline(audio_path):
    from hypr_voice.services.wispr_flow_direct import WisprFlowDirect
    from hypr_voice.services.voice import UniversalTTS, TTSConfig, TTSProvider

    # Transcribe
    wispr = WisprFlowDirect()
    transcription = await wispr.transcribe(audio_path)

    # Generate response (using your logic here)
    response_text = generate_response(transcription['text'])

    # Synthesize
    tts = UniversalTTS(TTSConfig(
        provider=TTSProvider.KOKORO,
        use_streaming=True,
        stream_and_play=True
    ))

    result = await tts.speak(response_text)
    return result
```

### With Discord Bot

```python
from hypr_voice.services.tools.discord_tool import DiscordClient

async def discord_tts(channel_id, text):
    discord = DiscordClient()
    await discord.initialize()

    tts = UniversalTTS(TTSConfig(
        provider=TTSProvider.DEEPGRAM,
        voice="aura-asteria-en"
    ))

    result = await tts.speak(text)

    if result['success']:
        await discord.send_file(
            channel_id,
            result['audio_file'],
            content="Here's your message"
        )
```

## API Reference

### UniversalTTS

**Constructor**:
- `config (TTSConfig)`: Configuration object

**Methods**:
- `async speak(text, **kwargs)`: Convert text to speech
- `list_voices()`: List available voices for current provider
- `list_models()`: List available models for current provider
- `static list_providers()`: List all providers
- `static list_all_voices()`: List all voices for all providers
- `static list_all_models()`: List all models for all providers

### TTSConfig

**Dataclass Fields**:
- `provider (TTSProvider)`: TTS provider to use
- `voice (str, optional)`: Voice name
- `model (str, optional)`: Model name
- `speed (float)`: Speech speed (default: 1.0)
- `pitch (float)`: Voice pitch (default: 0.0)
- `volume (float)`: Audio volume (default: 1.0)
- `sample_rate (int)`: Sample rate in Hz (default: 48000)
- `output_format (str)`: Audio format (default: "mp3")
- `use_random_voice (bool)`: Use random voice (default: False)
- `voice_gender (str, optional)`: Voice gender preference
- `voice_accent (str, optional)`: Voice accent preference
- `kokoro_url (str)`: Kokoro server URL (default: "http://localhost:8880")
- `deepgram_api_key (str, optional)`: Deepgram API key
- `elevenlabs_api_key (str, optional)`: ElevenLabs API key
- `save_to_file (bool)`: Save to file (default: True)
- `output_dir (str)`: Output directory (default: "./audio_output")
- `filename (str, optional)`: Output filename
- `use_streaming (bool)`: Enable streaming (default: True)
- `stream_and_play (bool)`: Play while streaming (default: False)

### TTSProvider

**Enum Values**:
- `TTSProvider.KOKORO`
- `TTSProvider.DEEPGRAM`
- `TTSProvider.ELEVENLABS`

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [Wispr Flow API](../api/wispr-flow-api.md)
- [Bot Integrations](./bot-integrations.md)
- [Architecture Overview](./ARCHITECTURE.md)
