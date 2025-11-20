# Gemini Live Integration

A comprehensive integration for Google's Gemini Live API with multimodal support (text + images), streaming responses, and token tracking.

## Features

- ✨ **Multimodal Support**: Send text and images together
- 🚀 **Streaming Responses**: Real-time token-by-token streaming
- 📊 **Token Tracking**: Monitor usage and calculate tokens/sec
- 🎨 **Rich TUI**: Beautiful terminal interface with Rich
- 🔧 **Configurable**: Extensive parameters for fine-tuning
- 📦 **Easy Integration**: Simple API similar to Cerebras integration

## Installation

```bash
# Install from requirements file
pip install -r requirements.txt

# Or install manually
pip install google-genai Pillow rich python-dotenv
```

## Configuration

Set your API key as an environment variable:

```bash
export GEMINI_API_KEY="your-api-key-here"
# or
export GOOGLE_API_KEY="your-api-key-here"
```

### Optional Configuration

```bash
# Model selection (default: gemini-2.0-flash-exp)
export GEMINI_MODEL="gemini-2.5-flash"

# For Vertex AI (optional)
export GEMINI_VERTEX_AI="true"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GEMINI_LOCATION="us-central1"
```

## Quick Start

### 1. Using the TUI

Launch the interactive terminal interface:

```bash
python -m hypr_voice.services.gemini_live.gemini_tui
```

Or run directly:

```bash
cd src/hypr_voice/services/gemini_live
python gemini_tui.py
```

#### TUI Commands

- `/help` - Show all commands
- `/image` - Add image(s) to the current message
- `/clear-img` - Clear loaded images
- `/model` - Select a different model
- `/stream` - Toggle streaming on/off
- `/temp` - Set temperature (0.0-2.0)
- `/tokens` - Set max output tokens
- `/system` - Set system instruction
- `/reset` - Clear conversation history
- `/stats` - Show detailed token statistics
- `/quit` - Exit the application

### 2. Using the Client API

```python
import asyncio
from pathlib import Path
from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig

async def main():
    # Initialize client
    config = GeminiConfig.from_env()
    client = GeminiClient(config)
    
    # Text-only query
    response = await client.generate_content(
        "Explain quantum computing in simple terms",
        temperature=0.7,
        max_output_tokens=500
    )
    print(response["content"])
    print(f"Tokens used: {response['usage']['total_tokens']}")
    
    # Multimodal query (text + image)
    image_path = Path("screenshot.png")
    response = await client.generate_content(
        ["What's in this image?", image_path],
        temperature=0.5
    )
    print(response["content"])
    
    # Streaming response
    print("Streaming response:")
    async for chunk in client.stream_content(
        "Write a short story about AI",
        temperature=0.8,
        max_output_tokens=1000
    ):
        print(chunk["content"], end="", flush=True)
        if chunk["is_final"]:
            print(f"\n\nTokens: {chunk['usage']['total_tokens']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 3. Using the Integration Helpers

```python
import asyncio
from pathlib import Path
from hypr_voice.services.gemini_live import GeminiIntegration

async def main():
    async with GeminiIntegration() as gemini:
        # Analyze an image
        analysis = await gemini.analyze_image(
            Path("photo.jpg"),
            prompt="Describe this photo in detail"
        )
        print(analysis)
        
        # Multimodal query with multiple images
        response = await gemini.multimodal_query(
            "Compare these images and explain the differences",
            images=[Path("image1.jpg"), Path("image2.jpg")]
        )
        print(response)
        
        # Quick text generation
        summary = await gemini.summarize(
            "Very long text here...",
            style="bullet_points",
            max_words=100
        )
        print(summary)
        
        # Classification
        category = await gemini.classify(
            "This product is amazing!",
            categories=["positive", "negative", "neutral"]
        )
        print(f"Sentiment: {category}")
        
        # Extract keywords
        keywords = await gemini.extract_keywords(
            "Long article text here...",
            max_keywords=5
        )
        print(f"Keywords: {', '.join(keywords)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Using Chat Sessions

```python
import asyncio
from hypr_voice.services.gemini_live import GeminiIntegration

async def main():
    async with GeminiIntegration() as gemini:
        # Create a chat session with system instruction
        session = gemini.session(
            system_instruction="You are a helpful coding assistant specialized in Python."
        )
        
        # Multi-turn conversation
        response1 = await session.send("How do I read a CSV file in Python?")
        print(f"Assistant: {response1}")
        
        response2 = await session.send("Can you show me an example with pandas?")
        print(f"Assistant: {response2}")
        
        # Stream responses
        print("Streaming response:")
        async for chunk in session.stream("Explain decorators in Python"):
            print(chunk, end="", flush=True)
        print()
        
        # View conversation history
        print(f"\nConversation has {len(session.messages)} messages")
        
        # Reset if needed
        session.reset()

if __name__ == "__main__":
    asyncio.run(main())
```

## API Reference

### GeminiClient

Core client for interacting with the Gemini API.

#### Methods

- `generate_content(content, *, model, temperature, max_output_tokens, top_p, top_k, system_instruction, **kwargs)` - Generate content with support for text and images
- `stream_content(content, *, model, temperature, max_output_tokens, top_p, top_k, system_instruction, **kwargs)` - Stream content generation
- `chat(messages, *, ...)` - Chat completion with conversation history
- `stream_chat(messages, *, ...)` - Stream chat responses

#### Properties

- `last_usage` - Get usage metadata from the last request

### GeminiIntegration

High-level integration helpers.

#### Methods

- `analyze_image(image, prompt, *, temperature, max_output_tokens, **kwargs)` - Analyze an image
- `stream_image_analysis(image, prompt, *, ...)` - Stream image analysis
- `multimodal_query(text, images, *, ...)` - Query with text and multiple images
- `stream_multimodal_query(text, images, *, ...)` - Stream multimodal query
- `quick_prompt(prompt, *, max_output_tokens, temperature, **kwargs)` - Quick text completion
- `summarize(text, *, max_words, style, temperature, **kwargs)` - Summarize text
- `classify(text, *, categories, temperature, **kwargs)` - Classify text
- `extract_keywords(text, *, max_keywords, temperature, **kwargs)` - Extract keywords
- `session(*, system_instruction, history)` - Create a chat session

### GeminiChatSession

Conversational state management.

#### Methods

- `send(message, **kwargs)` - Send a message and get response
- `stream(message, **kwargs)` - Send a message and stream response
- `reset()` - Reset conversation history

#### Properties

- `messages` - Get conversation history
- `system_instruction` - Get/set system instruction

## Available Models

- `gemini-2.0-flash-exp` (default) - Fast, efficient, multimodal
- `gemini-2.0-flash-thinking-exp-01-21` - Advanced reasoning
- `gemini-2.5-flash` - Latest flash model
- `gemini-2.5-pro` - Most capable model
- `gemini-1.5-flash` - Previous generation fast
- `gemini-1.5-pro` - Previous generation capable

## Parameters

### Generation Parameters

- `temperature` (0.0-2.0) - Controls randomness (default: 0.7)
  - Lower values (0.1-0.5): More focused and deterministic
  - Medium values (0.6-0.9): Balanced creativity
  - Higher values (1.0-2.0): More creative and diverse

- `max_output_tokens` - Maximum tokens to generate
  - Varies by model (typically 2048-8192)

- `top_p` (0.0-1.0) - Nucleus sampling parameter
  - Controls diversity by considering top probability mass

- `top_k` - Top-k sampling parameter
  - Limits token selection to top k most likely tokens

- `system_instruction` - System-level instruction for behavior
  - Sets overall behavior and persona of the model

## Content Types

The client supports multiple content types:

### Text
```python
await client.generate_content("Your text prompt here")
```

### Image from bytes
```python
with open("image.jpg", "rb") as f:
    image_bytes = f.read()
await client.generate_content(["Describe this:", image_bytes])
```

### PIL Image
```python
from PIL import Image
img = Image.open("photo.png")
await client.generate_content(["What's in this photo?", img])
```

### Path to image file
```python
from pathlib import Path
await client.generate_content(["Analyze:", Path("screenshot.png")])
```

### Multiple items
```python
await client.generate_content([
    Path("image1.jpg"),
    Path("image2.jpg"),
    "Compare these images"
])
```

## Token Tracking

The client automatically tracks token usage:

```python
response = await client.generate_content("Hello!")
usage = response["usage"]
print(f"Prompt tokens: {usage['prompt_tokens']}")
print(f"Completion tokens: {usage['completion_tokens']}")
print(f"Total tokens: {usage['total_tokens']}")

# Access last usage
print(client.last_usage)
```

## Error Handling

```python
try:
    response = await client.generate_content("Your prompt")
except ValueError as e:
    print(f"Configuration error: {e}")
except RuntimeError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Performance Tips

1. **Use streaming for long responses**: Reduces perceived latency
2. **Adjust temperature**: Lower for factual, higher for creative
3. **Limit max_output_tokens**: Faster responses and lower costs
4. **Batch image processing**: Process multiple images when possible
5. **Reuse client instances**: Avoid repeated initialization

## Comparison with Cerebras Integration

Both integrations follow similar patterns:

| Feature | Gemini Live | Cerebras |
|---------|-------------|----------|
| Streaming | ✅ | ✅ |
| Multimodal | ✅ Images | ❌ Text only |
| Token tracking | ✅ | ✅ |
| Multiple models | ✅ | ✅ |
| Chat sessions | ✅ | ✅ |
| TUI | ✅ | ✅ |
| API compatibility | Gemini-specific | OpenAI-compatible |

## Troubleshooting

### API Key Issues
```bash
# Make sure your API key is set
echo $GEMINI_API_KEY

# Or check if GOOGLE_API_KEY is set
echo $GOOGLE_API_KEY
```

### Import Errors
```bash
# Install missing dependencies
pip install google-genai Pillow rich
```

### Image Format Issues
Supported formats: JPEG, PNG, GIF, WebP, BMP

### Rate Limits
The Gemini API has rate limits. If you hit them:
- Add delays between requests
- Use exponential backoff
- Consider upgrading your API plan

## Contributing

This integration is part of Hypr-Voice. For contributions:
1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Ensure backward compatibility

## License

Part of the Hypr-Voice project. See main project LICENSE.

## Links

- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Google Gen AI Python SDK](https://github.com/googleapis/python-genai)
- [Hypr-Voice Project](https://github.com/yourusername/Hypr-Voice)

## Support

For issues related to:
- **Gemini API**: Check [Google AI Studio](https://makersuite.google.com/)
- **This Integration**: Open an issue in Hypr-Voice repository
- **Hypr-Voice**: See main project documentation

