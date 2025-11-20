"""
Event Hooks Module
Provides hooks for agent lifecycle events
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class HookEvent(Enum):
    """Hook event types"""
    AGENT_CREATED = "agent_created"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    
    TOOL_CALLED = "tool_called"
    TOOL_RESULT = "tool_result"
    
    CONTEXT_CHANGED = "context_changed"
    VOCABULARY_UPDATED = "vocabulary_updated"
    
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    
    SUBAGENT_CREATED = "subagent_created"
    SUBAGENT_TERMINATED = "subagent_terminated"


@dataclass
class HookContext:
    """Context passed to hook handlers"""
    event: HookEvent
    agent_id: str
    timestamp: datetime
    data: Dict[str, Any]
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "event": self.event.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata or {}
        }


class Hook:
    """Base hook class"""
    
    def __init__(self, 
                 name: str,
                 events: List[HookEvent],
                 handler: Callable,
                 priority: int = 0,
                 enabled: bool = True):
        """
        Initialize hook
        
        Args:
            name: Hook name
            events: Events to listen for
            handler: Async handler function
            priority: Execution priority (higher = earlier)
            enabled: Whether hook is enabled
        """
        self.name = name
        self.events = events
        self.handler = handler
        self.priority = priority
        self.enabled = enabled
        self.call_count = 0
        self.last_called = None
    
    async def execute(self, context: HookContext) -> Any:
        """Execute hook handler"""
        if not self.enabled:
            return None
        
        try:
            self.call_count += 1
            self.last_called = datetime.utcnow()
            
            result = await self.handler(context)
            return result
            
        except Exception as e:
            logger.error(f"Hook {self.name} failed: {e}")
            return None


class HookManager:
    """Manager for hooks"""
    
    def __init__(self):
        self.hooks: Dict[HookEvent, List[Hook]] = {}
        for event in HookEvent:
            self.hooks[event] = []
    
    def register_hook(self, hook: Hook):
        """Register a hook"""
        for event in hook.events:
            self.hooks[event].append(hook)
            # Sort by priority
            self.hooks[event].sort(key=lambda h: h.priority, reverse=True)
        
        logger.info(f"Registered hook: {hook.name} for events: {[e.value for e in hook.events]}")
    
    def unregister_hook(self, name: str):
        """Unregister a hook by name"""
        for event_hooks in self.hooks.values():
            event_hooks[:] = [h for h in event_hooks if h.name != name]
        
        logger.info(f"Unregistered hook: {name}")
    
    async def trigger(self, context: HookContext) -> List[Any]:
        """Trigger hooks for an event"""
        results = []
        
        event_hooks = self.hooks.get(context.event, [])
        
        for hook in event_hooks:
            if hook.enabled:
                try:
                    result = await hook.execute(context)
                    results.append((hook.name, result))
                except Exception as e:
                    logger.error(f"Error triggering hook {hook.name}: {e}")
        
        return results
    
    def enable_hook(self, name: str):
        """Enable a hook"""
        for event_hooks in self.hooks.values():
            for hook in event_hooks:
                if hook.name == name:
                    hook.enabled = True
    
    def disable_hook(self, name: str):
        """Disable a hook"""
        for event_hooks in self.hooks.values():
            for hook in event_hooks:
                if hook.name == name:
                    hook.enabled = False
    
    def list_hooks(self) -> List[Dict]:
        """List all registered hooks"""
        hooks = []
        seen = set()
        
        for event_hooks in self.hooks.values():
            for hook in event_hooks:
                if hook.name not in seen:
                    hooks.append({
                        "name": hook.name,
                        "events": [e.value for e in hook.events],
                        "priority": hook.priority,
                        "enabled": hook.enabled,
                        "call_count": hook.call_count,
                        "last_called": hook.last_called.isoformat() if hook.last_called else None
                    })
                    seen.add(hook.name)
        
        return hooks


# Pre-defined hooks

async def log_event_hook(context: HookContext):
    """Log all events"""
    logger.info(f"Event: {context.event.value} | Agent: {context.agent_id} | Data: {context.data}")


async def error_notification_hook(context: HookContext):
    """Send notifications on errors"""
    if context.event in [HookEvent.AGENT_ERROR, HookEvent.TASK_FAILED]:
        logger.error(f"Error notification: {context.data}")
        # Could send email, slack message, etc.


async def performance_monitor_hook(context: HookContext):
    """Monitor performance metrics"""
    if context.event == HookEvent.TASK_COMPLETED:
        duration = context.data.get("duration")
        if duration:
            logger.info(f"Task completed in {duration}ms")


async def context_sync_hook(context: HookContext):
    """Sync context changes"""
    if context.event == HookEvent.CONTEXT_CHANGED:
        app_context = context.data.get("application")
        logger.info(f"Context changed to: {app_context}")
        # Could update other systems


async def audit_trail_hook(context: HookContext):
    """Maintain audit trail"""
    # Log to file or database
    audit_entry = {
        "timestamp": context.timestamp.isoformat(),
        "event": context.event.value,
        "agent_id": context.agent_id,
        "data": context.data
    }
    # Save audit entry
    logger.debug(f"Audit: {audit_entry}")


# Create default hooks
def create_default_hooks() -> List[Hook]:
    """Create default system hooks"""
    return [
        Hook(
            name="event_logger",
            events=list(HookEvent),  # All events
            handler=log_event_hook,
            priority=10,
            enabled=True
        ),
        Hook(
            name="error_notifier",
            events=[HookEvent.AGENT_ERROR, HookEvent.TASK_FAILED],
            handler=error_notification_hook,
            priority=20,
            enabled=True
        ),
        Hook(
            name="performance_monitor",
            events=[HookEvent.TASK_COMPLETED],
            handler=performance_monitor_hook,
            priority=5,
            enabled=True
        ),
        Hook(
            name="context_sync",
            events=[HookEvent.CONTEXT_CHANGED, HookEvent.VOCABULARY_UPDATED],
            handler=context_sync_hook,
            priority=15,
            enabled=True
        ),
        Hook(
            name="audit_trail",
            events=list(HookEvent),  # All events
            handler=audit_trail_hook,
            priority=1,
            enabled=False  # Disabled by default
        )
    ]
