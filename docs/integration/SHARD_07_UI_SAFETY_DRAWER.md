# SHARD 07 — UI Safety & Routing Drawer

Goal: expose runtime toggles for sandbox mode and hook emission.

Placement
- Global top-right drawer accessible from navbar (“Safety” icon).

Controls
- Switch: “Run tools in E2B sandbox” (binds HYPR_VOICE_E2B_ENABLED)
- Switch: “Emit Claude hooks” (CLAUDE_HOOKS_ENABLED)
- Switch: “Play hook TTS alerts” (CLAUDE_TTS_ALERTS)
- Slider: “TTS prebuffer (ms)” (HYPR_VOICE_TTS_PREBUFFER_MS)
- Slider: “Flush timeout (s)” (HYPR_VOICE_TTS_FLUSH_TIMEOUT)

Persistence
- Writes to user-scoped settings in localStorage + pushes PATCH to orchestrator `/settings` (to add).

Telemetry
- Show last sandbox id used and last hook event time.
