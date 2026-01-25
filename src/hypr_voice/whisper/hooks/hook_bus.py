"""Simple hook/event bus for Hypr-Whisper.

Events (current):
  - backend_change(backend_name)
  - window_change(window_info)
  - vocab_change(vocab_name, app_name, backend_name)

Design: in-process, best-effort: exceptions are logged and swallowed so hooks
cannot break the main flow.
"""

import logging
from typing import Callable, Dict, List

logger = logging.getLogger(__name__)


_hooks: Dict[str, List[Callable]] = {}


def register(event: str, func: Callable):
    _hooks.setdefault(event, []).append(func)
    logger.debug("Registered hook %s for event %s", getattr(func, "__name__", func), event)


def emit(event: str, **kwargs):
    for func in _hooks.get(event, []):
        try:
            func(**kwargs)
        except Exception as e:
            logger.error("Hook %s failed on %s: %s", getattr(func, "__name__", func), event, e)
