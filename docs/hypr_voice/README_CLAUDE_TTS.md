# Claude Agent SDK with TTS Integration

A comprehensive integration of Anthropic's Claude Agent SDK with multi-provider Text-to-Speech capabilities, enabling voice-enabled AI agents with real-time synthesis.

## 🚀 Features

### Claude Agent SDK Integration
- **Official SDK**: Uses Anthropic's Claude Agent SDK (v0.1.5+)
- **Async Support**: Full async/await support for real-time interactions
- **Context Management**: Automatic conversation history tracking
- **Tool Access**: File system, web search, and custom tool integration

### Multi-Provider TTS Support
- **Kokoro**: Free, local TTS with 17 voices
- **Deepgram**: Premium cloud TTS with Aura voices  
- **ElevenLabs**: Ultra-premium TTS with 44+ voices
- **Unified Interface**: Single API for all providers

### MCP Server Integration
- **TTS MCP Server**: Standard MCP protocol for TTS tools
- **Tool Discovery**: Automatic tool registration and discovery
- **Error Handling**: Robust error handling and fallbacks

## 📦 Installation

```bash
# Clone the repository
git clone <repository-url>
cd Hypr-Voice

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements/hypr_voice.txt

# Install TTS dependencies
pip install kokoro-api  # For local TTS
# Or see provider-specific setup below
```

### Environment Setup

```bash
# Required for Claude Agent SDK
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional: For premium TTS providers
export DEEPGRAM_API_KEY="your-deepgram-api-key"
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"

# For Kokoro (local, free)
# Start Kokoro API server on localhost:8880
kokoro-api --port 8880
```

## 🎯 Quick Start

### Basic Usage

```python
import asyncio
from services.claude_tts_agent import ClaudeTTSAgent

async def main():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella"
    ) as agent:
        
        # Chat with automatic TTS synthesis
        result = await agent.chat(
            "Tell me a short story about AI and creativity.",
            synthesize_response=True
        )
        
        print(f"Response: {result['response']}")
        print(f"Audio file: {result.get('audio_file')}")

asyncio.run(main())
```

### Quick Chat Function

```python
from services.claude_tts_agent import quick_chat

# Simple one-liner
result = await quick_chat(
    "What are the benefits of voice interfaces?",
    tts_provider="kokoro",
    synthesize=True
)
```

### Orchestrator Integration

```python
from orchestrator import AgentOrchestrator, AgentConfig

# Configure agent with TTS
config = AgentConfig(
    name="Voice-Agent",
    working_directory="./workspace",
    enable_tts_agent=True,
    tts_provider="deepgram",
    tts_voice="aura-luna-en",
    auto_synthesize=True
)

# Create and run agent
orchestrator = AgentOrchestrator()
agent_id = await orchestrator.create_agent(config)

await orchestrator.execute_instruction(
    agent_id,
    "Write a poem and read it aloud."
)
```

## 🎭 TTS Providers

### Kokoro (Free, Local)
- **17 voices**: American, British, child, robot voices
- **No API key**: Completely offline and free
- **24kHz quality**: Good for most applications
- **Voice combining**: Mix multiple voices

```python
async with ClaudeTTSAgent(tts_provider="kokoro", tts_voice="af_bella") as agent:
    result = await agent.chat("Hello world!", synthesize_response=True)
```

### Deepgram (Premium, Cloud)
- **Aura voices**: asteria, luna, stella, athena, etc.
- **Ultra-low latency**: ~50ms TTFB
- **48kHz quality**: Premium audio quality
- **Streaming support**: Real-time audio streaming

```python
async with ClaudeTTSAgent(tts_provider="deepgram", tts_voice="aura-luna-en") as agent:
    result = await agent.chat("Welcome to our service!", synthesize_response=True)
```

### ElevenLabs (Ultra-Premium, Cloud)
- **44+ voices**: rachel, sarah, adam, antoni, etc.
- **Highest quality**: Professional-grade audio
- **Voice cloning**: Custom voice creation (Pro+)
- **32 languages**: Multilingual support

```python
async with ClaudeTTSAgent(tts_provider="elevenlabs", tts_voice="rachel") as agent:
    result = await agent.chat("Experience premium voice synthesis!", synthesize_response=True)
```

## 🛠️ MCP Server

The TTS MCP Server provides standard MCP tools for Claude Agent SDK:

### Available Tools

1. **synthesize_speech**: Convert text to speech
2. **list_voices**: List available voices
3. **get_tts_info**: Get provider information

### Running the MCP Server

```bash
# Start the TTS MCP server
python services/mcp/tts_mcp_server.py

# In your Claude Agent SDK client, the server will be automatically
# discovered and tools will be available for use
```

### MCP Tool Usage

```python
# Tools are automatically available in Claude Agent SDK
# No additional setup required

# Claude can now use TTS capabilities naturally:
await agent.chat("Please read this summary aloud for me.")
```

## 📚 Examples

### Voice Assistant

```python
async def voice_assistant():
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        system_prompt="You are Clara, a friendly voice assistant."
    ) as assistant:
        
        questions = [
            "What's the weather like?",
            "Tell me a fun fact",
            "How do I make coffee?"
        ]
        
        for question in questions:
            result = await assistant.chat(question, synthesize_response=True)
            print(f"🔊 {result.get('audio_file')}")
```

### Code Review with Voice

```python
async def code_review():
    code = """
def calculate_factorial(n):
    if n < 0:
        return "Error"
    # ... rest of code
"""
    
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="am_adam",
        system_prompt="You are a senior software engineer."
    ) as reviewer:
        
        result = await reviewer.chat(
            f"Review this code: {code}",
            synthesize_response=True
        )
        
        print(f"📝 Review: {result['response']}")
        print(f"🔊 Audio: {result.get('audio_file')}")
```

### Multilingual Storytelling

```python
async def storytelling():
    voices = [
        {"provider": "kokoro", "voice": "af_bella"},
        {"provider": "kokoro", "voice": "am_adam"},
        {"provider": "deepgram", "voice": "aura-luna-en"}
    ]
    
    story_prompt = "Tell a story about a robot discovering music"
    
    for voice_config in voices:
        async with ClaudeTTSAgent(
            tts_provider=voice_config["provider"],
            tts_voice=voice_config["voice"]
        ) as storyteller:
            
            result = await storyteller.chat(story_prompt, synthesize_response=True)
            print(f"🎭 {voice_config['voice']}: {result.get('audio_file')}")
```

## 🔧 Configuration

### Agent Configuration

```python
from services.claude_tts_agent import ClaudeTTSAgent

agent = ClaudeTTSAgent(
    api_key="your-api-key",           # or ANTHROPIC_API_KEY env var
    enable_tts=True,                  # Enable TTS capabilities
    tts_provider="kokoro",            # TTS provider
    tts_voice="af_bella",             # Specific voice
    working_directory="./workspace",  # File operations directory
    system_prompt="You are helpful."  # Custom system prompt
)
```

### TTS Provider Configuration

```python
# Kokoro (local, free)
config = TTSConfig(
    provider=TTSProvider.KOKORO,
    voice="af_bella",
    speed=1.0,
    use_streaming=False
)

# Deepgram (cloud, premium)
config = TTSConfig(
    provider=TTSProvider.DEEPGRAM,
    voice="aura-luna-en",
    speed=1.0,
    use_streaming=True
)

# ElevenLabs (cloud, ultra-premium)
config = TTSConfig(
    provider=TTSProvider.ELEVENLABS,
    voice="rachel",
    speed=1.0,
    use_streaming=True
)
```

## 🧪 Testing

### Run Test Suite

```bash
# Basic functionality tests
python test_claude_tts_agent.py

# Comprehensive examples
python examples_claude_tts_integration.py
```

### Test Different Providers

```bash
# Test with Kokoro (free)
export ANTHROPIC_API_KEY="your-key"
python test_claude_tts_agent.py

# Test with Deepgram (requires API key)
export DEEPGRAM_API_KEY="your-key"
python test_claude_tts_agent.py

# Test with ElevenLabs (requires API key)
export ELEVENLABS_API_KEY="your-key"
python test_claude_tts_agent.py
```

## 📊 Performance

### Provider Comparison

| Provider | Latency | Quality | Cost | Voices | Languages |
|----------|---------|---------|------|--------|-----------|
| **Kokoro** | ~200ms | Good | Free | 17 | 1 |
| **Deepgram** | ~50ms | High | Per char | 16+ | 2 |
| **ElevenLabs** | ~75ms | Premium | Per char | 44+ | 32 |

### Performance Tips

1. **Use Kokoro** for development and testing (free)
2. **Use Deepgram** for production with low latency
3. **Use ElevenLabs** for premium applications
4. **Enable streaming** for real-time applications
5. **Cache audio** for frequently used responses

## 🔍 Troubleshooting

### Common Issues

#### Claude SDK Not Available
```bash
pip install claude-agent-sdk
```

#### TTS Service Not Available
```bash
# Check voice service installation
cd ../services/voice
python test_tts.py --provider kokoro --quick
```

#### Kokoro Server Not Running
```bash
# Start Kokoro API server
kokoro-api --port 8880

# Check server status
curl http://localhost:8880/health
```

#### API Key Issues
```bash
# Verify API keys are set
echo $ANTHROPIC_API_KEY
echo $DEEPGRAM_API_KEY
echo $ELEVENLABS_API_KEY
```

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug logging for TTS agent
async with ClaudeTTSAgent(tts_provider="kokoro") as agent:
    result = await agent.chat("Test message", synthesize_response=True)
```

## 🚀 Advanced Usage

### Custom TTS Tools

```python
from claude_agent_sdk import tool, create_sdk_mcp_server

@tool("custom_tts", "Custom TTS with special effects", {"text": str})
async def custom_tts(args):
    # Your custom TTS logic
    return {"content": [{"type": "text", "text": "Audio generated"}]}

# Create custom MCP server
server = create_sdk_mcp_server(
    name="custom-tts",
    version="1.0.0",
    tools=[custom_tts]
)
```

### Voice Switching

```python
async def dynamic_voice_selection():
    async with ClaudeTTSAgent() as agent:
        
        # Use different voices based on content
        if "technical" in content:
            result = await agent.synthesize_only(
                content, 
                provider="kokoro", 
                voice="am_adam"
            )
        else:
            result = await agent.synthesize_only(
                content,
                provider="kokoro",
                voice="af_bella"
            )
```

### Streaming TTS

```python
async def streaming_example():
    async with ClaudeTTSAgent(
        tts_provider="deepgram",
        tts_voice="aura-luna-en"
    ) as agent:
        
        # Stream long responses
        result = await agent.chat(
            "Tell me a long story about artificial intelligence...",
            synthesize_response=True
        )
        
        # Audio is generated and saved as it streams
        print(f"Streaming audio: {result.get('audio_file')}")
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📞 Support

- **Issues**: Report bugs via GitHub issues
- **Documentation**: See `/docs` directory
- **Examples**: See `examples_claude_tts_integration.py`

---

**Built with ❤️ using Claude Agent SDK and multi-provider TTS services**
