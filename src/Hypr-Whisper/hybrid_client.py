import requests
import argparse
import json
import os
import time
import asyncio
import logging
import sys
import mimetypes
from typing import Optional, Callable

import numpy as np
import pyaudio
import websockets
from io import BytesIO

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("hybrid_client.log")
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# HYBRID WHISPER CLIENT
# ============================================================================
class HybridWhisperClient:
    """Client for both REST API and WebSocket transcription."""
    
    def __init__(self, server_url="http://localhost:9090"):
        self.server_url = server_url
        self.ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://")
        self.session_id = None
        self.stream = None
        self.websocket = None
        self.protocol = None  # 'rest' or 'websocket'
    
    # ========================================================================
    # REST API METHODS
    # ========================================================================
    def create_session(self, language="en", beam_size=3, vad_filter=True):
        """Create a new transcription session via REST API."""
        url = f"{self.server_url}/sessions"
        data = {
            "language": language,
            "beam_size": beam_size,
            "vad_filter": vad_filter
        }
        
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                result = response.json()
                self.session_id = result["session_id"]
                self.protocol = "rest"
                logger.info(f"Created session: {self.session_id}")
                return self.session_id
            else:
                logger.error(f"Error creating session: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    def get_session(self, session_id=None):
        """Get session status and transcription."""
        if not session_id and not self.session_id:
            logger.error("No session ID provided")
            return None
        
        sid = session_id if session_id else self.session_id
        url = f"{self.server_url}/sessions/{sid}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error getting session: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None
    
    def list_sessions(self):
        """List all active sessions."""
        url = f"{self.server_url}/sessions"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error listing sessions: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error listing sessions: {e}")
            return None
    
    def delete_session(self, session_id=None):
        """Stop and delete a session."""
        if not session_id and not self.session_id:
            logger.error("No session ID provided")
            return None
        
        sid = session_id if session_id else self.session_id
        url = f"{self.server_url}/sessions/{sid}"
        
        try:
            response = requests.delete(url)
            if response.status_code == 200:
                if sid == self.session_id:
                    self.session_id = None
                return response.json()
            else:
                logger.error(f"Error deleting session: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return None
    
    def transcribe_file(self, audio_file, session_id=None):
        """Transcribe an audio or video file via REST API."""
        if not os.path.exists(audio_file):
            logger.error(f"File not found: {audio_file}")
            return None
        
        if not session_id and not self.session_id:
            logger.info("Creating new session for transcription")
            self.create_session()
        
        sid = session_id if session_id else self.session_id
        url = f"{self.server_url}/sessions/{sid}/transcribe"
        
        content_type, _ = mimetypes.guess_type(audio_file)
        if content_type is None:
            ext = os.path.splitext(audio_file)[1].lower()
            if ext in ['.mp4', '.mkv']:
                content_type = 'video/mp4'
            else:
                content_type = "application/octet-stream"
        
        logger.info(f"Uploading file {audio_file} with content type {content_type}")
        
        try:
            with open(audio_file, "rb") as f:
                files = {"audio_file": (os.path.basename(audio_file), f, content_type)}
                response = requests.post(url, files=files)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Error transcribing file: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error transcribing file: {e}")
            return None
    
    def get_final_transcription(self, session_id=None, wait=True, interval=0.2, inactivity_timeout=60):
        """Wait for transcription to complete and return final result. Polls every 0.2s for fast response."""
        sid = session_id if session_id else self.session_id
        if not sid:
            logger.error("No session ID provided")
            return None
        
        start_time = time.time()
        last_text = ""
        last_update_time = start_time
        
        logger.info(f"Waiting for transcription... (Inactivity timeout: {inactivity_timeout}s)")
        
        while wait:
            session = self.get_session(sid)
            if not session:
                return None
            
            current_text = session.get("text", "")
            
            if current_text != last_text:
                print(f"\r{current_text}", end="", flush=True)
                last_text = current_text
                last_update_time = time.time()
            
            if time.time() - last_update_time > inactivity_timeout:
                logger.info("Transcription complete (inactivity timeout reached).")
                return session
            
            if session.get("status") in ["stopped", "error", "completed"]:
                logger.info(f"Transcription finished with status: {session.get('status')}")
                return session
            
            time.sleep(interval)
        
        return self.get_session(sid)
    
    # ========================================================================
    # WEBSOCKET METHODS
    # ========================================================================
    async def stream_microphone_ws(self, sample_rate=16000, device=None, chunk_size=4096):
        """Stream audio from microphone to server via WebSocket using PyAudio."""
        if not self.session_id:
            logger.info("Creating new session for streaming")
            self.create_session()
        
        logger.info(f"Session ID: {self.session_id}")
        ws_url = f"{self.ws_url}/ws/{self.session_id}"
        logger.info(f"Connecting to WebSocket: {ws_url}")
        
        # Initialize PyAudio
        p = pyaudio.PyAudio()
        
        try:
            logger.info(f"Opening audio stream: rate={sample_rate}Hz, chunk={chunk_size}")
            # Only specify device if explicitly provided, otherwise use default (PULSE_SOURCE env var)
            stream_params = {
                'format': pyaudio.paInt16,
                'channels': 1,
                'rate': sample_rate,
                'input': True,
                'frames_per_buffer': chunk_size,
            }
            if device is not None:
                stream_params['input_device_index'] = device
            
            stream = p.open(**stream_params)
        except OSError as error:
            logger.error(f"Unable to access microphone: {error}")
            p.terminate()
            raise
        
        async with websockets.connect(ws_url) as websocket:
            self.websocket = websocket
            self.protocol = "websocket"
            logger.info("Connected to WebSocket server. Streaming audio...")
            
            receive_task = asyncio.create_task(self.receive_transcription_updates_ws())
            
            try:
                print("\n🎤 Streaming audio... Speak or play audio to see transcriptions\n")
                chunk_count = 0
                while True:
                    # Read audio data from PyAudio stream
                    data = stream.read(chunk_size, exception_on_overflow=False)
                    
                    # Convert bytes to numpy array (int16 -> float32)
                    audio_array = np.frombuffer(data, dtype=np.int16).astype(np.float32) / 32768.0
                    
                    # Calculate audio level for debugging (less frequent)
                    rms = np.sqrt(np.mean(audio_array**2))
                    chunk_count += 1
                    
                    # Show audio level indicator every 50 chunks (less spam)
                    if chunk_count % 50 == 0:
                        level = "🔊" if rms > 0.01 else "🔇"
                        logger.debug(f"Audio level: {rms:.5f} {level}")
                    
                    # Send to server
                    await self.websocket.send(audio_array.tobytes())
                    
                    # Small delay to prevent overwhelming the server
                    await asyncio.sleep(0.01)
            
            except KeyboardInterrupt:
                logger.info("Stopping stream...")
            
            finally:
                stream.stop_stream()
                stream.close()
                p.terminate()
                receive_task.cancel()
    
    async def receive_transcription_updates_ws(self):
        """Receive and print transcription updates from WebSocket."""
        last_text = ""
        message_count = 0
        try:
            logger.info("Started receiving transcription updates")
            print("\n" + "="*80)
            print("📝 REAL-TIME TRANSCRIPTION")
            print("="*80 + "\n")
            
            while True:
                message = await self.websocket.recv()
                message_count += 1
                
                try:
                    data = json.loads(message)
                    text = data.get('text', '')
                    status = data.get('status', '')
                    
                    # Only log every 10th message to reduce spam
                    if message_count % 10 == 0:
                        logger.debug(f"Received {message_count} messages, latest text_length={len(text)}")
                    
                    if text and text != last_text:
                        # Clear screen and show full transcription
                        # Move cursor up to overwrite previous text
                        lines_to_clear = (len(last_text) // 80) + 2 if last_text else 0
                        
                        # Clear previous lines
                        if lines_to_clear > 0:
                            print(f"\033[{lines_to_clear}A", end="")  # Move cursor up
                            for _ in range(lines_to_clear):
                                print(" " * 80)  # Clear each line
                            print(f"\033[{lines_to_clear}A", end="")  # Move cursor back up
                        
                        # Word wrap text at 80 characters
                        import textwrap
                        wrapped = textwrap.fill(text, width=80)
                        print(wrapped, flush=True)
                        last_text = text
                        
                    elif not text and message_count % 10 == 0:
                        logger.debug(f"Received {message_count} messages so far, waiting for transcription...")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON: {e}")
                    logger.debug(f"Raw message: {message}")
                
                await asyncio.sleep(0.05)
        
        except asyncio.CancelledError:
            logger.info("Stopped receiving transcription updates")
            print("\nStopped receiving updates")
        except Exception as e:
            logger.error(f"Error receiving updates: {e}", exc_info=True)
            print(f"\nError receiving updates: {e}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def list_audio_devices(verbose=False):
    """List available audio input devices using PyAudio."""
    print("\nAvailable audio input devices:")
    print("ID | Name | Channels | Sample Rate")
    print("-" * 70)
    
    p = pyaudio.PyAudio()
    found_input_devices = False
    
    try:
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                found_input_devices = True
                print(f"{i:<3}| {device_info['name']:<40} | {device_info['maxInputChannels']} | {device_info['defaultSampleRate']:.0f} Hz")
                
                if verbose:
                    print(f"\nDevice {i} details:")
                    for key, value in device_info.items():
                        print(f"  {key}: {value}")
        
        if not found_input_devices:
            logger.error("No audio input devices found!")
    
    finally:
        p.terminate()

def test_audio_device(device_id, duration=3.0):
    """Test audio recording from specified device using PyAudio."""
    logger.info(f"Testing audio recording from device {device_id} for {duration} seconds...")
    
    p = pyaudio.PyAudio()
    
    try:
        device_info = p.get_device_info_by_index(device_id)
        sample_rate = int(device_info['defaultSampleRate'])
        
        chunk_size = 4096
        frames = []
        
        stream = p.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
            input_device_index=device_id
        )
        
        logger.info(f"Recording {duration}s of audio at {sample_rate}Hz")
        num_chunks = int(sample_rate * duration / chunk_size)
        
        for _ in range(num_chunks):
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        
        # Convert to numpy array and calculate statistics
        audio_data = np.frombuffer(b''.join(frames), dtype=np.int16).astype(np.float32) / 32768.0
        rms = np.sqrt(np.mean(audio_data**2))
        peak = np.max(np.abs(audio_data))
        
        logger.info(f"Recording complete: RMS: {rms:.5f}, Peak: {peak:.5f}")
        return True
    except Exception as e:
        logger.error(f"Error testing audio device: {e}", exc_info=True)
        return False
    finally:
        p.terminate()

# ============================================================================
# MAIN CLI
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="Hybrid Whisper Transcription Client")
    parser.add_argument("--server", default="http://localhost:9090", help="Server URL")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices")
    parser.add_argument("--stream", action="store_true", help="Stream from microphone via WebSocket")
    parser.add_argument("--device", type=int, help="Audio device ID for streaming")
    parser.add_argument("--file", help="Audio or video file to transcribe via REST API")
    parser.add_argument("--timeout", type=int, default=60, help="Inactivity timeout in seconds")
    parser.add_argument("--list-sessions", action="store_true", help="List active sessions")
    parser.add_argument("--delete-session", help="Delete a session by ID")
    parser.add_argument("--session", help="Use specific session ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--test-audio", type=int, metavar="DEVICE_ID", help="Test audio input from device")
    parser.add_argument("--test-duration", type=float, default=3.0, help="Duration for audio test in seconds")
    parser.add_argument("--detailed-devices", action="store_true", help="Show detailed device information")
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    if args.list_devices:
        list_audio_devices(verbose=args.detailed_devices)
        return
    
    if args.test_audio is not None:
        test_audio_device(args.test_audio, duration=args.test_duration)
        return
    
    client = HybridWhisperClient(args.server)
    
    if args.list_sessions:
        sessions = client.list_sessions()
        if sessions:
            print("\nActive sessions:")
            for session in sessions:
                print(f"ID: {session['session_id']}")
                print(f"Status: {session['status']}")
                print(f"Text: {session['text']}")
                print("-" * 50)
        return
    
    if args.delete_session:
        result = client.delete_session(args.delete_session)
        if result:
            print(f"Session deleted: {args.delete_session}")
        return
    
    if args.file:
        logger.info(f"Transcribing file via REST API: {args.file}")
        client.create_session()
        client.transcribe_file(args.file)
        result = client.get_final_transcription(wait=True, inactivity_timeout=args.timeout)
        if result and result.get("text"):
            print(f"\nTranscription:\n{result['text']}")
        sys.exit(0)
    
    if args.stream:
        # Don't auto-detect device if not specified - let PyAudio use PULSE_SOURCE env var
        if args.device is not None:
            logger.info(f"Using specified device ID: {args.device}")
        else:
            logger.info("Using default audio device (from PULSE_SOURCE env var if set)")
        
        try:
            asyncio.run(client.stream_microphone_ws(device=args.device))
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()
