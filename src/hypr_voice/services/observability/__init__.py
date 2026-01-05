"""
Observability helpers (Claude hooks compatible emitter).

This package exposes a lightweight, non-blocking event emitter used to forward
Hypr-Voice runtime events (transcription, routing, TTS, sandbox) to the same
endpoint consumed by the Claude hook stack. See docs/integration/SHARD_03_OBSERVABILITY_EMITTER.md.
"""

from .claude_hooks import ClaudeEventEmitter, emitter

__all__ = ["ClaudeEventEmitter", "emitter"]

