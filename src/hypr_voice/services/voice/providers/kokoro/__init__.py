"""
Simple Kokoro TTS Provider
Local text-to-speech without streaming complexity
"""

from .kokoro_tts import KokoroTTS

# Simple voice list function
def list_available_voices():
    """List available Kokoro voices"""
    return [
        "af_bella", "af_sarah", "af_sky", "af_nicole", "af_heart", "af_valley",
        "am_adam", "am_michael", "am_chris",
        "bf_emma", "bf_isabella", 
        "bm_george", "bm_lewis",
        "af_child", "am_child", "crob_1"
    ]

__all__ = [
    'KokoroTTS',
    'list_available_voices'
]

__version__ = "3.0.0"
