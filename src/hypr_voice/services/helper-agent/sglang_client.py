"""
SGLang Client for Helper Agent

This module provides an async client for communicating with SGLang service
running Qwen 3 1.7B model on port 30000.
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)


@dataclass
class SGLangConfig:
    """Configuration for SGLang client."""
    host: str = "localhost"
    port: int = 30000
    model: str = "qwen3-1.7b"
    timeout: int = 30
    health_check_interval: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0


class SGLangClient:
    """
    Async client for SGLang service communication.

    This client handles communication with the SGLang engine using its custom API format.
    It includes health checking, error handling, and retry logic.
    """

    def __init__(self, config: SGLangConfig):
        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_health_check = 0
        self.is_healthy = False

    async def __aenter__(self):
        """Async context manager entry."""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    async def initialize(self):
        """Initialize the HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={"Content-Type": "application/json"}
            )
        logger.info(f"SGLang client initialized for {self.base_url}")

    async def cleanup(self):
        """Cleanup the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("SGLang client cleaned up")

    async def health_check(self) -> bool:
        """
        Check if the SGLang service is healthy.

        Returns:
            True if service is healthy, False otherwise.
        """
        current_time = time.time()

        # Cache health check result for configured interval
        if current_time - self.last_health_check < self.config.health_check_interval:
            return self.is_healthy

        try:
            if not self.session:
                await self.initialize()

            # Try common health endpoints
            health_endpoints = ["/health", "/v1/health", "/status", "/ping"]

            for endpoint in health_endpoints:
                try:
                    async with self.session.get(f"{self.base_url}{endpoint}") as response:
                        if response.status == 200:
                            self.is_healthy = True
                            self.last_health_check = current_time
                            logger.debug(f"SGLang service healthy via {endpoint}")
                            return True
                except Exception:
                    continue

            # If no standard health endpoint works, try a simple generation
            test_response = await self.generate_text("test", max_tokens=1)
            if test_response:
                self.is_healthy = True
                self.last_health_check = current_time
                return True

        except Exception as e:
            logger.warning(f"SGLang health check failed: {e}")

        self.is_healthy = False
        self.last_health_check = current_time
        return False

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        stop_sequences: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Generate text using the SGLang service.

        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
            stop_sequences: List of stop sequences

        Returns:
            Generated text or None if generation failed.
        """
        if not await self.health_check():
            logger.error("SGLang service is not healthy")
            return None

        # Prepare request payload for SGLang custom format
        payload = {
            "text": prompt,
            "sampling_params": {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "stop": stop_sequences or []
            }
        }

        # Try different SGLang API endpoints
        endpoints = ["/generate", "/v1/generate", "/completions"]

        for attempt in range(self.config.max_retries):
            try:
                for endpoint in endpoints:
                    try:
                        async with self.session.post(
                            f"{self.base_url}{endpoint}",
                            json=payload
                        ) as response:
                            if response.status == 200:
                                result = await response.json()

                                # Handle different response formats
                                if "text" in result:
                                    return result["text"]
                                elif "choices" in result and result["choices"]:
                                    return result["choices"][0]["text"]
                                elif "output" in result:
                                    return result["output"]
                                else:
                                    logger.warning(f"Unexpected response format: {result}")

                    except aiohttp.ClientError as e:
                        logger.debug(f"Endpoint {endpoint} failed: {e}")
                        continue

                # If all endpoints failed, wait and retry
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

            except Exception as e:
                logger.error(f"Text generation attempt {attempt + 1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (2 ** attempt))

        logger.error("All text generation attempts failed")
        return None

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Optional[str]:
        """
        Generate chat completion using the SGLang service.

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            top_p: Top-p sampling parameter

        Returns:
            Generated response or None if generation failed.
        """
        # Convert messages to prompt format for Qwen
        prompt = self._format_messages_as_prompt(messages)
        return await self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p
        )

    def _format_messages_as_prompt(self, messages: List[Dict[str, str]]) -> str:
        """
        Format chat messages as a prompt for Qwen model.

        Args:
            messages: List of message dictionaries

        Returns:
            Formatted prompt string.
        """
        # Qwen chat format
        formatted_prompt = ""

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                formatted_prompt += f"<|system|>\n{content}\n"
            elif role == "user":
                formatted_prompt += f"<|user|>\n{content}\n"
            elif role == "assistant":
                formatted_prompt += f"