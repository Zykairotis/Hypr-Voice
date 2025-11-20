"""High-level helpers for integrating Gemini Live into Hypr-Voice."""

from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union

from .gemini_client import GeminiClient, GeminiConfig

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class GeminiIntegration:
    """Convenience wrapper exposing common integration flows."""

    def __init__(
        self,
        *,
        client: Optional[GeminiClient] = None,
        config: Optional[GeminiConfig] = None,
    ) -> None:
        if client is not None:
            self.client = client
            self._owns_client = False
        else:
            self.client = GeminiClient(config)
            self._owns_client = True

    async def analyze_image(
        self,
        image: Union[bytes, Image.Image, Path],
        prompt: str = "Describe this image in detail.",
        *,
        temperature: float = 0.5,
        max_output_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> str:
        """
        Analyze an image with a text prompt.

        Args:
            image: Image bytes, PIL Image, or Path to image file
            prompt: Text prompt for image analysis (default: describe image)
            temperature: Sampling temperature (default: 0.5)
            max_output_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            Analysis text
        """
        content = [prompt, image]
        response = await self.client.generate_content(
            content,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            **kwargs,
        )
        return response.get("content", "")

    async def stream_image_analysis(
        self,
        image: Union[bytes, Image.Image, Path],
        prompt: str = "Describe this image in detail.",
        *,
        temperature: float = 0.5,
        max_output_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream image analysis token by token.

        Args:
            image: Image bytes, PIL Image, or Path to image file
            prompt: Text prompt for image analysis (default: describe image)
            temperature: Sampling temperature (default: 0.5)
            max_output_tokens: Maximum tokens to generate
            **kwargs: Additional parameters passed to stream_content()

        Yields:
            Analysis text chunks
        """
        content = [prompt, image]
        async for chunk in self.client.stream_content(
            content,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            **kwargs,
        ):
            yield chunk.get("content", "")

    async def multimodal_query(
        self,
        text: str,
        images: Optional[Sequence[Union[bytes, Image.Image, Path]]] = None,
        *,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Query with text and optionally multiple images.

        Args:
            text: Text prompt
            images: Optional list of images (bytes, PIL Image, or Path)
            temperature: Sampling temperature (default: 0.7)
            max_output_tokens: Maximum tokens to generate
            system_instruction: System-level instruction for the model
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            Response text
        """
        content = []
        
        # Add images first
        if images:
            content.extend(images)
        
        # Add text
        content.append(text)
        
        response = await self.client.generate_content(
            content,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            **kwargs,
        )
        return response.get("content", "")

    async def stream_multimodal_query(
        self,
        text: str,
        images: Optional[Sequence[Union[bytes, Image.Image, Path]]] = None,
        *,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream multimodal query responses token by token.

        Args:
            text: Text prompt
            images: Optional list of images (bytes, PIL Image, or Path)
            temperature: Sampling temperature (default: 0.7)
            max_output_tokens: Maximum tokens to generate
            system_instruction: System-level instruction for the model
            **kwargs: Additional parameters passed to stream_content()

        Yields:
            Response text chunks
        """
        content = []
        
        # Add images first
        if images:
            content.extend(images)
        
        # Add text
        content.append(text)
        
        async for chunk in self.client.stream_content(
            content,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            system_instruction=system_instruction,
            **kwargs,
        ):
            yield chunk.get("content", "")

    async def quick_prompt(
        self,
        prompt: str,
        *,
        max_output_tokens: int = 100,
        temperature: float = 0.5,
        **kwargs: Any,
    ) -> str:
        """
        Quick single-prompt completion.

        Args:
            prompt: User prompt text
            max_output_tokens: Maximum tokens to generate (default: 100)
            temperature: Sampling temperature (default: 0.5)
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            Response text
        """
        response = await self.client.generate_content(
            prompt,
            max_output_tokens=max_output_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.get("content", "")

    async def summarize(
        self,
        text: str,
        *,
        max_words: int = 100,
        style: str = "concise",
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> str:
        """
        Summarize text with various styles.

        Args:
            text: Text to summarize
            max_words: Maximum words in summary (default: 100)
            style: "concise", "bullet_points", or "detailed" (default: "concise")
            temperature: Sampling temperature (default: 0.3)
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            Summarized text
        """
        system_prompts = {
            "concise": "Summarize the following text in one or two crisp sentences.",
            "bullet_points": "Summarize the following text as short bullet points.",
            "detailed": "Summarize the following text with clear detail in 3-4 sentences.",
        }

        prompt = system_prompts.get(style, system_prompts["concise"])
        max_tokens = max(16, int(max_words * 1.5))

        response = await self.client.generate_content(
            f"{prompt}\n\n{text}",
            max_output_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )
        return response.get("content", "")

    async def classify(
        self,
        text: str,
        *,
        categories: Sequence[str],
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        """
        Classify text into one of the provided categories.

        Args:
            text: Text to classify
            categories: List of possible category names
            temperature: Sampling temperature (default: 0.1 for deterministic)
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            Category name (falls back to last category if no match)
        """
        prompt = (
            "Classify the following text into ONE of these categories: "
            f"{', '.join(categories)}\n\n"
            f"Text: {text}\n\nCategory:"
        )
        response = await self.client.generate_content(
            prompt,
            max_output_tokens=10,
            temperature=temperature,
            **kwargs,
        )
        
        result = response.get("content", "").strip().lower()
        for category in categories:
            if category.lower() in result:
                return category
        return categories[-1]

    async def extract_keywords(
        self,
        text: str,
        *,
        max_keywords: int = 5,
        temperature: float = 0.2,
        **kwargs: Any,
    ) -> List[str]:
        """
        Extract keywords from text.

        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords (default: 5)
            temperature: Sampling temperature (default: 0.2)
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            List of keywords
        """
        prompt = (
            f"Extract the top {max_keywords} keywords from the following text. "
            "Return only the keywords, separated by commas.\n\n"
            f"Text: {text}\n\nKeywords:"
        )
        
        response = await self.client.generate_content(
            prompt,
            max_output_tokens=50,
            temperature=temperature,
            **kwargs,
        )
        
        keywords_text = response.get("content", "")
        keywords = [kw.strip() for kw in keywords_text.split(",")]
        return [kw for kw in keywords if kw][:max_keywords]

    def session(
        self,
        *,
        system_instruction: Optional[str] = None,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> "GeminiChatSession":
        """
        Create a chat session with conversation history.

        Args:
            system_instruction: System-level instruction for the model
            history: Initial conversation history

        Returns:
            GeminiChatSession instance
        """
        return GeminiChatSession(
            client=self.client,
            system_instruction=system_instruction,
            history=history,
        )

    async def close(self) -> None:
        """Close the client (if owned)."""
        # Gemini client doesn't require explicit cleanup
        pass

    async def __aenter__(self) -> "GeminiIntegration":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()


class GeminiChatSession:
    """Conversational state built on top of the Gemini client."""

    def __init__(
        self,
        *,
        client: GeminiClient,
        system_instruction: Optional[str] = None,
        history: Optional[Sequence[Dict[str, str]]] = None,
    ) -> None:
        self._client = client
        self._system_instruction = system_instruction
        self._messages: List[Dict[str, str]] = []

        if history:
            self._messages.extend(history)

    @property
    def messages(self) -> Sequence[Dict[str, str]]:
        """Get conversation history."""
        return tuple(self._messages)

    @property
    def system_instruction(self) -> Optional[str]:
        """Get system instruction."""
        return self._system_instruction

    @system_instruction.setter
    def system_instruction(self, value: Optional[str]) -> None:
        """Set system instruction."""
        self._system_instruction = value

    def reset(self) -> None:
        """Reset conversation history."""
        self._messages.clear()

    async def send(
        self,
        message: Union[str, List[Union[str, bytes, Image.Image, Path]]],
        **kwargs: Any,
    ) -> str:
        """
        Send a message and get response.

        Args:
            message: Text message, or list of text/images
            **kwargs: Additional parameters passed to generate_content()

        Returns:
            Response text
        """
        # Store user message
        if isinstance(message, str):
            self._messages.append({"role": "user", "content": message})
            content = message
        else:
            # For multimodal, store a representation
            text_parts = [p for p in message if isinstance(p, str)]
            self._messages.append({"role": "user", "content": " ".join(text_parts)})
            content = message

        # Generate response
        response = await self._client.generate_content(
            content,
            system_instruction=self._system_instruction,
            **kwargs,
        )
        
        response_text = response.get("content", "")
        self._messages.append({"role": "assistant", "content": response_text})
        
        return response_text

    async def stream(
        self,
        message: Union[str, List[Union[str, bytes, Image.Image, Path]]],
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Send a message and stream response.

        Args:
            message: Text message, or list of text/images
            **kwargs: Additional parameters passed to stream_content()

        Yields:
            Response text chunks
        """
        # Store user message
        if isinstance(message, str):
            self._messages.append({"role": "user", "content": message})
            content = message
        else:
            # For multimodal, store a representation
            text_parts = [p for p in message if isinstance(p, str)]
            self._messages.append({"role": "user", "content": " ".join(text_parts)})
            content = message

        # Stream response
        collected: List[str] = []
        async for chunk in self._client.stream_content(
            content,
            system_instruction=self._system_instruction,
            **kwargs,
        ):
            chunk_text = chunk.get("content", "")
            if chunk_text:
                collected.append(chunk_text)
                yield chunk_text

        # Store complete response
        if collected:
            self._messages.append({"role": "assistant", "content": "".join(collected)})
        else:
            self._messages.append({"role": "assistant", "content": ""})


__all__ = ["GeminiIntegration", "GeminiChatSession"]

