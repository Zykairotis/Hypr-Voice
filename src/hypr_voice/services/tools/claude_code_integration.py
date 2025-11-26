"""
Claude Code SDK Integration Module
Provides seamless integration with Claude Code instance for AI assistance
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncIterator
from datetime import datetime
from dataclasses import dataclass, field

try:
    # Try to import the real Claude SDK
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        AssistantMessage,
        UserMessage,
        SystemMessage,
        ResultMessage,
        TextBlock,
        ThinkingBlock,
        ToolUseBlock,
        ToolResultBlock,
        tool
    )
except ImportError:
    # Fall back to mock implementation
    from claude_agent_sdk_mock import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        AssistantMessage,
        UserMessage,
        SystemMessage,
        ResultMessage,
        TextBlock,
        ThinkingBlock,
        ToolUseBlock,
        ToolResultBlock,
        tool
    )
    logging.warning("Using mock Claude SDK implementation")

# Import vocabulary manager from Hypr-Whisper
sys.path.append(str(Path(__file__).parent.parent.parent / "Hypr-Whisper"))
try:
    from vocabulary_manager import VocabularyManager
    VOCABULARY_MANAGER_AVAILABLE = True
except ImportError:
    VOCABULARY_MANAGER_AVAILABLE = False
    logging.warning("Vocabulary manager not available")

logger = logging.getLogger(__name__)


@dataclass
class ApplicationContext:
    """Context about the currently active application"""
    window_class: str
    window_title: str
    vocabulary: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "window_class": self.window_class,
            "window_title": self.window_title,
            "vocabulary": self.vocabulary,
            "detected_at": self.detected_at.isoformat()
        }


class HyprlandMonitor:
    """Monitor Hyprland window manager for active applications"""
    
    def __init__(self, update_interval: float = 0.1):
        self.update_interval = update_interval
        self.current_context: Optional[ApplicationContext] = None
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self.callbacks = []
        
        # Initialize vocabulary manager if available
        self.vocabulary_manager = None
        if VOCABULARY_MANAGER_AVAILABLE:
            try:
                # Initialize with the Hypr-Whisper config path
                config_path = Path(__file__).parent.parent.parent / "Hypr-Whisper" / "config"
                self.vocabulary_manager = VocabularyManager(config_path=str(config_path))
                logger.info("Vocabulary manager initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize vocabulary manager: {e}")
        
    async def get_active_window(self) -> Optional[Dict]:
        """Get current active window from Hyprland"""
        try:
            process = await asyncio.create_subprocess_exec(
                'hyprctl', 'activewindow', '-j',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                data = json.loads(stdout.decode())
                return {
                    'class': data.get('class', ''),
                    'title': data.get('title', ''),
                    'initialClass': data.get('initialClass', ''),
                    'initialTitle': data.get('initialTitle', '')
                }
        except Exception as e:
            logger.error(f"Error getting Hyprland active window: {e}")
        return None
    
    async def get_all_clients(self) -> List[Dict]:
        """Get all client windows from Hyprland"""
        try:
            process = await asyncio.create_subprocess_exec(
                'hyprctl', 'clients', '-j',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return json.loads(stdout.decode())
        except Exception as e:
            logger.error(f"Error getting Hyprland clients: {e}")
        return []
    
    def register_callback(self, callback):
        """Register a callback for context changes"""
        self.callbacks.append(callback)
    
    async def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info(f"Starting Hyprland monitoring (interval: {self.update_interval}s)")
        
        while self._running:
            try:
                window_info = await self.get_active_window()
                
                if window_info:
                    # Check if context changed
                    window_class = window_info.get('class', '') or window_info.get('initialClass', '')
                    window_title = window_info.get('title', '') or window_info.get('initialTitle', '')
                    
                    if (not self.current_context or 
                        self.current_context.window_class != window_class or
                        self.current_context.window_title != window_title):
                        
                        # Context changed
                        self.current_context = ApplicationContext(
                            window_class=window_class,
                            window_title=window_title
                        )
                        
                        # Load vocabulary for this application
                        self.current_context.vocabulary = self._get_app_vocabulary(window_class)
                        
                        logger.info(f"Application context changed: {window_class} - {window_title}")
                        
                        # Notify callbacks
                        for callback in self.callbacks:
                            try:
                                await callback(self.current_context)
                            except Exception as e:
                                logger.error(f"Error in context callback: {e}")
                
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    def _get_app_vocabulary(self, app_class: str) -> List[str]:
        """Get vocabulary for specific application"""
        
        if self.vocabulary_manager:
            try:
                # Update vocabulary for the application
                self.vocabulary_manager.update_vocabulary(app_class)
                
                # Get active keywords as a list
                vocabulary = list(self.vocabulary_manager.active_keywords)
                
                logger.debug(f"Loaded {len(vocabulary)} vocabulary terms for {app_class}")
                return vocabulary
                
            except Exception as e:
                logger.warning(f"Failed to get vocabulary for {app_class}: {e}")
        
        # Fallback to default vocabularies if manager not available
        app_vocabularies = {
            'code': ['function', 'variable', 'class', 'import', 'async', 'await', 'const', 'let'],
            'firefox': ['tab', 'bookmark', 'url', 'search', 'download', 'refresh', 'back', 'forward'],
            'alacritty': ['cd', 'ls', 'git', 'npm', 'python', 'cargo', 'vim', 'nano'],
            'discord': ['channel', 'server', 'message', 'voice', 'mute', 'deafen', 'stream'],
            'obsidian': ['note', 'vault', 'link', 'tag', 'graph', 'markdown', 'backlink']
        }
        
        # Check for matching application
        app_lower = app_class.lower()
        for key, vocab in app_vocabularies.items():
            if key in app_lower:
                return vocab
        
        return []
    
    async def start(self):
        """Start monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """Stop monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass


class ClaudeCodeAgent:
    """Enhanced Claude agent with Code SDK and application context"""
    
    def __init__(self, 
                 options: Optional[ClaudeAgentOptions] = None,
                 enable_monitoring: bool = True,
                 monitor_interval: float = 0.1):
        """
        Initialize Claude Code Agent
        
        Args:
            options: Claude SDK options
            enable_monitoring: Enable Hyprland monitoring
            monitor_interval: Update interval for monitoring (seconds)
        """
        self.options = options or ClaudeAgentOptions()
        self.client: Optional[ClaudeSDKClient] = None
        self.current_context: Optional[ApplicationContext] = None
        self.conversation_history: List[Dict] = []
        
        # Initialize Hyprland monitor if enabled
        self.monitor = None
        if enable_monitoring:
            self.monitor = HyprlandMonitor(update_interval=monitor_interval)
            self.monitor.register_callback(self._on_context_change)
        
        self.logger = logging.getLogger(f"ClaudeCodeAgent-{id(self)}")
    
    async def _on_context_change(self, context: ApplicationContext):
        """Handle application context changes"""
        self.current_context = context
        self.logger.info(f"Context updated: {context.window_class}")
        
        # Add system message about context change if client is active
        if self.client:
            context_msg = self._create_context_message(context)
            # This would be added to the conversation context
            # The actual implementation depends on Claude SDK capabilities
    
    def _create_context_message(self, context: ApplicationContext) -> str:
        """Create a context message for Claude"""
        vocab_str = ", ".join(context.vocabulary[:10]) if context.vocabulary else "none"
        
        return f"""Application Context Update:
- Active Window: {context.window_class}
- Window Title: {context.window_title}
- Relevant Vocabulary: {vocab_str}
- Time: {context.detected_at.isoformat()}

Adjust your responses and suggestions to be relevant to {context.window_class}."""
    
    async def initialize(self):
        """Initialize the Claude client and monitoring"""
        try:
            # Create Claude SDK client
            self.client = ClaudeSDKClient(self.options)
            
            # Start monitoring if enabled
            if self.monitor:
                await self.monitor.start()
            
            self.logger.info("Claude Code Agent initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Claude Code Agent: {e}")
            raise
    
    async def query_with_context(self, prompt: str, include_context: bool = True) -> AsyncIterator[Any]:
        """
        Query Claude with application context
        
        Args:
            prompt: User prompt
            include_context: Include application context in prompt
            
        Yields:
            Response messages from Claude
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")
        
        # Prepare prompt with context if available
        full_prompt = prompt
        if include_context and self.current_context:
            context_info = f"\n[Current Application: {self.current_context.window_class}]\n"
            full_prompt = context_info + prompt
        
        # Send query
        await self.client.query(full_prompt)
        
        # Stream responses
        async for message in self.client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        yield block.text
                    elif isinstance(block, ThinkingBlock):
                        # Log thinking blocks for debugging
                        self.logger.debug(f"Claude thinking: {block.text}")
            elif isinstance(message, ResultMessage):
                # Handle result messages if needed
                pass
    
    async def continuous_conversation(self, initial_prompt: Optional[str] = None):
        """
        Start a continuous conversation with Claude
        
        Args:
            initial_prompt: Optional initial prompt
        """
        async with self.client:
            if initial_prompt:
                await self.client.query(initial_prompt)
                
                async for response in self.client.receive_response():
                    yield response
            
            # Keep the conversation open for follow-ups
            # This would be integrated with the WebSocket interface
    
    async def execute_with_tools(self, prompt: str, tools: List[Any]) -> Any:
        """
        Execute a query with custom tools
        
        Args:
            prompt: User prompt
            tools: List of tools to make available
        """
        # Update options with tools
        self.options.tools = tools
        
        # Reinitialize client with new options
        if self.client:
            await self.shutdown()
        
        self.client = ClaudeSDKClient(self.options)
        
        # Execute query
        results = []
        await self.client.query(prompt)
        
        async for message in self.client.receive_response():
            results.append(message)
        
        return results
    
    async def shutdown(self):
        """Shutdown the agent and cleanup resources"""
        try:
            # Stop monitoring
            if self.monitor:
                await self.monitor.stop()
            
            # Disconnect client
            if self.client:
                await self.client.disconnect()
            
            self.logger.info("Claude Code Agent shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# Custom tools for Claude
@tool(
    name="get_application_context",
    description="Get current application context and window information",
    input_schema={}
)
async def get_application_context(args: dict) -> Dict:
    """Get current application context from Hyprland"""
    monitor = HyprlandMonitor()
    window = await monitor.get_active_window()
    
    if window:
        result = {
            "class": window.get("class", ""),
            "title": window.get("title", ""),
            "detected": True
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": False,
            "data": result,
        }
    
    result = {"detected": False}
    return {
        "content": [{"type": "text", "text": json.dumps(result)}],
        "is_error": True,
        "data": result,
    }


@tool(
    name="switch_to_window",
    description="Switch to a specific window by class or title",
    input_schema={"window_identifier": str}
)
async def switch_to_window(args: dict) -> Dict:
    """Switch to a window using Hyprland"""
    window_identifier = (args or {}).get("window_identifier", "")
    if not window_identifier:
        result = {"success": False, "error": "window_identifier is required"}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
    try:
        # Get all clients
        monitor = HyprlandMonitor()
        clients = await monitor.get_all_clients()
        
        # Find matching window
        for client in clients:
            if (window_identifier.lower() in client.get("class", "").lower() or
                window_identifier.lower() in client.get("title", "").lower()):
                
                # Switch to window
                address = client.get("address", "")
                if address:
                    process = await asyncio.create_subprocess_exec(
                        'hyprctl', 'dispatch', 'focuswindow', f'address:{address}',
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await process.communicate()
                    
                    result = {
                        "success": True,
                        "switched_to": client.get("class", ""),
                        "title": client.get("title", "")
                    }
                    return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": False, "data": result}
        
        result = {"success": False, "error": "Window not found"}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
    except Exception as e:
        result = {"success": False, "error": str(e)}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


@tool(
    name="list_open_windows",
    description="List all open windows in Hyprland",
    input_schema={}
)
async def list_open_windows(args: dict) -> Dict:
    """List all open windows"""
    try:
        monitor = HyprlandMonitor()
        clients = await monitor.get_all_clients()
        
        windows = []
        for client in clients:
            windows.append({
                "class": client.get("class", ""),
                "title": client.get("title", ""),
                "workspace": client.get("workspace", {}).get("id", -1),
                "focused": client.get("focusHistoryID", -1) == 0
            })
        
        result = {
            "success": True,
            "windows": windows,
            "count": len(windows)
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": False, "data": result}
        
    except Exception as e:
        result = {"success": False, "error": str(e)}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


# Integration helper for the orchestrator
async def create_context_aware_agent(
    name: str,
    working_directory: str,
    enable_monitoring: bool = True,
    monitor_interval: float = 0.1,
    **kwargs
) -> ClaudeCodeAgent:
    """
    Create a context-aware Claude Code agent
    
    Args:
        name: Agent name
        working_directory: Working directory for the agent
        enable_monitoring: Enable application monitoring
        monitor_interval: Monitoring update interval
        **kwargs: Additional options for ClaudeAgentOptions
    
    Returns:
        Initialized ClaudeCodeAgent
    """
    options = ClaudeAgentOptions(
        tools=[
            get_application_context,
            switch_to_window,
            list_open_windows
        ],
        **kwargs
    )
    
    agent = ClaudeCodeAgent(
        options=options,
        enable_monitoring=enable_monitoring,
        monitor_interval=monitor_interval
    )
    
    await agent.initialize()
    
    return agent
