# 🎤 Claude TTS CLI - Ready to Use!

## Quick Start

Your Claude TTS CLI is now ready! Here's how to use it:

### 1. Set Environment Variables
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional for premium TTS
export DEEPGRAM_API_KEY="your-deepgram-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"
```

### 2. Start Kokoro for Free TTS (if not already running)
```bash
kokoro-api --port 8880
```

### 3. Use the CLI

#### Interactive Mode
```bash
# Basic usage with free Kokoro TTS
./claude-tts

# With specific voice
./claude-tts --voice af_bella

# With auto-play audio
./claude-tts --auto-play

# With premium providers
./claude-tts --provider deepgram --voice aura-luna-en
./claude-tts --provider elevenlabs --voice rachel
```

#### Quick Message Mode
```bash
# Single message with voice response
./claude-tts --quick "Tell me a fun fact about AI"

# With auto-play
./claude-tts --quick "Hello world!" --auto-play
```

## 🎭 Popular Voices

### Kokoro (Free)
- `af_bella` - Warm, gentle female voice
- `af_sarah` - Clear, professional female voice  
- `am_adam` - Deep, thoughtful male voice
- `bf_emma` - Child voice
- `bm_fable` - Robot voice

### Deepgram (Premium)
- `aura-luna-en` - Premium female voice
- `aura-asteria-en` - Clear female voice
- `aura-stella-en` - Warm female voice

### ElevenLabs (Premium)
- `rachel` - Professional female voice
- `sarah` - Friendly female voice
- `adam` - Confident male voice

## 🎮 CLI Commands

When in interactive mode:
- `help` - Show commands
- `status` - Show agent status
- `voices` - List available voices
- `clear` - Clear screen
- `quit` - Exit

## 📁 Audio Files

Responses are saved to `./cli_tts_output/` as WAV files.

## 🔊 Audio Playback

Install audio player for auto-play:
```bash
sudo apt install ffmpeg  # For ffplay
```

## 🚀 Example Usage

```bash
# Start interactive voice chat
./claude-tts --voice af_bella --auto-play

💬 You: Tell me a story about AI
🤖 Claude: [Response with voice]
🔊 Audio: ./cli_tts_output/claude_response_2024-01-01_12-00-00.wav
🔊 Playing audio...

💬 You: What's the weather like?
🤖 Claude: [Response with voice]
🔊 Audio: ./cli_tts_output/claude_response_2024-01-01_12-01-30.wav
🔊 Playing audio...
```

## 📚 Documentation

- `CLI_QUICK_START.md` - Detailed guide
- `README_CLAUDE_TTS.md` - Technical documentation
- `examples_claude_tts_integration.py` - Code examples

---

Enjoy your voice-powered Claude assistant! 🎉
