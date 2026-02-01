# Claude Integration Guide

How to integrate Hypr-Voice with Claude and Claude Code.

## Table of Contents

- [Overview](#overview)
- [Claude SDK Integration](#claude-sdk-integration)
- [Claude Code Integration](#claude-code-integration)
- [Context-Aware Responses](#context-aware-responses)
- [Voice with Claude](#voice-with-claude)
- [Examples](#examples)

---

## Overview

Hypr-Voice provides deep integration with Claude through multiple methods:

| Integration Type | Description | Use Case |
|------------------|-------------|----------|
| **Claude API** | Direct API calls | Simple Claude access |
| **Claude SDK** | Enhanced SDK with monitoring | Context-aware responses |
| **Claude Code** | Full Claude Code integration | Development workflows |

---

## Claude SDK Integration

### Configure Claude SDK

```yaml
# config/hypr_voice/claude-sdk.yaml

sdk:
  use_code_sdk: false           # Use API instead of Code
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 8096
  temperature: 1.0
  session_timeout: 3600
```

### Set API Key

```bash
# Add to .env
export ANTHROPIC_AUTH_TOKEN="your_claude_api_key"
export ANTHROPIC_BASE_URL="https://api.anthropic.com"
```

### Basic Usage

```python
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

async def basic_claude():
    async with ClaudeTTSAgent(
        model="claude-3-5-sonnet-20241022",
        system_prompt="You are a helpful assistant."
    ) as claude:

        result = await claude.chat(
            message="What's Python?",
            synthesize_response=False
        )

        print(f"Response: {result['response']}")
```

---

## Claude Code Integration

### Configure Claude Code

```yaml
# config/hypr_voice/claude-sdk.yaml

sdk:
  use_code_sdk: true            # Enable Claude Code
  model: "claude-3-5-sonnet-20241022"
```

### Enable Monitoring

```yaml
monitoring:
  enabled: true
  interval: 0.15                # 150ms update rate
  include_context: true
  monitor_all_workspaces: true
```

### Application Context

```yaml
applications:
  profiles:
    development:
      window_classes: ['Code', 'vim', 'nvim']
      extra_context: "User is coding. Provide technical assistance."

    browser:
      window_classes: ['firefox', 'chrome']
      extra_context: "User is browsing. Offer web assistance."
```

### Usage with Monitoring

```python
async def claude_with_monitoring():
    async with ClaudeTTSAgent(
        use_claude_code=True,
        enable_monitoring=True,
        monitor_interval=0.15
    ) as claude:

        # Claude knows what application you're using
        result = await claude.chat(
            message="Help me with this function",
            synthesize_response=True
        )

        print(f"Response: {result['response']}")
```

---

## Context-Aware Responses

### How It Works

1. **Application Detection** - Identifies active application
2. **Context Extraction** - Gets window title, class, workspace
3. **Vocabulary Selection** - Selects relevant vocabulary
4. **Enhanced Prompt** - Adds context to Claude prompt

### Configure Context

```yaml
context:
  include_window_class: true
  include_window_title: true
  include_vocabulary: true
  include_workspace: true
  max_vocabulary_terms: 20
```

### Enable Vocabulary Integration

```yaml
vocabulary:
  use_vocabulary_manager: true
  config_path: "config/hypr_voice/whisper"
  cache_vocabularies: true
  fuzzy_match_threshold: 0.85
```

### Context-Aware Example

```python
async def context_aware_example():
    # When in VSCode, Claude provides coding help
    # When in browser, Claude provides web assistance
    # When in terminal, Claude provides command-line help

    async with ClaudeTTSAgent(
        enable_monitoring=True,
        include_vocabulary=True
    ) as claude:

        # Response adapts to current application
        result = await claude.chat(
            message="How do I do X?",
            synthesize_response=True
        )
```

---

## Voice with Claude

### Text-to-Speech with Claude

```python
async def claude_tts():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        enable_monitoring=True
    ) as claude:

        # Claude speaks its response
        result = await claude.chat(
            message="Explain quantum computing",
            synthesize_response=True
        )

        print(f"Response: {result['response']}")
        print(f"Audio: {result['audio_file']}")
```

### Voice Presets with Claude

```python
async def claude_voice_presets():
    # Professional explanations
    async with ClaudeTTSAgent(
        tts_voice="am_adam",      # Professional voice
        preset="professional"
    ) as claude:
        result = await claude.chat(
            "Explain the architecture",
            synthesize_response=True
        )

    # Friendly explanations
    async with ClaudeTTSAgent(
        tts_voice="af_sky",       # Friendly voice
        preset="friendly"
    ) as claude:
        result = await claude.chat(
            "What's machine learning?",
            synthesize_response=True
        )
```

---

## Examples

### Coding Assistant

```python
async def coding_assistant():
    """Claude helps with coding while knowing the active file"""

    async with ClaudeTTSAgent(
        enable_monitoring=True,
        system_prompt="""You are a coding assistant that provides
        context-aware help based on the active file and application."""
    ) as assistant:

        # While in VSCode, working on Python file
        result = await assistant.chat(
            "How do I optimize this function?",
            synthesize_response=True
        )

        # Claude knows:
        # - You're in VSCode
        # - The file is Python
        # - Relevant programming vocabulary
```

### Voice Code Review

```python
async def voice_code_review():
    """Claude provides spoken code reviews"""

    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="am_adam",      # Professional male voice
        system_prompt="You are a senior engineer providing code reviews."
    ) as reviewer:

        code = '''
def calculate(data):
    result = 0
    for item in data:
        result += item
    return result
        '''

        prompt = f"Review this code for improvements:\n{code}"

        result = await reviewer.chat(
            prompt,
            synthesize_response=True
        )

        # Claude speaks the review
        print(f"Review: {result['response']}")
        print(f"Audio: {result['audio_file']}")
```

### Meeting Assistant

```python
async def meeting_assistant():
    """Claude assists during meetings with voice"""

    async with ClaudeTTSAgent(
        tts_provider="deepgram",   # Natural voice
        tts_voice="luna",         # Friendly voice
        enable_monitoring=True,
        system_prompt="""You are a meeting assistant that provides
        concise, helpful responses during meetings."""
    ) as assistant:

        # Transcribe and respond
        while True:
            # Get spoken input
            transcription = await get_speech_input()

            # Get Claude's response
            result = await assistant.chat(
                transcription,
                synthesize_response=True
            )

            # Play response
            play_audio(result['audio_file'])
```

### Learning Assistant

```python
async def learning_assistant():
    """Claude teaches new concepts with voice"""

    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",     # Clear, educational voice
        enable_monitoring=False,
        system_prompt="""You are a patient tutor that explains
        concepts clearly and step-by-step."""
    ) as tutor:

        topics = [
            "Explain async/await in Python",
            "What is a REST API?",
            "How does Docker work?"
        ]

        for topic in topics:
            print(f"\nQ: {topic}")

            result = await tutor.chat(
                topic,
                synthesize_response=True
            )

            print(f"A: {result['response'][:100]}...")
            print(f"🔊 Audio available")

            # Wait for user to be ready
            input("Press Enter for next topic...")
```

---

## Advanced Configuration

### Claude SDK with All Features

```python
async def full_claude_sdk():
    async with ClaudeTTSAgent(
        # Claude settings
        model="claude-3-5-sonnet-20241022",
        max_tokens=8096,
        temperature=0.7,

        # Monitoring
        enable_monitoring=True,
        monitor_interval=0.15,
        include_vocabulary=True,

        # Voice
        tts_provider="kokoro",
        tts_voice="af_bella",
        auto_synthesize=True,

        # System prompt
        system_prompt="""You are a context-aware assistant that
        provides helpful responses based on the active application
        and user context."""
    ) as assistant:

        # Full-featured context-aware voice assistant
        result = await assistant.chat(
            "Help me understand this code",
            synthesize_response=True
        )
```

### Custom Application Profiles

```yaml
# config/hypr_voice/claude-sdk.yaml

applications:
  profiles:
    # Custom profile for specific app
    obsidian:
      window_classes: ['obsidian']
      extra_context: "User is working with notes. Help with knowledge management."
      vocabulary: "productivity"

    # Custom profile for game development
    game_dev:
      window_classes: ['unity', 'unreal', 'godot']
      extra_context: "User is developing a game. Provide game dev help."
      vocabulary: "development"
```

---

## Troubleshooting

### Claude Code Not Detected

```bash
# Ensure Claude Code is running
claude --version

# Check installation
which claude

# Set path if needed
export PATH="$PATH:/path/to/claude"
```

### Monitoring Not Working

```bash
# Check Hyprland is running
hyprctl version

# Check monitoring permissions
# Ensure agent has access to Hyprland socket

# Test monitoring
python -c "from hypr_voice.claude_sdk.monitoring import AppMonitor; print('OK')"
```

### Context Not Included

```yaml
# Ensure settings are correct
monitoring:
  enabled: true
  include_context: true

context:
  include_window_class: true
  include_window_title: true
  include_vocabulary: true
```

---

## Best Practices

### For Development

```python
# Use professional voice, technical vocabulary
async with ClaudeTTSAgent(
    tts_voice="am_adam",
    vocabulary="development",
    system_prompt="You are a technical assistant providing code help."
) as assistant:
    # ...
```

### For Meetings

```python
# Use friendly voice, concise responses
async with ClaudeTTSAgent(
    tts_voice="af_sky",
    system_prompt="You are a meeting assistant. Be concise and clear."
) as assistant:
    # ...
```

### For Learning

```python
# Use clear voice, detailed explanations
async with ClaudeTTSAgent(
    tts_voice="af_bella",
    system_prompt="You are a patient tutor. Explain step-by-step."
) as assistant:
    # ...
```

---

## See Also

- [Agent Configuration](../../development/agent-config.md)
- [Voice Configuration](../../development/voice-config.md)
- [Code Examples](../code-examples.md)
