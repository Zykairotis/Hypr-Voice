# Hypr-Voice Project Documentation

This directory contains organized project documentation moved from the root folder for better structure and maintainability.

## 📁 Documentation Structure

### Core Documentation (`core-docs/`)
Essential project configuration and setup documentation:
- **[CLAUDE.md](core-docs/CLAUDE.md)** - Claude Code SDK configuration and SPARC development environment
- **[CLAUDE_CONTEXT_SEARCH_TEST.md](core-docs/CLAUDE_CONTEXT_SEARCH_TEST.md)** - Context search testing and validation

### Implementation Guides (`implementation-guides/`)
Technical implementation details and summaries:
- **[CONTEXT_MANAGER_COMPLETE_SUMMARY.md](implementation-guides/CONTEXT_MANAGER_COMPLETE_SUMMARY.md)** - Complete context management system overview
- **[CONTEXT_MANAGER_IMPLEMENTATION.md](implementation-guides/CONTEXT_MANAGER_IMPLEMENTATION.md)** - Context manager implementation details

### Integration (`integration/`)
Integration guides and API documentation:
- **[INTEGRATION_GUIDE.md](integration/INTEGRATION_GUIDE.md)** - Complete system integration guide

### TTS Control Panel (`tts-control-panel/`)
Text-to-Speech control panel specific documentation:
- **[TTS_CONTROL_PANEL_IMPLEMENTATION.md](tts-control-panel/TTS_CONTROL_PANEL_IMPLEMENTATION.md)** - TTS control panel implementation

## 🗂️ Project Organization

This documentation was organized and moved from the root directory to improve project structure:

**Before (Root Directory Scattered Files):**
```
Hypr-Voice/
├── CLAUDE.md
├── CONTEXT_MANAGER_*.md
├── INTEGRATION_GUIDE.md
├── TTS_CONTROL_PANEL_IMPLEMENTATION.md
└── test_ws.py
```

**After (Organized Structure):**
```
Hypr-Voice/
├── docs/project/
│   ├── README.md                          # This file
│   ├── core-docs/
│   ├── implementation-guides/
│   ├── integration/
│   └── tts-control-panel/
└── tests/integration/
    └── test_ws.py
```

## 🔗 Related Documentation

- **[Main Project Documentation](../../docs/README.md)** - Primary user documentation
- **[Technical Documentation](../../docs/technical/README.md)** - Technical implementation details
- **[Web UI Documentation](../../web-ui/README.md)** - Web interface documentation
- **[Hypr-Whisper Documentation](../../src/Hypr-Whisper/docs/README.md)** - Core transcription engine

## 📅 Organization Date

**Organized on:** 2025-11-25
**Purpose:** Improve project structure and maintainability by consolidating scattered documentation.