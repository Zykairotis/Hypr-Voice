"""Centralized path helpers for Hypr Voice runtime assets and configuration."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable


def _expand(path: str | os.PathLike[str]) -> Path:
    return Path(path).expanduser()


def _find_project_root() -> Path:
    env_root = os.getenv("HYPR_VOICE_PROJECT_ROOT")
    if env_root:
        return _expand(env_root).resolve()

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".git").exists() or (parent / "pyproject.toml").exists():
            return parent

    # Fallback to the repository-style layout (../../ from this file)
    return current.parents[2]


PACKAGE_ROOT: Path = Path(__file__).resolve().parent
SRC_ROOT: Path = PACKAGE_ROOT.parent
PROJECT_ROOT: Path = _find_project_root()

CONFIG_PACKAGE_DIR: Path = PACKAGE_ROOT / "config"
DEFAULT_CONFIG_DIR: Path = CONFIG_PACKAGE_DIR / "defaults"

USER_CONFIG_DIR: Path = _expand(
    os.getenv("HYPR_VOICE_CONFIG_DIR", PROJECT_ROOT / "config" / "hypr_voice")
)
STATE_DIR: Path = _expand(os.getenv("HYPR_VOICE_STATE_DIR", PROJECT_ROOT / "var" / "hypr_voice"))

TTS_OUTPUT_DIR: Path = _expand(
    os.getenv("HYPR_VOICE_TTS_DIR", STATE_DIR / "tts_output" / "claude")
)
CLI_OUTPUT_DIR: Path = _expand(
    os.getenv("HYPR_VOICE_CLI_OUTPUT_DIR", STATE_DIR / "cli_tts_output" / "history")
)
AUDIO_OUTPUT_DIR: Path = _expand(
    os.getenv("HYPR_VOICE_AUDIO_OUTPUT_DIR", STATE_DIR / "audio_output" / "raw_agent")
)
LOG_DIR: Path = _expand(os.getenv("HYPR_VOICE_LOG_DIR", STATE_DIR / "logs" / "raw"))


def runtime_directories() -> Iterable[Path]:
    yield STATE_DIR
    yield TTS_OUTPUT_DIR
    yield CLI_OUTPUT_DIR
    yield AUDIO_OUTPUT_DIR
    yield LOG_DIR


def ensure_runtime_directories() -> None:
    for directory in runtime_directories():
        directory.mkdir(parents=True, exist_ok=True)


def get_config_path(filename: str = "config.yaml") -> Path:
    """Resolve a configuration file path.

    Search order:
        1. User override directory (``HYPR_VOICE_CONFIG_DIR`` or ``config/hypr_voice``)
        2. Package-level config file (``src/hypr_voice/config/<name>``)
        3. Package defaults (``src/hypr_voice/config/defaults/<name>``)
    """

    candidates = [
        USER_CONFIG_DIR / filename,
        CONFIG_PACKAGE_DIR / filename,
        DEFAULT_CONFIG_DIR / filename,
    ]

    for path in candidates:
        try:
            resolved = path.expanduser()
            if resolved.exists():
                return resolved
        except RuntimeError:
            # Path resolution can fail on some systems if parts don't exist
            continue

    # Fall back to the default location even if the file is missing; callers can handle the error
    return DEFAULT_CONFIG_DIR / filename


__all__ = [
    "PACKAGE_ROOT",
    "SRC_ROOT",
    "PROJECT_ROOT",
    "CONFIG_PACKAGE_DIR",
    "DEFAULT_CONFIG_DIR",
    "USER_CONFIG_DIR",
    "STATE_DIR",
    "TTS_OUTPUT_DIR",
    "CLI_OUTPUT_DIR",
    "AUDIO_OUTPUT_DIR",
    "LOG_DIR",
    "runtime_directories",
    "ensure_runtime_directories",
    "get_config_path",
]

