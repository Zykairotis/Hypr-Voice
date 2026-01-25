# Claude TTS CLI - Quick Start Guide

## 🚀 Setup

### 1. Environment Variables
```bash
# Required for Claude
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional for premium TTS
export DEEPGRAM_API_KEY="your-deepgram-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"

# For local Kokoro TTS (free)
kokoro-api --port 8880  # Start Kokoro server
```

### 2. Activate Virtual Environment
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice
source .venv/bin/activate
```

## 💬 Usage

### Interactive Mode (Default)
```bash
# Basic usage with Kokoro (free)
python -m hypr_voice.cli.tts

# Use Deepgram (premium, requires API key)
python -m hypr_voice.cli.tts --provider deepgram

# Use ElevenLabs (premium, requires API key)
python -m hypr_voice.cli.tts --provider elevenlabs

# Use specific voice
python -m hypr_voice.cli.tts --voice af_bella

# Auto-play audio responses
python -m hypr_voice.cli.tts --auto-play
```

### Quick Message Mode
```bash
# Single message with voice response
python -m hypr_voice.cli.tts --quick "Tell me a fun fact about space"

# Quick message with specific provider
python -m hypr_voice.cli.tts --quick "What's the weather like?" --provider deepgram

# Quick message with auto-play
python -m hypr_voice.cli.tts --quick "Hello world!" --auto-play
```

## 🎭 Available Voices

### Kokoro (Free, Local)
```bash
# Female voices
python -m hypr_voice.cli.tts --voice af_bella    # Warm, gentle
python -m hypr_voice.cli.tts --voice af_sarah    # Clear, professional
python -m hypr_voice.cli.tts --voice af_sky      # Friendly, energetic

# Male voices
python -m hypr_voice.cli.tts --voice am_adam     # Deep, thoughtful
python -m hypr_voice.cli.tts --voice am_michael  # Confident, clear

# Special voices
python -m hypr_voice.cli.tts --voice bf_emma     # Child voice
python -m hypr_voice.cli.tts --voice bm_fable    # Robot voice
```

### Deepgram (Premium, Cloud)
```bash
python -m hypr_voice.cli.tts --provider deepgram --voice aura-luna-en
python -m hypr_voice.cli.tts --provider deepgram --voice aura-asteria-en
python -m hypr_voice.cli.tts --provider deepgram --voice aura-stella-en
```

### ElevenLabs (Premium, Cloud)
```bash
python -m hypr_voice.cli.tts --provider elevenlabs --voice rachel
python -m hypr_voice.cli.tts --provider elevenlabs --voice sarah
python -m hypr_voice.cli.tts --provider elevenlabs --voice adam
```

## 🎮 Interactive Commands

Once in the CLI, you can use these commands:

- `help` - Show available commands
- `status` - Show agent and TTS status
- `voices` - List available voices for current provider
- `clear` - Clear the screen
- `quit` or `exit` or `q` - Exit the CLI

## 📁 Output Files

Audio files are saved to `var/hypr_voice/cli_tts_output/history/` by default:
```
var/
└── hypr_voice/
    └── cli_tts_output/
        └── history/
            ├── claude_response_2024-01-01_12-00-00.wav
            ├── claude_response_2024-01-01_12-01-30.wav
            └── ...
```

## 🔊 Audio Playback

### Auto-play
```bash
python -m hypr_voice.cli.tts --auto-play
```

Requires one of these audio players:
- `ffplay` (from ffmpeg)
- `aplay` (Linux)
- `paplay` (Linux PulseAudio)
- `mpg123` (Cross-platform)

### Manual Playback
```bash
# Play with ffplay
ffplay -nodisp -autoexit var/hypr_voice/cli_tts_output/history/claude_response_*.wav

# Play with aplay (Linux)
aplay var/hypr_voice/cli_tts_output/history/claude_response_*.wav

# Play with paplay (Linux)
paplay var/hypr_voice/cli_tts_output/history/claude_response_*.wav
```

## 🛠️ Troubleshooting

### Claude API Key Not Set
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Kokoro Server Not Running
```bash
# Start Kokoro API server
kokoro-api --port 8880

# Check if running
curl http://localhost:8880/health
```

### Audio Not Playing
```bash
# Install audio player
sudo apt install ffmpeg  # For ffplay
# or
sudo apt install alsa-utils  # For aplay
# or
sudo apt install mpg123  # For mpg123
```

### TTS Provider Not Available
```bash
# Check provider status in CLI
python -m hypr_voice.cli.tts
> status

# Try different provider
python -m hypr_voice.cli.tts --provider kokoro  # Always available
```

## 📝 Example Sessions

### Voice Assistant
```bash
$ python -m hypr_voice.cli.tts --voice af_bella --auto-play

🤖 Claude TTS CLI - Interactive Voice Assistant
==================================================
🎤 TTS Provider: kokoro
🎭 Voice: af_bella
📁 Output Directory: var/hypr_voice/cli_tts_output/history
🔊 Auto-play: Enabled

Type 'help' for commands or 'quit' to exit.
--------------------------------------------------

💬 You: Tell me a short joke
🤖 Claude: Why don't scientists trust atoms? Because they make up everything!
🔊 Voice: af_bella
📁 Audio: var/hypr_voice/cli_tts_output/history/claude_response_2024-01-01_12-00-00.wav
🔊 Playing audio...

💬 You: What's the weather like today?
🤖 Claude: I don't have access to real-time weather data, but you can check your local weather app or website for current conditions in your area.
🔊 Voice: af_bella
📁 Audio: var/hypr_voice/cli_tts_output/history/claude_response_2024-01-01_12-01-30.wav
🔊 Playing audio...
```

### Quick Messages
```bash
$ python -m hypr_voice.cli.tts --quick "Explain quantum computing in simple terms" --auto-play

🤖 Claude: Processing your message...

📝 Response: Quantum computing uses quantum bits or qubits that can exist in multiple states simultaneously, allowing computers to process many possibilities at once and solve certain complex problems much faster than traditional computers.

🔊 Voice: af_bella
📁 Audio: ./cli_tts_output/claude_response_2024-01-01_12-05-00.wav
🔊 Playing audio...
```

## 🎯 Tips for Best Experience

1. **Use Kokoro for testing** - It's free and works offline
2. **Use headphones** - Better voice quality experience
3. **Short questions** - Get more natural voice responses
4. **Auto-play for convenience** - Hands-free experience
5. **Check voices command** - Discover all available voices

## 🚀 Advanced Usage

### Custom Output Directory
```bash
python -m hypr_voice.cli.tts --output-dir ~/my_claudio_responses
```

### Scripting
```bash
#!/bin/bash
# Batch processing
questions=(
    "What is artificial intelligence?"
    "How does photosynthesis work?"
    "Explain the theory of relativity"
)

for question in "${questions[@]}"; do
    python -m hypr_voice.cli.tts --quick "$question" --voice af_bella
done
```

### Voice Switching
```bash
# Start with one voice
python -m hypr_voice.cli.tts --voice af_bella

# In CLI, check available voices
> voices

# Exit and restart with different voice
python -m hypr_voice.cli.tts --voice am_adam
```

---

Enjoy your voice-powered Claude assistant! 🎉
