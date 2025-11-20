"""High-level helpers for integrating Cerebras into Hypr-Voice."""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, List, Optional, Sequence

from .client import CerebrasClient, CerebrasConfig


class CerebrasIntegration:
    """Convenience wrapper exposing common integration flows."""

    def __init__(
        self,
        *,
        client: Optional[CerebrasClient] = None,
        config: Optional[CerebrasConfig] = None,
    ) -> None:
        if client is not None:
            self.client = client
            self._owns_client = False
        else:
            self.client = CerebrasClient(config)
            self._owns_client = True

    async def summarize_for_tts(
        self,
        text: str,
        *,
        max_words: int = 60,
        style: str = "concise",
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        stop: Optional[Sequence[str]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Summarize text optimized for text-to-speech output.
        
        Args:
            text: Text to summarize
            max_words: Maximum words in summary (default: 60)
            style: "concise", "bullet_points", or "detailed" (default: "concise")
            temperature: Sampling temperature (default: 0.3)
            top_p: Nucleus sampling parameter
            stop: Stop sequences
            **kwargs: Additional parameters passed to summarize()
        
        Returns:
            Summarized text ready for TTS
        """
        max_tokens = max(16, int(max_words * 1.4))
        return await self.client.summarize(
            text,
            max_tokens=max_tokens,
            style=style,
            temperature=temperature,
            top_p=top_p,
            stop=stop,
            **kwargs,
        )

    async def classify(
        self,
        text: str,
        *,
        categories: Sequence[str],
        temperature: float = 0.1,
        top_p: Optional[float] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Classify text into one of the provided categories.
        
        Args:
            text: Text to classify
            categories: List of possible category names
            temperature: Sampling temperature (default: 0.1 for deterministic)
            top_p: Nucleus sampling parameter
            seed: Random seed for reproducibility
            **kwargs: Additional parameters passed to quick_prompt()
        
        Returns:
            Category name (falls back to last category if no match)
        """
        prompt = (
            "Classify the following text into ONE of these categories: "
            f"{', '.join(categories)}\n\n"
            f"Text: {text}\n\nCategory:"
        )
        response = await self.client.quick_prompt(
            prompt,
            max_tokens=6,
            temperature=temperature,
            top_p=top_p,
            seed=seed,
            **kwargs,
        )
        cleaned = response.strip().lower()
        for category in categories:
            if category.lower() in cleaned:
                return category
        return categories[-1]

    async def stream_summary(
        self,
        text: str,
        *,
        max_tokens: int = 160,
        temperature: float = 0.3,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        stop: Optional[Sequence[str]] = None,
        seed: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream summary generation token by token.
        
        Args:
            text: Text to summarize
            max_tokens: Maximum tokens in summary (default: 160)
            temperature: Sampling temperature (default: 0.3)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop: Stop sequences
            seed: Random seed for reproducibility
            **kwargs: Additional parameters passed to stream_chat()
        
        Yields:
            Summary chunks as strings (token by token)
        """
        messages = [
            {"role": "system", "content": "Summarize the user message concisely."},
            {"role": "user", "content": text},
        ]
        async for chunk in self.client.stream_chat(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop=stop,
            seed=seed,
            **kwargs,
        ):
            yield chunk

    def session(
        self,
        *,
        system_prompt: Optional[str] = None,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> "CerebrasChatSession":
        return CerebrasChatSession(
            client=self.client,
            system_prompt=system_prompt,
            history=history,
        )

    async def close(self) -> None:
        if self._owns_client:
            await self.client.close()

    async def __aenter__(self) -> "CerebrasIntegration":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


class CerebrasChatSession:
    """Minimal conversational state built on top of the Cerebras client."""

    def __init__(
        self,
        *,
        client: CerebrasClient,
        system_prompt: Optional[str] = None,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> None:
        self._client = client
        self._messages: List[Dict[str, str]] = []

        if system_prompt:
            self._messages.append({"role": "system", "content": system_prompt})

        if history:
            self._messages.extend(history)

    @property
    def messages(self) -> Sequence[Dict[str, str]]:
        return tuple(self._messages)

    def reset(self) -> None:
        self._messages = [msg for msg in self._messages if msg.get("role") == "system"]

    async def send(
        self,
        message: str,
        **kwargs: Any,
    ) -> str:
        self._messages.append({"role": "user", "content": message})
        response = await self._client.chat(self._messages, **kwargs)
        content = response.get("content", "")
        self._messages.append({"role": "assistant", "content": content})
        return content

    async def stream(
        self,
        message: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        self._messages.append({"role": "user", "content": message})
        collected: List[str] = []

        async for chunk in self._client.stream_chat(self._messages, **kwargs):
            collected.append(chunk)
            yield chunk

        if collected:
            self._messages.append({"role": "assistant", "content": "".join(collected)})
        else:
            self._messages.append({"role": "assistant", "content": ""})


__all__ = ["CerebrasIntegration", "CerebrasChatSession"]

