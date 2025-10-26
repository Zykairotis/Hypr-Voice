"""
Configuration manager for Hypr-Voice bridge service
"""

import yaml
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from loguru import logger
from pydantic import ValidationError

from models import (
    AudioConfigValidation,
    ServerConfigValidation,
    TimeoutConfigValidation
)


class ConfigManager:
    """Configuration manager with validation"""

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # Default to the main hypr-voice config directory
            self.config_dir = Path(__file__).parent.parent.parent / "hypr-voice" / "config"
        else:
            self.config_dir = config_dir

        self.config_cache = {}
        self._load_all_configs()

    def _load_all_configs(self):
        """Load all configuration files"""
        config_files = {
            'audio': 'audio_config.yaml',
            'servers': 'servers.yaml',
            'detection': 'detection_config.yaml',
            'llm_providers': 'llm_providers.yaml',
            'app_profiles': 'app_profiles.yaml',
            'model_config': 'model_config.json'
        }

        for section, filename in config_files.items():
            self._load_config(section, filename)

    def _load_config(self, section: str, filename: str):
        """Load a specific configuration file"""
        config_path = self.config_dir / filename

        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            self.config_cache[section] = {}
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    config = yaml.safe_load(f) or {}
                else:
                    config = json.load(f)

            self.config_cache[section] = config
            logger.debug(f"Loaded config from {config_path}")

        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            self.config_cache[section] = {}

    def get_config(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """Get configuration value"""
        if section not in self.config_cache:
            self._load_config(section, f"{section}.yaml")
            if section not in self.config_cache:
                self._load_config(section, f"{section}.json")

        config = self.config_cache.get(section, {})

        if key is None:
            return config

        # Support dot notation for nested keys
        keys = key.split('.')
        value = config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def update_config(self, section: str, updates: Dict[str, Any], validate: bool = True) -> tuple[bool, List[str]]:
        """Update configuration section"""
        if section not in self.config_cache:
            return False, [f"Unknown configuration section: {section}"]

        errors = []

        if validate:
            validation_errors = self._validate_config_section(section, updates)
            if validation_errors:
                return False, validation_errors

        # Apply updates
        current_config = self.config_cache[section].copy()
        self._deep_update(current_config, updates)
        self.config_cache[section] = current_config

        # Save to file
        saved, save_errors = self._save_config(section)
        if not saved:
            errors.extend(save_errors)

        return len(errors) == 0, errors

    def _validate_config_section(self, section: str, config_data: Dict[str, Any]) -> List[str]:
        """Validate configuration section"""
        errors = []

        try:
            if section == 'audio':
                # Validate audio configuration
                quality = config_data.get('quality', {})
                if quality:
                    AudioConfigValidation(**quality)

                # Validate timeouts
                timeouts = config_data.get('timeouts', {})
                if timeouts:
                    TimeoutConfigValidation(**timeouts)

            elif section == 'servers':
                # Validate server configuration
                services = config_data.get('services', {})
                if services and 'whisper' in services:
                    whisper_config = services['whisper']
                    ServerConfigValidation(
                        host=whisper_config.get('host', 'localhost'),
                        port=whisper_config.get('port', 9880),
                        protocol=whisper_config.get('protocol', 'http')
                    )

        except ValidationError as e:
            errors.extend([f"Validation error: {err['msg']}" for err in e.errors()])
        except Exception as e:
            errors.append(f"Validation error: {e}")

        return errors

    def _deep_update(self, base_dict: Dict[str, Any], update_dict: Dict[str, Any]):
        """Deep update dictionary"""
        for key, value in update_dict.items():
            if key in base_dict and isinstance(base_dict[key], dict) and isinstance(value, dict):
                self._deep_update(base_dict[key], value)
            else:
                base_dict[key] = value

    def _save_config(self, section: str) -> tuple[bool, List[str]]:
        """Save configuration section to file"""
        errors = []

        # Determine filename
        config_files = {
            'audio': 'audio_config.yaml',
            'servers': 'servers.yaml',
            'detection': 'detection_config.yaml',
            'llm_providers': 'llm_providers.yaml',
            'app_profiles': 'app_profiles.yaml',
            'model_config': 'model_config.json'
        }

        filename = config_files.get(section, f"{section}.yaml")
        config_path = self.config_dir / filename

        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            with open(config_path, 'w', encoding='utf-8') as f:
                if filename.endswith('.yaml') or filename.endswith('.yml'):
                    yaml.dump(self.config_cache[section], f, default_flow_style=False, indent=2)
                else:
                    json.dump(self.config_cache[section], f, indent=2)

            logger.info(f"Saved config to {config_path}")

        except Exception as e:
            error_msg = f"Failed to save config to {config_path}: {e}"
            logger.error(error_msg)
            errors.append(error_msg)

        return len(errors) == 0, errors

    def reload_config(self, section: Optional[str] = None):
        """Reload configuration from files"""
        if section:
            config_files = {
                'audio': 'audio_config.yaml',
                'servers': 'servers.yaml',
                'detection': 'detection_config.yaml',
                'llm_providers': 'llm_providers.yaml',
                'app_profiles': 'app_profiles.yaml',
                'model_config': 'model_config.json'
            }
            filename = config_files.get(section, f"{section}.yaml")
            self._load_config(section, filename)
        else:
            self._load_all_configs()

    def get_all_configs(self) -> Dict[str, Any]:
        """Get all configurations"""
        return self.config_cache.copy()

    def validate_all_configs(self) -> Dict[str, List[str]]:
        """Validate all configuration sections"""
        validation_results = {}

        for section in self.config_cache:
            errors = self._validate_config_section(section, self.config_cache[section])
            validation_results[section] = errors

        return validation_results

    def reset_config(self, section: str) -> tuple[bool, List[str]]:
        """Reset configuration section to defaults"""
        defaults = self._get_default_config(section)
        if defaults is None:
            return False, [f"No default configuration available for section: {section}"]

        return self.update_config(section, defaults, validate=False)

    def _get_default_config(self, section: str) -> Optional[Dict[str, Any]]:
        """Get default configuration for a section"""
        defaults = {
            'audio': {
                'quality': {
                    'sample_rate': 48000,
                    'channels': 1,
                    'dtype': 'float32',
                    'blocksize': 2048,
                    'fallback_sample_rates': [44100, 48000, 32000, 24000, 16000]
                },
                'devices': {
                    'primary': {'name': 'default'},
                    'secondary': {'name': 'default'},
                    'auto_fallback': True,
                    'list_on_startup': True
                },
                'recording': {
                    'max_duration': 300,
                    'silence_threshold': 0.01,
                    'silence_duration': 2.0,
                    'format': 'wav'
                },
                'timeouts': {
                    'poll_timeout': 300,
                    'request_timeout': 120,
                    'upload_timeout': 60
                },
                'whisper': {
                    'target_sample_rate': 16000,
                    'keep_originals': True,
                    'originals_dir': 'recordings/originals',
                    'processed_dir': 'recordings/processed'
                }
            },
            'servers': {
                'services': {
                    'whisper': {
                        'host': 'localhost',
                        'port': 9880,
                        'protocol': 'http'
                    }
                }
            },
            'detection': {
                'vad_enabled': True,
                'vad_aggressiveness': 2,
                'silence_threshold': 0.01,
                'min_speech_duration': 0.1
            }
        }

        return defaults.get(section)