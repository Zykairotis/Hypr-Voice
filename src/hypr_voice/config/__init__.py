"""Configuration helpers for Hypr Voice."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from hypr_voice.paths import get_config_path


def load_config(filename: str = "config.yaml") -> Dict[str, Any]:
    """Load a YAML configuration file.

    Args:
        filename: Name of the configuration file to locate.

    Returns:
        Parsed configuration as a dictionary.

    Raises:
        FileNotFoundError: If the resolved configuration file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """

    path: Path = get_config_path(filename)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream) or {}
    return data


__all__ = ["load_config", "get_config_path"]

