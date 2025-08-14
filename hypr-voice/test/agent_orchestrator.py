#!/usr/bin/env python3
"""
Agent Orchestrator for Hypr-Voice
Manages multi-provider LLM orchestration with MCP tools integration
"""

import os
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from loguru import logger
from dotenv import load_dotenv

# LLM Provider imports
from langchain_xai import ChatXAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_ollama import OllamaLLM
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import Tool
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate

load_dotenv()

class ProviderStatus(Enum):
    """Status of LLM providers"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"

@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    name: str
    priority: int  # Lower number = higher priority
    status: ProviderStatus = ProviderStatus.AVAILABLE
    model: str = ""
    temperature: float = 0.3
    max_tokens: int = 2048
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 30
    retry_count: int = 3
    fallback_to: Optional[str] = None

class MCPToolExecutor:
    """Executor for MCP tools"""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self.tool_servers: Dict[str, Any] = {}
        
    async def register_tool(self, tool_name: str, tool_func: Callable, description: str):
        """Register an MCP tool"""
        self.tools[tool_name] = Tool(
            name=tool_name,
            func=tool_func,
            description=description
        )
        logger.info(f"Registered MCP tool: {tool_name}")
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """Execute an MCP tool"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools[tool_name]
        try:
            result = await tool.arun(**kwargs) if asyncio.iscoroutinefunction(tool.func) else tool.run(**kwargs)
            logger.info(f"Executed tool {tool_name}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            raise

class AgentOrchestrator:
    """Main orchestrator for multi-provider LLM agents with MCP tools"""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("config/agent_config.yaml")
        self.providers: Dict[str, Any] = {}
        self.provider_configs: Dict[str, ProviderConfig] = {}
        self.mcp_executor = MCPToolExecutor()
        self.current_provider: Optional[str] = None
        self.conversation_history: List[Dict[str, str]] = []
        
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize all configured LLM providers"""
        # xAI (Primary)
        if os.getenv("XAI_API_KEY"):
            self._setup_xai()
        
        # OpenAI (Fallback 1)
        if os.getenv("OPENAI_API_KEY"):
            self._setup_openai()
        
        # Anthropic (Fallback 2)
        if os.getenv("ANTHROPIC_API_KEY"):
            self._setup_anthropic()
        
        # Ollama (Local fallback)
        self._setup_ollama()
        
        logger.info(f"Initialized {len(self.providers)} LLM providers")
    
    def _setup_xai(self):
        """Setup xAI/Grok provider"""
        try:
            config = ProviderConfig(
                name="xai",
                priority=1,
                model=os.getenv("XAI_MODEL", "grok-beta"),
                api_key=os.getenv("XAI_API_KEY"),
                base_url=os.getenv("XAI_API_BASE", "https://api.x.ai/v1"),
                temperature=float(os.getenv("XAI_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("XAI_MAX_TOKENS", "2048"))
            )
            
            self.providers["xai"] = ChatXAI(
                model=config.model,
                xai_api_key=config.api_key,
                xai_api_base=config.base_url,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            self.provider_configs["xai"] = config
            logger.info(f"xAI provider initialized with model: {config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize xAI provider: {e}")
    
    def _setup_openai(self):
        """Setup OpenAI provider"""
        try:
            config = ProviderConfig(
                name="openai",
                priority=2,
                model=os.getenv("OPENAI_MODEL", "gpt-4-turbo"),
                api_key=os.getenv("OPENAI_API_KEY"),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2048"))
            )
            
            self.providers["openai"] = ChatOpenAI(
                model=config.model,
                openai_api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            self.provider_configs["openai"] = config
            logger.info(f"OpenAI provider initialized with model: {config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
    
    def _setup_anthropic(self):
        """Setup Anthropic provider"""
        try:
            config = ProviderConfig(
                name="anthropic",
                priority=3,
                model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "2048"))
            )
            
            self.providers["anthropic"] = ChatAnthropic(
                model=config.model,
                anthropic_api_key=config.api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            )
            
            self.provider_configs["anthropic"] = config
            logger.info(f"Anthropic provider initialized with model: {config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
    
    def _setup_ollama(self):
        """Setup Ollama local provider"""
        try:
            config = ProviderConfig(
                name="ollama",
                priority=4,
                model=os.getenv("OLLAMA_MODEL", "llama3.1"),
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.3")),
                max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "2048"))
            )
            
            self.providers["ollama"] = OllamaLLM(
                model=config.model,
                base_url=config.base_url,
                temperature=config.temperature,
                num_predict=config.max_tokens
            )
            
            self.provider_configs["ollama"] = config
            logger.info(f"Ollama provider initialized with model: {config.model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        use_tools: bool = False,
        **kwargs
    ) -> str:
        """
        Generate response from LLM with automatic fallback
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            provider: Specific provider to use (optional)
            use_tools: Whether to use MCP tools
            **kwargs: Additional parameters
        
        Returns:
            Generated response text
        """
        # Get available providers sorted by priority
        available_providers = self._get_available_providers(provider)
        
        if not available_providers:
            logger.error("No LLM providers available")
            return "Error: No LLM providers available. Please check configuration."
        
        # Try each provider in order
        for provider_name in available_providers:
            try:
                logger.info(f"Attempting generation with provider: {provider_name}")
                
                llm = self.providers[provider_name]
                messages: List[BaseMessage] = []

                # Build message sequence: system -> history -> current prompt
                if system_prompt:
                    messages.append(SystemMessage(content=system_prompt))

                if kwargs.get("use_history", False) and self.conversation_history:
                    history_limit = int(os.getenv("AGENT_HISTORY_LIMIT", "10"))
                    for msg in self.conversation_history[-history_limit:]:
                        if msg["role"] == "user":
                            messages.append(HumanMessage(content=msg["content"]))
                        else:
                            messages.append(AIMessage(content=msg["content"]))

                messages.append(HumanMessage(content=prompt))

                # Provider config for timeouts/retries
                config = self.provider_configs.get(provider_name)
                retries = max(1, getattr(config, "retry_count", 1)) if config else 1
                timeout_s = getattr(config, "timeout", 0) if config else 0

                last_err: Optional[Exception] = None
                for attempt in range(retries):
                    try:
                        # Generate response
                        if use_tools and self.mcp_executor.tools:
                            response = await self._generate_with_tools(
                                llm, messages, input_text=prompt, **kwargs
                            )
                        else:
                            coro = llm.ainvoke(messages)
                            if timeout_s and timeout_s > 0:
                                result = await asyncio.wait_for(coro, timeout=timeout_s)
                            else:
                                result = await coro
                            response = result.content if hasattr(result, 'content') else str(result)
                        last_err = None
                        break
                    except Exception as e:
                        last_err = e
                        if attempt < retries - 1:
                            backoff = 2 ** attempt
                            logger.warning(f"Attempt {attempt+1}/{retries} failed on {provider_name}: {e}. Retrying in {backoff}s...")
                            await asyncio.sleep(backoff)
                        else:
                            raise

                # Update conversation history
                self.conversation_history.append({"role": "user", "content": prompt})
                self.conversation_history.append({"role": "assistant", "content": response})
                # Trim history
                max_history = int(os.getenv("AGENT_HISTORY_LIMIT", "20"))
                if max_history > 0 and len(self.conversation_history) > max_history:
                    self.conversation_history = self.conversation_history[-max_history:]
                
                self.current_provider = provider_name
                logger.info(f"Successfully generated response with {provider_name}")
                
                return response
                
            except Exception as e:
                logger.error(f"Provider {provider_name} failed: {e}")
                self._mark_provider_unavailable(provider_name)
                continue
        
        return "Error: All LLM providers failed. Please check logs for details."
    
    async def _generate_with_tools(
        self,
        llm: Any,
        messages: List[Any],
        **kwargs
    ) -> str:
        """Generate response using LLM with MCP tools"""
        # Create agent with tools
        tools = list(self.mcp_executor.tools.values())
        
        # Create ReAct agent
        prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template="""Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        agent = create_react_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5
        )
        
        # Execute agent
        input_text = kwargs.get("input_text")
        query = input_text if input_text is not None else (messages[-1].content if messages else "")
        result = await agent_executor.ainvoke({"input": query})
        return result.get("output", "")
    
    def _get_available_providers(self, preferred: Optional[str] = None) -> List[str]:
        """Get list of available providers sorted by priority"""
        available = []
        
        if preferred and preferred in self.providers:
            if self.provider_configs[preferred].status == ProviderStatus.AVAILABLE:
                available.append(preferred)
        
        # Add other providers by priority
        sorted_providers = sorted(
            self.provider_configs.items(),
            key=lambda x: x[1].priority
        )
        
        for name, config in sorted_providers:
            if name != preferred and config.status == ProviderStatus.AVAILABLE:
                available.append(name)
        
        return available
    
    def _mark_provider_unavailable(self, provider_name: str):
        """Mark a provider as temporarily unavailable"""
        if provider_name in self.provider_configs:
            self.provider_configs[provider_name].status = ProviderStatus.ERROR
            
            # Schedule recovery check
            asyncio.create_task(self._recover_provider(provider_name))
    
    async def _recover_provider(self, provider_name: str):
        """Attempt to recover a failed provider after delay"""
        await asyncio.sleep(60)  # Wait 1 minute
        
        if provider_name in self.provider_configs:
            self.provider_configs[provider_name].status = ProviderStatus.AVAILABLE
            logger.info(f"Provider {provider_name} marked as available again")
    
    async def register_mcp_tool(self, tool_name: str, tool_func: Callable, description: str):
        """Register an MCP tool with the orchestrator"""
        await self.mcp_executor.register_tool(tool_name, tool_func, description)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of all providers"""
        return {
            "current_provider": self.current_provider,
            "providers": {
                name: {
                    "status": config.status.value,
                    "model": config.model,
                    "priority": config.priority
                }
                for name, config in self.provider_configs.items()
            },
            "mcp_tools": list(self.mcp_executor.tools.keys()),
            "history_length": len(self.conversation_history)
        }
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared")


# Example MCP tool functions
async def search_documentation(query: str) -> str:
    """Search technical documentation"""
    # This would integrate with actual documentation search
    return f"Documentation search results for: {query}"

async def execute_code(code: str, language: str = "python") -> str:
    """Execute code snippet safely"""
    # This would integrate with safe code execution environment
    return f"Code execution result for {language}: [simulated]"

async def analyze_context(text: str) -> Dict[str, Any]:
    """Analyze text context and extract entities"""
    # This would integrate with NLP analysis
    return {
        "entities": [],
        "sentiment": "neutral",
        "topics": []
    }


# Test function
async def test_orchestrator():
    """Test the agent orchestrator"""
    orchestrator = AgentOrchestrator()
    
    # Register MCP tools
    await orchestrator.register_mcp_tool(
        "search_docs",
        search_documentation,
        "Search technical documentation for relevant information"
    )
    
    await orchestrator.register_mcp_tool(
        "execute_code",
        execute_code,
        "Execute code snippets safely"
    )
    
    await orchestrator.register_mcp_tool(
        "analyze_context",
        analyze_context,
        "Analyze text context and extract entities"
    )
    
    # Test generation
    response = await orchestrator.generate(
        "What is a REST API?",
        system_prompt="You are a helpful technical assistant.",
        use_tools=False
    )
    
    print(f"Response: {response}")
    print(f"Status: {orchestrator.get_status()}")


if __name__ == "__main__":
    asyncio.run(test_orchestrator())
