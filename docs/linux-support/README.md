# Linux Desktop Support Overview

This folder tracks the work to make Hypr-Whisper usable on common Linux desktops beyond Hyprland while keeping existing users untouched. Key documents:

- `cross-desktop-support-plan.md` – 5-part plan (detection, introspection adapters, input injection, packaging/permissions, QA).
- `cross-desktop-implementation-report.md` – what is implemented, how detection works, test steps, and known limits.

Quick usage
- Window backend auto-detects on first run and caches to `~/.cache/hypr-voice/backend.json`. Override with `HYPR_VOICE_WINDOW_BACKEND`.
- Input backend auto-picks ydotool → kdotool → wtype → xdotool; override with `HYPR_VOICE_INPUT_BACKEND`.
- Health check: `python src/Hypr-Whisper/scripts/backend_health.py` (add `--type-test` to send the string "Hello").

Safety
- All probes use short timeouts; missing tools just downgrade capabilities (no crashes).
- Typing failures log and no-op, keeping existing flows stable.

Where to read next
- See the plan for the roadmap and the implementation report for current coverage and gaps.
