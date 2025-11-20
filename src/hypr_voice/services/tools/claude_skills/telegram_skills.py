"""
Telegram Skills for Claude Code SDK Integration

This module provides Claude Code SDK skills for Telegram bot integration,
enabling Claude to interact with Telegram chats, users, and files.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class TelegramSkills:
    """
    Claude Code SDK skills for Telegram bot integration.

    Provides capabilities for:
    - Sending and receiving Telegram messages
    - Managing chats and users
    - Processing files and media
    - Bot administration
    """

    def __init__(self, telegram_client, message_handler, file_manager, auth_manager):
        """
        Initialize Telegram skills.

        Args:
            telegram_client: Initialized Telegram client
            message_handler: Telegram message handler
            file_manager: Telegram file manager
            auth_manager: Telegram authentication manager
        """
        self.telegram_client = telegram_client
        self.message_handler = message_handler
        self.file_manager = file_manager
        self.auth_manager = auth_manager

        # Skills registry for Claude Code SDK
        self.skills = {
            'send_telegram_message': self.send_message,
            'get_telegram_chat_history': self.get_chat_history,
            'send_telegram_file': self.send_file,
            'analyze_telegram_file': self.analyze_file,
            'get_telegram_chat_info': self.get_chat_info,
            'manage_telegram_users': self.manage_users,
            'telegram_bot_status': self.get_bot_status,
            'search_telegram_messages': self.search_messages,
            'telegram_voice_optimization': self.voice_optimization
        }

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: str = "HTML",
        disable_preview: bool = False,
        reply_to_message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a message to a Telegram chat.

        Args:
            chat_id: Target chat ID (user ID or group ID)
            text: Message text to send
            parse_mode: Parse mode (HTML, Markdown)
            disable_preview: Disable link preview
            reply_to_message_id: Reply to specific message

        Returns:
            Result dictionary with success status and message info
        """
        try:
            if not self.telegram_client or not self.telegram_client.is_running:
                return {
                    "success": False,
                    "error": "Telegram bot is not running",
                    "skill": "send_telegram_message"
                }

            result = await self.telegram_client.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_preview,
                reply_to_message_id=reply_to_message_id
            )

            if result:
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "chat_id": result.get("chat_id"),
                    "timestamp": result.get("date"),
                    "text": result.get("text"),
                    "skill": "send_telegram_message"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send message",
                    "skill": "send_telegram_message"
                }

        except Exception as e:
            logger.error(f"Error in send_message skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "send_telegram_message"
            }

    async def get_chat_history(
        self,
        chat_id: Union[int, str],
        limit: int = 100,
        offset: int = 0,
        message_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get chat history from a Telegram chat.

        Args:
            chat_id: Chat ID to get history from
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip
            message_types: Filter by message types (text, document, photo, etc.)

        Returns:
            Result dictionary with messages list
        """
        try:
            if not self.telegram_client or not self.telegram_client.is_running:
                return {
                    "success": False,
                    "error": "Telegram bot is not running",
                    "skill": "get_telegram_chat_history"
                }

            messages = await self.telegram_client.get_chat_history(
                chat_id=chat_id,
                limit=limit,
                offset=offset
            )

            # Filter by message types if specified
            if message_types:
                messages = [msg for msg in messages if msg.get("message_type") in message_types]

            # Process messages for Claude consumption
            processed_messages = []
            for msg in messages:
                processed_msg = {
                    "message_id": msg.get("message_id"),
                    "date": msg.get("date"),
                    "text": msg.get("text", ""),
                    "from_user": msg.get("from_user"),
                    "message_type": msg.get("message_type"),
                    "timestamp": msg.get("date").isoformat() if msg.get("date") else None
                }

                # Add file information if present
                if msg.get("document"):
                    processed_msg["file_info"] = {
                        "file_id": msg["document"].get("file_id"),
                        "file_name": msg["document"].get("file_name"),
                        "file_size": msg["document"].get("file_size")
                    }

                processed_messages.append(processed_msg)

            return {
                "success": True,
                "messages": processed_messages,
                "total_count": len(processed_messages),
                "chat_id": chat_id,
                "skill": "get_telegram_chat_history"
            }

        except Exception as e:
            logger.error(f"Error in get_chat_history skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "get_telegram_chat_history"
            }

    async def send_file(
        self,
        chat_id: Union[int, str],
        file_path: str,
        caption: Optional[str] = None,
        reply_to_message_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send a file to a Telegram chat.

        Args:
            chat_id: Target chat ID
            file_path: Path to file to send
            caption: Optional file caption
            reply_to_message_id: Reply to specific message

        Returns:
            Result dictionary with file information
        """
        try:
            if not self.telegram_client or not self.telegram_client.is_running:
                return {
                    "success": False,
                    "error": "Telegram bot is not running",
                    "skill": "send_telegram_file"
                }

            result = await self.telegram_client.send_file(
                chat_id=chat_id,
                file_path=file_path,
                caption=caption,
                reply_to_message_id=reply_to_message_id
            )

            if result:
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "chat_id": result.get("chat_id"),
                    "document_id": result.get("document_id"),
                    "file_name": result.get("file_name"),
                    "file_size": result.get("file_size"),
                    "caption": result.get("caption"),
                    "skill": "send_telegram_file"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send file",
                    "skill": "send_telegram_file"
                }

        except Exception as e:
            logger.error(f"Error in send_file skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "send_telegram_file"
            }

    async def analyze_file(
        self,
        file_path: str,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analyze a file from Telegram.

        Args:
            file_path: Path to file to analyze
            analysis_type: Type of analysis (summary, structure, content)

        Returns:
            Result dictionary with analysis information
        """
        try:
            if not self.file_manager:
                return {
                    "success": False,
                    "error": "File manager not available",
                    "skill": "analyze_telegram_file"
                }

            # Analyze file based on type
            if analysis_type == "summary":
                result = await self.file_manager.create_file_summary(file_path)
            elif analysis_type == "structure":
                result = await self.file_manager.analyze_file_structure(file_path)
            elif analysis_type == "content":
                result = await self.file_manager.extract_file_content(file_path)
            else:
                result = await self.file_manager.create_file_summary(file_path)

            return {
                "success": True,
                "analysis_type": analysis_type,
                "file_path": file_path,
                "result": result,
                "skill": "analyze_telegram_file"
            }

        except Exception as e:
            logger.error(f"Error in analyze_file skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "analyze_telegram_file"
            }

    async def get_chat_info(self, chat_id: Union[int, str]) -> Dict[str, Any]:
        """
        Get information about a Telegram chat.

        Args:
            chat_id: Chat ID to get info for

        Returns:
            Result dictionary with chat information
        """
        try:
            if not self.telegram_client or not self.telegram_client.is_running:
                return {
                    "success": False,
                    "error": "Telegram bot is not running",
                    "skill": "get_telegram_chat_info"
                }

            chat_info = await self.telegram_client.get_chat_info(chat_id)

            if chat_info:
                return {
                    "success": True,
                    "chat_id": chat_info.get("id"),
                    "type": chat_info.get("type"),
                    "title": chat_info.get("title"),
                    "username": chat_info.get("username"),
                    "first_name": chat_info.get("first_name"),
                    "last_name": chat_info.get("last_name"),
                    "description": chat_info.get("description"),
                    "skill": "get_telegram_chat_info"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to get chat info",
                    "skill": "get_telegram_chat_info"
                }

        except Exception as e:
            logger.error(f"Error in get_chat_info skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "get_telegram_chat_info"
            }

    async def manage_users(
        self,
        action: str,
        user_id: Optional[int] = None,
        permission_level: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Manage Telegram user permissions.

        Args:
            action: Action to perform (authorize, revoke, block, unblock)
            user_id: User ID to manage
            permission_level: Permission level for authorize action

        Returns:
            Result dictionary with operation status
        """
        try:
            if not self.auth_manager:
                return {
                    "success": False,
                    "error": "Auth manager not available",
                    "skill": "manage_telegram_users"
                }

            if action == "authorize" and user_id and permission_level:
                success = await self.auth_manager.authorize_user(user_id, permission_level)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "permission_level": permission_level,
                    "skill": "manage_telegram_users"
                }

            elif action == "revoke" and user_id:
                success = await self.auth_manager.revoke_user_authorization(user_id)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "skill": "manage_telegram_users"
                }

            elif action == "block" and user_id:
                success = await self.auth_manager.block_user(user_id)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "skill": "manage_telegram_users"
                }

            elif action == "unblock" and user_id:
                success = await self.auth_manager.unblock_user(user_id)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "skill": "manage_telegram_users"
                }

            else:
                return {
                    "success": False,
                    "error": "Invalid action or missing parameters",
                    "skill": "manage_telegram_users"
                }

        except Exception as e:
            logger.error(f"Error in manage_users skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "manage_telegram_users"
            }

    async def get_bot_status(self) -> Dict[str, Any]:
        """
        Get Telegram bot status and information.

        Returns:
            Result dictionary with bot status
        """
        try:
            if not self.telegram_client:
                return {
                    "success": False,
                    "error": "Telegram client not initialized",
                    "skill": "telegram_bot_status"
                }

            bot_info = self.telegram_client.get_bot_info()
            auth_stats = self.auth_manager.get_statistics() if self.auth_manager else {}
            file_stats = self.file_manager.get_statistics() if self.file_manager else {}

            return {
                "success": True,
                "is_running": self.telegram_client.is_running,
                "bot_info": bot_info,
                "auth_statistics": auth_stats,
                "file_statistics": file_stats,
                "skill": "telegram_bot_status"
            }

        except Exception as e:
            logger.error(f"Error in get_bot_status skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "telegram_bot_status"
            }

    async def search_messages(
        self,
        chat_id: Union[int, str],
        query: str,
        limit: int = 50,
        message_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for messages in a Telegram chat.

        Args:
            chat_id: Chat ID to search in
            query: Search query
            limit: Maximum number of results
            message_type: Filter by message type

        Returns:
            Result dictionary with search results
        """
        try:
            # Get chat history
            history_result = await self.get_chat_history(
                chat_id=chat_id,
                limit=limit * 2,  # Get more to search through
                message_types=[message_type] if message_type else None
            )

            if not history_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to get chat history",
                    "skill": "search_telegram_messages"
                }

            # Search through messages
            messages = history_result["messages"]
            query_lower = query.lower()
            matching_messages = []

            for msg in messages:
                text = msg.get("text", "").lower()
                if query_lower in text:
                    matching_messages.append(msg)

                if len(matching_messages) >= limit:
                    break

            return {
                "success": True,
                "query": query,
                "chat_id": chat_id,
                "results": matching_messages,
                "total_found": len(matching_messages),
                "skill": "search_telegram_messages"
            }

        except Exception as e:
            logger.error(f"Error in search_messages skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "search_telegram_messages"
            }

    async def voice_optimization(
        self,
        text: str,
        optimization_type: str = "readability"
    ) -> Dict[str, Any]:
        """
        Optimize text for voice output in Telegram.

        Args:
            text: Text to optimize
            optimization_type: Type of optimization (readability, pronunciation, pacing)

        Returns:
            Result dictionary with optimized text
        """
        try:
            # Import voice optimization tools if available
            try:
                from ...tools.voice_optimization import VoiceOptimizer
                optimizer = VoiceOptimizer()
            except ImportError:
                # Simple fallback optimization
                optimizer = None

            if optimizer:
                if optimization_type == "readability":
                    optimized = await optimizer.optimize_for_readability(text)
                elif optimization_type == "pronunciation":
                    optimized = await optimizer.optimize_for_pronunciation(text)
                elif optimization_type == "pacing":
                    optimized = await optimizer.optimize_for_pacing(text)
                else:
                    optimized = await optimizer.optimize_for_readability(text)
            else:
                # Basic optimization
                optimized = self._basic_voice_optimization(text)

            return {
                "success": True,
                "original_text": text,
                "optimized_text": optimized,
                "optimization_type": optimization_type,
                "skill": "telegram_voice_optimization"
            }

        except Exception as e:
            logger.error(f"Error in voice_optimization skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "telegram_voice_optimization"
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
        Get list of available Telegram skills for Claude.

        Returns:
            Dictionary of available skills with descriptions
        """
        return {
            "send_telegram_message": {
                "description": "Send a text message to a Telegram chat",
                "parameters": {
                    "chat_id": "Target chat ID (required)",
                    "text": "Message text to send (required)",
                    "parse_mode": "Parse mode (optional, default: HTML)",
                    "disable_preview": "Disable link preview (optional, default: False)",
                    "reply_to_message_id": "Reply to specific message (optional)"
                }
            },
            "get_telegram_chat_history": {
                "description": "Get message history from a Telegram chat",
                "parameters": {
                    "chat_id": "Chat ID to get history from (required)",
                    "limit": "Maximum number of messages (optional, default: 100)",
                    "offset": "Number of messages to skip (optional, default: 0)",
                    "message_types": "Filter by message types (optional)"
                }
            },
            "send_telegram_file": {
                "description": "Send a file to a Telegram chat",
                "parameters": {
                    "chat_id": "Target chat ID (required)",
                    "file_path": "Path to file to send (required)",
                    "caption": "File caption (optional)",
                    "reply_to_message_id": "Reply to specific message (optional)"
                }
            },
            "analyze_telegram_file": {
                "description": "Analyze a file from Telegram",
                "parameters": {
                    "file_path": "Path to file to analyze (required)",
                    "analysis_type": "Type of analysis (summary/structure/content, optional, default: summary)"
                }
            },
            "get_telegram_chat_info": {
                "description": "Get information about a Telegram chat",
                "parameters": {
                    "chat_id": "Chat ID to get info for (required)"
                }
            },
            "manage_telegram_users": {
                "description": "Manage Telegram user permissions",
                "parameters": {
                    "action": "Action to perform (authorize/revoke/block/unblock, required)",
                    "user_id": "User ID to manage (required for most actions)",
                    "permission_level": "Permission level for authorize action (optional)"
                }
            },
            "telegram_bot_status": {
                "description": "Get Telegram bot status and information",
                "parameters": {}
            },
            "search_telegram_messages": {
                "description": "Search for messages in a Telegram chat",
                "parameters": {
                    "chat_id": "Chat ID to search in (required)",
                    "query": "Search query (required)",
                    "limit": "Maximum number of results (optional, default: 50)",
                    "message_type": "Filter by message type (optional)"
                }
            },
            "telegram_voice_optimization": {
                "description": "Optimize text for voice output in Telegram",
                "parameters": {
                    "text": "Text to optimize (required)",
                    "optimization_type": "Type of optimization (readability/pronunciation/pacing, optional, default: readability)"
                }
            }
        }

    async def execute_skill(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a Telegram skill.

        Args:
            skill_name: Name of skill to execute
            **kwargs: Skill parameters

        Returns:
            Result from skill execution
        """
        if skill_name not in self.skills:
            return {
                "success": False,
                "error": f"Unknown skill: {skill_name}",
                "available_skills": list(self.skills.keys())
            }

        skill_func = self.skills[skill_name]
        return await skill_func(**kwargs)