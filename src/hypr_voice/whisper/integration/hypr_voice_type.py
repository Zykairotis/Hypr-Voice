#!/usr/bin/env python3
"""
Hypr-Voice Push-to-Talk Transcription
Records audio while F9 is pressed, transcribes it, and types the result.
"""

import sys
import tempfile
import asyncio
import pyaudio
import wave
import time
import argparse
import subprocess
import yaml
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from loguru import logger

# Allow running as a script with PYTHONPATH configured
if __name__ == "__main__" and not __package__:
    project_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(project_root / "src"))
    __package__ = "hypr_voice.whisper.integration"

from ..core.hybrid_client import HybridWhisperClient
from ..vocabulary.vocabulary_manager import get_vocabulary_manager
from ..backends.window_backends import detect_backend
from ..backends.input_backends import detect_input_backend
from ..paths import get_whisper_config_path, WHISPER_RECORDINGS_DIR, ensure_whisper_state_dirs

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SERVER_URL = "http://localhost:9099"
SAMPLE_RATE = 16000  # Standard for voice
CHUNK_SIZE = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16

# Save recordings under whisper state directory
RECORDINGS_DIR = WHISPER_RECORDINGS_DIR

# ============================================================================
# AUDIO DEVICE CONFIGURATION
# ============================================================================

def load_audio_config():
    """Load audio configuration from audio-profile.yaml."""
    config_path = get_whisper_config_path("audio-profile.yaml")
    
    if not config_path.exists():
        logger.warning(f"Audio config not found at {config_path}, using default device")
        return None, None, None
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            
        if 'pulseaudio' in config:
            device_name = config['pulseaudio'].get('device_name')
            device_type = config['pulseaudio'].get('device_type')
            default_source = config['pulseaudio'].get('default_source')
            
            # For microphone recording, we want source devices, not monitors
            if device_type == 'monitor':
                logger.info("Monitor device configured, switching to default mic for PTT")
                return None, None, None  # Use system default mic
            
            return device_name, device_type, default_source
    except Exception as e:
        logger.error(f"Error loading audio config: {e}")
        return None, None, None

def find_device_by_name(device_name):
    """Find PyAudio device ID by name."""
    if not device_name:
        return None
        
    p = pyaudio.PyAudio()
    device_id = None
    
    try:
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if device_name.lower() in info['name'].lower() and info['maxInputChannels'] > 0:
                device_id = i
                logger.info(f"Found audio device: {info['name']} (ID: {i})")
                break
    finally:
        p.terminate()
    
    return device_id

# ============================================================================
# INPUT DISPATCHER (prefers ydotool, falls back safely)
# ============================================================================

WINDOW_BACKEND = detect_backend()
INPUT_BACKEND = detect_input_backend(window_backend=WINDOW_BACKEND.name)


def type_text_words(text, words_per_second=10):
    """Type text word-by-word using the selected input backend."""
    ok = INPUT_BACKEND.type_text_words(text, words_per_second=words_per_second)
    if not ok:
        logger.warning(f"Typing (word mode) failed via backend {INPUT_BACKEND.name}")


def type_text_instant(text):
    """Type entire text using the selected input backend."""
    ok = INPUT_BACKEND.type_text_instant(text)
    if not ok:
        logger.warning(f"Typing (instant) failed via backend {INPUT_BACKEND.name}")

# ============================================================================
# PUSH-TO-TALK RECORDER
# ============================================================================

class PushToTalkRecorder:
    """Records audio while key is pressed, transcribes, and types."""

    def __init__(self, server_url=DEFAULT_SERVER_URL, save_recordings=True):
        self.client = HybridWhisperClient(server_url)
        self.save_recordings = save_recordings
        self.device_id = None
        self.recording = False
        self.frames = []

        # Initialize vocabulary manager
        self.vocabulary_manager = get_vocabulary_manager()

        # Start vocabulary detection
        try:
            asyncio.create_task(self.vocabulary_manager.start_detection())
            logger.info("Vocabulary detection started")
        except Exception as e:
            logger.warning(f"Could not start vocabulary detection: {e}")

        # Setup audio device
        device_name, device_type, default_source = load_audio_config()
        if device_name and device_type != 'monitor':
            self.device_id = find_device_by_name(device_name)

        # Create recordings directory (always, for better organization)
        ensure_whisper_state_dirs()
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

        if self.save_recordings:
            logger.info(f"Recordings will be saved to: {RECORDINGS_DIR}")
        else:
            logger.info("Using temp files (recordings not saved)")
        
        # ============================================================================
        # STREAMING CHUNKING STATE (for long recordings optimization)
        # ============================================================================
        # Smart defaults - no env vars needed unless you want to customize
        self.streaming_mode = os.getenv("FLOW_STREAMING_MODE", "1") == "1"
        # Use existing WISPR_FLOW_CHUNK_SECONDS if set, otherwise 27s default
        self.chunk_size_seconds = float(os.getenv("WISPR_FLOW_CHUNK_SECONDS", "27"))
        self.overlap_seconds = 3.0  # Fixed optimal value
        self.min_duration_for_streaming = 20.0  # Fixed threshold
        
        # Streaming state
        self.chunk_buffer = []           # Current chunk being built (audio frames)
        self.chunk_start_time = None     # When current chunk started
        self.pending_chunks = []         # Chunks ready to process
        self.transcription_results = []  # Partial results from chunks
        self.chunk_processor_task = None # Background processing task
        self.total_recording_duration = 0.0  # Track total duration
        
        if self.streaming_mode:
            logger.info(f"✨ Streaming mode enabled: {self.chunk_size_seconds}s chunks, {self.overlap_seconds}s overlap")
            logger.info(f"   Will activate for recordings > {self.min_duration_for_streaming}s")
    
    def start_recording(self):
        """Start recording audio (called when F9 pressed)."""
        if self.recording:
            logger.warning("Already recording!")
            return
        
        self.recording = True
        self.frames = []
        
        # Reset streaming state
        self.chunk_buffer = []
        self.chunk_start_time = None
        self.pending_chunks = []
        self.transcription_results = []
        self.total_recording_duration = 0.0
        
        # Visual/audio feedback
        logger.info("🔴 Recording started...")
        # Optional: Play a sound
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/message.oga"], 
                      capture_output=True, check=False)
        
        # Start recording in background
        asyncio.create_task(self._record_audio())
    
    def stop_recording(self):
        """Stop recording and process audio (called when F9 released)."""
        if not self.recording:
            logger.warning("Not recording!")
            return
        
        self.recording = False
        logger.info(f"⏹️ Recording stopped ({self.total_recording_duration:.1f}s)")
        
        # Handle final partial chunk if streaming mode was active
        if self.streaming_mode and len(self.chunk_buffer) > 0:
            final_chunk = np.array(self.chunk_buffer, dtype=np.int16)
            final_duration = len(final_chunk) / SAMPLE_RATE
            if final_duration > 1.0:  # Only process if > 1 second
                self.pending_chunks.append(final_chunk)
                logger.info(f"📦 Added final chunk: {final_duration:.1f}s")
        
        # Visual/audio feedback
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], 
                      capture_output=True, check=False)
        
        # Process the recording
        asyncio.create_task(self._process_recording())
    
    async def _record_audio(self):
        """Record audio in background with real-time chunking for streaming transcription."""
        p = pyaudio.PyAudio()
        
        try:
            stream_params = {
                'format': FORMAT,
                'channels': CHANNELS,
                'rate': SAMPLE_RATE,
                'input': True,
                'frames_per_buffer': CHUNK_SIZE,
            }
            
            if self.device_id is not None:
                stream_params['input_device_index'] = self.device_id
                logger.info(f"Using device ID: {self.device_id}")
            else:
                logger.info("Using system default microphone")
            
            stream = p.open(**stream_params)
            
            # Start background chunk processor if streaming mode enabled
            if self.streaming_mode:
                self.chunk_processor_task = asyncio.create_task(
                    self._background_chunk_processor()
                )
                logger.info("🚀 Background chunk processor started")
            
            logger.info("Recording audio...")
            recording_start_time = time.time()
            
            while self.recording:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    self.frames.append(data)
                    
                    # Calculate total recording duration
                    self.total_recording_duration = time.time() - recording_start_time
                    
                    # NEW: Real-time chunking logic for streaming mode
                    if self.streaming_mode and self.total_recording_duration >= self.min_duration_for_streaming:
                        # Convert to numpy array for processing
                        audio_np = np.frombuffer(data, dtype=np.int16)
                        self.chunk_buffer.extend(audio_np)
                        
                        # Initialize chunk timer
                        if self.chunk_start_time is None:
                            self.chunk_start_time = time.time()
                        
                        # Calculate current chunk duration
                        chunk_duration = len(self.chunk_buffer) / SAMPLE_RATE
                        
                        # When chunk reaches target size, process it
                        if chunk_duration >= self.chunk_size_seconds:
                            samples_per_chunk = int(self.chunk_size_seconds * SAMPLE_RATE)
                            overlap_samples = int(self.overlap_seconds * SAMPLE_RATE)
                            
                            # Extract full chunk
                            chunk = np.array(self.chunk_buffer[:samples_per_chunk], dtype=np.int16)
                            
                            # Queue for background processing
                            self.pending_chunks.append(chunk)
                            logger.info(f"📦 Chunk ready: {chunk_duration:.1f}s (queue: {len(self.pending_chunks)})")
                            
                            # Keep overlap for next chunk
                            self.chunk_buffer = list(self.chunk_buffer[samples_per_chunk - overlap_samples:])
                            self.chunk_start_time = time.time()
                    
                except Exception as e:
                    logger.error(f"Error recording: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            
        finally:
            p.terminate()
    
    async def _background_chunk_processor(self):
        """Process chunks in background while recording continues."""
        chunk_index = 0
        
        logger.info("🔄 Chunk processor: Waiting for chunks...")
        
        while self.recording or len(self.pending_chunks) > 0:
            if len(self.pending_chunks) > 0:
                chunk = self.pending_chunks.pop(0)
                
                logger.info(f"⚡ Processing chunk {chunk_index} in background ({len(chunk)/SAMPLE_RATE:.1f}s)...")
                
                try:
                    # Encode chunk to temporary file
                    chunk_file = await self._encode_chunk(chunk, chunk_index)
                    
                    # Send to transcription API
                    result = await self._transcribe_chunk(chunk_file, chunk_index)
                    
                    if result and result.get("success"):
                        chunk_text = result.get("text", "").strip()
                        self.transcription_results.append({
                            "index": chunk_index,
                            "text": chunk_text,
                            "timestamp": time.time()
                        })
                        logger.success(f"✅ Chunk {chunk_index} transcribed: {chunk_text[:60]}...")
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_index} failed: {result.get('error', 'Unknown error')}")
                    
                    # Clean up temp file
                    try:
                        if chunk_file.exists():
                            chunk_file.unlink()
                    except:
                        pass
                    
                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_index}: {e}")
                
                chunk_index += 1
            else:
                # Wait for new chunks
                await asyncio.sleep(0.1)
        
        logger.info(f"🏁 Background chunk processor finished ({chunk_index} chunks processed)")
    
    async def _encode_chunk(self, chunk: np.ndarray, chunk_index: int) -> Path:
        """Encode a single audio chunk to WAV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        chunk_file = RECORDINGS_DIR / f"chunk_{timestamp}_{chunk_index}.wav"
        
        try:
            # Convert to audio frames format
            audio_bytes = chunk.tobytes()
            
            # Save as WAV
            p = pyaudio.PyAudio()
            wf = wave.open(str(chunk_file), 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio_bytes)
            wf.close()
            p.terminate()
            
            logger.debug(f"Encoded chunk {chunk_index} to {chunk_file}")
            return chunk_file
            
        except Exception as e:
            logger.error(f"Error encoding chunk {chunk_index}: {e}")
            raise
    
    async def _transcribe_chunk(self, chunk_file: Path, chunk_index: int) -> dict:
        """Transcribe a single audio chunk."""
        try:
            # Create session if needed
            if not self.client.session_id:
                self.client.create_session(language=None)  # Auto-detect
            
            # Get previous text for context
            prev_text = ""
            if len(self.transcription_results) > 0:
                prev_text = self.transcription_results[-1].get("text", "")
            
            # Transcribe chunk
            result = self.client.transcribe_file(str(chunk_file))
            
            if result and 'text' in result:
                text = result['text'].strip()
                
                # Apply vocabulary enhancement
                if text:
                    enhanced_text = self.vocabulary_manager.post_process_transcription(text)
                    if enhanced_text != text:
                        logger.debug(f"Chunk {chunk_index} vocabulary enhanced")
                        text = enhanced_text
                
                return {"success": True, "text": text}
            else:
                return {"success": False, "error": "No text in result"}
                
        except Exception as e:
            logger.error(f"Error transcribing chunk {chunk_index}: {e}")
            return {"success": False, "error": str(e)}
    
    def _merge_chunk_results(self) -> str:
        """Merge all chunk transcription results with overlap handling."""
        if not self.transcription_results:
            return ""
        
        # Sort by index to ensure correct order
        sorted_results = sorted(self.transcription_results, key=lambda x: x["index"])
        
        # Simple concatenation for now (can be enhanced with overlap detection)
        merged_text = " ".join([r["text"] for r in sorted_results if r["text"]])
        
        return merged_text.strip()
    
    async def _process_recording(self):
        """Save recording, transcribe, and type result."""
        if not self.frames:
            logger.warning("No audio recorded")
            return
        
        # Check if streaming mode was used and we have results
        used_streaming = (self.streaming_mode and 
                         self.total_recording_duration >= self.min_duration_for_streaming and 
                         len(self.transcription_results) > 0)
        
        if used_streaming:
            # Wait for chunk processor to finish any pending chunks
            if self.chunk_processor_task:
                logger.info("⏳ Waiting for chunk processor to finish...")
                try:
                    await asyncio.wait_for(self.chunk_processor_task, timeout=30.0)
                except asyncio.TimeoutError:
                    logger.warning("Chunk processor timeout")
            
            # Use streaming results
            logger.info(f"✨ Using streaming results ({len(self.transcription_results)} chunks)")
            text = self._merge_chunk_results()
            
            if text:
                logger.success(f"📝 Merged transcription: {text[:100]}..." if len(text) > 100 else f"📝 Transcription: {text}")
                
                # Type the text
                logger.info("⌨️ Typing transcription...")
                type_text_instant(text)
                
                # Save full recording if enabled
                if self.save_recordings:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    audio_file = RECORDINGS_DIR / f"recording_{timestamp}.wav"
                    try:
                        p = pyaudio.PyAudio()
                        wf = wave.open(str(audio_file), 'wb')
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(p.get_sample_size(FORMAT))
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(b''.join(self.frames))
                        wf.close()
                        p.terminate()
                        logger.info(f"💾 Saved full recording to {audio_file}")
                    except Exception as e:
                        logger.error(f"Error saving recording: {e}")
            else:
                logger.warning("No speech detected in streaming chunks")
            
            return
        
        # Fallback: Traditional processing (short recordings or streaming disabled)
        logger.info("📋 Using traditional processing mode")
        
        # Create temp file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if self.save_recordings:
            audio_file = RECORDINGS_DIR / f"recording_{timestamp}.wav"
        else:
            # Use temp file
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            audio_file = Path(temp_file.name)
            temp_file.close()
        
        # Save audio to file
        try:
            p = pyaudio.PyAudio()
            wf = wave.open(str(audio_file), 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            p.terminate()
            
            duration = len(self.frames) * CHUNK_SIZE / SAMPLE_RATE
            logger.info(f"Saved {duration:.1f}s of audio to {audio_file}")
            
        except Exception as e:
            logger.error(f"Error saving audio: {e}")
            return
        
        # Transcribe the file
        try:
            logger.info("Transcribing audio...")
            
            # Create session if needed
            if not self.client.session_id:
                self.client.create_session(language=None)  # Auto-detect
            
            # Transcribe file
            result = self.client.transcribe_file(str(audio_file))
            
            if result and 'text' in result:
                text = result['text'].strip()

                if text:
                    # Apply vocabulary enhancement
                    enhanced_text = self.vocabulary_manager.post_process_transcription(text)

                    if enhanced_text != text:
                        logger.info(f"Vocabulary enhanced: '{text}' -> '{enhanced_text}'")
                        text = enhanced_text

                    logger.success(f"Transcribed: {text}")

                    # Type the text
                    logger.info("Typing transcription...")
                    type_text_instant(text)

                else:
                    logger.warning("No speech detected in recording")
            else:
                logger.error("Transcription failed")
        
        except Exception as e:
            logger.error(f"Error during transcription: {e}")
        
        finally:
            # Clean up temp file if not saving
            if not self.save_recordings and audio_file.exists():
                try:
                    audio_file.unlink()
                except:
                    pass

# ============================================================================
# COMMAND HANDLERS
# ============================================================================

async def handle_command(command, recorder):
    """Handle commands from Hyprland keybinds."""
    command = command.strip().lower()
    
    if command == "start":
        recorder.start_recording()
    elif command == "stop":
        recorder.stop_recording()
    elif command == "toggle":
        if recorder.recording:
            recorder.stop_recording()
        else:
            recorder.start_recording()
    elif command == "exit":
        if recorder.recording:
            recorder.stop_recording()
        return False  # Signal to exit
    else:
        logger.warning(f"Unknown command: {command}")
    
    return True  # Continue running

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Hypr-Voice Push-to-Talk")
    parser.add_argument(
        "command",
        nargs='?',
        choices=["start", "stop", "toggle", "daemon"],
        default="daemon",
        help="Command to execute (default: daemon mode)"
    )
    parser.add_argument(
        "--server",
        default=DEFAULT_SERVER_URL,
        help=f"Whisper server URL (default: {DEFAULT_SERVER_URL})"
    )
    parser.add_argument(
        "--save-recordings",
        action="store_true",
        default=True,
        help="Save recordings to disk (default: enabled)"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save recordings (use temp files only)"
    )
    
    args = parser.parse_args()
    
    # Determine save behavior (save by default unless --no-save specified)
    save_recordings = not args.no_save
    
    # Create recorder
    recorder = PushToTalkRecorder(
        server_url=args.server,
        save_recordings=save_recordings
    )
    
    # Handle single command
    if args.command != "daemon":
        await handle_command(args.command, recorder)
    else:
        # Daemon mode - read commands from stdin
        logger.info("Hypr-Voice PTT daemon started")
        logger.info("Waiting for commands (start/stop/toggle/exit)...")
        
        # Create async stdin reader
        import sys
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)
        
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                    
                command = line.decode().strip()
                if command:
                    if not await handle_command(command, recorder):
                        break
        
        except KeyboardInterrupt:
            logger.info("Daemon stopped")

if __name__ == "__main__":
    asyncio.run(main())
