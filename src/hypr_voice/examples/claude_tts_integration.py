#!/usr/bin/env python3
"""
Claude Agent SDK with TTS - Complete Example
Demonstrates real-world usage scenarios
"""

import asyncio
import logging
import os
from pathlib import Path

from ..services.claude_tts_agent import ClaudeTTSAgent
from ..core.orchestrator import AgentOrchestrator, AgentConfig
from hypr_voice.paths import TTS_OUTPUT_DIR, ensure_runtime_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def example_voice_assistant():
    """Example: Voice assistant that tells stories and answers questions"""
    
    print("\n" + "="*60)
    print("🎙️ Voice Assistant Example")
    print("="*60)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella",
        system_prompt="""You are a friendly voice assistant named Clara. 
        You provide helpful, concise responses that sound natural when spoken.
        Keep your answers under 3 sentences when possible."""
    ) as assistant:
        
        conversations = [
            "What's the weather like today?",
            "Tell me a fun fact about space",
            "How do you make a perfect cup of coffee?",
            "What's the best way to learn programming?",
            "Can you recommend a good book to read?"
        ]
        
        for i, question in enumerate(conversations, 1):
            print(f"\n👤 User: {question}")
            
            result = await assistant.chat(question, synthesize_response=True)
            
            if result["success"]:
                print(f"🤖 Clara: {result['response']}")
                if result.get("tts_synthesized"):
                    print(f"🔊 Audio: {result.get('audio_file')}")
            else:
                print(f"❌ Error: {result.get('error')}")

async def example_code_review_with_voice():
    """Example: Code review with voice explanations"""
    
    print("\n" + "="*60)
    print("💻 Code Review with Voice Example")
    print("="*60)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Sample code to review
    sample_code = '''
def calculate_factorial(n):
    if n < 0:
        return "Error: Negative number"
    elif n == 0:
        return 1
    else:
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result
'''
    
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="am_adam",  # Use male voice for technical content
        system_prompt="""You are a senior software engineer providing code reviews.
        Explain issues clearly and suggest improvements. Be technical but clear."""
    ) as reviewer:
        
        print(f"📝 Code to review:\n{sample_code}")
        
        review_prompt = f"Please review this Python code for correctness, style, and potential improvements:\n{sample_code}"
        
        result = await reviewer.chat(review_prompt, synthesize_response=True)
        
        if result["success"]:
            print(f"\n🔍 Review: {result['response']}")
            if result.get("tts_synthesized"):
                print(f"🔊 Audio explanation: {result.get('audio_file')}")
        else:
            print(f"❌ Review failed: {result.get('error')}")

async def example_multilingual_storytelling():
    """Example: Storytelling with different voices"""
    
    print("\n" + "="*60)
    print("📚 Multilingual Storytelling Example")
    print("="*60)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Different voice configurations
    voice_configs = [
        {"provider": "kokoro", "voice": "af_bella", "style": "gentle and warm"},
        {"provider": "kokoro", "voice": "am_adam", "style": "deep and thoughtful"},
        {"provider": "kokoro", "voice": "af_sarah", "style": "energetic and cheerful"},
    ]
    
    story_prompt = "Tell a short story about a robot who discovers music for the first time."
    
    for config in voice_configs:
        provider = config["provider"]
        voice = config["voice"]
        style = config["style"]
        
        print(f"\n🎭 Storytelling with {voice} ({style} voice)...")
        
        try:
            async with ClaudeTTSAgent(
                tts_provider=provider,
                tts_voice=voice,
                system_prompt=f"""You are a storyteller with a {style} voice.
                Create engaging, family-friendly stories that flow well when read aloud."""
            ) as storyteller:
                
                result = await storyteller.chat(story_prompt, synthesize_response=True)
                
                if result["success"]:
                    print(f"📖 Story: {result['response'][:200]}...")
                    if result.get("tts_synthesized"):
                        print(f"🔊 Audio story: {result.get('audio_file')}")
                else:
                    print(f"❌ Storytelling failed: {result.get('error')}")
                    
        except Exception as e:
            print(f"❌ Voice {voice} failed: {e}")

async def example_orchestrator_integration():
    """Example: Using the orchestrator with TTS agent"""
    
    print("\n" + "="*60)
    print("🎯 Orchestrator Integration Example")
    print("="*60)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    try:
        ensure_runtime_directories()
        workspace_dir = Path.cwd() / "workspace" / "tts_agent"
        workspace_dir.mkdir(parents=True, exist_ok=True)

        # Create agent configuration with TTS
        config = AgentConfig(
            name="TTS-Enhanced-Agent",
            working_directory=str(workspace_dir),
            enable_tts_agent=True,
            tts_provider="kokoro",
            tts_voice="af_bella",
            auto_synthesize=True,
            skills=["file_operations", "web_search"]
        )
        
        # Create orchestrator
        orchestrator = AgentOrchestrator()
        
        # Create agent
        agent_id = await orchestrator.create_agent(config)
        print(f"✅ Created TTS-enhanced agent: {agent_id}")
        
        # Execute instruction with TTS
        print("\n🎤 Executing instruction with automatic TTS...")
        await orchestrator.execute_instruction(
            agent_id,
            "Write a short poem about artificial intelligence and save it to a file."
        )
        
        # Wait a moment for processing
        await asyncio.sleep(3)
        
        print("✅ Agent execution completed with TTS synthesis!")
        
    except Exception as e:
        print(f"❌ Orchestrator example failed: {e}")
        logger.error(f"Orchestrator integration failed: {e}", exc_info=True)

async def example_productivity_assistant():
    """Example: Productivity assistant with voice summaries"""
    
    print("\n" + "="*60)
    print("📅 Productivity Assistant Example")
    print("="*60)
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return
    
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_sky",
        system_prompt="""You are a productivity assistant that helps people organize their day.
        Provide clear, actionable advice and summaries."""
    ) as assistant:
        
        tasks = [
            "Review project documentation and identify key action items",
            "Prepare meeting agenda for team standup",
            "Organize weekly priorities by urgency and importance",
            "Draft email response to client inquiry"
        ]
        
        print("📋 Today's tasks:")
        for i, task in enumerate(tasks, 1):
            print(f"   {i}. {task}")
        
        # Request prioritized summary
        summary_prompt = "Please prioritize these tasks and give me a brief action plan for today."
        
        result = await assistant.chat(summary_prompt, synthesize_response=True)
        
        if result["success"]:
            print(f"\n📊 Priority plan: {result['response']}")
            if result.get("tts_synthesized"):
                print(f"🔊 Voice summary: {result.get('audio_file')}")
                print("💡 You can listen to this plan while getting ready!")
        else:
            print(f"❌ Productivity planning failed: {result.get('error')}")

async def main():
    """Main function to run all examples"""
    
    print("🚀 Claude Agent SDK with TTS - Complete Examples")
    print("=" * 60)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print(f"   DEEPGRAM_API_KEY: {'✅ Set' if os.getenv('DEEPGRAM_API_KEY') else '⚠️ Missing'}")
    print(f"   ELEVENLABS_API_KEY: {'✅ Set' if os.getenv('ELEVENLABS_API_KEY') else '⚠️ Missing'}")
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n❌ ANTHROPIC_API_KEY is required for these examples")
        return
    
    # Create output directories
    ensure_runtime_directories()
    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    workspace_dir = Path.cwd() / "workspace" / "tts_agent"
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    # Run examples
    examples = [
        ("Voice Assistant", example_voice_assistant),
        ("Code Review with Voice", example_code_review_with_voice),
        ("Multilingual Storytelling", example_multilingual_storytelling),
        ("Productivity Assistant", example_productivity_assistant),
        ("Orchestrator Integration", example_orchestrator_integration),
    ]
    
    for example_name, example_func in examples:
        print(f"\n🎬 Running {example_name} example...")
        try:
            await example_func()
            print(f"✅ {example_name} example completed")
        except Exception as e:
            print(f"❌ {example_name} example failed: {e}")
            logger.error(f"{example_name} failed: {e}", exc_info=True)
        
        # Small delay between examples
        await asyncio.sleep(1)
    
    # Show generated files
    print("\n" + "="*60)
    print("📁 Generated Files")
    print("="*60)
    
    output_dirs = [str(TTS_OUTPUT_DIR), str(workspace_dir)]
    
    for directory in output_dirs:
        path = Path(directory)
        if path.exists():
            files = list(path.rglob("*"))
            audio_files = [f for f in files if f.suffix in ['.wav', '.mp3']]
            text_files = [f for f in files if f.suffix in ['.txt', '.md']]
            
            if audio_files:
                print(f"\n🎵 Audio files in {directory}:")
                for file in audio_files[:10]:  # Show first 10
                    print(f"   {file.relative_to(Path.cwd())}")
                if len(audio_files) > 10:
                    print(f"   ... and {len(audio_files) - 10} more audio files")
            
            if text_files:
                print(f"\n📝 Text files in {directory}:")
                for file in text_files:
                    print(f"   {file.relative_to(Path.cwd())}")
    
    print(f"\n🎉 All examples completed! Check the generated audio files to hear Claude speak.")

if __name__ == "__main__":
    asyncio.run(main())
