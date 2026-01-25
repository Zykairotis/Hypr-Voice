"""
Hybrid Whisper Server - wtype Integration
============================================

Simulates typing transcriptions on screen using wtype.

Two modes:
1. REALTIME: Streams audio via WebSocket, types new content every few seconds
2. API: Uploads file, waits for complete transcription, then types entire result
"""

import asyncio
import subprocess
import sys
import time
import threading
import os
import yaml
import pyaudio
from pathlib import Path

# Allow running as a script with PYTHONPATH configured
if __name__ == "__main__" and not __package__:
    project_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(project_root / "src"))
    __package__ = "hypr_voice.whisper.utils"

from ..core.hybrid_client import HybridWhisperClient
from ..paths import get_whisper_config_path

# ============================================================================
# AUDIO DEVICE UTILITIES
# ============================================================================

def load_audio_config():
    """Load audio configuration from audio-profile.yaml."""
    config_path = get_whisper_config_path("audio-profile.yaml")
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
            return config
    except Exception as e:
        print(f"⚠ Warning: Could not load audio config: {e}")
        return None

def find_device_by_name(device_name):
    """
    Find PyAudio device ID by matching device name.
    Returns device ID or None if not found.
    """
    if not device_name:
        return None
    
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                # Check if device name matches (case-insensitive partial match)
                if device_name.lower() in device_info['name'].lower():
                    return i
        return None
    finally:
        p.terminate()

def get_device_sample_rate(device_id):
    """Get the native sample rate for a device."""
    if device_id is None:
        return 16000  # Default for system default device
    
    p = pyaudio.PyAudio()
    try:
        device_info = p.get_device_info_by_index(device_id)
        return int(device_info['defaultSampleRate'])
    except Exception as e:
        print(f"⚠ Warning: Could not get sample rate for device {device_id}: {e}")
        return 16000
    finally:
        p.terminate()

def get_auto_device():
    """
    Automatically determine device from audio-profile.yaml.
    For monitor devices, uses PulseAudio environment variables instead of device ID.
    Returns tuple: (device_id, sample_rate, use_pulseaudio)
    """
    config = load_audio_config()
    
    if config and 'pulseaudio' in config:
        device_type = config['pulseaudio'].get('device_type', '')
        device_name = config['pulseaudio'].get('device_name')
        pulse_source = config['pulseaudio'].get('default_source')
        
        # Monitor devices (output captures) must use PulseAudio, not PyAudio device index
        if device_type == 'monitor' and pulse_source:
            print(f"✓ Detected monitor device: {device_name}")
            print(f"✓ Using PulseAudio source: {pulse_source}")
            
            # Set as system default source using pactl
            try:
                subprocess.run(
                    ["pactl", "set-default-source", pulse_source],
                    check=False,
                    capture_output=True
                )
            except Exception:
                pass  # Ignore pactl errors
            
            # Set PulseAudio environment variable
            os.environ['PULSE_SOURCE'] = pulse_source
            # Return None for device_id to use PulseAudio default
            return None, 48000, True  # Monitor devices typically use 48kHz
        
        # Regular input devices can use PyAudio device index
        if device_name:
            device_id = find_device_by_name(device_name)
            if device_id is not None:
                sample_rate = get_device_sample_rate(device_id)
                print(f"✓ Auto-detected device: {device_name} (ID: {device_id})")
                print(f"✓ Native sample rate: {sample_rate} Hz")
                return device_id, sample_rate, False
            else:
                print(f"⚠ Device '{device_name}' from config not found, using system default")
    
    return None, 16000, False  # Use system default with 16kHz

# ============================================================================
# WTYPE UTILITIES
# ============================================================================

def is_wayland():
    """Check if running on Wayland desktop."""
    return subprocess.run(
        ["echo", "$XDG_SESSION_TYPE"],
        capture_output=True,
        text=True
    ).stdout.strip() == "wayland" or "WAYLAND" in subprocess.run(
        ["env"],
        capture_output=True,
        text=True
    ).stdout

def check_wltype_installed():
    """Check if ydotool is installed."""
    try:
        result = subprocess.run(
            ["which", "ydotool"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return True
        print("✗ ydotool not found!")
        print("  Install with: sudo pacman -S ydotool (Arch)")
        print("  or build from source: https://github.com/ReimuNotMoe/ydotool")
        return False
    except Exception as e:
        print(f"✗ Error checking ydotool: {e}")
        return False

def type_text(text, typing_speed=0.01):
    """Type text using ydotool with configurable speed (use type_text_instant for fastest)."""
    for char in text:
        subprocess.run(["ydotool", "type", "-d", "1", "-H", "1", char], capture_output=True)
        time.sleep(typing_speed)

def type_text_instant(text):
    """Type text instantly using ydotool with 1ms delays (fastest possible)."""
    subprocess.run(["ydotool", "type", "-d", "1", "-H", "1", text], capture_output=True)

def type_text_words(text, words_per_second=5):
    """Type text word-by-word using ydotool - MUCH faster than character-by-character."""
    words = text.split()
    delay = 1.0 / words_per_second
    
    for i, word in enumerate(words):
        # Add space before word (except first word)
        if i > 0:
            subprocess.run(["ydotool", "type", "-d", "1", "-H", "1", " " + word], capture_output=True)
        else:
            subprocess.run(["ydotool", "type", "-d", "1", "-H", "1", word], capture_output=True)
        time.sleep(delay)

def type_text_gradually(text, chars_per_second=10):
    """Type text gradually, simulating natural typing."""
    typing_speed = 1.0 / chars_per_second
    type_text(text, typing_speed=typing_speed)

# ============================================================================
# MODE 1: REALTIME STREAMING WITH WLTYPE
# ============================================================================

class RealtimeTyper:
    """Stream audio and type incremental transcriptions."""
    
    def __init__(self, server_url="http://localhost:9099", device=None, typing_speed=0.02, sample_rate=16000, stability_checks=1, use_word_mode=True):
        self.client = HybridWhisperClient(server_url)
        self.device = device
        self.typing_speed = typing_speed
        self.sample_rate = sample_rate
        self.session_id = None
        self.monitoring = False
        self.use_word_mode = use_word_mode  # Type word-by-word instead of char-by-char
        # Optimized stability tracking
        self.stability_checks = stability_checks  # Reduced to 1 check (3 seconds)
        self.last_seen_text = ""
        self.stable_check_count = 0
        # NEVER RETYPE - track position of what we've typed
        self.typed_position = 0  # Character position of what we've already typed
        self.last_typed_full_text = ""  # Full text we last typed from
    
    async def start_streaming(self):
        """Start microphone streaming and type transcriptions."""
        print("\n" + "="*60)
        print("REALTIME TRANSCRIPTION WITH AUTO-TYPING")
        print("="*60)
        print("\n▶ Starting microphone stream...")
        print("  Click on a text field to start typing")
        print("  Press Ctrl+C to stop\n")
        
        # Create session (use None for auto-detection, not "auto")
        self.session_id = self.client.create_session(language=None)
        print(f"✓ Session created: {self.session_id}\n")
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self.monitor_and_type())
        
        try:
            # Start streaming with device's native sample rate
            await self.client.stream_microphone_ws(device=self.device, sample_rate=self.sample_rate)
        except KeyboardInterrupt:
            print("\n\n✓ Stopped")
        finally:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    async def monitor_and_type(self):
        """Monitor and type ONLY NEW content - NEVER retype."""
        try:
            check_interval = 1  # Check every second for faster response
            
            while True:
                await asyncio.sleep(check_interval)
                
                # Get current transcription
                result = self.client.get_session(self.session_id)
                if result:
                    current_text = result.get("text", "").strip()
                    
                    if not current_text:
                        continue
                    
                    # Check if text has changed
                    text_changed = current_text != self.last_seen_text
                    if text_changed:
                        # Reset stability counter when text changes
                        self.stable_check_count = 0
                        self.last_seen_text = current_text
                    else:
                        # Text is stable, increment counter
                        self.stable_check_count += 1
                    
                    # Only type when text has been stable
                    if self.stable_check_count >= self.stability_checks:
                        # CRITICAL: Find the common prefix between what we typed and current text
                        # This handles corrections without retyping
                        common_prefix_len = 0
                        if self.last_typed_full_text:
                            # Find how much of the beginning matches
                            for i in range(min(len(self.last_typed_full_text), len(current_text))):
                                if self.last_typed_full_text[i] == current_text[i]:
                                    common_prefix_len = i + 1
                                else:
                                    break
                            
                            # Never go backward - maintain forward progress
                            common_prefix_len = max(common_prefix_len, self.typed_position)
                        
                        # Only type content AFTER what we've already typed
                        if len(current_text) > common_prefix_len:
                            new_content = current_text[common_prefix_len:]
                            
                            if new_content.strip():  # Only type if there's actual content
                                # Add space if we're continuing from previous text
                                if common_prefix_len > 0 and not current_text[common_prefix_len-1].isspace():
                                    new_content = ' ' + new_content
                                
                                print(f"\n📝 Typing new content: {new_content[:50]}..." if len(new_content) > 50 else f"\n📝 Typing: {new_content}")
                                
                                # Type using fastest method
                                type_text_instant(new_content)
                                
                                # Update our position tracker
                                self.typed_position = len(current_text)
                                self.last_typed_full_text = current_text
        
        except asyncio.CancelledError:
            pass

# ============================================================================
# MODE 2: FILE UPLOAD WITH WLTYPE
# ============================================================================

class FileTyper:
    """Upload file, wait for transcription, then type result."""
    
    def __init__(self, server_url="http://localhost:9099", typing_speed=0.01):
        self.client = HybridWhisperClient(server_url)
        self.typing_speed = typing_speed
    
    def transcribe_and_type(self, filepath, language="en", timeout=300):
        """
        Upload file and type transcription result.
        
        Args:
            filepath: Path to audio/video file
            language: Language code (default: auto-detect)
            timeout: Maximum wait time in seconds
        """
        print("\n" + "="*60)
        print("FILE TRANSCRIPTION WITH AUTO-TYPING")
        print("="*60)
        
        print(f"\n▶ File: {filepath}")
        print("  Waiting for transcription...")
        
        # Create session
        session_id = self.client.create_session(language=language)
        print(f"✓ Session: {session_id}\n")
        
        # Upload file
        self.client.transcribe_file(filepath, session_id=session_id)
        print("✓ File uploaded\n")
        
        # Wait for transcription
        start_time = time.time()
        last_printed = ""
        
        print("⏳ Transcribing")
        print("-" * 60)
        
        while time.time() - start_time < timeout:
            result = self.client.get_session(session_id)
            
            if result:
                status = result.get("status")
                text = result.get("text", "")
                
                # Show updates
                if text != last_printed:
                    print(f"\r{text}", end="", flush=True)
                    last_printed = text
                
                # Check if done
                if status == "completed":
                    print("\n" + "-" * 60)
                    print("✓ Transcription complete\n")
                    
                    # Type the result
                    if text:
                        print(f"📝 Typing transcription ({len(text)} characters)...")
                        type_text_gradually(text, chars_per_second=10)
                        print("\n✓ Done typing")
                    else:
                        print("⚠ No transcription generated")
                    
                    return text
            
            time.sleep(1)
        
        print(f"\n✗ Timeout after {timeout} seconds")
        return None

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Hybrid Whisper with ydotool Auto-Typing"
    )
    
    parser.add_argument(
        "--server",
        default="http://localhost:9099",
        help="Server URL (default: http://localhost:9099)"
    )
    
    # Realtime mode
    realtime_group = parser.add_argument_group("Realtime Mode")
    realtime_group.add_argument(
        "--realtime",
        action="store_true",
        help="Stream microphone and auto-type transcriptions"
    )
    realtime_group.add_argument(
        "--device",
        type=int,
        help="Audio device ID (default: auto-detect from audio-profile.yaml)"
    )
    realtime_group.add_argument(
        "--use-microphone",
        action="store_true",
        help="Use system default microphone instead of config (for voice input)"
    )
    realtime_group.add_argument(
        "--typing-speed",
        type=float,
        default=0.02,
        help="Delay between characters (seconds, default: 0.02)"
    )
    realtime_group.add_argument(
        "--refresh-interval",
        type=int,
        default=3,
        help="Check for new text every N seconds (default: 3)"
    )
    realtime_group.add_argument(
        "--stability-checks",
        type=int,
        default=1,
        help="Number of consecutive stable checks before typing (default: 1, means 2s wait)"
    )
    realtime_group.add_argument(
        "--word-mode",
        action="store_true",
        default=True,
        help="Type word-by-word for faster typing (default: True)"
    )
    realtime_group.add_argument(
        "--char-mode",
        action="store_true",
        help="Type character-by-character (slower but more natural)"
    )
    
    # File mode
    file_group = parser.add_argument_group("File Mode")
    file_group.add_argument(
        "--file",
        help="Audio/video file to transcribe and auto-type"
    )
    file_group.add_argument(
        "--language",
        default="en",
        help="Language code (default: en)"
    )
    file_group.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Max wait time in seconds (default: 300)"
    )
    file_group.add_argument(
        "--type-speed",
        type=float,
        default=10,
        help="Characters per second for typing (default: 10)"
    )
    
    # Common
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List available audio devices"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if ydotool is installed"
    )
    
    args = parser.parse_args()
    
    # Check ydotool installation
    if args.check:
        if check_wltype_installed():
            print("✓ ydotool is installed")
        return
    
    # List devices
    if args.list_devices:
        print("\nAvailable audio devices:")
        from ..core.hybrid_client import list_audio_devices
        list_audio_devices()
        return
    
    # Realtime mode
    if args.realtime:
        if not check_wltype_installed():
            sys.exit(1)
        
        # Auto-detect device and sample rate from config if not specified
        device_to_use = args.device
        sample_rate_to_use = 16000  # Default
        using_pulseaudio = False
        
        # Override with microphone if requested
        if args.use_microphone:
            device_to_use = None  # Use system default microphone
            sample_rate_to_use = 16000  # Standard for voice
            print("✓ Using system default microphone")
            print("✓ Sample rate: 16000 Hz (standard for voice)")
        elif device_to_use is None:
            device_to_use, sample_rate_to_use, using_pulseaudio = get_auto_device()
        else:
            # If device specified manually, get its native sample rate
            sample_rate_to_use = get_device_sample_rate(device_to_use)
            print(f"✓ Using device: {device_to_use}")
            print(f"✓ Native sample rate: {sample_rate_to_use} Hz")
        
        print("\n⏰ Realtime Mode Configuration:")
        print(f"  Server: {args.server}")
        if using_pulseaudio:
            print(f"  Device: PulseAudio monitor (from audio-profile.yaml)")
            print(f"  Sample rate: {sample_rate_to_use} Hz")
        elif device_to_use is not None:
            print(f"  Device: {device_to_use} (from audio-profile.yaml)")
            print(f"  Sample rate: {sample_rate_to_use} Hz")
        else:
            print(f"  Device: system default")
            print(f"  Sample rate: {sample_rate_to_use} Hz")
        # Determine typing mode
        use_word_mode = not args.char_mode  # Default to word mode unless char mode specified
        if use_word_mode:
            print(f"  Typing mode: Word-by-word (8 words/sec)")
        else:
            print(f"  Typing mode: Character-by-character ({args.typing_speed}s/char)")
        print(f"  Check interval: 1s")
        if args.stability_checks == 0:
            print(f"  Typing: INSTANT (no wait)\n")
        else:
            print(f"  Stability wait: {args.stability_checks}s ({args.stability_checks} checks)\n")
        
        typer = RealtimeTyper(
            server_url=args.server,
            device=device_to_use,
            typing_speed=args.typing_speed,
            sample_rate=sample_rate_to_use,
            stability_checks=args.stability_checks,
            use_word_mode=not args.char_mode
        )
        
        asyncio.run(typer.start_streaming())
    
    # File mode
    elif args.file:
        if not check_wltype_installed():
            sys.exit(1)
        
        print("\n📁 File Mode Configuration:")
        print(f"  Server: {args.server}")
        print(f"  File: {args.file}")
        print(f"  Language: {args.language}")
        print(f"  Typing speed: {args.type_speed} chars/sec\n")
        
        typer = FileTyper(
            server_url=args.server,
            typing_speed=1.0 / args.type_speed
        )
        
        typer.transcribe_and_type(
            filepath=args.file,
            language=args.language,
            timeout=args.timeout
        )
    
    else:
        parser.print_help()
        print("\n" + "="*60)
        print("EXAMPLES")
        print("="*60)
        print("\n1. Realtime streaming with auto-typing:")
        print("   python wltype_integration.py --realtime --device 0")
        print("\n2. File transcription with auto-typing:")
        print("   python wltype_integration.py --file audio.mp3")
        print("\n3. Check if ydotool is installed:")
        print("   python wltype_integration.py --check")
        print("\n4. List audio devices:")
        print("   python wltype_integration.py --list-devices")

if __name__ == "__main__":
    main()
