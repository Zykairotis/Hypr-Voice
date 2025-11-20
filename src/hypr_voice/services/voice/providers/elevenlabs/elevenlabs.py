"""
ElevenLabs Text-to-Speech Service
Provides voice synthesis using ElevenLabs API
"""

import asyncio
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import tempfile
import hashlib

logger = logging.getLogger(__name__)

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs.play import play
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    logger.warning("ElevenLabs SDK not available. Install with: pip install elevenlabs")


@dataclass
class ElevenLabsVoice:
    """ElevenLabs voice configuration"""
    voice_id: str
    name: str
    category: Optional[str] = None
    labels: Dict[str, str] = field(default_factory=dict)
    settings: Dict[str, float] = field(default_factory=dict)
    
    @classmethod
    def from_name(cls, name: str) -> "ElevenLabsVoice":
        """Create voice from name (uses default voice IDs)"""
        voice_map = {
            # Default voices
            "rachel": "21m00Tcm4TlvDq8ikWAM",
            "adam": "pNInz6obpgDQGcFmaJgB",
            "antoni": "ErXwobaYiN019PkySvjV",
            "arnold": "VR6AewLTigWG4xSOukaG",
            "bella": "EXAVITQu4vr4xnSDxMaL",
            "domi": "AZnzlk1XvdvUeBnXmlld",
            "elli": "MF3mGyEYCl7XYWbV9V6O",
            "emily": "LcfcDJNUP1GQjkzn1xUU",
            "ethan": "g5CIjZEefAph4nQFvHAz",
            "fin": "D38z5RcWu1voky8WS1ja",
            "freya": "jsCqWAovK2LkecY7zXl4",
            "gigi": "jBpfuIE2acCO8z3wKNLl",
            "giovanni": "zcAOhNBS3c14rBihAFp1",
            "glinda": "z9fAnlkpzviPz146aGWa",
            "grace": "oWAxZDx7w5VEj9dCyTzz",
            "harry": "SOYHLrjzK2X1ezoPC6cr",
            "james": "ZQe5CZNOzWyzPSCn5a3c",
            "jeremy": "bVMeCyTHy58xNoL34h3p",
            "jessie": "t0jbNlBVZ17f02VDIeMI",
            "joseph": "Zlb1dXrM653N07WRdFW3",
            "josh": "TxGEqnHWrfWFTfGW9XjX",
            "liam": "TX3LPaxmHKxFdv7VOQHJ",
            "matilda": "XrExE9yKIg1WjnnlVkGX",
            "matthew": "Yko7PKHZNXotIFUBG7I9",
            "michael": "flq6f7yk4E4fJM5XTYuZ",
            "mimi": "zrHiDhphv9ZnVXBqCLjz",
            "nicole": "piTKgcLEGmPE4e6mEKli",
            "patrick": "ODq5zmih8GrVes37Dizd",
            "rachel": "21m00Tcm4TlvDq8ikWAM",
            "ryan": "wViXBPUzp2ZZixB1xQuM",
            "sam": "yoZ06aMxZJJ28mfd3POQ",
            "serena": "pMsXgVXv3BLzUgSXRplE",
            "thomas": "GBv7mTt0atIp3Br8iCZE",
        }
        
        voice_id = voice_map.get(name.lower(), "21m00Tcm4TlvDq8ikWAM")  # Default to Rachel
        return cls(voice_id=voice_id, name=name)


@dataclass
class ElevenLabsConfig:
    """Configuration for ElevenLabs TTS"""
    api_key: Optional[str] = None
    voice: str = "rachel"  # Default voice name
    model: str = "eleven_multilingual_v2"  # eleven_multilingual_v2, eleven_flash_v2_5, eleven_turbo_v2_5
    output_format: str = "mp3_44100_128"  # Output format
    stability: float = 0.5  # Voice stability (0-1)
    similarity_boost: float = 0.5  # Voice clarity (0-1)
    style: float = 0.0  # Style exaggeration (0-1)
    use_speaker_boost: bool = True
    cache_enabled: bool = True
    cache_dir: str = "/tmp/elevenlabs_cache"
    
    def __post_init__(self):
        # Get API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("ELEVENLABS_API_KEY")


class ElevenLabsTTS:
    """ElevenLabs Text-to-Speech service"""
    
    def __init__(self, config: Optional[ElevenLabsConfig] = None):
        """
        Initialize ElevenLabs TTS
        
        Args:
            config: ElevenLabs configuration
        """
        self.config = config or ElevenLabsConfig()
        self.client = None
        self.voice: Optional[ElevenLabsVoice] = None
        self.cache: Dict[str, str] = {}
        
        if not ELEVENLABS_AVAILABLE:
            raise ImportError("ElevenLabs SDK not available. Install with: pip install elevenlabs")
        
        if not self.config.api_key:
            logger.warning("No ElevenLabs API key provided. Set ELEVENLABS_API_KEY environment variable.")
        else:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ElevenLabs client"""
        try:
            self.client = ElevenLabs(api_key=self.config.api_key)
            self.voice = ElevenLabsVoice.from_name(self.config.voice)
            
            # Create cache directory if needed
            if self.config.cache_enabled:
                Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
            
            logger.info(f"ElevenLabs TTS initialized with voice: {self.config.voice}")
        except Exception as e:
            logger.error(f"Failed to initialize ElevenLabs client: {e}")
            self.client = None
    
    def _get_cache_key(self, text: str, voice: str, model: str) -> str:
        """Generate cache key for TTS request"""
        content = f"{text}:{voice}:{model}:{self.config.output_format}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def synthesize(self, 
                        text: str, 
                        output_path: Optional[str] = None,
                        voice: Optional[str] = None,
                        model: Optional[str] = None,
                        **kwargs) -> Optional[str]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            voice: Voice to use (overrides config)
            model: Model to use (overrides config)
            **kwargs: Additional parameters (stability, similarity_boost, style, etc.)
            
        Returns:
            Path to generated audio file or None on error
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return None
        
        try:
            # Use provided values or defaults
            voice = voice or self.config.voice
            model = model or self.config.model
            
            # Get voice configuration
            if voice != self.config.voice:
                voice_obj = ElevenLabsVoice.from_name(voice)
            else:
                voice_obj = self.voice
            
            # Check cache
            if self.config.cache_enabled:
                cache_key = self._get_cache_key(text, voice, model)
                cache_path = Path(self.config.cache_dir) / f"{cache_key}.mp3"
                
                if cache_path.exists():
                    logger.debug(f"Using cached audio: {cache_path}")
                    if output_path:
                        cache_path.rename(output_path)
                        return output_path
                    return str(cache_path)
            
            # Voice settings
            voice_settings = {
                "stability": kwargs.get("stability", self.config.stability),
                "similarity_boost": kwargs.get("similarity_boost", self.config.similarity_boost),
                "style": kwargs.get("style", self.config.style),
                "use_speaker_boost": kwargs.get("use_speaker_boost", self.config.use_speaker_boost)
            }
            
            # Generate audio
            audio = await asyncio.to_thread(
                self.client.text_to_speech.convert,
                text=text,
                voice_id=voice_obj.voice_id,
                model_id=model,
                output_format=self.config.output_format,
                voice_settings=voice_settings
            )
            
            # Save audio
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/elevenlabs_{timestamp}.mp3"
            
            output = Path(output_path)
            output.parent.mkdir(parents=True, exist_ok=True)
            
            # Write audio data
            with open(output, "wb") as f:
                for chunk in audio:
                    f.write(chunk)
            
            # Save to cache if enabled
            if self.config.cache_enabled:
                cache_path = Path(self.config.cache_dir) / f"{cache_key}.mp3"
                import shutil
                shutil.copy2(output, cache_path)
            
            logger.info(f"Generated speech: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to synthesize speech: {e}")
            return None
    
    async def synthesize_stream(self, 
                               text: str,
                               voice: Optional[str] = None,
                               model: Optional[str] = None,
                               **kwargs):
        """
        Stream synthesized speech
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            model: Model to use
            **kwargs: Additional parameters
            
        Yields:
            Audio chunks
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return
        
        try:
            voice = voice or self.config.voice
            model = model or self.config.model
            
            # Get voice configuration
            if voice != self.config.voice:
                voice_obj = ElevenLabsVoice.from_name(voice)
            else:
                voice_obj = self.voice
            
            # Voice settings
            voice_settings = {
                "stability": kwargs.get("stability", self.config.stability),
                "similarity_boost": kwargs.get("similarity_boost", self.config.similarity_boost),
                "style": kwargs.get("style", self.config.style),
                "use_speaker_boost": kwargs.get("use_speaker_boost", self.config.use_speaker_boost)
            }
            
            # Generate audio stream
            audio_stream = self.client.text_to_speech.convert_as_stream(
                text=text,
                voice_id=voice_obj.voice_id,
                model_id=model,
                output_format=self.config.output_format,
                voice_settings=voice_settings
            )
            
            async for chunk in audio_stream:
                yield chunk
                
        except Exception as e:
            logger.error(f"Failed to stream speech: {e}")
    
    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get available voices
        
        Returns:
            List of voice information
        """
        if not self.client:
            return []
        
        try:
            voices = await asyncio.to_thread(
                self.client.voices.get_all
            )
            
            return [
                {
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": voice.category,
                    "labels": voice.labels,
                    "preview_url": voice.preview_url
                }
                for voice in voices.voices
            ]
        except Exception as e:
            logger.error(f"Failed to get voices: {e}")
            return []
    
    async def clone_voice(self,
                         name: str,
                         audio_files: List[str],
                         description: Optional[str] = None) -> Optional[str]:
        """
        Clone a voice from audio samples
        
        Args:
            name: Name for the cloned voice
            audio_files: List of audio file paths
            description: Voice description
            
        Returns:
            Voice ID or None on error
        """
        if not self.client:
            logger.error("ElevenLabs client not initialized")
            return None
        
        try:
            # Read audio files
            files = []
            for path in audio_files:
                with open(path, "rb") as f:
                    files.append(f.read())
            
            # Clone voice
            voice = await asyncio.to_thread(
                self.client.clone,
                name=name,
                description=description,
                files=files
            )
            
            logger.info(f"Cloned voice: {name} with ID: {voice.voice_id}")
            return voice.voice_id
            
        except Exception as e:
            logger.error(f"Failed to clone voice: {e}")
            return None
    
    async def delete_voice(self, voice_id: str) -> bool:
        """
        Delete a custom voice
        
        Args:
            voice_id: Voice ID to delete
            
        Returns:
            True on success
        """
        if not self.client:
            return False
        
        try:
            await asyncio.to_thread(
                self.client.voices.delete,
                voice_id=voice_id
            )
            logger.info(f"Deleted voice: {voice_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete voice: {e}")
            return False
