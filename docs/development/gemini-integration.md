# Gemini Live Integration Guide

## Overview

Hypr-Voice integrates with Google Gemini Live API for multimodal AI capabilities including text, image analysis, and real-time streaming responses.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Gemini Live Integration                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              GeminiClient                             │   │
│  │  - Multimodal Support (Text + Images)                │   │
│  │  - Streaming Responses                               │   │
│  │  - Live API Support                                  │   │
│  │  - Vertex AI Integration                             │   │
│  └─────────────┬────────────────────────────────────────┘   │
│                │                                             │
│         ┌──────┴──────┐                                     │
│         │  Live API   │                                     │
│         │  / REST API │                                     │
│         └──────┬──────┘                                     │
│                │                                             │
│  ┌─────────────┴────────────────────────────────────────┐   │
│  │              Supported Models                         │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ Gemini Live  │  │ Gemini Flash │ │                 │   │
│  │  │ 2.5 Preview  │  │   2.5/2.0    │ │                 │   │
│  │  │ (WebSocket)  │  │  (REST)      │ │                 │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

```bash
# Required: Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# Alternative (Google also accepts this)
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Model selection
GEMINI_MODEL=gemini-live-2.5-flash-preview

# Optional: Vertex AI (Enterprise)
GEMINI_VERTEX_AI=true
GOOGLE_CLOUD_PROJECT=your-project-id
GCP_PROJECT=your-project-id
GEMINI_LOCATION=us-central1
```

### Getting Gemini API Key

1. Visit https://makersuite.google.com/app/apikey
2. Create a new API key
3. Copy the key to your `.env` file:
   ```bash
   GEMINI_API_KEY=your_api_key_here
   ```

### Python Installation

```bash
pip install google-genai
pip install pillow  # For image support
```

## Usage

### Basic Text Generation

```python
from hypr_voice.services.gemini_live.gemini_client import (
    GeminiClient,
    GeminiConfig
)

async def basic_example():
    # Load config from environment
    config = GeminiConfig.from_env()

    # Create client
    client = GeminiClient(config)

    # Generate content
    response = await client.generate_content(
        "Hello! How are you?"
    )

    print(f"Response: {response['content']}")
    print(f"Model: {response['model']}")
    print(f"Tokens: {response['usage']}")
```

### Streaming Responses

```python
async def streaming_example():
    client = GeminiClient(GeminiConfig.from_env())

    # Stream response
    async for chunk in client.stream_content(
        "Tell me a short story about AI"
    ):
        if not chunk['is_final']:
            print(chunk['content'], end='', flush=True)
        else:
            print(f"\n\nTotal tokens: {chunk['usage']['total_tokens']}")
```

### Multimodal (Text + Images)

```python
from pathlib import Path

async def multimodal_example():
    client = GeminiClient(GeminiConfig.from_env())

    # Text + Image
    response = await client.generate_content([
        "What's in this image?",
        Path("/path/to/image.jpg")
    ])

    print(response['content'])

    # Multiple images
    response = await client.generate_content([
        "Compare these two images",
        Path("/path/to/image1.jpg"),
        Path("/path/to/image2.jpg")
    ])

    # Image bytes
    with open("/path/to/image.png", "rb") as f:
        image_bytes = f.read()

    response = await client.generate_content([
        "Describe this image",
        image_bytes
    ])
```

### Chat with History

```python
async def chat_example():
    client = GeminiClient(GeminiConfig.from_env())

    messages = [
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi! How can I help?"},
        {"role": "user", "content": "What's the capital of France?"}
    ]

    response = await client.chat(messages)
    print(response['content'])
```

### Live API (WebSocket)

```python
async def live_api_example():
    config = GeminiConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-live-2.5-flash-preview"  # Live API model
    )

    client = GeminiClient(config)

    # Uses WebSocket Live API automatically
    response = await client.generate_content(
        "Explain quantum computing"
    )

    print(response['content'])
```

### Vertex AI Integration

```python
async def vertex_ai_example():
    config = GeminiConfig(
        api_key=None,  # Not needed for Vertex AI
        enable_vertex=True,
        project_id="your-gcp-project",
        location="us-central1"
    )

    client = GeminiClient(config)

    response = await client.generate_content(
        "Hello from Vertex AI!"
    )

    print(response['content'])
```

## Supported Models

### Live API Models (WebSocket)

These models use a WebSocket connection for real-time streaming:

- **gemini-live-2.5-flash-preview** (default)
  - Input: 64,000 tokens
  - Output: 1,000,000 tokens
  - Best for: Real-time conversations

- **gemini-2.5-flash-live-preview**
  - Input: 64,000 tokens
  - Output: 1,000,000 tokens
  - Similar to above

- **gemini-2.0-flash-live-001**
  - Input: 64,000 tokens
  - Output: 1,000,000 tokens
  - Previous generation

### REST API Models

Standard REST API models:

- **gemini-2.0-flash-exp**
  - Input: 1,048,576 tokens
  - Output: 8,192 tokens
  - Best for: Fast responses, large inputs

- **gemini-2.0-flash-thinking-exp-01-21**
  - Input: 1,048,576 tokens
  - Output: 64,000 tokens
  - Best for: Complex reasoning

- **gemini-2.5-flash**
  - Input: 1,048,576 tokens
  - Output: 65,536 tokens
  - Best for: General use

- **gemini-2.5-pro**
  - Input: 1,048,576 tokens
  - Output: 65,536 tokens
  - Best for: High quality

- **gemini-1.5-flash**
  - Input: 1,048,576 tokens
  - Output: 8,192 tokens
  - Best for: Speed

- **gemini-1.5-pro**
  - Input: 2,097,152 tokens
  - Output: 8,192 tokens
  - Best for: Large context

## API Methods

### Generate Content

```python
async def generate_content(
    content: Union[str, List[Union[str, bytes, Image.Image, Path]]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    system_instruction: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters**:
- `content`: Text, image, or list of both
- `model`: Model name (uses config default if None)
- `temperature`: Sampling temperature (0.0-2.0)
- `max_output_tokens`: Maximum tokens to generate
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

### Stream Content

```python
async def stream_content(
    content: Union[str, List],
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

### Chat Completion

```python
async def chat(
    messages: Sequence[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_output_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    top_k: Optional[int] = None,
    system_instruction: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters**:
- `messages`: Conversation history
  - Format: `[{"role": "user", "content": "..."}, ...]`

### Stream Chat

```python
async def stream_chat(
    messages: Sequence[Dict[str, str]],
    **kwargs
) -> AsyncIterator[Dict[str, Any]]
```

Streaming version of `chat()`.

## Multimodal Capabilities

### Image Analysis

```python
from PIL import Image

async def analyze_image():
    client = GeminiClient(GeminiConfig.from_env())

    # Load image
    image = Image.open("/path/to/image.jpg")

    # Analyze
    response = await client.generate_content([
        "Describe this image in detail",
        image
    ])

    print(response['content'])
```

### Multiple Images

```python
async def compare_images():
    client = GeminiClient(GeminiConfig.from_env())

    response = await client.generate_content([
        "What are the differences between these images?",
        Path("/path/to/image1.jpg"),
        Path("/path/to/image2.jpg"),
        Path("/path/to/image3.jpg")
    ])

    print(response['content'])
```

### Image Bytes

```python
async def analyze_image_bytes():
    client = GeminiClient(GeminiConfig.from_env())

    # Read image as bytes
    with open("/path/to/image.png", "rb") as f:
        image_bytes = f.read()

    response = await client.generate_content([
        "What's in this image?",
        image_bytes  # Automatically detected as PNG
    ])

    print(response['content'])
```

### Mixed Content

```python
async def mixed_content():
    client = GeminiClient(GeminiConfig.from_env())

    response = await client.generate_content([
        "Here's a photo of my cat: ",
        Path("/path/to/cat.jpg"),
        "\n\nAnd here's a photo of my dog: ",
        Path("/path/to/dog.jpg"),
        "\n\nWhich one is cuter?"
    ])

    print(response['content'])
```

## Live API Features

### Automatic Live API Detection

The client automatically uses the Live API for specific models:

```python
# These models trigger WebSocket Live API
LIVE_MODELS = {
    "gemini-live-2.5-flash-preview",
    "gemini-2.5-flash-live-preview",
    "gemini-2.0-flash-live-001"
}

config = GeminiConfig(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-live-2.5-flash-preview"  # Uses Live API
)

client = GeminiClient(config)
# WebSocket connection established automatically
```

### Live API Streaming

```python
async def live_streaming():
    config = GeminiConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-live-2.5-flash-preview"
    )

    client = GeminiClient(config)

    # Stream over WebSocket
    async for chunk in client.stream_content(
        "Tell me an interesting story"
    ):
        print(chunk['content'], end='', flush=True)
```

### Live API with Images

```python
async def live_multimodal():
    config = GeminiConfig(
        api_key=os.getenv("GEMINI_API_KEY"),
        model="gemini-live-2.5-flash-preview"
    )

    client = GeminiClient(config)

    response = await client.generate_content([
        "What do you see?",
        Path("/path/to/image.jpg")
    ])

    print(response['content'])
```

## Vertex AI Integration

### Vertex AI Setup

```python
config = GeminiConfig(
    # No API key needed for Vertex AI
    enable_vertex=True,
    project_id="your-gcp-project-id",
    location="us-central1"  # or other region
)

client = GeminiClient(config)
```

### Vertex AI Authentication

Vertex AI uses Google Cloud authentication:

```bash
# Using Application Default Credentials
gcloud auth application-default login

# Or set service account key
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### Vertex AI Usage

```python
# Same API as regular Gemini client
client = GeminiClient(GeminiConfig(
    enable_vertex=True,
    project_id="my-project"
))

response = await client.generate_content("Hello!")
print(response['content'])
```

## Troubleshooting

### API Key Not Found

**Error**: `Gemini API key not found`

**Solution**:
```bash
# Set API key
export GEMINI_API_KEY=your_api_key_here

# Or alternative
export GOOGLE_API_KEY=your_api_key_here
```

### Model Not Available

**Error**: `Model not found or not accessible`

**Solution**:
```python
# Use a different model
response = await client.generate_content(
    "...",
    model="gemini-2.0-flash-exp"  # Use available model
)
```

### Image Loading Failed

**Error**: `Failed to load image`

**Solution**:
```bash
# Install Pillow
pip install pillow

# Check image format
from PIL import Image
img = Image.open("/path/to/image.jpg")
print(img.format, img.size)
```

### Live API Connection Failed

**Error**: `Gemini Live API error`

**Solution**:
```python
# Use REST API model instead
config = GeminiConfig(
    api_key=os.getenv("GEMINI_API_KEY"),
    model="gemini-2.0-flash-exp"  # REST API model
)

client = GeminiClient(config)
```

### Vertex AI Authentication Failed

**Error**: `Could not determine project ID`

**Solution**:
```bash
# Set project explicitly
export GOOGLE_CLOUD_PROJECT=your-project-id

# Or authenticate
gcloud auth application-default login

# Or use service account
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

## Best Practices

### 1. Choose Appropriate Models

```python
MODEL_GUIDE = {
    "realtime": "gemini-live-2.5-flash-preview",
    "fast": "gemini-2.0-flash-exp",
    "reasoning": "gemini-2.0-flash-thinking-exp-01-21",
    "quality": "gemini-2.5-pro",
    "large_context": "gemini-1.5-pro"
}

def select_model(task_type):
    return MODEL_GUIDE.get(task_type, "gemini-2.5-flash")
```

### 2. Use Streaming for Long Responses

```python
async for chunk in client.stream_content(long_prompt):
    if not chunk['is_final']:
        # Display in real-time
        print(chunk['content'], end='', flush=True)
```

### 3. Handle Token Limits

```python
# Check model limits
from hypr_voice.services.gemini_live.gemini_client import MODEL_MAX_INPUT_TOKENS

model = "gemini-2.0-flash-exp"
max_tokens = MODEL_MAX_INPUT_TOKENS[model]

if len(input_tokens) > max_tokens:
    # Truncate or split input
    input_tokens = input_tokens[:max_tokens]
```

### 4. Optimize Image Inputs

```python
# Resize large images
from PIL import Image

def optimize_image(image_path, max_size=(1024, 1024)):
    img = Image.open(image_path)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)
    return img
```

### 5. Monitor Token Usage

```python
response = await client.generate_content(...)

usage = response['usage']
print(f"Prompt: {usage['prompt_tokens']}")
print(f"Completion: {usage['completion_tokens']}")
print(f"Total: {usage['total_tokens']}")

# Check last usage
last_usage = client.last_usage
print(f"Last request: {last_usage}")
```

## Integration Examples

### Image Captioning

```python
async def caption_image(image_path):
    client = GeminiClient(GeminiConfig.from_env())

    response = await client.generate_content([
        "Provide a detailed caption for this image",
        Path(image_path)
    ])

    return response['content']
```

### Visual Question Answering

```python
async def visual_qa(image_path, question):
    client = GeminiClient(GeminiConfig.from_env())

    response = await client.generate_content([
        f"Question: {question}\nAnswer:",
        Path(image_path)
    ])

    return response['content']
```

### Voice Assistant with Vision

```python
async def voice_with_vision(audio_transcript, image_path):
    from hypr_voice.services.gemini_live.gemini_client import GeminiClient

    client = GeminiClient(GeminiConfig.from_env())

    response = await client.generate_content([
        f"I said: {audio_transcript}",
        "\n\nLooking at this image: ",
        Path(image_path),
        "\n\nHow would you respond?"
    ])

    return response['content']
```

### Real-Time Image Analysis

```python
async def realtime_analysis(image_stream):
    client = GeminiClient(GeminiConfig.from_env())

    async for image in image_stream:
        response = await client.generate_content([
            "What's in this image?",
            image
        ])

        print(f"Analysis: {response['content']}")
```

## API Reference

### GeminiConfig

**Constructor Parameters**:
- `api_key (str)`: Gemini API key
- `model (str)`: Model name (default: "gemini-live-2.5-flash-preview")
- `timeout (float)`: Request timeout in seconds (default: 60.0)
- `max_retries (int)`: Maximum retry attempts (default: 2)
- `retry_backoff (float)`: Retry delay multiplier (default: 0.5)
- `enable_vertex (bool)`: Use Vertex AI (default: False)
- `project_id (str, optional)`: Google Cloud project ID
- `location (str)`: Vertex AI location (default: "us-central1")

**Class Methods**:
- `from_env()`: Load configuration from environment variables

### GeminiClient

**Constructor**:
- `config (GeminiConfig)`: Configuration object

**Methods**:
- `async generate_content(content, **kwargs)`: Generate content
- `async stream_content(content, **kwargs)`: Stream content generation
- `async chat(messages, **kwargs)`: Chat completion
- `async stream_chat(messages, **kwargs)`: Stream chat
- `property last_usage`: Get last request's token usage

### Constants

- `DEFAULT_MODEL`: Default model name
- `LIVE_MODELS`: List of Live API models
- `WEBSOCKET_MODELS`: Set of models requiring WebSocket
- `MODEL_MAX_OUTPUT_TOKENS`: Max output tokens per model
- `MODEL_MAX_INPUT_TOKENS`: Max input tokens per model

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [Cerebras Integration](./cerebras-integration.md)
- [TTS Integration](./tts-integration.md)
- [Architecture Overview](./ARCHITECTURE.md)
