# Hypr-Voice System Architecture

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Architectural Patterns](#core-architectural-patterns)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Configuration System](#configuration-system)
7. [Security Considerations](#security-considerations)
8. [Performance Optimizations](#performance-optimizations)

---

## System Overview

Hypr-Voice is a multi-agent voice assistant system built on the **Claude Agent SDK** patterns. The system follows Anthropic's recommended architecture for building sophisticated AI agents with specialized subagents, isolated contexts, and efficient orchestration.

### Core Philosophy

The architecture embodies these key principles from Anthropic's design patterns:

1. **Minimal Context in Orchestrator** - The orchestrator maintains only routing decisions and final results
2. **Subagent Isolation** - Each specialized agent operates with its own isolated context
3. **Result Summarization** - Subagent outputs are compressed before returning to orchestrator
4. **Fast, Single-Turn Operations** - Optimized for voice interactions where latency matters

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   REST API   │  │  WebSocket   │  │   CLI Tools  │         │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘         │
└─────────┼──────────────────┼──────────────────┼─────────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    Orchestrator Layer                           │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │           HyprVoiceOrchestrator (Central Coordinator)     │ │
│  │  • Query routing (keyword/Cerebras)                      │ │
│  │  • Session management                                     │ │
│  │  • Event emission                                         │ │
│  │  • Agent lifecycle                                        │ │
│  └────────┬──────────────────────────────┬──────────────────┘ │
│           │                              │                     │
│  ┌────────▼──────────┐         ┌────────▼──────────┐         │
│  │   QueryRouter     │         │  AgentRegistry     │         │
│  │  • Keyword match  │         │  • Session tracking│         │
│  │  • Cerebras AI    │         │  • Lifecycle mgmt  │         │
│  └───────────────────┘         │  • Parent-child    │         │
│                                └────────────────────┘         │
└────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    Specialized Agents                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Code Worker │  │  Research    │  │   Shell      │         │
│  │  • Sonnet    │  │  Worker      │  │   Worker     │         │
│  │  • File ops  │  │  • Haiku     │  │  • Sonnet    │         │
│  └──────────────┘  │  • Docs      │  │  • Bash      │         │
│                    └──────────────┘  └──────────────┘         │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │   Voice      │  │   General    │                          │
│  │   Worker     │  │Conversation  │                          │
│  │  • Haiku     │  │  • Haiku     │                          │
│  │  • TTS       │  │  • Chat      │                          │
│  └──────────────┘  └──────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────┼────────────────────────────────────┐
│                    Services Layer                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  TTS Engine  │  │  STT Engine  │  │   Claude     │         │
│  │  • Deepgram  │  │  • Whisper   │  │   SDK        │         │
│  │  • Kokoro    │  │  • Hybrid    │  │  • Anthropic │         │
│  │  • ElevenLabs│  │              │  │   API        │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Architectural Patterns

### 1. Multi-Agent Orchestration

The system implements **Anthropic's Routing Pattern** for multi-agent systems:

**Design Rationale:**
- **Why:** Different tasks require different expertise. A single agent trying to do everything becomes inefficient and unfocused.
- **How:** QueryRouter analyzes incoming requests and routes to specialized agents
- **Benefit:** Each agent can be optimized for its specific task with appropriate tools, prompts, and models

**Implementation:**
```python
# From orchestrator/orchestrator.py
async def process(self, query: str, session_id: Optional[str] = None):
    # 1. Route to appropriate agent
    route = await self.router.route_async(query)

    # 2. Emit routing decision
    await self._emit_event("route_decision", {
        "route": route.agent_type,
        "confidence": route.confidence,
        "reasoning": route.reasoning,
    })

    # 3. Process with specialized agent
    async for chunk in self._process_with_sdk(query, route, session_id):
        yield chunk
```

### 2. Context Isolation

Each agent maintains its own isolated context window following Anthropic's **Context Isolation Pattern**:

**Design Rationale:**
- **Why:** Sharing context between agents leads to bloated context windows and slower responses
- **How:** ContextManager creates separate windows for each agent
- **Benefit:** Fast responses (critical for voice), reduced token usage, clearer agent responsibilities

**Architecture:**
```
Orchestrator Context (minimal)
├── Route decisions only
└── Final results

Agent Contexts (isolated)
├── Code Worker Context
│   ├── Read files
│   ├── Tool results
│   └── Generated code
├── Research Worker Context
│   ├── Search queries
│   ├── Documentation
│   └── Synthesized findings
└── Shell Worker Context
    ├── Commands executed
    ├── Output
    └── System state
```

### 3. Event-Driven Architecture

The system uses an **Event-Driven Pattern** for loose coupling and extensibility:

**Design Rationale:**
- **Why:** Components need to react to state changes without tight coupling
- **How:** Orchestrator emits events that handlers can listen to
- **Benefit:** Easy to add monitoring, logging, analytics without modifying core logic

**Event Types:**
```python
# From orchestrator/orchestrator.py
class OrchestratorEvent:
    event_type: str  # "query_received", "route_decision", "query_completed"
    timestamp: str
    data: dict
    agent_id: Optional[str]
```

**Usage:**
```python
# Register event handler
orchestrator.register_event_handler(my_handler)

# Handlers receive all events
async def my_handler(event: OrchestratorEvent):
    if event.event_type == "query_completed":
        # Log metrics, update dashboards, etc.
        pass
```

---

## Component Architecture

### Orchestrator (`orchestrator/orchestrator.py`)

**Responsibilities:**
- Query routing and decision making
- Session management
- Agent lifecycle (spawn, track, destroy)
- Event emission
- Claude SDK integration

**Key Classes:**
- `HyprVoiceOrchestrator` - Main orchestrator
- `OrchestratorConfig` - Configuration dataclass
- `OrchestratorEvent` - Event data structure

**Configuration:**
```python
@dataclass
class OrchestratorConfig:
    model: str = "claude-sonnet-4-5"
    max_turns: int = 1  # Fast: single turn only
    enable_subagents: bool = False  # Direct API is faster for voice
    enable_context_compression: bool = True
    working_directory: Optional[str] = None
    allowed_tools: list[str] = ["Read", "Write", "Edit", "Grep", "Glob", "Bash"]
```

**Design Decision: Single-Turn Processing**
The orchestrator defaults to `max_turns=1` because:
- Voice interactions require fast responses (<3 seconds)
- Multi-turn conversations are handled at session level
- Reduces latency for real-time voice feedback

### Query Router (`orchestrator/router.py`)

**Responsibilities:**
- Analyze queries and determine appropriate agent
- Support multiple routing strategies (keyword, Cerebras AI)
- Provide confidence scores and reasoning

**Routing Strategies:**

1. **Keyword Router (Default)**
   - Instant matching (<1ms)
   - Pattern-based scoring
   - No external API calls

2. **Cerebras Router (Optional)**
   - AI-powered classification (~200ms)
   - Better accuracy for ambiguous queries
   - API key rotation for rate limiting

**Agent Types:**
```python
class AgentType(str, Enum):
    CODE = "code-worker"           # Programming tasks
    RESEARCH = "research-worker"   # Information gathering
    SHELL = "shell-worker"         # System operations
    VOICE = "voice-worker"         # TTS/STT operations
    GENERAL = "general-conversation"  # Casual chat
    ORCHESTRATOR = "orchestrator"  # Direct handling
```

**Routing Algorithm:**
```python
# Keyword matching with confidence scoring
for agent_type, config in self.patterns.items():
    score = 0.0

    # Check keywords (+0.1 per match)
    for keyword in config["keywords"]:
        if keyword in query_lower:
            score += 0.1

    # Check patterns (+0.3 per match)
    for pattern in self._compiled_patterns[agent_type]:
        if pattern.search(query):
            score += 0.3

    # Apply weight
    score *= config["weight"]
    scores[agent_type] = min(score, 1.0)
```

### Context Manager (`orchestrator/context_manager.py`)

**Responsibilities:**
- Create and manage isolated context windows
- Compress results before handoff
- Track token usage
- Detect when compression is needed

**Context Strategies:**

1. **Subagent Isolation**
   - Each agent gets its own context window
   - No cross-contamination between agents

2. **Result Summarization**
   - Compress subagent output before returning to orchestrator
   - Extract key information, discard verbosity

3. **Automatic Compaction**
   - SDK handles long sessions via built-in compaction
   - Maintains conversation history efficiently

**Compression Algorithm:**
```python
def _apply_compression(self, text: str, max_tokens: int) -> str:
    # Strategy 1: Remove empty lines and excessive whitespace
    lines = [line.strip() for line in lines if line.strip()]

    # Strategy 2: Truncate very long lines
    lines = [line[:200] + "..." if len(line) > 200 else line]

    # Strategy 3: Keep first and last sections, summarize middle
    first_part = result[:max_chars * 0.4]
    last_part = result[-max_chars * 0.4:]
    middle_summary = f"\n[... {omitted} chars omitted ...]\n"

    return first_part + middle_summary + last_part
```

### Agent Registry (`orchestrator/registry.py`)

**Responsibilities:**
- Track all active agent sessions
- Manage agent lifecycle (create, run, pause, complete, destroy)
- Handle parent-child relationships for subagents
- Cleanup stale sessions

**Session States:**
```python
class AgentStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    DESTROYED = "destroyed"
```

**Key Features:**
- Thread-safe operations with RLock
- Session history for metrics
- Automatic cleanup when capacity reached
- Parent-child tracking for subagent hierarchies

### Logging System (`core/loggurl.py`)

**Responsibilities:**
- Centralized logging for all components
- Component-specific loggers with color coding
- Semantic logging methods for common events
- Single log file for easy debugging

**Usage:**
```python
from hypr_voice.core.loggurl import LogGurl

log = LogGurl("orchestrator")
log.info("Processing query")
log.routing("general-conversation", 0.85, "casual greeting")
log.llm_start("claude-sonnet-4-5", "agent=code-worker")
log.llm_complete(len(response), duration_ms)
```

**Log Format:**
```
[HH:MM:SS.mmm] [  ORCHESTRATOR] [ INFO] Processing query
[HH:MM:SS.mmm] [     ROUTER   ] [ INFO] ROUTE → general-conversation (conf=0.85)
[HH:MM:SS.mmm] [       LLM    ] [ INFO] LLM → claude-sonnet-4-5 | agent=code-worker...
[HH:MM:SS.mmm] [       LLM    ] [ INFO] LLM ← 1234 chars in 2345ms
```

---

## Data Flow

### Query Processing Flow

```
User Input
    │
    ▼
┌──────────────────┐
│  REST/WebSocket  │
└────────┬─────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   HyprVoiceOrchestrator                      │
│  ┌────────────────────────────────────────────────────────┐│
│  │  1. Receive query + optional session_id               ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  2. Route query                                       ││
│  │     ├─ Keyword router (instant)                       ││
│  │     └─ Cerebras router (AI-powered, ~200ms)          ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  3. Emit route_decision event                         ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  4. Process with specialized agent                    ││
│  │     ├─ Get agent system prompt                        ││
│  │     ├─ Configure Claude SDK options                   ││
│  │     ├─ Call LLM (direct API or SDK)                   ││
│  │     └─ Stream response chunks                         ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  5. Emit query_completed event                        ││
│  └────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    Response Stream
                    ├─ route_decision
                    ├─ text chunks
                    ├─ tool_use events
                    └─ result metadata
```

### Voice Processing Flow

```
Audio Input
    │
    ▼
┌──────────────────┐
│  Whisper STT     │  ← Hybrid client (local + server)
└────────┬─────────┘
         │
         ▼
      Text Query
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                   VoiceOrchestrator                          │
│  ┌────────────────────────────────────────────────────────┐│
│  │  1. Transcribe audio → text                            ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  2. Route and process query                            ││
│  │     (uses same routing as text orchestrator)           ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  3. Get response text                                  ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  4. Convert to speech (TTS)                           ││
│  │     ├─ Deepgram Aura (fast, high quality)             ││
│  │     ├─ Kokoro (local, offline)                        ││
│  │     └─ ElevenLabs (premium voices)                    ││
│  └────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                      Audio Output
```

### Streaming Flow (Real-Time TTS)

```
Query
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              process_streaming() method                      │
│  ┌────────────────────────────────────────────────────────┐│
│  │  1. Route query (synchronous, fast)                   ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  2. Create session with route info                     ││
│  └────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────┐│
│  │  3. Stream from LLM with token-level granularity      ││
│  │     for token in stream.text_stream:                  ││
│  │         yield {"type": "token", "content": token}     ││
│  └────────────────────────────────────────────────────────┘│
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                  Token Stream (real-time)
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    TTS Engine                                │
│  • Convert tokens to audio as they arrive                  │
│  • Begin playback immediately                              │
│  • Overlap generation with playback                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    Audio Output (streaming)
```

---

## Design Patterns

### 1. Strategy Pattern

**Used in:** Query routing, TTS providers, STT engines

**Implementation:**
```python
# Multiple routing strategies
class QueryRouter:
    def route(self, query: str) -> RouteDecision:
        # Keyword-based strategy

class CerebrasRouter:
    def route(self, query: str) -> RouteDecision:
        # AI-powered strategy

# Interchangeable at runtime
orchestrator = HyprVoiceOrchestrator(
    use_cerebras_router=os.getenv("USE_CEREBRAS_ROUTER", "false") == "true"
)
```

### 2. Registry Pattern

**Used in:** AgentRegistry, TTS providers, STT engines

**Implementation:**
```python
class AgentRegistry:
    def __init__(self):
        self._sessions: dict[str, AgentSession] = {}

    def create_session(self, agent_type, query, ...) -> AgentSession:
        # Create and track session

    def get_session(self, session_id) -> Optional[AgentSession]:
        # Retrieve session

    def destroy_session(self, session_id) -> bool:
        # Remove and cleanup
```

### 3. Observer Pattern

**Used in:** Event hooks, orchestration events

**Implementation:**
```python
# Register observers
orchestrator.register_event_handler(my_handler)

# Emit events (subject)
await self._emit_event("query_completed", {"query": query})

# Handlers receive notification
async def my_handler(event: OrchestratorEvent):
    if event.event_type == "query_completed":
        # Handle event
```

### 4. Builder Pattern

**Used in:** Agent configuration, orchestrator setup

**Implementation:**
```python
@dataclass
class OrchestratorConfig:
    model: str = "claude-sonnet-4-5"
    max_turns: int = 1
    enable_subagents: bool = False
    # ... many configurable options

config = OrchestratorConfig(
    model="claude-opus-4-5",
    max_turns=5,
    enable_subagents=True,
)
orchestrator = HyprVoiceOrchestrator(config)
```

### 5. Adapter Pattern

**Used in:** Claude SDK compatibility layer

**Implementation:**
```python
# services/sdk_compat.py
# Adapts between official Claude SDK and mock implementation

try:
    from claude_agent_sdk import ClaudeSDKClient
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    from hypr_voice.services.claude_agent_sdk_mock import ClaudeSDKClient
    CLAUDE_SDK_AVAILABLE = True
    CLAUDE_SDK_MOCK = True
```

---

## Configuration System

### Environment-Based Configuration

The system uses environment variables for configuration, following 12-factor app principles:

**Key Configuration Files:**
- `/home/mewtwo/Zykairotis/Hypr-Voice/docs/ENVIRONMENT_VARIABLES.md` - Comprehensive reference

**Configuration Categories:**

1. **Anthropic API**
   - `ANTHROPIC_AUTH_TOKEN` - API key
   - `ANTHROPIC_BASE_URL` - Custom base URL
   - `ANTHROPIC_DEFAULT_SONNET_MODEL` - Model selection

2. **Router Configuration**
   - `USE_CEREBRAS_ROUTER` - Enable AI routing
   - `CEREBRAS_API_KEY_ONE/TWO/THREE` - API keys for rotation
   - `CEREBRAS_ROUTER_TIMEOUT` - Max wait time (default 3s)

3. **Orchestrator Settings**
   - `HYPR_VOICE_MODEL` - LLM model
   - `HYPR_VOICE_MAX_TURNS` - Conversation depth
   - `HYPR_VOICE_ENABLE_SUBAGENTS` - Use Claude SDK

4. **TTS Configuration**
   - `HYPR_VOICE_TTS_PROVIDER` - deepgram/kokoro/elevenlabs
   - `HYPR_VOICE_TTS_VOICE` - Voice selection
   - `DEEPGRAM_API_KEY` - Deepgram credentials

5. **STT Configuration**
   - `WHISPER_URL` - Whisper server endpoint
   - `WHISPER_MODEL_SIZE` - Model size (base/small/medium/large)

### Configuration Loading

```python
# Example from orchestrator initialization
config = OrchestratorConfig(
    model=os.getenv("HYPR_VOICE_MODEL", "claude-sonnet-4-5"),
    max_turns=int(os.getenv("HYPR_VOICE_MAX_TURNS", "1")),
    enable_subagents=os.getenv("HYPR_VOICE_ENABLE_SUBAGENTS", "false") == "true",
    working_directory=os.getenv("HYPR_VOICE_WORKING_DIR"),
)
```

---

## Security Considerations

### 1. API Key Management

**Practices:**
- Never hardcode credentials
- Use environment variables exclusively
- Support API key rotation (Cerebras router)
- Separate keys for different services

**Implementation:**
```python
# cerebras_router.py
def _load_api_keys(self) -> List[str]:
    keys = []
    for name in ["CEREBRAS_API_KEY_ONE", "CEREBRAS_API_KEY_TWO", "CEREBRAS_API_KEY_THREE"]:
        key = os.getenv(name)
        if key and key not in keys:
            keys.append(key)
    return keys

def _get_next_key(self) -> Optional[str]:
    # Round-robin rotation
    key = self.api_keys[self.current_key_index]
    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    return key
```

### 2. Tool Authorization

**Practices:**
- Whitelist allowed tools per agent
- Permission modes in Claude SDK
- File operation sandboxing

**Implementation:**
```python
@dataclass
class OrchestratorConfig:
    allowed_tools: list[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Grep", "Glob", "Bash", "Skill", "SlashCommand"
    ])
    permission_mode: str = "default"
```

### 3. Shell Command Safety

**Practices:**
- Shell agent has safety guidelines
- Prefer safe, reversible operations
- Validate commands before execution
- Use dry-run flags

**Implementation:**
```python
ShellAgent = AgentDefinition(
    prompt="""
    ## Safety Rules
    - NEVER run `rm -rf /` or similar destructive commands
    - NEVER expose secrets or credentials in output
    - ALWAYS check current directory before file operations
    - PREFER `mv` to backup before destructive changes
    """
)
```

### 4. Session Isolation

**Practices:**
- Each session has unique ID
- No cross-session data leakage
- Context windows are isolated
- Automatic cleanup on completion

---

## Performance Optimizations

### 1. Fast Routing

**Keyword Router:**
- Instant matching (<1ms)
- No external API calls
- Pre-compiled regex patterns

**Cerebras Router:**
- AI-powered but still fast (~200ms)
- Timeout protection (configurable)
- Automatic fallback to keyword router

### 2. Single-Turn Processing

**Design Decision:**
```python
@dataclass
class OrchestratorConfig:
    max_turns: int = 1  # Fast: single turn only
```

**Why:**
- Multi-turn conversations add latency
- Voice interactions require speed
- Session-level conversation tracking handles context
- Reduces LLM calls and costs

### 3. Direct API vs SDK

**Comparison:**
- **Direct API:** ~3 seconds for voice responses
- **Claude SDK:** ~68 seconds (due to subagent overhead)

**Implementation:**
```python
if CLAUDE_SDK_AVAILABLE and self.config.enable_subagents:
    async for chunk in self._process_with_sdk(query, route, session_id):
        yield chunk
else:
    # Use direct API for speed
    async for chunk in self._process_fallback(query, route, session_id):
        yield chunk
```

**Recommendation:** Use direct API for voice, SDK for complex tasks

### 4. Streaming Responses

**Token-Level Streaming:**
```python
async def process_streaming(self, query: str) -> AsyncIterator[dict]:
    # Stream individual tokens as they arrive
    with client.messages.stream(...) as stream:
        for text in stream.text_stream:
            yield {"type": "token", "content": text}
```

**Benefits:**
- Real-time TTS can start immediately
- Lower perceived latency
- Better user experience

### 5. Context Compression

**Strategies:**
- Remove empty lines and whitespace
- Truncate long lines
- Keep first/last sections, summarize middle
- Cache compressed results

**Impact:**
- Reduced token usage
- Faster response times
- Lower API costs

---

## Claude SDK Integration

### SDK Compatibility Layer

**Purpose:**
- Provides seamless integration with official Claude Agent SDK
- Falls back to mock implementation if SDK unavailable
- Single import point for SDK components

**Usage:**
```python
from hypr_voice.services.sdk_compat import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    sdk_query,
    CLAUDE_SDK_AVAILABLE,
)

if CLAUDE_SDK_AVAILABLE:
    async for message in sdk_query(prompt=prompt, options=options):
        # Process response
```

### Agent Definitions

**Following Claude SDK Patterns:**

```python
@dataclass
class AgentDefinition:
    name: str
    description: str  # When to use this agent
    prompt: str  # System prompt
    tools: list[str]  # Allowed tools
    model: AgentModel  # sonnet/opus/haiku

CodeAgent = AgentDefinition(
    name="code-worker",
    description="Code analysis, generation, and refactoring tasks",
    prompt="You are a specialized code agent...",
    tools=["Read", "Write", "Edit", "Grep", "Glob"],
    model=AgentModel.SONNET,
)
```

### SDK Query Function

**Simple Query Interface:**
```python
async def sdk_query(
    prompt: str,
    options: ClaudeAgentOptions,
) -> AsyncIterator[Union[AssistantMessage, ResultMessage]]:
    """
    Query Claude with agent configuration.
    Yields messages as they arrive.
    """
```

**Usage in Orchestrator:**
```python
options = ClaudeAgentOptions(
    system_prompt=system_prompt,
    permission_mode=self.config.permission_mode,
    max_turns=self.config.max_turns,
    working_directory=self.config.working_directory,
    allowed_tools=self.config.allowed_tools,
)

async for message in sdk_query(prompt=prompt, options=options):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                yield {"type": "text", "content": block.text}
```

---

## Event Hooks System

### Hook Architecture

**Purpose:** Extensible event handling for monitoring, logging, and custom behaviors

**Components:**
```python
class HookEvent(Enum):
    AGENT_CREATED = "agent_created"
    AGENT_STARTED = "agent_started"
    TASK_COMPLETED = "task_completed"
    TOOL_CALLED = "tool_called"
    # ... 15+ event types

class Hook:
    name: str
    events: List[HookEvent]
    handler: Callable
    priority: int  # Higher = earlier execution
    enabled: bool
```

**Predefined Hooks:**
- `event_logger` - Logs all events
- `error_notifier` - Sends error notifications
- `performance_monitor` - Tracks task duration
- `context_sync` - Syncs context changes
- `audit_trail` - Maintains audit log

**Usage:**
```python
from hypr_voice.services.hooks.event_hooks import HookManager, Hook, HookEvent

manager = HookManager()

# Register custom hook
hook = Hook(
    name="my_custom_hook",
    events=[HookEvent.TASK_COMPLETED],
    handler=my_handler,
    priority=10,
)
manager.register_hook(hook)

# Trigger events
await manager.trigger(HookContext(
    event=HookEvent.TASK_COMPLETED,
    agent_id="agent-123",
    timestamp=datetime.utcnow(),
    data={"duration": 1234},
))
```

---

## Module Structure

```
src/hypr_voice/
├── orchestrator/          # Multi-agent orchestration
│   ├── orchestrator.py    # Main orchestrator
│   ├── router.py          # Query routing
│   ├── cerebras_router.py # AI-powered routing
│   ├── context_manager.py # Context isolation
│   └── registry.py        # Agent lifecycle
├── core/                  # Core utilities
│   └── loggurl.py        # Centralized logging
├── agents/               # Agent definitions
│   └── definitions.py    # Predefined agents
├── services/             # External services
│   ├── sdk_compat.py     # Claude SDK compatibility
│   ├── hooks/            # Event hooks system
│   ├── voice/            # TTS providers
│   ├── Cerebras_integration/  # Cerebras client
│   └── gemini_live/      # Gemini Live API
├── whisper/              # Speech-to-text
│   ├── core/             # Hybrid client
│   ├── processors/       # Audio processors
│   └── hooks/            # Whisper event hooks
├── tools/                # Built-in tools
│   └── builtin/          # Voice tools
├── middleware/           # Request middleware
│   ├── hooks.py          # Middleware hooks
│   └── router.py         # Request routing
├── ipc/                  # Inter-process communication
│   ├── websocket.py      # WebSocket server
│   └── hyprland.py       # Hyprland IPC
├── server.py             # FastAPI server
└── paths.py              # Path utilities
```

---

## Design Principles Summary

### 1. Modularity
- Each component has a single responsibility
- Clear interfaces between modules
- Easy to swap implementations (TTS providers, routers)

### 2. Performance-First
- Optimized for voice (low latency)
- Streaming responses
- Single-turn processing by default
- Context compression

### 3. Extensibility
- Event hooks for custom behavior
- Plugin architecture for agents
- Registry pattern for providers
- Configuration via environment

### 4. Reliability
- Fallback mechanisms (Cerebras → keyword routing)
- Error handling throughout
- Session cleanup on errors
- Comprehensive logging

### 5. Developer Experience
- Clear documentation
- Semantic logging
- Type hints throughout
- Consistent patterns

---

## Future Architecture Considerations

### Potential Enhancements

1. **Multi-Modal Support**
   - Image processing agents
   - Video understanding
   - Multi-modal query routing

2. **Distributed Agents**
   - Agent instances across multiple machines
   - Load balancing for high-volume scenarios
   - Remote agent execution via IPC

3. **Advanced Routing**
   - Ensemble routing (multiple strategies combined)
   - Learning from past decisions
   - Custom routing models fine-tuned for use cases

4. **Enhanced Context Management**
   - Vector embeddings for semantic context retrieval
   - Long-term memory across sessions
   - Context prioritization based on relevance

5. **Performance Optimization**
   - Response caching for common queries
   - Batch processing for multiple requests
   - Parallel agent execution for independent tasks

---

## References

### Anthropic Documentation
- [Claude Agent SDK](https://docs.anthropic.com/en/docs/build-with-claude/agent-sdk)
- [Multi-Agent Orchestration](https://docs.anthropic.com/en/docs/build-with-claude/multi-agent-orchestration)
- [Context Window Management](https://docs.anthropic.com/en/docs/build-with-claude/context-management)

### Design Patterns
- Strategy Pattern - Routing, TTS providers
- Observer Pattern - Event hooks
- Registry Pattern - Agent lifecycle
- Adapter Pattern - SDK compatibility
- Builder Pattern - Configuration

### Project Documentation
- `docs/ENVIRONMENT_VARIABLES.md` - Configuration reference
- `CLAUDE.md` - SPARC methodology (if applicable)
- `README.md` - Project overview

---

**Last Updated:** 2026-01-26
**Architecture Version:** 1.0
**Maintained By:** Hypr-Voice Development Team
