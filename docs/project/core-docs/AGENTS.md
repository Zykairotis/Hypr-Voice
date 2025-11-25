# Repository Guidelines

## Project Structure & Module Organization
- `src/hypr_voice/`: FastAPI orchestrator (`server.py`), agent definitions (`agents/`), service clients/skills (`services/`, `tools/`), utilities (`core/`, `helper/`), examples, and backend tests in `tests/`.
- `src/Hypr-Whisper/`: Hybrid Whisper/LLM context server plus vocabulary hooks; runnable scripts live in `scripts/`.
- `web-ui/`: Next.js 16 dashboard and WS bridge (ports 8933/8934) for monitoring and issuing commands; `start-ui.sh` wraps the dev server.
- `scripts/`: Ops helpers; `start_everything.sh` boots hybrid + context WS + orchestrator + UI, and `hypr_voice/hypr-agent.sh` handles Hyprland push-to-talk capture.
- Dependencies sit in `requirements/` and `pyproject.toml`; UI deps in `web-ui/package.json`; logs output to `logs/` and `/tmp/hypr-voice-*.log`.

## Build, Test, and Development Commands
- Python env: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements/hypr_voice.txt`.
- Editable install (recommended for local imports): `pip install -e .`.
- Orchestrator dev server: `uvicorn hypr_voice.server:app --reload --port 9093`.
- Full stack: `./scripts/start_everything.sh start` (use `stop` or `status` to manage).
- Whisper-only: `cd src/Hypr-Whisper && ./scripts/start_hybrid_server.sh start`.
- Web UI: `cd web-ui && npm install && npm run dev`; production: `npm run build && npm run start`; lint: `npm run lint`.

## Coding Style & Naming Conventions
- Python: format with `black`, lint with `flake8`; snake_case functions/vars, PascalCase classes; add type hints on public functions; env/config keys stay UPPER_SNAKE_CASE.
- Tests/files: name `test_*.py`; co-locate fixtures with tests.
- TypeScript/React: follow repo ESLint config; functional components with camelCase props; keep styling in Tailwind classes; avoid embedding secrets in client bundles.
- Bash scripts: keep executable, start with `set -euo pipefail`, and log with concise prefixes (see existing scripts).

## Testing Guidelines
- Core backend: `pytest src/hypr_voice/tests -v` (pytest-asyncio is available).
- Helper-agent suite: `pytest src/hypr_voice/services/helper-agent/tests -v`.
- Coverage (optional): `pytest --cov=hypr_voice --cov-report=term`.
- Integration/TTS tests require keys: `ANTHROPIC_API_KEY`, `DEEPGRAM_API_KEY`, `ELEVENLABS_API_KEY`, `OPENAI_API_KEY`; tests skip or fail without them.
- Web UI: `npm run lint`; add component/unit tests under `web-ui/__tests__` if you introduce them.

## Commit & Pull Request Guidelines
- Use Conventional Commits as in history (`feat:`, `fix:`, `refactor:`, `chore:`, `docs:`).
- Keep changes scoped (orchestrator vs whisper vs UI) and mention affected services.
- PR checklist: concise summary + motivation, linked issue, test commands/output, note port changes, and include UI diffs/screenshots when touching `web-ui/`.
- Do not commit logs, recordings, or generated audio; update docs when behavior or ports change.

## Security & Configuration Tips
- Store secrets locally in `.env` (never in git); common keys: `HYPR_VOICE_MODEL`, `HYPR_VOICE_MAX_TURNS`, `ANTHROPIC_API_KEY`, provider TTS keys, `OPENAI_API_KEY`.
- Default ports: 9093 (orchestrator), 9091 (context WS), 9099 (hybrid server), 8933/8934 (UI/bridge); align UI env vars (`CONTEXT_WS_UPSTREAM`, `NEXT_PUBLIC_CONTEXT_WS`) if you change them.
- Clear temp logs in `/tmp/hypr-voice-*.log` after debugging and keep `logs/` out of commits.
