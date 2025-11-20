"""
Main Helper Agent Implementation

This module provides the main helper agent class that coordinates all capabilities
including summarization, analysis, planning, and Claude Code SDK integration.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from .sglang_client import SGLangClient
from .config_loader import get_config, get_prompts, reload_config
from .tools.summarization import SummarizationTools
from .tools.analysis import AnalysisTools
from .tools.planning import PlanningTools
from .tools.claude_bridge import ClaudeSDKBridge

logger = logging.getLogger(__name__)


class HelperAgent:
    """
    Main helper agent that provides intelligent assistance capabilities.

    This agent coordinates various tools and capabilities to assist with
    topic summarization, content analysis, task planning, and Claude Code SDK integration.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the helper agent.

        Args:
            config: Optional configuration dictionary, uses default if not provided.
        """
        self.config = get_config()
        self.prompts = get_prompts()

        # Override config if provided
        if config:
            self._update_config(config)

        # Initialize SGLang client
        self.sglang_client = SGLangClient(self.config.sglang)

        # Initialize tool modules
        self.summarization_tools = SummarizationTools(self.sglang_client, self.prompts)
        self.analysis_tools = AnalysisTools(self.sglang_client, self.prompts)
        self.planning_tools = PlanningTools(self.sglang_client, self.prompts)
        self.claude_bridge = ClaudeSDKBridge(self.sglang_client, self.prompts)

        self.is_initialized = False
        self.stats = {
            "requests_processed": 0,
            "total_tokens_generated": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

    async def initialize(self):
        """Initialize the helper agent and its components."""
        try:
            if not self.is_initialized:
                await self.sglang_client.initialize()

                # Verify SGLang service is healthy
                if await self.sglang_client.health_check():
                    logger.info("Helper agent initialized successfully")
                    self.is_initialized = True
                else:
                    logger.error("SGLang service is not healthy")
                    raise RuntimeError("SGLang service initialization failed")

        except Exception as e:
            logger.error(f"Failed to initialize helper agent: {e}")
            raise

    async def cleanup(self):
        """Cleanup helper agent resources."""
        try:
            await self.sglang_client.cleanup()
            self.is_initialized = False
            logger.info("Helper agent cleaned up")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def _update_config(self, config: Dict[str, Any]):
        """Update configuration with provided values."""
        if "enabled" in config:
            self.config.enabled = config["enabled"]

        if "sglang" in config:
            sglang_config = config["sglang"]
            for key, value in sglang_config.items():
                if hasattr(self.config.sglang, key):
                    setattr(self.config.sglang, key, value)

        if "capabilities" in config:
            self.config.capabilities.update(config["capabilities"])

    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all components.

        Returns:
            Dictionary containing health status of all components.
        """
        health_status = {
            "agent_healthy": self.is_initialized,
            "sglang_healthy": False,
            "capabilities": {},
            "stats": self.stats,
            "timestamp": datetime.now().isoformat()
        }

        try:
            # Check SGLang client
            if self.sglang_client:
                health_status["sglang_healthy"] = await self.sglang_client.health_check()

            # Check capabilities
            for capability, config in self.config.capabilities.items():
                health_status["capabilities"][capability] = {
                    "enabled": config.get("enabled", False),
                    "healthy": True  # TODO: Implement capability-specific health checks
                }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_status["error"] = str(e)

        return health_status

    async def summarize_text(
        self,
        text: str,
        max_length: Optional[int] = None,
        focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Summarize the given text for voice agent consumption.

        Args:
            text: Text to summarize
            max_length: Maximum summary length
            focus: Specific focus area for summarization

        Returns:
            Dictionary containing summary and metadata.
        """
        if not self.is_initialized:
            await self.initialize()

        if not self.config.capabilities.get("summarization", {}).get("enabled", False):
            return {"error": "Summarization capability is disabled"}

        try:
            self.stats["requests_processed"] += 1

            result = await self.summarization_tools.summarize_text(
                text=text,
                max_length=max_length or self.config.capabilities["summarization"]["max_length"],
                focus=focus
            )

            if "error" not in result:
                self.stats["total_tokens_generated"] += result.get("tokens_used", 0)

            return result

        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            self.stats["errors"] += 1
            return {"error": f"Summarization failed: {str(e)}"}

    async def analyze_content(
        self,
        content: str,
        optimize_for_voice: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Analyze content for voice agent optimization.

        Args:
            content: Content to analyze
            optimize_for_voice: Whether to optimize for voice output

        Returns:
            Dictionary containing analysis and recommendations.
        """
        if not self.is_initialized:
            await self.initialize()

        if not self.config.capabilities.get("analysis", {}).get("enabled", False):
            return {"error": "Analysis capability is disabled"}

        try:
            self.stats["requests_processed"] += 1

            result = await self.analysis_tools.analyze_content(
                content=content,
                optimize_for_voice=optimize_for_voice or
                self.config.capabilities["analysis"].get("optimize_for_voice", True)
            )

            if "error" not in result:
                self.stats["total_tokens_generated"] += result.get("tokens_used", 0)

            return result

        except Exception as e:
            logger.error(f"Content analysis failed: {e}")
            self.stats["errors"] += 1
            return {"error": f"Content analysis failed: {str(e)}"}

    async def plan_task(
        self,
        task: str,
        max_steps: Optional[int] = None,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Break down a task into actionable steps.

        Args:
            task: Task to break down
            max_steps: Maximum number of steps
            context: Additional context for planning

        Returns:
            Dictionary containing task plan and steps.
        """
        if not self.is_initialized:
            await self.initialize()

        if not self.config.capabilities.get("planning", {}).get("enabled", False):
            return {"error": "Planning capability is disabled"}

        try:
            self.stats["requests_processed"] += 1

            result = await self.planning_tools.plan_task(
                task=task,
                max_steps=max_steps or self.config.capabilities["planning"]["max_tasks"],
                context=context
            )

            if "error" not in result:
                self.stats["total_tokens_generated"] += result.get("tokens_used", 0)

            return result

        except Exception as e:
            logger.error(f"Task planning failed: {e}")
            self.stats["errors"] += 1
            return {"error": f"Task planning failed: {str(e)}"}

    async def bridge_to_claude_sdk(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        voice_optimized: bool = True
    ) -> Dict[str, Any]:
        """
        Bridge request to Claude Code SDK with context awareness.

        Args:
            request: Request to process
            context: Additional context for the request
            voice_optimized: Whether to optimize response for voice output

        Returns:
            Dictionary containing processed response.
        """
        if not self.is_initialized:
            await self.initialize()

        if not self.config.capabilities.get("claude_sdk_bridge", {}).get("enabled", False):
            return {"error": "Claude SDK bridge capability is disabled"}

        try:
            self.stats["requests_processed"] += 1

            result = await self.claude_bridge.process_request(
                request=request,
                context=context or {},
                voice_optimized=voice_optimized
            )

            if "error" not in result:
                self.stats["total_tokens_generated"] += result.get("tokens_used", 0)

            return result

        except Exception as e:
            logger.error(f"Claude SDK bridge failed: {e}")
            self.stats["errors"] += 1
            return {"error": f"Claude SDK bridge failed: {str(e)}"}

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get helper agent statistics.

        Returns:
            Dictionary containing usage statistics.
        """
        uptime = datetime.now() - self.stats["start_time"]

        return {
            **self.stats,
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split(".")[0],  # Remove microseconds
            "average_tokens_per_request": (
                self.stats["total_tokens_generated"] / max(self.stats["requests_processed"], 1)
            ),
            "error_rate": (
                self.stats["errors"] / max(self.stats["requests_processed"], 1) * 100
            )
        }

    async def reload_configuration(self):
        """Reload configuration from files."""
        try:
            reload_config()
            self.config = get_config()
            self.prompts = get_prompts()

            # Reinitialize tools with new configuration
            self.summarization_tools = SummarizationTools(self.sglang_client, self.prompts)
            self.analysis_tools = AnalysisTools(self.sglang_client, self.prompts)
            self.planning_tools = PlanningTools(self.sglang_client, self.prompts)
            self.claude_bridge = ClaudeSDKBridge(self.sglang_client, self.prompts)

            logger.info("Helper agent configuration reloaded successfully")

        except Exception as e:
            logger.error(f"Failed to reload configuration: {e}")
            raise


# Factory function for easy agent creation
async def create_helper_agent(config: Optional[Dict[str, Any]] = None) -> HelperAgent:
    """
    Create and initialize a helper agent.

    Args:
        config: Optional configuration dictionary

    Returns:
        Initialized helper agent
    """
    agent = HelperAgent(config)
    await agent.initialize()
    return agent