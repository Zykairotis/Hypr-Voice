# Gemini Live vs Cerebras Integration Comparison

This document compares the Gemini Live and Cerebras integrations in Hypr-Voice.

## Architecture Comparison

### Similarities

Both integrations follow the same architectural pattern:

```
├── client.py          # Low-level API client
├── integration.py     # High-level helpers
├── chat_tui.py        # Terminal UI
├── requirements.txt   # Dependencies
├── __init__.py        # Exports
└── README.md          # Documentation
```

### Key Features

| Feature | Gemini Live | Cerebras |
|---------|-------------|----------|
| **Streaming** | ✅ Token-by-token | ✅ Token-by-token |
| **Multimodal** | ✅ Text + Images | ❌ Text only |
| **Token Tracking** | ✅ Full usage stats | ✅ Full usage stats |
| **Multiple Models** | ✅ 6+ models | ✅ 8+ models |
| **Chat Sessions** | ✅ With history | ✅ With history |
| **Rich TUI** | ✅ Interactive | ✅ Interactive |
| **Temperature Control** | ✅ 0.0-2.0 | ✅ 0.0-2.0 |
| **Max Tokens** | ✅ Configurable | ✅ Configurable |
| **System Instructions** | ✅ Per-request | ✅ Per-session |
| **API Compatibility** | Gemini-specific | OpenAI-compatible |

## Client API Comparison

### Initialization

**Gemini:**
```python
from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig

config = GeminiConfig.from_env()
client = GeminiClient(config)
```

**Cerebras:**
```python
from hypr_voice.services.Cerebras_integration import CerebrasClient, CerebrasConfig

config = CerebrasConfig.from_env()
client = CerebrasClient(config)
```

### Basic Generation

**Gemini:**
```python
response = await client.generate_content(
    "Your prompt",
    temperature=0.7,
    max_output_tokens=500
)
print(response["content"])
```

**Cerebras:**
```python
response = await client.chat(
    messages=[{"role": "user", "content": "Your prompt"}],
    temperature=0.7,
    max_tokens=500
)
print(response["content"])
```

### Streaming

**Gemini:**
```python
async for chunk in client.stream_content("Your prompt"):
    print(chunk["content"], end="", flush=True)
```

**Cerebras:**
```python
async for chunk in client.stream_chat(messages):
    print(chunk, end="", flush=True)
```

### Multimodal (Gemini Only)

```python
from pathlib import Path

# Single image
response = await client.generate_content([
    "Describe this image:",
    Path("photo.jpg")
])

# Multiple images
response = await client.generate_content([
    Path("image1.jpg"),
    Path("image2.jpg"),
    "Compare these images"
])
```

## Integration Helpers Comparison

### Gemini Integration

```python
async with GeminiIntegration() as gemini:
    # Image analysis (unique to Gemini)
    analysis = await gemini.analyze_image(
        Path("photo.jpg"),
        prompt="Describe this image"
    )
    
    # Multimodal query
    response = await gemini.multimodal_query(
        "Analyze these images",
        images=[Path("img1.jpg"), Path("img2.jpg")]
    )
    
    # Text operations
    summary = await gemini.summarize(text, style="bullet_points")
    category = await gemini.classify(text, categories=["A", "B", "C"])
    keywords = await gemini.extract_keywords(text, max_keywords=5)
    
    # Chat session
    session = gemini.session(system_instruction="You are helpful")
    response = await session.send("Hello!")
```

### Cerebras Integration

```python
async with CerebrasIntegration() as cerebras:
    # Text summarization
    summary = await cerebras.summarize_for_tts(
        text,
        style="concise",
        max_words=60
    )
    
    # Classification
    category = await cerebras.classify(
        text,
        categories=["A", "B", "C"]
    )
    
    # Streaming summary
    async for chunk in cerebras.stream_summary(text):
        print(chunk, end="")
    
    # Chat session
    session = cerebras.session(system_prompt="You are helpful")
    response = await session.send("Hello!")
```

## TUI Comparison

### Common Features

Both TUIs support:
- Model selection
- Temperature adjustment
- Max tokens configuration
- Streaming toggle
- Conversation history
- Statistics display
- Keyboard shortcuts

### Gemini TUI Unique Features

- 🖼️ **Image upload** (`/image` command)
- 🗑️ **Clear images** (`/clear-img` command)
- 📊 **Enhanced stats** with multimodal tracking
- 🎨 **Visual indicators** for images in messages

### Commands Comparison

| Command | Gemini | Cerebras |
|---------|--------|----------|
| `/model` | ✅ | ✅ |
| `/image` | ✅ | ❌ |
| `/clear-img` | ✅ | ❌ |
| `/stream` | ✅ | ✅ |
| `/temp` | ✅ | ✅ |
| `/tokens` | ✅ | ✅ |
| `/system` | ✅ | ❌ |
| `/reset` | ✅ | ✅ |
| `/stats` | ✅ | ❌ |
| `/help` | ✅ | ✅ |
| `/quit` | ✅ | ✅ |

## Performance Comparison

### Streaming Performance

**Gemini Live:**
- Average: 30-50 tokens/sec
- Peak: 80+ tokens/sec
- Latency: ~100-200ms first token

**Cerebras:**
- Average: 100-200 tokens/sec
- Peak: 400+ tokens/sec
- Latency: ~50-100ms first token

**Winner:** Cerebras (significantly faster)

### Multimodal Performance

**Gemini Live:**
- Image processing: ~500ms-2s per image
- Supports: JPEG, PNG, GIF, WebP, BMP
- Max image size: ~20MB

**Cerebras:**
- N/A (text-only)

**Winner:** Gemini (only option for multimodal)

## Use Case Recommendations

### Use Gemini Live When:

1. **Multimodal tasks**
   - Image analysis
   - Visual question answering
   - Document understanding
   - Screenshot analysis

2. **Rich context**
   - Combining visual and textual information
   - UI/UX analysis
   - Photo descriptions

3. **Diverse models**
   - Access to Gemini 2.0/2.5 models
   - Different model capabilities

### Use Cerebras When:

1. **Speed is critical**
   - Real-time chat
   - Low-latency applications
   - High-throughput processing

2. **Text-only tasks**
   - Code generation
   - Text summarization
   - Conversational AI

3. **Cost optimization**
   - Potentially lower cost per token
   - Multiple API key rotation

## Configuration Comparison

### Environment Variables

**Gemini:**
```bash
GEMINI_API_KEY=your-key
GEMINI_MODEL=gemini-2.0-flash-exp
GEMINI_VERTEX_AI=false
GOOGLE_CLOUD_PROJECT=your-project
GEMINI_LOCATION=us-central1
```

**Cerebras:**
```bash
CEREBRAS_API_KEY=your-key
CEREBRAS_API_KEYS=key1,key2,key3  # Multiple keys
CEREBRAS_PREFERRED_MODELS=model1,model2
CEREBRAS_DEFAULT_MAX_TOKENS=16000
```

## Integration Patterns

### Pattern 1: Simple Query

**Gemini:**
```python
client = GeminiClient(GeminiConfig.from_env())
response = await client.generate_content("Question")
```

**Cerebras:**
```python
client = CerebrasClient(CerebrasConfig.from_env())
response = await client.chat([{"role": "user", "content": "Question"}])
```

### Pattern 2: Streaming with Context

**Gemini:**
```python
async for chunk in client.stream_content(
    ["Context image", "Question"],
    system_instruction="Be helpful"
):
    process(chunk["content"])
```

**Cerebras:**
```python
messages = [
    {"role": "system", "content": "Be helpful"},
    {"role": "user", "content": "Question"}
]
async for chunk in client.stream_chat(messages):
    process(chunk)
```

### Pattern 3: Session-Based Chat

Both follow similar patterns:

```python
# Gemini
session = integration.session(system_instruction="Be helpful")
response = await session.send("Hello")

# Cerebras
session = integration.session(system_prompt="Be helpful")
response = await session.send("Hello")
```

## Error Handling

Both integrations use similar error handling:

```python
try:
    response = await client.generate_content("Prompt")
except ValueError as e:
    # Configuration errors
except RuntimeError as e:
    # API errors
except Exception as e:
    # Other errors
```

## Migration Guide

### Cerebras to Gemini

```python
# Cerebras
from hypr_voice.services.Cerebras_integration import CerebrasClient

client = CerebrasClient()
response = await client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7,
    max_tokens=500
)

# Gemini equivalent
from hypr_voice.services.gemini_live import GeminiClient

client = GeminiClient()
response = await client.generate_content(
    "Hello",
    temperature=0.7,
    max_output_tokens=500
)
```

### Gemini to Cerebras

```python
# Gemini
from hypr_voice.services.gemini_live import GeminiClient

client = GeminiClient()
response = await client.generate_content(
    "Hello",
    temperature=0.7
)

# Cerebras equivalent
from hypr_voice.services.Cerebras_integration import CerebrasClient

client = CerebrasClient()
response = await client.chat(
    messages=[{"role": "user", "content": "Hello"}],
    temperature=0.7
)
```

## Conclusion

**Choose Gemini Live if:**
- You need multimodal capabilities (images + text)
- Visual understanding is important
- You want the latest Google AI models
- Image analysis is a key requirement

**Choose Cerebras if:**
- Speed and low latency are critical
- You only need text processing
- High throughput is important
- You want OpenAI-compatible API

**Use Both if:**
- Different tasks have different requirements
- You want redundancy and fallback options
- You're building a comprehensive AI system
- Budget allows for multiple providers

Both integrations are production-ready and follow the same architectural patterns, making it easy to use them interchangeably or together in your application.

