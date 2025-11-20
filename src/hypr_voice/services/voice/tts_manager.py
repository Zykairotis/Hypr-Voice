#!/usr/bin/env python3
"""
Universal Text-to-Speech Manager
Simple, clean interface for TTS across multiple providers
"""

import os
import random
import asyncio
import logging
from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

logger = logging.getLogger(__name__)


class TTSProvider(Enum):
    """Available TTS providers"""
    KOKORO = "kokoro"
    DEEPGRAM = "deepgram"
    ELEVENLABS = "elevenlabs"


@dataclass
class TTSConfig:
    """Configuration for TTS"""
    # Provider settings
    provider: TTSProvider = TTSProvider.KOKORO
    
    # Voice settings
    voice: Optional[str] = None  # None = use random voice
    model: Optional[str] = None  # Provider-specific model
    
    # Audio parameters
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    sample_rate: int = 48000
    output_format: str = "mp3"
    
    # Random voice settings
    use_random_voice: bool = False
    voice_gender: Optional[str] = None  # "male", "female", or None for any
    voice_accent: Optional[str] = None  # "american", "british", etc.
    
    # API settings
    kokoro_url: str = "http://localhost:8880"
    deepgram_api_key: Optional[str] = None
    elevenlabs_api_key: Optional[str] = None
    
    # Output settings
    save_to_file: bool = True
    output_dir: str = "./audio_output"
    filename: Optional[str] = None  # Auto-generate if None
    
    # Streaming settings
    use_streaming: bool = True  # Enable streaming mode for faster response
    stream_and_play: bool = False  # Play while streaming (fastest perceived latency)
    
    def __post_init__(self):
        """Load API keys from environment if not provided"""
        if not self.deepgram_api_key:
            self.deepgram_api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.elevenlabs_api_key:
            self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")


class VoiceLibrary:
    """Voice definitions for all providers"""
    
    KOKORO_VOICES = {
        "female": ["af_bella", "af_sarah", "af_sky", "af_nicole", "af_heart", "af_nova"],
        "male": ["am_adam", "am_michael", "am_echo"],
        "british_female": ["bf_emma", "bf_alice"],
        "british_male": ["bm_george", "bm_lewis"],
        "child": ["ef_dora", "em_alex"],
        "special": ["am_santa", "pm_santa"]
    }
    
    DEEPGRAM_VOICES = {
        "female": ["luna", "athena", "asteria", "aurora", "hera", "thalia", "andromeda", "helena"],
        "male": ["apollo", "atlas", "hermes", "draco", "aries", "arcas", "amalthea"],
        "all": ["luna", "athena", "apollo", "atlas", "hermes", "asteria", "aurora", 
                 "hera", "thalia", "andromeda", "helena", "draco", "aries", "arcas", "amalthea"]
    }
    
    ELEVENLABS_VOICES = {
        "female": ["rachel", "sarah", "emily", "lily", "jessica", "freya", "alice", "charlotte"],
        "male": ["adam", "antoni", "arnold", "bill", "brian", "callum", "charlie", "daniel"],
        "all": ["rachel", "sarah", "adam", "antoni", "emily", "lily", "jessica", "arnold",
                "bill", "brian", "callum", "charlie", "daniel", "freya", "alice", "charlotte"]
    }
    
    DEEPGRAM_MODELS = ["aura-2", "aura-1"]
    
    ELEVENLABS_MODELS = [
        "eleven_turbo_v2_5",
        "eleven_flash_v2_5", 
        "eleven_multilingual_v2",
        "eleven_flash_v2",
        "eleven_turbo_v2"
    ]
    
    @classmethod
    def get_random_voice(cls, provider: TTSProvider, gender: Optional[str] = None, 
                        accent: Optional[str] = None) -> str:
        """Get a random voice based on criteria"""
        if provider == TTSProvider.KOKORO:
            if gender == "male":
                voices = cls.KOKORO_VOICES["male"]
                if accent == "british":
                    voices = cls.KOKORO_VOICES["british_male"]
            elif gender == "female":
                voices = cls.KOKORO_VOICES["female"]
                if accent == "british":
                    voices = cls.KOKORO_VOICES["british_female"]
            else:
                # All voices
                voices = (cls.KOKORO_VOICES["female"] + cls.KOKORO_VOICES["male"] +
                         cls.KOKORO_VOICES["british_female"] + cls.KOKORO_VOICES["british_male"])
                         
        elif provider == TTSProvider.DEEPGRAM:
            if gender == "male":
                voices = cls.DEEPGRAM_VOICES["male"]
            elif gender == "female":
                voices = cls.DEEPGRAM_VOICES["female"]
            else:
                voices = cls.DEEPGRAM_VOICES["all"]
                
        elif provider == TTSProvider.ELEVENLABS:
            if gender == "male":
                voices = cls.ELEVENLABS_VOICES["male"]
            elif gender == "female":
                voices = cls.ELEVENLABS_VOICES["female"]
            else:
                voices = cls.ELEVENLABS_VOICES["all"]
        else:
            voices = ["default"]
        
        return random.choice(voices)
    
    @classmethod
    def get_default_model(cls, provider: TTSProvider) -> Optional[str]:
        """Get default model for a provider"""
        if provider == TTSProvider.DEEPGRAM:
            return None  # Deepgram TTS doesn't use separate model parameter
        elif provider == TTSProvider.ELEVENLABS:
            return cls.ELEVENLABS_MODELS[0]  # eleven_turbo_v2_5
        return None


class UniversalTTS:
    """Universal TTS Manager - Simple interface for all providers"""
    
    def __init__(self, config: Optional[TTSConfig] = None):
        """Initialize TTS manager"""
        self.config = config or TTSConfig()
        self._provider_instance = None
        self._initialize_provider()
        
    def _initialize_provider(self):
        """Initialize the selected provider"""
        provider = self.config.provider
        
        if provider == TTSProvider.KOKORO:
            from .providers.kokoro.kokoro_tts import KokoroTTS
            self._provider_instance = KokoroTTS(self.config)
            
        elif provider == TTSProvider.DEEPGRAM:
            if not self.config.deepgram_api_key:
                raise ValueError("Deepgram API key not configured")
            # Use REST API with HTTP streaming support
            from .providers.deepgram.deepgram_tts import DeepgramTTS
            self._provider_instance = DeepgramTTS(self.config)
            
        elif provider == TTSProvider.ELEVENLABS:
            if not self.config.elevenlabs_api_key:
                raise ValueError("ElevenLabs API key required. Set ELEVENLABS_API_KEY environment variable.")
            from .providers.elevenlabs.elevenlabs_tts import ElevenLabsTTS
            self._provider_instance = ElevenLabsTTS(self.config)
            
    def _select_voice(self) -> str:
        """Select voice based on configuration"""
        if self.config.use_random_voice or self.config.voice is None:
            voice = VoiceLibrary.get_random_voice(
                self.config.provider,
                self.config.voice_gender,
                self.config.voice_accent
            )
            logger.info(f"Selected random voice: {voice}")
            return voice
        return self.config.voice
    
    def _select_model(self) -> Optional[str]:
        """Select model based on configuration"""
        if self.config.model is None:
            return VoiceLibrary.get_default_model(self.config.provider)
        return self.config.model
        
    async def speak(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            **kwargs: Override config settings for this request
            
        Returns:
            Dictionary with:
                - success: bool
                - audio_file: str (path to audio file if saved)
                - audio_data: bytes (raw audio data)
                - voice_used: str (voice that was used)
                - model_used: str (model that was used)
                - provider: str (provider name)
                - duration: float (audio duration in seconds)
        """
        # Override config with kwargs
        voice = kwargs.get('voice', self._select_voice())
        model = kwargs.get('model', self._select_model())
        speed = kwargs.get('speed', self.config.speed)
        pitch = kwargs.get('pitch', self.config.pitch)
        volume = kwargs.get('volume', self.config.volume)
        
        # Log the request
        logger.info(f"TTS Request: provider={self.config.provider.value}, voice={voice}, model={model}")
        logger.debug(f"Text (first 100 chars): {text[:100]}...")
        
        try:
            # Call provider-specific TTS
            # Handle both sync and async providers
            generate_method = self._provider_instance.generate
            
            # Prepare arguments
            generate_args = {
                'text': text,
                'voice': voice,
                'model': model,
                'speed': speed,
                'pitch': pitch,
                'volume': volume
            }
            
            # Add streaming args for Kokoro and Deepgram
            if self.config.provider in [TTSProvider.KOKORO, TTSProvider.DEEPGRAM]:
                generate_args['use_streaming'] = self.config.use_streaming
                generate_args['auto_play'] = self.config.stream_and_play
            
            if asyncio.iscoroutinefunction(generate_method):
                # Async provider
                result = await generate_method(**generate_args)
            else:
                # Sync provider (like Kokoro with requests)
                result = await asyncio.to_thread(generate_method, **generate_args)
            
            # Save to file if configured
            audio_file = None
            if self.config.save_to_file and result.get('audio_data'):
                audio_format = result.get('format', 'mp3')
                audio_file = await self._save_audio(
                    result['audio_data'],
                    voice,
                    self.config.provider.value,
                    audio_format
                )
                result['audio_file'] = audio_file
            
            # Add metadata
            result.update({
                'success': True,
                'voice_used': voice,
                'model_used': model,
                'provider': self.config.provider.value
            })
            
            return result
            
        except Exception as e:
            import traceback
            error_msg = str(e) if str(e) else f"{type(e).__name__}: {repr(e)}"
            logger.error(f"TTS generation failed: {error_msg}")
            logger.debug(f"Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': error_msg,
                'provider': self.config.provider.value,
                'traceback': traceback.format_exc()
            }
        finally:
            # Clean up provider resources
            if hasattr(self._provider_instance, 'close'):
                try:
                    close_method = self._provider_instance.close
                    if asyncio.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()
                except Exception as cleanup_error:
                    logger.warning(f"Error during cleanup: {cleanup_error}")
    
    async def _save_audio(self, audio_data: bytes, voice: str, provider: str, audio_format: str = "mp3") -> str:
        """Save audio data to file"""
        # Create output directory
        output_dir = Path(self.config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        if self.config.filename:
            filename = self.config.filename
        else:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{provider}_{voice}_{timestamp}.{audio_format}"
        
        # Save file
        filepath = output_dir / filename
        with open(filepath, 'wb') as f:
            f.write(audio_data)
        
        logger.info(f"Audio saved to: {filepath}")
        return str(filepath)
    
    def list_voices(self) -> List[str]:
        """List available voices for current provider"""
        provider = self.config.provider
        
        if provider == TTSProvider.KOKORO:
            voices = (VoiceLibrary.KOKORO_VOICES["female"] + 
                     VoiceLibrary.KOKORO_VOICES["male"] +
                     VoiceLibrary.KOKORO_VOICES["british_female"] +
                     VoiceLibrary.KOKORO_VOICES["british_male"])
        elif provider == TTSProvider.DEEPGRAM:
            voices = VoiceLibrary.DEEPGRAM_VOICES["all"]
        elif provider == TTSProvider.ELEVENLABS:
            voices = VoiceLibrary.ELEVENLABS_VOICES["all"]
        else:
            voices = []
        
        return voices
    
    def list_models(self) -> List[str]:
        """List available models for current provider"""
        provider = self.config.provider
        
        if provider == TTSProvider.DEEPGRAM:
            return VoiceLibrary.DEEPGRAM_MODELS
        elif provider == TTSProvider.ELEVENLABS:
            return VoiceLibrary.ELEVENLABS_MODELS
        else:
            return []
    
    @staticmethod
    def list_providers() -> List[str]:
        """List all available providers"""
        return [p.value for p in TTSProvider]


# Convenience functions
async def text_to_speech(
    text: str,
    provider: Union[str, TTSProvider] = TTSProvider.KOKORO,
    voice: Optional[str] = None,
    model: Optional[str] = None,
    use_random_voice: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Simple function to convert text to speech
    
    Args:
        text: Text to convert
        provider: TTS provider to use
        voice: Voice to use (or None for random)
        model: Model to use (or None for default)
        use_random_voice: Use random voice
        **kwargs: Additional parameters
        
    Returns:
        Result dictionary with audio data and metadata
    """
    # Convert string to enum if needed
    if isinstance(provider, str):
        provider = TTSProvider(provider)
    
    # Create config
    config = TTSConfig(
        provider=provider,
        voice=voice,
        model=model,
        use_random_voice=use_random_voice,
        **kwargs
    )
    
    # Create TTS instance and generate
    tts = UniversalTTS(config)
    return await tts.speak(text)


def list_all_voices() -> Dict[str, List[str]]:
    """List all voices for all providers"""
    return {
        "kokoro": VoiceLibrary.KOKORO_VOICES,
        "deepgram": VoiceLibrary.DEEPGRAM_VOICES,
        "elevenlabs": VoiceLibrary.ELEVENLABS_VOICES
    }


def list_all_models() -> Dict[str, List[str]]:
    """List all models for all providers"""
    return {
        "deepgram": VoiceLibrary.DEEPGRAM_MODELS,
        "elevenlabs": VoiceLibrary.ELEVENLABS_MODELS
    }
