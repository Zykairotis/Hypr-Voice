"""
WebSocket Server

Real-time communication for web-ui and external clients.
"""

import asyncio
import json
import logging
from typing import Any, Callable, Optional, Set
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

# Try to import websockets
try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets package not available")


@dataclass
class WebSocketClient:
    """Represents a connected WebSocket client."""
    client_id: str
    websocket: Any
    subscriptions: Set[str]
    
    async def send(self, data: dict):
        """Send data to this client."""
        try:
            await self.websocket.send(json.dumps(data))
        except Exception as e:
            logger.error(f"Send error to {self.client_id}: {e}")


class WebSocketServer:
    """
    WebSocket server for real-time orchestrator events.
    
    Provides:
    - Client connection management
    - Event broadcasting
    - Subscription-based message routing
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9091):
        self.host = host
        self.port = port
        self.clients: dict[str, WebSocketClient] = {}
        self._server = None
        self._running = False
        self._message_handlers: dict[str, Callable] = {}
    
    def on_message(self, message_type: str, handler: Callable):
        """Register a message handler."""
        self._message_handlers[message_type] = handler
    
    async def start(self):
        """Start the WebSocket server."""
        if not WEBSOCKETS_AVAILABLE:
            logger.error("Cannot start WebSocket server: websockets package not available")
            return
        
        self._running = True
        self._server = await websockets.serve(
            self._handle_client,
            self.host,
            self.port,
        )
        
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
    
    async def stop(self):
        """Stop the WebSocket server."""
        self._running = False
        
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        
        # Close all client connections
        for client in list(self.clients.values()):
            try:
                await client.websocket.close()
            except:
                pass
        
        self.clients.clear()
        logger.info("WebSocket server stopped")
    
    async def _handle_client(self, websocket, path):
        """Handle a new WebSocket connection."""
        client_id = str(uuid.uuid4())
        client = WebSocketClient(
            client_id=client_id,
            websocket=websocket,
            subscriptions=set(),
        )
        
        self.clients[client_id] = client
        logger.info(f"Client connected: {client_id}")
        
        # Send welcome message
        await client.send({
            "type": "connected",
            "client_id": client_id,
        })
        
        try:
            async for message in websocket:
                await self._process_message(client, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        except Exception as e:
            logger.error(f"Client error: {e}")
        finally:
            del self.clients[client_id]
            logger.info(f"Client disconnected: {client_id}")
    
    async def _process_message(self, client: WebSocketClient, raw_message: str):
        """Process an incoming message."""
        try:
            message = json.loads(raw_message)
        except json.JSONDecodeError:
            await client.send({"type": "error", "error": "Invalid JSON"})
            return
        
        msg_type = message.get("type", "")
        
        # Handle built-in message types
        if msg_type == "ping":
            await client.send({"type": "pong", "client_id": client.client_id})
            return
        
        if msg_type == "subscribe":
            topic = message.get("topic", "")
            if topic:
                client.subscriptions.add(topic)
                await client.send({"type": "subscribed", "topic": topic})
            return
        
        if msg_type == "unsubscribe":
            topic = message.get("topic", "")
            client.subscriptions.discard(topic)
            await client.send({"type": "unsubscribed", "topic": topic})
            return
        
        # Handle custom message types
        if msg_type in self._message_handlers:
            handler = self._message_handlers[msg_type]
            try:
                if asyncio.iscoroutinefunction(handler):
                    response = await handler(message, client)
                else:
                    response = handler(message, client)
                
                if response:
                    await client.send(response)
            except Exception as e:
                logger.error(f"Handler error for {msg_type}: {e}")
                await client.send({"type": "error", "error": str(e)})
    
    async def broadcast(self, data: dict, topic: Optional[str] = None):
        """
        Broadcast data to all clients or to subscribers of a topic.
        
        Args:
            data: Data to broadcast
            topic: Optional topic to filter clients
        """
        for client in list(self.clients.values()):
            if topic is None or topic in client.subscriptions or "all" in client.subscriptions:
                await client.send(data)
    
    async def send_to_client(self, client_id: str, data: dict):
        """Send data to a specific client."""
        client = self.clients.get(client_id)
        if client:
            await client.send(data)
    
    def get_client_count(self) -> int:
        """Get the number of connected clients."""
        return len(self.clients)


class OrchestratorWebSocket(WebSocketServer):
    """
    WebSocket server specifically for orchestrator events.
    
    Handles:
    - Agent spawn/destroy notifications
    - Query processing events
    - Real-time agent output streaming
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 9091):
        super().__init__(host, port)
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Set up orchestrator-specific message handlers."""
        self.on_message("query", self._handle_query)
        self.on_message("spawn_agent", self._handle_spawn)
        self.on_message("destroy_agent", self._handle_destroy)
        self.on_message("list_agents", self._handle_list)
    
    async def _handle_query(self, message: dict, client: WebSocketClient) -> dict:
        """Handle a query request."""
        query = message.get("query", "")
        
        if not query:
            return {"type": "error", "error": "No query provided"}
        
        # Import orchestrator here to avoid circular imports
        from ..orchestrator import HyprVoiceOrchestrator
        
        orchestrator = HyprVoiceOrchestrator()
        
        # Stream results back to client
        async for chunk in orchestrator.process(query):
            await client.send({
                "type": "chunk",
                **chunk,
            })
        
        return {"type": "complete"}
    
    async def _handle_spawn(self, message: dict, client: WebSocketClient) -> dict:
        """Handle agent spawn request."""
        agent_type = message.get("agent_type", "")
        task = message.get("task", "")
        
        if not agent_type or not task:
            return {"type": "error", "error": "Missing agent_type or task"}
        
        from ..orchestrator import HyprVoiceOrchestrator
        
        orchestrator = HyprVoiceOrchestrator()
        
        try:
            session_id = await orchestrator.spawn_agent(agent_type, task)
            
            # Broadcast spawn event
            await self.broadcast({
                "type": "agent_spawned",
                "session_id": session_id,
                "agent_type": agent_type,
            }, topic="agents")
            
            return {"type": "spawned", "session_id": session_id}
        except Exception as e:
            return {"type": "error", "error": str(e)}
    
    async def _handle_destroy(self, message: dict, client: WebSocketClient) -> dict:
        """Handle agent destroy request."""
        session_id = message.get("session_id", "")
        
        if not session_id:
            return {"type": "error", "error": "Missing session_id"}
        
        from ..orchestrator import HyprVoiceOrchestrator
        
        orchestrator = HyprVoiceOrchestrator()
        
        success = await orchestrator.destroy_agent(session_id)
        
        if success:
            await self.broadcast({
                "type": "agent_destroyed",
                "session_id": session_id,
            }, topic="agents")
            
            return {"type": "destroyed", "session_id": session_id}
        else:
            return {"type": "error", "error": "Session not found"}
    
    async def _handle_list(self, message: dict, client: WebSocketClient) -> dict:
        """Handle list agents request."""
        from ..orchestrator import HyprVoiceOrchestrator
        
        orchestrator = HyprVoiceOrchestrator()
        agents = orchestrator.list_agents()
        
        return {"type": "agents_list", "agents": agents}
