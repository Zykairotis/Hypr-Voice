#!/usr/bin/env python3
"""
Hypr-Voice Push-to-Talk Transcription
Records audio while F9 is pressed, transcribes it, and types the result.
"""

import sys
import os
import tempfile
import asyncio
import pyaudio
import wave
import time
import argparse
import subprocess
import yaml
from datetime import datetime
from pathlib import Path
from loguru import logger

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hybrid_client import HybridWhisperClient
from vocabulary_manager import get_vocabulary_manager

# ============================================================================
# CONFIGURATION
# ============================================================================

DEFAULT_SERVER_URL = "http://localhost:9090"
SAMPLE_RATE = 16000  # Standard for voice
CHUNK_SIZE = 1024
CHANNELS = 1
FORMAT = pyaudio.paInt16

# Save recordings in project directory
SCRIPT_DIR = Path(__file__).parent
RECORDINGS_DIR = SCRIPT_DIR / "recordings"

# ============================================================================
# AUDIO DEVICE CONFIGURATION
# ============================================================================

def load_audio_config():
    """Load audio configuration from audio-profile.yaml."""
    config_path = Path(__file__).parent / "config" / "audio-profile.yaml"
    
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
# WTYPE INTEGRATION
# ============================================================================

def type_text_words(text, words_per_second=10):
    """Type text word-by-word using wtype - fast for PTT."""
    words = text.split()
    delay = 1.0 / words_per_second
    
    for i, word in enumerate(words):
        # Add space before word (except first word)
        if i > 0:
            subprocess.run(["wtype", " " + word], capture_output=True)
        else:
            subprocess.run(["wtype", word], capture_output=True)
        time.sleep(delay)

def type_text_instant(text):
    """Type entire text instantly using wtype with 1ms delay (fastest possible)."""
    try:
        subprocess.run(["wtype", "-d", "1", text], capture_output=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error typing text: {e}")

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
        RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)

        if self.save_recordings:
            logger.info(f"Recordings will be saved to: {RECORDINGS_DIR}")
        else:
            logger.info("Using temp files (recordings not saved)")
    
    def start_recording(self):
        """Start recording audio (called when F9 pressed)."""
        if self.recording:
            logger.warning("Already recording!")
            return
        
        self.recording = True
        self.frames = []
        
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
        logger.info("⏹️ Recording stopped")
        
        # Visual/audio feedback
        subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], 
                      capture_output=True, check=False)
        
        # Process the recording
        asyncio.create_task(self._process_recording())
    
    async def _record_audio(self):
        """Record audio in background."""
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
            
            logger.info("Recording audio...")
            while self.recording:
                try:
                    data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                    self.frames.append(data)
                except Exception as e:
                    logger.error(f"Error recording: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            
        finally:
            p.terminate()
    
    async def _process_recording(self):
        """Save recording, transcribe, and type result."""
        if not self.frames:
            logger.warning("No audio recorded")
            return
        
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
