"""
LangGraph Agent with ReAct Pattern

This module implements a LangGraph-based agent using the official ReAct (Reasoning + Acting)
pattern via create_react_agent, integrated with LiteLLM and MCP tool registry.
"""

import logging
from typing import Any, Dict, List, Optional, Sequence, TypedDict, Annotated
from pathlib import Path
import yaml

try:
    from langgraph.graph import StateGraph, END
    from langgraph.prebuilt import create_react_agent, ToolExecutor, ToolInvocation
    from langgraph.checkpoint.memory import MemorySaver
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
    from langchain_core.tools import BaseTool
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logging.warning("LangGraph not available. Install with: pip install langgraph")

from .model_factory import ModelFactory
from .tools.mcp_registry import MCPToolRegistry, ToolCategory

logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the agent graph (compatible with create_react_agent)."""
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]


class LangGraphAgent:
    """
    LangGraph agent using official create_react_agent with LiteLLM backend.
    
    Features:
    - Official LangGraph ReAct pattern via create_react_agent
    - Multi-provider LLM support via ModelFactory
    - Unified tool registry (MCP + LangChain)
    - State checkpointing and multi-turn conversations
    - Streaming support
    """
    
    def __init__(
        self,
        model_factory: Optional[ModelFactory] = None,
        tool_registry: Optional[MCPToolRegistry] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize LangGraph agent with official ReAct pattern.
        
        Args:
            model_factory: ModelFactory instance for creating LangChain models
            tool_registry: MCPToolRegistry instance for tool access
            provider: LLM provider name (auto-selected if None)
            model: Model name (uses provider default if None)
            config_path: Path to agent_config.yaml
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is required but not installed")
        
        # Initialize factories
        self.model_factory = model_factory or ModelFactory()
        self.tool_registry = tool_registry or MCPToolRegistry()
        
        # Provider settings
        self.provider = provider
        self.model = model
        
        # Load configuration
        self.config_path = config_path or Path(__file__).parent / "config" / "agent_config.yaml"
        self.config = self._load_config()
        
        # Agent settings
        self.agent_config = self.config.get("agent", {})
        self.workflow_config = self.config.get("workflow", {})
        self.max_iterations = self.workflow_config.get("react_pattern", {}).get("max_iterations", 5)
        
        # Create LangChain chat model
        self.chat_model = self._create_chat_model()
        
        # Get tools from registry
        self.tools = self._get_tools()
        
        # Initialize checkpointer
        self.checkpointer = MemorySaver()
        
        # Create ReAct agent using official prebuilt
        self.agent = create_react_agent(
            model=self.chat_model,
            tools=self.tools,
            checkpointer=self.checkpointer,
            state_modifier=self._get_system_prompt()
        )
        
        logger.info(f"LangGraph ReAct agent initialized with {len(self.tools)} tools")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f) or {}
            else:
                logger.warning(f"Agent config not found: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            return {}
    
    def _create_chat_model(self):
        """Create LangChain chat model via model factory."""
        temperature = self.agent_config.get("temperature", 0.7)
        max_tokens = self.agent_config.get("max_tokens", 2048)
        
        return self.model_factory.create_chat_model(
            provider=self.provider,
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens,
            streaming=False
        )
    
    def _get_tools(self) -> List[BaseTool]:
        """Get tools from registry."""
        tools_config = self.workflow_config.get("tools", {})
        enabled_categories = tools_config.get("enabled_categories", ["all"])
        
        if "all" in enabled_categories:
            return self.tool_registry.get_langchain_tools()
        
        # Get tools by category
        tools = []
        for category_name in enabled_categories:
            try:
                category = ToolCategory(category_name)
                tools.extend(self.tool_registry.get_langchain_tools(category=category))
            except ValueError:
                logger.warning(f"Unknown tool category: {category_name}")
        
        return tools
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the agent."""
        default_prompt = (
            "You are a helpful AI assistant with access to various tools. "
            "When given a task, think step by step about which tools to use and in what order. "
            "Always explain your reasoning before using tools. "
            "After using tools, synthesize the results into a clear, concise response."
        )
        
        return self.agent_config.get("system_prompt", default_prompt)
    
    async def initialize(self):
        """Initialize async components."""
        await self.model_factory.initialize()
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.model_factory.cleanup()
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    async def invoke(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke the agent with a query.
        
        Args:
            query: User query
            thread_id: Thread ID for conversation tracking
            **kwargs: Additional invoke parameters
            
        Returns:
            Agent response dictionary
        """
        # Build messages
        messages = [HumanMessage(content=query)]
        
        # Prepare config
        config = {"configurable": {}} if not thread_id else {"configurable": {"thread_id": thread_id}}
        config.update(kwargs.get("config", {}))
        
        try:
            # Invoke the ReAct agent
            result = await self.agent.ainvoke(
                {"messages": messages},
                config=config
            )
            
            # Extract final response
            final_messages = result.get("messages", [])
            if final_messages:
                final_message = final_messages[-1]
                content = final_message.content if hasattr(final_message, "content") else str(final_message)
            else:
                content = "No response generated"
            
            return {
                "response": content,
                "messages": final_messages,
                "thread_id": thread_id
            }
            
        except Exception as e:
            logger.error(f"Agent invocation error: {e}")
            return {
                "response": f"Error: {str(e)}",
                "error": str(e),
                "thread_id": thread_id
            }
    
    async def stream(
        self,
        query: str,
        thread_id: Optional[str] = None,
        **kwargs
    ):
        """
        Stream agent responses.
        
        Args:
            query: User query
            thread_id: Thread ID for conversation tracking
            **kwargs: Additional stream parameters
            
        Yields:
            Response chunks
        """
        # Build messages
        messages = [HumanMessage(content=query)]
        
        # Prepare config
        config = {"configurable": {}} if not thread_id else {"configurable": {"thread_id": thread_id}}
        config.update(kwargs.get("config", {}))
        
        try:
            # Stream from the ReAct agent
            async for chunk in self.agent.astream(
                {"messages": messages},
                config=config
            ):
                # Extract content from chunk
                if isinstance(chunk, dict):
                    messages = chunk.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, "content"):
                            yield last_message.content
                        else:
                            yield str(last_message)
                else:
                    yield str(chunk)
                    
        except Exception as e:
            logger.error(f"Agent streaming error: {e}")
            yield f"Error: {str(e)}"
    
    def get_conversation_history(self, thread_id: str) -> List[BaseMessage]:
        """
        Get conversation history for a thread.
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List of messages
        """
        try:
            checkpoint = self.checkpointer.get({"configurable": {"thread_id": thread_id}})
            if checkpoint and "messages" in checkpoint.get("values", {}):
                return checkpoint["values"]["messages"]
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
        
        return []
    
    def get_available_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self.tools]
    
    def get_provider_metrics(self) -> Dict[str, Any]:
        """Get metrics from the model factory."""
        return self.model_factory.get_provider_metrics()


__all__ = ["LangGraphAgent", "AgentState"]
