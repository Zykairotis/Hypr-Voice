"""
Hyprland IPC Integration

Provides communication with Hyprland compositor for:
- Keybinding triggers (F10 agent mode)
- Window focus detection
- Notification dispatch
"""

import asyncio
import json
import logging
import os
import socket
from pathlib import Path
from typing import Optional, Callable, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class HyprlandEvent:
    """Event from Hyprland IPC."""
    event_type: str
    data: str
    
    @classmethod
    def parse(cls, line: str) -> Optional["HyprlandEvent"]:
        """Parse an event line from Hyprland socket."""
        if ">>" in line:
            parts = line.split(">>", 1)
            return cls(event_type=parts[0], data=parts[1] if len(parts) > 1 else "")
        return None


class HyprlandIPC:
    """
    Hyprland IPC client for window management and notifications.
    
    Connects to Hyprland's Unix socket for:
    - Active window tracking
    - Workspace changes
    - Custom event handling
    """
    
    def __init__(self):
        self.signature = os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")
        self.socket_path = self._get_socket_path()
        self.event_socket_path = self._get_event_socket_path()
        self._event_handlers: dict[str, list[Callable]] = {}
        self._running = False
        
    def _get_socket_path(self) -> Optional[Path]:
        """Get the Hyprland command socket path."""
        if not self.signature:
            return None
        
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        return Path(xdg_runtime) / "hypr" / self.signature / ".socket.sock"
    
    def _get_event_socket_path(self) -> Optional[Path]:
        """Get the Hyprland event socket path."""
        if not self.signature:
            return None
        
        xdg_runtime = os.environ.get("XDG_RUNTIME_DIR", "/tmp")
        return Path(xdg_runtime) / "hypr" / self.signature / ".socket2.sock"
    
    def is_available(self) -> bool:
        """Check if Hyprland IPC is available."""
        return self.socket_path is not None and self.socket_path.exists()
    
    async def send_command(self, command: str) -> Optional[str]:
        """
        Send a command to Hyprland.
        
        Args:
            command: Hyprland command (e.g., "activewindow", "dispatch exec ...")
            
        Returns:
            Command response or None on error
        """
        if not self.socket_path or not self.socket_path.exists():
            logger.warning("Hyprland socket not available")
            return None
        
        try:
            reader, writer = await asyncio.open_unix_connection(str(self.socket_path))
            
            writer.write(command.encode())
            await writer.drain()
            
            response = await reader.read(8192)
            
            writer.close()
            await writer.wait_closed()
            
            return response.decode().strip()
            
        except Exception as e:
            logger.error(f"Hyprland command error: {e}")
            return None
    
    async def get_active_window(self) -> Optional[dict]:
        """Get information about the currently active window."""
        response = await self.send_command("j/activewindow")
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        return None
    
    async def get_workspaces(self) -> list[dict]:
        """Get all workspaces."""
        response = await self.send_command("j/workspaces")
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass
        return []
    
    async def dispatch(self, dispatcher: str, args: str = "") -> bool:
        """
        Execute a Hyprland dispatcher.
        
        Args:
            dispatcher: Dispatcher name (e.g., "exec", "workspace")
            args: Dispatcher arguments
            
        Returns:
            True if successful
        """
        command = f"dispatch {dispatcher} {args}".strip()
        response = await self.send_command(command)
        return response == "ok"
    
    def on_event(self, event_type: str, handler: Callable[[HyprlandEvent], Any]):
        """
        Register an event handler.
        
        Args:
            event_type: Event type to handle (e.g., "activewindow", "workspace")
            handler: Callback function
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    async def start_event_listener(self):
        """Start listening for Hyprland events."""
        if not self.event_socket_path or not self.event_socket_path.exists():
            logger.warning("Hyprland event socket not available")
            return
        
        self._running = True
        
        try:
            reader, _ = await asyncio.open_unix_connection(str(self.event_socket_path))
            
            while self._running:
                line = await reader.readline()
                if not line:
                    break
                
                event = HyprlandEvent.parse(line.decode().strip())
                if event and event.event_type in self._event_handlers:
                    for handler in self._event_handlers[event.event_type]:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event)
                            else:
                                handler(event)
                        except Exception as e:
                            logger.error(f"Event handler error: {e}")
                            
        except Exception as e:
            logger.error(f"Event listener error: {e}")
        finally:
            self._running = False
    
    def stop_event_listener(self):
        """Stop the event listener."""
        self._running = False


async def send_notification(
    title: str,
    message: str,
    urgency: str = "normal",
    timeout: int = 5000,
    app_name: str = "Hypr-Voice",
) -> bool:
    """
    Send a desktop notification.
    
    Args:
        title: Notification title
        message: Notification body
        urgency: low, normal, or critical
        timeout: Timeout in milliseconds
        app_name: Application name
        
    Returns:
        True if notification was sent
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "notify-send",
            "-a", app_name,
            "-u", urgency,
            "-t", str(timeout),
            title,
            message,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        await proc.wait()
        return proc.returncode == 0
    except Exception as e:
        logger.error(f"Notification error: {e}")
        return False


class AgentModeHandler:
    """
    Handler for F10 agent mode trigger.
    
    Manages the flow:
    1. F10 press -> Start recording
    2. F10 release -> Stop recording, transcribe, send to orchestrator
    """
    
    def __init__(self, orchestrator_port: int = 9091):
        self.orchestrator_port = orchestrator_port
        self._recording = False
        
    async def on_key_press(self):
        """Handle F10 key press - start agent input mode."""
        self._recording = True
        
        # Notify user
        await send_notification(
            "Agent Mode",
            "Recording... Release F10 to process",
            urgency="low",
            timeout=2000,
        )
        
        # Send start signal to orchestrator
        await self._send_to_orchestrator({"action": "start_agent_input"})
    
    async def on_key_release(self, transcribed_text: Optional[str] = None):
        """Handle F10 key release - process input."""
        self._recording = False
        
        if transcribed_text:
            # Send transcribed text to orchestrator
            await self._send_to_orchestrator({
                "action": "process_with_agent",
                "query": transcribed_text,
            })
            
            await send_notification(
                "Agent Processing",
                f"Processing: {transcribed_text[:50]}...",
                timeout=3000,
            )
    
    async def _send_to_orchestrator(self, data: dict) -> bool:
        """Send data to orchestrator via Unix socket or TCP."""
        try:
            reader, writer = await asyncio.open_connection(
                "localhost", self.orchestrator_port
            )
            
            writer.write(json.dumps(data).encode())
            await writer.drain()
            
            writer.close()
            await writer.wait_closed()
            
            return True
            
        except Exception as e:
            logger.error(f"Orchestrator connection error: {e}")
            return False
