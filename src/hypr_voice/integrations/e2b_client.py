"""Minimal E2B sandbox client wrapper.

This wraps the official `e2b` SDK when available. If the SDK is missing or the
API key is not configured, the client raises a clear error so callers can
fallback to local execution.

Capabilities (MVP):
- create sandbox
- exec command
- list files (optional)
- destroy sandbox

Environment:
- E2B_API_KEY (required when enabled)
- HYPR_VOICE_E2B_TEMPLATE (optional)
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Optional


class E2BUnavailable(RuntimeError):
    pass


@dataclass
class ExecResult:
    stdout: str
    stderr: str
    exit_code: int


class E2BClient:
    def __init__(self, api_key: Optional[str] = None, template: Optional[str] = None):
        self.api_key = api_key or os.getenv("E2B_API_KEY")
        self.template = template or os.getenv("HYPR_VOICE_E2B_TEMPLATE")
        self._sandbox = None
        self._sandbox_id: Optional[str] = None

    async def _ensure_client(self):
        try:
            from e2b import Sandbox
        except Exception as e:  # noqa: BLE001
            raise E2BUnavailable("e2b SDK not installed; pip install e2b") from e
        if not self.api_key:
            raise E2BUnavailable("E2B_API_KEY not set")

        if self._sandbox is None:
            self._sandbox = Sandbox(api_key=self.api_key, template=self.template)
            self._sandbox_id = self._sandbox.id
        return self._sandbox

    @property
    def sandbox_id(self) -> Optional[str]:
        return self._sandbox_id

    async def exec(self, command: str, workdir: str | None = None, timeout: int = 120) -> ExecResult:
        sb = await self._ensure_client()
        # e2b exec is synchronous; run in thread to avoid blocking loop
        def _run():
            res = sb.exec(command, cwd=workdir, timeout=timeout)
            return ExecResult(stdout=res.stdout, stderr=res.stderr, exit_code=res.exit_code)

        return await asyncio.to_thread(_run)

    async def destroy(self):
        if self._sandbox is not None:
            def _destroy():
                self._sandbox.close()

            await asyncio.to_thread(_destroy)
        self._sandbox = None
        self._sandbox_id = None


# Singleton helper
_client: Optional[E2BClient] = None


def get_client() -> E2BClient:
    global _client
    if _client is None:
        _client = E2BClient()
    return _client

