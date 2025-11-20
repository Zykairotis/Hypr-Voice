"""
Simple Deepgram TTS Provider
Cloud text-to-speech without streaming complexity
"""

from .deepgram_tts import DeepgramTTS

# Simple voice and model list functions
def list_available_voices():
    """List available Deepgram voices"""
    return [
        "luna", "athena", "asteria", "aurora", "hera", "thalia", "andromeda", "helena",
        "apollo", "atlas", "hermes", "draco", "aries", "arcas", "amalthea"
    ]

def list_available_models():
    """List available Deepgram models"""
    return ["aura-2", "aura-1"]

__all__ = [
    'DeepgramTTS',
    'list_available_voices', 
    'list_available_models'
]

__version__ = "3.0.0"
