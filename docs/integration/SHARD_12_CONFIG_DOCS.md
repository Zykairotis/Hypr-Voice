# SHARD 12 — Config & Setup Reference

Environment Variables
- CLAUDE_HOOKS_ENABLED (0/1)
- CLAUDE_HOOKS_SOURCE_APP=hypr-voice
- CLAUDE_HOOKS_OBS_URL=http://localhost:5173
- CLAUDE_TTS_ALERTS (0/1)
- E2B_API_KEY
- HYPR_VOICE_E2B_ENABLED (0/1)
- HYPR_VOICE_E2B_TEMPLATE=agent-sandbox-dev-node22
- HYPR_VOICE_E2B_TIMEOUT=120
- HYPR_VOICE_TTS_STREAMING=1
- HYPR_VOICE_TTS_PREBUFFER_MS=1000
- HYPR_VOICE_TTS_MIN_CHARS=140
- HYPR_VOICE_TTS_MAX_LATENCY=0.8
- HYPR_VOICE_TTS_FLUSH_TIMEOUT=15
- HYPR_VOICE_TTS_IDLE_TIMEOUT=3
- HYPR_AGENT_TIMEOUT=150
- ANTHROPIC_API_KEY, OPENAI_API_KEY, ELEVENLABS_API_KEY

Scripts to add/adjust
- `scripts/start_observability.sh` to boot Bun server + WS bridge (from observability repo).
- `scripts/start_sandbox_workflow.sh` to launch e2b workflow if needed.

Ports
- Observability server (Bun/Vue): 5173 (client) / 8787 (server) in ref repo; align with Hypr-Voice WS bridge 8933/8934 or proxy.

Logging
- Keep hook/event logs under `logs/observability/`.
- Rotate or truncate; avoid committing.
