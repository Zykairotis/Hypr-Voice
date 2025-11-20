"""
Basic Usage Examples for Helper Agent Integration

This demonstrates the core functionality of the multi-provider helper agent.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from integration import HelperAgentIntegration


async def example_basic_chat():
    """Example: Basic chat completion."""
    print("\n=== Basic Chat Example ===")
    
    async with HelperAgentIntegration() as agent:
        # Simple chat
        messages = [
            {"role": "user", "content": "What is the capital of France?"}
        ]
        
        response = await agent.chat(messages)
        print(f"Response: {response['content']}")
        print(f"Provider: {response['provider']}")
        print(f"Cost: ${response['cost']:.6f}")


async def example_quick_prompt():
    """Example: Quick prompt completion."""
    print("\n=== Quick Prompt Example ===")
    
    async with HelperAgentIntegration() as agent:
        response = await agent.quick_prompt(
            "Explain quantum computing in one sentence.",
            max_tokens=100
        )
        print(f"Response: {response}")


async def example_streaming():
    """Example: Streaming chat."""
    print("\n=== Streaming Example ===")
    
    async with HelperAgentIntegration() as agent:
        messages = [
            {"role": "user", "content": "Tell me a short story about AI."}
        ]
        
        print("Streaming response: ", end="", flush=True)
        async for chunk in agent.stream_chat(messages, max_tokens=200):
            print(chunk, end="", flush=True)
        print()


async def example_summarization():
    """Example: Text summarization for TTS."""
    print("\n=== Summarization Example ===")
    
    long_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, 
    as opposed to the natural intelligence displayed by animals including humans. 
    AI research has been defined as the field of study of intelligent agents, 
    which refers to any system that perceives its environment and takes actions 
    that maximize its chance of achieving its goals. The term "artificial intelligence" 
    had previously been used to describe machines that mimic and display "human" 
    cognitive skills that are associated with the human mind, such as "learning" 
    and "problem-solving". This definition has since been rejected by major AI 
    researchers who now describe AI in terms of rationality and acting rationally, 
    which does not limit how intelligence can be articulated.
    """
    
    async with HelperAgentIntegration() as agent:
        summary = await agent.summarize_for_tts(
            long_text,
            max_words=30,
            style="concise"
        )
        print(f"Summary: {summary}")


async def example_task_planning():
    """Example: Task planning."""
    print("\n=== Task Planning Example ===")
    
    async with HelperAgentIntegration() as agent:
        plan = await agent.plan_task(
            "Build a simple web application with user authentication",
            max_steps=5
        )
        print(f"Task Plan:\n{plan}")


async def example_session():
    """Example: Conversational session."""
    print("\n=== Session Example ===")
    
    async with HelperAgentIntegration() as agent:
        session = agent.session(
            system_prompt="You are a helpful coding assistant."
        )
        
        response1 = await session.send("What is Python?")
        print(f"Response 1: {response1[:100]}...")
        
        response2 = await session.send("Give me a hello world example.")
        print(f"Response 2: {response2[:100]}...")


async def example_provider_comparison():
    """Example: Compare different providers."""
    print("\n=== Provider Comparison Example ===")
    
    async with HelperAgentIntegration() as agent:
        prompt = "What is 2+2?"
        
        # List available providers
        providers = agent.list_providers()
        print(f"Available providers: {providers}")
        
        # Try first available provider
        if providers:
            response = await agent.quick_prompt(
                prompt,
                provider=providers[0]
            )
            print(f"\n{providers[0]}: {response}")


async def example_mcp_tools():
    """Example: MCP tool usage."""
    print("\n=== MCP Tools Example ===")
    
    async with HelperAgentIntegration() as agent:
        # List available tools
        tools = agent.list_mcp_tools()
        print(f"Available MCP tools: {len(tools)}")
        for tool in tools[:3]:
            print(f"  - {tool['name']}: {tool['description'][:60]}...")
        
        # Note: Actual tool calling requires agent to be fully initialized
        # with helper_agent instance


async def example_metrics():
    """Example: View usage metrics."""
    print("\n=== Metrics Example ===")
    
    async with HelperAgentIntegration() as agent:
        # Do some requests first
        await agent.quick_prompt("Hello!")
        
        # Get metrics
        metrics = agent.get_metrics()
        print(f"Total cost: ${metrics['total_cost']:.6f}")
        print(f"Providers used: {list(metrics['providers'].keys())}")


def main():
    """Run all examples."""
    print("Helper Agent Integration Examples")
    print("=" * 50)
    
    # Note: Some examples require API keys to be set in environment
    examples = [
        ("Basic Chat", example_basic_chat),
        ("Quick Prompt", example_quick_prompt),
        ("Streaming", example_streaming),
        ("Summarization", example_summarization),
        ("Task Planning", example_task_planning),
        ("Session", example_session),
        ("Provider Comparison", example_provider_comparison),
        ("MCP Tools", example_mcp_tools),
        ("Metrics", example_metrics),
    ]
    
    print("\nAvailable Examples:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"{i}. {name}")
    
    try:
        choice = input("\nSelect example (1-9, or 'all'): ").strip().lower()
        
        if choice == 'all':
            for name, example_func in examples:
                try:
                    asyncio.run(example_func())
                except Exception as e:
                    print(f"Error in {name}: {e}")
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, example_func = examples[int(choice) - 1]
            asyncio.run(example_func())
        else:
            print("Invalid choice")
    except KeyboardInterrupt:
        print("\n\nExamples interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        print("\nNote: Most examples require API keys to be set in environment variables.")
        print("Example: export OPENAI_API_KEY='your-key-here'")


if __name__ == "__main__":
    main()

