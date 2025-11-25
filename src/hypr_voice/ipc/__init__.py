"""
Hypr-Voice IPC Module

Inter-process communication for Hyprland integration.
"""

from .hyprland import HyprlandIPC, send_notification
from .websocket import WebSocketServer, OrchestratorWebSocket

__all__ = [
    "HyprlandIPC",
    "send_notification",
    "WebSocketServer",
    "OrchestratorWebSocket",
]
