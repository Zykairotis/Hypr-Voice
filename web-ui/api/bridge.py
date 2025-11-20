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

app = FastAPI(title="Hypr-Voice Web UI Bridge", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8933", "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration paths
BASE_DIR = Path(__file__).parent.parent.parent
WHISPER_CONFIG_DIR = BASE_DIR / "src/Hypr-Whisper/config"
AGENT_CONFIG_DIR = BASE_DIR / "config/hypr_voice"

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
            async with session.get("http://localhost:9090/", timeout=2) as resp:
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
            async with session.get("http://localhost:9090/api/audio/devices") as resp:
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
            async with session.get("http://localhost:8922/agents/list", timeout=2) as resp:
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
                    "http://localhost:9090/api/context",
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
    Streams context changes as they happen (every 100ms from Whisper server).
    """
    await websocket.accept()
    
    last_context = None
    connection_active = True
    
    try:
        while connection_active:
            try:
                # Get context from hybrid server
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.get(
                            "http://localhost:9090/api/context",
                            timeout=aiohttp.ClientTimeout(total=2)
                        ) as response:
                            if response.status == 200:
                                data = await response.json()
                                
                                # Only send if context changed
                                if data != last_context:
                                    try:
                                        await websocket.send_json(data)
                                        last_context = data
                                    except RuntimeError as e:
                                        # WebSocket already closed
                                        connection_active = False
                                        break
                    except asyncio.TimeoutError:
                        # Silently skip on timeout, don't spam errors
                        pass
                    except Exception:
                        # Skip other aiohttp errors
                        pass
                
                # Wait 100ms before next check (matching server update rate)
                await asyncio.sleep(0.1)
                
            except WebSocketDisconnect:
                connection_active = False
                break
            except RuntimeError:
                # WebSocket closed
                connection_active = False
                break
            except Exception as e:
                # Only log unexpected errors
                if "close message" not in str(e).lower():
                    print(f"Unexpected WebSocket error: {e}")
                connection_active = False
                break
                
    except WebSocketDisconnect:
        pass  # Client disconnected gracefully
    except Exception as e:
        if "close message" not in str(e).lower():
            print(f"WebSocket connection error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8934, log_level="info")

