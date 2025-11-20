"""Minimal Cerebras integration client.

This module provides a lightweight asynchronous Cerebras REST client with
automatic API key and model rotation. It keeps only the pieces required for a
fast integration inside Hypr-Voice and avoids pulling the heavy SDK or any of
the auxiliary tooling that previously lived in this directory.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, Iterable, List, Optional, Sequence

import httpx

DEFAULT_BASE_URL = "https://api.cerebras.ai/v1"

DEFAULT_MODEL_CONTEXT: Dict[str, int] = {
    "gpt-oss-120b": 65_536,
    "llama-3.3-70b": 65_536,
    "llama-4-scout-17b-16e-instruct": 8_192,
    "llama3.1-8b": 8_192,
    "llama3.1-70b": 65_536,
    "llama3-8b": 8_192,
    "llama3-70b": 65_536,
    "qwen-3-235b-a22b-instruct-2507": 65_536,
    "qwen-3-235b-a22b-thinking-2507": 65_536,
    "qwen-3-32b": 65_536,
    "qwen-3-coder-480b": 65_536,
}

DEFAULT_CONTEXT_FALLBACK = 65_536
DEFAULT_COMPLETION_LIMIT = 16_000

DEFAULT_MODEL_COMPLETION_LIMIT: Dict[str, int] = {
    model: min(DEFAULT_COMPLETION_LIMIT, context)
    for model, context in DEFAULT_MODEL_CONTEXT.items()
}

DEFAULT_MODELS: tuple[str, ...] = (
    "gpt-oss-120b",
    "llama-3.3-70b",
    "llama-4-scout-17b-16e-instruct",
    "llama3.1-8b",
    "qwen-3-235b-a22b-instruct-2507",
    "qwen-3-235b-a22b-thinking-2507",
    "qwen-3-32b",
    "qwen-3-coder-480b",
)


def _load_dotenv_if_available() -> None:
    """Attempt to load a nearby .env file without introducing a hard dependency."""

    try:
        from dotenv import load_dotenv  # type: ignore
    except ImportError:
        return

    current = Path(__file__).resolve().parent
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            break
        current = current.parent


def _dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen: set[str] = set()
    ordered: List[str] = []
    for item in values:
        if item and item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


@dataclass(slots=True)
class CerebrasConfig:
    """Configuration for the minimal Cerebras REST client."""

    api_keys: Sequence[str]
    model_priority: Sequence[str] = field(default_factory=lambda: DEFAULT_MODELS)
    base_url: str = DEFAULT_BASE_URL
    timeout: float = 30.0
    max_retries: int = 2
    retry_backoff: float = 0.25
    model_context_window: Dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_MODEL_CONTEXT)
    )
    default_context_window: int = DEFAULT_CONTEXT_FALLBACK
    model_max_tokens: Dict[str, int] = field(
        default_factory=lambda: dict(DEFAULT_MODEL_COMPLETION_LIMIT)
    )
    default_max_tokens: int = DEFAULT_COMPLETION_LIMIT

    @classmethod
    def from_env(cls) -> "CerebrasConfig":
        """Load configuration from environment variables and optional .env file."""

        _load_dotenv_if_available()

        raw_keys: List[str] = []

        # Explicit multi-key configuration (primary pattern used in Hypr-Voice)
        multi_env = os.getenv("CEREBRAS_API_KEYS")
        if multi_env:
            raw_keys.extend([key.strip() for key in multi_env.split(",")])

        # Enumerated keys (CEREBRAS_API_KEY_1, CEREBRAS_API_KEY_ONE, ...)
        index = 1
        while True:
            key = os.getenv(f"CEREBRAS_API_KEY_{index}")
            if not key:
                break
            raw_keys.append(key.strip())
            index += 1

        for suffix in ("ONE", "TWO", "THREE", "FOUR", "FIVE"):
            key = os.getenv(f"CEREBRAS_API_KEY_{suffix}")
            if key:
                raw_keys.append(key.strip())

        # Fallback single key
        single_key = os.getenv("CEREBRAS_API_KEY")
        if single_key:
            raw_keys.append(single_key.strip())

        api_keys = _dedupe_preserve_order(raw_keys)
        if not api_keys:
            raise ValueError(
                "Cerebras API key(s) not found. Set CEREBRAS_API_KEY or "
                "CEREBRAS_API_KEYS."
            )

        models_env = os.getenv("CEREBRAS_PREFERRED_MODELS") or os.getenv("CEREBRAS_MODELS")
        if models_env:
            models = _dedupe_preserve_order(model.strip() for model in models_env.split(","))
        else:
            models = list(DEFAULT_MODELS)

        default_max_tokens = int(
            os.getenv("CEREBRAS_DEFAULT_MAX_TOKENS", str(DEFAULT_COMPLETION_LIMIT))
        )

        context_window = dict(DEFAULT_MODEL_CONTEXT)
        model_max_tokens = {
            model_name: min(
                default_max_tokens,
                context_window.get(model_name, DEFAULT_CONTEXT_FALLBACK),
            )
            for model_name in models
        }

        custom_caps = os.getenv("CEREBRAS_MODEL_MAX_TOKENS")
        if custom_caps:
            for item in custom_caps.split(","):
                if ":" not in item:
                    continue
                name, value = item.split(":", 1)
                name = name.strip()
                try:
                    limit = int(value.strip())
                except ValueError:
                    continue
                context_limit = context_window.get(name, DEFAULT_CONTEXT_FALLBACK)
                model_max_tokens[name] = min(limit, context_limit)

        for model_name in models:
            env_key = (
                "CEREBRAS_MAX_TOKENS_"
                + model_name.upper().replace("-", "_").replace(".", "_")
            )
            env_value = os.getenv(env_key)
            if env_value:
                try:
                    limit = int(env_value)
                except ValueError:
                    continue
                context_limit = context_window.get(model_name, DEFAULT_CONTEXT_FALLBACK)
                model_max_tokens[model_name] = min(limit, context_limit)

        return cls(
            api_keys=tuple(api_keys),
            model_priority=tuple(models),
            model_context_window=context_window,
            model_max_tokens=model_max_tokens,
            default_max_tokens=default_max_tokens,
        )


class CerebrasClient:
    """Asynchronous Cerebras REST API client with key/model rotation."""

    def __init__(self, config: Optional[CerebrasConfig] = None):
        self.config = config or CerebrasConfig.from_env()
        self._http = httpx.AsyncClient(
            base_url=self.config.base_url,
            timeout=httpx.Timeout(self.config.timeout),
            limits=httpx.Limits(max_connections=32, max_keepalive_connections=16),
            http2=True,
        )

        self._key_failures: List[int] = [0 for _ in self.config.api_keys]
        self._model_failures: Dict[str, int] = {
            model: 0 for model in self.config.model_priority
        }
        self._cursor = 0

    # ------------------------------------------------------------------
    # Selection helpers
    # ------------------------------------------------------------------
    def _select_model_order(self, requested: Optional[str]) -> List[str]:
        if requested:
            return [requested]

        scored = [
            (self._model_failures.get(model, 0), index, model)
            for index, model in enumerate(self.config.model_priority)
        ]
        scored.sort()
        return [entry[2] for entry in scored]

    def _select_key(self, used: set[int]) -> Optional[int]:
        candidates = [
            (self._key_failures[idx], (idx - self._cursor) % len(self.config.api_keys), idx)
            for idx in range(len(self.config.api_keys))
            if idx not in used
        ]
        if not candidates:
            return None

        candidates.sort()
        chosen_idx = candidates[0][2]
        self._cursor = (chosen_idx + 1) % len(self.config.api_keys)
        return chosen_idx

    def _bump_key_failure(self, index: int, weight: int = 1) -> None:
        self._key_failures[index] = min(self._key_failures[index] + weight, 100)

    def _reward_key(self, index: int, weight: int = 1) -> None:
        self._key_failures[index] = max(self._key_failures[index] - weight, 0)

    def _bump_model_failure(self, model: str, weight: int = 1) -> None:
        previous = self._model_failures.get(model, 0)
        self._model_failures[model] = min(previous + weight, 100)

    def _reward_model(self, model: str, weight: int = 1) -> None:
        previous = self._model_failures.get(model, 0)
        self._model_failures[model] = max(previous - weight, 0)

    def _normalize_max_tokens(self, model: str, requested: Optional[int]) -> int:
        context_cap = self.config.model_context_window.get(
            model, self.config.default_context_window
        )
        configured_cap = self.config.model_max_tokens.get(
            model, self.config.default_max_tokens
        )
        hard_cap = min(self.config.default_max_tokens, configured_cap, context_cap)

        if requested is None:
            return hard_cap

        return max(1, min(int(requested), hard_cap))

    # ------------------------------------------------------------------
    # Core request flow
    # ------------------------------------------------------------------
    async def chat(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        model: Optional[str] = None,
        max_tokens: int = 16_000,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[Sequence[str]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        response_format: Optional[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Perform a standard chat completion request.
        
        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            model: Model name (uses rotation if None)
            max_tokens: Maximum tokens to generate (default: 16000, capped per model)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            top_p: Nucleus sampling parameter 0.0-1.0 (alternative to temperature)
            top_k: Top-k sampling parameter (model-dependent support)
            stop: Stop sequences (list of strings that stop generation)
            seed: Random seed for reproducibility
            user: User identifier for tracking/rate limiting
            response_format: Response format dict, e.g., {"type": "json_object"}
            stream: Enable streaming (ignored, use stream_chat() instead)
            **kwargs: Additional OpenAI-compatible parameters
        
        Returns:
            Dict with 'content', 'model', 'usage' keys
        """

        payload_base: Dict[str, Any] = {
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }
        
        # Add optional parameters if provided
        if top_p is not None:
            payload_base["top_p"] = top_p
        if top_k is not None:
            payload_base["top_k"] = top_k
        if stop is not None:
            payload_base["stop"] = list(stop) if isinstance(stop, (list, tuple)) else [stop]
        if seed is not None:
            payload_base["seed"] = seed
        if user is not None:
            payload_base["user"] = user
        if response_format is not None and not stream:
            payload_base["response_format"] = response_format
        
        payload_base.update(kwargs)

        models_to_try = self._select_model_order(model)
        last_error: Optional[Exception] = None

        for model_name in models_to_try:
            used_keys: set[int] = set()

            while len(used_keys) < len(self.config.api_keys):
                key_idx = self._select_key(used_keys)
                if key_idx is None:
                    break
                used_keys.add(key_idx)

                payload = dict(payload_base, model=model_name)
                payload["max_tokens"] = self._normalize_max_tokens(
                    model_name, payload.get("max_tokens")
                )
                headers = {
                    "Authorization": f"Bearer {self.config.api_keys[key_idx]}",
                    "Content-Type": "application/json",
                }

                try:
                    response = await self._http.post(
                        "/chat/completions",
                        json=payload,
                        headers=headers,
                    )
                except httpx.TimeoutException as exc:
                    last_error = exc
                    self._bump_key_failure(key_idx, 2)
                    self._bump_model_failure(model_name, 1)
                    await asyncio.sleep(self.config.retry_backoff)
                    continue
                except httpx.HTTPError as exc:
                    last_error = exc
                    self._bump_key_failure(key_idx, 2)
                    self._bump_model_failure(model_name, 1)
                    continue

                if response.status_code == 200:
                    data = response.json()
                    content = (
                        data.get("choices", [{}])[0]
                        .get("message", {})
                        .get("content", "")
                    )

                    self._reward_key(key_idx, 2)
                    self._reward_model(model_name, 2)

                    return {
                        "content": content,
                        "model": data.get("model", model_name),
                        "usage": data.get("usage", {}),
                    }

                # Handle known failure patterns
                should_switch = await self._handle_failure(
                    response=response,
                    key_idx=key_idx,
                    model_name=model_name,
                )

                try:
                    body = response.json()
                    message = body.get("error", {}).get("message", response.text)
                except json.JSONDecodeError:
                    message = response.text

                last_error = RuntimeError(
                    f"Cerebras API error {response.status_code}: {message.strip()}"
                )

                if should_switch:
                    break

            if last_error and isinstance(last_error, RuntimeError):
                continue

        if last_error:
            raise last_error
        raise RuntimeError("Cerebras request failed with no additional context")

    async def stream_chat(
        self,
        messages: Sequence[Dict[str, str]],
        *,
        model: Optional[str] = None,
        max_tokens: int = 16_000,
        temperature: float = 0.7,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[Sequence[str]] = None,
        seed: Optional[int] = None,
        user: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream chat responses token by token.
        
        Args:
            messages: Chat messages [{"role": "user", "content": "..."}]
            model: Model name (uses rotation if None)
            max_tokens: Maximum tokens to generate (default: 16000, capped per model)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            top_p: Nucleus sampling parameter 0.0-1.0 (alternative to temperature)
            top_k: Top-k sampling parameter (model-dependent support)
            stop: Stop sequences (list of strings that stop generation)
            seed: Random seed for reproducibility
            user: User identifier for tracking/rate limiting
            **kwargs: Additional OpenAI-compatible parameters
        
        Yields:
            Content chunks as strings (token by token)
        
        Note:
            response_format is not supported with streaming
        """

        payload_base: Dict[str, Any] = {
            "messages": list(messages),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        
        # Add optional parameters if provided
        if top_p is not None:
            payload_base["top_p"] = top_p
        if top_k is not None:
            payload_base["top_k"] = top_k
        if stop is not None:
            payload_base["stop"] = list(stop) if isinstance(stop, (list, tuple)) else [stop]
        if seed is not None:
            payload_base["seed"] = seed
        if user is not None:
            payload_base["user"] = user
        
        payload_base.update(kwargs)

        models_to_try = self._select_model_order(model)
        last_error: Optional[Exception] = None

        for model_name in models_to_try:
            used_keys: set[int] = set()

            while len(used_keys) < len(self.config.api_keys):
                key_idx = self._select_key(used_keys)
                if key_idx is None:
                    break
                used_keys.add(key_idx)

                payload = dict(payload_base, model=model_name)
                payload["max_tokens"] = self._normalize_max_tokens(
                    model_name, payload.get("max_tokens")
                )
                headers = {
                    "Authorization": f"Bearer {self.config.api_keys[key_idx]}",
                    "Content-Type": "application/json",
                }

                try:
                    async with self._http.stream(
                        "POST",
                        "/chat/completions",
                        json=payload,
                        headers=headers,
                    ) as response:
                        if response.status_code != 200:
                            should_switch = await self._handle_failure(
                                response=response,
                                key_idx=key_idx,
                                model_name=model_name,
                            )

                            text = await response.aread()
                            last_error = RuntimeError(
                                f"Cerebras streaming error {response.status_code}: "
                                f"{text.decode(errors='ignore').strip()}"
                            )

                            if should_switch:
                                break
                            continue

                        self._reward_key(key_idx, 2)
                        self._reward_model(model_name, 2)

                        async for line in response.aiter_lines():
                            if not line or line.startswith(":"):
                                continue
                            if line.startswith("data: "):
                                payload_str = line[6:].strip()
                                if payload_str == "[DONE]":
                                    return
                                try:
                                    chunk = json.loads(payload_str)
                                except json.JSONDecodeError:
                                    continue
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content")
                                if content:
                                    yield content
                        return

                except httpx.TimeoutException as exc:
                    last_error = exc
                    self._bump_key_failure(key_idx, 2)
                    self._bump_model_failure(model_name, 1)
                    await asyncio.sleep(self.config.retry_backoff)
                    continue
                except httpx.HTTPError as exc:
                    last_error = exc
                    self._bump_key_failure(key_idx, 2)
                    self._bump_model_failure(model_name, 1)
                    continue

        if last_error:
            raise last_error
        raise RuntimeError("Cerebras streaming request failed")

    async def summarize(
        self,
        text: str,
        *,
        max_tokens: int = 120,
        style: str = "concise",
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        stop: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Summarize text with various styles.
        
        Args:
            text: Text to summarize
            max_tokens: Maximum tokens in summary (default: 120)
            style: "concise", "bullet_points", or "detailed" (default: "concise")
            temperature: Sampling temperature (default: 0.3)
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            **kwargs: Additional parameters passed to chat()
        
        Returns:
            Summarized text
        """
        system_prompts = {
            "concise": "Summarize the user content in one or two crisp sentences.",
            "bullet_points": "Summarize the user content as short bullet points.",
            "detailed": "Summarize the user content with clear detail in 3-4 sentences.",
        }

        messages = [
            {"role": "system", "content": system_prompts.get(style, system_prompts["concise"])},
            {"role": "user", "content": text},
        ]

        response = await self.chat(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            **kwargs,
        )
        return response.get("content", "")

    async def quick_prompt(
        self,
        prompt: str,
        *,
        max_tokens: int = 100,
        temperature: float = 0.5,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[Sequence[str]] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Quick single-prompt completion without system message.
        
        Args:
            prompt: User prompt text
            max_tokens: Maximum tokens to generate (default: 100)
            temperature: Sampling temperature (default: 0.5)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop: Stop sequences
            seed: Random seed for reproducibility
            **kwargs: Additional parameters passed to chat()
        
        Returns:
            Response text
        """
        messages = [{"role": "user", "content": prompt}]
        response = await self.chat(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop=stop,
            seed=seed,
            **kwargs,
        )
        return response.get("content", "")

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "CerebrasClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def _handle_failure(
        self,
        *,
        response: httpx.Response,
        key_idx: int,
        model_name: str,
    ) -> bool:
        """Update failure counters and return whether the caller should switch model."""

        status = response.status_code

        if status == 429:
            self._bump_key_failure(key_idx, 5)
            self._bump_model_failure(model_name, 2)
            return False

        if status in (401, 403):
            self._bump_key_failure(key_idx, 100)
            return False

        if status == 404:
            self._bump_model_failure(model_name, 50)
            return True

        if status >= 500:
            self._bump_key_failure(key_idx, 4)
            self._bump_model_failure(model_name, 3)
            return False

        # Generic client error
        self._bump_key_failure(key_idx, 2)
        self._bump_model_failure(model_name, 1)
        return False


class SyncCerebrasClient:
    """Synchronous wrapper around :class:`CerebrasClient`."""

    def __init__(self, config: Optional[CerebrasConfig] = None):
        self._client = CerebrasClient(config)
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _ensure_loop(self) -> asyncio.AbstractEventLoop:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            if self._loop is None:
                self._loop = asyncio.new_event_loop()
            loop = self._loop
            asyncio.set_event_loop(loop)
        return loop

    def chat(self, messages: Sequence[Dict[str, str]], **kwargs: Any) -> Dict[str, Any]:
        loop = self._ensure_loop()
        return loop.run_until_complete(self._client.chat(messages, **kwargs))

    def summarize(self, text: str, **kwargs: Any) -> str:
        loop = self._ensure_loop()
        return loop.run_until_complete(self._client.summarize(text, **kwargs))

    def quick_prompt(self, prompt: str, **kwargs: Any) -> str:
        loop = self._ensure_loop()
        return loop.run_until_complete(self._client.quick_prompt(prompt, **kwargs))

    def close(self) -> None:
        if self._loop is None:
            loop = self._ensure_loop()
        else:
            loop = self._loop
        loop.run_until_complete(self._client.close())

__all__ = ["CerebrasConfig", "CerebrasClient", "SyncCerebrasClient"]

