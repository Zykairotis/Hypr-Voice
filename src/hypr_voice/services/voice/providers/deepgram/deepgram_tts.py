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
    
    # Voice mapping for beta API (working model from your example)
    BETA_VOICE_MAP = {
        "aura-luna-en": "alpha-stella-en-v2",    # Use working model for all
        "aura-athena-en": "alpha-stella-en-v2", 
        "aura-asteria-en": "alpha-stella-en-v2",
        "aura-apollo-en": "alpha-stella-en-v2",
        "aura-atlas-en": "alpha-stella-en-v2",
        "aura-hermes-en": "alpha-stella-en-v2",
        "aura-aurora-en": "alpha-stella-en-v2",
        "aura-hera-en": "alpha-stella-en-v2"
    }
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.deepgram_api_key
        # Try beta endpoint first (works with older keys), fallback to production
        self.api_url = "https://api.beta.deepgram.com/v1/speak"
        self.use_beta = True
        
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
        if use_streaming and auto_play:
            return await self._generate_streaming(text, voice)
        else:
            return await self._generate_non_streaming(text, voice)
    
    async def _generate_streaming(self, text: str, voice: str) -> Dict[str, Any]:
        """Generate with HTTP streaming and real-time playback"""
        # Map voice name if using beta API
        if self.use_beta and voice in self.BETA_VOICE_MAP:
            model_name = self.BETA_VOICE_MAP[voice]
        else:
            model_name = voice
            
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
        
        logger.info(f"Streaming TTS from Deepgram...")
        
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
                        player_process = subprocess.Popen(
                            player_command,
                            stdin=subprocess.PIPE,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                        logger.debug("Started ffplay for streaming playback")
                    except FileNotFoundError:
                        logger.warning("ffplay not found, collecting audio without playback")
                    
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
                    logger.info(f"Received total {len(audio_data)} bytes")
                    
                    return {
                        "audio_data": audio_data,
                        "format": "wav",
                        "sample_rate": 24000,
                        "duration": None
                    }
                    
        except Exception as e:
            logger.error(f"Streaming TTS failed: {e}")
            if player_process:
                player_process.kill()
            raise
    
    async def _generate_non_streaming(self, text: str, voice: str) -> Dict[str, Any]:
        """Generate without streaming (wait for full audio)"""
        # Map voice name if using beta API
        if self.use_beta and voice in self.BETA_VOICE_MAP:
            model_name = self.BETA_VOICE_MAP[voice]
        else:
            model_name = voice
            
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
            "Accept": "audio/*"
        }
        
        # Just send text in payload (model is in URL params)
        data = {"text": text}
        
        logger.debug(f"Making REST API request to Deepgram TTS: {url}")
        
        try:
            async with aiohttp.ClientSession() as session:
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
                        raise Exception(f"Deepgram API error: {response.status} - {error_text}")
                        
        except Exception as e:
            logger.error(f"Deepgram TTS failed: {e}")
            raise
    
    async def close(self):
        """Cleanup (no persistent connection for Deepgram)"""
        pass
