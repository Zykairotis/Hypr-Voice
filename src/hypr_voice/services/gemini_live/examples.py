#!/usr/bin/env python3
"""Example usage of Gemini Live integration."""

import asyncio
from pathlib import Path
from hypr_voice.services.gemini_live import (
    GeminiClient,
    GeminiConfig,
    GeminiIntegration,
)


async def example_basic_text():
    """Example 1: Basic text generation."""
    print("=" * 60)
    print("Example 1: Basic Text Generation")
    print("=" * 60)
    
    config = GeminiConfig.from_env()
    client = GeminiClient(config)
    
    response = await client.generate_content(
        "Explain quantum computing in 3 sentences.",
        temperature=0.7,
        max_output_tokens=150
    )
    
    print(f"\nResponse: {response['content']}")
    print(f"\nUsage: {response['usage']}")


async def example_streaming():
    """Example 2: Streaming responses with token tracking."""
    print("\n" + "=" * 60)
    print("Example 2: Streaming with Token Tracking")
    print("=" * 60)
    
    config = GeminiConfig.from_env()
    client = GeminiClient(config)
    
    print("\nStreaming response:")
    print("-" * 60)
    
    import time
    start_time = time.time()
    token_count = 0
    
    async for chunk in client.stream_content(
        "Write a haiku about artificial intelligence",
        temperature=0.8,
        max_output_tokens=100
    ):
        print(chunk["content"], end="", flush=True)
        if chunk["is_final"]:
            token_count = chunk["usage"].get("completion_tokens", 0)
    
    elapsed = time.time() - start_time
    tokens_per_sec = token_count / elapsed if elapsed > 0 else 0
    
    print("\n" + "-" * 60)
    print(f"Tokens: {token_count} | Speed: {tokens_per_sec:.1f} tok/s | Time: {elapsed:.2f}s")


async def example_multimodal():
    """Example 3: Multimodal input (text + image)."""
    print("\n" + "=" * 60)
    print("Example 3: Multimodal Input (Text + Image)")
    print("=" * 60)
    
    # This example requires an image file
    # You can replace with your own image path
    test_image = Path("test_image.jpg")
    
    if not test_image.exists():
        print("\nℹ️  Skipping multimodal example (no test image found)")
        print("   Create test_image.jpg to run this example")
        return
    
    config = GeminiConfig.from_env()
    client = GeminiClient(config)
    
    response = await client.generate_content(
        ["Describe this image in detail:", test_image],
        temperature=0.5
    )
    
    print(f"\nImage Analysis: {response['content']}")
    print(f"\nUsage: {response['usage']}")


async def example_integration_helpers():
    """Example 4: Using integration helpers."""
    print("\n" + "=" * 60)
    print("Example 4: Integration Helpers")
    print("=" * 60)
    
    async with GeminiIntegration() as gemini:
        # Quick summarization
        print("\n1. Summarization:")
        print("-" * 40)
        text = """
        Artificial Intelligence (AI) has transformed numerous industries, 
        from healthcare to finance. Machine learning algorithms can now 
        diagnose diseases, predict stock market trends, and even create art. 
        However, ethical considerations around AI deployment remain crucial, 
        including concerns about bias, privacy, and job displacement.
        """
        
        summary = await gemini.summarize(
            text,
            style="bullet_points",
            max_words=50
        )
        print(summary)
        
        # Classification
        print("\n2. Classification:")
        print("-" * 40)
        category = await gemini.classify(
            "This product exceeded my expectations! Highly recommended.",
            categories=["positive", "negative", "neutral"]
        )
        print(f"Sentiment: {category}")
        
        # Keyword extraction
        print("\n3. Keyword Extraction:")
        print("-" * 40)
        keywords = await gemini.extract_keywords(
            "Quantum computing uses quantum mechanics principles to process "
            "information in ways that classical computers cannot.",
            max_keywords=3
        )
        print(f"Keywords: {', '.join(keywords)}")


async def example_chat_session():
    """Example 5: Chat session with conversation history."""
    print("\n" + "=" * 60)
    print("Example 5: Chat Session")
    print("=" * 60)
    
    async with GeminiIntegration() as gemini:
        session = gemini.session(
            system_instruction="You are a helpful Python programming tutor."
        )
        
        print("\nConversation:")
        print("-" * 60)
        
        # First message
        print("User: How do I sort a list in Python?")
        response1 = await session.send(
            "How do I sort a list in Python?",
            temperature=0.5,
            max_output_tokens=200
        )
        print(f"Assistant: {response1}\n")
        
        # Follow-up question (with context)
        print("User: Can you show me a reverse sort?")
        response2 = await session.send(
            "Can you show me a reverse sort?",
            temperature=0.5,
            max_output_tokens=200
        )
        print(f"Assistant: {response2}\n")
        
        print(f"Total messages in conversation: {len(session.messages)}")


async def example_streaming_multimodal():
    """Example 6: Streaming multimodal response."""
    print("\n" + "=" * 60)
    print("Example 6: Streaming Multimodal")
    print("=" * 60)
    
    test_image = Path("test_image.jpg")
    
    if not test_image.exists():
        print("\nℹ️  Skipping streaming multimodal example (no test image found)")
        return
    
    async with GeminiIntegration() as gemini:
        print("\nStreaming image analysis:")
        print("-" * 60)
        
        async for chunk in gemini.stream_image_analysis(
            test_image,
            prompt="Analyze this image and describe its key elements in detail.",
            temperature=0.6
        ):
            print(chunk, end="", flush=True)
        
        print("\n" + "-" * 60)


async def example_custom_parameters():
    """Example 7: Custom parameters and system instructions."""
    print("\n" + "=" * 60)
    print("Example 7: Custom Parameters")
    print("=" * 60)
    
    config = GeminiConfig.from_env()
    client = GeminiClient(config)
    
    # Creative writing with high temperature
    print("\n1. Creative mode (high temperature):")
    print("-" * 40)
    response1 = await client.generate_content(
        "Write a creative opening line for a sci-fi novel",
        temperature=1.2,
        max_output_tokens=50
    )
    print(response1["content"])
    
    # Factual response with low temperature
    print("\n2. Factual mode (low temperature):")
    print("-" * 40)
    response2 = await client.generate_content(
        "What is the capital of France?",
        temperature=0.1,
        max_output_tokens=20
    )
    print(response2["content"])
    
    # With system instruction
    print("\n3. With system instruction:")
    print("-" * 40)
    response3 = await client.generate_content(
        "Explain recursion",
        temperature=0.5,
        max_output_tokens=150,
        system_instruction="Explain concepts using simple analogies suitable for beginners."
    )
    print(response3["content"])


async def main():
    """Run all examples."""
    print("\n🔮 Gemini Live Integration - Examples\n")
    
    try:
        await example_basic_text()
        await example_streaming()
        await example_multimodal()
        await example_integration_helpers()
        await example_chat_session()
        await example_streaming_multimodal()
        await example_custom_parameters()
        
        print("\n" + "=" * 60)
        print("✅ All examples completed!")
        print("=" * 60)
        
    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        print("\nMake sure you have set GEMINI_API_KEY or GOOGLE_API_KEY")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())

