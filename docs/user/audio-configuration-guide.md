# Audio Configuration Guide for Hypr-Voice

## Overview
Hypr-Voice supports advanced audio configuration for high-quality recording with primary/secondary device selection, automatic fallback, and configurable audio processing.

## Configuration File
Audio settings are stored in `/home/mewtwo/Code/Hypr-V/hypr-voice/config/audio_config.yaml`

## Configuration Options

### Input Devices

```yaml
input:
  primary:
    name: "device_name"  # Primary audio input device
    index: null          # Optional: specific device index
  secondary:
    name: "backup_device"  # Fallback device if primary fails
    index: null
```

**Device Selection Logic:**
1. System attempts to use primary device first
2. If primary fails, automatically falls back to secondary
3. If both fail, uses system default

### Recording Quality

```yaml
recording:
  sample_rate: 48000      # Sample rate in Hz (48kHz for high quality)
  channels: 1             # 1 for mono, 2 for stereo
  dtype: "float32"        # Audio data type (float32 recommended)
  chunk_duration: 0.1     # Chunk size in seconds
  buffer_size: 2048       # Audio buffer size
```

**Recommended Settings:**
- **48kHz sample rate**: Professional audio quality
- **Mono (1 channel)**: Optimal for voice, reduces file size
- **float32**: Best dynamic range and precision
- **0.1s chunks**: Good balance of latency and stability

### Audio Processing

```yaml
processing:
  noise_reduction: true      # Enable noise reduction
  auto_gain_control: true    # Normalize volume levels
  echo_cancellation: false   # AEC (if supported)
  voice_activity_detection: true  # VAD for silence detection
```

## Finding Your Audio Devices

List available input devices:
```bash
python -c "import sounddevice as sd; print(sd.query_devices())"
```

Example output:
```
> 0 HDA Intel PCH: ALC892 Analog (hw:0,0), ALSA (2 in, 2 out)
  1 HDA Intel PCH: ALC892 Alt Analog (hw:0,2), ALSA (2 in, 0 out)
  2 pulse, ALSA (32 in, 32 out)
< 3 default, ALSA (32 in, 32 out)
```

Use the device name (e.g., "pulse" or "HDA Intel PCH: ALC892 Analog") in your config.

## Complete Example Configuration

```yaml
input:
  primary:
    name: "Blue Yeti Stereo Microphone"  # USB microphone
    index: null
  secondary:
    name: "pulse"  # PulseAudio fallback
    index: null

recording:
  sample_rate: 48000
  channels: 1
  dtype: "float32"
  chunk_duration: 0.1
  buffer_size: 2048

processing:
  noise_reduction: true
  auto_gain_control: true
  echo_cancellation: false
  voice_activity_detection: true

fallback:
  use_system_default: true  # Use system default if all else fails
  log_device_errors: true   # Log device selection issues
```

## Troubleshooting

### Common Issues

1. **"Device not found" error**
   - Check device name spelling exactly matches `sd.query_devices()` output
   - Ensure device is connected and recognized by system

2. **Poor audio quality**
   - Increase sample_rate to 48000
   - Ensure dtype is "float32"
   - Enable noise_reduction and auto_gain_control

3. **Recording latency**
   - Reduce chunk_duration (minimum 0.05)
   - Decrease buffer_size (minimum 512)

4. **No audio recorded**
   - Check if correct device is selected
   - Verify device permissions
   - Test with system default first

### Debug Commands

Check current audio setup:
```bash
./scripts/hypr-voice-control.sh status
```

Monitor daemon logs:
```bash
tail -f /tmp/hypr-voice-daemon.log
```

Test specific device:
```bash
python -c "import sounddevice as sd; sd.check_input_settings(device='your_device_name')"
```

## Performance Impact

High-quality audio settings (48kHz, float32) use more resources:
- **CPU**: ~2-5% during recording
- **Memory**: ~50MB for 1 minute of audio
- **Disk**: ~11MB per minute (before compression)

For lower-spec systems, consider:
- Reducing sample_rate to 16000
- Using dtype "int16"
- Disabling processing features

## Integration with Push-to-Talk

The audio configuration is automatically loaded when:
1. Hypr-Voice daemon starts
2. Push-to-talk recording begins (SUPER+` press)

No restart needed after config changes - new recordings will use updated settings.

## Advanced Features

### Per-Application Audio Profiles
Future enhancement to support different audio settings per application:
```yaml
profiles:
  meetings:
    sample_rate: 16000  # Lower for bandwidth
    echo_cancellation: true
  dictation:
    sample_rate: 48000  # Higher for accuracy
    noise_reduction: true
```

### Multi-Device Recording
Planned support for simultaneous multi-device recording:
```yaml
multi_device:
  enabled: false
  devices: ["device1", "device2"]
  mix_mode: "separate"  # or "combined"
```

## Related Documentation
- [Push-to-Talk Setup](./PUSH_TO_TALK.md)
- [Hyprland Integration](./HYPRLAND_INTEGRATION.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
