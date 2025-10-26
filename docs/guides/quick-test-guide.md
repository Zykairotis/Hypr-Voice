# Quick Test Guide - Hypr-Voice Optimized

## ✅ Verify Installation

### 1. Check Service Status
```bash
./scripts/run_hypr_voice.sh status
```

**Expected output:**
```
Whisper Server: RUNNING
  PID: XXXXX
  Port: 9880
  
Hypr-Voice Client: RUNNING
  PID: XXXXX
  Socket: ACTIVE
```

### 2. Verify RAW_MODE Configuration
```bash
tail /tmp/hypr-voice-client.log | grep RAW_MODE
```

**Expected output:**
```
⚡ RAW_MODE enabled - skipping context engine (max speed)
```

### 3. Verify VAD Initialization
```bash
tail /tmp/hypr-voice-client.log | grep VAD
```

**Expected output:**
```
🎙️ VAD initialized for silence trimming
```

---

## 🎤 Test Voice Recording

### Test 1: Normal Speech
1. **Press and hold F9**
2. **Speak**: "This is a test of the voice recognition system"
3. **Release F9**

**Expected:**
- Text appears immediately in active application
- Notification: "✅ Pasted" with transcribed text
- **Time**: <2 seconds from release to paste

### Test 2: Silence Handling
1. **Press and hold F9**
2. **Wait 2 seconds (silence)**
3. **Release F9**

**Expected:**
- Notification: "No speech detected"
- No text pasted (VAD filtered silence)
- No "thank you" or other hallucinations

### Test 3: Speech with Pauses
1. **Press and hold F9**
2. **Speak**: "Hello world" [pause 1 second] "testing one two three"
3. **Release F9**

**Expected:**
- Clean transcription without filler words
- VAD trims silence at start/end
- Text: "Hello world testing one two three" or similar

---

## 📊 Performance Benchmarks

### Startup Performance
```bash
# Stop services
./scripts/run_hypr_voice.sh stop

# Time startup
time ./scripts/run_hypr_voice.sh start
```

**Expected:** <5 seconds total startup time

### Recording Performance
Monitor logs in real-time:
```bash
tail -f /tmp/hypr-voice-client.log
```

Look for timing indicators:
- `Recording duration: XXXms` - How long you held F9
- `VAD trimmed: X.XXs → X.XXs` - Silence removal
- `⚡ RAW MODE: Direct paste` - Fast path confirmed
- `✅ Pasted` - Success notification

---

## 🐛 Troubleshooting

### Issue: Slow transcription (>5 seconds)
**Check:**
```bash
grep "context engine\|Cognee\|MCP" /tmp/hypr-voice-client.log
```
**Expected:** Should see `⚡ RAW_MODE enabled - skipping context engine`

**Fix:** Ensure `.env` has `RAW_MODE=true`

### Issue: "thank you" hallucinations
**Check:**
```bash
grep "Filtered.*hallucination" /tmp/hypr-voice-client.log
```
**Expected:** Should see `⚠️ Filtered Whisper hallucination` messages

**Fix:** VAD may not be working. Check:
```bash
grep "VAD initialized" /tmp/hypr-voice-client.log
```

### Issue: No paste action
**Check Keybind:**
```bash
hyprctl binds | grep F9
```
**Expected:**
```
bind -> F9, exec, .../scripts/hypr-voice-control.sh start
bindr -> F9, exec, .../scripts/hypr-voice-control.sh stop
```

**Fix:** Ensure hyprland.conf has correct keybind configuration and run:
```bash
hyprctl reload
```

### Issue: Empty transcriptions
**Check Audio Device:**
```bash
grep "Found device" /tmp/hypr-voice-client.log
```
**Expected:** Should show "USB Audio" or your configured device

**Fix:** Update `audio_config.yaml` with correct device name

---

## 📈 Monitor Performance

### Real-time Monitoring
```bash
./scripts/run_hypr_voice.sh foreground
```
Press F9 and speak to see all processing steps in real-time.

### Log Analysis
```bash
# Last 100 lines of client activity
tail -100 /tmp/hypr-voice-client.log

# Filter for key events
grep -E "STARTING|STOPPING|VAD|Pasted|hallucination" /tmp/hypr-voice-client.log | tail -20

# Check timing information
grep "duration\|trimmed" /tmp/hypr-voice-client.log | tail -10
```

---

## 🎯 Success Criteria Checklist

- [ ] Service starts in <5 seconds
- [ ] RAW_MODE log shows "⚡ RAW_MODE enabled"
- [ ] VAD log shows "🎙️ VAD initialized"
- [ ] First recording: <5 seconds release-to-paste
- [ ] Subsequent recordings: <2 seconds release-to-paste
- [ ] Silence recordings: No "thank you" hallucinations
- [ ] Normal speech: Clean transcriptions
- [ ] Direct paste: No prompts or menus

---

## 🚀 Daily Usage

### Start Service (Once per boot)
```bash
cd ~/Zykairotis/Hypr-Voice-main/hypr-voice
./scripts/run_hypr_voice.sh start
```

### Using Voice Input
1. Focus any text input field
2. Press and hold **F9**
3. Speak your text
4. Release **F9**
5. Text appears automatically!

### Optional: Status Check
Press **Super+F9** to see status notification

### Optional: Force Stop Stuck Recording
Press **Super+Shift+F9** to emergency stop

---

## 🔄 Restart Service (After Config Changes)
```bash
./scripts/run_hypr_voice.sh restart
```

---

## 📝 Configuration Tips

### Adjust VAD Sensitivity
Edit `hypr_voice.py` line 100:
```python
self.vad = webrtcvad.Vad(2)  # 0-3, higher = more aggressive
```

- `0` - Quality (keep more audio)
- `1` - Low aggressive
- `2` - Balanced (default) ✅
- `3` - Aggressive (may cut soft speech)

### Add Custom Hallucination Filters
Edit `hypr_voice.py` line 407-425 to add more filtered phrases.

### Switch to Enhanced Mode
Edit `.env`:
```bash
RAW_MODE=false
```
Restart service to enable context engine, MCP tools, and AI improvements.

---

## 📞 Support

Check logs for errors:
- Client: `/tmp/hypr-voice-client.log`
- Server: `/tmp/hypr-voice-server.log`

Detailed documentation: `OPTIMIZATION_SUMMARY.md`
