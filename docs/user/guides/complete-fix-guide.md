# Complete Fix Guide: Windsurf Paste Issue

## Current Situation

✅ **Working**: Kitty terminal (uses Ctrl+Shift+V)  
❌ **Not Working**: Windsurf, VSCode, other Electron apps

## Root Cause Analysis

You have **TWO ydotoold daemons** running:
```bash
$ ps aux | grep ydotoold
root         900  ...  /usr/bin/ydotoold    # ← Problem: owned by root
mewtwo      1259  ...  /usr/bin/ydotoold    # ← Your user's daemon
```

The **root-owned daemon** created the socket with restricted permissions:
```bash
$ ls -la /tmp/.ydotool_socket
srw------- 1 root input ...  # ← Only root can access
```

This causes the "Permission denied" error when Hypr-Voice tries to use ydotool.

## Step-by-Step Fix

### Step 1: Run the Fix Script

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main
./fix_ydotool.sh
```

This will:
1. Kill all ydotoold processes (including the root one)
2. Remove the root-owned socket
3. Start ydotoold as your user
4. Test that ydotool works

### Step 2: Find What's Auto-Starting ydotool as Root

Check for system-level startup scripts:

```bash
# Check systemd
sudo systemctl list-units | grep ydotool

# If found, disable it:
sudo systemctl disable ydotool
sudo systemctl stop ydotool

# Also check user systemd
systemctl --user list-units | grep ydotool
```

Check your shell startup files:
```bash
grep -r "ydotool" ~/.bashrc ~/.zshrc ~/.profile 2>/dev/null
```

### Step 3: Add ydotoold to YOUR Hyprland Config (Recommended)

Edit `~/.config/hypr/hyprland.conf` and add:

```conf
# Start ydotoold as current user for Electron app paste support
exec-once = ydotoold
```

**Why this is best:**
- Starts with Hyprland (graphical session)
- Runs as your user (correct permissions)
- Only starts once per session
- No need to modify shell configs

### Step 4: Restart Hyprland

```bash
# Log out and back in, OR
hyprctl reload

# OR restart Hyprland entirely:
# killall Hyprland (then log back in)
```

### Step 5: Verify the Fix

```bash
# 1. Check only ONE ydotoold is running (as YOUR user)
ps aux | grep ydotoold | grep -v grep
# Should show: mewtwo ... /usr/bin/ydotoold (NOT root)

# 2. Check socket permissions
ls -la /tmp/.ydotool_socket
# Should show: srw------- 1 mewtwo input ...

# 3. Test ydotool
ydotool key 1:0
# Should return without errors

# 4. Test paste in Windsurf
cd /home/mewtwo/Zykairotis/Hypr-Voice-main
./test_paste.py 6
# Switch to Windsurf within 5 seconds - should paste successfully
```

### Step 6: Test Hypr-Voice

```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice-main
./scripts/run_hypr_voice.sh foreground

# Hold SUPER+` and speak in Windsurf
# Text should paste automatically when you release
```

## Expected Results

### Success Logs (Windsurf)
```
2025-09-30 15:44:53.624 | DEBUG | Detected Electron app: windsurf, using extended delay
2025-09-30 15:44:53.934 | INFO  | Electron app detected: windsurf, trying ydotool
2025-09-30 15:44:53.947 | INFO  | Text pasted at cursor (ydotool method)
```

### Success Logs (Kitty)
```
2025-09-30 15:44:01.017 | INFO | Detected terminal app: kitty, using Ctrl+Shift+V
2025-09-30 15:44:01.025 | INFO | Text pasted at cursor (wtype method)
```

## Troubleshooting

### Still Getting "Permission denied"?

1. **Check who owns the socket:**
   ```bash
   ls -la /tmp/.ydotool_socket
   ```
   If it shows `root`, run `./fix_ydotool.sh` again.

2. **Check if root daemon is still running:**
   ```bash
   ps aux | grep ydotoold | grep root
   ```
   If found, you need to find and disable what's starting it.

3. **Check your user is in the input group:**
   ```bash
   groups | grep input
   ```
   If not found, you may have logged in before the group was added. Log out and back in.

### Paste Still Doesn't Work in Windsurf?

Try these in order:

1. **Test method 3 (direct typing):**
   ```bash
   ./test_paste.py 3
   ```
   If this works, ydotool isn't configured properly but wtype direct typing works.

2. **Check Windsurf window focus:**
   Ensure Windsurf is the active window when paste happens.

3. **Increase the delay:**
   Edit `hypr-voice/hypr_voice.py` line 1159:
   ```python
   time.sleep(0.3)  # Try 0.5 or 0.7
   ```

4. **Check Windsurf is detected as Electron:**
   Add logging to see if detection works:
   ```python
   logger.debug(f"Current app: {self.current_app}, is_electron: {is_electron}")
   ```

## Alternative Solutions

### If ydotool Continues to Have Issues

The fallback methods will automatically trigger:

1. **Method 2 (wtype)**: Tries wtype with Ctrl+V
2. **Method 3 (hyprctl)**: Uses Hyprland IPC to send paste command
3. **Method 4 (direct typing)**: Types character-by-character (slow but reliable)

To **force** direct typing (skip ydotool):
```python
# In hypr_voice.py, comment out the ydotool section:
# if is_electron:
#     try:
#         ...ydotool code...
```

## Configuration Reference

### Your Current Setup

**Hyprland config**: `~/.config/hypr/hyprland.conf`
```conf
env = YDOTOOL_SOCKET,/tmp/.ydotool_socket  # ✅ Already set
exec-once = ydotoold  # ← Add this line
```

**Hypr-Voice**: Already configured to detect and handle Electron apps

**Test script**: `./test_paste.py 6` - tests ydotool directly

## Summary Checklist

- [ ] Run `./fix_ydotool.sh`
- [ ] Find and disable root ydotool service
- [ ] Add `exec-once = ydotoold` to Hyprland config
- [ ] Restart Hyprland
- [ ] Verify only ONE ydotoold (as your user)
- [ ] Test with `./test_paste.py 6` in Windsurf
- [ ] Test Hypr-Voice voice input in Windsurf
- [ ] Celebrate! 🎉

## Quick Test Commands

```bash
# One-line check
ps aux | grep ydotoold | grep -v grep && ls -la /tmp/.ydotool_socket && ydotool key 1:0

# Expected output:
# mewtwo ... ydotoold
# srw------- 1 mewtwo input ... /tmp/.ydotool_socket
# (no error from ydotool)
```

## Files Reference

- **Main fix**: `./fix_ydotool.sh`
- **Test script**: `./test_paste.py`
- **Diagnostic**: `./diagnose_paste.sh`
- **Setup script**: `./setup_ydotool.sh`
- **Updated code**: `hypr-voice/hypr_voice.py` (paste_to_cursor function)
- **Detailed docs**: `WINDSURF_PASTE_FIX.md`, `PASTE_FIX_README.md`
