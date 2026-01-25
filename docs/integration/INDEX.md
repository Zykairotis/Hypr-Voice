# Hypr-Voice Integration Plan (Ref-github-outsource)

This folder breaks the integration into shards so we can ship in slices. Execute in order; each shard is independent documentation with concrete steps.

## Execution Order
1) SHARD_01_HOOKS_BOOTSTRAP.md  
2) SHARD_02_TTS_ALERTS.md  
3) SHARD_03_OBSERVABILITY_EMITTER.md  
4) SHARD_04_E2B_CLIENT.md  
5) SHARD_05_SANDBOX_EXECUTOR.md  
6) SHARD_06_UI_OBSERVABILITY.md  
7) SHARD_07_UI_SAFETY_DRAWER.md  
8) SHARD_08_UI_SANDBOX_CONSOLE.md  
9) SHARD_09_UI_PULSE_CHART.md  
10) SHARD_10_WHISPER_HOOKS.md  
11) SHARD_11_STATUS_STYLES.md  
12) SHARD_12_CONFIG_DOCS.md

## Environment Variables (global set)
- CLAUDE_HOOKS_ENABLED=1
- CLAUDE_HOOKS_SOURCE_APP=hypr-voice
- CLAUDE_HOOKS_OBS_URL=http://localhost:5173 (Bun/Vue observability server)  
- E2B_API_KEY=… (from e2b.dev)
- HYPR_VOICE_E2B_ENABLED=0|1
- HYPR_VOICE_TTS_STREAMING=1
- HYPR_VOICE_TTS_PREBUFFER_MS=1000
- HYPR_VOICE_TTS_MIN_CHARS=140
- HYPR_VOICE_TTS_MAX_LATENCY=0.8
- HYPR_VOICE_TTS_FLUSH_TIMEOUT=15
- HYPR_VOICE_TTS_IDLE_TIMEOUT=3
- HYPR_AGENT_TIMEOUT=150

## Links to reference material
- Ref-github-outsource/agent-sandboxes (e2b CLI/MCP/workflows)
- Ref-github-outsource/claude-code-hooks-mastery (.claude hooks + TTS utils)
- Ref-github-outsource/claude-code-hooks-multi-agent-observability (hooks + Bun/Vue observability stack)
