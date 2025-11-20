"""
Discord Tool for Helper Agent

This module provides Discord Bot API integration for the Helper Agent system,
enabling Claude Code SDK to interact with Discord servers, channels, and files.
"""

from .discord_client import DiscordClient
from .message_handler import DiscordMessageHandler
from .file_manager import DiscordFileManager
from .auth_manager import DiscordAuthManager

__version__ = "1.0.0"
__author__ = "Hypr-Voice Team"

__all__ = [
    "DiscordClient",
    "DiscordMessageHandler",
    "DiscordFileManager",
    "DiscordAuthManager",
]