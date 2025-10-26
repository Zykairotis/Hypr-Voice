"""
FastAPI bridge service for Hypr-Voice control
Converts HTTP requests to Unix socket commands with WebSocket support
"""

import asyncio
import json
import time
import os
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from models import (
    APIResponse, RecordingStartRequest, RecordingEnhancedStartRequest,
    ConfigUpdateRequest, RecordingStatusResponse, ServerStatusResponse,
    ConfigResponse, LogEntry, LogType, LogLevel, SessionInfo,
    SystemMetrics, ErrorResponse, WebSocketMessage
)
from unix_client import UnixSocketClient, ProcessManager
from config_manager import ConfigManager
from log_streamer import LogStreamer

# Initialize FastAPI app
app = FastAPI(
    title="Hypr-Voice Bridge API",
    description="HTTP to Unix socket bridge for Hypr-Voice control",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
socket_client = UnixSocketClient()
process_manager = ProcessManager()
config_manager = ConfigManager()
log_streamer = LogStreamer()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await log_streamer.start()
    logger.info("Hypr-Voice Bridge API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await log_streamer.stop()
    logger.info("Hypr-Voice Bridge API stopped")

# Utility functions
def create_success_response(message: str, data: Any = None) -> APIResponse:
    """Create success response"""
    return APIResponse(success=True, message=message, data=data)

def create_error_response(message: str, error_code: str = None, details: Dict[str, Any] = None) -> ErrorResponse:
    """Create error response"""
    return ErrorResponse(error=message, error_code=error_code, details=details)

def handle_socket_error(func):
    """Decorator to handle socket errors"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Socket error in {func.__name__}: {e}")
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
    return wrapper

# Recording Control Endpoints
@app.post("/api/recording/start", response_model=APIResponse)
@handle_socket_error
async def start_recording(request: RecordingStartRequest = None):
    """Start recording (F9 raw mode)"""
    if request is None:
        request = RecordingStartRequest()

    if socket_client.is_recording():
        raise HTTPException(status_code=409, detail="Already recording")

    success = socket_client.start_recording(request.mode.value)
    if success:
        return create_success_response(f"Recording started in {request.mode.value} mode")
    else:
        raise HTTPException(status_code=500, detail="Failed to start recording")

@app.post("/api/recording/enhanced", response_model=APIResponse)
@handle_socket_error
async def start_enhanced_recording(request: RecordingEnhancedStartRequest = None):
    """Start enhanced recording (F10 enhanced mode)"""
    if request is None:
        request = RecordingEnhancedStartRequest()

    if socket_client.is_recording():
        raise HTTPException(status_code=409, detail="Already recording")

    success = socket_client.start_recording("enhanced")
    if success:
        return create_success_response("Enhanced recording started")
    else:
        raise HTTPException(status_code=500, detail="Failed to start enhanced recording")

@app.post("/api/recording/stop", response_model=APIResponse)
@handle_socket_error
async def stop_recording():
    """Stop recording"""
    if not socket_client.is_recording():
        raise HTTPException(status_code=409, detail="Not currently recording")

    success = socket_client.stop_recording()
    if success:
        return create_success_response("Recording stopped")
    else:
        raise HTTPException(status_code=500, detail="Failed to stop recording")

@app.post("/api/recording/force-stop", response_model=APIResponse)
@handle_socket_error
async def force_stop_recording():
    """Force stop recording and discard buffers"""
    success = socket_client.force_stop_recording()
    if success:
        return create_success_response("Recording force-stopped")
    else:
        raise HTTPException(status_code=500, detail="Failed to force stop recording")

@app.get("/api/recording/status", response_model=RecordingStatusResponse)
@handle_socket_error
async def get_recording_status():
    """Get current recording status"""
    status_data = socket_client.get_status()
    if not status_data:
        # Check if socket is available
        if not socket_client.check_connection():
            raise HTTPException(status_code=503, detail="Hypr-Voice service not running")

    return RecordingStatusResponse(
        status="recording" if status_data.get("state") == "recording" else "ready",
        is_recording=status_data.get("state") == "recording",
        audio_chunks=status_data.get("recording_chunks", 0),
        total_frames=status_data.get("total_frames", 0),
        device_name=status_data.get("device"),
        app_context=status_data.get("app_context")
    )

# Server Management Endpoints
@app.post("/api/server/start", response_model=APIResponse)
async def start_server():
    """Start Hypr-Voice server"""
    success = process_manager.start_server()
    if success:
        return create_success_response("Server started successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to start server")

@app.post("/api/server/stop", response_model=APIResponse)
async def stop_server():
    """Stop Hypr-Voice server"""
    success = process_manager.stop_server()
    if success:
        return create_success_response("Server stopped successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to stop server")

@app.post("/api/server/restart", response_model=APIResponse)
async def restart_server():
    """Restart Hypr-Voice server"""
    success = process_manager.restart_server()
    if success:
        return create_success_response("Server restarted successfully")
    else:
        raise HTTPException(status_code=500, detail="Failed to restart server")

@app.get("/api/server/status", response_model=ServerStatusResponse)
async def get_server_status():
    """Get server status"""
    server_info = process_manager.get_server_info()

    status = ServerStatus.RUNNING if server_info["running"] else ServerStatus.STOPPED

    # Get system metrics
    memory_usage = None
    cpu_usage = None
    try:
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        cpu_usage = process.cpu_percent()
    except:
        pass

    return ServerStatusResponse(
        status=status,
        uptime_seconds=time.time() if server_info["running"] else None,
        memory_usage_mb=memory_usage,
        active_connections=log_streamer.get_subscription_count()
    )

# Configuration Management Endpoints
@app.get("/api/config/{section}", response_model=ConfigResponse)
async def get_config_section(section: str):
    """Get configuration section"""
    try:
        config_data = config_manager.get_config(section)
        if config_data is None:
            raise HTTPException(status_code=404, detail=f"Configuration section '{section}' not found")

        return ConfigResponse(
            section=section,
            config_data=config_data,
            valid=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting configuration: {str(e)}")

@app.put("/api/config/{section}", response_model=ConfigResponse)
async def update_config_section(section: str, request: ConfigUpdateRequest):
    """Update configuration section"""
    if section != request.section:
        raise HTTPException(status_code=400, detail="Section mismatch")

    try:
        success, errors = config_manager.update_config(section, request.config_data, request.validate)

        if not success:
            raise HTTPException(status_code=400, detail={
                "message": "Configuration validation failed",
                "errors": errors
            })

        return ConfigResponse(
            section=section,
            config_data=config_manager.get_config(section),
            valid=True
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")

# WebSocket Log Streaming
@app.websocket("/api/logs/stream")
async def websocket_log_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time log streaming"""
    await websocket.accept()

    subscription_id = None
    try:
        # Parse query parameters
        query_params = websocket.query_params

        log_types = []
        if "type" in query_params:
            type_str = query_params["type"]
            if type_str == "all":
                log_types = [LogType.ALL]
            else:
                try:
                    log_types = [LogType(type_str)]
                except ValueError:
                    log_types = [LogType.ALL]
        else:
            log_types = [LogType.ALL]

        levels = []
        if "level" in query_params:
            level_str = query_params["level"]
            try:
                levels = [LogLevel(level_str)]
            except ValueError:
                levels = list(LogLevel)
        else:
            levels = list(LogLevel)

        # Subscribe to log stream
        subscription_id = await log_streamer.subscribe(websocket, log_types, levels)

        logger.info(f"WebSocket log stream connected: {subscription_id}")

        # Keep connection alive
        while True:
            try:
                # Wait for any message (ping/pong)
                await websocket.receive_text()
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket log stream disconnected: {subscription_id}")
    except Exception as e:
        logger.error(f"WebSocket log stream error: {e}")
    finally:
        if subscription_id:
            await log_streamer.unsubscribe(subscription_id)

@app.get("/api/logs/{log_type}/recent", response_model=List[LogEntry])
async def get_recent_logs(log_type: str, limit: int = 50):
    """Get recent log entries"""
    try:
        log_type_enum = LogType(log_type)
        logs = await log_streamer.get_recent_logs(log_type_enum, limit)
        return logs
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid log type: {log_type}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting logs: {str(e)}")

# Session Management Endpoints
@app.get("/api/sessions", response_model=List[SessionInfo])
async def get_sessions():
    """Get active and recent sessions"""
    try:
        # Import status monitor from existing code
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hypr-voice" / "src" / "core"))
        from status_monitor import get_status_monitor

        monitor = get_status_monitor()
        active_sessions = monitor.get_active_sessions()

        sessions = []
        for session in active_sessions:
            session_info = SessionInfo(
                session_id=session.session_id,
                start_time=session.start_time,
                status=session.status,
                duration_seconds=session.duration_seconds,
                primary_agent=session.primary_agent,
                input_text=session.input_text,
                response_preview=session.response_preview,
                tokens_used=session.tokens_used,
                cost_usd=session.cost_usd,
                tools_used=session.tools_used
            )
            sessions.append(session_info)

        return sessions
    except Exception as e:
        logger.error(f"Error getting sessions: {e}")
        return []

# Metrics Endpoint
@app.get("/api/metrics", response_model=SystemMetrics)
async def get_system_metrics():
    """Get system metrics"""
    try:
        # Import status monitor from existing code
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hypr-voice" / "src" / "core"))
        from status_monitor import get_status_monitor

        monitor = get_status_monitor()
        system_status = monitor.update_status()

        # Get system resource usage
        memory_usage = None
        cpu_usage = None
        try:
            process = psutil.Process()
            memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            cpu_usage = process.cpu_percent()
        except:
            pass

        return SystemMetrics(
            timestamp=system_status.timestamp,
            active_sessions=system_status.active_sessions,
            completed_sessions_today=system_status.completed_sessions_today,
            total_sessions_today=system_status.total_sessions_today,
            claude_sdk_status=system_status.claude_sdk_status,
            litellm_status=system_status.litellm_status,
            last_activity=system_status.last_activity,
            error_count=system_status.error_count,
            average_response_time=system_status.average_response_time,
            total_cost_today=system_status.total_cost_today,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        # Return basic metrics
        return SystemMetrics(
            timestamp=datetime.now(),
            active_sessions=0,
            completed_sessions_today=0,
            total_sessions_today=0,
            claude_sdk_status="UNKNOWN",
            litellm_status="UNKNOWN"
        )

# Health Check Endpoint
@app.get("/api/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "socket_client": socket_client.check_connection(),
            "log_streamer": log_streamer.running,
            "config_manager": True
        }
    }

    # Overall health
    all_healthy = all(health_status["services"].values())
    health_status["status"] = "healthy" if all_healthy else "degraded"

    return health_status

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=create_error_response("Internal server error", "INTERNAL_ERROR", {"exception": str(exc)}).dict()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )