#!/usr/bin/env python3
"""
Simple ElevenLabs TTS Provider
Focus on basic text-to-speech functionality
"""

import aiohttp
import asyncio
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ElevenLabsTTS:
    """Simple ElevenLabs TTS implementation"""
    
    # Voice name to ID mapping
    VOICE_IDS = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",
        "sarah": "EXAVITQu4vr4xnSDxMaL",
        "adam": "pNInz6obpgDQGcFmaJgB",
        "antoni": "ErXwobaYiN019PkySvjV",
        "arnold": "VR6AewLTigWG4xSOukaG",
        "emily": "LcfcDJNUP1GQjkzn1xUU",
        "lily": "pFZP5JQG7iQjIQuC4Bku",
        "jessica": "cgSgspJ2msm6clMCkdW9",
        "bill": "pqHfZKP75CvOlQylNhV4",
        "brian": "nPczCjzI2devNBz1zQrb",
        "callum": "N2lVS1w4EtoT3dr4eOWO",
        "charlie": "IKne3meq5aSn9XLyUdCD",
        "daniel": "onwK4e9ZLuTAKqWW03F9",
        "freya": "jsCqWAovK2LkecY7zXl4",
        "alice": "Xb7hH8MSUJpSbSDYk0k2",
        "charlotte": "XB0fDUnXU5powFXDhCwa",
    }
    
    def __init__(self, config):
        self.config = config
        self.api_key = config.elevenlabs_api_key
        self.session = None
        
    async def _ensure_session(self):
        """Ensure aiohttp session exists"""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    def _get_voice_id(self, voice_name: str) -> str:
        """Get voice ID from name"""
        # If it looks like an ID already, return it
        if len(voice_name) == 20 and not voice_name.replace("_", "").replace("-", "").isalpha():
            return voice_name
        
        # Look up voice ID
        voice_id = self.VOICE_IDS.get(voice_name.lower())
        if not voice_id:
            # Default to rachel if unknown
            logger.warning(f"Unknown voice '{voice_name}', using 'rachel'")
            voice_id = self.VOICE_IDS["rachel"]
        
        return voice_id
    
    async def generate(self, text: str, voice: str, model: Optional[str] = None,
                      speed: float = 1.0, pitch: float = 0.0, volume: float = 1.0) -> Dict[str, Any]:
        """
        Generate audio from text using ElevenLabs
        
        Args:
            text: Text to convert
            voice: Voice name or ID
            model: Model ID (e.g., "eleven_turbo_v2_5")
            speed: Speech speed (not directly supported, will adjust with voice settings)
            pitch: Voice pitch (not directly supported)
            volume: Audio volume (not directly supported)
            
        Returns:
            Dictionary with audio_data and metadata
        """
        await self._ensure_session()
        
        # Get voice ID
        voice_id = self._get_voice_id(voice)
        
        # Use default model if not specified
        if not model:
            model = "eleven_turbo_v2_5"
        
        # Build API endpoint
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        # Headers
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        # Request body
        body = {
            "text": text,
            "model_id": model,
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        # Adjust voice settings based on speed (approximation)
        if speed > 1.2:
            body["voice_settings"]["stability"] = 0.3
        elif speed < 0.8:
            body["voice_settings"]["stability"] = 0.7
        
        try:
            # Make request
            async with self.session.post(url, json=body, headers=headers) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    
                    return {
                        "audio_data": audio_data,
                        "format": "mp3",
                        "sample_rate": 44100,  # ElevenLabs default
                        "duration": None
                    }
                else:
                    error = await response.text()
                    raise Exception(f"ElevenLabs API error: {response.status} - {error}")
                    
        except Exception as e:
            logger.error(f"ElevenLabs TTS failed: {e}")
            raise
    
    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None
    
    async def __aenter__(self):
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
