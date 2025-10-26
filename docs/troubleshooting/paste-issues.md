# Paste Troubleshooting Guide

## Issue
Text is transcribed successfully but doesn't paste into the active application.

## Recent Changes
Updated `wtype` command to use explicit key press/release:
- **Old**: `-k v` (simple key press)
- **New**: `-P v -p v` (explicit press and release)

This provides better reliability across different applications.

## Testing Steps

### 1. Verify Clipboard Content
After recording, check what's in the clipboard:
```bash
wl-paste
```
You should see your transcribed text.

### 2. Manual Paste Test
Try pasting manually:
```bash
# For regular apps
wtype -M ctrl -P v -p v -m ctrl

# For terminals
wtype -M ctrl -M shift -P v -p v -m shift -m ctrl
```

### 3. Check Application Detection
Look at the logs for:
```
INFO | Regular app: windsurf, using Ctrl+V
# or
INFO | Detected terminal app: kitty, using Ctrl+Shift+V
```

## Common Issues & Solutions

### Issue 1: wtype Too Fast
**Symptom**: Keypresses not registered
**Solution**: Already implemented - added 50ms delay after clipboard copy

### Issue 2: Application Not Focused
**Symptom**: Paste goes to wrong window or nowhere
**Solution**: Ensure the target app has focus when you release the key

### Issue 3: Clipboard Overwritten
**Symptom**: Wrong content pasted (like log text)
**Solution**: Check if other processes are writing to clipboard

### Issue 4: Terminal App Detection Wrong
**Symptom**: Regular app treated as terminal (or vice versa)
**Solution**: Check `self.current_app` value in logs

## Alternative Paste Methods

### Method 1: Direct Text Input (ydotool)
Install ydotool as an alternative:
```bash
yay -S ydotool
sudo systemctl enable --now ydotool
```

### Method 2: wl-clip-persist
Keep clipboard content persistent:
```bash
yay -S wl-clip-persist
wl-clip-persist --clipboard both
```

### Method 3: Manual Paste Mode
Set environment variable to only copy (no auto-paste):
```bash
export AUTO_PASTE=false
```
Then manually paste with Ctrl+V

## Debug Mode

Enable detailed paste logging:
```bash
# In the logs, look for:
2025-09-30 15:30:20.622 | INFO | 📋 Pasting text: 'Your transcribed text here'
2025-09-30 15:30:20.645 | INFO | Regular app: windsurf, using Ctrl+V
2025-09-30 15:30:20.656 | INFO | Text pasted at cursor
```

## wtype Command Breakdown

### For Regular Apps (Ctrl+V):
```
wtype -M ctrl     # Hold Ctrl modifier
      -P v        # Press 'v' key down
      -p v        # Release 'v' key up
      -m ctrl     # Release Ctrl modifier
```

### For Terminals (Ctrl+Shift+V):
```
wtype -M ctrl     # Hold Ctrl modifier
      -M shift    # Hold Shift modifier
      -P v        # Press 'v' key down
      -p v        # Release 'v' key up
      -m shift    # Release Shift modifier
      -m ctrl     # Release Ctrl modifier
```

## Hyprland-Specific Issues

### Check Input Handling
Some Hyprland animations or transitions might interfere:
```bash
# In hyprland.conf
animations {
    enabled = yes
    bezier = myBezier, 0.05, 0.9, 0.1, 1.05
    animation = windows, 1, 7, myBezier
    animation = fade, 1, 7, default
}
```

### Check Window Rules
Make sure no window rules prevent input:
```bash
hyprctl clients  # Check active windows
hyprctl keyword bind  # Check keybindings
```

## Fallback: Use Notification Actions

If auto-paste doesn't work, use the notification:
1. After transcription, notification appears
2. Click "PASTE" action in notification
3. This might have better focus handling

## Environment Variables

Relevant env vars for debugging:
```bash
export WAYLAND_DEBUG=1        # Show Wayland protocol messages
export HYPRLAND_LOG=/tmp/hypr.log  # Log Hyprland events
export SHOW_AUDIO_LEVELS=true # Keep audio visualization
```

## Test Command Sequence

Full test sequence:
```bash
# 1. Start Hypr-Voice
./scripts/run_hypr_voice.sh foreground

# 2. Focus target application (e.g., text editor)

# 3. Hold SUPER+` and speak
# Audio level bar should show activity

# 4. Release key
# Should see in logs:
#   - "📋 Pasting text: '...'"
#   - "Regular app: appname, using Ctrl+V"
#   - "Text pasted at cursor"

# 5. Check clipboard
wl-paste

# 6. Manual paste if needed
# In app: Ctrl+V (or Ctrl+Shift+V for terminals)
```

## Report Issues

If pasting still doesn't work, provide:
1. Log output showing the paste attempt
2. Output of `wl-paste` after transcription
3. Target application name
4. Manual paste test result
5. Hyprland version: `hyprctl version`
