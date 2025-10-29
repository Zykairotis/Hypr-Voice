# Hypr-Voice Vocabulary Enhancement System

## Overview

The Hypr-Voice vocabulary enhancement system automatically improves transcription accuracy for technical terms, product names, and domain-specific language. It works seamlessly with the hybrid Whisper server to correct commonly misrecognized words in real-time.

## Features

- **Automatic Vocabulary Enhancement**: Post-processes transcriptions to correct technical terms
- **Application-Aware**: Detects active applications and switches vocabularies automatically
- **Stop Word Filtering**: Avoids false matches on common words
- **Case Preservation**: Maintains original capitalization patterns
- **Fuzzy Matching**: Corrects slight misspellings (85% similarity threshold)

## Architecture

```
Whisper Transcription → Hallucination Filter → Vocabulary Enhancement → Clean Text
```

## Configuration

### Main Configuration

The vocabulary system is configured in `src/Hypr-Whisper/config/vocabulary.yaml`:

```yaml
global:
  technical_terms:
    - "Docker"
    - "Kubernetes"
    - "REST"
    - "API"
    - "GraphQL"
    # ... more terms
```

### Application-Specific Vocabularies

Located in `src/Hypr-Whisper/config/vocabularies/`:
- `development.yaml` - Programming and development terms
- `productivity.yaml` - Business and office terms  
- `gaming.yaml` - Gaming-related terms

## Usage

### With Hybrid Server

The vocabulary system is automatically integrated into `hybrid_server.py`. When transcribing:

1. Raw transcription is generated
2. Hallucinations are filtered
3. **Vocabulary enhancement is applied**
4. Clean text is output

### With PTT System

The push-to-talk system (`hypr-voice-type.py`) also uses vocabulary enhancement:

```python
# Automatic enhancement after transcription
enhanced_text = vocabulary_manager.post_process_transcription(text)
```

## Examples

### Before Enhancement
```
"i use docker and kubernetes with rest api"
"the python script uses tensorflow"
"deploy to aws using terraform"
```

### After Enhancement
```
"i use Docker and Kubernetes with REST API"
"the Python script uses TensorFlow"
"deploy to AWS using Terraform"
```

## Adding Custom Terms

### Method 1: Edit YAML Configuration

Add terms to `config/vocabulary.yaml`:

```yaml
global:
  technical_terms:
    - "YourProduct"
    - "YourTechnology"
```

### Method 2: Application-Specific

Add to relevant file in `config/vocabularies/`:

```yaml
# development.yaml
keywords:
  frameworks:
    - "YourFramework"
```

## Performance

- **Minimal Overhead**: < 5ms for typical transcriptions
- **Smart Matching**: Only corrects when confidence > 85%
- **Stop Words**: Common words are ignored to avoid false positives

## Files

- `src/Hypr-Whisper/vocabulary_manager.py` - Core vocabulary engine
- `src/Hypr-Whisper/config/vocabulary.yaml` - Global vocabulary configuration
- `src/Hypr-Whisper/config/vocabularies/*.yaml` - Application-specific vocabularies
- `src/Hypr-Whisper/scripts/app_detector.py` - Application detection (Hyprland/X11)
- `src/Hypr-Whisper/hybrid_server.py` - Server integration
- `src/Hypr-Whisper/hypr-voice-type.py` - PTT integration

## Troubleshooting

### Terms not being corrected

1. Check if term is in vocabulary:
```bash
grep -i "yourterm" config/vocabulary.yaml
```

2. Verify vocabulary is loaded:
```python
from vocabulary_manager import get_vocabulary_manager
vm = get_vocabulary_manager()
print(vm.vocabularies.keys())
```

3. Test correction directly:
```python
enhanced = vm.post_process_transcription("your test text")
```

### Too aggressive matching

Increase the similarity threshold in `vocabulary_manager.py`:
```python
best_ratio = 0.90  # Increase from 0.85
```

## Integration Status

✅ **Integrated with:**
- Hybrid Whisper Server (`hybrid_server.py`)
- Push-to-Talk System (`hypr-voice-type.py`)
- Application detection (Hyprland/X11)

✅ **Features Working:**
- Post-processing correction
- Case preservation
- Stop word filtering
- Fuzzy matching (85% threshold)

⚠️ **Future Improvements:**
- Real-time application detection
- Hot-reload vocabulary changes
- Metrics and statistics
- Custom vocabulary UI
