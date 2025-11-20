"""
Unified MCP Tool Registry

This module provides a unified registry that converts MCP tool definitions into
LangChain StructuredTools, ensuring both MCP server and LangGraph agent use the
same tool implementations.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Union
from pydantic import BaseModel, Field, create_model
from enum import Enum

try:
    from langchain.tools import StructuredTool
    from langchain_core.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available")

from .mcp_tools import MCPToolWrappers

logger = logging.getLogger(__name__)


class ToolCategory(str, Enum):
    """Tool category types."""
    TEXT_PROCESSING = "text_processing"
    PLANNING = "planning"
    COMPUTATION = "computation"
    AI_INTEGRATION = "ai_integration"
    CUSTOM = "custom"


class ToolDefinition:
    """Definition for a unified tool that works with both MCP and LangChain."""
    
    def __init__(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any],
        category: ToolCategory = ToolCategory.CUSTOM,
        enabled: bool = True,
        async_func: bool = True
    ):
        """
        Initialize tool definition.
        
        Args:
            name: Tool name
            description: Tool description
            func: Tool function (async)
            parameters: JSON Schema parameters for MCP
            category: Tool category
            enabled: Whether tool is enabled
            async_func: Whether function is async
        """
        self.name = name
        self.description = description
        self.func = func
        self.parameters = parameters
        self.category = category
        self.enabled = enabled
        self.async_func = async_func
    
    def to_pydantic_model(self) -> type[BaseModel]:
        """
        Convert JSON Schema parameters to Pydantic model.
        
        Returns:
            Pydantic model class
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain required to create Pydantic models")
        
        # Extract properties from JSON schema
        props = self.parameters.get("properties", {})
        required = set(self.parameters.get("required", []))
        
        # Build field definitions
        fields = {}
        for field_name, field_def in props.items():
            field_type = self._json_type_to_python(field_def.get("type"))
            field_desc = field_def.get("description", "")
            field_default = field_def.get("default", ...)
            
            # Handle nullable fields
            if field_def.get("nullable") or field_name not in required:
                field_type = Optional[field_type]
                if field_default == ...:
                    field_default = None
            
            # Handle enums
            if "enum" in field_def:
                # Create string literal type for enum values
                field_type = str
            
            fields[field_name] = (
                field_type,
                Field(default=field_default, description=field_desc)
            )
        
        # Create dynamic Pydantic model
        model_name = f"{self.name.title().replace('_', '')}Input"
        return create_model(model_name, **fields)
    
    def _json_type_to_python(self, json_type: str) -> type:
        """Convert JSON Schema type to Python type."""
        type_map = {
            "string": str,
            "integer": int,
            "number": float,
            "boolean": bool,
            "array": List,
            "object": Dict,
        }
        return type_map.get(json_type, str)
    
    def to_langchain_tool(self) -> StructuredTool:
        """
        Convert to LangChain StructuredTool.
        
        Returns:
            StructuredTool instance
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain required to create tools")
        
        if not self.enabled:
            raise ValueError(f"Tool {self.name} is disabled")
        
        # Create Pydantic model for args
        args_schema = self.to_pydantic_model()
        
        return StructuredTool.from_function(
            func=self.func,
            name=self.name,
            description=self.description,
            args_schema=args_schema,
            return_direct=False,
            coroutine=self.func if self.async_func else None
        )
    
    def to_mcp_spec(self) -> Dict[str, Any]:
        """
        Convert to MCP tool specification.
        
        Returns:
            MCP tool spec dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "category": self.category.value,
            "enabled": self.enabled
        }


class MCPToolRegistry:
    """
    Unified registry for MCP and LangChain tools.
    
    Features:
    - Single source of truth for tool definitions
    - Automatic conversion to LangChain StructuredTools
    - Automatic registration with MCP server
    - Category-based tool organization
    - Enable/disable individual tools
    """
    
    def __init__(self, helper_agent_instance=None):
        """
        Initialize the tool registry.
        
        Args:
            helper_agent_instance: HelperAgent instance for tool access
        """
        self.agent = helper_agent_instance
        self.tools: Dict[str, ToolDefinition] = {}
        self.mcp_wrappers: Optional[MCPToolWrappers] = None
        
        # Initialize tool definitions
        self._register_builtin_tools()
    
    def _register_builtin_tools(self):
        """Register built-in MCP tools."""
        # Create MCP wrappers instance
        self.mcp_wrappers = MCPToolWrappers(self.agent)
        
        # Summarization tool
        self.register_tool(
            name="summarize_text",
            description="Summarize text content for voice agent consumption with configurable length and style",
            func=self.mcp_wrappers.summarize_text_mcp,
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text content to summarize"
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Maximum length of summary in characters",
                        "default": 500
                    },
                    "style": {
                        "type": "string",
                        "description": "Summary style",
                        "enum": ["voice_optimized", "concise", "detailed"],
                        "default": "voice_optimized"
                    },
                    "focus": {
                        "type": "string",
                        "description": "Specific focus area",
                        "enum": ["technical", "actionable", "key_points", "decisions"],
                        "nullable": True
                    }
                },
                "required": ["text"]
            },
            category=ToolCategory.TEXT_PROCESSING
        )
        
        # Analysis tool
        self.register_tool(
            name="analyze_content",
            description="Analyze content for voice agent optimization including sentiment, readability, and key insights",
            func=self.mcp_wrappers.analyze_content_mcp,
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Content to analyze"
                    },
                    "analysis_type": {
                        "type": "string",
                        "description": "Type of analysis",
                        "enum": ["comprehensive", "sentiment", "readability", "technical"],
                        "default": "comprehensive"
                    },
                    "optimize_for_voice": {
                        "type": "boolean",
                        "description": "Whether to optimize for voice output",
                        "default": True
                    }
                },
                "required": ["content"]
            },
            category=ToolCategory.TEXT_PROCESSING
        )
        
        # Planning tool
        self.register_tool(
            name="plan_task",
            description="Break down complex tasks into actionable steps with priorities and time estimates",
            func=self.mcp_wrappers.plan_task_mcp,
            parameters={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task description to plan"
                    },
                    "max_steps": {
                        "type": "integer",
                        "description": "Maximum number of steps to generate",
                        "default": 10
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context for planning",
                        "nullable": True
                    },
                    "complexity": {
                        "type": "string",
                        "description": "Task complexity level",
                        "enum": ["simple", "medium", "complex"],
                        "default": "medium"
                    }
                },
                "required": ["task"]
            },
            category=ToolCategory.PLANNING
        )
        
        # Extraction tool
        self.register_tool(
            name="extract_information",
            description="Extract specific types of information from text (dates, people, actions, etc.)",
            func=self.mcp_wrappers.extract_information_mcp,
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract information from"
                    },
                    "information_types": {
                        "type": "array",
                        "description": "Types of information to extract",
                        "items": {
                            "type": "string"
                        },
                        "default": ["actions", "key_points", "decisions"]
                    }
                },
                "required": ["text"]
            },
            category=ToolCategory.TEXT_PROCESSING
        )
        
        # Calculator tool
        self.register_tool(
            name="calculator",
            description="Perform mathematical calculations with support for basic arithmetic and functions",
            func=self.mcp_wrappers.calculator_mcp,
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    },
                    "precision": {
                        "type": "integer",
                        "description": "Number of decimal places",
                        "default": 2
                    }
                },
                "required": ["expression"]
            },
            category=ToolCategory.COMPUTATION
        )
        
        # Claude SDK bridge tool
        self.register_tool(
            name="claude_sdk_bridge",
            description="Bridge to Claude Code SDK for context-aware assistance and coding support",
            func=self.mcp_wrappers.claude_sdk_bridge_mcp,
            parameters={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "Request to process via Claude SDK"
                    },
                    "context": {
                        "type": "object",
                        "description": "Additional context",
                        "nullable": True
                    },
                    "voice_optimized": {
                        "type": "boolean",
                        "description": "Optimize response for voice output",
                        "default": True
                    }
                },
                "required": ["request"]
            },
            category=ToolCategory.AI_INTEGRATION
        )
        
        logger.info(f"Registered {len(self.tools)} built-in tools")
    
    def register_tool(
        self,
        name: str,
        description: str,
        func: Callable,
        parameters: Dict[str, Any],
        category: ToolCategory = ToolCategory.CUSTOM,
        enabled: bool = True,
        async_func: bool = True
    ):
        """
        Register a new tool in the registry.
        
        Args:
            name: Tool name
            description: Tool description
            func: Tool function
            parameters: JSON Schema parameters
            category: Tool category
            enabled: Whether tool is enabled
            async_func: Whether function is async
        """
        tool_def = ToolDefinition(
            name=name,
            description=description,
            func=func,
            parameters=parameters,
            category=category,
            enabled=enabled,
            async_func=async_func
        )
        
        self.tools[name] = tool_def
        logger.debug(f"Registered tool: {name}")
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool definition by name."""
        return self.tools.get(name)
    
    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """
        List available tools.
        
        Args:
            category: Filter by category (None for all)
            enabled_only: Only return enabled tools
            
        Returns:
            List of tool names
        """
        tools = []
        for name, tool_def in self.tools.items():
            if enabled_only and not tool_def.enabled:
                continue
            if category and tool_def.category != category:
                continue
            tools.append(name)
        return tools
    
    def get_langchain_tools(
        self,
        category: Optional[ToolCategory] = None,
        tool_names: Optional[List[str]] = None
    ) -> List[StructuredTool]:
        """
        Get LangChain StructuredTools.
        
        Args:
            category: Filter by category (None for all)
            tool_names: Specific tool names to get (None for all)
            
        Returns:
            List of LangChain StructuredTools
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain required")
        
        tools = []
        for name, tool_def in self.tools.items():
            if not tool_def.enabled:
                continue
            if category and tool_def.category != category:
                continue
            if tool_names and name not in tool_names:
                continue
            
            try:
                lc_tool = tool_def.to_langchain_tool()
                tools.append(lc_tool)
            except Exception as e:
                logger.error(f"Failed to create LangChain tool for {name}: {e}")
        
        return tools
    
    def register_with_mcp_server(self, mcp_server):
        """
        Register all tools with an MCP server.
        
        Args:
            mcp_server: MCPServer instance
        """
        for name, tool_def in self.tools.items():
            if not tool_def.enabled:
                continue
            
            try:
                mcp_server.register_tool(
                    name=name,
                    description=tool_def.description,
                    parameters=tool_def.parameters,
                    func=tool_def.func,
                    category=tool_def.category.value,
                    enabled=tool_def.enabled
                )
            except Exception as e:
                logger.error(f"Failed to register MCP tool {name}: {e}")
        
        logger.info(f"Registered {len(self.tools)} tools with MCP server")
    
    def get_tools_by_category(self, category: ToolCategory) -> Dict[str, ToolDefinition]:
        """Get all tools in a category."""
        return {
            name: tool_def
            for name, tool_def in self.tools.items()
            if tool_def.category == category and tool_def.enabled
        }
    
    def enable_tool(self, name: str):
        """Enable a tool."""
        if name in self.tools:
            self.tools[name].enabled = True
            logger.info(f"Enabled tool: {name}")
    
    def disable_tool(self, name: str):
        """Disable a tool."""
        if name in self.tools:
            self.tools[name].enabled = False
            logger.info(f"Disabled tool: {name}")
    
    def get_tool_count(self, category: Optional[ToolCategory] = None) -> int:
        """Get count of tools."""
        return len(self.list_tools(category=category, enabled_only=True))


__all__ = ["MCPToolRegistry", "ToolDefinition", "ToolCategory"]

