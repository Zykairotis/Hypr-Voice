"""
Simple ElevenLabs TTS Provider
Premium cloud text-to-speech without streaming complexity
"""

from .elevenlabs_tts import ElevenLabsTTS

# Simple voice and model list functions
def list_available_voices():
    """List available ElevenLabs voices"""
    return [
        "rachel", "sarah", "emily", "lily", "jessica", "freya", "alice", "charlotte",
        "adam", "antoni", "arnold", "bill", "brian", "callum", "charlie", "daniel"
    ]

def list_available_models():
    """List available ElevenLabs models"""
    return [
        "eleven_turbo_v2_5",
        "eleven_flash_v2_5",
        "eleven_multilingual_v2",
        "eleven_flash_v2",
        "eleven_turbo_v2"
    ]

def get_voice_id(voice_name: str) -> str:
    """Get voice ID from name"""
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
    return VOICE_IDS.get(voice_name.lower(), VOICE_IDS["rachel"])

__all__ = [
    'ElevenLabsTTS',
    'list_available_voices',
    'list_available_models',
    'get_voice_id'
]

__version__ = "3.0.0"
