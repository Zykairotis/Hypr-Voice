"""
FastAPI Backend Bridge for Hypr-Voice Web UI
Provides API endpoints for configuration management and status monitoring
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import yaml
import json
from pathlib import Path
import asyncio
import aiohttp
import os
import sys
from loguru import logger

# Configure Loguru
LOG_DIR = os.getenv("HYPR_VOICE_LOG_DIR", "/tmp/hypr-voice")
LOG_FILE = os.path.join(LOG_DIR, "hypr-voice.log")

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

# Remove default handler and add file handler
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="1 day",
    format="{time:HH:mm:ss.SSS} [bridge] [{level}] {message}",
    level="INFO"
)

logger.info("Bridge API starting up...")

app = FastAPI(title="Hypr-Voice Web UI Bridge", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8933",
        "http://127.0.0.1:8933",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration paths
BASE_DIR = Path(__file__).parent.parent.parent
WHISPER_CONFIG_DIR = BASE_DIR / "src/Hypr-Whisper/config"
AGENT_CONFIG_DIR = BASE_DIR / "config/hypr_voice"
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "http://localhost:9093")

# Pydantic models for request/response
class AudioConfig(BaseModel):
    input_device: Optional[str] = None
    sample_rate: int = 16000
    channels: int = 1
    buffer_size: int = 1024
    save_recordings: bool = False
    auto_cleanup: Optional[Dict[str, Any]] = None

class ModelConfig(BaseModel):
    model_path: str
    device: str
    language: str
    translate: bool
    compute_type: str
    num_workers: int
    cpu_threads: int
    vad_enabled: bool
    vad_threshold: float
    min_speech_duration: float
    max_silence_duration: float

class VocabularyConfig(BaseModel):
    enabled: bool
    custom_words: List[str]
    categories: Optional[Dict[str, List[str]]] = None
    categories_enabled: Optional[Dict[str, bool]] = None

class ModelConfigEnhanced(BaseModel):
    # Basic
    model_path: str
    device: str
    language: str
    translate: bool
    compute_type: str
    # Performance
    num_workers: int
    cpu_threads: int
    download_root: str
    local_files_only: bool
    # VAD
    vad_enabled: bool
    vad_threshold: float
    min_speech_duration: float
    max_silence_duration: float
    # CTranslate2
    beam_size: int
    patience: float
    length_penalty: float
    temperature: float
    compression_ratio_threshold: float
    log_prob_threshold: float
    no_speech_threshold: float
    inter_threads: int
    intra_threads: int

class VoiceConfig(BaseModel):
    default_provider: str
    fallback_provider: str
    auto_fallback: bool
    voice: str
    preset: str
    speed: float = 1.0
    pitch: float = 1.0


# ============================================================================
# WHISPER SERVER ENDPOINTS
# ============================================================================

@app.get("/health")
async def health_check():
    """Check if the bridge is running"""
    return {"status": "ok", "service": "Hypr-Voice Web UI Bridge"}


@app.get("/api/whisper/status")
async def get_whisper_status():
    """Get Whisper server status"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9099/", timeout=2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"status": "online", **data}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


@app.get("/api/audio/devices")
async def get_audio_devices():
    """Get available audio input devices"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9099/api/audio/devices") as resp:
                if resp.status == 200:
                    return await resp.json()
    except Exception:
        pass
    
    # Return mock data for development if Whisper server is not available
    return {
        "devices": [
            {"name": "GA102 High Definition Audio Controller", "index": 0, "channels": 2, "sampleRate": 48000},
            {"name": "Default PulseAudio Input", "index": 1, "channels": 2, "sampleRate": 44100},
        ]
    }


@app.get("/api/config/audio")
async def get_audio_config():
    """Get current audio configuration"""
    try:
        config_path = WHISPER_CONFIG_DIR / "audio-profile.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return {
                "input_device": config.get("pulseaudio", {}).get("default_source"),
                "sample_rate": config.get("audio", {}).get("sample_rate", 16000),
                "channels": config.get("audio", {}).get("channels", 1),
                "buffer_size": config.get("audio", {}).get("chunk_size", 1024),
                "save_recordings": config.get("recording", {}).get("save_recordings", False),
                "auto_cleanup": config.get("recording", {}).get("auto_cleanup", {"enabled": False}),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/audio")
async def update_audio_config(config: AudioConfig):
    """Update audio configuration"""
    try:
        config_path = WHISPER_CONFIG_DIR / "audio-profile.yaml"
        
        # Load existing config
        existing = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing = yaml.safe_load(f) or {}
        
        # Update config
        if "pulseaudio" not in existing:
            existing["pulseaudio"] = {}
        if "audio" not in existing:
            existing["audio"] = {}
        if "recording" not in existing:
            existing["recording"] = {}
        
        existing["pulseaudio"]["default_source"] = config.input_device
        existing["audio"]["sample_rate"] = config.sample_rate
        existing["audio"]["channels"] = config.channels
        existing["audio"]["chunk_size"] = config.buffer_size
        existing["recording"]["save_recordings"] = config.save_recordings
        existing["recording"]["auto_cleanup"] = config.auto_cleanup or {"enabled": False}
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.safe_dump(existing, f, default_flow_style=False)
        
        return {"status": "success", "message": "Audio configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/model")
async def get_model_config():
    """Get current model configuration"""
    try:
        config_path = WHISPER_CONFIG_DIR / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            backend = config.get("backend", {})
            hypr_voice = config.get("hypr_voice", {})
            
            return {
                "model_path": backend.get("model_path"),
                "device": backend.get("device", "cuda"),
                "language": backend.get("language", "auto"),
                "translate": backend.get("translate", False),
                "compute_type": backend.get("compute_type", "int8"),  # Fixed: read from backend not model
                "num_workers": config.get("model", {}).get("num_workers", 2),
                "cpu_threads": config.get("performance", {}).get("omp_num_threads", 4),  # Fixed: read from performance
                "vad_enabled": hypr_voice.get("vad_enabled", True),
                "vad_threshold": hypr_voice.get("vad_threshold", 0.1),
                "min_speech_duration": hypr_voice.get("min_speech_duration", 0.3),
                "max_silence_duration": hypr_voice.get("max_silence_duration", 1.5),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/model")
async def update_model_config(config: ModelConfig):
    """Update model configuration"""
    try:
        config_path = WHISPER_CONFIG_DIR / "config.yaml"
        
        # Load existing config
        existing = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing = yaml.safe_load(f) or {}
        
        # Update config
        if "backend" not in existing:
            existing["backend"] = {}
        if "model" not in existing:
            existing["model"] = {}
        if "performance" not in existing:
            existing["performance"] = {}
        if "hypr_voice" not in existing:
            existing["hypr_voice"] = {}
        
        existing["backend"]["model_path"] = config.model_path
        existing["backend"]["device"] = config.device
        existing["backend"]["language"] = config.language
        existing["backend"]["translate"] = config.translate
        existing["backend"]["compute_type"] = config.compute_type  # Fixed: write to backend not model
        existing["model"]["num_workers"] = config.num_workers
        existing["performance"]["omp_num_threads"] = config.cpu_threads  # Fixed: write to performance
        existing["hypr_voice"]["vad_enabled"] = config.vad_enabled
        existing["hypr_voice"]["vad_threshold"] = config.vad_threshold
        existing["hypr_voice"]["min_speech_duration"] = config.min_speech_duration
        existing["hypr_voice"]["max_silence_duration"] = config.max_silence_duration
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.safe_dump(existing, f, default_flow_style=False)
        
        return {"status": "success", "message": "Model configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/model/enhanced")
async def get_model_config_enhanced():
    """Get enhanced model configuration with all CTranslate2 parameters"""
    try:
        config_path = WHISPER_CONFIG_DIR / "config.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            backend = config.get("backend", {})
            model = config.get("model", {})
            hypr_voice = config.get("hypr_voice", {})
            ctranslate2 = config.get("ctranslate2", {})
            
            return {
                # Basic
                "model_path": backend.get("model_path", "openai/whisper-large-v3-turbo"),
                "device": backend.get("device", "cuda"),
                "language": backend.get("language", "auto"),
                "translate": backend.get("translate", False),
                "compute_type": backend.get("compute_type", "int8"),
                # Performance
                "num_workers": model.get("num_workers", 2),
                "cpu_threads": config.get("performance", {}).get("omp_num_threads", 4),
                "download_root": model.get("download_root", "/tmp/whisper-models"),
                "local_files_only": model.get("local_files_only", False),
                # VAD
                "vad_enabled": hypr_voice.get("vad_enabled", True),
                "vad_threshold": hypr_voice.get("vad_threshold", 0.1),
                "min_speech_duration": hypr_voice.get("min_speech_duration", 0.3),
                "max_silence_duration": hypr_voice.get("max_silence_duration", 1.5),
                # CTranslate2
                "beam_size": ctranslate2.get("beam_size", 3),
                "patience": ctranslate2.get("patience", 1.0),
                "length_penalty": ctranslate2.get("length_penalty", 1.0),
                "temperature": ctranslate2.get("temperature", 0.0),
                "compression_ratio_threshold": ctranslate2.get("compression_ratio_threshold", 2.4),
                "log_prob_threshold": ctranslate2.get("log_prob_threshold", -1.0),
                "no_speech_threshold": ctranslate2.get("no_speech_threshold", 0.6),
                "inter_threads": ctranslate2.get("inter_threads", 1),
                "intra_threads": ctranslate2.get("intra_threads", 4),
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/model/enhanced")
async def update_model_config_enhanced(config: ModelConfigEnhanced):
    """Update enhanced model configuration with all CTranslate2 parameters"""
    try:
        config_path = WHISPER_CONFIG_DIR / "config.yaml"
        
        # Load existing config
        existing = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing = yaml.safe_load(f) or {}
        
        # Update config sections
        if "backend" not in existing:
            existing["backend"] = {}
        if "model" not in existing:
            existing["model"] = {}
        if "performance" not in existing:
            existing["performance"] = {}
        if "hypr_voice" not in existing:
            existing["hypr_voice"] = {}
        if "ctranslate2" not in existing:
            existing["ctranslate2"] = {}
        
        # Basic settings
        existing["backend"]["model_path"] = config.model_path
        existing["backend"]["device"] = config.device
        existing["backend"]["language"] = config.language
        existing["backend"]["translate"] = config.translate
        existing["backend"]["compute_type"] = config.compute_type
        
        # Performance settings
        existing["model"]["num_workers"] = config.num_workers
        existing["model"]["download_root"] = config.download_root
        existing["model"]["local_files_only"] = config.local_files_only
        existing["performance"]["omp_num_threads"] = config.cpu_threads
        
        # VAD settings
        existing["hypr_voice"]["vad_enabled"] = config.vad_enabled
        existing["hypr_voice"]["vad_threshold"] = config.vad_threshold
        existing["hypr_voice"]["min_speech_duration"] = config.min_speech_duration
        existing["hypr_voice"]["max_silence_duration"] = config.max_silence_duration
        
        # CTranslate2 settings
        existing["ctranslate2"]["beam_size"] = config.beam_size
        existing["ctranslate2"]["patience"] = config.patience
        existing["ctranslate2"]["length_penalty"] = config.length_penalty
        existing["ctranslate2"]["temperature"] = config.temperature
        existing["ctranslate2"]["compression_ratio_threshold"] = config.compression_ratio_threshold
        existing["ctranslate2"]["log_prob_threshold"] = config.log_prob_threshold
        existing["ctranslate2"]["no_speech_threshold"] = config.no_speech_threshold
        existing["ctranslate2"]["inter_threads"] = config.inter_threads
        existing["ctranslate2"]["intra_threads"] = config.intra_threads
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.safe_dump(existing, f, default_flow_style=False)
        
        return {"status": "success", "message": "Enhanced model configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config/vocabulary")
async def get_vocabulary_config():
    """Get current vocabulary configuration"""
    try:
        config_path = WHISPER_CONFIG_DIR / "vocabulary.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            return {
                "enabled": config.get("settings", {}).get("post_processing", {}).get("enabled", True),
                "custom_words": config.get("global", {}).get("technical_terms", [])[:20],  # Return first 20
                "categories": {
                    "technical_terms": config.get("global", {}).get("technical_terms", []),
                    "programming": config.get("global", {}).get("programming", {}).get("keywords", []),
                    "sysadmin": config.get("global", {}).get("sysadmin", {}).get("commands", []),
                },
                "categories_enabled": {
                    "technical_terms": True,
                    "programming": True,
                    "sysadmin": True,
                }
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config/vocabulary")
async def update_vocabulary_config(config: VocabularyConfig):
    """Update vocabulary configuration"""
    try:
        config_path = WHISPER_CONFIG_DIR / "vocabulary.yaml"
        
        # Load existing config
        existing = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing = yaml.safe_load(f) or {}
        
        # Update config
        if "settings" not in existing:
            existing["settings"] = {}
        if "post_processing" not in existing["settings"]:
            existing["settings"]["post_processing"] = {}
        
        existing["settings"]["post_processing"]["enabled"] = config.enabled
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.safe_dump(existing, f, default_flow_style=False)
        
        return {"status": "success", "message": "Vocabulary configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AGENT SERVER ENDPOINTS
# ============================================================================

@app.get("/api/agent/status")
async def get_agent_status():
    """Get Agent server status"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9093/agents", timeout=2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"status": "online", "agents": data.get("agents", [])}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


@app.post("/api/config/voice")
async def update_voice_config(config: VoiceConfig):
    """Update voice synthesis configuration"""
    try:
        config_path = AGENT_CONFIG_DIR / "config.yaml"
        
        # Load existing config
        existing = {}
        if config_path.exists():
            with open(config_path, 'r') as f:
                existing = yaml.safe_load(f) or {}
        
        # Update voice config
        if "voice" not in existing:
            existing["voice"] = {}
        
        existing["voice"]["default_provider"] = config.default_provider
        existing["voice"]["fallback_provider"] = config.fallback_provider
        existing["voice"]["auto_fallback"] = config.auto_fallback
        
        # Save config
        with open(config_path, 'w') as f:
            yaml.safe_dump(existing, f, default_flow_style=False)
        
        return {"status": "success", "message": "Voice configuration updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/context")
async def get_context():
    """
    Get live context from Hypr-Whisper including:
    - Current application/window info
    - Recent shell commands and clipboard
    - Project context (git, files)
    - Triggered hooks
    """
    try:
        # Try to get context from hybrid server
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    "http://localhost:9099/api/context",
                    timeout=aiohttp.ClientTimeout(total=2)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
            except:
                pass
        
        # Fallback: Return empty context structure
        return {
            "workspace": {
                "application": "",
                "category": "other",
                "window_title": "",
                "active_file": None
            },
            "recent_activity": {
                "commands": [],
                "clipboard": [],
                "keywords": []
            },
            "project_context": {
                "git_branch": None,
                "git_status": None,
                "project_root": None
            },
            "hooks": {
                "triggered": [],
                "context_additions": {}
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/context")
async def websocket_context(websocket: WebSocket):
    """
    WebSocket endpoint for real-time context updates.

    Polls the Whisper backend HTTP context endpoint (~10Hz) and streams
    updates to the UI. This matches the existing UI schema and avoids CORS
    mismatches seen when proxying raw upstream sockets.
    """

    await websocket.accept()

    upstream_url = os.getenv("CONTEXT_WS_UPSTREAM", "ws://localhost:9091")

    async def transform_and_send(raw: Dict[str, Any]):
        """Transform upstream data to UI schema and send."""
        # Extract parts from upstream
        context = raw.get("data", {}).get("context", {})
        meta = raw.get("data", {}).get("meta", {})
        
        # Extract window info
        window = context.get("window", {})
        window_meta = window.get("metadata", {})
        
        # Map to UI payload
        ui_payload = {
            "workspace": {
                "application": window.get("application", "") or window_meta.get("class", "") or "None",
                "category": window_meta.get("category", "other"), # backend might not provide category yet
                "window_title": window.get("title", ""),
                "active_file": None, # TODO: Extract from title if possible
                "states": {},
                "workspace_name": window_meta.get("workspace", ""),
                "monitor": None,
                "pid": window_meta.get("pid"),
            },
            "recent_activity": {
                "commands": context.get("shell", {}).get("recent_commands", []),
                "clipboard": context.get("clipboard", {}).get("recent_entries", []),
                "keywords": raw.get("data", {}).get("vocabulary", [])
            },
            "project_context": {
                "git_branch": None,
                "git_status": None,
                "project_root": None
            },
            "hooks": {
                "triggered": [],
                "context_additions": {}
            },
            "meta": meta,
        }
        
        await websocket.send_json({
            "type": "context_update",
            "data": ui_payload
        })
    async def relay():
        retry_delay = 1
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(upstream_url, heartbeat=15) as upstream:
                        retry_delay = 1
                        async for msg in upstream:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    raw = json.loads(msg.data)
                                    await transform_and_send(raw if isinstance(raw, dict) else {})
                                except Exception:
                                    pass
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
            except asyncio.CancelledError:
                break
            except Exception as e:
            except Exception as e:
                logger.warning(f"Upstream context WS reconnect in {retry_delay}s: {e}")
                await asyncio.sleep(min(retry_delay, 5))
                retry_delay = min(retry_delay * 2, 10)

    relay_task = asyncio.create_task(relay())

    try:
        await relay_task
    except WebSocketDisconnect:
        relay_task.cancel()
    except Exception as e:
    except Exception as e:
        if "close message" not in str(e).lower():
            logger.error(f"WebSocket connection error: {e}")


# ============================================================================
# ORCHESTRATOR ENDPOINTS
# ============================================================================

class OrchestratorQuery(BaseModel):
    query: str
    session_id: Optional[str] = None


class SpawnAgentRequest(BaseModel):
    agent_type: str
    task: str
    parent_session: Optional[str] = None


@app.get("/api/orchestrator/status")
async def get_orchestrator_status():
    """Get Agent Orchestrator status"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9093/health", timeout=2) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {"status": "online", **data}
    except Exception as e:
        return {"status": "offline", "error": str(e)}


@app.get("/api/orchestrator/agents")
async def list_orchestrator_agents():
    """List all active agents in the orchestrator"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9093/agents", timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"agents": [], "error": "Failed to fetch agents"}
    except Exception as e:
        return {"agents": [], "error": str(e)}


@app.get("/api/orchestrator/agent-types")
async def get_agent_types():
    """Get available agent types"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:9093/agent-types", timeout=5) as resp:
                if resp.status == 200:
                    return await resp.json()
    except:
        pass
    
    # Return default agent types if orchestrator not available
    return {
        "types": [
            {
                "name": "code-worker",
                "description": "Code analysis, generation, and refactoring tasks",
                "tools": ["Read", "Write", "Edit", "Grep", "Glob"],
                "model": "sonnet"
            },
            {
                "name": "research-worker", 
                "description": "Research, information gathering, and documentation tasks",
                "tools": ["Read", "Grep", "Glob"],
                "model": "haiku"
            },
            {
                "name": "shell-worker",
                "description": "System operations and bash commands",
                "tools": ["Bash", "Read", "Grep"],
                "model": "sonnet"
            },
            {
                "name": "voice-worker",
                "description": "Text-to-speech and speech-to-text operations",
                "tools": ["Read"],
                "model": "haiku"
            }
        ]
    }


@app.post("/api/orchestrator/query")
async def orchestrator_query(request: OrchestratorQuery):
    """Send a query to the orchestrator"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:9093/query",
                json={"query": request.query, "session_id": request.session_id},
                timeout=60
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"Orchestrator returned status {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# VOICE / TTS PROXY ENDPOINTS
# ============================================================================


@app.get("/api/voice/conversations")
async def get_voice_conversations():
    """List conversations from the voice orchestrator."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/voice/conversations", timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"conversations": [], "error": f"voice orchestrator returned {resp.status}"}
    except Exception as e:
        return {"conversations": [], "error": str(e)}


@app.post("/api/voice/conversations")
async def create_voice_conversation():
    """Create a new conversation via the voice orchestrator."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{ORCHESTRATOR_URL}/voice/conversations", timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"failed to create conversation: {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/voice/conversations/{conversation_id}")
async def get_voice_conversation(conversation_id: str):
    """Get a specific conversation."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{ORCHESTRATOR_URL}/voice/conversations/{conversation_id}", timeout=10) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"conversation fetch failed: {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/voice/process")
async def process_voice(request: Dict[str, Any]):
    """Process text through the voice orchestrator (chat + TTS)."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ORCHESTRATOR_URL}/voice/process",
                json=request,
                timeout=60
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"voice process failed: {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/voice/speak")
async def speak_voice(request: Dict[str, Any]):
    """Speak text via the voice orchestrator."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{ORCHESTRATOR_URL}/voice/speak",
                json=request,
                timeout=30
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"voice speak failed: {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/api/orchestrator/spawn")
async def spawn_agent(request: SpawnAgentRequest):
    """Spawn a new agent"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:9093/spawn",
                json={
                    "agent_type": request.agent_type,
                    "task": request.task,
                    "parent_session": request.parent_session
                },
                timeout=10
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                return {"error": f"Failed to spawn agent: {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.delete("/api/orchestrator/agents/{session_id}")
async def destroy_agent(session_id: str):
    """Destroy an agent session"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"http://localhost:9093/agents/{session_id}",
                timeout=10
            ) as resp:
                if resp.status == 200:
                    return {"status": "destroyed", "session_id": session_id}
                return {"error": f"Failed to destroy agent: {resp.status}"}
    except Exception as e:
        return {"error": str(e)}


@app.websocket("/ws/orchestrator")
async def websocket_orchestrator(websocket: WebSocket):
    """WebSocket endpoint for real-time orchestrator events"""
    await websocket.accept()
    
    orchestrator_url = os.getenv("ORCHESTRATOR_WS_URL", "ws://localhost:9093")
    
    async def relay():
        retry_delay = 1
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.ws_connect(orchestrator_url, heartbeat=15) as upstream:
                        retry_delay = 1
                        
                        # Subscribe to all events
                        await upstream.send_json({"type": "subscribe", "topic": "all"})
                        
                        async for msg in upstream:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                try:
                                    data = json.loads(msg.data)
                                    await websocket.send_json(data)
                                except Exception:
                                    pass
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                break
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Orchestrator WS reconnect in {retry_delay}s: {e}")
                await asyncio.sleep(min(retry_delay, 5))
                retry_delay = min(retry_delay * 2, 10)
    
    relay_task = asyncio.create_task(relay())
    
    try:
        # Also handle incoming messages from the web client
        while True:
            data = await websocket.receive_json()
            # Forward queries to orchestrator
            if data.get("type") == "query":
                # Process via HTTP for now
                pass
    except WebSocketDisconnect:
        relay_task.cancel()
    except Exception as e:
        if "close message" not in str(e).lower():
            print(f"Orchestrator WebSocket error: {e}")
        relay_task.cancel()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8934, log_level="info")
