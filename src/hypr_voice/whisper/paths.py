"""Path helpers for Hypr-Whisper assets and configuration."""

from __future__ import annotations

import os
from pathlib import Path

from hypr_voice.paths import PROJECT_ROOT, USER_CONFIG_DIR, STATE_DIR

WHISPER_PACKAGE_ROOT: Path = Path(__file__).resolve().parent
WHISPER_PACKAGE_CONFIG_DIR: Path = WHISPER_PACKAGE_ROOT / "config"

WHISPER_CONFIG_DIR: Path = Path(
    os.getenv("HYPR_VOICE_WHISPER_CONFIG_DIR", USER_CONFIG_DIR / "whisper")
).expanduser()
WHISPER_STATE_DIR: Path = Path(
    os.getenv("HYPR_VOICE_WHISPER_STATE_DIR", STATE_DIR / "whisper")
).expanduser()
WHISPER_RECORDINGS_DIR: Path = Path(
    os.getenv("HYPR_VOICE_WHISPER_RECORDINGS_DIR", WHISPER_STATE_DIR / "recordings")
).expanduser()


def get_whisper_config_dir() -> Path:
    """Return the best available config directory for whisper."""
    for candidate in (WHISPER_CONFIG_DIR, WHISPER_PACKAGE_CONFIG_DIR):
        if candidate.exists():
            return candidate
    return WHISPER_CONFIG_DIR


def get_whisper_config_path(filename: str) -> Path:
    """Resolve a config file path for whisper."""
    for base in (WHISPER_CONFIG_DIR, WHISPER_PACKAGE_CONFIG_DIR):
        candidate = base / filename
        if candidate.exists():
            return candidate
    return WHISPER_CONFIG_DIR / filename


def ensure_whisper_state_dirs() -> None:
    """Ensure whisper state directories exist."""
    WHISPER_STATE_DIR.mkdir(parents=True, exist_ok=True)
    WHISPER_RECORDINGS_DIR.mkdir(parents=True, exist_ok=True)


__all__ = [
    "PROJECT_ROOT",
    "WHISPER_PACKAGE_ROOT",
    "WHISPER_PACKAGE_CONFIG_DIR",
    "WHISPER_CONFIG_DIR",
    "WHISPER_STATE_DIR",
    "WHISPER_RECORDINGS_DIR",
    "get_whisper_config_dir",
    "get_whisper_config_path",
    "ensure_whisper_state_dirs",
]
