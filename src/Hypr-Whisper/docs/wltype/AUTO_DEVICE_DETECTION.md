# wtype Integration - Automatic Audio Device Detection

The wtype integration now automatically detects and uses the audio device configured in `audio-profile.yaml`, matching the behavior of the other Hypr-Voice scripts.

---

## How It Works

### 1. Configuration File
The device is defined in `/src/Hypr-Whisper/config/audio-profile.yaml`:

```yaml
pulseaudio:
  default_source: "alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor"
  device_name: "GA102 High Definition Audio Controller Digital Stereo (HDMI)"
  device_type: "monitor"
```

### 2. Device Selection Process

When you run `wltype_integration.py --realtime` **without** specifying `--device`:

1. **Load Config**: Reads `audio-profile.yaml`
2. **Extract Name**: Gets `device_name` from config
3. **Find Device**: Searches PyAudio devices for name match (case-insensitive)
4. **Use Device**: Automatically selects the matching device ID
5. **Fallback**: Uses system default if not found

### 3. Name-Based Matching

The script searches for devices whose name **contains** the configured device name:

```python
# From config: "GA102 High Definition Audio Controller Digital Stereo (HDMI)"
# Will match PyAudio device: "GA102 High Definition Audio Controller..."
```

This partial matching makes it robust against slight name variations.

---

## Usage

### Auto-Detection (Recommended)

```bash
# Uses device from audio-profile.yaml automatically
python wltype_integration.py --realtime
```

**Output:**
```
✓ Auto-detected device: GA102 High Definition Audio Controller... (ID: 2)

⏰ Realtime Mode Configuration:
  Server: http://localhost:9099
  Device: 2 (from audio-profile.yaml)
  Typing speed: 0.05s per char
  Refresh interval: 3s
```

### Manual Override

```bash
# Explicitly specify device ID (overrides config)
python wltype_integration.py --realtime --device 0
```

### Quick Start Script

```bash
# Easiest way - handles everything automatically
./scripts/start_wtype_realtime.sh
```

---

## Device Configuration

### View Current Config

```bash
cat config/audio-profile.yaml
```

### Update Device

Edit `config/audio-profile.yaml`:

```yaml
pulseaudio:
  device_name: "YOUR_DEVICE_NAME_HERE"
```

### Find Available Devices

```bash
# List all audio devices
python wltype_integration.py --list-devices

# Or use hybrid_client
python hybrid_client.py --list-devices
```

**Example output:**
```
Available audio input devices:
ID | Name | Channels | Sample Rate
────────────────────────────────────────────
0  | Default Input                            | 2 | 48000 Hz
1  | Built-in Microphone                      | 2 | 48000 Hz
2  | GA102 HDMI Digital Stereo (HDMI)        | 2 | 48000 Hz ✓
```

---

## Benefits

### ✅ **Consistency**
- Same device selection across all Hypr-Voice tools
- Single configuration file (`audio-profile.yaml`)
- No need to remember device IDs

### ✅ **Portability**
- Works across different systems
- Name-based matching handles device ID changes
- Automatic fallback to system default

### ✅ **Convenience**
- No `--device` flag needed
- Works out of the box
- Matches `start_client_mic.sh` behavior

---

## Comparison with Other Scripts

### start_client_mic.sh (Bash)
```bash
# Extracts device name from YAML
DEVICE_NAME=$(python -c "
import yaml
with open('config/audio-profile.yaml', 'r') as f:
    config = yaml.safe_load(f)
    print(config['pulseaudio']['device_name'])
")

# Sets PulseAudio default
pactl set-default-source "$PULSE_DEVICE"
```

### wltype_integration.py (Python)
```python
# Same approach in Python
config = load_audio_config()
device_name = config['pulseaudio']['device_name']
device_id = find_device_by_name(device_name)
```

Both use the same config file and device matching logic!

---

## Troubleshooting

### Device Not Found

**Issue:** `⚠ Device 'XXX' from config not found, using system default`

**Solution:**
1. List available devices:
   ```bash
   python wltype_integration.py --list-devices
   ```

2. Update `audio-profile.yaml` with correct device name

3. Verify the name matches (partial match is OK):
   ```bash
   # Config has: "GA102 High Definition"
   # Device shows: "GA102 High Definition Audio Controller"
   # ✓ This will match!
   ```

### Wrong Device Selected

**Solution:**
1. Check current config:
   ```bash
   cat config/audio-profile.yaml
   ```

2. Override manually:
   ```bash
   python wltype_integration.py --realtime --device 1
   ```

3. Update config for permanent change

---

## Technical Details

### Code Flow

```python
def get_auto_device():
    """Auto-detect device from audio-profile.yaml"""
    config = load_audio_config()
    
    if config and 'pulseaudio' in config:
        device_name = config['pulseaudio'].get('device_name')
        if device_name:
            device_id = find_device_by_name(device_name)
            if device_id is not None:
                print(f"✓ Auto-detected device: {device_name} (ID: {device_id})")
                return device_id
    
    return None  # Use system default
```

### Device Matching

```python
def find_device_by_name(device_name):
    """Find device ID by name matching"""
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_device_count()):
            device_info = p.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                # Case-insensitive partial match
                if device_name.lower() in device_info['name'].lower():
                    return i
        return None
    finally:
        p.terminate()
```

---

## Summary

**Before:**
```bash
# Had to manually specify device
python wltype_integration.py --realtime --device 2
```

**After:**
```bash
# Auto-detects from config
python wltype_integration.py --realtime

# Or even simpler
./scripts/start_wtype_realtime.sh
```

**Result:** 🎉 Seamless integration with existing Hypr-Voice configuration!
