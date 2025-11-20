"""
Simplified Universal TTS System
Clean, simple text-to-speech for multiple providers
No LLM streaming - just pure TTS functionality
"""

# Main TTS Manager
from .tts_manager import (
    UniversalTTS,
    TTSConfig,
    TTSProvider,
    VoiceLibrary,
    text_to_speech,
    list_all_voices,
    list_all_models
)

# Export main classes
__all__ = [
    # Main classes
    'UniversalTTS',
    'TTSConfig',
    'TTSProvider',
    'VoiceLibrary',
    
    # Convenience functions
    'text_to_speech',
    'list_all_voices',
    'list_all_models',
]

# Version
__version__ = '3.0.0'  # Simplified version

def quick_tts(text: str, provider: str = "kokoro") -> None:
    """
    Super simple synchronous TTS for quick testing
    
    Args:
        text: Text to speak
        provider: Provider name (kokoro, deepgram, elevenlabs)
    """
    import asyncio
    
    async def _speak():
        result = await text_to_speech(text, provider=provider)
        if result['success']:
            print(f"✅ TTS successful! Voice: {result['voice_used']}")
            if result.get('audio_file'):
                print(f"   Audio saved to: {result['audio_file']}")
        else:
            print(f"❌ TTS failed: {result.get('error')}")
    
    asyncio.run(_speak())
