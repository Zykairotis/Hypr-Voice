# Zed Editor Research Summary - Quick Reference

## Key Findings

### Window Class Information
- **Primary Class**: `dev.zed.Zed`
- **Wayland App ID**: `dev.zed.Zed`
- **Desktop File**: `dev.zed.Zed.desktop`
- **Executable**: `zeditor` (Arch) or `zed` (other)

### Terminal vs Editor Detection

**Challenge**: Zed uses same window class for both contexts

**Solution**: Window title pattern matching

#### Editor Context Patterns
```
^(.+) — (.+)$    # filename — project format
\.[a-z]+$        # File extensions
^[^@]*$          # No @ symbol (not terminal)
```

#### Terminal Context Patterns
```
^.*@.*:.*$       # user@host:path format
^Terminal        # Generic terminal
^(bash|zsh|fish) # Shell names
.*\$(            # Shell prompt
^~\$(            # Home directory prompt
```

## Implementation Files Created

1. **Research Report**: `/docs/research/zed_editor_window_title_research.md`
   - Comprehensive technical analysis
   - Detection algorithms
   - Implementation strategies

2. **Profile Updates**: `/config/zed_profiles_update.json`
   - Zed-specific clipboard profiles
   - Detection patterns
   - Configuration examples

3. **Detection Script**: `/scripts/detect_zed_context.sh`
   - Real-time context monitoring
   - Pattern testing
   - Integration helper

4. **Updated Clipboard Manager**: `/src/clipboard_manager.py`
   - Added Zed profiles
   - Context-aware paste methods

## Usage Examples

### Command Line Detection
```bash
# Detect current Zed context
./scripts/detect_zed_context.sh

# Monitor focus changes
./scripts/detect_zed_context.sh monitor

# Test patterns
./scripts/detect_zed_context.sh test
```

### Clipboard Manager Integration
```python
# Zed profiles automatically detect context:
# - Editor context: Ctrl+V paste
# - Terminal context: Ctrl+Shift+V paste
```

### Hyprland Rules
```bash
# Zed-specific window rules
windowrulev2 = workspace 2, class:^(dev\.zed\.Zed)$
bind = $mainMod, Z, exec, zeditor
```

## Testing Verification

To test the implementation:

1. **Open Zed Editor**
2. **Test detection script**:
   ```bash
   ./scripts/detect_zed_context.sh
   ```
3. **Switch between editor and terminal**
4. **Monitor real-time changes**:
   ```bash
   ./scripts/detect_zed_context.sh monitor
   ```

## Special Considerations

- **Shell Configuration**: Terminal titles depend on `PROMPT_COMMAND` setup
- **Title Reliability**: Some users may have custom title formats
- **Performance**: Real-time monitoring uses 0.5s intervals
- **Fallbacks**: Unknown context tries both editor and terminal methods

## Next Steps

1. **Test with different shell configurations**
2. **Verify with various file types**
3. **Performance testing in real usage**
4. **User feedback collection**

---

*Research completed: October 25, 2025*