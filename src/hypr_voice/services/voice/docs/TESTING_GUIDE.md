# TTS Testing Guide

## Quick Start

The easiest way to test the unified TTS system:

```bash
cd test_tts_voice
./run_tests.sh
```

This will show an interactive menu with all test options.

## Fixed Issues

✅ **Import errors fixed** - All relative imports now have fallback support  
✅ **Bash script syntax fixed** - Missing quote error resolved  
✅ **Python execution fixed** - Uses `python3` consistently  

## Test Options

### 1. Quick System Verification

Tests that all providers can be initialized and lists what's available.

```bash
cd test_tts_voice
./run_tests.sh
# Select option 1
```

**OR directly:**
```bash
cd /path/to/services/voice
python3 run_quick_test.py
```

### 2. Interactive Provider Test

Manual testing with provider/voice selection.

```bash
cd test_tts_voice  
python3 interactive_test.py
```

### 3. Streaming Speed Test

Tests a specific words-per-second rate (default: 10).

```bash
cd test_tts_voice
python3 streaming_test.py
```

### 4. Multi-Speed Test

Tests multiple speeds automatically (5, 10, 15, 20 wps).

```bash
cd test_tts_voice
./run_tests.sh
# Select option 4
```

## Common Issues & Solutions

### ImportError with relative imports

**Fixed!** The code now handles both package imports and direct script execution.

### "No providers available"

**Check:**
1. API keys in `.env`:
   ```bash
   ELEVENLABS_API_KEY=your_key
   DEEPGRAM_API_KEY=your_key
   ```
2. Kokoro should always work (local, no key needed)
3. Check if Kokoro server is running: `localhost:8880`

### Permission denied

Make scripts executable:
```bash
chmod +x test_tts_voice/*.py
chmod +x test_tts_voice/run_tests.sh
chmod +x run_quick_test.py
```

## Test Output Locations

```
test_tts_voice/
├── audio/          # Generated audio files
│   └── {provider}_{voice}_{timestamp}.mp3
├── metrics/        # Performance metrics (JSON)
│   └── streaming_test_{wps}wps_{timestamp}.json
└── test_data/      # Input test files
    └── sample_100words.txt
```

## Running Tests from Different Directories

The test system is designed to work from the correct directory:

```bash
# From anywhere in the project
cd src/Hypr-Voice/Agent/services/voice/test_tts_voice
./run_tests.sh

# Or for quick test
cd src/Hypr-Voice/Agent/services/voice  
python3 run_quick_test.py
```

## Expected Output

### Quick Verification Test

```
🚀 Starting unified TTS system test...
🚀 Initializing Voice Manager...
✅ Available providers: kokoro, elevenlabs, deepgram

========================================
Testing: kokoro
========================================
✅ Found 17 voices
   Using voice: af_bella
🔌 Testing connection...
✅ Connected successfully
🎙️ Testing TTS streaming...
✅ Received 12 audio chunks
✅ Disconnected
...
```

### Streaming Speed Test

```
Testing: elevenlabs
Voice: rachel
Model: eleven_turbo_v2_5
Speed: 10.0 words/second
==========================================
🔌 Connecting...
✅ Connected in 0.85s
🎙️ Starting TTS streaming...
🎵 First audio chunk received after 0.32s
✅ Completed in 10.45s
...
```

## Troubleshooting

### Test fails immediately

```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check if in correct directory
pwd  # Should end with .../services/voice or .../test_tts_voice
```

### Audio not playing

The tests save audio files even if playback fails. Check `test_tts_voice/audio/` directory.

### Provider not found

```python
# Check what's available
from services.voice import UnifiedVoiceManager
manager = UnifiedVoiceManager()
print(manager.list_providers())
```

## Integration Testing

To test with your own LLM generator:

```python
import asyncio
from services.voice import UnifiedVoiceManager

async def test_with_llm():
    manager = UnifiedVoiceManager()
    
    # Your LLM generator
    async def my_llm_generator():
        for word in "Hello world from LLM".split():
            yield word + " "
            await asyncio.sleep(0.1)
    
    # Stream to TTS
    async for audio in manager.stream_from_llm(
        my_llm_generator(),
        provider="elevenlabs"
    ):
        pass
    
    print("Done!")

asyncio.run(test_with_llm())
```

## Performance Expectations

| Provider | Connect Time | First Audio | Quality |
|----------|-------------|-------------|---------|
| Kokoro | ~0.02s | ~0.55s | Good |
| ElevenLabs | ~0.85s | ~0.32s | Highest |
| Deepgram | ~0.9s | ~0.28s | High |

## Next Steps

After successful testing:

1. **Integrate with orchestrator**:
   ```python
   from services.voice import UnifiedVoiceManager
   self.voice_manager = UnifiedVoiceManager()
   ```

2. **Add Claude Code SDK integration** when available

3. **Configure auto-fallback** for production:
   ```python
   config = UnifiedVoiceConfig(
       default_provider="elevenlabs",
       fallback_providers=["deepgram", "kokoro"],
       auto_fallback=True
   )
   ```

4. **Monitor metrics** in `test_tts_voice/metrics/` for performance tuning

## Support

For issues:
1. Check this guide
2. Review `UNIFIED_TTS_ARCHITECTURE.md`
3. Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`
4. Check test output files in `audio/` and `metrics/` directories
