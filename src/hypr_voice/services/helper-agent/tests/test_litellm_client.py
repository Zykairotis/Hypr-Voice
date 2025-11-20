"""
Tests for LiteLLM Client

Run with: pytest test_litellm_client.py
"""

import pytest
import asyncio
from pathlib import Path

try:
    from ..litellm_client import LiteLLMClient
    from ..config_loader import get_config_loader
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from litellm_client import LiteLLMClient
    from config_loader import get_config_loader


class TestLiteLLMClient:
    """Test cases for LiteLLM client."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        client = LiteLLMClient()
        await client.initialize()
        yield client
        await client.cleanup()
    
    @pytest.mark.asyncio
    async def test_client_initialization(self, client):
        """Test client initialization."""
        assert client is not None
        assert len(client.providers) > 0
        assert client.litellm_client is not None
    
    @pytest.mark.asyncio
    async def test_provider_selection(self, client):
        """Test provider selection."""
        provider, model = client._get_provider_model()
        assert provider is not None
        assert model is not None
        assert provider in client.providers
    
    @pytest.mark.asyncio
    async def test_list_providers(self, client):
        """Test listing providers."""
        providers = client.list_providers()
        assert isinstance(providers, list)
        assert len(providers) > 0
    
    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """Test listing models."""
        models = client.list_models()
        assert isinstance(models, dict)
    
    @pytest.mark.asyncio
    async def test_get_metrics(self, client):
        """Test metrics retrieval."""
        metrics = client.get_metrics()
        assert isinstance(metrics, dict)
        assert "total_cost" in metrics
        assert "providers" in metrics
    
    # Note: Actual completion tests require API keys
    @pytest.mark.skip(reason="Requires API keys")
    @pytest.mark.asyncio
    async def test_chat_completion(self, client):
        """Test chat completion."""
        messages = [{"role": "user", "content": "Hello!"}]
        response = await client.chat(messages, max_tokens=50)
        assert "content" in response
        assert response["content"] != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

