"""
Unified Bot Skills for Claude Code SDK Integration

This module provides unified Claude Code SDK skills that work with both Telegram
and Discord platforms through a single interface.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class UnifiedBotSkills:
    """
    Unified Claude Code SDK skills for Telegram and Discord bot integration.

    Provides a single interface for:
    - Cross-platform messaging
    - Unified file operations
    - Platform-agnostic bot management
    - Centralized authentication
    - Cross-platform search and analysis
    """

    def __init__(self, bot_integration_manager):
        """
        Initialize unified bot skills.

        Args:
            bot_integration_manager: Initialized bot integration manager
        """
        self.bot_manager = bot_integration_manager

        # Initialize platform-specific skills
        self.telegram_skills = None
        self.discord_skills = None

        # Platform-specific skill mappings
        self.platform_skills = {
            'telegram': {},
            'discord': {}
        }

        # Initialize platform skills
        self._initialize_platform_skills()

        # Unified skills registry
        self.unified_skills = {
            'send_message': self.unified_send_message,
            'get_chat_history': self.unified_get_chat_history,
            'send_file': self.unified_send_file,
            'analyze_file': self.unified_analyze_file,
            'search_messages': self.unified_search_messages,
            'get_platform_status': self.unified_get_status,
            'manage_users': self.unified_manage_users,
            'voice_optimization': self.unified_voice_optimization,
            'cross_platform_search': self.cross_platform_search,
            'platform_chat_info': self.unified_get_chat_info
        }

    def _initialize_platform_skills(self):
        """Initialize platform-specific skills."""
        try:
            # Initialize Telegram skills
            if (self.bot_manager.telegram_client and
                self.bot_manager.telegram_handler and
                self.bot_manager.telegram_file_manager and
                self.bot_manager.telegram_auth_manager):

                from .telegram_skills import TelegramSkills
                self.telegram_skills = TelegramSkills(
                    self.bot_manager.telegram_client,
                    self.bot_manager.telegram_handler,
                    self.bot_manager.telegram_file_manager,
                    self.bot_manager.telegram_auth_manager
                )
                self.platform_skills['telegram'] = self.telegram_skills.skills
                logger.info("Telegram skills initialized")

            # Initialize Discord skills
            if (self.bot_manager.discord_client and
                self.bot_manager.discord_handler and
                self.bot_manager.discord_file_manager and
                self.bot_manager.discord_auth_manager):

                from .discord_skills import DiscordSkills
                self.discord_skills = DiscordSkills(
                    self.bot_manager.discord_client,
                    self.bot_manager.discord_handler,
                    self.bot_manager.discord_file_manager,
                    self.bot_manager.discord_auth_manager
                )
                self.platform_skills['discord'] = self.discord_skills.skills
                logger.info("Discord skills initialized")

        except Exception as e:
            logger.error(f"Error initializing platform skills: {e}")

    async def unified_send_message(
        self,
        platform: str,
        chat_id: Union[int, str],
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message on the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            chat_id: Target chat/channel ID
            text: Message text to send
            **kwargs: Platform-specific parameters

        Returns:
            Result dictionary with success status
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.send_message(chat_id, text, **kwargs)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.send_message(chat_id, text, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_send_message"
                }

        except Exception as e:
            logger.error(f"Error in unified_send_message: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_send_message"
            }

    async def unified_get_chat_history(
        self,
        platform: str,
        chat_id: Union[int, str],
        limit: int = 100,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Get chat history from the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            chat_id: Chat/channel ID
            limit: Maximum number of messages
            **kwargs: Platform-specific parameters

        Returns:
            Result dictionary with messages
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.get_chat_history(chat_id, limit, **kwargs)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.get_channel_history(chat_id, limit, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_get_chat_history"
                }

        except Exception as e:
            logger.error(f"Error in unified_get_chat_history: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_get_chat_history"
            }

    async def unified_send_file(
        self,
        platform: str,
        chat_id: Union[int, str],
        file_path: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a file on the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            chat_id: Target chat/channel ID
            file_path: Path to file to send
            **kwargs: Platform-specific parameters

        Returns:
            Result dictionary with file information
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.send_file(chat_id, file_path, **kwargs)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.send_file(chat_id, file_path, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_send_file"
                }

        except Exception as e:
            logger.error(f"Error in unified_send_file: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_send_file"
            }

    async def unified_analyze_file(
        self,
        platform: str,
        file_path: str,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analyze a file from the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            file_path: Path to file to analyze
            analysis_type: Type of analysis

        Returns:
            Result dictionary with analysis information
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.analyze_file(file_path, analysis_type)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.analyze_file(file_path, analysis_type)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_analyze_file"
                }

        except Exception as e:
            logger.error(f"Error in unified_analyze_file: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_analyze_file"
            }

    async def unified_search_messages(
        self,
        platform: str,
        chat_id: Union[int, str],
        query: str,
        limit: int = 50,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search messages on the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            chat_id: Chat/channel ID to search in
            query: Search query
            limit: Maximum number of results
            **kwargs: Platform-specific parameters

        Returns:
            Result dictionary with search results
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.search_messages(chat_id, query, limit, **kwargs)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.search_messages(chat_id, query, limit, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_search_messages"
                }

        except Exception as e:
            logger.error(f"Error in unified_search_messages: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_search_messages"
            }

    async def unified_get_status(self, platform: Optional[str] = None) -> Dict[str, Any]:
        """
        Get status for specified platform or all platforms.

        Args:
            platform: Optional platform to get status for

        Returns:
            Result dictionary with status information
        """
        try:
            results = {}

            if platform is None or platform == 'telegram':
                if self.telegram_skills:
                    results['telegram'] = await self.telegram_skills.get_bot_status()
                else:
                    results['telegram'] = {"success": False, "error": "Telegram not initialized"}

            if platform is None or platform == 'discord':
                if self.discord_skills:
                    results['discord'] = await self.discord_skills.get_bot_status()
                else:
                    results['discord'] = {"success": False, "error": "Discord not initialized"}

            return {
                "success": True,
                "platforms": results,
                "overall_status": self.bot_manager.get_statistics(),
                "skill": "unified_get_status"
            }

        except Exception as e:
            logger.error(f"Error in unified_get_status: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_get_status"
            }

    async def unified_manage_users(
        self,
        platform: str,
        action: str,
        user_id: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Manage users on the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            action: Action to perform
            user_id: User ID to manage
            **kwargs: Platform-specific parameters

        Returns:
            Result dictionary with operation status
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.manage_users(action, user_id, **kwargs)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.manage_permissions(action, user_id, **kwargs)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_manage_users"
                }

        except Exception as e:
            logger.error(f"Error in unified_manage_users: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_manage_users"
            }

    async def unified_voice_optimization(
        self,
        text: str,
        optimization_type: str = "readability",
        platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Optimize text for voice output.

        Args:
            text: Text to optimize
            optimization_type: Type of optimization
            platform: Optional platform for platform-specific optimization

        Returns:
            Result dictionary with optimized text
        """
        try:
            # Use available platform or generic optimization
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.voice_optimization(text, optimization_type)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.voice_optimization(text, optimization_type)
            else:
                # Generic optimization
                optimized = self._basic_voice_optimization(text)
                return {
                    "success": True,
                    "original_text": text,
                    "optimized_text": optimized,
                    "optimization_type": optimization_type,
                    "skill": "unified_voice_optimization"
                }

        except Exception as e:
            logger.error(f"Error in unified_voice_optimization: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_voice_optimization"
            }

    async def cross_platform_search(
        self,
        query: str,
        platforms: Optional[List[str]] = None,
        chat_ids: Optional[Dict[str, Union[int, str]]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Search for messages across multiple platforms.

        Args:
            query: Search query
            platforms: List of platforms to search (optional, defaults to all available)
            chat_ids: Dictionary of platform -> chat_id mappings
            limit: Maximum results per platform

        Returns:
            Result dictionary with cross-platform search results
        """
        try:
            if platforms is None:
                platforms = []
                if self.telegram_skills:
                    platforms.append('telegram')
                if self.discord_skills:
                    platforms.append('discord')

            results = {}
            total_results = 0

            for platform in platforms:
                if chat_ids and platform in chat_ids:
                    chat_id = chat_ids[platform]
                    result = await self.unified_search_messages(platform, chat_id, query, limit)
                    if result.get("success"):
                        results[platform] = result
                        total_results += result.get("total_found", 0)
                    else:
                        results[platform] = {"success": False, "error": result.get("error")}
                else:
                    results[platform] = {"success": False, "error": "No chat ID provided for platform"}

            return {
                "success": True,
                "query": query,
                "platforms": platforms,
                "results": results,
                "total_results": total_results,
                "skill": "cross_platform_search"
            }

        except Exception as e:
            logger.error(f"Error in cross_platform_search: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "cross_platform_search"
            }

    async def unified_get_chat_info(
        self,
        platform: str,
        chat_id: Union[int, str]
    ) -> Dict[str, Any]:
        """
        Get chat information from the specified platform.

        Args:
            platform: Platform to use (telegram/discord)
            chat_id: Chat/channel ID

        Returns:
            Result dictionary with chat information
        """
        try:
            if platform == 'telegram' and self.telegram_skills:
                return await self.telegram_skills.get_chat_info(chat_id)
            elif platform == 'discord' and self.discord_skills:
                return await self.discord_skills.get_channel_info(chat_id)
            else:
                return {
                    "success": False,
                    "error": f"Platform '{platform}' not available or not initialized",
                    "skill": "unified_get_chat_info"
                }

        except Exception as e:
            logger.error(f"Error in unified_get_chat_info: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "unified_get_chat_info"
            }

    async def broadcast_message(
        self,
        message: str,
        platforms: Optional[List[str]] = None,
        chat_ids: Optional[Dict[str, List[Union[int, str]]]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Broadcast a message to multiple platforms and chats.

        Args:
            message: Message to broadcast
            platforms: List of platforms to broadcast to
            chat_ids: Dictionary of platform -> list of chat IDs
            **kwargs: Platform-specific parameters

        Returns:
            Result dictionary with broadcast results
        """
        try:
            if platforms is None:
                platforms = []
                if self.telegram_skills:
                    platforms.append('telegram')
                if self.discord_skills:
                    platforms.append('discord')

            results = {}
            successful_sends = 0
            total_sends = 0

            for platform in platforms:
                platform_results = []
                platform_chat_ids = chat_ids.get(platform, []) if chat_ids else []

                if not platform_chat_ids:
                    results[platform] = {"success": False, "error": "No chat IDs provided"}
                    continue

                for chat_id in platform_chat_ids:
                    total_sends += 1
                    result = await self.unified_send_message(platform, chat_id, message, **kwargs)
                    platform_results.append(result)
                    if result.get("success"):
                        successful_sends += 1

                results[platform] = {
                    "success": len([r for r in platform_results if r.get("success")]) > 0,
                    "results": platform_results,
                    "successful_sends": len([r for r in platform_results if r.get("success")]),
                    "total_sends": len(platform_results)
                }

            return {
                "success": successful_sends > 0,
                "message": message,
                "platforms": platforms,
                "results": results,
                "successful_sends": successful_sends,
                "total_sends": total_sends,
                "success_rate": successful_sends / total_sends if total_sends > 0 else 0,
                "skill": "broadcast_message"
            }

        except Exception as e:
            logger.error(f"Error in broadcast_message: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "broadcast_message"
            }

    def _basic_voice_optimization(self, text: str) -> str:
        """Basic voice optimization fallback."""
        # Simple text cleaning for voice output
        text = text.replace("e.g.", "for example")
        text = text.replace("i.e.", "that is")
        text = text.replace("etc.", "et cetera")
        text = text.replace("&", "and")
        text = text.replace("%", "percent")
        text = text.replace("$", "dollars")
        text = text.replace("#", "number")

        # Add pauses for commas and periods
        text = text.replace(",", ", <pause>")
        text = text.replace(".", ". <pause>")

        return text

    def get_available_skills(self) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available unified skills for Claude.

        Returns:
            Dictionary of available skills with descriptions
        """
        return {
            "send_message": {
                "description": "Send a message on a specified platform (telegram/discord)",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "chat_id": "Target chat/channel ID (required)",
                    "text": "Message text to send (required)",
                    "kwargs": "Platform-specific parameters (optional)"
                }
            },
            "get_chat_history": {
                "description": "Get chat history from a specified platform",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "chat_id": "Chat/channel ID (required)",
                    "limit": "Maximum number of messages (optional, default: 100)",
                    "kwargs": "Platform-specific parameters (optional)"
                }
            },
            "send_file": {
                "description": "Send a file on a specified platform",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "chat_id": "Target chat/channel ID (required)",
                    "file_path": "Path to file to send (required)",
                    "kwargs": "Platform-specific parameters (optional)"
                }
            },
            "analyze_file": {
                "description": "Analyze a file from a specified platform",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "file_path": "Path to file to analyze (required)",
                    "analysis_type": "Type of analysis (summary/structure/content, optional, default: summary)"
                }
            },
            "search_messages": {
                "description": "Search messages on a specified platform",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "chat_id": "Chat/channel ID to search in (required)",
                    "query": "Search query (required)",
                    "limit": "Maximum number of results (optional, default: 50)",
                    "kwargs": "Platform-specific parameters (optional)"
                }
            },
            "get_platform_status": {
                "description": "Get status for specified platform or all platforms",
                "parameters": {
                    "platform": "Optional platform to get status for (telegram/discord)"
                }
            },
            "manage_users": {
                "description": "Manage users on a specified platform",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "action": "Action to perform (required)",
                    "user_id": "User ID to manage (required)",
                    "kwargs": "Platform-specific parameters (optional)"
                }
            },
            "voice_optimization": {
                "description": "Optimize text for voice output",
                "parameters": {
                    "text": "Text to optimize (required)",
                    "optimization_type": "Type of optimization (readability/pronunciation/pacing, optional, default: readability)",
                    "platform": "Optional platform for platform-specific optimization"
                }
            },
            "cross_platform_search": {
                "description": "Search for messages across multiple platforms",
                "parameters": {
                    "query": "Search query (required)",
                    "platforms": "List of platforms to search (optional, defaults to all available)",
                    "chat_ids": "Dictionary of platform -> chat_id mappings (optional)",
                    "limit": "Maximum results per platform (optional, default: 50)"
                }
            },
            "platform_chat_info": {
                "description": "Get chat information from a specified platform",
                "parameters": {
                    "platform": "Platform to use (telegram/discord, required)",
                    "chat_id": "Chat/channel ID (required)"
                }
            },
            "broadcast_message": {
                "description": "Broadcast a message to multiple platforms and chats",
                "parameters": {
                    "message": "Message to broadcast (required)",
                    "platforms": "List of platforms to broadcast to (optional)",
                    "chat_ids": "Dictionary of platform -> list of chat IDs (optional)",
                    "kwargs": "Platform-specific parameters (optional)"
                }
            }
        }

    async def execute_skill(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a unified bot skill.

        Args:
            skill_name: Name of skill to execute
            **kwargs: Skill parameters

        Returns:
            Result from skill execution
        """
        if skill_name not in self.unified_skills:
            return {
                "success": False,
                "error": f"Unknown skill: {skill_name}",
                "available_skills": list(self.unified_skills.keys())
            }

        skill_func = self.unified_skills[skill_name]
        return await skill_func(**kwargs)