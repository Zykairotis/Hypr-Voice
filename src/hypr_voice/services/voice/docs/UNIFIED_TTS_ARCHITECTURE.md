# Unified TTS Architecture

## Overview

The Unified TTS System provides a consistent interface for managing multiple Text-to-Speech providers (ElevenLabs, Deepgram, Kokoro) with automatic fallback, unified configuration, and comprehensive testing infrastructure.

## Architecture Components

### 1. Base Interface Layer (`base_provider.py`)

Defines the abstract interface that all TTS providers must implement:

```python
class BaseTTSProvider(ABC):
    async def connect() -> bool
    async def disconnect() -> None
    async def stream_text(text: str) -> None
    async def flush() -> None
    async def stream_from_llm(llm_generator) -> AsyncIterator[bytes]
    def get_available_voices() -> List[Dict]
    def get_available_models() -> List[Dict]
    def set_voice(voice: str) -> None
    def set_model(model: str) -> None
    def get_stats() -> Dict
```

**Key Features:**
- Common interface for all providers
- Unified configuration with `TTSConfig`
- Standard streaming states with `StreamingState` enum
- Factory pattern with `ProviderFactory`

### 2. Provider Adapters (`unified_providers.py`)

Adapts each provider's specific implementation to the common interface:

#### ElevenLabsAdapter
- Wraps `ElevenLabsLLMStreamer`
- Converts generic config to ElevenLabs-specific config
- Maps voice names to voice IDs
- Handles WebSocket protocol

#### DeepgramAdapter
- Wraps `DeepgramLLMStreamer`
- Adapts Deepgram WebSocket implementation
- Manages Aura voice configurations
- Handles real-time streaming

#### KokoroAdapter
- Wraps `KokoroLLMStreamer`
- Adapts HTTP REST implementation
- No API key required (local)
- Free alternative provider

### 3. Unified Voice Manager (`voice_manager_unified.py`)

Central manager that orchestrates all providers:

```python
class UnifiedVoiceManager:
    def set_provider(provider: str) -> bool
    def list_providers() -> List[str]
    def list_voices(provider: str) -> List[Dict]
    def list_models(provider: str) -> List[Dict]
    def set_voice(voice: str, provider: str)
    def set_model(model: str, provider: str)
    async def connect(provider: str) -> bool
    async def stream_from_llm(generator, provider: str) -> AsyncIterator[bytes]
```

**Key Features:**
- Provider switching
- Automatic fallback on failure
- Metrics collection and saving
- Unified configuration management
- Audio file saving
- Statistics aggregation

### 4. Testing Infrastructure (`test_tts_voice/`)

Comprehensive testing suite for validation and benchmarking:

#### Interactive Test (`interactive_test.py`)
- Manual provider selection
- Voice browsing and selection
- Custom text input
- Audio generation and playback

#### Streaming Speed Test (`streaming_test.py`)
- Configurable words-per-second rates
- Performance benchmarking
- Latency measurements
- Comparison tables
- Multi-speed testing

#### Test Data
- 100-word sample text
- Audio output directory
- Metrics JSON storage

## Provider Comparison

| Feature | ElevenLabs | Deepgram | Kokoro |
|---------|------------|----------|---------|
| **Protocol** | WebSocket | WebSocket | HTTP REST |
| **Hosting** | Cloud | Cloud | Local |
| **API Key** | Required | Required | Not needed |
| **Latency** | ~75-275ms | ~50ms | Medium |
| **Quality** | Highest | High | Good |
| **Voices** | 44 | 55+ | 17 |
| **Models** | 5 | 2 | 1 |
| **Languages** | 32 | 2 | 1 |
| **Cost** | Per char | Per char | Free |
| **Fallback Priority** | 2 | 1 | 3 (default) |

## Usage Examples

### Basic Usage

```python
from services.voice import UnifiedVoiceManager, UnifiedVoiceConfig

# Initialize with config
config = UnifiedVoiceConfig(
    default_provider="elevenlabs",
    fallback_providers=["deepgram", "kokoro"],
    auto_fallback=True
)

manager = UnifiedVoiceManager(config)

# List available providers
providers = manager.list_providers()
print(f"Available: {providers}")

# Set provider and voice
manager.set_provider("elevenlabs")
manager.set_voice("rachel")

# Stream text
await manager.connect()
await manager.stream_text("Hello world!")
await manager.flush()
await manager.disconnect()
```

### LLM Integration

```python
# Stream from LLM generator
async def llm_generator():
    for word in "Hello world from LLM".split():
        yield word + " "
        await asyncio.sleep(0.1)

# Stream with auto-play
async for audio_chunk in manager.stream_from_llm(
    llm_generator(),
    auto_play=True,
    provider="elevenlabs",
    save_audio=True
):
    # Audio plays automatically
    pass
```

### With Claude Code SDK Integration

```python
from claude_code_sdk import ClaudeCodeSDK  # When available
from services.voice import UnifiedVoiceManager

manager = UnifiedVoiceManager()
claude = ClaudeCodeSDK()

# Direct streaming from Claude to TTS
async for audio in manager.stream_from_llm(
    claude.generate_response("Tell me a story"),
    provider="elevenlabs"
):
    # Real-time audio generation
    pass
```

### Testing Providers

```python
# Interactive test
cd test_tts_voice
python interactive_test.py

# Streaming speed test
python streaming_test.py
```

## Configuration

### Environment Variables

```bash
# .env file
ELEVENLABS_API_KEY=your_elevenlabs_key
DEEPGRAM_API_KEY=your_deepgram_key
# Kokoro runs locally, no key needed
```

### UnifiedVoiceConfig Options

```python
config = UnifiedVoiceConfig(
    # Provider settings
    default_provider="kokoro",          # Default TTS provider
    fallback_providers=["kokoro"],      # Fallback order
    
    # API keys
    elevenlabs_api_key="...",           # Or use env var
    deepgram_api_key="...",             # Or use env var
    
    # Default voices per provider
    default_voices={
        'elevenlabs': 'rachel',
        'deepgram': 'luna',
        'kokoro': 'af_bella'
    },
    
    # Default models per provider
    default_models={
        'elevenlabs': 'eleven_turbo_v2_5',
        'deepgram': 'aura-2',
        'kokoro': 'kokoro-v1'
    },
    
    # Features
    auto_fallback=True,                 # Auto-switch on failure
    save_metrics=True,                  # Save performance data
    
    # Audio settings
    default_speed=1.0,                  # Speech speed
    default_pitch=0.0,                  # Voice pitch
    default_volume=1.0,                 # Audio volume
    
    # Buffering
    min_buffer_size=10,                 # Min words before send
    max_buffer_size=200,                # Max buffer size
    flush_timeout=0.5,                  # Auto-flush timeout
    flush_on_punctuation=True           # Flush on sentence end
)
```

## Performance Metrics

The system automatically collects and saves metrics:

### Metrics Collected

```json
{
  "timestamp": "2024-10-29T13:45:00",
  "provider": "elevenlabs",
  "voice": "rachel",
  "model": "eleven_turbo_v2_5",
  "connect_time": 0.85,
  "first_audio_latency": 0.32,
  "total_time": 10.45,
  "audio_chunks": 45,
  "total_bytes": 128689,
  "status": "success"
}
```

### Typical Performance

| Metric | ElevenLabs | Deepgram | Kokoro |
|--------|------------|----------|---------|
| Connect Time | ~0.85s | ~0.9s | ~0.02s |
| First Audio | ~0.32s | ~0.28s | ~0.55s |
| Streaming | Real-time | Real-time | Real-time |
| 10 wps Test | ~10.45s | ~10.12s | ~10.23s |

## Auto-Fallback Mechanism

The system automatically falls back to available providers on failure:

1. **Primary attempt**: Use specified provider
2. **On failure**: Try fallback providers in order
3. **Last resort**: Use Kokoro (always available)

```python
# Example with fallback
config = UnifiedVoiceConfig(
    default_provider="elevenlabs",      # Try first
    fallback_providers=["deepgram", "kokoro"],  # Fallback order
    auto_fallback=True
)

# If ElevenLabs fails, automatically tries Deepgram, then Kokoro
```

## Best Practices

### 1. Provider Selection

- **Quality Priority**: ElevenLabs → Deepgram → Kokoro
- **Speed Priority**: Deepgram → ElevenLabs (Flash) → Kokoro
- **Cost Priority**: Kokoro → Deepgram → ElevenLabs
- **Privacy Priority**: Kokoro (local only)

### 2. Voice Selection

```python
# List voices for provider
voices = manager.list_voices("elevenlabs")
for voice in voices[:5]:
    print(f"- {voice['name']}: {voice['id']}")

# Set optimal voices
manager.set_voice("rachel", "elevenlabs")  # Professional
manager.set_voice("luna", "deepgram")      # Soothing
manager.set_voice("af_bella", "kokoro")    # Versatile
```

### 3. Model Selection

```python
# For speed (ElevenLabs)
manager.set_model("eleven_flash_v2_5", "elevenlabs")

# For quality (ElevenLabs)
manager.set_model("eleven_multilingual_v2", "elevenlabs")

# Balanced (ElevenLabs)
manager.set_model("eleven_turbo_v2_5", "elevenlabs")
```

### 4. Streaming Optimization

```python
# Fast streaming (10-15 words/second)
config.min_buffer_size = 5
config.max_buffer_size = 50
config.flush_timeout = 0.2

# Quality streaming (5-10 words/second)
config.min_buffer_size = 20
config.max_buffer_size = 200
config.flush_timeout = 1.0
```

## Troubleshooting

### No Providers Available

```python
# Check API keys
print(f"ElevenLabs key: {bool(os.environ.get('ELEVENLABS_API_KEY'))}")
print(f"Deepgram key: {bool(os.environ.get('DEEPGRAM_API_KEY'))}")

# Kokoro should always work
manager = UnifiedVoiceManager()
if "kokoro" not in manager.list_providers():
    # Check if Kokoro server is running on localhost:8880
    pass
```

### Connection Failures

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Test connection
connected = await manager.connect("elevenlabs")
if not connected:
    print("Check: API key, internet connection, service status")
```

### Audio Issues

```python
# Disable auto-play for debugging
async for chunk in manager.stream_from_llm(
    generator(),
    auto_play=False,  # Don't play audio
    save_audio=True    # Save to file instead
):
    print(f"Received {len(chunk)} bytes")
```

## Integration with Orchestrator

The unified manager integrates seamlessly with the Claude Code SDK orchestrator:

```python
from Agent.orchestrator import Orchestrator
from services.voice import UnifiedVoiceManager

# In orchestrator
self.voice_manager = UnifiedVoiceManager()

# Stream Claude responses to TTS
async def process_response(text_generator):
    async for audio in self.voice_manager.stream_from_llm(
        text_generator,
        provider="elevenlabs"
    ):
        # Audio handled automatically
        pass
```

## Future Enhancements

### Planned Features

1. **Voice Cloning** - ElevenLabs Pro+ integration
2. **Emotion Detection** - Dynamic voice modulation
3. **Multi-speaker** - Dialogue with different voices
4. **Caching Layer** - Cache repeated phrases
5. **Voice Blending** - Kokoro voice combining
6. **SSML Support** - Advanced pronunciation control

### Claude Code SDK Full Integration

When the SDK is available:
- Context-aware voice selection
- Emotion-based voice parameters
- Code pronunciation optimization
- Multi-language auto-switching

## Summary

The Unified TTS System provides:

✅ **Consistent Interface** - Same API for all providers  
✅ **Auto-Fallback** - Seamless provider switching  
✅ **Performance Metrics** - Detailed tracking  
✅ **Comprehensive Testing** - Interactive and automated  
✅ **LLM Ready** - Direct streaming integration  
✅ **Production Ready** - Error handling and logging  

The system ensures reliable TTS functionality regardless of provider availability, with Kokoro as the always-available fallback option.
