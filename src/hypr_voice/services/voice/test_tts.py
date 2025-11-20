#!/usr/bin/env python3
"""
TTS Test Script
Tests text-to-speech with various pronunciation challenges
"""

import asyncio
import argparse
import sys
import logging
from tts_manager import text_to_speech, TTSProvider, UniversalTTS, TTSConfig

# Enable logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s - %(name)s - %(message)s'
)

# Comprehensive test text with various pronunciation challenges
DEFAULT_TEST_TEXT = """Hello! Welcome to this text-to-speech test at 6:30 AM on October 30th, 2025. Let's verify pronunciation with numbers: 1, 2, 3, 10, 100, 1,000, and 1,234,567.
Now for percentages & symbols: 25% discount, $99.99 price, €50, £30, ¥1000. Email test: user@example.com. Website: https://example.com/test-page?id=123&ref=demo.
Punctuation check: "Are you ready?" she asked. He replied, "Yes! Absolutely." They wondered—would it work? It's amazing; truly remarkable. Let's try more: (parentheses), [brackets], {braces}, and <angle brackets>.
Mathematical expressions: 2 + 2 = 4, 10 - 5 = 5, 3 × 4 = 12, 20 ÷ 4 = 5. Temperature: -10°C or 98.6°F.
Special characters test: #hashtag, @mention, asterisk, underscore, ~tilde~, backtick, |pipe|, \\backslash/, ^caret^.
Time formats: 3:45 PM, 15:45, 00:00:00. Dates: 10/30/2025, 2025-10-30.
Final check with contractions: I'm, you're, we've, they'd, won't, can't, shouldn't.
Ending with emphasis: THIS IS ALL CAPS! this is lowercase. MiXeD CaSe TeXt.
Thank you for testing!"""

# Short test text for fast response (~1-2 seconds)
SHORT_TEST_TEXT = """Hello! This is a quick test of the text-to-speech system. Numbers: 1, 2, 3, 100. Thank you!"""


async def test_tts(provider: str, voice: str = None, model: str = None, speed: float = 1.0, 
                   text: str = None, auto_play: bool = True, use_streaming: bool = False):
    """
    Test TTS with specified parameters
    
    Args:
        provider: TTS provider (kokoro, deepgram, elevenlabs)
        voice: Voice name (optional, will use default or random)
        model: Model name (optional, will use default)
        speed: Speech speed (default: 1.0)
        text: Text to speak (optional, will use default test text)
        auto_play: Auto-play generated audio (default: True)
        use_streaming: Enable streaming mode (play while generating, ~5sec for long text)
    """
    import time
    import subprocess
    
    # Use default test text if not provided
    if text is None:
        text = DEFAULT_TEST_TEXT
    
    # Convert provider string to enum
    try:
        provider_enum = TTSProvider(provider.lower())
    except ValueError:
        print(f"❌ Invalid provider '{provider}'. Valid options: kokoro, deepgram, elevenlabs")
        return
    
    print("\n" + "="*60)
    print("TTS TEST")
    print("="*60)
    print(f"Provider: {provider}")
    print(f"Voice: {voice or 'default/random'}")
    print(f"Model: {model or 'default'}")
    print(f"Speed: {speed}x")
    print(f"Text length: {len(text)} characters")
    print("="*60)
    
    # Create config
    config = TTSConfig(
        provider=provider_enum,
        voice=voice,
        model=model,
        speed=speed,
        output_dir="./tts_test_output",
        save_to_file=True,
        use_streaming=use_streaming,
        stream_and_play=use_streaming  # Auto-play while streaming
    )
    
    # Initialize TTS
    tts = UniversalTTS(config)
    
    print("\n🎙️  Generating audio...")
    
    # Start timing
    start_time = time.time()
    
    # Generate speech
    result = await tts.speak(text)
    
    # Calculate generation time
    generation_time = time.time() - start_time
    
    if result['success']:
        print("\n✅ SUCCESS!")
        print(f"   Voice used: {result['voice_used']}")
        print(f"   Model used: {result.get('model_used', 'N/A')}")
        print(f"   Provider: {result['provider']}")
        print(f"   Format: {result.get('format', 'N/A')}")
        print(f"   Sample rate: {result.get('sample_rate', 'N/A')} Hz")
        
        if use_streaming:
            print(f"   ⏱️  Total time (generation + playback): {generation_time:.2f} seconds")
            print(f"   🌊 Streaming mode: Audio played while generating!")
        else:
            print(f"   ⏱️  Generation time: {generation_time:.2f} seconds")
        
        if result.get('audio_data'):
            size_kb = len(result['audio_data']) / 1024
            print(f"   📊 Audio size: {size_kb:.2f} KB")
        
        if result.get('audio_file'):
            audio_file = result['audio_file']
            print(f"   📁 Audio saved to: {audio_file}")
            
            # Auto-play the audio if enabled (not in streaming mode)
            if auto_play and not use_streaming:
                print(f"\n🔊 Playing audio...")
                
                # Wake up audio device with brief silence (prevents cutoff)
                try:
                    subprocess.run(
                        ["aplay", "-d", "0.2", "/dev/zero"],
                        capture_output=True,
                        timeout=1,
                        check=False
                    )
                    time.sleep(0.05)
                except:
                    pass
                
                # Try multiple audio players in order of preference
                players = [
                    ["pw-play", audio_file],           # PipeWire
                    ["paplay", audio_file],            # PulseAudio  
                    ["aplay", audio_file],             # ALSA
                    ["ffplay", "-nodisp", "-autoexit", "-hide_banner", "-loglevel", "quiet", audio_file],
                    ["mpv", "--no-video", audio_file], # MPV
                    ["play", "-q", audio_file],        # sox
                ]
                
                played = False
                for player_cmd in players:
                    try:
                        subprocess.run(
                            player_cmd,
                            check=True,
                            capture_output=True,
                            timeout=120  # 2 minute timeout for playback
                        )
                        played = True
                        print("✅ Playback complete!")
                        break
                    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                        continue
                
                if not played:
                    print(f"⚠️  No audio player found. Manual playback:")
                    print(f"   ffplay {audio_file}")
                    print(f"   # or")
                    print(f"   mpv {audio_file}")
            else:
                print(f"\n💡 To play the audio:")
                print(f"   ffplay {audio_file}")
                print(f"   # or")
                print(f"   mpv {audio_file}")
    else:
        print(f"\n❌ FAILED!")
        print(f"   Error: {result.get('error', 'Unknown error')}")
        print(f"   Provider: {result.get('provider', 'Unknown')}")
        
        # Show traceback if available
        if 'traceback' in result and result['traceback']:
            print(f"\n🔍 Full traceback:")
            print(result['traceback'])


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Test TTS with comprehensive pronunciation challenges',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with Kokoro (local)
  python test_tts.py --provider kokoro --voice af_bella
  
  # Test with Deepgram
  python test_tts.py --provider deepgram --voice luna --model aura-2
  
  # Test with ElevenLabs at slower speed
  python test_tts.py --provider elevenlabs --voice rachel --speed 0.8
  
  # Test with custom text
  python test_tts.py --provider kokoro --text "Hello world"
  
  # Test with random voice
  python test_tts.py --provider kokoro
        """
    )
    
    parser.add_argument(
        '--provider', '-p',
        type=str,
        default='kokoro',
        choices=['kokoro', 'deepgram', 'elevenlabs'],
        help='TTS provider to use (default: kokoro)'
    )
    
    parser.add_argument(
        '--voice', '-v',
        type=str,
        default=None,
        help='Voice name (default: provider default or random)'
    )
    
    parser.add_argument(
        '--model', '-m',
        type=str,
        default=None,
        help='Model name (default: provider default)'
    )
    
    parser.add_argument(
        '--speed', '-s',
        type=float,
        default=1.0,
        help='Speech speed multiplier (default: 1.0)'
    )
    
    parser.add_argument(
        '--text', '-t',
        type=str,
        default=None,
        help='Custom text to speak (default: comprehensive test text)'
    )
    
    parser.add_argument(
        '--show-text',
        action='store_true',
        help='Show the default test text and exit'
    )
    
    parser.add_argument(
        '--no-play',
        action='store_true',
        help='Do not auto-play the generated audio'
    )
    
    parser.add_argument(
        '--quick',
        action='store_true',
        help='Use short test text for fast response (~1-2 seconds)'
    )
    
    parser.add_argument(
        '--stream',
        action='store_true',
        help='Enable streaming mode (play while generating, ~5sec perceived latency for long text)'
    )
    
    args = parser.parse_args()
    
    # Show test text if requested
    if args.show_text:
        print("\nDefault Test Text:")
        print("="*60)
        print(DEFAULT_TEST_TEXT)
        print("="*60)
        return
    
    # Check for API keys if using cloud providers
    if args.provider == 'deepgram':
        import os
        if not os.getenv('DEEPGRAM_API_KEY'):
            print("⚠️  Warning: DEEPGRAM_API_KEY not set in environment")
            print("   Set it with: export DEEPGRAM_API_KEY='your_key'")
            return
    
    if args.provider == 'elevenlabs':
        import os
        if not os.getenv('ELEVENLABS_API_KEY'):
            print("⚠️  Warning: ELEVENLABS_API_KEY not set in environment")
            print("   Set it with: export ELEVENLABS_API_KEY='your_key'")
            return
    
    if args.provider == 'kokoro':
        print("⚠️  Note: Make sure Kokoro server is running on localhost:8880")
        print("   Run: python Kokoro-FastAPI/server.py --host 0.0.0.0 --port 8880\n")
    
    # Use short text if --quick flag is set
    test_text = args.text
    if args.quick and not args.text:
        test_text = SHORT_TEST_TEXT
        print("🚀 Quick mode: Using short test text for fast response\n")
    
    # Show streaming info
    if args.stream:
        print("🌊 Streaming mode enabled: Audio will play while being generated\n")
    
    # Run the test
    asyncio.run(test_tts(
        provider=args.provider,
        voice=args.voice,
        model=args.model,
        speed=args.speed,
        text=test_text,
        auto_play=not args.no_play and not args.stream,  # Auto-play unless --no-play or --stream
        use_streaming=args.stream
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
