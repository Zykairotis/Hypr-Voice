# SHARD 11 — Status Lines & Output Styles

Goal: port the richer status lines/output styles from `claude-code-hooks-mastery` to improve CLI/TTY feedback.

Assets to copy
- `.claude/status_lines/status_line_v3.py` (sessions + history)
- `.claude/output-styles/tts-summary.md` (for hook TTS summaries)

Hypr-Voice usage
- Optional: render status line in CLI runner or logs during long ops (transcription, TTS, sandbox).
- Keep behind flag `CLAUDE_STATUS_LINE=1`.
