# How to Run TTS Tests

## ✅ Fixed: Works from Any Directory!

The test script now works whether you run it from the project root or from within the test directory.

## Quick Start

### From Project Root (Where .env is)
```bash
./src/Hypr-Voice/Agent/services/voice/test_tts_voice/run_tests.sh
```

### From Test Directory
```bash
cd src/Hypr-Voice/Agent/services/voice/test_tts_voice
./run_tests.sh
```

## What's Been Fixed

✅ **Path Resolution** - Script auto-detects its location  
✅ **Voice Names** - Only valid full names like "af_bella"  
✅ **Session Cleanup** - No more unclosed session warnings  
✅ **Import System** - Works for both package and direct execution  

## Test Menu Options

```
1. Quick System Verification  - Test all providers quickly
2. Interactive Provider Test  - Manual testing with voice selection
3. Streaming Speed Test       - Test at 10 words/second
4. Multi-Speed Streaming Test - Test at 5, 10, 15, 20 wps
5. Run All Tests              - Complete test suite
0. Exit
```

## Expected Output

### With No API Keys (Kokoro Only)
```
✅ Available providers: kokoro
Testing: kokoro
✅ Found 15 voices  (filtered, valid full names only)
   Using voice: af_bella
✅ Connected successfully
🎙️ Testing TTS streaming...
✅ Received audio chunks
✅ Disconnected
```

### With API Keys (All Providers)
```
✅ Available providers: kokoro, elevenlabs, deepgram
```

## Enable All Providers

Add to `.env` in project root:
```bash
ELEVENLABS_API_KEY=your_elevenlabs_key
DEEPGRAM_API_KEY=your_deepgram_key
```

## Output Locations

Results are saved to:
```
src/Hypr-Voice/Agent/services/voice/test_tts_voice/
├── audio/     # Generated MP3 files
└── metrics/   # Performance JSON data
```

## Troubleshooting

### "Voice 'af' not found"
✅ **Fixed!** The adapter now filters out short names and only uses valid full names.

### "No such file or directory"
✅ **Fixed!** Script now uses absolute paths based on its own location.

### "Unclosed client session"
✅ **Fixed!** Added proper cleanup in finally blocks.

## Quick Test Command

One-liner from project root:
```bash
echo "1" | ./src/Hypr-Voice/Agent/services/voice/test_tts_voice/run_tests.sh
```

## Integration Example

```python
from services.voice import UnifiedVoiceManager

manager = UnifiedVoiceManager()

# List what's available
print(f"Providers: {manager.list_providers()}")
print(f"Kokoro voices: {len(manager.list_voices('kokoro'))}")

# Use it
manager.set_provider("kokoro")
manager.set_voice("af_bella")

async for audio in manager.stream_from_llm(text_generator):
    # Audio generated and played
    pass
```

## All Fixed Issues Summary

| Issue | Status | Solution |
|-------|--------|----------|
| Import errors | ✅ Fixed | Fallback imports added |
| Path resolution | ✅ Fixed | Auto-detect script location |
| Voice validation | ✅ Fixed | Filter short names |
| Session cleanup | ✅ Fixed | Finally blocks added |
| Bash syntax | ✅ Fixed | Missing quotes added |

## Ready to Use!

The unified TTS system is fully operational. Just run the test script from anywhere in your project!
