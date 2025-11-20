# 🚀 Multi-Agent Orchestration System

A production-ready, real-time multi-agent orchestration system with Claude SDK integration, WebSocket streaming, MCP servers, hierarchical agents, and voice synthesis capabilities.

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start both agents
./scripts/start_all.sh

# Or start individually
./scripts/start_claude_sdk.sh  # Claude SDK on port 8922
./scripts/start_litellm.sh     # LiteLLM on port 8001

# Test the agents
python test_client.py
```

## 📁 Project Structure

```
Agent/
├── claude-sdk/          # Claude Computer Use SDK implementation
│   ├── __init__.py
│   ├── orchestrator.py  # Main Claude orchestrator with computer use
│   └── ...
├── litellm-agent/       # LiteLLM simple agent implementation  
│   ├── __init__.py
│   ├── agent.py         # Simple LLM agent with tools
│   ├── orchestrator.py  # Agent orchestrator
│   └── tools.py         # Tool registry
├── config/              # Configuration files
│   ├── claude-sdk.yaml  # Claude SDK config
│   └── litellm.yaml     # LiteLLM config
├── scripts/             # Utility scripts
│   ├── start_all.sh     # Start both agents
│   ├── stop_all.sh      # Stop all agents
│   └── ...
├── workspaces/          # Agent working directories
├── logs/                # Log files
├── test_client.py       # Interactive test client
└── requirements.txt     # Python dependencies
```

## 🎯 Features

### Claude Computer Use SDK Agent
- **Computer Control**: Screenshot, click, type, and keyboard control
- **Local Claude Integration**: Uses claude-computer-use instead of API
- **File Operations**: Read, write, list, and delete files
- **Bash Execution**: Run shell commands
- **Real-time Events**: WebSocket support for live updates
- **FastAPI Server**: RESTful API on port 8922

### LiteLLM Simple Agent
- **Multi-Model Support**: Works with Claude, GPT-4, Gemini, and local models
- **Tool System**: Extensible tool registry for custom functions
- **File Operations**: Complete file management capabilities
- **Command Execution**: Shell and Python code execution
- **Session Management**: Save and load conversation sessions
- **Flexible Configuration**: Easy model switching
- **FastAPI Server**: RESTful API on port 8001

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Hypr-Voice virtual environment activated
- (Optional) Claude Computer Use installed
- (Optional) API keys for LLM providers

### Setup

1. **Activate Hypr-Voice virtual environment**:
```bash
source /home/mewtwo/Zykairotis/Hypr-Voice/.venv/bin/activate
```

2. **Install dependencies**:
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice
pip install -r requirements/hypr_voice.txt
```

3. **Configure API keys** (optional):
```bash
# For Claude SDK (if using actual API)
export ANTHROPIC_API_KEY="your-key"

# For LiteLLM (choose one or more)
export ANTHROPIC_API_KEY="your-anthropic-key"
export OPENAI_API_KEY="your-openai-key"
export GOOGLE_API_KEY="your-google-key"
```

## 🚦 Usage

### Starting the Agents

**Start both agents**:
```bash
./scripts/start_all.sh
```

**Start individually**:
```bash
# Claude SDK Agent
./scripts/start_claude_sdk.sh

# LiteLLM Agent
./scripts/start_litellm.sh
```

**Stop all agents**:
```bash
./scripts/stop_all.sh
```

### API Endpoints

#### Claude SDK Agent (Port 8922)

- `POST /agents/create` - Create a new Claude agent
- `POST /agents/{agent_id}/instruct` - Send instruction to agent
- `GET /agents/list` - List all agents
- `GET /agents/{agent_id}/status` - Get agent status

#### LiteLLM Agent (Port 8001)

- `POST /agents/create` - Create a new LiteLLM agent
- `POST /agents/{agent_id}/chat` - Chat with agent
- `GET /agents/list` - List all agents
- `GET /agents/{agent_id}/info` - Get agent information
- `GET /agents/{agent_id}/history` - Get conversation history
- `POST /agents/{agent_id}/clear` - Clear conversation history
- `POST /agents/{agent_id}/save` - Save session
- `POST /agents/{agent_id}/load` - Load session
- `DELETE /agents/{agent_id}` - Delete agent

### Interactive Testing

Run the test client for interactive testing:

```bash
# Interactive mode (choose agent type)
python test_client.py

# Test specific agent
python test_client.py claude    # Test Claude SDK
python test_client.py litellm   # Test LiteLLM
python test_client.py both      # Test both agents
```

## 💻 Programming Examples

### Claude SDK Agent

```python
import aiohttp
import asyncio

async def use_claude_agent():
    async with aiohttp.ClientSession() as session:
        # Create agent
        create_data = {
            "name": "My Claude Agent",
            "working_directory": "/tmp/claude_workspace",
            "use_computer": True
        }
        
        async with session.post("http://localhost:8922/agents/create", 
                               json=create_data) as resp:
            result = await resp.json()
            agent_id = result["agent_id"]
        
        # Send instruction
        instruct_data = {
            "instruction": "Take a screenshot and describe what you see"
        }
        
        async with session.post(f"http://localhost:8922/agents/{agent_id}/instruct",
                               params=instruct_data) as resp:
            result = await resp.json()
            print(result)

asyncio.run(use_claude_agent())
```

### LiteLLM Agent

```python
import aiohttp
import asyncio

async def use_litellm_agent():
    async with aiohttp.ClientSession() as session:
        # Create agent
        create_data = {
            "name": "My LiteLLM Agent",
            "working_directory": "/tmp/litellm_workspace",
            "model": "claude-3-5-sonnet-20241022",
            "temperature": 0.7,
            "system_prompt": "You are a helpful coding assistant."
        }
        
        async with session.post("http://localhost:8001/agents/create",
                               json=create_data) as resp:
            result = await resp.json()
            agent_id = result["agent_id"]
        
        # Chat with tools
        chat_data = {
            "message": "Create a Python script that prints Fibonacci numbers",
            "use_tools": True
        }
        
        async with session.post(f"http://localhost:8001/agents/{agent_id}/chat",
                               json=chat_data) as resp:
            result = await resp.json()
            print(result["content"])
            
            # Check if tools were used
            if result.get("tool_calls"):
                for tool in result["tool_calls"]:
                    print(f"Tool used: {tool['tool']}")

asyncio.run(use_litellm_agent())
```

## 🔧 Configuration

### Claude SDK Configuration (`config/claude-sdk.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8922
  
defaults:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 8096
  use_computer: true
  
computer_use:
  headless: true
  screenshot_enabled: true
  click_enabled: true
```

### LiteLLM Configuration (`config/litellm.yaml`)

```yaml
server:
  host: "0.0.0.0"
  port: 8001
  
models:
  default: "claude-3-5-sonnet-20241022"
  
providers:
  anthropic:
    models: ["claude-3-5-sonnet-20241022"]
  openai:
    models: ["gpt-4", "gpt-3.5-turbo"]
  google:
    models: ["gemini-pro"]
```

## 📊 Available Tools

### Claude SDK Tools
- **screenshot**: Take a screenshot
- **click**: Click at coordinates
- **type_text**: Type text via keyboard
- **key_press**: Press keyboard keys
- **file_operations**: File management
- **bash_execution**: Run shell commands

### LiteLLM Tools
- **read_file**: Read file contents
- **write_file**: Write to files
- **list_files**: List directory contents
- **run_command**: Execute shell commands
- **run_python**: Execute Python code

## 🔍 Monitoring

### Logs
- Claude SDK: `logs/claude-sdk.log`
- LiteLLM: `logs/litellm.log`

### API Documentation
- Claude SDK: http://localhost:8922/docs
- LiteLLM: http://localhost:8001/docs

### Health Check
- Claude SDK: http://localhost:8922/agents/list
- LiteLLM: http://localhost:8001/health

## 🤝 Integration with Hypr-Voice

Both agent systems are designed to integrate with the Hypr-Voice project:

1. **Voice Commands**: Agents can process voice-transcribed commands
2. **Audio Generation**: Integration with Kokoro TTS for voice output
3. **File Management**: Manage audio files and transcriptions
4. **Workflow Automation**: Create complex voice-driven workflows

Example integration:
```python
# Process voice command with agent
voice_command = "Create a summary of today's recordings"
response = await agent.chat(voice_command, use_tools=True)

# Convert response to speech
from kokoro_integration import synthesize_speech
audio_file = await synthesize_speech(response["content"])
```

## 🐛 Troubleshooting

### Agent won't start
- Check virtual environment is activated
- Verify dependencies are installed: `pip install -r requirements.txt`
- Check logs in `logs/` directory

### API connection refused
- Ensure agent is running: `ps aux | grep uvicorn`
- Check port availability: `lsof -i:8922` or `lsof -i:8001`
- Verify firewall settings

### Mock mode (no API keys)
- Agents will run in mock mode without API keys
- Set appropriate environment variables for full functionality

## 📝 License

Part of the Hypr-Voice project. See main project LICENSE.

## 🚧 Future Enhancements

- [ ] WebSocket support for LiteLLM agent
- [ ] Multi-agent collaboration
- [ ] Voice synthesis integration
- [ ] Persistent agent state
- [ ] Agent templates and presets
- [ ] Advanced tool chaining
- [ ] Monitoring dashboard

## 📚 References

- [Claude Computer Use Documentation](https://docs.anthropic.com/claude/docs/computer-use)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hypr-Voice Project](../../../README.md)
