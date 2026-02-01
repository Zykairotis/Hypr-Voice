# Tutorial: Creating Your First Agent

Learn how to create and use your first Hypr-Voice agent from scratch.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Step 1: Installation](#step-1-installation)
- [Step 2: Configuration](#step-2-configuration)
- [Step 3: Creating Your First Agent](#step-3-creating-your-first-agent)
- [Step 4: Running Your Agent](#step-4-running-your-agent)
- [Step 5: Advanced Features](#step-5-advanced-features)
- [Next Steps](#next-steps)

---

## Prerequisites

Before you begin, ensure you have:

- **Python 3.10+** installed
- **pip** package manager
- **API keys** for at least one provider:
  - Cerebras (for LLM)
  - Wispr Flow (for transcription)
  - Deepgram or ElevenLabs (for TTS)

### Checking Your Installation

```bash
# Check Python version
python --version

# Check pip
pip --version
```

---

## Step 1: Installation

### Clone the Repository

```bash
# Clone Hypr-Voice
git clone https://github.com/yourusername/Hypr-Voice.git
cd Hypr-Voice
```

### Install Dependencies

```bash
# Install in development mode
pip install -e .

# Or install specific components
pip install hypr-voice[agent,tts,whisper]
```

### Verify Installation

```bash
# Test installation
python -c "from hypr_voice.client import AgentClient; print('Installation successful!')"
```

---

## Step 2: Configuration

### Create Environment File

```bash
# Copy example environment file
cp .env.example .env
```

### Edit .env File

```bash
# Open .env in your editor
nano .env
# or
vim .env
```

### Add Your API Keys

```bash
# Minimum required variables
CEREBRAS_API_KEY_ONE=your_cerebras_key_here
WISPR_FLOW_JWT_TOKEN=your_wispr_token_here
WISPR_FLOW_BASETEN_API_KEY=your_baseten_key_here
WISPR_FLOW_USER_UUID=your_uuid_here
DEEPGRAM_API_KEY=your_deepgram_key_here
```

### Where to Get API Keys

| Service | URL | Cost |
|---------|-----|------|
| Cerebras | https://cloud.cerebras.ai | Free tier available |
| Wispr Flow | https://wispr-flow.baseten.co | Check pricing |
| Deepgram | https://deepgram.com | Free tier available |
| ElevenLabs | https://elevenlabs.io | Free tier available |

---

## Step 3: Creating Your First Agent

### Basic Agent Script

Create a file called `my_first_agent.py`:

```python
#!/usr/bin/env python3
"""
My First Hypr-Voice Agent
"""

import asyncio
from hypr_voice.client import AgentClient, AgentConfig

async def main():
    # Create agent client
    client = AgentClient()

    # Define agent configuration
    config = AgentConfig(
        name="my-first-agent",
        working_directory="/tmp/agents/my-first",
        skills=["file_operations"],
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        temperature=0.7
    )

    print("Creating agent...")

    # Create the agent
    agent_id = await client.create_agent(config)

    print(f"Agent created with ID: {agent_id}")

    # Send instruction to the agent
    instruction = """
    Please do the following:
    1. Create a file called 'hello.txt'
    2. Write 'Hello from my first agent!' in the file
    3. Read the file back and show me the contents
    """

    print("Sending instruction to agent...")
    await client.instruct(agent_id, instruction)

    # Wait for agent to complete
    print("Agent is working...")
    await asyncio.sleep(5)

    # Check agent status
    status = await client.get_agent_status(agent_id)
    print(f"Agent status: {status}")

    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Your First Agent

```bash
# Make script executable
chmod +x my_first_agent.py

# Run the agent
python my_first_agent.py
```

### Expected Output

```
Creating agent...
Agent created with ID: agent-abc123
Sending instruction to agent...
Agent is working...
Agent status: completed
Done!
```

---

## Step 4: Running Your Agent

### Quick Agent Function

For even simpler agent creation, use the `quick_agent` function:

```python
#!/usr/bin/env python3
"""
Quick Agent Example
"""

import asyncio
from hypr_voice.client import quick_agent

async def main():
    print("Creating quick agent...")

    agent_id = await quick_agent(
        name="quick-agent",
        working_directory="/tmp/agents/quick",
        instruction="""
        Create a Python script that:
        - Defines a function called greet() that prints 'Hello, World!'
        - Calls the function
        - Save it as greet.py
        """,
        skills=["file_operations", "bash_execution"],
        monitor=True
    )

    print(f"Agent {agent_id} is running!")
    print("Check /tmp/agents/quick for results")

if __name__ == "__main__":
    asyncio.run(main())
```

### Run Quick Agent

```bash
python quick_agent.py
```

---

## Step 5: Advanced Features

### Agent with Voice Output

```python
#!/usr/bin/env python3
"""
Agent with Voice Output
"""

import asyncio
from hypr_voice.client import AgentClient, AgentConfig

async def main():
    client = AgentClient()

    config = AgentConfig(
        name="voice-agent",
        working_directory="/tmp/agents/voice",
        skills=["voice_synthesis", "file_operations"],
        enable_voice=True,
        tts_provider="kokoro",
        tts_voice="af_bella"
    )

    agent_id = await client.create_agent(config)

    # Agent will speak its response
    await client.instruct(agent_id, """
    Write a short poem about artificial intelligence
    and convert it to speech.
    """)

    await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent with Multiple Skills

```python
#!/usr/bin/env python3
"""
Multi-Skilled Agent
"""

import asyncio
from hypr_voice.client import AgentClient, AgentConfig

async def main():
    client = AgentClient()

    config = AgentConfig(
        name="multi-skilled-agent",
        working_directory="/tmp/agents/multi",
        skills=[
            "file_operations",
            "bash_execution",
            "voice_synthesis",
            "hierarchical_agents"
        ],
        enable_voice=True,
        mcp_servers=["filesystem", "git"]
    )

    agent_id = await client.create_agent(config)

    # Complex task using multiple skills
    await client.instruct(agent_id, """
    1. Create a new git repository
    2. Initialize it with a README.md
    3. Create a Python script that calculates fibonacci numbers
    4. Run the script and show the output
    5. Make a git commit
    6. Summarize what you did in spoken form
    """)

    await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
```

### Agent with Context Awareness

```python
#!/usr/bin/env python3
"""
Context-Aware Agent
"""

import asyncio
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

async def main():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        enable_monitoring=True,  # Enable application monitoring
        monitor_interval=0.15,   # 150ms update rate
        system_prompt="""You are a helpful assistant that provides
        context-aware responses based on the active application."""
    ) as assistant:

        # Agent knows what application you're using
        questions = [
            "How do I create a new file here?",  # Will use app context
            "What's the keyboard shortcut for save?",
            "Help me understand this error"
        ]

        for question in questions:
            print(f"\nYou: {question}")

            result = await assistant.chat(
                message=question,
                synthesize_response=True
            )

            print(f"Assistant: {result['response']}")
            print(f"Audio: {result.get('audio_file')}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Troubleshooting

### Common Issues

#### Issue: Module Not Found

```bash
# Error: ModuleNotFoundError: No module named 'hypr_voice'

# Solution: Reinstall the package
pip install -e .
```

#### Issue: API Key Errors

```bash
# Error: API key not found

# Solution: Check your .env file
cat .env | grep API_KEY

# Ensure no trailing spaces
# Ensure variables are exported
source .env
```

#### Issue: Agent Timeout

```python
# Error: Agent timeout

# Solution: Increase timeout
config = AgentConfig(
    name="my-agent",
    timeout=600,  # 10 minutes
    # ... other config
)
```

#### Issue: Permission Denied

```bash
# Error: Permission denied when creating files

# Solution: Check working directory permissions
ls -la /tmp/agents/

# Create directory if needed
mkdir -p /tmp/agents/my-agent
chmod 755 /tmp/agents/my-agent
```

---

## Next Steps

Congratulations! You've created your first agent. Here's what to explore next:

### Learn More

- [Basic Usage Examples](../basic-usage.md) - More examples
- [TTS Setup Tutorial](tts-setup.md) - Set up text-to-speech
- [Whisper Setup Tutorial](whisper-setup.md) - Set up speech-to-text

### Advanced Features

- [Code Examples](../code-examples.md) - Code snippets for common tasks
- [Custom Agents](../advanced/custom-agents.md) - Create custom agent types
- [Performance Tuning](../advanced/performance-tuning.md) - Optimize your agents

### Integration

- [Claude Integration](../integrations/claude-integration.md) - Integrate with Claude
- [Discord Bot](../integrations/discord-bot.md) - Build a Discord bot
- [Telegram Bot](../integrations/telegram-bot.md) - Build a Telegram bot

---

## Reference

### AgentConfig Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | string | Required | Agent name |
| `working_directory` | string | Required | Working directory |
| `skills` | list | `["file_operations"]` | Agent skills |
| `model` | string | `"claude-3-5-sonnet-20241022"` | LLM model |
| `max_tokens` | integer | `8096` | Max tokens per response |
| `temperature` | float | `1.0` | Response randomness |
| `timeout` | integer | `300` | Timeout (seconds) |
| `enable_voice` | boolean | `false` | Enable voice output |
| `mcp_servers` | list | `[]` | MCP servers to use |

### Available Skills

| Skill | Description |
|-------|-------------|
| `file_operations` | Read, write, manipulate files |
| `bash_execution` | Execute bash commands |
| `voice_synthesis` | Text-to-speech conversion |
| `hierarchical_agents` | Create sub-agents |
| `web_search` | Web search capabilities |

---

## Summary

In this tutorial, you learned:

1. How to install Hypr-Voice
2. How to configure API keys
3. How to create a basic agent
4. How to send instructions to agents
5. How to add advanced features like voice and context awareness

You're now ready to explore more features and build powerful voice-enabled agents!

---

## See Also

- [Basic Usage Examples](../basic-usage.md)
- [TTS Setup Tutorial](tts-setup.md)
- [Whisper Setup Tutorial](whisper-setup.md)
- [Configuration Reference](../../development/configuration-reference.md)
