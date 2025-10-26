# Zed Editor Window Title Behavior and Terminal Integration Research Report

## Executive Summary

This research report provides comprehensive findings about Zed Editor's window title behavior, window class identification, and terminal integration patterns specifically for keymapper detection and context switching in Hyprland environments. The research covers Zed's unique terminal implementation, window title dynamics, and practical detection patterns for automation tools.

## Research Findings

### 1. Zed Editor Window Class and Identification

**Primary Window Class**: `dev.zed.Zed`
- **Wayland App ID**: `dev.zed.Zed`
- **X11 Resource Class**: `dev.zed.Zed` (identical to Wayland)
- **Desktop File**: `dev.zed.Zed.desktop`
- **Executable**: `zeditor` (Arch Linux) or `zed` (other distributions)

**Hyprland Detection Examples**:
```bash
# Get active window info
hyprctl activewindow -j

# Sample output for Zed
{
  "class": "dev.zed.Zed",
  "title": "settings.nix — nixcfg",
  "initialClass": "dev.zed.Zed",
  "initialTitle": "nixcfg",
  "pid": 1479692,
  "xwayland": 0,
  "floating": 0,
  "workspace": {"id": 2, "name": "code"}
}
```

**Window Rule Examples for Hyprland**:
```bash
# Open Zed in specific workspace
windowrulev2 = workspace 2, class:^(dev.zed.Zed)$

# Float Zed window
windowrulev2 = float, class:^(dev.zed.Zed)$

# Keybinding for launching
bind = $mainMod, Z, exec, zeditor
```

### 2. Zed's Terminal Panel Architecture

**Terminal Integration Type**: Native embedded terminal
- **Implementation**: Integrated terminal panel (not external process)
- **Dock Positions**: Left, right, or bottom of editor window
- **Context Switching**: Internal focus management between editor and terminal panes
- **Window Class**: Always `dev.zed.Zed` (no separate window class for terminal)

**Terminal Configuration**:
```json
{
  "terminal": {
    "dock": "bottom",
    "button": true,
    "default_width": 640,
    "default_height": 320,
    "blinking": "terminal_controlled",
    "cursor_shape": "block",
    "env": {},
    "scrollbar": {"show": null},
    "font_family": "Fira Code",
    "font_size": 15,
    "font_weight": 400,
    "line_height": "comfortable",
    "max_scroll_history_lines": 10000,
    "toolbar": {
      "breadcrumbs": true
    }
  }
}
```

### 3. Window Title Dynamics and Pattern Analysis

**Title Format Pattern**: `{filename} — {project_name}`
- **Base Title**: Shows current file and project
- **Terminal Context**: Terminal pane can emit titles via OSC escape sequences
- **Dynamic Updates**: Title changes when switching files or terminal updates

**Terminal Title Detection**:
- **Mechanism**: OSC escape sequences (`\033]0;Title\007` or `\e]2;Title\007`)
- **Shell Integration**: Uses `PROMPT_COMMAND` (Bash) or `precmd` (Zsh)
- **Terminal Toolbar**: Shows terminal title when `terminal.toolbar.breadcrumbs: true`

**Shell Configuration Examples**:
```bash
# Bash - add to ~/.bashrc
PROMPT_COMMAND="echo -ne \"\033]0;${PWD/#$HOME/~}\007\""

# Zsh - add to ~/.zshrc
precmd () {echo -ne "\033]0;${PWD/#$HOME/~}\007"}

# Manual title setting
echo -e "\e]2;Custom Title\007"
```

### 4. Keymapper Detection Patterns

**Challenge**: Zed uses the same window class (`dev.zed.Zed`) for both editor and terminal contexts, making traditional window class detection insufficient for context switching.

**Detection Strategies**:

#### 4.1 Window Title Pattern Matching
```regex
# Editor context patterns
^(.+) — (.+)$           # File editing: filename — project
^[^—]+$                  # Single file without project name

# Terminal context patterns
^.*@.*:~$               # User@hostname:directory
^.*@.*:/.+              # User@hostname:/full/path
^Terminal               # Generic terminal title
^bash — .+              # Shell with project context
^zsh — .+               # Zsh with project context
```

#### 4.2 Focus Detection Methods
```python
# Method 1: Monitor title changes for terminal patterns
def is_terminal_active(title):
    terminal_patterns = [
        r'^.*@.*:.*$',      # user@host:path
        r'^.*\$',           # shell prompt
        r'^Terminal',       # generic terminal
        r'^bash|^zsh|^fish' # shell names
    ]
    return any(re.search(pattern, title) for pattern in terminal_patterns)

# Method 2: Hyprland IPC event monitoring
def monitor_zed_focus():
    # Monitor activewindow events
    # Check if class == "dev.zed.Zed"
    # Analyze title for context
    pass
```

#### 4.3 Enhanced Profile Configuration
```json
{
  "name": "Zed Editor",
  "class_pattern": "(dev\\.zed\\.Zed)",
  "window_title_pattern": "^(.+) — (.+)$",
  "app_type": "ide",
  "primary_method": "ctrl+v",
  "fallback_methods": ["middle_click", "wtype"],
  "delay_before": 0.1,
  "delay_after": 0.05,
  "notes": "Zed Editor main context - standard paste behavior"
},
{
  "name": "Zed Terminal Panel",
  "class_pattern": "(dev\\.zed\\.Zed)",
  "window_title_pattern": "^(.*@.*:.+|Terminal|bash.*|zsh.*)$",
  "app_type": "terminal",
  "primary_method": "ctrl+shift+v",
  "fallback_methods": ["middle_click", "direct_type"],
  "delay_before": 0.15,
  "delay_after": 0.05,
  "notes": "Zed's embedded terminal - uses terminal paste shortcuts"
}
```

### 5. Practical Implementation for Keymapper

#### 5.1 Detection Algorithm
```python
def detect_zed_context(window_class, window_title):
    """Detect Zed editor vs terminal context"""

    if window_class.lower() != "dev.zed.zed":
        return None  # Not Zed

    # Terminal context detection
    terminal_indicators = [
        "@" in title and ":" in title,  # user@host:path format
        title.startswith(("bash", "zsh", "fish", "Terminal")),
        re.search(r'^[^—]*\$', title),    # Shell prompt pattern
        re.search(r'~\$|^/.*\$', title)   # Directory prompt
    ]

    if any(terminal_indicators):
        return "terminal"

    # Editor context detection
    editor_indicators = [
        " — " in title,                   # filename — project format
        "." in title and not "@" in title, # filename with extension
        not any(terminal_indicators)      # Not terminal
    ]

    if any(editor_indicators):
        return "editor"

    return "unknown"  # Fallback
```

#### 5.2 Hyprland Integration Script
```bash
#!/bin/bash
# Zed context detection for Hyprland keymapper

detect_zed_context() {
    local window_info=$(hyprctl activewindow -j)
    local class=$(echo "$window_info" | jq -r '.class')
    local title=$(echo "$window_info" | jq -r '.title')

    if [[ "$class" != "dev.zed.Zed" ]]; then
        echo "other"
        return
    fi

    # Terminal context detection
    if [[ "$title" =~ ^.*@.*:.*$ ]] || \
       [[ "$title" =~ ^(bash|zsh|fish|Terminal) ]] || \
       [[ "$title" =~ \$ ]]; then
        echo "terminal"
        return
    fi

    # Editor context
    if [[ "$title" =~ " — " ]] || [[ "$title" =~ \..*$ ]]; then
        echo "editor"
        return
    fi

    echo "unknown"
}

# Usage example
CONTEXT=$(detect_zed_context)
echo "Current Zed context: $CONTEXT"
```

### 6. Keybinding Recommendations

#### 6.1 Hyprland Keybind Configuration
```bash
# Zed-specific keybindings using title matching
bind = $mainMod, V, pass, class:^(dev\.zed\.Zed)$, title:^(.+) — (.+)$  # Editor context
bind = $mainMod SHIFT, V, pass, class:^(dev\.zed\.Zed)$, title:^(.*@.*:.+)$  # Terminal context

# Alternative: Use submaps for context switching
bind = $mainMod, Z, submap, zed_editor
submap = zed_editor
    bind = , escape, submap, reset
    bind = $mainMod, V, exec, [clipboard_manager --method ctrl+v --app zed_editor]
submap = reset
```

#### 6.2 Universal Clipboard Manager Integration
```python
# Enhanced profile for Zed in clipboard_manager.py
ApplicationProfile(
    name="Zed Editor (Editor Context)",
    class_pattern=r"(dev\.zed\.Zed)",
    window_title_pattern=r"^(.+) — (.+)$",
    app_type=ApplicationType.IDE,
    primary_method=PasteMethod.CTRL_V,
    fallback_methods=[PasteMethod.MIDDLE_CLICK, PasteMethod.WTYPE],
    delay_before=0.1,
    delay_after=0.05,
    notes="Zed editor context - standard paste behavior"
),

ApplicationProfile(
    name="Zed Editor (Terminal Context)",
    class_pattern=r"(dev\.zed\.Zed)",
    window_title_pattern=r"^(.*@.*:.+|Terminal|bash.*|zsh.*)$",
    app_type=ApplicationType.TERMINAL,
    primary_method=PasteMethod.CTRL_SHIFT_V,
    fallback_methods=[PasteMethod.MIDDLE_CLICK, PasteMethod.DIRECT_TYPE],
    delay_before=0.15,
    delay_after=0.05,
    notes="Zed's embedded terminal - uses terminal paste shortcuts"
)
```

### 7. Special Considerations and Limitations

#### 7.1 Detection Challenges
- **Same Window Class**: Both editor and terminal use `dev.zed.Zed`
- **Title Dependency**: Detection relies heavily on title patterns
- **Custom Shells**: Users with custom shell configurations may have different title patterns
- **Empty Titles**: Terminal might not emit titles if `PROMPT_COMMAND` not configured

#### 7.2 Performance Considerations
- **Real-time Monitoring**: Title change monitoring requires continuous checking
- **Hyprland IPC Overhead**: Frequent `hyprctl activewindow` calls
- **Regex Performance**: Complex title patterns can impact detection speed

#### 7.3 Edge Cases
- **No Terminal Title**: If terminal doesn't emit titles, falls back to generic detection
- **Custom Title Formats**: Users may customize title formats
- **Multiple Terminal Instances**: Distinguishing between multiple terminal panes

### 8. Recommended Implementation Strategy

#### 8.1 Primary Detection Method
1. **Window Class Filter**: Check for `dev.zed.Zed`
2. **Title Pattern Analysis**: Use regex patterns to distinguish contexts
3. **Fallback to Default**: If patterns don't match, assume editor context

#### 8.2 Configuration Updates
Add Zed-specific profiles to clipboard configuration:
```json
{
  "name": "Zed Editor - Context Aware",
  "class_pattern": "(dev\\.zed\\.Zed)",
  "window_title_pattern": "^(.+)$",
  "app_type": "ide",
  "primary_method": "context_aware",
  "fallback_methods": ["ctrl+v", "ctrl+shift+v"],
  "context_detection": {
    "terminal_patterns": ["@.*:.*", "^Terminal", "bash|zsh|fish"],
    "editor_patterns": [" — ", "\\.[a-z]+$"]
  }
}
```

#### 8.3 Testing and Validation
1. **Test Environment**: Verify with various file types and terminal states
2. **Pattern Validation**: Test title patterns against user's shell configuration
3. **Performance Testing**: Ensure real-time detection doesn't impact system performance

## Conclusion

Zed Editor presents unique challenges for keymapper detection due to its integrated terminal architecture. The key findings are:

1. **Single Window Class**: Both editor and terminal contexts use `dev.zed.Zed`
2. **Title-Based Detection**: Window title patterns are the primary method for context detection
3. **Terminal Title Integration**: Zed's terminal can emit titles via standard OSC escape sequences
4. **Context Switching**: Internal focus management doesn't change window class, only title

The recommended approach combines window class filtering with sophisticated title pattern matching to distinguish between editor and terminal contexts. This provides reliable detection while maintaining flexibility for different user configurations and shell setups.

---

**Report Generated**: October 25, 2025
**Research Methods**: Perplexity AI search, system testing, code analysis, documentation review
**Target Environment**: Hyprland (Wayland) with Zed Editor
**Focus Area**: Keymapper detection and context switching automation