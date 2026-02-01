# Basic Usage Examples

Getting started with Hypr-Voice - simple examples and common use cases.

## Table of Contents

- [Quick Start](#quick-start)
- [Creating Your First Agent](#creating-your-first-agent)
- [Speech-to-Text](#speech-to-text)
- [Text-to-Speech](#text-to-speech)
- [Voice Assistant](#voice-assistant)
- [Common Tasks](#common-tasks)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/Hypr-Voice.git
cd Hypr-Voice

# Install dependencies
pip install -e .

# Set up environment
cp .env.example .env
# Edit .env with your API keys
```

### Basic Setup

```python
import asyncio
from hypr_voice.client import AgentClient, AgentConfig

async def main():
    # Create client
    client = AgentClient()

    # Create simple agent
    config = AgentConfig(
        name="my-agent",
        working_directory="/tmp/agents/my-agent",
        skills=["file_operations", "bash_execution"]
    )

    agent_id = await client.create_agent(config)

    # Send instruction
    await client.instruct(
        agent_id,
        "Create a file called hello.txt with 'Hello World' inside"
    )

    # Wait for completion
    await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Creating Your First Agent

### Simple Agent

```python
from hypr_voice.client import AgentClient, AgentConfig

async def create_simple_agent():
    client = AgentClient()

    config = AgentConfig(
        name="simple-agent",
        working_directory="/tmp/agents/simple",
        skills=["file_operations"],
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096
    )

    agent_id = await client.create_agent(config)
    return agent_id
```

### Agent with Multiple Skills

```python
async def create_skilled_agent():
    client = AgentClient()

    config = AgentConfig(
        name="skilled-agent",
        working_directory="/tmp/agents/skilled",
        skills=[
            "file_operations",
            "bash_execution",
            "voice_synthesis"
        ],
        enable_voice=True,
        tts_provider="kokoro",
        tts_voice="af_bella"
    )

    agent_id = await client.create_agent(config)
    return agent_id
```

### Agent with MCP Servers

```python
async def create_mcp_agent():
    client = AgentClient()

    config = AgentConfig(
        name="mcp-agent",
        working_directory="/tmp/agents/mcp",
        skills=["file_operations"],
        mcp_servers=["filesystem", "git", "github"]
    )

    agent_id = await client.create_agent(config)
    return agent_id
```

---

## Speech-to-Text

### Basic Transcription

```python
from hypr_voice.whisper.client import WhisperClient

async def transcribe_audio():
    # Create Whisper client
    client = WhisperClient()

    # Transcribe audio file
    result = await client.transcribe(
        audio_file="recording.wav",
        language="en",
        vocabulary="development"  # Use development vocabulary
    )

    print(f"Transcription: {result['text']}")
    print(f"Confidence: {result['confidence']}")
```

### Real-time Transcription

```python
async def transcribe_realtime():
    client = WhisperClient()

    # Start real-time transcription
    async for transcription in client.transcribe_stream():
        print(f"Live: {transcription['text']}")
```

### With Custom Vocabulary

```python
async def transcribe_with_vocabulary():
    client = WhisperClient()

    # Define custom vocabulary
    custom_vocab = {
        "technical_terms": ["Kubernetes", "Docker", "Terraform"],
        "programming": ["async", "await", "callback"]
    }

    result = await client.transcribe(
        audio_file="tech_talk.wav",
        vocabulary=custom_vocab
    )

    print(f"Transcription: {result['text']}")
```

---

## Text-to-Speech

### Basic TTS

```python
from hypr_voice.services.voice.tts_manager import VoiceManager

async def text_to_speech():
    manager = VoiceManager()

    # Synthesize speech
    audio_file = await manager.synthesize(
        text="Hello, world!",
        provider="kokoro",
        voice="af_bella"
    )

    print(f"Audio saved to: {audio_file}")
```

### With Different Voices

```python
async def tts_with_voices():
    manager = VoiceManager()

    # Different voices for different contexts
    voices = {
        "professional": "af_bella",
        "friendly": "af_sky",
        "narrator": "bm_george"
    }

    for style, voice in voices.items():
        audio = await manager.synthesize(
            text=f"This is a {style} voice example.",
            provider="kokoro",
            voice=voice
        )
        print(f"{style}: {audio}")
```

### Streaming TTS

```python
async def streaming_tts():
    manager = VoiceManager()

    # Stream long text
    text = "This is a long text that will be streamed..."

    async for chunk in manager.synthesize_stream(
        text=text,
        provider="kokoro",
        voice="af_bella"
    ):
        # Process each chunk
        await play_audio_chunk(chunk)
```

### Voice Presets

```python
async def tts_with_presets():
    manager = VoiceManager()

    # Use preset configuration
    audio = await manager.synthesize(
        text="Welcome to our business meeting.",
        preset="professional"  # professional, friendly, technical, narrator
    )

    print(f"Audio: {audio}")
```

---

## Voice Assistant

### Basic Voice Assistant

```python
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

async def voice_assistant():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        system_prompt="You are a helpful voice assistant."
    ) as assistant:

        # Chat with voice response
        result = await assistant.chat(
            message="What's the weather like today?",
            synthesize_response=True
        )

        print(f"Response: {result['response']}")
        print(f"Audio: {result.get('audio_file')}")
```

### Context-Aware Assistant

```python
async def context_aware_assistant():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        enable_monitoring=True,
        monitor_interval=0.15  # 150ms
    ) as assistant:

        # Assistant knows current application
        result = await assistant.chat(
            message="Help me with this code.",
            synthesize_response=True
        )

        print(f"Response: {result['response']}")
```

### Multi-turn Conversation

```python
async def conversation():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_sky"
    ) as assistant:

        questions = [
            "What's Python?",
            "How do I install it?",
            "Show me a hello world example"
        ]

        for question in questions:
            print(f"You: {question}")

            result = await assistant.chat(
                message=question,
                synthesize_response=True
            )

            print(f"Assistant: {result['response']}")
            print()
```

---

## Common Tasks

### File Operations

```python
async def file_operations():
    client = AgentClient()

    config = AgentConfig(
        name="file-agent",
        working_directory="/tmp/agents/files",
        skills=["file_operations"]
    )

    agent_id = await client.create_agent(config)

    # File operations
    await client.instruct(agent_id, """
    1. Create a directory called 'project'
    2. Create a file called 'project/README.md'
    3. Write '# My Project' in the README
    4. List the contents of 'project'
    """)
```

### Code Generation

```python
async def generate_code():
    client = AgentClient()

    config = AgentConfig(
        name="coder",
        working_directory="/tmp/agents/coder",
        skills=["file_operations", "bash_execution"]
    )

    agent_id = await client.create_agent(config)

    # Generate and test code
    await client.instruct(agent_id, """
    Create a Python script that:
    - Defines a function to calculate fibonacci numbers
    - Includes a main block that tests the function
    - Save it as fibonacci.py
    - Run the script and show the output
    """)
```

### Web Search

```python
async def web_search():
    client = AgentClient()

    config = AgentConfig(
        name="researcher",
        working_directory="/tmp/agents/researcher",
        skills=["file_operations"],
        mcp_servers=["brave-search"]  # Requires BRAVE_API_KEY
    )

    agent_id = await client.create_agent(config)

    # Search and summarize
    await client.instruct(agent_id, """
    Search for information about Python 3.12 new features
    and create a summary document.
    """)
```

### Git Operations

```python
async def git_operations():
    client = AgentClient()

    config = AgentConfig(
        name="git-agent",
        working_directory="/tmp/agents/git",
        skills=["file_operations"],
        mcp_servers=["git"]
    )

    agent_id = await client.create_agent(config)

    # Git operations
    await client.instruct(agent_id, """
    1. Initialize a git repository
    2. Create a .gitignore file
    3. Create a README.md
    4. Make an initial commit
    5. Show the git log
    """)
```

---

## Quick Agent Function

### One-Line Agent Creation

```python
from hypr_voice.client import quick_agent

async def quick_example():
    agent_id = await quick_agent(
        name="quick-agent",
        working_directory="/tmp/agents/quick",
        instruction="Create a hello world script and run it",
        skills=["file_operations", "bash_execution"],
        monitor=True
    )

    print(f"Agent running: {agent_id}")
```

---

## Error Handling

### Basic Error Handling

```python
async def safe_agent():
    try:
        client = AgentClient()
        config = AgentConfig(
            name="safe-agent",
            working_directory="/tmp/agents/safe",
            skills=["file_operations"]
        )

        agent_id = await client.create_agent(config)
        await client.instruct(agent_id, "Do something")

    except Exception as e:
        print(f"Error: {e}")
        # Handle error appropriately
```

### With Retry

```python
async def agent_with_retry():
    max_retries = 3

    for attempt in range(max_retries):
        try:
            client = AgentClient()
            config = AgentConfig(
                name="retry-agent",
                working_directory="/tmp/agents/retry",
                skills=["file_operations"]
            )

            agent_id = await client.create_agent(config)
            await client.instruct(agent_id, "Do something")
            break  # Success

        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on last attempt
            print(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(1)
```

---

## Monitoring Agents

### Check Agent Status

```python
async def check_status():
    client = AgentClient()

    # Create agent
    agent_id = await client.create_agent(config)

    # Check status
    status = await client.get_agent_status(agent_id)
    print(f"Status: {status}")

    # Get details
    details = await client.get_agent_details(agent_id)
    print(f"Details: {details}")
```

### Real-time Monitoring

```python
from hypr_voice.client import RichMonitor

async def monitor_agent():
    client = AgentClient()
    monitor = RichMonitor(client)

    # Start monitoring
    monitor_task = asyncio.create_task(monitor.start())

    # Create and run agent
    agent_id = await client.create_agent(config)
    await client.instruct(agent_id, "Do work")

    # Display status
    print(monitor.display_agents_table())

    # Cleanup
    client.disconnect()
```

---

## See Also

- [Tutorials: First Agent](tutorials/first-agent.md)
- [Tutorials: TTS Setup](tutorials/tts-setup.md)
- [Code Examples](code-examples.md)
- [Configuration Reference](../development/configuration-reference.md)
