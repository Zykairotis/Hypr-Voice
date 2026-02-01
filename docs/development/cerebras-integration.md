# Cerebras Integration Guide

## Overview

Hypr-Voice integrates with Cerebras Cloud API for high-performance LLM inference. Cerebras provides extremely fast inference with support for multiple open-source models including Llama, Qwen, and more.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│               Cerebras Integration                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         CerebrasClient                                │   │
│  │  - API Key Rotation                                  │   │
│  │  - Model Selection                                   │   │
│  │  - Automatic Retry                                   │   │
│  └─────────────┬────────────────────────────────────────┘   │
│                │                                             │
│         ┌──────┴──────┐                                     │
│         │  REST API   │                                     │
│         │  Client     │                                     │
│         └──────┬──────┘                                     │
│                │                                             │
│  ┌─────────────┴────────────────────────────────────────┐   │
│  │              Supported Models                         │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │  │ Llama 3  │ │  Qwen 3  │ │  GPT-OSS │ │             │   │
│  │  │   70B    │ │  235B    │ │  120B    │ │             │   │
│  │  └──────────┘ └──────────┘ └──────────┘             │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Required: Cerebras API Keys
# You can specify multiple keys for rotation
CEREBRAS_API_KEY_ONE=your_first_key_here
CEREBRAS_API_KEY_TWO=your_second_key_here
CEREBRAS_API_KEY_THREE=your_third_key_here

# Alternative: Single key
CEREBRAS_API_KEY=your_key_here

# Alternative: Comma-separated list
CEREBRAS_API_KEYS=key1,key2,key3

# Optional: Model preferences
CEREBRAS_PREFERRED_MODELS=gpt-oss-120b,llama-3.3-70b,qwen-3-235b-a22b-thinking-2507
CEREBRAS_MODELS=llama-3.3-70b

# Optional: Token limits
CEREBRAS_DEFAULT_MAX_TOKENS=16000
CEREBRAS_MAX_TOKENS_LLAMA_3_3_70B=16000

# Optional: Connection settings
CEREBRAS_TIMEOUT=60
CEREBRAS_MAX_RETRIES=3
CEREBRAS_DEBUG=false
```

### Getting Cerebras API Keys

1. Visit https://cloud.cerebras.ai
2. Sign up for an account
3. Navigate to API Keys section
4. Generate one or more API keys
5. Copy keys to your `.env` file

## Usage

### Basic Usage

```python
from hypr_voice.services.Cerebras_integration.client import (
    CerebrasClient,
    CerebrasConfig
)

async def basic_example():
    # Load config from environment
    config = CerebrasConfig.from_env()

    # Create client
    client = CerebrasClient(config)

    # Simple chat completion
    response = await client.chat(
        messages=[{
            "role": "user",
            "content": "Hello! How are you?"
        }]
    )

    print(f"Response: {response['content']}")
    print(f"Model: {response['model']}")
    print(f"Tokens: {response['usage']}")
```

### Streaming Responses

```python
async def streaming_example():
    config = CerebrasConfig.from_env()
    client = CerebrasClient(config)

    messages = [{
        "role": "user",
        "content": "Tell me a short story about AI"
    }]

    # Stream response
    async for chunk in client.stream_chat(messages):
        if not chunk['is_final']:
            print(chunk['content'], end='', flush=True)
        else:
            print(f"\n\nTotal tokens: {chunk['usage']['total_tokens']}")
```

### Model Selection

```python
async def model_selection_example():
    config = CerebrasConfig(
        api_keys=["sk-..."],
        model_priority=[
            "gpt-oss-120b",        # Try GPT-OSS first
            "llama-3.3-70b",        # Fallback to Llama
            "qwen-3-235b-a22b-thinking-2507"  # Or Qwen
        ]
    )

    client = CerebrasClient(config)

    response = await client.chat(
        messages=[{"role": "user", "content": "..."}],
        model="llama-3.3-70b"  # Specific model
    )
```

### System Instructions

```python
async def system_prompt_example():
    client = CerebrasClient(CerebrasConfig.from_env())

    response = await client.chat(
        messages=[{
            "role": "user",
            "content": "What's the capital of France?"
        }],
        system_instruction="You are a helpful geography expert. " +
                          "Keep answers concise and accurate.",
        temperature=0.3  # Lower for factual responses
    )
```

### Advanced Configuration

```python
from hypr_voice.services.Cerebras_integration.client import (
    CerebrasClient,
    CerebrasConfig
)

config = CerebrasConfig(
    api_keys=["key1", "key2", "key3"],

    # Model priority
    model_priority=[
        "gpt-oss-120b",
        "llama-3.3-70b",
        "qwen-3-235b-a22b-instruct-2507"
    ],

    # Token limits
    default_max_tokens=16000,
    model_max_tokens={
        "llama-3.3-70b": 16000,
        "gpt-oss-120b": 16000,
        "qwen-3-235b-a22b-instruct-2507": 8192
    },

    # Connection settings
    base_url="https://api.cerebras.ai/v1",
    timeout=30.0,
    max_retries=3,
    retry_backoff=0.5
)

client = CerebrasClient(config)
```

## Supported Models

### GPT-OSS
- **gpt-oss-120b**: 120B parameter model
  - Context window: 65,536 tokens
  - Best for: General purpose, complex reasoning

### Llama 3.3
- **llama-3.3-70b**: 70B parameter model
  - Context window: 65,536 tokens
  - Best for: Chat, instructions, general tasks

- **llama3.1-70b**: Previous version
  - Context window: 65,536 tokens

- **llama3.1-8b**: Lightweight version
  - Context window: 8,192 tokens
  - Best for: Fast responses, simple tasks

### Qwen 3
- **qwen-3-235b-a22b-instruct-2507**: 235B parameter model
  - Context window: 65,536 tokens
  - Best for: Complex instructions, reasoning

- **qwen-3-235b-a22b-thinking-2507**: Thinking variant
  - Context window: 65,536 tokens
  - Best for: Deep reasoning, analysis

- **qwen-3-32b**: 32B parameter model
  - Context window: 65,536 tokens
  - Best for: Balanced performance

- **qwen-3-coder-480b**: 480B code model
  - Context window: 65,536 tokens
  - Best for: Code generation, programming

### Llama 4 (Experimental)
- **llama-4-scout-17b-16e-instruct**: 17B parameter model
  - Context window: 8,192 tokens
  - Best for: Fast responses, experimentation

## API Methods

### Chat Completion

```python
async def chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    system_instruction: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters**:
- `messages`: Conversation history
- `model`: Model name (uses first in priority if None)
- `temperature`: Sampling temperature (0.0-2.0)
- `max_tokens`: Maximum tokens to generate
- `top_p`: Nucleus sampling (0.0-1.0)
- `top_k`: Top-k sampling
- `system_instruction`: System-level instruction

**Returns**:
```python
{
    "content": str,      # Generated text
    "model": str,        # Model used
    "usage": {           # Token usage
        "prompt_tokens": int,
        "completion_tokens": int,
        "total_tokens": int
    }
}
```

### Streaming Chat

```python
async def stream_chat(
    messages: List[Dict[str, str]],
    **kwargs
) -> AsyncIterator[Dict[str, Any]]
```

**Yields**:
```python
{
    "content": str,      # Text chunk
    "usage": dict,       # Token usage (final chunk only)
    "is_final": bool,    # True for last chunk
    "chunk_index": int   # Chunk number
}
```

### Generate Content

```python
async def generate_content(
    content: Union[str, List[str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    system_instruction: Optional[str] = None
) -> Dict[str, Any]
```

Similar to `chat()` but accepts simpler content format.

### Stream Content

```python
async def stream_content(
    content: Union[str, List[str]],
    **kwargs
) -> AsyncIterator[Dict[str, Any]]
```

Streaming version of `generate_content()`.

## API Key Rotation

The Cerebras client automatically rotates through multiple API keys to distribute load and handle rate limits.

```python
config = CerebrasConfig(
    api_keys=[
        "sk-key1-...",
        "sk-key2-...",
        "sk-key3-..."
    ]
)

# Client automatically rotates keys on each request
client = CerebrasClient(config)

# Request 1 uses key1
response1 = await client.chat(messages=[...])

# Request 2 uses key2
response2 = await client.chat(messages=[...])

# Request 3 uses key3
response3 = await client.chat(messages=[...])

# Request 4 cycles back to key1
response4 = await client.chat(messages=[...])
```

## Model Selection Strategy

The client uses a priority-based model selection:

```python
config = CerebrasConfig(
    model_priority=[
        "gpt-oss-120b",              # 1st choice
        "llama-3.3-70b",             # 2nd choice
        "qwen-3-235b-a22b-instruct-2507"  # 3rd choice
    ]
)

client = CerebrasClient(config)

# Uses gpt-oss-120b (first available)
response1 = await client.chat(messages=[...])

# Explicitly use llama-3.3-70b
response2 = await client.chat(
    messages=[...],
    model="llama-3.3-70b"
)
```

## Troubleshooting

### API Key Not Found

**Error**: `ValueError: Cerebras API key(s) not found`

**Solution**:
```bash
# Set at least one API key
export CEREBRAS_API_KEY=your_key_here

# Or use numbered keys
export CEREBRAS_API_KEY_ONE=your_key_here

# Or comma-separated
export CEREBRAS_API_KEYS=key1,key2,key3
```

### Model Not Available

**Error**: `Model not found or not accessible`

**Solution**:
```python
# Check available models in your account
# Visit: https://cloud.cerebras.ai/dashboard

# Use a different model
response = await client.chat(
    messages=[...],
    model="llama-3.3-70b"  # Use available model
)
```

### Timeout Errors

**Error**: `Request timeout after 30 seconds`

**Solution**:
```python
config = CerebrasConfig(
    api_keys=[...],
    timeout=120.0  # Increase to 2 minutes
)
```

### Rate Limiting

**Error**: `Rate limit exceeded`

**Solution**:
```python
# Use multiple API keys for rotation
config = CerebrasConfig(
    api_keys=[
        "key1",
        "key2",
        "key3",  # More keys = higher rate limit
        "key4",
        "key5"
    ]
)

# Or reduce request frequency
import asyncio
await asyncio.sleep(1)  # Delay between requests
```

### Context Window Exceeded

**Error**: `Input exceeds model context window`

**Solution**:
```python
# Reduce input length
messages = messages[-10:]  # Keep last 10 messages

# Or use model with larger context
response = await client.chat(
    messages=messages,
    model="llama-3.3-70b"  # 65k context
)
```

## Performance Optimization

### For Speed

```python
config = CerebrasConfig(
    api_keys=["key1", "key2"],  # Multiple keys for parallelism
    model_priority=["llama3.1-8b"],  # Smaller model
    timeout=30.0  # Lower timeout
)
```

### For Quality

```python
response = await client.chat(
    messages=[...],
    model="qwen-3-235b-a22b-thinking-2507",  # Largest model
    temperature=0.7,  # Balanced creativity
    max_tokens=16000  # Allow longer responses
)
```

### For Cost Efficiency

```python
config = CerebrasConfig(
    model_priority=["llama3.1-8b"],  # Smaller/cheaper model
    default_max_tokens=4096  # Limit output tokens
)
```

### For Code Generation

```python
response = await client.chat(
    messages=[{
        "role": "user",
        "content": "Write a Python function to..."
    }],
    model="qwen-3-coder-480b",  # Code-optimized model
    temperature=0.2,  # Lower for more deterministic code
    max_tokens=4096
)
```

## Best Practices

### 1. Use Multiple API Keys

```python
# Distribute load and handle rate limits
config = CerebrasConfig(
    api_keys=os.getenv("CEREBRAS_API_KEYS", "").split(",")
)
```

### 2. Implement Retry Logic

```python
# Client automatically retries with exponential backoff
config = CerebrasConfig(
    api_keys=[...],
    max_retries=3,
    retry_backoff=0.5  # 0.5s, 1s, 2s
)
```

### 3. Choose Appropriate Models

```python
# Fast tasks: Small models
# Complex tasks: Large models
# Code tasks: Code models

MODEL_GUIDE = {
    "chat": "llama-3.3-70b",
    "reasoning": "qwen-3-235b-a22b-thinking-2507",
    "code": "qwen-3-coder-480b",
    "fast": "llama3.1-8b"
}
```

### 4. Monitor Token Usage

```python
response = await client.chat(messages=[...])

usage = response['usage']
print(f"Prompt: {usage['prompt_tokens']}")
print(f"Completion: {usage['completion_tokens']}")
print(f"Total: {usage['total_tokens']}")

# Track costs (assuming $0.60/1M tokens for input)
cost = (usage['prompt_tokens'] / 1_000_000) * 0.60
print(f"Estimated cost: ${cost:.4f}")
```

### 5. Use Streaming for Long Responses

```python
async for chunk in client.stream_chat(messages):
    if not chunk['is_final']:
        # Display partial response
        print(chunk['content'], end='', flush=True)
```

## Integration Examples

### Voice Assistant

```python
async def voice_assistant(user_input):
    from hypr_voice.services.Cerebras_integration.client import (
        CerebrasClient, CerebrasConfig
    )

    config = CerebrasConfig.from_env()
    client = CerebrasClient(config)

    # Generate response
    response = await client.chat(
        messages=[{
            "role": "user",
            "content": user_input
        }],
        system_instruction="You are a helpful voice assistant. " +
                          "Keep responses concise and conversational.",
        temperature=0.8
    )

    return response['content']
```

### Code Generation

```python
async def generate_code(prompt):
    client = CerebrasClient(CerebrasConfig.from_env())

    response = await client.chat(
        messages=[{
            "role": "user",
            "content": f"Write a Python function to: {prompt}"
        }],
        model="qwen-3-coder-480b",
        temperature=0.2,
        max_tokens=4096
    )

    return response['content']
```

### Document Analysis

```python
async def analyze_document(document_text):
    client = CerebrasClient(CerebrasConfig.from_env())

    response = await client.chat(
        messages=[{
            "role": "user",
            "content": f"Analyze this document:\n\n{document_text}"
        }],
        model="qwen-3-235b-a22b-thinking-2507",
        temperature=0.5,
        max_tokens=8192
    )

    return response['content']
```

### Multi-Turn Conversation

```python
async def conversation():
    client = CerebrasClient(CerebrasConfig.from_env())

    messages = []

    while True:
        user_input = input("You: ")

        messages.append({
            "role": "user",
            "content": user_input
        })

        response = await client.chat(messages=messages)
        assistant_message = response['content']

        print(f"Assistant: {assistant_message}")

        messages.append({
            "role": "assistant",
            "content": assistant_message
        })
```

## API Reference

### CerebrasConfig

**Constructor Parameters**:
- `api_keys (Sequence[str])`: API keys for rotation
- `model_priority (Sequence[str])`: Model selection priority
- `base_url (str)`: API base URL (default: "https://api.cerebras.ai/v1")
- `timeout (float)`: Request timeout in seconds (default: 30.0)
- `max_retries (int)`: Maximum retry attempts (default: 2)
- `retry_backoff (float)`: Retry delay multiplier (default: 0.25)
- `model_context_window (Dict[str, int])`: Context window sizes
- `model_max_tokens (Dict[str, int])`: Max tokens per model
- `default_max_tokens (int)`: Default max tokens (default: 16000)

**Class Methods**:
- `from_env()`: Load configuration from environment variables

### CerebrasClient

**Constructor**:
- `config (CerebrasConfig)`: Configuration object

**Methods**:
- `async chat(messages, **kwargs)`: Chat completion
- `async stream_chat(messages, **kwargs)`: Streaming chat
- `async generate_content(content, **kwargs)`: Generate content
- `async stream_content(content, **kwargs)`: Streaming content
- `property last_usage`: Get last request's token usage

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [Gemini Integration](./gemini-integration.md)
- [TTS Integration](./tts-integration.md)
- [Architecture Overview](./ARCHITECTURE.md)
