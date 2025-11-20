"""
Telegram Tool for Helper Agent

This module provides Telegram Bot API integration for the Helper Agent system,
enabling Claude Code SDK to interact with Telegram chats, groups, and files.
"""

from .telegram_client import TelegramClient
from .message_handler import TelegramMessageHandler
from .file_manager import TelegramFileManager
from .auth_manager import TelegramAuthManager

__version__ = "1.0.0"
__author__ = "Hypr-Voice Team"

__all__ = [
    "TelegramClient",
    "TelegramMessageHandler",
    "TelegramFileManager",
    "TelegramAuthManager",
]