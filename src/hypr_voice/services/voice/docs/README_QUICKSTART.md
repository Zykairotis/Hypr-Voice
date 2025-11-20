# Unified TTS Quick Start

## 🚀 Ready to Test!

All fixes have been applied. The system is operational.

## Quick Test (30 seconds)

```bash
cd test_tts_voice
./run_tests.sh
```

Select option `1` for quick verification.

## What You'll See

```
✅ Manager created with 1 providers  # Kokoro (free, local)
⚠️ ElevenLabs API key not found     # Add key to enable
⚠️ Deepgram API key not found       # Add key to enable
```

## Enable All Providers

Add to `.env`:
```bash
ELEVENLABS_API_KEY=your_key
DEEPGRAM_API_KEY=your_key
```

## Usage in Code

```python
from services.voice import UnifiedVoiceManager

manager = UnifiedVoiceManager()

# Stream text
async for audio in manager.stream_from_llm(text_generator):
    pass
```

## Files to Know

- `STATUS.md` - Current system status ⭐
- `TESTING_GUIDE.md` - Complete testing guide
- `UNIFIED_TTS_ARCHITECTURE.md` - Full architecture
- `test_import.sh` - Quick import test

## That's It!

The system works. Run `./run_tests.sh` in `test_tts_voice/` to try it out.
