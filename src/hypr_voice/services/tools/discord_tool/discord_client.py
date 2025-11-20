"""
Discord Client for Helper Agent

This module provides the main Discord Bot API client for the Helper Agent system.
It handles bot initialization, message sending, and basic bot operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import os
from dotenv import load_dotenv

try:
    import discord
    from discord.ext import commands
    from discord import File, Embed, Message, TextChannel, User, Member
except ImportError:
    logging.error("discord.py not installed. Run: pip install discord.py")
    raise ImportError("discord.py is required for Discord integration")

logger = logging.getLogger(__name__)

load_dotenv()


class DiscordClient:
    """
    Discord Bot API client for Helper Agent integration.

    Provides functionality to:
    - Initialize and run Discord bot
    - Send messages, files, and alerts
    - Read chat history and channel messages
    - Handle user interactions and server management
    """

    def __init__(self, bot_token: Optional[str] = None, command_prefix: str = "!"):
        """
        Initialize Discord client.

        Args:
            bot_token: Discord bot token (defaults to environment variable)
            command_prefix: Command prefix for bot commands
        """
        self.bot_token = bot_token or os.getenv('DISCORD_BOT_TOKEN')
        self.command_prefix = command_prefix
        self.bot: Optional[commands.Bot] = None
        self.is_running = False
        self.message_handlers = []

        # Configuration
        self.max_file_size_mb = 8  # Discord standard limit
        self.rate_limit_per_minute = 30
        self.allowed_message_types = [
            'message', 'file_upload', 'reaction', 'join', 'leave'
        ]

        if not self.bot_token:
            raise ValueError("DISCORD_BOT_TOKEN environment variable or bot_token parameter is required")

    async def initialize(self) -> bool:
        """
        Initialize the Discord bot application.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Define intents for the bot
            intents = discord.Intents.default()
            intents.messages = True
            intents.message_content = True
            intents.guilds = True
            intents.members = True
            intents.reactions = True

            # Create bot instance with intents
            self.bot = commands.Bot(
                command_prefix=self.command_prefix,
                intents=intents,
                help_command=None  # We'll use custom help command
            )

            # Set up event handlers
            await self._setup_event_handlers()

            # Set up default commands
            await self._setup_default_commands()

            logger.info("Discord client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Discord client: {e}")
            return False

    async def start(self):
        """Start the Discord bot."""
        if not self.bot:
            await self.initialize()

        try:
            await self.bot.start(self.bot_token)
            self.is_running = True
            logger.info("Discord bot started successfully")

        except Exception as e:
            logger.error(f"Failed to start Discord bot: {e}")
            raise

    async def stop(self):
        """Stop the Discord bot."""
        try:
            if self.bot:
                await self.bot.close()

            self.is_running = False
            logger.info("Discord bot stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping Discord bot: {e}")

    async def send_message(
        self,
        channel_id: int,
        text: str,
        embed: Optional[Embed] = None,
        file_path: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a message to a Discord channel.

        Args:
            channel_id: Target channel ID
            text: Message text to send
            embed: Discord embed object
            file_path: Optional file path to attach

        Returns:
            Dictionary containing message information or None if failed
        """
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return None

            if not isinstance(channel, discord.TextChannel):
                logger.error(f"Channel {channel_id} is not a text channel")
                return None

            kwargs = {}
            if embed:
                kwargs['embed'] = embed
            if file_path:
                file = discord.File(file_path)
                kwargs['file'] = file

            message = await channel.send(text, **kwargs)

            return {
                "message_id": message.id,
                "channel_id": message.channel.id,
                "content": message.content,
                "author": message.author.name,
                "timestamp": message.created_at,
                "attachments": [att.url for att in message.attachments]
            }

        except Exception as e:
            logger.error(f"Failed to send message to channel {channel_id}: {e}")
            return None

    async def send_file(
        self,
        channel_id: int,
        file_path: str,
        content: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a file to a Discord channel.

        Args:
            channel_id: Target channel ID
            file_path: Path to file to send
            content: Optional message content

        Returns:
            Dictionary containing file information or None if failed
        """
        try:
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                logger.error(f"File size {file_size_mb:.2f}MB exceeds limit of {self.max_file_size_mb}MB")
                return None

            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                logger.error(f"Invalid channel {channel_id}")
                return None

            file = discord.File(file_path)
            message = await channel.send(content=content, file=file)

            return {
                "message_id": message.id,
                "channel_id": message.channel.id,
                "attachments": [att.url for att in message.attachments],
                "file_name": file.filename,
                "content": message.content
            }

        except Exception as e:
            logger.error(f"Failed to send file {file_path} to channel {channel_id}: {e}")
            return None

    async def get_channel_history(
        self,
        channel_id: int,
        limit: int = 100,
        before: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get message history from a channel.

        Args:
            channel_id: Channel ID to get history from
            limit: Maximum number of messages to retrieve
            before: Get messages before this timestamp

        Returns:
            List of message dictionaries
        """
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel or not isinstance(channel, discord.TextChannel):
                logger.error(f"Invalid channel {channel_id}")
                return []

            messages = []
            async for message in channel.history(limit=limit, before=before):
                if message.author.bot:
                    continue  # Skip bot messages

                message_data = {
                    "message_id": message.id,
                    "content": message.content,
                    "author": {
                        "id": message.author.id,
                        "name": message.author.name,
                        "display_name": message.author.display_name,
                        "is_bot": message.author.bot
                    },
                    "timestamp": message.created_at,
                    "message_type": self._get_message_type(message),
                    "attachments": [att.url for att in message.attachments]
                }

                messages.append(message_data)

            return messages

        except Exception as e:
            logger.error(f"Failed to get channel history for {channel_id}: {e}")
            return []

    async def get_channel_info(self, channel_id: int) -> Optional[Dict[str, Any]]:
        """
        Get information about a channel.

        Args:
            channel_id: Channel ID to get info for

        Returns:
            Dictionary containing channel information or None if failed
        """
        try:
            channel = self.bot.get_channel(channel_id)
            if not channel:
                return None

            return {
                "id": channel.id,
                "name": channel.name,
                "type": str(channel.type),
                "guild_id": channel.guild.id if channel.guild else None,
                "guild_name": channel.guild.name if channel.guild else None,
                "topic": getattr(channel, 'topic', None),
                "nsfw": getattr(channel, 'nsfw', False),
                "position": getattr(channel, 'position', None)
            }

        except Exception as e:
            logger.error(f"Failed to get channel info for {channel_id}: {e}")
            return None

    async def get_guild_channels(self, guild_id: int) -> List[Dict[str, Any]]:
        """
        Get all text channels in a guild.

        Args:
            guild_id: Guild ID to get channels from

        Returns:
            List of channel dictionaries
        """
        try:
            guild = self.bot.get_guild(guild_id)
            if not guild:
                logger.error(f"Guild {guild_id} not found")
                return []

            channels = []
            for channel in guild.text_channels:
                channels.append({
                    "id": channel.id,
                    "name": channel.name,
                    "topic": channel.topic,
                    "nsfw": channel.nsfw,
                    "position": channel.position
                })

            return channels

        except Exception as e:
            logger.error(f"Failed to get channels for guild {guild_id}: {e}")
            return []

    async def _setup_event_handlers(self):
        """Set up Discord event handlers."""

        @self.bot.event
        async def on_ready():
            logger.info(f"Discord bot logged in as {self.bot.user}")
            logger.info(f"Bot is in {len(self.bot.guilds)} servers")

        @self.bot.event
        async def on_message(message: Message):
            # Skip bot messages
            if message.author.bot:
                return

            # Process message through handlers
            message_data = {
                "message_id": message.id,
                "channel_id": message.channel.id,
                "content": message.content,
                "author": {
                    "id": message.author.id,
                    "name": message.author.name,
                    "display_name": message.author.display_name
                },
                "timestamp": message.created_at,
                "guild_id": message.guild.id if message.guild else None,
                "attachments": [att.url for att in message.attachments]
            }

            logger.debug(f"Received message from {message.author.name}: {message.content[:50]}...")

        @self.bot.event
        async def on_guild_join(guild):
            logger.info(f"Bot joined guild: {guild.name}")

        @self.bot.event
        async def on_guild_remove(guild):
            logger.info(f"Bot left guild: {guild.name}")

    async def _setup_default_commands(self):
        """Set up default bot commands."""

        @self.bot.command(name='help')
        async def help_command(ctx):
            """Show help message."""
            help_text = """
            🤖 **Helper Agent Bot Help**

            **Commands:**
            • `!help` - Show this help message
            • `!info` - Show bot information
            • `!analyze` - Analyze attached files
            • `!summarize <text>` - Summarize text

            **Features:**
            • File analysis (CSV, text, documents)
            • Content summarization
            • Voice optimization
            • Claude Code SDK integration
            """

            embed = discord.Embed(
                title="Helper Agent Bot",
                description="AI-powered assistance for voice agent applications",
                color=discord.Color.blue()
            )
            embed.add_field(name="Commands", value=help_text, inline=False)
            embed.set_footer(text="Powered by Hypr-Voice")

            await ctx.send(embed=embed)

        @self.bot.command(name='info')
        async def info_command(ctx):
            """Show bot information."""
            embed = discord.Embed(
                title="Bot Information",
                color=discord.Color.green()
            )
            embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
            embed.add_field(name="Guilds", value=str(len(self.bot.guilds)), inline=True)
            embed.add_field(name="Users", value=str(len(self.bot.users)), inline=True)
            embed.set_footer(text="Helper Agent v1.0.0")

            await ctx.send(embed=embed)

    def _get_message_type(self, message: Message) -> str:
        """Get the type of a message."""
        if message.attachments:
            return "file"
        elif message.embeds:
            return "embed"
        elif message.content:
            return "text"
        else:
            return "other"

    def add_message_handler(self, handler):
        """Add a custom message handler."""
        self.message_handlers.append(handler)

    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """Get bot information."""
        if self.bot:
            return {
                "is_running": self.is_running,
                "user": {
                    "id": self.bot.user.id if self.bot.user else None,
                    "name": self.bot.user.name if self.bot.user else None,
                    "discriminator": self.bot.user.discriminator if self.bot.user else None
                },
                "guilds_count": len(self.bot.guilds),
                "users_count": len(self.bot.users),
                "max_file_size_mb": self.max_file_size_mb,
                "rate_limit_per_minute": self.rate_limit_per_minute,
                "message_handlers_count": len(self.message_handlers)
            }
        return None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Factory function for easy client creation
async def create_discord_client(bot_token: Optional[str] = None, command_prefix: str = "!") -> DiscordClient:
    """
    Create and initialize a Discord client.

    Args:
        bot_token: Optional bot token (defaults to environment variable)
        command_prefix: Command prefix for bot commands

    Returns:
        Initialized Discord client
    """
    client = DiscordClient(bot_token, command_prefix)
    success = await client.initialize()

    if not success:
        raise RuntimeError("Failed to initialize Discord client")

    return client