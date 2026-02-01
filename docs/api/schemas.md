# Hypr-Voice API Schemas

## Overview

This document describes all request and response schemas used in the Hypr-Voice API. Schemas are defined using Pydantic models and provide type safety, validation, and automatic API documentation.

---

## Table of Contents

- [Request Schemas](#request-schemas)
- [Response Schemas](#response-schemas)
- [Agent Configuration](#agent-configuration)
- [Conversation Models](#conversation-models)
- [Voice Models](#voice-models)
- [Error Models](#error-models)

---

## Request Schemas

### QueryRequest

Used for processing queries through the orchestrator.

```python
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
```

**Fields:**
- `query` (string, required): The query text to process
- `session_id` (string, optional): Session ID for conversation context

**Example:**
```json
{
  "query": "What is the capital of France?",
  "session_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

### SpawnRequest

Used to spawn new agent instances.

```python
class SpawnRequest(BaseModel):
    agent_type: str
    task: str
    parent_session: Optional[str] = None
```

**Fields:**
- `agent_type` (string, required): Type of agent to spawn
  - Supported: `code-worker`, `research-worker`, `shell-worker`, `voice-worker`, `general-conversation`
- `task` (string, required): Initial task or instruction
- `parent_session` (string, optional): Parent session ID for hierarchical agents

**Example:**
```json
{
  "agent_type": "code-worker",
  "task": "Create a Python function to calculate fibonacci numbers",
  "parent_session": null
}
```

---

### VoiceProcessRequest

Used for voice processing pipeline.

```python
class VoiceProcessRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    speak_response: bool = True
```

**Fields:**
- `text` (string, required): Input text to process
- `conversation_id` (string, optional): Conversation ID for context
- `speak_response` (boolean, optional): Whether to generate TTS audio (default: true)

**Example:**
```json
{
  "text": "Tell me about artificial intelligence",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "speak_response": true
}
```

---

### EnhancedProcessRequest

Used for enhanced context-aware processing.

```python
class EnhancedProcessRequest(BaseModel):
    text: str
    context: Dict[str, Any]
    conversation_id: Optional[str] = None
    speak_response: bool = True
```

**Fields:**
- `text` (string, required): User query or instruction
- `context` (object, required): Enhanced context information
  - `window` (object): Active window details
    - `class` (string): Window class (e.g., "kitty", "firefox")
    - `title` (string): Window title
    - `workspace` (object): Workspace information
  - `clipboard` (string): Clipboard content
  - `timestamp` (string): ISO 8601 timestamp
- `conversation_id` (string, optional): Conversation ID for continuity
- `speak_response` (boolean, optional): Enable TTS (default: true)

**Example:**
```json
{
  "text": "Help me with this code",
  "context": {
    "window": {
      "class": "nvim",
      "title": "main.py - Neovim",
      "workspace": {
        "id": 1,
        "name": "dev"
      }
    },
    "clipboard": "def hello():\n    print('world')",
    "timestamp": "2026-01-26T12:00:00Z"
  },
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "speak_response": true
}
```

---

### StreamingTTSRequest

Used for real-time streaming TTS processing.

```python
class StreamingTTSRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    auto_play: bool = False
```

**Fields:**
- `text` (string, required): Input text to process
- `conversation_id` (string, optional): Conversation ID for context
- `auto_play` (boolean, optional): Server-side audio playback (default: false)

**Example:**
```json
{
  "text": "This is a test of streaming TTS",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "auto_play": false
}
```

---

### TTSSpeakRequest

Used for text-to-speech conversion.

```python
class TTSSpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = None
```

**Fields:**
- `text` (string, required): Text to synthesize
- `voice` (string, optional): Voice name (uses default if not specified)
  - Deepgram: `aura-luna-en`, `aura-asteria-en`, `aura-stella-en`
  - Kokoro: `af_bella`, `am_michael`, `bf_emma`

**Example:**
```json
{
  "text": "Hello, world!",
  "voice": "aura-luna-en"
}
```

---

## Response Schemas

### HealthResponse

Health check response.

```python
class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
```

**Fields:**
- `status` (string): Service status ("healthy", "degraded", "unhealthy")
- `timestamp` (string): ISO 8601 timestamp
- `version` (string): API version

**Example:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-26T12:00:00.000000",
  "version": "0.2.0"
}
```

---

### AgentListResponse

Response for listing agents.

```python
class AgentListResponse(BaseModel):
    agents: List[AgentInfo]
```

**AgentInfo fields:**
- `agent_id` (string): Unique agent identifier
- `name` (string): Agent display name
- `status` (string): Agent status ("idle", "running", "completed", "error")
- `working_directory` (string): Agent working directory path
- `parent_id` (string, optional): Parent agent ID
- `subagents` (array): List of subagent names

**Example:**
```json
{
  "agents": [
    {
      "agent_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "code-worker-1",
      "status": "running",
      "working_directory": "/home/user/hypr-voice/workspace",
      "parent_id": null,
      "subagents": ["helper-1", "tester-1"]
    }
  ]
}
```

---

### VoiceProcessResponse

Response from voice processing.

```python
class VoiceProcessResponse(BaseModel):
    success: bool
    response_text: Optional[str]
    routing_decision: Optional[RoutingDecision]
    audio_file: Optional[str]
    conversation_id: Optional[str]
    metrics: Optional[Metrics]
```

**Fields:**
- `success` (boolean): Whether processing succeeded
- `response_text` (string, optional): Generated response text
- `routing_decision` (object, optional): Agent routing decision
  - `agent_type` (string): Selected agent type
  - `confidence` (number): Routing confidence (0-1)
  - `reasoning` (string): Explanation for routing
- `audio_file` (string, optional): Path to generated audio file
- `conversation_id` (string): Conversation ID
- `metrics` (object, optional): Performance metrics
  - `total_time` (number): Total processing time (seconds)
  - `llm_time` (number): LLM processing time (seconds)
  - `tts_time` (number): TTS generation time (seconds)

**Example:**
```json
{
  "success": true,
  "response_text": "Paris is the capital of France.",
  "routing_decision": {
    "agent_type": "general-conversation",
    "confidence": 0.95,
    "reasoning": "Query is a general knowledge question"
  },
  "audio_file": "/tmp/response_20260126_120000.wav",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "metrics": {
    "total_time": 2.5,
    "llm_time": 1.8,
    "tts_time": 0.7
  }
}
```

---

### TranscriptionResponse

Response from audio transcription.

```python
class TranscriptionResponse(BaseModel):
    success: bool
    text: Optional[str]
    detected_language: Optional[str]
    error: Optional[str]
```

**Fields:**
- `success` (boolean): Whether transcription succeeded
- `text` (string, optional): Transcribed text
- `detected_language` (string, optional): Detected language code (ISO 639-1)
- `error` (string, optional): Error message if failed

**Example:**
```json
{
  "success": true,
  "text": "Hello, how are you today?",
  "detected_language": "en",
  "error": null
}
```

---

### EnhancedProcessResponse

Response from enhanced context processing.

```python
class EnhancedProcessResponse(BaseModel):
    success: bool
    response_text: str
    conversation_id: str
    audio_file: Optional[str]
    context_used: bool
    agent_type: str
    tools_used: List[str]
    timestamp: str
```

**Fields:**
- `success` (boolean): Whether processing succeeded
- `response_text` (string): Generated response
- `conversation_id` (string): Conversation ID for follow-ups
- `audio_file` (string, optional): Path to TTS audio file
- `context_used` (boolean): Whether context was utilized
- `agent_type` (string): Type of agent that processed the request
- `tools_used` (array): List of tools used during processing
- `timestamp` (string): ISO 8601 timestamp

**Example:**
```json
{
  "success": true,
  "response_text": "I can see you're working on a Python file. How can I help?",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_file": "/tmp/response_20260126_120000.wav",
  "context_used": true,
  "agent_type": "enhanced-context",
  "tools_used": ["hyprland_monitor", "file_reader"],
  "timestamp": "2026-01-26T12:00:00Z"
}
```

---

## Agent Configuration

### AgentConfig

Configuration for creating agents.

```python
class AgentConfig(BaseModel):
    name: str
    working_directory: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 8096
    temperature: float = 1.0
    permission_mode: str = "default"
    system_prompt: Optional[str] = None
    setting_sources: List[str] = ["project"]
    allowed_tools: List[str]
    skills: List[str] = []
    mcp_servers: List[str] = []
    enable_voice: bool = False
    enable_tts_agent: bool = False
    tts_provider: str = "kokoro"
    enable_monitoring: bool = True
    capture_clipboard: bool = False
    permission_timeout: int = 30
```

**Fields:**
- `name` (string, required): Agent display name
- `working_directory` (string, required): Working directory path
- `model` (string): Claude model to use (default: claude-3-5-sonnet-20241022)
- `max_tokens` (integer): Maximum tokens in response (default: 8096)
- `temperature` (number): Response randomness 0-1 (default: 1.0)
- `permission_mode` (string): Permission handling mode
- `system_prompt` (string, optional): Custom system prompt
- `setting_sources` (array): Configuration sources
- `allowed_tools` (array): Permitted tool names
- `skills` (array): Active skill names
- `mcp_servers` (array): MCP server connections
- `enable_voice` (boolean): Enable voice synthesis
- `enable_tts_agent` (boolean): Enable TTS agent
- `tts_provider` (string): TTS provider ("kokoro", "deepgram", "elevenlabs")
- `enable_monitoring` (boolean): Enable Hyprland window monitoring
- `capture_clipboard` (boolean): Capture clipboard for context
- `permission_timeout` (integer): Permission request timeout (seconds)

**Example:**
```json
{
  "name": "code-assistant",
  "working_directory": "/home/user/projects",
  "model": "claude-3-5-sonnet-20241022",
  "max_tokens": 4096,
  "temperature": 0.7,
  "permission_mode": "auto",
  "system_prompt": "You are a helpful coding assistant.",
  "allowed_tools": ["Read", "Write", "Edit", "Bash", "Grep"],
  "skills": ["file_operations", "bash_execution"],
  "enable_monitoring": true,
  "capture_clipboard": false
}
```

---

## Conversation Models

### Conversation

Represents a conversation with messages.

```python
class Conversation(BaseModel):
    conversation_id: str
    created_at: str
    messages: List[Message]
```

**Message fields:**
- `role` (string): "user" or "assistant"
- `content` (string): Message content
- `timestamp` (string): ISO 8601 timestamp

**Example:**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-01-26T12:00:00Z",
  "messages": [
    {
      "role": "user",
      "content": "What is Python?",
      "timestamp": "2026-01-26T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "Python is a high-level programming language...",
      "timestamp": "2026-01-26T12:00:01Z"
    }
  ]
}
```

---

## Voice Models

### RouteDecision

Agent routing decision.

```python
class RouteDecision(BaseModel):
    agent_type: str
    confidence: float
    reasoning: str
    keywords_matched: List[str]
    should_parallelize: bool = False
    secondary_agents: List[str] = []
```

**Fields:**
- `agent_type` (string): Selected agent type
- `confidence` (number): Confidence score 0-1
- `reasoning` (string): Explanation for decision
- `keywords_matched` (array): Matched keywords
- `should_parallelize` (boolean): Whether to use parallel agents
- `secondary_agents` (array): Additional agent types to use

**Example:**
```json
{
  "agent_type": "code-worker",
  "confidence": 0.92,
  "reasoning": "Query involves code-related tasks: 'function', 'Python'",
  "keywords_matched": ["function", "python", "code"],
  "should_parallelize": false,
  "secondary_agents": []
}
```

---

## Error Models

### HTTPException

Standard error response.

```python
class HTTPException(BaseModel):
    detail: str
```

**Fields:**
- `detail` (string): Error description

**Example:**
```json
{
  "detail": "Agent not found"
}
```

---

### ErrorResponse

Detailed error response.

```python
class ErrorResponse(BaseModel):
    error: str
    type: Optional[str]
    details: Optional[Dict[str, Any]]
```

**Fields:**
- `error` (string): Error message
- `type` (string, optional): Error type/category
- `details` (object, optional): Additional error details

**Example:**
```json
{
  "error": "Failed to process request",
  "type": "ValidationError",
  "details": {
    "field": "query",
    "issue": "This field is required"
  }
}
```

---

## Validation Rules

### String Fields
- Minimum length: 1 character (unless nullable)
- Maximum length: Varies by field (typically 1000-10000 characters)
- Whitespace: Trimmed automatically unless otherwise specified

### Numeric Fields
- Integers: Must be whole numbers
- Floats: Must be decimal numbers
- Ranges: Specified per field (e.g., 0-1 for probabilities)

### Boolean Fields
- Accepts: `true`, `false`
- JSON compatible

### Array Fields
- Must be valid JSON array
- Item validation applies to each element

### Object Fields
- Must be valid JSON object
- Nested validation applies

---

## Type Conversion

The API automatically handles type conversion:

### Request Conversion
- Strings to integers/floats where appropriate
- Booleans from various truthy/falsy values
- ISO 8601 strings to datetime objects
- Base64 strings to binary data

### Response Conversion
- Datetime objects to ISO 8601 strings
- Enums to string values
- Path objects to strings
- Binary data to base64 or file responses

---

## Common Patterns

### Optional Fields

Fields marked as `Optional` can be omitted from requests:

```json
{
  "text": "Required field",
  "optional_field": null  // Can be omitted or null
}
```

### Default Values

Fields with default values can be omitted:

```json
{
  "text": "Hello"
  // speak_response uses default value of true
}
```

### Array Defaults

Empty arrays when field is omitted:

```json
{
  "name": "agent"
  // skills defaults to []
}
```

---

## Schema Evolution

The API schemas follow semantic versioning:

- **Major version**: Breaking changes to schemas
- **Minor version**: New fields added (backward compatible)
- **Patch version**: Bug fixes, documentation

New required fields are only added in major versions. New optional fields may be added in minor versions.

---

## OpenAPI/Swagger

Complete schemas are available in OpenAPI format:

```
http://localhost:9091/docs
http://localhost:9091/openapi.json
```

These provide interactive documentation and schema validation.
