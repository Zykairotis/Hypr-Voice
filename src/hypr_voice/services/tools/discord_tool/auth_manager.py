"""
Discord Auth Manager for Helper Agent

This module provides comprehensive authentication and authorization management
for Discord Bot integration, including user permissions, rate limiting, and security.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from collections import defaultdict, deque
import hashlib
import os
import discord

logger = logging.getLogger(__name__)


@dataclass
class UserPermission:
    """User permission data structure."""
    user_id: int
    username: str
    permission_level: str  # 'user', 'moderator', 'admin', 'owner'
    guilds: List[int]  # Guild IDs where user has access
    channels: List[int]  # Channel IDs where user has access
    created_at: datetime
    last_activity: datetime
    is_active: bool = True


@dataclass
class RateLimitInfo:
    """Rate limiting information."""
    user_id: int
    requests: deque  # Request timestamps
    max_requests: int
    window_seconds: int


class DiscordAuthManager:
    """
    Authentication and authorization manager for Discord Bot integration.

    Features:
    - User permission management
    - Rate limiting
    - Guild and channel access control
    - Session management
    - Security validation
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Discord auth manager.

        Args:
            config: Authentication configuration dictionary
        """
        self.config = config or {}

        # Permission levels (hierarchical)
        self.permission_hierarchy = {
            'user': 1,
            'moderator': 2,
            'admin': 3,
            'owner': 4
        }

        # User permissions storage
        self.user_permissions: Dict[int, UserPermission] = {}
        self.authorized_guilds: Set[int] = set()
        self.authorized_channels: Set[int] = set()
        self.blocked_users: Set[int] = set()

        # Rate limiting
        self.rate_limits: Dict[int, RateLimitInfo] = {}
        self.default_rate_limit = self.config.get('default_rate_limit', 30)
        self.rate_limit_window = self.config.get('rate_limit_window', 60)  # seconds

        # Session management
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        self.session_timeout = self.config.get('session_timeout', 3600)  # 1 hour

        # Security settings
        self.require_guild_membership = self.config.get('require_guild_membership', True)
        self.allowed_guilds: Set[int] = set(self.config.get('allowed_guilds', []))
        self.owner_ids: Set[int] = set(self.config.get('owner_ids', []))

        # Audit logging
        self.audit_log: List[Dict[str, Any]] = []
        self.max_audit_entries = 1000

        # Load initial configuration
        self._load_configuration()

    async def authenticate_user(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild] = None, channel: Optional[discord.TextChannel] = None) -> Dict[str, Any]:
        """
        Authenticate a Discord user.

        Args:
            user: Discord user or member object
            guild: Optional guild context
            channel: Optional channel context

        Returns:
            Authentication result dictionary
        """
        try:
            user_id = user.id
            username = user.name

            # Check if user is blocked
            if user_id in self.blocked_users:
                await self._log_audit_event('auth_blocked', user_id, username, 'User is blocked')
                return {"authenticated": False, "reason": "User is blocked"}

            # Check rate limiting
            if not await self._check_rate_limit(user_id):
                await self._log_audit_event('auth_rate_limited', user_id, username, 'Rate limit exceeded')
                return {"authenticated": False, "reason": "Rate limit exceeded"}

            # Check if user has existing permissions
            if user_id in self.user_permissions:
                permission = self.user_permissions[user_id]

                # Update last activity
                permission.last_activity = datetime.utcnow()

                # Validate access context
                if guild and not await self._validate_guild_access(user_id, guild.id):
                    return {"authenticated": False, "reason": "Guild access denied"}

                if channel and not await self._validate_channel_access(user_id, channel.id):
                    return {"authenticated": False, "reason": "Channel access denied"}

                await self._log_audit_event('auth_success', user_id, username, f'Authenticated with level: {permission.permission_level}')
                return {
                    "authenticated": True,
                    "user_id": user_id,
                    "username": username,
                    "permission_level": permission.permission_level,
                    "guilds": permission.guilds,
                    "channels": permission.channels
                }

            # New user - assign default permissions
            permission_level = await self._determine_default_permission_level(user, guild, channel)

            permission = UserPermission(
                user_id=user_id,
                username=username,
                permission_level=permission_level,
                guilds=[guild.id] if guild else [],
                channels=[channel.id] if channel else [],
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                is_active=True
            )

            self.user_permissions[user_id] = permission

            # Create session
            await self._create_user_session(user_id, permission)

            await self._log_audit_event('auth_new_user', user_id, username, f'New user authenticated with level: {permission_level}')

            return {
                "authenticated": True,
                "user_id": user_id,
                "username": username,
                "permission_level": permission_level,
                "is_new_user": True
            }

        except Exception as e:
            logger.error(f"Authentication error for user {user.id}: {e}")
            await self._log_audit_event('auth_error', user.id, user.name, f'Authentication error: {str(e)}')
            return {"authenticated": False, "reason": "Authentication error"}

    async def authorize_action(self, user_id: int, action: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Authorize a user action.

        Args:
            user_id: User ID to authorize
            action: Action to authorize
            context: Optional context (guild, channel, etc.)

        Returns:
            True if authorized, False otherwise
        """
        try:
            # Check if user exists
            if user_id not in self.user_permissions:
                await self._log_audit_event('authz_user_not_found', user_id, 'unknown', f'User not found for action: {action}')
                return False

            permission = self.user_permissions[user_id]

            # Check if user is active
            if not permission.is_active:
                await self._log_audit_event('authz_inactive_user', user_id, permission.username, f'Inactive user attempted action: {action}')
                return False

            # Check action permissions based on level
            required_level = self._get_required_permission_level(action)
            user_level = self.permission_hierarchy.get(permission.permission_level, 0)

            if user_level < required_level:
                await self._log_audit_event('authz_insufficient_permission', user_id, permission.username, f'Insufficient permission for action: {action}')
                return False

            # Check context permissions if provided
            if context:
                if 'guild_id' in context and not await self._validate_guild_access(user_id, context['guild_id']):
                    await self._log_audit_event('authz_guild_denied', user_id, permission.username, f'Guild access denied for action: {action}')
                    return False

                if 'channel_id' in context and not await self._validate_channel_access(user_id, context['channel_id']):
                    await self._log_audit_event('authz_channel_denied', user_id, permission.username, f'Channel access denied for action: {action}')
                    return False

            await self._log_audit_event('authz_success', user_id, permission.username, f'Action authorized: {action}')
            return True

        except Exception as e:
            logger.error(f"Authorization error for user {user_id}: {e}")
            return False

    async def update_user_permission(self, user_id: int, permission_level: str, updated_by: int) -> bool:
        """
        Update user permission level.

        Args:
            user_id: User ID to update
            permission_level: New permission level
            updated_by: User ID making the update

        Returns:
            True if updated successfully, False otherwise
        """
        try:
            # Check if updater has sufficient permissions
            if not await self.authorize_action(updated_by, 'manage_permissions'):
                await self._log_audit_event('perm_update_denied', updated_by, 'unknown', f'Insufficient permission to update user {user_id}')
                return False

            if user_id not in self.user_permissions:
                await self._log_audit_event('perm_update_user_not_found', updated_by, 'unknown', f'User {user_id} not found')
                return False

            old_level = self.user_permissions[user_id].permission_level
            self.user_permissions[user_id].permission_level = permission_level
            self.user_permissions[user_id].last_activity = datetime.utcnow()

            await self._log_audit_event('perm_updated', user_id, self.user_permissions[user_id].username, f'Permission updated from {old_level} to {permission_level} by {updated_by}')
            return True

        except Exception as e:
            logger.error(f"Error updating permission for user {user_id}: {e}")
            return False

    async def block_user(self, user_id: int, blocked_by: int, reason: str = "") -> bool:
        """
        Block a user.

        Args:
            user_id: User ID to block
            blocked_by: User ID performing the block
            reason: Reason for blocking

        Returns:
            True if blocked successfully, False otherwise
        """
        try:
            # Check if blocker has sufficient permissions
            if not await self.authorize_action(blocked_by, 'block_users'):
                await self._log_audit_event('block_denied', blocked_by, 'unknown', f'Insufficient permission to block user {user_id}')
                return False

            username = self.user_permissions.get(user_id, {}).username if user_id in self.user_permissions else 'unknown'

            self.blocked_users.add(user_id)

            # Deactivate user permission if exists
            if user_id in self.user_permissions:
                self.user_permissions[user_id].is_active = False

            # Remove user session if exists
            if user_id in self.user_sessions:
                del self.user_sessions[user_id]

            await self._log_audit_event('user_blocked', user_id, username, f'User blocked by {blocked_by}. Reason: {reason}')
            return True

        except Exception as e:
            logger.error(f"Error blocking user {user_id}: {e}")
            return False

    async def unblock_user(self, user_id: int, unblocked_by: int) -> bool:
        """
        Unblock a user.

        Args:
            user_id: User ID to unblock
            unblocked_by: User ID performing the unblock

        Returns:
            True if unblocked successfully, False otherwise
        """
        try:
            # Check if unblocker has sufficient permissions
            if not await self.authorize_action(unblocked_by, 'block_users'):
                await self._log_audit_event('unblock_denied', unblocked_by, 'unknown', f'Insufficient permission to unblock user {user_id}')
                return False

            if user_id not in self.blocked_users:
                await self._log_audit_event('unblock_not_blocked', unblocked_by, 'unknown', f'User {user_id} was not blocked')
                return False

            self.blocked_users.remove(user_id)

            # Reactivate user permission if exists
            if user_id in self.user_permissions:
                self.user_permissions[user_id].is_active = True

            username = self.user_permissions.get(user_id, {}).username if user_id in self.user_permissions else 'unknown'
            await self._log_audit_event('user_unblocked', user_id, username, f'User unblocked by {unblocked_by}')
            return True

        except Exception as e:
            logger.error(f"Error unblocking user {user_id}: {e}")
            return False

    async def add_guild_access(self, user_id: int, guild_id: int, added_by: int) -> bool:
        """Add guild access for a user."""
        try:
            if not await self.authorize_action(added_by, 'manage_guild_access'):
                return False

            if user_id in self.user_permissions:
                if guild_id not in self.user_permissions[user_id].guilds:
                    self.user_permissions[user_id].guilds.append(guild_id)
                    self.user_permissions[user_id].last_activity = datetime.utcnow()

            username = self.user_permissions.get(user_id, {}).username if user_id in self.user_permissions else 'unknown'
            await self._log_audit_event('guild_access_added', user_id, username, f'Guild {guild_id} access added by {added_by}')
            return True

        except Exception as e:
            logger.error(f"Error adding guild access for user {user_id}: {e}")
            return False

    async def add_channel_access(self, user_id: int, channel_id: int, added_by: int) -> bool:
        """Add channel access for a user."""
        try:
            if not await self.authorize_action(added_by, 'manage_channel_access'):
                return False

            if user_id in self.user_permissions:
                if channel_id not in self.user_permissions[user_id].channels:
                    self.user_permissions[user_id].channels.append(channel_id)
                    self.user_permissions[user_id].last_activity = datetime.utcnow()

            username = self.user_permissions.get(user_id, {}).username if user_id in self.user_permissions else 'unknown'
            await self._log_audit_event('channel_access_added', user_id, username, f'Channel {channel_id} access added by {added_by}')
            return True

        except Exception as e:
            logger.error(f"Error adding channel access for user {user_id}: {e}")
            return False

    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user information."""
        if user_id not in self.user_permissions:
            return None

        permission = self.user_permissions[user_id]
        session = self.user_sessions.get(user_id, {})

        return {
            "user_id": user_id,
            "username": permission.username,
            "permission_level": permission.permission_level,
            "guilds": permission.guilds,
            "channels": permission.channels,
            "is_active": permission.is_active,
            "is_blocked": user_id in self.blocked_users,
            "created_at": permission.created_at,
            "last_activity": permission.last_activity,
            "session_active": session.get('active', False),
            "session_created": session.get('created_at')
        }

    def get_audit_log(self, limit: int = 100, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get audit log entries."""
        log = self.audit_log

        if user_id:
            log = [entry for entry in log if entry.get('user_id') == user_id]

        return log[-limit:] if len(log) > limit else log

    def get_statistics(self) -> Dict[str, Any]:
        """Get authentication statistics."""
        active_sessions = len([s for s in self.user_sessions.values() if s.get('active', False)])

        return {
            "total_users": len(self.user_permissions),
            "active_users": len([u for u in self.user_permissions.values() if u.is_active]),
            "blocked_users": len(self.blocked_users),
            "active_sessions": active_sessions,
            "authorized_guilds": len(self.authorized_guilds),
            "authorized_channels": len(self.authorized_channels),
            "audit_log_entries": len(self.audit_log),
            "rate_limit_entries": len(self.rate_limits)
        }

    async def cleanup_expired_sessions(self):
        """Clean up expired user sessions."""
        try:
            current_time = datetime.utcnow()
            expired_sessions = []

            for user_id, session in self.user_sessions.items():
                if not session.get('active', False):
                    continue

                session_age = current_time - session.get('created_at', current_time)
                if session_age.total_seconds() > self.session_timeout:
                    expired_sessions.append(user_id)

            for user_id in expired_sessions:
                del self.user_sessions[user_id]
                if user_id in self.user_permissions:
                    self.user_permissions[user_id].last_activity = current_time

            # Clean up old rate limit entries
            current_time_ts = time.time()
            expired_rate_limits = [
                user_id for user_id, rate_info in self.rate_limits.items()
                if all(current_time_ts - req_time > rate_info.window_seconds for req_time in rate_info.requests)
            ]

            for user_id in expired_rate_limits:
                del self.rate_limits[user_id]

            # Clean up old audit log entries
            if len(self.audit_log) > self.max_audit_entries:
                self.audit_log = self.audit_log[-self.max_audit_entries:]

            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions and {len(expired_rate_limits)} expired rate limits")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def _load_configuration(self):
        """Load initial configuration."""
        try:
            # Add owner IDs to authorized users with owner level
            for owner_id in self.owner_ids:
                self.user_permissions[owner_id] = UserPermission(
                    user_id=owner_id,
                    username="owner",
                    permission_level="owner",
                    guilds=[],
                    channels=[],
                    created_at=datetime.utcnow(),
                    last_activity=datetime.utcnow(),
                    is_active=True
                )

            logger.info(f"Loaded configuration with {len(self.owner_ids)} owners")

        except Exception as e:
            logger.error(f"Error loading configuration: {e}")

    async def _determine_default_permission_level(self, user: Union[discord.User, discord.Member], guild: Optional[discord.Guild] = None, channel: Optional[discord.TextChannel] = None) -> str:
        """Determine default permission level for a new user."""
        # Check if user is an owner
        if user.id in self.owner_ids:
            return "owner"

        # Check if user is a guild admin/moderator
        if guild and isinstance(user, discord.Member):
            if user.guild_permissions.administrator:
                return "admin"
            elif user.guild_permissions.manage_messages or user.guild_permissions.kick_members:
                return "moderator"

        # Default to user level
        return "user"

    async def _check_rate_limit(self, user_id: int) -> bool:
        """Check if user is within rate limits."""
        current_time = time.time()

        if user_id not in self.rate_limits:
            self.rate_limits[user_id] = RateLimitInfo(
                user_id=user_id,
                requests=deque([current_time]),
                max_requests=self.default_rate_limit,
                window_seconds=self.rate_limit_window
            )
            return True

        rate_info = self.rate_limits[user_id]
        requests = rate_info.requests

        # Remove old requests outside the window
        while requests and current_time - requests[0] > rate_info.window_seconds:
            requests.popleft()

        # Check if under limit
        if len(requests) < rate_info.max_requests:
            requests.append(current_time)
            return True

        return False

    async def _validate_guild_access(self, user_id: int, guild_id: int) -> bool:
        """Validate user's access to a guild."""
        # If user is owner, allow all guilds
        if user_id in self.owner_ids:
            return True

        # If no guild restrictions, allow all
        if not self.allowed_guilds:
            return True

        # Check if guild is in allowed list
        if guild_id not in self.allowed_guilds:
            return False

        # Check user's specific guild permissions
        if user_id in self.user_permissions:
            return guild_id in self.user_permissions[user_id].guilds

        return False

    async def _validate_channel_access(self, user_id: int, channel_id: int) -> bool:
        """Validate user's access to a channel."""
        # If user is owner, allow all channels
        if user_id in self.owner_ids:
            return True

        # Check user's specific channel permissions
        if user_id in self.user_permissions:
            return channel_id in self.user_permissions[user_id].channels

        return False

    def _get_required_permission_level(self, action: str) -> int:
        """Get required permission level for an action."""
        action_permissions = {
            'read_messages': 1,        # user
            'send_messages': 1,        # user
            'upload_files': 1,         # user
            'manage_channels': 2,      # moderator
            'kick_members': 2,         # moderator
            'manage_permissions': 3,   # admin
            'block_users': 3,          # admin
            'manage_guild_access': 3,  # admin
            'manage_channel_access': 3, # admin
            'bot_settings': 4,         # owner
            'system_admin': 4          # owner
        }

        return action_permissions.get(action, 1)  # Default to user level

    async def _create_user_session(self, user_id: int, permission: UserPermission):
        """Create a new user session."""
        session_data = {
            "user_id": user_id,
            "permission_level": permission.permission_level,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "active": True,
            "ip_address": None,  # Could be added if needed
            "user_agent": None   # Could be added if needed
        }

        self.user_sessions[user_id] = session_data

    async def _log_audit_event(self, event_type: str, user_id: int, username: str, details: str):
        """Log an audit event."""
        try:
            audit_entry = {
                "timestamp": datetime.utcnow(),
                "event_type": event_type,
                "user_id": user_id,
                "username": username,
                "details": details
            }

            self.audit_log.append(audit_entry)

            # Keep audit log size manageable
            if len(self.audit_log) > self.max_audit_entries:
                self.audit_log = self.audit_log[-self.max_audit_entries:]

            logger.debug(f"Audit event: {event_type} - User: {username} - {details}")

        except Exception as e:
            logger.error(f"Error logging audit event: {e}")