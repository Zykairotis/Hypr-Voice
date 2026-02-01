# Claude AI SDK Integration Guide

## Overview

Hypr-Voice integrates with Claude AI through two primary methods:
1. **Claude Agent SDK** - API-based integration with Anthropic's Claude
2. **Local Claude Code** - Integration with locally installed Claude Code CLI

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude TTSAgent                          │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐    ┌───────────────────────────┐ │
│  │  Claude Agent SDK    │    │  Local Claude Code        │ │
│  │  (API-based)         │    │  (CLI subprocess)         │ │
│  └──────────┬───────────┘    └───────────┬───────────────┘ │
│             │                             │                  │
│             └──────────┬──────────────────┘                  │
│                        │                                     │
│                   ┌────▼─────┐                               │
│                   │  Chat    │                               │
│                   │ Handler  │                               │
│                   └────┬─────┘                               │
│                        │                                     │
│                   ┌────▼─────┐    ┌──────────────────────┐   │
│                   │   TTS    │◄───┤  Text-to-Speech      │   │
│                   │ Optional │    │  Integration         │   │
│                   └──────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Required for API-based Claude
ANTHROPIC_API_KEY=your_api_key_here

# Optional: Custom Claude Code binary path
CLAUDE_CODE_PATH=/usr/local/bin/claude
```

### Python Installation

```bash
pip install claude-agent-sdk
```

### Local Claude Code Setup

```bash
# Install Claude Code CLI
npm install -g @anthropic-ai/claude-code

# Verify installation
claude --version
```

## Usage

### Basic Usage

```python
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

async def basic_example():
    # Initialize agent
    agent = ClaudeTTSAgent(
        api_key="your_anthropic_api_key",
        enable_tts=True,
        tts_provider="kokoro",
        tts_voice="af_bella"
    )

    # Connect to Claude
    await agent.connect()

    # Send message
    result = await agent.chat("Hello! How are you?")

    print(f"Response: {result['response']}")
    if result.get('tts_synthesized'):
        print(f"Audio: {result['audio_file']}")

    # Close connection
    await agent.close()
```

### Using Local Claude Code

```python
agent = ClaudeTTSAgent(
    use_local_claude=True,
    enable_tts=False,  # Local Claude doesn't support TTS
    working_directory="/path/to/project"
)

await agent.connect()
result = await agent.chat("Analyze this codebase")
await agent.close()
```

### With Context Manager

```python
async with ClaudeTTSAgent(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    tts_provider="deepgram",
    tts_voice="aura-asteria-en"
) as agent:
    result = await agent.chat(
        "Tell me a short story about AI",
        synthesize_response=True
    )
```

### Custom System Prompt

```python
agent = ClaudeTTSAgent(
    api_key=api_key,
    system_prompt="""You are a voice assistant specializing in
    clear, concise responses optimized for text-to-speech.
    Use simple language and avoid complex punctuation."""
)
```

### TTS-Only Mode

```python
# Synthesize text without Claude processing
result = await agent.synthesize_only(
    text="Hello, world!",
    provider="elevenlabs",
    voice="rachel"
)
```

### Available Voices

```python
# Get all available voices
voices = await agent.get_available_voices(provider="all")
print(voices)

# Get specific provider voices
kokoro_voices = await agent.get_available_voices(provider="kokoro")
deepgram_voices = await agent.get_available_voices(provider="deepgram")
elevenlabs_voices = await agent.get_available_voices(provider="elevenlabs")
```

## Agent Options

### Claude Agent Options

```python
from hypr_voice.services.sdk_compat import ClaudeAgentOptions

options = ClaudeAgentOptions(
    system_prompt="Custom system prompt",
    max_turns=5,
    permission_mode="default",
    cwd="/working/directory",
    setting_sources=["project"],
    allowed_tools=[
        "Read", "Write", "Edit", "Grep",
        "Glob", "Bash", "Skill", "SlashCommand"
    ]
)
```

### TTS Configuration

```python
from hypr_voice.services.voice import TTSConfig, TTSProvider

config = TTSConfig(
    provider=TTSProvider.KOKORO,
    voice="af_bella",
    speed=1.0,
    sample_rate=48000,
    output_format="mp3",
    use_streaming=True,
    stream_and_play=False
)
```

## Quick Chat Function

```python
from hypr_voice.services.claude_tts_agent import quick_chat

# Simple one-liner
result = await quick_chat(
    message="What's the weather like?",
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    tts_provider="kokoro",
    synthesize=True
)
```

## Troubleshooting

### Claude SDK Not Available

**Error**: `ImportError: Claude Agent SDK is required`

**Solution**:
```bash
pip install claude-agent-sdk
```

### API Key Not Found

**Error**: `ValueError: API key is required`

**Solution**:
```bash
export ANTHROPIC_API_KEY=your_key_here
```

### Local Claude Code Not Detected

**Issue**: Local Claude integration not working

**Solution**:
```bash
# Verify Claude Code is installed
which claude

# Check version
claude --version

# Install if missing
npm install -g @anthropic-ai/claude-code
```

### TTS Initialization Failed

**Error**: `Failed to initialize TTS`

**Solution**:
- Check TTS provider API keys
- Verify TTS server is running (for Kokoro)
- Check network connectivity

### Connection Timeout

**Error**: `Request timeout for query`

**Solution**:
```python
agent = ClaudeTTSAgent(
    api_key=api_key,
    # Increase timeout
    # (Note: timeout is handled in the query method)
)

result = await agent.chat(
    message="...",
    timeout=120  # 2 minutes
)
```

## Best Practices

### 1. Use Context Managers

```python
# Good
async with ClaudeTTSAgent(api_key=key) as agent:
    result = await agent.chat("...")

# Avoid
agent = ClaudeTTSAgent(api_key=key)
await agent.connect()
# ... error occurs here ...
await agent.close()  # Never reached
```

### 2. Handle Errors Gracefully

```python
try:
    result = await agent.chat("...")
    if result['success']:
        print(result['response'])
    else:
        print(f"Error: {result['error']}")
except Exception as e:
    logger.error(f"Chat failed: {e}")
```

### 3. Optimize for Voice Output

```python
system_prompt = """You are a voice assistant. Follow these guidelines:
- Use clear, concise language
- Avoid complex punctuation
- Break long responses into shorter paragraphs
- Use conversational tone when appropriate
- Spell out abbreviations (e.g., "AI" as "A I")
"""

agent = ClaudeTTSAgent(
    api_key=api_key,
    system_prompt=system_prompt
)
```

### 4. Monitor Resource Usage

```python
# Check agent status
status = agent.get_status()
print(f"Claude SDK: {status['claude_sdk_available']}")
print(f"Claude Code Local: {status['claude_code_local']}")
print(f"TTS Available: {status['tts_available']}")
print(f"Connected: {status['connected']}")
```

### 5. Use Appropriate TTS Settings

```python
# For fast responses
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    use_streaming=True,
    stream_and_play=True
)

# For high quality
config = TTSConfig(
    provider=TTSProvider.ELEVENLABS,
    model="eleven_turbo_v2_5",
    sample_rate=48000
)
```

## API Reference

### ClaudeTTSAgent

**Constructor Parameters**:
- `api_key` (str, optional): Anthropic API key
- `enable_tts` (bool): Enable TTS capabilities (default: True)
- `tts_provider` (str): TTS provider name (default: "kokoro")
- `tts_voice` (str, optional): Specific voice to use
- `working_directory` (str, optional): Working directory for file operations
- `system_prompt` (str, optional): Custom system prompt
- `use_local_claude` (bool): Use local Claude Code (default: False)

**Methods**:
- `async connect()`: Connect to Claude (API or local)
- `async close()`: Close connection
- `async chat(message, synthesize_response=None, **kwargs)`: Send message and get response
- `async synthesize_only(text, provider=None, voice=None, **kwargs)`: TTS only
- `async get_available_voices(provider="all")`: List available voices
- `get_status()`: Get agent status

### LocalClaudeCodeIntegration

**Constructor Parameters**:
- `working_directory` (str, optional): Working directory

**Methods**:
- `async query(prompt, timeout=60)`: Query Claude Code
- `get_status()`: Get Claude Code status

## Integration Examples

### Discord Bot Integration

```python
from hypr_voice.services.tools.discord_tool import DiscordClient
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

discord = DiscordClient()
await discord.initialize()

claude = ClaudeTTSAgent(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    enable_tts=True
)
await claude.connect()

async def handle_discord_message(message):
    result = await claude.chat(message.content)

    if result.get('tts_synthesized'):
        # Send audio file to Discord
        await discord.send_file(
            message.channel.id,
            result['audio_file'],
            content=result['response']
        )
    else:
        await discord.send_message(
            message.channel.id,
            result['response']
        )
```

### Telegram Bot Integration

```python
from hypr_voice.services.tools.telegram_tool import TelegramClient

telegram = TelegramClient()
await telegram.initialize()

claude = ClaudeTTSAgent(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    tts_provider="kokoro"
)
await claude.connect()

async def handle_telegram_message(update):
    result = await claude.chat(update.message.text)

    if result.get('tts_synthesized'):
        await telegram.send_file(
            update.message.chat.id,
            result['audio_file'],
            caption=result['response']
        )
```

### Voice Pipeline Integration

```python
from hypr_voice.services.wispr_flow_direct import WisprFlowDirect

wispr = WisprFlowDirect()
await wispr.connect()

claude = ClaudeTTSAgent(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    enable_tts=True
)
await claude.connect()

async def voice_pipeline(audio_path):
    # Transcribe audio
    transcription = await wispr.transcribe(audio_path)

    # Process with Claude
    result = await claude.chat(transcription['text'])

    # Synthesize response
    if result.get('tts_synthesized'):
        return result['audio_file']

    return None
```

## Performance Tips

1. **Use Streaming**: Enable TTS streaming for faster response times
2. **Cache Voices**: Pre-select voices to avoid runtime lookups
3. **Connection Pooling**: Reuse agent instances across multiple requests
4. **Batch Processing**: Process multiple messages in a single session
5. **Local Claude**: Use local Claude Code for code analysis tasks

## Security Considerations

1. **API Keys**: Never commit API keys to version control
2. **Permissions**: Use appropriate permission_mode for Claude Agent SDK
3. **File Access**: Be mindful of working_directory permissions
4. **Rate Limiting**: Implement rate limiting for production use
5. **Input Validation**: Validate and sanitize user input

## Related Documentation

- [TTS Integration](./tts-integration.md)
- [Wispr Flow Integration](../api/wispr-flow-api.md)
- [Bot Integrations](./bot-integrations.md)
- [MCP Integration](./mcp-integration.md)
