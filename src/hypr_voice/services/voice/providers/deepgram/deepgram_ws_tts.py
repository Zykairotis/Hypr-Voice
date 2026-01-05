#!/usr/bin/env python3
"""
Deepgram WebSocket TTS Provider

Enables real-time text-to-speech streaming via WebSocket connection.
Audio playback begins as soon as the first LLM tokens arrive, providing
near-instant voice response.

WebSocket endpoint: wss://api.deepgram.com/v1/speak
Protocol:
  - Send: {"type": "Speak", "text": "..."} for each text chunk
  - Send: {"type": "Flush"} when done
  - Receive: binary audio chunks (linear16 PCM)
"""

import asyncio
import json
import logging
import os
import threading
import queue
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_MODEL = "aura-2-thalia-en"
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_ENCODING = "linear16"
DEFAULT_PREBUFFER_MS = 1000  # wait for ~1.0s audio before starting playback to avoid underruns


@dataclass
class DeepgramWSConfig:
    """Configuration for Deepgram WebSocket TTS."""
    api_key: str
    model: str = DEFAULT_MODEL
    sample_rate: int = DEFAULT_SAMPLE_RATE
    encoding: str = DEFAULT_ENCODING


class DeepgramWebSocketTTS:
    """
    Deepgram WebSocket TTS client for real-time streaming.
    
    Usage:
        tts = DeepgramWebSocketTTS(config)
        await tts.connect()
        
        # As LLM tokens arrive:
        await tts.send_text("Hello, ")
        await tts.send_text("how are you?")
        
        # When done:
        await tts.flush()
        await tts.close()
    """
    
    def __init__(self, config: DeepgramWSConfig, on_audio: Optional[Callable[[bytes], None]] = None):
        """
        Initialize WebSocket TTS client.
        
        Args:
            config: Deepgram configuration
            on_audio: Callback function for audio chunks (called with bytes)
        """
        self.config = config
        self.on_audio_callback = on_audio
        self._ws = None
        self._receive_task = None
        self._audio_queue = queue.Queue()
        self._audio_chunks: list[bytes] = []
        self._flush_event = asyncio.Event()
        self._is_connected = False
        self._is_closing = False
        
    @property
    def ws_url(self) -> str:
        """Build WebSocket URL with parameters."""
        return (
            f"wss://api.deepgram.com/v1/speak"
            f"?model={self.config.model}"
            f"&encoding={self.config.encoding}"
            f"&sample_rate={self.config.sample_rate}"
        )
    
    async def connect(self) -> bool:
        """
        Open WebSocket connection to Deepgram TTS.
        
        Returns:
            True if connected successfully
        """
        try:
            import websockets
            
            headers = {
                "Authorization": f"Token {self.config.api_key}"
            }
            
            logger.info(f"Connecting to Deepgram TTS WebSocket: {self.config.model}")
            # Note: websockets >= 10.0 uses 'additional_headers' instead of 'extra_headers'
            self._ws = await websockets.connect(
                self.ws_url,
                additional_headers=headers,
                ping_interval=20,
                ping_timeout=10,
            )
            self._is_connected = True
            self._is_closing = False
            
            # Start receiver task
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            logger.info("Deepgram TTS WebSocket connected")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Deepgram TTS WebSocket: {e}")
            self._is_connected = False
            return False
    
    async def _receive_loop(self):
        """Background task to receive audio chunks from WebSocket."""
        try:
            async for message in self._ws:
                if self._is_closing:
                    break
                    
                if isinstance(message, bytes):
                    # Audio data received
                    self._audio_chunks.append(message)
                    self._audio_queue.put(message)
                    if self.on_audio_callback:
                        try:
                            self.on_audio_callback(message)
                        except Exception as e:
                            logger.error(f"Audio callback error: {e}")
                elif isinstance(message, str):
                    # Control message (JSON)
                    try:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        logger.debug(f"Deepgram control message: {msg_type}")
                        
                        if msg_type == "Flushed":
                            logger.debug("Deepgram: Flush completed")
                            self._flush_event.set()
                        elif msg_type == "Warning":
                            logger.warning(f"Deepgram warning: {data.get('warn_msg', 'unknown')}")
                        elif msg_type == "Error":
                            logger.error(f"Deepgram error: {data.get('err_msg', 'unknown')}")
                    except json.JSONDecodeError:
                        logger.debug(f"Deepgram text message: {message[:100]}")
                        
        except asyncio.CancelledError:
            logger.debug("Receive loop cancelled")
        except Exception as e:
            if not self._is_closing:
                logger.error(f"Receive loop error: {e}")
    
    async def send_text(self, text: str) -> bool:
        """
        Send text chunk to be converted to speech.
        
        Args:
            text: Text to convert (can be partial sentence)
            
        Returns:
            True if sent successfully
        """
        if not self._is_connected or not self._ws:
            logger.warning("Cannot send text: not connected")
            return False
            
        if not text or not text.strip():
            return True  # Skip empty text
            
        try:
            message = json.dumps({"type": "Speak", "text": text})
            await self._ws.send(message)
            logger.debug(f"Sent text chunk: {text[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to send text: {e}")
            return False
    
    async def flush(self, ack_timeout: Optional[float] = None) -> bool:
        """
        Signal end of text input. Deepgram will finish generating remaining audio.
        
        Returns:
            True if flush sent successfully
        """
        if not self._is_connected or not self._ws:
            logger.warning("Cannot flush: not connected")
            return False
            
        try:
            self._flush_event.clear()
            message = json.dumps({"type": "Flush"})
            await self._ws.send(message)
            logger.debug("Sent flush command")
            # Wait briefly for server confirmation so we don't close too early
            try:
                timeout = ack_timeout if ack_timeout is not None else float(os.getenv("HYPR_VOICE_TTS_FLUSH_TIMEOUT", "15"))
                await asyncio.wait_for(self._flush_event.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                logger.warning("Deepgram flush acknowledgement timed out; continuing shutdown")
            return True
        except Exception as e:
            logger.error(f"Failed to send flush: {e}")
            return False
    
    async def close(self):
        """Close WebSocket connection and cleanup."""
        self._is_closing = True
        self._is_connected = False
        
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        if self._ws:
            try:
                # Send close message
                await self._ws.send(json.dumps({"type": "Close"}))
                await self._ws.close()
            except Exception as e:
                logger.debug(f"Error during close: {e}")
            self._ws = None
            
        logger.info("Deepgram TTS WebSocket closed")
    
    def get_audio_chunk(self, timeout: float = 0.1) -> Optional[bytes]:
        """
        Get next audio chunk from queue (non-blocking).
        
        Args:
            timeout: Max time to wait for chunk
            
        Returns:
            Audio bytes or None if no data available
        """
        try:
            return self._audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_all_audio(self) -> bytes:
        """
        Get all accumulated audio data.
        
        Returns:
            Combined audio bytes
        """
        return b"".join(self._audio_chunks)

    def save_audio(self, output_dir: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Save accumulated audio to disk.
        
        Args:
            output_dir: Directory where audio will be saved
            filename: Optional filename; autogenerated if omitted
        
        Returns:
            Path to the saved file or None if no audio
        """
        audio_data = self.get_all_audio()
        if not audio_data:
            return None
        
        from pathlib import Path
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not filename:
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"deepgram_{self.config.model}_{timestamp}.wav"
        
        file_path = output_path / filename
        with open(file_path, "wb") as f:
            f.write(audio_data)
        
        logger.info(f"Saved Deepgram TTS audio to {file_path}")
        return str(file_path)

    def estimate_duration_ms(self) -> Optional[int]:
        """
        Estimate duration of generated audio using sample rate and 16-bit PCM.
        """
        audio_data = self.get_all_audio()
        if not audio_data:
            return None
        samples = len(audio_data) / 2  # 16-bit PCM => 2 bytes per sample
        duration_sec = samples / float(self.config.sample_rate)
        return int(duration_sec * 1000)
    
    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._is_connected and self._ws is not None


class StreamingTTSSession:
    """
    High-level session manager for streaming TTS with automatic playback.
    
    Usage:
        async with StreamingTTSSession(api_key) as session:
            async for token in llm_stream:
                await session.send(token)
    """
    
    def __init__(
        self, 
        api_key: str,
        model: str = DEFAULT_MODEL,
        sample_rate: int = DEFAULT_SAMPLE_RATE,
        auto_play: bool = True,
        prebuffer_ms: int = DEFAULT_PREBUFFER_MS,
    ):
        self.config = DeepgramWSConfig(
            api_key=api_key,
            model=model,
            sample_rate=sample_rate,
        )
        self.auto_play = auto_play
        self.prebuffer_ms = max(0, prebuffer_ms)
        self._tts = None
        self._player = None
        self._all_audio = []
        self._last_audio_time = None
        self._first_audio_time = None
        self._total_audio_bytes = 0
        self._pending_audio: list[bytes] = []
        self._pending_bytes: int = 0
        self._playback_started = False
        
    async def __aenter__(self):
        """Start session."""
        self._tts = DeepgramWebSocketTTS(
            self.config,
            on_audio=self._handle_audio
        )
        await self._tts.connect()
        
        if self.auto_play:
            self._start_player()
            
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End session."""
        import time
        
        if self._tts:
            # Flush and wait for tail audio before closing
            await self._tts.flush(ack_timeout=float(os.getenv("HYPR_VOICE_TTS_FLUSH_TIMEOUT", "60")))
            # Allow extra time for trailing audio to arrive even if ack is missing
            tail_wait = float(os.getenv("HYPR_VOICE_TTS_IDLE_TIMEOUT", "5.0"))
            if self._last_audio_time:
                # wait until no audio has arrived for tail_wait seconds
                while (time.time() - self._last_audio_time) < tail_wait:
                    await asyncio.sleep(0.1)
            else:
                # no audio yet; small pause to avoid immediate close
                await asyncio.sleep(0.5)
            await self._tts.close()
        
        # If we never hit the prebuffer threshold but did receive audio, play it now
        if self._player and not self._playback_started and self._pending_audio:
            for chunk in self._pending_audio:
                self._player.play(chunk)
            self._pending_audio = []
            self._pending_bytes = 0
            self._playback_started = True
        
        # Calculate remaining playback time
        # Audio was played in real-time as it streamed, so we only need to wait
        # for the audio that was received but not yet played
        if self._player and self._first_audio_time and self._last_audio_time:
            # Total audio duration (bytes / 2 bytes per sample / sample_rate)
            total_duration_sec = self._total_audio_bytes / 2 / self.config.sample_rate
            
            # Time elapsed since we started receiving audio
            elapsed_since_first = time.time() - self._first_audio_time
            
            # How much more time we need to wait
            remaining_time = total_duration_sec - elapsed_since_first + 1.0  # +1s buffer
            
            if remaining_time > 0:
                logger.info(f"[StreamingTTSSession] Audio: {self._total_audio_bytes} bytes ({total_duration_sec:.1f}s), "
                           f"elapsed: {elapsed_since_first:.1f}s, waiting: {remaining_time:.1f}s")
                await asyncio.sleep(remaining_time)
            else:
                logger.info(f"[StreamingTTSSession] Audio already finished (total: {total_duration_sec:.1f}s, elapsed: {elapsed_since_first:.1f}s)")
            
            logger.info(f"[StreamingTTSSession] Playback complete, stopping player")
            self._stop_player()
        elif self._player:
            # No audio received, just stop
            logger.info(f"[StreamingTTSSession] No audio received, stopping player")
            self._stop_player()
    
    def _handle_audio(self, audio_chunk: bytes):
        """Handle incoming audio chunk."""
        import time
        now = time.time()
        if self._first_audio_time is None:
            self._first_audio_time = now
        self._last_audio_time = now
        self._total_audio_bytes += len(audio_chunk)
        
        self._all_audio.append(audio_chunk)
        if self._player:
            # Buffer until we have enough audio to avoid PyAudio underruns, then start playback
            if not self._playback_started and self.prebuffer_ms > 0:
                self._pending_audio.append(audio_chunk)
                self._pending_bytes += len(audio_chunk)
                bytes_needed = int(self.config.sample_rate * 2 * (self.prebuffer_ms / 1000.0))
                if self._pending_bytes >= bytes_needed:
                    for chunk in self._pending_audio:
                        self._player.play(chunk)
                    self._pending_audio = []
                    self._pending_bytes = 0
                    self._playback_started = True
            else:
                self._playback_started = True
                self._player.play(audio_chunk)
    
    def _start_player(self):
        """Initialize audio player."""
        logger.info(f"[StreamingTTSSession] Starting audio player (auto_play={self.auto_play})")
        try:
            from hypr_voice.services.voice.audio_player import AudioPlayer
            self._player = AudioPlayer(sample_rate=self.config.sample_rate)
            started = self._player.start()
            logger.info(f"[StreamingTTSSession] AudioPlayer started: {started}, backend: {self._player._backend}")
        except ImportError as e:
            logger.error(f"[StreamingTTSSession] AudioPlayer import failed: {e}")
            self.auto_play = False
        except Exception as e:
            logger.error(f"[StreamingTTSSession] Failed to start audio player: {e}", exc_info=True)
            self.auto_play = False
    
    def _stop_player(self):
        """Stop audio player."""
        if self._player:
            try:
                # Wait for remaining audio to finish before stopping
                self._player.stop(wait=True, timeout=10.0)
                logger.info("[StreamingTTSSession] Audio player stopped")
            except Exception as e:
                logger.error(f"[StreamingTTSSession] Failed to stop audio player: {e}")
            self._player = None
    
    async def send(self, text: str):
        """Send text chunk to TTS."""
        if self._tts:
            await self._tts.send_text(text)
    
    def get_all_audio(self) -> bytes:
        """Get all audio generated in this session."""
        return b''.join(self._all_audio)
