"""
Unified Architecture Example

Demonstrates the unified helper-agent architecture with:
- ModelFactory for multi-provider LLM access
- MCPToolRegistry for unified tool management
- LangGraph ReAct agent with official create_react_agent
- Streaming support
"""

import asyncio
import logging
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_model_factory():
    """Example: Using ModelFactory to create LangChain chat models."""
    from model_factory import ModelFactory
    
    logger.info("=== Model Factory Example ===")
    
    # Create model factory
    factory = ModelFactory()
    
    # Initialize
    await factory.initialize()
    
    try:
        # List available providers and models
        providers = factory.list_available_providers()
        logger.info(f"Available providers: {providers}")
        
        models = factory.list_available_models()
        logger.info(f"Available models: {models}")
        
        # Create a chat model (auto-selects best provider)
        chat_model = factory.create_chat_model(
            temperature=0.7,
            max_tokens=100
        )
        
        logger.info(f"Created chat model: {chat_model}")
        
        # Use the model directly if needed
        from langchain_core.messages import HumanMessage
        response = await chat_model.ainvoke([HumanMessage(content="Hello! Say hi in one sentence.")])
        logger.info(f"Model response: {response.content}")
        
        # Get metrics
        metrics = factory.get_provider_metrics()
        logger.info(f"Provider metrics: {metrics}")
        
    finally:
        await factory.cleanup()


async def example_tool_registry():
    """Example: Using MCPToolRegistry for unified tool management."""
    from tools.mcp_registry import MCPToolRegistry, ToolCategory
    
    logger.info("=== Tool Registry Example ===")
    
    # Create tool registry
    registry = MCPToolRegistry()
    
    # List all tools
    all_tools = registry.list_tools()
    logger.info(f"All tools: {all_tools}")
    
    # Get tools by category
    text_tools = registry.list_tools(category=ToolCategory.TEXT_PROCESSING)
    logger.info(f"Text processing tools: {text_tools}")
    
    # Get LangChain tools
    langchain_tools = registry.get_langchain_tools(category=ToolCategory.TEXT_PROCESSING)
    logger.info(f"LangChain tools count: {len(langchain_tools)}")
    
    # Tool details
    for tool in langchain_tools:
        logger.info(f"Tool: {tool.name} - {tool.description}")


async def example_unified_agent():
    """Example: Using unified LangGraph ReAct agent."""
    from agent_graph import LangGraphAgent
    from model_factory import ModelFactory
    from tools.mcp_registry import MCPToolRegistry
    
    logger.info("=== Unified Agent Example ===")
    
    # Create components
    model_factory = ModelFactory()
    tool_registry = MCPToolRegistry()
    
    # Create agent
    agent = LangGraphAgent(
        model_factory=model_factory,
        tool_registry=tool_registry
    )
    
    # Initialize
    await agent.initialize()
    
    try:
        # Simple query without tools
        result = await agent.invoke("What is 2 + 2?")
        logger.info(f"Simple query result: {result['response']}")
        
        # Query that uses tools
        result = await agent.invoke("Calculate the square root of 144")
        logger.info(f"Tool query result: {result['response']}")
        
        # Multi-turn conversation with thread ID
        thread_id = "user-123"
        
        result1 = await agent.invoke("My name is Alice", thread_id=thread_id)
        logger.info(f"Turn 1: {result1['response']}")
        
        result2 = await agent.invoke("What's my name?", thread_id=thread_id)
        logger.info(f"Turn 2: {result2['response']}")
        
    finally:
        await agent.cleanup()


async def example_streaming_agent():
    """Example: Streaming with unified agent."""
    from agent_graph import LangGraphAgent
    from model_factory import ModelFactory
    from tools.mcp_registry import MCPToolRegistry
    
    logger.info("=== Streaming Agent Example ===")
    
    # Create components
    model_factory = ModelFactory()
    tool_registry = MCPToolRegistry()
    agent = LangGraphAgent(model_factory=model_factory, tool_registry=tool_registry)
    
    await agent.initialize()
    
    try:
        logger.info("Streaming response:")
        async for chunk in agent.stream("Tell me a joke about programming"):
            print(chunk, end="", flush=True)
        print()  # New line
        
    finally:
        await agent.cleanup()


async def example_integration_api():
    """Example: Using high-level HelperAgentIntegration API."""
    from integration import HelperAgentIntegration
    
    logger.info("=== Integration API Example ===")
    
    # Create integration
    integration = HelperAgentIntegration()
    
    # Initialize
    await integration.initialize()
    
    try:
        # Direct chat (without agent)
        response = await integration.chat([
            {"role": "user", "content": "Hello! Say hi."}
        ])
        logger.info(f"Direct chat: {response['content']}")
        
        # Agentic query (with ReAct workflow)
        result = await integration.agentic_query(
            "Summarize the benefits of Python and calculate how many letters are in 'Python'"
        )
        logger.info(f"Agentic query: {result['response']}")
        
        # Streaming agentic query
        logger.info("Streaming agentic query:")
        async for chunk in integration.stream_agentic_query("What is machine learning?"):
            print(chunk, end="", flush=True)
        print()  # New line
        
        # Call MCP tool directly
        tool_result = await integration.call_mcp_tool(
            tool_name="calculator",
            args={"expression": "10 * 5", "precision": 2}
        )
        logger.info(f"MCP tool result: {tool_result}")
        
    finally:
        await integration.cleanup()


async def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Unified Helper-Agent Architecture Examples")
    print("="*60 + "\n")
    
    try:
        # Run examples
        await example_model_factory()
        print()
        
        await example_tool_registry()
        print()
        
        await example_unified_agent()
        print()
        
        await example_streaming_agent()
        print()
        
        await example_integration_api()
        print()
        
    except Exception as e:
        logger.error(f"Example error: {e}", exc_info=True)
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

