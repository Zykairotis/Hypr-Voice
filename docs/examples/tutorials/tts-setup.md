# Tutorial: TTS Setup Guide

Learn how to set up and use text-to-speech in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Step 1: Provider Selection](#step-1-provider-selection)
- [Step 2: Kokoro Setup (Free)](#step-2-kokoro-setup-free)
- [Step 3: Deepgram Setup](#step-3-deepgram-setup)
- [Step 4: ElevenLabs Setup](#step-4-elevenlabs-setup)
- [Step 5: Basic Usage](#step-5-basic-usage)
- [Step 6: Advanced Configuration](#step-6-advanced-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

Hypr-Voice supports three TTS providers:

| Provider | Type | Cost | Quality | Latency | Setup Difficulty |
|----------|------|------|---------|---------|------------------|
| **Kokoro** | Local | Free | Good | Low (~50ms) | Easy |
| **Deepgram** | Cloud | Paid | Very Good | Low (~100ms) | Easy |
| **ElevenLabs** | Cloud | Paid | Excellent | Medium (~200ms) | Easy |

### Recommendation

- **Start with Kokoro** - Free, fast, no API key needed
- **Add Deepgram** for production - Low latency, natural sounding
- **Add ElevenLabs** for premium quality - Best quality available

---

## Step 1: Provider Selection

### Choose Your Provider(s)

```bash
# For development/testing
# Use Kokoro (free, local)

# For production
# Use Deepgram (low latency) or ElevenLabs (best quality)

# For redundancy
# Configure multiple providers with automatic fallback
```

### Configuration

Edit `/home/mewtwo/Zykairotis/Hypr-Voice/config/hypr_voice/config.yaml`:

```yaml
voice:
  default_provider: "kokoro"     # Primary provider
  fallback_provider: "deepgram"  # Backup if primary fails
  auto_fallback: true            # Enable automatic fallback
```

---

## Step 2: Kokoro Setup (Free)

Kokoro is a free, local TTS engine that requires no API keys.

### Installation

```bash
# Install Kokoro dependencies
pip install kokoro-onnx

# Install phonemizer (required)
pip install phonemizer

# Install espeak-ng (for phonemizer)
# Ubuntu/Debian:
sudo apt-get install espeak-ng

# Fedora:
sudo dnf install espeak-ng

# Arch:
sudo pacman -S espeak-ng
```

### Verify Installation

```bash
# Test Kokoro installation
python -c "from hypr_voice.services.voice.providers.kokoro.kokoro import VoiceManager; print('Kokoro installed!')"
```

### Configuration

```yaml
voice:
  kokoro:
    enabled: true
    default_voice: "af_bella"     # See voice options below
    cache_enabled: true
    cache_dir: "/tmp/kokoro_cache"
    sample_rate: 24000
    phonemizer: "espeak"          # espeak or gruut
```

### Available Voices

| Voice ID | Gender | Style | Best For |
|----------|--------|-------|----------|
| `af_bella` | Female | Neutral | **Default** - All-purpose |
| `af_sky` | Female | Energetic | Cheerful content |
| `af_sarah` | Female | Warm | Friendly, conversational |
| `am_adam` | Male | Professional | Technical content |
| `am_michael` | Male | Calm | Relaxed narration |
| `bf_emma` | Female | Bright | Clear articulation |
| `bm_george` | Male | Narrator | Storytelling |

### Basic Usage

```python
import asyncio
from hypr_voice.services.voice.tts_manager import VoiceManager

async def main():
    manager = VoiceManager()

    # Synthesize speech
    audio_file = await manager.synthesize(
        text="Hello, world!",
        provider="kokoro",
        voice="af_bella"
    )

    print(f"Audio saved to: {audio_file}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 3: Deepgram Setup

Deepgram offers fast, natural-sounding TTS with low latency.

### Get API Key

1. Go to https://deepgram.com
2. Sign up for an account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

### Configure Environment Variable

```bash
# Add to .env file
echo "DEEPGRAM_API_KEY=your_deepgram_key_here" >> .env
```

### Configuration

```yaml
voice:
  deepgram:
    enabled: true
    api_key: "${DEEPGRAM_API_KEY}"
    default_voice: "asteria"      # See voice options below
    language: "en"
    sample_rate: 24000
    encoding: "mp3"               # mp3, wav, pcm, opus, flac
    cache_enabled: true
    cache_dir: "/tmp/deepgram_cache"
```

### Available Voices

| Voice ID | Gender | Style | Best For |
|----------|--------|-------|----------|
| `asteria` | Female | Professional | **Default** - All-purpose |
| `luna` | Female | Friendly | Conversational |
| `orion` | Male | Authoritative | Professional content |
| `stella` | Female | Energetic | Dynamic content |
| `nova` | Female | Calm | Soothing content |

### Basic Usage

```python
import asyncio
from hypr_voice.services.voice.tts_manager import VoiceManager

async def main():
    manager = VoiceManager()

    # Synthesize speech
    audio_file = await manager.synthesize(
        text="Hello from Deepgram!",
        provider="deepgram",
        voice="asteria"
    )

    print(f"Audio saved to: {audio_file}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 4: ElevenLabs Setup

ElevenLabs offers the highest quality TTS with excellent naturalness.

### Get API Key

1. Go to https://elevenlabs.io
2. Sign up for an account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

### Configure Environment Variable

```bash
# Add to .env file
echo "ELEVENLABS_API_KEY=your_elevenlabs_key_here" >> .env
```

### Configuration

```yaml
voice:
  elevenlabs:
    enabled: true
    api_key: "${ELEVENLABS_API_KEY}"
    default_voice: "rachel"       # See voice options below
    model: "eleven_multilingual_v2"  # See model options below
    output_format: "mp3_44100_128"
    stability: 0.5                # 0.0 - 1.0
    similarity_boost: 0.5         # 0.0 - 1.0
    style: 0.0                    # 0.0 - 1.0
    use_speaker_boost: true
    cache_enabled: true
    cache_dir: "/tmp/elevenlabs_cache"
```

### Available Models

| Model | Quality | Speed | Languages | Best For |
|-------|---------|-------|-----------|----------|
| `eleven_multilingual_v2` | Best | Medium | 29 | **Recommended** |
| `eleven_turbo_v2_5` | Good | Fast | 29 | Low latency |
| `eleven_flash_v2_5` | Good | Fastest | 29 | Real-time |

### Popular Voices

| Voice ID | Gender | Style | Best For |
|----------|--------|-------|----------|
| `rachel` | Female | Professional | **Default** - All-purpose |
| `bella` | Female | Friendly | Conversational |
| `eleven` | Male | Authoritative | Professional |
| `sam` | Male | Calm | Narration |
| `charlie` | Male | Energetic | Dynamic content |

### Basic Usage

```python
import asyncio
from hypr_voice.services.voice.tts_manager import VoiceManager

async def main():
    manager = VoiceManager()

    # Synthesize speech
    audio_file = await manager.synthesize(
        text="Hello from ElevenLabs!",
        provider="elevenlabs",
        voice="rachel"
    )

    print(f"Audio saved to: {audio_file}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 5: Basic Usage

### Simple TTS

```python
from hypr_voice.services.voice.tts_manager import VoiceManager

async def simple_tts():
    manager = VoiceManager()

    # Use default provider
    audio = await manager.synthesize(
        text="Hello, world!"
    )

    print(f"Audio: {audio}")
```

### With Custom Voice

```python
async def custom_voice_tts():
    manager = VoiceManager()

    # Specify provider and voice
    audio = await manager.synthesize(
        text="This uses a custom voice",
        provider="kokoro",
        voice="af_sky"
    )

    print(f"Audio: {audio}")
```

### Stream TTS

```python
async def stream_tts():
    manager = VoiceManager()

    text = "This is a long text that will be streamed..."

    async for chunk in manager.synthesize_stream(
        text=text,
        provider="kokoro",
        voice="af_bella"
    ):
        # Process each audio chunk
        await process_chunk(chunk)
```

### Voice Presets

```python
async def preset_tts():
    manager = VoiceManager()

    # Use predefined preset
    audio = await manager.synthesize(
        text="Welcome to our meeting",
        preset="professional"  # professional, friendly, technical, narrator
    )

    print(f"Audio: {audio}")
```

---

## Step 6: Advanced Configuration

### Voice Presets

Define custom voice presets in `config.yaml`:

```yaml
voice:
  presets:
    professional:
      kokoro: {voice: "af_bella", speed: 1.0, pitch: 1.0}
      elevenlabs: {voice: "rachel", stability: 0.7, similarity_boost: 0.7}
      deepgram: {voice: "asteria", speaking_rate: 1.0}

    friendly:
      kokoro: {voice: "af_sky", speed: 1.1, pitch: 1.1}
      elevenlabs: {voice: "bella", stability: 0.5, similarity_boost: 0.8}
      deepgram: {voice: "luna", speaking_rate: 1.1}
```

### Custom Voice Configuration

```python
from hypr_voice.services.voice.providers.kokoro.kokoro import KokoroConfig, KokoroVoice

async def custom_voice():
    manager = VoiceManager()

    # Register custom voice
    manager.register_voice(
        "my_custom_voice",
        KokoroConfig(
            voice=KokoroVoice.AF_BELLA,
            speed=1.2,
            pitch=1.1,
            emotion="happy"
        )
    )

    # Use custom voice
    audio = await manager.synthesize_with_voice(
        text="Happy to help!",
        voice_name="my_custom_voice"
    )
```

### Streaming Configuration

```yaml
# Environment variables or config.yaml
tts:
  streaming:
    enabled: true
    prebuffer_ms: 800            # Prebuffer duration
    min_chars: 100               # Min chars for streaming
    max_latency: 0.5             # Max latency (seconds)
    flush_timeout: 15            # Flush timeout (seconds)
    idle_timeout: 3.0            # Idle timeout (seconds)
```

---

## Troubleshooting

### Kokoro Issues

#### Issue: Phonemizer not found

```bash
# Error: phonemizer not found

# Solution: Install phonemizer
pip install phonemizer

# Install espeak-ng
sudo apt-get install espeak-ng
```

#### Issue: Voice not found

```bash
# Error: Voice 'xyz' not found

# Solution: Check available voices
python -c "from hypr_voice.services.voice.providers.kokoro.kokoro import KokoroVoice; print(dir(KokoroVoice))"
```

### Deepgram Issues

#### Issue: Invalid API key

```bash
# Error: Invalid API key

# Solution: Verify API key
echo $DEEPGRAM_API_KEY

# Re-add to .env
echo "DEEPGRAM_API_KEY=your_correct_key" >> .env
```

#### Issue: Rate limit exceeded

```bash
# Error: Rate limit exceeded

# Solution: Wait or upgrade plan
# Implement caching to reduce API calls
```

### ElevenLabs Issues

#### Issue: Quota exceeded

```bash
# Error: Quota exceeded

# Solution: Check usage at elevenlabs.io
# Wait for quota reset or upgrade plan
```

#### Issue: Voice not available

```bash
# Error: Voice not available

# Solution: Check available voices in your account
# Use a different voice
```

### General Issues

#### Issue: Audio not playing

```bash
# Solution: Check audio output
# Test with aplay
aplay /tmp/test.wav

# Check PulseAudio
pactl list sinks short
```

#### Issue: Poor audio quality

```bash
# Solution: Adjust sample rate
# In config.yaml:
voice:
  kokoro:
    sample_rate: 24000  # Try 22050 or 44100

# Or adjust encoding
voice:
  deepgram:
    encoding: "wav"  # Try wav instead of mp3
```

---

## Performance Tips

### For Low Latency

```yaml
# Use Kokoro (fastest)
voice:
  default_provider: "kokoro"

# Reduce prebuffer
tts:
  streaming:
    prebuffer_ms: 300
    min_chars: 50
```

### For Best Quality

```yaml
# Use ElevenLabs
voice:
  default_provider: "elevenlabs"

# Increase sample rate
voice:
  elevenlabs:
    output_format: "wav_44100_128"  # Lossless
```

### For Cost Efficiency

```yaml
# Enable caching
voice:
  kokoro:
    cache_enabled: true
  deepgram:
    cache_enabled: true
  elevenlabs:
    cache_enabled: true

# Use fallback
voice:
  default_provider: "kokoro"      # Free first
  fallback_provider: "deepgram"   # Paid backup
```

---

## Next Steps

Now that TTS is set up:

- [Basic Usage Examples](../basic-usage.md) - More TTS examples
- [Voice Configuration](../../development/voice-config.md) - Detailed config
- [Whisper Setup Tutorial](whisper-setup.md) - Add speech-to-text
- [Voice Assistant Tutorial](../code-examples.md) - Build voice assistant

---

## See Also

- [Voice Configuration](../../development/voice-config.md)
- [Audio Profiles](../../development/audio-profiles.md)
- [Environment Variables](../../development/environment-variables.md)
