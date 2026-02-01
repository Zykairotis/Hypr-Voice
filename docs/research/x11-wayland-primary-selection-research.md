# X11 PRIMARY Selection and Wayland Equivalents Research

## Executive Summary

This research document covers X11 PRIMARY selection (middle-click paste), Wayland equivalents, programmatic paste mechanisms, and Python implementation examples for universal paste functionality.

---

## 1. X11 PRIMARY Selection Mechanism

### 1.1 How PRIMARY Selection Works

The X11 PRIMARY selection enables instant "select-to-copy, middle-click-to-paste" functionality, distinct from the CLIPBOARD (Ctrl+C/V) mechanism defined in the ICCCM (Inter-Client Communication Conventions Manual).

#### Protocol Flow

1. **Selection (Copy) Phase:**
   - User highlights text in an X11 application
   - Owning client calls `XSetSelectionOwner(display, PRIMARY_atom, window, timestamp)`
   - Client claims ownership of the PRIMARY selection atom
   - Data is NOT stored centrally; client holds a promise to supply it on request

2. **Paste Phase (Middle-Click):**
   - User middle-clicks (Button-2) in target window
   - Target client queries owner: `XGetSelectionOwner(display, PRIMARY_atom)`
   - Target issues: `XConvertSelection(display, PRIMARY_atom, target, property, requestor, time)`
   - This triggers a `SelectionRequest` event to the owner

3. **Data Transfer Phase:**
   - Owner responds by setting property on requestor's window: `XChangeProperty()`
   - Owner sends `SelectionNotify` event to confirm
   - Target reads data via `XGetProperty()`
   - Target inserts text at cursor and deletes property

#### Key Characteristics

- **Implicit Operation:** No explicit copy command needed
- **Asynchronous:** Data transferred on-demand via events
- **Owner-Dependent:** Selection lost if source app closes
- **Network Transparent:** Works over X11 network connections
- **Format Negotiation:** Supports multiple targets (TEXT, UTF8_STRING, etc.)

### 1.2 PRIMARY vs CLIPBOARD

| Aspect | PRIMARY | CLIPBOARD |
|--------|---------|-----------|
| Activation | Auto on text highlight | Explicit (Ctrl+C/Cmd+C) |
| Paste | Middle-click (Button-2) | Ctrl+V/Cmd+V |
| Persistence | Lost when owner app exits | Often managed by clipboard managers |
| Data Transfer | On-demand via X events | Typically stored centrally |
| Typical Use | Quick terminal/editor operations | Explicit user actions |

---

## 2. Wayland Primary Selection Support

### 2.1 Protocol Overview

Wayland lacks native PRIMARY selection in the core protocol but supports it via the unstable protocol:
- **Protocol:** `zwp_primary_selection_unstable_v1`
- **Interface:** `zwp_primary_selection_device_manager_v1`

#### Protocol Differences from X11

| Aspect | X11 PRIMARY | Wayland Primary |
|--------|-------------|-----------------|
| Activation | Auto on select | Client sets source after select |
| Data Transfer | Properties/events (chunked) | Pipe fds with MIME types |
| Scope | Global, network-aware | Per-seat, local, focus-dependent |
| Compositor Dependency | None (X server) | Required (wlroots, Mutter, KWin) |
| Security Model | Any client can hijack | Compositor-mediated, more secure |

### 2.2 Compositor Support

All major Wayland compositors support the primary selection protocol:

| Compositor | Support Status | Version Required | Notes |
|------------|----------------|------------------|-------|
| **Hyprland** | Full support | v0.48+ | wlroots-based; XWayland sync issues possible |
| **Sway** | Full support | v1.11+ | Native wlroots support |
| **GNOME (Mutter)** | Enabled by default | v48+ | Via ext-primary-selection |
| **KDE (KWin)** | Full support | v6.4+ | Protocol compliant |

#### Verification

```bash
# Check if primary selection protocol is available
wayland-info | grep primary

# Test functionality
wl-paste --primary  # Should not error if supported
```

### 2.3 Wayland Protocol Flow

1. **Get Manager:**
   ```python
   # Bind to zwp_primary_selection_device_manager_v1 global
   manager = registry.bind(manager_interface, version)
   ```

2. **Create Device:**
   ```python
   device = manager.get_device(seat)  # seat from wl_seat global
   ```

3. **Set Selection (Copy):**
   ```python
   source = manager.create_source()
   source.offer("text/plain")
   source.offer("text/plain;charset=utf-8")
   device.set_selection(source, serial)  # serial from pointer event
   ```

4. **Handle Data Request:**
   ```python
   def on_send(source, mime_type, fd):
       os.write(fd, data.encode())
       os.close(fd)
   ```

---

## 3. Programmatic Paste Tools

### 3.1 X11 Tools

#### xdotool (X11 only)

```bash
# Simulate middle-click at current position
xdotool click 2

# Click at specific coordinates
xdotool click --window WINDOW_ID 2

# Type selection instead of clicking
xsel -o -p | xdotool type --file -
```

**Limitations:**
- X11 only (fails on Wayland)
- Requires XTEST extension
- No window management on Wayland

#### xsel / xclip

```bash
# Read primary selection
xsel -o -p          # Output primary
xclip -selection primary -o

# Write to primary selection
echo "text" | xsel -i -p
echo "text" | xclip -selection primary -i

# Paste by combining with xdotool
xsel -o -p | xdotool type --file -
```

### 3.2 Wayland Tools

#### ydotool (Cross-platform)

```bash
# Simulate middle-click (requires root or input group)
ydotool click 0xC2  # Middle button code

# Alternative: type clipboard contents
wl-paste --primary | ydotool type -

# Setup permissions
sudo usermod -a -G input $USER
```

**Advantages:**
- Works on X11, Wayland, and TTY
- Uses uinput for device-level simulation
- No X11 dependencies

**Disadvantages:**
- Requires root or input group membership
- Less intuitive syntax than xdotool
- No window management functions

#### wtype (Wayland-only typing)

```bash
# Type clipboard contents character-by-character
wl-paste --primary | wtype -d 20 -

# With delay for focus timing
sleep 0.5 && wl-paste | wtype -

# Requires virtual-keyboard protocol support
wayland-info | grep virtual_keyboard
```

**Advantages:**
- Native Wayland solution
- No root required
- Supports Unicode, modifiers, delays

**Disadvantages:**
- Requires `zwp_virtual_keyboard_manager_v1` support
- May not work on GNOME/KDE
- Character-by-character typing is slow

#### dotool

```bash
# Stream commands
echo "click middle" | dotool

# Chain with delays
echo "click middle; sleep 0.5; click middle" | dotool
```

**Advantages:**
- Streams commands
- Chaining support
- Broad compatibility

---

## 4. Terminal and Application Compatibility

### 4.1 Terminal Emulators

| Terminal | X11 Primary | Wayland Primary | Notes |
|----------|-------------|-----------------|-------|
| **Alacritty** | Partial (bugs reported) | Limited | Relies on winit/GLFW; selection issues |
| **foot** | Full | Full (native) | Auto-copy on release; excellent Wayland support |
| **kitty** | Full | Partial | Configurable via `copy_on_select` option |
| **GNOME Console** | Standard GTK | Standard GTK | Right-click menu; syncs via clipboard managers |

#### Terminal Configuration Examples

**foot:**
```ini
# Foot has excellent primary selection support by default
# Shift+insert to paste primary selection
# Ctrl+shift+r to paste clipboard
```

**kitty:**
```kitty
# Enable copy on select
copy_on_select yes
# Select target: clipboard, primary, or both
select_by_word_characters @-./_~?&=%+#
```

**Alacritty:**
```yaml
# Alacritty has known issues with primary selection
# Use clipboard managers or manual copy instead
selection:
  save_to_clipboard: true  # Use clipboard instead
```

### 4.2 GUI Application Support

**Native Wayland Applications:**
- Most GTK4/Qt6 applications support primary selection
- Firefox (Wayland build): Full support
- GNOME/KDE applications: Varies by desktop environment settings

**XWayland Applications:**
- Generally work but may not sync with Wayland primary selection
- May need synchronization tools

**Configuration:**
```bash
# GNOME: Enable primary paste
gsettings set org.gnome.desktop.interface gtk-enable-primary-paste true

# Or use GNOME Tweaks
```

---

## 5. Python Implementation Examples

### 5.1 X11 Primary Selection with xsel/xclip

```python
#!/usr/bin/env python3
"""
X11 PRIMARY Selection Utilities

Supports both xsel and xclip with automatic fallback.
"""

import subprocess
import shutil
from typing import Optional

class X11PrimarySelection:
    """Handle X11 PRIMARY selection (middle-click paste)."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.tool = self._detect_tool()

    def _detect_tool(self) -> Optional[str]:
        """Detect available clipboard tool."""
        for tool in ['xsel', 'xclip']:
            if shutil.which(tool):
                return tool
        return None

    def is_available(self) -> bool:
        """Check if X11 primary selection is available."""
        return self.tool is not None

    def get_primary(self) -> Optional[str]:
        """
        Get text from X11 PRIMARY selection.

        Returns:
            Text content or None if unavailable/empty
        """
        if not self.tool:
            raise RuntimeError("No clipboard tool available (install xsel or xclip)")

        try:
            if self.tool == 'xsel':
                result = subprocess.run(
                    ['xsel', '-p', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
            else:  # xclip
                result = subprocess.run(
                    ['xclip', '-selection', 'primary', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )

            return result.stdout.strip()

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return None

    def set_primary(self, text: str) -> bool:
        """
        Set text to X11 PRIMARY selection.

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        if not self.tool:
            raise RuntimeError("No clipboard tool available (install xsel or xclip)")

        try:
            if self.tool == 'xsel':
                subprocess.run(
                    ['xsel', '-i', '-p'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
            else:  # xclip
                subprocess.run(
                    ['xclip', '-selection', 'primary', '-i'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
            return True

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            return False

# Usage example
if __name__ == "__main__":
    x11 = X11PrimarySelection()

    if x11.is_available():
        # Get current selection
        text = x11.get_primary()
        print(f"Primary selection: {text}")

        # Set new selection
        x11.set_primary("Hello from X11!")
    else:
        print("X11 primary selection not available")
```

### 5.2 Wayland Primary Selection with wl-clipboard

```python
#!/usr/bin/env python3
"""
Wayland PRIMARY Selection Utilities

Uses wl-clipboard (wl-copy/wl-paste) for Wayland selection support.
"""

import subprocess
import shutil
import os
from typing import Optional

class WaylandPrimarySelection:
    """Handle Wayland primary selection."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self._check_wayland()

    def _check_wayland(self) -> bool:
        """Check if running on Wayland."""
        return os.environ.get('WAYLAND_DISPLAY') is not None

    def is_available(self) -> bool:
        """Check if Wayland primary selection is available."""
        if not self._check_wayland():
            return False
        return shutil.which('wl-paste') is not None

    def get_primary(self) -> Optional[str]:
        """
        Get text from Wayland primary selection.

        Returns:
            Text content or None if unavailable/empty
        """
        if not self.is_available():
            raise RuntimeError("Wayland primary selection not available")

        try:
            result = subprocess.run(
                ['wl-paste', '--primary'],
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout.strip()

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return None

    def set_primary(self, text: str) -> bool:
        """
        Set text to Wayland primary selection.

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        if not self.is_available():
            raise RuntimeError("Wayland primary selection not available")

        try:
            subprocess.run(
                ['wl-copy', '--primary'],
                input=text,
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout
            )
            return True

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

# Usage example
if __name__ == "__main__":
    wayland = WaylandPrimarySelection()

    if wayland.is_available():
        # Get current selection
        text = wayland.get_primary()
        print(f"Primary selection: {text}")

        # Set new selection
        wayland.set_primary("Hello from Wayland!")
    else:
        print("Wayland primary selection not available")
```

### 5.3 Universal Paste (X11 + Wayland)

```python
#!/usr/bin/env python3
"""
Universal Clipboard/Paste System

Automatically detects and uses the best available clipboard mechanism:
- X11 PRIMARY selection (xsel/xclip)
- Wayland primary selection (wl-clipboard)
- Fallback to standard clipboard
"""

import os
import shutil
import subprocess
from typing import Optional, Literal

type ClipboardType = Literal['x11', 'wayland', 'unknown']

class UniversalClipboard:
    """Universal clipboard supporting X11 and Wayland."""

    def __init__(self, timeout: int = 5):
        self.timeout = timeout
        self.backend = self._detect_backend()

    def _detect_backend(self) -> ClipboardType:
        """Detect clipboard backend."""
        # Check Wayland first
        if os.environ.get('WAYLAND_DISPLAY'):
            if shutil.which('wl-paste'):
                return 'wayland'

        # Check X11
        if os.environ.get('DISPLAY'):
            if shutil.which('xsel') or shutil.which('xclip'):
                return 'x11'

        return 'unknown'

    def is_available(self) -> bool:
        """Check if any clipboard is available."""
        return self.backend != 'unknown'

    def get_backend(self) -> ClipboardType:
        """Get current backend name."""
        return self.backend

    def get_primary(self) -> Optional[str]:
        """
        Get text from primary selection (auto-detect backend).

        Returns:
            Text content or None if unavailable
        """
        if self.backend == 'wayland':
            return self._get_wayland_primary()
        elif self.backend == 'x11':
            return self._get_x11_primary()
        return None

    def set_primary(self, text: str) -> bool:
        """
        Set text to primary selection (auto-detect backend).

        Args:
            text: Text to copy

        Returns:
            True if successful
        """
        if self.backend == 'wayland':
            return self._set_wayland_primary(text)
        elif self.backend == 'x11':
            return self._set_x11_primary(text)
        return False

    def _get_x11_primary(self) -> Optional[str]:
        """Get X11 primary selection."""
        # Try xsel first, then xclip
        if shutil.which('xsel'):
            try:
                result = subprocess.run(
                    ['xsel', '-p', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        if shutil.which('xclip'):
            try:
                result = subprocess.run(
                    ['xclip', '-selection', 'primary', '-o'],
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return result.stdout.strip()
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        return None

    def _set_x11_primary(self, text: str) -> bool:
        """Set X11 primary selection."""
        if shutil.which('xsel'):
            try:
                subprocess.run(
                    ['xsel', '-i', '-p'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        if shutil.which('xclip'):
            try:
                subprocess.run(
                    ['xclip', '-selection', 'primary', '-i'],
                    input=text,
                    capture_output=True,
                    check=True,
                    text=True,
                    timeout=self.timeout
                )
                return True
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                pass

        return False

    def _get_wayland_primary(self) -> Optional[str]:
        """Get Wayland primary selection."""
        try:
            result = subprocess.run(
                ['wl-paste', '--primary'],
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout
            )
            return result.stdout.strip()
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return None

    def _set_wayland_primary(self, text: str) -> bool:
        """Set Wayland primary selection."""
        try:
            subprocess.run(
                ['wl-copy', '--primary'],
                input=text,
                capture_output=True,
                check=True,
                text=True,
                timeout=self.timeout
            )
            return True
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return False

# Usage example
if __name__ == "__main__":
    clipboard = UniversalClipboard()

    print(f"Backend: {clipboard.get_backend()}")

    if clipboard.is_available():
        # Get current selection
        text = clipboard.get_primary()
        print(f"Current selection: {text}")

        # Set new selection
        clipboard.set_primary("Hello, universal world!")

        # Verify
        new_text = clipboard.get_primary()
        print(f"New selection: {new_text}")
    else:
        print("No clipboard backend available")
```

### 5.4 Programmatic Middle-Click Paste

```python
#!/usr/bin/env python3
"""
Programmatic Middle-Click Paste

Simulates middle-click paste on X11 and Wayland.
"""

import os
import shutil
import subprocess
import time
from typing import Literal

type PasteMethod = Literal['xdotool', 'ydotool', 'wtype', 'none']

class ProgrammaticPaster:
    """Programmatically paste via middle-click simulation."""

    def __init__(self, method: PasteMethod = 'auto'):
        self.method = self._detect_method() if method == 'auto' else method

    def _detect_method(self) -> PasteMethod:
        """Detect best available paste method."""
        # Prefer wtype on Wayland
        if os.environ.get('WAYLAND_DISPLAY'):
            if shutil.which('wtype') and shutil.which('wl-paste'):
                # Verify virtual keyboard support
                try:
                    result = subprocess.run(
                        ['wayland-info'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    if 'virtual_keyboard' in result.stdout:
                        return 'wtype'
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    pass

            # Fall back to ydotool
            if shutil.which('ydotool'):
                return 'ydotool'

        # Use xdotool on X11
        if os.environ.get('DISPLAY'):
            if shutil.which('xdotool'):
                return 'xdotool'

        return 'none'

    def is_available(self) -> bool:
        """Check if paste method is available."""
        return self.method != 'none'

    def paste(self, delay: float = 0.1) -> bool:
        """
        Simulate middle-click paste.

        Args:
            delay: Delay before paste (for focus)

        Returns:
            True if successful
        """
        if delay > 0:
            time.sleep(delay)

        if self.method == 'xdotool':
            return self._paste_xdotool()
        elif self.method == 'ydotool':
            return self._paste_ydotool()
        elif self.method == 'wtype':
            return self._paste_wtype()
        return False

    def paste_text(self, text: str, delay: float = 0.1) -> bool:
        """
        Type text instead of middle-click paste.

        Args:
            text: Text to type
            delay: Delay before typing (for focus)

        Returns:
            True if successful
        """
        if delay > 0:
            time.sleep(delay)

        if self.method == 'xdotool':
            return self._type_xdotool(text)
        elif self.method == 'ydotool':
            return self._type_ydotool(text)
        elif self.method == 'wtype':
            return self._type_wtype(text)
        return False

    def _paste_xdotool(self) -> bool:
        """Paste using xdotool middle-click."""
        try:
            subprocess.run(
                ['xdotool', 'click', '2'],
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _type_xdotool(self, text: str) -> bool:
        """Type text using xdotool."""
        try:
            # xdotool doesn't support stdin, so we need a temp file
            with open('/tmp/xdotool_type.txt', 'w') as f:
                f.write(text)

            subprocess.run(
                ['xdotool', 'type', '--file', '/tmp/xdotool_type.txt'],
                capture_output=True,
                check=True,
                timeout=10  # Longer timeout for typing
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, IOError):
            return False

    def _paste_ydotool(self) -> bool:
        """Paste using ydotool middle-click."""
        try:
            subprocess.run(
                ['ydotool', 'click', '0xC2'],  # Middle button code
                capture_output=True,
                check=True,
                timeout=2
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _type_ydotool(self, text: str) -> bool:
        """Type text using ydotool."""
        try:
            subprocess.run(
                ['ydotool', 'type', text],
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _paste_wtype(self) -> bool:
        """Paste using wtype (type primary selection)."""
        try:
            # Get primary selection and type it
            subprocess.run(
                'wl-paste --primary | wtype -d 20 -',
                shell=True,
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

    def _type_wtype(self, text: str) -> bool:
        """Type text using wtype."""
        try:
            subprocess.run(
                ['wtype', '-d', '20', text],
                capture_output=True,
                check=True,
                timeout=10
            )
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False

# Usage example
if __name__ == "__main__":
    paster = ProgrammaticPaster()

    print(f"Method: {paster.method}")

    if paster.is_available():
        # Simulate middle-click paste
        print("Pasting in 2 seconds... (focus target window)")
        paster.paste(delay=2.0)

        # Or type specific text
        # paster.paste_text("Hello, world!", delay=2.0)
    else:
        print("No paste method available")
```

### 5.5 Advanced: Monitor Primary Selection Changes

```python
#!/usr/bin/env python3
"""
Monitor Primary Selection Changes

Watches for changes to the primary selection and triggers callbacks.
"""

import subprocess
import threading
import time
from typing import Callable, Optional

class PrimarySelectionMonitor:
    """Monitor primary selection for changes."""

    def __init__(self, poll_interval: float = 0.5):
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._last_content = ""
        self._callback: Optional[Callable[[str], None]] = None

    def _get_primary(self) -> Optional[str]:
        """Get current primary selection content."""
        try:
            # Try wl-paste first (Wayland), then xsel (X11)
            for cmd in [['wl-paste', '--primary'], ['xsel', '-p', '-o']]:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        check=True,
                        text=True,
                        timeout=1
                    )
                    return result.stdout.strip()
                except (subprocess.CalledProcessError, FileNotFoundError):
                    continue
        except subprocess.TimeoutExpired:
            pass
        return None

    def _monitor_loop(self):
        """Monitoring loop."""
        while self._running:
            content = self._get_primary()

            if content is not None and content != self._last_content:
                if self._callback:
                    self._callback(content)
                self._last_content = content

            time.sleep(self.poll_interval)

    def start(self, callback: Callable[[str], None]):
        """
        Start monitoring primary selection.

        Args:
            callback: Function to call when selection changes
        """
        if self._running:
            return

        self._callback = callback
        self._running = True
        self._last_content = self._get_primary() or ""

        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop monitoring."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None

# Usage example
if __name__ == "__main__":
    def on_selection_change(text: str):
        print(f"Selection changed: {text[:50]}...")

    monitor = PrimarySelectionMonitor()
    monitor.start(on_selection_change)

    print("Monitoring primary selection (Ctrl+C to stop)...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        monitor.stop()
        print("Stopped monitoring")
```

---

## 6. Integration Examples

### 6.1 Quick Copy-Paste Script

```python
#!/usr/bin/env python3
"""
Quick universal copy-paste utility.

Usage:
    python universal_paste.py              # Paste primary selection
    python universal_paste.py --copy TEXT  # Copy text to primary
    python universal_paste.py --type TEXT  # Type text instead of paste
"""

import sys
import argparse
from universal_clipboard import UniversalClipboard
from programmatic_paste import ProgrammaticPaster

def main():
    parser = argparse.ArgumentParser(description='Universal clipboard utility')
    parser.add_argument('--copy', metavar='TEXT', help='Copy text to primary')
    parser.add_argument('--type', metavar='TEXT', help='Type text instead of paste')
    parser.add_argument('--delay', type=float, default=0.5,
                       help='Delay before paste/type (default: 0.5s)')

    args = parser.parse_args()

    clipboard = UniversalClipboard()

    if args.copy:
        # Copy to primary selection
        if clipboard.set_primary(args.copy):
            print(f"Copied to primary selection: {args.copy}")
        else:
            print("Failed to copy", file=sys.stderr)
            sys.exit(1)

    elif args.type:
        # Type text programmatically
        paster = ProgrammaticPaster()
        if paster.paste_text(args.type, delay=args.delay):
            print(f"Typed: {args.type}")
        else:
            print("Failed to type", file=sys.stderr)
            sys.exit(1)

    else:
        # Paste primary selection
        text = clipboard.get_primary()
        if text:
            print(text)
        else:
            print("No primary selection content", file=sys.stderr)
            sys.exit(1)

if __name__ == '__main__':
    main()
```

### 6.2 Clipboard Sync (X11 <-> Wayland)

```bash
#!/bin/bash
# Sync X11 primary selection to Wayland primary selection

# X11 -> Wayland
while true; do
    xsel -o -p | wl-copy --primary
    sleep 0.5
done &

# Wayland -> X11
while true; do
    wl-paste --primary | xsel -i -p
    sleep 0.5
done &
```

---

## 7. Best Practices and Recommendations

### 7.1 For Developers

1. **Detect Backend:**
   - Check `WAYLAND_DISPLAY` environment variable
   - Verify `DISPLAY` for X11
   - Test tool availability before use

2. **Error Handling:**
   - Always use timeouts for subprocess calls
   - Handle both `CalledProcessError` and `TimeoutExpired`
   - Provide fallback mechanisms

3. **User Experience:**
   - Add delays before programmatic paste for focus
   - Show feedback when copy/paste succeeds
   - Gracefully handle empty selections

4. **Security:**
   - Never use `shell=True` with user input
   - Validate clipboard content before use
   - Be aware of pastejacking risks

### 7.2 For Users

1. **Terminal Selection:**
   - Use foot or kitty for best Wayland primary selection support
   - Configure `copy_on_select` in your terminal
   - Use Shift+insert to paste primary selection

2. **Compositor Configuration:**
   - Enable primary selection in GNOME: `gsettings set org.gnome.desktop.interface gtk-enable-primary-paste true`
   - Use wlroots-based compositors (Sway, Hyprland) for best support
   - Install wl-clipboard for command-line access

3. **XWayland Compatibility:**
   - Be aware that XWayland apps may not sync with Wayland primary
   - Use synchronization tools like wl-clipboard-x11 if needed
   - Test both native and XWayland applications

### 7.3 Tool Recommendations

| Use Case | Recommended Tool | Notes |
|----------|------------------|-------|
| **X11 paste** | xdotool | Simple, no root required |
| **Wayland paste** | wtype | Native, but requires virtual keyboard |
| **Cross-platform** | ydotool | Works everywhere, needs root/input group |
| **Clipboard access** | wl-clipboard | Modern Wayland standard |
| **Terminal** | foot | Best Wayland support |
| **GUI apps** | GTK4/Qt6 | Native primary selection support |

---

## 8. Troubleshooting

### 8.1 Primary Selection Not Working

**Symptoms:**
- Middle-click paste doesn't work
- `wl-paste --primary` returns error
- Selection not syncing between apps

**Solutions:**
1. Verify compositor support: `wayland-info | grep primary`
2. Check application is Wayland-native (not XWayland)
3. Enable primary selection in desktop settings
4. Restart affected applications

### 8.2 Programmatic Paste Fails

**Symptoms:**
- `xdotool` fails on Wayland
- `wtype` types nothing
- Permission denied errors

**Solutions:**
1. Use ydotool for Wayland (add user to input group)
2. Check virtual keyboard support: `wayland-info | grep virtual_keyboard`
3. Verify window focus before paste (add delay)
4. Test with simple command first: `wl-paste | wtype -`

### 8.3 Python Subprocess Hangs

**Symptoms:**
- Script hangs when calling clipboard tools
- Timeout errors

**Solutions:**
1. Always use `timeout` parameter in `subprocess.run()`
2. Use `capture_output=True` to handle output properly
3. Check for dead selection owners
4. Implement proper error handling

---

## 9. References

- **X11 ICCCM:** https://x.org/releases/X11R7.6/doc/xorg-docs/specs/ICCCM/icccm.html
- **Wayland Primary Selection Protocol:** https://wayland.app/protocols/primary-selection-unstable-v1
- **wl-clipboard:** https://github.com/bugaevc/wl-clipboard
- **xdotool:** https://manpages.ubuntu.com/manpages/trusty/man1/xdotool.1.html
- **ydotool:** https://github.com/ReimuNotMoe/ydotool
- **wtype:** https://github.com/atx/wtype
- **pywayland:** https://github.com/flacjacket/pywayland
- **pyperclip:** https://github.com/asweigart/pyperclip

---

## 10. Summary

**X11 PRIMARY Selection:**
- Mature, ubiquitous, works everywhere on X11
- Implicit select-to-copy, middle-click paste
- Network transparent, but less secure

**Wayland Primary Selection:**
- Optional protocol (zwp_primary_selection_unstable_v1)
- Supported by all major compositors (Hyprland, Sway, GNOME, KDE)
- More secure, compositor-mediated
- Requires protocol support in applications

**Programmatic Paste:**
- X11: xdotool (requires XTEST)
- Wayland: ydotool (uinput), wtype (virtual keyboard)
- Universal: Use wl-clipboard for clipboard access

**Python Integration:**
- Use subprocess with xsel/xclip for X11
- Use wl-clipboard for Wayland
- Always implement timeouts and error handling
- Detect backend automatically for best compatibility

**Application Support:**
- Terminals: foot > kitty > Alacritty (Wayland)
- GUI: GTK4/Qt6 have best support
- XWayland: May need sync tools

This research provides the foundation for implementing universal paste functionality that works across X11 and Wayland environments.
