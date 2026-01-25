# SHARD 08 — UI Sandbox Console

Goal: let users inspect sandbox output per session.

Features
- Tabs: Logs | Files | Terminal (read-only) | Artifacts
- Logs: stream latest sandbox stdout/stderr (tail via orchestrator proxy).
- Files: tree view with download button.
- Terminal: run whitelisted read-only commands (`ls`, `cat`, `du -h --max-depth=1`).
- Artifacts: list files produced by tasks (from e2b file list).

API
- Add orchestrator endpoints: `/sandbox/{id}/logs`, `/sandbox/{id}/files`, `/sandbox/{id}/exec`.
- Require `HYPR_VOICE_E2B_ENABLED=1`.

UI Placement
- Conversation detail page secondary tab or side drawer.
