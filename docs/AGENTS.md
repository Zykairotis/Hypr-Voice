# Repository Guidelines

## Project Structure & Module Organization
- `src/hypr_voice/`: FastAPI orchestrator (`server.py`), agents (`agents/`), services & skills (`services/`, `tools/`), utilities (`core/`, `helper/`), examples, and tests in `tests/`.
- `src/Hypr-Whisper/`: Hybrid Whisper/LLM context server and vocabulary hooks; runnable via `scripts/`.
- `web-ui/`: Next.js 16 dashboard + WS bridge on ports 8933/8934; `start-ui.sh` wraps the dev server.
- `scripts/`: Operational helpers; `start_everything.sh` boots hybrid + context WS + orchestrator + UI; `hypr_voice/hypr-agent.sh` manages Hyprland push-to-talk.
- Dependencies live in `requirements/` + `pyproject.toml`; UI deps in `web-ui/package.json`; runtime logs land in `logs/` or `/tmp/hypr-voice-*.log`.

## Build, Test, and Development Commands
- Python setup: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements/hypr_voice.txt`; optional `pip install -e .` for editable imports.
- Orchestrator dev: `uvicorn hypr_voice.server:app --reload --port 9093`.
- Full stack: `./scripts/start_everything.sh start` (`stop`/`status` available).
- Whisper only: `cd src/Hypr-Whisper && ./scripts/start_hybrid_server.sh start`.
- Web UI: `cd web-ui && npm install && npm run dev`; production: `npm run build && npm run start`; lint: `npm run lint`.

## Coding Style & Naming Conventions
- Python: format with `black`, lint with `flake8`; snake_case for functions/vars, PascalCase classes, type hints on public funcs; env keys UPPER_SNAKE_CASE.
- Tests/files: `test_*.py` naming; fixtures beside tests.
- TypeScript/React: follow repo ESLint; functional components, camelCase props, Tailwind classes for styling; keep secrets out of client code.
- Bash: keep executable, use `set -euo pipefail`, and concise log prefixes.

## Testing Guidelines
- Core backend: `pytest src/hypr_voice/tests -v`.
- Helper-agent suite: `pytest src/hypr_voice/services/helper-agent/tests -v`.
- Coverage: `pytest --cov=hypr_voice --cov-report=term`.
- Integration/TTS tests expect `ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`; skipped or fail without them.
- Web UI: `npm run lint`; add component tests under `web-ui/__tests__` when created.

## Commit & Pull Request Guidelines
- Prefer Conventional Commits (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`) as seen in history.
- Keep commits scoped (orchestrator vs whisper vs UI) and mention touched services.
- PRs: concise summary + motivation, linked issue, test commands/results, note port/env changes, and attach UI screenshots when modifying `web-ui/`.
- Exclude logs, recordings, and generated audio; update docs when behavior or ports change.

## Security & Configuration Tips
- Keep secrets in local `.env`; common keys: `HYPR_VOICE_MODEL`, `HYPR_VOICE_MAX_TURNS`, `ANTHROPIC_API_KEY`, provider TTS keys, `OPENAI_API_KEY`.
- Default ports: 9093 (orchestrator), 9091 (context WS), 9099 (hybrid server), 8933/8934 (UI/bridge); adjust UI env (`CONTEXT_WS_UPSTREAM`, `NEXT_PUBLIC_CONTEXT_WS`) if changed.
- Clear `/tmp/hypr-voice-*.log` after debugging; keep `logs/` out of commits.
