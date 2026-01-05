#!/usr/bin/env python3
"""
Audio Analysis Tool for Microphone Testing
Analyzes recorded audio to identify potential issues
"""

import sys
import numpy as np
from scipy.io import wavfile
from pathlib import Path

def analyze_audio(file_path):
    """Analyze audio file for quality issues."""
    
    if not Path(file_path).exists():
        print(f"❌ File not found: {file_path}")
        return
    
    print(f"🔍 Analyzing: {file_path}")
    print("=" * 60)
    
    try:
        # Load audio
        rate, data = wavfile.read(file_path)
        
        # Handle stereo
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        # Convert to float
        if data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        
        duration = len(data) / rate
        
        print(f"📊 Basic Info:")
        print(f"   Sample Rate: {rate} Hz")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Samples: {len(data):,}")
        print("")
        
        # Calculate levels
        rms = np.sqrt(np.mean(data**2))
        peak = np.max(np.abs(data))
        
        # Convert to dB
        rms_db = 20 * np.log10(rms + 1e-10)
        peak_db = 20 * np.log10(peak + 1e-10)
        
        print(f"📈 Audio Levels:")
        print(f"   RMS (average): {rms_db:.1f} dB")
        print(f"   Peak (max): {peak_db:.1f} dB")
        print(f"   Dynamic Range: {peak_db - rms_db:.1f} dB")
        print("")
        
        # Detect silence
        silence_threshold = 0.01  # -40dB
        silent_samples = np.sum(np.abs(data) < silence_threshold)
        silence_percent = (silent_samples / len(data)) * 100
        
        print(f"🔇 Silence Detection:")
        if silence_percent > 80:
            print(f"   ⚠️  {silence_percent:.1f}% silence - Mic may be too quiet!")
        elif silence_percent > 50:
            print(f"   ⚠️  {silence_percent:.1f}% silence - Low audio level")
        else:
            print(f"   ✅ {silence_percent:.1f}% silence - Good")
        print("")
        
        # Detect clipping
        clipped = np.sum(np.abs(data) > 0.99)
        clipped_percent = (clipped / len(data)) * 100
        
        print(f"📢 Clipping Detection:")
        if clipped_percent > 0.1:
            print(f"   ⚠️  {clipped_percent:.2f}% clipped - Audio may be distorted!")
        elif clipped_percent > 0:
            print(f"   ⚠️  {clipped_percent:.3f}% clipped - Minor clipping")
        else:
            print(f"   ✅ No clipping detected")
        print("")
        
        # Noise floor (quietest part)
        window_size = int(rate * 0.1)  # 100ms windows
        num_windows = len(data) // window_size
        noise_levels = []
        
        for i in range(num_windows):
            window = data[i*window_size:(i+1)*window_size]
            noise_levels.append(np.sqrt(np.mean(window**2)))
        
        noise_floor = 20 * np.log10(min(noise_levels) + 1e-10)
        
        print(f"🔊 Noise Floor:")
        if noise_floor > -50:
            print(f"   ⚠️  {noise_floor:.1f} dB - High background noise!")
        elif noise_floor > -60:
            print(f"   ⚠️  {noise_floor:.1f} dB - Moderate noise")
        else:
            print(f"   ✅ {noise_floor:.1f} dB - Low noise")
        print("")
        
        # Overall assessment
        print(f"📋 Overall Assessment:")
        issues = []
        
        if rms_db < -40:
            issues.append("Audio too quiet (move closer or increase gain)")
        if rms_db > -10:
            issues.append("Audio too loud (may cause distortion)")
        if clipped_percent > 0.1:
            issues.append("Significant clipping (reduce gain)")
        if silence_percent > 80:
            issues.append("Too much silence (check mic connection)")
        if noise_floor > -50:
            issues.append("High background noise (quiet environment needed)")
        
        if issues:
            print("   ⚠️  ISSUES FOUND:")
            for i, issue in enumerate(issues, 1):
                print(f"      {i}. {issue}")
        else:
            print("   ✅ Audio quality looks good!")
        
        print("")
        print(f"💡 Recommendations:")
        
        if rms_db < -40:
            print("   - Move closer to microphone")
            print("   - Increase microphone gain in PulseAudio")
            print("   - Use 'pavucontrol' to adjust levels")
        elif rms_db > -10:
            print("   - Move further from microphone")
            print("   - Decrease microphone gain")
        
        if clipped_percent > 0.1:
            print("   - Reduce microphone gain")
            print("   - Don't speak too loudly")
        
        if noise_floor > -50:
            print("   - Move to quieter environment")
            print("   - Use noise gate or filter")
            print("   - Get a better microphone")
        
        print("")
        print(f"🎤 For Whisper transcription:")
        
        # Whisper-specific recommendations
        if -30 <= rms_db <= -15 and clipped_percent < 0.1:
            print(f"   ✅ Optimal range for accurate transcription")
        elif rms_db < -40:
            print(f"   ⚠️  May fail to detect speech")
            print(f"   → Increase volume or get closer to mic")
        elif clipped_percent > 0.1:
            print(f"   ⚠️  May transcribe incorrectly due to distortion")
            print(f"   → Reduce gain to avoid clipping")
        
        print("")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    if len(sys.argv) < 2:
        print("Usage: analyze_audio.py <audio_file.wav>")
        print("")
        print("Example:")
        print("  ./analyze_audio.py /tmp/mic_test_123456.wav")
        sys.exit(1)
    
    analyze_audio(sys.argv[1])

if __name__ == "__main__":
    main()
