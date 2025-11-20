"""
Helper Agent Integration API

High-level API for accessing helper agent capabilities with multi-provider support,
agentic workflows, MCP tools, and streaming.
"""

import asyncio
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union
from pathlib import Path

from .litellm_client import LiteLLMClient
from .model_factory import ModelFactory
from .mcp_server import MCPServer
from .agent_graph import LangGraphAgent
from .langgraph_tools import LangChainTools
from .tools.mcp_tools import MCPToolWrappers
from .tools.mcp_registry import MCPToolRegistry
from .streaming import stream_llm_response, SSEFormatter

logger = logging.getLogger(__name__)


class HelperAgentSession:
    """Session for conversational interactions."""
    
    def __init__(
        self,
        client: "HelperAgentIntegration",
        system_prompt: Optional[str] = None
    ):
        """
        Initialize session.
        
        Args:
            client: HelperAgentIntegration instance
            system_prompt: System prompt for conversation
        """
        self.client = client
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = []
        
        if system_prompt:
            self.messages.append({
                "role": "system",
                "content": system_prompt
            })
    
    async def send(self, message: str, **kwargs) -> str:
        """
        Send message and get response.
        
        Args:
            message: User message
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        response = await self.client.chat(self.messages, **kwargs)
        response_text = response.get("content", "")
        
        self.messages.append({
            "role": "assistant",
            "content": response_text
        })
        
        return response_text
    
    async def stream(self, message: str, **kwargs) -> AsyncIterator[str]:
        """
        Send message and stream response.
        
        Args:
            message: User message
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        self.messages.append({
            "role": "user",
            "content": message
        })
        
        collected = []
        async for chunk in self.client.stream_chat(self.messages, **kwargs):
            collected.append(chunk)
            yield chunk
        
        self.messages.append({
            "role": "assistant",
            "content": "".join(collected)
        })
    
    def reset(self):
        """Reset conversation history."""
        self.messages = []
        if self.system_prompt:
            self.messages.append({
                "role": "system",
                "content": self.system_prompt
            })


class HelperAgentIntegration:
    """
    High-level integration API for Helper Agent.
    
    Provides unified access to:
    - Multi-provider LLM access (10+ providers) via ModelFactory
    - Unified tool registry (MCP + LangChain)
    - LangGraph ReAct agent with official create_react_agent
    - MCP tool calling
    - Streaming support with SSE
    """
    
    def __init__(
        self,
        config_dir: Optional[Path] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize Helper Agent integration with unified architecture.
        
        Args:
            config_dir: Configuration directory
            provider: Default provider name (auto-selected if None)
            model: Default model name
        """
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.provider = provider
        self.model = model
        
        # Initialize LiteLLM client (for backwards compatibility and direct access)
        self.client = LiteLLMClient(
            config_path=self.config_dir / "providers.yaml"
        )
        
        # Initialize Model Factory
        self.model_factory = ModelFactory(
            config_path=self.config_dir / "providers.yaml"
        )
        
        # Initialize MCP Tool Registry
        self.tool_registry = MCPToolRegistry()
        
        # Initialize MCP server
        self.mcp_server = MCPServer(
            config_path=self.config_dir / "mcp_tools.yaml"
        )
        
        # Register tools with MCP server
        self.tool_registry.register_with_mcp_server(self.mcp_server)
        
        # Initialize LangGraph agent
        self.agent = LangGraphAgent(
            model_factory=self.model_factory,
            tool_registry=self.tool_registry,
            provider=self.provider,
            model=self.model,
            config_path=self.config_dir / "agent_config.yaml"
        )
        
        # Legacy references (for backwards compatibility)
        self.helper_agent = None
        self.mcp_tool_wrappers = None
        self.langchain_tools = None
        
        self._initialized = False
        
        logger.info("Helper Agent Integration initialized with unified architecture")
    
    async def initialize(self):
        """Initialize all async components."""
        if self._initialized:
            return
        
        # Initialize LiteLLM client
        await self.client.initialize()
        
        # Initialize Model Factory
        await self.model_factory.initialize()
        
        # Initialize LangGraph agent
        await self.agent.initialize()
        
        self._initialized = True
        logger.info("Helper Agent Integration fully initialized")
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.client.cleanup()
        await self.model_factory.cleanup()
        await self.agent.cleanup()
        self._initialized = False
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    # ===== General Chat Methods =====
    
    async def chat(
        self,
        messages: Sequence[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Chat completion.
        
        Args:
            messages: Chat messages
            provider: Provider name (auto-selected if None)
            model: Model name
            **kwargs: Additional parameters
            
        Returns:
            Response with content, provider, usage, cost
        """
        return await self.client.chat(
            messages,
            provider=provider,
            model=model,
            **kwargs
        )
    
    async def stream_chat(
        self,
        messages: Sequence[Dict[str, str]],
        provider: Optional[str] = None,
        model: Optional[str] = None,
        format_sse: bool = False,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion.
        
        Args:
            messages: Chat messages
            provider: Provider name
            model: Model name
            format_sse: Format as SSE events
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        stream = self.client.stream_chat(
            messages,
            provider=provider,
            model=model,
            **kwargs
        )
        
        if format_sse:
            async for chunk in stream_llm_response(stream, format_sse=True):
                yield chunk
        else:
            async for chunk in stream:
                yield chunk
    
    async def quick_prompt(
        self,
        prompt: str,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Quick single-prompt completion.
        
        Args:
            prompt: User prompt
            provider: Provider name
            model: Model name
            **kwargs: Additional parameters
            
        Returns:
            Response text
        """
        return await self.client.completion(
            prompt,
            provider=provider,
            model=model,
            **kwargs
        )
    
    # ===== Specialized Capabilities =====
    
    async def summarize_for_tts(
        self,
        text: str,
        max_words: int = 60,
        style: str = "concise",
        provider: Optional[str] = None
    ) -> str:
        """
        Summarize text optimized for TTS output.
        
        Args:
            text: Text to summarize
            max_words: Maximum words in summary
            style: Summary style
            provider: Provider to use
            
        Returns:
            Summary text
        """
        prompt = f"""Summarize the following text in {max_words} words or less, optimized for text-to-speech. Use clear, simple language.

Style: {style}

Text: {text}

Summary:"""
        
        return await self.quick_prompt(
            prompt,
            provider=provider,
            max_tokens=max(100, max_words * 2),
            temperature=0.3
        )
    
    async def analyze_content(
        self,
        content: str,
        analysis_type: str = "comprehensive",
        provider: Optional[str] = None
    ) -> str:
        """
        Analyze content.
        
        Args:
            content: Content to analyze
            analysis_type: Type of analysis
            provider: Provider to use
            
        Returns:
            Analysis result
        """
        prompt = f"""Analyze the following content ({analysis_type} analysis):

{content}

Provide a clear analysis:"""
        
        return await self.quick_prompt(
            prompt,
            provider=provider,
            max_tokens=800,
            temperature=0.5
        )
    
    async def plan_task(
        self,
        task: str,
        max_steps: int = 10,
        provider: Optional[str] = None
    ) -> str:
        """
        Plan a task into steps.
        
        Args:
            task: Task to plan
            max_steps: Maximum steps
            provider: Provider to use
            
        Returns:
            Task plan
        """
        prompt = f"""Break down the following task into {max_steps} or fewer clear, actionable steps:

Task: {task}

Steps:"""
        
        return await self.quick_prompt(
            prompt,
            provider=provider,
            max_tokens=600,
            temperature=0.7
        )
    
    # ===== Agentic Methods =====
    
    async def agentic_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute agentic query using LangGraph ReAct agent.
        
        Args:
            query: Query to execute
            thread_id: Thread ID for conversation tracking
            **kwargs: Additional parameters
            
        Returns:
            Agent response with reasoning and tool usage
        """
        if not self.agent:
            return {
                "success": False,
                "error": "Agent not initialized",
                "response": ""
            }
        
        result = await self.agent.invoke(query, thread_id=thread_id, **kwargs)
        
        return {
            "success": "error" not in result,
            "response": result.get("response", ""),
            "messages": result.get("messages", []),
            "thread_id": result.get("thread_id")
        }
    
    async def stream_agentic_query(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream agentic query execution using LangGraph ReAct agent.
        
        Args:
            query: Query to execute
            thread_id: Thread ID for conversation tracking
            **kwargs: Additional parameters
            
        Yields:
            Response chunks
        """
        if not self.agent:
            yield "Error: Agent not initialized"
            return
        
        async for chunk in self.agent.stream(query, thread_id=thread_id, **kwargs):
            yield chunk
    
    # ===== MCP Methods =====
    
    async def call_mcp_tool(
        self,
        tool_name: str,
        args: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call MCP tool.
        
        Args:
            tool_name: Tool name
            args: Tool arguments
            session_id: Session ID
            
        Returns:
            Tool result
        """
        return await self.mcp_server.call_tool(
            tool_name=tool_name,
            args=args,
            session_id=session_id
        )
    
    def list_mcp_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available MCP tools.
        
        Args:
            category: Filter by category
            
        Returns:
            List of tool information
        """
        return self.mcp_server.list_tools(category=category)
    
    def get_mcp_tools_for_provider(self, provider: str = "openai") -> List[Dict[str, Any]]:
        """
        Get MCP tools formatted for provider.
        
        Args:
            provider: Provider name
            
        Returns:
            Tool definitions
        """
        return self.mcp_server.get_tools_for_provider(provider)
    
    # ===== Session Management =====
    
    def session(
        self,
        system_prompt: Optional[str] = None
    ) -> HelperAgentSession:
        """
        Create conversational session.
        
        Args:
            system_prompt: System prompt
            
        Returns:
            Session instance
        """
        return HelperAgentSession(
            client=self,
            system_prompt=system_prompt
        )
    
    # ===== Metrics & Info =====
    
    def get_metrics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage metrics.
        
        Args:
            provider: Specific provider or None for all
            
        Returns:
            Metrics dictionary
        """
        return self.client.get_metrics(provider)
    
    def list_providers(self) -> List[str]:
        """List available providers."""
        return self.client.list_providers()
    
    def list_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """List available models."""
        return self.client.list_models(provider)
    
    def get_mcp_metrics(self) -> Dict[str, Any]:
        """Get MCP tool metrics."""
        return self.mcp_server.get_tool_metrics()


__all__ = ["HelperAgentIntegration", "HelperAgentSession"]

