#!/usr/bin/env python3
"""
Claude Agent SDK Wrapper with TTS Integration
Provides a high-level interface for Claude Agent SDK with voice synthesis capabilities
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, AsyncIterator

try:
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        AssistantMessage,
        TextBlock,
        ResultMessage
    )
    CLAUDE_SDK_AVAILABLE = True
except ImportError:
    CLAUDE_SDK_AVAILABLE = False
    logging.warning("Claude Agent SDK not available")

# Try to import local Claude Code integration
try:
    import subprocess
    import json
    import os
    from pathlib import Path
    
    # Check if Claude Code is available locally
    def check_claude_code():
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    CLAUDE_CODE_LOCAL = check_claude_code()
    if CLAUDE_CODE_LOCAL:
        logging.info("Local Claude Code detected and available")
    
except ImportError:
    CLAUDE_CODE_LOCAL = False
    logging.warning("Local Claude Code integration not available")

# Import our TTS system
try:
    from .voice import UniversalTTS as TTSManager, TTSConfig, TTSProvider
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logging.warning("TTS service not available")

from hypr_voice.paths import TTS_OUTPUT_DIR, ensure_runtime_directories

logger = logging.getLogger(__name__)

class LocalClaudeCodeIntegration:
    """Integration with local Claude Code installation"""
    
    def __init__(self, working_directory: str = None):
        self.working_directory = working_directory or str(Path.cwd())
        self.logger = logging.getLogger("LocalClaudeCode")
    
    async def query(self, prompt: str, timeout: int = 60) -> str:
        """
        Query local Claude Code with a prompt
        
        Args:
            prompt: The prompt to send to Claude Code
            timeout: Timeout in seconds
            
        Returns:
            Claude's response as text
        """
        try:
            # Ensure working directory exists
            Path(self.working_directory).mkdir(parents=True, exist_ok=True)
            
            # Create a temporary file for the prompt
            prompt_file = Path(self.working_directory) / ".claude_prompt.txt"
            with open(prompt_file, 'w') as f:
                f.write(prompt)
            
            # Run Claude Code in print mode
            cmd = [
                "claude",
                "-p",
                "--output-format", "text",
                str(prompt_file)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            # Clean up prompt file
            try:
                prompt_file.unlink()
            except:
                pass
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                raise Exception(f"Claude Code failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            raise Exception(f"Claude Code timed out after {timeout} seconds")
        except Exception as e:
            self.logger.error(f"Local Claude Code query failed: {e}")
            raise
    
    def get_status(self) -> dict:
        """Get status of local Claude Code"""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                return {
                    "available": True,
                    "version": version,
                    "type": "local"
                }
            else:
                return {
                    "available": False,
                    "error": result.stderr.strip()
                }
        except Exception as e:
            return {
                "available": False,
                "error": str(e)
            }

class ClaudeTTSAgent:
    """
    Claude Agent SDK wrapper with integrated TTS capabilities
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_tts: bool = True,
        tts_provider: str = "kokoro",
        tts_voice: Optional[str] = None,
        working_directory: Optional[str] = None,
        system_prompt: Optional[str] = None,
        use_local_claude: bool = True
    ):
        """
        Initialize Claude TTS Agent
        
        Args:
            api_key: Anthropic API key (or set ANTHROPIC_API_KEY env var)
            enable_tts: Whether to enable TTS capabilities
            tts_provider: TTS provider to use (kokoro, deepgram, elevenlabs)
            tts_voice: Specific voice to use (optional)
            working_directory: Working directory for file operations
            system_prompt: Custom system prompt for the agent
            use_local_claude: Whether to use local Claude Code installation
        """
        self.working_directory = working_directory or str(Path.cwd())
        self.use_local_claude = use_local_claude and CLAUDE_CODE_LOCAL
        self.enable_tts = enable_tts and TTS_AVAILABLE
        self.tts_provider = tts_provider
        self.tts_voice = tts_voice
        
        # Initialize local Claude Code if available and requested
        self.local_claude = None
        if self.use_local_claude:
            self.local_claude = LocalClaudeCodeIntegration(self.working_directory)
            logger.info("Using local Claude Code installation")
        
        # Initialize API-based Claude if local not available or API key provided
        self.client = None
        if not self.use_local_claude:
            if not CLAUDE_SDK_AVAILABLE:
                raise ImportError("Claude Agent SDK is required. Install with: pip install claude-agent-sdk")
            
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not self.api_key:
                raise ValueError("API key is required. Set ANTHROPIC_API_KEY environment variable or pass api_key parameter")
        
        # Initialize TTS if enabled
        self.tts_manager = None
        if self.enable_tts:
            self._initialize_tts()
        
        # Setup Claude Agent options (for API-based mode)
        self.agent_options = None
        if not self.use_local_claude:
            self.agent_options = self._setup_agent_options(system_prompt)
        
        logger.info(f"Claude TTS Agent initialized - Local: {self.use_local_claude}, TTS: {self.enable_tts}")
    
    def _initialize_tts(self):
        """Initialize TTS manager"""
        try:
            ensure_runtime_directories()
            provider_enum = TTSProvider(self.tts_provider.lower())
            config = TTSConfig(
                provider=provider_enum,
                voice=self.tts_voice,
                use_streaming=False,  # Don't use streaming for agent responses
                output_dir=str(TTS_OUTPUT_DIR)
            )
            self.tts_manager = TTSManager(config)
            logger.info(f"TTS initialized with {self.tts_provider} provider")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            self.enable_tts = False
    
    def _setup_agent_options(
        self, 
        working_directory: Optional[str], 
        system_prompt: Optional[str]
    ) -> ClaudeAgentOptions:
        """Setup Claude Agent options"""
        
        # Default system prompt with TTS awareness
        default_prompt = """You are a helpful AI assistant with access to text-to-speech capabilities.

When you provide responses that would benefit from being spoken aloud:
- Use clear, concise language
- Avoid complex punctuation that sounds unnatural when spoken
- Break long responses into shorter paragraphs
- Use conversational tone when appropriate

You have access to file system tools, web search, and TTS synthesis capabilities."""
        
        if system_prompt:
            default_prompt = system_prompt
        
        options = ClaudeAgentOptions(
            system_prompt=default_prompt,
            max_turns=5,
            permission_mode="acceptEdits",  # Auto-accept file edits
            cwd=working_directory or str(Path.cwd())
        )
        
        return options
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def connect(self):
        """Connect to Claude (local or API)"""
        try:
            if self.use_local_claude:
                # Local Claude Code is already "connected" via subprocess
                logger.info("Using local Claude Code - no connection needed")
            else:
                # Connect to API-based Claude Agent SDK
                self.client = ClaudeSDKClient(options=self.agent_options)
                await self.client.__aenter__()
                logger.info("Connected to Claude Agent SDK")
        except Exception as e:
            logger.error(f"Failed to connect to Claude: {e}")
            raise
    
    async def close(self):
        """Close connection to Claude Agent SDK"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                logger.info("Closed connection to Claude Agent SDK")
            except Exception as e:
                logger.error(f"Error closing Claude Agent SDK: {e}")
    
    async def chat(
        self, 
        message: str, 
        synthesize_response: bool = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a message to Claude and optionally synthesize the response
        
        Args:
            message: Message to send to Claude
            synthesize_response: Whether to synthesize response to speech
                                 (None=use default enable_tts)
            **kwargs: Additional arguments for TTS
        
        Returns:
            Dictionary with response and optional TTS info
        """
        if not self.use_local_claude and not self.client:
            raise RuntimeError("Agent not connected. Call await connect() first.")
        
        # Determine if we should synthesize
        should_synthesize = synthesize_response if synthesize_response is not None else self.enable_tts
        
        try:
            # Send message to Claude
            if self.use_local_claude:
                # Use local Claude Code
                response_text = await self.local_claude.query(message)
                claude_source = "local_claude_code"
            else:
                # Use API-based Claude Agent SDK
                await self.client.query(message)
                
                # Collect response
                response_text = ""
                async for msg in self.client.receive_response():
                    if hasattr(msg, 'text'):
                        response_text += msg.text
                    elif hasattr(msg, 'content'):
                        if isinstance(msg.content, list):
                            for block in msg.content:
                                if hasattr(block, 'text'):
                                    response_text += block.text
                        else:
                            response_text += str(msg.content)
                claude_source = "claude_agent_sdk"
            
            result = {
                "success": True,
                "message": message,
                "response": response_text,
                "claude_source": claude_source,
                "tts_synthesized": False
            }
            
            # Synthesize response if requested
            if should_synthesize and response_text.strip() and self.tts_manager:
                try:
                    tts_result = await self.tts_manager.speak(response_text, **kwargs)
                    result.update({
                        "tts_synthesized": True,
                        "tts_result": tts_result,
                        "audio_file": tts_result.get("audio_file") or tts_result.get("audio_path"),
                        "voice_used": tts_result.get("voice_used")
                    })
                except Exception as e:
                    logger.error(f"TTS synthesis failed: {e}")
                    result["tts_error"] = str(e)
            
            return result
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {
                "success": False,
                "message": message,
                "error": str(e),
                "tts_synthesized": False
            }
    
    async def synthesize_only(
        self, 
        text: str, 
        provider: Optional[str] = None,
        voice: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synthesize text to speech without Claude processing
        
        Args:
            text: Text to synthesize
            provider: Override TTS provider
            voice: Override voice
            **kwargs: Additional TTS parameters
        
        Returns:
            TTS synthesis result
        """
        if not self.enable_tts or not self.tts_manager:
            return {
                "success": False,
                "error": "TTS not enabled or available"
            }
        
        try:
            # Create temporary config if overriding provider/voice
            if provider or voice:
                provider_enum = TTSProvider(
                    (provider or self.tts_provider).lower()
                )
                config = TTSConfig(
                    provider=provider_enum,
                    voice=voice or self.tts_voice,
                    use_streaming=False,
                    output_dir=str(TTS_OUTPUT_DIR)
                )
                tts = TTSManager(config)
                result = await tts.speak(text, **kwargs)
            else:
                result = await self.tts_manager.speak(text, **kwargs)
            
            return {
                "success": True,
                **result
            }
            
        except Exception as e:
            logger.error(f"Direct TTS synthesis failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_available_voices(self, provider: str = "all") -> Dict[str, Any]:
        """Get available voices for TTS providers"""
        if not self.enable_tts:
            return {"success": False, "error": "TTS not enabled"}
        
        try:
            if provider == "all":
                voices = {}
                for prov in ["kokoro", "deepgram", "elevenlabs"]:
                    try:
                        provider_enum = TTSProvider(prov)
                        config = TTSConfig(provider=provider_enum)
                        tts = TTSManager(config)
                        voices[prov] = tts.list_voices()
                    except Exception as e:
                        voices[prov] = [f"Error: {str(e)}"]
                
                return {"success": True, "voices": voices}
            else:
                provider_enum = TTSProvider(provider.lower())
                config = TTSConfig(provider=provider_enum)
                tts = TTSManager(config)
                voices = tts.list_voices()
                
                return {"success": True, "voices": {provider: voices}}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        status = {
            "claude_sdk_available": CLAUDE_SDK_AVAILABLE,
            "claude_code_local": CLAUDE_CODE_LOCAL,
            "tts_available": TTS_AVAILABLE,
            "tts_enabled": self.enable_tts,
            "tts_provider": self.tts_provider if self.enable_tts else None,
            "tts_voice": self.tts_voice if self.enable_tts else None,
            "using_local_claude": self.use_local_claude,
            "connected": self.client is not None or self.use_local_claude
        }
        
        # Add local Claude Code status if available
        if self.use_local_claude and self.local_claude:
            status["local_claude_status"] = self.local_claude.get_status()
        
        return status

# Convenience function for quick usage
async def quick_chat(
    message: str,
    api_key: Optional[str] = None,
    tts_provider: str = "kokoro",
    synthesize: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    Quick chat function for simple usage
    
    Args:
        message: Message to send
        api_key: Anthropic API key
        tts_provider: TTS provider
        synthesize: Whether to synthesize response
        **kwargs: Additional arguments
    
    Returns:
        Chat result
    """
    async with ClaudeTTSAgent(
        api_key=api_key,
        enable_tts=synthesize,
        tts_provider=tts_provider
    ) as agent:
        return await agent.chat(message, synthesize_response=synthesize, **kwargs)

# Example usage
async def example_usage():
    """Example of how to use the Claude TTS Agent"""
    
    # Check if API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    # Use with context manager
    async with ClaudeTTSAgent(
        tts_provider="kokoro",
        tts_voice="af_bella"
    ) as agent:
        
        # Simple chat with TTS
        result = await agent.chat(
            "Hello! Can you tell me a short story about a robot learning to paint?"
        )
        
        print(f"Claude response: {result['response']}")
        if result.get('tts_synthesized'):
            print(f"Audio synthesized: {result.get('audio_file')}")
        
        # Get available voices
        voices = await agent.get_available_voices()
        print(f"Available voices: {voices}")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
