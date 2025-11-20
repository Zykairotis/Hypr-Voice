"""
MCP Server Loader and Manager
Handles dynamic loading, configuration, and communication with MCP servers
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Protocol
from dataclasses import dataclass
from pathlib import Path
import yaml
import subprocess
import os
import uuid
from abc import ABC, abstractmethod


# ============================================================================
# MCP PROTOCOL DEFINITIONS
# ============================================================================

@dataclass
class MCPToolDefinition:
    """MCP Tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str
    
    def to_claude_format(self) -> Dict:
        """Convert to Claude SDK tool format"""
        return {
            "name": f"{self.server_name}_{self.name}",
            "description": f"[MCP:{self.server_name}] {self.description}",
            "input_schema": self.input_schema
        }


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    env: Optional[Dict[str, str]] = None
    description: str = ""
    enabled: bool = True
    timeout: int = 30
    auto_restart: bool = True


class MCPProtocol:
    """Implementation of MCP protocol for communication"""
    
    def __init__(self, process: asyncio.subprocess.Process, server_name: str):
        self.process = process
        self.server_name = server_name
        self.logger = logging.getLogger(f"MCPProtocol-{server_name}")
        self.request_id = 0
        self._response_futures: Dict[int, asyncio.Future] = {}
        self._reader_task = None
    
    async def start(self):
        """Start the protocol handler"""
        self._reader_task = asyncio.create_task(self._read_responses())
    
    async def stop(self):
        """Stop the protocol handler"""
        if self._reader_task:
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
    
    async def _read_responses(self):
        """Read responses from the MCP server"""
        while True:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    response = json.loads(line.decode())
                    request_id = response.get("id")
                    
                    if request_id in self._response_futures:
                        self._response_futures[request_id].set_result(response)
                        del self._response_futures[request_id]
                    else:
                        # Handle notifications or events
                        await self._handle_notification(response)
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Invalid JSON from MCP server: {e}")
                    
            except Exception as e:
                self.logger.error(f"Error reading from MCP server: {e}")
                break
    
    async def _handle_notification(self, notification: Dict):
        """Handle notifications from MCP server"""
        method = notification.get("method")
        params = notification.get("params", {})
        
        self.logger.debug(f"Notification: {method} - {params}")
    
    async def send_request(self, method: str, params: Optional[Dict] = None) -> Any:
        """Send a JSON-RPC request to the MCP server"""
        self.request_id += 1
        request = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params or {}
        }
        
        # Create future for response
        future = asyncio.Future()
        self._response_futures[self.request_id] = future
        
        # Send request
        request_data = json.dumps(request).encode() + b'\n'
        self.process.stdin.write(request_data)
        await self.process.stdin.drain()
        
        # Wait for response with timeout
        try:
            response = await asyncio.wait_for(future, timeout=10)
            
            if "error" in response:
                raise Exception(f"MCP Error: {response['error']}")
            
            return response.get("result")
            
        except asyncio.TimeoutError:
            del self._response_futures[self.request_id]
            raise Exception(f"Request timeout for {method}")
    
    async def initialize(self) -> Dict:
        """Initialize the MCP server connection"""
        return await self.send_request("initialize", {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "tools": True,
                "resources": True,
                "prompts": True
            }
        })
    
    async def list_tools(self) -> List[Dict]:
        """List available tools from the MCP server"""
        result = await self.send_request("tools/list")
        return result.get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on the MCP server"""
        return await self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments
        })


# ============================================================================
# MCP SERVER INSTANCE
# ============================================================================

class MCPServerInstance:
    """Represents a running MCP server instance"""
    
    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.process: Optional[asyncio.subprocess.Process] = None
        self.protocol: Optional[MCPProtocol] = None
        self.tools: List[MCPToolDefinition] = []
        self.logger = logging.getLogger(f"MCPServer-{config.name}")
        self.status = "stopped"
        self._restart_count = 0
    
    async def start(self):
        """Start the MCP server"""
        try:
            # Prepare environment
            env = os.environ.copy()
            if self.config.env:
                env.update(self.config.env)
            
            # Start process
            self.process = await asyncio.create_subprocess_exec(
                self.config.command,
                *self.config.args,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env
            )
            
            self.protocol = MCPProtocol(self.process, self.config.name)
            await self.protocol.start()
            
            # Initialize connection
            init_result = await self.protocol.initialize()
            self.logger.info(f"MCP server '{self.config.name}' initialized: {init_result}")
            
            # Discover tools
            await self._discover_tools()
            
            self.status = "running"
            self.logger.info(f"MCP server '{self.config.name}' started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start MCP server '{self.config.name}': {e}")
            self.status = "error"
            raise
    
    async def stop(self):
        """Stop the MCP server"""
        if self.protocol:
            await self.protocol.stop()
        
        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.process.kill()
                await self.process.wait()
        
        self.status = "stopped"
        self.logger.info(f"MCP server '{self.config.name}' stopped")
    
    async def restart(self):
        """Restart the MCP server"""
        self._restart_count += 1
        self.logger.info(f"Restarting MCP server '{self.config.name}' (attempt {self._restart_count})")
        
        await self.stop()
        await asyncio.sleep(1)  # Brief pause before restart
        await self.start()
    
    async def _discover_tools(self):
        """Discover available tools from the MCP server"""
        try:
            tools_data = await self.protocol.list_tools()
            
            self.tools = []
            for tool_data in tools_data:
                tool = MCPToolDefinition(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=self.config.name
                )
                self.tools.append(tool)
            
            self.logger.info(f"Discovered {len(self.tools)} tools from '{self.config.name}'")
            
        except Exception as e:
            self.logger.error(f"Failed to discover tools: {e}")
    
    async def call_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on this MCP server"""
        if not self.protocol:
            raise Exception(f"MCP server '{self.config.name}' is not running")
        
        return await self.protocol.call_tool(tool_name, arguments)
    
    def get_tool_definitions(self) -> List[Dict]:
        """Get Claude-compatible tool definitions"""
        return [tool.to_claude_format() for tool in self.tools]


# ============================================================================
# MCP CONFIGURATION LOADER
# ============================================================================

class MCPConfigLoader:
    """Load MCP server configurations from various sources"""
    
    @staticmethod
    def load_from_yaml(config_path: str) -> Dict[str, MCPServerConfig]:
        """Load MCP configurations from YAML file"""
        configs = {}
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        mcp_servers = data.get("mcp_servers", {})
        
        for name, server_data in mcp_servers.items():
            if not server_data.get("enabled", True):
                continue
            
            config = MCPServerConfig(
                name=name,
                command=server_data["command"],
                args=server_data.get("args", []),
                env=MCPConfigLoader._expand_env_vars(server_data.get("env", {})),
                description=server_data.get("description", ""),
                enabled=server_data.get("enabled", True),
                timeout=server_data.get("timeout", 30),
                auto_restart=server_data.get("auto_restart", True)
            )
            
            configs[name] = config
        
        return configs
    
    @staticmethod
    def _expand_env_vars(env_dict: Dict[str, str]) -> Dict[str, str]:
        """Expand environment variables in configuration"""
        import re
        
        expanded = {}
        pattern = r'\$\{([^}]+)\}'
        
        for key, value in env_dict.items():
            def replacer(match):
                var_name = match.group(1)
                return os.environ.get(var_name, match.group(0))
            
            expanded[key] = re.sub(pattern, replacer, str(value))
        
        return expanded
    
    @staticmethod
    def get_presets() -> Dict[str, MCPServerConfig]:
        """Get preset MCP server configurations"""
        return {
            "filesystem": MCPServerConfig(
                name="filesystem",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/"],
                description="File system operations MCP server"
            ),
            "github": MCPServerConfig(
                name="github",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")},
                description="GitHub operations MCP server"
            ),
            "git": MCPServerConfig(
                name="git",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-git"],
                description="Git operations MCP server"
            ),
            "brave-search": MCPServerConfig(
                name="brave-search",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-brave-search"],
                env={"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")},
                description="Brave web search MCP server"
            ),
            "postgres": MCPServerConfig(
                name="postgres",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-postgres"],
                env={"DATABASE_URL": os.environ.get("DATABASE_URL", "")},
                description="PostgreSQL database MCP server"
            ),
            "sqlite": MCPServerConfig(
                name="sqlite",
                command="npx",
                args=["-y", "@modelcontextprotocol/server-sqlite", "database.db"],
                description="SQLite database MCP server"
            )
        }


# ============================================================================
# ENHANCED MCP MANAGER
# ============================================================================

class EnhancedMCPManager:
    """Enhanced MCP Manager with dynamic loading and management"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.servers: Dict[str, MCPServerInstance] = {}
        self.config_path = config_path
        self.logger = logging.getLogger("EnhancedMCPManager")
        self.presets = MCPConfigLoader.get_presets()
    
    async def load_from_config(self, config_path: Optional[str] = None):
        """Load and start MCP servers from configuration file"""
        config_path = config_path or self.config_path
        
        if not config_path or not Path(config_path).exists():
            self.logger.warning(f"Config file not found: {config_path}")
            return
        
        try:
            configs = MCPConfigLoader.load_from_yaml(config_path)
            
            for name, config in configs.items():
                await self.add_server(config)
                
        except Exception as e:
            self.logger.error(f"Failed to load MCP configuration: {e}")
    
    async def add_server(self, config: MCPServerConfig):
        """Add and start a new MCP server"""
        if config.name in self.servers:
            self.logger.warning(f"MCP server '{config.name}' already exists")
            return
        
        try:
            server = MCPServerInstance(config)
            await server.start()
            self.servers[config.name] = server
            
            self.logger.info(f"Added MCP server: {config.name}")
            
        except Exception as e:
            self.logger.error(f"Failed to add MCP server '{config.name}': {e}")
    
    async def add_preset_server(self, preset_name: str):
        """Add a preset MCP server"""
        if preset_name not in self.presets:
            raise ValueError(f"Unknown preset: {preset_name}")
        
        await self.add_server(self.presets[preset_name])
    
    async def remove_server(self, name: str):
        """Remove and stop an MCP server"""
        if name in self.servers:
            await self.servers[name].stop()
            del self.servers[name]
            self.logger.info(f"Removed MCP server: {name}")
    
    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict) -> Any:
        """Call a tool on a specific MCP server"""
        if server_name not in self.servers:
            raise ValueError(f"MCP server '{server_name}' not found")
        
        return await self.servers[server_name].call_tool(tool_name, arguments)
    
    def get_all_tools(self) -> List[MCPToolDefinition]:
        """Get all tools from all running MCP servers"""
        all_tools = []
        for server in self.servers.values():
            all_tools.extend(server.tools)
        return all_tools
    
    def get_tool_definitions(self) -> List[Dict]:
        """Get all Claude-compatible tool definitions"""
        definitions = []
        for server in self.servers.values():
            definitions.extend(server.get_tool_definitions())
        return definitions
    
    async def restart_server(self, name: str):
        """Restart a specific MCP server"""
        if name in self.servers:
            await self.servers[name].restart()
    
    async def shutdown(self):
        """Shutdown all MCP servers"""
        for server in self.servers.values():
            await server.stop()
        
        self.servers.clear()
        self.logger.info("All MCP servers shut down")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all MCP servers"""
        return {
            name: {
                "status": server.status,
                "tools_count": len(server.tools),
                "restart_count": server._restart_count
            }
            for name, server in self.servers.items()
        }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_basic_mcp():
    """Example of basic MCP server usage"""
    manager = EnhancedMCPManager()
    
    # Add preset servers
    await manager.add_preset_server("filesystem")
    await manager.add_preset_server("git")
    
    # Get all tools
    tools = manager.get_all_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
    
    # Call a tool
    result = await manager.call_tool(
        "filesystem",
        "read_file",
        {"path": "/etc/hosts"}
    )
    print(f"Tool result: {result}")
    
    # Shutdown
    await manager.shutdown()


async def example_config_loading():
    """Example of loading MCP servers from config"""
    # Create sample config
    config_data = {
        "mcp_servers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home"],
                "description": "File system MCP server",
                "enabled": True
            },
            "github": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "env": {
                    "GITHUB_TOKEN": "${GITHUB_TOKEN}"
                },
                "description": "GitHub MCP server",
                "enabled": True
            }
        }
    }
    
    # Save config
    config_path = "mcp_config.yaml"
    with open(config_path, 'w') as f:
        yaml.dump(config_data, f)
    
    # Load from config
    manager = EnhancedMCPManager()
    await manager.load_from_config(config_path)
    
    # Check status
    status = manager.get_status()
    print(f"MCP servers status: {status}")
    
    # Cleanup
    await manager.shutdown()
    Path(config_path).unlink()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_basic_mcp())
