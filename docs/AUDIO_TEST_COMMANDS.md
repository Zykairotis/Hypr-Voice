# Audio Testing Commands

## Step 1: Test Your Audio Device (harvard.wav)

**Run this first to confirm your NordBuds 2 are working:**

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice && .venv/bin/python3 test_audio_playback.py
```

✅ You should hear: *"The stale smell of old beer lingers..."* from harvard.wav

---

## Step 2: Test LLM Streaming with Audio

**Once you confirm audio works, run this:**

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice && .venv/bin/python3 src/hypr_voice/services/voice/test_tts.py
```

✅ You should hear: *"Hello! I am testing the real-time text-to-speech streaming system..."*

---

## Quick Copy-Paste Commands

**Test 1 - Audio Device (harvard.wav):**
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice && .venv/bin/python3 test_audio_playback.py
```

**Test 2 - LLM Streaming with Real TTS:**
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice && .venv/bin/python3 src/hypr_voice/services/voice/test_tts.py
```

> **Note:** Use `.venv/bin/python3` directly instead of `source .venv/bin/activate` to ensure the correct Python interpreter is used.

---

## What Was Fixed

1. ✅ Installed `sounddevice` and `soundfile` for audio playback
2. ✅ Fixed ElevenLabs WebSocket recv() conflict (receiver task management)
3. ✅ Fixed Deepgram connection race condition
4. ✅ Created audio device test with harvard.wav

---

## Troubleshooting

**If you don't hear audio:**

1. Check Bluetooth connection:
   ```bash
   bluetoothctl devices
   bluetoothctl info <device-mac>
   ```

2. Check default audio device:
   ```bash
   pactl list sinks short
   pactl info | grep "Default Sink"
   ```

3. Set NordBuds as default:
   ```bash
   pactl set-default-sink <sink-name>
   ```

4. Test with system player:
   ```bash
   aplay harvard.wav
   # or
   paplay harvard.wav
   ```

