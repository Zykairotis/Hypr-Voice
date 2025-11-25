"""
Hypr-Voice Orchestrator Server

Main entry point for the agent orchestrator service.
Provides REST API and WebSocket endpoints.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from .orchestrator import HyprVoiceOrchestrator, OrchestratorConfig
from .agents import get_all_agents
from .ipc import OrchestratorWebSocket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instance
orchestrator: Optional[HyprVoiceOrchestrator] = None
ws_server: Optional[OrchestratorWebSocket] = None


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class SpawnRequest(BaseModel):
    agent_type: str
    task: str
    parent_session: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator, ws_server
    
    # Startup
    logger.info("Starting Hypr-Voice Orchestrator...")
    
    config = OrchestratorConfig(
        model=os.getenv("HYPR_VOICE_MODEL", "claude-sonnet-4-5"),
        max_turns=int(os.getenv("HYPR_VOICE_MAX_TURNS", "20")),
        working_directory=os.getenv("HYPR_VOICE_WORKING_DIR"),
    )
    
    orchestrator = HyprVoiceOrchestrator(config)
    
    # Start WebSocket server (if not using uvicorn WebSocket)
    # ws_server = OrchestratorWebSocket(port=9091)
    # await ws_server.start()
    
    logger.info("Orchestrator started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down orchestrator...")
    if orchestrator:
        await orchestrator.shutdown()
    if ws_server:
        await ws_server.stop()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Hypr-Voice Orchestrator",
    description="Agent orchestration service using Claude Agent SDK patterns",
    version="0.2.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "0.2.0",
    }


@app.get("/agents")
async def list_agents():
    """List all active agent sessions."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return {"agents": orchestrator.list_agents()}


@app.get("/agent-types")
async def get_agent_types():
    """Get available agent types."""
    if not orchestrator:
        # Return from static definitions
        agents = get_all_agents()
        return {
            "types": [
                {
                    "name": name,
                    "description": agent.description,
                    "tools": agent.tools,
                    "model": agent.model.value,
                }
                for name, agent in agents.items()
            ]
        }
    
    return {"types": orchestrator.get_agent_types()}


@app.post("/query")
async def process_query(request: QueryRequest):
    """Process a query through the orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    results = []
    async for chunk in orchestrator.process(request.query, request.session_id):
        results.append(chunk)
    
    return {"results": results}


@app.post("/spawn")
async def spawn_agent(request: SpawnRequest):
    """Spawn a new agent."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        session_id = await orchestrator.spawn_agent(
            request.agent_type,
            request.task,
            request.parent_session,
        )
        return {"session_id": session_id, "status": "spawned"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/agents/{session_id}")
async def destroy_agent(session_id: str):
    """Destroy an agent session."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    success = await orchestrator.destroy_agent(session_id)
    
    if success:
        return {"status": "destroyed", "session_id": session_id}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time events."""
    await websocket.accept()
    
    client_id = None
    
    try:
        # Wait for subscription message
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type", "")
            
            if msg_type == "subscribe":
                topic = data.get("topic", "all")
                client_id = data.get("client_id", "unknown")
                await websocket.send_json({
                    "type": "subscribed",
                    "topic": topic,
                    "client_id": client_id,
                })
                
            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                
            elif msg_type == "query" and orchestrator:
                query = data.get("query", "")
                session_id = data.get("session_id")
                
                async for chunk in orchestrator.process(query, session_id):
                    await websocket.send_json({
                        "type": "chunk",
                        **chunk,
                    })
                
                await websocket.send_json({"type": "complete"})
                
            elif msg_type == "list_agents" and orchestrator:
                agents = orchestrator.list_agents()
                await websocket.send_json({
                    "type": "agents_list",
                    "agents": agents,
                })
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


def run_server(host: str = "0.0.0.0", port: int = 9091):
    """Run the orchestrator server."""
    import uvicorn
    uvicorn.run(
        "hypr_voice.server:app",
        host=host,
        port=port,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    run_server()
