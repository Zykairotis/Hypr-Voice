# Project Rename: whisper → Hypr-Whisper

## Summary
Successfully renamed the project directory from `src/whisper` to `src/Hypr-Whisper`

## Date
October 29, 2025 at 4:24am UTC-04:00

## Changes Made

### 1. Directory Renamed
- **Old**: `/home/mewtwo/Zykairotis/Hypr-Voice/src/whisper`
- **New**: `/home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper`

### 2. Files Updated

#### Shell Scripts
- `src/Hypr-Whisper/scripts/*.sh` - All path references updated
- `src/Hypr-Whisper/config/hyprvoice.conf` - Hyprland keybind paths updated

#### Documentation
- `docs/*.md` - Path references updated
- `src/Hypr-Whisper/docs/*.md` - Path references updated

### 3. Verified Working
✅ Python imports (hybrid_server, vocabulary_manager, hybrid_client)
✅ Vocabulary system initialization
✅ Startup scripts
✅ Configuration files
✅ Keybind configuration

## Usage

### Start Server
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
./scripts/start_hybrid_server.sh start
```

### PTT System
```bash
# Hold F9 to record, release to transcribe
# Configured in config/hyprvoice.conf
```

### Add Vocabulary Words
```bash
cd /home/mewtwo/Zykairotis/Hypr-Voice/src/Hypr-Whisper
./add_vocabulary.py
```

## Structure

```
Hypr-Voice/
├── src/
│   └── Hypr-Whisper/          # ← Renamed from "whisper"
│       ├── hybrid_server.py   # Server with vocabulary
│       ├── vocabulary_manager.py
│       ├── config/
│       │   ├── vocabulary.yaml
│       │   └── vocabularies/
│       ├── scripts/
│       │   ├── start_hybrid_server.sh
│       │   └── hypr-voice-record.sh
│       └── docs/
└── .venv/                     # Unchanged
```

## What Stayed the Same
- Virtual environment path: `/home/mewtwo/Zykairotis/Hypr-Voice/.venv`
- Project root: `/home/mewtwo/Zykairotis/Hypr-Voice`
- All functionality intact
- Vocabulary system configuration
- PTT integration

## Migration Notes
No migration needed for users - all paths have been automatically updated in configuration files.
