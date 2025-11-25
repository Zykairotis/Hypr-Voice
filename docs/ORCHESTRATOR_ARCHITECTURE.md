# Hypr-Voice Orchestrator Architecture

The Agent Orchestrator is a Claude Agent SDK-based system that spawns specialized subagents for different task types, maintaining isolated context windows for each.

## Services & Ports

| Service | Port | Purpose |
|---------|------|---------|
| Hybrid Whisper | 9099 | Speech-to-text transcription server |
| Context WebSocket | 9091 | Live context streaming (window, clipboard, project) |
| Agent Orchestrator | 9093 | Claude Agent SDK orchestrator |
| Web UI Frontend | 8933 | Next.js dashboard |
| Bridge API | 8934 | FastAPI backend proxy |

## Starting All Services

```bash
# Start everything
./scripts/start_everything.sh start

# Check status
./scripts/start_everything.sh status

# Stop all
./scripts/start_everything.sh stop
```

## Agent Types

The orchestrator can spawn 4 specialized agent types:

| Agent | Model | Purpose | Tools |
|-------|-------|---------|-------|
| `code-worker` | sonnet | Code analysis, generation, refactoring | Read, Write, Edit, Grep, Glob |
| `research-worker` | haiku | Research, information gathering | Read, Grep, Glob |
| `shell-worker` | sonnet | System operations, bash commands | Bash, Read, Grep |
| `voice-worker` | haiku | TTS/STT operations | Read |

## API Endpoints

### Orchestrator (Port 9093)

```
GET  /health              - Health check
GET  /agents              - List active agent sessions
GET  /agent-types         - Get available agent types
POST /query               - Send query to orchestrator
POST /spawn               - Spawn a new agent
DELETE /agents/{id}       - Destroy an agent session
WS   /ws                  - Real-time event stream
```

### Bridge API (Port 8934)

The bridge proxies requests to backend services:

```
# Whisper
GET  /api/whisper/status
GET  /api/audio/devices

# Orchestrator
GET  /api/orchestrator/status
GET  /api/orchestrator/agents
GET  /api/orchestrator/agent-types
POST /api/orchestrator/query
POST /api/orchestrator/spawn
DELETE /api/orchestrator/agents/{id}

# WebSocket proxies
WS   /ws/context          - Context WebSocket proxy
WS   /ws/orchestrator     - Orchestrator WebSocket proxy
```

## Architecture Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web UI (8933)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Bridge API (8934)                          │
│  - REST proxy to backend services                               │
│  - WebSocket relay for real-time updates                        │
└─────────────────────────────────────────────────────────────────┘
          │                   │                    │
          ▼                   ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ Hybrid Whisper  │  │  Context WS     │  │  Orchestrator   │
│     (9099)      │  │    (9091)       │  │    (9093)       │
│                 │  │                 │  │                 │
│ - Transcription │  │ - Window info   │  │ - Agent spawn   │
│ - VAD           │  │ - Clipboard     │  │ - Query routing │
│ - Audio input   │  │ - Project ctx   │  │ - Context mgmt  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## Voice Input (F10 Keybinding)

The F10 key triggers voice input mode:

1. **F10 Press** → Start audio recording
2. **F10 Release** → Stop recording, transcribe via Whisper, send to orchestrator

```bash
# Manual usage
./scripts/hypr-agent.sh start    # Start recording
./scripts/hypr-agent.sh process  # Stop and process
./scripts/hypr-agent.sh status   # Check status
./scripts/hypr-agent.sh query "your text query"
```

## Orchestrator Internals

### Query Routing

The orchestrator uses keyword/pattern matching to route queries:

```python
# Example routing
"write a function" → code-worker
"search for docs"  → research-worker
"run npm install"  → shell-worker
"say hello"        → voice-worker
```

### Context Management

Each agent maintains isolated context:
- **Token estimation**: ~4 chars per token
- **Max context**: 100,000 tokens (configurable)
- **Compression**: Automatic summarization when context exceeds limits

### Agent Lifecycle

```
CREATED → RUNNING → COMPLETED
              ↓
           ERROR
```

Agents can be destroyed on demand via API or UI.

## Configuration

### Environment Variables

```bash
ORCHESTRATOR_PORT=9093       # Orchestrator port
HYPR_AGENT_PORT=9093         # For hypr-agent.sh
HYPR_WHISPER_PORT=9099       # Whisper server port
CONTEXT_WS_UPSTREAM=ws://localhost:9091  # Context WS
```

### Model Configuration

Default models in `src/hypr_voice/agents/definitions.py`:
- Sonnet: `claude-sonnet-4-5` (code, shell tasks)
- Haiku: `claude-haiku` (research, voice tasks)

## Logs

```bash
# View logs
tail -f /tmp/hypr-voice-orchestrator.log
tail -f /tmp/hypr-voice-context-ws.log
tail -f /tmp/hybrid-whisper-server.log
tail -f /tmp/hypr-voice-ui.log
```

## Troubleshooting

### Orchestrator Shows Offline

1. Check if running: `curl http://localhost:9093/health`
2. Check logs: `cat /tmp/hypr-voice-orchestrator.log`
3. Restart: `./scripts/start_everything.sh stop && ./scripts/start_everything.sh start`

### Port Already in Use

```bash
# Find process on port
lsof -i :9093

# Kill if needed
kill -9 <PID>
```

### WebSocket Connection Failed

1. Verify bridge is running: `curl http://localhost:8934/docs`
2. Check browser console for CORS errors
3. Ensure all upstream services are running
