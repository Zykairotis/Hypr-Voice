"""
Discord Skills for Claude Code SDK Integration

This module provides Claude Code SDK skills for Discord bot integration,
enabling Claude to interact with Discord servers, channels, and files.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DiscordSkills:
    """
    Claude Code SDK skills for Discord bot integration.

    Provides capabilities for:
    - Sending and receiving Discord messages
    - Managing servers and channels
    - Processing files and media
    - Bot administration
    - User and role management
    """

    def __init__(self, discord_client, message_handler, file_manager, auth_manager):
        """
        Initialize Discord skills.

        Args:
            discord_client: Initialized Discord client
            message_handler: Discord message handler
            file_manager: Discord file manager
            auth_manager: Discord authentication manager
        """
        self.discord_client = discord_client
        self.message_handler = message_handler
        self.file_manager = file_manager
        self.auth_manager = auth_manager

        # Skills registry for Claude Code SDK
        self.skills = {
            'send_discord_message': self.send_message,
            'get_discord_channel_history': self.get_channel_history,
            'send_discord_file': self.send_file,
            'analyze_discord_file': self.analyze_file,
            'get_discord_server_info': self.get_server_info,
            'get_discord_channel_info': self.get_channel_info,
            'manage_discord_permissions': self.manage_permissions,
            'discord_bot_status': self.get_bot_status,
            'search_discord_messages': self.search_messages,
            'discord_voice_optimization': self.voice_optimization,
            'list_discord_channels': self.list_channels,
            'create_discord_embed': self.create_embed
        }

    async def send_message(
        self,
        channel_id: int,
        text: str,
        embed_title: Optional[str] = None,
        embed_description: Optional[str] = None,
        embed_fields: Optional[List[tuple]] = None,
        embed_color: str = "blue"
    ) -> Dict[str, Any]:
        """
        Send a message to a Discord channel.

        Args:
            channel_id: Target channel ID
            text: Message text to send
            embed_title: Optional embed title
            embed_description: Optional embed description
            embed_fields: Optional list of (name, value) tuples for embed fields
            embed_color: Embed color (blue, green, red, etc.)

        Returns:
            Result dictionary with success status and message info
        """
        try:
            if not self.discord_client or not self.discord_client.is_running:
                return {
                    "success": False,
                    "error": "Discord bot is not running",
                    "skill": "send_discord_message"
                }

            import discord

            # Create embed if embed parameters provided
            embed = None
            if embed_title or embed_description or embed_fields:
                color_map = {
                    "blue": discord.Color.blue(),
                    "green": discord.Color.green(),
                    "red": discord.Color.red(),
                    "yellow": discord.Color.yellow(),
                    "purple": discord.Color.purple(),
                    "orange": discord.Color.orange()
                }
                color = color_map.get(embed_color.lower(), discord.Color.blue())

                embed = discord.Embed(
                    title=embed_title,
                    description=embed_description,
                    color=color,
                    timestamp=datetime.utcnow()
                )

                if embed_fields:
                    for name, value in embed_fields:
                        embed.add_field(name=name, value=value, inline=False)

                embed.set_footer(text="Helper Agent Bot")

            result = await self.discord_client.send_message(
                channel_id=channel_id,
                text=text,
                embed=embed
            )

            if result:
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "channel_id": result.get("channel_id"),
                    "content": result.get("content"),
                    "timestamp": result.get("timestamp"),
                    "attachments": result.get("attachments", []),
                    "skill": "send_discord_message"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send message",
                    "skill": "send_discord_message"
                }

        except Exception as e:
            logger.error(f"Error in send_message skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "send_discord_message"
            }

    async def get_channel_history(
        self,
        channel_id: int,
        limit: int = 100,
        before_date: Optional[datetime] = None,
        message_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get message history from a Discord channel.

        Args:
            channel_id: Channel ID to get history from
            limit: Maximum number of messages to retrieve
            before_date: Get messages before this date
            message_types: Filter by message types (text, file, embed, etc.)

        Returns:
            Result dictionary with messages list
        """
        try:
            if not self.discord_client or not self.discord_client.is_running:
                return {
                    "success": False,
                    "error": "Discord bot is not running",
                    "skill": "get_discord_channel_history"
                }

            messages = await self.discord_client.get_channel_history(
                channel_id=channel_id,
                limit=limit,
                before=before_date
            )

            # Filter by message types if specified
            if message_types:
                messages = [msg for msg in messages if msg.get("message_type") in message_types]

            # Process messages for Claude consumption
            processed_messages = []
            for msg in messages:
                processed_msg = {
                    "message_id": msg.get("message_id"),
                    "content": msg.get("content", ""),
                    "author": msg.get("author", {}),
                    "timestamp": msg.get("timestamp").isoformat() if msg.get("timestamp") else None,
                    "message_type": msg.get("message_type"),
                    "attachments": msg.get("attachments", [])
                }

                processed_messages.append(processed_msg)

            return {
                "success": True,
                "messages": processed_messages,
                "total_count": len(processed_messages),
                "channel_id": channel_id,
                "skill": "get_discord_channel_history"
            }

        except Exception as e:
            logger.error(f"Error in get_channel_history skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "get_discord_channel_history"
            }

    async def send_file(
        self,
        channel_id: int,
        file_path: str,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a file to a Discord channel.

        Args:
            channel_id: Target channel ID
            file_path: Path to file to send
            content: Optional message content

        Returns:
            Result dictionary with file information
        """
        try:
            if not self.discord_client or not self.discord_client.is_running:
                return {
                    "success": False,
                    "error": "Discord bot is not running",
                    "skill": "send_discord_file"
                }

            result = await self.discord_client.send_file(
                channel_id=channel_id,
                file_path=file_path,
                content=content
            )

            if result:
                return {
                    "success": True,
                    "message_id": result.get("message_id"),
                    "channel_id": result.get("channel_id"),
                    "file_name": result.get("file_name"),
                    "content": result.get("content"),
                    "attachments": result.get("attachments", []),
                    "timestamp": result.get("timestamp"),
                    "skill": "send_discord_file"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to send file",
                    "skill": "send_discord_file"
                }

        except Exception as e:
            logger.error(f"Error in send_file skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "send_discord_file"
            }

    async def analyze_file(
        self,
        file_path: str,
        analysis_type: str = "summary"
    ) -> Dict[str, Any]:
        """
        Analyze a file from Discord.

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
                    "skill": "analyze_discord_file"
                }

            # Analyze file based on type
            if analysis_type == "summary":
                result = await self.file_manager.create_summary_report(file_path)
            elif analysis_type == "structure":
                result = await self.file_manager.analyze_file(file_path)
            elif analysis_type == "content":
                result = await self.file_manager.process_file_content(file_path)
            else:
                result = await self.file_manager.create_summary_report(file_path)

            return {
                "success": True,
                "analysis_type": analysis_type,
                "file_path": file_path,
                "result": result,
                "skill": "analyze_discord_file"
            }

        except Exception as e:
            logger.error(f"Error in analyze_file skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "analyze_discord_file"
            }

    async def get_server_info(self, guild_id: int) -> Dict[str, Any]:
        """
        Get information about a Discord server.

        Args:
            guild_id: Server ID to get info for

        Returns:
            Result dictionary with server information
        """
        try:
            if not self.discord_client or not self.discord_client.is_running:
                return {
                    "success": False,
                    "error": "Discord bot is not running",
                    "skill": "get_discord_server_info"
                }

            guild = self.discord_client.bot.get_guild(guild_id)
            if not guild:
                return {
                    "success": False,
                    "error": "Server not found or bot not in server",
                    "skill": "get_discord_server_info"
                }

            # Get channels list
            channels = await self.discord_client.get_guild_channels(guild_id)

            return {
                "success": True,
                "guild_id": guild.id,
                "name": guild.name,
                "owner_id": guild.owner_id if guild.owner else None,
                "member_count": guild.member_count,
                "created_at": guild.created_at.isoformat() if guild.created_at else None,
                "features": list(guild.features) if guild.features else [],
                "channels": channels,
                "skill": "get_discord_server_info"
            }

        except Exception as e:
            logger.error(f"Error in get_server_info skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "get_discord_server_info"
            }

    async def get_channel_info(self, channel_id: int) -> Dict[str, Any]:
        """
        Get information about a Discord channel.

        Args:
            channel_id: Channel ID to get info for

        Returns:
            Result dictionary with channel information
        """
        try:
            if not self.discord_client or not self.discord_client.is_running:
                return {
                    "success": False,
                    "error": "Discord bot is not running",
                    "skill": "get_discord_channel_info"
                }

            channel_info = await self.discord_client.get_channel_info(channel_id)

            if channel_info:
                return {
                    "success": True,
                    "channel_id": channel_info.get("id"),
                    "name": channel_info.get("name"),
                    "type": channel_info.get("type"),
                    "guild_id": channel_info.get("guild_id"),
                    "guild_name": channel_info.get("guild_name"),
                    "topic": channel_info.get("topic"),
                    "nsfw": channel_info.get("nsfw"),
                    "position": channel_info.get("position"),
                    "skill": "get_discord_channel_info"
                }
            else:
                return {
                    "success": False,
                    "error": "Failed to get channel info",
                    "skill": "get_discord_channel_info"
                }

        except Exception as e:
            logger.error(f"Error in get_channel_info skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "get_discord_channel_info"
            }

    async def manage_permissions(
        self,
        action: str,
        user_id: int,
        permission_level: Optional[str] = None,
        guild_id: Optional[int] = None,
        channel_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Manage Discord user permissions.

        Args:
            action: Action to perform (authorize, update, block, unblock)
            user_id: User ID to manage
            permission_level: Permission level for authorize/update actions
            guild_id: Guild ID for guild-specific permissions
            channel_id: Channel ID for channel-specific permissions

        Returns:
            Result dictionary with operation status
        """
        try:
            if not self.auth_manager:
                return {
                    "success": False,
                    "error": "Auth manager not available",
                    "skill": "manage_discord_permissions"
                }

            if action == "authorize":
                # Authenticate user first
                import discord
                user = self.discord_client.bot.get_user(user_id)
                guild = self.discord_client.bot.get_guild(guild_id) if guild_id else None
                channel = self.discord_client.bot.get_channel(channel_id) if channel_id else None

                auth_result = await self.auth_manager.authenticate_user(user, guild, channel)

                if auth_result["authenticated"]:
                    # Update permission level if specified
                    if permission_level and permission_level != auth_result["permission_level"]:
                        success = await self.auth_manager.update_user_permission(user_id, permission_level, user_id)
                        return {
                            "success": success,
                            "action": action,
                            "user_id": user_id,
                            "permission_level": permission_level,
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "skill": "manage_discord_permissions"
                        }
                    else:
                        return {
                            "success": True,
                            "action": action,
                            "user_id": user_id,
                            "permission_level": auth_result["permission_level"],
                            "guild_id": guild_id,
                            "channel_id": channel_id,
                            "skill": "manage_discord_permissions"
                        }
                else:
                    return {
                        "success": False,
                        "error": auth_result.get("reason", "Authentication failed"),
                        "skill": "manage_discord_permissions"
                    }

            elif action == "update" and user_id and permission_level:
                success = await self.auth_manager.update_user_permission(user_id, permission_level, user_id)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "permission_level": permission_level,
                    "skill": "manage_discord_permissions"
                }

            elif action == "block" and user_id:
                success = await self.auth_manager.block_user(user_id, user_id)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "skill": "manage_discord_permissions"
                }

            elif action == "unblock" and user_id:
                success = await self.auth_manager.unblock_user(user_id, user_id)
                return {
                    "success": success,
                    "action": action,
                    "user_id": user_id,
                    "skill": "manage_discord_permissions"
                }

            else:
                return {
                    "success": False,
                    "error": "Invalid action or missing parameters",
                    "skill": "manage_discord_permissions"
                }

        except Exception as e:
            logger.error(f"Error in manage_permissions skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "manage_discord_permissions"
            }

    async def get_bot_status(self) -> Dict[str, Any]:
        """
        Get Discord bot status and information.

        Returns:
            Result dictionary with bot status
        """
        try:
            if not self.discord_client:
                return {
                    "success": False,
                    "error": "Discord client not initialized",
                    "skill": "discord_bot_status"
                }

            bot_info = self.discord_client.get_bot_info()
            auth_stats = self.auth_manager.get_statistics() if self.auth_manager else {}
            file_stats = self.file_manager.get_statistics() if self.file_manager else {}

            return {
                "success": True,
                "is_running": self.discord_client.is_running,
                "bot_info": bot_info,
                "auth_statistics": auth_stats,
                "file_statistics": file_stats,
                "skill": "discord_bot_status"
            }

        except Exception as e:
            logger.error(f"Error in get_bot_status skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "discord_bot_status"
            }

    async def search_messages(
        self,
        channel_id: int,
        query: str,
        limit: int = 50,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Search for messages in a Discord channel.

        Args:
            channel_id: Channel ID to search in
            query: Search query
            limit: Maximum number of results
            user_id: Filter by specific user ID

        Returns:
            Result dictionary with search results
        """
        try:
            # Get channel history
            history_result = await self.get_channel_history(
                channel_id=channel_id,
                limit=limit * 2  # Get more to search through
            )

            if not history_result["success"]:
                return {
                    "success": False,
                    "error": "Failed to get channel history",
                    "skill": "search_discord_messages"
                }

            # Search through messages
            messages = history_result["messages"]
            query_lower = query.lower()
            matching_messages = []

            for msg in messages:
                # Filter by user if specified
                if user_id and msg.get("author", {}).get("id") != user_id:
                    continue

                content = msg.get("content", "").lower()
                if query_lower in content:
                    matching_messages.append(msg)

                if len(matching_messages) >= limit:
                    break

            return {
                "success": True,
                "query": query,
                "channel_id": channel_id,
                "user_id": user_id,
                "results": matching_messages,
                "total_found": len(matching_messages),
                "skill": "search_discord_messages"
            }

        except Exception as e:
            logger.error(f"Error in search_messages skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "search_discord_messages"
            }

    async def voice_optimization(
        self,
        text: str,
        optimization_type: str = "readability"
    ) -> Dict[str, Any]:
        """
        Optimize text for voice output in Discord.

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
                "skill": "discord_voice_optimization"
            }

        except Exception as e:
            logger.error(f"Error in voice_optimization skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "discord_voice_optimization"
            }

    async def list_channels(self, guild_id: int) -> Dict[str, Any]:
        """
        List all channels in a Discord server.

        Args:
            guild_id: Server ID to list channels for

        Returns:
            Result dictionary with channels list
        """
        try:
            if not self.discord_client or not self.discord_client.is_running:
                return {
                    "success": False,
                    "error": "Discord bot is not running",
                    "skill": "list_discord_channels"
                }

            channels = await self.discord_client.get_guild_channels(guild_id)

            return {
                "success": True,
                "guild_id": guild_id,
                "channels": channels,
                "total_count": len(channels),
                "skill": "list_discord_channels"
            }

        except Exception as e:
            logger.error(f"Error in list_channels skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "list_discord_channels"
            }

    async def create_embed(
        self,
        title: str,
        description: str,
        fields: Optional[List[Dict[str, str]]] = None,
        color: str = "blue",
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a Discord embed message structure.

        Args:
            title: Embed title
            description: Embed description
            fields: List of field dictionaries with 'name' and 'value' keys
            color: Embed color
            footer_text: Optional footer text

        Returns:
            Result dictionary with embed structure
        """
        try:
            import discord

            color_map = {
                "blue": discord.Color.blue(),
                "green": discord.Color.green(),
                "red": discord.Color.red(),
                "yellow": discord.Color.yellow(),
                "purple": discord.Color.purple(),
                "orange": discord.Color.orange()
            }
            embed_color = color_map.get(color.lower(), discord.Color.blue())

            embed = discord.Embed(
                title=title,
                description=description,
                color=embed_color,
                timestamp=datetime.utcnow()
            )

            if fields:
                for field in fields:
                    embed.add_field(
                        name=field.get("name", ""),
                        value=field.get("value", ""),
                        inline=field.get("inline", False)
                    )

            if footer_text:
                embed.set_footer(text=footer_text)
            else:
                embed.set_footer(text="Helper Agent Bot")

            return {
                "success": True,
                "embed_data": {
                    "title": title,
                    "description": description,
                    "fields": fields,
                    "color": color,
                    "footer_text": footer_text
                },
                "embed_object": embed,
                "skill": "create_discord_embed"
            }

        except Exception as e:
            logger.error(f"Error in create_embed skill: {e}")
            return {
                "success": False,
                "error": str(e),
                "skill": "create_discord_embed"
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
        Get list of available Discord skills for Claude.

        Returns:
            Dictionary of available skills with descriptions
        """
        return {
            "send_discord_message": {
                "description": "Send a message to a Discord channel",
                "parameters": {
                    "channel_id": "Target channel ID (required)",
                    "text": "Message text to send (required)",
                    "embed_title": "Optional embed title",
                    "embed_description": "Optional embed description",
                    "embed_fields": "Optional list of field dictionaries",
                    "embed_color": "Embed color (blue/green/red/etc., optional, default: blue)"
                }
            },
            "get_discord_channel_history": {
                "description": "Get message history from a Discord channel",
                "parameters": {
                    "channel_id": "Channel ID to get history from (required)",
                    "limit": "Maximum number of messages (optional, default: 100)",
                    "before_date": "Get messages before this date (optional)",
                    "message_types": "Filter by message types (optional)"
                }
            },
            "send_discord_file": {
                "description": "Send a file to a Discord channel",
                "parameters": {
                    "channel_id": "Target channel ID (required)",
                    "file_path": "Path to file to send (required)",
                    "content": "Optional message content"
                }
            },
            "analyze_discord_file": {
                "description": "Analyze a file from Discord",
                "parameters": {
                    "file_path": "Path to file to analyze (required)",
                    "analysis_type": "Type of analysis (summary/structure/content, optional, default: summary)"
                }
            },
            "get_discord_server_info": {
                "description": "Get information about a Discord server",
                "parameters": {
                    "guild_id": "Server ID to get info for (required)"
                }
            },
            "get_discord_channel_info": {
                "description": "Get information about a Discord channel",
                "parameters": {
                    "channel_id": "Channel ID to get info for (required)"
                }
            },
            "manage_discord_permissions": {
                "description": "Manage Discord user permissions",
                "parameters": {
                    "action": "Action to perform (authorize/update/block/unblock, required)",
                    "user_id": "User ID to manage (required)",
                    "permission_level": "Permission level (optional)",
                    "guild_id": "Guild ID for guild permissions (optional)",
                    "channel_id": "Channel ID for channel permissions (optional)"
                }
            },
            "discord_bot_status": {
                "description": "Get Discord bot status and information",
                "parameters": {}
            },
            "search_discord_messages": {
                "description": "Search for messages in a Discord channel",
                "parameters": {
                    "channel_id": "Channel ID to search in (required)",
                    "query": "Search query (required)",
                    "limit": "Maximum number of results (optional, default: 50)",
                    "user_id": "Filter by specific user ID (optional)"
                }
            },
            "discord_voice_optimization": {
                "description": "Optimize text for voice output in Discord",
                "parameters": {
                    "text": "Text to optimize (required)",
                    "optimization_type": "Type of optimization (readability/pronunciation/pacing, optional, default: readability)"
                }
            },
            "list_discord_channels": {
                "description": "List all channels in a Discord server",
                "parameters": {
                    "guild_id": "Server ID to list channels for (required)"
                }
            },
            "create_discord_embed": {
                "description": "Create a Discord embed message structure",
                "parameters": {
                    "title": "Embed title (required)",
                    "description": "Embed description (required)",
                    "fields": "List of field dictionaries (optional)",
                    "color": "Embed color (blue/green/red/etc., optional, default: blue)",
                    "footer_text": "Optional footer text"
                }
            }
        }

    async def execute_skill(self, skill_name: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a Discord skill.

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