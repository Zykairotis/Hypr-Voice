# 🔧 Troubleshooting Documentation

Comprehensive guides for diagnosing and resolving common issues with Hypr-Voice.

## 🚨 Current Issues & Solutions

### 🔧 F9 Mode Issues
- **[F9 Analysis](F9_ANALYSIS.md)** - Technical analysis of F9 mode problems
- **[F9 Blocking Issues](F9_BLOCKING_ISSUE_REPORT.md)** - Known critical problems
- **[F9 Current Status](F9_CURRENT_STATUS.md)** - Current implementation status
- **[F9 Final Fix](F9_FINAL_FIX.md)** - Complete fix documentation

### 📋 Clipboard Issues
- **[Paste Issues](paste-issues.md)** - Universal clipboard troubleshooting

## 🎯 Quick Troubleshooting Guide

### 🎤 Audio Problems
```bash
# Test audio devices
./scripts/test_audio.sh

# Check audio configuration
./scripts/debug_setup.sh

# List audio devices
pactl list sinks
pactl list sources
```

### 🔗 Service Issues
```bash
# Check service status
./scripts/run_hypr_voice.sh status

# View service logs
./scripts/run_hypr_voice.sh logs

# Restart services
./scripts/run_hypr_voice.sh stop
./scripts/run_hypr_voice.sh start
```

### 📋 Clipboard Problems
```bash
# Test clipboard
echo "test" | wl-copy
wl-paste

# Test ydotool
ydotool type "test"

# Check Wayland clipboard
wayland-info | grep clipboard
```

## 🔧 Common Issues & Solutions

### 🎤 No Audio Input
**Symptoms**: No sound detected, audio levels stay at 0
**Solutions**:
1. Check microphone permissions: `pactl list sources`
2. Verify device selection in audio config
3. Test with different audio input devices
4. Check system audio settings

### ⚡ Mode Switching Not Working
**Symptoms**: F9/F10 keys don't switch modes
**Solutions**:
1. Verify Hyprland keybinds in `hyprland.conf`
2. Check if SUPER key is properly configured
3. Restart Hypr-Voice services
4. Test with different key combinations

### 📋 Paste Not Working
**Symptoms**: Transcribed text doesn't paste in applications
**Solutions**:
1. Try different paste methods (Ctrl+V, Ctrl+Shift+V)
2. Check application-specific settings
3. Verify clipboard daemon is running
4. Test with manual clipboard operations

### 🧠 Enhanced Mode Errors
**Symptoms**: F10 mode gives errors or crashes
**Solutions**:
1. Check LLM provider configuration
2. Verify network connectivity
3. Test with different providers
4. Fall back to Raw mode (F9)

## 🚨 Error Messages

### 🎤 Audio Errors
- **"No audio devices found"**: Check audio driver and device connections
- **"Permission denied"**: Add user to audio group: `sudo usermod -a -G audio $USER`
- **"Device busy"**: Close other audio applications

### 🔗 Service Errors
- **"Connection refused"**: Services not running, restart with start script
- **"Port already in use"**: Kill existing processes: `pkill hypr-voice`
- **"Configuration error"**: Check YAML syntax in config files

### 📋 Clipboard Errors
- **"Clipboard access denied"**: Check Wayland clipboard permissions
- **"Ydotool not found"**: Install ydotool package
- **"Paste failed"**: Try alternative paste methods

## 🔍 Diagnostic Commands

### 🎤 System Diagnostics
```bash
# Audio system info
pactl info
arecord -l
ls /dev/snd/

# Process information
ps aux | grep hypr
systemctl --user status hypr-voice

# Network connectivity
ping google.com
curl -I https://api.openai.com
```

### 📋 Clipboard Diagnostics
```bash
# Wayland clipboard info
wayland-info
wl-paste -t text -l

# Test ydotool
ydotool --help
ydotool type "test"

# Process clipboard
killall -9 wl-copy
killall -9 wl-paste
```

### 🧠 Enhanced Mode Diagnostics
```bash
# Test LLM providers
curl -H "Authorization: Bearer $API_KEY" https://api.openai.com/v1/models

# Check memory usage
free -h
ps aux --sort=-%mem | head

# Monitor system resources
htop
iotop
```

## 🔧 Configuration Fixes

### 🎤 Audio Configuration
```yaml
# config/audio_config.yaml
audio:
  device: "alsa_input.usb-USB_Microphone-00.analog-mono"
  sample_rate: 48000
  channels: 1
  buffer_size: 1024
```

### 🔗 Keybind Configuration
```ini
# ~/.config/hypr/hyprland.conf
bind = SUPER, Grave, exec, hypr-voice-toggle
bind = SUPER, F9, exec, hypr-voice-mode raw
bind = SUPER, F10, exec, hypr-voice-mode enhanced
```

### 📋 Application Profiles
```yaml
# config/app_profiles.yaml
applications:
  terminal:
    class: "kitty|alacritty|gnome-terminal"
    paste_method: "ctrl_shift_v"
  browser:
    class: "firefox|chromium|webkit2gtk"
    paste_method: "ctrl_v"
```

## 🔗 Getting Help

### 📋 Self-Service
1. **Check this documentation** - Most issues covered here
2. **Run diagnostics** - `./scripts/debug_setup.sh`
3. **Review logs** - `./scripts/run_hypr_voice.sh logs`
4. **Try fixes** - Follow step-by-step solutions

### 👥 Community Support
- **GitHub Issues**: Report bugs with detailed information
- **Discussions**: Ask questions and share solutions
- **Wiki**: Community-contributed tips and tricks

### 📧 Bug Reports
When reporting issues, include:
- System information (OS, Hyprland version)
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior
- Configuration files (sanitized)

## 🔗 Related Documentation

- **[User Guides](../user/)** - Feature configuration and usage
- **[Technical](../technical/)** - System architecture details
- **[Installation](../installation/)** - Setup and verification