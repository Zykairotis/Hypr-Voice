"""
Hypr-Voice Agents Module

Specialized agent definitions for different task types.
"""

from .definitions import (
    AgentDefinition,
    CodeAgent,
    ResearchAgent,
    ShellAgent,
    VoiceAgent,
    create_agent,
    get_all_agents,
)

__all__ = [
    "AgentDefinition",
    "CodeAgent",
    "ResearchAgent",
    "ShellAgent",
    "VoiceAgent",
    "create_agent",
    "get_all_agents",
]
