# Hypr-Voice Data Flow and Communication Patterns

This document describes how data flows through the Hypr-Voice system and the communication patterns used between components.

## Table of Contents

1. [Query Processing Flow](#query-processing-flow)
2. [Voice Interaction Flow](#voice-interaction-flow)
3. [Agent Lifecycle Flow](#agent-lifecycle-flow)
4. [WebSocket Communication](#websocket-communication)
5. [MCP Protocol Flow](#mcp-protocol-flow)
6. [Hook Execution Flow](#hook-execution-flow)
7. [Hyprland Integration Flow](#hyprland-integration-flow)

---

## Query Processing Flow

### Standard Query Flow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Router
    participant Agent
    participant LLM
    participant Tools
    participant ContextMgr

    User->>Orchestrator: process(query)
    Orchestrator->>Router: route(query)
    Router-->>Orchestrator: RouteDecision

    Orchestrator->>ContextMgr: create_window(agent_id)
    ContextMgr-->>Orchestrator: window

    Orchestrator->>Agent: Execute with system prompt
    Agent->>LLM: Generate response
    LLM-->>Agent: Response chunks

    loop For each chunk
        Agent->>Orchestrator: yield chunk
        Orchestrator->>User: Stream chunk
    end

    Agent->>Tools: Use tool (if needed)
    Tools-->>Agent: Tool result
    Agent->>LLM: Continue with result

    Agent-->>Orchestrator: Final result
    Orchestrator->>ContextMgr: compress_result()
    ContextMgr-->>Orchestrator: Compressed result
    Orchestrator->>User: Final response
```

### Data Transformation Pipeline

**Input Query:**
```
"Write a Python function that sorts a list of dictionaries"
```

**Stage 1: Routing**
```json
{
  "type": "route_decision",
  "route": "code-worker",
  "confidence": 0.85,
  "reasoning": "Query involves code-related tasks",
  "keywords_matched": ["code", "function", "python"]
}
```

**Stage 2: Agent Invocation**
```python
{
  "agent": "code-worker",
  "model": "sonnet",
  "system_prompt": "You are a specialized code agent...",
  "allowed_tools": ["Read", "Write", "Edit", "Grep", "Glob"]
}
```

**Stage 3: LLM Response Streaming**
```python
# Each chunk yielded
{"type": "text", "content": "Here's a Python function", "agent": "code-worker"}
{"type": "text", "content": " that sorts dictionaries:", "agent": "code-worker"}
# ...
```

**Stage 4: Tool Execution (if needed)**
```json
{
  "type": "tool_use",
  "tool": "Write",
  "input": {"file_path": "sort_dicts.py", "content": "..."}
}
```

**Stage 5: Final Result**
```json
{
  "type": "result",
  "content": "Completed",
  "session_id": "abc123...",
  "turns": 1,
  "cost_usd": 0.0021
}
```

---

## Voice Interaction Flow

### F10 Agent Mode (Hyprland Integration)

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Recording: F10 pressed
    Recording --> Transcribing: F10 released
    Transcribing --> Routing: Transcription complete
    Routing --> Streaming: Route decision
    Streaming --> Synthesis: LLM tokens
    Synthesis --> Playback: Audio ready
    Playback --> Idle: Complete

    note right of Recording
        User speaks while F10 held
        Audio captured from microphone
    end note

    note right of Transcribing
        Whisper processes audio
        TCPGen biases decoding
    end note

    note right of Streaming
        Token-level streaming
        Real-time TTS possible
    end note

    note right of Playback
        Kokoro/Deepgram synthesis
        PulseAudio playback
    end note
```

### Voice Processing Pipeline

```mermaid
graph LR
    A[Microphone] --> B[Audio Buffer]
    B --> C[Whisper STT]
    C --> D[TCPGen Decoder]
    D --> E[Transcription]
    E --> F[Orchestrator]
    F --> G[LLM Streaming]
    G --> H[TTS Engine]
    H --> I[Audio Stream]
    I --> J[PulseAudio]
    J --> K[Speaker]
```

**Audio Flow Details:**

1. **Capture:**
   - PyAudio: 16kHz, 1 channel, int16
   - Chunk size: 4096 samples
   - Device: `PULSE_SOURCE` env var

2. **Transmission:**
   - WebSocket: Binary audio frames
   - Conversion: int16 -> float32 [-1, 1]
   - Chunk interval: 10ms

3. **Transcription:**
   - Whisper Live: Real-time VAD
   - TCPGen: Vocabulary biasing
   - Output: Incremental text

4. **Routing:**
   - QueryRouter: <1ms
   - Or CerebrasRouter: 2-8s
   - Decision: Agent type + confidence

5. **Generation:**
   - LLM: Streaming tokens
   - Interval: 50-100ms per token
   - Context: Agent-specific prompt

6. **Synthesis:**
   - Kokoro: HTTP streaming
   - Deepgram: WebSocket streaming
   - Format: WAV/Opus

7. **Playback:**
   - PulseAudio: Direct stream
   - Buffering: 200-500ms
   - Latency: <1s total

---

## Agent Lifecycle Flow

### Session State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: create_session()
    Created --> Running: start_session()
    Running --> Paused: pause()
    Paused --> Running: resume()
    Running --> Completed: complete_session(result)
    Running --> Error: error_session(error)
    Error --> Destroyed: destroy_session()
    Completed --> Destroyed: destroy_session()
    Destroyed --> [*]

    note right of Created
        session_id generated
        context window created
        metadata stored
    end note

    note right of Running
        agent executing
        events emitted
        context filling
    end note

    note right of Completed
        result compressed
        archived to history
        statistics updated
    end note
```

### Parent-Child Relationships

```mermaid
graph TB
    Orchestrator[Orchestrator Session]
    Code1[code-worker #1]
    Code2[code-worker #2]
    Research[research-worker]
    Sub1[subagent #1]
    Sub2[subagent #2]

    Orchestrator -->|spawn| Code1
    Orchestrator -->|spawn| Code2
    Orchestrator -->|spawn| Research

    Code1 -->|spawn| Sub1
    Research -->|spawn| Sub2

    style Orchestrator fill:#f9f,stroke:#333,stroke-width:4px
    style Code1 fill:#bbf,stroke:#333,stroke-width:2px
    style Code2 fill:#bbf,stroke:#333,stroke-width:2px
```

**Relationship Tracking:**
```python
# Parent session
parent_session = {
    "session_id": "orch-123",
    "agent_type": "orchestrator",
    "status": "running"
}

# Child session
child_session = registry.spawn_child(
    parent_id="orch-123",
    agent_type="code-worker",
    query="Implement feature X"
)

# Child inherits context
child_session.metadata = {
    "spawned_from": "orch-123",
    "parent_agent_type": "orchestrator"
}
```

---

## WebSocket Communication

### Message Protocol

**Client to Server:**

```json
{
  "type": "query|spawn_agent|destroy_agent|list_agents|ping|subscribe|unsubscribe",
  "query": "...",           // for query
  "agent_type": "...",      // for spawn_agent
  "task": "...",            // for spawn_agent
  "session_id": "...",      // for destroy_agent
  "topic": "..."            // for subscribe/unsubscribe
}
```

**Server to Client:**

```json
{
  "type": "chunk|route_decision|result|error|agent_spawned|pong|subscribed",
  "content": "...",         // text content
  "route": "...",           // agent type
  "confidence": 0.85,       // routing confidence
  "agent": "...",           // agent type
  "session_id": "...",      // session ID
  "error": "..."            // error message
}
```

### Subscription Model

```mermaid
graph LR
    Client1[Client 1] -->|subscribe all| Topics[Topic Manager]
    Client2[Client 2] -->|subscribe agents| Topics
    Client3[Client 3] -->|subscribe voice| Topics

    Topics -->|broadcast all| Client1
    Topics -->|broadcast agents| Client2
    Topics -->|broadcast voice| Client3

    Broadcast[Event Broadcaster] -->|agent events| Topics
    Broadcast -->|voice events| Topics
```

**Topic Categories:**
- `all` - All events
- `agents` - Agent lifecycle
- `voice` - Voice synthesis
- `transcription` - Speech recognition

### WebSocket Event Flow

```mermaid
sequenceDiagram
    participant Client
    participant WS as WebSocket Server
    participant Orch as Orchestrator
    participant Agent

    Client->>WS: Connect
    WS-->>Client: connected {client_id}

    Client->>WS: subscribe {topic: "agents"}
    WS-->>Client: subscribed {topic: "agents"}

    Client->>WS: query {query: "Write code"}
    WS->>Orch: process(query)

    loop Streaming
        Orch->>WS: chunk {type: "text"}
        WS->>Client: chunk {type: "text"}
    end

    Orch->>WS: chunk {type: "result"}
    WS->>Client: chunk {type: "result"}

    Orch->>WS: broadcast {agent_spawned}
    WS->>Client: agent_spawned (subscribed)
```

---

## MCP Protocol Flow

### JSON-RPC Communication

```mermaid
sequenceDiagram
    participant Manager as MCP Manager
    participant Process as Server Process
    participant Protocol as MCP Protocol
    participant Server as MCP Server

    Manager->>Process: spawn subprocess
    Process->>Protocol: start()
    Protocol->>Protocol: _read_responses() loop

    Manager->>Protocol: send_request("initialize", {...})
    Protocol->>Server: write JSON-RPC request
    Server-->>Protocol: JSON-RPC response
    Protocol-->>Manager: initialized

    Manager->>Protocol: send_request("tools/list")
    Protocol->>Server: write JSON-RPC request
    Server-->>Protocol: tools array
    Protocol-->>Manager: tool definitions

    Manager->>Protocol: send_request("tools/call", {...})
    Protocol->>Server: write JSON-RPC request
    Server-->>Protocol: tool result
    Protocol-->>Manager: execution result
```

### Request Format

**Initialize Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "0.1.0",
    "capabilities": {
      "tools": true,
      "resources": true,
      "prompts": true
    }
  }
}
```

**Tool Call Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "read_file",
    "arguments": {
      "path": "/etc/hosts"
    }
  }
}
```

### Response Format

**Success Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "127.0.0.1 localhost..."
      }
    ]
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32602,
    "message": "Invalid params"
  }
}
```

### MCP Tool Discovery

```python
# 1. Server starts
await server.start()

# 2. Initialize handshake
result = await server.protocol.initialize()

# 3. Discover tools
tools_data = await server.protocol.list_tools()
for tool in tools_data:
    print(f"Tool: {tool['name']}")
    print(f"  Description: {tool['description']}")
    print(f"  Schema: {tool['inputSchema']}")

# 4. Convert to Claude format
claude_tools = [
    {
        "name": f"{server_name}_{tool['name']}",
        "description": f"[MCP:{server_name}] {tool['description']}",
        "input_schema": tool['inputSchema']
    }
    for tool in tools_data
]
```

---

## Hook Execution Flow

### Pre-Tool-Use Hook

```mermaid
sequenceDiagram
    participant Agent
    participant HookMgr as Hook Manager
    participant Hook1 as Hook 1
    participant Hook2 as Hook 2
    participant Tool

    Agent->>HookMgr: execute(PRE_TOOL_USE, input_data)
    HookMgr->>Hook1: execute(input_data)
    Hook1-->>HookMgr: HookResult(allow=True)
    HookMgr->>Hook2: execute(input_data)
    Hook2-->>HookMgr: HookResult(modified_input={...})
    HookMgr-->>Agent: Combined HookResult

    alt Hook allows
        Agent->>Tool: Use tool with modified_input
        Tool-->>Agent: Tool result
    else Hook denies
        Agent->>Agent: Skip tool execution
        Agent-->>Agent: Return error
    end
```

### Hook Priority and Chaining

```python
# Hooks are sorted by priority (higher = earlier)
hooks = [
    Hook(name="audit", priority=1),      # Runs first
    Hook(name="validation", priority=10), # Runs second
    Hook(name="logging", priority=20),    # Runs third
]

# Execution order
for hook in sorted_hooks:
    result = await hook.execute(context)
    if not result.allow:
        break  # Stop chain

    if result.modified_input:
        input_data = result.modified_input  # Pass to next
```

### Hook Result Propagation

```python
# Hook 1: Add metadata
result1 = HookResult(
    allow=True,
    metadata={"stage": "validation"}
)

# Hook 2: Modify input
result2 = HookResult(
    allow=True,
    modified_input={"command": "safe_" + command},
    system_message="Command sanitized"
)

# Combined result
final = {
    "allow": True,
    "modified_input": {"command": "safe_ls"},
    "system_message": "Command sanitized",
    "metadata": {"stage": "validation"}  # Merged
}
```

---

## Hyprland Integration Flow

### F10 Agent Mode Sequence

```mermaid
stateDiagram-v2
    [*] --> Waiting: F10 not pressed
    Waiting --> Recording: F10 down (keydown)
    Recording --> Recording: Capturing audio...
    Recording --> Processing: F10 up (keyup)
    Processing --> Transcribing: Send to Whisper
    Transcribing --> Routing: Got transcription
    Routing --> Streaming: Route to agent
    Streaming --> Playing: Stream tokens to TTS
    Playing --> Waiting: Playback complete

    note right of Recording
        User speaks into microphone
        PyAudio captures PCM data
        Stored in circular buffer
    end note

    note right of Transcribing
        Whisper Live processes
        Returns incremental text
        TCPGen biases for app-specific vocab
    end note

    note right of Streaming
        Orchestrator routes query
        LLM streams tokens
        TTS begins immediately
    end note
```

### Hyprland Event Handling

```python
# 1. Start event listener
await hypr_ipc.start_event_listener()

# 2. Register event handler
def on_activewindow(event: HyprlandEvent):
    window_info = json.loads(event.data)
    app_name = window_info.get("class", "")

    # Update vocabulary for app
    hook_bus.emit("vocab_change", app_name=app_name)

hypr_ipc.on_event("activewindow", on_activewindow)

# 3. Event loop
while running:
    line = await reader.readline()
    event = HyprlandEvent.parse(line)
    # Dispatch to handlers
```

### Notification Dispatch

```python
# Send notification via notify-send
await send_notification(
    title="Agent Mode",
    message="Processing your request...",
    urgency="normal",  # low, normal, critical
    timeout=5000,       # milliseconds
    app_name="Hypr-Voice"
)

# Implementation via subprocess
proc = await asyncio.create_subprocess_exec(
    "notify-send",
    "-a", "Hypr-Voice",
    "-u", "normal",
    "-t", "5000",
    "Agent Mode",
    "Processing your request..."
)
```

---

## Data Formats

### Session Data

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_type": "code-worker",
  "status": "running",
  "query": "Write a sorting function",
  "created_at": "2024-01-26T10:30:00Z",
  "updated_at": "2024-01-26T10:30:15Z",
  "parent_id": null,
  "result": null,
  "error": null,
  "metadata": {
    "turns": 1,
    "tokens_used": 450,
    "cost_usd": 0.0015
  }
}
```

### Context Entry

```json
{
  "content": "def sort_dicts(items, key):...",
  "type": "result",
  "timestamp": "2024-01-26T10:30:10Z",
  "tokens": 120,
  "agent_id": "code-worker-123",
  "metadata": {
    "tool_used": "Write",
    "file_path": "sort_dicts.py"
  }
}
```

### Route Decision

```json
{
  "agent_type": "code-worker",
  "confidence": 0.85,
  "reasoning": "Query involves code-related tasks. Matched keywords: code, function, python",
  "keywords_matched": ["code", "function", "python"],
  "should_parallelize": false,
  "secondary_agents": []
}
```

---

## Performance Metrics

### Latency Breakdown

| Stage | Typical | Best | Worst |
|-------|---------|------|-------|
| Routing (keyword) | <1ms | <1ms | <1ms |
| Routing (Cerebras) | 5s | 2s | 8s |
| LLM (first token) | 800ms | 300ms | 2s |
| LLM (per token) | 80ms | 40ms | 200ms |
| TTS (Kokoro) | 200ms | 100ms | 500ms |
| TTS (Deepgram) | 150ms | 80ms | 400ms |
| STT (Whisper) | 300ms | 100ms | 1s |

### Throughput

| Component | Rate |
|-----------|------|
| Orchestrator queries | ~100 req/s |
| WebSocket messages | ~1000 msg/s |
| Audio streaming | 16 KB/s (16kHz) |
| LLM tokens | 10-20 tokens/s |

---

## Error Handling

### Error Propagation

```mermaid
graph TB
    Error[Error Occurs] --> Catch{Caught?}
    Catch -->|Yes| Log[Log Error]
    Catch -->|No| Crash[Uncaught Exception]

    Log --> Emit[Emit Error Event]
    Emit --> Cleanup[Cleanup Resources]
    Cleanup --> Return[Return Error Response]

    style Error fill:#f99
    style Crash fill:#f00
    style Return fill:#9f9
```

### Error Response Format

```json
{
  "type": "error",
  "error": "Failed to synthesize speech",
  "details": {
    "provider": "kokoro",
    "code": "CONNECTION_ERROR",
    "message": "Connection refused"
  },
  "timestamp": "2024-01-26T10:30:00Z",
  "session_id": "abc123..."
}
```

---

## Security Considerations

### Input Validation

```python
# 1. Hook-based validation
async def validate_bash(input_data, tool_use_id, context):
    if input_data["tool_name"] == "Bash":
        command = input_data["tool_input"]["command"]
        if "rm -rf /" in command:
            return HookResult.deny_action("Dangerous command")
    return HookResult.allow_action()

# 2. Size limits
MAX_QUERY_LENGTH = 10000
if len(query) > MAX_QUERY_LENGTH:
    raise ValueError("Query too long")

# 3. Sanitization
def sanitize_path(path: str) -> str:
    # Remove directory traversal
    path = path.replace("..", "").replace("~", "")
    # Ensure absolute path
    return os.path.abspath(path)
```

### Audit Trail

```python
# All events logged
audit_entry = {
    "timestamp": datetime.utcnow().isoformat(),
    "event": "tool_called",
    "agent_id": "code-worker-123",
    "tool_name": "Bash",
    "input": {"command": "ls -la"},
    "result": "success"
}

# Write to audit log
with open("/var/log/hypr_voice/audit.log", "a") as f:
    f.write(json.dumps(audit_entry) + "\n")
```
