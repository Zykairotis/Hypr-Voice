# Code Examples

Collection of code snippets and examples for common tasks in Hypr-Voice.

## Table of Contents

- [Agent Operations](#agent-operations)
- [File Operations](#file-operations)
- [Web Interactions](#web-interactions)
- [Voice Operations](#voice-operations)
- [MCP Integration](#mcp-integration)
- [Error Handling](#error-handling)
- [Performance Tips](#performance-tips)

---

## Agent Operations

### Create Simple Agent

```python
from hypr_voice.client import AgentClient, AgentConfig

async def create_agent():
    client = AgentClient()

    config = AgentConfig(
        name="my-agent",
        working_directory="/tmp/agents/my-agent",
        skills=["file_operations"]
    )

    agent_id = await client.create_agent(config)
    return agent_id
```

### Create Agent with Multiple Skills

```python
async def create_multi_skill_agent():
    client = AgentClient()

    config = AgentConfig(
        name="multi-skill-agent",
        working_directory="/tmp/agents/multi",
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

### Create Agent with MCP Servers

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

### Send Instruction to Agent

```python
async def instruct_agent(agent_id):
    client = AgentClient()

    await client.instruct(
        agent_id,
        "Create a Python script that prints 'Hello World'"
    )
```

### Monitor Agent Status

```python
async def monitor_agent(agent_id):
    client = AgentClient()

    # Get status
    status = await client.get_agent_status(agent_id)
    print(f"Status: {status}")

    # Get details
    details = await client.get_agent_details(agent_id)
    print(f"Details: {details}")

    # Subscribe to events
    await client.subscribe_to_agent(agent_id)
```

### Quick Agent (One-liner)

```python
from hypr_voice.client import quick_agent

async def quick_example():
    agent_id = await quick_agent(
        name="quick-agent",
        working_directory="/tmp/agents/quick",
        instruction="Create hello.py and run it",
        skills=["file_operations", "bash_execution"]
    )
    return agent_id
```

---

## File Operations

### Create File

```python
async def create_file():
    client = AgentClient()

    config = AgentConfig(
        name="file-creator",
        working_directory="/tmp/agents/files",
        skills=["file_operations"]
    )

    agent_id = await client.create_agent(config)

    await client.instruct(agent_id, """
    Create a file called 'test.txt' with the following content:
    'Hello, World!'
    """)
```

### Read File

```python
async def read_file():
    client = AgentClient()

    agent_id = await client.create_agent(config)

    await client.instruct(agent_id, """
    Read the file 'test.txt' and display its contents
    """)
```

### Edit File

```python
async def edit_file():
    client = AgentClient()

    agent_id = await client.create_agent(config)

    await client.instruct(agent_id, """
    Open 'config.yaml' and change the port from 8080 to 9090
    """)
```

### Directory Operations

```python
async def directory_ops():
    client = AgentClient()

    agent_id = await client.create_agent(config)

    await client.instruct(agent_id, """
    1. Create a directory called 'project'
    2. Create 'project/src' and 'project/tests'
    3. Create 'project/README.md'
    4. List the directory structure
    """)
```

---

## Web Interactions

### Web Search

```python
async def web_search():
    client = AgentClient()

    config = AgentConfig(
        name="researcher",
        working_directory="/tmp/agents/research",
        skills=["file_operations"],
        mcp_servers=["brave-search"]  # Requires BRAVE_API_KEY
    )

    agent_id = await client.create_agent(config)

    await client.instruct(agent_id, """
    Search for information about Python 3.12 new features
    and create a summary document.
    """)
```

### Fetch Webpage

```python
async def fetch_webpage():
    client = AgentClient()

    config = AgentConfig(
        name="fetcher",
        working_directory="/tmp/agents/fetch",
        skills=["file_operations"],
        mcp_servers=["fetch"]
    )

    agent_id = await client.create_agent(config)

    await client.instruct(agent_id, """
    Fetch the content from https://example.com
    and save it to a file.
    """)
```

---

## Voice Operations

### Text-to-Speech

```python
from hypr_voice.services.voice.tts_manager import VoiceManager

async def text_to_speech():
    manager = VoiceManager()

    # Basic TTS
    audio_file = await manager.synthesize(
        text="Hello, world!",
        provider="kokoro",
        voice="af_bella"
    )

    print(f"Audio: {audio_file}")
```

### TTS with Different Voices

```python
async def tts_voices():
    manager = VoiceManager()

    voices = {
        "professional": "af_bella",
        "friendly": "af_sky",
        "narrator": "bm_george"
    }

    for style, voice in voices.items():
        audio = await manager.synthesize(
            text=f"This is a {style} voice.",
            provider="kokoro",
            voice=voice
        )
        print(f"{style}: {audio}")
```

### Streaming TTS

```python
async def streaming_tts():
    manager = VoiceManager()

    text = "This is a long text that will be streamed..."

    async for chunk in manager.synthesize_stream(
        text=text,
        provider="kokoro",
        voice="af_bella"
    ):
        # Process each chunk
        await play_chunk(chunk)
```

### Speech-to-Text

```python
from hypr_voice.whisper.client import WhisperClient

async def speech_to_text():
    client = WhisperClient(mode="FLOW")

    result = await client.transcribe(
        audio_file="recording.wav",
        vocabulary="development"
    )

    print(f"Transcription: {result['text']}")
```

### Real-time Transcription

```python
async def realtime_transcription():
    client = WhisperClient(mode="LOCAL")

    async for transcription in client.transcribe_stream():
        print(f"Live: {transcription['text']}")
```

---

## MCP Integration

### Initialize MCP Manager

```python
from hypr_voice.services.mcp.mcp_loader import EnhancedMCPManager

async def init_mcp():
    manager = EnhancedMCPManager()

    # Add preset servers
    await manager.add_preset_server("filesystem")
    await manager.add_preset_server("git")

    # Add custom server
    from hypr_voice.services.mcp.mcp_loader import MCPServerConfig

    custom_config = MCPServerConfig(
        name="custom-server",
        command="python",
        args=["-m", "custom_mcp_server"],
        env={"API_KEY": "secret"}
    )

    await manager.add_server(custom_config)

    return manager
```

### Call MCP Tool

```python
async def call_mcp_tool():
    manager = EnhancedMCPManager()

    # Call filesystem tool
    result = await manager.call_tool(
        "filesystem",
        "list_directory",
        {"path": "/tmp"}
    )

    print(f"Result: {result}")
```

### Get Available Tools

```python
async def list_mcp_tools():
    manager = EnhancedMCPManager()

    tools = manager.get_all_tools()

    for tool in tools:
        print(f"{tool.server}: {tool.name}")
        print(f"  Description: {tool.description}")
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
        # Handle error
```

### With Retry Logic

```python
async def agent_with_retry():
    max_retries = 3

    for attempt in range(max_retries):
        try:
            client = AgentClient()
            agent_id = await client.create_agent(config)
            await client.instruct(agent_id, "Do something")
            break  # Success

        except Exception as e:
            if attempt == max_retries - 1:
                raise  # Re-raise on last attempt
            print(f"Attempt {attempt + 1} failed, retrying...")
            await asyncio.sleep(1)
```

### Timeout Handling

```python
async def agent_with_timeout():
    try:
        client = AgentClient()

        config = AgentConfig(
            name="timeout-agent",
            working_directory="/tmp/agents/timeout",
            timeout=60,  # 60 second timeout
            skills=["file_operations"]
        )

        agent_id = await client.create_agent(config)

        # Use asyncio.timeout for additional control
        async with asyncio.timeout(30):
            await client.instruct(agent_id, "Quick task")

    except asyncio.TimeoutError:
        print("Task timed out")
```

---

## Performance Tips

### Use Caching

```python
async def cached_tts():
    manager = VoiceManager()

    # Enable caching for repeated text
    config = AgentConfig(
        name="cached-agent",
        working_directory="/tmp/agents/cached",
        enable_voice=True,
        tts_cache_enabled=True
    )

    agent_id = await client.create_agent(config)
```

### Parallel Execution

```python
async def parallel_agents():
    client = AgentClient()

    # Create multiple agents
    agents = []
    for i in range(3):
        config = AgentConfig(
            name=f"parallel-agent-{i}",
            working_directory=f"/tmp/agents/parallel-{i}",
            skills=["file_operations"]
        )
        agent_id = await client.create_agent(config)
        agents.append(agent_id)

    # Execute in parallel
    tasks = [
        client.instruct(agent_id, f"Task {i}")
        for i, agent_id in enumerate(agents)
    ]

    await asyncio.gather(*tasks)
```

### Optimize Chunk Size

```python
async def optimized_transcription():
    client = WhisperClient()

    # Use optimal chunk size for your use case
    result = await client.transcribe(
        audio_file="long_recording.wav",
        chunk_size=30,  # 30 seconds (recommended)
        use_opus=True   # Enable Opus for faster upload
    )
```

---

## Advanced Examples

### Hierarchical Agents

```python
async def hierarchical_agents():
    orchestrator = AgentOrchestrator()

    # Create parent agent
    parent_config = AgentConfig(
        name="team-leader",
        working_directory="/tmp/agents/team",
        skills=["hierarchical_agents"]
    )

    parent_id = await orchestrator.create_agent(parent_config)
    parent_agent = orchestrator.get_agent(parent_id)

    # Create sub-agents
    developer = await parent_agent.create_subagent(
        "developer",
        skills=["file_operations", "bash_execution"]
    )

    tester = await parent_agent.create_subagent(
        "tester",
        skills=["bash_execution"]
    )

    # Execute sequentially
    await parent_agent.execute_subagents_sequential(
        ["developer", "tester"],
        {
            "developer": "Create calculator.py",
            "tester": "Test calculator.py"
        }
    )
```

### Workflow

```python
async def workflow_example():
    orchestrator = AgentOrchestrator()
    workflow = AgentWorkflow("my-workflow", orchestrator)

    # Add steps
    workflow.add_agent_step(
        name="step1",
        role="worker",
        instructions="Do task 1",
        skills=["file_operations"]
    )

    workflow.add_agent_step(
        name="step2",
        role="processor",
        instructions="Do task 2",
        skills=["bash_execution"],
        depends_on=["step1"]
    )

    # Execute workflow
    results = await workflow.execute()
    print(f"Results: {results}")
```

### Context-Aware Agent

```python
async def context_aware_agent():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        enable_monitoring=True,
        monitor_interval=0.15
    ) as assistant:

        # Agent knows active application
        result = await assistant.chat(
            message="Help me with this code",
            synthesize_response=True
        )

        print(f"Response: {result['response']}")
```

---

## See Also

- [Basic Usage Examples](basic-usage.md)
- [First Agent Tutorial](tutorials/first-agent.md)
- [Configuration Reference](../development/configuration-reference.md)
