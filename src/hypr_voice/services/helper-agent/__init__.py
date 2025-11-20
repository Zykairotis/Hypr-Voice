"""
Helper Agent Service for Hypr-Voice

Multi-provider LLM service with LiteLLM, LangGraph agent workflows, MCP protocol support,
and specialized capabilities (summarization, analysis, planning). Supports 10+ providers
including OpenAI, Claude, Groq, xAI, Ollama, OpenRouter, Cohere, Together AI, Mistral AI,
Perplexity, and SGLang custom integration.
"""

# Core components
from .helper_agent import HelperAgent
from .integration import HelperAgentIntegration, HelperAgentSession

# Multi-provider LLM
from .litellm_client import LiteLLMClient, ProviderConfig, ProviderMetrics
from .model_factory import ModelFactory, ProviderMetricsCallback

# MCP Protocol
from .mcp_server import MCPServer, MCPTool, MCPSession

# LangGraph Agent
from .agent_graph import LangGraphAgent, AgentState

# Tools
from .langgraph_tools import LangChainTools
from .tools.mcp_tools import MCPToolWrappers
from .tools.mcp_registry import MCPToolRegistry, ToolDefinition, ToolCategory

# Streaming
from .streaming import (
    SSEFormatter,
    SSEStreamWrapper,
    SSEConnectionManager,
    StreamingBuffer,
    stream_llm_response
)

# Legacy components (backwards compatibility)
from .sglang_client import SGLangClient, SGLangConfig
from .config_loader import ConfigLoader

__version__ = "2.0.0"
__author__ = "Hypr-Voice Team"

__all__ = [
    # Main API
    "HelperAgentIntegration",
    "HelperAgentSession",
    
    # Core components
    "HelperAgent",
    "LiteLLMClient",
    "ModelFactory",
    "MCPServer",
    "LangGraphAgent",
    
    # Providers & Models
    "ProviderConfig",
    "ProviderMetrics",
    "ProviderMetricsCallback",
    
    # MCP
    "MCPTool",
    "MCPSession",
    "MCPToolRegistry",
    "ToolDefinition",
    "ToolCategory",
    
    # Agent
    "AgentState",
    
    # Tools
    "LangChainTools",
    "MCPToolWrappers",
    
    # Streaming
    "SSEFormatter",
    "SSEStreamWrapper",
    "SSEConnectionManager",
    "StreamingBuffer",
    "stream_llm_response",
    
    # Legacy (backwards compatibility)
    "SGLangClient",
    "SGLangConfig",
    "ConfigLoader",
]