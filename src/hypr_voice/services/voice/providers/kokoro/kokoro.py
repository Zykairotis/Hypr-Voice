"""
Kokoro TTS Integration for Voice Synthesis
Provides voice synthesis capabilities for agents
"""

import asyncio
import logging
import struct
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List, Dict, Any, AsyncIterator
import json
from datetime import datetime
from enum import Enum
import queue
import threading


# ============================================================================
# VOICE MODELS AND CONFIGURATION
# ============================================================================

class KokoroVoice(str, Enum):
    """Available Kokoro voices"""
    # American English voices
    AF = "af"  # American Female
    AF_BELLA = "af_bella"
    AF_SARAH = "af_sarah"
    AF_SKY = "af_sky"
    AF_NICOLE = "af_nicole"
    
    AM = "am"  # American Male
    AM_ADAM = "am_adam"
    AM_MICHAEL = "am_michael"
    
    # British English voices
    BF_EMMA = "bf_emma"
    BF_ISABELLA = "bf_isabella"
    
    BM_GEORGE = "bm_george"
    BM_LEWIS = "bm_lewis"
    
    # Special voices
    CHILD_F = "af_child"
    CHILD_M = "am_child"
    ROBOT = "robot"
    
    @classmethod
    def get_by_gender_and_accent(cls, gender: str = "female", accent: str = "american"):
        """Get default voice by gender and accent"""
        if gender.lower() == "female":
            if accent.lower() == "american":
                return cls.AF_BELLA
            elif accent.lower() == "british":
                return cls.BF_EMMA
        else:
            if accent.lower() == "american":
                return cls.AM_ADAM
            elif accent.lower() == "british":
                return cls.BM_GEORGE
        
        return cls.AF_BELLA  # Default


@dataclass
class KokoroConfig:
    """Configuration for Kokoro TTS"""
    voice: str = KokoroVoice.AF_BELLA
    speed: float = 1.0
    volume: float = 1.0
    pitch: float = 1.0
    emotion: Optional[str] = None  # happy, sad, angry, neutral
    sample_rate: int = 24000
    output_format: str = "wav"
    cache_enabled: bool = True
    cache_dir: str = "/tmp/kokoro_cache"


# ============================================================================
# KOKORO TTS CORE
# ============================================================================

class KokoroTTS:
    """Core Kokoro TTS implementation"""
    
    def __init__(self, config: KokoroConfig = None):
        self.config = config or KokoroConfig()
        self.logger = logging.getLogger("KokoroTTS")
        self._cache = {} if self.config.cache_enabled else None
        self._ensure_cache_dir()
        
        # Try to import kokoro if available
        self.kokoro_available = False
        try:
            import kokoro_onnx
            self.kokoro_onnx = kokoro_onnx
            self.kokoro_available = True
            self.logger.info("Kokoro ONNX loaded successfully")
        except ImportError:
            self.logger.warning("Kokoro ONNX not available, using mock mode")
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if self.config.cache_enabled:
            Path(self.config.cache_dir).mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, text: str, voice: str) -> str:
        """Generate cache key for text and voice combination"""
        import hashlib
        content = f"{text}_{voice}_{self.config.speed}_{self.config.pitch}"
        return hashlib.md5(content.encode()).hexdigest()
    
    async def synthesize(
        self,
        text: str,
        output_path: Optional[str] = None,
        voice: Optional[str] = None
    ) -> str:
        """Synthesize speech from text"""
        
        voice = voice or self.config.voice
        
        # Check cache
        if self.config.cache_enabled:
            cache_key = self._get_cache_key(text, voice)
            cached_file = Path(self.config.cache_dir) / f"{cache_key}.wav"
            
            if cached_file.exists():
                self.logger.info(f"Using cached audio: {cached_file}")
                
                if output_path:
                    import shutil
                    shutil.copy(cached_file, output_path)
                    return output_path
                
                return str(cached_file)
        
        # Generate audio
        if self.kokoro_available:
            audio_data = await self._generate_kokoro(text, voice)
        else:
            audio_data = await self._generate_mock(text, voice)
        
        # Determine output path
        if not output_path:
            output_path = f"/tmp/kokoro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        
        # Save audio
        self._save_audio(audio_data, output_path)
        
        # Cache if enabled
        if self.config.cache_enabled:
            cache_file = Path(self.config.cache_dir) / f"{cache_key}.wav"
            import shutil
            shutil.copy(output_path, cache_file)
        
        self.logger.info(f"Synthesized audio saved to: {output_path}")
        
        return output_path
    
    async def _generate_kokoro(self, text: str, voice: str) -> bytes:
        """Generate audio using Kokoro"""
        
        # This would use actual Kokoro library
        # For now, return mock data
        return await self._generate_mock(text, voice)
    
    async def _generate_mock(self, text: str, voice: str) -> bytes:
        """Generate mock audio data"""
        
        # Generate silent audio as placeholder
        duration = len(text) * 0.1  # Rough estimate
        sample_rate = self.config.sample_rate
        num_samples = int(duration * sample_rate)
        
        # Generate simple sine wave
        import math
        frequency = 440  # A4 note
        amplitude = 0.5
        
        samples = []
        for i in range(num_samples):
            t = i / sample_rate
            sample = amplitude * math.sin(2 * math.pi * frequency * t)
            samples.append(int(sample * 32767))
        
        # Convert to bytes
        audio_data = struct.pack('<' + 'h' * len(samples), *samples)
        
        return audio_data
    
    def _save_audio(self, audio_data: bytes, output_path: str):
        """Save audio data to WAV file"""
        
        with wave.open(output_path, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes(audio_data)
    
    async def synthesize_batch(
        self,
        texts: List[str],
        voice: Optional[str] = None
    ) -> List[str]:
        """Synthesize multiple texts in batch"""
        
        tasks = [
            self.synthesize(text, voice=voice)
            for text in texts
        ]
        
        results = await asyncio.gather(*tasks)
        
        return results


# ============================================================================
# STREAMING SYNTHESIS
# ============================================================================

class StreamingSynthesizer:
    """Streaming TTS synthesis for real-time output"""
    
    def __init__(self, config: KokoroConfig = None):
        self.config = config or KokoroConfig()
        self.tts = KokoroTTS(config)
        self.logger = logging.getLogger("StreamingSynthesizer")
        self._audio_queue = asyncio.Queue()
        self._synthesis_task = None
    
    async def start_stream(self) -> AsyncIterator[bytes]:
        """Start streaming synthesis"""
        
        self.logger.info("Starting streaming synthesis")
        
        while True:
            try:
                audio_chunk = await self._audio_queue.get()
                
                if audio_chunk is None:  # End of stream
                    break
                
                yield audio_chunk
                
            except Exception as e:
                self.logger.error(f"Streaming error: {e}")
                break
    
    async def synthesize_chunk(self, text: str, voice: Optional[str] = None):
        """Synthesize a text chunk and add to stream"""
        
        # Split text into sentences for smoother streaming
        sentences = self._split_sentences(text)
        
        for sentence in sentences:
            if sentence.strip():
                audio_file = await self.tts.synthesize(sentence, voice=voice)
                
                # Read audio file and add to queue
                with open(audio_file, 'rb') as f:
                    audio_data = f.read()
                    await self._audio_queue.put(audio_data)
    
    async def end_stream(self):
        """End the streaming session"""
        
        await self._audio_queue.put(None)
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        
        return [s.strip() for s in sentences if s.strip()]


# ============================================================================
# VOICE MANAGER
# ============================================================================

class VoiceManager:
    """Manages multiple voices and synthesis queues"""
    
    def __init__(self):
        self.synthesizers: Dict[str, KokoroTTS] = {}
        self.voice_queues: Dict[str, asyncio.Queue] = {}
        self.active_voices: Dict[str, KokoroConfig] = {}
        self.logger = logging.getLogger("VoiceManager")
    
    def register_voice(self, name: str, config: KokoroConfig):
        """Register a new voice configuration"""
        
        self.active_voices[name] = config
        self.synthesizers[name] = KokoroTTS(config)
        self.voice_queues[name] = asyncio.Queue()
        
        self.logger.info(f"Registered voice: {name} with {config.voice}")
    
    async def synthesize_with_voice(
        self,
        text: str,
        voice_name: str,
        output_path: Optional[str] = None
    ) -> str:
        """Synthesize using a specific registered voice"""
        
        if voice_name not in self.synthesizers:
            raise ValueError(f"Voice '{voice_name}' not registered")
        
        synthesizer = self.synthesizers[voice_name]
        
        return await synthesizer.synthesize(text, output_path)
    
    async def queue_synthesis(self, voice_name: str, text: str):
        """Queue text for synthesis"""
        
        if voice_name not in self.voice_queues:
            raise ValueError(f"Voice '{voice_name}' not registered")
        
        await self.voice_queues[voice_name].put(text)
    
    async def process_voice_queue(self, voice_name: str):
        """Process synthesis queue for a voice"""
        
        if voice_name not in self.voice_queues:
            return
        
        queue = self.voice_queues[voice_name]
        synthesizer = self.synthesizers[voice_name]
        
        while True:
            try:
                text = await queue.get()
                
                if text is None:  # Shutdown signal
                    break
                
                await synthesizer.synthesize(text)
                
            except Exception as e:
                self.logger.error(f"Error processing voice queue: {e}")
    
    def list_voices(self) -> List[Dict[str, Any]]:
        """List all registered voices"""
        
        return [
            {
                "name": name,
                "voice": config.voice,
                "speed": config.speed,
                "pitch": config.pitch
            }
            for name, config in self.active_voices.items()
        ]


# ============================================================================
# AGENT VOICE SKILL
# ============================================================================

class VoiceSkill:
    """Voice synthesis skill for agents"""
    
    def __init__(self, voice_manager: Optional[VoiceManager] = None):
        self.voice_manager = voice_manager or VoiceManager()
        self.logger = logging.getLogger("VoiceSkill")
        
        # Register default voices
        self._register_default_voices()
    
    def _register_default_voices(self):
        """Register default voice configurations"""
        
        # Professional voice
        self.voice_manager.register_voice(
            "professional",
            KokoroConfig(
                voice=KokoroVoice.AF_BELLA,
                speed=1.0,
                pitch=1.0
            )
        )
        
        # Friendly voice
        self.voice_manager.register_voice(
            "friendly",
            KokoroConfig(
                voice=KokoroVoice.AF_SKY,
                speed=1.1,
                pitch=1.1,
                emotion="happy"
            )
        )
        
        # Technical voice
        self.voice_manager.register_voice(
            "technical",
            KokoroConfig(
                voice=KokoroVoice.AM_ADAM,
                speed=0.95,
                pitch=0.95
            )
        )
        
        # Child voice
        self.voice_manager.register_voice(
            "child",
            KokoroConfig(
                voice=KokoroVoice.CHILD_F,
                speed=1.2,
                pitch=1.3
            )
        )
    
    async def execute(
        self,
        agent_context: Dict,
        text: str,
        voice_type: str = "professional",
        **kwargs
    ) -> Dict[str, Any]:
        """Execute voice synthesis for agent"""
        
        working_dir = Path(agent_context.get("working_directory", "/tmp"))
        output_dir = working_dir / "audio"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_path = output_dir / f"speech_{timestamp}.wav"
        
        try:
            audio_file = await self.voice_manager.synthesize_with_voice(
                text,
                voice_type,
                str(output_path)
            )
            
            return {
                "status": "success",
                "audio_file": audio_file,
                "voice_type": voice_type,
                "text_length": len(text),
                "timestamp": timestamp
            }
            
        except Exception as e:
            self.logger.error(f"Voice synthesis error: {e}")
            
            return {
                "status": "error",
                "error": str(e)
            }


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

async def example_basic_synthesis():
    """Basic synthesis example"""
    
    config = KokoroConfig(
        voice=KokoroVoice.AF_BELLA,
        speed=1.0,
        emotion="happy"
    )
    
    tts = KokoroTTS(config)
    
    text = "Hello! I'm your AI assistant. How can I help you today?"
    
    audio_file = await tts.synthesize(text)
    
    print(f"Audio synthesized: {audio_file}")


async def example_streaming():
    """Streaming synthesis example"""
    
    config = KokoroConfig(voice=KokoroVoice.AM_ADAM)
    
    streamer = StreamingSynthesizer(config)
    
    # Start streaming
    stream_task = asyncio.create_task(streamer.start_stream())
    
    # Add text chunks
    texts = [
        "This is the first part of the message.",
        "Here comes the second part.",
        "And finally, the last part."
    ]
    
    for text in texts:
        await streamer.synthesize_chunk(text)
        await asyncio.sleep(0.5)
    
    await streamer.end_stream()
    
    # Collect audio chunks
    audio_chunks = []
    async for chunk in stream_task:
        audio_chunks.append(chunk)
    
    print(f"Streamed {len(audio_chunks)} audio chunks")


async def example_voice_manager():
    """Voice manager example"""
    
    manager = VoiceManager()
    
    # Register custom voices
    manager.register_voice(
        "narrator",
        KokoroConfig(
            voice=KokoroVoice.BM_GEORGE,
            speed=0.9,
            pitch=0.95
        )
    )
    
    manager.register_voice(
        "character1",
        KokoroConfig(
            voice=KokoroVoice.AF_SARAH,
            speed=1.1,
            emotion="happy"
        )
    )
    
    # Synthesize dialogue
    dialogue = [
        ("narrator", "Once upon a time, in a digital world..."),
        ("character1", "Hello! I'm an AI assistant!"),
        ("narrator", "Said the cheerful assistant."),
    ]
    
    for voice_name, text in dialogue:
        audio_file = await manager.synthesize_with_voice(text, voice_name)
        print(f"{voice_name}: {audio_file}")


async def example_agent_with_voice():
    """Agent that speaks its output"""
    
    from hypr_voice.client import AgentClient, AgentConfig
    
    client = AgentClient()
    
    config = AgentConfig(
        name="speaking-agent",
        working_directory="/tmp/agents/voice",
        skills=["voice_synthesis", "file_operations"],
        enable_voice=True
    )
    
    agent_id = await client.create_agent(config)
    
    await client.instruct(
        agent_id,
        """
        Analyze the current directory and create a summary report.
        Then convert your summary to speech using the voice_synthesis skill.
        Use a clear, professional voice.
        """
    )
    
    await asyncio.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Run examples
    asyncio.run(example_basic_synthesis())
    # asyncio.run(example_streaming())
    # asyncio.run(example_voice_manager())
    # asyncio.run(example_agent_with_voice())
