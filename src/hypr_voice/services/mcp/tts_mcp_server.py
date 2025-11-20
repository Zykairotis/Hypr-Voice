#!/usr/bin/env python3
"""
TTS MCP Server for Claude Agent SDK
Provides text-to-speech capabilities through MCP protocol
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Import our TTS system
try:
    from ..voice import TTSManager, TTSConfig, TTSProvider
    TTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"TTS service not available: {e}")
    TTS_AVAILABLE = False

from hypr_voice.paths import TTS_OUTPUT_DIR, ensure_runtime_directories

logger = logging.getLogger(__name__)

class TTSMCPServer:
    """TTS MCP Server for Claude Agent SDK integration"""
    
    def __init__(self):
        self.server = Server("tts-server")
        self.tts_manager = None
        self._setup_handlers()
        
        if TTS_AVAILABLE:
            self._initialize_tts()
    
    def _initialize_tts(self):
        """Initialize TTS manager with default configuration"""
        try:
            # Default to Kokoro for free local TTS
            ensure_runtime_directories()
            config = TTSConfig(
                provider=TTSProvider.KOKORO,
                voice="af_bella",
                use_streaming=True,
                stream_and_play=False,  # Don't auto-play in MCP context
                output_dir=str(TTS_OUTPUT_DIR)
            )
            self.tts_manager = TTSManager(config)
            logger.info("TTS manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize TTS manager: {e}")
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available TTS tools"""
            tools = [
                Tool(
                    name="synthesize_speech",
                    description="Convert text to speech using available TTS providers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Text to convert to speech"
                            },
                            "provider": {
                                "type": "string",
                                "enum": ["kokoro", "deepgram", "elevenlabs"],
                                "description": "TTS provider to use (default: kokoro)",
                                "default": "kokoro"
                            },
                            "voice": {
                                "type": "string",
                                "description": "Voice name to use (optional, will use default)"
                            },
                            "speed": {
                                "type": "number",
                                "minimum": 0.25,
                                "maximum": 4.0,
                                "description": "Speech speed (0.25-4.0, default: 1.0)",
                                "default": 1.0
                            },
                            "save_file": {
                                "type": "boolean",
                                "description": "Whether to save audio file (default: true)",
                                "default": True
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="list_voices",
                    description="List available voices for TTS providers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "provider": {
                                "type": "string",
                                "enum": ["kokoro", "deepgram", "elevenlabs"],
                                "description": "TTS provider (default: all)",
                                "default": "all"
                            }
                        }
                    }
                ),
                Tool(
                    name="get_tts_info",
                    description="Get information about TTS providers and capabilities",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
            
            if not TTS_AVAILABLE:
                return []  # Return empty list if TTS not available
                
            return tools
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            
            if not TTS_AVAILABLE:
                return [TextContent(
                    type="text",
                    text="Error: TTS service not available. Please check the voice service installation."
                )]
            
            try:
                if name == "synthesize_speech":
                    return await self._handle_synthesize_speech(arguments)
                elif name == "list_voices":
                    return await self._handle_list_voices(arguments)
                elif name == "get_tts_info":
                    return await self._handle_get_tts_info(arguments)
                else:
                    return [TextContent(
                        type="text",
                        text=f"Error: Unknown tool '{name}'"
                    )]
            except Exception as e:
                logger.error(f"Error in tool {name}: {e}")
                return [TextContent(
                    type="text",
                    text=f"Error: {str(e)}"
                )]
    
    async def _handle_synthesize_speech(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle speech synthesis"""
        
        text = arguments.get("text", "")
        provider = arguments.get("provider", "kokoro")
        voice = arguments.get("voice")
        speed = arguments.get("speed", 1.0)
        save_file = arguments.get("save_file", True)
        
        if not text.strip():
            return [TextContent(
                type="text",
                text="Error: Text parameter is required and cannot be empty"
            )]
        
        try:
            # Convert provider string to enum
            provider_enum = TTSProvider(provider.lower())
            
            # Create configuration
            config = TTSConfig(
                provider=provider_enum,
                voice=voice,
                speed=speed,
                use_streaming=False,  # Don't use streaming for MCP
                output_dir="./tts_mcp_output" if save_file else None
            )
            
            # Create new TTS manager instance
            tts = TTSManager(config)
            
            # Generate speech
            result = await tts.speak(text)
            
            if result.get("success"):
                response_parts = [
                    f"✅ Speech synthesized successfully!",
                    f"Provider: {result.get('provider', provider)}",
                    f"Voice used: {result.get('voice_used', 'default')}",
                    f"Audio size: {result.get('audio_size', 'unknown')}",
                ]
                
                if save_file and result.get("audio_path"):
                    response_parts.append(f"Audio file: {result['audio_path']}")
                
                return [TextContent(
                    type="text",
                    text="\n".join(response_parts)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"❌ Failed to synthesize speech: {result.get('error', 'Unknown error')}"
                )]
                
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Error: Invalid provider '{provider}'. Available: kokoro, deepgram, elevenlabs"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    async def _handle_list_voices(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle listing voices"""
        
        provider = arguments.get("provider", "all")
        
        try:
            if provider == "all":
                # List voices for all providers
                voices_info = {}
                for prov in ["kokoro", "deepgram", "elevenlabs"]:
                    try:
                        config = TTSConfig(provider=TTSProvider(prov))
                        tts = TTSManager(config)
                        voices = tts.list_voices()
                        voices_info[prov] = voices
                    except Exception as e:
                        voices_info[prov] = [f"Error: {str(e)}"]
                
                response = ["Available voices by provider:\n"]
                for prov, voices in voices_info.items():
                    response.append(f"\n{prov.upper()}:")
                    if isinstance(voices, list) and voices:
                        for voice in voices[:10]:  # Limit to first 10 voices
                            response.append(f"  - {voice}")
                        if len(voices) > 10:
                            response.append(f"  ... and {len(voices) - 10} more")
                    else:
                        response.append(f"  {voices}")
                
                return [TextContent(
                    type="text",
                    text="\n".join(response)
                )]
            else:
                # List voices for specific provider
                provider_enum = TTSProvider(provider.lower())
                config = TTSConfig(provider=provider_enum)
                tts = TTSManager(config)
                voices = tts.list_voices()
                
                response = [f"Available voices for {provider.upper()}:\n"]
                for voice in voices:
                    response.append(f"  - {voice}")
                
                return [TextContent(
                    type="text",
                    text="\n".join(response)
                )]
                
        except ValueError as e:
            return [TextContent(
                type="text",
                text=f"Error: Invalid provider '{provider}'. Available: kokoro, deepgram, elevenlabs, all"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error: {str(e)}"
            )]
    
    async def _handle_get_tts_info(self, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle getting TTS information"""
        
        info = [
            "TTS (Text-to-Speech) Provider Information:",
            "=" * 50,
            "",
            "KOKORO (Local, Free):",
            "  - 17 voices available",
            "  - Multiple accents (American, British)",
            "  - Child and robot voices",
            "  - Completely offline and free",
            "  - HTTP streaming support",
            "",
            "DEEPGRAM (Cloud, Premium):",
            "  - Aura series voices (asteria, luna, stella, etc.)",
            "  - Premium quality audio",
            "  - HTTP streaming support",
            "  - Per-character pricing",
            "  - Requires DEEPGRAM_API_KEY",
            "",
            "ELEVENLABS (Cloud, Premium):",
            "  - 44+ premade voices",
            "  - Highest quality audio",
            "  - Voice cloning capabilities",
            "  - Per-character pricing",
            "  - Requires ELEVENLABS_API_KEY",
            "",
            "Usage:",
            "  1. Use kokoro for free, local TTS",
            "  2. Use deepgram for premium quality with streaming",
            "  3. Use elevenlabs for maximum quality and features",
        ]
        
        if not TTS_AVAILABLE:
            info.insert(0, "⚠️ TTS service is currently not available")
        
        return [TextContent(
            type="text",
            text="\n".join(info)
        )]

async def main():
    """Main entry point for the TTS MCP server"""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and run server
    tts_server = TTSMCPServer()
    
    # Create output directory
    Path("./tts_mcp_output").mkdir(exist_ok=True)
    
    logger.info("Starting TTS MCP Server...")
    
    async with stdio_server() as (read_stream, write_stream):
        await tts_server.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tts-server",
                server_version="1.0.0",
                capabilities=tts_server.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities={}
                )
            )
        )

if __name__ == "__main__":
    asyncio.run(main())
