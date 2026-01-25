"""
Tool Registry

Manages tool definitions using Claude Agent SDK patterns.
Provides @tool decorator and MCP server creation.
"""

import logging
from typing import Any, Callable, Awaitable, Optional
from dataclasses import dataclass, field
from functools import wraps
import inspect

logger = logging.getLogger(__name__)

# Claude SDK compatibility layer
from ..services.sdk_compat import tool as sdk_tool, create_sdk_mcp_server, CLAUDE_SDK_AVAILABLE as SDK_AVAILABLE


@dataclass
class ToolDefinition:
    """Definition of a tool."""
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict], Awaitable[dict]]
    category: str = "general"
    enabled: bool = True
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "category": self.category,
            "enabled": self.enabled,
        }


class ToolRegistry:
    """
    Registry for managing tools.
    
    Provides:
    - Tool registration via @tool decorator
    - Tool lookup by name or category
    - MCP server creation for SDK integration
    """
    
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._categories: dict[str, list[str]] = {}
    
    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        handler: Callable,
        category: str = "general",
    ) -> ToolDefinition:
        """
        Register a tool.
        
        Args:
            name: Unique tool name
            description: Human-readable description
            input_schema: JSON schema for input validation
            handler: Async function to execute the tool
            category: Tool category for organization
            
        Returns:
            Registered ToolDefinition
        """
        tool_def = ToolDefinition(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            category=category,
        )
        
        self._tools[name] = tool_def
        
        # Update category index
        if category not in self._categories:
            self._categories[category] = []
        if name not in self._categories[category]:
            self._categories[category].append(name)
        
        logger.debug(f"Registered tool: {name} in category {category}")
        return tool_def
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def list_tools(self, category: Optional[str] = None, enabled_only: bool = True) -> list[dict]:
        """
        List all registered tools.
        
        Args:
            category: Filter by category
            enabled_only: Only return enabled tools
            
        Returns:
            List of tool dictionaries
        """
        tools = list(self._tools.values())
        
        if category:
            tools = [t for t in tools if t.category == category]
        if enabled_only:
            tools = [t for t in tools if t.enabled]
        
        return [t.to_dict() for t in tools]
    
    def list_categories(self) -> list[str]:
        """List all tool categories."""
        return list(self._categories.keys())
    
    def enable_tool(self, name: str) -> bool:
        """Enable a tool."""
        if name in self._tools:
            self._tools[name].enabled = True
            return True
        return False
    
    def disable_tool(self, name: str) -> bool:
        """Disable a tool."""
        if name in self._tools:
            self._tools[name].enabled = False
            return True
        return False
    
    async def execute(self, name: str, args: dict) -> dict:
        """
        Execute a tool by name.
        
        Args:
            name: Tool name
            args: Tool arguments
            
        Returns:
            Tool result dictionary
        """
        tool_def = self._tools.get(name)
        if not tool_def:
            return {
                "content": [{"type": "text", "text": f"Tool not found: {name}"}],
                "is_error": True,
            }
        
        if not tool_def.enabled:
            return {
                "content": [{"type": "text", "text": f"Tool disabled: {name}"}],
                "is_error": True,
            }
        
        try:
            return await tool_def.handler(args)
        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "is_error": True,
            }
    
    def create_mcp_server(self, name: str, version: str = "1.0.0", tools: list[str] = None):
        """
        Create an MCP server with registered tools.
        
        Args:
            name: Server name
            version: Server version
            tools: List of tool names to include (all if None)
            
        Returns:
            MCP server configuration
        """
        if not SDK_AVAILABLE:
            logger.warning("SDK not available for MCP server creation")
            return None
        
        tool_list = []
        for tool_name, tool_def in self._tools.items():
            if tools is None or tool_name in tools:
                if tool_def.enabled:
                    # Create SDK tool from our definition
                    tool_list.append(self._create_sdk_tool(tool_def))
        
        return create_sdk_mcp_server(
            name=name,
            version=version,
            tools=tool_list,
        )
    
    def _create_sdk_tool(self, tool_def: ToolDefinition):
        """Create SDK-compatible tool from definition."""
        if SDK_AVAILABLE:
            @sdk_tool(tool_def.name, tool_def.description, tool_def.input_schema)
            async def wrapper(args: dict) -> dict:
                return await tool_def.handler(args)
            return wrapper
        return None


# Global registry instance
_registry = ToolRegistry()


def tool(
    name: str,
    description: str,
    input_schema: dict[str, Any],
    category: str = "general",
):
    """
    Decorator for defining tools.
    
    Usage:
        @tool("my_tool", "Does something", {"param": str})
        async def my_tool(args: dict) -> dict:
            return {"content": [{"type": "text", "text": "result"}]}
    
    Args:
        name: Unique tool name
        description: Human-readable description
        input_schema: Schema for input parameters
        category: Tool category
        
    Returns:
        Decorated function registered as a tool
    """
    def decorator(func: Callable[[dict], Awaitable[dict]]):
        # Register with global registry
        _registry.register(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=func,
            category=category,
        )
        
        @wraps(func)
        async def wrapper(args: dict) -> dict:
            return await func(args)
        
        # Attach metadata
        wrapper._tool_name = name
        wrapper._tool_description = description
        wrapper._tool_schema = input_schema
        
        return wrapper
    
    return decorator


def create_mcp_server(name: str, version: str = "1.0.0", tools: list[str] = None):
    """Create an MCP server from the global registry."""
    return _registry.create_mcp_server(name, version, tools)


def get_registry() -> ToolRegistry:
    """Get the global tool registry."""
    return _registry


# Built-in tool definitions

@tool(
    "hypr_voice_status",
    "Get the current status of Hypr-Voice services",
    {},
    category="system"
)
async def hypr_voice_status(args: dict) -> dict:
    """Get Hypr-Voice system status."""
    return {
        "content": [{
            "type": "text",
            "text": "Hypr-Voice Status: Running\nOrchestrator: Active\nAgents: Ready"
        }]
    }


@tool(
    "list_agents",
    "List all available agent types",
    {},
    category="orchestrator"
)
async def list_agents_tool(args: dict) -> dict:
    """List available agents."""
    from ..agents import get_all_agents
    
    agents = get_all_agents()
    agent_list = "\n".join([
        f"- {name}: {agent.description}"
        for name, agent in agents.items()
    ])
    
    return {
        "content": [{
            "type": "text",
            "text": f"Available Agents:\n{agent_list}"
        }]
    }
