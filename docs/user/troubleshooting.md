# Troubleshooting Guide

This guide helps you diagnose and resolve common issues with Hypr-Voice.

## Quick Diagnostics

### Health Check Script

```bash
# Run comprehensive health check
./scripts/start_everything.sh status
```

This checks:
- All service statuses
- Port availability
- Configuration validity
- API connectivity

### Manual Health Check

```bash
# Check each service
curl http://localhost:9099/health  # Whisper
curl http://localhost:9093/health  # Orchestrator
curl http://localhost:9091/health  # Context WS
curl http://localhost:8933  # Web UI
```

---

## Installation Issues

### Problem: Python Dependencies Won't Install

**Symptoms:**
- `pip install` fails
- Import errors
- Missing packages

**Solutions:**

1. **Upgrade pip:**
```bash
pip install --upgrade pip setuptools wheel
```

2. **Install with specific versions:**
```bash
pip install --no-cache-dir -r requirements.txt
```

3. **Check Python version:**
```bash
python3 --version  # Should be 3.10+
```

4. **Create fresh venv:**
```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Problem: PyAudio Installation Fails

**Symptoms:**
- `error: command 'gcc' failed`
- PortAudio not found

**Solutions:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install portaudio19-dev python3-dev
pip install pyaudio
```

**Arch Linux:**
```bash
sudo pacman -S portaudio python
pip install pyaudio
```

**Fedora:**
```bash
sudo dnf install portaudio-devel python3-devel
pip install pyaudio
```

### Problem: Node.js Dependencies Won't Install

**Symptoms:**
- `npm install` fails
- Module not found errors

**Solutions:**

1. **Clear npm cache:**
```bash
npm cache clean --force
```

2. **Delete node_modules:**
```bash
cd web-ui
rm -rf node_modules package-lock.json
npm install
```

3. **Update Node.js:**
```bash
# Install nvm
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# Install latest Node
nvm install node
nvm use node
```

### Problem: API Key Authentication Errors

**Symptoms:**
- 401 Unauthorized
- Invalid API key messages

**Solutions:**

1. **Verify API keys in `.env`:**
```bash
cat .env | grep API_KEY
```

2. **Check for extra spaces:**
```bash
# Should be exactly:
CEREBRAS_API_KEY_ONE=your_key_here
# NOT:
CEREBRAS_API_KEY_ONE = your_key_here  # Wrong!
CEREBRAS_API_KEY_ONE="your_key_here"  # Wrong!
```

3. **Test API keys manually:**
```bash
curl -H "Authorization: Bearer $CEREBRAS_API_KEY_ONE" \
  https://api.cerebras.ai/v1/models
```

4. **Check key status:**
- Verify keys are active
- Check for usage limits
- Confirm no expiration

---

## Service Startup Issues

### Problem: Services Won't Start

**Symptoms:**
- "Failed to start" messages
- Ports already in use
- Permission denied

**Solutions:**

1. **Check if ports are in use:**
```bash
lsof -i :9099  # Whisper
lsof -i :9093  # Orchestrator
lsof -i :9091  # Context WS
lsof -i :8933  # Web UI
```

2. **Kill processes using ports:**
```bash
kill -9 $(lsof -t -i:9099)
# Or for all services:
kill -9 $(lsof -t -i:9099) $(lsof -t -i:9093) $(lsof -t -i:9091)
```

3. **Check permissions:**
```bash
# Make scripts executable
chmod +x scripts/*.sh
chmod +x scripts/utils/*.sh
```

4. **Check log files:**
```bash
tail -50 /tmp/hybrid-whisper-server.log
tail -50 /tmp/hypr-voice-orchestrator.log
```

### Problem: Whisper Server Won't Start

**Symptoms:**
- Whisper status shows offline
- Can't transcribe audio

**Solutions:**

1. **Check Whisper server:**
```bash
./scripts/start_hybrid_server.sh status
```

2. **View logs:**
```bash
tail -f /tmp/hybrid-whisper-server.log
```

3. **Test manually:**
```bash
cd src/hypr_voice/whisper
python server.py
```

4. **Check model download:**
```bash
# Models should be in:
~/.cache/whisper/ or ~/.cache/huggingface/
```

5. **Reinstall Whisper:**
```bash
pip uninstall faster-whisper openai-whisper
pip install faster-whisper openai-whisper
```

### Problem: Web UI Won't Load

**Symptoms:**
- Browser shows connection refused
- Page won't load
- White screen

**Solutions:**

1. **Check if running:**
```bash
ps aux | grep next
```

2. **Start manually:**
```bash
cd web-ui
npm start
```

3. **Check logs:**
```bash
tail -f /tmp/hypr-voice-ui.log
```

4. **Clear browser cache:**
- Hard refresh: Ctrl+Shift+R
- Clear cache and cookies
- Try different browser

5. **Rebuild:**
```bash
cd web-ui
rm -rf .next
npm run build
npm start
```

### Problem: Orchestrator Not Responding

**Symptoms:**
- Agent queries timeout
- No response from agent

**Solutions:**

1. **Check orchestrator:**
```bash
./scripts/start_everything.sh status
```

2. **Test API:**
```bash
curl http://localhost:9093/health
```

3. **View logs:**
```bash
tail -f /tmp/hypr-voice-orchestrator.log
```

4. **Check API keys:**
```bash
echo $CEREBRAS_API_KEY_ONE
```

5. **Restart orchestrator:**
```bash
# Kill process
kill -9 $(lsof -t -i:9093)

# Restart
./scripts/start_everything.sh start
```

---

## Audio Issues

### Problem: Microphone Not Working

**Symptoms:**
- Can't record audio
- No sound detected
- Recording level zero

**Solutions:**

1. **Test microphone:**
```bash
./scripts/utils/test_mic.sh
```

2. **List audio devices:**
```bash
pactl list sources short
```

3. **Check PulseAudio:**
```bash
pulseaudio --check
# If not running:
pulseaudio --start
```

4. **Restart audio:**
```bash
pulseaudio --kill
pulseaudio --start
```

5. **Check permissions:**
```bash
# Add user to audio group
sudo usermod -a -G audio $USER
# Log out and back in
```

6. **Test recording:**
```bash
arecord -f cd -d 5 test.wav
aplay test.wav
```

### Problem: Poor Transcription Quality

**Symptoms:**
- Many incorrect words
- Missing punctuation
- Poor accuracy

**Solutions:**

1. **Check audio quality:**
```bash
./scripts/utils/test_mic.sh
# Look for:
# - Good levels (50-80%)
# - No clipping
# - Low noise
```

2. **Improve audio input:**
- Reduce background noise
- Get closer to microphone
- Speak clearly and at moderate pace
- Use quality microphone

3. **Add custom vocabulary:**
```bash
# Edit vocabulary file
nano config/hypr_voice/whisper/vocabulary.txt

# Add domain-specific terms, one per line
```

4. **Check mode settings:**
```bash
# Try FLOW mode for better accuracy
MODE=FLOW
```

5. **Adjust audio settings:**
```bash
# In config/hypr_voice/whisper/audio-profile.yaml
sample_rate: 16000  # Try 44100 for better quality
channels: 1
```

### Problem: TTS Not Working

**Symptoms:**
- No audio output
- TTS errors in logs

**Solutions:**

1. **Check API key:**
```bash
echo $DEEPGRAM_API_KEY
# or
echo $ELEVENLABS_API_KEY
```

2. **Test TTS manually:**
```bash
# Via Web UI
# Go to TTS Control Panel
# Enter test text and click "Test"
```

3. **Check TTS configuration:**
```bash
# In .env
HYPR_VOICE_TTS_STREAMING=1
HYPR_VOICE_TTS_PROVIDER=deepgram
HYPR_VOICE_TTS_VOICE=aura-luna-en
```

4. **Test audio output:**
```bash
# Test system audio
aplay /usr/share/sounds/alsa/Front_Center.wav
```

5. **Check logs:**
```bash
grep -i tts /tmp/hypr-voice-orchestrator.log
```

---

## Agent Issues

### Problem: Agent Gives Wrong Response

**Symptoms:**
- Irrelevant answer
- Missed the point
- Inappropriate for task

**Solutions:**

1. **Use appropriate agent:**
- Code Agent → Programming tasks
- Research Agent → Information gathering
- Shell Agent → System operations
- Enhanced Context → Context-sensitive tasks

2. **Be more specific:**
```bash
# Instead of:
"Help with this code"

# Try:
"Add error handling to the login function in auth.py"
```

3. **Provide context:**
```bash
# Include relevant information
"I'm working on a Python Flask app and need help with..."
```

4. **Break down complex tasks:**
```bash
# Instead of:
"Build a complete website"

# Try:
"Create the database schema"
"Then create the API endpoints"
"Then create the frontend"
```

### Problem: Agent Won't Use Tools

**Symptoms:**
- Agent says it can't do something
- Tools not available
- Permission errors

**Solutions:**

1. **Check enabled skills:**
```bash
# In Web UI: Skills Library panel
# Verify required tools are enabled
```

2. **Check agent configuration:**
```bash
# In config/hypr_voice/config.yaml
# Verify tools are listed
```

3. **Check file permissions:**
```bash
# Ensure agent can access files
ls -la ~/.config/hypr_voice/
```

4. **Use Enhanced Context Agent:**
- Has access to more tools
- Better for complex tasks

### Problem: Agent Response Too Slow

**Symptoms:**
- Long wait times
- Timeout errors

**Solutions:**

1. **Enable optimizations:**
```bash
# In .env
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_CHUNK_SECONDS=30
FLOW_STREAMING_MODE=1
```

2. **Check network:**
```bash
ping api.cerebras.ai
ping chain-o232k03l.api.baseten.co
```

3. **Reduce query complexity:**
- Break into smaller queries
- Be more specific
- Avoid vague requests

4. **Check API quota:**
- Verify you have credits
- Check rate limits
- Monitor usage

---

## Performance Issues

### Problem: High CPU Usage

**Symptoms:**
- System slows down
- Fans running loud
- High CPU in top

**Solutions:**

1. **Identify the process:**
```bash
ps aux | grep -E "whisper|orchestrator|node"
```

2. **Adjust Whisper model:**
```bash
# In config/hypr_voice/whisper/config.yaml
model_size: "tiny"  # Instead of "base" or "medium"
```

3. **Reduce chunk size:**
```bash
# In .env
WISPR_FLOW_CHUNK_SECONDS=15  # Instead of 30
```

4. **Limit concurrent operations:**
- Don't run multiple recordings simultaneously
- Close unused browser tabs
- Stop other AI services

### Problem: High Memory Usage

**Symptoms:**
- System becomes sluggish
- Swap usage increases
- OOM errors

**Solutions:**

1. **Check memory usage:**
```bash
ps aux --sort=-%mem | head -10
```

2. **Clear caches:**
```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null

# Clear Next.js cache
cd web-ui && rm -rf .next
```

3. **Reduce agent sessions:**
- Close old conversations
- Use shorter conversations
- Clear history periodically

4. **Restart services:**
```bash
./scripts/start_everything.sh restart
```

### Problem: Slow Transcription

**Symptoms:**
- Long wait after recording
- Processing takes too long

**Solutions:**

1. **Enable streaming mode:**
```bash
# In .env
FLOW_STREAMING_MODE=1
```

2. **Use Opus compression:**
```bash
# In .env
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_OPUS_BITRATE=24k
```

3. **Adjust chunk size:**
```bash
# Larger chunks = faster but less responsive
WISPR_FLOW_CHUNK_SECONDS=30
```

4. **Check network speed:**
```bash
speedtest-cli  # Or similar
```

---

## Web UI Issues

### Problem: Can't Access Web UI

**Symptoms:**
- Connection refused
- Page not found
- Blank screen

**Solutions:**

1. **Check if running:**
```bash
curl http://localhost:8933
```

2. **Check port:**
```bash
lsof -i :8933
```

3. **Start manually:**
```bash
cd web-ui
npm start
```

4. **Check firewall:**
```bash
# Allow port 8933
sudo ufw allow 8933
```

5. **Try different browser:**
- Chrome/Chromium
- Firefox
- Edge

### Problem: WebSocket Connection Failed

**Symptoms:**
- Real-time features not working
- Status indicators show offline
- Connection errors in console

**Solutions:**

1. **Check WebSocket server:**
```bash
lsof -i :9091  # Context WS
lsof -i :8934  # Bridge
```

2. **Check browser console:**
- Press F12
- Look for WebSocket errors
- Note error messages

3. **Verify URLs in .env:**
```bash
NEXT_PUBLIC_CONTEXT_WS=ws://localhost:9091/ws
NEXT_PUBLIC_ORCHESTRATOR_WS=ws://localhost:9093/ws
```

4. **Restart WebSocket services:**
```bash
kill -9 $(lsof -t -i:9091)
kill -9 $(lsof -t -i:8934)
./scripts/start_everything.sh start
```

### Problem: Recording Not Working in Web UI

**Symptoms:**
- Can't start recording
- No waveform shown
- Recording immediately stops

**Solutions:**

1. **Check microphone permissions:**
- Allow microphone access in browser
- Check site settings
- Try different browser

2. **Test microphone elsewhere:**
- Test in other websites
- Check system microphone settings

3. **Check browser console:**
- Look for errors
- Note permission denied messages

4. **Use HTTPS (if remote):**
- Web Audio API requires HTTPS
- Or use localhost

---

## Error Messages

### "API Key Invalid"

**Cause:** API key is missing or incorrect

**Solution:**
```bash
# Verify in .env
cat .env | grep API_KEY

# Re-enter key correctly
nano .env
# No quotes, no extra spaces
CEREBRAS_API_KEY_ONE=sk-abc123...
```

### "Port Already in Use"

**Cause:** Another process is using the port

**Solution:**
```bash
# Find process
lsof -i :9099

# Kill process
kill -9 $(lsof -t -i:9099)

# Or change port in .env
HYPR_WHISPER_PORT=9100
```

### "Module Not Found"

**Cause:** Python dependency not installed

**Solution:**
```bash
# Activate venv
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Install specific module
pip install <module_name>
```

### "Connection Refused"

**Cause:** Service not running

**Solution:**
```bash
# Check service status
./scripts/start_everything.sh status

# Start services
./scripts/start_everything.sh start

# Check specific port
curl http://localhost:9099/health
```

### "Permission Denied"

**Cause:** Insufficient permissions

**Solution:**
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Fix file ownership
sudo chown -R $USER:$USER /path/to/Hypr-Voice

# Add to audio group
sudo usermod -a -G audio $USER
```

---

## Getting Help

### Collect Debug Information

Before asking for help, collect this information:

```bash
# System info
uname -a
python3 --version
node --version
npm --version

# Service status
./scripts/start_everything.sh status

# Recent logs
tail -100 /tmp/hybrid-whisper-server.log
tail -100 /tmp/hypr-voice-orchestrator.log
tail -100 /tmp/hypr-voice-ui.log

# Configuration
cat .env | grep -v "API_KEY"  # Hide API keys!
cat config/hypr_voice/whisper/config.yaml

# Error details
grep -i error /tmp/hypr-voice-*.log | tail -50
```

### Enable Debug Logging

In `.env`:
```bash
HYPR_VOICE_TRACE=1
HYPR_VOICE_FLOW_TRACE=1
HYPR_VOICE_TRACE_CONTEXT=1
```

Then check logs:
```bash
tail -f /tmp/hypr-voice-*.log
```

### Common Resources

- **Installation Issues** → [Installation Guide](./installation.md)
- **Feature Questions** → [Features Overview](./features.md)
- **Usage Help** → [Quick Start](./quickstart.md)
- **Web UI Problems** → [Web UI Guide](./web-ui-guide.md)
- **CLI Problems** → [CLI Guide](./cli-guide.md)

### When All Else Fails

1. **Clean restart:**
```bash
# Stop everything
./scripts/start_everything.sh stop

# Kill any remaining processes
kill -9 $(lsof -t -i:9099) $(lsof -t -i:9093) $(lsof -t -i:9091) $(lsof -t -i:8933)

# Start fresh
./scripts/start_everything.sh start
```

2. **Reinstall:**
```bash
# Remove venv
rm -rf .venv

# Create new venv
python3 -m venv .venv
source .venv/bin/activate

# Reinstall
pip install -r requirements.txt

# Reinstall Web UI dependencies
cd web-ui
rm -rf node_modules
npm install
```

3. **Check for updates:**
```bash
git pull origin main
pip install -r requirements.txt --upgrade
cd web-ui && npm update
```

---

## FAQ

### Q: Is Hypr-Voice free?

**A:** It depends on your configuration:
- **LOCAL mode**: Free (uses your own computer)
- **FLOW mode**: Paid API costs (Wispr Flow)
- **LLM**: Paid API costs (Cerebras, Anthropic, etc.)
- **TTS**: Freemium (Deepgram has free tier)

### Q: Can I use offline?

**A:** Partially:
- **LOCAL mode**: Yes, after initial model download
- **FLOW mode**: No, requires internet
- **LLM responses**: No, requires internet
- **TTS**: Only with Kokoro-ONNX (local option)

### Q: What languages are supported?

**A:**
- **Transcription**: 90+ languages (via Whisper)
- **LLM**: English is best, others vary by provider
- **TTS**: Multiple languages (depends on provider)

### Q: How accurate is the transcription?

**A:**
- **LOCAL mode**: Good accuracy (~95%)
- **FLOW mode**: Excellent accuracy (~98%)
- Improves with custom vocabulary
- Depends on audio quality

### Q: Can I use multiple microphones?

**A:** Yes, configure in:
```bash
config/hypr_voice/whisper/audio-profile.yaml
```

### Q: How do I improve response time?

**A:**
1. Enable Opus compression
2. Use streaming mode
3. Increase chunk size
4. Use faster model (Haiku)
5. Improve network speed

### Q: Is my data private?

**A:**
- **LOCAL mode**: Audio stays on your computer
- **FLOW mode**: Audio sent to cloud API
- **LLM**: Queries sent to API provider
- Check provider privacy policies

For more information:
- [Installation Guide](./installation.md)
- [Features Overview](./features.md)
- [Quick Start](./quickstart.md)
