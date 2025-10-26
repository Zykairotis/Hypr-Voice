# Terminal vs GUI Application Detection Research Report

## Executive Summary

This research report provides comprehensive analysis of methods for detecting whether the active application is a terminal emulator or a regular GUI application on Linux systems, with particular focus on Wayland/Hyprland environments. The research covers multiple detection approaches, tools, APIs, and practical implementation considerations.

## Research Findings

### 1. Current Implementation Analysis

**Existing Codebase Implementation** (`/home/mewtwo/Zykairotis/Hypr-Voice-main/hypr-voice/hypr_voice.py`):

The current Hypr-Voice implementation uses a basic window class detection approach:

```python
# Lines 1167-1172: Terminal emulator detection
terminal_apps = ['kitty', 'alacritty', 'foot', 'wezterm', 'terminator', 'konsole', 'gnome-terminal', 'xterm']
is_terminal = self.current_app and any(term in self.current_app.lower() for term in terminal_apps)

# Lines 1171-1172: Electron application detection
electron_apps = ['windsurf', 'code', 'cursor', 'vscodium', 'electron', 'discord', 'slack', 'teams']
is_electron = self.current_app and any(app in self.current_app.lower() for app in electron_apps)
```

**Active Window Detection Method** (Lines 210-238):
```python
async def update_active_window(self):
    """Get current active window from Hyprland"""
    result = subprocess.run(
        ["hyprctl", "activewindow", "-j"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        window_info = json.loads(result.stdout)
        app_class = window_info.get("class", "").lower()
```

**Current Limitations**:
- Limited to hardcoded application lists
- No dynamic detection of unknown terminals
- Missing Wayland-specific considerations
- No process tree analysis

### 2. Linux Window Class Detection Methods

#### 2.1 X11 Tools (Limited on Wayland)

**xprop** - X Window Property Display:
- `xprop` - Interactive window selection
- `xprop -id WINDOW_ID` - Query specific window
- `xprop -root _NET_ACTIVE_WINDOW` - Get active window ID
- **Limitation**: Only works for XWayland applications on Wayland

**wmctrl** - Window Manager Control:
- `wmctrl -l` - List all windows with IDs and titles
- `wmctrl -lp` - Include Process IDs
- **Limitation**: Requires EWMH support, not always available

**xdotool** - Advanced Window Automation:
- `xdotool getactivewindow` - Get active window ID
- `xdotool getactivewindow getwindowname` - Get window name
- `xdotool getactivewindow getwindowpid` - Get window PID
- **Limitation**: X11-only, fails on native Wayland

#### 2.2 Wayland Native Methods

**Hyprland (Primary Environment)**:
```bash
hyprctl activewindow -j    # JSON active window info
hyprctl clients -j         # All windows with properties
```

**Key Window Properties**:
- `class` - Window class/app_id
- `title` - Window title
- `pid` - Process ID
- `xwayland` - Boolean indicating XWayland status
- `initialClass` - Class at window creation

**Example Output**:
```json
{
  "class": "kitty",
  "title": "~",
  "pid": 12345,
  "xwayland": false,
  "monitor": 0,
  "workspace": {"id": 1, "name": "1"}
}
```

### 3. Terminal Emulator Identification Techniques

#### 3.1 Window Class Detection

**Common Terminal WM_CLASS Values**:
- **Alacritty**: `"Alacritty", "Alacritty"`
- **Kitty**: `"kitty", "kitty"`
- **Foot**: `"foot", "foot"`
- **WezTerm**: `"wezterm", "WezTerm"`
- **GNOME Terminal**: `"gnome-terminal", "Gnome-terminal"`
- **Konsole**: `"konsole", "Konsole"`

#### 3.2 Process Tree Analysis

**Most Reliable Cross-Terminal Method**:
```bash
# Get parent process ID (terminal) vs current process
ppid=$PPID
active_pid=$(xdotool getactivewindow getwindowpid 2>/dev/null || echo "")

if [ "$active_pid" = "$PPID" ]; then
    echo "Terminal window is active"
fi
```

**Process Hierarchy Traversal**:
```bash
# Traverse process tree to find terminal
ppid=$PPID
while [ "$ppid" != "1" ]; do
    cmd=$(ps -p $ppid -o comm=)
    case "$cmd" in
        alacritty|kitty|konsole|gnome-terminal|xterm|foot|wezterm)
            echo "Terminal: $cmd"
            break
            ;;
    esac
    ppid=$(ps -p $ppid -o ppid= | tr -d ' ')
done
```

#### 3.3 Environment Variable Detection

**$WINDOWID Variable**:
- **Works**: xterm, konsole
- **Broken**: VTE-based terminals (incorrect value)
- **Missing**: terminology (not set)
- **Reliability**: Low, not recommended

### 4. Electron Application Detection

#### 4.1 Native Wayland vs XWayland Detection

**Visual Detection Methods**:
- `xeyes` - Eyes follow cursor on XWayland only
- `xlsclients` - Lists XWayland applications only
- `xwininfo` - Crosshair appears over XWayland windows

**Programmatic Detection in Hyprland**:
```bash
hyprctl clients -j | jq '.[] | select(.xwayland == true)'
```

#### 4.2 Electron Wayland Support

**Native Wayland Flags**:
```bash
# Modern Electron (v28+)
export ELECTRON_OZONE_PLATFORM_HINT=wayland
/path/to/electron-app --enable-features=UseOzonePlatform --ozone-platform=wayland
```

**Common Electron Applications**:
- VS Code, Windsurf, Cursor
- Discord, Slack, Teams
- Obsidian, Signal
- Many modern development tools

**Electron WM_CLASS Patterns**:
- Often generic: `"electron", "Electron"`
- Sometimes branded: `"code", "Code"` (VS Code)
- Variable between applications

### 5. Focus Change Monitoring Tools

#### 5.1 Hyprland IPC System

**Socket-Based Event Monitoring**:
```bash
# Real-time focus events
socat -U - UNIX-CONNECT:$XDG_RUNTIME_DIR/hypr/$HYPRLAND_INSTANCE_SIGNATURE/.socket2.sock
```

**Key Events**:
- `activewindow>>WINDOWCLASS,WINDOWTITLE` - Active window changed
- `focusedmon>>MONNAME,WORKSPACENAME` - Monitor focus changed
- `openwindow>>WINDOWADDRESS,WORKSPACENAME,WINDOWCLASS,WINDOWTITLE`

#### 5.2 Python Libraries

**Hyprpy** - Python Bindings:
```python
from hyprpy import Hyprland

instance = Hyprland()
window = instance.get_active_window()
print(window.wm_class, window.title)

def on_window_changed(sender, **kwargs):
    print(f"Focused: {kwargs.get('window_class')}")

instance.signals.activewindow.connect(on_window_changed)
instance.watch()
```

**Alternative Implementations**:
- **Pyland** - Python with systemd integration
- **Rust**: hyprland-rs crate for comprehensive bindings
- **Shell**: hyprevents for bash-based event handling

### 6. APIs and Command-Line Tools Summary

#### 6.1 Available Tools (Current System)

**✅ Installed**:
- `hyprctl` - Hyprland control utility
- `xprop` - X11 property display (XWayland only)
- `xdotool` - X11 automation tool (XWayland only)

**❌ Missing**:
- `wmctrl` - Window manager control
- `xwininfo` - X11 window information

#### 6.2 Recommended Tools for Installation

```bash
# Essential window management tools
sudo pacman -S wmctrl xwininfo

# Python Hyprland bindings
pip install hyprpy

# Wayland automation tools
sudo pacman -S wtype ydotool
```

#### 6.3 Tool Capabilities Matrix

| Tool | Wayland Native | XWayland | Active Window | Window Class | PID Detection |
|------|----------------|----------|---------------|---------------|---------------|
| hyprctl | ✅ | ✅ | ✅ | ✅ | ✅ |
| xprop | ❌ | ✅ | ❌ | ✅ | ✅ |
| xdotool | ❌ | ✅ | ✅ | ✅ | ✅ |
| wmctrl | ❌ | ✅ | ✅ | ✅ | ✅ |
| wtype | ✅ | ✅ | ❌ | ❌ | ❌ |

## Recommendations

### 1. Enhanced Detection Algorithm

**Multi-Method Approach**:
```python
async def detect_application_type(self, window_info):
    """Comprehensive application type detection"""

    # Method 1: Direct class matching (existing)
    if self._is_terminal_class(window_info['class']):
        return 'terminal'
    elif self._is_electron_class(window_info['class']):
        return 'electron'

    # Method 2: Process tree analysis
    if self._is_terminal_by_process_tree(window_info['pid']):
        return 'terminal'

    # Method 3: XWayland detection
    if window_info.get('xwayland', False):
        x11_props = await self._get_x11_properties(window_info['address'])
        if self._is_terminal_x11(x11_props):
            return 'terminal'

    return 'gui'
```

### 2. Real-Time Focus Monitoring

**Implement Hyprland IPC Events**:
```python
import socket
import asyncio

async def monitor_focus_changes(self):
    """Real-time focus change monitoring using Hyprland IPC"""

    socket_path = f"/tmp/hypr/{os.getenv('HYPRLAND_INSTANCE_SIGNATURE')}/.socket2.sock"

    while True:
        try:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect(socket_path)
                while True:
                    line = sock.recv(1024).decode('utf-8').strip()
                    if line.startswith('activewindow>>'):
                        await self.update_active_window()
        except Exception as e:
            logger.error(f"Focus monitoring error: {e}")
            await asyncio.sleep(1)
```

### 3. Terminal Detection Enhancements

**Process-Based Detection**:
```python
def _is_terminal_by_process_tree(self, pid):
    """Detect terminal by analyzing process tree"""
    try:
        # Get process command line
        result = subprocess.run(['ps', '-p', str(pid), '-o', 'comm='],
                              capture_output=True, text=True)
        process_name = result.stdout.strip()

        # Direct terminal detection
        terminals = {'alacritty', 'kitty', 'foot', 'wezterm',
                    'gnome-terminal-', 'konsole', 'xterm'}
        if any(term in process_name for term in terminals):
            return True

        # Check parent process
        parent_result = subprocess.run(['ps', '-o', 'ppid=', '-p', str(pid)],
                                    capture_output=True, text=True)
        ppid = parent_result.stdout.strip()
        if ppid and ppid.isdigit():
            return self._is_terminal_by_process_tree(int(ppid))

    except Exception as e:
        logger.debug(f"Process tree detection failed: {e}")

    return False
```

### 4. Configuration Improvements

**Dynamic Terminal Configuration**:
```yaml
# config/terminal_detection.yaml
terminal_patterns:
  wm_class:
    - "kitty"
    - "Alacritty"
    - "foot"
    - "wezterm"
    - "gnome-terminal"
    - "konsole"

  process_names:
    - "alacritty"
    - "kitty"
    - "foot-client"
    - "wezterm"
    - "gnome-terminal"
    - "konsole"

  parent_processes:
    - "alacritty"
    - "kitty"
    - "foot"
    - "wezterm-gui"

electron_patterns:
  wm_class:
    - "electron"
    - "code"        # VS Code
    - "windsurf"
    - "cursor"
    - "discord"
    - "slack"
```

## Implementation Priority

### High Priority (Immediate)
1. **Enhanced process tree detection** - Most reliable across terminals
2. **Hyprland IPC focus monitoring** - Real-time updates without polling
3. **Dynamic configuration system** - Easy addition of new terminals

### Medium Priority (Next Sprint)
1. **XWayland fallback detection** - Handle mixed environments
2. **Electron native Wayland detection** - Future-proofing
3. **Performance optimization** - Reduce system calls

### Low Priority (Future)
1. **Machine learning classification** - Pattern-based detection
2. **User preference learning** - Adapt to user habits
3. **Cross-platform compatibility** - Beyond Hyprland

## Security Considerations

- **Wayland isolation**: Native Wayland prevents cross-app window inspection
- **Privilege escalation**: Some detection methods may require elevated permissions
- **Privacy implications**: Window monitoring should be transparent to users

## Conclusion

This research provides a comprehensive foundation for implementing robust terminal vs GUI application detection in Hypr-Voice. The recommended multi-method approach combining window class analysis, process tree inspection, and real-time IPC monitoring will significantly improve detection accuracy and user experience across diverse application environments.

The key insight is that no single detection method is universally reliable - the most effective solution combines multiple approaches with appropriate fallbacks for different window managers, display protocols, and application types.

---

**Report Generated**: October 25, 2025
**Environment**: Arch Linux with Hyprland (Wayland)
**Research Methods**: Perplexity AI search, system testing, code analysis