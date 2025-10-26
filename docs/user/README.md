# 👥 User Documentation

Comprehensive guides for using Hypr-Voice's features and capabilities.

## 📚 User Guides

### 🎤 Core Features
- **[Audio Configuration Guide](audio-configuration-guide.md)** - Microphone setup and audio settings
- **[Enhanced Mode Guide](enhanced-mode-guide.md)** - Understanding Raw (F9) vs Enhanced (F10) modes
- **[Web UI Guide](web-ui-guide.md)** - Using the web management interface
- **[Universal Clipboard Guide](universal-clipboard-guide.md)** - Cross-application paste support

### 🔧 Feature Documentation
- **[Audio Level Visualization](features/audio-level-visualization.md)** - Real-time audio feedback
- **[Paste Fix](features/paste-fix.md)** - Universal paste support for all apps
- **[Paste Troubleshooting](features/paste-troubleshooting.md)** - Solving paste-specific issues

### 📖 Detailed Guides
- **[Setup Guide](guides/setup-guide.md)** - Comprehensive configuration reference
- **[Quick Test Guide](guides/quick-test-guide.md)** - Testing system functionality
- **[Complete Fix Guide](guides/complete-fix-guide.md)** - Comprehensive troubleshooting

## 🎯 Key Concepts

### 🎹 Mode Selection
- **F9 (Raw Mode)**: Fast, instant transcription without AI processing
- **F10 (Enhanced Mode)**: Smart, context-aware processing with corrections
- **Super+F9**: Show raw mode status
- **Super+F10**: Show enhanced mode status

### 🔗 Application Support
- **Terminals**: Auto-detection for Ctrl+Shift+V vs Ctrl+V
- **Electron Apps**: Special handling for VS Code, Windsurf, Discord
- **Web Browsers**: Optimized paste behavior and text improvement
- **Code Editors**: Enhanced terminology correction for technical content

### 🎤 Audio Features
- **Device Detection**: Automatic USB/Bluetooth microphone setup
- **Level Monitoring**: Real-time audio visualization
- **Quality Settings**: 48kHz recording optimized for Whisper
- **Troubleshooting**: Common audio issues and solutions

## 🚀 Quick Reference

### Daily Usage
```bash
# Start voice input
# Hold SUPER+Grave, speak, release

# Switch modes
F9  - Raw mode (fast)
F10 - Enhanced mode (smart)

# Check status
Super+F9  - Raw mode status
Super+F10 - Enhanced mode status

# Web interface
# Open http://localhost:8080
```

### Configuration
```bash
# Audio settings
# Web UI: Audio Configuration tab
# Config: config/audio_config.yaml

# Application profiles
# Web UI: Applications tab
# Config: config/app_profiles.yaml

# Enhanced mode settings
# Web UI: LLM Providers tab
# Config: config/llm_providers.yaml
```

## 🔗 Related Documentation

- **[Installation](../installation/)** - Getting started setup
- **[Technical](../technical/)** - System architecture and internals
- **[Troubleshooting](../troubleshooting/)** - Common issues and solutions

## 💡 Tips & Best Practices

### 🎤 Audio Quality
- Use a quality USB microphone for best results
- Speak clearly and at moderate pace
- Minimize background noise
- Test with different audio settings

### ⚡ Performance
- Use Raw mode (F9) for speed-critical tasks
- Use Enhanced mode (F10) for accuracy-critical work
- Close unused applications when using Enhanced mode
- Monitor audio levels for optimal input

### 🔗 Application Compatibility
- Check the application profiles for your favorite apps
- Create custom profiles for unsupported applications
- Use the universal clipboard for problematic apps
- Test different paste methods for best results