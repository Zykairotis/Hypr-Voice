# Gemini Live Integration - Quick Start Guide

Get up and running with Gemini Live in 5 minutes!

## 1. Install Dependencies

```bash
cd src/hypr_voice/services/gemini_live
pip install -r requirements.txt
```

Or install manually:
```bash
pip install google-genai Pillow rich python-dotenv
```

## 2. Set Up API Key

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```bash
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

## 3. Launch the TUI

```bash
python gemini_tui.py
```

You should see:
```
╭─────────────────────────────────────────────────────────╮
│           🔮 Gemini Live TUI                            │
│      Multimodal AI with Text & Images                   │
╰─────────────────────────────────────────────────────────╯
```

## 4. Try Your First Commands

### Send a text message:
```
You> What is the meaning of life?
```

### Add an image:
```
You> /image
Image path(s)> /path/to/your/image.jpg
You> Describe this image
```

### Change the model:
```
You> /model
Select model number> 1
```

### Adjust creativity:
```
You> /temp
Temperature (0.0-2.0)> 0.9
```

### View statistics:
```
You> /stats
```

## 5. Quick Code Examples

### Example 1: Simple Text Generation

```python
import asyncio
from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig

async def main():
    client = GeminiClient(GeminiConfig.from_env())
    
    response = await client.generate_content(
        "Write a haiku about coding",
        temperature=0.8
    )
    
    print(response["content"])
    print(f"Tokens: {response['usage']['total_tokens']}")

asyncio.run(main())
```

### Example 2: Image Analysis

```python
import asyncio
from pathlib import Path
from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig

async def main():
    client = GeminiClient(GeminiConfig.from_env())
    
    response = await client.generate_content(
        ["What's in this image?", Path("photo.jpg")],
        temperature=0.5
    )
    
    print(response["content"])

asyncio.run(main())
```

### Example 3: Streaming Response

```python
import asyncio
from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig

async def main():
    client = GeminiClient(GeminiConfig.from_env())
    
    async for chunk in client.stream_content(
        "Tell me a story about AI",
        temperature=0.7
    ):
        print(chunk["content"], end="", flush=True)

asyncio.run(main())
```

### Example 4: Using Integration Helpers

```python
import asyncio
from hypr_voice.services.gemini_live import GeminiIntegration

async def main():
    async with GeminiIntegration() as gemini:
        # Quick prompt
        result = await gemini.quick_prompt(
            "What is 2+2?",
            temperature=0.1
        )
        print(result)
        
        # Summarize
        summary = await gemini.summarize(
            "Very long text here...",
            style="concise",
            max_words=50
        )
        print(summary)
        
        # Classify
        sentiment = await gemini.classify(
            "This is amazing!",
            categories=["positive", "negative", "neutral"]
        )
        print(sentiment)

asyncio.run(main())
```

### Example 5: Chat Session

```python
import asyncio
from hypr_voice.services.gemini_live import GeminiIntegration

async def main():
    async with GeminiIntegration() as gemini:
        session = gemini.session(
            system_instruction="You are a helpful coding assistant"
        )
        
        # Multi-turn conversation
        response1 = await session.send("How do I read a file in Python?")
        print(f"Bot: {response1}")
        
        response2 = await session.send("What about CSV files?")
        print(f"Bot: {response2}")
        
        # Conversation maintains context automatically
        print(f"Total messages: {len(session.messages)}")

asyncio.run(main())
```

## 6. Common Use Cases

### Use Case 1: Document Analysis

```python
async def analyze_document(image_path: str, questions: list[str]):
    async with GeminiIntegration() as gemini:
        for question in questions:
            answer = await gemini.analyze_image(
                Path(image_path),
                prompt=question,
                temperature=0.3
            )
            print(f"Q: {question}")
            print(f"A: {answer}\n")

# Usage
asyncio.run(analyze_document(
    "document.png",
    [
        "What is the main topic?",
        "Extract key dates and numbers",
        "Summarize in 2 sentences"
    ]
))
```

### Use Case 2: Screenshot Understanding

```python
async def understand_screenshot(screenshot_path: str):
    async with GeminiIntegration() as gemini:
        analysis = await gemini.analyze_image(
            Path(screenshot_path),
            prompt="""Analyze this screenshot and provide:
            1. What application is shown
            2. What the user is doing
            3. Any errors or issues visible
            4. Suggestions for improvement""",
            temperature=0.5
        )
        return analysis

# Usage
result = asyncio.run(understand_screenshot("screen.png"))
print(result)
```

### Use Case 3: Batch Image Processing

```python
async def batch_process_images(image_paths: list[Path]):
    async with GeminiIntegration() as gemini:
        results = []
        for img_path in image_paths:
            description = await gemini.analyze_image(
                img_path,
                prompt="Provide a concise description",
                temperature=0.5
            )
            results.append({
                "file": img_path.name,
                "description": description
            })
        return results

# Usage
images = [Path(f"image{i}.jpg") for i in range(1, 6)]
results = asyncio.run(batch_process_images(images))
for r in results:
    print(f"{r['file']}: {r['description']}")
```

### Use Case 4: Streaming with Progress

```python
import asyncio
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

async def stream_with_progress(prompt: str):
    from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig
    
    client = GeminiClient(GeminiConfig.from_env())
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("Generating...", total=None)
        
        start_time = time.time()
        chunks = []
        
        async for chunk in client.stream_content(prompt):
            content = chunk["content"]
            chunks.append(content)
            progress.stop()
            console.print(content, end="", markup=False)
        
        elapsed = time.time() - start_time
        total_text = "".join(chunks)
        console.print(f"\n\n[dim]Time: {elapsed:.2f}s | Length: {len(total_text)} chars[/dim]")

# Usage
asyncio.run(stream_with_progress("Write a poem about stars"))
```

## 7. TUI Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Enter` | Send message |
| `Ctrl+C` | Interrupt (doesn't quit) |
| `Ctrl+D` | Quit application |

## 8. Environment Variables Reference

```bash
# Required
GEMINI_API_KEY=your-key-here

# Optional
GEMINI_MODEL=gemini-2.0-flash-exp          # Default model
GEMINI_VERTEX_AI=false                      # Use Vertex AI
GOOGLE_CLOUD_PROJECT=your-project           # For Vertex AI
GEMINI_LOCATION=us-central1                 # For Vertex AI
```

## 9. Troubleshooting

### "API key not found"
```bash
# Check if set
echo $GEMINI_API_KEY

# Set temporarily
export GEMINI_API_KEY="your-key"

# Set permanently (add to ~/.bashrc or ~/.zshrc)
echo 'export GEMINI_API_KEY="your-key"' >> ~/.bashrc
source ~/.bashrc
```

### "Module not found"
```bash
# Install dependencies
pip install google-genai Pillow rich python-dotenv

# Or use requirements.txt
pip install -r requirements.txt
```

### "Image file not found"
- Use absolute paths: `/home/user/image.jpg`
- Or relative to current directory: `./image.jpg`
- Check file exists: `ls -la /path/to/image.jpg`

### "Rate limit exceeded"
- Wait a few seconds between requests
- Use lower temperature for caching
- Consider upgrading API plan

## 10. Next Steps

### Learn More
- Read the full [README.md](README.md)
- Check out [examples.py](examples.py)
- Compare with [Cerebras Integration](COMPARISON.md)

### Advanced Topics
- Using Vertex AI for enterprise
- Batch processing optimization
- Custom model configurations
- Error handling best practices

### Integration with Hypr-Voice
- Use in voice pipelines
- Combine with TTS/STT
- Build multimodal workflows
- Create custom agents

## 11. Quick Tips

1. **Lower temperature (0.1-0.3)** for factual answers
2. **Higher temperature (0.8-1.2)** for creative content
3. **Stream long responses** for better UX
4. **Reuse client instances** for performance
5. **Use system instructions** to set behavior
6. **Batch similar requests** when possible
7. **Track token usage** to manage costs
8. **Enable multimodal** when visual context helps

## 12. Common Patterns

### Pattern: Error-Resilient Request
```python
async def safe_request(prompt: str, max_retries: int = 3):
    from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig
    
    client = GeminiClient(GeminiConfig.from_env())
    
    for attempt in range(max_retries):
        try:
            response = await client.generate_content(prompt)
            return response["content"]
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
```

### Pattern: Streaming with Callbacks
```python
async def stream_with_callback(prompt: str, on_chunk, on_complete):
    from hypr_voice.services.gemini_live import GeminiClient, GeminiConfig
    
    client = GeminiClient(GeminiConfig.from_env())
    chunks = []
    
    async for chunk in client.stream_content(prompt):
        content = chunk["content"]
        chunks.append(content)
        await on_chunk(content)
    
    await on_complete("".join(chunks))

# Usage
async def on_chunk(text):
    print(text, end="", flush=True)

async def on_complete(full_text):
    print(f"\n\nGenerated {len(full_text)} characters")

asyncio.run(stream_with_callback("Tell me a story", on_chunk, on_complete))
```

### Pattern: Multimodal Context Manager
```python
class ImageContext:
    def __init__(self):
        self.images = []
    
    def add(self, path: str):
        self.images.append(Path(path))
        return self
    
    async def ask(self, question: str):
        from hypr_voice.services.gemini_live import GeminiIntegration
        
        async with GeminiIntegration() as gemini:
            return await gemini.multimodal_query(
                question,
                images=self.images
            )

# Usage
context = ImageContext()
context.add("photo1.jpg").add("photo2.jpg")
answer = asyncio.run(context.ask("Compare these photos"))
```

## Support

- 📚 [Full Documentation](README.md)
- 🔍 [Examples](examples.py)
- ⚖️ [Comparison with Cerebras](COMPARISON.md)
- 🐛 [Report Issues](https://github.com/yourusername/Hypr-Voice/issues)

Happy coding with Gemini Live! 🚀

