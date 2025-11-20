# Unified TTS System Architecture

## Overview

The Unified TTS System provides a clean, modular architecture for integrating multiple Text-to-Speech providers with streaming support for real-time LLM integration.

## Directory Structure

```
voice/
├── __init__.py              # Package exports and version
├── README.md               # Quick start guide
│
├── core/                   # Core system components
│   ├── base_provider.py    # Abstract base classes and interfaces
│   ├── unified_providers.py # Provider adapter implementations
│   ├── voice_manager_unified.py # Main voice manager
│   └── voice_manager.py   # Legacy manager (backward compatibility)
│
├── providers/              # TTS provider implementations
│   ├── deepgram/          # Deepgram WebSocket provider
│   │   ├── llm_streamer.py
│   │   ├── audio_player.py
│   │   ├── config/
│   │   └── ...
│   ├── elevenlabs/        # ElevenLabs WebSocket provider
│   │   ├── llm_streamer.py
│   │   ├── config/
│   │   └── ...
│   └── kokoro/            # Local Kokoro HTTP provider
│       ├── llm_streamer.py
│       ├── config/
│       └── ...
│
├── examples/              # Usage examples and demos
│   ├── example_streaming_llm.py # LLM integration examples
│   └── streaming_example.py     # Basic streaming demo
│
└── docs/                  # Documentation
    ├── README.md         # Main documentation
    ├── SETUP.md          # Installation guide
    ├── ARCHITECTURE.md   # This file
    └── ...
```

## Core Components

### 1. Base Provider (`core/base_provider.py`)

Defines the abstract interfaces that all TTS providers must implement:

```python
class BaseTTSProvider(ABC):
    """Abstract base class for TTS providers"""
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to provider"""
    
    @abstractmethod
    async def stream_text(self, text: str) -> None:
        """Stream text for TTS conversion"""
    
    @abstractmethod
    async def flush(self) -> None:
        """Flush any buffered text"""
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection"""
```

### 2. Provider Adapters (`core/unified_providers.py`)

Adapts each provider's specific implementation to the common interface:

- **KokoroAdapter**: Adapts Kokoro's HTTP API
- **DeepgramAdapter**: Adapts Deepgram's WebSocket API
- **ElevenLabsAdapter**: Adapts ElevenLabs' WebSocket API

### 3. Voice Manager (`core/voice_manager_unified.py`)

The main entry point that:
- Manages multiple providers
- Handles provider selection and fallback
- Provides unified streaming interface
- Manages audio playback
- Tracks metrics and statistics

## Provider Implementations

### Kokoro (Local, Free)
- **Protocol**: HTTP REST API
- **Location**: `providers/kokoro/`
- **Features**: 
  - No API key required
  - 17 voices
  - Voice combining
  - Word-level timestamps
- **Best for**: Development, privacy-focused applications

### Deepgram (Cloud, WebSocket)
- **Protocol**: WebSocket streaming
- **Location**: `providers/deepgram/`
- **Features**:
  - Low latency (~50ms)
  - 55+ voices
  - Real-time streaming
  - High quality
- **Best for**: Production applications, real-time streaming

### ElevenLabs (Premium Cloud)
- **Protocol**: WebSocket streaming
- **Location**: `providers/elevenlabs/`
- **Features**:
  - Highest quality
  - 44 voices
  - 5 models
  - 32 languages
  - Voice cloning (Pro+)
- **Best for**: Premium applications, content creation

## Data Flow

### 1. Text Input Flow
```
User Text → Voice Manager → Provider Adapter → Provider Implementation → TTS API
```

### 2. Audio Output Flow
```
TTS API → Provider Implementation → Audio Queue → Audio Player → Speakers
```

### 3. LLM Streaming Flow
```
LLM Generator → Text Buffer → Flush Logic → TTS Stream → Audio Chunks → Auto-play
```

## Key Design Patterns

### 1. Adapter Pattern
Each provider has an adapter that converts its specific API to the common interface.

### 2. Factory Pattern
`ProviderFactory` creates the appropriate provider instance based on configuration.

### 3. Strategy Pattern
Different buffering and flushing strategies based on use case (quality vs latency).

### 4. Observer Pattern
Callbacks for audio chunks, text processing, and errors.

## Configuration System

### Unified Configuration
```python
config = UnifiedVoiceConfig(
    default_provider=VoiceProvider.KOKORO,
    voice="af_bella",
    min_buffer_size=10,
    max_buffer_size=100,
    flush_timeout=0.5,
    punctuation_flush=True
)
```

### Provider-Specific Settings
Each provider can have specific settings while maintaining the unified interface:

```python
# Deepgram specific
config.sample_rate = 48000
config.encoding = "linear16"

# ElevenLabs specific
config.model = "eleven_turbo_v2_5"
config.optimize_streaming_latency = 3
```

## Audio Playback

### Supported Backends
1. **sounddevice** (preferred for raw PCM)
2. **pydub + simpleaudio** (for MP3/compressed audio)
3. **pyaudio** (fallback)

### Audio Flow
1. Provider generates audio chunks
2. Chunks queued in thread-safe queue
3. Audio player consumes queue
4. Direct playback to system audio

## Streaming & Buffering

### Text Buffering Strategy
- **Minimum buffer**: Start generating audio
- **Maximum buffer**: Force flush
- **Punctuation flush**: Flush on sentence boundaries
- **Timeout flush**: Flush after inactivity

### LLM Integration
```python
async for text_chunk in llm_generator:
    buffer.add(text_chunk)
    if should_flush():
        await provider.stream_text(buffer.get())
        buffer.clear()
```

## Error Handling

### Provider Fallback
```python
providers = [primary, fallback1, fallback2]
for provider in providers:
    try:
        await provider.connect()
        break
    except:
        continue
```

### Connection Recovery
- Automatic reconnection on disconnect
- Exponential backoff for retries
- Circuit breaker pattern for failing providers

## Performance Considerations

### Latency Optimization
- Small buffers (5-20 chars)
- Fast flush timeout (0.2-0.5s)
- Punctuation-based flushing
- WebSocket providers (Deepgram/ElevenLabs)

### Quality Optimization
- Large buffers (50-200 chars)
- Slow flush timeout (1-2s)
- Context-aware buffering
- Premium providers (ElevenLabs)

## Security

### API Key Management
- Environment variables for keys
- Never hardcode keys
- Separate keys per environment

### Data Privacy
- Kokoro for local-only processing
- No data leaves machine with Kokoro
- Cloud providers have their own policies

## Future Enhancements

### Planned Features
1. **Claude Code SDK Integration**
   - Context-aware voice selection
   - Emotion detection
   - Code pronunciation rules

2. **Advanced Audio Processing**
   - Real-time effects
   - Volume normalization
   - Noise reduction

3. **Multi-language Support**
   - Language detection
   - Auto voice selection
   - Translation integration

4. **Caching System**
   - Response caching
   - Offline mode
   - Bandwidth optimization
