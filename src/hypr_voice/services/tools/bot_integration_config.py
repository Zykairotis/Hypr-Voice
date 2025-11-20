"""
Unified Bot Integration Configuration

This module provides centralized configuration and management for both Telegram
and Discord bot integrations with the Helper Agent system.
"""

import asyncio
import logging
import json
import os
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import yaml

logger = logging.getLogger(__name__)


@dataclass
class TelegramConfig:
    """Telegram bot configuration."""
    bot_token: str
    enabled: bool = True
    max_file_size_mb: int = 20
    rate_limit_per_minute: int = 30
    authorized_users: List[int] = None
    authorized_chats: List[int] = None
    webhook_url: Optional[str] = None
    webhook_port: int = 8443
    use_webhook: bool = False

    def __post_init__(self):
        if self.authorized_users is None:
            self.authorized_users = []
        if self.authorized_chats is None:
            self.authorized_chats = []


@dataclass
class DiscordConfig:
    """Discord bot configuration."""
    bot_token: str
    enabled: bool = True
    command_prefix: str = "!"
    max_file_size_mb: int = 8
    rate_limit_per_minute: int = 30
    owner_ids: List[int] = None
    allowed_guilds: List[int] = None
    require_guild_membership: bool = True
    default_permission_level: str = "user"

    def __post_init__(self):
        if self.owner_ids is None:
            self.owner_ids = []
        if self.allowed_guilds is None:
            self.allowed_guilds = []


@dataclass
class BotIntegrationConfig:
    """Complete bot integration configuration."""
    telegram: Optional[TelegramConfig] = None
    discord: Optional[DiscordConfig] = None
    helper_agent_enabled: bool = True
    log_level: str = "INFO"
    temp_directory: str = "/tmp/bot_files"
    cleanup_interval_hours: int = 24
    max_concurrent_users: int = 100
    enable_voice_features: bool = True
    enable_file_processing: bool = True
    enable_summarization: bool = True


class BotIntegrationManager:
    """
    Unified manager for Telegram and Discord bot integrations.

    Handles:
    - Configuration management
    - Bot initialization and lifecycle
    - Message routing and processing
    - Helper Agent integration
    - File handling coordination
    - Authentication and security
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize bot integration manager.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path or "config/bot_integration.yaml"
        self.config = BotIntegrationConfig()

        # Bot instances
        self.telegram_client = None
        self.discord_client = None

        # Message handlers
        self.telegram_handler = None
        self.discord_handler = None

        # File managers
        self.telegram_file_manager = None
        self.discord_file_manager = None

        # Auth managers
        self.telegram_auth_manager = None
        self.discord_auth_manager = None

        # Helper Agent integration
        self.helper_agent = None

        # Runtime state
        self.is_running = False
        self.active_users = set()
        self.message_stats = {
            'telegram_messages': 0,
            'discord_messages': 0,
            'files_processed': 0,
            'errors': 0
        }

        # Load configuration
        self._load_configuration()

    def _load_configuration(self):
        """Load configuration from file."""
        try:
            config_file = Path(self.config_path)
            if config_file.exists():
                with open(config_file, 'r') as f:
                    if config_file.suffix.lower() == '.yaml':
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)

                # Convert to config objects
                if 'telegram' in data:
                    self.config.telegram = TelegramConfig(**data['telegram'])
                if 'discord' in data:
                    self.config.discord = DiscordConfig(**data['discord'])

                # Update main config
                for key, value in data.items():
                    if key not in ['telegram', 'discord'] and hasattr(self.config, key):
                        setattr(self.config, key, value)

                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found, using defaults")
                self._create_default_config()

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            self._create_default_config()

    def _create_default_config(self):
        """Create default configuration."""
        # Load from environment variables
        telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        discord_token = os.getenv('DISCORD_BOT_TOKEN')

        if telegram_token:
            self.config.telegram = TelegramConfig(
                bot_token=telegram_token,
                enabled=os.getenv('TELEGRAM_ENABLED', 'true').lower() == 'true'
            )

        if discord_token:
            self.config.discord = DiscordConfig(
                bot_token=discord_token,
                enabled=os.getenv('DISCORD_ENABLED', 'true').lower() == 'true'
            )

        # General settings
        self.config.log_level = os.getenv('BOT_LOG_LEVEL', 'INFO')
        self.config.temp_directory = os.getenv('BOT_TEMP_DIR', '/tmp/bot_files')
        self.config.helper_agent_enabled = os.getenv('HELPER_AGENT_ENABLED', 'true').lower() == 'true'

    async def initialize(self) -> bool:
        """
        Initialize the bot integration system.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing bot integration system...")

            # Create temp directory
            Path(self.config.temp_directory).mkdir(parents=True, exist_ok=True)

            # Initialize Helper Agent if enabled
            if self.config.helper_agent_enabled:
                await self._initialize_helper_agent()

            # Initialize Telegram if enabled
            if self.config.telegram and self.config.telegram.enabled:
                await self._initialize_telegram()

            # Initialize Discord if enabled
            if self.config.discord and self.config.discord.enabled:
                await self._initialize_discord()

            # Start cleanup task
            asyncio.create_task(self._cleanup_task())

            logger.info("Bot integration system initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize bot integration system: {e}")
            return False

    async def start(self) -> bool:
        """
        Start the bot integration system.

        Returns:
            True if started successfully, False otherwise
        """
        try:
            if not await self.initialize():
                return False

            logger.info("Starting bot integration system...")

            # Start Telegram bot
            if self.telegram_client:
                if self.config.telegram.use_webhook:
                    await self.telegram_client.start(
                        webhook_url=self.config.telegram.webhook_url,
                        port=self.config.telegram.webhook_port
                    )
                else:
                    # Start Telegram in background
                    asyncio.create_task(self.telegram_client.start())
                logger.info("Telegram bot started")

            # Start Discord bot
            if self.discord_client:
                # Start Discord in background
                asyncio.create_task(self.discord_client.start())
                logger.info("Discord bot started")

            self.is_running = True
            logger.info("Bot integration system started successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to start bot integration system: {e}")
            return False

    async def stop(self):
        """Stop the bot integration system."""
        try:
            logger.info("Stopping bot integration system...")

            # Stop Telegram bot
            if self.telegram_client:
                await self.telegram_client.stop()
                logger.info("Telegram bot stopped")

            # Stop Discord bot
            if self.discord_client:
                await self.discord_client.stop()
                logger.info("Discord bot stopped")

            self.is_running = False
            logger.info("Bot integration system stopped")

        except Exception as e:
            logger.error(f"Error stopping bot integration system: {e}")

    async def _initialize_helper_agent(self):
        """Initialize Helper Agent integration."""
        try:
            # Import Helper Agent
            try:
                from ...helper_agent import HelperAgent
                self.helper_agent = HelperAgent()
                logger.info("Helper Agent initialized")
            except ImportError:
                logger.warning("Helper Agent not available, running in standalone mode")
                self.helper_agent = None

        except Exception as e:
            logger.error(f"Error initializing Helper Agent: {e}")
            self.helper_agent = None

    async def _initialize_telegram(self):
        """Initialize Telegram bot."""
        try:
            from .telegram_tool import TelegramClient, TelegramMessageHandler, TelegramFileManager, TelegramAuthManager

            # Initialize Telegram client
            self.telegram_client = TelegramClient(self.config.telegram.bot_token)
            await self.telegram_client.initialize()

            # Initialize auth manager
            telegram_auth_config = {
                'authorized_users': self.config.telegram.authorized_users,
                'authorized_chats': self.config.telegram.authorized_chats,
                'max_requests_per_minute': self.config.telegram.rate_limit_per_minute
            }
            self.telegram_auth_manager = TelegramAuthManager(telegram_auth_config)

            # Initialize file manager
            self.telegram_file_manager = TelegramFileManager(
                self.telegram_client.bot,
                temp_dir=os.path.join(self.config.temp_directory, 'telegram')
            )

            # Initialize message handler
            self.telegram_handler = TelegramMessageHandler(
                self.telegram_client,
                self.helper_agent,
                self.telegram_file_manager,
                self.telegram_auth_manager
            )

            # Register message handler
            self.telegram_client.add_message_handler(self.telegram_handler.handle_message)

            logger.info("Telegram integration initialized")

        except Exception as e:
            logger.error(f"Error initializing Telegram: {e}")
            raise

    async def _initialize_discord(self):
        """Initialize Discord bot."""
        try:
            from .discord_tool import DiscordClient, DiscordMessageHandler, DiscordFileManager, DiscordAuthManager

            # Initialize Discord client
            self.discord_client = DiscordClient(
                self.config.discord.bot_token,
                command_prefix=self.config.discord.command_prefix
            )
            await self.discord_client.initialize()

            # Initialize auth manager
            discord_auth_config = {
                'owner_ids': self.config.discord.owner_ids,
                'allowed_guilds': self.config.discord.allowed_guilds,
                'require_guild_membership': self.config.discord.require_guild_membership,
                'default_rate_limit': self.config.discord.rate_limit_per_minute
            }
            self.discord_auth_manager = DiscordAuthManager(discord_auth_config)

            # Initialize file manager
            self.discord_file_manager = DiscordFileManager(
                self.discord_client.bot,
                temp_dir=os.path.join(self.config.temp_directory, 'discord')
            )

            # Initialize message handler
            self.discord_handler = DiscordMessageHandler(
                self.discord_client,
                self.helper_agent
            )

            # Set up Discord message handling
            @self.discord_client.bot.event
            async def on_message(message):
                if not message.author.bot:
                    await self.discord_handler.handle_message(message)

            logger.info("Discord integration initialized")

        except Exception as e:
            logger.error(f"Error initializing Discord: {e}")
            raise

    async def _cleanup_task(self):
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(self.config.cleanup_interval_hours * 3600)

                # Clean up temp files
                if self.telegram_file_manager:
                    await self.telegram_file_manager.cleanup_temp_files()
                if self.discord_file_manager:
                    await self.discord_file_manager.cleanup_temp_files()

                # Clean up auth sessions
                if self.telegram_auth_manager:
                    await self.telegram_auth_manager.cleanup_expired_sessions()
                if self.discord_auth_manager:
                    await self.discord_auth_manager.cleanup_expired_sessions()

                logger.info("Periodic cleanup completed")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        stats = {
            'is_running': self.is_running,
            'active_users': len(self.active_users),
            'message_stats': self.message_stats.copy(),
            'config': {
                'telegram_enabled': self.config.telegram.enabled if self.config.telegram else False,
                'discord_enabled': self.config.discord.enabled if self.config.discord else False,
                'helper_agent_enabled': self.config.helper_agent_enabled,
                'voice_features_enabled': self.config.enable_voice_features,
                'file_processing_enabled': self.config.enable_file_processing
            }
        }

        # Add bot-specific stats
        if self.telegram_client:
            stats['telegram_bot_info'] = self.telegram_client.get_bot_info()
        if self.discord_client:
            stats['discord_bot_info'] = self.discord_client.get_bot_info()

        # Add auth stats
        if self.telegram_auth_manager:
            stats['telegram_auth_stats'] = self.telegram_auth_manager.get_statistics()
        if self.discord_auth_manager:
            stats['discord_auth_stats'] = self.discord_auth_manager.get_statistics()

        return stats

    def get_configuration(self) -> Dict[str, Any]:
        """Get current configuration (without sensitive tokens)."""
        config_dict = asdict(self.config)

        # Remove sensitive tokens
        if config_dict.get('telegram'):
            config_dict['telegram']['bot_token'] = '***' if config_dict['telegram']['bot_token'] else None
        if config_dict.get('discord'):
            config_dict['discord']['bot_token'] = '***' if config_dict['discord']['bot_token'] else None

        return config_dict

    async def update_configuration(self, updates: Dict[str, Any]) -> bool:
        """
        Update configuration.

        Args:
            updates: Configuration updates

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Apply updates
            for key, value in updates.items():
                if hasattr(self.config, key):
                    setattr(self.config, key, value)

            # Save configuration
            await self._save_configuration()

            logger.info("Configuration updated successfully")
            return True

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

    async def _save_configuration(self):
        """Save configuration to file."""
        try:
            config_file = Path(self.config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)

            config_dict = asdict(self.config)

            with open(config_file, 'w') as f:
                if config_file.suffix.lower() == '.yaml':
                    yaml.dump(config_dict, f, default_flow_style=False)
                else:
                    json.dump(config_dict, f, indent=2)

            logger.info(f"Configuration saved to {self.config_path}")

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")

    async def send_telegram_message(self, chat_id: int, text: str, **kwargs) -> bool:
        """Send message via Telegram bot."""
        if not self.telegram_client:
            logger.error("Telegram client not initialized")
            return False

        try:
            result = await self.telegram_client.send_message(chat_id, text, **kwargs)
            if result:
                self.message_stats['telegram_messages'] += 1
            return result is not None

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            self.message_stats['errors'] += 1
            return False

    async def send_discord_message(self, channel_id: int, text: str, **kwargs) -> bool:
        """Send message via Discord bot."""
        if not self.discord_client:
            logger.error("Discord client not initialized")
            return False

        try:
            result = await self.discord_client.send_message(channel_id, text, **kwargs)
            if result:
                self.message_stats['discord_messages'] += 1
            return result is not None

        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            self.message_stats['errors'] += 1
            return False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Factory function for easy manager creation
async def create_bot_integration_manager(config_path: Optional[str] = None) -> BotIntegrationManager:
    """
    Create and initialize a bot integration manager.

    Args:
        config_path: Optional path to configuration file

    Returns:
        Initialized bot integration manager
    """
    manager = BotIntegrationManager(config_path)
    success = await manager.initialize()

    if not success:
        raise RuntimeError("Failed to initialize bot integration manager")

    return manager