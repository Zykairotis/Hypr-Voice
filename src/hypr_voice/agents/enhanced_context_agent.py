"""
Enhanced Context Agent

Claude SDK-based agent for context-aware AI assistance with Hyprland integration.
Provides intelligent responses using active window context, clipboard data, and system state.
"""

import asyncio
import logging
import uuid
from typing import AsyncIterator, Optional, Dict, Any, List
from datetime import datetime

from ..services.sdk_compat import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    CLAUDE_SDK_AVAILABLE
)

if not CLAUDE_SDK_AVAILABLE:
    logging.warning("Claude Agent SDK not available - enhanced mode will be disabled")

from ..services.tools import hyprland_ss_ctx

logger = logging.getLogger(__name__)


class EnhancedContextAgent:
    """
    Context-aware AI agent using Claude Agent SDK.

    Features:
    - Full context awareness (active window, clipboard, workspace)
    - Claude SDK with custom Hyprland tools
    - Session persistence for conversation continuity
    - Streaming support for real-time TTS
    - Intelligent context-based prompts
    """

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        max_turns: int = 5,
        working_directory: Optional[str] = None,
    ):
        """
        Initialize the Enhanced Context Agent.

        Args:
            model: Claude model to use (sonnet/opus/haiku)
            max_turns: Maximum conversation turns
            working_directory: Working directory for file operations
        """
        self.model = model
        self.max_turns = max_turns
        self.working_directory = working_directory
        self.sessions: Dict[str, Dict[str, Any]] = {}

        if not CLAUDE_SDK_AVAILABLE:
            raise RuntimeError("Claude Agent SDK is required for EnhancedContextAgent")

        logger.info(f"Enhanced Context Agent initialized (model={model}, max_turns={max_turns})")

    async def process(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_id: Optional[str] = None,
        speak_response: bool = True,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Process a query with full context awareness.

        Args:
            query: User's question or command
            context: Environment context (window, clipboard, etc.)
            conversation_id: Optional conversation ID for continuity
            speak_response: Whether response should be optimized for speech

        Yields:
            Dict containing response chunks with types:
            - "text": Text content chunk
            - "conversation_id": The conversation ID for follow-ups
            - "tool_use": Tool execution information
            - "thinking": Agent's internal reasoning
        """
        try:
            # Generate or use existing conversation ID
            if not conversation_id:
                conversation_id = f"enhanced_{uuid.uuid4().hex[:8]}"

            # Build context-aware system prompt
            system_prompt = self._build_system_prompt(context, speak_response)

            # Configure Claude SDK
            options = ClaudeAgentOptions(
                system_prompt=system_prompt,
                model=self.model,
                max_turns=self.max_turns,
                working_directory=self.working_directory,
                # Use built-in tools + Hyprland tools via import
                allowed_tools=[
                    # File operations
                    "Read", "Write", "Edit",
                    # System operations
                    "Bash",
                    # Research
                    "WebSearch", "WebFetch",
                    # Hyprland context tools (imported from hyprland_ss_ctx)
                    "get_hyprland_active_client",
                    "get_hyprland_all_clients",
                    "get_hyprland_clients_by_class",
                    "get_hyprland_clients_by_title",
                    "screenshot_hyprland_active_window",
                    "screenshot_hyprland_client",
                ],
                permission_mode="bypassPermissions",  # Trust internal tools
                resume=conversation_id if conversation_id in self.sessions else None,
            )

            # Create SDK client and process query
            async with ClaudeSDKClient(options=options) as client:
                # Store session
                self.sessions[conversation_id] = {
                    "client": client,
                    "context": context,
                    "started_at": datetime.utcnow().isoformat(),
                    "query": query,
                }

                # Send conversation ID first
                yield {
                    "type": "conversation_id",
                    "id": conversation_id,
                    "timestamp": datetime.utcnow().isoformat(),
                }

                # Execute query
                await client.query(query)

                # Stream responses
                full_text = ""
                async for message in client.receive_response():
                    chunk = self._format_message(message)
                    if chunk:
                        # Accumulate text for session storage
                        if chunk.get("type") == "text":
                            full_text += chunk.get("content", "")
                        yield chunk

                # Update session with response
                if conversation_id in self.sessions:
                    self.sessions[conversation_id]["response"] = full_text
                    self.sessions[conversation_id]["completed_at"] = datetime.utcnow().isoformat()

                logger.info(f"Enhanced query completed (conversation_id={conversation_id})")

        except Exception as e:
            logger.error(f"Enhanced processing error: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            }

    def _build_system_prompt(
        self,
        context: Dict[str, Any],
        speak_response: bool = True,
    ) -> str:
        """
        Build context-aware system prompt.

        Args:
            context: Environment context
            speak_response: Whether to optimize for voice output

        Returns:
            System prompt string
        """
        window = context.get("window", {})
        clipboard = context.get("clipboard", "")
        timestamp = context.get("timestamp", datetime.utcnow().isoformat())

        # Extract window information
        window_class = window.get("class", "unknown")
        window_title = window.get("title", "unknown")
        workspace_id = window.get("workspace", {}).get("id", "unknown")

        # Truncate clipboard for prompt
        clipboard_preview = clipboard[:200] if clipboard else "empty"
        if len(clipboard) > 200:
            clipboard_preview += "... (truncated)"

        voice_instructions = ""
        if speak_response:
            voice_instructions = """
VOICE RESPONSE GUIDELINES:
- Keep responses conversational and natural for voice output
- Avoid bullet points, lists, and formatted text
- Speak in complete, flowing sentences
- Be concise - aim for 2-3 sentences unless more detail is needed
- Use natural transitions between ideas
- Avoid saying "according to" or "based on" - just state information naturally
"""

        return f"""You are an intelligent context-aware assistant with deep understanding of the user's current environment and tasks.

CURRENT ENVIRONMENT CONTEXT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• Active Application: {window_class}
• Window Title: {window_title}
• Workspace: {workspace_id}
• Clipboard: {clipboard_preview}
• Timestamp: {timestamp}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CAPABILITIES:
You have access to powerful tools for:
1. **Hyprland Window Management**
   - Query active window details
   - List all windows
   - Search by class/title
   - Take screenshots of windows

2. **File Operations**
   - Read files (code, configs, docs)
   - Write and edit files
   - Search codebase

3. **System Operations**
   - Execute bash commands
   - System queries

4. **Research**
   - Web search for current information
   - Fetch documentation and resources

CONTEXT-AWARE INSTRUCTIONS:
• When the user says "this window", "current app", or "here" - use the active window context above
• If clipboard contains code/text, reference it naturally when relevant
• Consider the application type when providing assistance:
  - Code editors (VSCode, Cursor): Offer code-specific help, debugging, refactoring
  - Terminals (kitty, alacritty): Provide command suggestions, system help
  - Browsers (Firefox, Chrome): Help with research, summaries, web tasks
  - Communication (Discord, Slack): Assist with messaging, formatting

• Prefer using tools over making assumptions - if unsure, check via tools
• For file operations, use absolute paths when possible
• Be proactive but respectful of the user's workflow
{voice_instructions}

RESPONSE STYLE:
- Be helpful, friendly, and conversational
- Provide actionable solutions
- Explain your reasoning briefly
- If you use tools, summarize what you found/did
- Match the user's energy level and technical depth
- Be honest about limitations

Remember: You're assisting with real work in a real environment. Be practical, efficient, and context-aware."""

    def _format_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Format SDK message for yielding.

        Args:
            message: Raw message from SDK

        Returns:
            Formatted message dict or None
        """
        msg_type = message.get("type")

        if msg_type == "text":
            return {
                "type": "text",
                "content": message.get("content", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }
        elif msg_type == "tool_use":
            return {
                "type": "tool_use",
                "tool": message.get("name", ""),
                "input": message.get("input", {}),
                "timestamp": datetime.utcnow().isoformat(),
            }
        elif msg_type == "thinking":
            return {
                "type": "thinking",
                "content": message.get("content", ""),
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Unknown message type - log and skip
        if msg_type:
            logger.debug(f"Unknown message type: {msg_type}")
        return None

    def get_session(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get session data for a conversation."""
        return self.sessions.get(conversation_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all active sessions."""
        return [
            {
                "conversation_id": conv_id,
                "context": session.get("context", {}),
                "started_at": session.get("started_at"),
                "completed_at": session.get("completed_at"),
                "query": session.get("query", ""),
            }
            for conv_id, session in self.sessions.items()
        ]

    def clear_session(self, conversation_id: str) -> bool:
        """Clear a specific session."""
        if conversation_id in self.sessions:
            del self.sessions[conversation_id]
            logger.info(f"Cleared session: {conversation_id}")
            return True
        return False

    def clear_all_sessions(self):
        """Clear all sessions."""
        count = len(self.sessions)
        self.sessions.clear()
        logger.info(f"Cleared {count} sessions")

    async def shutdown(self):
        """Cleanup on shutdown."""
        self.clear_all_sessions()
        logger.info("Enhanced Context Agent shutdown")
