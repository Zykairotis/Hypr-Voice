# Hypr-Voice Configuration Guide

## Configuration Files

### 1. Notifications (`config/notifications.yaml`)

Control all desktop notifications during voice typing operations.

**Location:** `/home/mewtwo/Zykairotis/Hypr-Voice/src/whisper/config/notifications.yaml`

```yaml
notifications:
  enabled: false  # Master toggle - set to true to enable all notifications
  
  # Individual toggles (when enabled: true)
  recording_started: false      # "🔴 Recording..." 
  recording_stopped: false      # "⏹️ Processing..."
  transcription_success: false  # "✅ Typed [text preview]"
  transcription_empty: false    # "🔇 No Speech"
  transcription_error: false    # "❌ Error"
  
  duration_ms: 3000  # How long notifications stay visible
```

**Current Status:** ✅ **All notifications DISABLED**

---

### 2. Recording Storage (`config/audio-profile.yaml`)

Control whether recordings are saved to disk or deleted after transcription.

**Location:** `/home/mewtwo/Zykairotis/Hypr-Voice/src/whisper/config/audio-profile.yaml`

```yaml
recording:
  save_recordings: false  # true = save to recordings/, false = delete after use
  format: "wav"
  sample_rate: 16000
  channels: 1
  
  auto_cleanup:
    enabled: false
    days_to_keep: 7  # Auto-delete recordings older than this
```

**Current Status:** ✅ **Recording saves DISABLED** (uses temp files, auto-deleted)

**When enabled:**
- Recordings saved to: `src/whisper/recordings/`
- Filenames: `recording_YYYYMMDD_HHMMSS.wav` (F9 PTT) or `quick_YYYYMMDD_HHMMSS.wav` (quick mode)

---

## Quick Configuration Changes

### Enable Notifications

```bash
# Edit the config
nano config/notifications.yaml

# Change this line:
enabled: true  # Changed from false
```

### Enable Recording Saves

```bash
# Edit the config
nano config/audio-profile.yaml

# Change this line:
save_recordings: true  # Changed from false
```

**No restart needed!** Changes take effect immediately on next F9 press.

---

## Performance Impact

### Current Settings (Optimized for Speed)

✅ **Notifications:** Disabled  
✅ **Recording saves:** Disabled  
✅ **Polling interval:** 0.2 seconds  
✅ **Typing speed:** 1ms delay (instant)

**Result:** ~1-3 second total latency from F9 release to text appearing

### If You Enable Features

| Feature | Impact | When to Enable |
|---------|--------|---------------|
| **Notifications** | +0ms (parallel) | Visual feedback desired |
| **Recording saves** | +10-50ms (I/O) | Need audio archive/review |

---

## Audio Device Configuration

**Also in:** `config/audio-profile.yaml`

```yaml
pulseaudio:
  default_source: "alsa_output.pci-0000_2d_00.1.hdmi-stereo.monitor"
  device_name: "GA102 High Definition Audio Controller"
  device_type: "monitor"  # monitor = capture output, source = microphone
```

**Change device:**
```bash
# List available sources
pactl list sources short

# Update config with your source name
nano config/audio-profile.yaml
```

---

## Files That Read These Configs

- `scripts/hypr-voice-record.sh` - F9 push-to-talk (reads both configs)
- `scripts/hypr-voice-quick.sh` - Quick recording (reads both configs)
- `hypr-voice-type.py` - PTT daemon (would need update to read configs)

---

## Troubleshooting

### Notifications not showing even when enabled?

Check if `notify-send` is installed:
```bash
which notify-send
# If not found:
sudo apt install libnotify-bin
```

### Recordings not saving even when enabled?

Check directory permissions:
```bash
ls -ld src/whisper/recordings/
# Should show: drwxr-xr-x

# If missing:
mkdir -p src/whisper/recordings/
chmod 755 src/whisper/recordings/
```

### Config changes not working?

Configs are read on **every** F9 press, so changes are immediate. If not working:
```bash
# Check config syntax
cat config/notifications.yaml | grep "enabled:"
cat config/audio-profile.yaml | grep "save_recordings:"

# Verify correct boolean format (lowercase, no quotes)
# ✅ Correct: enabled: false
# ❌ Wrong:   enabled: "false"
# ❌ Wrong:   enabled: False
```

---

## Default Locations

| File | Purpose | Current State |
|------|---------|---------------|
| `config/notifications.yaml` | Desktop notifications | All disabled |
| `config/audio-profile.yaml` | Audio device + recording saves | Saves disabled |
| `recordings/` | Saved audio files | Empty (saves disabled) |
| `/tmp/` | Temp recordings | Auto-deleted after use |

---

## Recommended Settings

### For Development/Testing
```yaml
# notifications.yaml
enabled: true  # See what's happening

# audio-profile.yaml  
save_recordings: true  # Review recordings for issues
```

### For Production Use (Current)
```yaml
# notifications.yaml
enabled: false  # Maximum speed, no distractions

# audio-profile.yaml
save_recordings: false  # Privacy, no disk usage
```

### For Privacy-Critical Use
```yaml
# notifications.yaml
enabled: false  # No notification history

# audio-profile.yaml
save_recordings: false  # No audio saved anywhere
```
