# MCP (Model Context Protocol) Integration Guide

## Overview

Hypr-Voice integrates with MCP (Model Context Protocol) servers to extend functionality with external tools and resources. MCP provides a standardized way for AI assistants to interact with various services like filesystems, databases, APIs, and more.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              MCP Integration Layer                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         EnhancedMCPManager                           │   │
│  │  - Dynamic Server Loading                            │   │
│  │  - Tool Discovery                                    │   │
│  │  - Request Routing                                   │   │
│  │  - Error Handling                                    │   │
│  └─────────────┬────────────────────────────────────────┘   │
│                │                                             │
│         ┌──────┴──────┐                                     │
│         │  MCP Protocol│                                     │
│         │  (JSON-RPC)  │                                     │
│         └──────┬──────┘                                     │
│                │                                             │
│  ┌─────────────┴────────────────────────────────────────┐   │
│  │              MCP Servers                              │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │  │Filesystem│ │  GitHub  │ │  Git     │ │             │   │
│  │  └──────────┘ └──────────┘ └──────────┘             │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │   │
│  │  │PostgreSQL│ │  SQLite  │ │  Brave   │ │             │   │
│  │  └──────────┘ └──────────┘ └──────────┘             │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### MCP Configuration File

Create `mcp_config.yaml`:

```yaml
mcp_servers:
  filesystem:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-filesystem"
      - /home/user
    description: File system operations
    enabled: true
    timeout: 30

  github:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-github"
    env:
      GITHUB_TOKEN: ${GITHUB_TOKEN}
    description: GitHub operations
    enabled: true
    timeout: 30

  git:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-git"
    description: Git operations
    enabled: true
    timeout: 30

  brave-search:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-brave-search"
    env:
      BRAVE_API_KEY: ${BRAVE_API_KEY}
    description: Web search
    enabled: true
    timeout: 30

  postgres:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-postgres"
    env:
      DATABASE_URL: ${DATABASE_URL}
    description: PostgreSQL database
    enabled: false  # Disabled by default
    timeout: 30

  sqlite:
    command: npx
    args:
      - -y
      - "@modelcontextprotocol/server-sqlite"
      - database.db
    description: SQLite database
    enabled: false
    timeout: 30
```

### Environment Variables

```bash
# GitHub integration
GITHUB_TOKEN=your_github_token_here

# Brave Search
BRAVE_API_KEY=your_brave_api_key_here

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Custom MCP servers can have their own variables
```

## Usage

### Basic MCP Manager Setup

```python
from hypr_voice.services.mcp.mcp_loader import EnhancedMCPManager

async def basic_mcp_setup():
    # Create manager
    manager = EnhancedMCPManager()

    # Load from config file
    await manager.load_from_config("mcp_config.yaml")

    # Check status
    status = manager.get_status()
    print(f"Running servers: {list(status.keys())}")

    # Shutdown when done
    await manager.shutdown()
```

### Adding Preset Servers

```python
async def preset_servers_example():
    manager = EnhancedMCPManager()

    # Add preset servers
    await manager.add_preset_server("filesystem")
    await manager.add_preset_server("git")
    await manager.add_preset_server("github")

    # Get all tools
    tools = manager.get_all_tools()
    print(f"Available tools: {[t.name for t in tools]}")

    await manager.shutdown()
```

### Calling MCP Tools

```python
async def call_tool_example():
    manager = EnhancedMCPManager()

    # Add servers
    await manager.add_preset_server("filesystem")
    await manager.add_preset_server("brave-search")

    # Call filesystem tool
    result = await manager.call_tool(
        "filesystem",
        "read_file",
        {"path": "/etc/hostname"}
    )
    print(f"Hostname: {result}")

    # Call search tool
    result = await manager.call_tool(
        "brave-search",
        "search",
        {"query": "Python async await"}
    )
    print(f"Search results: {result}")

    await manager.shutdown()
```

### Dynamic Server Management

```python
from hypr_voice.services.mcp.mcp_loader import MCPServerConfig

async def dynamic_servers_example():
    manager = EnhancedMCPManager()

    # Add custom server
    custom_config = MCPServerConfig(
        name="my-server",
        command="python",
        args=["-m", "my_mcp_server"],
        env={"API_KEY": "secret"},
        description="My custom MCP server",
        enabled=True,
        timeout=60,
        auto_restart=True
    )

    await manager.add_server(custom_config)

    # Use server
    result = await manager.call_tool(
        "my-server",
        "my_tool",
        {"param": "value"}
    )

    # Restart server if needed
    await manager.restart_server("my-server")

    # Remove server
    await manager.remove_server("my-server")

    await manager.shutdown()
```

### Getting Tool Definitions

```python
async def tool_definitions_example():
    manager = EnhancedMCPManager()

    await manager.add_preset_server("filesystem")
    await manager.add_preset_server("github")

    # Get Claude-compatible tool definitions
    definitions = manager.get_tool_definitions()

    for tool_def in definitions:
        print(f"Tool: {tool_def['name']}")
        print(f"Description: {tool_def['description']}")
        print(f"Schema: {tool_def['input_schema']}")
        print()

    # Use with Claude SDK
    claude_tools = [
        {
            "name": tool_def['name'],
            "description": tool_def['description'],
            "input_schema": tool_def['input_schema']
        }
        for tool_def in definitions
    ]

    await manager.shutdown()
```

## Available MCP Servers

### Filesystem Server

**Description**: Read, write, and manage files

**Usage**:
```python
await manager.add_preset_server("filesystem")

# Read file
result = await manager.call_tool(
    "filesystem",
    "read_file",
    {"path": "/path/to/file.txt"}
)

# Write file
result = await manager.call_tool(
    "filesystem",
    "write_file",
    {
        "path": "/path/to/file.txt",
        "content": "Hello, world!"
    }
)

# List directory
result = await manager.call_tool(
    "filesystem",
    "list_directory",
    {"path": "/path/to/dir"}
)
```

### GitHub Server

**Description**: Interact with GitHub repositories

**Requirements**: `GITHUB_TOKEN` environment variable

**Usage**:
```python
await manager.add_preset_server("github")

# List repositories
result = await manager.call_tool(
    "github",
    "list_repositories",
    {"owner": "username"}
)

# Create issue
result = await manager.call_tool(
    "github",
    "create_issue",
    {
        "owner": "username",
        "repo": "repository",
        "title": "Issue title",
        "body": "Issue description"
    }
)
```

### Git Server

**Description**: Git operations

**Usage**:
```python
await manager.add_preset_server("git")

# Get status
result = await manager.call_tool(
    "git",
    "status",
    {"path": "/path/to/repo"}
)

# Create commit
result = await manager.call_tool(
    "git",
    "commit",
    {
        "path": "/path/to/repo",
        "message": "Commit message"
    }
)
```

### Brave Search Server

**Description**: Web search using Brave Search API

**Requirements**: `BRAVE_API_KEY` environment variable

**Usage**:
```python
await manager.add_preset_server("brave-search")

# Search web
result = await manager.call_tool(
    "brave-search",
    "search",
    {"query": "Python async programming"}
)
```

### PostgreSQL Server

**Description**: PostgreSQL database operations

**Requirements**: `DATABASE_URL` environment variable

**Usage**:
```python
# Enable in config
postgres_config = MCPServerConfig(
    name="postgres",
    command="npx",
    args=["-y", "@modelcontextprotocol/server-postgres"],
    env={"DATABASE_URL": os.getenv("DATABASE_URL")},
    enabled=True
)

await manager.add_server(postgres_config)

# Query database
result = await manager.call_tool(
    "postgres",
    "query",
    {"sql": "SELECT * FROM users LIMIT 10"}
)
```

### SQLite Server

**Description**: SQLite database operations

**Usage**:
```python
await manager.add_preset_server("sqlite")

# Query database
result = await manager.call_tool(
    "sqlite",
    "query",
    {
        "database": "mydb.db",
        "sql": "SELECT * FROM users"
    }
)
```

## MCP Protocol Implementation

### JSON-RPC Communication

MCP uses JSON-RPC 2.0 protocol:

```python
# Request format
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "tool_name",
        "arguments": {...}
    }
}

# Response format
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {...}
}
```

### MCP Operations

**Initialize**:
```python
await protocol.initialize({
    "protocolVersion": "0.1.0",
    "capabilities": {
        "tools": True,
        "resources": True,
        "prompts": True
    }
})
```

**List Tools**:
```python
tools = await protocol.list_tools()
```

**Call Tool**:
```python
result = await protocol.call_tool(
    "tool_name",
    {"arg1": "value1", "arg2": "value2"}
)
```

## Advanced Usage

### Custom MCP Server

```python
import asyncio
import json
from sys import stdin, stdout

async def my_custom_mcp_server():
    """Simple MCP server implementation"""

    async def handle_request(request):
        method = request.get("method")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {"tools": True}
                }
            }

        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "my_tool",
                            "description": "My custom tool",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "input": {"type": "string"}
                                },
                                "required": ["input"]
                            }
                        }
                    ]
                }
            }

        elif method == "tools/call":
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if tool_name == "my_tool":
                result = process_tool(arguments)
                return {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }

    async def main():
        while True:
            line = await asyncio.get_event_loop().run_in_executor(
                None, stdin.readline
            )
            if not line:
                break

            request = json.loads(line)
            response = await handle_request(request)
            stdout.write(json.dumps(response) + "\n")
            stdout.flush()

    await main()
```

### Error Handling

```python
async def error_handling_example():
    manager = EnhancedMCPManager()

    try:
        await manager.add_preset_server("filesystem")
        result = await manager.call_tool(
            "filesystem",
            "read_file",
            {"path": "/nonexistent/file.txt"}
        )
    except Exception as e:
        print(f"Error: {e}")

        # Check server status
        status = manager.get_status()
        if status.get("filesystem", {}).get("status") == "error":
            # Restart server
            await manager.restart_server("filesystem")

    await manager.shutdown()
```

### Tool Discovery

```python
async def discover_tools_example():
    manager = EnhancedMCPManager()

    await manager.load_from_config("mcp_config.yaml")

    # Get all tools from all servers
    all_tools = manager.get_all_tools()

    # Group by server
    tools_by_server = {}
    for tool in all_tools:
        server = tool.server_name
        if server not in tools_by_server:
            tools_by_server[server] = []
        tools_by_server[server].append(tool.name)

    # Print discovered tools
    for server, tools in tools_by_server.items():
        print(f"{server}:")
        for tool in tools:
            print(f"  - {tool}")

    await manager.shutdown()
```

## Integration Examples

### With Claude AI

```python
async def claude_with_mcp():
    from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent
    from hypr_voice.services.mcp.mcp_loader import EnhancedMCPManager

    # Setup MCP
    mcp_manager = EnhancedMCPManager()
    await mcp_manager.add_preset_server("filesystem")
    await mcp_manager.add_preset_server("github")

    # Get tool definitions
    tool_definitions = mcp_manager.get_tool_definitions()

    # Setup Claude with MCP tools
    agent = ClaudeTTSAgent(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        system_prompt="You have access to filesystem and GitHub tools"
    )
    await agent.connect()

    # Use tools through Claude
    result = await agent.chat(
        "Read the README.md file and summarize it",
        # Tool definitions would be passed here
    )

    await agent.close()
    await mcp_manager.shutdown()
```

### With Voice Assistant

```python
async def voice_assistant_with_mcp():
    from hypr_voice.services.wispr_flow_direct import WisprFlowDirect
    from hypr_voice.services.mcp.mcp_loader import EnhancedMCPManager

    # Setup MCP for web search
    mcp_manager = EnhancedMCPManager()
    await mcp_manager.add_preset_server("brave-search")

    # Transcribe voice input
    wispr = WisprFlowDirect()
    await wispr.connect()

    audio_path = "user_query.wav"
    transcription = await wispr.transcribe(audio_path)

    # Use MCP to search
    search_result = await mcp_manager.call_tool(
        "brave-search",
        "search",
        {"query": transcription['text']}
    )

    # Generate response from search results
    response_text = generate_response_from_search(search_result)

    # TTS response
    from hypr_voice.services.voice import UniversalTTS, TTSConfig, TTSProvider
    tts = UniversalTTS(TTSConfig(provider=TTSProvider.KOKORO))
    result = await tts.speak(response_text)

    await wispr.close()
    await mcp_manager.shutdown()
```

## Troubleshooting

### Server Not Starting

**Error**: `Failed to start MCP server`

**Solution**:
```bash
# Check if npx is available
which npx

# Test MCP server manually
npx -y @modelcontextprotocol/server-filesystem /home

# Check command syntax in config
```

### Tool Not Found

**Error**: `Tool not found on server`

**Solution**:
```python
# List available tools
tools = manager.get_all_tools()
for tool in tools:
    print(f"{tool.server_name}.{tool.name}")

# Check server status
status = manager.get_status()
print(status)
```

### Authentication Failed

**Error**: `Authentication failed`

**Solution**:
```bash
# Check environment variables
echo $GITHUB_TOKEN
echo $BRAVE_API_KEY

# Set in config with proper expansion
env:
  GITHUB_TOKEN: ${GITHUB_TOKEN}
```

### Connection Timeout

**Error**: `Request timeout for tool`

**Solution**:
```python
config = MCPServerConfig(
    name="my-server",
    command="...",
    args=[...],
    timeout=60  # Increase timeout
)
```

## Best Practices

### 1. Use Environment Variables

```yaml
env:
  API_KEY: ${API_KEY}  # Expands from environment
```

### 2. Enable/Disable Servers

```yaml
mcp_servers:
  filesystem:
    enabled: true  # Always on
  postgres:
    enabled: false  # Off by default
```

### 3. Set Appropriate Timeouts

```python
config = MCPServerConfig(
    name="slow-server",
    timeout=120  # 2 minutes for slow operations
)
```

### 4. Monitor Server Health

```python
status = manager.get_status()

for server_name, server_status in status.items():
    if server_status['status'] == 'error':
        logger.error(f"Server {server_name} has errors")
        # Restart if needed
        await manager.restart_server(server_name)
```

### 5. Handle Auto-Restart

```python
config = MCPServerConfig(
    name="critical-server",
    command="...",
    args=[...],
    auto_restart=True  # Auto-restart on failure
)
```

## API Reference

### EnhancedMCPManager

**Constructor**:
- `config_path (str, optional)`: Path to MCP config file

**Methods**:
- `async load_from_config(config_path)`: Load servers from YAML
- `async add_server(config)`: Add server dynamically
- `async add_preset_server(preset_name)`: Add preset server
- `async remove_server(name)`: Remove and stop server
- `async call_tool(server_name, tool_name, arguments)`: Call tool
- `async restart_server(name)`: Restart server
- `async shutdown()`: Shutdown all servers
- `get_all_tools()`: Get all tools from all servers
- `get_tool_definitions()`: Get Claude-compatible definitions
- `get_status()`: Get status of all servers

### MCPServerConfig

**Constructor Parameters**:
- `name (str)`: Server name
- `command (str)`: Command to run
- `args (List[str])`: Command arguments
- `env (Dict[str, str], optional)`: Environment variables
- `description (str)`: Server description
- `enabled (bool)`: Enabled status (default: True)
- `timeout (int)`: Request timeout in seconds (default: 30)
- `auto_restart (bool)`: Auto-restart on failure (default: True)

### MCPConfigLoader

**Static Methods**:
- `load_from_yaml(config_path)`: Load from YAML file
- `get_presets()`: Get preset server configurations

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [Bot Integrations](./bot-integrations.md)
- [Architecture Overview](./ARCHITECTURE.md)
