# Voice Configuration Guide

Complete configuration reference for text-to-speech (TTS) and voice services in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Provider Configuration](#provider-configuration)
- [Voice Presets](#voice-presets)
- [TTS Settings](#tts-settings)
- [Streaming Configuration](#streaming-configuration)
- [Audio Output](#audio-output)

---

## Overview

Hypr-Voice supports multiple text-to-speech providers with automatic fallback:

### Supported Providers

| Provider | Type | Cost | Quality | Latency | Languages |
|----------|------|------|---------|---------|-----------|
| **Kokoro** | Local | Free | Good | Low (~50ms) | English |
| **Deepgram** | Cloud | Paid | Very Good | Low (~100ms) | Multi |
| **ElevenLabs** | Cloud | Paid | Excellent | Medium (~200ms) | Multi (29+) |

### Provider Selection Strategy

```yaml
voice:
  default_provider: "kokoro"     # Try this first
  fallback_provider: "deepgram"  # Use if primary fails
  auto_fallback: true            # Enable automatic fallback
```

---

## Provider Configuration

### Kokoro TTS (Local, Free)

```yaml
voice:
  kokoro:
    enabled: true
    default_voice: "af_bella"
    cache_enabled: true
    cache_dir: "/tmp/kokoro_cache"
    sample_rate: 24000
    phonemizer: "espeak"         # espeak or gruut
```

#### Kokoro Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Kokoro TTS |
| `default_voice` | string | `"af_bella"` | Default voice |
| `cache_enabled` | boolean | `true` | Enable audio caching |
| `cache_dir` | string | `"/tmp/kokoro_cache"` | Cache directory |
| `sample_rate` | integer | `24000` | Output sample rate (Hz) |
| `phonemizer` | string | `"espeak"` | Phonemizer backend |

#### Available Kokoro Voices

| Voice ID | Gender | Style | Description |
|----------|--------|-------|-------------|
| `af_bella` | Female | Neutral | **Default** - Balanced voice |
| `af_sky` | Female | Energetic | Cheerful, upbeat |
| `af_sarah` | Female | Warm | Friendly, gentle |
| `am_adam` | Male | Professional | Deep, clear |
| `am_michael` | Male | Calm | Smooth, relaxed |
| `bf_emma` | Female | Bright | Clear, articulate |
| `bm_george` | Male | Narrator | Storytelling style |

#### Phonemizer Options

| Option | Speed | Accuracy | Dependencies |
|--------|-------|----------|--------------|
| `espeak` | Fast | Good | `espeak-ng` |
| `gruut` | Slow | Excellent | `gruut` + models |

### Deepgram TTS (Cloud)

```yaml
voice:
  deepgram:
    enabled: true
    api_key: "${DEEPGRAM_API_KEY}"
    default_voice: "asteria"
    language: "en"
    sample_rate: 24000
    encoding: "mp3"               # mp3, wav, pcm, opus, flac
    cache_enabled: true
    cache_dir: "/tmp/deepgram_cache"
```

#### Deepgram Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Deepgram |
| `api_key` | string | - | API key (from env) |
| `default_voice` | string | `"asteria"` | Default voice |
| `language` | string | `"en"` | Language code |
| `sample_rate` | integer | `24000` | Output sample rate |
| `encoding` | string | `"mp3"` | Audio encoding |
| `cache_enabled` | boolean | `true` | Enable caching |

#### Available Deepgram Voices

| Voice ID | Gender | Style | Description |
|----------|--------|-------|-------------|
| `asteria` | Female | Professional | **Default** - Clear, neutral |
| `luna` | Female | Friendly | Warm, conversational |
| `orion` | Male | Authoritative | Deep, confident |
| `stella` | Female | Energetic | Bright, dynamic |
| `nova` | Female | Calm | Soothing, peaceful |

#### Audio Encoding Options

| Encoding | Size | Quality | Compatibility |
|----------|------|---------|----------------|
| `mp3` | Small | Good | Universal |
| `wav` | Large | Best | Universal |
| `opus` | Smallest | Good | Modern browsers |
| `flac` | Medium | Excellent | Lossless |
| `pcm` | Large | Best | Raw audio |

### ElevenLabs TTS (Cloud, Premium)

```yaml
voice:
  elevenlabs:
    enabled: true
    api_key: "${ELEVENLABS_API_KEY}"
    default_voice: "rachel"
    model: "eleven_multilingual_v2"
    output_format: "mp3_44100_128"
    stability: 0.5                # 0.0 - 1.0
    similarity_boost: 0.5         # 0.0 - 1.0
    style: 0.0                    # 0.0 - 1.0
    use_speaker_boost: true
    cache_enabled: true
    cache_dir: "/tmp/elevenlabs_cache"
```

#### ElevenLabs Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable ElevenLabs |
| `api_key` | string | - | API key (from env) |
| `default_voice` | string | `"rachel"` | Default voice |
| `model` | string | `"eleven_multilingual_v2"` | TTS model |
| `output_format` | string | `"mp3_44100_128"` | Audio format |
| `stability` | float | `0.5` | Stability (0-1) |
| `similarity_boost` | float | `0.5` | Similarity (0-1) |
| `style` | float | `0.0` | Style enhancement (0-1) |
| `use_speaker_boost` | boolean | `true` | Speaker boost |

#### Available ElevenLabs Models

| Model | Quality | Speed | Languages | Use Case |
|-------|---------|-------|-----------|----------|
| `eleven_multilingual_v2` | Best | Medium | 29 | **Recommended** |
| `eleven_turbo_v2_5` | Good | Fast | 29 | Low latency |
| `eleven_flash_v2_5` | Good | Fastest | 29 | Real-time |

#### Popular ElevenLabs Voices

| Voice ID | Gender | Style | Description |
|----------|--------|-------|-------------|
| `rachel` | Female | Professional | **Default** - Clear, balanced |
| `bella` | Female | Friendly | Warm, conversational |
| `eleven` | Male | Authoritative | Deep, confident |
| `sam` | Male | Calm | Smooth, relaxed |
| `charlie` | Male | Energetic | Bright, dynamic |

---

## Voice Presets

Pre-configured voice settings for different contexts:

### Professional Preset

```yaml
voice:
  presets:
    professional:
      kokoro: {voice: "af_bella", speed: 1.0, pitch: 1.0}
      elevenlabs: {voice: "rachel", stability: 0.7, similarity_boost: 0.7}
      deepgram: {voice: "asteria", speaking_rate: 1.0}
```

**Best for:** Business meetings, presentations, tutorials

### Friendly Preset

```yaml
voice:
  presets:
    friendly:
      kokoro: {voice: "af_sky", speed: 1.1, pitch: 1.1}
      elevenlabs: {voice: "bella", stability: 0.5, similarity_boost: 0.8}
      deepgram: {voice: "luna", speaking_rate: 1.1}
```

**Best for:** Chatbots, assistants, casual interactions

### Technical Preset

```yaml
voice:
  presets:
    technical:
      kokoro: {voice: "am_adam", speed: 0.95, pitch: 0.95}
      elevenlabs: {voice: "adam", stability: 0.8, similarity_boost: 0.6}
      deepgram: {voice: "orion", speaking_rate: 0.95}
```

**Best for:** Code explanations, technical documentation

### Narrator Preset

```yaml
voice:
  presets:
    narrator:
      kokoro: {voice: "bm_george", speed: 0.9, pitch: 0.95}
      elevenlabs: {voice: "antoni", stability: 0.9, similarity_boost: 0.7}
      deepgram: {voice: "zeus", speaking_rate: 0.9}
```

**Best for:** Audiobooks, storytelling, long-form content

---

## TTS Settings

### Environment Variables

```bash
# TTS Provider Selection
export HYPR_VOICE_TTS_PROVIDER="kokoro"  # kokoro, deepgram, elevenlabs

# API Keys (for cloud providers)
export DEEPGRAM_API_KEY="your_deepgram_key"
export ELEVENLABS_API_KEY="your_elevenlabs_key"

# TTS Streaming
export HYPR_VOICE_TTS_STREAMING=1
export HYPR_VOICE_TTS_REST_STREAMING=1
export HYPR_VOICE_TTS_PREBUFFER_MS=800
export HYPR_VOICE_TTS_MIN_CHARS=100
export HYPR_VOICE_TTS_MAX_LATENCY=0.5
export HYPR_VOICE_TTS_FLUSH_TIMEOUT=15
export HYPR_VOICE_TTS_IDLE_TIMEOUT=3.0
```

### TTS Settings Reference

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `HYPR_VOICE_TTS_PROVIDER` | string | `"kokoro"` | Default TTS provider |
| `DEEPGRAM_API_KEY` | string | - | Deepgram API key |
| `ELEVENLABS_API_KEY` | string | - | ElevenLabs API key |
| `HYPR_VOICE_TTS_STREAMING` | boolean | `1` | Enable streaming |
| `HYPR_VOICE_TTS_PREBUFFER_MS` | integer | `800` | Prebuffer duration |
| `HYPR_VOICE_TTS_MIN_CHARS` | integer | `100` | Min chars for streaming |
| `HYPR_VOICE_TTS_MAX_LATENCY` | float | `0.5` | Max latency (seconds) |
| `HYPR_VOICE_TTS_FLUSH_TIMEOUT` | integer | `15` | Flush timeout (seconds) |
| `HYPR_VOICE_TTS_IDLE_TIMEOUT` | float | `3.0` | Idle timeout (seconds) |

---

## Streaming Configuration

### Streaming Settings

```yaml
# In config.yaml or via environment variables
tts:
  streaming:
    enabled: true
    prebuffer_ms: 800            # Prebuffer audio (milliseconds)
    min_chars: 100               # Minimum characters for streaming
    max_latency: 0.5             # Maximum latency (seconds)
    flush_timeout: 15            # Flush timeout (seconds)
    idle_timeout: 3.0            # Idle timeout (seconds)
```

### Streaming Behavior

| Setting | Effect | Recommended Value |
|---------|--------|-------------------|
| `prebuffer_ms` | Audio buffered before playback | 500-1000ms |
| `min_chars` | Min text length for streaming | 50-200 chars |
| `max_latency` | Maximum allowed latency | 0.3-1.0s |
| `flush_timeout` | Force flush after timeout | 10-30s |
| `idle_timeout` | Close idle connections | 2-5s |

### Optimization Profiles

#### Low Latency (Real-time)

```yaml
tts:
  streaming:
    prebuffer_ms: 300
    min_chars: 50
    max_latency: 0.3
```

#### Balanced (Default)

```yaml
tts:
  streaming:
    prebuffer_ms: 800
    min_chars: 100
    max_latency: 0.5
```

#### High Quality (More Latency)

```yaml
tts:
  streaming:
    prebuffer_ms: 1500
    min_chars: 200
    max_latency: 1.0
```

---

## Audio Output

### Audio Player Configuration

```python
from hypr_voice.services.voice.audio_player import AudioPlayer

# Create audio player
player = AudioPlayer(
    sample_rate=24000,
    channels=1,
    format="int16",
    device="default"              # PulseAudio device name
)

# Play audio
await player.play(audio_file)

# Adjust playback
player.set_volume(0.8)            # Volume 0.0 - 1.0
player.set_speed(1.2)             # Speed 0.5 - 2.0
```

### Audio Player Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sample_rate` | integer | `24000` | Sample rate (Hz) |
| `channels` | integer | `1` | Number of channels |
| `format` | string | `"int16"` | Audio format |
| `device` | string | `"default"` | Output device |
| `volume` | float | `1.0` | Volume (0.0-1.0) |
| `speed` | float | `1.0` | Playback speed (0.5-2.0) |

### Output Devices

#### PulseAudio Device Selection

```bash
# List available devices
pactl list sinks short

# Set default device
pactl set-default-sink <device_name>
```

#### Common Device Names

| Device | Description |
|--------|-------------|
| `default` | System default |
| `alsa_output.pci-*.analog-stereo` | Analog output |
| `alsa_output.pci-*.hdmi-stereo` | HDMI output |
| `bluez_sink.*` | Bluetooth device |

---

## Voice Synthesis Examples

### Basic Synthesis

```python
from hypr_voice.services.voice.tts_manager import VoiceManager

manager = VoiceManager()

# Synthesize with default voice
audio_file = await manager.synthesize(
    "Hello, world!",
    provider="kokoro",
    voice="af_bella"
)
```

### With Custom Settings

```python
# Synthesize with custom voice
audio_file = await manager.synthesize(
    "Hello, world!",
    provider="kokoro",
    voice="af_bella",
    speed=1.1,                    # Playback speed
    pitch=1.0,                    # Pitch adjustment
    output_file="/tmp/output.wav"
)
```

### Streaming Synthesis

```python
from hypr_voice.services.voice.tts_manager import VoiceManager

manager = VoiceManager()

# Stream synthesis
async for chunk in manager.synthesize_stream(
    "This is a long text that will be streamed...",
    provider="kokoro",
    voice="af_bella"
):
    # Process audio chunk
    await player.play_chunk(chunk)
```

---

## See Also

- [Configuration Reference](configuration-reference.md)
- [Environment Variables](environment-variables.md)
- [Audio Profiles](audio-profiles.md)
- [Examples](../examples/basic-usage.md)
