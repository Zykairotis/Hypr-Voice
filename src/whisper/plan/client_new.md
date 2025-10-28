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
import sounddevice as sd
import soundfile as sf
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
    
    def get_final_transcription(self, session_id=None, wait=True, interval=5, inactivity_timeout=60):
        """Wait for transcription to complete and return final result."""
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
    async def stream_microphone_ws(self, sample_rate=None, device=None, block_duration=0.1):
        """Stream audio from microphone to server via WebSocket."""
        if not self.session_id:
            logger.info("Creating new session for streaming")
            self.create_session()
        
        logger.info(f"Session ID: {self.session_id}")
        ws_url = f"{self.ws_url}/ws/{self.session_id}"
        logger.info(f"Connecting to WebSocket: {ws_url}")
        
        # Get device info
        try:
            device_info = sd.query_devices(device=device)
            logger.debug(f"Device info: {device_info}")
            
            if device_info['max_input_channels'] <= 0:
                logger.error(f"Device {device} does not support audio input")
                raise ValueError(f"Selected device {device} does not support audio input")
            
            native_sample_rate = int(device_info['default_samplerate'])
            channels = min(2, device_info['max_input_channels'])
            
            if sample_rate is None:
                sample_rate = native_sample_rate
                logger.info(f"Using device native sample rate: {sample_rate} Hz")
            
            logger.info(f"Opening audio stream: device={device}, rate={native_sample_rate}Hz, channels={channels}")
            self.stream = sd.InputStream(
                samplerate=native_sample_rate,
                channels=channels,
                dtype='float32',
                blocksize=int(native_sample_rate * block_duration),
                device=device
            )
        except Exception as e:
            logger.error(f"Error getting device info: {e}", exc_info=True)
            raise
        
        async with websockets.connect(ws_url) as websocket:
            self.websocket = websocket
            self.protocol = "websocket"
            logger.info("Connected to WebSocket server. Streaming audio...")
            
            receive_task = asyncio.create_task(self.receive_transcription_updates_ws())
            
            with self.stream:
                logger.info("Audio stream started")
                chunk_size = int(native_sample_rate * 0.1)
                
                try:
                    while True:
                        try:
                            indata, overflowed = self.stream.read(chunk_size)
                            if overflowed:
                                logger.warning("Audio buffer overflow")
                        except Exception as e:
                            logger.error(f"Error reading from audio stream: {e}")
                            await asyncio.sleep(0.1)
                            continue
                        
                        if indata is None or len(indata) == 0:
                            logger.warning("Received empty audio data")
                            await asyncio.sleep(0.1)
                            continue
                        
                        rms = np.sqrt(np.mean(indata**2)) if indata.size > 0 else 0
                        if rms < 0.001:
                            logger.debug(f"Skipping quiet audio: RMS={rms:.5f}")
                            await asyncio.sleep(0.01)
                            continue
                        
                        audio_data = indata.copy()
                        if audio_data.ndim > 1 and audio_data.shape[1] > 1:
                            audio_data = np.mean(audio_data, axis=1)
                        
                        await self.websocket.send(audio_data.astype(np.float32).tobytes())
                        logger.debug(f"Sent {len(audio_data)} audio samples")
                        
                        await asyncio.sleep(0.01)
                
                except KeyboardInterrupt:
                    logger.info("Stopping stream...")
            
            receive_task.cancel()
    
    async def receive_transcription_updates_ws(self):
        """Receive and print transcription updates from WebSocket."""
        last_text = ""
        try:
            logger.info("Started receiving transcription updates")
            while True:
                message = await self.websocket.recv()
                logger.debug(f"Received websocket message: {message[:100]}...")
                
                data = json.loads(message)
                text = data.get('text', '')
                
                if text != last_text:
                    print(f"\r{text}", end="", flush=True)
                    last_text = text
                
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
    """List available audio input devices."""
    print("\nAvailable audio input devices:")
    print("ID | Name | Channels | Sample Rate | Recommended")
    print("-" * 70)
    
    try:
        default_device = sd.default.device[0]
    except:
        default_device = None
    
    devices = sd.query_devices()
    found_input_devices = False
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            found_input_devices = True
            
            is_recommended = False
            if default_device == i:
                is_recommended = True
            elif "mic" in device['name'].lower() or "input" in device['name'].lower():
                is_recommended = True
            
            recommended = "✓" if is_recommended else ""
            print(f"{i:<3}| {device['name']:<30} | {device['max_input_channels']} | {device['default_samplerate']:.0f} Hz | {recommended}")
    
    if not found_input_devices:
        logger.error("No audio input devices found!")
    
    if verbose:
        print("\nDETAILED DEVICE INFORMATION:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"\nDevice {i}: {device['name']}")
                for key, value in device.items():
                    print(f"  {key}: {value}")

def test_audio_device(device_id, duration=3.0):
    """Test audio recording from specified device."""
    logger.info(f"Testing audio recording from device {device_id} for {duration} seconds...")
    
    try:
        device_info = sd.query_devices(device=device_id)
        sample_rate = int(device_info['default_samplerate'])
        channels = min(2, device_info['max_input_channels'])
        
        frames = int(duration * sample_rate)
        logger.info(f"Recording {duration}s of audio at {sample_rate}Hz with {channels} channels")
        recording = sd.rec(frames, samplerate=sample_rate, channels=channels, dtype='float32')
        sd.wait()
        
        rms = np.sqrt(np.mean(recording**2))
        peak = np.max(np.abs(recording))
        
        logger.info(f"Recording complete: RMS: {rms:.5f}, Peak: {peak:.5f}")
        return True
    except Exception as e:
        logger.error(f"Error testing audio device: {e}", exc_info=True)
        return False

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
        if args.device is None:
            try:
                default_device_info = sd.query_devices(kind='input')
                args.device = default_device_info['index']
                logger.info(f"Using default input device: {default_device_info['name']} (ID: {args.device})")
            except Exception as e:
                logger.error(f"Could not find default input device: {e}")
                print("Error: No audio input device specified and no default found.")
                sys.exit(1)
        
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