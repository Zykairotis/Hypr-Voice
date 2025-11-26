"""
Hypr-Voice Orchestrator

Main orchestrator using Claude Agent SDK patterns.
Maintains minimal context, delegates to specialized subagents.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid

from .router import QueryRouter, RouteDecision
from .cerebras_router import CerebrasRouter
from .context_manager import ContextManager
from .registry import AgentRegistry, AgentSession

logger = logging.getLogger(__name__)

# Try to import Claude Agent SDK, fall back to compatibility mode
try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        AgentDefinition,
        query as sdk_query,
        AssistantMessage,
        TextBlock,
        ToolUseBlock,
        ResultMessage,
    )
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    logger.warning("Claude Agent SDK not available. Using fallback mode.")


@dataclass
class OrchestratorConfig:
    """Configuration for the orchestrator."""
    model: str = "claude-sonnet-4-5"
    max_turns: int = 20
    permission_mode: str = "acceptEdits"
    enable_subagents: bool = True
    enable_context_compression: bool = True
    working_directory: Optional[str] = None
    allowed_tools: list[str] = field(default_factory=lambda: [
        "Read", "Write", "Edit", "Grep", "Glob", "Bash"
    ])


@dataclass
class OrchestratorEvent:
    """Event emitted by the orchestrator."""
    event_type: str
    timestamp: str
    data: dict[str, Any]
    agent_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data,
            "agent_id": self.agent_id,
        }


class HyprVoiceOrchestrator:
    """
    Central orchestrator for Hypr-Voice agent system.
    
    Design Principles (from Anthropic docs):
    - Maintains minimal context - only routing decisions and final results
    - Delegates to specialized subagents with isolated contexts
    - Uses ClaudeSDKClient for session persistence across turns
    - Implements agents parameter for programmatic subagent definitions
    """
    
    def __init__(self, config: Optional[OrchestratorConfig] = None, use_cerebras_router: bool = True):
        self.config = config or OrchestratorConfig()
        
        # Use Cerebras for intelligent routing, fallback to keyword matching
        if use_cerebras_router:
            self.router = CerebrasRouter()
            self.keyword_router = QueryRouter()  # Keep as fallback
            logger.info("Using Cerebras-powered intelligent router")
        else:
            self.router = QueryRouter()
            self.keyword_router = None
            logger.info("Using keyword-based router")
        
        self.context_manager = ContextManager()
        self.registry = AgentRegistry()
        self.session_id = str(uuid.uuid4())
        self._event_handlers: list[callable] = []
        self._running = False
        
        # Define subagents
        self.agent_definitions = self._define_agents()
        
        logger.info(f"Orchestrator initialized with session {self.session_id[:8]}")
    
    def _define_agents(self) -> dict[str, dict]:
        """Define specialized subagent configurations."""
        return {
            "code-worker": {
                "description": "Code analysis, generation, and refactoring tasks. Use for any programming-related queries.",
                "prompt": """You are a specialized code agent with expertise in software development.

Your capabilities:
- Analyze code structure and patterns
- Generate new code following best practices
- Refactor existing code for clarity and performance
- Debug issues and suggest fixes
- Review code for security and quality

Be thorough but concise. Focus on actionable insights.""",
                "tools": ["Read", "Write", "Edit", "Grep", "Glob"],
                "model": "sonnet"
            },
            "research-worker": {
                "description": "Research, information gathering, and web search tasks. Use for questions requiring external knowledge.",
                "prompt": """You are a research specialist focused on gathering and synthesizing information.

Your capabilities:
- Search and analyze documentation
- Find relevant examples and patterns
- Synthesize information from multiple sources
- Provide comprehensive summaries

Focus on accuracy and cite sources when possible.""",
                "tools": ["Read", "Grep", "Glob"],
                "model": "haiku"
            },
            "shell-worker": {
                "description": "System operations, bash commands, and environment management. Use for system-level tasks.",
                "prompt": """You are a system operations specialist.

Your capabilities:
- Execute shell commands safely
- Manage files and directories
- Monitor system state
- Automate routine tasks

Always validate commands before execution. Prefer safe, reversible operations.""",
                "tools": ["Bash", "Read", "Grep"],
                "model": "sonnet"
            },
            "voice-worker": {
                "description": "Text-to-speech and speech-to-text operations. Use for voice synthesis tasks.",
                "prompt": """You are a voice synthesis specialist.

Your capabilities:
- Convert text to natural speech
- Optimize text for speech output
- Handle pronunciation and pacing

Focus on clear, natural-sounding output.""",
                "tools": ["Read"],
                "model": "haiku"
            },
            "general-conversation": {
                "description": "General conversation and casual chat. Use for everyday questions, life advice, friendly discussion, greetings.",
                "prompt": """You are a friendly, helpful conversational assistant with a warm personality.

Your capabilities:
- Engage in natural, warm conversation
- Provide thoughtful life advice and perspective
- Answer general knowledge questions
- Be empathetic and supportive
- Have casual, friendly discussions

Guidelines for voice output:
- Keep responses conversational and natural
- Aim for spoken-friendly length (2-4 sentences typically)
- Avoid bullet points or lists - use flowing prose
- Be concise but meaningful
- Sound like a helpful friend, not a robot""",
                "tools": [],
                "model": "haiku"
            },
        }
    
    def register_event_handler(self, handler: callable):
        """Register a handler for orchestrator events."""
        self._event_handlers.append(handler)
    
    async def _emit_event(self, event_type: str, data: dict, agent_id: Optional[str] = None):
        """Emit an event to all registered handlers."""
        event = OrchestratorEvent(
            event_type=event_type,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            agent_id=agent_id,
        )
        for handler in self._event_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
    
    async def process(self, query: str, session_id: Optional[str] = None) -> AsyncIterator[dict]:
        """
        Process a query through the orchestrator.
        
        Args:
            query: The user query to process
            session_id: Optional session ID for conversation continuity
            
        Yields:
            Response chunks as dictionaries
        """
        session_id = session_id or self.session_id
        
        await self._emit_event("query_received", {"query": query}, session_id)
        
        # Route the query to determine handling strategy
        route = self.router.route(query)
        
        await self._emit_event("route_decision", {
            "route": route.agent_type,
            "confidence": route.confidence,
            "reasoning": route.reasoning,
        }, session_id)
        
        if CLAUDE_SDK_AVAILABLE and self.config.enable_subagents:
            async for chunk in self._process_with_sdk(query, route, session_id):
                yield chunk
        else:
            async for chunk in self._process_fallback(query, route, session_id):
                yield chunk
        
        await self._emit_event("query_completed", {"query": query}, session_id)
    
    async def _process_with_sdk(
        self, 
        query: str, 
        route: RouteDecision, 
        session_id: str
    ) -> AsyncIterator[dict]:
        """Process query using Claude Agent SDK."""
        # Convert agent definitions to SDK format
        agents = {}
        for name, config in self.agent_definitions.items():
            agents[name] = AgentDefinition(
                description=config["description"],
                prompt=config["prompt"],
                tools=config.get("tools"),
                model=config.get("model"),
            )
        
        options = ClaudeAgentOptions(
            system_prompt={"type": "preset", "preset": "claude_code"},
            agents=agents,
            permission_mode=self.config.permission_mode,
            max_turns=self.config.max_turns,
            allowed_tools=self.config.allowed_tools,
            cwd=self.config.working_directory,
        )
        
        try:
            async with ClaudeSDKClient(options) as client:
                # Register this session
                agent_session = self.registry.create_session(
                    session_id=session_id,
                    agent_type=route.agent_type,
                    query=query,
                )
                
                await client.query(query, session_id=session_id)
                
                async for message in client.receive_response():
                    if isinstance(message, AssistantMessage):
                        for block in message.content:
                            if isinstance(block, TextBlock):
                                yield {
                                    "type": "text",
                                    "content": block.text,
                                    "agent": route.agent_type,
                                }
                            elif isinstance(block, ToolUseBlock):
                                yield {
                                    "type": "tool_use",
                                    "tool": block.name,
                                    "input": block.input,
                                    "agent": route.agent_type,
                                }
                    elif isinstance(message, ResultMessage):
                        # Compress result for context management
                        if self.config.enable_context_compression:
                            compressed = self.context_manager.compress_result(
                                message.result or "",
                                max_tokens=500
                            )
                        else:
                            compressed = message.result
                        
                        yield {
                            "type": "result",
                            "content": compressed,
                            "session_id": message.session_id,
                            "cost_usd": message.total_cost_usd,
                            "turns": message.num_turns,
                        }
                        
                        # Update session
                        self.registry.complete_session(session_id)
                        
        except Exception as e:
            logger.error(f"SDK processing error: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "agent": route.agent_type,
            }
    
    async def _process_fallback(
        self, 
        query: str, 
        route: RouteDecision, 
        session_id: str
    ) -> AsyncIterator[dict]:
        """Fallback processing when SDK is not available."""
        yield {
            "type": "info",
            "content": f"Processing with {route.agent_type} (fallback mode)",
        }
        
        # Use direct Anthropic API as fallback
        try:
            import anthropic
            import os
            
            # Support custom Anthropic configuration from environment
            api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            model = os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL") or self.config.model
            
            client_kwargs = {}
            if api_key:
                client_kwargs["api_key"] = api_key
            if base_url:
                client_kwargs["base_url"] = base_url
            
            client = anthropic.Anthropic(**client_kwargs)
            agent_config = self.agent_definitions.get(route.agent_type, {})
            
            response = client.messages.create(
                model=model,
                max_tokens=4096,
                system=agent_config.get("prompt", "You are a helpful assistant."),
                messages=[{"role": "user", "content": query}],
            )
            
            for block in response.content:
                if hasattr(block, "text"):
                    yield {
                        "type": "text",
                        "content": block.text,
                        "agent": route.agent_type,
                    }
            
            yield {
                "type": "result",
                "content": "Completed",
                "session_id": session_id,
                "cost_usd": None,
                "turns": 1,
            }
            
        except Exception as e:
            logger.error(f"Fallback processing error: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "agent": route.agent_type,
            }
    
    async def _process_fallback_streaming(
        self, 
        query: str, 
        route: RouteDecision, 
        session_id: str
    ) -> AsyncIterator[dict]:
        """
        Streaming fallback processing - yields individual tokens as they arrive.
        
        This enables real-time TTS where audio can begin playing before
        the full response is generated.
        """
        yield {
            "type": "info",
            "content": f"Processing with {route.agent_type} (streaming mode)",
        }
        
        try:
            import anthropic
            import os
            
            # Support custom Anthropic configuration from environment
            api_key = os.getenv("ANTHROPIC_AUTH_TOKEN") or os.getenv("ANTHROPIC_API_KEY")
            base_url = os.getenv("ANTHROPIC_BASE_URL")
            model = os.getenv("ANTHROPIC_DEFAULT_SONNET_MODEL") or self.config.model
            
            client_kwargs = {}
            if api_key:
                client_kwargs["api_key"] = api_key
            if base_url:
                client_kwargs["base_url"] = base_url
            
            client = anthropic.Anthropic(**client_kwargs)
            agent_config = self.agent_definitions.get(route.agent_type, {})
            
            full_response = ""
            
            # Use streaming API
            with client.messages.stream(
                model=model,
                max_tokens=4096,
                system=agent_config.get("prompt", "You are a helpful assistant."),
                messages=[{"role": "user", "content": query}],
            ) as stream:
                for text in stream.text_stream:
                    if text:
                        full_response += text
                        yield {
                            "type": "token",
                            "content": text,
                            "agent": route.agent_type,
                        }
            
            # Final complete text for reference
            yield {
                "type": "text",
                "content": full_response,
                "agent": route.agent_type,
            }
            
            yield {
                "type": "result",
                "content": "Completed",
                "session_id": session_id,
                "cost_usd": None,
                "turns": 1,
            }
            
        except Exception as e:
            logger.error(f"Streaming fallback error: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "agent": route.agent_type,
            }
    
    async def process_streaming(
        self, 
        query: str, 
        context: Optional[dict] = None
    ) -> AsyncIterator[dict]:
        """
        Process query with token-level streaming for real-time TTS.
        
        Yields individual tokens as they arrive from the LLM,
        enabling audio playback to begin immediately.
        
        Args:
            query: User query
            context: Optional context dictionary
            
        Yields:
            Streaming events including 'token' events for each chunk
        """
        # Route the query first
        route = self.router.route(query)
        
        # Create session with route info
        session = self.registry.create_session(route.agent_type, query[:100])
        session_id = session.session_id
        
        yield {
            "type": "route",
            "agent_type": route.agent_type,
            "confidence": route.confidence,
            "reasoning": route.reasoning,
        }
        
        # Update status
        self.registry.update_session(session_id, {"status": "streaming"})
        
        # Process with streaming
        async for event in self._process_fallback_streaming(query, route, session_id):
            yield event
        
        self.registry.update_session(session_id, {"status": "completed"})
    
    async def spawn_agent(
        self, 
        agent_type: str, 
        task: str,
        parent_session: Optional[str] = None
    ) -> str:
        """
        Spawn a specialized agent for a specific task.
        
        Args:
            agent_type: Type of agent to spawn
            task: Task description for the agent
            parent_session: Optional parent session ID
            
        Returns:
            New agent session ID
        """
        if agent_type not in self.agent_definitions:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        session = self.registry.create_session(
            agent_type=agent_type,
            query=task,
            parent_id=parent_session,
        )
        
        await self._emit_event("agent_spawned", {
            "agent_type": agent_type,
            "task": task,
            "parent_session": parent_session,
        }, session.session_id)
        
        return session.session_id
    
    async def destroy_agent(self, session_id: str) -> bool:
        """
        Destroy an agent session and clean up resources.
        
        Args:
            session_id: Session ID to destroy
            
        Returns:
            True if destroyed successfully
        """
        success = self.registry.destroy_session(session_id)
        
        if success:
            await self._emit_event("agent_destroyed", {
                "session_id": session_id,
            })
        
        return success
    
    def list_agents(self) -> list[dict]:
        """List all active agent sessions."""
        return self.registry.list_sessions()
    
    def get_agent_types(self) -> list[dict]:
        """Get available agent types and their descriptions."""
        return [
            {
                "name": name,
                "description": config["description"],
                "tools": config.get("tools", []),
                "model": config.get("model"),
            }
            for name, config in self.agent_definitions.items()
        ]
    
    async def shutdown(self):
        """Shutdown the orchestrator and cleanup all sessions."""
        logger.info("Shutting down orchestrator...")
        
        # Destroy all active sessions
        for session in self.registry.list_sessions():
            await self.destroy_agent(session["session_id"])
        
        self._running = False
        logger.info("Orchestrator shutdown complete")
