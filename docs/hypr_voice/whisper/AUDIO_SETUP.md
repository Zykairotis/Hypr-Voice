# Audio Configuration Guide for Hypr-Voice WhisperLive

## Overview

This setup configures WhisperLive to capture audio from your **GA102 High Definition Audio Controller (HDMI)** using PulseAudio monitors.

## Files

### 1. `audio-profile.yaml`
Main audio configuration file. Specifies:
- PulseAudio source device
- Audio format settings
- Device description

**Current Configuration:**
```yaml
pulseaudio:
  default_source: "alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor"
  device_name: "GA102 High Definition Audio Controller Digital Stereo (HDMI)"
```

### 2. `.asoundrc`
ALSA configuration to suppress unnecessary warnings about unavailable audio devices.
- Redirects all audio through PulseAudio
- Disables probing of unavailable devices (modem, phoneline, etc.)

### 3. `audio-setup.sh`
Helper script for audio configuration and testing.

**Commands:**
```bash
# List all available audio devices
./audio-setup.sh list

# Show current audio configuration
./audio-setup.sh current

# Test recording (5 seconds)
./audio-setup.sh test

# Test recording from specific device (10 seconds)
./audio-setup.sh test alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor 10

# Apply audio-profile.yaml settings
./audio-setup.sh apply
```

## How It Works

### Audio Flow
```
System Audio Output 
    ↓
HDMI Audio Device (GA102)
    ↓
PulseAudio Monitor (captures output)
    ↓
WhisperLive Client
    ↓
WebSocket → WhisperLive Server
    ↓
Transcription
```

### Startup Process

When you run `./start_client_mic.sh`:

1. ✅ Activates Python virtual environment
2. ✅ Loads `.asoundrc` to suppress ALSA warnings
3. ✅ Reads `audio-profile.yaml`
4. ✅ Sets PulseAudio default source using `pactl`
5. ✅ Exports `PULSE_SOURCE` environment variable
6. ✅ Starts WhisperLive client with microphone input

## Common Tasks

### Change Audio Device

1. **Find your device:**
   ```bash
   pactl list sources short
   # or
   ./audio-setup.sh list
   ```

2. **Update `audio-profile.yaml`:**
   ```yaml
   pulseaudio:
     default_source: "your-device-name-here"
     device_name: "Your Device Description"
   ```

3. **Apply changes:**
   ```bash
   ./audio-setup.sh apply
   # or just restart the client
   ./start_client_mic.sh
   ```

### Test Audio Capture

```bash
# Test default device (5 seconds)
./audio-setup.sh test

# Test specific device (10 seconds)
./audio-setup.sh test alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor 10

# Play the recording
paplay /tmp/audio-test-*.wav
```

### Manual Configuration

```bash
# Set default source manually
pactl set-default-source alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor

# Check current default
pactl get-default-source

# List all sources with details
pactl list sources
```

## Understanding PulseAudio Monitors

**What is a monitor?**
- A "monitor" captures the OUTPUT of an audio device
- Perfect for recording "what's playing" (system audio, browser, etc.)
- Different from a microphone source (captures input)

**Common device types:**
- `*.monitor` = Output capture (what's playing)
- `alsa_input.*` = Microphone input
- `alsa_output.*` = Speaker/headphone output

**Your setup:**
- Device: `alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor`
- Type: HDMI output monitor
- Captures: All audio playing through HDMI

## Troubleshooting

### ALSA Warnings Persist

If you still see ALSA warnings:
1. Check `.asoundrc` exists in the whisper directory
2. Verify `ALSA_CONFIG_PATH` is set in the script
3. Try redirecting stderr: `./start_client_mic.sh 2>/dev/null`

### No Audio Captured

1. **Check device is available:**
   ```bash
   pactl list sources short | grep hdmi
   ```

2. **Test recording manually:**
   ```bash
   parecord --channels=1 --rate=16000 test.wav
   # Let it record, then Ctrl+C
   paplay test.wav
   ```

3. **Verify PulseAudio source is set:**
   ```bash
   pactl get-default-source
   ```

4. **Check server logs:**
   ```bash
   tail -f /tmp/whisper-live-hypr-voice.log
   ```

### Device Not Found

Your audio device may have a different name. To find it:

```bash
# List all sources
pactl list sources short

# Look for your HDMI device
pactl list sources | grep -A 10 "hdmi"

# Update audio-profile.yaml with correct name
```

## Quick Reference

| Task | Command |
|------|---------|
| Start client | `./start_client_mic.sh` |
| List devices | `./audio-setup.sh list` |
| Test audio | `./audio-setup.sh test` |
| Apply profile | `./audio-setup.sh apply` |
| Check current | `./audio-setup.sh current` |
| View logs | `tail -f /tmp/whisper-live-hypr-voice.log` |

## Configuration Summary

✅ **Audio Profile:** `audio-profile.yaml`  
✅ **ALSA Config:** `.asoundrc`  
✅ **Audio Helper:** `audio-setup.sh`  
✅ **Client Script:** `start_client_mic.sh` (updated to use audio profile)  
✅ **Device:** GA102 HDMI Monitor  
✅ **Format:** 16kHz, Mono, Int16  

---

**Ready to test?**
```bash
./start_client_mic.sh
```
