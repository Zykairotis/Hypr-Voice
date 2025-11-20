# Helper Agent Service

A sophisticated helper agent service for Hypr-Voice that provides intelligent assistance capabilities using SGLang backend with Qwen 3 1.7B model.

## 🎯 Overview

The Helper Agent service is a comprehensive solution that bridges voice systems with AI-powered text processing, offering:

- **Topic Summarization** - Intelligent content summarization for voice agents
- **Content Analysis** - Advanced analysis with voice optimization recommendations
- **Task Planning** - Intelligent task breakdown and workflow creation
- **Claude Code SDK Integration** - Seamless bridge to Claude Code SDK

## 🚀 Features

### Core Capabilities

1. **Intelligent Summarization**
   - Voice-optimized summaries
   - Configurable length and focus areas
   - Multiple text summarization
   - Key information extraction

2. **Content Analysis**
   - Readability assessment
   - Voice optimization recommendations
   - Sentiment analysis
   - Content improvement suggestions

3. **Task Planning**
   - Task breakdown into actionable steps
   - Workflow creation with stages
   - Task prioritization
   - Progress tracking

4. **Claude Code SDK Bridge**
   - Context-aware assistance
   - Voice-to-Claude translation
   - Tool recommendation
   - Content formatting

## 📁 Architecture

```
helper-agent/
├── __init__.py              # Package initialization
├── sglang_client.py         # SGLang engine client
├── helper_agent.py          # Main helper agent class
├── config_loader.py         # Configuration management
├── tools/                   # Tool modules
│   ├── summarization.py     # Summarization tools
│   ├── analysis.py          # Content analysis tools
│   ├── planning.py          # Task planning tools
│   └── claude_bridge.py     # Claude SDK integration
├── config/                  # Configuration files
│   ├── helper_agent.yaml    # Main configuration
│   └── prompts.yaml         # Prompt templates
├── docs/                    # Documentation
│   ├── README.md            # This file
│   ├── API.md               # API reference
│   ├── INTEGRATION.md       # Integration guide
│   └── EXAMPLES.md          # Usage examples
└── tests/                   # Test files
    ├── test_client.py       # Client tests
    └── test_integration.py  # Integration tests
```

## ⚙️ Configuration

### Basic Configuration

The service uses YAML-based configuration located in `config/helper_agent.yaml`:

```yaml
# Service Settings
enabled: true

# SGLang Configuration
sglang:
  host: "localhost"
  port: 30000
  model: "qwen3-1.7b"
  timeout: 30

# Capability Settings
capabilities:
  summarization:
    enabled: true
    max_length: 500
    temperature: 0.3
  analysis:
    enabled: true
    optimize_for_voice: true
    temperature: 0.5
  planning:
    enabled: true
    max_tasks: 10
    temperature: 0.7
  claude_sdk_bridge:
    enabled: true
    context_aware: true
    timeout: 30
```

### Environment Variables

Override configuration with environment variables:

```bash
export HELPER_AGENT_SGLANG_HOST=localhost
export HELPER_AGENT_SGLANG_PORT=30000
export HELPER_AGENT_SGLANG_MODEL=qwen3-1.7b
```

## 🔧 Usage

### Basic Usage

```python
from helper_agent import HelperAgent

async def main():
    # Create and initialize helper agent
    async with HelperAgent() as agent:
        # Summarize text
        summary_result = await agent.summarize_text(
            text="Your long text here...",
            max_length=200,
            focus="key_points"
        )

        print("Summary:", summary_result["summary"])

        # Analyze content
        analysis_result = await agent.analyze_content(
            content="Your content here...",
            optimize_for_voice=True
        )

        print("Voice optimizations:", analysis_result["voice_optimization"])

        # Plan task
        plan_result = await agent.plan_task(
            task="Implement a new feature",
            max_steps=8,
            complexity="medium"
        )

        print("Steps:", plan_result["steps"])
```

### Using Individual Tools

```python
from helper_agent.tools.summarization import SummarizationTools
from helper_agent.sglang_client import SGLangClient

async def use_summarization():
    # Create SGLang client
    client = SGLangClient()
    await client.initialize()

    # Create summarization tool
    summarizer = SummarizationTools(client, prompts)

    # Summarize text
    result = await summarizer.summarize_text(
        text="Text to summarize...",
        max_length=300
    )

    print(result["summary"])
```

## 📡 API Reference

### HelperAgent Class

#### Main Methods

- `summarize_text(text, max_length, focus)` - Summarize text
- `analyze_content(content, optimize_for_voice)` - Analyze content
- `plan_task(task, max_steps, context)` - Plan task breakdown
- `bridge_to_claude_sdk(request, context, voice_optimized)` - Claude SDK bridge

#### Utility Methods

- `health_check()` - Check service health
- `get_stats()` - Get usage statistics
- `reload_configuration()` - Reload configuration

### SGLangClient Class

#### Core Methods

- `generate_text(prompt, max_tokens, temperature)` - Generate text
- `chat_completion(messages, max_tokens, temperature)` - Chat completion
- `health_check()` - Check SGLang service health

## 🔗 Integration

### With Hypr-Voice System

The helper agent integrates seamlessly with the Hypr-Voice system:

```python
# In your Hypr-Voice agent
from helper_agent import HelperAgent

class VoiceAgent:
    def __init__(self):
        self.helper_agent = HelperAgent()

    async def process_voice_input(self, text):
        # Analyze and optimize for voice
        analysis = await self.helper_agent.analyze_content(
            content=text,
            optimize_for_voice=True
        )

        # Get voice optimization suggestions
        suggestions = analysis["voice_optimization"]["suggestions"]

        return suggestions
```

### With Claude Code SDK

```python
# Bridge to Claude Code SDK
claude_response = await agent.bridge_to_claude_sdk(
    request="Help me implement a new feature",
    context={
        "application": "VSCode",
        "task": "coding",
        "language": "python"
    },
    voice_optimized=True
)

# Use the response for voice output
voice_response = claude_response["response"]
claude_instructions = claude_response["claude_instructions"]
```

## 📊 Monitoring

### Health Check

```python
health = await agent.health_check()
print(f"Agent healthy: {health['agent_healthy']}")
print(f"SGLang healthy: {health['sglang_healthy']}")
```

### Statistics

```python
stats = await agent.get_stats()
print(f"Requests processed: {stats['requests_processed']}")
print(f"Average tokens per request: {stats['average_tokens_per_request']}")
print(f"Error rate: {stats['error_rate']}%")
```

## 🛠️ Development

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_client.py

# Run with coverage
python -m pytest tests/ --cov=helper_agent
```

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd helper-agent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python -m helper_agent --debug
```

### Configuration for Development

```yaml
# config/helper_agent.yaml
development:
  debug_mode: true
  mock_sglang: false
  test_mode: true
  verbose_logging: true
```

## 🐛 Troubleshooting

### Common Issues

1. **SGLang Service Not Available**
   ```bash
   # Check if SGLang is running on port 30000
   curl http://localhost:30000/health

   # Start SGLang service
   # (Follow your SGLang setup instructions)
   ```

2. **Configuration Not Loading**
   ```bash
   # Check configuration file path
   ls -la config/helper_agent.yaml

   # Validate YAML syntax
   python -c "import yaml; yaml.safe_load(open('config/helper_agent.yaml'))"
   ```

3. **Memory Usage High**
   ```yaml
   # Reduce concurrent requests
   performance:
     max_concurrent_requests: 2
   ```

### Debug Mode

Enable debug mode for detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or in configuration
development:
  debug_mode: true
  verbose_logging: true
```

## 📚 Advanced Topics

### Custom Prompts

Create custom prompts in `config/prompts.yaml`:

```yaml
custom_prompts:
  my_summarizer:
    system: "You are an expert in technical documentation."
    template: "Summarize this technical content: {text}"
```

### Extending Tools

Create custom tools by extending base classes:

```python
from helper_agent.tools.summarization import SummarizationTools

class CustomSummarizer(SummarizationTools):
    async def custom_summary_method(self, text):
        # Custom implementation
        return await self.summarize_text(
            text=text,
            max_length=100,
            focus="custom"
        )
```

### Performance Optimization

```yaml
performance:
  # Enable caching
  cache_enabled: true
  cache_ttl: 3600

  # Rate limiting
  rate_limiting:
    enabled: true
    requests_per_minute: 30

  # Concurrent requests
  max_concurrent_requests: 5
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **SGLang Team** - For the efficient serving framework
- **Qwen Team** - For the Qwen 3 language model
- **Hypr-Voice Team** - For the voice agent framework
- **Claude Code SDK** - For the development platform integration

---

## 📞 Support

For support and questions:

- Check the [documentation](docs/)
- Review [examples](docs/EXAMPLES.md)
- Open an issue on GitHub
- Check the [troubleshooting guide](docs/TROUBLESHOOTING.md)