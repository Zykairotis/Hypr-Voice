"""
Voice Tools

Text-to-speech and speech-to-text tools.
"""

import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..registry import tool

logger = logging.getLogger(__name__)


@tool(
    "synthesize_speech",
    "Convert text to speech audio file",
    {
        "text": str,
        "voice": str,
        "output_path": str,
    },
    category="voice"
)
async def synthesize_speech(args: dict) -> dict:
    """
    Synthesize speech from text.
    
    Args:
        text: Text to synthesize
        voice: Voice ID to use (e.g., "af_bella")
        output_path: Optional output file path
    """
    text = args.get("text", "")
    voice = args.get("voice", "af_bella")
    output_path = args.get("output_path")
    
    if not text:
        return {
            "content": [{"type": "text", "text": "Error: No text provided"}],
            "is_error": True,
        }
    
    try:
        # Try to use Kokoro TTS if available
        from hypr_voice.services.voice import text_to_speech, TTSConfig
        
        config = TTSConfig(voice=voice)
        
        if not output_path:
            output_path = f"/tmp/speech_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        audio_file = await text_to_speech(text, output_path, config)
        
        return {
            "content": [{
                "type": "text",
                "text": f"Speech synthesized successfully: {audio_file}"
            }]
        }
        
    except ImportError:
        logger.warning("Voice services not available")
        return {
            "content": [{
                "type": "text",
                "text": "Voice synthesis not available. Install voice dependencies."
            }],
            "is_error": True,
        }
    except Exception as e:
        logger.error(f"Speech synthesis error: {e}")
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True,
        }


@tool(
    "transcribe_audio",
    "Transcribe speech from audio file to text",
    {
        "audio_path": str,
        "language": str,
    },
    category="voice"
)
async def transcribe_audio(args: dict) -> dict:
    """
    Transcribe audio to text.
    
    Args:
        audio_path: Path to audio file
        language: Language code (e.g., "en", "auto")
    """
    audio_path = args.get("audio_path", "")
    language = args.get("language", "auto")
    
    if not audio_path:
        return {
            "content": [{"type": "text", "text": "Error: No audio path provided"}],
            "is_error": True,
        }
    
    if not Path(audio_path).exists():
        return {
            "content": [{"type": "text", "text": f"Error: File not found: {audio_path}"}],
            "is_error": True,
        }
    
    try:
        # Try to use Whisper if available
        # This would integrate with the existing Hypr-Whisper system
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:9090/transcribe",
                json={"audio_path": audio_path, "language": language},
                timeout=30,
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "content": [{
                            "type": "text",
                            "text": result.get("text", "")
                        }]
                    }
                else:
                    return {
                        "content": [{"type": "text", "text": "Transcription service unavailable"}],
                        "is_error": True,
                    }
                    
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True,
        }
