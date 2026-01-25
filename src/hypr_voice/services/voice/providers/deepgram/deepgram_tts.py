#!/usr/bin/env python3
"""
Simple Deepgram TTS Provider
Focus on basic text-to-speech functionality using REST API with streaming
"""

import asyncio
import aiohttp
import logging
import subprocess
import tempfile
import os
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class DeepgramTTS:
    """Simple Deepgram TTS implementation using REST API with streaming support"""
    
    # Valid Deepgram Aura voices (use directly, no mapping needed)
    VALID_VOICES = {
        "aura-asteria-en", "aura-luna-en", "aura-stella-en", "aura-athena-en",
        "aura-hera-en", "aura-orion-en", "aura-arcas-en", "aura-perseus-en",
        "aura-angus-en", "aura-orpheus-en", "aura-helios-en", "aura-zeus-en"
    }
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.deepgram_api_key
        # Use production API endpoint
        self.api_url = "https://api.deepgram.com/v1/speak"
        
    async def generate(self, text: str, voice: str, model: Optional[str] = None,
                      speed: float = 1.0, pitch: float = 0.0, volume: float = 1.0,
                      use_streaming: bool = False, auto_play: bool = False) -> Dict[str, Any]:
        """
        Generate audio from text using Deepgram REST API with streaming
        
        Args:
            text: Text to convert
            voice: Voice name (e.g., "aura-luna-en")
            model: Model name (not used - included in voice)
            speed: Speech speed
            pitch: Voice pitch
            volume: Audio volume
            use_streaming: Enable HTTP streaming for faster response
            auto_play: Play audio while streaming (faster perceived latency)
            
        Returns:
            Dictionary with audio_data and metadata
        """
        logger.info(f"[DeepgramTTS.generate] text_len={len(text)}, voice={voice}, streaming={use_streaming}, auto_play={auto_play}")
        logger.info(f"[DeepgramTTS.generate] API key present: {bool(self.api_key)}")
        played_audio = False

        # Prefer non-streaming by default; only use HTTP streaming when explicitly requested
        if use_streaming and auto_play:
            result = await self._generate_streaming(text, voice)
            result["streaming"] = True
            return result

        # Non-streaming path (fetch full audio first)
        result = await self._generate_non_streaming(text, voice)
        result["streaming"] = False

        # Optional auto-play even in non-streaming mode
        if auto_play and result.get("audio_data"):
            try:
                # Play on a background thread to avoid blocking the event loop
                from hypr_voice.services.voice.audio_player import play_audio_blocking
                await asyncio.to_thread(
                    play_audio_blocking,
                    result["audio_data"],
                    result.get("sample_rate", self.config.sample_rate),
                )
                played_audio = True
            except Exception as e:
                logger.warning(f"[DeepgramTTS.generate] Auto-play failed, trying ffplay fallback: {e}")
                played_audio = await asyncio.to_thread(self._play_with_ffplay, result["audio_data"])

        result["played"] = played_audio
        return result
    
    async def _generate_streaming(self, text: str, voice: str) -> Dict[str, Any]:
        """Generate with HTTP streaming and real-time playback"""
        logger.info(f"[DeepgramTTS._generate_streaming] Starting - voice={voice}, text_len={len(text)}")
        # Use voice directly (validated voices work as model names)
        model_name = voice if voice in self.VALID_VOICES else "aura-asteria-en"
        logger.info(f"[DeepgramTTS._generate_streaming] Using model: {model_name}")
            
        # Build query parameters
        params = {
            "model": model_name,
            "encoding": "linear16",
            "sample_rate": "24000"  # 24kHz for lower latency
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.api_url}?{query_string}"
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Just send text in payload (model is in URL params)
        data = {"text": text}
        
        logger.info(f"[DeepgramTTS._generate_streaming] Calling Deepgram API: {url}")
        
        audio_chunks = []
        player_process = None
        start_time = time.time()
        first_byte_time = None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Deepgram API error: {response.status} - {error_text}")
                    
                    # Start ffplay process
                    # Let ffplay auto-detect format (Deepgram sends WAV with headers)
                    player_command = [
                        "ffplay",
                        "-autoexit",
                        "-nodisp",
                        "-loglevel", "error",  # Show errors but not info
                        "-"
                    ]
                    try:
                        logger.info("[DeepgramTTS._generate_streaming] Starting ffplay for audio playback...")
                        player_process = subprocess.Popen(
                            player_command,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE  # Capture stderr for debugging
                        )
                        logger.info(f"[DeepgramTTS._generate_streaming] ffplay started with PID: {player_process.pid}")
                    except FileNotFoundError:
                        logger.error("[DeepgramTTS._generate_streaming] ffplay not found! Install ffmpeg for audio playback")
                    
                    # Stream audio chunks
                    chunk_count = 0
                    async for chunk in response.content.iter_chunked(1024):
                        if chunk:
                            if first_byte_time is None:
                                first_byte_time = time.time()
                                ttfb = int((first_byte_time - start_time) * 1000)
                                logger.info(f"✅ Time to First Byte (TTFB): {ttfb}ms - Audio starting!")
                                # Check if it's WAV format (starts with RIFF)
                                if chunk[:4] == b'RIFF':
                                    logger.debug("Detected WAV format with headers")
                            
                            audio_chunks.append(chunk)
                            chunk_count += 1
                            
                            # Send to player if available
                            if player_process and player_process.stdin:
                                try:
                                    player_process.stdin.write(chunk)
                                    player_process.stdin.flush()
                                except (BrokenPipeError, IOError) as e:
                                    logger.debug(f"Player closed stdin: {e}")
                                    player_process = None  # Stop trying to write
                    
                    logger.debug(f"Streamed {chunk_count} chunks")
                    
                    # Close player stdin
                    if player_process and player_process.stdin:
                        try:
                            player_process.stdin.close()
                        except:
                            pass
                        player_process.wait()
                    
                    # Combine audio data
                    audio_data = b''.join(audio_chunks)
                    logger.info(f"[DeepgramTTS._generate_streaming] Received total {len(audio_data)} bytes in {chunk_count} chunks")
                    
                    # Check for ffplay errors
                    if player_process and player_process.stderr:
                        try:
                            stderr_output = player_process.stderr.read()
                            if stderr_output:
                                logger.warning(f"[DeepgramTTS._generate_streaming] ffplay stderr: {stderr_output.decode()}")
                        except:
                            pass
                    
                    logger.info(f"[DeepgramTTS._generate_streaming] Playback complete")
                    
                    return {
                        "audio_data": audio_data,
                        "format": "wav",
                        "sample_rate": 24000,
                        "duration": None
                    }
                    
        except Exception as e:
            logger.error(f"[DeepgramTTS._generate_streaming] FAILED: {e}", exc_info=True)
            if player_process:
                player_process.kill()
            raise
    
    async def _generate_non_streaming(self, text: str, voice: str) -> Dict[str, Any]:
        """Generate without streaming (wait for full audio)"""
        logger.info(f"[DeepgramTTS._generate_non_streaming] Starting - voice={voice}, text_len={len(text)}")
        # Use voice directly (validated voices work as model names)
        model_name = voice if voice in self.VALID_VOICES else "aura-asteria-en"
        logger.info(f"[DeepgramTTS._generate_non_streaming] Using model: {model_name}")
            
        params = {
            "model": model_name,
            "encoding": "linear16",
            "sample_rate": self.config.sample_rate
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.api_url}?{query_string}"
        
        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "audio/*",
            "Accept-Encoding": "identity",  # Disable compression to avoid encoding issues
        }
        
        # Just send text in payload (model is in URL params)
        data = {"text": text}
        
        logger.info(f"[DeepgramTTS._generate_non_streaming] Calling Deepgram API: {url}")
        
        try:
            # Disable auto decompress to handle raw audio response
            async with aiohttp.ClientSession(auto_decompress=False) as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        
                        if not audio_data:
                            raise Exception("No audio data received from Deepgram")
                        
                        logger.info(f"Received {len(audio_data)} bytes of audio from Deepgram")
                        
                        return {
                            "audio_data": audio_data,
                            "format": "wav",
                            "sample_rate": self.config.sample_rate,
                            "duration": None
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Deepgram API error details: status={response.status}, url={url}, error={error_text}")
                        raise Exception(f"Deepgram API error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Deepgram TTS failed: {e}")
            raise

    def _play_with_ffplay(self, audio_data: bytes) -> bool:
        """Best-effort playback of a WAV/PCM blob using ffplay."""
        player_command = [
            "ffplay",
            "-autoexit",
            "-nodisp",
            "-loglevel", "error",
            "-"
        ]
        try:
            proc = subprocess.Popen(
                player_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            if proc.stdin:
                proc.stdin.write(audio_data)
                proc.stdin.close()
            proc.wait(timeout=15)
            return True
        except Exception as e:
            logger.error(f"[DeepgramTTS._play_with_ffplay] Failed: {e}")
            return False
    
    async def close(self):
        """Cleanup (no persistent connection for Deepgram)"""
        pass
