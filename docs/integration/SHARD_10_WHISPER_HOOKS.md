# SHARD 10 — Hypr-Whisper Event Emission

Goal: emit Whisper events into the same observability stream for end-to-end tracing.

Touchpoints
- `src/Hypr-Whisper/hybrid_server.py`: on session create, upload start/complete, transcription complete/error.

Mechanics
- POST to CLAUDE_HOOKS_OBS_URL with event_type `WHISPER_*`, include session_id, file name, duration_ms, language.
- Guarded by `CLAUDE_HOOKS_ENABLED`.

Edge
- Do not block transcription path; failures warn only.
