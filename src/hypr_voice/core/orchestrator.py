"""
Multi-Agent Orchestration System with Claude SDK
Main orchestrator with WebSocket real-time monitoring
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
from enum import Enum
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Claude SDK compatibility layer
from ..services.sdk_compat import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    AssistantMessage,
    TextBlock,
    ResultMessage,
    PermissionResultAllow,
    PermissionResultDeny,
    CLAUDE_SDK_AVAILABLE,
    CLAUDE_SDK_MOCK,
    create_sdk_mcp_server
)

# Import our Claude Code integration from services
try:
    from ..services.tools import (
        ClaudeCodeAgent,
        HyprlandMonitor,
        ApplicationContext,
        create_context_aware_agent
    )
    CLAUDE_CODE_AVAILABLE = True
except ImportError:
    CLAUDE_CODE_AVAILABLE = False
    print("Warning: Claude Code integration not available")

# Import services
from ..services.agent_skills import SkillRegistry
from ..services.hooks import HookManager, HookEvent
from ..services.mcp import MCPServerManager
from ..services.subagents import SubAgentSystem

# Import TTS agent
try:
    from ..services.claude_tts_agent import ClaudeTTSAgent
    TTS_AGENT_AVAILABLE = True
except ImportError:
    TTS_AGENT_AVAILABLE = False
    print("Warning: Claude TTS Agent not available")

from hypr_voice.config import load_config


# ============================================================================
# CONFIGURATION & MODELS
# ============================================================================

class AgentStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    COMPLETED = "completed"


class EventType(str, Enum):
    AGENT_CREATED = "agent_created"
    AGENT_STARTED = "agent_started"
    AGENT_OUTPUT = "agent_output"
    AGENT_ERROR = "agent_error"
    AGENT_COMPLETED = "agent_completed"
    TOOL_EXECUTION = "tool_execution"
    MCP_EVENT = "mcp_event"
    SKILL_EXECUTED = "skill_executed"
    SUBAGENT_CREATED = "subagent_created"
    VOICE_SYNTHESIS = "voice_synthesis"


@dataclass
class AgentEvent:
    event_type: EventType
    agent_id: str
    timestamp: str
    data: Dict[str, Any]
    
    def to_dict(self):
        return {
            "event_type": self.event_type.value,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "data": self.data
        }


class AgentConfig(BaseModel):
    name: str
    working_directory: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 8096
    temperature: float = 1.0
    permission_mode: str = "default"
    system_prompt: Optional[str] = None
    setting_sources: List[str] = ["project"]
    allowed_tools: List[str] = ["Read", "Write", "Edit", "Grep", "Glob", "Bash", "Skill", "SlashCommand"]
    skills: List[str] = []
    mcp_servers: List[str] = []
    custom_tools: List[str] = []
    enable_voice: bool = False
    enable_monitoring: bool = True  # Enable Hyprland monitoring
    monitor_interval: float = 0.15  # Application context update interval
    use_claude_code: bool = True  # Use Claude Code SDK
    capture_clipboard: bool = False  # Safety default: off
    capture_terminal_history: bool = False  # Safety default: off
    terminal_history_lines: int = 5
    parent_id: Optional[str] = None
    # TTS Agent Configuration
    enable_tts_agent: bool = False  # Use Claude TTS Agent
    tts_provider: str = "kokoro"  # kokoro, deepgram, elevenlabs
    tts_voice: Optional[str] = None  # Specific voice or None for default
    auto_synthesize: bool = True  # Auto-synthesize responses
    permission_timeout: int = 30  # Timeout for permission requests in seconds


# ============================================================================
# WEBSOCKET MANAGER
# ============================================================================

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.agent_subscriptions: Dict[str, Set[str]] = {}  # agent_id -> client_ids
        self.logger = logging.getLogger("ConnectionManager")
    
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        self.active_connections[client_id].append(websocket)
        self.logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
            if not self.active_connections[client_id]:
                del self.active_connections[client_id]
        self.logger.info(f"Client {client_id} disconnected")
    
    async def subscribe_to_agent(self, client_id: str, agent_id: str):
        """Subscribe a client to agent events"""
        if agent_id not in self.agent_subscriptions:
            self.agent_subscriptions[agent_id] = set()
        self.agent_subscriptions[agent_id].add(client_id)
    
    async def broadcast_event(self, event: AgentEvent):
        """Broadcast event to subscribed clients"""
        message = json.dumps(event.to_dict())
        
        # Get clients subscribed to this agent
        subscribed_clients = self.agent_subscriptions.get(event.agent_id, set())
        
        # Also broadcast to all clients for now (can be configured)
        all_clients = set(self.active_connections.keys())
        target_clients = all_clients | subscribed_clients
        
        disconnected = []
        for client_id in target_clients:
            if client_id in self.active_connections:
                for connection in self.active_connections[client_id]:
                    try:
                        await connection.send_text(message)
                    except Exception as e:
                        self.logger.error(f"Error sending to {client_id}: {e}")
                        disconnected.append((client_id, connection))
        
        # Clean up disconnected clients
        for client_id, connection in disconnected:
            self.disconnect(connection, client_id)


# ============================================================================
# SKILL SYSTEM
# ============================================================================

class Skill:
    """Base class for agent skills"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = True
    
    async def execute(self, agent_context: Dict, **kwargs) -> Any:
        raise NotImplementedError
    
    def to_tool(self):
        """Convert to Claude SDK tool format"""
        @tool(name=self.name, description=self.description)
        async def skill_tool(**kwargs):
            return await self.execute(kwargs.get('agent_context', {}), **kwargs)
        return skill_tool


class FileOperationsSkill(Skill):
    def __init__(self):
        super().__init__(
            name="file_operations",
            description="Read, write, and manipulate files in the working directory"
        )
    
    async def execute(self, agent_context: Dict, operation: str, **kwargs) -> Any:
        working_dir = Path(agent_context.get("working_directory", "/tmp"))
        
        if operation == "read":
            file_path = working_dir / kwargs.get("path", "")
            if file_path.exists():
                return file_path.read_text()
            return f"File not found: {file_path}"
            
        elif operation == "write":
            file_path = working_dir / kwargs.get("path", "")
            content = kwargs.get("content", "")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            return f"Written to {file_path}"
            
        elif operation == "list":
            path = working_dir / kwargs.get("path", ".")
            if path.exists() and path.is_dir():
                return [str(p.relative_to(working_dir)) 
                       for p in path.rglob("*") if p.is_file()]
            return []
            
        elif operation == "delete":
            file_path = working_dir / kwargs.get("path", "")
            if file_path.exists():
                file_path.unlink()
                return f"Deleted {file_path}"
            return f"File not found: {file_path}"


class BashExecutionSkill(Skill):
    def __init__(self):
        super().__init__(
            name="bash_execution",
            description="Execute bash commands in the agent's working directory"
        )
    
    async def execute(self, agent_context: Dict, command: str, **kwargs) -> Any:
        working_dir = agent_context.get("working_directory", "/tmp")
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "stdout": stdout.decode(),
            "stderr": stderr.decode(),
            "returncode": process.returncode
        }


class VoiceSkill(Skill):
    """Voice synthesis skill using Kokoro TTS"""
    def __init__(self):
        super().__init__(
            name="voice_synthesis",
            description="Convert text to speech using Kokoro TTS"
        )
    
    async def execute(self, agent_context: Dict, text: str, voice: str = "af_bella", **kwargs) -> Any:
        # Import Kokoro integration if available
        try:
            from hypr_voice.services.voice.providers.kokoro.kokoro import (
                KokoroTTS,
                KokoroConfig,
                KokoroVoice,
            )
            
            config = KokoroConfig(voice=voice)
            tts = KokoroTTS(config)
            
            working_dir = Path(agent_context.get("working_directory", "/tmp"))
            output_path = working_dir / f"speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            audio_file = await tts.synthesize(text, str(output_path))
            
            return {
                "status": "synthesized",
                "text": text,
                "voice": voice,
                "audio_path": str(audio_file)
            }
        except ImportError:
            return {
                "status": "error",
                "error": "Kokoro TTS not available"
            }


class SkillRegistry:
    def __init__(self):
        self.skills: Dict[str, Skill] = {}
        self._register_default_skills()
    
    def _register_default_skills(self):
        self.register(FileOperationsSkill())
        self.register(BashExecutionSkill())
        self.register(VoiceSkill())
    
    def register(self, skill: Skill):
        self.skills[skill.name] = skill
    
    def get(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)
    
    def list_skills(self) -> List[Dict]:
        return [
            {"name": s.name, "description": s.description, "enabled": s.enabled}
            for s in self.skills.values()
        ]
    
    def get_tools(self, skill_names: List[str]) -> List[Any]:
        """Get Claude SDK tools for specified skills"""
        tools = []
        for name in skill_names:
            skill = self.get(name)
            if skill:
                tools.append(skill.to_tool())
        return tools


# ============================================================================
# MCP INTEGRATION
# ============================================================================

class MCPServerManager:
    """Manages MCP servers for agents"""
    
    def __init__(self):
        self.servers: Dict[str, Any] = {}
        self.logger = logging.getLogger("MCPServerManager")
        self._load_presets()
    
    def _load_presets(self):
        """Load preset MCP server configurations"""
        self.presets = {
            "filesystem": {
                "name": "filesystem",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "description": "File system operations"
            },
            "github": {
                "name": "github",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-github"],
                "description": "GitHub operations",
                "env": {"GITHUB_TOKEN": os.environ.get("GITHUB_TOKEN", "")}
            },
            "git": {
                "name": "git",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-git"],
                "description": "Git operations"
            },
            "brave-search": {
                "name": "brave-search",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "description": "Brave search",
                "env": {"BRAVE_API_KEY": os.environ.get("BRAVE_API_KEY", "")}
            }
        }
    
    def get_server_config(self, name: str) -> Optional[Dict]:
        """Get MCP server configuration"""
        if name in self.presets:
            return self.presets[name]
        return None
    
    def create_mcp_server(self, name: str) -> Optional[Any]:
        """Create MCP server for Claude SDK"""
        if CLAUDE_SDK_AVAILABLE:
            config = self.get_server_config(name)
            if config:
                # Create SDK MCP server
                tools = []  # Add MCP-specific tools here
                return create_sdk_mcp_server(
                    name=config["name"],
                    version="1.0.0",
                    tools=tools
                )
        return None


# ============================================================================
# AGENT IMPLEMENTATION
# ============================================================================

class EnhancedAgent:
    """Enhanced agent with Claude SDK integration"""
    
    def __init__(
        self,
        agent_id: str,
        config: AgentConfig,
        event_manager: ConnectionManager,
        skill_registry: SkillRegistry,
        mcp_manager: MCPServerManager,
        parent_agent: Optional['EnhancedAgent'] = None
    ):
        self.agent_id = agent_id
        self.config = config
        self.status = AgentStatus.IDLE
        self.event_manager = event_manager
        self.skill_registry = skill_registry
        self.mcp_manager = mcp_manager
        self.parent_agent = parent_agent
        self.subagents: Dict[str, 'EnhancedAgent'] = {}
        self.conversation_history: List[Dict] = []
        self.logger = logging.getLogger(f"Agent-{agent_id}")
        self.permission_waiters: Dict[str, asyncio.Future] = {}
        
        # Ensure working directory exists
        self.working_dir = Path(config.working_directory)
        self.working_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Claude SDK agent if available
        self.claude_agent = None
        self._initialize_claude_agent()
        
        # Initialize TTS agent if enabled
        self.tts_agent = None
        if self.config.enable_tts_agent and TTS_AGENT_AVAILABLE:
            self._initialize_tts_agent()
    
    def _initialize_claude_agent(self):
        """Initialize Claude SDK agent"""
        if CLAUDE_CODE_AVAILABLE and self.config.use_claude_code:
            # Use Claude Code integration with Hyprland monitoring
            try:
                asyncio.create_task(self._init_claude_code_agent())
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude Code agent: {e}")
                self.claude_agent = None
                
        elif CLAUDE_SDK_AVAILABLE:
            # Fallback to standard Claude SDK
            try:
                # Prepare tools
                tools = self.skill_registry.get_tools(self.config.skills)
                
                # Prepare MCP servers
                mcp_servers = []
                for server_name in self.config.mcp_servers:
                    server = self.mcp_manager.create_mcp_server(server_name)
                    if server:
                        mcp_servers.append(server)
                
                # Create agent options
                options = ClaudeAgentOptions(
                    model=self.config.model,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    tools=tools,
                    mcp_servers=mcp_servers,
                    permission_mode=self.config.permission_mode,
                    working_directory=str(self.working_dir),
                    system_prompt=self.config.system_prompt,
                    setting_sources=self.config.setting_sources,
                    allowed_tools=self.config.allowed_tools,
                    can_use_tool=self._permission_callback if PermissionResultAllow else None,
                )
                
                # Create Claude SDK client
                self.claude_agent = ClaudeSDKClient(options)
                
            except Exception as e:
                self.logger.error(f"Failed to initialize Claude SDK: {e}")
                self.claude_agent = None
    
    async def _init_claude_code_agent(self):
        """Initialize Claude Code agent with monitoring"""
        try:
            # Prepare tools
            tools = self.skill_registry.get_tools(self.config.skills)
            
            # Create context-aware agent
            self.claude_agent = await create_context_aware_agent(
                name=self.config.name,
                working_directory=str(self.working_dir),
                enable_monitoring=self.config.enable_monitoring,
                monitor_interval=self.config.monitor_interval,
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                permission_mode=self.config.permission_mode,
                system_prompt=self.config.system_prompt,
                setting_sources=self.config.setting_sources,
                allowed_tools=self.config.allowed_tools,
                can_use_tool=self._permission_callback if PermissionResultAllow else None,
                tools=tools
            )
            
            # Register context change handler
            if self.claude_agent.monitor:
                self.claude_agent.monitor.register_callback(self._on_app_context_change)
            
            self.logger.info(f"Claude Code agent initialized with monitoring: {self.config.enable_monitoring}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude Code agent: {e}")
            self.claude_agent = None
    
    async def _on_app_context_change(self, context: ApplicationContext):
        """Handle application context changes"""
        await self._emit_event(
            EventType.AGENT_OUTPUT,
            {
                "type": "context_change",
                "application": context.window_class,
                "title": context.window_title,
                "vocabulary_size": len(context.vocabulary)
            }
        )
    
    def _initialize_tts_agent(self):
        """Initialize TTS agent"""
        try:
            self.tts_agent = ClaudeTTSAgent(
                enable_tts=True,
                tts_provider=self.config.tts_provider,
                tts_voice=self.config.tts_voice,
                tts_voice=self.config.tts_voice,
                working_directory=str(self.working_dir),
                system_prompt="You are a helpful AI assistant with text-to-speech capabilities.",
                use_local_claude=False
            )
            self.logger.info(f"TTS agent initialized with provider: {self.config.tts_provider}")
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS agent: {e}")
            self.tts_agent = None
    
    async def _emit_event(self, event_type: EventType, data: Dict):
        """Emit an event"""
        event = AgentEvent(
            event_type=event_type,
            agent_id=self.agent_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data
        )
        
        await self.event_manager.broadcast_event(event)
    
    async def execute_instruction(self, instruction: str, stream: bool = True):
        """Execute an instruction"""
        self.status = AgentStatus.RUNNING
        
        await self._emit_event(
            EventType.AGENT_STARTED,
            {
                "instruction": instruction,
                "working_directory": str(self.working_dir),
                "parent_id": self.config.parent_id
            }
        )
        
        try:
            # Build contextualized instruction
            ctx_prefix = await self._build_context_prefix()
            full_instruction = f"{ctx_prefix}\n\n{instruction}" if ctx_prefix else instruction
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": full_instruction
            })
            
            if self.claude_agent:
                # Use Claude SDK
                response = await self.claude_agent.run(full_instruction)
                
                # Stream response
                if stream:
                    async for chunk in response:
                        await self._emit_event(
                            EventType.AGENT_OUTPUT,
                            {
                                "type": "text_delta",
                                "content": chunk
                            }
                        )
                
                # Add to history
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response.content if hasattr(response, 'content') else str(response)
                })
                
            else:
                # Mock response for testing
                response = f"[Mock Response] Processing: {instruction}"
                
                await self._emit_event(
                    EventType.AGENT_OUTPUT,
                    {
                        "type": "text",
                        "content": response
                    }
                )
                
                self.conversation_history.append({
                    "role": "assistant",
                    "content": response
                })
            
            # Handle voice synthesis if enabled
            if self.config.enable_voice and response:
                await self._synthesize_voice(str(response))
            
            # Handle TTS agent synthesis if enabled
            if self.config.enable_tts_agent and self.tts_agent and self.config.auto_synthesize and response:
                await self._synthesize_with_tts_agent(str(response))
            
            self.status = AgentStatus.COMPLETED
            await self._emit_event(
                EventType.AGENT_COMPLETED,
                {
                    "final_output": str(response),
                    "conversation_length": len(self.conversation_history)
                }
            )
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Agent error: {e}", exc_info=True)
            await self._emit_event(
                EventType.AGENT_ERROR,
                {"error": str(e), "type": type(e).__name__}
            )
            raise
    
    async def _synthesize_voice(self, text: str):
        """Synthesize voice for text"""
        voice_skill = self.skill_registry.get("voice_synthesis")
        if voice_skill:
            result = await voice_skill.execute(
                {"working_directory": str(self.working_dir)},
                text=text
            )
            
            await self._emit_event(
                EventType.VOICE_SYNTHESIS,
                result
            )

    async def _build_context_prefix(self) -> str:
        """Collect contextual signals to prepend to user prompt."""
        parts = []
        
        # Active application context from Claude Code monitor if available
        app_ctx = None
        if hasattr(self, "claude_agent") and getattr(self, "claude_agent", None):
            app_ctx = getattr(self.claude_agent, "current_context", None)
        if not app_ctx and CLAUDE_CODE_AVAILABLE:
            try:
                monitor = HyprlandMonitor(update_interval=self.config.monitor_interval)
                window = await monitor.get_active_window()
                if window:
                    app_ctx = ApplicationContext(
                        window_class=window.get("class", ""),
                        window_title=window.get("title", ""),
                        vocabulary=[]
                    )
            except Exception:
                app_ctx = None
        
        if app_ctx:
            parts.append(f"[Active Window] class={app_ctx.window_class} title={app_ctx.window_title}")
            if app_ctx.vocabulary:
                vocab_preview = ", ".join(app_ctx.vocabulary[:10])
                parts.append(f"[Vocabulary] {vocab_preview}")
        
        # Clipboard text (optional)
        if self.config.capture_clipboard:
            clip = await self._get_clipboard_text()
            if clip:
                parts.append(f"[Clipboard] {clip[:500]}")
        
        # Terminal history (optional)
        if self.config.capture_terminal_history:
            history = self._get_recent_commands(self.config.terminal_history_lines)
            if history:
                parts.append("[Recent Commands]\n" + "\n".join(history))
        
        return "\n".join(parts)
    
    async def _permission_callback(self, tool_name: str, tool_input: dict, context: Any):
        """
        Permission callback for Claude Agent SDK.
        Emits a permission request event and waits for user approval via WebSocket.
        """
        if not PermissionResultAllow:
            return None
        
        request_id = str(uuid.uuid4())
        loop = asyncio.get_running_loop()
        fut: asyncio.Future = loop.create_future()
        self.permission_waiters[request_id] = fut
        
        # Broadcast request
        await self._emit_event(
            EventType.TOOL_EXECUTION,
            {
                "type": "permission_request",
                "request_id": request_id,
                "tool_name": tool_name,
                "tool_input": tool_input,
                "agent_id": self.agent_id,
            }
        )
        
        try:
            decision = await asyncio.wait_for(fut, timeout=self.config.permission_timeout)
        except asyncio.TimeoutError:
            return PermissionResultDeny(behavior="deny", message="Permission timed out", interrupt=False)
        finally:
            self.permission_waiters.pop(request_id, None)
        
        if not isinstance(decision, dict):
            return PermissionResultDeny(behavior="deny", message="Invalid permission response", interrupt=False)
        
        approved = decision.get("allow", False)
        updated_input = decision.get("updated_input")
        if approved:
            return PermissionResultAllow(behavior="allow", updated_input=updated_input)
        return PermissionResultDeny(
            behavior="deny",
            message=decision.get("reason", "Denied by user"),
            interrupt=False
        )
    
    def receive_permission_response(self, request_id: str, allow: bool, updated_input: Optional[dict] = None, reason: str = ""):
        """Handle permission response from client."""
        fut = self.permission_waiters.get(request_id)
        if fut and not fut.done():
            fut.set_result({"allow": allow, "updated_input": updated_input, "reason": reason})
    
    async def _get_clipboard_text(self) -> Optional[str]:
        """Read clipboard text using wl-paste or xclip."""
        cmds = [
            ["wl-paste", "-n"],
            ["xclip", "-selection", "clipboard", "-o"]
        ]
        for cmd in cmds:
            try:
                proc = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                out, _ = await proc.communicate()
                if proc.returncode == 0:
                    text = out.decode(errors="ignore").strip()
                    if text:
                        return text
            except FileNotFoundError:
                continue
            except Exception:
                continue
        return None
    
    def _get_recent_commands(self, n: int) -> List[str]:
        """Tail recent shell commands."""
        history_paths = []
        shell = os.getenv("SHELL", "")
        home = Path.home()
        if "zsh" in shell:
            history_paths.append(home / ".zsh_history")
        if "bash" in shell:
            history_paths.append(home / ".bash_history")
        history_paths.append(home / ".local/share/fish/fish_history")
        
        for path in history_paths:
            if path.exists():
                try:
                    lines = path.read_text(errors="ignore").splitlines()
                    if "fish_history" in str(path):
                        # fish format: - cmd: ...
                        cmds = [ln.split(": ", 1)[1] for ln in lines if ln.strip().startswith("- cmd:")]
                    else:
                        cmds = [ln for ln in lines if ln.strip()]
                    return cmds[-n:] if len(cmds) >= n else cmds
                except Exception:
                    continue
        return []
    
    async def _synthesize_with_tts_agent(self, text: str):
        """Synthesize speech using TTS agent"""
        try:
            await self.tts_agent.connect()
            result = await self.tts_agent.chat(
                text,
                synthesize_response=True,
                save_file=True
            )
            
            await self._emit_event(
                EventType.VOICE_SYNTHESIS,
                {
                    "type": "tts_agent_synthesis",
                    "provider": self.config.tts_provider,
                    "voice_used": result.get("voice_used"),
                    "audio_file": result.get("audio_file"),
                    "success": result.get("success"),
                    "text": text
                }
            )
            
            self.logger.info(f"TTS agent synthesis completed: {result.get('audio_file')}")
            
        except Exception as e:
            self.logger.error(f"TTS agent synthesis failed: {e}")
            await self._emit_event(
                EventType.VOICE_SYNTHESIS,
                {
                    "type": "tts_agent_error",
                    "error": str(e),
                    "text": text
                }
            )
        finally:
            try:
                await self.tts_agent.close()
            except:
                pass
    
    async def create_subagent(self, name: str, skills: List[str] = None) -> 'EnhancedAgent':
        """Create a subagent"""
        subagent_config = AgentConfig(
            name=f"{self.config.name}/{name}",
            working_directory=str(self.working_dir / "subagents" / name),
            model=self.config.model,
            skills=skills or ["file_operations"],
            parent_id=self.agent_id
        )
        
        subagent = EnhancedAgent(
            agent_id=str(uuid.uuid4()),
            config=subagent_config,
            event_manager=self.event_manager,
            skill_registry=self.skill_registry,
            mcp_manager=self.mcp_manager,
            parent_agent=self
        )
        
        self.subagents[name] = subagent
        
        await self._emit_event(
            EventType.SUBAGENT_CREATED,
            {
                "subagent_id": subagent.agent_id,
                "name": name,
                "parent_id": self.agent_id
            }
        )
        
        return subagent
    
    async def execute_subagents_parallel(self, subagent_names: List[str], instruction: str):
        """Execute multiple subagents in parallel"""
        tasks = []
        for name in subagent_names:
            if name in self.subagents:
                tasks.append(self.subagents[name].execute_instruction(instruction))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
    
    async def execute_subagents_sequential(self, subagent_names: List[str], instructions: Dict[str, str]):
        """Execute subagents sequentially with different instructions"""
        results = {}
        for name in subagent_names:
            if name in self.subagents and name in instructions:
                result = await self.subagents[name].execute_instruction(instructions[name])
                results[name] = result
        return results


# ============================================================================
# AGENT ORCHESTRATOR
# ============================================================================

class AgentOrchestrator:
    """Main orchestrator for managing agents"""
    
    def __init__(self):
        self.agents: Dict[str, EnhancedAgent] = {}
        self.event_manager = ConnectionManager()
        self.skill_registry = SkillRegistry()
        self.mcp_manager = MCPServerManager()
        self.logger = logging.getLogger("Orchestrator")
        self._load_configuration()
    
    def _load_configuration(self):
        """Load configuration from file"""
        try:
            self.config = load_config()
        except FileNotFoundError:
            self.config = self._default_config()
        except Exception as exc:  # pragma: no cover - defensive logging only
            self.logger.warning(f"Failed to load configuration, using defaults: {exc}")
            self.config = self._default_config()

    @staticmethod
    def _default_config() -> Dict[str, Any]:
        return {
            "server": {
                "host": "0.0.0.0",
                "port": 8922,
                "log_level": "INFO",
            },
            "defaults": {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 8096,
                "temperature": 1.0,
                "permission_timeout": 30,
            },
        }

    async def create_agent(self, config: AgentConfig) -> str:
        """Create a new agent"""
        agent_id = str(uuid.uuid4())

        # Apply defaults from configuration
        if not config.model:
            config.model = self.config.get("defaults", {}).get("model", "claude-3-5-sonnet-20241022")
        if not config.max_tokens:
            config.max_tokens = self.config.get("defaults", {}).get("max_tokens", 8096)

        # Load permission timeout from orchestrator section or defaults
        if config.permission_timeout == 30:  # If still at default
            config.permission_timeout = self.config.get("orchestrator", {}).get(
                "permission_timeout",
                self.config.get("defaults", {}).get("permission_timeout", 30)
            )
        
        agent = EnhancedAgent(
            agent_id=agent_id,
            config=config,
            event_manager=self.event_manager,
            skill_registry=self.skill_registry,
            mcp_manager=self.mcp_manager
        )
        
        self.agents[agent_id] = agent
        
        await agent._emit_event(
            EventType.AGENT_CREATED,
            {"config": config.dict()}
        )
        
        self.logger.info(f"Created agent {agent_id} ({config.name})")
        return agent_id
    
    def get_agent(self, agent_id: str) -> Optional[EnhancedAgent]:
        """Get an agent by ID"""
        return self.agents.get(agent_id)
    
    async def execute_instruction(self, agent_id: str, instruction: str, stream: bool = True):
        """Execute instruction on an agent"""
        agent = self.get_agent(agent_id)
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        await agent.execute_instruction(instruction, stream)
    
    def list_agents(self) -> List[Dict]:
        """List all agents"""
        return [
            {
                "agent_id": agent_id,
                "name": agent.config.name,
                "status": agent.status.value,
                "working_directory": agent.config.working_directory,
                "parent_id": agent.config.parent_id,
                "subagents": list(agent.subagents.keys())
            }
            for agent_id, agent in self.agents.items()
        ]
    
    def delete_agent(self, agent_id: str) -> bool:
        """Delete an agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self.logger.info(f"Deleted agent {agent_id}")
            return True
        return False
    
    async def shutdown(self):
        """Shutdown all agents"""
        for agent in self.agents.values():
            if hasattr(agent, 'claude_agent') and agent.claude_agent:
                # Cleanup Claude SDK resources
                pass
        self.logger.info("Orchestrator shutdown complete")


# ============================================================================
# FASTAPI APPLICATION
# ============================================================================

# Create orchestrator
orchestrator = AgentOrchestrator()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    yield
    # Shutdown
    await orchestrator.shutdown()

app = FastAPI(
    title="Multi-Agent Orchestration System",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/agents/create")
async def create_agent(config: AgentConfig):
    agent_id = await orchestrator.create_agent(config)
    return {"agent_id": agent_id, "status": "created"}


@app.post("/agents/{agent_id}/instruct")
async def instruct_agent(agent_id: str, instruction: str, stream: bool = True):
    asyncio.create_task(
        orchestrator.execute_instruction(agent_id, instruction, stream)
    )
    return {"status": "instruction_queued", "agent_id": agent_id}


@app.get("/agents/list")
async def list_agents():
    return {"agents": orchestrator.list_agents()}


@app.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    return {
        "agent_id": agent_id,
        "name": agent.config.name,
        "status": agent.status.value,
        "working_directory": agent.config.working_directory,
        "conversation_length": len(agent.conversation_history),
        "subagents": list(agent.subagents.keys())
    }


@app.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str):
    if orchestrator.delete_agent(agent_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Agent not found")


@app.post("/agents/{agent_id}/subagents/create")
async def create_subagent(agent_id: str, name: str, skills: List[str] = None):
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    subagent = await agent.create_subagent(name, skills)
    return {
        "subagent_id": subagent.agent_id,
        "name": name,
        "parent_id": agent_id
    }


@app.get("/skills/list")
async def list_skills():
    return {"skills": orchestrator.skill_registry.list_skills()}


@app.get("/mcp/presets")
async def list_mcp_presets():
    return {"presets": list(orchestrator.mcp_manager.presets.keys())}


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await orchestrator.event_manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message.get("type") == "subscribe":
                agent_id = message.get("agent_id")
                if agent_id:
                    await orchestrator.event_manager.subscribe_to_agent(client_id, agent_id)
                    await websocket.send_json({"type": "subscribed", "agent_id": agent_id})
            
            elif message.get("type") == "ping":
                await websocket.send_json({"type": "pong", "client_id": client_id})
            
            elif message.get("type") == "permission_response":
                request_id = message.get("request_id")
                allow = bool(message.get("allow", False))
                updated_input = message.get("updated_input")
                reason = message.get("reason", "")
                target_agent = message.get("agent_id")
                agent = orchestrator.get_agent(target_agent) if target_agent else None
                if agent and hasattr(agent, "receive_permission_response"):
                    agent.receive_permission_response(request_id, allow, updated_input, reason)
                    await websocket.send_json({"type": "permission_ack", "request_id": request_id})
                else:
                    await websocket.send_json({"type": "permission_error", "request_id": request_id, "error": "agent_not_found"})
            
    except WebSocketDisconnect:
        orchestrator.event_manager.disconnect(websocket, client_id)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agents_count": len(orchestrator.agents),
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8922)
