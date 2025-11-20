"""Gemini Live API Client with multimodal support.

This module provides a lightweight asynchronous Gemini client with support for
text and image inputs, streaming responses, and token tracking. It integrates
the gemini-2.0-flash-live model for real-time interactions.
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Sequence, Union
from io import BytesIO

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


DEFAULT_MODEL = "gemini-live-2.5-flash-preview"
LIVE_MODELS = [
    "gemini-live-2.5-flash-preview",
    "gemini-2.5-flash-live-preview",
    "gemini-2.0-flash-live-001",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-2.0-flash-exp",
    "gemini-2.0-flash-thinking-exp-01-21",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

# Models that use WebSocket Live API (different protocol)
WEBSOCKET_MODELS = {
    "gemini-live-2.5-flash-preview",
    "gemini-2.5-flash-live-preview",
    "gemini-2.0-flash-live-001",
}

MODEL_MAX_OUTPUT_TOKENS = {
    "gemini-live-2.5-flash-preview": 1000000,
    "gemini-2.5-flash-live-preview": 1000000,
    "gemini-2.0-flash-live-001": 1000000,
    "gemini-2.0-flash-exp": 8192,
    "gemini-2.0-flash-thinking-exp-01-21": 64000,
    "gemini-2.5-flash": 65536,
    "gemini-2.5-pro": 65536,
    "gemini-1.5-flash": 8192,
    "gemini-1.5-pro": 8192,
}

MODEL_MAX_INPUT_TOKENS = {
    "gemini-live-2.5-flash-preview": 64000,
    "gemini-2.5-flash-live-preview": 64000,
    "gemini-2.0-flash-live-001": 64000,
    "gemini-2.0-flash-exp": 1048576,
    "gemini-2.0-flash-thinking-exp-01-21": 1048576,
    "gemini-2.5-flash": 1048576,
    "gemini-2.5-pro": 1048576,
    "gemini-1.5-flash": 1048576,
    "gemini-1.5-pro": 2097152,
}


def _load_dotenv_if_available() -> None:
    """Attempt to load a nearby .env file without introducing a hard dependency."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    current = Path(__file__).resolve().parent
    for _ in range(5):
        env_path = current / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            break
        current = current.parent


@dataclass(slots=True)
class GeminiConfig:
    """Configuration for the Gemini Live API client."""

    api_key: str
    model: str = DEFAULT_MODEL
    timeout: float = 60.0
    max_retries: int = 2
    retry_backoff: float = 0.5
    enable_vertex: bool = False
    project_id: Optional[str] = None
    location: str = "us-central1"

    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Load configuration from environment variables and optional .env file."""
        _load_dotenv_if_available()

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY or GOOGLE_API_KEY."
            )

        model = os.getenv("GEMINI_MODEL", DEFAULT_MODEL)
        enable_vertex = os.getenv("GEMINI_VERTEX_AI", "false").lower() == "true"
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCP_PROJECT")
        location = os.getenv("GEMINI_LOCATION", "us-central1")

        return cls(
            api_key=api_key,
            model=model,
            enable_vertex=enable_vertex,
            project_id=project_id,
            location=location,
        )


class GeminiClient:
    """Asynchronous Gemini API client with multimodal support."""

    def __init__(self, config: Optional[GeminiConfig] = None):
        if not GENAI_AVAILABLE:
            raise ImportError(
                "google-genai is not installed. Install with: pip install google-genai"
            )

        self.config = config or GeminiConfig.from_env()

        # Initialize the client
        if self.config.enable_vertex and self.config.project_id:
            self.client = genai.Client(
                vertexai=True,
                project=self.config.project_id,
                location=self.config.location,
            )
        else:
            self.client = genai.Client(api_key=self.config.api_key)

        self._last_usage: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # Helper methods for content preparation
    # ------------------------------------------------------------------
    def _prepare_content(
        self,
        content: Union[str, List[Union[str, bytes, Image.Image, Path]]],
    ) -> List[Union[str, types.Part]]:
        """
        Prepare content for API request, handling text, images, and mixed inputs.

        Args:
            content: String, bytes, PIL Image, Path, or list of these

        Returns:
            List of content parts ready for the API
        """
        if isinstance(content, str):
            return [content]

        if not isinstance(content, list):
            content = [content]

        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, bytes):
                # Determine MIME type from bytes
                mime_type = self._guess_image_mime_type(item)
                parts.append(types.Part.from_bytes(data=item, mime_type=mime_type))
            elif PIL_AVAILABLE and isinstance(item, Image.Image):
                parts.append(item)
            elif isinstance(item, Path):
                parts.append(self._load_image_from_path(item))
            else:
                raise ValueError(f"Unsupported content type: {type(item)}")

        return parts

    def _load_image_from_path(self, path: Path) -> Union[types.Part, Image.Image]:
        """Load image from file path."""
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {path}")

        # Try PIL first
        if PIL_AVAILABLE:
            return Image.open(path)

        # Fallback to bytes
        with open(path, "rb") as f:
            image_bytes = f.read()
        mime_type = self._guess_image_mime_type(image_bytes, path.suffix)
        return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    def _guess_image_mime_type(
        self, data: bytes, extension: Optional[str] = None
    ) -> str:
        """Guess MIME type from image bytes or extension."""
        if extension:
            ext = extension.lower().lstrip(".")
            mime_types = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png",
                "gif": "image/gif",
                "webp": "image/webp",
                "bmp": "image/bmp",
            }
            return mime_types.get(ext, "image/jpeg")

        # Simple magic number detection
        if data[:2] == b"\xff\xd8":
            return "image/jpeg"
        elif data[:8] == b"\x89PNG\r\n\x1a\n":
            return "image/png"
        elif data[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        else:
            return "image/jpeg"  # Default

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def _is_websocket_model(self, model: Optional[str] = None) -> bool:
        """Check if model requires WebSocket Live API."""
        model_name = model or self.config.model
        return model_name in WEBSOCKET_MODELS

    # ------------------------------------------------------------------
    # WebSocket Live API methods
    # ------------------------------------------------------------------
    async def _generate_content_live(
        self,
        content: Union[str, List[Union[str, bytes, Image.Image, Path]]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate content using WebSocket Live API."""
        model_name = model or self.config.model
        parts = self._prepare_content(content)
        
        # Separate text and images
        text_parts = []
        image_parts = []
        
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            else:
                # Image part
                if hasattr(part, 'inline_data'):
                    image_parts.append(part)
                elif isinstance(part, Image.Image) if PIL_AVAILABLE else False:
                    # Convert PIL Image to bytes
                    from io import BytesIO
                    img_byte_arr = BytesIO()
                    part.save(img_byte_arr, format='PNG')
                    image_data = img_byte_arr.getvalue()
                    image_parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type="image/png",
                            data=image_data
                        )
                    ))
                elif isinstance(part, Path):
                    # Load from path
                    image_data = part.read_bytes()
                    mime_type = self._guess_image_mime_type(image_data, part.suffix)
                    image_parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_data
                        )
                    ))
        
        # Combine text
        text_prompt = " ".join(text_parts) if text_parts else "Analyze this."
        
        # Build content parts
        content_parts = [types.Part(text=text_prompt)]
        content_parts.extend(image_parts)
        
        try:
            # Get model-specific max tokens
            model_max = MODEL_MAX_OUTPUT_TOKENS.get(model_name, 8192)
            output_tokens = max_output_tokens or model_max
            output_tokens = min(output_tokens, model_max)  # Ensure within limits
            
            # Build generation config
            gen_config = {
                "temperature": temperature,
                "max_output_tokens": output_tokens,
            }
            
            # Add optional parameters
            if top_p is not None:
                gen_config["top_p"] = top_p
            if top_k is not None:
                gen_config["top_k"] = top_k
            
            # Configure Live API session
            config_params = {
                "response_modalities": [types.Modality.TEXT],
                "generation_config": gen_config,
            }
            
            # Add system instruction if provided
            if system_instruction:
                config_params["system_instruction"] = system_instruction
            
            config = types.LiveConnectConfig(**config_params)
            
            # Connect to Live API
            async with self.client.aio.live.connect(model=model_name, config=config) as session:
                # Send content
                await session.send_client_content(
                    turns=[
                        types.Content(
                            role="user",
                            parts=content_parts
                        )
                    ]
                )
                
                # Collect response
                response_parts = []
                async for message in session.receive():
                    if message.text:
                        response_parts.append(message.text)
                
                full_response = ''.join(response_parts)
                
                # Note: Live API doesn't provide detailed usage metadata
                return {
                    "content": full_response,
                    "model": model_name,
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                }
                
        except Exception as e:
            raise RuntimeError(f"Gemini Live API error: {str(e)}") from e

    async def _stream_content_live(
        self,
        content: Union[str, List[Union[str, bytes, Image.Image, Path]]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Stream content using WebSocket Live API."""
        model_name = model or self.config.model
        parts = self._prepare_content(content)
        
        # Separate text and images
        text_parts = []
        image_parts = []
        
        for part in parts:
            if isinstance(part, str):
                text_parts.append(part)
            else:
                # Image part
                if isinstance(part, Image.Image) if PIL_AVAILABLE else False:
                    from io import BytesIO
                    img_byte_arr = BytesIO()
                    part.save(img_byte_arr, format='PNG')
                    image_data = img_byte_arr.getvalue()
                    image_parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type="image/png",
                            data=image_data
                        )
                    ))
                elif isinstance(part, Path):
                    image_data = part.read_bytes()
                    mime_type = self._guess_image_mime_type(image_data, part.suffix)
                    image_parts.append(types.Part(
                        inline_data=types.Blob(
                            mime_type=mime_type,
                            data=image_data
                        )
                    ))
        
        text_prompt = " ".join(text_parts) if text_parts else "Analyze this."
        content_parts = [types.Part(text=text_prompt)]
        content_parts.extend(image_parts)
        
        try:
            # Get model-specific max tokens
            model_max = MODEL_MAX_OUTPUT_TOKENS.get(model_name, 8192)
            output_tokens = max_output_tokens or model_max
            output_tokens = min(output_tokens, model_max)  # Ensure within limits
            
            # Build generation config
            gen_config = {
                "temperature": temperature,
                "max_output_tokens": output_tokens,
            }
            
            # Add optional parameters
            if top_p is not None:
                gen_config["top_p"] = top_p
            if top_k is not None:
                gen_config["top_k"] = top_k
            
            # Configure Live API session
            config_params = {
                "response_modalities": [types.Modality.TEXT],
                "generation_config": gen_config,
            }
            
            # Add system instruction if provided
            if system_instruction:
                config_params["system_instruction"] = system_instruction
            
            config = types.LiveConnectConfig(**config_params)
            
            async with self.client.aio.live.connect(model=model_name, config=config) as session:
                await session.send_client_content(
                    turns=[types.Content(role="user", parts=content_parts)]
                )
                
                chunk_count = 0
                async for message in session.receive():
                    if message.text:
                        chunk_count += 1
                        yield {
                            "content": message.text,
                            "usage": {},
                            "is_final": False,
                            "chunk_index": chunk_count,
                        }
                
                # Send final marker
                yield {
                    "content": "",
                    "usage": {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    },
                    "is_final": True,
                    "chunk_index": chunk_count,
                }
                
        except Exception as e:
            raise RuntimeError(f"Gemini Live streaming error: {str(e)}") from e

    # ------------------------------------------------------------------
    # Core API methods
    # ------------------------------------------------------------------
    async def generate_content(
        self,
        content: Union[str, List[Union[str, bytes, Image.Image, Path]]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Generate content with support for text and images.

        Args:
            content: Text, image bytes, PIL Image, Path, or list of these
            model: Model name (uses config default if None)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            max_output_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter 0.0-1.0
            top_k: Top-k sampling parameter
            system_instruction: System-level instruction for the model
            **kwargs: Additional parameters

        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        # Check if we should use Live API
        if self._is_websocket_model(model):
            return await self._generate_content_live(
                content,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k,
                system_instruction=system_instruction,
                **kwargs
            )
        
        model_name = model or self.config.model
        parts = self._prepare_content(content)

        # Prepare generation config
        config_dict = {"temperature": temperature}
        if max_output_tokens:
            config_dict["max_output_tokens"] = max_output_tokens
        if top_p is not None:
            config_dict["top_p"] = top_p
        if top_k is not None:
            config_dict["top_k"] = top_k

        generation_config = types.GenerateContentConfig(**config_dict)

        # Build request parameters
        request_params = {
            "model": model_name,
            "contents": parts,
            "config": generation_config,
        }

        if system_instruction:
            request_params["system_instruction"] = system_instruction

        request_params.update(kwargs)

        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content, **request_params
            )

            # Extract usage metadata
            usage = {}
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                metadata = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(metadata, "prompt_token_count", 0),
                    "completion_tokens": getattr(metadata, "candidates_token_count", 0),
                    "total_tokens": getattr(metadata, "total_token_count", 0),
                }
            self._last_usage = usage

            return {
                "content": response.text,
                "model": model_name,
                "usage": usage,
            }

        except Exception as e:
            raise RuntimeError(f"Gemini API error: {str(e)}") from e

    async def stream_content(
        self,
        content: Union[str, List[Union[str, bytes, Image.Image, Path]]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream content generation with support for text and images.

        Args:
            content: Text, image bytes, PIL Image, Path, or list of these
            model: Model name (uses config default if None)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            max_output_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter 0.0-1.0
            top_k: Top-k sampling parameter
            system_instruction: System-level instruction for the model
            **kwargs: Additional parameters

        Yields:
            Dict with 'content', 'usage', 'is_final' keys
        """
        # Check if we should use Live API
        if self._is_websocket_model(model):
            async for chunk in self._stream_content_live(
                content,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k,
                system_instruction=system_instruction,
                **kwargs
            ):
                yield chunk
            return
        
        model_name = model or self.config.model
        parts = self._prepare_content(content)

        # Prepare generation config
        config_dict = {"temperature": temperature}
        if max_output_tokens:
            config_dict["max_output_tokens"] = max_output_tokens
        if top_p is not None:
            config_dict["top_p"] = top_p
        if top_k is not None:
            config_dict["top_k"] = top_k

        generation_config = types.GenerateContentConfig(**config_dict)

        # Build request parameters
        request_params = {
            "model": model_name,
            "contents": parts,
            "config": generation_config,
        }

        if system_instruction:
            request_params["system_instruction"] = system_instruction

        request_params.update(kwargs)

        try:
            # Stream in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            stream_iterator = await loop.run_in_executor(
                None, lambda: self.client.models.generate_content_stream(**request_params)
            )

            chunk_count = 0
            for chunk in stream_iterator:
                chunk_count += 1
                is_final = False

                # Extract usage metadata from final chunk
                usage = {}
                if hasattr(chunk, "usage_metadata") and chunk.usage_metadata:
                    metadata = chunk.usage_metadata
                    usage = {
                        "prompt_tokens": getattr(metadata, "prompt_token_count", 0),
                        "completion_tokens": getattr(metadata, "candidates_token_count", 0),
                        "total_tokens": getattr(metadata, "total_token_count", 0),
                    }
                    self._last_usage = usage
                    is_final = True

                yield {
                    "content": chunk.text,
                    "usage": usage,
                    "is_final": is_final,
                    "chunk_index": chunk_count,
                }

        except Exception as e:
            raise RuntimeError(f"Gemini streaming error: {str(e)}") from e

    async def chat(
        self,
        messages: Sequence[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Perform a chat completion with conversation history.

        Args:
            messages: List of messages [{"role": "user", "content": "..."}, ...]
            model: Model name (uses config default if None)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            max_output_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter 0.0-1.0
            top_k: Top-k sampling parameter
            system_instruction: System-level instruction for the model
            **kwargs: Additional parameters

        Returns:
            Dict with 'content', 'model', 'usage' keys
        """
        # Convert messages to Gemini format
        if messages and messages[-1].get("role") == "user":
            # Use the last user message
            last_message = messages[-1]["content"]
            return await self.generate_content(
                last_message,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k,
                system_instruction=system_instruction,
                **kwargs,
            )
        else:
            raise ValueError("Last message must be from user")

    async def stream_chat(
        self,
        messages: Sequence[Dict[str, Any]],
        *,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_output_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        top_k: Optional[int] = None,
        system_instruction: Optional[str] = None,
        **kwargs: Any,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Stream chat responses token by token.

        Args:
            messages: List of messages [{"role": "user", "content": "..."}, ...]
            model: Model name (uses config default if None)
            temperature: Sampling temperature 0.0-2.0 (default: 0.7)
            max_output_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter 0.0-1.0
            top_k: Top-k sampling parameter
            system_instruction: System-level instruction for the model
            **kwargs: Additional parameters

        Yields:
            Dict with 'content', 'usage', 'is_final' keys
        """
        # Convert messages to Gemini format
        if messages and messages[-1].get("role") == "user":
            last_message = messages[-1]["content"]
            async for chunk in self.stream_content(
                last_message,
                model=model,
                temperature=temperature,
                max_output_tokens=max_output_tokens,
                top_p=top_p,
                top_k=top_k,
                system_instruction=system_instruction,
                **kwargs,
            ):
                yield chunk
        else:
            raise ValueError("Last message must be from user")

    @property
    def last_usage(self) -> Optional[Dict[str, Any]]:
        """Get the usage metadata from the last request."""
        return self._last_usage


__all__ = ["GeminiConfig", "GeminiClient", "DEFAULT_MODEL", "LIVE_MODELS", "MODEL_MAX_OUTPUT_TOKENS", "MODEL_MAX_INPUT_TOKENS", "WEBSOCKET_MODELS"]

