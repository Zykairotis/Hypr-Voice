# 🎯 Quick Reference Guide

## 🚀 Core System Components

### 1. **orchestrator.py** - Main FastAPI Server
```python
# Create orchestrator
orchestrator = AgentOrchestrator()

# Create agent
agent_id = await orchestrator.create_agent(config)

# Execute instruction
await orchestrator.execute_instruction(agent_id, "Do something")
```

### 2. **client.py** - Python SDK
```python
# Quick agent creation
agent_id = await quick_agent(
    name="my-agent",
    working_directory="/tmp/agent",
    instruction="Create a hello world program",
    skills=["file_operations", "bash_execution"],
    monitor=True
)
```

### 3. **mcp_loader.py** - MCP System
```python
# Load MCP servers
manager = EnhancedMCPManager()
await manager.add_preset_server("filesystem")
await manager.add_preset_server("github")
```

### 4. **subagent_system.py** - Hierarchical Agents
```python
# Create sub-agents
coordinator = SubAgentCoordinator(parent_id, orchestrator)
await coordinator.create_sub_agent(definition)
await coordinator.execute_parallel(["agent1", "agent2"])
```

### 5. **kokoro_integration.py** - Voice Synthesis
```python
# Synthesize speech
tts = KokoroTTS(config)
audio_file = await tts.synthesize("Hello world")
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/create` | Create new agent |
| POST | `/agents/{id}/instruct` | Send instruction |
| GET | `/agents/list` | List all agents |
| GET | `/agents/{id}/status` | Get agent status |
| DELETE | `/agents/{id}` | Delete agent |
| POST | `/agents/{id}/subagents/create` | Create subagent |
| GET | `/skills/list` | List available skills |
| GET | `/mcp/presets` | List MCP presets |
| WS | `/ws/{client_id}` | WebSocket connection |

## 🛠️ Available Skills

- **file_operations** - Read, write, manipulate files
- **bash_execution** - Execute shell commands
- **voice_synthesis** - Convert text to speech
- **hierarchical_agents** - Create/manage sub-agents
- **web_search** - Search the web (optional)

## 🔌 MCP Server Presets

- **filesystem** - File system operations
- **github** - GitHub operations
- **git** - Git operations
- **brave-search** - Web search
- **postgres** - PostgreSQL database
- **sqlite** - SQLite database

## 🎤 Voice Models

- `af_bella` - American Female (Professional)
- `af_sky` - American Female (Friendly)
- `am_adam` - American Male (Technical)
- `bf_emma` - British Female
- `bm_george` - British Male (Narrator)

## 🔥 WebSocket Events

```javascript
// Event Types
AGENT_CREATED      // New agent created
AGENT_STARTED      // Instruction started
AGENT_OUTPUT       // Output streaming
AGENT_COMPLETED    // Execution complete
AGENT_ERROR        // Error occurred
TOOL_EXECUTION     // Tool being executed
SKILL_EXECUTED     // Skill completed
MCP_EVENT          // MCP server event
SUBAGENT_CREATED   // Sub-agent created
VOICE_SYNTHESIS    // Voice generated
```

## 📝 Agent Configuration

```python
config = AgentConfig(
    name="my-agent",
    working_directory="/tmp/agent",
    model="claude-3-5-sonnet-20241022",
    max_tokens=8096,
    temperature=1.0,
    skills=["file_operations", "bash_execution"],
    mcp_servers=["filesystem", "git"],
    enable_voice=True,
    parent_id=None  # For sub-agents
)
```

## 🔄 Workflow Definition

```python
workflow = AgentWorkflow("my-workflow", orchestrator)

# Add steps
workflow.add_agent_step(
    name="step1",
    role="developer",
    instructions="Write code",
    skills=["file_operations"],
    depends_on=[]
)

# Execute
results = await workflow.execute()
```

## 🚦 Quick Commands

### Start System
```bash
# Using systemd
systemctl start agent-orchestrator

# Using Docker
docker-compose up -d

# Direct Python
uvicorn orchestrator:app --host 0.0.0.0 --port 8922
```

### Monitor Agents
```python
# Real-time monitoring
monitor = RichMonitor(client)
await monitor.start()
```

### Health Check
```bash
curl http://localhost:8922/health
```

## 🔧 Environment Variables

```bash
# Required
ANTHROPIC_API_KEY=your_key
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379/0

# Optional
OPENAI_API_KEY=your_key
GOOGLE_API_KEY=your_key
GITHUB_TOKEN=your_token
BRAVE_API_KEY=your_key
```

## 📊 Monitoring URLs

- API: `http://localhost:8922`
- API Docs: `http://localhost:8922/docs`
- WebSocket: `ws://localhost:8922/ws/{client_id}`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## 🐛 Debugging

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Mock mode (no API keys)
config.mock_mode = True

# View agent history
agent = orchestrator.get_agent(agent_id)
print(agent.conversation_history)
```

## 💡 Common Patterns

### Parallel Agent Execution
```python
agents = ["agent1", "agent2", "agent3"]
results = await coordinator.execute_parallel(agents)
```

### Sequential with Context Passing
```python
results = await coordinator.execute_sequential(
    agents,
    pass_results=True
)
```

### Voice-Enabled Agent
```python
config.enable_voice = True
await agent.execute_instruction("Explain this and speak it")
```

### MCP Tool Usage
```python
result = await mcp_manager.call_tool(
    "filesystem",
    "read_file",
    {"path": "/etc/hosts"}
)
```
