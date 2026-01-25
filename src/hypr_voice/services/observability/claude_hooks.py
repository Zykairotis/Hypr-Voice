import asyncio
import json
import os
import logging
from datetime import datetime, timezone
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


def _iso_now() -> str:
    return datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()


class ClaudeEventEmitter:
    """Non-blocking HTTP emitter for observability events.

    Payloads are aligned with the `send_event.py` helper from the
    claude-code-hooks-multi-agent-observability repo.
    """

    def __init__(self):
        self.enabled = os.getenv("CLAUDE_HOOKS_ENABLED", "0") == "1"
        self.source_app = os.getenv("CLAUDE_HOOKS_SOURCE_APP", "hypr-voice")
        self.obs_url = os.getenv("CLAUDE_HOOKS_OBS_URL", "")

        if self.enabled and not self.obs_url:
            logger.warning("CLAUDE_HOOKS_ENABLED=1 but CLAUDE_HOOKS_OBS_URL is not set; disabling emitter")
            self.enabled = False

    async def emit(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        *,
        severity: str = "info",
        session_id: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        data = {
            "source_app": self.source_app,
            "event_type": event_type,
            "session_id": session_id,
            "payload": payload or {},
            "severity": severity,
            "ts": _iso_now(),
        }

        # Fire-and-forget; errors should never break the user flow
        asyncio.create_task(self._post(data))

    async def _post(self, data: dict[str, Any]) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.obs_url, json=data, timeout=5) as resp:
                    if resp.status >= 400:
                        body = await resp.text()
                        logger.debug(f"Observability emit failed {resp.status}: {body}")
        except Exception as e:  # noqa: BLE001
            logger.debug(f"Observability emit error: {e}")


# Singleton for convenience
emitter = ClaudeEventEmitter()

