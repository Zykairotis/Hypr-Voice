#!/usr/bin/env python3
"""
Claude TTS CLI - Command Line Interface with Voice Responses
Interactive chat with Claude using text-to-speech for responses
"""

import asyncio
import argparse
import logging
import os
from pathlib import Path
from typing import Optional

from ..services.claude_tts_agent import ClaudeTTSAgent
from hypr_voice.paths import CLI_OUTPUT_DIR, ensure_runtime_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

class ClaudeTTSCLI:
    """Interactive CLI for Claude TTS Agent"""
    
    def __init__(
        self,
        provider: str = "kokoro",
        voice: Optional[str] = None,
        auto_play: bool = False,
        output_dir: str = str(CLI_OUTPUT_DIR)
    ):
        self.provider = provider
        self.voice = voice
        self.auto_play = auto_play
        self.output_dir = output_dir
        self.agent = None
        
        # Create output directory
        ensure_runtime_directories()
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async def start(self):
        """Start the interactive CLI"""
        print("🤖 Claude TTS CLI - Interactive Voice Assistant")
        print("=" * 50)
        
        # Check environment (local Claude Code doesn't need API key)
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️ ANTHROPIC_API_KEY not set - will use local Claude Code if available")
            print("   Set API key for cloud-based Claude if needed")
        
        # Show provider info
        print(f"🎤 TTS Provider: {self.provider}")
        if self.voice:
            print(f"🎭 Voice: {self.voice}")
        print(f"📁 Output Directory: {self.output_dir}")
        print(f"🔊 Auto-play: {'Enabled' if self.auto_play else 'Disabled'}")
        print("\nType 'help' for commands or 'quit' to exit.")
        print("-" * 50)
        
        try:
            # Initialize agent (will use local Claude Code by default)
            self.agent = ClaudeTTSAgent(
                enable_tts=True,
                tts_provider=self.provider,
                tts_voice=self.voice,
                working_directory=self.output_dir,
                system_prompt="""You are a helpful voice assistant. Provide clear, concise responses 
                that sound natural when spoken aloud. Keep answers under 3 sentences when possible.""",
                use_local_claude=True  # Use local Claude Code if available
            )
            
            await self.agent.connect()
            
            # Show which Claude is being used
            status = self.agent.get_status()
            if status.get("using_local_claude"):
                local_status = status.get("local_claude_status", {})
                version = local_status.get("version", "Unknown")
                print(f"✅ Using local Claude Code ({version}) with TTS capabilities")
            else:
                print("✅ Connected to cloud Claude with TTS capabilities")
            
            # Main interaction loop
            await self.interaction_loop()
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.error(f"CLI error: {e}", exc_info=True)
        finally:
            if self.agent:
                try:
                    await self.agent.close()
                except:
                    pass
    
    async def interaction_loop(self):
        """Main interaction loop"""
        
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'help':
                    self.show_help()
                    continue
                
                if user_input.lower() == 'status':
                    self.show_status()
                    continue
                
                if user_input.lower() == 'voices':
                    await self.show_voices()
                    continue
                
                if user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    continue
                
                if not user_input:
                    continue
                
                # Process with Claude and TTS
                print("🤖 Claude: ", end="", flush=True)
                
                result = await self.agent.chat(
                    user_input,
                    synthesize_response=True,
                    save_file=True
                )
                
                if result["success"]:
                    # Display text response
                    print(result["response"])
                    
                    # Show TTS info
                    if result.get("tts_synthesized"):
                        audio_file = result.get("audio_file")
                        voice_used = result.get("voice_used")
                        
                        print(f"🔊 Voice: {voice_used}")
                        print(f"📁 Audio: {audio_file}")
                        
                        # Auto-play if enabled
                        if self.auto_play and audio_file and os.path.exists(audio_file):
                            await self.play_audio(audio_file)
                    else:
                        print("⚠️ Voice synthesis failed")
                else:
                    print(f"❌ Error: {result.get('error')}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Interaction error: {e}")
    
    def show_help(self):
        """Show help commands"""
        print("\n📚 Available Commands:")
        print("  help    - Show this help message")
        print("  status  - Show agent and TTS status")
        print("  voices  - List available voices")
        print("  clear   - Clear the screen")
        print("  quit    - Exit the CLI")
        print("  exit    - Exit the CLI")
        print("  q       - Exit the CLI")
    
    def show_status(self):
        """Show current status"""
        if self.agent:
            status = self.agent.get_status()
            print(f"\n📊 Agent Status:")
            for key, value in status.items():
                print(f"   {key}: {value}")
        else:
            print("\n❌ Agent not initialized")
    
    async def show_voices(self):
        """Show available voices"""
        if not self.agent:
            print("❌ Agent not initialized")
            return
        
        print(f"\n🎭 Available Voices for {self.provider}:")
        
        try:
            voices = await self.agent.get_available_voices(self.provider)
            
            if voices["success"]:
                provider_voices = voices["voices"].get(self.provider, [])
                
                if provider_voices and isinstance(provider_voices, list):
                    for i, voice in enumerate(provider_voices[:10], 1):
                        print(f"   {i:2d}. {voice}")
                    
                    if len(provider_voices) > 10:
                        print(f"   ... and {len(provider_voices) - 10} more voices")
                else:
                    print(f"   Error: {provider_voices}")
            else:
                print(f"   Error: {voices.get('error')}")
                
        except Exception as e:
            print(f"   Error: {e}")
    
    async def play_audio(self, audio_file: str):
        """Play audio file"""
        try:
            import subprocess
            
            # Try different audio players
            players = [
                ["ffplay", "-nodisp", "-autoexit", audio_file],
                ["aplay", audio_file],
                ["paplay", audio_file],
                ["mpg123", audio_file]
            ]
            
            for player in players:
                try:
                    subprocess.run(player, check=True, capture_output=True)
                    print("🔊 Playing audio...")
                    return
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
            
            print("⚠️ No audio player found. Install ffplay, aplay, paplay, or mpg123")
            
        except Exception as e:
            print(f"⚠️ Error playing audio: {e}")

async def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="Claude TTS CLI - Interactive voice assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python claude_tts_cli.py                           # Use Kokoro (free)
  python claude_tts_cli.py --provider deepgram       # Use Deepgram (premium)
  python claude_tts_cli.py --provider elevenlabs     # Use ElevenLabs (premium)
  python claude_tts_cli.py --voice af_bella          # Use specific voice
  python claude_tts_cli.py --auto-play               # Auto-play responses
        """
    )
    
    parser.add_argument(
        "--provider",
        choices=["kokoro", "deepgram", "elevenlabs"],
        default="kokoro",
        help="TTS provider (default: kokoro)"
    )
    
    parser.add_argument(
        "--voice",
        type=str,
        help="Specific voice to use"
    )
    
    parser.add_argument(
        "--auto-play",
        action="store_true",
        help="Auto-play audio responses"
    )
    
    parser.add_argument(
        "--output-dir",
        default=str(CLI_OUTPUT_DIR),
        help="Output directory for audio files"
    )
    
    parser.add_argument(
        "--quick",
        type=str,
        help="Quick single message mode"
    )
    
    args = parser.parse_args()
    
    # Quick mode for single messages
    if args.quick:
        await quick_message(args)
        return
    
    # Interactive mode
    cli = ClaudeTTSCLI(
        provider=args.provider,
        voice=args.voice,
        auto_play=args.auto_play,
        output_dir=args.output_dir
    )
    
    await cli.start()

async def quick_message(args):
    """Quick single message mode"""
    
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️ ANTHROPIC_API_KEY not set - will use local Claude Code if available")
    
    print(f"🤖 Claude: Processing your message...")
    
    try:
        async with ClaudeTTSAgent(
            enable_tts=True,
            tts_provider=args.provider,
            tts_voice=args.voice,
            working_directory=args.output_dir,
            use_local_claude=True  # Use local Claude Code if available
        ) as agent:
            
            # Show which Claude is being used
            status = agent.get_status()
            if status.get("using_local_claude"):
                local_status = status.get("local_claude_status", {})
                version = local_status.get("version", "Unknown")
                print(f"📍 Using local Claude Code ({version})")
            else:
                print("📍 Using cloud Claude API")
            
            result = await agent.chat(
                args.quick,
                synthesize_response=True,
                save_file=True
            )
            
            if result["success"]:
                print(f"\n📝 Response: {result['response']}")
                
                if result.get("tts_synthesized"):
                    audio_file = result.get("audio_file")
                    voice_used = result.get("voice_used")
                    
                    print(f"🔊 Voice: {voice_used}")
                    print(f"📁 Audio: {audio_file}")
                    
                    # Auto-play if requested
                    if args.auto_play and audio_file and os.path.exists(audio_file):
                        cli = ClaudeTTSCLI()
                        await cli.play_audio(audio_file)
                else:
                    print("⚠️ Voice synthesis failed")
            else:
                print(f"❌ Error: {result.get('error')}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())


def run() -> None:
    """Entry-point compatible wrapper for console scripts."""
    asyncio.run(main())
