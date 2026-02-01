# Whisper STT Configuration Guide

Complete configuration reference for Whisper speech-to-text transcription in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Server Configuration](#server-configuration)
- [Backend Configuration](#backend-configuration)
- [Audio Configuration](#audio-configuration)
- [Vocabulary Enhancement](#vocabulary-enhancement)
- [Performance Tuning](#performance-tuning)
- [Hybrid Mode](#hybrid-mode)

---

## Overview

Hypr-Voice uses WhisperLive for real-time and offline speech-to-text transcription. The system supports:

- **Real-time streaming** via WebSocket
- **Offline batch processing** via REST API
- **Hybrid mode** combining both approaches
- **Custom vocabulary enhancement** for technical terms
- **Multiple backend types** (faster-whisper, TensorRT, OpenVINO)

### Configuration Files

```
config/hypr_voice/whisper/
├── config.yaml              # Main Whisper configuration
├── audio-profile.yaml       # Audio input/output settings
├── vocabulary.yaml          # Vocabulary configuration
├── context.yaml             # Context extraction
├── categories.yaml          # Application categories
├── custom_dictionary.yaml   # Custom terms
├── backend_overlays.yaml    # Backend-specific vocab
├── notifications.yaml       # Notification settings
├── context_enhanced.yaml    # Enhanced context
└── vocabularies/            # Domain-specific vocabularies
    ├── development.yaml
    ├── gaming.yaml
    └── productivity.yaml
```

---

## Server Configuration

### Basic Server Settings

```yaml
# config/hypr_voice/whisper/config.yaml

server:
  host: "0.0.0.0"              # Listen on all interfaces
  port: 9099                   # Server port
  max_clients: 10              # Maximum concurrent clients
  max_connection_time: 3600    # Max session duration (seconds)
```

#### Server Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | `"0.0.0.0"` | Server bind address |
| `port` | integer | `9099` | Server port |
| `max_clients` | integer | `10` | Maximum concurrent clients |
| `max_connection_time` | integer | `3600` | Max session duration (seconds) |

---

## Backend Configuration

### Backend Types

```yaml
backend:
  type: "faster_whisper"       # Options: faster_whisper, tensorrt, openvino
  model_path: "small.en"       # Model size and language
  device: "cuda"               # Options: cpu, cuda
  language: "en"               # Language code
  translate: false             # Translate to English
```

### Available Models

| Model | Size | Accuracy | Speed | VRAM | Use Case |
|-------|------|----------|-------|------|----------|
| `tiny` | ~40MB | Low | Fast | ~1GB | Quick drafts |
| `tiny.en` | ~40MB | Low (EN) | Fast | ~1GB | English quick drafts |
| `base` | ~75MB | Medium | Medium | ~1GB | General use |
| `base.en` | ~75MB | Medium (EN) | Medium | ~1GB | English general |
| `small` | ~250MB | High | Medium | ~2GB | Good balance |
| `small.en` | ~250MB | High (EN) | Medium | ~2GB | **Recommended** |
| `medium` | ~770MB | Very High | Slow | ~5GB | High accuracy |
| `medium.en` | ~770MB | Very High (EN) | Slow | ~5GB | English high accuracy |
| `large` | ~1550MB | Best | Very Slow | ~10GB | Best accuracy |
| `large-v1` | ~1550MB | Best | Very Slow | ~10GB | Legacy best |
| `large-v2` | ~1550MB | Best | Very Slow | ~10GB | Version 2 best |

### Device Configuration

| Device | Description | Requirements |
|--------|-------------|--------------|
| `cpu` | CPU inference | No GPU required |
| `cuda` | NVIDIA GPU | CUDA-compatible GPU |

### Backend Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `type` | string | `"faster_whisper"` | Backend type |
| `model_path` | string | `"small.en"` | Model identifier |
| `device` | string | `"cuda"` | Compute device |
| `language` | string | `"en"` | Language code |
| `translate` | boolean | `false` | Auto-translate to English |

---

## Audio Configuration

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

recording:
  auto_cleanup:
    days_to_keep: 7
    enabled: false
  channels: 1
  format: wav
  sample_rate: 16000
  save_recordings: true
```

### Audio Options

#### ALSA Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `suppress_warnings` | boolean | `true` | Suppress ALSA warnings |
| `use_pulseaudio_only` | boolean | `true` | Use only PulseAudio |

#### Audio Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `channels` | integer | `1` | Number of audio channels |
| `chunk_size` | integer | `2048` | Audio chunk size |
| `format` | string | `int16` | Audio format |
| `sample_rate` | integer | `16000` | Sample rate (Hz) |

#### PulseAudio Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `default_source` | string | - | PulseAudio source name |
| `device_name` | string | - | Display device name |
| `device_type` | string | `monitor` | Device type |

#### Recording Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `auto_cleanup.enabled` | boolean | `false` | Enable auto-cleanup |
| `auto_cleanup.days_to_keep` | integer | `7` | Days to keep recordings |
| `save_recordings` | boolean | `true` | Save recordings to disk |

### Sample Rate Support

| Sample Rate | Quality | Bandwidth | Use Case |
|-------------|---------|-----------|----------|
| 8000 Hz | Low | Telephone grade | Basic speech |
| 16000 Hz | Standard | Wideband speech | **Recommended** |
| 22050 Hz | Good | Music grade | Better quality |
| 44100 Hz | High | CD quality | Best quality |
| 48000 Hz | High | Professional | Professional audio |

---

## Vocabulary Enhancement

### Vocabulary Configuration

```yaml
# config/hypr_voice/whisper/vocabulary.yaml

global:
  technical_terms:
    - CLI
    - API
    - GUI
    - IDE
    - SDK
    # ... more terms

  programming:
    keywords:
      - function
      - variable
      - class
      # ... more keywords

  common_corrections:
    get hub: GitHub
    pie torch: PyTorch
    hyper land: Hyprland

applications:
  terminal:
    window_class_patterns:
      - Alacritty
      - kitty
      - gnome-terminal
    vocabulary:
      shell_commands:
        - ls
        - cd
        - pwd
        # ... more commands

settings:
  enhancement_method: prompt_engineering
  fuzzy_matching: true
  confidence_threshold: 0.7
```

### Vocabulary Options

#### Global Vocabulary

| Option | Type | Description |
|--------|------|-------------|
| `technical_terms` | list | General technical terms |
| `programming` | dict | Programming-related keywords |
| `common_corrections` | dict | Common misspellings |

#### Application-Specific Vocabulary

| Option | Type | Description |
|--------|------|-------------|
| `window_class_patterns` | list | Application window class patterns |
| `vocabulary` | dict | Application-specific terms |

#### Enhancement Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enhancement_method` | string | `"prompt_engineering"` | Enhancement method |
| `fuzzy_matching` | boolean | `true` | Enable fuzzy matching |
| `confidence_threshold` | float | `0.7` | Match confidence threshold |

### Domain-Specific Vocabularies

#### Development Vocabulary

```yaml
# config/hypr_voice/whisper/vocabularies/development.yaml

name: "Development"
description: "Vocabulary for software development"

keywords:
  languages:
    - "javascript"
    - "typescript"
    - "python"
    # ... more languages

  frameworks:
    - "react"
    - "vue"
    - "angular"
    # ... more frameworks

  tools:
    - "git"
    - "docker"
    - "kubernetes"
    # ... more tools
```

#### Gaming Vocabulary

```yaml
# config/hypr_voice/whisper/vocabularies/gaming.yaml

name: "Gaming"
description: "Vocabulary for gaming"

keywords:
  genres:
    - "RPG"
    - "MMORPG"
    - "FPS"
    # ... more genres

  gaming_terms:
    - "noob"
    - "pro"
    - "nerf"
    # ... more terms
```

#### Productivity Vocabulary

```yaml
# config/hypr_voice/whisper/vocabularies/productivity.yaml

name: "Productivity"
description: "Vocabulary for business and productivity"

keywords:
  business:
    - "meeting"
    - "presentation"
    - "deadline"
    # ... more terms
```

---

## Performance Tuning

### CTranslate2 Settings

```yaml
ctranslate2:
  inter_threads: 4               # Inter-op parallelism
  intra_threads: 8               # Intra-op parallelism
  beam_size: 5                   # Beam search size
  patience: 2.0                  # Beam search patience
  length_penalty: 1.0            # Length penalty
  temperature: 0.0               # Sampling temperature
  compression_ratio_threshold: 2.4
  log_prob_threshold: -1.0
  no_speech_threshold: 0.4
```

### Performance Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `inter_threads` | integer | `4` | Inter-op parallelism |
| `intra_threads` | integer | `8` | Intra-op parallelism |
| `beam_size` | integer | `5` | Beam search size |
| `patience` | float | `2.0` | Beam search patience |
| `temperature` | float | `0.0` | Sampling temperature |

### Performance Tuning Guide

#### For Speed (Lower Quality)

```yaml
ctranslate2:
  beam_size: 1                   # Greedy decoding
  inter_threads: 2
  intra_threads: 4
```

#### For Accuracy (Slower)

```yaml
ctranslate2:
  beam_size: 5                   # Beam search
  patience: 2.0
  inter_threads: 4
  intra_threads: 8
```

#### For Balanced Performance

```yaml
ctranslate2:
  beam_size: 3                   # Middle ground
  patience: 1.5
  inter_threads: 4
  intra_threads: 6
```

### Model Settings

```yaml
model:
  download_root: "/tmp/whisper-models"
  local_files_only: false
  compute_type: "float16"        # Options: float16, int8, float32
  num_workers: 4
  cpu_threads: 8
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `compute_type` | string | `"float16"` | Computation precision |
| `num_workers` | integer | `4` | Number of workers |
| `cpu_threads` | integer | `8` | CPU threads |

---

## Hybrid Mode

### Hybrid Configuration

```yaml
hybrid:
  enabled: true
  protocol: "both"               # Options: websocket, rest, both

  rest_api:
    enabled: true
    max_upload_size: 500         # MB
    allowed_formats:
      - wav
      - mp3
      - mp4
      - mkv
      - flac
      - m4a
      - ogg
      - webm
    job_queue: true
    cleanup_after: 3600          # seconds

  websocket:
    enabled: true
    heartbeat_interval: 30       # seconds
    max_message_size: 10         # MB

  shared_model: true             # Share model between APIs
```

### Hybrid Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable hybrid mode |
| `protocol` | string | `"both"` | Protocol(s) to enable |
| `shared_model` | boolean | `true` | Share model instance |

#### REST API Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable REST API |
| `max_upload_size` | integer | `500` | Max upload size (MB) |
| `allowed_formats` | list | - | Allowed audio formats |
| `job_queue` | boolean | `true` | Enable job queue |
| `cleanup_after` | integer | `3600` | Cleanup time (seconds) |

#### WebSocket Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable WebSocket |
| `heartbeat_interval` | integer | `30` | Heartbeat interval (seconds) |
| `max_message_size` | integer | `10` | Max message size (MB) |

---

## Context Configuration

### Context Extraction

```yaml
# config/hypr_voice/whisper/context.yaml

application_detection:
  enabled: true
  method: auto                   # auto, hyprland, sway, gnome, kde, x11
  update_interval: 200           # milliseconds
  fallback_behavior: global

shell_history:
  enabled: true
  count: 40
  sources:
    - ~/.zsh_history
    - ~/.bash_history

clipboard_history:
  enabled: true
  count: 5
  tool: cliphist                 # cliphist or wl-paste

window_context:
  enabled: true
  extract_from_title: true
  extract_from_class: true
```

### Context Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `application_detection.enabled` | boolean | `true` | Enable app detection |
| `application_detection.method` | string | `"auto"` | Detection method |
| `shell_history.count` | integer | `40` | Commands to analyze |
| `clipboard_history.count` | integer | `5` | Clipboard entries |

---

## Notification Configuration

```yaml
# config/hypr_voice/whisper/notifications.yaml

notifications:
  enabled: false                 # Master toggle

  recording_started: false       # "🔴 Recording..."
  recording_stopped: false       # "⏹️ Processing..."
  transcription_success: false   # "✅ Typed"
  transcription_empty: false     # "🔇 No Speech"
  transcription_error: false     # "❌ Error"
  already_recording: false       # "⚠️ Already Recording"
  not_recording: false           # "⚠️ Not Recording"
  recording_failed: false        # "⚠️ Recording Failed"

  duration_ms: 3000              # Display duration
```

---

## See Also

- [Configuration Reference](configuration-reference.md)
- [Audio Profiles](audio-profiles.md)
- [Vocabulary Configuration](vocabulary-config.md)
- [Environment Variables](environment-variables.md)
