# Agent Configuration Guide

Complete configuration reference for multi-agent orchestration in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Agent Configuration](#agent-configuration)
- [Skills Configuration](#skills-configuration)
- [MCP Server Integration](#mcp-server-integration)
- [Claude SDK Configuration](#claude-sdk-configuration)
- [Workflow Configuration](#workflow-configuration)
- [Sub-Agent Configuration](#sub-agent-configuration)

---

## Overview

Hypr-Voice uses a sophisticated multi-agent orchestration system that supports:

- **Multiple agents** running in parallel
- **Hierarchical sub-agents** for complex tasks
- **Skills system** for agent capabilities
- **MCP server integration** for extended functionality
- **Claude SDK** integration for context-aware responses
- **Workflow orchestration** for multi-step processes

---

## Agent Configuration

### Agent Definition

```yaml
# In config.yaml
defaults:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 8096
  temperature: 1.0
  working_directory: "/tmp/agents"
  default_skills:
    - file_operations
    - bash_execution
  timeout: 300
```

### Agent Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `"claude-3-5-sonnet-20241022"` | LLM model to use |
| `max_tokens` | integer | `8096` | Maximum tokens per response |
| `temperature` | float | `1.0` | Response randomness (0-2) |
| `working_directory` | string | `"/tmp/agents"` | Agent working directory |
| `default_skills` | list | - | Default agent skills |
| `timeout` | integer | `300` | Agent timeout (seconds) |

### Creating Agents

#### Python API

```python
from hypr_voice.client import AgentClient, AgentConfig

# Create agent configuration
config = AgentConfig(
    name="my-agent",
    working_directory="/tmp/agents/my-agent",
    skills=["file_operations", "bash_execution"],
    model="claude-3-5-sonnet-20241022",
    max_tokens=4096,
    temperature=0.7
)

# Create agent
client = AgentClient()
agent_id = await client.create_agent(config)
```

#### With MCP Servers

```python
config = AgentConfig(
    name="mcp-agent",
    working_directory="/tmp/agents/mcp",
    skills=["file_operations"],
    mcp_servers=["filesystem", "git", "github"]
)

agent_id = await client.create_agent(config)
```

#### With Voice

```python
config = AgentConfig(
    name="voice-agent",
    working_directory="/tmp/agents/voice",
    skills=["voice_synthesis", "file_operations"],
    enable_voice=True,
    tts_provider="kokoro",
    tts_voice="af_bella"
)

agent_id = await client.create_agent(config)
```

---

## Skills Configuration

### Available Skills

```yaml
skills:
  file_operations:
    enabled: true
    description: "Read, write, and manipulate files"

  bash_execution:
    enabled: true
    description: "Execute bash commands"
    timeout: 60

  voice_synthesis:
    enabled: true
    description: "Convert text to speech using Kokoro TTS"
    default_voice: "af_bella"

  hierarchical_agents:
    enabled: true
    description: "Create and manage sub-agents"
    max_subagents: 10

  web_search:
    enabled: false
    description: "Search the web"
    provider: "brave"
```

### Built-in Skills

| Skill | Description | Dependencies |
|-------|-------------|--------------|
| `file_operations` | Read, write, manipulate files | None |
| `bash_execution` | Execute bash commands | None |
| `voice_synthesis` | Text-to-speech conversion | TTS provider |
| `hierarchical_agents` | Create sub-agents | None |
| `web_search` | Web search capabilities | Brave API |

### Custom Skills

#### Creating Custom Skills

```python
from hypr_voice.core.orchestrator import Skill

class CustomSkill(Skill):
    name = "custom_skill"
    description = "My custom skill"

    async def execute(self, context, **kwargs):
        # Skill implementation
        result = await self.do_something(kwargs)
        return result

# Register skill
orchestrator.register_skill(CustomSkill())
```

#### Skill Configuration

```yaml
skills:
  custom_skill:
    enabled: true
    description: "My custom skill"
    config:
      option1: "value1"
      option2: 42
```

---

## MCP Server Integration

### MCP Server Configuration

```yaml
mcp_servers:
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/"]
    description: "File system operations MCP server"
    enabled: true
    auto_restart: true
    timeout: 30

  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
    description: "GitHub operations MCP server"
    enabled: true

  git:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-git"]
    description: "Git operations MCP server"
    enabled: true
```

### Available MCP Servers

| Server | Description | Required Variables |
|--------|-------------|-------------------|
| `filesystem` | File system operations | None |
| `github` | GitHub API operations | `GITHUB_TOKEN` |
| `git` | Git repository operations | None |
| `brave-search` | Brave web search | `BRAVE_API_KEY` |
| `postgres` | PostgreSQL database | `DATABASE_URL` |
| `sqlite` | SQLite database | None |
| `fetch` | HTTP requests | None |
| `puppeteer` | Browser automation | None |

### MCP Server Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command` | string | - | Command to start server |
| `args` | list | `[]` | Command arguments |
| `env` | dict | `{}` | Environment variables |
| `description` | string | - | Server description |
| `enabled` | boolean | `false` | Enable/disable server |
| `auto_restart` | boolean | `false` | Auto-restart on failure |
| `timeout` | integer | `30` | Startup timeout (seconds) |

### Using MCP Servers

```python
from hypr_voice.services.mcp.mcp_loader import EnhancedMCPManager

# Initialize MCP manager
manager = EnhancedMCPManager()

# Add preset servers
await manager.add_preset_server("filesystem")
await manager.add_preset_server("git")

# Add custom server
from hypr_voice.services.mcp.mcp_loader import MCPServerConfig

custom_config = MCPServerConfig(
    name="custom-tool",
    command="python",
    args=["-m", "custom_mcp_server"],
    env={"API_KEY": "secret"},
    description="Custom MCP server"
)

await manager.add_server(custom_config)

# Get all tools
tools = manager.get_all_tools()

# Call a tool
result = await manager.call_tool(
    "filesystem",
    "list_directory",
    {"path": "/tmp"}
)
```

---

## Claude SDK Configuration

### Claude SDK Settings

```yaml
claude_sdk:
  enabled: true
  use_code_sdk: true              # Use Claude Code instance
  config_file: "claude-sdk.yaml"

  monitoring:
    enabled: true
    interval: 0.15                # 150ms update interval
    include_vocabulary: true

  defaults:
    enable_monitoring: true
    monitor_interval: 0.15
    use_claude_code: true
```

### Claude SDK Configuration File

```yaml
# config/hypr_voice/claude-sdk.yaml

sdk:
  use_code_sdk: true
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 8096
  temperature: 1.0
  session_timeout: 3600
  persist_sessions: true

monitoring:
  enabled: true
  interval: 0.15                  # 150ms
  include_context: true
  monitor_all_workspaces: true

context:
  include_window_class: true
  include_window_title: true
  include_vocabulary: true
  include_workspace: true
  max_vocabulary_terms: 20

applications:
  profiles:
    development:
      window_classes: ['Code', 'vim', 'nvim']
      extra_context: "User is coding"
    browsing:
      window_classes: ['firefox', 'chrome']
      extra_context: "User is browsing"
```

### Monitoring Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable monitoring |
| `interval` | float | `0.15` | Update interval (seconds) |
| `include_context` | boolean | `true` | Include app context |
| `monitor_all_workspaces` | boolean | `true` | Monitor all workspaces |

### Context Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `include_window_class` | boolean | `true` | Include window class |
| `include_window_title` | boolean | `true` | Include window title |
| `include_vocabulary` | boolean | `true` | Include vocabulary |
| `include_workspace` | boolean | `true` | Include workspace |
| `max_vocabulary_terms` | integer | `20` | Max vocabulary terms |

### Application Profiles

Pre-configured profiles for common applications:

| Profile | Window Classes | Context |
|---------|----------------|---------|
| `development` | Code, vim, nvim, emacs | Coding assistance |
| `browsing` | firefox, chrome, brave | Web assistance |
| `terminal` | alacritty, kitty, gnome-terminal | Command-line help |
| `communication` | discord, slack, teams | Concise responses |
| `documentation` | obsidian, notion, roam | Knowledge management |

---

## Workflow Configuration

### Workflow Definition

```python
from hypr_voice.services.subagents.subagent_system import AgentWorkflow
from hypr_voice.core.orchestrator import AgentOrchestrator

# Create orchestrator
orchestrator = AgentOrchestrator()

# Create workflow
workflow = AgentWorkflow("my-workflow", orchestrator)

# Add steps
workflow.add_agent_step(
    name="step1",
    role="worker",
    instructions="Do something",
    skills=["file_operations"]
)

workflow.add_agent_step(
    name="step2",
    role="processor",
    instructions="Process the results",
    skills=["bash_execution"],
    depends_on=["step1"]
)

# Execute workflow
results = await workflow.execute()
```

### Workflow Options

| Option | Type | Description |
|--------|------|-------------|
| `name` | string | Workflow name |
| `orchestrator` | AgentOrchestrator | Orchestrator instance |

### Workflow Step Types

#### Agent Step

```python
workflow.add_agent_step(
    name="step-name",
    role="agent-role",
    instructions="What to do",
    skills=["skill1", "skill2"],
    depends_on=["previous-step"]
)
```

#### Parallel Group

```python
workflow.add_parallel_group(
    "group-name",
    ["step1", "step2", "step3"]
)
```

#### Decision Step

```python
workflow.add_decision_step(
    name="decision",
    condition_agent="qa",
    condition_instruction="Does this meet quality standards?",
    true_branch=["documentation", "deployment"],
    false_branch=["bug-fixing", "retesting"]
)
```

#### Aggregation Step

```python
workflow.add_aggregation_step(
    name="summary",
    aggregate_from=["step1", "step2", "step3"],
    instructions="Summarize all results"
)
```

---

## Sub-Agent Configuration

### Sub-Agent System

```python
from hypr_voice.core.orchestrator import AgentOrchestrator, AgentConfig

# Create orchestrator
orchestrator = AgentOrchestrator()

# Create parent agent
parent_config = AgentConfig(
    name="team-leader",
    working_directory="/tmp/agents/team",
    skills=["hierarchical_agents", "file_operations"]
)

parent_id = await orchestrator.create_agent(parent_config)
parent_agent = orchestrator.get_agent(parent_id)

# Create sub-agents
developer = await parent_agent.create_subagent(
    "developer",
    skills=["file_operations", "bash_execution"]
)

tester = await parent_agent.create_subagent(
    "tester",
    skills=["bash_execution"]
)

reviewer = await parent_agent.create_subagent(
    "reviewer",
    skills=["file_operations"]
)
```

### Sub-Agent Limits

```yaml
limits:
  max_agents: 50
  max_conversation_length: 100
  max_subagents_per_agent: 10
  max_parallel_executions: 5
  max_workflow_steps: 50
```

### Sub-Agent Execution

#### Sequential Execution

```python
await parent_agent.execute_subagents_sequential(
    ["developer", "tester", "reviewer"],
    {
        "developer": "Create a Python calculator",
        "tester": "Test the calculator",
        "reviewer": "Review the code"
    }
)
```

#### Parallel Execution

```python
from hypr_voice.services.subagents.subagent_system import SubAgentCoordinator

coordinator = SubAgentCoordinator(parent_id, orchestrator)

results = await coordinator.execute_parallel(
    ["developer", "tester", "reviewer"]
)
```

---

## Agent Limits Configuration

```yaml
limits:
  max_agents: 50                 # Maximum concurrent agents
  max_conversation_length: 100   # Max messages per conversation
  max_subagents_per_agent: 10    # Max sub-agents per parent
  max_parallel_executions: 5     # Max parallel agent executions
  max_workflow_steps: 50         # Max workflow steps
```

### Limit Recommendations

| Use Case | max_agents | max_subagents | max_parallel |
|----------|------------|---------------|--------------|
| Development | 10-20 | 5 | 3-5 |
| Production | 50+ | 10 | 5-10 |
| Testing | 5-10 | 3 | 2-3 |

---

## WebSocket Configuration

```yaml
websocket:
  ping_interval: 30              # Ping interval (seconds)
  ping_timeout: 10               # Ping timeout (seconds)
  max_connections_per_client: 5  # Max connections per client
  message_queue_size: 1000       # Message queue size
```

### WebSocket Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ping_interval` | integer | `30` | Ping interval (seconds) |
| `ping_timeout` | integer | `10` | Ping timeout (seconds) |
| `max_connections_per_client` | integer | `5` | Max connections per client |
| `message_queue_size` | integer | `1000` | Message queue size |

---

## Storage Configuration

```yaml
storage:
  agent_data_dir: "/tmp/agents/data"
  session_dir: "/tmp/agents/sessions"
  logs_dir: "/tmp/agents/logs"
  cleanup_after_hours: 24
```

### Storage Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `agent_data_dir` | string | - | Agent data directory |
| `session_dir` | string | - | Session storage |
| `logs_dir` | string | - | Log file directory |
| `cleanup_after_hours` | integer | `24` | Cleanup interval (hours) |

---

## Security Configuration

```yaml
security:
  api_key_required: false
  api_key: "${API_KEY}"
  allowed_ips: []
  rate_limit:
    enabled: true
    requests_per_minute: 60
```

### Security Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `api_key_required` | boolean | `false` | Require API key |
| `api_key` | string | - | API key (from env) |
| `allowed_ips` | list | `[]` | Allowed IP addresses |
| `rate_limit.enabled` | boolean | `true` | Enable rate limiting |
| `rate_limit.requests_per_minute` | integer | `60` | Requests per minute |

---

## See Also

- [Configuration Reference](configuration-reference.md)
- [Environment Variables](environment-variables.md)
- [Examples](../examples/basic-usage.md)
- [Advanced: Custom Agents](../examples/advanced/custom-agents.md)
