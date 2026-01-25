#!/usr/bin/env python3
"""
Real-time Audio Player for Streaming TTS

Based on Deepgram's recommended implementation for WebSocket TTS streaming.
Uses PyAudio with queue-based architecture for smooth, continuous playback.

Reference: https://developers.deepgram.com/docs/send-llm-outputs-to-the-tts-web-socket
"""

import asyncio
import logging
import queue
import threading
import time
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Audio configuration defaults (matching Deepgram recommendations)
DEFAULT_SAMPLE_RATE = 48000
DEFAULT_CHANNELS = 1
DEFAULT_CHUNK_SIZE = 4800  # 100ms of audio at 48kHz (reduced for smoother playback)
QUEUE_TIMEOUT = 0.010  # 10ms - reduced for lower latency
SILENCE_ON_UNDERRUN = True  # Write silence instead of gaps to prevent crackling


@dataclass 
class AudioConfig:
    """Audio playback configuration."""
    sample_rate: int = DEFAULT_SAMPLE_RATE
    channels: int = DEFAULT_CHANNELS
    chunk_size: int = DEFAULT_CHUNK_SIZE
    output_device: Optional[int] = None  # None = default device


class AudioPlayer:
    """
    Queue-based audio player for real-time streaming playback.
    
    Based on Deepgram's Speaker class implementation for reliable
    streaming audio playback without crackling or dropouts.
    
    Usage:
        player = AudioPlayer(sample_rate=48000)
        player.start()
        
        # As audio chunks arrive:
        player.play(audio_bytes)
        player.play(more_audio_bytes)
        
        # When done:
        player.stop()
    """
    
    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE, channels: int = DEFAULT_CHANNELS):
        """
        Initialize audio player.
        
        Args:
            sample_rate: Audio sample rate in Hz
            channels: Number of audio channels (1=mono, 2=stereo)
        """
        self.config = AudioConfig(
            sample_rate=sample_rate,
            channels=channels,
        )
        
        self._queue: queue.Queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._stream = None
        self._backend = None
        self._pyaudio_instance = None
        
    def start(self) -> bool:
        """
        Start audio playback thread.
        
        Returns:
            True if started successfully
        """
        if self._thread and self._thread.is_alive():
            logger.warning("Audio player already running")
            return True
            
        self._stop_event.clear()
        self._queue = queue.Queue()
        
        # Use PyAudio (Deepgram's recommended backend)
        if self._init_pyaudio():
            self._backend = "pyaudio"
        elif self._init_sounddevice():
            self._backend = "sounddevice"
        else:
            logger.error("No audio backend available (install pyaudio or sounddevice)")
            return False
            
        logger.info(f"Audio player started with {self._backend} backend")
        return True
    
    def _init_pyaudio(self) -> bool:
        """Initialize pyaudio backend (Deepgram recommended)."""
        try:
            import pyaudio
            
            self._pyaudio_instance = pyaudio.PyAudio()
            self._stream = self._pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.config.channels,
                rate=self.config.sample_rate,
                input=False,
                output=True,
                frames_per_buffer=self.config.chunk_size,
                output_device_index=self.config.output_device,
            )
            
            # Start playback thread
            self._thread = threading.Thread(target=self._pyaudio_loop, daemon=True)
            self._thread.start()
            
            # Start the stream
            self._stream.start_stream()
            return True
            
        except ImportError:
            logger.debug("pyaudio not available")
            return False
        except Exception as e:
            logger.debug(f"pyaudio init failed: {e}")
            return False
    
    def _init_sounddevice(self) -> bool:
        """Initialize sounddevice backend (fallback)."""
        try:
            import sounddevice as sd
            import numpy as np
            
            self._sd = sd
            self._np = np
            
            # Open output stream for continuous playback
            self._sd_stream = sd.OutputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.channels,
                dtype='int16',
                blocksize=self.config.chunk_size,
            )
            self._sd_stream.start()
            
            # Start playback thread
            self._thread = threading.Thread(target=self._sounddevice_loop, daemon=True)
            self._thread.start()
            return True
            
        except ImportError:
            logger.debug("sounddevice not available")
            return False
        except Exception as e:
            logger.debug(f"sounddevice init failed: {e}")
            return False
    
    def _pyaudio_loop(self):
        """Playback loop using pyaudio (Deepgram's reference implementation)."""
        # Pre-allocate silence buffer to avoid crackling on underruns
        silence_buffer = b'\x00' * (self.config.chunk_size * 2)  # 16-bit = 2 bytes per sample
        
        while not self._stop_event.is_set():
            try:
                data = self._queue.get(timeout=QUEUE_TIMEOUT)
                if data is None:
                    continue
                    
                # Write directly to stream
                self._stream.write(data)
                
            except queue.Empty:
                # Write silence to prevent crackling/popping on buffer underrun
                if SILENCE_ON_UNDERRUN and self._stream:
                    try:
                        self._stream.write(silence_buffer)
                    except Exception:
                        pass
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"PyAudio playback error: {e}")
    
    def _sounddevice_loop(self):
        """Playback loop using sounddevice (fallback)."""
        # Pre-allocate silence buffer to avoid crackling on underruns
        silence_array = self._np.zeros(self.config.chunk_size, dtype=self._np.int16)
        
        while not self._stop_event.is_set():
            try:
                data = self._queue.get(timeout=QUEUE_TIMEOUT)
                if data is None:
                    continue
                    
                # Convert bytes to numpy array
                array = self._np.frombuffer(data, dtype=self._np.int16)
                
                # Write to continuous output stream
                self._sd_stream.write(array)
                
            except queue.Empty:
                # Write silence to prevent crackling/popping on buffer underrun
                if SILENCE_ON_UNDERRUN and hasattr(self, '_sd_stream') and self._sd_stream:
                    try:
                        self._sd_stream.write(silence_array)
                    except Exception:
                        pass
            except Exception as e:
                if not self._stop_event.is_set():
                    logger.error(f"Sounddevice playback error: {e}")
    
    def play(self, audio_data: bytes):
        """
        Queue audio data for playback.
        
        Args:
            audio_data: Raw PCM audio bytes (linear16)
        """
        if not audio_data:
            return
            
        self._queue.put(audio_data)
    
    def stop(self, wait: bool = True, timeout: float = 2.0):
        """
        Stop audio playback.
        
        Args:
            wait: Wait for remaining audio to finish
            timeout: Max time to wait for queue to drain
        """
        if wait:
            # Wait for queue to drain
            start = time.time()
            while not self._queue.empty() and (time.time() - start) < timeout:
                time.sleep(0.1)
        
        self._stop_event.set()
        
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        
        # Cleanup backend
        if self._backend == "pyaudio":
            if self._stream:
                try:
                    self._stream.stop_stream()
                    self._stream.close()
                except:
                    pass
                self._stream = None
            if self._pyaudio_instance:
                try:
                    self._pyaudio_instance.terminate()
                except:
                    pass
                self._pyaudio_instance = None
        elif self._backend == "sounddevice":
            if hasattr(self, '_sd_stream') and self._sd_stream:
                try:
                    self._sd_stream.stop()
                    self._sd_stream.close()
                except:
                    pass
                self._sd_stream = None
        
        logger.info("Audio player stopped")
    
    def clear(self):
        """Clear any queued audio."""
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
            except queue.Empty:
                break
    
    @property
    def is_playing(self) -> bool:
        """Check if player is active."""
        return self._thread is not None and self._thread.is_alive()
    
    @property
    def queue_size(self) -> int:
        """Get number of chunks in queue."""
        return self._queue.qsize()


class AsyncAudioPlayer:
    """
    Async wrapper for AudioPlayer.
    
    Usage:
        async with AsyncAudioPlayer() as player:
            await player.play(audio_bytes)
    """
    
    def __init__(self, sample_rate: int = DEFAULT_SAMPLE_RATE):
        self._player = AudioPlayer(sample_rate=sample_rate)
        
    async def __aenter__(self):
        self._player.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._player.stop()
        
    async def play(self, audio_data: bytes):
        """Queue audio for playback (non-blocking)."""
        self._player.play(audio_data)
        
    async def wait_until_done(self, timeout: float = 30.0):
        """Wait for all queued audio to finish playing."""
        start = time.time()
        while self._player.queue_size > 0 and (time.time() - start) < timeout:
            await asyncio.sleep(0.1)


def play_audio_blocking(audio_data: bytes, sample_rate: int = DEFAULT_SAMPLE_RATE):
    """
    Simple blocking audio playback.
    
    Args:
        audio_data: Raw PCM audio bytes
        sample_rate: Audio sample rate
    """
    try:
        import sounddevice as sd
        import numpy as np
        
        array = np.frombuffer(audio_data, dtype=np.int16)
        sd.play(array, sample_rate)
        sd.wait()
        
    except ImportError:
        try:
            import pyaudio
            
            p = pyaudio.PyAudio()
            stream = p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True,
            )
            stream.write(audio_data)
            stream.stop_stream()
            stream.close()
            p.terminate()
            
        except ImportError:
            logger.error("No audio backend available")
            raise RuntimeError("Install sounddevice or pyaudio for audio playback")
