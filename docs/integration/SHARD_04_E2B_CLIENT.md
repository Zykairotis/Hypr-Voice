# SHARD 04 — E2B Sandbox Client

Goal: embed the minimal e2b SDK wrapper so agents can execute commands/files in isolated sandboxes instead of host.

Source reference
- `Ref-github-outsource/agent-sandboxes/apps/sandbox_cli/src`

Target file
- `src/hypr_voice/integrations/e2b_client.py`

Capabilities (MVP)
- create sandbox (template optional)
- exec command (stdin/out/err)
- upload/download files
- list files
- keepalive / destroy

Config
- `E2B_API_KEY` (required)
- `HYPR_VOICE_E2B_TEMPLATE=agent-sandbox-dev-node22` (optional)

Testing
- Unit-style: `python -m hypr_voice.integrations.e2b_client --smoke "echo hi"` prints output, exits 0.
