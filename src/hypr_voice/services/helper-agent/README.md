# Helper Agent - Multi-Provider AI Service

A comprehensive multi-provider LLM service with LiteLLM, LangGraph agent workflows, MCP protocol support, and specialized capabilities for the Hypr-Voice ecosystem.

## Features

### 🌐 Multi-Provider Support (10+ Providers)
- **OpenAI** - GPT-4, GPT-3.5 Turbo
- **Anthropic** - Claude 3 (Opus, Sonnet, Haiku)
- **Groq** - Llama 3, Mixtral, Gemma
- **xAI** - Grok Beta
- **Ollama** - Local models (Llama 2, Mistral, CodeLlama)
- **OpenRouter** - 100+ models
- **Cohere** - Command, Command-Light
- **Together AI** - Llama 2, Mixtral
- **Mistral AI** - Mistral Large, Medium, Small
- **Perplexity** - Online search-enabled models
- **SGLang** - Custom Qwen 3 integration

### 🤖 Agentic Workflows
- **LangGraph** integration with ReAct pattern
- Multi-step reasoning and tool execution
- Automatic tool selection and chaining
- State management and checkpointing

### 🔧 MCP Protocol Support
- Model Context Protocol implementation
- Tool registration and discovery
- Function calling with JSON schemas
- Session management

### ✨ Specialized Capabilities
- **Summarization** - Voice-optimized text summarization
- **Analysis** - Content analysis and insights
- **Planning** - Task breakdown and planning
- **Claude SDK Bridge** - Context-aware assistance

### 📡 Streaming Support
- Server-Sent Events (SSE)
- Real-time response streaming
- Connection management
- Heartbeat support

## Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# Or install specific packages
pip install litellm langchain langchain-core langgraph sse-starlette
```

## Quick Start

### Basic Usage

```python
import asyncio
from integration import HelperAgentIntegration

async def main():
    async with HelperAgentIntegration() as agent:
        # Simple chat
        response = await agent.chat([
            {"role": "user", "content": "Hello!"}
        ])
        print(response['content'])

asyncio.run(main())
```

### Provider Selection

```python
# Auto-select best provider
response = await agent.chat(messages)

# Specify provider
response = await agent.chat(messages, provider="openai")

# Specify provider and model
response = await agent.chat(messages, provider="claude", model="claude-3-sonnet-20240229")
```

### Streaming

```python
async for chunk in agent.stream_chat(messages):
    print(chunk, end="", flush=True)
```

### Specialized Capabilities

```python
# Summarization for TTS
summary = await agent.summarize_for_tts(
    long_text,
    max_words=60,
    style="concise"
)

# Task planning
plan = await agent.plan_task(
    "Build a web application",
    max_steps=10
)

# Content analysis
analysis = await agent.analyze_content(
    content,
    analysis_type="comprehensive"
)
```

### Agentic Workflows

```python
# Execute with multi-step reasoning
result = await agent.agentic_query(
    "Research and summarize latest AI news",
    tools=["web_search", "summarization"]
)
print(result['response'])
```

### Conversational Sessions

```python
session = agent.session(system_prompt="You are a helpful assistant.")

response1 = await session.send("What is Python?")
response2 = await session.send("Give me an example.")
```

### MCP Tool Usage

```python
# List available tools
tools = agent.list_mcp_tools()

# Call a tool
result = await agent.call_mcp_tool(
    "summarize_text",
    {"text": "Long text here...", "max_length": 300}
)
```

## Configuration

### Provider Configuration

Edit `config/providers.yaml` to configure providers:

```yaml
providers:
  openai:
    enabled: true
    api_key_env: "OPENAI_API_KEY"
    default_model: "gpt-3.5-turbo"
    
  claude:
    enabled: true
    api_key_env: "ANTHROPIC_API_KEY"
    default_model: "claude-3-sonnet-20240229"
```

### Agent Configuration

Edit `config/agent_config.yaml` for agent behavior:

```yaml
agent:
  mode: "auto"  # auto, agentic, direct
  max_iterations: 5

workflow:
  react_pattern:
    enabled: true
```

### MCP Tools Configuration

Edit `config/mcp_tools.yaml` for tool settings:

```yaml
tools:
  summarize_text:
    enabled: true
    parameters:
      type: "object"
      properties:
        text:
          type: "string"
```

## Environment Variables

Required API keys (set only for providers you'll use):

```bash
# OpenAI
export OPENAI_API_KEY="your-key-here"

# Anthropic Claude
export ANTHROPIC_API_KEY="your-key-here"

# Groq
export GROQ_API_KEY="your-key-here"

# xAI
export XAI_API_KEY="your-key-here"

# OpenRouter
export OPENROUTER_API_KEY="your-key-here"

# Cohere
export COHERE_API_KEY="your-key-here"

# Together AI
export TOGETHER_API_KEY="your-key-here"

# Mistral AI
export MISTRAL_API_KEY="your-key-here"

# Perplexity
export PERPLEXITY_API_KEY="your-key-here"

# Ollama (if not using default)
export OLLAMA_BASE_URL="http://localhost:11434"

# SGLang (if not using default)
export SGLANG_BASE_URL="http://localhost:30000"
```

## API Reference

### HelperAgentIntegration

Main integration class providing unified API.

#### Methods

- `chat(messages, provider=None, model=None, **kwargs)` - Chat completion
- `stream_chat(messages, provider=None, model=None, **kwargs)` - Streaming chat
- `quick_prompt(prompt, provider=None, **kwargs)` - Quick completion
- `summarize_for_tts(text, max_words, style)` - Summarize for TTS
- `analyze_content(content, analysis_type)` - Analyze content
- `plan_task(task, max_steps)` - Plan task
- `agentic_query(query, tools)` - Agentic execution
- `call_mcp_tool(tool_name, args)` - Call MCP tool
- `session(system_prompt)` - Create session
- `get_metrics(provider)` - Get usage metrics
- `list_providers()` - List available providers
- `list_models(provider)` - List available models

### LiteLLMClient

Low-level multi-provider LLM client.

### MCPServer

MCP protocol server for tool management.

### LangGraphAgent

Agent with ReAct pattern workflow.

## Examples

See `examples/` directory for detailed examples:

- `basic_usage.py` - Basic API usage
- `streaming_example.py` - Streaming responses
- `agentic_workflow.py` - Multi-step reasoning
- `mcp_tools_example.py` - MCP tool usage
- `provider_comparison.py` - Provider comparison

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_litellm_client.py -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

## Architecture

```
helper-agent/
├── integration.py          # High-level API
├── litellm_client.py       # Multi-provider client
├── agent_graph.py          # LangGraph agent
├── mcp_server.py           # MCP protocol
├── streaming.py            # SSE streaming
├── langgraph_tools.py      # LangChain tools
├── config/                 # Configuration files
├── tools/                  # Tool implementations
├── tests/                  # Test suite
└── examples/               # Usage examples
```

## Performance

- **Provider rotation** - Automatic failover
- **Rate limiting** - Per-provider limits
- **Cost tracking** - Real-time cost monitoring
- **Caching** - Response caching (configurable)
- **Streaming** - Low-latency streaming
- **Parallel execution** - Concurrent tool calls

## Backwards Compatibility

The original HelperAgent API is preserved for backwards compatibility:

```python
from helper_agent import HelperAgent

async with HelperAgent() as agent:
    result = await agent.summarize_text(text)
```

## Contributing

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Run linters before submitting

## License

Part of the Hypr-Voice project.

## Version

Current version: 2.0.0

## Changelog

### 2.0.0 (Current)
- Multi-provider support with LiteLLM
- LangGraph agent workflows
- MCP protocol implementation
- SSE streaming support
- Enhanced configuration system
- Comprehensive test suite
- Detailed documentation

### 1.0.0
- Initial SGLang-based implementation
- Basic summarization and analysis
- Single provider support

