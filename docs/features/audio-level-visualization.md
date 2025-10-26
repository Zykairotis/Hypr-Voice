# Audio Level Visualization Feature

## Overview
Real-time audio level visualization for Hypr-Voice provides instant visual feedback during voice recording, helping you confirm that your microphone is working properly and optimizing recording levels for better transcription accuracy.

## Features

### Visual Level Meter
- **Real-time display**: Shows current audio input strength as a visual bar
- **Peak tracking**: Marks the loudest point reached during recording
- **Automatic updates**: Refreshes every 5 audio chunks during recording
- **Clean shutdown**: Clears display when recording stops

### Display Format
```
🎤 Level: [█████████████████████████░░░░░░░░░░░░░│░░░] 45% (peak: 82%)
```
- **Filled bars (█)**: Current audio level
- **Empty bars (░)**: Unused range
- **Peak marker (│)**: Highest level reached
- **Percentage**: Current audio strength

## Configuration

### Environment Variables
```bash
SHOW_AUDIO_LEVELS=true    # Enable visualization (default)
SHOW_AUDIO_LEVELS=false   # Disable visualization
```

### Audio Device Configuration
The system supports automatic device fallback:
- **Primary device**: GA102 High Definition Audio Controller (NVIDIA HDMI)
- **Secondary device**: Parth's iPhone (Bluetooth fallback)
- Configuration location: `config/audio_config.yaml`

## Usage

### Start with Audio Levels (Default)
```bash
./scripts/run_hypr_voice.sh start
# Hold SUPER+` to record
# Audio level bar appears automatically
```

### Disable Audio Levels
```bash
export SHOW_AUDIO_LEVELS=false
./scripts/run_hypr_voice.sh start
```

### Test Audio Levels
```bash
# Quick test
./scripts/test_audio.sh

# Interactive test
./scripts/run_hypr_voice.sh foreground
# Hold SUPER+` and speak to see the level bar
```

## Technical Details

### Audio Level Calculation
- Uses **RMS (Root Mean Square)** of audio samples
- Scales levels for voice input (0-100%)
- Updates in real-time during recording
- Minimal performance overhead

### Implementation Details
- **Location**: `hypr_voice.py` lines 298-325
- **Method**: `_display_audio_level()`
- **Update frequency**: Every 5 audio chunks
- **Display type**: In-place terminal overwrite

## Recommended Recording Levels

### Optimal Range
- **30-70%**: Ideal for transcription accuracy
- **Aim for consistent levels** in this range during speech

### Level Indicators
- **0-30%**: Too low (may miss words)
- **30-70%**: Good (optimal transcription)
- **70-100%**: High (risk of clipping/distortion)

### Peak Levels
- Brief peaks to 80-100% are acceptable during emphasis
- Consistent levels above 80% may indicate gain issues

## Troubleshooting

### No Audio Bar Appears
```bash
# Check if enabled
echo $SHOW_AUDIO_LEVELS

# Enable if needed
export SHOW_AUDIO_LEVELS=true

# Restart service
./scripts/run_hypr_voice.sh restart
```

### Bar Shows 0% Constantly
1. **Check device selection**:
   ```bash
   grep "Using input device:" /tmp/hypr-voice-client.log
   ```

2. **Test microphone directly**:
   ```bash
   arecord -d 3 test.wav
   aplay test.wav
   ```

3. **Verify configuration**:
   ```bash
   cat config/audio_config.yaml | grep -A 3 "primary:"
   ```

### Device Not Found
```bash
# List available devices
python3 -c "import sounddevice as sd; print(sd.query_devices())"

# Update config with correct device name
nano config/audio_config.yaml
```

### Performance Issues
- Audio visualization has minimal overhead
- If experiencing lag, try disabling:
  ```bash
  export SHOW_AUDIO_LEVELS=false
  ```

## Testing

### Basic Functionality Test
1. Start Hypr-Voice: `./scripts/run_hypr_voice.sh start`
2. Hold `SUPER+`` to begin recording
3. Speak into microphone
4. Verify level bar responds to voice input
5. Release key and check transcription works

### Device Fallback Test
1. Disconnect primary audio device
2. Start recording
3. Verify system switches to secondary device
4. Check logs for device switching message

### Level Accuracy Test
1. Speak at different volumes
2. Observe level bar changes
3. Aim for 30-70% range during normal speech
4. Verify peak indicator captures loud moments

## Expected Log Output

When recording starts successfully:
```
2025-09-30 15:21:03 | INFO | Trying device: GA102 High Definition Audio Controller
2025-09-30 15:21:03 | INFO | ✅ High-quality input stream opened!
2025-09-30 15:21:03 | INFO |    Device: GA102 High Definition Audio Controller
2025-09-30 15:21:03 | INFO |    Quality: 48000 Hz, 1 channel(s), float32
```

## Benefits

1. **Instant Feedback**: Know immediately if your microphone is working
2. **Level Optimization**: Adjust speaking distance/volume for best results
3. **Troubleshooting**: Quickly identify audio issues
4. **Quality Assurance**: Ensure consistent recording levels
5. **User Confidence**: Visual confirmation improves user experience

## Compatibility

- Works with all configured audio devices
- Compatible with RAW_MODE and enhanced LLM mode
- Supports all terminal and application environments
- No additional dependencies required
