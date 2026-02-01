# Audio Configuration and Profiles Guide

Complete reference for audio input/output configuration in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Audio Input Configuration](#audio-input-configuration)
- [Audio Output Configuration](#audio-output-configuration)
- [Audio Formats](#audio-formats)
- [Sample Rates](#sample-rates)
- [Device Configuration](#device-configuration)
- [Audio Profiles](#audio-profiles)
- [Recording Configuration](#recording-configuration)
- [Troubleshooting](#troubleshooting)

---

## Overview

Hypr-Voice supports multiple audio backends and configurations:

- **PulseAudio** - Default on modern Linux systems
- **ALSA** - Low-level audio interface
- **File-based** - Record to WAV/MP3 files

### Configuration Files

```
config/hypr_voice/whisper/
├── audio-profile.yaml       # Audio input/output settings
└── config.yaml              # Whisper audio settings
```

---

## Audio Input Configuration

### Audio Profile Settings

```yaml
# config/hypr_voice/whisper/audio-profile.yaml

alsa:
  suppress_warnings: true
  use_pulseaudio_only: true

audio:
  channels: 1
  chunk_size: 2048
  format: int16
  sample_rate: 16000

pulseaudio:
  default_source: alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor
  device_name: HDMI Monitor (from iPhone)
  device_type: monitor
```

### Input Options

#### ALSA Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `suppress_warnings` | boolean | `true` | Suppress ALSA warnings |
| `use_pulseaudio_only` | boolean | `true` | Use only PulseAudio |

#### Audio Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `channels` | integer | `1` | Number of audio channels (1=mono, 2=stereo) |
| `chunk_size` | integer | `2048` | Audio chunk size (samples) |
| `format` | string | `"int16"` | Audio format |
| `sample_rate` | integer | `16000` | Sample rate (Hz) |

#### PulseAudio Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_source` | string | - | PulseAudio source name |
| `device_name` | string | - | Display device name |
| `device_type` | string | `monitor` | Device type (source/sink/monitor) |

---

## Audio Output Configuration

### TTS Audio Settings

```yaml
voice:
  kokoro:
    sample_rate: 24000
    phonemizer: "espeak"

  deepgram:
    sample_rate: 24000
    encoding: "mp3"
    language: "en"

  elevenlabs:
    output_format: "mp3_44100_128"
```

### Output Options

| Provider | Option | Type | Default | Description |
|----------|--------|------|---------|-------------|
| `kokoro` | `sample_rate` | integer | `24000` | Output sample rate |
| `deepgram` | `sample_rate` | integer | `24000` | Output sample rate |
| `deepgram` | `encoding` | string | `"mp3"` | Audio encoding |
| `elevenlabs` | `output_format` | string | `"mp3_44100_128"` | Audio format |

---

## Audio Formats

### Input Formats

| Format | Description | Quality | Size | Use Case |
|--------|-------------|---------|------|----------|
| `wav` | Uncompressed | Best | Large | Recording |
| `mp3` | Compressed | Good | Small | Sharing |
| `opus` | Compressed | Very Good | Smallest | Streaming |
| `flac` | Lossless | Excellent | Medium | Archiving |

### Output Formats

| Format | Description | Quality | Size | Use Case |
|--------|-------------|---------|------|----------|
| `wav` | Uncompressed | Best | Large | High quality |
| `mp3` | Compressed | Good | Small | Universal |
| `opus` | Compressed | Very Good | Smallest | Streaming |
| `flac` | Lossless | Excellent | Medium | Archiving |
| `pcm` | Raw | Best | Large | Processing |

### Format Selection Guide

#### For Recording (Input)

```yaml
# Recommended for recording
recording:
  format: wav                   # Lossless for best quality
  sample_rate: 16000            # Match Whisper requirements
  channels: 1                   # Mono is sufficient for speech
```

#### For TTS (Output)

```yaml
# Recommended for TTS
voice:
  kokoro:
    format: wav                 # Fast generation
    sample_rate: 24000          # Good quality

  deepgram:
    encoding: mp3               # Good compression
    sample_rate: 24000
```

---

## Sample Rates

### Common Sample Rates

| Sample Rate | Quality | Bandwidth | Use Case | Whisper Support |
|-------------|---------|-----------|----------|-----------------|
| 8000 Hz | Low | Telephone | Basic speech | Resampled |
| 16000 Hz | Standard | Wideband | **Recommended for STT** | **Native** |
| 22050 Hz | Good | Music | Better quality | Resampled |
| 44100 Hz | High | CD | High quality | Resampled |
| 48000 Hz | High | Professional | Professional audio | Resampled |

### Sample Rate Recommendations

#### For Speech Recognition (Whisper)

```yaml
audio:
  sample_rate: 16000            # Whisper's native rate
  channels: 1                   # Mono is sufficient
```

#### For TTS Output

```yaml
voice:
  kokoro:
    sample_rate: 24000          # Kokoro's optimal rate
```

#### For High-Quality Recording

```yaml
recording:
  sample_rate: 44100            # CD quality
  channels: 2                   # Stereo
  format: wav                   # Lossless
```

---

## Device Configuration

### PulseAudio Device Selection

#### List Available Devices

```bash
# List all sources (input devices)
pactl list sources short

# List all sinks (output devices)
pactl list sinks short

# List all devices with details
pactl list sources
pactl list sinks
```

#### Example Output

```
# Sources (Input)
0    alsa_input.pci-0000_00_1f.3.analog-stereo    PipeWire source    ...
1    alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor    Monitor of ...

# Sinks (Output)
0    alsa_output.pci-0000_00_1f.3.analog-stereo    PipeWire sink    ...
1    alsa_output.pci-0000_2d_00.1.hdmi-stereo    ...
```

#### Configure Device

```yaml
pulseaudio:
  default_source: alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor
  device_name: HDMI Monitor (from iPhone)
  device_type: monitor
```

### ALSA Device Selection

#### List Available Devices

```bash
# List all PCM devices
aplay -l                      # Output devices
arecord -l                    # Input devices

# List with more details
aplay -L
arecord -L
```

#### Configure Device

```python
import pyaudio

p = pyaudio.PyAudio()

# List devices
for i in range(p.get_device_count()):
    info = p.get_device_info_by_index(i)
    print(f"{i}: {info['name']}")

# Use specific device
stream = p.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    input_device_index=5       # Use device index 5
)
```

### Common Device Names

| Device Type | Pattern | Description |
|-------------|---------|-------------|
| Analog input | `alsa_input.pci-*.analog-stereo` | Built-in mic |
| HDMI output | `alsa_output.pci-*.hdmi-stereo` | HDMI audio |
| HDMI monitor | `alsa_output.pci-*.hdmi-stereo.monitor` | Monitor HDMI |
| USB device | `alsa_input.usb-*` | USB microphone |
| Bluetooth | `bluez_sink.*` / `bluez_source.*` | Bluetooth audio |

---

## Audio Profiles

### Pre-configured Profiles

#### Voice Input Profile

```yaml
# config/hypr_voice/whisper/audio-profile.yaml

# Optimized for speech recognition
audio:
  channels: 1                   # Mono for speech
  chunk_size: 2048              # Balanced latency
  format: int16                 # Standard format
  sample_rate: 16000            # Whisper's native rate

pulseaudio:
  default_source: alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor
  device_type: monitor
```

#### High-Quality Recording Profile

```yaml
# For high-quality recordings
audio:
  channels: 2                   # Stereo
  chunk_size: 4096              # Lower latency
  format: int24                 # Higher bit depth
  sample_rate: 48000            # Professional rate

recording:
  format: wav                   # Lossless
  save_recordings: true
```

#### Low-Latency Profile

```yaml
# For real-time applications
audio:
  channels: 1
  chunk_size: 1024              # Lower latency
  format: int16
  sample_rate: 16000

pulseaudio:
  default_source: alsa_input.pci-*.analog-stereo
```

---

## Recording Configuration

### Recording Settings

```yaml
recording:
  auto_cleanup:
    days_to_keep: 7
    enabled: false

  channels: 1
  format: wav
  sample_rate: 16000
  save_recordings: true
```

### Recording Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_cleanup.enabled` | boolean | `false` | Enable auto-cleanup |
| `auto_cleanup.days_to_keep` | integer | `7` | Days to keep |
| `save_recordings` | boolean | `true` | Save to disk |
| `format` | string | `"wav"` | Recording format |
| `sample_rate` | integer | `16000` | Recording sample rate |
| `channels` | integer | `1` | Number of channels |

### Recording Locations

```python
# Default recording locations
recordings_dir = "/tmp/whisper_recordings"

# Recording file naming
# Format: {timestamp}_{session_id}.{format}
# Example: 20240126_123456_abc123.wav
```

---

## Audio Performance

### Chunk Size Tuning

| Chunk Size | Latency | CPU Usage | Use Case |
|------------|---------|-----------|----------|
| 512 | Very Low | High | Real-time processing |
| 1024 | Low | Medium-High | Interactive apps |
| 2048 | Medium | Medium | **Recommended** |
| 4096 | High | Low | Batch processing |
| 8192 | Very High | Very Low | Background tasks |

### Channel Configuration

| Channels | Description | Use Case | Size |
|----------|-------------|----------|------|
| 1 (Mono) | Single channel | Speech recognition | Smallest |
| 2 (Stereo) | Two channels | Music, ambient sound | 2x mono |

### Format Selection

| Format | Bits | Range | Use Case |
|--------|------|-------|----------|
| `int8` | 8 | -128 to 127 | Low quality |
| `int16` | 16 | -32768 to 32767 | **Recommended** |
| `int24` | 24 | Large range | High quality |
| `int32` | 32 | Very large range | Professional |
| `float32` | 32 | -1.0 to 1.0 | Processing |

---

## Troubleshooting

### Common Issues

#### Issue: No audio input detected

**Symptoms:**
- Empty transcriptions
- "No speech detected" errors

**Solutions:**
```bash
# Check if source exists
pactl list sources short

# Test microphone
arecord -f cd -d 5 test.wav

# Check default source
pactl get-default-source

# Set default source
pactl set-default-source <source_name>
```

#### Issue: Poor audio quality

**Symptoms:**
- Garbled audio
- Background noise
- Low volume

**Solutions:**
```yaml
# Increase sample rate
audio:
  sample_rate: 44100

# Increase bit depth
audio:
  format: int24

# Enable noise reduction (if supported)
pulseaudio:
  noise_reduction: true
```

#### Issue: High latency

**Symptoms:**
- Delay between speech and transcription
- Slow TTS response

**Solutions:**
```yaml
# Reduce chunk size
audio:
  chunk_size: 1024

# Reduce TTS prebuffer
tts:
  streaming:
    prebuffer_ms: 300
```

#### Issue: Audio device not found

**Symptoms:**
- "Device not found" errors
- Failed to open audio device

**Solutions:**
```bash
# Check device permissions
groups $USER                    # Should include 'audio'

# Add user to audio group
sudo usermod -aG audio $USER

# Restart PulseAudio
pulseaudio --kill
pulseaudio --start

# Check PipeWire
pactl info
```

---

## Best Practices

### For Speech Recognition

```yaml
# Optimal settings for Whisper
audio:
  sample_rate: 16000            # Native rate
  channels: 1                   # Mono sufficient
  chunk_size: 2048              # Balanced
  format: int16                 # Standard
```

### For TTS Output

```yaml
# Optimal settings for TTS
voice:
  kokoro:
    sample_rate: 24000          # Kokoro's optimal

  deepgram:
    sample_rate: 24000
    encoding: mp3               # Good compression
```

### For Recording

```yaml
# High-quality recording
recording:
  format: wav                   # Lossless
  sample_rate: 44100            # CD quality
  channels: 2                   # Stereo
  save_recordings: true
```

---

## See Also

- [Whisper Configuration](whisper-config.md)
- [Voice Configuration](voice-config.md)
- [Configuration Reference](configuration-reference.md)
- [Environment Variables](environment-variables.md)
