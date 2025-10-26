#!/usr/bin/env python3
"""
Audio Device Diagnostic Script for Hypr-Voice
Tests audio recording from different devices and provides recommendations
"""

import numpy as np
import sounddevice as sd
import soundfile as sf
import time
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_audio_devices():
    """List all available audio input devices with detailed information"""
    print("\n=== AUDIO INPUT DEVICES ===")
    print("ID | Name                                    | Channels | Sample Rate | Type")
    print("-" * 85)

    devices = sd.query_devices()
    default_input = sd.default.device[0]

    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            device_type = "UNKNOWN"
            device_name = device['name'].lower()

            # Classify device type
            if any(keyword in device_name for keyword in ['hdmi', 'displayport', 'monitor']):
                device_type = "OUTPUT_MONITOR (Not Recommended)"
            elif any(keyword in device_name for keyword in ['mic', 'microphone']):
                device_type = "MICROPHONE (Recommended)"
            elif any(keyword in device_name for keyword in ['usb audio']):
                device_type = "USB_AUDIO (Good)"
            elif any(keyword in device_name for keyword in ['pulse', 'pipewire']):
                device_type = "SYSTEM_AUDIO (Good)"
            elif any(keyword in device_name for keyword in ['bluetooth', 'buds']):
                device_type = "BLUETOOTH (Good)"
            elif any(keyword in device_name for keyword in ['line', 'aux']):
                device_type = "LINE_INPUT (OK)"

            # Mark default device
            marker = " [DEFAULT]" if i == default_input else ""

            print(f"{i:<3}| {device['name']:<40} | {device['max_input_channels']:8} | {device['default_samplerate']:.0f} Hz | {device_type}{marker}")

    print("\nRECOMMENDATIONS:")
    print("1. Avoid HDMI/display devices for microphone input")
    print("2. Prefer devices labeled 'MICROPHONE' or with 'mic' in the name")
    print("3. USB microphones usually provide the best quality")
    print("4. System audio (pulse/pipewire) can work but may pick up system sounds")

def test_audio_device(device_id, duration=3.0, output_dir="test_recordings"):
    """Test audio recording from a specific device"""
    print(f"\n=== TESTING DEVICE {device_id} ===")

    try:
        # Get device info
        device_info = sd.query_devices(device_id)
        device_name = device_info['name']
        sample_rate = int(device_info['default_samplerate'])
        channels = min(2, device_info['max_input_channels'])

        print(f"Device: {device_name}")
        print(f"Sample Rate: {sample_rate} Hz")
        print(f"Channels: {channels}")
        print(f"Duration: {duration} seconds")

        # Calculate frame count
        frames = int(duration * sample_rate)

        # Create output directory
        Path(output_dir).mkdir(exist_ok=True)

        # Record audio
        print("Recording... Speak clearly now!")
        recording = sd.rec(
            frames,
            samplerate=sample_rate,
            channels=channels,
            dtype='float32',
            device=device_id
        )

        # Show progress
        for i in range(int(duration * 10)):
            time.sleep(0.1)
            if i % 5 == 0:  # Update every 0.5 seconds
                print(f"Recording: {i/10:.1f}s / {duration}s")

        # Wait for recording to complete
        sd.wait()
        print("Recording complete!")

        # Calculate audio statistics
        if channels > 1:
            # Convert to mono for analysis
            recording_mono = np.mean(recording, axis=1)
        else:
            recording_mono = recording.flatten()

        rms = np.sqrt(np.mean(recording_mono ** 2))
        peak = np.max(np.abs(recording_mono))

        # Analyze audio content
        if rms < 0.001:
            audio_quality = "NO AUDIO DETECTED"
            recommendation = "Check microphone connection/mute"
        elif rms < 0.01:
            audio_quality = "VERY QUIET"
            recommendation = "Increase microphone gain or speak closer"
        elif rms < 0.1:
            audio_quality = "QUIET BUT USABLE"
            recommendation = "Good for quiet environments"
        elif rms < 0.3:
            audio_quality = "GOOD AUDIO LEVEL"
            recommendation = "Optimal recording level"
        else:
            audio_quality = "LOUD AUDIO"
            recommendation = "May be clipping, reduce gain"

        print(f"\nAudio Analysis:")
        print(f"  RMS Level: {rms:.5f}")
        print(f"  Peak Level: {peak:.5f}")
        print(f"  Quality: {audio_quality}")
        print(f"  Recommendation: {recommendation}")

        # Save test recording
        timestamp = int(time.time())
        filename = f"{output_dir}/test_device_{device_id}_{timestamp}.wav"
        sf.write(filename, recording, sample_rate)
        print(f"  Saved to: {filename}")

        # Test file integrity
        try:
            # Read back the file to verify
            test_read, sr = sf.read(filename)
            print(f"  File verification: SUCCESS ({len(test_read)} samples, {sr} Hz)")
            return True, rms, audio_quality
        except Exception as e:
            print(f"  File verification: FAILED - {e}")
            return False, rms, "FILE_ERROR"

    except Exception as e:
        print(f"Error testing device {device_id}: {e}")
        return False, 0, "ERROR"

def test_whisper_compatibility(device_id, duration=3.0):
    """Test if audio from device is compatible with Whisper (16kHz, mono)"""
    print(f"\n=== WHISPER COMPATIBILITY TEST FOR DEVICE {device_id} ===")

    try:
        # Get device info
        device_info = sd.query_devices(device_id)
        sample_rate = int(device_info['default_samplerate'])
        channels = min(2, device_info['max_input_channels'])

        # Record short sample
        frames = int(duration * sample_rate)
        recording = sd.rec(
            frames,
            samplerate=sample_rate,
            channels=channels,
            dtype='float32',
            device=device_id
        )
        sd.wait()

        # Convert to 16kHz mono (Whisper format)
        if channels > 1:
            recording = np.mean(recording, axis=1)

        if sample_rate != 16000:
            # Resample to 16kHz
            target_length = int(len(recording) * 16000 / sample_rate)
            indices = np.linspace(0, len(recording) - 1, target_length)
            recording_resampled = np.interp(indices, np.arange(len(recording)), recording)
        else:
            recording_resampled = recording

        # Check audio quality after resampling
        rms = np.sqrt(np.mean(recording_resampled ** 2))

        print(f"Original: {sample_rate} Hz, {channels} channels")
        print(f"Whisper format: 16000 Hz, 1 channel")
        print(f"Resampled audio RMS: {rms:.5f}")

        if rms > 0.001:
            print("✓ Audio quality sufficient for Whisper")
            return True
        else:
            print("✗ Audio too quiet for Whisper")
            return False

    except Exception as e:
        print(f"Error testing Whisper compatibility: {e}")
        return False

def recommend_best_device():
    """Test and recommend the best audio device"""
    print("\n=== FINDING BEST AUDIO DEVICE ===")

    devices = sd.query_devices()
    input_devices = []

    # Collect input devices with priority scores
    for i, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            device_name = device['name'].lower()
            score = 0

            # Scoring system
            if 'mic' in device_name or 'microphone' in device_name:
                score += 100
            elif 'usb audio' in device_name and ('mic' in device_name or 'input' in device_name):
                score += 80
            elif 'bluetooth' in device_name or 'buds' in device_name:
                score += 70
            elif 'pulse' in device_name or 'pipewire' in device_name:
                score += 60
            elif 'hdmi' in device_name or 'displayport' in device_name:
                score += 10  # Low priority for HDMI
            else:
                score += 50

            input_devices.append((i, device, score))

    # Sort by score (highest first)
    input_devices.sort(key=lambda x: x[2], reverse=True)

    print("Testing devices in priority order...")

    best_device = None
    best_rms = 0

    for device_id, device, score in input_devices[:5]:  # Test top 5
        print(f"\nTesting device {device_id}: {device['name']} (Score: {score})")
        success, rms, quality = test_audio_device(device_id, duration=2.0)

        if success and rms > best_rms:
            best_device = device_id
            best_rms = rms

        if rms > 0.01:  # Good enough audio found
            break

    if best_device is not None:
        print(f"\n=== RECOMMENDED DEVICE ===")
        best_info = sd.query_devices(best_device)
        print(f"Device ID: {best_device}")
        print(f"Name: {best_info['name']}")
        print(f"Audio Level: {best_rms:.5f}")
        print(f"\nTo use this device, run:")
        print(f"python3 hypr-voice/src/audio/whisper_client.py --stream --device {best_device}")
        return best_device
    else:
        print("\nNo suitable audio device found!")
        return None

def main():
    parser = argparse.ArgumentParser(description="Audio Device Diagnostic Tool")
    parser.add_argument("--list", action="store_true", help="List all audio devices")
    parser.add_argument("--test", type=int, metavar="DEVICE_ID", help="Test specific device")
    parser.add_argument("--recommend", action="store_true", help="Find and recommend best device")
    parser.add_argument("--whisper-test", type=int, metavar="DEVICE_ID", help="Test Whisper compatibility")
    parser.add_argument("--duration", type=float, default=3.0, help="Test duration in seconds")
    parser.add_argument("--output-dir", default="test_recordings", help="Output directory for test files")

    args = parser.parse_args()

    if args.list:
        list_audio_devices()
    elif args.test is not None:
        test_audio_device(args.test, args.duration, args.output_dir)
    elif args.whisper_test is not None:
        test_whisper_compatibility(args.whisper_test, args.duration)
    elif args.recommend:
        recommend_best_device()
    else:
        # Default: list devices and recommend
        list_audio_devices()
        recommend_best_device()

if __name__ == "__main__":
    main()