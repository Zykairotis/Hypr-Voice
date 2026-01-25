# 🔄 Vocabulary Update Behavior Analysis

## Current Implementation

### ✅ How It Works Now:

1. **Background Window Monitoring** (Running every 100ms):
   - Monitors for window changes using `hyprctl activewindow -j`
   - Detects when you switch applications
   - **Logs the change** but doesn't update vocabulary yet

2. **Before Each Transcription** (On-demand):
   - Gets current active window
   - Calls `vocabulary_manager.update_vocabulary(app_class, app_title)`
   - Updates vocabulary with current application context

### Timeline:
```
You switch from Terminal → Cursor
    ↓
Background monitor detects change (100ms)
    ↓
Logs: "Window changed: cursor - Cursor - file.py"
    ↓
Vocabulary: NOT updated yet (still using terminal vocab)
    ↓
You press push-to-talk to speak
    ↓
BEFORE transcription: Updates vocabulary to Cursor
    ↓
Transcription happens with Cursor vocabulary ✅
```

---

## ⚠️ The Issue

**Vocabulary updates BEFORE each transcription, not WHEN you switch apps.**

This means:
- ✅ You switch to Cursor → speak → uses Cursor vocabulary (correct)
- ⚠️ You switch to Terminal → wait 5 seconds → speak → uses Terminal vocabulary (correct)
- ✅ The vocabulary is always correct for the CURRENT window at transcription time

---

## ✅ The Solution

I'll enhance the system to update vocabulary **immediately when you switch apps**, not just before transcription:

### Update the window monitoring code to trigger vocabulary updates:
