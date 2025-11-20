"""
Configuration Loader for Helper Agent

This module handles loading and managing configuration for the helper agent service.
"""

import yaml
import logging
import os
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from .sglang_client import SGLangConfig

logger = logging.getLogger(__name__)


@dataclass
class HelperAgentConfig:
    """Configuration for the helper agent service."""
    enabled: bool = True
    sglang: SGLangConfig = None
    capabilities: Dict[str, Any] = None

    def __post_init__(self):
        if self.sglang is None:
            self.sglang = SGLangConfig()
        if self.capabilities is None:
            self.capabilities = {
                "summarization": {
                    "enabled": True,
                    "max_length": 500,
                    "temperature": 0.3
                },
                "analysis": {
                    "enabled": True,
                    "optimize_for_voice": True,
                    "temperature": 0.5
                },
                "planning": {
                    "enabled": True,
                    "max_tasks": 10,
                    "temperature": 0.7
                },
                "claude_sdk_bridge": {
                    "enabled": True,
                    "context_aware": True,
                    "timeout": 30
                }
            }


class ConfigLoader:
    """
    Configuration loader for helper agent service.

    Handles loading configuration from YAML files and environment variables.
    """

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            # Default to the config directory within the helper-agent folder
            config_dir = Path(__file__).parent / "config"

        self.config_dir = Path(config_dir)
        self.main_config_path = self.config_dir / "helper_agent.yaml"
        self.prompts_config_path = self.config_dir / "prompts.yaml"
        self.providers_config_path = self.config_dir / "providers.yaml"
        self.mcp_tools_config_path = self.config_dir / "mcp_tools.yaml"
        self.agent_config_path = self.config_dir / "agent_config.yaml"

    def load_config(self) -> HelperAgentConfig:
        """
        Load helper agent configuration from file.

        Returns:
            HelperAgentConfig object with loaded settings.
        """
        try:
            # Load main configuration
            config_data = {}
            if self.main_config_path.exists():
                with open(self.main_config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f) or {}
            else:
                logger.warning(f"Main config file not found: {self.main_config_path}")
                logger.info("Using default configuration")

            # Extract SGLang configuration
            sglang_data = config_data.get("sglang", {})
            sglang_config = SGLangConfig(
                host=sglang_data.get("host", "localhost"),
                port=sglang_data.get("port", 30000),
                model=sglang_data.get("model", "qwen3-1.7b"),
                timeout=sglang_data.get("timeout", 30),
                health_check_interval=sglang_data.get("health_check_interval", 60),
                max_retries=sglang_data.get("max_retries", 3),
                retry_delay=sglang_data.get("retry_delay", 1.0)
            )

            # Override with environment variables
            sglang_config.host = os.getenv("HELPER_AGENT_SGLANG_HOST", sglang_config.host)
            sglang_config.port = int(os.getenv("HELPER_AGENT_SGLANG_PORT", sglang_config.port))
            sglang_config.model = os.getenv("HELPER_AGENT_SGLANG_MODEL", sglang_config.model)

            # Create main configuration
            helper_config = HelperAgentConfig(
                enabled=config_data.get("enabled", True),
                sglang=sglang_config,
                capabilities=config_data.get("capabilities", {})
            )

            logger.info(f"Configuration loaded from {self.main_config_path}")
            return helper_config

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            logger.info("Using default configuration")
            return HelperAgentConfig()

    def load_prompts(self) -> Dict[str, Any]:
        """
        Load prompts configuration from file.

        Returns:
            Dictionary containing prompt templates.
        """
        try:
            if self.prompts_config_path.exists():
                with open(self.prompts_config_path, 'r', encoding='utf-8') as f:
                    prompts = yaml.safe_load(f) or {}
                logger.info(f"Prompts loaded from {self.prompts_config_path}")
                return prompts
            else:
                logger.warning(f"Prompts config file not found: {self.prompts_config_path}")
                return self._get_default_prompts()

        except Exception as e:
            logger.error(f"Failed to load prompts: {e}")
            return self._get_default_prompts()

    def _get_default_prompts(self) -> Dict[str, Any]:
        """
        Get default prompt templates.

        Returns:
            Dictionary containing default prompt templates.
        """
        return {
            "summarization": {
                "system": "You are a helpful assistant that creates concise, accurate summaries.",
                "user_template": "Please summarize the following text for a voice agent application:\n\n{text}\n\nSummary:"
            },
            "analysis": {
                "system": "You are a content analysis expert specializing in optimizing text for voice output.",
                "user_template": "Analyze the following content and provide insights for voice agent optimization:\n\n{text}\n\nAnalysis:"
            },
            "planning": {
                "system": "You are a task planning expert that breaks down complex tasks into actionable steps.",
                "user_template": "Break down the following task into clear, actionable steps for voice workflow:\n\n{task}\n\nPlan:"
            },
            "claude_bridge": {
                "system": "You are a bridge between voice systems and Claude Code SDK, providing context-aware assistance.",
                "user_template": "Context: {context}\n\nUser request: {request}\n\nProvide assistance:"
            }
        }

    def save_config(self, config: HelperAgentConfig):
        """
        Save configuration to file.

        Args:
            config: HelperAgentConfig object to save.
        """
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Convert configuration to dictionary
            config_dict = {
                "enabled": config.enabled,
                "sglang": asdict(config.sglang),
                "capabilities": config.capabilities
            }

            # Save to file
            with open(self.main_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {self.main_config_path}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def save_prompts(self, prompts: Dict[str, Any]):
        """
        Save prompts configuration to file.

        Args:
            prompts: Dictionary containing prompt templates.
        """
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(self.prompts_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(prompts, f, default_flow_style=False, indent=2)

            logger.info(f"Prompts saved to {self.prompts_config_path}")

        except Exception as e:
            logger.error(f"Failed to save prompts: {e}")
    
    def load_providers_config(self) -> Dict[str, Any]:
        """
        Load providers configuration from file.
        
        Returns:
            Dictionary containing provider configurations.
        """
        try:
            if self.providers_config_path.exists():
                with open(self.providers_config_path, 'r', encoding='utf-8') as f:
                    providers = yaml.safe_load(f) or {}
                logger.info(f"Providers config loaded from {self.providers_config_path}")
                return providers
            else:
                logger.warning(f"Providers config file not found: {self.providers_config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load providers config: {e}")
            return {}
    
    def load_mcp_tools_config(self) -> Dict[str, Any]:
        """
        Load MCP tools configuration from file.
        
        Returns:
            Dictionary containing MCP tool configurations.
        """
        try:
            if self.mcp_tools_config_path.exists():
                with open(self.mcp_tools_config_path, 'r', encoding='utf-8') as f:
                    mcp_tools = yaml.safe_load(f) or {}
                logger.info(f"MCP tools config loaded from {self.mcp_tools_config_path}")
                return mcp_tools
            else:
                logger.warning(f"MCP tools config file not found: {self.mcp_tools_config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load MCP tools config: {e}")
            return {}
    
    def load_agent_config(self) -> Dict[str, Any]:
        """
        Load agent configuration from file.
        
        Returns:
            Dictionary containing agent configurations.
        """
        try:
            if self.agent_config_path.exists():
                with open(self.agent_config_path, 'r', encoding='utf-8') as f:
                    agent_config = yaml.safe_load(f) or {}
                logger.info(f"Agent config loaded from {self.agent_config_path}")
                return agent_config
            else:
                logger.warning(f"Agent config file not found: {self.agent_config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            return {}


# Global configuration instance
_config_loader: Optional[ConfigLoader] = None
_config: Optional[HelperAgentConfig] = None
_prompts: Optional[Dict[str, Any]] = None


def get_config_loader() -> ConfigLoader:
    """Get the global configuration loader instance."""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


def get_config() -> HelperAgentConfig:
    """Get the global helper agent configuration."""
    global _config
    if _config is None:
        _config = get_config_loader().load_config()
    return _config


def get_prompts() -> Dict[str, Any]:
    """Get the global prompts configuration."""
    global _prompts
    if _prompts is None:
        _prompts = get_config_loader().load_prompts()
    return _prompts


def reload_config():
    """Reload configuration from files."""
    global _config, _prompts
    _config = None
    _prompts = None
    logger.info("Configuration reloaded")