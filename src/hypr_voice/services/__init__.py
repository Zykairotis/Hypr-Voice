"""
Services Module
Contains all agent services
"""

from .agent_skills import SkillRegistry
from .hooks import HookManager, HookEvent, HookContext, Hook
from .voice import (
    UniversalTTS, TTSConfig, TTSProvider,
    text_to_speech, list_all_voices
)
from .mcp import MCPServerManager
from .subagents import SubAgentSystem
# from .tools import HYPRLAND_TOOLS
# from .gemini_live import GEMINI_TOOLS

__all__ = [
    # Skills
    'SkillRegistry',
    
    # Hooks
    'HookManager', 'HookEvent', 'HookContext', 'Hook',
    
    # Voice
    'UniversalTTS', 'TTSConfig', 'TTSProvider',
    'text_to_speech', 'list_all_voices',
    
    # MCP
    'MCPServerManager',
    
    # Subagents
    'SubAgentSystem',
    
    # Tools
    # 'HYPRLAND_TOOLS', 'GEMINI_TOOLS'
]
