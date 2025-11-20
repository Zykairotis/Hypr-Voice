"""
Telegram Auth Manager for Helper Agent

This module handles Telegram bot authentication, token management,
and security validation for the Helper Agent system.
"""

import os
import logging
import hashlib
import secrets
from typing import Dict, Optional, List, Any, Set
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    from telegram import Bot, Update
    from telegram.ext import Application, filters
except ImportError:
    raise ImportError("python-telegram-bot is required for Telegram integration")

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class TelegramAuthManager:
    """
    Manages Telegram bot authentication and security.

    Provides functionality to:
    - Validate bot tokens
    - Manage user permissions
    - Track authorized users and chats
    - Handle rate limiting
    - Validate message sources
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Telegram auth manager.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.authorized_users: Set[int] = set()
        self.authorized_chats: Set[int] = set()
        self.blocked_users: Set[int] = set()
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        self.rate_limit_tracker: Dict[int, List[float]] = {}

        # Configuration
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.owner_user_id = self.config.get('owner_user_id')
        self.admin_user_ids = set(self.config.get('admin_user_ids', []))
        self.max_requests_per_minute = self.config.get('max_requests_per_minute', 30)
        self.session_timeout_minutes = self.config.get('session_timeout_minutes', 60)
        self.auth_required = self.config.get('auth_required', False)

        # Security settings
        self.trusted_file_extensions = {
            '.txt', '.md', '.csv', '.json', '.xml', '.yaml', '.yml',
            '.pdf', '.doc', '.docx', '.odt',
            '.jpg', '.jpeg', '.png', '.gif', '.webp'
        }

        # Initialize with owner if provided
        if self.owner_user_id:
            self.authorized_users.add(self.owner_user_id)
            self.authorized_chats.add(self.owner_user_id)

        # Load authorized users from config
        self._load_authorized_users()

        logger.info("Telegram auth manager initialized")

    def _load_authorized_users(self):
        """Load authorized users from configuration."""
        try:
            # Load from config file if exists
            config_file = Path(__file__).parent / 'config' / 'telegram_auth.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    auth_data = json.load(f)

                self.authorized_users.update(auth_data.get('authorized_users', []))
                self.authorized_chats.update(auth_data.get('authorized_chats', []))
                self.blocked_users.update(auth_data.get('blocked_users', []))

                logger.info(f"Loaded {len(self.authorized_users)} authorized users from config")

        except Exception as e:
            logger.warning(f"Could not load auth config: {e}")

    def _save_authorized_users(self):
        """Save authorized users to configuration file."""
        try:
            config_dir = Path(__file__).parent / 'config'
            config_dir.mkdir(exist_ok=True)

            auth_data = {
                "authorized_users": list(self.authorized_users),
                "authorized_chats": list(self.authorized_chats),
                "blocked_users": list(self.blocked_users),
                "updated_at": datetime.now().isoformat()
            }

            config_file = config_dir / 'telegram_auth.json'
            with open(config_file, 'w') as f:
                json.dump(auth_data, f, indent=2)

            logger.info("Saved authorized users configuration")

        except Exception as e:
            logger.error(f"Failed to save auth config: {e}")

    async def validate_bot_token(self, bot_token: Optional[str] = None) -> bool:
        """
        Validate Telegram bot token.

        Args:
            bot_token: Bot token to validate

        Returns:
            True if token is valid, False otherwise
        """
        token_to_validate = bot_token or self.bot_token

        if not token_to_validate:
            logger.error("No bot token provided")
            return False

        try:
            # Create bot instance to validate token
            bot = Bot(token=token_to_validate)
            bot_info = await bot.get_me()

            logger.info(f"Bot token validated successfully for @{bot_info.username} (ID: {bot_info.id})")
            return True

        except Exception as e:
            logger.error(f"Bot token validation failed: {e}")
            return False

    def is_user_authorized(self, user_id: int) -> bool:
        """
        Check if a user is authorized to use the bot.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is authorized, False otherwise
        """
        # If auth is not required, allow all users
        if not self.auth_required:
            return True

        # Check if user is in authorized list or is owner/admin
        return (
            user_id in self.authorized_users or
            user_id == self.owner_user_id or
            user_id in self.admin_user_ids
        )

    def is_chat_authorized(self, chat_id: int) -> bool:
        """
        Check if a chat is authorized for bot operations.

        Args:
            chat_id: Telegram chat ID

        Returns:
            True if chat is authorized, False otherwise
        """
        # If auth is not required, allow all chats
        if not self.auth_required:
            return True

        # Check if chat is in authorized list
        return chat_id in self.authorized_chats

    def is_user_blocked(self, user_id: int) -> bool:
        """
        Check if a user is blocked.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is blocked, False otherwise
        """
        return user_id in self.blocked_users

    def authorize_user(self, user_id: int, added_by: Optional[int] = None) -> bool:
        """
        Add a user to the authorized list.

        Args:
            user_id: Telegram user ID to authorize
            added_by: User ID who added this authorization

        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id in self.authorized_users:
                logger.warning(f"User {user_id} is already authorized")
                return False

            self.authorized_users.add(user_id)
            self._save_authorized_users()

            logger.info(f"Authorized user {user_id} (added by {added_by})")
            return True

        except Exception as e:
            logger.error(f"Failed to authorize user {user_id}: {e}")
            return False

    def revoke_user_authorization(self, user_id: int) -> bool:
        """
        Remove a user from the authorized list.

        Args:
            user_id: Telegram user ID to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.authorized_users:
                logger.warning(f"User {user_id} is not authorized")
                return False

            # Cannot revoke owner or admin users
            if user_id == self.owner_user_id or user_id in self.authorized_users:
                logger.warning(f"Cannot revoke authorization for owner/admin user {user_id}")
                return False

            self.authorized_users.remove(user_id)
            self._save_authorized_users()

            logger.info(f"Revoked authorization for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to revoke user authorization {user_id}: {e}")
            return False

    def authorize_chat(self, chat_id: int, added_by: Optional[int] = None) -> bool:
        """
        Add a chat to the authorized list.

        Args:
            chat_id: Telegram chat ID to authorize
            added_by: User ID who added this authorization

        Returns:
            True if successful, False otherwise
        """
        try:
            if chat_id in self.authorized_chats:
                logger.warning(f"Chat {chat_id} is already authorized")
                return False

            self.authorized_chats.add(chat_id)
            self._save_authorized_users()

            logger.info(f"Authorized chat {chat_id} (added by {added_by})")
            return True

        except Exception as e:
            logger.error(f"Failed to authorize chat {chat_id}: {e}")
            return False

    def block_user(self, user_id: int, blocked_by: Optional[int] = None) -> bool:
        """
        Block a user from using the bot.

        Args:
            user_id: Telegram user ID to block
            blocked_by: User ID who blocked this user

        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id in self.blocked_users:
                logger.warning(f"User {user_id} is already blocked")
                return False

            # Cannot block owner or admin users
            if user_id == self.owner_user_id or user_id in self.admin_user_ids:
                logger.warning(f"Cannot block owner/admin user {user_id}")
                return False

            self.blocked_users.add(user_id)
            self._save_authorized_users()

            logger.info(f"Blocked user {user_id} (blocked by {blocked_by})")
            return True

        except Exception as e:
            logger.error(f"Failed to block user {user_id}: {e}")
            return False

    def unblock_user(self, user_id: int) -> bool:
        """
        Unblock a user.

        Args:
            user_id: Telegram user ID to unblock

        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.blocked_users:
                logger.warning(f"User {user_id} is not blocked")
                return False

            self.blocked_users.remove(user_id)
            self._save_authorized_users()

            logger.info(f"Unblocked user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unblock user {user_id}: {e}")
            return False

    async def check_rate_limit(self, user_id: int) -> Dict[str, Any]:
        """
        Check rate limiting for a user.

        Args:
            user_id: Telegram user ID

        Returns:
            Dictionary containing rate limit information
        """
        try:
            current_time = datetime.now().timestamp()

            # Initialize rate limit tracker for user if needed
            if user_id not in self.rate_limit_tracker:
                self.rate_limit_tracker[user_id] = []

            # Clean old requests (older than 1 minute)
            cutoff_time = current_time - 60  # 1 minute ago
            self.rate_limit_tracker[user_id] = [
                req_time for req_time in self.rate_limit_tracker[user_id]
                if req_time > cutoff_time
            ]

            # Add current request
            self.rate_limit_tracker[user_id].append(current_time)

            # Count requests in last minute
            requests_in_minute = len(self.rate_limit_tracker[user_id])

            # Check if rate limit exceeded
            is_rate_limited = requests_in_minute >= self.max_requests_per_minute
            reset_time = current_time + 60 if is_rate_limited else None

            return {
                "user_id": user_id,
                "requests_in_minute": requests_in_minute,
                "max_requests_per_minute": self.max_requests_per_minute,
                "is_rate_limited": is_rate_limited,
                "reset_time": reset_time,
                "remaining_requests": max(0, self.max_requests_per_minute - requests_in_minute)
            }

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            return {"error": str(e)}

    def create_user_session(self, user_id: int, update: Update) -> Dict[str, Any]:
        """
        Create or update a user session.

        Args:
            user_id: Telegram user ID
            update: Telegram Update object

        Returns:
            Dictionary containing session information
        """
        try:
            user = update.from_user
            chat = update.chat

            session_data = {
                "user_id": user_id,
                "chat_id": chat.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_bot": user.is_bot,
                "language_code": user.language_code,
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
                "message_count": 0,
                "files_processed": 0,
                "session_id": self._generate_session_id(user_id, chat.id)
            }

            self.user_sessions[user_id] = session_data

            logger.debug(f"Created session for user {user_id} in chat {chat.id}")
            return session_data

        except Exception as e:
            logger.error(f"Failed to create user session: {e}")
            return {}

    def update_user_session(self, user_id: int, activity_data: Dict[str, Any]) -> bool:
        """
        Update user session with activity data.

        Args:
            user_id: Telegram user ID
            activity_data: Dictionary with activity information

        Returns:
            True if successful, False otherwise
        """
        try:
            if user_id not in self.user_sessions:
                return False

            session = self.user_sessions[user_id]
            session["last_activity"] = datetime.now()
            session["message_count"] += activity_data.get("message_count", 0)
            session["files_processed"] += activity_data.get("files_processed", 0)

            # Update custom fields
            for key, value in activity_data.items():
                if key not in ["message_count", "files_processed"]:
                    session[key] = value

            self.user_sessions[user_id] = session

            return True

        except Exception as e:
            logger.error(f"Failed to update user session {user_id}: {e}")
            return False

    def get_user_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user session information.

        Args:
            user_id: Telegram user ID

        Returns:
            Session information dictionary or None if not found
        """
        session = self.user_sessions.get(user_id)

        if session:
            # Check if session has expired
            session_age = datetime.now() - session["created_at"]
            if session_age > timedelta(minutes=self.session_timeout_minutes):
                # Remove expired session
                del self.user_sessions[user_id]
                return None

        return session

    def cleanup_expired_sessions(self) -> int:
        """Clean up expired user sessions."""
        try:
            expired_sessions = [
                user_id for user_id, session in self.user_sessions.items()
                if datetime.now() - session["created_at"] > timedelta(minutes=self.session_timeout_minutes)
            ]

            for user_id in expired_sessions:
                del self.user_sessions[user_id]

            if expired_sessions:
                logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

            return len(expired_sessions)

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    def _generate_session_id(self, user_id: int, chat_id: int) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().timestamp()
        random_data = secrets.token_hex(8)
        session_data = f"{user_id}_{chat_id}_{timestamp}_{random_data}"
        return hashlib.md5(session_data.encode()).hexdigest()[:16]

    def validate_message_source(self, update: Update) -> bool:
        """
        Validate that a message comes from an authorized source.

        Args:
            update: Telegram Update object

        Returns:
            True if message source is valid, False otherwise
        """
        try:
            if not update.message:
                return False

            message = update.message
            user_id = message.from_user.id if message.from_user else None
            chat_id = message.chat.id

            # Check if user is blocked
            if user_id and self.is_user_blocked(user_id):
                logger.warning(f"Blocked message from user {user_id}")
                return False

            # Check authorization if required
            if self.auth_required:
                if user_id and not self.is_user_authorized(user_id):
                    logger.warning(f"Unauthorized message from user {user_id}")
                    return False

                if chat_id and not self.is_chat_authorized(chat_id):
                    logger.warning(f"Unauthorized message in chat {chat_id}")
                    return False

            # Validate message content
            if not self._validate_message_content(message):
                logger.warning(f"Invalid message content detected")
                return False

            return True

        except Exception as e:
            logger.error(f"Message source validation error: {e}")
            return False

    def _validate_message_content(self, message) -> bool:
        """Validate message content for security."""
        try:
            # Check for suspicious content
            text = message.text or message.caption or ""
            suspicious_patterns = [
                "http://", "https://",
                "bitcoin", "cryptocurrency", "investment",
                "adult", "xxx", "spam", "scam"
            ]

            text_lower = text.lower()
            if any(pattern in text_lower for pattern in suspicious_patterns):
                logger.warning(f"Suspicious content detected: {text[:100]}")
                return False

            # Validate file attachments
            if message.document:
                file_name = message.document.file_name.lower()
                if not self._is_safe_file_type(file_name):
                    logger.warning(f"Unsafe file type: {file_name}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Message content validation error: {e}")
            return False

    def _is_safe_file_type(self, filename: str) -> bool:
        """Check if a file type is safe."""
        extension = Path(filename).suffix.lower()
        return extension in self.trusted_file_extensions

    def get_auth_statistics(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        return {
            "authorized_users_count": len(self.authorized_users),
            "authorized_chats_count": len(self.authorized_chats),
            "blocked_users_count": len(self.blocked_users),
            "active_sessions_count": len(self.user_sessions),
            "auth_required": self.auth_required,
            "max_requests_per_minute": self.max_requests_per_minute,
            "session_timeout_minutes": self.session_timeout_minutes,
            "owner_configured": bool(self.owner_user_id),
            "admin_count": len(self.admin_user_ids)
        }

    def get_user_permissions(self, user_id: int) -> Dict[str, Any]:
        """Get permissions for a user."""
        permissions = {
            "can_send_messages": True,
            "can_receive_files": True,
            "can_access_admin_features": False,
            "can_manage_users": False,
            "can_manage_chats": False
        }

        # Owner has all permissions
        if user_id == self.owner_user_id:
            permissions.update({
                "can_access_admin_features": True,
                "can_manage_users": True,
                "can_manage_chats": True
            })

        # Admins have some admin features
        if user_id in self.admin_user_ids:
            permissions["can_access_admin_features"] = True

        return permissions

    def export_configuration(self) -> Dict[str, Any]:
        """Export current configuration for backup."""
        return {
            "authorized_users": list(self.authorized_users),
            "authorized_chats": list(self.authorized_chats),
            "blocked_users": list(self.blocked_users),
            "admin_user_ids": list(self.admin_user_ids),
            "owner_user_id": self.owner_user_id,
            "auth_required": self.auth_required,
            "max_requests_per_minute": self.max_requests_per_minute,
            "session_timeout_minutes": self.session_timeout_minutes,
            "trusted_file_extensions": list(self.trusted_file_extensions),
            "config": self.config
        }

    def import_configuration(self, config_data: Dict[str, Any]) -> bool:
        """
        Import configuration from backup.

        Args:
            config_data: Configuration data to import

        Returns:
            True if successful, False otherwise
        """
        try:
            self.authorized_users = set(config_data.get("authorized_users", []))
            self.authorized_chats = set(config_data.get("authorized_chats", []))
            self.blocked_users = set(config_data.get("blocked_users", []))
            self.admin_user_ids = set(config_data.get("admin_user_ids", []))
            self.owner_user_id = config_data.get("owner_user_id")
            self.auth_required = config_data.get("auth_required", False)
            self.max_requests_per_minute = config_data.get("max_requests_per_minute", 30)
            self.session_timeout_minutes = config_data.get("session_timeout_minutes", 60)

            if "config" in config_data:
                self.config.update(config_data["config"])

            logger.info("Imported configuration successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to import configuration: {e}")
            return False


# Factory function for easy auth manager creation
def create_telegram_auth_manager(config: Optional[Dict[str, Any]] = None) -> TelegramAuthManager:
    """
    Create and initialize a Telegram auth manager.

    Args:
        config: Optional configuration dictionary

    Returns:
        Initialized Telegram auth manager
    """
    return TelegramAuthManager(config)