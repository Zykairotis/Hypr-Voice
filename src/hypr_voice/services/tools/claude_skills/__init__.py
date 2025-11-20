"""
Claude Code SDK Integration Skills

This module provides Claude Code SDK integration skills for Telegram and Discord
bot integrations, enabling Claude to interact with messaging platforms.
"""

from .telegram_skills import TelegramSkills
from .discord_skills import DiscordSkills
from .unified_bot_skills import UnifiedBotSkills

__version__ = "1.0.0"
__author__ = "Hypr-Voice Team"

__all__ = [
    "TelegramSkills",
    "DiscordSkills",
    "UnifiedBotSkills",
]