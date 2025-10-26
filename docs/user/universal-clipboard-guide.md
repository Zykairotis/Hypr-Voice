# Universal Clipboard System for Hypr-Voice

A comprehensive, intelligent clipboard management system that automatically detects applications and adapts paste methods for optimal compatibility across terminals, Electron apps, code editors, and more.

## 🚀 Overview

The Universal Clipboard System solves the common problem of inconsistent paste behavior across different applications on Wayland/Hyprland. It provides:

- **Automatic Application Detection**: Identifies the current active application
- **Adaptive Paste Methods**: Chooses the best paste method for each application type
- **Content Validation & Sanitization**: Ensures safe and clean clipboard content
- **Voice-to-Text Integration**: Seamless integration with voice transcription workflows
- **Fallback Mechanisms**: Multiple backup methods for reliability
- **Comprehensive Testing**: Built-in test suite for validation

## 📋 Features

### Core Functionality
- ✅ Application detection via Hyprland
- ✅ Intelligent paste method selection
- ✅ Multiple paste methods (Ctrl+V, Ctrl+Shift+V, ydotool, direct typing, etc.)
- ✅ Content validation and sanitization
- ✅ Automatic text corrections
- ✅ Unicode and special character support
- ✅ Configuration profiles for different applications

### Integration Features
- ✅ Voice-to-text workflow integration
- ✅ Session management
- ✅ Statistics tracking
- ✅ Custom correction rules
- ✅ Callback system for events
- ✅ Error handling and retry logic

### Paste Methods Supported
1. **Ctrl+V** - Standard paste for most applications
2. **Ctrl+Shift+V** - Terminal paste method
3. **ydotool** - Hardware-level key injection
4. **wtype** - Wayland-native typing
5. **Direct Typing** - Character-by-character input
6. **Middle Click** - Primary selection paste
7. **Custom Commands** - User-defined paste actions

## 🛠️ Installation

### Prerequisites

#### Required Tools
```bash
# Core Wayland clipboard tools
sudo pacman -S wl-clipboard wtype

# Hyprland (for application detection)
# Already installed if using Hyprland
```

#### Optional Tools
```bash
# Enhanced Electron app support
sudo pacman -S ydotool

# Setup ydotool service
sudo systemctl enable --now ydotool
# Or add to hyprland.conf: exec-once = ydotoold
```

### Install Universal Clipboard System

1. **Clone or download the files** to your Hypr-Voice directory
2. **Make scripts executable**:
   ```bash
   chmod +x hypr-voice/src/*.py
   chmod +x hypr-voice/scripts/*.py
   ```

3. **Install Python dependencies**:
   ```bash
   pip install --user -r requirements.txt  # If available
   ```

## 🔧 Configuration

### Application Profiles

The system uses JSON configuration files to define how different applications should be handled:

- **Configuration File**: `hypr-voice/config/clipboard_profiles.json`
- **Validation Rules**: `hypr-voice/config/clipboard_validation.json`

#### Adding Custom Application Profiles

Edit `clipboard_profiles.json` to add support for specific applications:

```json
{
  "name": "My Custom App",
  "class_pattern": "(myapp|custom_app)",
  "window_title_pattern": ".*",
  "app_type": "editor",
  "primary_method": "ctrl+v",
  "fallback_methods": ["middle_click", "direct_type"],
  "delay_before": 0.1,
  "delay_after": 0.05,
  "notes": "Custom application settings"
}
```

#### Validation Levels

Configure content validation strictness:

- **minimal**: Basic safety checks only
- **standard**: Normal validation and sanitization (default)
- **strict**: Maximum security and validation

## 🎤 Voice Integration

### Transcription Modes

1. **Raw Mode**: Direct paste without processing
2. **Validated Mode**: Content validation before paste
3. **Enhanced Mode**: LLM enhancement (if available)
4. **Interactive Mode**: Show options to user
5. **Auto-Correct Mode**: Apply intelligent corrections

### Automatic Corrections

The system includes automatic text corrections:

- Capitalization fixes
- Spacing normalization
- Filler word removal
- Punctuation improvements
- Command formatting

#### Custom Correction Rules

Add custom corrections in `voice_corrections.json`:

```json
{
  "name": "custom_rule",
  "pattern": "\\b(myword)\\b",
  "replacement": "MyWord",
  "description": "Custom word replacement",
  "priority": 1,
  "content_types": ["dictation", "message"]
}
```

## 🧪 Testing

### Run the Test Suite

```bash
# Run comprehensive tests
python hypr-voice/src/clipboard_test_suite.py

# Run specific tests
python hypr-voice/src/clipboard_test_suite.py --filter terminal

# Interactive testing
python hypr-voice/src/clipboard_test_suite.py --interactive

# Dry run (no actual paste operations)
python hypr-voice/src/clipboard_test_suite.py --dry-run
```

### Run the Demo

```bash
# Full demonstration
python hypr-voice/scripts/universal_clipboard_demo.py

# Skip system checks
python hypr-voice/scripts/universal_clipboard_demo.py --skip-checks

# Run specific demo
python hypr-voice/scripts/universal_clipboard_demo.py --demo interactive
```

## 🔍 Usage Examples

### Basic Usage

```python
from src.clipboard_manager import UniversalClipboardManager

# Initialize manager
manager = UniversalClipboardManager()

# Intelligent paste
result = manager.intelligent_paste("Hello, World!")
print(f"Success: {result.success}, Method: {result.method_used.value}")
```

### Voice Integration

```python
from src.voice_clipboard_integration import VoiceClipboardIntegration, TranscriptionMode

# Initialize integration
integration = VoiceClipboardIntegration()

# Create voice session
session = integration.create_session(mode=TranscriptionMode.VALIDATED)

# Process transcription
result = await integration.process_transcription(
    session.session_id,
    "Hello world",
    confidence=0.95
)
```

### Content Validation

```python
from src.clipboard_validator import ClipboardValidator, ValidationLevel

# Initialize validator
validator = ClipboardValidator()

# Validate content
result = validator.validate_and_sanitize("Hello &amp; world", ValidationLevel.STANDARD)
print(f"Valid: {result.is_valid}, Processed: {result.processed_content}")
```

## 🎯 Application Support

### Supported Application Types

| Type | Examples | Primary Method | Fallbacks |
|------|----------|----------------|-----------|
| **Terminal** | kitty, alacritty, foot | Ctrl+Shift+V | Middle Click, Direct Type |
| **Electron** | Discord, Slack, VSCode | ydotool | wtype, Direct Type |
| **IDE** | VSCode, Vim, Emacs | Ctrl+V | Middle Click, wtype |
| **Browser** | Firefox, Chrome | Ctrl+V | Middle Click, Shift+Insert |
| **Editor** | Gedit, Mousepad | Ctrl+V | Middle Click, Shift+Insert |
| **Remote** | Remmina, VNC | Ctrl+V | Ctrl+Shift+V |
| **System** | Default applications | Ctrl+V | Middle Click, wtype |

### Adding New Applications

1. **Detect the application class**:
   ```bash
   hyprctl activewindow -j | jq '.class'
   ```

2. **Add profile** to `clipboard_profiles.json`:
   ```json
   {
     "name": "New Application",
     "class_pattern": "newapp",
     "primary_method": "ctrl+v",
     "fallback_methods": ["wtype"]
   }
   ```

3. **Test the configuration**:
   ```bash
   python -c "
   from src.clipboard_manager import UniversalClipboardManager
   manager = UniversalClipboardManager()
   result = manager.intelligent_paste('Test')
   print(result.method_used.value)
   "
   ```

## 🐛 Troubleshooting

### Common Issues

#### ydotool Permission Issues
```bash
# Fix ydotool permissions
./hypr-voice/scripts/fix_ydotool.sh

# Or setup manually
sudo usermod -aG input $USER
# Log out and back in
```

#### Clipboard Not Working
```bash
# Check clipboard tools
wl-copy "test"
wl-paste  # Should show "test"

# Check Wayland session
echo $XDG_SESSION_TYPE  # Should be "wayland"
```

#### Application Detection Issues
```bash
# Check Hyprland IPC
hyprctl activewindow -j

# Test application detection
python -c "
from src.clipboard_manager import UniversalClipboardManager
manager = UniversalClipboardManager()
print(manager.detect_active_application())
"
```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Issues

- **Large text**: Use direct typing method for very large content
- **Electron apps**: Prefer ydotool over wtype for better reliability
- **Terminals**: Use Ctrl+Shift+V to avoid shell interpretation

## 📊 Statistics and Monitoring

### View Usage Statistics

```python
from src.voice_clipboard_integration import VoiceClipboardIntegration

integration = VoiceClipboardIntegration()
stats = integration.get_statistics()
print(stats)
```

### Session Management

```python
# View active sessions
print(integration.active_sessions)

# Cleanup old sessions
integration.cleanup_sessions(max_age_hours=24)
```

## 🔧 Advanced Configuration

### Custom Paste Methods

Create custom paste commands:

```json
{
  "name": "Custom Browser Paste",
  "class_pattern": "(firefox|chrome)",
  "custom_command": "xdotool key ctrl+v && notify-send 'Pasted in browser'",
  "primary_method": "custom"
}
```

### Environment Variables

```bash
# Validation level
export CLIPBOARD_VALIDATION_LEVEL=strict

# Default paste method
export CLIPBOARD_DEFAULT_METHOD=ydotool

# Debug mode
export CLIPBOARD_DEBUG=true
```

## 🤝 Integration with Hypr-Voice

### Hypr-Voice Integration

The universal clipboard system integrates seamlessly with the existing Hypr-Voice workflow:

1. **Voice Recording** → Transcription
2. **Content Validation** → Sanitization
3. **Application Detection** → Method Selection
4. **Intelligent Pasting** → Success/Fallback

### Example Integration

```python
# In hypr_voice.py, replace the paste_to_cursor method:

async def process_transcription(self, text: str):
    # Create voice session
    integration = VoiceClipboardIntegration()
    session = integration.create_session()

    # Process with universal clipboard
    result = await integration.process_transcription(session.session_id, text)

    # Handle result
    if result.confidence > 0.8:
        self.notify("Transcription Complete", result.text[:100])
    else:
        self.notify("Low Confidence", f"Confidence: {result.confidence:.1f}")
```

## 📚 API Reference

### UniversalClipboardManager

```python
class UniversalClipboardManager:
    def intelligent_paste(text: str, force_method: Optional[PasteMethod] = None) -> PasteResult
    def detect_active_application() -> Tuple[str, str]
    def get_application_profile(app_class: str, window_title: str) -> ApplicationProfile
    def copy_to_clipboard(text: str) -> bool
    def test_paste_methods(text: str) -> Dict[PasteMethod, bool]
```

### ClipboardValidator

```python
class ClipboardValidator:
    def validate_and_sanitize(content: str, level: ValidationLevel) -> ValidationResult
    def detect_content_type(content: str) -> ContentType
    def set_validation_level(level: ValidationLevel)
    def add_custom_rule(level: str, rule: ValidationRule)
```

### VoiceClipboardIntegration

```python
class VoiceClipboardIntegration:
    def create_session(mode: TranscriptionMode) -> VoiceSession
    def process_transcription(session_id: str, text: str) -> TranscriptionResult
    def apply_corrections(text: str, content_type: ContentType) -> Tuple[str, List[str]]
    def register_callback(event: str, callback: Callable)
    def get_statistics() -> Dict[str, Any]
```

## 🎉 Conclusion

The Universal Clipboard System provides a robust, intelligent solution for clipboard management on Wayland/Hyprland. With automatic application detection, adaptive paste methods, and comprehensive validation, it ensures reliable text input across all your applications.

For more information, testing, or customization, refer to the source code documentation and built-in test suite.

---

**Happy voice typing!** 🎤✨