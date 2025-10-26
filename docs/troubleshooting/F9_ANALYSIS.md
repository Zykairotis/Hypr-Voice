# F9 Blocking Issue - Deep Analysis

**Current Understanding:**

## Flow When You Release F9:
1. **bindr F9** → `hypr-voice-control.sh stop` → sends "STOP" to socket
2. **Hypr-Voice client** receives "STOP" command
3. **Client processes:**
   - Stop recording (fast)
   - Send to Whisper for transcription (GPU fast ~1s)
   - Receive transcribed text
   - Call `paste_to_cursor(text)` → **subprocess.run(universal_paste.sh)**
   - **universal_paste.sh runs wtype** (this is where F9 gets blocked)

## Root Cause:
The **subprocess.run()** call in `paste_to_cursor()` is **synchronous blocking**. While wtype is typing, the entire Hypr-Voice client process is blocked and cannot accept new socket connections. This means F9 keybinds cannot register new commands.

## Solution Options:

### Option 1: Make paste non-blocking (Recommended)
Change `paste_to_cursor()` to run in background thread so client can immediately accept new F9 commands.

### Option 2: Reduce wtype execution time
- wtype is already at maximum speed (-d 0 is default)
- Focus on making the subprocess call non-blocking

### Option 3: Queue paste operations
- Return immediately after starting paste
- Let paste complete in background

## Key Insight:
The issue isn't wtype speed - it's that the **client blocks while waiting for wtype to complete**. We need to make the paste operation asynchronous so the client can immediately handle new F9 commands.