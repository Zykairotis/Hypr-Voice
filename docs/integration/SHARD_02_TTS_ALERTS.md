# SHARD 02 — Hook-triggered TTS Alerts

Goal: reuse the TTS utility stack from `claude-code-hooks-mastery/.claude/hooks/utils/tts` to play short alerts on hook events (Notification, Stop, SubagentStop).

Steps
- Copy `utils/tts/` and `utils/llm/` from the mastery repo into `.claude/hooks/utils/`.
- Wire `notification.py` and `stop.py` to call the TTS helper when `--notify` flag present.
- Default voice priority: ElevenLabs > OpenAI > pyttsx3 (offline).  
  Configure with `ELEVENLABS_API_KEY` or `OPENAI_API_KEY`.
- Keep alerts <1.5s to avoid overlapping with Hypr-Voice audio output.

Config
- `CLAUDE_TTS_ALERTS=1` (gate)
- `CLAUDE_TTS_ALERT_VOICE=...` (optional)

Validation
- `uv run .claude/hooks/notification.py --notify --message "Agent waiting"` plays once, logs JSON.
