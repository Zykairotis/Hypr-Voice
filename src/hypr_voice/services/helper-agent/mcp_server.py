"""
Model Context Protocol (MCP) Server Implementation

This module implements the MCP protocol for tool registration, function calling,
and session management, enabling structured communication with LLM providers that
support function calling.
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import yaml

logger = logging.getLogger(__name__)


class MCPTool:
    """Represents an MCP-compatible tool."""
    
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: Callable,
        returns: Optional[Dict[str, Any]] = None,
        category: str = "general",
        enabled: bool = True
    ):
        """
        Initialize MCP tool.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            func: Tool function
            returns: JSON schema for return value
            category: Tool category
            enabled: Whether tool is enabled
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.func = func
        self.returns = returns
        self.category = category
        self.enabled = enabled
        self.call_count = 0
        self.error_count = 0
        self.total_execution_time = 0.0
    
    def to_openai_function(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
    
    def to_anthropic_tool(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters
        }
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute tool with given arguments.
        
        Returns:
            Execution result
        """
        start_time = datetime.now()
        self.call_count += 1
        
        try:
            # Execute function
            if asyncio.iscoroutinefunction(self.func):
                result = await self.func(**kwargs)
            else:
                result = self.func(**kwargs)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            self.total_execution_time += execution_time
            
            return {
                "success": True,
                "result": result,
                "execution_time": execution_time,
                "tool_name": self.name
            }
            
        except Exception as e:
            self.error_count += 1
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(f"Tool execution error ({self.name}): {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "tool_name": self.name
            }


class MCPSession:
    """Represents an MCP session with state and history."""
    
    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize MCP session.
        
        Args:
            session_id: Session ID (generated if not provided)
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.created_at = datetime.now()
        self.last_activity = datetime.now()
        self.tool_calls = []
        self.context = {}
        self.is_active = True
    
    def add_tool_call(self, tool_name: str, args: Dict[str, Any], result: Dict[str, Any]):
        """Record a tool call in session history."""
        self.tool_calls.append({
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "args": args,
            "result": result
        })
        self.last_activity = datetime.now()
    
    def set_context(self, key: str, value: Any):
        """Set session context value."""
        self.context[key] = value
        self.last_activity = datetime.now()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get session context value."""
        return self.context.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary."""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "tool_calls_count": len(self.tool_calls),
            "context_keys": list(self.context.keys()),
            "is_active": self.is_active
        }


class MCPServer:
    """
    MCP (Model Context Protocol) Server implementation.
    
    Manages tool registration, function calling, and session management
    for structured LLM interactions.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize MCP server.
        
        Args:
            config_path: Path to mcp_tools.yaml configuration
        """
        self.config_path = config_path or Path(__file__).parent / "config" / "mcp_tools.yaml"
        self.config = self._load_config()
        
        self.tools: Dict[str, MCPTool] = {}
        self.sessions: Dict[str, MCPSession] = {}
        self.tool_categories: Dict[str, List[str]] = {}
        
        # Global settings
        self.enabled = self.config.get("mcp", {}).get("enabled", True)
        self.max_parallel_tools = self.config.get("mcp", {}).get("max_parallel_tools", 5)
        self.tool_timeout = self.config.get("mcp", {}).get("tool_timeout", 30)
        
        logger.info("MCP server initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning(f"MCP config not found: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load MCP config: {e}")
            return {}
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        func: Callable,
        returns: Optional[Dict[str, Any]] = None,
        category: str = "general",
        enabled: bool = True
    ):
        """
        Register a tool with the MCP server.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            func: Tool function
            returns: JSON schema for return value
            category: Tool category
            enabled: Whether tool is enabled
        """
        tool = MCPTool(
            name=name,
            description=description,
            parameters=parameters,
            func=func,
            returns=returns,
            category=category,
            enabled=enabled
        )
        
        self.tools[name] = tool
        
        # Update category mapping
        if category not in self.tool_categories:
            self.tool_categories[category] = []
        self.tool_categories[category].append(name)
        
        logger.info(f"Registered MCP tool: {name} (category: {category})")
    
    def register_from_config(self):
        """Register tools from configuration file."""
        tools_config = self.config.get("tools", {})
        
        for tool_name, tool_data in tools_config.items():
            if not tool_data.get("enabled", True):
                continue
            
            # Note: Function implementations need to be provided separately
            # This just registers the schema
            logger.info(f"Tool schema loaded from config: {tool_name}")
    
    def unregister_tool(self, name: str):
        """Unregister a tool."""
        if name in self.tools:
            tool = self.tools[name]
            del self.tools[name]
            
            # Update category mapping
            if tool.category in self.tool_categories:
                self.tool_categories[tool.category].remove(name)
            
            logger.info(f"Unregistered MCP tool: {name}")
    
    def get_tool(self, name: str) -> Optional[MCPTool]:
        """Get tool by name."""
        return self.tools.get(name)
    
    def list_tools(
        self,
        category: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List available tools.
        
        Args:
            category: Filter by category
            enabled_only: Only return enabled tools
            
        Returns:
            List of tool information
        """
        tools = self.tools.values()
        
        if category:
            tools = [t for t in tools if t.category == category]
        
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "category": tool.category,
                "parameters": tool.parameters,
                "enabled": tool.enabled,
                "call_count": tool.call_count,
                "error_count": tool.error_count,
                "avg_execution_time": (
                    tool.total_execution_time / max(1, tool.call_count)
                )
            }
            for tool in tools
        ]
    
    def get_tools_for_provider(self, provider: str = "openai") -> List[Dict[str, Any]]:
        """
        Get tools formatted for specific provider.
        
        Args:
            provider: Provider name (openai, anthropic, etc.)
            
        Returns:
            List of tool definitions in provider format
        """
        enabled_tools = [t for t in self.tools.values() if t.enabled]
        
        if provider == "openai":
            return [tool.to_openai_function() for tool in enabled_tools]
        elif provider == "anthropic":
            return [tool.to_anthropic_tool() for tool in enabled_tools]
        else:
            # Default to OpenAI format
            return [tool.to_openai_function() for tool in enabled_tools]
    
    async def call_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call a tool with given arguments.
        
        Args:
            tool_name: Tool name
            args: Tool arguments
            session_id: Session ID
            timeout: Execution timeout
            
        Returns:
            Tool execution result
        """
        # Get tool
        tool = self.get_tool(tool_name)
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}"
            }
        
        if not tool.enabled:
            return {
                "success": False,
                "error": f"Tool disabled: {tool_name}"
            }
        
        # Execute tool with timeout
        timeout = timeout or self.tool_timeout
        try:
            result = await asyncio.wait_for(
                tool.execute(**args),
                timeout=timeout
            )
            
            # Record in session if provided
            if session_id and session_id in self.sessions:
                session = self.sessions[session_id]
                session.add_tool_call(tool_name, args, result)
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"Tool execution timeout: {tool_name}")
            return {
                "success": False,
                "error": f"Tool execution timeout after {timeout}s",
                "tool_name": tool_name
            }
    
    async def call_tools_parallel(
        self,
        tool_calls: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Call multiple tools in parallel.
        
        Args:
            tool_calls: List of {tool_name, args} dicts
            session_id: Session ID
            
        Returns:
            List of tool execution results
        """
        # Limit parallel execution
        tool_calls = tool_calls[:self.max_parallel_tools]
        
        # Create tasks
        tasks = [
            self.call_tool(
                call["tool_name"],
                call.get("args", {}),
                session_id=session_id
            )
            for call in tool_calls
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "success": False,
                    "error": str(result),
                    "tool_name": tool_calls[i]["tool_name"]
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    def create_session(self, session_id: Optional[str] = None) -> MCPSession:
        """Create a new MCP session."""
        session = MCPSession(session_id=session_id)
        self.sessions[session.session_id] = session
        logger.info(f"Created MCP session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[MCPSession]:
        """Get session by ID."""
        return self.sessions.get(session_id)
    
    def close_session(self, session_id: str):
        """Close and remove a session."""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.is_active = False
            del self.sessions[session_id]
            logger.info(f"Closed MCP session: {session_id}")
    
    def list_sessions(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """List all sessions."""
        sessions = self.sessions.values()
        
        if active_only:
            sessions = [s for s in sessions if s.is_active]
        
        return [session.to_dict() for session in sessions]
    
    def get_tool_metrics(self) -> Dict[str, Any]:
        """Get metrics for all tools."""
        return {
            "total_tools": len(self.tools),
            "enabled_tools": len([t for t in self.tools.values() if t.enabled]),
            "total_calls": sum(t.call_count for t in self.tools.values()),
            "total_errors": sum(t.error_count for t in self.tools.values()),
            "tools": [
                {
                    "name": tool.name,
                    "category": tool.category,
                    "call_count": tool.call_count,
                    "error_count": tool.error_count,
                    "avg_execution_time": (
                        tool.total_execution_time / max(1, tool.call_count)
                    ),
                    "success_rate": (
                        (tool.call_count - tool.error_count) / max(1, tool.call_count)
                    )
                }
                for tool in self.tools.values()
            ]
        }
    
    def parse_tool_calls_from_response(
        self,
        response: Dict[str, Any],
        provider: str = "openai"
    ) -> List[Dict[str, Any]]:
        """
        Parse tool calls from LLM response.
        
        Args:
            response: LLM response
            provider: Provider name
            
        Returns:
            List of parsed tool calls
        """
        tool_calls = []
        
        if provider == "openai":
            # Parse OpenAI format
            if "function_call" in response:
                tool_calls.append({
                    "tool_name": response["function_call"]["name"],
                    "args": json.loads(response["function_call"]["arguments"])
                })
            elif "tool_calls" in response:
                for call in response["tool_calls"]:
                    tool_calls.append({
                        "tool_name": call["function"]["name"],
                        "args": json.loads(call["function"]["arguments"])
                    })
        
        elif provider == "anthropic":
            # Parse Anthropic format
            if "content" in response:
                for block in response.get("content", []):
                    if block.get("type") == "tool_use":
                        tool_calls.append({
                            "tool_name": block["name"],
                            "args": block["input"]
                        })
        
        return tool_calls


__all__ = ["MCPServer", "MCPTool", "MCPSession"]

