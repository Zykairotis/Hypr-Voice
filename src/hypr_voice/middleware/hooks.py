"""
Hook System

Intercept and modify tool execution and events.
Based on Claude Agent SDK hook patterns.
"""

import asyncio
import logging
from typing import Any, Callable, Awaitable, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class HookEvent(str, Enum):
    """Supported hook events matching Claude Agent SDK."""
    PRE_TOOL_USE = "PreToolUse"
    POST_TOOL_USE = "PostToolUse"
    USER_PROMPT_SUBMIT = "UserPromptSubmit"
    AGENT_STARTED = "AgentStarted"
    AGENT_COMPLETED = "AgentCompleted"
    STOP = "Stop"
    SUBAGENT_STOP = "SubagentStop"
    PRE_COMPACT = "PreCompact"


@dataclass
class HookContext:
    """Context passed to hook callbacks."""
    event: HookEvent
    timestamp: str
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: dict = field(default_factory=dict)


@dataclass
class HookResult:
    """Result from a hook callback."""
    allow: bool = True
    modified_input: Optional[dict] = None
    system_message: Optional[str] = None
    metadata: dict = field(default_factory=dict)
    
    @classmethod
    def allow_action(cls) -> "HookResult":
        return cls(allow=True)
    
    @classmethod
    def deny_action(cls, reason: str) -> "HookResult":
        return cls(allow=False, metadata={"reason": reason})
    
    @classmethod
    def modify_input(cls, new_input: dict) -> "HookResult":
        return cls(allow=True, modified_input=new_input)


# Type alias for hook callbacks
HookCallback = Callable[[dict, Optional[str], HookContext], Awaitable[HookResult]]


@dataclass
class HookMatcher:
    """Configuration for matching hooks to events."""
    matcher: Optional[str] = None  # Tool name pattern or None for all
    callbacks: list[HookCallback] = field(default_factory=list)


class HookManager:
    """
    Manages hook registration and execution.
    
    Hooks can:
    - Intercept tool calls before execution (PreToolUse)
    - Process tool results after execution (PostToolUse)
    - Modify user prompts before processing (UserPromptSubmit)
    - React to agent lifecycle events
    """
    
    def __init__(self):
        self._hooks: dict[HookEvent, list[HookMatcher]] = {
            event: [] for event in HookEvent
        }
        self._global_hooks: list[HookCallback] = []
    
    def register(
        self,
        event: HookEvent,
        callback: HookCallback,
        matcher: Optional[str] = None,
    ):
        """
        Register a hook callback.
        
        Args:
            event: Event to hook into
            callback: Async callback function
            matcher: Optional pattern to match (e.g., tool name)
        """
        hook_matcher = HookMatcher(matcher=matcher, callbacks=[callback])
        self._hooks[event].append(hook_matcher)
        
        logger.debug(f"Registered hook for {event.value} (matcher: {matcher})")
    
    def register_global(self, callback: HookCallback):
        """Register a global hook that runs for all events."""
        self._global_hooks.append(callback)
    
    async def execute(
        self,
        event: HookEvent,
        input_data: dict,
        tool_use_id: Optional[str] = None,
        context: Optional[HookContext] = None,
    ) -> HookResult:
        """
        Execute hooks for an event.
        
        Args:
            event: The event being triggered
            input_data: Event-specific input data
            tool_use_id: Optional tool use identifier
            context: Optional hook context
            
        Returns:
            Aggregated HookResult
        """
        if context is None:
            context = HookContext(
                event=event,
                timestamp=datetime.utcnow().isoformat(),
            )
        
        # Collect applicable hooks
        hooks_to_run = []
        
        # Global hooks
        hooks_to_run.extend(self._global_hooks)
        
        # Event-specific hooks
        for hook_matcher in self._hooks[event]:
            if hook_matcher.matcher is None:
                # Matches all
                hooks_to_run.extend(hook_matcher.callbacks)
            elif "tool_name" in input_data:
                # Check if matcher matches tool name
                tool_name = input_data["tool_name"]
                if self._matches_pattern(hook_matcher.matcher, tool_name):
                    hooks_to_run.extend(hook_matcher.callbacks)
        
        # Execute hooks
        result = HookResult()
        current_input = input_data.copy()
        
        for callback in hooks_to_run:
            try:
                hook_result = await callback(current_input, tool_use_id, context)
                
                # If any hook denies, stop and return denial
                if not hook_result.allow:
                    return hook_result
                
                # Apply input modifications
                if hook_result.modified_input:
                    current_input = hook_result.modified_input
                    result.modified_input = current_input
                
                # Collect system messages
                if hook_result.system_message:
                    if result.system_message:
                        result.system_message += "\n" + hook_result.system_message
                    else:
                        result.system_message = hook_result.system_message
                
                # Merge metadata
                result.metadata.update(hook_result.metadata)
                
            except Exception as e:
                logger.error(f"Hook execution error: {e}")
                # Continue with other hooks
        
        return result
    
    def _matches_pattern(self, pattern: str, value: str) -> bool:
        """Check if a value matches a pattern."""
        import re
        try:
            return bool(re.match(pattern, value, re.IGNORECASE))
        except re.error:
            # Fall back to simple string match
            return pattern.lower() in value.lower()
    
    def list_hooks(self) -> dict[str, int]:
        """List registered hooks by event."""
        return {
            event.value: len(matchers)
            for event, matchers in self._hooks.items()
        }


# Predefined hook callbacks

async def logging_hook(
    input_data: dict,
    tool_use_id: Optional[str],
    context: HookContext,
) -> HookResult:
    """Log all tool usage."""
    tool_name = input_data.get("tool_name", "unknown")
    logger.info(f"[Hook] {context.event.value}: {tool_name}")
    return HookResult.allow_action()


async def dangerous_command_hook(
    input_data: dict,
    tool_use_id: Optional[str],
    context: HookContext,
) -> HookResult:
    """Block dangerous bash commands."""
    if input_data.get("tool_name") != "Bash":
        return HookResult.allow_action()
    
    command = str(input_data.get("tool_input", {}).get("command", ""))
    
    # List of dangerous patterns
    dangerous_patterns = [
        "rm -rf /",
        "rm -rf ~",
        ":(){ :|:& };:",  # Fork bomb
        "dd if=/dev/zero of=/dev/sda",
        "> /dev/sda",
        "mkfs.",
    ]
    
    for pattern in dangerous_patterns:
        if pattern in command:
            return HookResult.deny_action(f"Dangerous command blocked: {pattern}")
    
    return HookResult.allow_action()


async def audit_hook(
    input_data: dict,
    tool_use_id: Optional[str],
    context: HookContext,
) -> HookResult:
    """Audit all tool usage to a log file."""
    import json
    from pathlib import Path
    
    audit_log = Path.home() / ".hypr_voice" / "audit.log"
    audit_log.parent.mkdir(exist_ok=True)
    
    entry = {
        "timestamp": context.timestamp,
        "event": context.event.value,
        "tool_name": input_data.get("tool_name"),
        "agent_id": context.agent_id,
    }
    
    with open(audit_log, "a") as f:
        f.write(json.dumps(entry) + "\n")
    
    return HookResult.allow_action()
