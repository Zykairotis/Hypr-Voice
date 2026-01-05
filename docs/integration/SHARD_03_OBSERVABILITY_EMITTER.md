# SHARD 03 — Python Observability Emitter

Goal: forward Hypr-Voice runtime events to the same endpoint the Claude hooks use, so web-ui shows a unified timeline.

Target file
- `src/hypr_voice/services/observability/claude_hooks.py` (new)

Events to emit
- Transcription: start/complete/error
- Routing: route_decision (agent, confidence, reasoning)
- TTS: start/complete (streaming flag, duration_ms, provider)
- Sandbox exec (see SHARD_05): command, status, sandbox_id
- Web UI interactions (optional)

Payload shape (match `send_event.py`)
```json
{
  "source_app": "hypr-voice",
  "event_type": "TTS_COMPLETE",
  "session_id": "<conv_id>",
  "payload": {...},
  "ts": "<iso8601>",
  "severity": "info"
}
```

Config
- `CLAUDE_HOOKS_ENABLED=1`
- `CLAUDE_HOOKS_OBS_URL=http://localhost:5173` (or whatever the Bun server exposes)

Implementation sketch
- Lightweight async HTTP POST using `aiohttp`.
- Non-blocking: failures are logged, never raise.
- Helper `emit(event_type, payload, severity="info", session_id=None)`.
- Hook `voice_orchestrator.py` to call emitter at existing log points.
