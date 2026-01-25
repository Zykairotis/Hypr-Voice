"""
Hypr Voice Package

Agent orchestration system using Claude Agent SDK patterns.
"""

# Legacy exports (for backwards compatibility)
from .client import AgentClient, AgentConfig, quick_agent

# New orchestrator system
from .orchestrator import (
    HyprVoiceOrchestrator,
    QueryRouter,
    RouteDecision,
    ContextManager,
    AgentRegistry,
    AgentSession,
)

# Agent definitions
from .agents import (
    AgentDefinition,
    CodeAgent,
    ResearchAgent,
    ShellAgent,
    VoiceAgent,
    create_agent,
    get_all_agents,
)

# Tools
from .tools import ToolRegistry, tool, create_mcp_server

# IPC
from .ipc import HyprlandIPC, send_notification, OrchestratorWebSocket

# Middleware
from .middleware import HookManager, HookEvent, RequestRouter

__all__ = [
    # Legacy
    "AgentClient",
    "AgentConfig",
    "quick_agent",
    
    # Orchestrator
    "HyprVoiceOrchestrator",
    "QueryRouter",
    "RouteDecision",
    "ContextManager",
    "AgentRegistry",
    "AgentSession",
    
    # Agents
    "AgentDefinition",
    "CodeAgent",
    "ResearchAgent",
    "ShellAgent",
    "VoiceAgent",
    "create_agent",
    "get_all_agents",
    
    # Tools
    "ToolRegistry",
    "tool",
    "create_mcp_server",
    
    # IPC
    "HyprlandIPC",
    "send_notification",
    "OrchestratorWebSocket",
    
    # Middleware
    "HookManager",
    "HookEvent",
    "RequestRouter",
]

__version__ = "0.2.0"

