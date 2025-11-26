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

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import json

from .orchestrator import HyprVoiceOrchestrator, OrchestratorConfig, VoiceOrchestrator, VoiceOrchestratorConfig
from .agents import get_all_agents
from .ipc import OrchestratorWebSocket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global orchestrator instances
orchestrator: Optional[HyprVoiceOrchestrator] = None
voice_orchestrator: Optional[VoiceOrchestrator] = None
ws_server: Optional[OrchestratorWebSocket] = None


# Pydantic models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class SpawnRequest(BaseModel):
    agent_type: str
    task: str
    parent_session: Optional[str] = None


class VoiceProcessRequest(BaseModel):
    text: str
    conversation_id: Optional[str] = None
    speak_response: bool = True


class TTSSpeakRequest(BaseModel):
    text: str
    voice: Optional[str] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global orchestrator, voice_orchestrator, ws_server
    
    # Startup
    logger.info("Starting Hypr-Voice Orchestrator...")
    
    config = OrchestratorConfig(
        model=os.getenv("HYPR_VOICE_MODEL", "claude-sonnet-4-5"),
        max_turns=int(os.getenv("HYPR_VOICE_MAX_TURNS", "20")),
        working_directory=os.getenv("HYPR_VOICE_WORKING_DIR"),
    )
    
    orchestrator = HyprVoiceOrchestrator(config)
    
    # Initialize voice orchestrator with TTS
    voice_config = VoiceOrchestratorConfig(
        tts_provider=os.getenv("HYPR_VOICE_TTS_PROVIDER", "deepgram"),
        tts_voice=os.getenv("HYPR_VOICE_TTS_VOICE", "aura-luna-en"),  # Deepgram Aura voice
        whisper_url=os.getenv("WHISPER_URL", "http://localhost:9099"),
        save_to_file=True,
    )
    voice_orchestrator = VoiceOrchestrator(voice_config)
    
    logger.info("Orchestrator started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down orchestrator...")
    if orchestrator:
        await orchestrator.shutdown()
    if voice_orchestrator:
        await voice_orchestrator.shutdown()
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


# ============================================================================
# VOICE ENDPOINTS
# ============================================================================

@app.post("/voice/process")
async def voice_process(request: VoiceProcessRequest):
    """
    Process text through the voice pipeline.
    Routes to appropriate agent, generates response, and speaks via TTS.
    """
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    result = await voice_orchestrator.quick_response(
        request.text, 
        speak=request.speak_response
    )
    
    return result


@app.post("/voice/process/stream")
async def voice_process_stream(request: VoiceProcessRequest):
    """
    Stream process text through the voice pipeline.
    Returns Server-Sent Events with progress updates.
    """
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    async def event_generator():
        async for chunk in voice_orchestrator.process_text(
            request.text,
            request.conversation_id,
            request.speak_response
        ):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


class StreamingTTSRequest(BaseModel):
    """Request for streaming TTS processing."""
    text: str
    conversation_id: Optional[str] = None
    auto_play: bool = False  # Server-side audio playback (usually False for API)


@app.post("/voice/process/streaming")
async def voice_process_streaming(request: StreamingTTSRequest):
    """
    Process text with real-time streaming TTS via WebSocket.
    
    Audio playback begins as soon as the first LLM tokens arrive,
    providing near-instant voice response (<500ms to first audio).
    
    Returns Server-Sent Events (SSE) with:
    - token: Individual LLM tokens as they arrive
    - first_token: Time to first token metric
    - routing: Agent routing decision
    - tts_connected: TTS WebSocket status
    - complete: Final response with metrics
    """
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    async def event_generator():
        async for event in voice_orchestrator.process_text_streaming(
            request.text,
            request.conversation_id,
            auto_play=request.auto_play
        ):
            yield f"data: {json.dumps(event)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@app.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    """
    Transcribe an audio file using Whisper.
    """
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        text = await voice_orchestrator.transcribe(tmp_path)
        return {"text": text, "success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Cleanup temp file
        import os
        os.unlink(tmp_path)


@app.post("/voice/speak")
async def voice_speak(request: TTSSpeakRequest):
    """
    Convert text to speech using Deepgram TTS.
    Returns audio file path or streams audio.
    """
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    result = await voice_orchestrator.speak(request.text)
    
    if result.get("success") and result.get("audio_file"):
        # Return the audio file with proper headers for inline playback
        return FileResponse(
            result["audio_file"],
            media_type="audio/wav",
            filename="response.wav",
            headers={
                "Content-Disposition": "inline; filename=\"response.wav\"",
                "Content-Type": "audio/wav",
                "Accept-Ranges": "bytes"
            }
        )
    
    return result


@app.get("/voice/conversations")
async def list_conversations():
    """List all conversations."""
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    return {"conversations": voice_orchestrator.list_conversations()}


@app.get("/voice/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get a specific conversation."""
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    conv = voice_orchestrator.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conv.to_dict()


@app.post("/voice/conversations")
async def create_conversation():
    """Create a new conversation."""
    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")
    
    conv = voice_orchestrator.create_conversation()
    return conv.to_dict()


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
