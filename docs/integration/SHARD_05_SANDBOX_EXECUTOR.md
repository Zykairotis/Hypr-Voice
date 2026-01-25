# SHARD 05 — Shell Worker Sandbox Mode

Goal: route shell-worker agent commands through E2B when enabled.

Changes
- `src/hypr_voice/services/helper/agents/shell_worker.py` (or equivalent): add flag `use_sandbox = env.bool("HYPR_VOICE_E2B_ENABLED", False)`.
- When true: acquire sandbox via `e2b_client`, exec commands there, stream stdout/stderr back.
- Attach `sandbox_id` to orchestrator response and emit OBS event.
- Add timeout guard; auto-destroy sandboxes after inactivity.

Env
- `HYPR_VOICE_E2B_ENABLED=1`
- `HYPR_VOICE_E2B_TEMPLATE=...`
- `HYPR_VOICE_E2B_TIMEOUT=120`

Validation
- Run a shell-worker query; logs should show sandbox id and command output.
- Ensure fallback to local exec when sandbox creation fails.
