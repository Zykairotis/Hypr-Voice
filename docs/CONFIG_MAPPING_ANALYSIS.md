# Configuration Mapping Analysis: Web UI ↔ Hypr-Whisper

## Executive Summary

The web UI configuration parameters ARE properly linked to the Hypr-Whisper config files, but there are **2 critical issues** that need fixing:

1. **CPU Threads mapping mismatch** - Bridge saves to wrong config key
2. **COMPUTE_TYPE default value mismatch** - Bridge defaults differ from server

---

## Configuration File Mapping

### 1. Audio Configuration (`audio-profile.yaml`)

| Web UI Component | Bridge API Field | Config File Path | Server Usage | ✓/✗ |
|-----------------|------------------|------------------|--------------|-----|
| Input Device | `input_device` | `pulseaudio.default_source` | ❌ NOT USED by hybrid_server | ✗ |
| Sample Rate | `sample_rate` | `audio.sample_rate` | ✅ `PERFORMANCE_CONFIG.sample_rate` | ✓ |
| Channels | `channels` | `audio.channels` | ❌ NOT USED by hybrid_server | ✗ |
| Buffer Size | `buffer_size` | `audio.chunk_size` | ❌ NOT USED by hybrid_server | ✗ |
| Save Recordings | `save_recordings` | `recording.save_recordings` | ❌ NOT USED by hybrid_server | ✗ |
| Auto Cleanup | `auto_cleanup` | `recording.auto_cleanup` | ❌ NOT USED by hybrid_server | ✗ |

**Status:** ✗ **BROKEN** - audio-profile.yaml is loaded by client scripts (hypr-voice-type.py) but NOT by hybrid_server.py

---

### 2. Model Configuration (`config.yaml`)

| Web UI Component | Bridge API Field | Config File Path | Server Usage | ✓/✗ |
|-----------------|------------------|------------------|--------------|-----|
| Model Path | `model_path` | `backend.model_path` | ✅ `MODEL_SIZE` (line 73) | ✓ |
| Device | `device` | `backend.device` | ✅ `DEVICE` (line 74) | ✓ |
| Language | `language` | `backend.language` | ❌ NOT USED by hybrid_server | ✗ |
| Translate | `translate` | `backend.translate` | ❌ NOT USED by hybrid_server | ✗ |
| Compute Type | `compute_type` | `model.compute_type` | **MISMATCH** - Server reads from `backend.compute_type` (line 75) | ✗ |
| Num Workers | `num_workers` | `model.num_workers` | ✅ `MODEL_CONFIG.num_workers` (line 254) | ✓ |
| CPU Threads | `cpu_threads` | `model.cpu_threads` | **MISMATCH** - Server uses `performance.omp_num_threads` (line 253) | ✗ |
| VAD Enabled | `vad_enabled` | `hypr_voice.vad_enabled` | ❌ NOT USED by hybrid_server | ✗ |
| VAD Threshold | `vad_threshold` | `hypr_voice.vad_threshold` | ❌ NOT USED by hybrid_server | ✗ |
| Min Speech Duration | `min_speech_duration` | `hypr_voice.min_speech_duration` | ❌ NOT USED by hybrid_server | ✗ |
| Max Silence Duration | `max_silence_duration` | `hypr_voice.max_silence_duration` | ❌ NOT USED by hybrid_server | ✗ |

**Critical Issues:**
1. **Compute Type:** Bridge writes to `model.compute_type` but server reads from `backend.compute_type`
2. **CPU Threads:** Bridge writes to `model.cpu_threads` but server reads from `performance.omp_num_threads`

---

### 3. Vocabulary Configuration (`vocabulary.yaml`)

| Web UI Component | Bridge API Field | Config File Path | Server Usage | ✓/✗ |
|-----------------|------------------|------------------|--------------|-----|
| Vocabulary Enabled | `enabled` | `settings.post_processing.enabled` | ✅ Used by vocabulary_manager.py | ✓ |
| Custom Words | `custom_words` | `global.technical_terms` | ✅ Used by vocabulary_manager.py | ✓ |

**Status:** ✓ **WORKING** - Vocabulary configuration is properly integrated

---

## Critical Fixes Needed

### Fix #1: Compute Type Path

**Current (WRONG):**
```python
# Bridge writes to:
existing["model"]["compute_type"] = config.compute_type

# Server reads from:
COMPUTE_TYPE = BACKEND_CONFIG.get('compute_type', 'int8')
```

**Should be:**
```python
# Bridge should write to:
existing["backend"]["compute_type"] = config.compute_type
```

**OR** update server to read from `MODEL_CONFIG`:
```python
COMPUTE_TYPE = MODEL_CONFIG.get('compute_type', 'int8_float16')
```

### Fix #2: CPU Threads Path

**Current (WRONG):**
```python
# Bridge writes to:
existing["model"]["cpu_threads"] = config.cpu_threads

# Server reads from:
cpu_threads=PERFORMANCE_CONFIG.get('omp_num_threads', 4)
```

**Should be:**
```python
# Bridge should write to:
existing["performance"]["omp_num_threads"] = config.cpu_threads
```

---

## Secondary Issues (Features Not Implemented)

The following config options are **saved correctly** but **NOT used** by hybrid_server.py:

1. **Language detection** (`backend.language`) - Server doesn't pass this to WhisperModel
2. **Translation** (`backend.translate`) - Server doesn't use this parameter
3. **VAD settings** (`hypr_voice.*`) - Server doesn't implement Voice Activity Detection
4. **Audio device settings** from `audio-profile.yaml` - Only used by client scripts, not server

---

## Recommendations

### Immediate (Critical):
1. ✅ Fix compute_type mapping mismatch in bridge.py
2. ✅ Fix cpu_threads mapping mismatch in bridge.py

### Short-term (Important):
3. Update hybrid_server.py to use audio-profile.yaml for device selection
4. Implement language and translate parameters in transcription
5. Implement VAD settings in the WebSocket handler

### Long-term (Enhancement):
6. Add configuration validation to ensure bridge and server stay in sync
7. Add a "restart required" notification when critical settings change
8. Implement hot-reload for non-critical config changes

---

## Conclusion

**YES**, the web UI parameters ARE linked to the config files, **BUT**:
- ✅ The config files are being read and written correctly
- ✗ There are 2 path mismatches that prevent some settings from working
- ✗ Many advanced features (VAD, language, translate) are configured but not implemented in the server

The bridge is doing its job - the issue is the hybrid_server.py needs updates to:
1. Read from the correct config paths
2. Actually use the advanced parameters

