# Unified Helper-Agent Architecture

## Overview

The helper-agent has been refactored into a **unified architecture** that combines:

- **ModelFactory**: LangChain chat models built on top of LiteLLM for multi-provider routing
- **MCPToolRegistry**: Single source of truth for both MCP server and LangGraph agent tools
- **LangGraph ReAct Agent**: Official `create_react_agent` for intelligent reasoning and tool use
- **HelperAgentIntegration**: High-level API that ties everything together

## Architecture Components

### 1. ModelFactory (`model_factory.py`)

Creates LangChain chat models using LiteLLM backend with automatic provider selection and metrics tracking.

```python
from helper_agent import ModelFactory

# Create factory
factory = ModelFactory()
await factory.initialize()

# Auto-select best provider
chat_model = factory.create_chat_model(temperature=0.7, max_tokens=1024)

# Or specify provider
chat_model = factory.create_chat_model(provider="openai", model="gpt-4")

# Get metrics
metrics = factory.get_provider_metrics()
```

**Features:**
- Automatic provider selection based on availability, cost, speed
- Rate limiting and fallback handling
- Usage/cost tracking via LangChain callbacks
- Support for all LiteLLM providers (OpenAI, Claude, Groq, xAI, Ollama, etc.)

### 2. MCPToolRegistry (`tools/mcp_registry.py`)

Unified registry that converts tool definitions into both MCP specs and LangChain `StructuredTool`s.

```python
from helper_agent import MCPToolRegistry, ToolCategory

# Create registry
registry = MCPToolRegistry()

# List tools
all_tools = registry.list_tools()
text_tools = registry.list_tools(category=ToolCategory.TEXT_PROCESSING)

# Get LangChain tools
langchain_tools = registry.get_langchain_tools()

# Register with MCP server
registry.register_with_mcp_server(mcp_server)
```

**Features:**
- Single source of truth for tool definitions
- Automatic conversion to LangChain `StructuredTool`s
- Category-based organization
- JSON Schema → Pydantic model conversion

### 3. LangGraph ReAct Agent (`agent_graph.py`)

Official LangGraph ReAct agent using `create_react_agent` with ModelFactory and MCPToolRegistry.

```python
from helper_agent import LangGraphAgent, ModelFactory, MCPToolRegistry

# Create agent
agent = LangGraphAgent(
    model_factory=ModelFactory(),
    tool_registry=MCPToolRegistry(),
    provider="openai"  # optional
)

await agent.initialize()

# Simple invocation
result = await agent.invoke("What is 2 + 2?")
print(result["response"])

# Multi-turn conversation
result = await agent.invoke("My name is Alice", thread_id="user-123")
result = await agent.invoke("What's my name?", thread_id="user-123")

# Streaming
async for chunk in agent.stream("Tell me a joke"):
    print(chunk, end="", flush=True)
```

**Features:**
- Official LangGraph `create_react_agent` pattern
- State checkpointing for multi-turn conversations
- Streaming support
- Tool calling with reasoning

### 4. HelperAgentIntegration (`integration.py`)

High-level API that orchestrates all components.

```python
from helper_agent import HelperAgentIntegration

# Create integration
integration = HelperAgentIntegration(
    provider="openai",  # optional
    model="gpt-4"       # optional
)

await integration.initialize()

# Direct chat (no tools)
response = await integration.chat([
    {"role": "user", "content": "Hello!"}
])

# Agentic query (with tools and reasoning)
result = await integration.agentic_query(
    "Summarize this text and calculate word count"
)

# Streaming agentic query
async for chunk in integration.stream_agentic_query("Explain quantum computing"):
    print(chunk, end="", flush=True)

# Call MCP tool directly
result = await integration.call_mcp_tool(
    tool_name="calculator",
    args={"expression": "10 * 5"}
)
```

## Migration Guide

### Old Approach (Custom Workflow)

```python
# Old: Manual LiteLLM client + custom workflow
client = LiteLLMClient()
agent = LangGraphAgent(litellm_client=client, tools=tools)
result = await agent.run(task)
```

### New Approach (Unified Architecture)

```python
# New: Unified with ModelFactory + MCPToolRegistry
integration = HelperAgentIntegration()
await integration.initialize()
result = await integration.agentic_query(query)
```

## Key Improvements

1. **Single Source of Truth**: MCPToolRegistry ensures MCP server and LangGraph agent use identical tool definitions

2. **Official Patterns**: Uses `create_react_agent` from LangGraph instead of custom workflow

3. **Better Separation**: ModelFactory handles model creation, agent handles workflow, integration ties them together

4. **Type Safety**: Pydantic models generated from JSON Schema for tool parameters

5. **Metrics & Callbacks**: LangChain callbacks automatically track usage/cost for all providers

6. **Backwards Compatible**: Old `LiteLLMClient` still works for direct access

## Configuration

All configuration remains in YAML files:

- `config/providers.yaml` - Provider settings, API keys, models
- `config/mcp_tools.yaml` - MCP tool definitions (optional, registry has builtins)
- `config/agent_config.yaml` - Agent settings, system prompt, tool categories

## Tool Categories

Available tool categories in MCPToolRegistry:

- `TEXT_PROCESSING` - summarize_text, analyze_content, extract_information
- `PLANNING` - plan_task
- `COMPUTATION` - calculator
- `AI_INTEGRATION` - claude_sdk_bridge
- `CUSTOM` - User-defined tools

## Provider Support

All LiteLLM providers are supported:

- **OpenAI** (gpt-4, gpt-3.5-turbo, etc.)
- **Anthropic** (claude-3-opus, sonnet, haiku)
- **Groq** (llama3-70b, mixtral, gemma)
- **xAI** (grok-beta)
- **Ollama** (local models)
- **OpenRouter** (unified access to many models)
- **Cohere** (command, command-r-plus)
- **Together AI** (open source models)
- **Mistral AI** (mistral-large, medium, small)
- **Perplexity** (pplx-70b-online, pplx-7b-online)
- **SGLang** (custom Qwen3 integration)

## Examples

See `examples/unified_architecture.py` for comprehensive usage examples.

## Testing

Run tests for the unified architecture:

```bash
pytest tests/test_model_factory.py
pytest tests/test_mcp_registry.py
pytest tests/test_unified_agent.py
```

## Next Steps

1. **Add Custom Tools**: Register your own tools with MCPToolRegistry
2. **Provider Optimization**: Configure task-specific provider preferences in `providers.yaml`
3. **Multi-Agent**: Use multiple agents with different providers for specialized tasks
4. **Production Deployment**: Enable metrics export and monitoring in config

