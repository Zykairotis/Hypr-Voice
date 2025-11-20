#!/usr/bin/env python3
"""
Simple Kokoro TTS Provider
Focus on basic text-to-speech functionality
Using synchronous requests with streaming support
"""

import requests
import logging
import subprocess
import tempfile
import os
import time
from typing import Dict, Any, Optional
from io import BytesIO

logger = logging.getLogger(__name__)


class KokoroTTS:
    """Simple Kokoro TTS implementation using requests with streaming support"""
    
    def __init__(self, config):
        self.config = config
        self.api_url = config.kokoro_url
    
    def generate(self, text: str, voice: str, model: Optional[str] = None,
                 speed: float = 1.0, pitch: float = 0.0, volume: float = 1.0,
                 use_streaming: bool = True, auto_play: bool = False) -> Dict[str, Any]:
        """
        Generate audio from text with optional streaming
        
        Args:
            text: Text to convert
            voice: Voice name
            model: Not used for Kokoro
            speed: Speech speed
            pitch: Voice pitch  
            volume: Audio volume
            use_streaming: Enable streaming mode for faster response
            auto_play: Play audio while streaming (faster perceived latency)
            
        Returns:
            Dictionary with audio_data and metadata
        """
        # Build request payload
        payload = {
            "model": "kokoro",
            "input": text,
            "voice": voice,
            "response_format": self.config.output_format,
            "speed": speed,
            "stream": use_streaming  # Enable streaming
        }
        
        # Add volume if not default
        if volume != 1.0:
            payload["volume_multiplier"] = volume
        
        # Make request (synchronous with streaming)
        endpoint = f"{self.api_url}/v1/audio/speech"
        logger.debug(f"Making request to {endpoint} with voice={voice}, speed={speed}, streaming={use_streaming}")
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                timeout=120,  # Longer timeout for streaming
                stream=use_streaming  # Stream response
            )
            
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                if use_streaming and auto_play:
                    # Stream audio chunks and play in real-time
                    audio_data = self._stream_and_play(response)
                else:
                    # Collect all audio data
                    audio_data = response.content
                
                logger.info(f"Received {len(audio_data)} bytes of audio data")
                
                if not audio_data:
                    raise Exception("Received empty audio data from Kokoro API")
                
                return {
                    "audio_data": audio_data,
                    "format": self.config.output_format,
                    "sample_rate": 24000,  # Kokoro uses 24kHz
                    "duration": None
                }
            else:
                raise Exception(f"Kokoro API error: {response.status_code} - {response.text}")
                
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to Kokoro server at {self.api_url}")
        except requests.exceptions.Timeout:
            raise Exception(f"Request timed out")
    
    def _stream_and_play(self, response) -> bytes:
        """Stream audio chunks and play in real-time"""
        # Create temp file for streaming playback
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
            
            # Start audio player process
            player_process = None
            audio_chunks = []
            chunk_size = 0
            
            try:
                # Wake up audio device
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
                
                # Stream chunks
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        audio_chunks.append(chunk)
                        chunk_size += len(chunk)
                        temp_file.write(chunk)
                        temp_file.flush()
                        
                        # Start player after first few chunks
                        if player_process is None and chunk_size > 16384:  # ~16KB
                            logger.info(f"Starting playback after {chunk_size} bytes...")
                            # Try to start player
                            players = [
                                ["ffplay", "-nodisp", "-autoexit", "-hide_banner", "-loglevel", "quiet", temp_path],
                                ["mpv", "--no-video", temp_path],
                            ]
                            
                            for player_cmd in players:
                                try:
                                    player_process = subprocess.Popen(
                                        player_cmd,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL
                                    )
                                    logger.info("✅ Audio started playing while generating...")
                                    break
                                except FileNotFoundError:
                                    continue
                
                # Wait for player to finish
                if player_process:
                    player_process.wait()
                
                # Return all collected audio data
                return b''.join(audio_chunks)
                
            finally:
                # Clean up temp file
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def close(self):
        """Cleanup (no persistent connection needed)"""
        pass

    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
