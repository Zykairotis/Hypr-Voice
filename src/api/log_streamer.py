"""
Log streaming service for real-time log monitoring
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, AsyncGenerator, Set, Any
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass
import aiofiles

from models import LogEntry, LogLevel, LogType


@dataclass
class LogSubscription:
    """WebSocket log subscription"""
    websocket: Any  # WebSocket object
    log_types: List[LogType]
    levels: List[LogLevel]
    subscription_id: str
    last_position: Dict[str, int] = None


class LogStreamer:
    """Real-time log streaming service"""

    def __init__(self, log_dir: str = "/tmp"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

        # Log file paths - using actual Hypr-Voice log locations
        self.log_files = {
            LogType.SERVER: Path("/tmp/hypr-voice-server.log"),
            LogType.CLIENT: Path("/tmp/hypr-voice-client.log"),
            LogType.AGENT: self.log_dir / "hypr-voice-logs" / "agent.log",
            LogType.RESPONSE: self.log_dir / "hypr-voice-logs" / "response.log",
            LogType.STATUS: self.log_dir / "hypr-voice-logs" / "status.log"
        }

        # Active subscriptions
        self.subscriptions: Dict[str, LogSubscription] = {}
        self.subscription_counter = 0

        # File positions for each log file
        self.file_positions: Dict[str, int] = {}

        # Background monitoring task
        self.monitor_task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self):
        """Start log streaming service"""
        if self.running:
            return

        self.running = True
        self.monitor_task = asyncio.create_task(self._monitor_logs())
        logger.info("Log streaming service started")

    async def stop(self):
        """Stop log streaming service"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Log streaming service stopped")

    async def subscribe(
        self,
        websocket: Any,
        log_types: List[LogType] = None,
        levels: List[LogLevel] = None,
        max_recent_entries: int = 50
    ) -> str:
        """Subscribe to log stream"""
        if log_types is None:
            log_types = [LogType.ALL]
        if levels is None:
            levels = list(LogLevel)

        subscription_id = f"sub_{self.subscription_counter}"
        self.subscription_counter += 1

        subscription = LogSubscription(
            websocket=websocket,
            log_types=log_types,
            levels=levels,
            subscription_id=subscription_id,
            last_position={}
        )

        self.subscriptions[subscription_id] = subscription

        # Send recent log entries
        await self._send_recent_logs(subscription, max_recent_entries)

        # Initialize file positions
        for log_type in LogType:
            if log_type != LogType.ALL:
                file_path = self.log_files.get(log_type)
                if file_path and file_path.exists():
                    subscription.last_position[str(log_type)] = file_path.stat().st_size

        logger.info(f"Added log subscription: {subscription_id}")
        return subscription_id

    async def unsubscribe(self, subscription_id: str):
        """Unsubscribe from log stream"""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            logger.info(f"Removed log subscription: {subscription_id}")

    async def _monitor_logs(self):
        """Monitor log files for changes"""
        while self.running:
            try:
                await self._check_log_changes()
                await asyncio.sleep(0.1)  # Check every 100ms
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring logs: {e}")
                await asyncio.sleep(1)

    async def _check_log_changes(self):
        """Check for changes in log files"""
        for log_type, file_path in self.log_files.items():
            if not file_path.exists():
                continue

            try:
                current_size = file_path.stat().st_size
                last_size = self.file_positions.get(str(file_path), 0)

                if current_size > last_size:
                    # Read new log entries
                    await self._read_new_entries(log_type, file_path, last_size)
                    self.file_positions[str(file_path)] = current_size

            except Exception as e:
                logger.debug(f"Error checking log file {file_path}: {e}")

    async def _read_new_entries(self, log_type: LogType, file_path: Path, start_pos: int):
        """Read new log entries from file"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                await f.seek(start_pos)
                new_lines = await f.readlines()

            for line in new_lines:
                line = line.strip()
                if not line:
                    continue

                try:
                    log_entry = self._parse_log_entry(line, log_type)
                    if log_entry:
                        await self._broadcast_log_entry(log_entry)
                except Exception as e:
                    logger.debug(f"Error parsing log entry: {e}")

        except Exception as e:
            logger.debug(f"Error reading new entries from {file_path}: {e}")

    async def _send_recent_logs(self, subscription: LogSubscription, max_entries: int):
        """Send recent log entries to new subscription"""
        for log_type in subscription.log_types:
            if log_type == LogType.ALL:
                continue

            file_path = self.log_files.get(log_type)
            if not file_path or not file_path.exists():
                continue

            try:
                recent_entries = await self._get_recent_log_entries(file_path, max_entries)
                for entry in recent_entries:
                    await self._send_to_subscription(subscription, entry)
            except Exception as e:
                logger.debug(f"Error sending recent logs for {log_type}: {e}")

    async def _get_recent_log_entries(self, file_path: Path, max_entries: int) -> List[LogEntry]:
        """Get recent log entries from file"""
        entries = []

        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()

            # Get last N lines
            recent_lines = lines[-max_entries:] if len(lines) > max_entries else lines

            for line in recent_lines:
                line = line.strip()
                if line:
                    try:
                        entry = self._parse_log_entry(line)
                        if entry:
                            entries.append(entry)
                    except Exception:
                        continue

        except Exception as e:
            logger.debug(f"Error getting recent log entries from {file_path}: {e}")

        return entries

    def _parse_log_entry(self, line: str, log_type: LogType = None) -> Optional[LogEntry]:
        """Parse log entry from JSON line"""
        try:
            data = json.loads(line)

            # Extract timestamp
            timestamp_str = data.get('timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.now()

            # Determine log level
            level = LogLevel.INFO
            if 'status' in data:
                status = data['status'].upper()
                if 'ERROR' in status:
                    level = LogLevel.ERROR
                elif status in ['STARTED', 'PROCESSING']:
                    level = LogLevel.INFO
                elif status == 'COMPLETED':
                    level = LogLevel.INFO
            elif 'error_message' in data:
                level = LogLevel.ERROR

            # Create log entry
            return LogEntry(
                timestamp=timestamp,
                level=level,
                message=self._format_log_message(data),
                context=data,
                source=str(log_type) if log_type else 'unknown'
            )

        except Exception as e:
            logger.debug(f"Error parsing log entry: {e}")
            return None

    def _format_log_message(self, data: Dict[str, Any]) -> str:
        """Format log message from data"""
        if 'input_text' in data:
            return f"Voice input: {data['input_text'][:100]}..."
        elif 'response' in data:
            return f"Response: {data['response'][:100]}..."
        elif 'summary' in data:
            return f"Summary: {data['summary'][:100]}..."
        elif 'status' in data:
            return f"Status: {data['status']}"
        elif 'event' in data:
            return f"Event: {data['event']}"
        else:
            return str(data)

    async def _broadcast_log_entry(self, log_entry: LogEntry):
        """Broadcast log entry to all matching subscriptions"""
        for subscription in list(self.subscriptions.values()):
            if self._should_send_to_subscription(subscription, log_entry):
                await self._send_to_subscription(subscription, log_entry)

    def _should_send_to_subscription(self, subscription: LogSubscription, log_entry: LogEntry) -> bool:
        """Check if log entry should be sent to subscription"""
        # Check log type
        if LogType.ALL not in subscription.log_types:
            source_matches = any(
                log_entry.source == str(log_type) for log_type in subscription.log_types
            )
            if not source_matches:
                return False

        # Check log level
        if log_entry.level not in subscription.levels:
            return False

        return True

    async def _send_to_subscription(self, subscription: LogSubscription, log_entry: LogEntry):
        """Send log entry to subscription"""
        try:
            from models import LogStreamMessage

            message = LogStreamMessage(log_entry=log_entry)
            await subscription.websocket.send_json(message.dict())

        except Exception as e:
            # Remove subscription if WebSocket is closed
            if subscription.subscription_id in self.subscriptions:
                del self.subscriptions[subscription.subscription_id]
                logger.debug(f"Removed closed subscription: {subscription.subscription_id}")

    async def get_recent_logs(self, log_type: LogType, limit: int = 50) -> List[LogEntry]:
        """Get recent logs of specified type"""
        if log_type == LogType.ALL:
            all_entries = []
            for l_type in [LogType.AGENT, LogType.RESPONSE, LogType.STATUS]:
                file_path = self.log_files.get(l_type)
                if file_path and file_path.exists():
                    entries = await self._get_recent_log_entries(file_path, limit)
                    all_entries.extend(entries)

            # Sort by timestamp and limit
            all_entries.sort(key=lambda x: x.timestamp, reverse=True)
            return all_entries[:limit]

        else:
            file_path = self.log_files.get(log_type)
            if file_path and file_path.exists():
                return await self._get_recent_log_entries(file_path, limit)
            return []

    def get_subscription_count(self) -> int:
        """Get number of active subscriptions"""
        return len(self.subscriptions)