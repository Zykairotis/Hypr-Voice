# Universal Clipboard Module

Cross-platform clipboard support for X11 and Wayland primary selection with programmatic paste capabilities.

## Features

- **Automatic Backend Detection**: Seamlessly switches between X11 (xsel/xclip) and Wayland (wl-clipboard)
- **Primary Selection Support**: Full support for X11-style select-to-copy, middle-click paste
- **Programmatic Paste**: Simulate middle-click or type text programmatically
- **Selection Monitoring**: Watch for selection changes in real-time
- **Cross-Platform**: Works on X11, Wayland, and hybrid environments

## Installation

### System Dependencies

**X11:**
```bash
# Ubuntu/Debian
sudo apt install xsel xclip xdotool

# Arch Linux
sudo pacman -S xsel xclip xdotool

# Fedora
sudo dnf install xsel xclip xdotool
```

**Wayland:**
```bash
# Ubuntu/Debian
sudo apt install wl-clipboard wtype

# Arch Linux
sudo pacman -S wl-clipboard wtype

# Fedora
sudo dnf install wl-clipboard wtype
```

**Cross-platform (ydotool):**
```bash
# Ubuntu/Debian
sudo apt install ydotool
sudo usermod -a -G input $USER  # Add user to input group

# Arch Linux
sudo pacman -S ydotool
sudo gpasswd -a $USER input

# Fedora
sudo dnf install ydotool
sudo usermod -a -G input $USER
```

### Python Module

```bash
# Add to your Python path
export PYTHONPATH="/path/to/Hypr-Voice/src:$PYTHONPATH"
```

## Usage

### Command-Line Interface

```bash
# Paste primary selection
python cli.py

# Copy text to primary selection
python cli.py --copy "Hello, world!"

# Type text programmatically (useful when paste is blocked)
python cli.py --type "Hello, world!"

# Monitor selection changes
python cli.py --monitor
```

### Python API

```python
from universal_clipboard import (
    UniversalClipboard,
    ProgrammaticPaster,
    PrimarySelectionMonitor
)

# Access primary selection
clipboard = UniversalClipboard()

# Get current selection
text = clipboard.get_primary()
print(f"Current selection: {text}")

# Set selection
clipboard.set_primary("New text")

# Programmatic paste
paster = ProgrammaticPaster()

# Simulate middle-click paste
paster.paste(delay=0.5)  # 500ms delay for focus

# Type text instead
paster.paste_text("Hello, world!", delay=0.5)

# Monitor selection changes
def on_change(text):
    print(f"Selection changed: {text}")

monitor = PrimarySelectionMonitor()
monitor.start(on_change)

# Later...
monitor.stop()
```

### Backend-Specific Usage

**X11 Only:**
```python
from universal_clipboard import X11PrimarySelection

x11 = X11PrimarySelection()
text = x11.get_primary()
x11.set_primary("X11 text")
```

**Wayland Only:**
```python
from universal_clipboard import WaylandPrimarySelection

wayland = WaylandPrimarySelection()
text = wayland.get_primary()
wayland.set_primary("Wayland text")
```

## Architecture

### Primary Selection Mechanisms

**X11 PRIMARY:**
- Automatic on text highlight (select-to-copy)
- Middle-click paste (Button-2)
- Asynchronous property-based transfer
- Network transparent

**Wayland Primary:**
- Optional protocol (`zwp_primary_selection_unstable_v1`)
- Client sets source after selection
- Pipe-based fd transfer
- Compositor-mediated security

### Programmatic Paste Methods

| Method | Platform | Requirements | Notes |
|--------|----------|--------------|-------|
| **xdotool** | X11 only | XTEST extension | Simple, no root |
| **ydotool** | X11, Wayland, TTY | input group | uinput-based |
| **wtype** | Wayland only | virtual_keyboard protocol | Native Wayland |

### Terminal Compatibility

| Terminal | X11 Primary | Wayland Primary | Notes |
|----------|-------------|-----------------|-------|
| **foot** | Excellent | Excellent (native) | Best Wayland support |
| **kitty** | Good | Partial | Configurable |
| **Alacritty** | Partial | Limited | Known issues |
| **GNOME Console** | Standard GTK | Standard GTK | Desktop integration |

## API Reference

### `UniversalClipboard`

Main class for automatic backend detection and clipboard access.

```python
clipboard = UniversalClipboard(timeout=5)

# Check availability
clipboard.is_available() -> bool

# Get backend type
clipboard.get_backend() -> Literal['x11', 'wayland', 'unknown']

# Get primary selection
clipboard.get_primary() -> Optional[str]

# Set primary selection
clipboard.set_primary(text: str) -> bool
```

### `X11PrimarySelection`

X11-specific clipboard using xsel/xclip.

```python
x11 = X11PrimarySelection(timeout=5)

x11.is_available() -> bool
x11.get_primary() -> Optional[str]
x11.set_primary(text: str) -> bool
```

### `WaylandPrimarySelection`

Wayland-specific clipboard using wl-clipboard.

```python
wayland = WaylandPrimarySelection(timeout=5)

wayland.is_available() -> bool
wayland.get_primary() -> Optional[str]
wayland.set_primary(text: str) -> bool
```

### `ProgrammaticPaster`

Programmatic paste simulation.

```python
paster = ProgrammaticPaster(method='auto')

paster.is_available() -> bool
paster.paste(delay=0.1) -> bool
paster.paste_text(text: str, delay=0.1) -> bool
```

### `PrimarySelectionMonitor`

Monitor selection changes in real-time.

```python
monitor = PrimarySelectionMonitor(poll_interval=0.5)

def callback(text: str):
    print(f"Changed: {text}")

monitor.start(callback)
monitor.stop()
```

## Troubleshooting

### Primary Selection Not Working

1. **Verify compositor support:**
   ```bash
   wayland-info | grep primary
   ```

2. **Test tools directly:**
   ```bash
   # Wayland
   wl-paste --primary
   wl-copy --primary "test"

   # X11
   xsel -o -p
   xsel -i -p <<< "test"
   ```

3. **Check application type:**
   - Native Wayland apps work best
   - XWayland apps may need sync tools

### Programmatic Paste Fails

1. **Check tool availability:**
   ```bash
   which xdotool ydotool wtype
   ```

2. **Verify permissions (ydotool):**
   ```bash
   groups $USER | grep input
   ```

3. **Test virtual keyboard (wtype):**
   ```bash
   wayland-info | grep virtual_keyboard
   ```

### Subprocess Hangs

All subprocess calls include timeouts, but if issues persist:

1. Check for dead selection owners
2. Reduce timeout in constructor
3. Use error handling patterns from examples

## Examples

### Quick Copy-Paste Script

```python
#!/usr/bin/env python3
import sys
from universal_clipboard import UniversalClipboard, ProgrammaticPaster

def main():
    if len(sys.argv) > 1:
        # Copy to primary
        clipboard = UniversalClipboard()
        clipboard.set_primary(sys.argv[1])
        print(f"Copied: {sys.argv[1]}")
    else:
        # Paste from primary
        paster = ProgrammaticPaster()
        print("Pasting in 2 seconds...")
        paster.paste(delay=2.0)

if __name__ == '__main__':
    main()
```

### Selection Logger

```python
#!/usr/bin/env python3
from universal_clipboard import PrimarySelectionMonitor
import datetime

def log_selection(text):
    timestamp = datetime.datetime.now().isoformat()
    with open('selection_log.txt', 'a') as f:
        f.write(f"{timestamp}: {text}\n")
    print(f"[{timestamp}] Logged: {text[:50]}...")

monitor = PrimarySelectionMonitor()
monitor.start(log_selection)

print("Logging selections (Ctrl+C to stop)...")
import signal
import time

def signal_handler(sig, frame):
    monitor.stop()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True:
    time.sleep(1)
```

### Clipboard Sync

```python
#!/usr/bin/env python3
"""
Sync primary selection to clipboard periodically.
"""

import time
from universal_clipboard import UniversalClipboard

clipboard = UniversalClipboard()

last_primary = ""
while True:
    current = clipboard.get_primary()
    if current and current != last_primary:
        # Sync to clipboard (implementation dependent)
        last_primary = current
        print(f"Synced: {current[:50]}...")
    time.sleep(0.5)
```

## Security Considerations

1. **Pastejacking:** Be aware that programmatic paste can be exploited
2. **Validation:** Always validate clipboard content before use
3. **Permissions:** Some tools (ydotool) require elevated permissions
4. **X11 Security:** X11 PRIMARY is inherently less secure than Wayland

## Contributing

When adding features:

1. Support both X11 and Wayland
2. Include timeout handling
3. Test on multiple compositors
4. Document terminal compatibility
5. Handle errors gracefully

## License

Part of the Hypr-Voice project.

## References

- [X11 ICCCM](https://x.org/releases/X11R7.6/doc/xorg-docs/specs/ICCCM/icccm.html)
- [Wayland Primary Selection Protocol](https://wayland.app/protocols/primary-selection-unstable-v1)
- [wl-clipboard](https://github.com/bugaevc/wl-clipboard)
- [xdotool](https://manpages.ubuntu.com/manpages/trusty/man1/xdotool.1.html)
- [ydotool](https://github.com/ReimuNotMoe/ydotool)
- [wtype](https://github.com/atx/wtype)
