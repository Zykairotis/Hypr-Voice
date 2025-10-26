"""
Pydantic models for FastAPI bridge service request/response validation
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class RecordingMode(str, Enum):
    """Recording mode enumeration"""
    RAW = "raw"
    ENHANCED = "enhanced"


class RecordingStatus(str, Enum):
    """Recording status enumeration"""
    READY = "ready"
    RECORDING = "recording"
    PROCESSING = "processing"
    ERROR = "error"


class ServerStatus(str, Enum):
    """Server status enumeration"""
    RUNNING = "running"
    STOPPED = "stopped"
    STARTING = "starting"
    ERROR = "error"


class LogLevel(str, Enum):
    """Log level enumeration"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class LogType(str, Enum):
    """Log type enumeration"""
    AGENT = "agent"
    RESPONSE = "response"
    STATUS = "status"
    SERVER = "server"
    CLIENT = "client"
    ALL = "all"


# Request Models
class RecordingStartRequest(BaseModel):
    """Request to start recording"""
    mode: Optional[RecordingMode] = RecordingMode.RAW
    context: Optional[Dict[str, Any]] = None


class RecordingEnhancedStartRequest(BaseModel):
    """Request to start enhanced recording"""
    context: Optional[Dict[str, Any]] = None


class ConfigUpdateRequest(BaseModel):
    """Request to update configuration"""
    section: str
    config_data: Dict[str, Any]
    validate: Optional[bool] = True


# Response Models
class APIResponse(BaseModel):
    """Generic API response"""
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class RecordingStatusResponse(BaseModel):
    """Recording status response"""
    status: RecordingStatus
    is_recording: bool
    mode: Optional[RecordingMode] = None
    duration_seconds: Optional[float] = None
    audio_chunks: int = 0
    total_frames: int = 0
    device_name: Optional[str] = None
    app_context: Optional[str] = None


class ServerStatusResponse(BaseModel):
    """Server status response"""
    status: ServerStatus
    uptime_seconds: Optional[float] = None
    version: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    active_connections: int = 0


class ConfigResponse(BaseModel):
    """Configuration response"""
    section: str
    config_data: Dict[str, Any]
    valid: bool = True
    errors: Optional[List[str]] = None


class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: datetime
    level: LogLevel
    message: str
    context: Optional[Dict[str, Any]] = None
    source: Optional[str] = None


class SessionInfo(BaseModel):
    """Session information model"""
    session_id: str
    start_time: datetime
    status: str
    duration_seconds: Optional[float] = None
    primary_agent: Optional[str] = None
    input_text: Optional[str] = None
    response_preview: Optional[str] = None
    tokens_used: Optional[int] = None
    cost_usd: Optional[float] = None
    tools_used: Optional[List[str]] = None


class SystemMetrics(BaseModel):
    """System metrics model"""
    timestamp: datetime
    active_sessions: int
    completed_sessions_today: int
    total_sessions_today: int
    claude_sdk_status: str
    litellm_status: str
    last_activity: Optional[datetime] = None
    error_count: int = 0
    average_response_time: Optional[float] = None
    total_cost_today: float = 0.0
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None


class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


# WebSocket Messages
class WebSocketMessage(BaseModel):
    """WebSocket message base model"""
    type: str
    timestamp: datetime = Field(default_factory=datetime.now)


class LogStreamMessage(WebSocketMessage):
    """Log stream message"""
    type: str = "log_stream"
    log_entry: LogEntry


class StatusUpdateMessage(WebSocketMessage):
    """Status update message"""
    type: str = "status_update"
    status: RecordingStatus
    details: Optional[Dict[str, Any]] = None


# Config Validation Models
class AudioConfigValidation(BaseModel):
    """Audio configuration validation model"""
    sample_rate: int = Field(ge=8000, le=192000)
    channels: int = Field(ge=1, le=8)
    blocksize: int = Field(ge=64, le=8192)
    dtype: str = Field(pattern="^(int16|int32|float32|float64)$")


class ServerConfigValidation(BaseModel):
    """Server configuration validation model"""
    host: str = Field(pattern=r"^[\w\.-]+$")
    port: int = Field(ge=1, le=65535)
    protocol: str = Field(pattern="^(http|https|ws|wss)$")


class TimeoutConfigValidation(BaseModel):
    """Timeout configuration validation model"""
    poll_timeout: int = Field(ge=1)
    request_timeout: int = Field(ge=1)
    upload_timeout: int = Field(ge=1)