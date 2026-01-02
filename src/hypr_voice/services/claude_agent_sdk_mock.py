"""
Mock implementation of Claude Agent SDK
This provides a compatible interface while the official SDK is not available
"""

import asyncio
import logging
from typing import AsyncIterator, Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import json

logger = logging.getLogger(__name__)


# Message types
@dataclass
class Message:
    """Base message class"""
    role: str
    content: Any
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UserMessage(Message):
    """User message"""
    def __init__(self, content: str):
        super().__init__(role="user", content=content)


@dataclass
class AssistantMessage(Message):
    """Assistant message"""
    def __init__(self, content: List[Any]):
        super().__init__(role="assistant", content=content)


@dataclass
class SystemMessage(Message):
    """System message"""
    def __init__(self, content: str):
        super().__init__(role="system", content=content)


@dataclass
class ResultMessage(Message):
    """Result message"""
    def __init__(self, result: Any):
        super().__init__(role="result", content=result)


# Content block types
@dataclass
class ContentBlock:
    """Base content block"""
    type: str
    

@dataclass
class TextBlock(ContentBlock):
    """Text content block"""
    text: str
    
    def __init__(self, text: str):
        super().__init__(type="text")
        self.text = text


@dataclass
class ThinkingBlock(ContentBlock):
    """Thinking content block"""
    text: str
    
    def __init__(self, text: str):
        super().__init__(type="thinking")
        self.text = text


@dataclass
class ToolUseBlock(ContentBlock):
    """Tool use block"""
    tool_name: str
    parameters: Dict[str, Any]
    
    def __init__(self, tool_name: str, parameters: Dict[str, Any]):
        super().__init__(type="tool_use")
        self.tool_name = tool_name
        self.parameters = parameters


@dataclass
class ToolResultBlock(ContentBlock):
    """Tool result block"""
    tool_name: str
    result: Any

    def __init__(self, tool_name: str, result: Any):
        super().__init__(type="tool_result")
        self.tool_name = tool_name
        self.result = result


# Permission results
@dataclass
class PermissionResultAllow:
    """Allow tool execution"""
    behavior: str = "allow"
    message: Optional[str] = None
    updated_input: Optional[Dict[str, Any]] = None


@dataclass
class PermissionResultDeny:
    """Deny tool execution"""
    behavior: str = "deny"
    message: Optional[str] = None


# Options and configuration
@dataclass
class ClaudeAgentOptions:
    """Configuration options for Claude agent"""
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 8096
    temperature: float = 1.0
    tools: List[Callable] = field(default_factory=list)
    mcp_servers: List[Any] = field(default_factory=list)
    system_prompt: Optional[str] = None
    

# Tool decorator
def tool(name: str = None, description: str = None):
    """Decorator to register a tool function"""
    def decorator(func):
        func._tool_name = name or func.__name__
        func._tool_description = description or func.__doc__
        func._is_tool = True
        return func
    return decorator


# Main client
class ClaudeSDKClient:
    """Mock Claude SDK Client"""
    
    def __init__(self, options: Optional[ClaudeAgentOptions] = None):
        self.options = options or ClaudeAgentOptions()
        self.conversation_history: List[Message] = []
        self.connected = False
        self.session_id = None
        logger.info("Mock Claude SDK Client initialized")
        
    async def __aenter__(self):
        """Async context manager enter"""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    async def connect(self, prompt: Optional[str] = None):
        """Connect to Claude (mock)"""
        self.connected = True
        self.session_id = f"mock-session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        logger.info(f"Mock client connected: {self.session_id}")
        
        if prompt:
            await self.query(prompt)
            
    async def query(self, prompt: str, session_id: str = "default"):
        """Send a query to Claude (mock)"""
        if not self.connected:
            await self.connect()
            
        # Add to history
        self.conversation_history.append(UserMessage(prompt))
        logger.info(f"Mock query received: {prompt[:100]}...")
        
        # Generate mock response
        self._current_response = self._generate_mock_response(prompt)
        
    async def receive_messages(self) -> AsyncIterator[Message]:
        """Receive all messages (mock)"""
        if hasattr(self, '_current_response'):
            for message in self._current_response:
                yield message
                await asyncio.sleep(0.01)  # Simulate streaming delay
                
    async def receive_response(self) -> AsyncIterator[Message]:
        """Receive response messages (mock)"""
        async for message in self.receive_messages():
            if isinstance(message, (AssistantMessage, ResultMessage)):
                yield message
                
    async def interrupt(self):
        """Interrupt current operation (mock)"""
        logger.info("Mock interrupt called")
        self._current_response = []
        
    async def disconnect(self):
        """Disconnect from Claude (mock)"""
        self.connected = False
        logger.info(f"Mock client disconnected: {self.session_id}")
        
    def _generate_mock_response(self, prompt: str) -> List[Message]:
        """Generate a mock response based on the prompt"""
        responses = []
        
        # Check for specific patterns
        if "application" in prompt.lower() or "window" in prompt.lower():
            content = [
                TextBlock("I can see you're asking about application context. "),
                TextBlock("In a real implementation, I would detect the active window using Hyprland. "),
                TextBlock("The current mock implementation simulates this functionality.")
            ]
        elif "code" in prompt.lower() or "program" in prompt.lower():
            content = [
                TextBlock("I can help you with coding tasks. "),
                TextBlock("This is a mock response demonstrating the Claude SDK interface. "),
                TextBlock("In production, I would provide actual code assistance.")
            ]
        else:
            content = [
                TextBlock(f"Mock response to: {prompt[:50]}... "),
                TextBlock("This is a simulated Claude SDK response. "),
                TextBlock("The actual SDK would provide more intelligent responses.")
            ]
            
        responses.append(AssistantMessage(content))
        
        # Add result message
        responses.append(ResultMessage({
            "status": "success",
            "mock": True,
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        return responses


# MCP Server creation (mock)
def create_sdk_mcp_server(name: str, version: str, tools: List[Any]) -> Dict:
    """Create a mock MCP server configuration"""
    return {
        "name": name,
        "version": version,
        "tools": [t.__name__ if hasattr(t, '__name__') else str(t) for t in tools],
        "mock": True
    }


# Export mock implementations as if they were real
__all__ = [
    'ClaudeSDKClient',
    'ClaudeAgentOptions',
    'Message',
    'UserMessage',
    'AssistantMessage',
    'SystemMessage',
    'ResultMessage',
    'TextBlock',
    'ThinkingBlock',
    'ToolUseBlock',
    'ToolResultBlock',
    'PermissionResultAllow',
    'PermissionResultDeny',
    'tool',
    'create_sdk_mcp_server',
    'query',
    'AgentDefinition'
]

async def query(**kwargs):
    """Mock query function"""
    options = kwargs.get('options')
    client = ClaudeSDKClient(options)
    await client.connect()
    await client.query(kwargs.get('prompt', ''))
    async for msg in client.receive_messages():
        yield msg

class AgentDefinition:
    """Mock AgentDefinition"""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
