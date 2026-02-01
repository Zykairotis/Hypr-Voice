# Hypr-Voice Configuration Reference

Complete reference for all configuration files, options, and settings in Hypr-Voice.

## Table of Contents

- [Configuration Overview](#configuration-overview)
- [Configuration File Structure](#configuration-file-structure)
- [Environment Variables](#environment-variables)
- [Configuration Loading](#configuration-loading)
- [Validation and Troubleshooting](#validation-and-troubleshooting)

---

## Configuration Overview

Hypr-Voice uses a hierarchical configuration system:

```
config/hypr_voice/
├── config.yaml              # Main orchestration & agent config
├── claude-sdk.yaml          # Claude Code SDK integration
└── whisper/                 # Whisper STT configuration
    ├── config.yaml          # Whisper server settings
    ├── audio-profile.yaml   # Audio input/output settings
    ├── vocabulary.yaml      # Main vocabulary configuration
    ├── context.yaml         # Context extraction settings
    ├── categories.yaml      # Application categories
    ├── custom_dictionary.yaml
    ├── context_enhanced.yaml
    ├── backend_overlays.yaml
    ├── notifications.yaml
    └── vocabularies/
        ├── development.yaml
        ├── gaming.yaml
        └── productivity.yaml
```

### Configuration Priority

1. **Environment variables** (highest priority)
2. **User configuration files** in `~/.config/hypr-voice/`
3. **System configuration** in `/etc/hypr-voice/`
4. **Default configuration** in `config/hypr_voice/`

---

## Configuration File Structure

### 1. Main Configuration (`config.yaml`)

The main configuration file controls the multi-agent orchestration system.

```yaml
# Multi-Agent Orchestration System Configuration

server:
  host: "0.0.0.0"              # Server bind address
  port: 8922                    # Server port
  log_level: "INFO"             # DEBUG, INFO, WARNING, ERROR
  workers: 4                    # Number of worker processes
  reload: false                 # Auto-reload on code changes
  cors:
    allow_origins: ["*"]        # CORS allowed origins
    allow_credentials: true
    allow_methods: ["*"]
    allow_headers: ["*"]

defaults:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 8096
  temperature: 1.0
  working_directory: "/tmp/agents"
  default_skills:
    - file_operations
    - bash_execution
  timeout: 300                  # Agent timeout in seconds
```

#### Server Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | `"0.0.0.0"` | Server bind address |
| `port` | integer | `8922` | Server port |
| `log_level` | string | `"INFO"` | Logging level |
| `workers` | integer | `4` | Number of worker processes |
| `reload` | boolean | `false` | Enable auto-reload |

#### Default Agent Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `model` | string | `"claude-3-5-sonnet-20241022"` | Default LLM model |
| `max_tokens` | integer | `8096` | Maximum tokens per response |
| `temperature` | float | `1.0` | Response randomness (0-2) |
| `working_directory` | string | `"/tmp/agents"` | Agent working directory |
| `default_skills` | list | `["file_operations", "bash_execution"]` | Default agent skills |
| `timeout` | integer | `300` | Default timeout (seconds) |

---

### 2. MCP Servers Configuration

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

#### Available MCP Servers

| Server | Description | Required Environment Variables |
|--------|-------------|-------------------------------|
| `filesystem` | File system operations | None |
| `github` | GitHub API operations | `GITHUB_TOKEN` |
| `git` | Git repository operations | None |
| `brave-search` | Brave web search | `BRAVE_API_KEY` |
| `postgres` | PostgreSQL database | `DATABASE_URL` |
| `sqlite` | SQLite database | None |
| `fetch` | HTTP requests | None |
| `puppeteer` | Browser automation | None |

#### MCP Server Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command` | string | - | Command to start server |
| `args` | list | `[]` | Command arguments |
| `env` | dict | `{}` | Environment variables |
| `description` | string | - | Server description |
| `enabled` | boolean | `false` | Enable/disable server |
| `auto_restart` | boolean | `false` | Auto-restart on failure |
| `timeout` | integer | `30` | Startup timeout (seconds) |

---

### 3. Voice Configuration

```yaml
voice:
  default_provider: "kokoro"     # kokoro, elevenlabs, deepgram
  fallback_provider: "deepgram"  # Fallback if primary fails
  auto_fallback: true

  # Kokoro TTS (Local, Free)
  kokoro:
    enabled: true
    default_voice: "af_bella"
    cache_enabled: true
    cache_dir: "/tmp/kokoro_cache"
    sample_rate: 24000
    phonemizer: "espeak"         # espeak or gruut

  # ElevenLabs (Cloud, Premium Quality)
  elevenlabs:
    enabled: true
    api_key: "${ELEVENLABS_API_KEY}"
    default_voice: "rachel"
    model: "eleven_multilingual_v2"
    output_format: "mp3_44100_128"
    stability: 0.5
    similarity_boost: 0.5
    style: 0.0
    use_speaker_boost: true

  # Deepgram (Cloud, Fast & Natural)
  deepgram:
    enabled: true
    api_key: "${DEEPGRAM_API_KEY}"
    default_voice: "asteria"
    language: "en"
    sample_rate: 24000
    encoding: "mp3"
```

#### Voice Providers

| Provider | Type | Cost | Quality | Latency |
|----------|------|------|---------|---------|
| `kokoro` | Local | Free | Good | Low |
| `elevenlabs` | Cloud | Paid | Excellent | Medium |
| `deepgram` | Cloud | Paid | Very Good | Low |

#### Kokoro Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Kokoro TTS |
| `default_voice` | string | `"af_bella"` | Default voice |
| `cache_enabled` | boolean | `true` | Enable caching |
| `cache_dir` | string | `"/tmp/kokoro_cache"` | Cache directory |
| `sample_rate` | integer | `24000` | Audio sample rate |
| `phonemizer` | string | `"espeak"` | Phonemizer (espeak/gruut) |

#### ElevenLabs Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable ElevenLabs |
| `api_key` | string | - | API key from env |
| `default_voice` | string | `"rachel"` | Default voice |
| `model` | string | `"eleven_multilingual_v2"` | TTS model |
| `output_format` | string | `"mp3_44100_128"` | Audio format |
| `stability` | float | `0.5` | Stability (0-1) |
| `similarity_boost` | float | `0.5` | Similarity (0-1) |
| `style` | float | `0.0` | Style enhancement (0-1) |
| `use_speaker_boost` | boolean | `true` | Speaker boost |

#### Deepgram Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable Deepgram |
| `api_key` | string | - | API key from env |
| `default_voice` | string | `"asteria"` | Default voice |
| `language` | string | `"en"` | Language code |
| `sample_rate` | integer | `24000` | Audio sample rate |
| `encoding` | string | `"mp3"` | Audio encoding |

---

### 4. Agent Limits

```yaml
limits:
  max_agents: 50
  max_conversation_length: 100
  max_subagents_per_agent: 10
  max_parallel_executions: 5
  max_workflow_steps: 50
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `max_agents` | integer | `50` | Maximum concurrent agents |
| `max_conversation_length` | integer | `100` | Max messages per conversation |
| `max_subagents_per_agent` | integer | `10` | Max sub-agents per parent |
| `max_parallel_executions` | integer | `5` | Max parallel agent executions |
| `max_workflow_steps` | integer | `50` | Max workflow steps |

---

### 5. WebSocket Configuration

```yaml
websocket:
  ping_interval: 30
  ping_timeout: 10
  max_connections_per_client: 5
  message_queue_size: 1000
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `ping_interval` | integer | `30` | Ping interval (seconds) |
| `ping_timeout` | integer | `10` | Ping timeout (seconds) |
| `max_connections_per_client` | integer | `5` | Max connections per client |
| `message_queue_size` | integer | `1000` | Message queue size |

---

### 6. Storage Configuration

```yaml
storage:
  agent_data_dir: "/tmp/agents/data"
  session_dir: "/tmp/agents/sessions"
  logs_dir: "/tmp/agents/logs"
  cleanup_after_hours: 24
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `agent_data_dir` | string | - | Agent data directory |
| `session_dir` | string | - | Session storage |
| `logs_dir` | string | - | Log file directory |
| `cleanup_after_hours` | integer | `24` | Cleanup interval (hours) |

---

## Configuration Loading

### Python API

```python
from hypr_voice.config import load_config

# Load main configuration
config = load_config("config.yaml")

# Access configuration values
server_host = config["server"]["host"]
server_port = config["server"]["port"]

# Load Whisper configuration
whisper_config = load_config("whisper/config.yaml")
```

### Environment Variable Substitution

Configuration files support environment variable substitution using the `${VAR_NAME}` syntax:

```yaml
api_key: "${API_KEY}"           # Required variable
api_key: "${API_KEY:-default}"  # With default
api_key: "${API_KEY:?error}"    # Required with error message
```

### Configuration Path Resolution

The system searches for configuration files in the following order:

1. `/home/mewtwo/Zykairotis/Hypr-Voice/config/hypr_voice/` (project config)
2. `~/.config/hypr-voice/` (user config)
3. `/etc/hypr-voice/` (system config)

---

## Validation and Troubleshooting

### Configuration Validation

```python
from hypr_voice.config import load_config
import yaml

try:
    config = load_config("config.yaml")
    print("Configuration loaded successfully")
except FileNotFoundError as e:
    print(f"Config file not found: {e}")
except yaml.YAMLError as e:
    print(f"Invalid YAML: {e}")
```

### Common Issues

#### Issue: Configuration file not found

**Error:**
```
FileNotFoundError: Configuration file not found: /path/to/config.yaml
```

**Solution:**
- Verify the file exists
- Check the configuration path
- Ensure proper permissions

#### Issue: Invalid YAML syntax

**Error:**
```
yaml.YAMLError: Unexpected character
```

**Solution:**
- Validate YAML syntax using online tools
- Check for proper indentation
- Ensure quotes are balanced

#### Issue: Environment variable not set

**Error:**
```
KeyError: 'API_KEY'
```

**Solution:**
- Set the environment variable
- Use default values in config: `${API_KEY:-default}`
- Check `.env` file

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```bash
export HYPR_VOICE_TRACE=1
export HYPR_VOICE_FLOW_TRACE=1
```

### Configuration Validation Script

```bash
# Validate all configuration files
python -m hypr_voice.tools.validate_config
```

---

## See Also

- [Environment Variables Reference](environment-variables.md)
- [Whisper Configuration](whisper-config.md)
- [Voice Configuration](voice-config.md)
- [Agent Configuration](agent-config.md)
