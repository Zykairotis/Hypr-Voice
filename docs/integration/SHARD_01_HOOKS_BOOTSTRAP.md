# SHARD 01 — Claude Hooks Bootstrap

Goal: import the full `.claude` hook set from `Ref-github-outsource/claude-code-hooks-multi-agent-observability` and register Hypr-Voice as the source app.

Steps
- Copy `.claude/` into repo root. Keep hook scripts and `settings.json`.
- In `.claude/settings.json` set `"source-app": "hypr-voice"` and ensure all hook types point to `uv run .claude/hooks/send_event.py ...`.
- Add `.claude` to `.gitignore` exceptions if needed (we do want it committed).
- Create `./.env.local` entries for `ANTHROPIC_API_KEY` (required by hook scripts) and optional `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`.

Validation
- From repo root: `uv run .claude/hooks/user_prompt_submit.py --log-only --prompt "hello"` should emit a JSON log in `logs/`.
- Hooks should not block runtime if `CLAUDE_HOOKS_ENABLED=0` (guard to be added in SHARD_03).
