# Wispr Flow Direct Mode

## Overview

Direct mode eliminates the API server overhead by calling the wisper-flow transcription module directly in-process, bypassing the HTTP server on port 9095.

**Status:** ✅ Enabled by default (as of January 2026)

## Performance Comparison

| Metric | API Mode (Legacy) | Direct Mode | Improvement |
|--------|-------------------|-------------|-------------|
| HTTP Overhead | 50-200ms | 0ms | **-50 to -200ms** |
| Audio Preprocessing | 500-2000ms | < 15ms | **40-600x faster** |
| Memory | Disk I/O | In-memory | Zero disk I/O |
| Processes | 2 (server + client) | 1 | Simpler |
| Total Latency | ~2-5s | ~1-3s | **~50% faster** |

## How It Works

### Before (API Mode)
```
Audio → hybrid_server.py → HTTP POST → wispr_flow_server.py:9095 → Baseten API → Response
                          ↑                                    ↑
                     +50-200ms                            subprocess overhead
```

### After (Direct Mode)
```
Audio → hybrid_server.py → wispr_flow_direct.py → Baseten API → Response
                          ↑
                    In-memory, no HTTP
```

## Configuration

### Enable Direct Mode (Default)

Direct mode is enabled by default. No configuration needed!

```bash
# .env (optional - this is the default)
FLOW_DIRECT_MODE=1
MODE=FLOW
```

### Disable Direct Mode (Use Legacy API Server)

```bash
# .env
FLOW_DIRECT_MODE=0
MODE=FLOW
```

Then start the API server:
```bash
./scripts/start_wispr_flow.sh start
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MODE` | `LOCAL` | Set to `FLOW` to use Wispr Flow transcription |
| `FLOW_DIRECT_MODE` | `1` | Set to `0` to use legacy API server mode |
| `WISPR_FLOW_JWT_TOKEN` | (required) | JWT authentication token |
| `WISPR_FLOW_BASETEN_API_KEY` | (required) | Baseten API key |
| `WISPR_FLOW_USER_UUID` | (required) | User UUID |

## Usage

### With hybrid_server.py (Recommended)

Just start the hybrid server - direct mode is automatic:

```bash
# Start hybrid server (direct mode is default)
python -m hypr_voice.whisper.core.hybrid_server

# Or use the start script
./scripts/start_hybrid_server.sh
```

You'll see this in the logs:
```
============================================================
🚀 FLOW DIRECT MODE ENABLED
============================================================
Bypassing API server for maximum performance:
  • Audio preprocessing: < 15ms (vs 500-2000ms)
  • No HTTP overhead: saves 50-200ms per request
  • Parallel chunk processing: built-in

To use legacy API mode: set FLOW_DIRECT_MODE=0
============================================================
```

### Programmatic Usage

```python
from hypr_voice.services.wispr_flow_direct import DirectWisprFlowClient
import asyncio

async def transcribe():
    client = DirectWisprFlowClient()
    
    result = await client.transcribe_file(
        audio_path="audio.wav",
        language=["en"],
        app_type="code",
        app_name="VS Code",
        dictionary_words=["Kubernetes", "PostgreSQL"],
    )
    
    if result["success"]:
        print(f"Text: {result['text']}")
        print(f"Preprocessing: {result['metadata']['preprocess_ms']}ms")
        print(f"Network: {result['metadata']['network_ms']}ms")
    else:
        print(f"Error: {result['error']}")

asyncio.run(transcribe())
```

## Troubleshooting

### "Direct flow client not available"

The system will automatically fall back to API mode. Check:

1. **Credentials**: Ensure these env vars are set:
   ```bash
   WISPR_FLOW_JWT_TOKEN=<your_token>
   WISPR_FLOW_BASETEN_API_KEY=<your_key>
   WISPR_FLOW_USER_UUID=<your_uuid>
   ```

2. **wisper-flow module**: Ensure `src/wisper-flow/transcribe.py` exists

3. **Dependencies**: Install required packages:
   ```bash
   pip install httpx soundfile numpy
   ```

### Import Errors

Ensure the wisper-flow module exists:
```bash
ls src/wisper-flow/transcribe.py
```

### Still Slow?

1. Check that `FLOW_DIRECT_MODE=1` in `.env`
2. Restart hybrid_server.py
3. Look for "🚀 FLOW DIRECT MODE ENABLED" in startup logs

### Want to Use Legacy API Mode?

```bash
# 1. Set env var
echo "FLOW_DIRECT_MODE=0" >> .env

# 2. Start API server
./scripts/start_wispr_flow.sh start

# 3. Restart hybrid server
./scripts/start_hybrid_server.sh restart
```

## Migration Guide

### From API Mode to Direct Mode

1. **Stop the API server** (optional, saves resources):
   ```bash
   ./scripts/start_wispr_flow.sh stop
   ```

2. **Set direct mode** (or just remove the line - it's default):
   ```bash
   # In .env
   FLOW_DIRECT_MODE=1
   ```

3. **Restart hybrid server**:
   ```bash
   ./scripts/start_hybrid_server.sh restart
   ```

4. **Verify**: Look for "🚀 FLOW DIRECT MODE ENABLED" in logs

### From Direct Mode to API Mode (Rollback)

1. **Set API mode**:
   ```bash
   # In .env
   FLOW_DIRECT_MODE=0
   ```

2. **Start API server**:
   ```bash
   ./scripts/start_wispr_flow.sh start
   ```

3. **Restart hybrid server**:
   ```bash
   ./scripts/start_hybrid_server.sh restart
   ```

## Architecture

### Direct Mode Components

```
src/
├── hypr_voice/
│   ├── services/
│   │   └── wispr_flow_direct.py    # Direct client wrapper
│   └── whisper/
│       └── core/
│           └── hybrid_server.py     # Routes to direct/API mode
└── wisper-flow/
    └── transcribe.py                # Core transcription logic
```

### Key Functions

| Function | File | Purpose |
|----------|------|---------|
| `DirectWisprFlowClient` | `wispr_flow_direct.py` | Direct API client |
| `_get_direct_flow_client()` | `hybrid_server.py` | Lazy client initialization |
| `_flow_transcribe_file_direct()` | `hybrid_server.py` | Direct transcription handler |
| `_flow_transcribe_file()` | `hybrid_server.py` | Routes to direct/API mode |
| `transcribe_file_async()` | `wisper-flow/transcribe.py` | Core transcription |

## Benefits Summary

✅ **50-200ms faster** per request (no HTTP overhead)  
✅ **40-600x faster** audio preprocessing  
✅ **Single process** architecture  
✅ **In-memory** processing (no disk I/O)  
✅ **Parallel** chunk processing built-in  
✅ **Zero** new dependencies  
✅ **Easy** rollback via env variable  
✅ **Backward** compatible  

## Related Documentation

- [Implementation Plan](../plan/wispr_flow_direct_integration_plan.md)
- [Wispr Flow API Documentation](../src/hypr_voice/services/WISPR_FLOW_API.md)
- [Architecture Report](../report/report.md)
