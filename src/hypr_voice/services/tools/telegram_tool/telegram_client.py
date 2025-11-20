"""
Telegram Client for Helper Agent

This module provides the main Telegram Bot API client for the Helper Agent system.
It handles bot initialization, message sending, and basic bot operations.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import os
from dotenv import load_dotenv

try:
    from telegram import Update, Bot, Document, PhotoSize
    from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
    from telegram.constants import ParseMode
except ImportError:
    logging.error("python-telegram-bot not installed. Run: pip install 'python-telegram-bot[all]'")
    raise ImportError("python-telegram-bot is required for Telegram integration")

logger = logging.getLogger(__name__)

load_dotenv()


class TelegramClient:
    """
    Telegram Bot API client for Helper Agent integration.

    Provides functionality to:
    - Initialize and run Telegram bot
    - Send messages, files, and alerts
    - Read chat history
    - Handle user interactions
    """

    def __init__(self, bot_token: Optional[str] = None):
        """
        Initialize Telegram client.

        Args:
            bot_token: Telegram bot token (defaults to environment variable)
        """
        self.bot_token = bot_token or os.getenv('TELEGRAM_BOT_TOKEN')
        self.application: Optional[Application] = None
        self.bot: Optional[Bot] = None
        self.is_running = False
        self.message_handlers = []

        # Configuration
        self.max_file_size_mb = 20  # Telegram standard limit
        self.rate_limit_per_minute = 30

        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable or bot_token parameter is required")

    async def initialize(self) -> bool:
        """
        Initialize the Telegram bot application.

        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create application with token
            self.application = Application.builder().token(self.bot_token).build()
            self.bot = self.application.bot

            # Get bot information to verify connection
            bot_info = await self.bot.get_me()
            logger.info(f"Telegram bot initialized: @{bot_info.username} (ID: {bot_info.id})")

            # Set up default handlers
            await self._setup_default_handlers()

            logger.info("Telegram client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Telegram client: {e}")
            return False

    async def start(self, webhook_url: Optional[str] = None, port: int = 8443):
        """
        Start the Telegram bot.

        Args:
            webhook_url: Optional webhook URL (if None, runs in polling mode)
            port: Port for webhook server
        """
        if not self.application:
            await self.initialize()

        try:
            if webhook_url:
                # Start with webhook
                await self.application.bot.set_webhook(url=webhook_url)
                await self.application.run_webhook(
                    listen="0.0.0.0",
                    port=port,
                    webhook_url=webhook_url
                )
            else:
                # Start with polling
                await self.application.initialize()
                await self.application.start()
                await self.application.updater.start_polling()

            self.is_running = True
            logger.info("Telegram bot started successfully")

        except Exception as e:
            logger.error(f"Failed to start Telegram bot: {e}")
            raise

    async def stop(self):
        """Stop the Telegram bot."""
        try:
            if self.application:
                await self.application.stop()
                await self.application.shutdown()

            self.is_running = False
            logger.info("Telegram bot stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping Telegram bot: {e}")

    async def send_message(
        self,
        chat_id: Union[int, str],
        text: str,
        parse_mode: Optional[str] = ParseMode.HTML,
        disable_web_page_preview: bool = False,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a text message to a chat.

        Args:
            chat_id: Target chat ID (user ID or group ID)
            text: Message text to send
            parse_mode: Parse mode (HTML, Markdown, etc.)
            disable_web_page_preview: Disable link preview
            reply_to_message_id: Reply to specific message

        Returns:
            Dictionary containing message information or None if failed
        """
        try:
            message = await self.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                reply_to_message_id=reply_to_message_id
            )

            return {
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "text": message.text,
                "date": message.date,
                "from_user": message.from_user.username if message.from_user else None
            }

        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")
            return None

    async def send_file(
        self,
        chat_id: Union[int, str],
        file_path: str,
        caption: Optional[str] = None,
        reply_to_message_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Send a file to a chat.

        Args:
            chat_id: Target chat ID
            file_path: Path to file to send
            caption: Optional file caption
            reply_to_message_id: Reply to specific message

        Returns:
            Dictionary containing file information or None if failed
        """
        try:
            # Check file size
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if file_size_mb > self.max_file_size_mb:
                logger.error(f"File size {file_size_mb:.2f}MB exceeds limit of {self.max_file_size_mb}MB")
                return None

            with open(file_path, 'rb') as file:
                message = await self.bot.send_document(
                    chat_id=chat_id,
                    document=file,
                    caption=caption,
                    reply_to_message_id=reply_to_message_id
                )

            return {
                "message_id": message.message_id,
                "chat_id": message.chat.id,
                "document_id": message.document.file_id,
                "file_name": message.document.file_name,
                "file_size": message.document.file_size,
                "caption": message.caption
            }

        except Exception as e:
            logger.error(f"Failed to send file {file_path} to {chat_id}: {e}")
            return None

    async def get_chat_history(
        self,
        chat_id: Union[int, str],
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get chat history.

        Args:
            chat_id: Chat ID to get history from
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip

        Returns:
            List of message dictionaries
        """
        try:
            # Note: This requires bot to be admin in the chat
            messages = []
            message_count = 0
            skip_count = 0

            async for message in self.application.bot.get_chat_history(
                chat_id=chat_id,
                limit=limit + offset
            ):
                if skip_count < offset:
                    skip_count += 1
                    continue

                if message_count >= limit:
                    break

                message_data = {
                    "message_id": message.message_id,
                    "date": message.date,
                    "text": message.text or "",
                    "from_user": message.from_user.username if message.from_user else None,
                    "message_type": self._get_message_type(message)
                }

                # Add file information if present
                if message.document:
                    message_data["document"] = {
                        "file_id": message.document.file_id,
                        "file_name": message.document.file_name,
                        "file_size": message.document.file_size
                    }

                messages.append(message_data)
                message_count += 1

            return messages

        except Exception as e:
            logger.error(f"Failed to get chat history for {chat_id}: {e}")
            return []

    async def get_chat_info(self, chat_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        Get information about a chat.

        Args:
            chat_id: Chat ID to get info for

        Returns:
            Dictionary containing chat information or None if failed
        """
        try:
            chat = await self.bot.get_chat(chat_id)

            return {
                "id": chat.id,
                "type": chat.type,
                "title": getattr(chat, 'title', None),
                "username": getattr(chat, 'username', None),
                "first_name": getattr(chat, 'first_name', None),
                "last_name": getattr(chat, 'last_name', None),
                "description": getattr(chat, 'description', None)
            }

        except Exception as e:
            logger.error(f"Failed to get chat info for {chat_id}: {e}")
            return None

    async def _setup_default_handlers(self):
        """Set up default message handlers."""
        # Default command handlers
        self.application.add_handler(CommandHandler("start", self._handle_start))
        self.application.add_handler(CommandHandler("help", self._handle_help))

        # Default message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_text_message))
        self.application.add_handler(MessageHandler(filters.Document.ALL, self._handle_document))
        self.application.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))

    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        await update.message.reply_text(
            "🤖 Hello! I'm the Helper Agent bot for Hypr-Voice.\n\n"
            "I can help you with:\n"
            "• Summarizing long texts\n"
            "• Analyzing content for voice optimization\n"
            "• Planning tasks and workflows\n"
            "• Integrating with Claude Code SDK\n\n"
            "Type /help to see available commands."
        )

    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_text = """
        📋 **Available Commands:**
        • /start - Start the bot
        • /help - Show this help message

        📨 **File Operations:**
        • Send any text file for analysis
        • Send CSV files for processing
        • Send documents for summarization

        💬 **Chat Features:**
        • Send me text to summarize
        • Ask me to analyze content
        • Request task planning help
        """

        await update.message.reply_text(help_text, parse_mode=ParseMode.MARKDOWN)

    async def _handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages."""
        # Store message for potential Claude processing
        message_data = {
            "message_id": update.message.message_id,
            "chat_id": update.message.chat.id,
            "text": update.message.text,
            "from_user": update.message.from_user.username,
            "date": update.message.date,
            "message_type": "text"
        }

        # Log message for debugging
        logger.debug(f"Received text message from {message_data['from_user']}: {message_data['text'][:50]}...")

    async def _handle_document(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle document uploads."""
        document = update.message.document
        message_data = {
            "message_id": update.message.message_id,
            "chat_id": update.message.chat.id,
            "document": {
                "file_id": document.file_id,
                "file_name": document.file_name,
                "file_size": document.file_size,
                "mime_type": document.mime_type
            },
            "from_user": update.message.from_user.username,
            "date": update.message.date,
            "message_type": "document"
        }

        logger.info(f"Received document: {document.file_name} ({document.file_size} bytes)")

    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo uploads."""
        photo = update.message.photo[-1]  # Get highest resolution photo
        message_data = {
            "message_id": update.message.message_id,
            "chat_id": update.message.chat.id,
            "photo": {
                "file_id": photo.file_id,
                "width": photo.width,
                "height": photo.height,
                "file_size": photo.file_size
            },
            "from_user": update.message.from_user.username,
            "date": update.message.date,
            "message_type": "photo"
        }

        logger.debug(f"Received photo from {message_data['from_user']}: {photo.width}x{photo.height}")

    def _get_message_type(self, message) -> str:
        """Get the type of a message."""
        if message.text:
            return "text"
        elif message.document:
            return "document"
        elif message.photo:
            return "photo"
        elif message.audio:
            return "audio"
        elif message.video:
            return "video"
        elif message.sticker:
            return "sticker"
        else:
            return "unknown"

    def add_message_handler(self, handler):
        """Add a custom message handler."""
        self.message_handlers.append(handler)
        if self.application:
            self.application.add_handler(handler)

    def get_bot_info(self) -> Optional[Dict[str, Any]]:
        """Get bot information."""
        if self.bot:
            return {
                "is_running": self.is_running,
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
async def create_telegram_client(bot_token: Optional[str] = None) -> TelegramClient:
    """
    Create and initialize a Telegram client.

    Args:
        bot_token: Optional bot token (defaults to environment variable)

    Returns:
        Initialized Telegram client
    """
    client = TelegramClient(bot_token)
    success = await client.initialize()

    if not success:
        raise RuntimeError("Failed to initialize Telegram client")

    return client