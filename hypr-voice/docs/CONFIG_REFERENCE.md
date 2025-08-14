# Hypr-Voice Configuration Reference & Usage Mapping

This document maps each configuration file under `config/` to its usage in the codebase, and catalogs relevant environment variables and CLI flags.

- Project root: `hypr-voice/`
- Config directory: `hypr-voice/config/`
- Audio guide: see `docs/AUDIO_CONFIGURATION.md`

## Config files in config/

- `config/audio_config.yaml`
  - Used by: `hypr_voice.py` in `HyprVoice._load_audio_config()` (lines ~159–212)
  - Purpose: Audio device selection, recording quality, processing, and whisper preprocessing.
  - Keys recognized by `hypr_voice.py` (with defaults when missing):
    - `audio.quality.sample_rate` (48000)
    - `audio.quality.channels` (1)
    - `audio.quality.dtype` (float32)
    - `audio.quality.blocksize` (2048)
    - `audio.quality.fallback_sample_rates` ([44100, 48000, 32000, 24000, 16000])
    - `audio.devices.primary.name` ('default')
    - `audio.devices.secondary.name` ('default')
    - `audio.devices.auto_fallback` (True)
    - `audio.devices.list_on_startup` (True triggers `print_audio_devices()`)
    - `audio.recording.max_duration` (60 seconds)
    - `audio.recording.silence_threshold` (0.01)
    - `audio.recording.silence_duration` (2.0 seconds)
    - `audio.recording.format` ('wav')
    - `audio.whisper.target_sample_rate` (16000)
    - `audio.whisper.keep_originals` (True)
    - `audio.whisper.originals_dir` ('recordings/originals')
    - `audio.whisper.processed_dir` ('recordings/processed')
  - See: `docs/AUDIO_CONFIGURATION.md` for deeper audio coverage and best practices.

- `config/app_profiles.yaml`
  - Used by:
    - `simple_improvement_engine.py` → `_load_profiles()` (lines ~65–98) to build `AppProfile` objects with:
      - `app_class`, `writing_style`, `context_rules`, `abbreviations`, `terminology`, `extra_context`, `llm_config`, `output_format`, `memory_scope`, `system_prompt`
    - `context_engine_cognee.py` → `_load_profiles()` (lines ~250–295) to build `ApplicationProfile` with:
      - `patterns`, `context_rules`, `mcp_tools`, `system_prompt`, plus `llm_config`, `output_format`, `memory_scope`
      - Ensures a robust `default` profile if missing
    - `enhanced_prompting.py` → `_load_config("app_profiles.yaml")` (lines ~74–79)
  - Purpose: Per-application/profile behavior, context rules, and LLM settings.

- `config/global_tools.yaml`
  - Used by: `enhanced_prompting.py` → `_load_config("global_tools.yaml")` (line ~77)
  - Purpose: Global MCP tools available across profiles (consumed by the enhanced prompting pipeline).

- `config/profile_tools.yaml`
  - Used by: `enhanced_prompting.py` → `_load_config("profile_tools.yaml")` (line ~79)
  - Purpose: MCP tools restricted to specific profiles/apps for contextual operations.

- `config/llm_providers.yaml`
  - Used by: `enhanced_prompting.py` → `_load_config("llm_providers.yaml")` (line ~78)
  - Purpose: Configure LLM providers (OpenAI, Anthropic, Google, xAI, etc.). API keys are injected via env vars in the YAML:
    - Example lines: `${OPENAI_API_KEY}`, `${ANTHROPIC_API_KEY}`, `${GOOGLE_API_KEY}`, `${XAI_API_KEY}`.

## Additional config sources

- `mcp.json` (project root)
  - Used by:
    - `enhanced_prompting.py` → `_load_mcp_config()` (lines ~98–112)
    - `context_engine_cognee.py` → `_load_mcp_tools()` (lines ~319–328)
  - Purpose: Define MCP servers; both modules log how many servers are loaded and list sample server names.

- `config/mcp_tools.yaml` (optional)
  - Referenced by: `context_engine_cognee.py` (line ~312)
  - Purpose: Define MCP tools via YAML. If not present, the engine falls back to `mcp.json`.

- `config/agent_config.yaml` (optional)
  - Referenced by: `agent_orchestrator.py` (line ~85) as the default `config_path` if provided.
  - Note: This file is not present by default; the orchestrator primarily uses environment variables to enable providers.

## Environment variables (by usage)

- LLM providers and keys
  - `XAI_API_KEY`
    - Used in: `agent_orchestrator.py` (provider setup), `simple_improvement_engine.py` (HTTP auth), `context_engine_cognee.py` (LLM config), `config/llm_providers.yaml`
  - `OPENAI_API_KEY`
    - Used in: `agent_orchestrator.py`, `config/llm_providers.yaml`
  - `ANTHROPIC_API_KEY`
    - Used in: `agent_orchestrator.py`, `config/llm_providers.yaml`
  - `GOOGLE_API_KEY`
    - Used in: `config/llm_providers.yaml`
  - `VOYAGE_API_KEY`
    - Used in: `enhanced_prompting.py` embedding registry (`registry.get("voyage").create(..., api_key="${VOYAGE_API_KEY}")`)

- Audio and whisper
  - `WHISPER_SERVER_URL` (default `http://localhost:9880`)
    - Used in: `hypr_voice.py` for remote transcription server endpoint

- Hypr-Voice toggles
  - `HYPR_VOICE_NO_IMPROVE` ("true" to disable LLM improvement)
    - Used in: `hypr_voice.py`
  - `HYPR_VOICE_INPUT_DEVICE` (string index or name substring)
    - Used in: `hypr_voice.py`; can be overridden by CLI `-d/--input-device`

- Performance knobs
  - `HYPR_DISABLE_RUNTIME_CONTEXT` (1/true/yes to skip runtime `extra_context` shell commands)
    - Used in: `enhanced_prompting.py` (line ~559)
  - `VOYAGE_CACHE_SIZE` (default `512`) LRU size for query embeddings
    - Used in: `enhanced_prompting.py` (line ~71)
  - `AGENT_HISTORY_LIMIT` (e.g., 10/20) trims chat history for cost/latency
    - Used in: `agent_orchestrator.py` (e.g., lines ~256, ~300)
  - `XAI_TIMEOUT` (seconds, default ~8.0) HTTP timeout
    - Used in: `simple_improvement_engine.py` (line ~57)

- Other examples in `.env.example`
  - The example includes additional keys (e.g., `LLM_PROVIDER`, `EMBEDDING_MODEL`, `OLLAMA_BASE_URL`), but not all are consumed directly by the code. The authoritative sources are the usages listed above and `config/llm_providers.yaml`.

## CLI flags (Hypr-Voice client)

- File: `hypr_voice.py` → `main()` argparse block (lines ~1188–1269)
- Flags:
  - `-f, --file <path>`
  - `-c, --config <dir>` override config directory (default `hypr-voice/config/`)
  - `-p, --push-to-talk` enable PTT mode
  - `--list-devices` list audio input devices and exit
  - IPC shortcuts: `--start`, `--stop`, `--force-stop`, `--status`
  - `-d, --input-device <id|name-substr>` overrides `$HYPR_VOICE_INPUT_DEVICE`
  - `--no-improve` skip LLM improvement
  - `--test-recording SECONDS` record mic audio for N seconds to `recordings/`

## How the pieces work together

- `hypr_voice.py` consumes `audio_config.yaml` and environment variables to control audio capture and whisper preprocessing; it exposes runtime toggles via CLI flags.
- `simple_improvement_engine.py` and `context_engine_cognee.py` consume `app_profiles.yaml` for application-aware behavior; the former handles improvement policies and terminology, the latter builds profile objects and MCP tool lists.
- `enhanced_prompting.py` consolidates configs (`app_profiles.yaml`, `global_tools.yaml`, `profile_tools.yaml`, `llm_providers.yaml`) and `mcp.json`, builds semantic context tables (LanceDB + VoyageAI), and can skip runtime shell-context via `HYPR_DISABLE_RUNTIME_CONTEXT`.
- `agent_orchestrator.py` selects and orchestrates LLM providers based on available environment variables (and an optional `config/agent_config.yaml`), trimming history via `AGENT_HISTORY_LIMIT`.

## Known optional/missing configs

- `config/mcp_tools.yaml`: not present by default; `context_engine_cognee.py` will rely on `mcp.json` if absent.
- `config/agent_config.yaml`: not present by default; providers are enabled via env vars.

## Recommended commands

Use the project virtual environment (uv):

```bash
cd /home/mewtwo/Code/Hypr-V/hypr-voice
uv run python hypr_voice.py -p  # push-to-talk mode
uv run python hypr_voice.py --list-devices
uv run python hypr_voice.py -d "<device name substring>"
```

## Cross-references

- Audio specifics: `docs/AUDIO_CONFIGURATION.md`
- Profiles: `config/app_profiles.yaml`
- LLM providers: `config/llm_providers.yaml`
- MCP servers: `mcp.json`

If you’d like, we can add a link from `README.md` to this reference.
