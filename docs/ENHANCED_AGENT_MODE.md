# Enhanced Agent Mode - Smart Context-Aware Voice Input

## Overview

The **Enhanced Agent Mode** provides a faster, smarter AI experience triggered by **Right Control + F9**. This mode automatically gathers context from your current environment and uses AI to provide intelligent, application-aware responses.

## Features

### 🚀 Smart Context Gathering
- **Active Application Detection**: Automatically detects your current app (VSCode, Browser, Terminal, etc.)
- **Window Title Context**: Captures the current window title for additional context
- **Clipboard Integration**: Uses clipboard content when relevant to your query
- **Workspace Awareness**: Knows which workspace you're on

### 🧠 AI-Enhanced Processing
- **Prompt Enhancement**: Your voice input is processed with full context awareness
- **Application-Specific Responses**: Tailored responses based on what you're working on
- **Conversation Memory**: Maintains context across multiple queries
- **TTS Spoken Responses**: Hear the AI's response via Text-to-Speech

### ⚡ Speed Optimizations
- Context gathered **before** recording starts (no waiting)
- Parallel processing of transcription and AI enhancement
- Cached Hyprland client data (100ms TTL) for ultra-fast context lookup

## Keybindings

| Key Combination | Action |
|----------------|---------|
| **F9** (alone) | Basic voice transcription (paste as text) |
| **F10** | Standard agent mode (no context enhancement) |
| **Right Ctrl + F9** | **Enhanced agent mode** (smart context-aware) |

## How It Works

### Press: Right Control + F9

1. **Context Gathering**:
   - Detects active window (class, title, workspace)
   - Captures clipboard content (first 500 chars)
   - Saves context for processing

2. **Recording Starts**:
   - Audio feedback sound plays
   - Red indicator (if visual feedback enabled)
   - Records your voice input

### Release: Right Control + F9

3. **Transcription**:
   - Sends audio to Whisper server
   - Fast transcription with beam search

4. **AI Enhancement**:
   - Combines transcription with gathered context
   - Sends enhanced prompt to orchestrator
   - AI processes with application awareness

5. **Response**:
   - Text response generated
   - Spoken via TTS
   - Conversation ID saved for follow-ups

## Usage Examples

### Example 1: Coding in VSCode

**Context**: You're in VSCode editing `server.py`

**You say**: *"How do I handle async database connections?"*

**AI Response** (context-aware):
> "In Python, for handling async database connections in your Flask server, I recommend using `asyncpg` for PostgreSQL or `motor` for MongoDB. Here's an example for your `server.py`..."

### Example 2: Browser Research

**Context**: You're in Brave browser on a trading analysis page

**You say**: *"Explain this"*

**AI Response** (uses clipboard + window context):
> "Based on the trading chart you have selected, this shows a bullish engulfing pattern indicating potential upward momentum..."

### Example 3: Terminal Commands

**Context**: You're in WezTerm terminal

**You say**: *"Start the development server"*

**AI Response** (context-aware):
> "Based on your current directory, run: `npm run dev` to start your Next.js development server on port 3000."

## Configuration

### Environment Variables

```bash
# Optional: Override defaults
export HYPR_AGENT_PORT=9093          # Orchestrator port
export HYPR_WHISPER_PORT=9099        # Whisper server port
export HYPR_AGENT_TIMEOUT=300        # Response timeout (seconds)
export HYPR_VOICE_LOG_DIR=/tmp/hypr-voice  # Log directory
```

### Audio Source Configuration

The script automatically reads audio source from:
`src/Hypr-Whisper/config/config.yaml`

Or override with:
```bash
export HYPR_AGENT_MIC="alsa_input.usb-Your_Mic-mono-fallback"
```

## Logs and Debugging

### View Logs

```bash
# Real-time logs
tail -f /tmp/hypr-voice/hypr-voice.log

# Filter enhanced agent logs
tail -f /tmp/hypr-voice/hypr-voice.log | grep enhanced
```

### Check Status

```bash
# Check if orchestrator and whisper are running
/home/mewtwo/Zykairotis/Hypr-Voice/scripts/hypr-agent-enhanced.sh status
```

### Test Manually

```bash
# Start recording (won't stop automatically)
/home/mewtwo/Zykairotis/Hypr-Voice/scripts/hypr-agent-enhanced.sh start

# Process the recording
/home/mewtwo/Zykairotis/Hypr-Voice/scripts/hypr-agent-enhanced.sh process
```

## Troubleshooting

### Issue: No response or timeout

**Solution**:
1. Check if orchestrator is running:
   ```bash
   curl http://localhost:9093/health
   ```

2. Check if Whisper server is running:
   ```bash
   curl http://localhost:9099/health
   ```

3. Increase timeout:
   ```bash
   export HYPR_AGENT_TIMEOUT=600  # 10 minutes
   ```

### Issue: Context not gathered

**Solution**:
1. Verify `hyprctl` is available:
   ```bash
   hyprctl activewindow -j
   ```

2. Check if `wl-paste` works:
   ```bash
   wl-paste
   ```

### Issue: No TTS output

**Solution**:
1. Check TTS provider configuration in orchestrator
2. Verify audio output device
3. Check logs for TTS errors

## Comparison: Standard vs Enhanced Mode

| Feature | F10 (Standard) | Right Ctrl + F9 (Enhanced) |
|---------|---------------|---------------------------|
| Context Gathering | ❌ No | ✅ Yes (app, clipboard, window) |
| AI Enhancement | Basic | Smart context-aware |
| Speed | Normal | Optimized (parallel processing) |
| Application Awareness | ❌ No | ✅ Yes |
| Response Quality | Good | Excellent (context-specific) |
| Conversation Memory | ✅ Yes | ✅ Yes |
| TTS Output | ✅ Yes | ✅ Yes |

## Advanced Features

### Conversation Continuity

The enhanced agent maintains conversation context across multiple queries:

1. **First query**: *"What's the best way to handle authentication?"*
2. **Follow-up**: *"Show me an example"* ← Knows you mean authentication
3. **Third query**: *"What about refresh tokens?"* ← Continues the auth topic

### Context-Aware Clipboard

If you copy code/text before using the agent:

```python
# You copy this code
async def get_user(user_id: int):
    # TODO: Implement
    pass
```

**You say**: *"Complete this function"*

**AI Response**: Uses copied code as context and provides implementation.

## Tips for Best Results

1. **Be Specific**: "Explain this chart" works better when you have relevant content in clipboard
2. **Use Follow-ups**: Take advantage of conversation memory for multi-turn interactions
3. **Context Matters**: The AI knows what app you're in, so "open the settings" will be app-specific
4. **Clipboard is Key**: Copy relevant text/code before asking about it

## File Locations

- **Script**: `/home/mewtwo/Zykairotis/Hypr-Voice/scripts/hypr-agent-enhanced.sh`
- **Config**: `/home/mewtwo/.config/hypr/hyprvoice.conf`
- **Logs**: `/tmp/hypr-voice/hypr-voice.log`
- **State Files**: `/tmp/hypr-agent-enhanced-*`

## Related Documentation

- [Standard Agent Mode (F10)](./AGENT_MODE.md)
- [Basic Voice Input (F9)](./VOICE_INPUT.md)
- [Hyprland Tools Integration](../src/hypr_voice/services/tools/hyprland_ss_ctx.py)
- [Voice Orchestrator](../src/hypr_voice/orchestrator/voice_orchestrator.py)

---

**Enjoy your enhanced, context-aware AI assistant! 🚀**
