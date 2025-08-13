#!/usr/bin/env python3
"""
Hypr-Voice: Voice-driven input system for Hyprland/Arch Linux
Main client with LLM context enhancement and MCP tools integration
"""

import os
import sys
import asyncio
import json
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Lazy-import heavy deps when needed to avoid optional dependency issues in PTT mode
# Context engine is imported lazily in _ensure_context_engine()
from loguru import logger
from dotenv import load_dotenv
import argparse
import socket

# Load environment variables
load_dotenv()

class HyprVoice:
    """Main Hypr-Voice client with context-aware transcription"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """Initialize Hypr-Voice client"""
        self.config_dir = config_dir or Path(__file__).parent / "config"
        self.context_engine = None
        self.whisper_server_url = os.getenv("WHISPER_SERVER_URL", "http://localhost:9880")
        self.current_app = None
        
        # Recording state
        self.is_recording = False
        self.recording_audio = []
        self.stream = None
        self.app_at_recording_start = None
        
        # Metrics / timing
        self._record_started_at = 0.0
        self._total_frames = 0
        
        # Load audio configuration
        self.audio_config = self._load_audio_config()
        
        # Audio device selection from config or env
        audio_devices = self.audio_config.get('devices', {})
        self.primary_device = audio_devices.get('primary', {}).get('name', 'default')
        self.secondary_device = audio_devices.get('secondary', {}).get('name', 'default')
        self.auto_fallback = audio_devices.get('auto_fallback', True)
        
        # Override with env if set
        if os.getenv("HYPR_VOICE_INPUT_DEVICE"):
            self.primary_device = os.getenv("HYPR_VOICE_INPUT_DEVICE")
        
        self.input_device = self.primary_device
        
        # High-quality audio settings from config
        audio_quality = self.audio_config.get('quality', {})
        self.input_samplerate = audio_quality.get('sample_rate', 48000)  # Default to high quality
        self.input_channels = audio_quality.get('channels', 1)
        self.input_dtype = audio_quality.get('dtype', 'float32')
        self.blocksize = audio_quality.get('blocksize', 2048)
        self.fallback_sample_rates = audio_quality.get('fallback_sample_rates', [44100, 48000, 32000, 24000, 16000])
        
        # Whisper settings
        whisper_config = self.audio_config.get('whisper', {})
        self.whisper_target_rate = whisper_config.get('target_sample_rate', 16000)
        self.keep_originals = whisper_config.get('keep_originals', True)
        
        # Create directories for recordings
        self.recordings_dir = Path(__file__).parent / "recordings"
        if self.keep_originals:
            self.originals_dir = self.recordings_dir / "originals"
            self.processed_dir = self.recordings_dir / "processed"
            self.originals_dir.mkdir(parents=True, exist_ok=True)
            self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Notification actions
        self.actions = {
            "COPY": self.copy_to_clipboard,
            "IMPROVE": self.improve_text,
            "EDIT": self.edit_text,
            "PASTE": self.paste_to_cursor
        }
        
        logger.info("Initializing Hypr-Voice...")
    
    async def _ensure_context_engine(self) -> bool:
        """Lazily import and initialize the context engine. Returns True if available."""
        if self.context_engine is not None:
            return True
        try:
            from context_engine_cognee import CogneeContextEngine
            self.context_engine = CogneeContextEngine(config_dir=self.config_dir)
            await self.context_engine.initialize()
            return True
        except Exception as e:
            logger.warning(f"Context engine unavailable, proceeding without enhancements: {e}")
            self.context_engine = None
            return False
    
    async def initialize(self):
        """Initialize async components"""
        # Check for sounddevice
        try:
            import sounddevice as sd
            logger.info(f"Audio devices available: {len(sd.query_devices())}")
        except ImportError:
            logger.warning("sounddevice not installed - recording won't work")
        
        # Get current active window (context engine is optional and lazy)
        await self.update_active_window()
        
        # Create recordings directory
        recordings_dir = Path(__file__).parent / "recordings"
        recordings_dir.mkdir(exist_ok=True)
        
        logger.info("Hypr-Voice initialized successfully")
    
    def _load_audio_config(self) -> dict:
        """Load audio configuration from audio_config.yaml"""
        audio_config_path = self.config_dir / "audio_config.yaml"
        
        # Default configuration if file doesn't exist
        default_config = {
            'audio': {
                'quality': {
                    'sample_rate': 48000,
                    'channels': 1,
                    'dtype': 'float32',
                    'blocksize': 2048,
                    'fallback_sample_rates': [44100, 48000, 32000, 24000, 16000]
                },
                'devices': {
                    'primary': {'name': 'default'},
                    'secondary': {'name': 'default'},
                    'auto_fallback': True,
                    'list_on_startup': True
                },
                'recording': {
                    'max_duration': 60,
                    'silence_threshold': 0.01,
                    'silence_duration': 2.0,
                    'format': 'wav'
                },
                'whisper': {
                    'target_sample_rate': 16000,
                    'keep_originals': True,
                    'originals_dir': 'recordings/originals',
                    'processed_dir': 'recordings/processed'
                }
            }
        }
        
        if audio_config_path.exists():
            try:
                with open(audio_config_path, 'r') as f:
                    import yaml
                    config = yaml.safe_load(f)
                    logger.info(f"Loaded audio config from {audio_config_path}")
                    
                    # List devices on startup if configured
                    if config.get('audio', {}).get('devices', {}).get('list_on_startup', False):
                        logger.info("Listing available audio devices:")
                        self.print_audio_devices()
                    
                    return config.get('audio', default_config['audio'])
            except Exception as e:
                logger.warning(f"Failed to load audio config: {e}. Using defaults.")
                return default_config['audio']
        else:
            logger.info(f"No audio config found at {audio_config_path}. Using defaults.")
            return default_config['audio']
    
    async def update_active_window(self):
        """Get current active window from Hyprland"""
        try:
            # Use hyprctl to get active window
            result = subprocess.run(
                ["hyprctl", "activewindow", "-j"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                window_info = json.loads(result.stdout)
                app_class = window_info.get("class", "").lower()
                
                if app_class != self.current_app:
                    self.current_app = app_class
                    # Update context engine profile if available
                    if self.context_engine:
                        try:
                            await self.context_engine.set_active_application(app_class)
                        except Exception as _e:
                            logger.debug(f"Context engine not ready: {_e}")
                    
                    logger.info(f"Active application: {app_class}")
            
        except Exception as e:
            logger.error(f"Failed to get active window: {e}")
            self.current_app = "default"
    
    async def monitor_active_window(self):
        """Monitor active window changes every second"""
        while True:
            await self.update_active_window()
            await asyncio.sleep(1)
    
    def _resolve_input_device(self, device_spec: Optional[str]):
        """Resolve an input device spec (index or name substring) to a sounddevice-compatible value.
        Returns int index, exact name string, or None for default.
        """
        try:
            import sounddevice as sd
        except Exception:
            return None
        
        if not device_spec or str(device_spec).strip().lower() in {"default", "none"}:
            return None
        
        # If numeric index provided
        try:
            idx = int(device_spec)
            # Validate the index exists and has input channels
            devices = sd.query_devices()
            if 0 <= idx < len(devices) and devices[idx].get("max_input_channels", 0) > 0:
                return idx
            else:
                logger.warning(f"Device index {idx} invalid or has no input channels")
        except ValueError:
            pass
        
        # Try case-insensitive substring match on device name (input-capable only)
        try:
            devices = sd.query_devices()
            for i, d in enumerate(devices):
                if d.get("max_input_channels", 0) > 0 and str(device_spec).lower() in d.get("name", "").lower():
                    logger.info(f"Found device '{d.get('name')}' at index {i}")
                    return i
        except Exception:
            pass
        
        logger.warning(f"Input device '{device_spec}' not found; using system default")
        return None
    
    def get_input_device_info(self) -> Optional[Dict[str, Any]]:
        """Return info about the currently selected input device."""
        try:
            import sounddevice as sd
            dev = self._resolve_input_device(self.input_device)
            info = sd.query_devices(dev, kind='input')
            default = sd.default.device
            default_in = default[0] if isinstance(default, (list, tuple)) else default
            is_default = dev is None
            name = info.get('name', 'unknown')
            max_in = info.get('max_input_channels')
            hostapi = info.get('hostapi')
            default_sr = int(info.get('default_samplerate') or 0)
            return {"name": name, "index": (default_in if is_default else dev), "is_default": is_default, "max_input_channels": max_in, "hostapi": hostapi, "default_samplerate": default_sr}
        except Exception as e:
            logger.warning(f"Unable to get input device info: {e}")
            return None
    
    @staticmethod
    def print_audio_devices():
        """Print available audio devices with a star next to the default input."""
        try:
            import sounddevice as sd
            devices = sd.query_devices()
            default = sd.default.device
            default_in = default[0] if isinstance(default, (list, tuple)) else default
            print("Audio devices ( * = default input ):")
            for i, d in enumerate(devices):
                star = "*" if i == default_in else " "
                mi = d.get('max_input_channels', 0)
                mo = d.get('max_output_channels', 0)
                print(f"{star} {i:>3} {d.get('name','unknown')} ({mi} in, {mo} out)  default_sr={int(d.get('default_samplerate') or 0)}")
        except Exception as e:
            print(f"Failed to list devices: {e}", file=sys.stderr)
    
    @staticmethod
    def _to_mono(data):
        import numpy as np
        if data.ndim == 2 and data.shape[1] > 1:
            return data.mean(axis=1)
        return data.reshape(-1)
    
    @staticmethod
    def _resample_audio(x, from_sr: int, to_sr: int):
        """Simple linear resampling using numpy.interp; expects 1D float32 array."""
        import numpy as np
        if from_sr == to_sr:
            return x
        n_old = x.shape[0]
        n_new = max(1, int(round(n_old * to_sr / from_sr)))
        xp = np.linspace(0.0, 1.0, num=n_old, endpoint=False, dtype=np.float64)
        x_new = np.linspace(0.0, 1.0, num=n_new, endpoint=False, dtype=np.float64)
        y = np.interp(x_new, xp, x.astype(np.float64))
        return y.astype(np.float32)
    
    async def start_recording(self):
        """Start audio recording"""
        if self.is_recording:
            logger.warning("Already recording")
            return
        
        logger.info("=== STARTING RECORDING ===")
        
        self.is_recording = True
        self.recording_audio = []
        self.app_at_recording_start = self.current_app  # Save app at start
        
        # Mark start time for optional min-duration guard
        try:
            import time as _time
            self._record_started_at = _time.monotonic()
            logger.info(f"Recording start time: {self._record_started_at}")
        except Exception:
            self._record_started_at = 0.0
        
        # Reset counters
        self._total_frames = 0
        
        logger.info(f"Started recording (app: {self.app_at_recording_start})")
        self.notify("Recording started...", f"Context: {self.app_at_recording_start}", urgency="low")
        
        # Start recording with sounddevice
        try:
            import sounddevice as sd
            import numpy as np
            
            # Log selected input device
            info = self.get_input_device_info()
            if info:
                logger.info(f"Using input device: {info['name']} (index {info['index']})")
            
            def audio_callback(indata, frames, time, status):
                if status:
                    logger.warning(f"Audio callback status: {status}")
                if self.is_recording:
                    # Check recording flag before appending (for quick stop)
                    if self.is_recording:  # Double-check flag
                        self.recording_audio.append(indata.copy())
                    self._total_frames += int(frames)
                    # Log every 10th chunk to track recording progress
                    if len(self.recording_audio) % 10 == 0:
                        logger.debug(f"Recording: {len(self.recording_audio)} chunks, {self._total_frames} frames")
            
            # Try primary device first, then fallback to secondary if configured
            devices_to_try = [self.input_device]
            if self.auto_fallback and self.secondary_device != self.input_device:
                devices_to_try.append(self.secondary_device)
            
            opened = False
            for device_spec in devices_to_try:
                dev = self._resolve_input_device(device_spec)
                
                # Get device info if possible
                try:
                    dinfo = sd.query_devices(dev, kind='input')
                    dev_default_sr = int(dinfo.get('default_samplerate') or 48000)
                    device_name = dinfo.get('name', 'unknown')
                except Exception:
                    dinfo = None
                    dev_default_sr = 48000
                    device_name = 'unknown'
                
                logger.info(f"Trying device: {device_name} (spec: {device_spec})")
                
                last_error = None
                # Use configured channels or detect from device
                channels_options = [self.input_channels]
                if self.input_channels == 1 and dinfo and int(dinfo.get('max_input_channels') or 0) >= 2:
                    channels_options.append(2)  # Try stereo as fallback
                
                # Try configured sample rate first, then fallbacks
                sample_rates = [self.input_samplerate] + [sr for sr in self.fallback_sample_rates if sr != self.input_samplerate]
                
                for sr_try in sample_rates:
                    for ch_try in channels_options:
                        for dtype_try in (self.input_dtype, 'int16', 'float32'):
                            try:
                                # Use configured blocksize
                                block_sz = self.blocksize
                                self.stream = sd.InputStream(
                                    callback=audio_callback,
                                    channels=ch_try,
                                    samplerate=sr_try,
                                    dtype=dtype_try,
                                    device=dev,
                                    blocksize=block_sz
                                )
                                self.stream.start()
                                # Update actual recording params
                                self.actual_samplerate = sr_try
                                self.actual_channels = ch_try
                                self.actual_dtype = dtype_try
                                self.actual_device = device_name
                                logger.info(f"✅ High-quality input stream opened!")
                                logger.info(f"   Device: {device_name}")
                                logger.info(f"   Quality: {sr_try} Hz, {ch_try} channel(s), {dtype_try}")
                                logger.info(f"   Blocksize: {block_sz}")
                                opened = True
                                break
                            except Exception as e_open:
                                last_error = e_open
                                continue
                        if opened:
                            break
                    if opened:
                        break
                if opened:
                    break
            
            if not opened:
                raise last_error or RuntimeError("Failed to open input stream")
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            self.is_recording = False
            self._total_frames = 0
            self.notify("Recording Error", str(e), urgency="critical")
    
    async def stop_recording(self):
        """Stop recording and process audio - optimized for quick response"""
        # Check if already stopped (handles race conditions)
        if not self.is_recording and not hasattr(self, 'stream'):
            logger.debug("Already stopped - ignoring duplicate STOP")
            return
        
        logger.info("=== STOPPING RECORDING ===")
        
        # Immediately set flag to stop accepting new audio
        self.is_recording = False
        
        # Calculate recording duration
        try:
            import time as _time
            if hasattr(self, '_record_started_at') and self._record_started_at > 0:
                duration = _time.monotonic() - self._record_started_at
                logger.info(f"Recording duration: {duration:.3f} seconds")
            
            # Log recording duration but don't enforce minimum for push-to-talk
            if hasattr(self, '_record_started_at') and self._record_started_at > 0:
                elapsed = int((_time.monotonic() - self._record_started_at) * 1000)
                logger.info(f"Recording duration: {elapsed}ms")
                # Remove minimum duration check - user controls timing with key press/release
        except Exception as e:
            logger.warning(f"Could not calculate duration: {e}")
        
        # Stop the stream immediately
        try:
            if hasattr(self, 'stream') and self.stream:
                # Stop stream first (stops audio callback)
                try:
                    self.stream.stop()
                except:
                    pass
                # Then close it
                try:
                    self.stream.close()
                except:
                    pass
                self.stream = None
                logger.info("Audio stream stopped")
        except Exception as e:
            logger.warning(f"Stream stop error (non-critical): {e}")
        
        logger.info(f"Recorded {len(self.recording_audio)} audio chunks, total frames: {self._total_frames}")
        
        # Check if we have any audio data
        if not self.recording_audio:
            logger.error("No audio chunks recorded!")
            self.notify("No Audio", "No audio data was captured during recording", urgency="normal")
            return
        
        # Double-check we're actually stopped before processing
        if self.is_recording:
            logger.warning("Still recording flag set after stop - clearing")
            self.is_recording = False
        
        self.notify("Processing...", "Transcribing audio", urgency="low")
        
        # Process recorded audio
        try:
            import numpy as np
            import soundfile as sf
            
            # Concatenate all recorded chunks
            audio_data = np.concatenate(self.recording_audio, axis=0)
            
            # Log captured stats
            frames = int(self._total_frames)
            sr = int(self.input_samplerate)
            dur = frames / sr if sr else 0.0
            logger.info(f"Captured frames={frames}, samplerate={sr}, duration={dur:.2f}s, chunks={len(self.recording_audio)}")
            
            # Convert to mono 1D float32
            mono = self._to_mono(audio_data).astype('float32')
            
            # Normalize if original capture was int16
            if self.input_dtype == 'int16':
                mono = mono / 32768.0
            
            # Resample to 16k if necessary
            if self.input_samplerate != 16000:
                mono = self._resample_audio(mono, self.input_samplerate, 16000)
            
            # Create debug directory if it doesn't exist
            recordings_dir = Path(__file__).parent / "recordings"
            recordings_dir.mkdir(exist_ok=True)
            
            # Save recording with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
            recording_path = recordings_dir / f"recording_{timestamp}.wav"
            sf.write(str(recording_path), mono, 16000)
            logger.info(f"Saved recording to {recording_path}")
            
            # Send to transcription server
            await self.transcribe_audio_file(str(recording_path))
            
        except Exception as e:
            logger.error(f"Failed to process recording: {e}")
            self.notify("Processing Error", str(e), urgency="critical")
        
        finally:
            # Clean up
            self.recording_audio = []
            self.app_at_recording_start = None
            self._total_frames = 0
    
    async def force_stop_recording(self):
        """Emergency stop: abort stream immediately and discard buffers (no transcription)."""
        try:
            logger.warning("Force-stopping recording: aborting stream and discarding buffers")
            # Ensure flag is down so callback stops appending
            self.is_recording = False
            # Stop/abort stream immediately
            try:
                if hasattr(self, 'stream') and self.stream:
                    try:
                        # Abort is immediate if available, else stop
                        if hasattr(self.stream, 'abort'):
                            self.stream.abort()
                        else:
                            self.stream.stop()
                    except Exception:
                        pass
                    try:
                        self.stream.close()
                    except Exception:
                        pass
                    self.stream = None
            except Exception as e:
                logger.debug(f"Force-stop stream error: {e}")
            
            # Discard any captured audio and reset counters
            try:
                self.recording_audio = []
            except Exception:
                pass
            self._total_frames = 0
            self._record_started_at = 0.0
            self.app_at_recording_start = None
            
            # Notify user
            self.notify("Recording aborted", "Recording force-stopped; buffers discarded", urgency="normal")
            logger.info("Force stop complete")
        except Exception as e:
            logger.error(f"Force stop encountered an error: {e}")
    
    async def transcribe_audio_file(self, audio_file_path: str):
        """Transcribe audio file using the server API"""
        try:
            import requests
            import time
            
            server_url = self.whisper_server_url
            # If someone configured 0.0.0.0 (bind address), use localhost for client connections
            if '0.0.0.0' in server_url:
                server_url = server_url.replace('0.0.0.0', 'localhost')
            
            # 1) Create session
            session_payload = {
                "language": "en",
                "beam_size": 3,
                "vad_filter": False,
                "compute_type": "int8",
                "device": "auto"
            }
            
            logger.info("Creating transcription session...")
            sess_resp = requests.post(f"{server_url}/sessions", json=session_payload, timeout=10)
            sess_resp.raise_for_status()
            sess_json = sess_resp.json()
            
            # Be flexible about field naming from server
            session_id = (
                sess_json.get("session_id")
                or sess_json.get("id")
                or sess_json.get("uuid")
                or sess_json.get("sessionId")
            )
            
            if not session_id:
                raise Exception("No session ID returned from server")
            
            logger.info(f"Created session: {session_id}")
            
            # 2) Upload audio file
            logger.info(f"Uploading audio file: {audio_file_path}")
            with open(audio_file_path, 'rb') as f:
                files = {"audio_file": (os.path.basename(audio_file_path), f, 'audio/wav')}
                upload_resp = requests.post(
                    f"{server_url}/sessions/{session_id}/transcribe", 
                    files=files, 
                    timeout=30
                )
            
            upload_resp.raise_for_status()
            logger.info(f"Successfully uploaded file to session {session_id}")
            
            # 3) Poll for transcription result
            logger.info("Waiting for transcription...")
            start_poll = time.time()
            poll_timeout = int(os.getenv("HYPR_VOICE_POLL_TIMEOUT", "90"))
            transcription = None
            
            while time.time() - start_poll < poll_timeout:
                try:
                    status_resp = requests.get(f"{server_url}/sessions/{session_id}", timeout=10)
                    status_resp.raise_for_status()
                    status_json = status_resp.json()
                    
                    # Try multiple fields for transcription text
                    text = (
                        (status_json.get('text') or '')
                        or (status_json.get('transcription') or '')
                        or (status_json.get('transcript') or '')
                        or (status_json.get('result') or '')
                        or (status_json.get('output') or '')
                    )
                    
                    # If segments are provided, concatenate
                    if (not text) and isinstance(status_json.get('segments'), list):
                        try:
                            text = ' '.join(seg.get('text', '') for seg in status_json['segments'])
                        except Exception:
                            pass
                    
                    # If nested under data
                    if (not text) and isinstance(status_json.get('data'), dict):
                        d = status_json['data']
                        text = (
                            (d.get('text') or '')
                            or (d.get('transcription') or '')
                            or (d.get('transcript') or '')
                        )
                    
                    text = (text or '').strip()
                    status = status_json.get('status')
                    
                    logger.info(f"Polling session {session_id}: status={status}, text_length={len(text)}")
                    
                    if text:
                        transcription = text
                        logger.info(f"Transcription complete: {transcription}")
                        break
                    
                    if status in ("stopped", "error", "failed", "completed"):
                        logger.info(f"Session ended with status: {status}")
                        break
                    
                except Exception as e:
                    logger.warning(f"Polling error: {e}")
                
                await asyncio.sleep(1)  # Wait 1 second before next poll
            
            # Process transcription
            if transcription:
                await self.process_transcription(transcription)
            else:
                logger.warning("No transcription text available")
                self.notify("No speech detected", "Try speaking louder or clearer", urgency="normal")
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            self.notify("Transcription Error", str(e), urgency="critical")
    
    async def process_transcription(self, text: str):
        """Process transcription with context-aware improvements"""
        try:
            # Process with context engine (optional)
            processed = text
            try:
                if await self._ensure_context_engine():
                    processed = await self.context_engine.process_transcription(
                        text,
                        improve=True,  # Improve by default
                        use_memory=True,
                        use_tools=True
                    )
            except Exception as _e:
                logger.debug(f"Context processing skipped: {_e}")
            
            # Show notification with action buttons
            self.notify(
                "Transcription Ready",
                processed[:200] + "..." if len(processed) > 200 else processed,
                actions=["COPY", "IMPROVE", "EDIT", "PASTE"],
                urgency="normal"
            )
            
            # Auto-paste if configured
            if os.getenv("AUTO_PASTE", "false").lower() == "true":
                self.paste_to_cursor(processed)
            else:
                # Just copy to clipboard by default
                self.copy_to_clipboard(processed)
            
            return processed
            
        except Exception as e:
            logger.error(f"Failed to process transcription: {e}")
            self.notify("Error", str(e), urgency="critical")
            return text
    
    async def listen_for_commands(self):
        """Listen for commands from Hyprland via socket - optimized for responsiveness"""
        import socket
        import os
        
        # Create socket for IPC
        socket_path = "/tmp/hypr-voice.sock"
        
        # Remove old socket if exists
        if os.path.exists(socket_path):
            os.unlink(socket_path)
        
        # Create Unix socket - non-blocking for better responsiveness
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.setblocking(False)  # Non-blocking socket
        server.bind(socket_path)
        server.listen(10)  # Increased backlog for faster handling
        
        # Make socket accessible
        os.chmod(socket_path, 0o666)
        
        logger.info(f"Listening for commands on {socket_path}")
        
        # Track last command time for debouncing
        last_start_time = 0
        last_stop_time = 0
        
        while True:
            try:
                # Use asyncio-friendly socket handling
                await asyncio.sleep(0.001)  # Very short sleep for high responsiveness
                
                try:
                    conn, addr = server.accept()
                    conn.setblocking(False)  # Non-blocking connection
                    
                    # Try to read command immediately
                    try:
                        data = conn.recv(1024).decode('utf-8').strip()
                    except BlockingIOError:
                        # No data yet, give it a tiny moment
                        await asyncio.sleep(0.001)
                        try:
                            data = conn.recv(1024).decode('utf-8').strip()
                        except:
                            data = ""
                    
                    current_time = time.monotonic()
                    
                    if data == "START":
                        # Debounce START commands (ignore if too close to last one)
                        if current_time - last_start_time > 0.1:  # 100ms debounce
                            logger.info("=== IPC: START command ===")
                            if not self.is_recording:
                                # Send response BEFORE starting to avoid timeout
                                try:
                                    conn.setblocking(False)
                                    conn.send(b"OK")
                                except:
                                    pass  # Don't block on send
                                asyncio.create_task(self.start_recording())  # Non-blocking
                            else:
                                try:
                                    conn.send(b"ALREADY_RECORDING")
                                except:
                                    pass
                            last_start_time = current_time
                        else:
                            try:
                                conn.send(b"DEBOUNCED")
                            except:
                                pass
                            
                    elif data == "STOP":
                        # Always process STOP immediately - high priority
                        logger.info("=== IPC: STOP command ===")
                        if self.is_recording:
                            # Force stop immediately
                            self.is_recording = False  # Stop flag first
                            # Send response BEFORE cleanup to avoid timeout
                            try:
                                conn.setblocking(False)
                                conn.send(b"OK")
                            except:
                                pass  # Don't block on send
                            # Now do cleanup async
                            asyncio.create_task(self.stop_recording())  # Then cleanup
                        else:
                            try:
                                conn.send(b"NOT_RECORDING")
                            except:
                                pass
                        last_stop_time = current_time
                        
                    elif data == "FORCE_STOP":
                        # Emergency force stop - highest priority, discard buffers
                        logger.warning("=== IPC: FORCE_STOP command ===")
                        self.is_recording = False
                        try:
                            conn.setblocking(False)
                            conn.send(b"OK")
                        except:
                            pass
                        asyncio.create_task(self.force_stop_recording())
                        
                    elif data == "STATUS":
                        info = self.get_input_device_info()
                        payload = {
                            "state": "recording" if self.is_recording else "ready",
                            "device": (info["name"] if info else "unknown"),
                            "recording_chunks": len(self.recording_audio) if hasattr(self, 'recording_audio') else 0,
                            "total_frames": getattr(self, '_total_frames', 0)
                        }
                        response_data = json.dumps(payload).encode('utf-8')
                        try:
                            conn.setblocking(False)
                            conn.send(response_data)
                        except:
                            pass  # Don't block on send
                        
                    else:
                        if data:
                            logger.warning(f"Unknown command: {data}")
                        try:
                            conn.send(b"ERROR")
                        except:
                            pass
                    
                    try:
                        conn.close()
                    except:
                        pass
                    
                except BlockingIOError:
                    # No connection ready, continue
                    pass
                except Exception as e:
                    if "Resource temporarily unavailable" not in str(e):
                        logger.debug(f"Connection handling: {e}")
                
            except Exception as e:
                if "Resource temporarily unavailable" not in str(e):
                    logger.error(f"Error in command listener: {e}")
                await asyncio.sleep(0.01)
    
    @staticmethod
    def send_ipc_command(cmd: str, socket_path: str = "/tmp/hypr-voice.sock") -> Optional[str]:
        """Send a command to the Hypr-Voice IPC socket. Returns response (for STATUS) or None."""
        try:
            import socket as _socket
            s = _socket.socket(_socket.AF_UNIX, _socket.SOCK_STREAM)
            # Short timeout for fire-and-forget commands; longer for STATUS which returns JSON
            s.settimeout(1.0 if cmd == "STATUS" else 0.2)
            s.connect(socket_path)
            s.sendall(cmd.encode("utf-8"))
            resp = None
            if cmd == "STATUS":
                try:
                    resp = s.recv(4096).decode("utf-8", errors="ignore")
                except Exception:
                    resp = None
            s.close()
            return resp
        except Exception as e:
            logger.error(f"Failed to send IPC command '{cmd}': {e}")
            return None
    
    def copy_to_clipboard(self, text: str):
        """Copy text to clipboard using wl-copy"""
        try:
            subprocess.run(
                ["wl-copy"],
                input=text,
                text=True,
                check=True
            )
            logger.info("Text copied to clipboard")
            self.notify("Copied", text[:100] + "..." if len(text) > 100 else text, urgency="low")
        except Exception as e:
            logger.error(f"Failed to copy to clipboard: {e}")
    
    def paste_to_cursor(self, text: str):
        """Paste text at cursor position"""
        try:
            # First copy to clipboard
            subprocess.run(
                ["wl-copy"],
                input=text,
                text=True,
                check=True
            )
            
            # Then simulate Ctrl+V using ydotool
            subprocess.run(
                ["ydotool", "key", "ctrl+v"],
                check=True
            )
            logger.info("Text pasted at cursor")
            self.notify("Pasted", text[:50] + "..." if len(text) > 50 else text, urgency="low")
        except Exception as e:
            logger.error(f"Failed to paste at cursor: {e}")
    
    async def improve_text(self, text: str) -> str:
        """Improve text using context engine"""
        try:
            if await self._ensure_context_engine():
                improved = await self.context_engine.process_transcription(
                    text,
                    improve=True,
                    use_memory=True,
                    use_tools=True
                )
                return improved
            return text
        except Exception as e:
            logger.error(f"Failed to improve text: {e}")
            return text
    
    def edit_text(self, text: str):
        """Open text in editor for manual editing"""
        try:
            # Create temporary file
            import tempfile
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.txt',
                delete=False
            ) as f:
                f.write(text)
                temp_path = f.name
            
            # Open in preferred editor
            editor = os.getenv("EDITOR", "nano")
            subprocess.run([editor, temp_path], check=True)
            
            # Read edited text
            with open(temp_path, 'r') as f:
                edited_text = f.read()
            
            # Clean up
            os.unlink(temp_path)
            
            return edited_text
        except Exception as e:
            logger.error(f"Failed to edit text: {e}")
            return text
    
    def notify(
        self,
        title: str,
        body: str,
        actions: Optional[list] = None,
        urgency: str = "normal"
    ):
        """Send desktop notification using notify-send"""
        try:
            cmd = ["notify-send", "-u", urgency, title, body]
            
            if actions:
                for action in actions:
                    cmd.extend(["-A", action])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Handle action selection
            if result.returncode == 0 and result.stdout.strip().isdigit():
                action_idx = int(result.stdout.strip())
                if actions and 0 <= action_idx < len(actions):
                    return actions[action_idx]
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
        
        return None
    
    async def run_push_to_talk(self):
        """Run in push-to-talk mode"""
        logger.info("Push-to-talk mode - Hold SUPER+` to record")
        
        self.notify(
            "Hypr-Voice Ready",
            "Hold SUPER+` to record",
            urgency="low"
        )
        
        # Start background task to monitor active window
        asyncio.create_task(self.monitor_active_window())
        
        # Keep running and wait for commands via socket/pipe
        try:
            await self.listen_for_commands()
        except KeyboardInterrupt:
            logger.info("Shutting down...")


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hypr-Voice: Voice-driven input for Hyprland"
    )
    
    parser.add_argument(
        "-f", "--file",
        help="Audio file to transcribe"
    )
    
    parser.add_argument(
        "-c", "--config",
        help="Path to config directory (overrides default 'hypr-voice/config/')",
        type=str
    )
    
    parser.add_argument(
        "-p", "--push-to-talk",
        action="store_true",
        help="Run in push-to-talk mode"
    )
    
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List audio devices and exit"
    )
    
    # IPC client shortcuts (useful for Hyprland keybind press/release)
    parser.add_argument("--start", action="store_true", help="Send START to Hypr-Voice IPC")
    parser.add_argument("--stop", action="store_true", help="Send STOP to Hypr-Voice IPC")
    parser.add_argument("--force-stop", dest="force_stop", action="store_true", help="Send FORCE_STOP to Hypr-Voice IPC")
    parser.add_argument("--status", action="store_true", help="Query STATUS from Hypr-Voice IPC")
    
    parser.add_argument(
        "-d", "--input-device",
        help="Input device (index or substring of name). Overrides $HYPR_VOICE_INPUT_DEVICE"
    )
    
    parser.add_argument(
        "--no-improve",
        action="store_true",
        help="Skip LLM improvement"
    )
    
    parser.add_argument(
        "--test-recording",
        type=int,
        metavar="SECONDS",
        help="Test recording for N seconds and save to recordings/ folder"
    )
    
    args = parser.parse_args()
    
    # If invoked as an IPC client, send command and exit quickly
    if args.start or args.stop or args.status or args.force_stop:
        cmd = "START" if args.start else ("STOP" if args.stop else ("FORCE_STOP" if args.force_stop else "STATUS"))
        resp = HyprVoice.send_ipc_command(cmd)
        if resp:
            try:
                # Pretty print JSON if possible
                print(json.dumps(json.loads(resp), indent=2))
            except Exception:
                print(resp)
        return
    
    # Early exit: list devices
    if args.list_devices:
        HyprVoice.print_audio_devices()
        return
    
    # Initialize client
    config_dir = Path(args.config) if args.config else None
    client = HyprVoice(config_dir=config_dir)
    # CLI takes precedence over env
    client.input_device = args.input_device or os.getenv("HYPR_VOICE_INPUT_DEVICE")
    await client.initialize()
    
    # Run appropriate mode
    if args.file:
        # For file processing, just transcribe it directly
        await client.transcribe_audio_file(args.file)
    elif args.push_to_talk:
        await client.run_push_to_talk()
    else:
        # Default: push-to-talk mode
        await client.run_push_to_talk()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)