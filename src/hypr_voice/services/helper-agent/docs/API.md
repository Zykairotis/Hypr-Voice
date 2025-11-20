# Helper Agent API Reference

This document provides a comprehensive API reference for the Helper Agent service.

## Table of Contents

- [HelperAgent Class](#helperagent-class)
- [SGLangClient Class](#sglangclient-class)
- [Tool Classes](#tool-classes)
- [Configuration](#configuration)
- [Error Handling](#error-handling)

## HelperAgent Class

The main class that provides all helper agent capabilities.

### Constructor

```python
HelperAgent(config: Optional[Dict[str, Any]] = None)
```

**Parameters:**
- `config` (Optional[Dict]): Configuration dictionary to override defaults

**Example:**
```python
from helper_agent import HelperAgent

# With default configuration
agent = HelperAgent()

# With custom configuration
custom_config = {
    "sglang": {"host": "localhost", "port": 30000},
    "capabilities": {"summarization": {"enabled": True}}
}
agent = HelperAgent(custom_config)
```

### Methods

#### `initialize()`

Initialize the helper agent and connect to SGLang service.

```python
async def initialize() -> None
```

**Example:**
```python
await agent.initialize()
```

#### `cleanup()`

Cleanup resources and close connections.

```python
async def cleanup() -> None
```

**Example:**
```python
await agent.cleanup()
```

#### `health_check()`

Perform comprehensive health check.

```python
async def health_check() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Health status information

**Response Structure:**
```json
{
  "agent_healthy": true,
  "sglang_healthy": true,
  "capabilities": {
    "summarization": {"enabled": true, "healthy": true},
    "analysis": {"enabled": true, "healthy": true},
    "planning": {"enabled": true, "healthy": true},
    "claude_sdk_bridge": {"enabled": true, "healthy": true}
  },
  "stats": {...},
  "timestamp": "2024-01-01T12:00:00"
}
```

#### `summarize_text()`

Summarize text for voice agent consumption.

```python
async def summarize_text(
    text: str,
    max_length: Optional[int] = None,
    focus: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `text` (str): Text to summarize
- `max_length` (Optional[int]): Maximum summary length in characters
- `focus` (Optional[str]): Focus area ("technical", "actionable", "key_points", "decisions")

**Returns:**
- `Dict[str, Any]`: Summary and metadata

**Response Structure:**
```json
{
  "summary": "The summarized text...",
  "key_points": ["Point 1", "Point 2"],
  "original_length": 1500,
  "summary_length": 250,
  "compression_ratio": 0.167,
  "focus": "key_points",
  "tokens_used": 150
}
```

**Example:**
```python
result = await agent.summarize_text(
    text="Long article text here...",
    max_length=300,
    focus="technical"
)
print(result["summary"])
```

#### `analyze_content()`

Analyze content for voice agent optimization.

```python
async def analyze_content(
    content: str,
    optimize_for_voice: Optional[bool] = None
) -> Dict[str, Any]
```

**Parameters:**
- `content` (str): Content to analyze
- `optimize_for_voice` (Optional[bool]): Whether to provide voice optimization

**Returns:**
- `Dict[str, Any]`: Analysis results and recommendations

**Response Structure:**
```json
{
  "analysis": {
    "overall_assessment": "Content is well-structured",
    "strengths": ["Clear structure", "Good flow"],
    "weaknesses": ["Long sentences", "Complex vocabulary"],
    "recommendations": ["Shorten sentences", "Simplify language"]
  },
  "metrics": {
    "word_count": 500,
    "sentence_count": 25,
    "avg_sentence_length": 20.0,
    "vocabulary_diversity": 0.65
  },
  "voice_optimization": {
    "status": "needs_improvement",
    "issues_identified": ["long_sentences", "complex_language"],
    "suggestions": ["Break down long sentences", "Use simpler words"]
  }
}
```

#### `plan_task()`

Break down a task into actionable steps.

```python
async def plan_task(
    task: str,
    max_steps: Optional[int] = None,
    context: Optional[str] = None
) -> Dict[str, Any]
```

**Parameters:**
- `task` (str): Task to break down
- `max_steps` (Optional[int]): Maximum number of steps
- `context` (Optional[str]): Additional context for planning

**Returns:**
- `Dict[str, Any]`: Task plan and steps

**Response Structure:**
```json
{
  "steps": [
    {
      "step_number": 1,
      "description": "Research requirements",
      "priority": "high",
      "estimated_time": "30 minutes",
      "dependencies": [],
      "time_minutes": 30
    }
  ],
  "total_steps": 5,
  "total_estimated_time": 120,
  "total_estimated_time_formatted": "2 hours",
  "quality_score": 85.0,
  "original_task": "Implement new feature",
  "complexity": "medium"
}
```

#### `bridge_to_claude_sdk()`

Bridge request to Claude Code SDK with context awareness.

```python
async def bridge_to_claude_sdk(
    request: str,
    context: Optional[Dict[str, Any]] = None,
    voice_optimized: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- `request` (str): Request to process
- `context` (Optional[Dict]): Additional context
- `voice_optimized` (bool): Whether to optimize for voice

**Returns:**
- `Dict[str, Any]`: Processed response and actions

**Response Structure:**
```json
{
  "response": "Here's how to implement the feature...",
  "actions": ["Create new file", "Write tests"],
  "claude_instructions": ["Use the 'write-file' tool", "Run 'npm test'"],
  "voice_output": "To implement this feature, you'll need to create a new file and write tests",
  "tools_required": ["file_operations", "development_tools"],
  "context_id": "abc123"
}
```

#### `get_stats()`

Get helper agent usage statistics.

```python
async def get_stats() -> Dict[str, Any]
```

**Returns:**
- `Dict[str, Any]`: Usage statistics

**Response Structure:**
```json
{
  "requests_processed": 150,
  "total_tokens_generated": 25000,
  "errors": 2,
  "uptime_seconds": 3600,
  "uptime_formatted": "1 hour",
  "average_tokens_per_request": 166.7,
  "error_rate": 1.33
}
```

## SGLangClient Class

Client for communicating with SGLang service.

### Constructor

```python
SGLangClient(config: SGLangConfig)
```

**Parameters:**
- `config` (SGLangConfig): SGLang configuration

### Methods

#### `initialize()`

Initialize HTTP session.

```python
async def initialize() -> None
```

#### `cleanup()`

Cleanup HTTP session.

```python
async def cleanup() -> None
```

#### `health_check()`

Check SGLang service health.

```python
async def health_check() -> bool
```

**Returns:**
- `bool`: True if healthy, False otherwise

#### `generate_text()`

Generate text using SGLang service.

```python
async def generate_text(
    prompt: str,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9,
    stop_sequences: Optional[List[str]] = None
) -> Optional[str]
```

**Parameters:**
- `prompt` (str): Input prompt
- `max_tokens` (int): Maximum tokens to generate
- `temperature` (float): Sampling temperature
- `top_p` (float): Top-p sampling parameter
- `stop_sequences` (Optional[List[str]]): Stop sequences

**Returns:**
- `Optional[str]`: Generated text or None if failed

#### `chat_completion()`

Generate chat completion.

```python
async def chat_completion(
    messages: List[Dict[str, str]],
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> Optional[str]
```

**Parameters:**
- `messages` (List[Dict]): Message list with 'role' and 'content'
- `max_tokens` (int): Maximum tokens to generate
- `temperature` (float): Sampling temperature
- `top_p` (float): Top-p sampling parameter

**Returns:**
- `Optional[str]`: Generated response or None if failed

## Tool Classes

### SummarizationTools

#### `summarize_text()`

```python
async def summarize_text(
    text: str,
    max_length: int = 500,
    focus: Optional[str] = None,
    style: str = "voice_optimized"
) -> Dict[str, Any]
```

#### `summarize_multiple_texts()`

```python
async def summarize_multiple_texts(
    texts: List[str],
    max_length_per_summary: int = 200,
    overall_max_length: int = 800
) -> Dict[str, Any]
```

#### `extract_key_information()`

```python
async def extract_key_information(
    text: str,
    information_types: List[str] = None
) -> Dict[str, Any]
```

### AnalysisTools

#### `analyze_content()`

```python
async def analyze_content(
    content: str,
    optimize_for_voice: bool = True,
    analysis_type: str = "comprehensive"
) -> Dict[str, Any]
```

#### `check_readability()`

```python
async def check_readability(
    content: str,
    target_audience: str = "general"
) -> Dict[str, Any]
```

#### `analyze_sentiment()`

```python
async def analyze_sentiment(
    content: str,
    context: Optional[str] = None
) -> Dict[str, Any]
```

#### `suggest_voice_improvements()`

```python
async def suggest_voice_improvements(
    content: str,
    voice_style: str = "conversational"
) -> Dict[str, Any]
```

### PlanningTools

#### `plan_task()`

```python
async def plan_task(
    task: str,
    max_steps: int = 10,
    context: Optional[str] = None,
    complexity: str = "medium"
) -> Dict[str, Any]
```

#### `create_workflow()`

```python
async def create_workflow(
    goal: str,
    stages: Optional[List[str]] = None,
    resources: Optional[List[str]] = None
) -> Dict[str, Any]
```

#### `prioritize_tasks()`

```python
async def prioritize_tasks(
    tasks: List[str],
    criteria: Optional[List[str]] = None,
    constraints: Optional[str] = None
) -> Dict[str, Any]
```

#### `suggest_next_steps()`

```python
async def suggest_next_steps(
    current_state: str,
    goal: str,
    completed_steps: Optional[List[str]] = None
) -> Dict[str, Any]
```

#### `create_checklist()`

```python
async def create_checklist(
    process: str,
    detail_level: str = "medium"
) -> Dict[str, Any]
```

### ClaudeSDKBridge

#### `process_request()`

```python
async def process_request(
    request: str,
    context: Optional[Dict[str, Any]] = None,
    voice_optimized: bool = True,
    available_tools: Optional[List[str]] = None
) -> Dict[str, Any]
```

#### `suggest_claude_actions()`

```python
async def suggest_claude_actions(
    situation: str,
    goal: str,
    constraints: Optional[List[str]] = None
) -> Dict[str, Any]
```

#### `format_for_claude_sdk()`

```python
async def format_for_claude_sdk(
    content: str,
    purpose: str = "general",
    target_format: str = "json"
) -> Dict[str, Any]
```

#### `translate_voice_to_claude()`

```python
async def translate_voice_to_claude(
    voice_input: str,
    intent: str = "general",
    context_window: Optional[str] = None
) -> Dict[str, Any]
```

#### `get_context_recommendations()`

```python
async def get_context_recommendations(
    current_task: str,
    context_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]
```

## Configuration

### HelperAgentConfig

```python
@dataclass
class HelperAgentConfig:
    enabled: bool = True
    sglang: SGLangConfig = None
    capabilities: Dict[str, Any] = None
```

### SGLangConfig

```python
@dataclass
class SGLangConfig:
    host: str = "localhost"
    port: int = 30000
    model: str = "qwen3-1.7b"
    timeout: int = 30
    health_check_interval: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
```

## Error Handling

### Common Error Responses

All API methods return a dictionary with an "error" key when an error occurs:

```json
{
  "error": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "details": {...}
}
```

### Error Types

1. **Connection Errors**
   - SGLang service unavailable
   - Network connectivity issues
   - Timeout errors

2. **Validation Errors**
   - Invalid input parameters
   - Missing required fields
   - Invalid format

3. **Processing Errors**
   - Model inference failures
   - Content too large
   - Rate limiting

4. **Configuration Errors**
   - Invalid configuration
   - Missing required settings

### Error Handling Example

```python
try:
    result = await agent.summarize_text(text="...")
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Summary: {result['summary']}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Response Formats

### Standard Response Structure

Most responses follow this structure:

```json
{
  "data": {...},  // Main response data
  "metadata": {
    "tokens_used": 150,
    "processing_time": 2.5,
    "model": "qwen3-1.7b",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### Error Response Structure

```json
{
  "error": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "details": {
    "original_request": "...",
    "suggestion": "Try reducing text length",
    "retry_after": 30
  }
}
```

## Rate Limiting

When rate limiting is enabled, responses include rate limit headers:

```json
{
  "data": {...},
  "rate_limit": {
    "remaining": 25,
    "reset_time": "2024-01-01T12:01:00Z",
    "limit": 30
  }
}
```

## Async Context Manager

The HelperAgent class supports async context managers:

```python
async with HelperAgent() as agent:
    result = await agent.summarize_text(text="...")
    # Automatically cleaned up
```

This ensures proper initialization and cleanup of resources.