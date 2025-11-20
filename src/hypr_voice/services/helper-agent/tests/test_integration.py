"""
Integration Tests for Helper Agent

This module contains integration tests for the helper agent service.
"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helper_agent import HelperAgent
from config_loader import ConfigLoader


class TestConfigLoader:
    """Test configuration loading."""

    @pytest.fixture
    def config_dir(self, tmp_path):
        """Create temporary config directory."""
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        return config_dir

    def test_load_default_config(self, config_dir):
        """Test loading default configuration when no file exists."""
        loader = ConfigLoader(config_dir)
        config = loader.load_config()

        assert config.enabled is True
        assert config.sglang.host == "localhost"
        assert config.sglang.port == 30000
        assert "summarization" in config.capabilities
        assert "analysis" in config.capabilities

    def test_load_config_from_file(self, config_dir):
        """Test loading configuration from file."""
        # Create test config file
        config_data = {
            "enabled": False,
            "sglang": {
                "host": "example.com",
                "port": 8080
            },
            "capabilities": {
                "summarization": {
                    "enabled": False,
                    "max_length": 200
                }
            }
        }

        config_file = config_dir / "helper_agent.yaml"
        with open(config_file, 'w') as f:
            import yaml
            yaml.dump(config_data, f)

        loader = ConfigLoader(config_dir)
        config = loader.load_config()

        assert config.enabled is False
        assert config.sglang.host == "example.com"
        assert config.sglang.port == 8080
        assert config.capabilities["summarization"]["enabled"] is False
        assert config.capabilities["summarization"]["max_length"] == 200

    def test_load_prompts_default(self, config_dir):
        """Test loading default prompts."""
        loader = ConfigLoader(config_dir)
        prompts = loader.load_prompts()

        assert "summarization" in prompts
        assert "analysis" in prompts
        assert "planning" in prompts
        assert "claude_bridge" in prompts

    def test_environment_override(self, config_dir):
        """Test environment variable override."""
        # Set environment variable
        os.environ["HELPER_AGENT_SGLANG_HOST"] = "env-host"
        os.environ["HELPER_AGENT_SGLANG_PORT"] = "9999"

        try:
            loader = ConfigLoader(config_dir)
            config = loader.load_config()

            assert config.sglang.host == "env-host"
            assert config.sglang.port == 9999
        finally:
            # Clean up environment variables
            os.environ.pop("HELPER_AGENT_SGLANG_HOST", None)
            os.environ.pop("HELPER_AGENT_SGLANG_PORT", None)


class TestHelperAgentIntegration:
    """Test helper agent integration."""

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        from config_loader import HelperAgentConfig, SGLangConfig
        return HelperAgentConfig(
            sglang=SGLangConfig(host="localhost", port=30000, timeout=5)
        )

    @pytest.fixture
    def agent(self, mock_config):
        """Create test agent with mocked dependencies."""
        with patch('helper_agent.SGLangClient') as mock_client:
            agent = HelperAgent()
            agent.sglang_client = mock_client.return_value
            return agent

    @pytest.mark.asyncio
    async def test_initialize_success(self, agent):
        """Test successful agent initialization."""
        # Mock successful health check
        agent.sglang_client.initialize = AsyncMock()
        agent.sglang_client.health_check = AsyncMock(return_value=True)

        await agent.initialize()

        assert agent.is_initialized is True
        agent.sglang_client.initialize.assert_called_once()
        agent.sglang_client.health_check.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_failure(self, agent):
        """Test agent initialization failure."""
        # Mock failed health check
        agent.sglang_client.initialize = AsyncMock()
        agent.sglang_client.health_check = AsyncMock(return_value=False)

        with pytest.raises(RuntimeError):
            await agent.initialize()

        assert agent.is_initialized is False

    @pytest.mark.asyncio
    async def test_summarize_text(self, agent):
        """Test text summarization."""
        # Mock dependencies
        agent.is_initialized = True
        agent.summarization_tools.summarize_text = AsyncMock(return_value={
            "summary": "Test summary",
            "original_length": 100,
            "summary_length": 20,
            "tokens_used": 15
        })

        result = await agent.summarize_text("Test text", max_length=50)

        assert result["summary"] == "Test summary"
        assert result["original_length"] == 100
        assert result["summary_length"] == 20
        assert result["tokens_used"] == 15

        # Check that stats were updated
        assert agent.stats["requests_processed"] == 1
        assert agent.stats["total_tokens_generated"] == 15

    @pytest.mark.asyncio
    async def test_summarize_text_disabled(self, agent):
        """Test summarization when capability is disabled."""
        agent.is_initialized = True
        agent.config.capabilities["summarization"]["enabled"] = False

        result = await agent.summarize_text("Test text")

        assert "error" in result
        assert "disabled" in result["error"]

    @pytest.mark.asyncio
    async def test_analyze_content(self, agent):
        """Test content analysis."""
        agent.is_initialized = True
        agent.analysis_tools.analyze_content = AsyncMock(return_value={
            "analysis": {"overall_assessment": "Good content"},
            "metrics": {"word_count": 50},
            "voice_optimization": {"status": "optimal"},
            "tokens_used": 20
        })

        result = await agent.analyze_content("Test content")

        assert result["analysis"]["overall_assessment"] == "Good content"
        assert result["metrics"]["word_count"] == 50
        assert result["voice_optimization"]["status"] == "optimal"

    @pytest.mark.asyncio
    async def test_plan_task(self, agent):
        """Test task planning."""
        agent.is_initialized = True
        agent.planning_tools.plan_task = AsyncMock(return_value={
            "steps": [
                {"step_number": 1, "description": "First step"},
                {"step_number": 2, "description": "Second step"}
            ],
            "total_steps": 2,
            "original_task": "Test task",
            "tokens_used": 25
        })

        result = await agent.plan_task("Test task")

        assert len(result["steps"]) == 2
        assert result["total_steps"] == 2
        assert result["original_task"] == "Test task"

    @pytest.mark.asyncio
    async def test_bridge_to_claude_sdk(self, agent):
        """Test Claude SDK bridge."""
        agent.is_initialized = True
        agent.claude_bridge.process_request = AsyncMock(return_value={
            "response": "Claude response",
            "actions": ["Action 1", "Action 2"],
            "claude_instructions": ["Instruction 1"],
            "tokens_used": 30
        })

        result = await agent.bridge_to_claude_sdk(
            request="Test request",
            context={"app": "test"}
        )

        assert result["response"] == "Claude response"
        assert len(result["actions"]) == 2
        assert len(result["claude_instructions"]) == 1

    @pytest.mark.asyncio
    async def test_health_check(self, agent):
        """Test health check."""
        agent.is_initialized = True
        agent.sglang_client.health_check = AsyncMock(return_value=True)

        result = await agent.health_check()

        assert result["agent_healthy"] is True
        assert result["sglang_healthy"] is True
        assert "capabilities" in result
        assert "stats" in result

    @pytest.mark.asyncio
    async def test_get_stats(self, agent):
        """Test getting statistics."""
        # Set some initial stats
        agent.stats = {
            "requests_processed": 10,
            "total_tokens_generated": 500,
            "errors": 1,
            "start_time": agent.stats["start_time"]
        }

        result = await agent.get_stats()

        assert result["requests_processed"] == 10
        assert result["total_tokens_generated"] == 500
        assert result["errors"] == 1
        assert "uptime_seconds" in result
        assert "average_tokens_per_request" in result
        assert "error_rate" in result

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_config):
        """Test async context manager."""
        with patch('helper_agent.SGLangClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value = mock_client_instance
            mock_client_instance.health_check = AsyncMock(return_value=True)

            async with HelperAgent(mock_config.__dict__) as agent:
                assert agent.is_initialized is True

            # Should be cleaned up after context
            mock_client_instance.cleanup.assert_called_once()


class TestHelperAgentErrorHandling:
    """Test error handling in helper agent."""

    @pytest.fixture
    def agent(self):
        """Create test agent."""
        with patch('helper_agent.SGLangClient'):
            agent = HelperAgent()
            agent.sglang_client = AsyncMock()
            return agent

    @pytest.mark.asyncio
    async def test_summarize_text_error(self, agent):
        """Test error handling in summarization."""
        agent.is_initialized = True
        agent.summarization_tools.summarize_text = AsyncMock(
            side_effect=Exception("Test error")
        )

        result = await agent.summarize_text("Test text")

        assert "error" in result
        assert "Test error" in result["error"]

        # Check that error stats were updated
        assert agent.stats["errors"] == 1

    @pytest.mark.asyncio
    async def test_analyze_content_error(self, agent):
        """Test error handling in content analysis."""
        agent.is_initialized = True
        agent.analysis_tools.analyze_content = AsyncMock(
            side_effect=Exception("Analysis error")
        )

        result = await agent.analyze_content("Test content")

        assert "error" in result
        assert "Analysis error" in result["error"]

    @pytest.mark.asyncio
    async def test_plan_task_error(self, agent):
        """Test error handling in task planning."""
        agent.is_initialized = True
        agent.planning_tools.plan_task = AsyncMock(
            side_effect=Exception("Planning error")
        )

        result = await agent.plan_task("Test task")

        assert "error" in result
        assert "Planning error" in result["error"]

    @pytest.mark.asyncio
    async def test_bridge_error(self, agent):
        """Test error handling in Claude SDK bridge."""
        agent.is_initialized = True
        agent.claude_bridge.process_request = AsyncMock(
            side_effect=Exception("Bridge error")
        )

        result = await agent.bridge_to_claude_sdk("Test request")

        assert "error" in result
        assert "Bridge error" in result["error"]

    @pytest.mark.asyncio
    async def test_empty_input_handling(self, agent):
        """Test handling of empty inputs."""
        agent.is_initialized = True

        # Test empty text
        result = await agent.summarize_text("")
        assert "error" in result
        assert "No text provided" in result["error"]

        result = await agent.analyze_content("")
        assert "error" in result
        assert "No content provided" in result["error"]

        result = await agent.plan_task("")
        assert "error" in result
        assert "No task provided" in result["error"]


class TestHelperAgentConfiguration:
    """Test helper agent configuration."""

    def test_config_override(self):
        """Test configuration override."""
        custom_config = {
            "enabled": False,
            "sglang": {
                "host": "custom-host",
                "port": 9999
            },
            "capabilities": {
                "summarization": {
                    "enabled": False,
                    "max_length": 100
                }
            }
        }

        with patch('helper_agent.SGLangClient'):
            agent = HelperAgent(custom_config)

            assert agent.config.enabled is False
            assert agent.config.sglang.host == "custom-host"
            assert agent.config.sglang.port == 9999
            assert agent.config.capabilities["summarization"]["enabled"] is False
            assert agent.config.capabilities["summarization"]["max_length"] == 100


@pytest.mark.asyncio
async def test_create_helper_agent():
    """Test the factory function for creating helper agent."""
    with patch('helper_agent.HelperAgent') as mock_agent_class:
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent

        from helper_agent import create_helper_agent

        result = await create_helper_agent()

        mock_agent.initialize.assert_called_once()
        assert result == mock_agent


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])