#!/usr/bin/env python3
"""
WebSocket server for real-time context updates.
Integrates with the ContextManager to provide live context data to the web UI.
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any
import websockets
from websockets.server import WebSocketServerProtocol

logger = logging.getLogger(__name__)

class ContextWebSocketServer:
    """WebSocket server for broadcasting context updates."""

    def __init__(self, host: str = 'localhost', port: int = 9091):
        self.host = host
        self.port = port
        self.clients: Dict[str, WebSocketServerProtocol] = {}
        self.running = False
        self.app_detector = None  # Will be injected

        # Import context manager
        try:
            from context_manager import get_context_manager
            self.context_manager = get_context_manager()
            logger.info("Context manager initialized")
        except ImportError:
            logger.error("Context manager not available")
            self.context_manager = None

    def set_app_detector(self, detector):
        """Set the application detector instance."""
        self.app_detector = detector

    async def register_client(self, websocket: WebSocketServerProtocol, path: str = ""):
        """Register a new WebSocket client."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        self.clients[client_id] = websocket
        logger.info(f"Client connected: {client_id}")

        try:
            await self.send_initial_context(websocket)

            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_message(client_id, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON from {client_id}")
                except Exception as e:
                    logger.error(f"Error handling message from {client_id}: {e}")
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            logger.info(f"Client removed: {client_id}")

    async def send_initial_context(self, websocket: WebSocketServerProtocol):
        """Send initial context data to a new client."""
        if not self.context_manager:
            return

        try:
            # Get current window info if available
            window_info = None
            if self.app_detector:
                window_info = self.app_detector.get_active_window()

            context_data = self.context_manager.get_comprehensive_context(window_info)
            await websocket.send(json.dumps({
                'type': 'context_update',
                'data': context_data
            }))
        except Exception as e:
            logger.error(f"Error sending initial context: {e}")

    async def handle_message(self, client_id: str, data: Dict[str, Any]):
        """Handle incoming message from client."""
        message_type = data.get('type')

        if message_type == 'ping':
            await self.send_pong(client_id)
        elif message_type == 'request_context':
            await self.send_context_update(client_id)
        elif message_type == 'update_filters':
            # Store client-specific filters
            pass

    async def send_pong(self, client_id: str):
        """Send pong response to ping."""
        if client_id in self.clients:
            await self.clients[client_id].send(json.dumps({
                'type': 'pong',
                'timestamp': int(time.time())
            }))

    async def send_context_update(self, client_id: str = None):
        """Send context update to all clients or specific client."""
        if not self.context_manager:
            return

        try:
            # Get current window info if available
            window_info = None
            if self.app_detector:
                window_info = self.app_detector.get_active_window()

            # Get current context
            context_data = self.context_manager.get_comprehensive_context(window_info)

            # Enrich with backend + vocabulary metadata if available
            backend_name = None
            vocab_name = None
            try:
                from window_backends import detect_backend
                backend_name = detect_backend().name
            except Exception:
                pass
            try:
                from vocabulary_manager import get_vocabulary_manager
                vm = get_vocabulary_manager()
                vocab_name = vm.current_vocabulary
            except Exception:
                pass

            context_data = {
                **context_data,
                'meta': {
                    'backend': backend_name,
                    'vocabulary': vocab_name,
                }
            }

            # Format for WebSocket
            message = json.dumps({
                'type': 'context_update',
                'data': context_data,
                'timestamp': int(time.time())
            })

            if client_id and client_id in self.clients:
                # Send to specific client
                await self.clients[client_id].send(message)
            else:
                # Broadcast to all clients
                if self.clients:
                    await asyncio.gather(
                        *[ws.send(message) for ws in self.clients.values()],
                        return_exceptions=True
                    )
        except Exception as e:
            logger.error(f"Error sending context update: {e}")

    async def broadcast_window_change(self, window_info: Dict[str, Any]):
        """Broadcast window change event."""
        if not self.context_manager:
            return

        try:
            # Extract context from window (backend-agnostic)
            window_context = self.context_manager.extract_context_from_window(window_info)
            if isinstance(window_info, dict) and 'backend' in window_info:
                window_context['backend'] = window_info.get('backend')

            # Ensure JSON-serializable payload
            if isinstance(window_context.get('keywords'), set):
                window_context['keywords'] = list(window_context['keywords'])

            message = json.dumps({
                'type': 'window_change',
                'data': window_context,
                'timestamp': int(time.time())
            })

            if self.clients:
                await asyncio.gather(
                    *[ws.send(message) for ws in self.clients.values()],
                    return_exceptions=True
                )
        except Exception as e:
            logger.error(f"Error broadcasting window change: {e}")

    async def cleanup_old_data(self):
        """Periodically clean up old context data."""
        # This could implement data retention policies
        pass

    async def run(self):
        """Start the WebSocket server."""
        self.running = True
        logger.info(f"Starting Context WebSocket Server on {self.host}:{self.port}")

        # Background task for periodic updates
        asyncio.create_task(self.update_loop())

        # Background task for cleanup
        asyncio.create_task(self.cleanup_loop())

        # Start WebSocket server
        async with websockets.serve(self.register_client, self.host, self.port):
            logger.info("WebSocket server running")
            await asyncio.Future()  # Run forever

    async def update_loop(self):
        """Periodically send context updates."""
        while self.running:
            try:
                await asyncio.sleep(5)  # Update every 5 seconds
                await self.send_context_update()
            except Exception as e:
                logger.error(f"Error in update loop: {e}")

    async def cleanup_loop(self):
        """Periodically clean up old data."""
        while self.running:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes
                await self.cleanup_old_data()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")

    def stop(self):
        """Stop the WebSocket server."""
        self.running = False
        logger.info("Stopping WebSocket server")


# Context Monitor - integrates with app_detector for window tracking
class ContextMonitor:
    """Monitor for context changes."""

    def __init__(self, ws_server: ContextWebSocketServer):
        self.ws_server = ws_server
        self.last_window = None

        # Import application detector
        try:
            from scripts.app_detector import ApplicationDetector
            self.app_detector = ApplicationDetector()
            logger.info("Application detector initialized")
            
            # Inject into WS server
            self.ws_server.set_app_detector(self.app_detector)
            
        except ImportError:
            logger.warning("Application detector not available")
            self.app_detector = None

    async def monitor_loop(self):
        """Monitor for context changes."""
        while True:
            try:
                if self.app_detector:
                    # Check for window changes
                    window_info = self.app_detector.get_active_window()

                    if window_info:
                        # Check if window changed
                        current_window = f"{window_info.get('class', '')}-{window_info.get('title', '')}"

                        if current_window != self.last_window:
                            logger.info(f"Window changed: {window_info.get('class')}")
                            self.last_window = current_window

                            # Broadcast window change
                            await self.ws_server.broadcast_window_change(window_info)

                            # Update vocabulary with new window context
                            try:
                                from vocabulary_manager import get_vocabulary_manager
                                vocab_manager = get_vocabulary_manager()
                                if vocab_manager:
                                    app_class = window_info.get('class', '')
                                    app_title = window_info.get('title', '')
                                    vocab_manager.update_vocabulary(app_class, app_title, backend=self.app_detector.backend.name)
                                    try:
                                        import hook_bus
                                        hook_bus.emit('window_change', window_info=window_info)
                                    except Exception:
                                        pass
                            except ImportError:
                                pass

                await asyncio.sleep(2)  # Check every 2 seconds
            except Exception as e:
                logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(5)


async def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create WebSocket server
    ws_server = ContextWebSocketServer(host='0.0.0.0', port=9091)

    # Create monitor (which now injects app_detector into ws_server)
    monitor = ContextMonitor(ws_server)

    try:
        # Start monitor task
        monitor_task = asyncio.create_task(monitor.monitor_loop())

        # Start WebSocket server
        await ws_server.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        ws_server.stop()
        monitor_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
