import requests
import argparse
import json
import os
import time
import websockets
import asyncio
import numpy as np
import sounddevice as sd
import soundfile as sf
from io import BytesIO
import logging
import sys
import mimetypes

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("client.log")
    ]
)
logger = logging.getLogger(__name__)

class WhisperClient:
    def __init__(self, server_url="http://localhost:9880"):
        self.server_url = server_url
        self.session_id = None
        self.stream = None
        # Optional async or sync callback to receive live transcription updates
        # Signature: async def on_update(text: str) -> None
        self.on_update = None

    def create_session(self, language="en", beam_size=3, vad_filter=True):
        """Create a new transcription session."""
        url = f"{self.server_url}/sessions"
        data = {
            "language": language, 
            "beam_size": beam_size,
            "vad_filter": vad_filter
        }
        
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            self.session_id = result["session_id"]
            print(f"Created session: {self.session_id}")
            return self.session_id
        else:
            print(f"Error creating session: {response.status_code} - {response.text}")
            return None

    def get_session(self, session_id=None):
        """Get session status and transcription."""
        if not session_id and not self.session_id:
            print("No session ID provided")
            return None
            
        sid = session_id if session_id else self.session_id
        url = f"{self.server_url}/sessions/{sid}"
        
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error getting session: {response.status_code} - {response.text}")
            return None

    def list_sessions(self):
        """List all active sessions."""
        url = f"{self.server_url}/sessions"
        
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error listing sessions: {response.status_code} - {response.text}")
            return None

    def delete_session(self, session_id=None):
        """Stop and delete a session."""
        if not session_id and not self.session_id:
            print("No session ID provided")
            return None
            
        sid = session_id if session_id else self.session_id
        url = f"{self.server_url}/sessions/{sid}"
        
        response = requests.delete(url)
        if response.status_code == 200:
            if sid == self.session_id:
                self.session_id = None
            return response.json()
        else:
            print(f"Error deleting session: {response.status_code} - {response.text}")
            return None

    def transcribe_file(self, audio_file, session_id=None):
        """Transcribe an audio or video file."""
        if not os.path.exists(audio_file):
            print(f"File not found: {audio_file}")
            return None

        if not session_id and not self.session_id:
            print("Creating new session for transcription")
            self.create_session()

        sid = session_id if session_id else self.session_id
        url = f"{self.server_url}/sessions/{sid}/transcribe"

        # Determine MIME type
        content_type, _ = mimetypes.guess_type(audio_file)
        if content_type is None:
            # Fallback for unknown types, especially on systems without a mime.types file
            ext = os.path.splitext(audio_file)[1].lower()
            if ext in ['.mp4', '.mkv']:
                content_type = 'video/mp4'  # Server will handle it
            else:
                content_type = "application/octet-stream"
        
        logger.info(f"Uploading file {audio_file} with content type {content_type}")

        with open(audio_file, "rb") as f:
            files = {"audio_file": (os.path.basename(audio_file), f, content_type)}
            response = requests.post(url, files=files)

        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error transcribing file: {response.status_code} - {response.text}")
            return None
    
    def get_final_transcription(self, session_id=None, wait=True, interval=5, inactivity_timeout=60):
        """Wait for transcription to complete and return final result."""
        sid = session_id if session_id else self.session_id
        if not sid:
            print("No session ID provided")
            return None
        
        start_time = time.time()
        last_text = ""
        last_update_time = start_time

        print(f"Waiting for transcription... (Inactivity timeout: {inactivity_timeout}s)")

        while wait:
            session = self.get_session(sid)
            if not session:
                return None
                
            current_text = session.get("text", "")
            
            if current_text != last_text:
                print(f"\r{current_text}", end="", flush=True)
                last_text = current_text
                last_update_time = time.time()
            
            # Check for inactivity
            if time.time() - last_update_time > inactivity_timeout:
                print("\nTranscription complete (inactivity timeout reached).")
                return session

            # Check if the session has finished or failed
            if session.get("status") in ["stopped", "error"]:
                print(f"\nTranscription finished with status: {session.get('status')}.")
                return session
                
            time.sleep(interval)

        return self.get_session(sid)

    async def stream_microphone(self, sample_rate=None, device=None, block_duration=0.1):
        """Stream audio from microphone to server via WebSocket."""
        if not self.session_id:
            logger.info("Creating new session for streaming")
            self.create_session()
            
        logger.info(f"Session ID: {self.session_id}")
        ws_url = f"{self.server_url.replace('http://', 'ws://')}/ws/{self.session_id}"
        logger.info(f"Connecting to WebSocket: {ws_url}")
        
        # Define callback to send audio chunks through websocket
        # Track audio stats for debugging
        audio_stats = {
            'chunks_sent': 0,
            'last_log_time': time.time(),
            'last_rms': 0
        }
        
        async def audio_callback(indata, frames, time_info, status):
            # Note: time_info parameter may be None, avoid using it directly
            
            if status:
                logger.warning(f"Audio status: {status}")
            
            # Convert to mono float32 
            audio_data = indata.copy()
            if audio_data.ndim > 1 and audio_data.shape[1] > 1:
                logger.debug(f"Converting {audio_data.shape[1]} channels to mono")
                audio_data = np.mean(audio_data, axis=1)
            
            # Calculate audio stats
            audio_rms = np.sqrt(np.mean(audio_data**2)) if len(audio_data) > 0 else 0
            audio_stats['last_rms'] = audio_rms
            audio_stats['chunks_sent'] += 1
            
            # Log audio stats periodically (every 5 seconds)
            now = time.time()
            if now - audio_stats['last_log_time'] > 5:
                logger.info(f"Audio stats: RMS={audio_rms:.5f}, sent {audio_stats['chunks_sent']} chunks")
                audio_stats['last_log_time'] = now
                
            # Optionally log audio level as a meter
            if logger.level <= logging.DEBUG and audio_rms > 0.001:
                meter = int(audio_rms * 50)
                logger.debug(f"Audio level: {'|' * meter} {audio_rms:.5f}")
            
            # Resample to 16kHz (what Whisper expects)
            if native_sample_rate != 16000:
                # Simple resampling
                target_length = int(len(audio_data) * 16000 / native_sample_rate)
                indices = np.linspace(0, len(audio_data) - 1, target_length)
                resampled_audio = np.interp(indices, np.arange(len(audio_data)), audio_data)
                audio_data = resampled_audio
                logger.debug(f"Resampled audio from {native_sample_rate}Hz to 16000Hz: {len(audio_data)} samples")
                
            # Send as bytes
            try:
                await self.websocket.send(audio_data.astype(np.float32).tobytes())
                logger.debug(f"Sent {len(audio_data)} audio samples to server")
            except Exception as e:
                logger.error(f"Error sending audio: {e}")
                raise
        
        # Get device info to use native sample rate
        try:
            device_info = sd.query_devices(device=device)
            logger.debug(f"Device info: {device_info}")
            
            # Check if this device actually supports input
            if device_info['max_input_channels'] <= 0:
                logger.error(f"Device {device} does not support audio input (has {device_info['max_input_channels']} input channels)")
                raise ValueError(f"Selected device {device} ({device_info['name']}) does not support audio input")
                
            native_sample_rate = int(device_info['default_samplerate'])
            channels = min(2, device_info['max_input_channels'])  # Use at most 2 channels
            
            # Use native sample rate if none specified
            if sample_rate is None:
                sample_rate = native_sample_rate
                logger.info(f"Using device native sample rate: {sample_rate} Hz")
            
            # Set up sounddevice stream with native sample rate
            logger.info(f"Opening audio stream: device={device}, rate={native_sample_rate}Hz, channels={channels}")
            self.stream = sd.InputStream(
                samplerate=native_sample_rate,
                channels=channels,
                dtype='float32',
                blocksize=int(native_sample_rate * block_duration),
                device=device
            )
            logger.info(f"Stream opened with sample rate {native_sample_rate} Hz, {channels} channels")
        except Exception as e:
            logger.error(f"Error getting device info: {e}", exc_info=True)
            raise
        
        async with websockets.connect(ws_url) as websocket:
            self.websocket = websocket
            print("Connected to WebSocket server. Streaming audio...")
            
            # Start receiving transcription updates in background
            receive_task = asyncio.create_task(self.receive_transcription_updates())
            
            # Start the audio stream
            with self.stream:
                logger.info("Audio stream started")
                
                # Capture data in small chunks with minimal delay
                chunk_size = int(native_sample_rate * 0.1)  # 100ms chunks
                
                while True:
                    try:
                        # Read audio data with error handling
                        try:
                            indata, overflowed = self.stream.read(chunk_size)
                            if overflowed:
                                logger.warning("Audio buffer overflow")
                        except Exception as e:
                            logger.error(f"Error reading from audio stream: {e}")
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Skip if we got empty data
                        if indata is None or len(indata) == 0:
                            logger.warning("Received empty audio data")
                            await asyncio.sleep(0.1)
                            continue
                            
                        # Skip if audio level is too low (silence)
                        rms = np.sqrt(np.mean(indata**2)) if indata.size > 0 else 0
                        if rms < 0.001:  # Skip very quiet audio
                            logger.debug(f"Skipping quiet audio: RMS={rms:.5f}")
                            await asyncio.sleep(0.01)
                            continue
                        
                        # Send audio data
                        await audio_callback(indata, len(indata), None, None)
                        
                        # Sleep a bit to avoid flooding
                        await asyncio.sleep(0.01)
                        
                    except KeyboardInterrupt:
                        print("\nStopping stream...")
                        break
                    except Exception as e:
                        print(f"Error in audio streaming: {e}")
                        break
            
            # Cleanup
            receive_task.cancel()
            
    async def receive_transcription_updates(self):
        """Receive and print transcription updates from WebSocket."""
        last_text = ""
        try:
            logger.info("Started receiving transcription updates")
            while True:
                message = await self.websocket.recv()
                logger.debug(f"Received websocket message: {message[:100]}...")
                
                data = json.loads(message)
                text = data.get('text', '')
                
                # Only update if the text has actually changed
                if text != last_text:
                    # Clear line and print updated transcription for user (full version)
                    print(f"\r{text}", end="", flush=True)
                    last_text = text
                    # Forward to registered callback if any
                    try:
                        if callable(self.on_update) and text:
                            if asyncio.iscoroutinefunction(self.on_update):
                                asyncio.create_task(self.on_update(text))
                            else:
                                # Run sync callbacks in a thread to avoid blocking
                                asyncio.get_running_loop().run_in_executor(None, self.on_update, text)
                    except Exception as cb_err:
                        logger.error(f"on_update callback error: {cb_err}")
                
                await asyncio.sleep(0.05) # Small delay to prevent busy-waiting
                
        except asyncio.CancelledError:
            logger.info("Stopped receiving transcription updates")
            print("\nStopped receiving updates")
        except Exception as e:
            logger.error(f"Error receiving updates: {e}", exc_info=True)
            print(f"\nError receiving updates: {e}")

def list_audio_devices(verbose=False):
    """List available audio input devices."""
    print("\nAvailable audio input devices:")
    print("ID | Name | Channels | Sample Rate | Recommended")
    print("-" * 70)
    
    # Get default device
    try:
        default_device = sd.default.device[0]  # Default input device
    except:
        default_device = None
    
    devices = sd.query_devices()
    found_input_devices = False
    
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            found_input_devices = True
            
            # Check if this is likely to be a good audio input device
            is_recommended = False
            if default_device == i:
                is_recommended = True
            elif "mic" in device['name'].lower() or "input" in device['name'].lower():
                is_recommended = True
                
            recommended = "✓" if is_recommended else ""
            
            print(f"{i:<3}| {device['name']:<30} | {device['max_input_channels']} | {device['default_samplerate']:.0f} Hz | {recommended}")
    
    if not found_input_devices:
        print("No audio input devices found! Check your system audio settings.")
        print("You may need to connect a microphone or enable an input device.")
        
    # Print recommendations
    print("\nRECOMMENDATIONS:")
    if default_device is not None:
        print(f"* Try device {default_device} first (system default input).")
    print("* Look for devices with 'mic' or 'input' in their name.")
    print("* Try running a device test before streaming:")
    
    # Show more detailed info for every device if verbose is enabled
    if verbose:
        print("\nDETAILED DEVICE INFORMATION:")
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                print(f"\nDevice {i}: {device['name']}")
                for key, value in device.items():
                    print(f"  {key}: {value}")
                print()
                
def test_audio_device(device_id, duration=3.0):
    """Test audio recording from specified device."""
    logger.info(f"Testing audio recording from device {device_id} for {duration} seconds...")
    
    try:
        # Get device info to determine sample rate
        device_info = sd.query_devices(device=device_id)
        sample_rate = int(device_info['default_samplerate'])
        channels = min(2, device_info['max_input_channels'])
        
        # Calculate frame count
        frames = int(duration * sample_rate)
        
        # Record audio
        logger.info(f"Recording {duration}s of audio at {sample_rate}Hz with {channels} channels")
        recording = sd.rec(frames, samplerate=sample_rate, channels=channels, dtype='float32')
        
        # Show a progress bar
        from tqdm import tqdm
        for _ in tqdm(range(int(duration * 10)), desc="Recording"):
            time.sleep(0.1)
            
        # Wait for recording to complete
        sd.wait()
        
        # Calculate audio stats
        rms = np.sqrt(np.mean(recording**2))
        peak = np.max(np.abs(recording))
        
        logger.info(f"Recording complete: {frames} frames, RMS: {rms:.5f}, Peak: {peak:.5f}")
        
        # Show a simple visualization of the waveform
        if logger.level <= logging.DEBUG:
            # Calculate average amplitude per segment
            segments = 40
            chunk_size = len(recording) // segments
            
            print("\nAudio waveform:")
            for i in range(segments):
                if i * chunk_size < len(recording):
                    chunk = recording[i*chunk_size:(i+1)*chunk_size]
                    amp = np.max(np.abs(chunk)) * 50
                    print(f"|{'*' * int(amp)}")
            
        return True
    except Exception as e:
        logger.error(f"Error testing audio device: {e}", exc_info=True)
        return False

def main():
    parser = argparse.ArgumentParser(description="Whisper Transcription Client")
    parser.add_argument("--server", default="http://localhost:9880", help="Server URL")
    parser.add_argument("--list-devices", action="store_true", help="List audio devices")
    parser.add_argument("--stream", action="store_true", help="Stream from microphone")
    parser.add_argument("--device", type=int, help="Audio device ID for streaming")
    parser.add_argument("--file", help="Audio or video file to transcribe")
    parser.add_argument("--timeout", type=int, default=60, help="Inactivity timeout in seconds for waiting for transcription")
    parser.add_argument("--list-sessions", action="store_true", help="List active sessions")
    parser.add_argument("--delete-session", help="Delete a session by ID")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    parser.add_argument("--debug-audio", action="store_true", help="Enable audio debugging")
    parser.add_argument("--test-audio", type=int, metavar="DEVICE_ID", help="Test audio input from device")
    parser.add_argument("--test-duration", type=float, default=3.0, help="Duration for audio test in seconds")
    parser.add_argument("--detailed-devices", action="store_true", help="Show detailed device information")
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")
    
    # Configure sounddevice debugging
    if args.debug_audio:
        # sounddevice doesn't have a built-in logger, so we'll handle it manually
        # Set higher log level to capture more details
        logger.setLevel(logging.DEBUG)
        logger.info("Audio debugging enabled - will show detailed stream information")
    
    if args.list_devices:
        list_audio_devices(verbose=args.detailed_devices)
        return
    
    if args.test_audio is not None:
        test_audio_device(args.test_audio, duration=args.test_duration)
        return
        
    client = WhisperClient(args.server)
    
    if args.list_sessions:
        sessions = client.list_sessions()
        if sessions:
            print("\nActive sessions:")
            for session in sessions:
                created = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(session["created_at"]))
                last_active = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(session["last_active"]))
                print(f"ID: {session['session_id']}")
                print(f"Status: {session['status']}")
                print(f"Created: {created}")
                print(f"Last Active: {last_active}")
                print(f"Text: {session['text']}")
                print("-" * 50)
        return
        
    if args.delete_session:
        result = client.delete_session(args.delete_session)
        if result:
            print(f"Session deleted: {args.delete_session}")
        return
        
    if args.file:
        client.create_session()
        print(f"Transcribing file: {args.file}")
        client.transcribe_file(args.file)
        result = client.get_final_transcription(wait=True, inactivity_timeout=args.timeout)
        if result and result.get("text"):
            print(f"\nTranscription:\n{result['text']}")
        sys.exit(0)
        
    if args.stream:
        # If no device is specified, try to find the default input device
        if args.device is None:
            try:
                default_device_info = sd.query_devices(kind='input')
                args.device = default_device_info['index']
                logger.info(f"No input device specified. Using default: {default_device_info['name']} (ID: {args.device})")
            except Exception as e:
                logger.error(f"Could not find a default input device: {e}")
                print("Error: No audio input device specified and no default found. Please specify one with --device.")
                sys.exit(1)
        asyncio.run(client.stream_microphone(device=args.device))
        return
        
    # If no specific action, show help
    parser.print_help()

if __name__ == "__main__":
    main() 