"""
LangChain Model Factory for Helper Agent

This module creates LangChain chat models backed by LiteLLM, enabling multi-provider
routing with intelligent selection, rate limiting, and cost tracking.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path

try:
    from langchain_community.chat_models import ChatLiteLLM
    from langchain_core.callbacks import BaseCallbackHandler
    from langchain_core.messages import BaseMessage
    from langchain_core.outputs import LLMResult
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain not available. Install with: pip install langchain langchain-community")

from .litellm_client import LiteLLMClient, ProviderConfig, ProviderMetrics
from .config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class ProviderMetricsCallback(BaseCallbackHandler):
    """Callback handler to track provider metrics from LangChain calls."""
    
    def __init__(self, metrics_tracker: Callable[[str, bool, float, int, float], None]):
        """
        Initialize callback handler.
        
        Args:
            metrics_tracker: Function to call with (provider, success, latency, tokens, cost)
        """
        super().__init__()
        self.metrics_tracker = metrics_tracker
        self.start_time = None
        self.provider = None
        self.model = None
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts."""
        import time
        self.start_time = time.time()
        # Extract provider and model from kwargs if available
        self.provider = kwargs.get("invocation_params", {}).get("model", "unknown").split("/")[0]
        self.model = kwargs.get("invocation_params", {}).get("model", "unknown")
    
    def on_llm_end(self, response: LLMResult, **kwargs) -> None:
        """Called when LLM ends successfully."""
        import time
        latency = time.time() - self.start_time if self.start_time else 0.0
        
        # Extract token usage
        tokens = 0
        if response.llm_output and "token_usage" in response.llm_output:
            usage = response.llm_output["token_usage"]
            tokens = usage.get("total_tokens", 0)
        
        # Track metrics (cost calculation happens in tracker)
        if self.metrics_tracker and self.provider:
            self.metrics_tracker(self.provider, True, latency, tokens, 0.0)
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        """Called when LLM errors."""
        import time
        latency = time.time() - self.start_time if self.start_time else 0.0
        
        if self.metrics_tracker and self.provider:
            self.metrics_tracker(self.provider, False, latency, 0, 0.0)


class ModelFactory:
    """
    Factory for creating LangChain chat models backed by LiteLLM.
    
    Features:
    - Multi-provider support via LiteLLM
    - Intelligent provider selection
    - Cost and usage tracking
    - Automatic fallback and rotation
    - LangChain-compatible chat models
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the model factory.
        
        Args:
            config_path: Path to providers.yaml configuration file
        """
        if not LANGCHAIN_AVAILABLE:
            raise ImportError("LangChain is required but not installed")
        
        # Initialize LiteLLM client for provider management
        self.litellm_client = LiteLLMClient(config_path)
        
        # Load configuration
        self.config_loader = ConfigLoader()
        self.provider_config = self.config_loader.load_providers_config()
        
        # Track created models
        self.active_models: Dict[str, ChatLiteLLM] = {}
        
        logger.info("Model factory initialized with %d providers", 
                   len(self.litellm_client.providers))
    
    async def initialize(self):
        """Initialize async components."""
        await self.litellm_client.initialize()
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.litellm_client.cleanup()
        self.active_models.clear()
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
    
    def create_chat_model(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        streaming: bool = False,
        callbacks: Optional[List[BaseCallbackHandler]] = None,
        **kwargs
    ) -> ChatLiteLLM:
        """
        Create a LangChain chat model with LiteLLM backend.
        
        Args:
            provider: Provider name (auto-selected if None)
            model: Model name (uses provider default if None)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            streaming: Enable streaming responses
            callbacks: LangChain callback handlers
            **kwargs: Additional model parameters
            
        Returns:
            ChatLiteLLM instance configured for the selected provider
        """
        # Select provider and model
        selected_provider, selected_model = self.litellm_client._get_provider_model(
            provider, model
        )
        
        # Get provider configuration
        prov_config = self.litellm_client.providers.get(selected_provider)
        if not prov_config:
            raise ValueError(f"Provider not found: {selected_provider}")
        
        # Format model name for LiteLLM
        model_name = self.litellm_client._format_model_name(selected_provider, selected_model)
        
        # Prepare model parameters
        model_params = {
            "model": model_name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "streaming": streaming,
        }
        
        # Add API key if required
        if prov_config.api_key_env:
            api_key = os.getenv(prov_config.api_key_env)
            if api_key:
                model_params["api_key"] = api_key
        
        # Add base URL if specified
        if prov_config.base_url:
            model_params["api_base"] = prov_config.base_url
        
        # Add provider-specific parameters
        model_params.update(prov_config.parameters)
        model_params.update(kwargs)
        
        # Add metrics callback
        if callbacks is None:
            callbacks = []
        
        metrics_callback = ProviderMetricsCallback(
            self.litellm_client._update_metrics
        )
        callbacks.append(metrics_callback)
        
        # Create ChatLiteLLM model
        try:
            chat_model = ChatLiteLLM(
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
                callbacks=callbacks,
                **{k: v for k, v in model_params.items() 
                   if k not in ["model", "temperature", "max_tokens", "streaming"]}
            )
            
            # Cache the model
            cache_key = f"{selected_provider}:{selected_model}"
            self.active_models[cache_key] = chat_model
            
            logger.info(f"Created chat model: {model_name} (provider: {selected_provider})")
            return chat_model
            
        except Exception as e:
            logger.error(f"Failed to create chat model for {selected_provider}: {e}")
            
            # Try fallback if enabled
            if self.provider_config.get("global", {}).get("fallback_enabled"):
                return self._create_fallback_model(
                    selected_provider, temperature, max_tokens, streaming, callbacks, **kwargs
                )
            
            raise
    
    def _create_fallback_model(
        self,
        failed_provider: str,
        temperature: float,
        max_tokens: int,
        streaming: bool,
        callbacks: Optional[List[BaseCallbackHandler]],
        **kwargs
    ) -> ChatLiteLLM:
        """Try creating a model with fallback providers."""
        fallback_chain = self.provider_config.get("global", {}).get("fallback_chain", [])
        
        for fallback_prov in fallback_chain:
            if fallback_prov == failed_provider:
                continue
            if fallback_prov not in self.litellm_client.providers:
                continue
            
            try:
                logger.info(f"Trying fallback provider: {fallback_prov}")
                return self.create_chat_model(
                    provider=fallback_prov,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    streaming=streaming,
                    callbacks=callbacks,
                    **kwargs
                )
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_prov} also failed: {e}")
                continue
        
        raise RuntimeError(f"All fallback providers failed after {failed_provider}")
    
    def get_model(self, provider: str, model: str) -> Optional[ChatLiteLLM]:
        """
        Get a cached model instance.
        
        Args:
            provider: Provider name
            model: Model name
            
        Returns:
            Cached ChatLiteLLM instance or None
        """
        cache_key = f"{provider}:{model}"
        return self.active_models.get(cache_key)
    
    def list_available_providers(self) -> List[str]:
        """List available providers."""
        return self.litellm_client.list_providers()
    
    def list_available_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List available models.
        
        Args:
            provider: Specific provider or None for all
            
        Returns:
            Dictionary mapping provider to list of models
        """
        return self.litellm_client.list_models(provider)
    
    def get_provider_metrics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get provider usage metrics.
        
        Args:
            provider: Specific provider or None for all
            
        Returns:
            Dictionary of metrics
        """
        return self.litellm_client.get_metrics(provider)
    
    def get_best_provider_for_task(self, task_type: str) -> tuple[str, str]:
        """
        Get the best provider and model for a specific task.
        
        Args:
            task_type: Task type (summarization, analysis, planning, etc.)
            
        Returns:
            (provider_name, model_name) tuple
        """
        return self.litellm_client._select_best_provider(task_type)


__all__ = ["ModelFactory", "ProviderMetricsCallback"]

