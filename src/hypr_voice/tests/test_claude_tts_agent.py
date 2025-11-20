#!/usr/bin/env python3
"""
Test Claude Agent SDK with TTS Integration
Demonstrates the Claude TTS Agent capabilities
"""

import asyncio
import logging
import os
from pathlib import Path

from ..services.claude_tts_agent import ClaudeTTSAgent, quick_chat
from hypr_voice.paths import TTS_OUTPUT_DIR, ensure_runtime_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

async def test_basic_tts_agent():
    """Test basic Claude TTS Agent functionality"""
    
    print("\n" + "="*60)
    print("🤖 Testing Claude TTS Agent - Basic Functionality")
    print("="*60)
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return False
    
    try:
        async with ClaudeTTSAgent(
            tts_provider="kokoro",
            tts_voice="af_bella"
        ) as agent:
            
            # Test 1: Simple chat with TTS
            print("\n1️⃣ Testing simple chat with TTS synthesis...")
            result = await agent.chat(
                "Hello! Can you tell me a very short joke about programming?"
            )
            
            if result["success"]:
                print(f"✅ Claude response: {result['response']}")
                if result.get("tts_synthesized"):
                    print(f"🔊 Audio synthesized: {result.get('audio_file')}")
                    print(f"🎤 Voice used: {result.get('voice_used')}")
                else:
                    print("⚠️ TTS synthesis failed or disabled")
            else:
                print(f"❌ Chat failed: {result.get('error')}")
                return False
            
            # Test 2: Direct TTS synthesis
            print("\n2️⃣ Testing direct TTS synthesis...")
            tts_result = await agent.synthesize_only(
                "This is a test of the direct text-to-speech synthesis feature."
            )
            
            if tts_result["success"]:
                print(f"✅ Direct TTS successful: {tts_result.get('audio_path')}")
                print(f"🎤 Voice used: {tts_result.get('voice_used')}")
            else:
                print(f"❌ Direct TTS failed: {tts_result.get('error')}")
            
            # Test 3: Get available voices
            print("\n3️⃣ Testing voice listing...")
            voices = await agent.get_available_voices("kokoro")
            
            if voices["success"]:
                print(f"✅ Available Kokoro voices: {len(voices['voices']['kokoro'])}")
                for voice in voices['voices']['kokoro'][:5]:  # Show first 5
                    print(f"   🎤 {voice}")
                if len(voices['voices']['kokoro']) > 5:
                    print(f"   ... and {len(voices['voices']['kokoro']) - 5} more")
            else:
                print(f"❌ Voice listing failed: {voices.get('error')}")
            
            # Test 4: Agent status
            print("\n4️⃣ Testing agent status...")
            status = agent.get_status()
            print(f"✅ Agent Status:")
            for key, value in status.items():
                print(f"   {key}: {value}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        logger.error(f"Basic TTS agent test failed: {e}", exc_info=True)
        return False

async def test_quick_chat():
    """Test the quick chat convenience function"""
    
    print("\n" + "="*60)
    print("⚡ Testing Quick Chat Function")
    print("="*60)
    
    # Check API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return False
    
    try:
        # Test quick chat
        print("\n1️⃣ Testing quick chat with TTS...")
        result = await quick_chat(
            "What are the three main benefits of using text-to-speech in AI applications?",
            tts_provider="kokoro",
            synthesize=True
        )
        
        if result["success"]:
            print(f"✅ Quick chat successful!")
            print(f"📝 Response length: {len(result['response'])} characters")
            print(f"🔊 TTS synthesized: {result.get('tts_synthesized', False)}")
            if result.get('audio_file'):
                print(f"📁 Audio file: {result['audio_file']}")
        else:
            print(f"❌ Quick chat failed: {result.get('error')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Quick chat test failed: {e}")
        logger.error(f"Quick chat test failed: {e}", exc_info=True)
        return False

async def test_multiple_providers():
    """Test different TTS providers"""
    
    print("\n" + "="*60)
    print("🎭 Testing Multiple TTS Providers")
    print("="*60)
    
    # Check API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ Please set ANTHROPIC_API_KEY environment variable")
        return False
    
    providers_to_test = [
        {"provider": "kokoro", "voice": "af_bella"},
        {"provider": "kokoro", "voice": "am_adam"},
    ]
    
    # Add Deepgram if API key is available
    if os.getenv("DEEPGRAM_API_KEY"):
        providers_to_test.append({"provider": "deepgram", "voice": "aura-luna-en"})
    else:
        print("⚠️ DEEPGRAM_API_KEY not set, skipping Deepgram tests")
    
    # Add ElevenLabs if API key is available
    if os.getenv("ELEVENLABS_API_KEY"):
        providers_to_test.append({"provider": "elevenlabs", "voice": "rachel"})
    else:
        print("⚠️ ELEVENLABS_API_KEY not set, skipping ElevenLabs tests")
    
    test_text = "This is a test of multiple text-to-speech providers."
    
    for provider_config in providers_to_test:
        provider = provider_config["provider"]
        voice = provider_config["voice"]
        
        print(f"\n🎤 Testing {provider} with voice {voice}...")
        
        try:
            async with ClaudeTTSAgent(
                tts_provider=provider,
                tts_voice=voice
            ) as agent:
                
                result = await agent.synthesize_only(test_text)
                
                if result["success"]:
                    print(f"✅ {provider.title()} synthesis successful!")
                    print(f"📁 Audio file: {result.get('audio_path')}")
                    print(f"🎤 Voice used: {result.get('voice_used')}")
                    print(f"📊 Audio size: {result.get('audio_size', 'unknown')}")
                else:
                    print(f"❌ {provider.title()} synthesis failed: {result.get('error')}")
                    
        except Exception as e:
            print(f"❌ {provider.title()} test failed: {e}")
    
    return True

async def test_error_handling():
    """Test error handling scenarios"""
    
    print("\n" + "="*60)
    print("🛠️ Testing Error Handling")
    print("="*60)
    
    # Test 1: Invalid provider
    print("\n1️⃣ Testing invalid provider...")
    try:
        async with ClaudeTTSAgent(tts_provider="invalid_provider") as agent:
            pass
    except Exception as e:
        print(f"✅ Caught expected error for invalid provider: {e}")
    
    # Test 2: Empty text
    print("\n2️⃣ Testing empty text synthesis...")
    try:
        async with ClaudeTTSAgent(tts_provider="kokoro") as agent:
            result = await agent.synthesize_only("")
            if not result["success"]:
                print(f"✅ Properly handled empty text: {result.get('error')}")
            else:
                print("⚠️ Empty text should have failed but didn't")
    except Exception as e:
        print(f"✅ Caught expected error for empty text: {e}")
    
    # Test 3: Missing API key
    print("\n3️⃣ Testing missing API key...")
    original_key = os.getenv("ANTHROPIC_API_KEY")
    os.environ.pop("ANTHROPIC_API_KEY", None)
    
    try:
        async with ClaudeTTSAgent() as agent:
            pass
    except Exception as e:
        print(f"✅ Caught expected error for missing API key: {e}")
    finally:
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key
    
    return True

async def main():
    """Main test function"""
    
    print("🚀 Claude Agent SDK with TTS Integration Test")
    print("=" * 60)
    
    # Check environment
    print("\n📋 Environment Check:")
    print(f"   ANTHROPIC_API_KEY: {'✅ Set' if os.getenv('ANTHROPIC_API_KEY') else '❌ Missing'}")
    print(f"   DEEPGRAM_API_KEY: {'✅ Set' if os.getenv('DEEPGRAM_API_KEY') else '⚠️ Missing'}")
    print(f"   ELEVENLABS_API_KEY: {'✅ Set' if os.getenv('ELEVENLABS_API_KEY') else '⚠️ Missing'}")
    
    # Create output directory
    ensure_runtime_directories()
    TTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Run tests
    tests = [
        ("Basic TTS Agent", test_basic_tts_agent),
        ("Quick Chat Function", test_quick_chat),
        ("Multiple Providers", test_multiple_providers),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name} test...")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Claude Agent SDK with TTS is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check the logs above.")
    
    # Show output files
    output_dir = TTS_OUTPUT_DIR
    if output_dir.exists():
        audio_files = list(output_dir.glob("*.wav")) + list(output_dir.glob("*.mp3"))
        if audio_files:
            print(f"\n📁 Generated audio files ({len(audio_files)}):")
            for file in audio_files[:5]:  # Show first 5
                print(f"   🎵 {file.name}")
            if len(audio_files) > 5:
                print(f"   ... and {len(audio_files) - 5} more files")

if __name__ == "__main__":
    asyncio.run(main())
