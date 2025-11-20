"""
LiteLLM Multi-Provider Client for Helper Agent

This module provides a unified client for accessing 10+ LLM providers through LiteLLM,
with intelligent provider rotation, rate limiting, cost tracking, and streaming support.
"""

import asyncio
import logging
import os
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import yaml
from pathlib import Path

try:
    import litellm
    from litellm import acompletion, completion
    LITELLM_AVAILABLE = True
except ImportError:
    LITELLM_AVAILABLE = False
    logging.warning("LiteLLM not available. Install with: pip install litellm")

from .sglang_client import SGLangClient, SGLangConfig

logger = logging.getLogger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider."""
    name: str
    enabled: bool = True
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    base_url_env: Optional[str] = None
    default_model: str = ""
    models: Dict[str, Any] = field(default_factory=dict)
    rate_limit: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    custom_provider: bool = False


@dataclass
class ProviderMetrics:
    """Metrics tracking for a provider."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    avg_latency: float = 0.0
    last_request_time: Optional[float] = None
    failure_count: int = 0
    last_failure_time: Optional[float] = None
    cooldown_until: Optional[float] = None


class LiteLLMClient:
    """
    Multi-provider LLM client using LiteLLM with intelligent routing and fallback.
    
    Features:
    - 10+ provider support via LiteLLM
    - SGLang custom provider integration
    - Automatic provider rotation and failover
    - Rate limiting and quota management
    - Cost tracking and usage metrics
    - Streaming support with SSE
    - Context window tracking per model
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the LiteLLM client.
        
        Args:
            config_path: Path to providers.yaml configuration file
        """
        if not LITELLM_AVAILABLE:
            raise ImportError("LiteLLM is required but not installed")
        
        # Load configuration
        self.config_path = config_path or Path(__file__).parent / "config" / "providers.yaml"
        self.config = self._load_config()
        
        # Initialize provider configurations
        self.providers: Dict[str, ProviderConfig] = {}
        self.provider_metrics: Dict[str, ProviderMetrics] = {}
        self._initialize_providers()
        
        # SGLang custom provider
        self.sglang_client: Optional[SGLangClient] = None
        if self.providers.get("sglang", {}).enabled:
            self._initialize_sglang()
        
        # Rate limiting
        self.request_times: Dict[str, List[float]] = {}
        self.token_counts: Dict[str, List[tuple[float, int]]] = {}
        
        # Cost tracking
        self.total_cost = 0.0
        self.cost_by_provider: Dict[str, float] = {}
        
        # Configure LiteLLM
        litellm.drop_params = True  # Drop unsupported params instead of erroring
        litellm.set_verbose = False
        
        logger.info("LiteLLM client initialized with %d providers", len(self.providers))

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                return config or {}
            else:
                logger.warning(f"Config file not found: {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {}

    def _initialize_providers(self):
        """Initialize provider configurations from config."""
        providers_config = self.config.get("providers", {})
        
        for provider_name, provider_data in providers_config.items():
            if not provider_data.get("enabled", True):
                continue
                
            # Get API key from environment
            api_key_env = provider_data.get("api_key_env")
            if api_key_env and not os.getenv(api_key_env) and not provider_data.get("custom_provider"):
                logger.warning(f"API key not found for {provider_name}: {api_key_env}")
                continue
            
            # Get base URL
            base_url = provider_data.get("base_url")
            base_url_env = provider_data.get("base_url_env")
            if base_url_env:
                base_url = os.getenv(base_url_env, base_url)
            
            self.providers[provider_name] = ProviderConfig(
                name=provider_name,
                enabled=provider_data.get("enabled", True),
                api_key_env=api_key_env,
                base_url=base_url,
                base_url_env=base_url_env,
                default_model=provider_data.get("default_model", ""),
                models=provider_data.get("models", {}),
                rate_limit=provider_data.get("rate_limit", {}),
                parameters=provider_data.get("parameters", {}),
                custom_provider=provider_data.get("custom_provider", False)
            )
            
            self.provider_metrics[provider_name] = ProviderMetrics()
            self.request_times[provider_name] = []
            self.token_counts[provider_name] = []
            self.cost_by_provider[provider_name] = 0.0
            
        logger.info(f"Initialized {len(self.providers)} providers")

    def _initialize_sglang(self):
        """Initialize SGLang custom provider."""
        try:
            sglang_config = self.providers.get("sglang")
            if not sglang_config:
                return
                
            base_url = sglang_config.base_url or "http://localhost:30000"
            host, port_str = base_url.replace("http://", "").replace("https://", "").split(":")
            port = int(port_str)
            
            sg_config = SGLangConfig(
                host=host,
                port=port,
                model=sglang_config.default_model or "qwen3-1.7b"
            )
            
            self.sglang_client = SGLangClient(sg_config)
            logger.info("SGLang custom provider initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SGLang: {e}")

    async def initialize(self):
        """Initialize async components."""
        if self.sglang_client:
            await self.sglang_client.initialize()

    async def cleanup(self):
        """Cleanup resources."""
        if self.sglang_client:
            await self.sglang_client.cleanup()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

    def _get_provider_model(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> tuple[str, str]:
        """
        Get provider and model, selecting best if not specified.
        
        Returns:
            (provider_name, model_name) tuple
        """
        # If provider specified, use it
        if provider and provider in self.providers:
            if not model:
                model = self.providers[provider].default_model
            return provider, model
        
        # If model specified, determine provider
        if model:
            for prov_name, prov_config in self.providers.items():
                if model in prov_config.models or model == prov_config.default_model:
                    return prov_name, model
        
        # Auto-select best provider
        return self._select_best_provider()

    def _select_best_provider(self, task_type: Optional[str] = None) -> tuple[str, str]:
        """
        Intelligently select the best provider based on metrics and availability.
        
        Args:
            task_type: Type of task (e.g., "summarization", "analysis")
            
        Returns:
            (provider_name, model_name) tuple
        """
        strategy = self.config.get("selection_strategy", {})
        mode = strategy.get("mode", "smart")
        
        # Get task preferences
        task_prefs = strategy.get("task_preferences", {}).get(task_type, {})
        preferred = task_prefs.get("preferred", [])
        avoid = task_prefs.get("avoid", [])
        
        # Score each provider
        scores = []
        for prov_name, prov_config in self.providers.items():
            if not prov_config.enabled:
                continue
            if prov_name in avoid:
                continue
                
            metrics = self.provider_metrics[prov_name]
            
            # Check cooldown
            if metrics.cooldown_until and time.time() < metrics.cooldown_until:
                continue
            
            # Calculate score
            score = 100.0
            
            # Preference bonus
            if prov_name in preferred:
                score += 50
            
            # Success rate
            if metrics.total_requests > 0:
                success_rate = metrics.successful_requests / metrics.total_requests
                score += success_rate * 30
            
            # Recent failures penalty
            if metrics.failure_count > 0:
                score -= metrics.failure_count * 10
            
            # Latency factor
            if metrics.avg_latency > 0:
                # Prefer faster providers (lower latency)
                score += max(0, 20 - metrics.avg_latency)
            
            # Cost factor (if enabled)
            if self.config.get("global", {}).get("cost_tracking"):
                # Prefer cheaper providers
                if prov_name in self.cost_by_provider:
                    avg_cost = self.cost_by_provider[prov_name] / max(1, metrics.total_requests)
                    score -= avg_cost * 100
            
            scores.append((score, prov_name, prov_config.default_model))
        
        if not scores:
            # Fallback to first enabled provider
            for prov_name, prov_config in self.providers.items():
                if prov_config.enabled:
                    return prov_name, prov_config.default_model
            raise RuntimeError("No providers available")
        
        # Sort by score (highest first)
        scores.sort(reverse=True, key=lambda x: x[0])
        _, provider, model = scores[0]
        
        logger.debug(f"Selected provider: {provider} with model: {model}")
        return provider, model

    async def _check_rate_limit(self, provider: str) -> bool:
        """Check if request would exceed rate limits."""
        prov_config = self.providers.get(provider)
        if not prov_config:
            return True
            
        rate_limit = prov_config.rate_limit
        if not rate_limit:
            return True
        
        current_time = time.time()
        
        # Check requests per minute
        rpm_limit = rate_limit.get("requests_per_minute")
        if rpm_limit:
            # Clean old requests
            cutoff = current_time - 60
            self.request_times[provider] = [
                t for t in self.request_times[provider] if t > cutoff
            ]
            
            if len(self.request_times[provider]) >= rpm_limit:
                logger.warning(f"Rate limit exceeded for {provider}: {rpm_limit} RPM")
                return False
        
        # Check tokens per minute
        tpm_limit = rate_limit.get("tokens_per_minute")
        if tpm_limit:
            # Clean old token counts
            cutoff = current_time - 60
            self.token_counts[provider] = [
                (t, c) for t, c in self.token_counts[provider] if t > cutoff
            ]
            
            total_tokens = sum(c for _, c in self.token_counts[provider])
            if total_tokens >= tpm_limit:
                logger.warning(f"Token limit exceeded for {provider}: {tpm_limit} TPM")
                return False
        
        return True

    def _record_request(self, provider: str, tokens: int = 0):
        """Record a request for rate limiting."""
        current_time = time.time()
        self.request_times[provider].append(current_time)
        if tokens > 0:
            self.token_counts[provider].append((current_time, tokens))

    def _update_metrics(
        self,
        provider: str,
        success: bool,
        latency: float,
        tokens: int = 0,
        cost: float = 0.0
    ):
        """Update provider metrics."""
        metrics = self.provider_metrics[provider]
        
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
            metrics.failure_count = max(0, metrics.failure_count - 1)
        else:
            metrics.failed_requests += 1
            metrics.failure_count += 1
            metrics.last_failure_time = time.time()
            
            # Set cooldown if too many failures
            if metrics.failure_count >= 3:
                metrics.cooldown_until = time.time() + 60  # 1 minute cooldown
        
        metrics.total_tokens += tokens
        metrics.total_cost += cost
        
        # Update average latency
        if metrics.avg_latency == 0:
            metrics.avg_latency = latency
        else:
            metrics.avg_latency = (metrics.avg_latency * 0.9) + (latency * 0.1)
        
        metrics.last_request_time = time.time()
        
        # Update global cost tracking
        self.cost_by_provider[provider] += cost
        self.total_cost += cost

    def _format_model_name(self, provider: str, model: str) -> str:
        """Format model name for LiteLLM."""
        # LiteLLM expects format: provider/model for some providers
        if provider in ["openrouter", "together", "mistral", "cohere", "perplexity"]:
            if "/" not in model:
                return f"{provider}/{model}"
        return model

    def _calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> float:
        """Calculate cost based on token usage."""
        prov_config = self.providers.get(provider)
        if not prov_config:
            return 0.0
        
        model_config = prov_config.models.get(model, {})
        prompt_cost = model_config.get("cost_per_1k_prompt", 0.0)
        completion_cost = model_config.get("cost_per_1k_completion", 0.0)
        
        total_cost = (prompt_tokens / 1000.0 * prompt_cost) + \
                     (completion_tokens / 1000.0 * completion_cost)
        
        return total_cost

    async def chat(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop: Optional[Sequence[str]] = None,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Perform chat completion.
        
        Args:
            messages: Chat messages
            provider: Provider name (auto-selected if None)
            model: Model name (uses provider default if None)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            stream: Whether to stream (use stream_chat instead)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Response dictionary with content, model, usage, cost
        """
        # Select provider and model
        selected_provider, selected_model = self._get_provider_model(provider, model)
        
        # Handle SGLang custom provider
        if selected_provider == "sglang" and self.sglang_client:
            return await self._chat_sglang(messages, max_tokens, temperature)
        
        # Check rate limits
        if not await self._check_rate_limit(selected_provider):
            # Try fallback provider
            fallback_chain = self.config.get("global", {}).get("fallback_chain", [])
            for fallback_prov in fallback_chain:
                if fallback_prov != selected_provider and fallback_prov in self.providers:
                    if await self._check_rate_limit(fallback_prov):
                        selected_provider = fallback_prov
                        selected_model = self.providers[fallback_prov].default_model
                        break
            else:
                raise RuntimeError("All providers rate limited")
        
        # Record request
        self._record_request(selected_provider)
        
        # Format model name
        model_name = self._format_model_name(selected_provider, selected_model)
        
        # Prepare parameters
        params = {
            "model": model_name,
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        
        if top_p is not None:
            params["top_p"] = top_p
        if stop:
            params["stop"] = list(stop)
        
        # Add provider-specific parameters
        prov_config = self.providers[selected_provider]
        params.update(prov_config.parameters)
        params.update(kwargs)
        
        # Make request
        start_time = time.time()
        try:
            response = await acompletion(**params)
            latency = time.time() - start_time
            
            # Extract response data
            content = response.choices[0].message.content
            usage = response.usage if hasattr(response, 'usage') else {}
            
            prompt_tokens = getattr(usage, 'prompt_tokens', 0)
            completion_tokens = getattr(usage, 'completion_tokens', 0)
            total_tokens = prompt_tokens + completion_tokens
            
            # Calculate cost
            cost = self._calculate_cost(
                selected_provider,
                selected_model,
                prompt_tokens,
                completion_tokens
            )
            
            # Update metrics
            self._update_metrics(
                selected_provider,
                success=True,
                latency=latency,
                tokens=total_tokens,
                cost=cost
            )
            
            return {
                "content": content,
                "provider": selected_provider,
                "model": selected_model,
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                },
                "cost": cost,
                "latency": latency
            }
            
        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics(selected_provider, success=False, latency=latency)
            logger.error(f"Chat completion failed for {selected_provider}: {e}")
            
            # Try fallback
            if self.config.get("global", {}).get("fallback_enabled"):
                return await self._try_fallback_chat(messages, selected_provider, **params)
            
            raise

    async def _chat_sglang(
        self,
        messages: Sequence[Dict[str, str]],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Handle chat completion for SGLang custom provider."""
        start_time = time.time()
        
        try:
            response = await self.sglang_client.chat_completion(
                messages=list(messages),
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            latency = time.time() - start_time
            
            # Estimate tokens (rough approximation)
            tokens = len(response.split()) if response else 0
            
            self._update_metrics("sglang", success=True, latency=latency, tokens=tokens)
            
            return {
                "content": response or "",
                "provider": "sglang",
                "model": "qwen3-1.7b",
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": tokens,
                    "total_tokens": tokens
                },
                "cost": 0.0,
                "latency": latency
            }
        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics("sglang", success=False, latency=latency)
            raise

    async def _try_fallback_chat(
        self,
        messages: Sequence[Dict[str, str]],
        failed_provider: str,
        **params
    ) -> Dict[str, Any]:
        """Try fallback providers for chat completion."""
        fallback_chain = self.config.get("global", {}).get("fallback_chain", [])
        
        for fallback_prov in fallback_chain:
            if fallback_prov == failed_provider:
                continue
            if fallback_prov not in self.providers:
                continue
            if not self.providers[fallback_prov].enabled:
                continue
            
            try:
                logger.info(f"Trying fallback provider: {fallback_prov}")
                return await self.chat(messages, provider=fallback_prov, **params)
            except Exception as e:
                logger.warning(f"Fallback provider {fallback_prov} also failed: {e}")
                continue
        
        raise RuntimeError(f"All fallback providers failed after {failed_provider}")

    async def stream_chat(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        stop: Optional[Sequence[str]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream chat completion token by token.
        
        Args:
            messages: Chat messages
            provider: Provider name (auto-selected if None)
            model: Model name (uses provider default if None)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Content chunks as strings
        """
        # Select provider and model
        selected_provider, selected_model = self._get_provider_model(provider, model)
        
        # Check rate limits
        if not await self._check_rate_limit(selected_provider):
            raise RuntimeError(f"Rate limit exceeded for {selected_provider}")
        
        # Record request
        self._record_request(selected_provider)
        
        # Format model name
        model_name = self._format_model_name(selected_provider, selected_model)
        
        # Prepare parameters
        params = {
            "model": model_name,
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True
        }
        
        if top_p is not None:
            params["top_p"] = top_p
        if stop:
            params["stop"] = list(stop)
        
        # Add provider-specific parameters
        prov_config = self.providers[selected_provider]
        params.update(prov_config.parameters)
        params.update(kwargs)
        
        # Make streaming request
        start_time = time.time()
        try:
            response = await acompletion(**params)
            
            total_tokens = 0
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        total_tokens += 1
                        yield delta.content
            
            latency = time.time() - start_time
            self._update_metrics(
                selected_provider,
                success=True,
                latency=latency,
                tokens=total_tokens
            )
            
        except Exception as e:
            latency = time.time() - start_time
            self._update_metrics(selected_provider, success=False, latency=latency)
            logger.error(f"Streaming failed for {selected_provider}: {e}")
            raise

    async def completion(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """
        Simple completion (non-chat format).
        
        Args:
            prompt: Text prompt
            provider: Provider name
            model: Model name
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(
            messages,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        return response["content"]

    async def stream_completion(
        self,
        prompt: str,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream simple completion.
        
        Args:
            prompt: Text prompt
            provider: Provider name
            model: Model name
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            **kwargs: Additional parameters
            
        Yields:
            Content chunks
        """
        messages = [{"role": "user", "content": prompt}]
        async for chunk in self.stream_chat(
            messages,
            provider=provider,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        ):
            yield chunk

    def get_metrics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get usage metrics.
        
        Args:
            provider: Specific provider or None for all
            
        Returns:
            Dictionary of metrics
        """
        if provider:
            if provider not in self.provider_metrics:
                return {}
            
            metrics = self.provider_metrics[provider]
            return {
                "provider": provider,
                "total_requests": metrics.total_requests,
                "successful_requests": metrics.successful_requests,
                "failed_requests": metrics.failed_requests,
                "success_rate": (
                    metrics.successful_requests / max(1, metrics.total_requests)
                ),
                "total_tokens": metrics.total_tokens,
                "total_cost": metrics.total_cost,
                "avg_latency": metrics.avg_latency,
                "failure_count": metrics.failure_count,
                "in_cooldown": (
                    metrics.cooldown_until and time.time() < metrics.cooldown_until
                )
            }
        
        # Return all metrics
        return {
            "total_cost": self.total_cost,
            "providers": {
                prov: self.get_metrics(prov)
                for prov in self.provider_metrics.keys()
            }
        }

    def list_providers(self) -> List[str]:
        """List available providers."""
        return [
            name for name, config in self.providers.items()
            if config.enabled
        ]

    def list_models(self, provider: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List available models.
        
        Args:
            provider: Specific provider or None for all
            
        Returns:
            Dictionary mapping provider to list of models
        """
        if provider:
            if provider not in self.providers:
                return {}
            return {provider: list(self.providers[provider].models.keys())}
        
        return {
            prov: list(config.models.keys())
            for prov, config in self.providers.items()
            if config.enabled
        }


__all__ = ["LiteLLMClient", "ProviderConfig", "ProviderMetrics"]

