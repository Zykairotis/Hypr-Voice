#!/usr/bin/env python3
"""
Raw Transcription Processor - Fast transcription without enhancement

This module provides direct Whisper server communication for raw transcription
without LLM enhancement, optimized for speed and minimal resource usage.
"""

import os
import asyncio
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
from loguru import logger
import numpy as np
import soundfile as sf


@dataclass
class RawModeConfig:
    """Configuration for raw transcription mode"""
    enabled: bool = True
    max_processing_time_ms: int = 500
    silence_detection_enabled: bool = True
    silence_threshold: float = 0.01
    silence_duration: float = 2.0
    output_format: str = "text"  # text, json
    save_audio_files: bool = False
    whisper_timeout: float = 10.0
    max_retries: int = 2


@dataclass
class ProcessingResult:
    """Result from transcription processing"""
    text: str
    processing_time_ms: int
    mode_used: str
    audio_duration_ms: int
    confidence_score: Optional[float] = None
    error: Optional[str] = None


class RawTranscriptionProcessor:
    """
    Raw transcription processor for fast, direct Whisper communication
    """
    
    def __init__(self, whisper_server_url: str, audio_config: dict, raw_config: Optional[RawModeConfig] = None):
        """
        Initialize raw transcription processor
        
        Args:
            whisper_server_url: URL of Whisper server
            audio_config: Audio configuration dictionary
            raw_config: Raw mode specific configuration
        """
        self.whisper_server_url = whisper_server_url
        self.audio_config = audio_config
        self.raw_config = raw_config or RawModeConfig()
        
        # Audio processing settings
        self.target_sample_rate = audio_config.get('whisper', {}).get('target_sample_rate', 16000)
        
        # Performance tracking
        self._last_processing_time = 0.0
        
        logger.info(f"Raw transcription processor initialized - target: {self.raw_config.max_processing_time_ms}ms")
    
    async def process_raw_transcription(self, audio_data: np.ndarray, sample_rate: int) -> ProcessingResult:
        """
        Process audio directly through Whisper without enhancement
        
        Args:
            audio_data: Raw audio data as numpy array
            sample_rate: Sample rate of audio data
            
        Returns:
            ProcessingResult with transcription and timing info
        """
        start_time = time.time()
        
        try:
            # Prepare audio for Whisper
            processed_audio = self._prepare_audio_for_whisper(audio_data, sample_rate)
            
            # Calculate audio duration
            audio_duration_ms = int((len(processed_audio) / self.target_sample_rate) * 1000)
            
            # Save temporary audio file
            temp_audio_path = await self._save_temp_audio(processed_audio)
            
            try:
                # Send to Whisper server
                transcription = await self._send_to_whisper_server(temp_audio_path)
                
                # Calculate processing time
                processing_time_ms = int((time.time() - start_time) * 1000)
                self._last_processing_time = processing_time_ms
                
                # Clean up temp file unless configured to save
                if not self.raw_config.save_audio_files:
                    try:
                        os.unlink(temp_audio_path)
                    except:
                        pass
                
                # Log performance
                if processing_time_ms > self.raw_config.max_processing_time_ms:
                    logger.warning(f"Raw processing exceeded target: {processing_time_ms}ms > {self.raw_config.max_processing_time_ms}ms")
                else:
                    logger.info(f"✅ Raw processing completed in {processing_time_ms}ms")
                
                return ProcessingResult(
                    text=transcription,
                    processing_time_ms=processing_time_ms,
                    mode_used="raw",
                    audio_duration_ms=audio_duration_ms,
                    confidence_score=None  # Raw mode doesn't provide confidence
                )
                
            finally:
                # Always clean up temp file on error
                if not self.raw_config.save_audio_files:
                    try:
                        os.unlink(temp_audio_path)
                    except:
                        pass
                        
        except Exception as e:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Raw transcription failed after {processing_time_ms}ms: {e}")
            
            return ProcessingResult(
                text="",
                processing_time_ms=processing_time_ms,
                mode_used="raw",
                audio_duration_ms=0,
                error=str(e)
            )
    
    def _prepare_audio_for_whisper(self, audio_data: np.ndarray, sample_rate: int) -> np.ndarray:
        """
        Prepare audio data for Whisper processing
        
        Args:
            audio_data: Raw audio data
            sample_rate: Current sample rate
            
        Returns:
            Processed audio data ready for Whisper
        """
        # Convert to mono if needed
        if audio_data.ndim == 2:
            audio_data = audio_data.mean(axis=1)
        
        # Ensure float32
        audio_data = audio_data.astype(np.float32)
        
        # Normalize if needed (handle int16 input)
        if audio_data.dtype == np.int16:
            audio_data = audio_data / 32768.0
        
        # Resample to target rate if needed
        if sample_rate != self.target_sample_rate:
            audio_data = self._resample_audio(audio_data, sample_rate, self.target_sample_rate)
        
        return audio_data
    
    @staticmethod
    def _resample_audio(audio_data: np.ndarray, from_sr: int, to_sr: int) -> np.ndarray:
        """Simple linear resampling using numpy.interp"""
        if from_sr == to_sr:
            return audio_data
            
        n_old = len(audio_data)
        n_new = max(1, int(round(n_old * to_sr / from_sr)))
        
        # Create time indices
        old_indices = np.linspace(0, 1, n_old, endpoint=False)
        new_indices = np.linspace(0, 1, n_new, endpoint=False)
        
        # Interpolate
        resampled = np.interp(new_indices, old_indices, audio_data.astype(np.float64))
        return resampled.astype(np.float32)
    
    async def _save_temp_audio(self, audio_data: np.ndarray) -> str:
        """Save audio data to temporary file"""
        from datetime import datetime
        
        # Create temp filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        temp_dir = Path("/tmp") / "hypr-voice-raw"
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / f"raw_{timestamp}.wav"
        
        # Save audio file
        sf.write(str(temp_path), audio_data, self.target_sample_rate)
        
        return str(temp_path)
    
    async def _send_to_whisper_server(self, audio_file_path: str) -> str:
        """
        Send audio to Whisper server and get raw transcription
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Raw transcription text
        """
        server_url = self.whisper_server_url
        
        # Handle 0.0.0.0 bind address
        if '0.0.0.0' in server_url:
            server_url = server_url.replace('0.0.0.0', 'localhost')
        
        # Create session with minimal settings for speed
        session_payload = {
            "language": "en",
            "beam_size": 1,  # Reduced for speed
            "vad_filter": False,  # Disabled for speed
            "compute_type": "int8",  # Fast inference
            "device": "auto"
        }
        
        try:
            # Create session
            sess_resp = requests.post(
                f"{server_url}/sessions", 
                json=session_payload, 
                timeout=self.raw_config.whisper_timeout
            )
            sess_resp.raise_for_status()
            sess_json = sess_resp.json()
            
            # Get session ID
            session_id = (
                sess_json.get("session_id") or
                sess_json.get("id") or
                sess_json.get("uuid") or
                sess_json.get("sessionId")
            )
            
            if not session_id:
                raise Exception("No session ID returned from Whisper server")
            
            # Upload audio file
            with open(audio_file_path, 'rb') as f:
                files = {"audio_file": (os.path.basename(audio_file_path), f, 'audio/wav')}
                upload_resp = requests.post(
                    f"{server_url}/sessions/{session_id}/transcribe",
                    files=files,
                    timeout=self.raw_config.whisper_timeout
                )
            
            upload_resp.raise_for_status()
            
            # Poll for result with shorter timeout for raw mode
            transcription = await self._poll_transcription_result(server_url, session_id)
            
            return transcription or ""
            
        except Exception as e:
            logger.error(f"Whisper server communication failed: {e}")
            raise
    
    async def _poll_transcription_result(self, server_url: str, session_id: str) -> Optional[str]:
        """
        Poll Whisper server for transcription result with optimized timing for raw mode
        """
        start_poll = time.time()
        poll_timeout = min(self.raw_config.whisper_timeout, 15.0)  # Shorter timeout for raw mode
        
        while time.time() - start_poll < poll_timeout:
            try:
                status_resp = requests.get(
                    f"{server_url}/sessions/{session_id}",
                    timeout=2.0  # Short timeout for polling
                )
                status_resp.raise_for_status()
                status_json = status_resp.json()
                
                # Extract transcription text
                text = self._extract_transcription_text(status_json)
                
                if text:
                    return text.strip()
                
                # Check if processing is complete
                status = status_json.get('status')
                if status in ("stopped", "error", "failed", "completed"):
                    break
                
            except Exception as e:
                logger.debug(f"Polling error: {e}")
            
            # Short sleep for raw mode responsiveness
            await asyncio.sleep(0.1)  # 100ms polling interval
        
        return None
    
    def _extract_transcription_text(self, status_json: dict) -> str:
        """Extract transcription text from various possible response formats"""
        # Try multiple fields for transcription text
        text = (
            status_json.get('text') or
            status_json.get('transcription') or
            status_json.get('transcript') or
            status_json.get('result') or
            status_json.get('output') or
            ""
        )
        
        # If segments are provided, concatenate
        if not text and isinstance(status_json.get('segments'), list):
            try:
                text = ' '.join(seg.get('text', '') for seg in status_json['segments'])
            except Exception:
                pass
        
        # If nested under data
        if not text and isinstance(status_json.get('data'), dict):
            data = status_json['data']
            text = (
                data.get('text') or
                data.get('transcription') or
                data.get('transcript') or
                ""
            )
        
        return text.strip()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics for raw mode"""
        return {
            "last_processing_time_ms": self._last_processing_time,
            "target_processing_time_ms": self.raw_config.max_processing_time_ms,
            "performance_ratio": self._last_processing_time / self.raw_config.max_processing_time_ms if self.raw_config.max_processing_time_ms > 0 else 0,
            "config": {
                "max_processing_time_ms": self.raw_config.max_processing_time_ms,
                "silence_detection_enabled": self.raw_config.silence_detection_enabled,
                "save_audio_files": self.raw_config.save_audio_files
            }
        }


# Test function
async def test_raw_processor():
    """Test the raw transcription processor"""
    # Create test audio data (1 second of sine wave)
    sample_rate = 48000
    duration = 1.0
    frequency = 440.0
    
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    audio_data = np.sin(2 * np.pi * frequency * t).astype(np.float32)
    
    # Create processor
    audio_config = {
        'whisper': {
            'target_sample_rate': 16000
        }
    }
    
    processor = RawTranscriptionProcessor(
        whisper_server_url="http://localhost:9880",
        audio_config=audio_config
    )
    
    # Process audio
    result = await processor.process_raw_transcription(audio_data, sample_rate)
    
    print(f"Processing time: {result.processing_time_ms}ms")
    print(f"Audio duration: {result.audio_duration_ms}ms")
    print(f"Transcription: {result.text}")
    print(f"Error: {result.error}")
    
    return result


if __name__ == "__main__":
    asyncio.run(test_raw_processor())