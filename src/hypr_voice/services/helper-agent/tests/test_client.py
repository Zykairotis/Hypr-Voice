"""
Tests for SGLang Client

This module contains tests for the SGLang client functionality.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock, patch, MagicMock

# Import the modules we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sglang_client import SGLangClient, SGLangConfig


class TestSGLangConfig:
    """Test SGLang configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SGLangConfig()

        assert config.host == "localhost"
        assert config.port == 30000
        assert config.model == "qwen3-1.7b"
        assert config.timeout == 30
        assert config.health_check_interval == 60
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SGLangConfig(
            host="example.com",
            port=8080,
            model="custom-model",
            timeout=60
        )

        assert config.host == "example.com"
        assert config.port == 8080
        assert config.model == "custom-model"
        assert config.timeout == 60


class TestSGLangClient:
    """Test SGLang client functionality."""

    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return SGLangConfig(host="localhost", port=30000, timeout=5)

    @pytest.fixture
    def client(self, config):
        """Create test client."""
        return SGLangClient(config)

    @pytest.mark.asyncio
    async def test_initialize(self, client):
        """Test client initialization."""
        assert client.session is None

        await client.initialize()

        assert client.session is not None
        assert isinstance(client.session, aiohttp.ClientSession)

        await client.cleanup()
        assert client.session is None

    @pytest.mark.asyncio
    async def test_context_manager(self, config):
        """Test async context manager."""
        async with SGLangClient(config) as client:
            assert client.session is not None

        # Session should be cleaned up after context
        assert client.session is None

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_health_check_success(self, mock_get, client):
        """Test successful health check."""
        # Mock successful health check response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_get.return_value.__aenter__.return_value = mock_response

        await client.initialize()

        result = await client.health_check()

        assert result is True
        assert client.is_healthy is True
        assert client.last_health_check > 0

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    @patch('aiohttp.ClientSession.post')
    async def test_health_check_with_generation(self, mock_post, mock_get, client):
        """Test health check using text generation fallback."""
        # Mock failed health endpoints
        mock_response = AsyncMock()
        mock_response.status = 404
        mock_get.return_value.__aenter__.return_value = mock_response

        # Mock successful generation
        mock_gen_response = AsyncMock()
        mock_gen_response.status = 200
        mock_post.return_value.__aenter__.return_value = mock_gen_response

        await client.initialize()

        result = await client.health_check()

        assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, client):
        """Test failed health check."""
        # Don't initialize session to simulate failure
        result = await client.health_check()

        assert result is False
        assert client.is_healthy is False

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_generate_text_success(self, mock_post, client):
        """Test successful text generation."""
        # Mock successful generation response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"text": "Generated text"})
        mock_post.return_value.__aenter__.return_value = mock_response

        await client.initialize()

        result = await client.generate_text("Test prompt")

        assert result == "Generated text"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_generate_text_different_response_formats(self, mock_post, client):
        """Test text generation with different response formats."""
        await client.initialize()

        # Test choices format
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"choices": [{"text": "Choice text"}]})
        mock_post.return_value.__aenter__.return_value = mock_response

        result = await client.generate_text("Test prompt")
        assert result == "Choice text"

        # Test output format
        mock_response.json = AsyncMock(return_value={"output": "Output text"})
        result = await client.generate_text("Test prompt")
        assert result == "Output text"

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_generate_text_with_parameters(self, mock_post, client):
        """Test text generation with custom parameters."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"text": "Generated text"})
        mock_post.return_value.__aenter__.return_value = mock_response

        await client.initialize()

        result = await client.generate_text(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.5,
            top_p=0.8,
            stop_sequences=["STOP"]
        )

        assert result == "Generated text"

        # Check that parameters were passed correctly
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        payload = call_args.kwargs["json"]
        assert payload["text"] == "Test prompt"
        assert payload["sampling_params"]["max_new_tokens"] == 100
        assert payload["sampling_params"]["temperature"] == 0.5
        assert payload["sampling_params"]["top_p"] == 0.8
        assert payload["sampling_params"]["stop"] == ["STOP"]

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_generate_text_retry(self, mock_post, client):
        """Test text generation with retry logic."""
        # Mock first failure, then success
        mock_response_fail = AsyncMock()
        mock_response_fail.status = 500

        mock_response_success = AsyncMock()
        mock_response_success.status = 200
        mock_response_success.json = AsyncMock(return_value={"text": "Success after retry"})

        mock_post.return_value.__aenter__.side_effect = [
            mock_response_fail,
            mock_response_success
        ]

        await client.initialize()

        result = await client.generate_text("Test prompt")

        assert result == "Success after retry"
        assert mock_post.call_count == 2

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_generate_text_failure(self, mock_post, client):
        """Test text generation failure."""
        # Mock failed response
        mock_response = AsyncMock()
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response

        await client.initialize()

        result = await client.generate_text("Test prompt")

        assert result is None

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_chat_completion(self, mock_post, client):
        """Test chat completion."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"text": "Chat response"})
        mock_post.return_value.__aenter__.return_value = mock_response

        await client.initialize()

        messages = [
            {"role": "system", "content": "You are a helpful assistant"},
            {"role": "user", "content": "Hello"}
        ]

        result = await client.chat_completion(messages)

        assert result == "Chat response"
        mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_completion_message_formatting(self, client):
        """Test that chat completion formats messages correctly."""
        # This tests the internal _format_messages_as_prompt method
        messages = [
            {"role": "system", "content": "System message"},
            {"role": "user", "content": "User message"},
            {"role": "assistant", "content": "Assistant message"}
        ]

        formatted_prompt = client._format_messages_as_prompt(messages)

        # Check that all roles are included
        assert "System message" in formatted_prompt
        assert "User message" in formatted_prompt
        assert "Assistant message" in formatted_prompt

    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.get')
    async def test_get_model_info(self, mock_get, client):
        """Test getting model information."""
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            "model_name": "qwen3-1.7b",
            "model_size": "1.7B"
        })
        mock_get.return_value.__aenter__.return_value = mock_response

        await client.initialize()

        result = await client.get_model_info()

        assert result is not None
        assert result["model_name"] == "qwen3-1.7b"
        assert result["model_size"] == "1.7B"

    @pytest.mark.asyncio
    async def test_get_model_info_failure(self, client):
        """Test getting model information when it fails."""
        await client.initialize()

        result = await client.get_model_info()

        assert result is None


@pytest.mark.asyncio
async def test_create_sglang_client():
    """Test the factory function for creating SGLang client."""
    with patch('sglang_client.SGLangClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        from sglang_client import create_sglang_client

        result = await create_sglang_client()

        mock_client.initialize.assert_called_once()
        assert result == mock_client


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])