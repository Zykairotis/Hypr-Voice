#!/bin/bash
# Quick audio test script for Hypr-Voice

echo "Testing audio setup..."
echo ""

# Check if sounddevice is available
if ! python3 -c "import sounddevice" 2>/dev/null; then
    echo "Error: sounddevice not installed"
    echo "Install: pip install sounddevice"
    exit 1
fi

# List all available devices
echo "=== Available Audio Input Devices ==="
python3 << 'PYEOF'
import sounddevice as sd

devices = sd.query_devices()
print("\nAll devices:")
for i, dev in enumerate(devices):
    if dev['max_input_channels'] > 0:
        marker = " <-- DEFAULT" if i == sd.default.device[0] else ""
        print(f"  [{i}] {dev['name']}{marker}")
        print(f"      Max Channels: {dev['max_input_channels']}")
        print(f"      Default Sample Rate: {dev['default_samplerate']} Hz")
        print()
PYEOF

echo ""
echo "=== Testing Primary Device (USB Audio) ==="

# Test recording with primary device
python3 << 'PYEOF'
import sounddevice as sd
import numpy as np
import time

# Find USB Audio device
devices = sd.query_devices()
usb_device = None
for i, dev in enumerate(devices):
    if 'USB Audio' in dev['name'] and dev['max_input_channels'] > 0:
        usb_device = i
        print(f"Found USB Audio device: [{i}] {dev['name']}")
        break

if usb_device is None:
    print("USB Audio device not found!")
    print("Check if it's connected and recognized by the system")
    exit(1)

# Test recording
print("\nRecording 2 seconds of audio...")
try:
    duration = 2  # seconds
    fs = 48000  # sample rate
    
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, 
                       dtype='float32', device=usb_device)
    sd.wait()
    
    # Calculate RMS to check if audio was captured
    rms = np.sqrt(np.mean(recording**2))
    
    print(f"Recording complete!")
    print(f"RMS level: {rms:.6f}")
    
    if rms > 0.001:
        print("✓ Audio detected! Device is working.")
    else:
        print("⚠ Warning: Very low audio level. Check microphone or speak louder.")
        
except Exception as e:
    print(f"✗ Error recording: {e}")
    exit(1)

PYEOF

echo ""
echo "=== Configuration Check ==="
echo "Current config/audio_config.yaml:"
grep -A 3 "primary:" /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice/config/audio_config.yaml | head -4

echo ""
echo "Test complete!"
echo ""
echo "If audio was detected, you're ready to use Hypr-Voice."
echo "Start with: /home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice/scripts/run_hypr_voice.sh start"
