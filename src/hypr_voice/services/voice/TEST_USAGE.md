# TTS Test Script Usage

## Quick Start

```bash
# Test with Kokoro (local, no API key needed)
python test_tts.py --provider kokoro --voice af_bella

# Test with Deepgram
python test_tts.py --provider deepgram --voice luna --model aura-2

# Test with ElevenLabs
python test_tts.py --provider elevenlabs --voice rachel --model eleven_turbo_v2_5

# Test with custom speed
python test_tts.py --provider kokoro --voice am_adam --speed 1.5
```

## Command-Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--provider` | `-p` | TTS provider (kokoro, deepgram, elevenlabs) | kokoro |
| `--voice` | `-v` | Voice name | default/random |
| `--model` | `-m` | Model name | provider default |
| `--speed` | `-s` | Speech speed (0.5-2.0) | 1.0 |
| `--text` | `-t` | Custom text to speak | default test text |
| `--show-text` | | Show the default test text | |

## Available Voices

### Kokoro (Local)
```bash
# Female voices
python test_tts.py -p kokoro -v af_bella
python test_tts.py -p kokoro -v af_sarah
python test_tts.py -p kokoro -v af_sky
python test_tts.py -p kokoro -v af_nicole

# Male voices
python test_tts.py -p kokoro -v am_adam
python test_tts.py -p kokoro -v am_michael
python test_tts.py -p kokoro -v am_echo

# British voices
python test_tts.py -p kokoro -v bf_emma
python test_tts.py -p kokoro -v bm_george
```

### Deepgram (Cloud)
```bash
# Female voices
python test_tts.py -p deepgram -v luna -m aura-2
python test_tts.py -p deepgram -v athena -m aura-2
python test_tts.py -p deepgram -v asteria -m aura-1

# Male voices
python test_tts.py -p deepgram -v apollo -m aura-2
python test_tts.py -p deepgram -v atlas -m aura-1
python test_tts.py -p deepgram -v hermes -m aura-2
```

### ElevenLabs (Premium)
```bash
# Female voices
python test_tts.py -p elevenlabs -v rachel -m eleven_turbo_v2_5
python test_tts.py -p elevenlabs -v sarah -m eleven_flash_v2_5
python test_tts.py -p elevenlabs -v emily -m eleven_multilingual_v2

# Male voices
python test_tts.py -p elevenlabs -v adam -m eleven_turbo_v2_5
python test_tts.py -p elevenlabs -v antoni -m eleven_flash_v2_5
python test_tts.py -p elevenlabs -v brian -m eleven_turbo_v2_5
```

## Speed Examples

```bash
# Slower speech (0.8x)
python test_tts.py -p kokoro -v af_bella -s 0.8

# Normal speech (1.0x - default)
python test_tts.py -p kokoro -v af_bella -s 1.0

# Faster speech (1.5x)
python test_tts.py -p kokoro -v af_bella -s 1.5

# Very fast speech (2.0x)
python test_tts.py -p kokoro -v af_bella -s 2.0
```

## Custom Text

```bash
# Custom text
python test_tts.py -p kokoro -v af_bella -t "Hello world, this is a custom message!"

# Show default test text
python test_tts.py --show-text
```

## Test Text Features

The default test text includes:
- ✅ Numbers: 1, 2, 3, 1,234,567
- ✅ Dates & Times: 10/30/2025, 3:45 PM
- ✅ Currency: $99.99, €50, £30, ¥1000
- ✅ Percentages: 25%
- ✅ Email & URLs: user@example.com, https://example.com
- ✅ Punctuation: quotes, hyphens, parentheses, brackets
- ✅ Mathematical expressions: 2 + 2 = 4
- ✅ Special characters: #, @, *, _, ~, |, \, ^
- ✅ Contractions: I'm, you're, won't, can't
- ✅ Mixed case: CAPS, lowercase, MiXeD

## Output

Audio files are saved to: `./tts_test_output/`

File naming format: `{provider}_{voice}_{timestamp}.mp3`

Example: `kokoro_af_bella_20251030_063000.mp3`

## Requirements

### Kokoro
- Kokoro server running on localhost:8880
- No API key required

### Deepgram
- Set environment variable: `export DEEPGRAM_API_KEY="your_key"`

### ElevenLabs
- Set environment variable: `export ELEVENLABS_API_KEY="your_key"`

## Troubleshooting

### "Kokoro API error: 400"
- Make sure Kokoro server is running: `python Kokoro-FastAPI/server.py --host 0.0.0.0 --port 8880`
- Check that the voice name is correct

### "DEEPGRAM_API_KEY not set"
- Set your API key: `export DEEPGRAM_API_KEY="your_key"`

### "ELEVENLABS_API_KEY not set"
- Set your API key: `export ELEVENLABS_API_KEY="your_key"`

## Complete Examples

```bash
# Test all providers with same voice characteristics
python test_tts.py -p kokoro -v af_bella -s 1.0
python test_tts.py -p deepgram -v luna -m aura-2 -s 1.0
python test_tts.py -p elevenlabs -v rachel -m eleven_turbo_v2_5 -s 1.0

# Test speed variations
python test_tts.py -p kokoro -v af_bella -s 0.8  # Slow
python test_tts.py -p kokoro -v af_bella -s 1.0  # Normal
python test_tts.py -p kokoro -v af_bella -s 1.5  # Fast

# Test different voice types
python test_tts.py -p kokoro -v af_bella     # Female American
python test_tts.py -p kokoro -v am_adam      # Male American
python test_tts.py -p kokoro -v bf_emma      # Female British
python test_tts.py -p kokoro -v bm_george    # Male British
```
