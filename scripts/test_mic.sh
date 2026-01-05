#!/bin/bash
# Microphone Test Script for Hypr-Voice

echo "🎤 Microphone Test Script"
echo "=========================="
echo ""

# Check recording tools
if command -v ffmpeg &> /dev/null; then
    echo "✅ ffmpeg found"
else
    echo "❌ ffmpeg not found - install with: sudo pacman -S ffmpeg"
    exit 1
fi

# Get PulseAudio device info
echo ""
echo "📻 Audio Devices:"
pactl list sources short | grep -v ".monitor"

# Find USB microphone
USB_MIC=$(pactl list sources short | grep "USB" | grep -v "monitor" | awk '{print $1}')

if [ -z "$USB_MIC" ]; then
    echo ""
    echo "⚠️  No USB microphone found, using default"
    MIC_DEVICE="default"
else
    echo ""
    echo "✅ Found USB microphone: source $USB_MIC"
    MIC_DEVICE="$USB_MIC"
fi

echo ""
echo "🎙️  Recording 5 seconds of audio..."
echo "Speak now! (count to 5 or say 'test one two three')"
echo ""

# Record 5 seconds
OUTPUT="/tmp/mic_test_$(date +%s).wav"
ffmpeg -f pulse -i "$MIC_DEVICE" -t 5 -acodec pcm_s16le -ac 1 -ar 16000 "$OUTPUT" -y -loglevel quiet 2>&1

if [ -f "$OUTPUT" ]; then
    echo "✅ Recording saved: $OUTPUT"
    echo ""
    echo "📊 Audio Info:"
    ffprobe -hide_banner "$OUTPUT" 2>&1 | grep -E "(Duration|Stream|Audio)"
    echo ""
    
    # Check audio levels
    echo "📈 Checking audio levels..."
    python3 << PYTHON
import numpy as np
from scipy.io import wavfile

try:
    rate, data = wavfile.read("$OUTPUT")
    
    # Convert to float for analysis
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    
    # Calculate stats
    rms = np.sqrt(np.mean(data**2))
    peak = np.max(np.abs(data))
    
    # Convert to dB
    rms_db = 20 * np.log10(rms + 1e-10)
    peak_db = 20 * np.log10(peak + 1e-10)
    
    print(f"RMS Level: {rms_db:.1f} dB")
    print(f"Peak Level: {peak_db:.1f} dB")
    print(f"Dynamic Range: {peak_db - rms_db:.1f} dB")
    print("")
    
    # Assess quality
    if rms_db < -40:
        print("⚠️  AUDIO TOO QUIET - Move closer to mic or increase gain")
        print("   Your speech may not be detected properly")
    elif rms_db > -10:
        print("⚠️  AUDIO TOO LOUD - May cause distortion")
    elif -40 <= rms_db <= -10:
        print("✅ AUDIO LEVEL GOOD - Within acceptable range")
    
    if peak_db < -20:
        print("⚠️  LOW PEAK - Mic may be insensitive")
    elif peak_db > -3:
        print("⚠️  CLIPPING RISK - Audio may be distorted")
    
except Exception as e:
    print(f"Error analyzing audio: {e}")
PYTHON
    
    echo ""
    echo "🔊 Playing back your recording..."
    echo "   (Does it sound clear? Too quiet? Too loud?)"
    echo ""
    sleep 1
    
    # Play with multiple methods
    if command -v paplay &> /dev/null; then
        paplay "$OUTPUT"
    elif command -v aplay &> /dev/null; then
        aplay "$OUTPUT"
    elif command -v ffplay &> /dev/null; then
        ffplay -autoexit -nodisp "$OUTPUT" 2>&1
    else
        echo "❌ No audio player found"
        echo "   Play manually: ffplay $OUTPUT"
    fi
    
    echo ""
    echo "📁 Recording file: $OUTPUT"
    echo "   Keep this file to share if you want me to analyze it"
    echo ""
    echo "💡 To record again: ./scripts/test_mic.sh"
    
else
    echo "❌ Recording failed!"
    echo "   Check microphone permissions and connections"
fi
