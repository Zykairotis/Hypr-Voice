# Hypr-Voice Design Patterns and Best Practices

This document documents the design patterns, architectural decisions, and best practices used throughout the Hypr-Voice codebase.

## Table of Contents

1. [Architectural Patterns](#architectural-patterns)
2. [Design Patterns](#design-patterns)
3. [Best Practices](#best-practices)
4. [Code Organization](#code-organization)
5. [Performance Patterns](#performance-patterns)
6. [Testing Patterns](#testing-patterns)
7. [Error Handling Patterns](#error-handling-patterns)
8. [Configuration Patterns](#configuration-patterns)

---

## Architectural Patterns

### 1. Orchestrator-Subagent Pattern

**Purpose:** Maintain minimal context in orchestrator while delegating complex tasks to specialized subagents.

**Implementation:**

```python
class HyprVoiceOrchestrator:
    def __init__(self):
        self.agent_definitions = self._define_agents()
        self.registry = AgentRegistry()
        self.context_manager = ContextManager()

    async def process(self, query: str):
        # 1. Route to appropriate agent
        route = self.router.route(query)

        # 2. Spawn subagent with isolated context
        session = self.registry.create_session(
            agent_type=route.agent_type,
            query=query
        )

        # 3. Delegate to agent
        result = await self._execute_agent(session)

        # 4. Compress result for minimal context
        compressed = self.context_manager.compress_result(result)

        return compressed
```

**Benefits:**
- Reduced token usage in main context
- Parallel agent execution
- Clean separation of concerns
- Easier debugging and testing

**Trade-offs:**
- Increased complexity in coordination
- Additional latency for spawning

---

### 2. Router Pattern

**Purpose:** Intelligent query routing to specialized handlers.

**Keyword-Based Router:**

```python
class QueryRouter:
    def __init__(self):
        self.patterns = {
            AgentType.CODE: {
                "keywords": ["code", "function", "class", ...],
                "patterns": [r"write\s+(a\s+)?function", ...],
                "weight": 1.0
            },
            # ... other agents
        }

    def route(self, query: str) -> RouteDecision:
        scores = {}
        for agent_type, config in self.patterns.items():
            # Score by keywords and patterns
            score = self._score_agent(query, config)
            scores[agent_type] = score

        # Return highest-scoring agent
        best = max(scores, key=scores.get)
        return RouteDecision(agent_type=best, confidence=scores[best])
```

**LLM-Powered Router (Optional):**

```python
class CerebrasRouter:
    async def route_async(self, query: str) -> RouteDecision:
        prompt = f"""
        Classify this query: {query}

        Options:
        - code: Programming tasks
        - research: Information gathering
        - shell: System operations
        - voice: Speech tasks
        - general: Casual conversation
        """

        response = await self.llm.generate(prompt)
        return RouteDecision.from_response(response)
```

**When to Use:**
- Keyword router: Fast (<1ms), high precision
- LLM router: Complex queries, 2-8s latency

---

### 3. Context Isolation Pattern

**Purpose:** Each agent maintains its own context window to prevent pollution.

```python
class ContextManager:
    def __init__(self):
        self.windows: dict[str, ContextWindow] = {}

    def create_window(self, agent_id: str) -> ContextWindow:
        window = ContextWindow(
            agent_id=agent_id,
            max_tokens=100000,
            entries=[]
        )
        self.windows[agent_id] = window
        return window

    def compress_result(self, result: str) -> str:
        # Compress before returning to orchestrator
        return self._apply_compression(result, max_tokens=500)
```

**Benefits:**
- No context bleeding between agents
- Predictable memory usage
- Easier context debugging

---

### 4. Event-Driven Architecture

**Purpose:** Loose coupling through event emission and handling.

```python
class HyprVoiceOrchestrator:
    def __init__(self):
        self._event_handlers: list[callable] = []

    def register_event_handler(self, handler: callable):
        self._event_handlers.append(handler)

    async def _emit_event(self, event_type: str, data: dict):
        event = OrchestratorEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            data=data
        )
        for handler in self._event_handlers:
            await handler(event)
```

**Usage:**
```python
# Register handler
async def log_events(event):
    logger.info(f"{event.event_type}: {event.data}")

orchestrator.register_event_handler(log_events)

# Events emitted automatically
# - query_received
# - route_decision
# - agent_spawned
# - query_completed
```

---

## Design Patterns

### 1. Factory Pattern

**Purpose:** Create agent instances dynamically.

```python
def create_agent(
    name: str,
    description: str,
    prompt: str,
    tools: list[str] = None,
    model: str = "sonnet"
) -> AgentDefinition:
    return AgentDefinition(
        name=name,
        description=description,
        prompt=prompt,
        tools=tools or [],
        model=AgentModel(model)
    )

# Usage
custom_agent = create_agent(
    name="documentation-writer",
    description="Write technical documentation",
    prompt="You are a technical writer...",
    tools=["Read", "Write", "Grep"]
)
```

---

### 2. Strategy Pattern

**Purpose:** Interchangeable algorithms for TTS providers.

```python
class TTSProvider(str, Enum):
    KOKORO = "kokoro"
    DEEPGRAM = "deepgram"
    ELEVENLABS = "elevenlabs"

class UniversalTTS:
    def __init__(self, config: TTSConfig):
        self.provider = config.provider
        self._strategy = self._create_strategy()

    def _create_strategy):
        if self.provider == TTSProvider.KOKORO:
            return KokoroStrategy()
        elif self.provider == TTSProvider.DEEPGRAM:
            return DeepgramStrategy()
        elif self.provider == TTSProvider.ELEVENLABS:
            return ElevenLabsStrategy()

    async def speak(self, text: str):
        return await self._strategy.synthesize(text)
```

---

### 3. Decorator Pattern

**Purpose:** Tool registration and metadata.

```python
def tool(
    name: str,
    description: str,
    input_schema: dict,
    category: str = "general"
):
    def decorator(func):
        func._tool_name = name
        func._tool_description = description
        func._tool_schema = input_schema
        func._tool_category = category
        return func
    return decorator

# Usage
@tool(
    name="synthesize_speech",
    description="Convert text to speech",
    input_schema={"text": str, "voice": str},
    category="voice"
)
async def synthesize_speech(args: dict) -> dict:
    # Implementation
    pass
```

---

### 4. Observer Pattern

**Purpose:** Hook system for event interception.

```python
class HookManager:
    def __init__(self):
        self._hooks: dict[HookEvent, list[Hook]] = {}

    def register(self, event: HookEvent, callback: callable):
        hook = Hook(
            name=f"hook_{uuid.uuid4()}",
            events=[event],
            handler=callback
        )
        self._hooks[event].append(hook)

    async def execute(self, event: HookEvent, input_data: dict):
        for hook in self._hooks.get(event, []):
            result = await hook.execute(input_data)
            if not result.allow:
                return result  # Stop chain
        return HookResult.allow_action()
```

---

### 5. Chain of Responsibility

**Purpose:** Sequential hook execution with modification.

```python
async def execute_hooks(self, event: HookEvent, input_data: dict):
    current_input = input_data

    for hook in self._hooks[event]:
        result = await hook.execute(current_input)

        # Stop if denied
        if not result.allow:
            return result

        # Pass modified input to next
        if result.modified_input:
            current_input = result.modified_input

    return HookResult(allow=True)
```

---

### 6. Adapter Pattern

**Purpose:** MCP tool conversion to Claude SDK format.

```python
@dataclass
class MCPToolDefinition:
    name: str
    description: str
    input_schema: dict
    server_name: str

    def to_claude_format(self) -> dict:
        """Convert to Claude SDK tool format"""
        return {
            "name": f"{self.server_name}_{self.name}",
            "description": f"[MCP:{self.server_name}] {self.description}",
            "input_schema": self.input_schema
        }
```

---

### 7. Builder Pattern

**Purpose:** Complex configuration construction.

```python
class TTSConfigBuilder:
    def __init__(self):
        self._provider = TTSProvider.KOKORO
        self._voice = "af_bella"
        self._speed = 1.0
        self._streaming = True

    def provider(self, provider: TTSProvider):
        self._provider = provider
        return self

    def voice(self, voice: str):
        self._voice = voice
        return self

    def speed(self, speed: float):
        self._speed = speed
        return self

    def build(self) -> TTSConfig:
        return TTSConfig(
            provider=self._provider,
            voice=self._voice,
            speed=self._speed,
            use_streaming=self._streaming
        )

# Usage
config = (TTSConfigBuilder()
    .provider(TTSProvider.DEEPGRAM)
    .voice("asteria")
    .speed(1.2)
    .build())
```

---

## Best Practices

### 1. Async/Await Throughout

**DO:**
```python
async def process_query(self, query: str) -> AsyncIterator[dict]:
    route = await self.router.route_async(query)
    async for chunk in self._execute_agent(route):
        yield chunk
```

**DON'T:**
```python
def process_query(self, query: str):
    route = self.router.route(query)  # Blocking!
    for chunk in self._execute_agent(route):  # Blocking!
        yield chunk
```

---

### 2. Type Hints Everywhere

**DO:**
```python
from typing import Optional, AsyncIterator

async def process(
    self,
    query: str,
    session_id: Optional[str] = None
) -> AsyncIterator[dict]:
    ...
```

**DON'T:**
```python
async def process(self, query, session_id=None):
    ...
```

---

### 3. Dataclasses for Data Structures

**DO:**
```python
@dataclass
class RouteDecision:
    agent_type: str
    confidence: float
    reasoning: str
    keywords_matched: list[str]
    should_parallelize: bool = False
```

**DON'T:**
```python
def make_route_decision(agent_type, confidence, reasoning, keywords):
    return {
        "agent_type": agent_type,
        "confidence": confidence,
        ...
    }
```

---

### 4. Context Managers for Resources

**DO:**
```python
class HelperAgent:
    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

# Usage
async with HelperAgent() as agent:
    result = await agent.summarize_text(text)
```

**DON'T:**
```python
agent = HelperAgent()
await agent.initialize()
try:
    result = await agent.summarize_text(text)
finally:
    await agent.cleanup()
```

---

### 5. Dependency Injection

**DO:**
```python
class HyprVoiceOrchestrator:
    def __init__(
        self,
        router: QueryRouter,
        context_manager: ContextManager,
        registry: AgentRegistry
    ):
        self.router = router
        self.context_manager = context_manager
        self.registry = registry
```

**DON'T:**
```python
class HyprVoiceOrchestrator:
    def __init__(self):
        self.router = QueryRouter()  # Hard to test
        self.context_manager = ContextManager()
        self.registry = AgentRegistry()
```

---

### 6. Configuration Over Code

**DO:**
```python
# config.yaml
agents:
  code-worker:
    model: sonnet
    tools: [Read, Write, Edit]
    prompt: "You are a code specialist..."

# Load in code
with open("config.yaml") as f:
    config = yaml.safe_load(f)
```

**DON'T:**
```python
# Hardcoded
self.agents = {
    "code-worker": {
        "model": "sonnet",
        "tools": ["Read", "Write", "Edit"],
        "prompt": "You are a code specialist..."
    }
}
```

---

### 7. Fail Fast with Clear Errors

**DO:**
```python
if not api_key:
    raise ValueError(
        "ANTHROPIC_API_KEY environment variable is required. "
        "Set it with: export ANTHROPIC_API_KEY=sk-..."
    )
```

**DON'T:**
```python
if not api_key:
    raise ValueError("Missing API key")
```

---

### 8. Logging with Context

**DO:**
```python
from loguru import logger

logger.info(
    "Processing query",
    session_id=session_id[:8],
    query_length=len(query),
    agent_type=route.agent_type
)
```

**DON'T:**
```python
print(f"Processing query for session {session_id}")
```

---

## Code Organization

### Package Structure

```
src/hypr_voice/
├── orchestrator/          # Core orchestration
│   ├── __init__.py
│   ├── orchestrator.py    # Main orchestrator
│   ├── router.py          # Query routing
│   ├── context_manager.py # Context management
│   └── registry.py        # Agent registry
├── agents/                # Agent definitions
│   └── definitions.py
├── services/              # Shared services
│   ├── voice/             # TTS/STT
│   ├── mcp/               # MCP integration
│   └── hooks/             # Event hooks
├── middleware/            # Request/response handling
│   ├── hooks.py
│   └── router.py
├── ipc/                   # Inter-process communication
│   ├── websocket.py
│   └── hyprland.py
├── tools/                 # Tool registry
│   └── builtin/
└── whisper/               # Speech recognition
    ├── core/
    ├── processors/
    └── hooks/
```

### Module Guidelines

1. **Keep modules under 500 lines**
2. **One class per file** (large classes)
3. **Related functions together**
4. **Clear imports at top**

---

## Performance Patterns

### 1. Streaming for Latency

**DO:**
```python
async def process_streaming(self, query: str):
    async for token in self.llm.stream(query):
        yield {"type": "token", "content": token}
        # TTS can start immediately
```

**DON'T:**
```python
async def process_blocking(self, query: str):
    full_response = await self.llm.generate(query)
    yield {"type": "text", "content": full_response}
```

---

### 2. Caching Expensive Operations

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_agent_definition(agent_type: str) -> AgentDefinition:
    # Expensive parsing/calculation
    return parse_agent_config(agent_type)
```

---

### 3. Connection Pooling

```python
class HTTPClient:
    def __init__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            connector=aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10
            )
        )

    async def close(self):
        await self.session.close()
```

---

### 4. Batch Processing

```python
async def batch_transcribe(self, files: list[str]) -> list[dict]:
    # Process in parallel
    tasks = [self.transcribe_file(f) for f in files]
    return await asyncio.gather(*tasks)
```

---

## Testing Patterns

### 1. Dependency Injection for Mocking

```python
# Test setup
def test_orchestrator():
    mock_router = Mock(spec=QueryRouter)
    mock_router.route.return_value = RouteDecision(
        agent_type="code-worker",
        confidence=0.9
    )

    orchestrator = HyprVoiceOrchestrator(
        router=mock_router
    )

    # Test
    result = await orchestrator.process("Write code")
    assert result["agent"] == "code-worker"
```

---

### 2. Async Test Fixtures

```python
import pytest

@pytest.fixture
async def orchestrator():
    orch = HyprVoiceOrchestrator()
    yield orch
    await orch.shutdown()

@pytest.mark.asyncio
async def test_process(orchestrator):
    result = await orchestrator.process("Hello")
    assert result is not None
```

---

### 3. Property-Based Testing

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, max_size=1000))
async def test_query_length(query):
    orchestrator = HyprVoiceOrchestrator()
    result = await orchestrator.process(query)

    # Should handle any length
    assert result is not None
```

---

## Error Handling Patterns

### 1. Explicit Error Types

```python
class OrchestratorError(Exception):
    """Base error for orchestrator"""
    pass

class AgentNotFoundError(OrchestratorError):
    """Agent type not found"""
    pass

class ContextFullError(OrchestratorError):
    """Context window exceeded"""
    pass
```

---

### 2. Graceful Degradation

```python
async def route_with_fallback(self, query: str):
    try:
        return await self.cerebras_router.route_async(query)
    except Exception as e:
        logger.warning(f"Cerebras routing failed: {e}")
        return self.keyword_router.route(query)  # Fallback
```

---

### 3. Retry with Exponential Backoff

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def call_llm(self, prompt: str):
    return await self.client.generate(prompt)
```

---

## Configuration Patterns

### 1. Environment Variable Expansion

```python
import re
import os

def expand_env_vars(config: dict) -> dict:
    """Expand ${VAR} patterns in config"""
    pattern = re.compile(r'\$\{([^}]+)\}')

    def replacer(match):
        var_name = match.group(1)
        return os.environ.get(var_name, match.group(0))

    return {
        k: pattern.sub(replacer, str(v)) if isinstance(v, str) else v
        for k, v in config.items()
    }
```

---

### 2. Configuration Validation

```python
from pydantic import BaseModel, validator

class OrchestratorConfig(BaseModel):
    model: str
    max_turns: int
    enable_subagents: bool

    @validator("max_turns")
    def validate_turns(cls, v):
        if v < 1 or v > 10:
            raise ValueError("max_turns must be 1-10")
        return v
```

---

### 3. Default Configuration

```python
DEFAULT_CONFIG = {
    "model": "claude-sonnet-4-5",
    "max_turns": 1,
    "enable_subagents": False,
    "allowed_tools": ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
}

def get_config(user_config: dict = None) -> dict:
    return {**DEFAULT_CONFIG, **(user_config or {})}
```

---

## Security Patterns

### 1. Hook-Based Validation

```python
async def dangerous_command_hook(input_data, tool_use_id, context):
    if input_data.get("tool_name") != "Bash":
        return HookResult.allow_action()

    command = input_data["tool_input"].get("command", "")
    dangerous = ["rm -rf /", "mkfs.", "dd if=/dev/zero"]

    for pattern in dangerous:
        if pattern in command:
            return HookResult.deny_action(f"Dangerous: {pattern}")

    return HookResult.allow_action()
```

---

### 2. Secret Redaction

```python
import re

def redact_secrets(text: str) -> str:
    """Redact potential secrets from logs"""
    patterns = [
        (r'(sk-ant-[a-zA-Z0-9_-]{20,})', 'sk-ant-***'),
        (r'(Bearer [a-zA-Z0-9_-]{20,})', 'Bearer ***'),
        (r'("api_key":\s*")[^"]+(")', r'\1***\2'),
    ]

    for pattern, replacement in patterns:
        text = re.sub(pattern, replacement, text)

    return text
```

---

### 3. Path Traversal Prevention

```python
def safe_join(base_path: str, user_path: str) -> str:
    """Safely join paths, preventing traversal"""
    base = os.path.abspath(base_path)
    target = os.path.abspath(os.path.join(base, user_path))

    if not target.startswith(base):
        raise ValueError("Path traversal detected")

    return target
```

---

## Documentation Patterns

### 1. Docstring Standards

```python
async def process(
    self,
    query: str,
    session_id: Optional[str] = None
) -> AsyncIterator[dict]:
    """
    Process a query through the orchestrator.

    Args:
        query: The user query to process
        session_id: Optional session ID for conversation continuity

    Yields:
        Response chunks as dictionaries with keys:
        - type: "route_decision", "text", "tool_use", "result"
        - content: The actual content
        - agent: The agent type

    Example:
        >>> async for chunk in orchestrator.process("Hello"):
        ...     print(chunk["content"])

    Raises:
        ValueError: If query is empty
        OrchestratorError: If processing fails
    """
```

---

### 2. Type Aliases for Clarity

```python
from typing import AsyncIterator, Dict, Any

# Clear type alias
OrchestratorStream = AsyncIterator[Dict[str, Any]]

async def process(self, query: str) -> OrchestratorStream:
    ...
```

---

### 3. Architecture Decision Records

```markdown
# ADR-001: Use Claude Agent SDK

## Status
Accepted

## Context
Need multi-agent orchestration with context isolation.

## Decision
Use Claude Agent SDK for agent management.

## Consequences
- **Positive:** Native SDK support, session persistence
- **Negative:** Additional dependency, learning curve
```

---

## Summary

This architecture emphasizes:

1. **Separation of Concerns** - Clear module boundaries
2. **Async-First** - Non-blocking operations throughout
3. **Type Safety** - Comprehensive type hints
4. **Extensibility** - Hooks, plugins, MCP integration
5. **Performance** - Streaming, caching, connection pooling
6. **Security** - Validation, hooks, audit trails
7. **Testability** - Dependency injection, clear interfaces

These patterns enable a maintainable, scalable voice agent system that can evolve with changing requirements.
