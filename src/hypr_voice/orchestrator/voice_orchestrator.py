"""
Voice Orchestrator

Integrates Hypr-Whisper STT with the orchestrator and Deepgram TTS for responses.
Provides a complete voice-to-voice conversation pipeline.
"""

import asyncio
import logging
import os
import tempfile
import time
from typing import Optional, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import aiohttp
from pathlib import Path

from .orchestrator import HyprVoiceOrchestrator, OrchestratorConfig

logger = logging.getLogger(__name__)

# Regex for stripping markdown
import re

def strip_markdown_for_tts(text: str) -> str:
    """
    Remove markdown formatting from text for clean TTS output.
    
    For streaming tokens, we can't match pairs like **bold** because
    the markers may be split across tokens. Instead, we aggressively
    remove all markdown-style characters.
    """
    if not text:
        return text
    
    # Remove all asterisks (bold/italic markers)
    text = text.replace('*', '')
    
    # Remove all backticks (code markers)
    text = text.replace('`', '')
    
    # Remove underscores at word boundaries (but keep snake_case)
    # Simple approach: remove _ when surrounded by spaces or at edges
    text = re.sub(r'\s_+', ' ', text)  # space followed by underscores
    text = re.sub(r'_+\s', ' ', text)  # underscores followed by space
    text = re.sub(r'^_+', '', text)    # leading underscores
    text = re.sub(r'_+$', '', text)    # trailing underscores
    
    # Remove hash symbols at start (headers)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    
    # Remove blockquote markers
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    
    # Clean up extra whitespace
    text = re.sub(r'  +', ' ', text)
    
    return text


# Try to import TTS system
try:
    from ..services.voice import UniversalTTS, TTSConfig, TTSProvider
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False
    logger.warning("TTS system not available")


@dataclass
class ConversationMessage:
    """A single message in a conversation."""
    id: str
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    agent_type: Optional[str] = None
    audio_file: Optional[str] = None
    duration_ms: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
            "agent_type": self.agent_type,
            "audio_file": self.audio_file,
            "duration_ms": self.duration_ms,
        }


@dataclass
class Conversation:
    """A conversation session with message history."""
    id: str
    created_at: str
    messages: list[ConversationMessage] = field(default_factory=list)
    title: Optional[str] = None
    
    def add_message(self, role: str, content: str, agent_type: Optional[str] = None, 
                   audio_file: Optional[str] = None) -> ConversationMessage:
        msg = ConversationMessage(
            id=str(uuid.uuid4())[:8],
            role=role,
            content=content,
            timestamp=datetime.utcnow().isoformat(),
            agent_type=agent_type,
            audio_file=audio_file,
        )
        self.messages.append(msg)
        
        # Auto-generate title from first user message
        if not self.title and role == "user":
            self.title = content[:50] + ("..." if len(content) > 50 else "")
        
        return msg
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at,
            "title": self.title,
            "messages": [m.to_dict() for m in self.messages],
            "message_count": len(self.messages),
        }


@dataclass
class VoiceOrchestratorConfig:
    """Configuration for the voice orchestrator."""
    tts_provider: str = "deepgram"
    tts_voice: str = "aura-luna-en"  # Deepgram Aura voice
    whisper_url: str = "http://localhost:9099"
    output_dir: Optional[str] = None
    save_to_file: bool = True
    

class VoiceOrchestrator:
    """
    Voice-enabled orchestrator with STT and TTS integration.
    
    Provides:
    - Speech-to-text via Hypr-Whisper
    - Query routing via HyprVoiceOrchestrator
    - Text-to-speech via Deepgram (or other providers)
    - Conversation history management
    """
    
    def __init__(self, config: Optional[VoiceOrchestratorConfig] = None):
        self.config = config or VoiceOrchestratorConfig()
        self.orchestrator = HyprVoiceOrchestrator()
        self.conversations: dict[str, Conversation] = {}
        self.current_conversation_id: Optional[str] = None
        
        # Initialize TTS
        self.tts = None
        if TTS_AVAILABLE:
            self._initialize_tts()
        else:
            logger.warning("TTS not available - responses will be text only")
    
    def _initialize_tts(self):
        """Initialize TTS with Deepgram."""
        try:
            # Get API key from environment
            deepgram_key = os.getenv("DEEPGRAM_API_KEY")
            logger.info(f"[TTS Init] DEEPGRAM_API_KEY present: {bool(deepgram_key)}, provider: {self.config.tts_provider}")
            if not deepgram_key:
                logger.warning("DEEPGRAM_API_KEY not set - TTS disabled")
                return
            
            provider = TTSProvider(self.config.tts_provider.lower())
            tts_config = TTSConfig(
                provider=provider,
                voice=self.config.tts_voice,
                deepgram_api_key=deepgram_key,
                save_to_file=self.config.save_to_file,
                output_dir=self.config.output_dir or "./audio_output",
                use_streaming=True,
                stream_and_play=True,  # Enable auto-play during streaming
            )
            self.tts = UniversalTTS(tts_config)
            logger.info(f"[TTS Init] SUCCESS - provider={self.config.tts_provider}, voice={self.config.tts_voice}")
        except Exception as e:
            logger.error(f"[TTS Init] FAILED: {e}", exc_info=True)
            self.tts = None
    
    def create_conversation(self) -> Conversation:
        """Create a new conversation session."""
        conv = Conversation(
            id=str(uuid.uuid4())[:12],
            created_at=datetime.utcnow().isoformat(),
        )
        self.conversations[conv.id] = conv
        self.current_conversation_id = conv.id
        logger.info(f"Created conversation {conv.id}")
        return conv
    
    def get_conversation(self, conversation_id: Optional[str] = None) -> Optional[Conversation]:
        """Get a conversation by ID or the current one."""
        conv_id = conversation_id or self.current_conversation_id
        if not conv_id:
            return None
        return self.conversations.get(conv_id)
    
    def list_conversations(self) -> list[dict]:
        """List all conversations."""
        return [conv.to_dict() for conv in self.conversations.values()]
    
    async def transcribe(self, audio_path: str) -> str:
        """
        Transcribe audio file using Hypr-Whisper.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Check if Whisper server is running
                try:
                    async with session.get(f"{self.config.whisper_url}/") as resp:
                        if resp.status != 200:
                            raise Exception("Whisper server not responding")
                except aiohttp.ClientError:
                    raise Exception(f"Cannot connect to Whisper at {self.config.whisper_url}")
                
                # Send audio for transcription
                data = aiohttp.FormData()
                data.add_field('file', open(audio_path, 'rb'), 
                              filename=os.path.basename(audio_path))
                
                async with session.post(
                    f"{self.config.whisper_url}/transcribe",
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("text", result.get("transcription", ""))
                    else:
                        error = await resp.text()
                        raise Exception(f"Transcription failed: {error}")
                        
        except Exception as e:
            logger.error(f"Transcription error: {e}")
            raise
    
    async def speak(self, text: str) -> dict:
        """
        Convert text to speech using configured TTS provider.
        
        Args:
            text: Text to speak
            
        Returns:
            Dict with audio info
        """
        logger.info(f"[speak] Called with text len={len(text)}, TTS available={self.tts is not None}")
        if not self.tts:
            logger.warning("[speak] TTS not available, returning error")
            return {
                "success": False,
                "error": "TTS not available",
                "text": text,
            }
        
        try:
            start_time = time.time()
            logger.info(f"[speak] Calling TTS.speak() for text: '{text[:100]}...'")
            result = await self.tts.speak(text)
            duration_ms = int((time.time() - start_time) * 1000)
            
            audio_file = result.get("audio_file") or result.get("audio_path")
            logger.info(f"[speak] TTS returned in {duration_ms}ms, audio_file={audio_file}")
            
            return {
                "success": True,
                "text": text,
                "audio_file": audio_file,
                "voice_used": result.get("voice_used", self.config.tts_voice),
                "duration_ms": duration_ms,
                "provider": self.config.tts_provider,
            }
        except Exception as e:
            logger.error(f"[speak] TTS error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "text": text,
            }
    
    async def process_text(
        self, 
        text: str, 
        conversation_id: Optional[str] = None,
        speak_response: bool = True
    ) -> AsyncIterator[dict]:
        """
        Process a text query through the full pipeline.
        
        Args:
            text: User query text
            conversation_id: Optional conversation ID
            speak_response: Whether to speak the response via TTS
            
        Yields:
            Response chunks with status updates
        """
        # Get or create conversation
        conv = self.get_conversation(conversation_id)
        if not conv:
            conv = self.create_conversation()
        
        # Add user message
        user_msg = conv.add_message("user", text)
        
        yield {
            "type": "user_message",
            "message": user_msg.to_dict(),
            "conversation_id": conv.id,
        }
        
        # Process through orchestrator
        response_text = ""
        agent_type = None
        # Optional streaming Deepgram WebSocket session (for instant audio)
        dg_stream_cm = None
        dg_session = None
        dg_audio_data: Optional[bytes] = None
        dg_sample_rate = 48000
        streaming_tts_used = False
        if (
            speak_response
            and os.getenv("DEEPGRAM_API_KEY")
            and self.config.tts_provider.lower() == "deepgram"
        ):
            try:
                from ..services.voice.providers.deepgram.deepgram_ws_tts import (
                    StreamingTTSSession,
                )
                
                dg_sample_rate = getattr(self.tts.config, "sample_rate", 48000) if self.tts else 48000
                dg_model = os.getenv("HYPR_VOICE_TTS_MODEL", self.config.tts_voice)
                
                dg_stream_cm = StreamingTTSSession(
                    api_key=os.getenv("DEEPGRAM_API_KEY"),
                    model=dg_model,
                    sample_rate=dg_sample_rate,
                    auto_play=True,  # Auto-play audio as it streams
                )
                dg_session = await dg_stream_cm.__aenter__()
                streaming_tts_used = True
                
                yield {
                    "type": "tts_start",
                    "text": "(streaming) Deepgram WebSocket connected",
                    "provider": "deepgram",
                    "model": dg_model,
                }
            except Exception as e:
                logger.warning(f"Deepgram WebSocket TTS unavailable, falling back: {e}")
                dg_stream_cm = None
                dg_session = None
                streaming_tts_used = False
        
        async for chunk in self.orchestrator.process(text):
            yield {
                "type": "orchestrator_chunk",
                "chunk": chunk,
            }
            
            if chunk.get("type") == "text":
                content = chunk.get("content", "")
                response_text += content
                agent_type = chunk.get("agent")
                
                # Stream text to Deepgram WebSocket immediately
                if dg_session:
                    try:
                        await dg_session.send(content)
                    except Exception as e:
                        logger.warning(f"Failed to send chunk to Deepgram WS: {e}")
            elif chunk.get("type") == "route_decision":
                yield {
                    "type": "routing",
                    "agent": chunk.get("route"),
                    "confidence": chunk.get("confidence"),
                    "reasoning": chunk.get("reasoning"),
                }
        
        if not response_text:
            response_text = "I'm sorry, I couldn't generate a response."
        
        # Add assistant message
        assistant_msg = conv.add_message("assistant", response_text, agent_type=agent_type)
        
        yield {
            "type": "assistant_message",
            "message": assistant_msg.to_dict(),
            "conversation_id": conv.id,
        }
        
        # Speak response if requested
        if speak_response:
            if streaming_tts_used and dg_stream_cm:
                try:
                    await dg_stream_cm.__aexit__(None, None, None)
                    dg_audio_data = dg_stream_cm.get_all_audio()
                except Exception as e:
                    logger.warning(f"Deepgram streaming shutdown issue: {e}")
                    dg_audio_data = None
                
                audio_file = None
                duration_ms = None
                if dg_audio_data:
                    duration_ms = int(len(dg_audio_data) / 2 / dg_sample_rate * 1000)
                    if self.config.save_to_file:
                        output_dir = Path(self.config.output_dir or "./audio_output")
                        output_dir.mkdir(parents=True, exist_ok=True)
                        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
                        filename = f"deepgram_stream_{timestamp}.wav"
                        file_path = output_dir / filename
                        with open(file_path, "wb") as f:
                            f.write(dg_audio_data)
                        audio_file = str(file_path)
                        assistant_msg.audio_file = audio_file
                    assistant_msg.duration_ms = duration_ms
                
                yield {
                    "type": "tts_complete",
                    "result": {
                        "success": dg_audio_data is not None,
                        "audio_file": audio_file,
                        "duration_ms": duration_ms,
                        "provider": "deepgram",
                        "voice_used": self.config.tts_voice,
                        "sample_rate": dg_sample_rate,
                        "streaming": True,
                    },
                }
            elif self.tts:
                yield {
                    "type": "tts_start",
                    "text": response_text[:100] + "..." if len(response_text) > 100 else response_text,
                }
                
                tts_result = await self.speak(response_text)
                
                # Update message with audio info
                assistant_msg.audio_file = tts_result.get("audio_file")
                assistant_msg.duration_ms = tts_result.get("duration_ms")
                
                yield {
                    "type": "tts_complete",
                    "result": tts_result,
                }
        
        yield {
            "type": "complete",
            "conversation_id": conv.id,
            "response_text": response_text,
            "agent_type": agent_type,
        }
    
    async def process_audio(
        self,
        audio_path: str,
        conversation_id: Optional[str] = None,
        speak_response: bool = True
    ) -> AsyncIterator[dict]:
        """
        Process audio input through the full voice-to-voice pipeline.
        
        Args:
            audio_path: Path to audio file
            conversation_id: Optional conversation ID
            speak_response: Whether to speak the response
            
        Yields:
            Response chunks with status updates
        """
        yield {
            "type": "transcription_start",
            "audio_path": audio_path,
        }
        
        try:
            # Transcribe audio
            text = await self.transcribe(audio_path)
            
            yield {
                "type": "transcription_complete",
                "text": text,
            }
            
            # Process as text
            async for chunk in self.process_text(text, conversation_id, speak_response):
                yield chunk
                
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            yield {
                "type": "error",
                "error": str(e),
            }
    
    async def quick_response(self, text: str, speak: bool = True) -> dict:
        """
        Get a quick response without streaming.
        
        Args:
            text: User query
            speak: Whether to speak the response
            
        Returns:
            Complete response dict
        """
        logger.info(f"[quick_response] Starting: text='{text[:50]}...', speak={speak}")
        logger.info(f"[quick_response] TTS available: {self.tts is not None}, provider: {self.config.tts_provider}")
        
        result = {
            "input_text": text,
            "response_text": "",
            "agent_type": None,
            "audio_file": None,
            "conversation_id": None,
        }
        
        try:
            async for chunk in self.process_text(text, speak_response=speak):
                logger.debug(f"[quick_response] chunk type: {chunk.get('type')}")
                if chunk["type"] == "complete":
                    result["response_text"] = chunk["response_text"]
                    result["agent_type"] = chunk["agent_type"]
                    result["conversation_id"] = chunk["conversation_id"]
                    logger.info(f"[quick_response] Got response: agent={result['agent_type']}, len={len(result['response_text'])}")
                elif chunk["type"] == "tts_complete":
                    tts_result = chunk.get("result", {})
                    result["audio_file"] = tts_result.get("audio_file")
                    logger.info(f"[quick_response] TTS complete: success={tts_result.get('success')}, file={result['audio_file']}")
                elif chunk["type"] == "error":
                    logger.error(f"[quick_response] Error chunk: {chunk}")
        except Exception as e:
            logger.error(f"[quick_response] Exception: {e}", exc_info=True)
        
        logger.info(f"[quick_response] Returning: response_len={len(result['response_text'])}, audio={result['audio_file']}")
        return result
    
    def get_agent_types(self) -> list[dict]:
        """Get available agent types from the orchestrator."""
        return self.orchestrator.get_agent_types()
    
    async def process_text_streaming(
        self,
        text: str,
        conversation_id: Optional[str] = None,
        auto_play: bool = True
    ) -> AsyncIterator[dict]:
        """
        Process text with real-time streaming TTS via WebSocket.
        
        Audio playback begins as soon as the first LLM tokens arrive,
        providing near-instant voice response (<500ms to first audio).
        
        Args:
            text: User query text
            conversation_id: Optional conversation ID
            auto_play: Whether to auto-play audio (requires audio hardware)
            
        Yields:
            Streaming events including tokens and audio status
        """
        # Get or create conversation
        conv = self.get_conversation(conversation_id)
        if not conv:
            conv = self.create_conversation()
        
        # Add user message
        user_msg = conv.add_message("user", text)
        
        yield {
            "type": "user_message",
            "message": user_msg.to_dict(),
            "conversation_id": conv.id,
        }
        
        # Initialize Deepgram WebSocket TTS
        deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        if not deepgram_key:
            yield {"type": "error", "error": "DEEPGRAM_API_KEY not set"}
            return
        
        try:
            from ..services.voice.providers.deepgram.deepgram_ws_tts import (
                DeepgramWebSocketTTS, DeepgramWSConfig
            )
            from ..services.voice.audio_player import AudioPlayer
        except ImportError as e:
            logger.error(f"Failed to import streaming TTS: {e}")
            yield {"type": "error", "error": f"Streaming TTS not available: {e}"}
            return
        
        # Setup WebSocket TTS
        ws_config = DeepgramWSConfig(
            api_key=deepgram_key,
            model=os.getenv("HYPR_VOICE_TTS_MODEL", "aura-2-thalia-en"),
            sample_rate=48000,
        )
        
        # Audio player for real-time playback
        player = None
        if auto_play:
            try:
                player = AudioPlayer(sample_rate=48000)
                player.start()
            except Exception as e:
                logger.warning(f"Audio player not available: {e}")
                player = None
        
        # Audio callback
        all_audio = []
        def on_audio(chunk: bytes):
            all_audio.append(chunk)
            if player:
                player.play(chunk)
        
        tts = DeepgramWebSocketTTS(ws_config, on_audio=on_audio)
        
        yield {"type": "tts_connecting"}
        
        if not await tts.connect():
            yield {"type": "error", "error": "Failed to connect to Deepgram TTS"}
            return
        
        yield {"type": "tts_connected", "model": ws_config.model}
        
        # Process through orchestrator with streaming
        response_text = ""
        agent_type = None
        token_count = 0
        start_time = time.time()
        first_token_time = None
        
        try:
            async for event in self.orchestrator.process_streaming(text):
                event_type = event.get("type")
                
                if event_type == "route":
                    agent_type = event.get("agent_type")
                    yield {
                        "type": "routing",
                        "agent": agent_type,
                        "confidence": event.get("confidence"),
                        "reasoning": event.get("reasoning"),
                    }
                
                elif event_type == "token":
                    # Individual token from LLM
                    token = event.get("content", "")
                    if token:
                        if first_token_time is None:
                            first_token_time = time.time()
                            ttft_ms = int((first_token_time - start_time) * 1000)
                            yield {"type": "first_token", "ttft_ms": ttft_ms}
                        
                        response_text += token
                        token_count += 1
                        
                        # Strip markdown before sending to TTS
                        clean_token = strip_markdown_for_tts(token)
                        if clean_token:
                            await tts.send_text(clean_token)
                        
                        yield {
                            "type": "token",
                            "content": token,
                            "token_count": token_count,
                        }
                
                elif event_type == "text":
                    # Full response (for reference)
                    pass
                
                elif event_type == "error":
                    yield event
                    break
            
            # Flush remaining audio
            await tts.flush()
            yield {"type": "tts_flushed"}
            
            # Wait for audio to finish playing
            if player:
                await asyncio.sleep(0.5)  # Give time for final audio
                while player.queue_size > 0:
                    await asyncio.sleep(0.1)
            
        finally:
            # Cleanup
            await tts.close()
            if player:
                player.stop()
        
        # Calculate metrics
        total_time_ms = int((time.time() - start_time) * 1000)
        ttft_ms = int((first_token_time - start_time) * 1000) if first_token_time else None
        
        # Add assistant message
        assistant_msg = conv.add_message(
            "assistant", 
            response_text or "I'm sorry, I couldn't generate a response.",
            agent_type=agent_type
        )
        
        yield {
            "type": "complete",
            "conversation_id": conv.id,
            "response_text": response_text,
            "agent_type": agent_type,
            "token_count": token_count,
            "total_time_ms": total_time_ms,
            "time_to_first_token_ms": ttft_ms,
            "audio_chunks": len(all_audio),
        }
    
    async def shutdown(self):
        """Shutdown the voice orchestrator."""
        await self.orchestrator.shutdown()
        logger.info("Voice orchestrator shutdown complete")
