import os
import sys
import time
import uuid
import gc
import yaml
import threading
import queue
import asyncio
import logging
import json
import base64
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Callable, Any
from io import BytesIO
from dataclasses import dataclass
import tempfile
import shutil
import aiohttp
import torch
import requests

import numpy as np
import uvicorn
from fastapi import FastAPI, UploadFile, File, WebSocket, BackgroundTasks, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import ffmpeg
import soundfile as sf
from faster_whisper import WhisperModel
import ctranslate2
from huggingface_hub import snapshot_download
import re

# Allow running as a script with PYTHONPATH configured
if __name__ == "__main__" and not __package__:
    project_root = Path(__file__).resolve().parents[4]
    sys.path.insert(0, str(project_root / "src"))
    __package__ = "hypr_voice.whisper.core"

from ..paths import get_whisper_config_path

# Package root for local fallback imports
_current_file = Path(__file__).resolve()
_whisper_package_root = _current_file.parent.parent

# Load .env from project root if available (for MODE and WISPR_FLOW_* settings)
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # Up to project root from src/hypr_voice/whisper/core/
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=False)
except Exception:
    # dotenv is optional; environment may already be set
    pass

# Transcription mode (LOCAL = Hypr-Whisper, FLOW = Wispr Flow API)
TRANSCRIPTION_MODE = os.getenv("MODE", "LOCAL").upper()
FLOW_MODE = TRANSCRIPTION_MODE == "FLOW"

FLOW_SERVER_URL = os.getenv("WISPR_FLOW_URL")
if not FLOW_SERVER_URL:
    FLOW_PORT = os.getenv("WISPR_FLOW_PORT", "9095")
    FLOW_SERVER_URL = f"http://localhost:{FLOW_PORT}"
FLOW_SERVER_URL = FLOW_SERVER_URL.rstrip("/")
FLOW_TIMEOUT = float(os.getenv("WISPR_FLOW_TIMEOUT", "30"))
FLOW_MAX_DICTIONARY_WORDS = int(os.getenv("WISPR_FLOW_MAX_DICTIONARY_WORDS", "25"))
FLOW_SYNC = os.getenv("WISPR_FLOW_SYNC", "1") == "1"
FLOW_TRIM_SILENCE = os.getenv("WISPR_FLOW_TRIM_SILENCE", "1") == "1"
FLOW_SILENCE_THRESHOLD = float(os.getenv("WISPR_FLOW_SILENCE_THRESHOLD", "0.01"))
FLOW_SILENCE_PAD_MS = int(os.getenv("WISPR_FLOW_SILENCE_PAD_MS", "200"))
FLOW_CHUNK_MODE = os.getenv("WISPR_FLOW_CHUNK_MODE", "0") == "1"
FLOW_CHUNK_SECONDS = float(os.getenv("WISPR_FLOW_CHUNK_SECONDS", "2.0"))
FLOW_CHUNK_OVERLAP = float(os.getenv("WISPR_FLOW_CHUNK_OVERLAP", "0.2"))
FLOW_USE_OPUS = os.getenv("WISPR_FLOW_USE_OPUS", "1") == "1"  # Use Opus encoding for ~5x faster uploads
FLOW_OPUS_BITRATE = os.getenv("WISPR_FLOW_OPUS_BITRATE", "24k")  # Opus bitrate (16k-64k)
FLOW_AUTO_CHUNK = os.getenv("WISPR_FLOW_AUTO_CHUNK", "1") == "1"
FLOW_MAX_BASE64_MB = float(os.getenv("WISPR_FLOW_MAX_BASE64_MB", "50"))
FLOW_MAX_BASE64_CHARS = int(max(FLOW_MAX_BASE64_MB, 0) * 1024 * 1024)
FLOW_MAX_DICTIONARY_WORDS = int(os.getenv("WISPR_FLOW_MAX_DICTIONARY_WORDS", "50"))

# Wispr Flow Authentication (for direct Baseten API access)
FLOW_JWT_TOKEN = os.getenv("WISPR_FLOW_JWT_TOKEN")
FLOW_USER_UUID = os.getenv("WISPR_FLOW_USER_UUID")
FLOW_BASETEN_API_KEY = os.getenv("WISPR_FLOW_BASETEN_API_KEY")
FLOW_BASETEN_URL = os.getenv("WISPR_FLOW_BASETEN_URL")
FLOW_USE_BASETEN = bool(FLOW_BASETEN_URL and FLOW_JWT_TOKEN)

# Direct mode - bypass API server for better performance (default: enabled)
# Set FLOW_DIRECT_MODE=0 to use legacy API server mode
FLOW_DIRECT_MODE = os.getenv("FLOW_DIRECT_MODE", "1") == "1"

_flow_session = requests.Session()

# Direct flow client (lazy initialized)
_direct_flow_client = None

# Import vocabulary manager (deferred until after logger setup)
VOCABULARY_ENABLED = False
vocabulary_manager = None
application_detector = None
APP_DETECTOR_ENABLED = False

# ============================================================================
# CONFIG LOADING
# ============================================================================
def load_config(config_path: Optional[str] = None):
    """Load configuration from YAML file."""
    paths_to_try = []

    if config_path:
        paths_to_try.append(Path(config_path))

    # Primary: whisper config directory
    paths_to_try.append(get_whisper_config_path("config.yaml"))
    # Fallbacks: current working dir + legacy relative names
    paths_to_try.append(Path.cwd() / "config.yaml")
    paths_to_try.append(Path.cwd() / "config" / "config.yaml")

    for path in paths_to_try:
        try:
            if path and path.exists():
                with open(path, 'r') as f:
                    config = yaml.safe_load(f)
                    logging.info(f"Loaded config from: {path}")
                    return config
        except Exception:
            continue

    logging.warning("Config file not found, using defaults")
    return {}

# Load config
CONFIG = load_config()

# Extract settings from config
SERVER_CONFIG = CONFIG.get('server', {})
BACKEND_CONFIG = CONFIG.get('backend', {})
PERFORMANCE_CONFIG = CONFIG.get('performance', {})
MODEL_CONFIG = CONFIG.get('model', {})
CTRANSLATE_CONFIG = CONFIG.get('ctranslate2', {})
HYBRID_CONFIG = CONFIG.get('hybrid', {})
API_CONFIG = CONFIG.get('api', {})
OBS_URL = os.getenv("CLAUDE_HOOKS_OBS_URL", "")
OBS_ENABLED = os.getenv("CLAUDE_HOOKS_ENABLED", "0") == "1" and bool(OBS_URL)
OBS_SOURCE = os.getenv("CLAUDE_HOOKS_SOURCE_APP", "hypr-voice")

HOST = SERVER_CONFIG.get('host', 'localhost')
PORT = SERVER_CONFIG.get('port', 9099)
MAX_CLIENTS = SERVER_CONFIG.get('max_clients', 10)
MAX_CONNECTION_TIME = SERVER_CONFIG.get('max_connection_time', 3600)

MODEL_SIZE = BACKEND_CONFIG.get('model_path', 'openai/whisper-large-v3-turbo')
DEVICE = BACKEND_CONFIG.get('device', 'cuda')
COMPUTE_TYPE = BACKEND_CONFIG.get('compute_type', 'int8')
SAMPLE_RATE = PERFORMANCE_CONFIG.get('sample_rate', 16000)
CACHE_PATH = PERFORMANCE_CONFIG.get('cache_path', '/tmp/whisper-live-cache')

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Enable debug logging for troubleshooting

log_dir = 'logs'
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

file_handler = logging.FileHandler(f'{log_dir}/hybrid_server.log')
console_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# ============================================================================
# TRACE LOGGING (OPTIONAL, FOR PERFORMANCE MONITORING)
# ============================================================================
TRACE_ENABLED = os.getenv("HYPR_VOICE_TRACE", "0") == "1"
TRACE_SLOW_MS = float(os.getenv("HYPR_VOICE_TRACE_SLOW_MS", "0"))


def _trace_duration(label: str, start_time: float, **fields) -> float:
    """Log timing for a span if tracing is enabled or exceeds slow threshold."""
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    should_log = TRACE_ENABLED or (TRACE_SLOW_MS > 0 and elapsed_ms >= TRACE_SLOW_MS)
    if should_log:
        field_str = " ".join(f"{k}={v}" for k, v in fields.items() if v is not None)
        if field_str:
            logger.info(f"[TRACE] {label} {elapsed_ms:.1f}ms {field_str}")
        else:
            logger.info(f"[TRACE] {label} {elapsed_ms:.1f}ms")
    return elapsed_ms

# Import vocabulary manager after logger setup
# Use absolute import that works whether run as module or script
try:
    # Try relative import first (when run as module)
    from ..vocabulary.vocabulary_manager import get_vocabulary_manager
    VOCABULARY_ENABLED = True
    logger.info("Vocabulary manager module loaded (relative import)")
except (ImportError, ValueError):
    try:
        # Fallback to absolute import with explicit path (when run as script)
        import importlib.util
        vocab_path = _whisper_package_root / "vocabulary" / "vocabulary_manager.py"
        spec = importlib.util.spec_from_file_location("vocabulary_manager", vocab_path)
        vocab_module = importlib.util.module_from_spec(spec)
        sys.modules["vocabulary.vocabulary_manager"] = vocab_module
        sys.modules["vocabulary_manager"] = vocab_module
        spec.loader.exec_module(vocab_module)
        get_vocabulary_manager = vocab_module.get_vocabulary_manager
        VOCABULARY_ENABLED = True
        logger.info("Vocabulary manager module loaded (script import)")
    except Exception as e:
        logger.warning(f"Vocabulary manager not found: {e}, transcription enhancement disabled")
        VOCABULARY_ENABLED = False

# Import application detector
try:
    from ..scripts.app_detector import ApplicationDetector
    APP_DETECTOR_ENABLED = True
    logger.info("Application detector module loaded")
except ImportError as e:
    logger.warning(f"Application detector not found: {e}, context-aware vocabulary disabled")
    APP_DETECTOR_ENABLED = False

# ============================================================================
# PYDANTIC MODELS
# ============================================================================
@dataclass
class TranscriptionProgress:
    """Progress update for long-running transcriptions."""
    current_chunk: int
    total_chunks: int
    chunk_text: str
    percent_complete: float


class TranscriptionRequest(BaseModel):
    language: Optional[str] = "en"
    beam_size: Optional[int] = 3
    vad_filter: Optional[bool] = False
    compute_type: Optional[str] = COMPUTE_TYPE
    device: Optional[str] = DEVICE

class TranscriptionResponse(BaseModel):
    session_id: str
    status: str
    text: Optional[str] = None
    error: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    status: str
    created_at: float
    last_active: float
    text: str = ""

# ============================================================================
# GLOBAL STATE
# ============================================================================
model = None
active_sessions = {}
last_gc_time = time.time()
GC_INTERVAL = 10

# Observability helper (non-blocking)
async def emit_event(event_type: str, payload: dict):
    if not OBS_ENABLED:
        return
    data = {
        "source_app": OBS_SOURCE,
        "event_type": event_type,
        "payload": payload,
        "ts": datetime.utcnow().isoformat(),
    }
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(OBS_URL, json=data, timeout=3)
    except Exception as e:
        logger.debug(f"Obs emit failed: {e}")

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def check_cuda_availability():
    """Check if CUDA is available and return appropriate device and compute_type."""
    try:
        import torch
        if torch.cuda.is_available():
            try:
                test_tensor = torch.zeros(1).cuda()
                del test_tensor
                logger.info("CUDA is available. Using GPU acceleration.")
                return "cuda", "float16"
            except Exception as e:
                logger.error(f"PyTorch CUDA error: {e}")
                logger.info("Falling back to CPU.")
                return "cpu", "int8"
        else:
            logger.info("CUDA is not available. Using CPU.")
            return "cpu", "int8"
    except ImportError:
        try:
            test_model = WhisperModel("tiny", device="cuda", compute_type="float16")
            del test_model
            logger.info("CUDA is available. Using GPU acceleration.")
            return "cuda", "float16"
        except Exception as e:
            logger.error(f"CUDA error: {e}")
            logger.info("Falling back to CPU.")
            return "cpu", "int8"

def load_whisper_model():
    """Load the Whisper model and return it."""
    global DEVICE, COMPUTE_TYPE
    
    if DEVICE != "cpu":
        detected_device, _ = check_cuda_availability()
        DEVICE = detected_device
    
    valid_compute_types = {
        "cpu": ["int8", "float16", "float32"],
        "cuda": ["float16", "int8", "int8_float16"]
    }
    
    if COMPUTE_TYPE not in valid_compute_types[DEVICE]:
        logger.warning(f"{COMPUTE_TYPE} is not valid for {DEVICE}. Using default.")
        COMPUTE_TYPE = valid_compute_types[DEVICE][0]
    
    logger.info(f"Loading model: {MODEL_SIZE} ({DEVICE}, {COMPUTE_TYPE})")
    gc.collect()
    
    cache_dir = os.path.expanduser(CACHE_PATH)
    os.makedirs(cache_dir, exist_ok=True)
    
    # List of standard model sizes
    model_sizes = [
        "tiny", "tiny.en", "base", "base.en", "small", "small.en",
        "medium", "medium.en", "large-v2", "large-v3", "distil-small.en",
        "distil-medium.en", "distil-large-v2", "distil-large-v3",
        "large-v3-turbo", "turbo"
    ]
    
    model_ref = MODEL_SIZE
    
    # Check if it's a standard model size
    if model_ref in model_sizes:
        model_to_load = model_ref
    else:
        logger.info(f"Model not in standard sizes, checking if it's a HuggingFace model...")
        
        # Check if it's already a local CTranslate2 directory
        if os.path.isdir(model_ref) and ctranslate2.contains_model(model_ref):
            model_to_load = model_ref
        else:
            # Download from HuggingFace
            try:
                logger.info(f"Downloading model from HuggingFace: {model_ref}")
                local_snapshot = snapshot_download(
                    repo_id=model_ref,
                    repo_type="model",
                )
                logger.info(f"Model downloaded to: {local_snapshot}")
                
                # Check if already in CTranslate2 format
                if ctranslate2.contains_model(local_snapshot):
                    model_to_load = local_snapshot
                else:
                    # Need to convert to CTranslate2 format
                    ct2_cache_root = os.path.join(cache_dir, "whisper-ct2-models")
                    os.makedirs(ct2_cache_root, exist_ok=True)
                    safe_name = model_ref.replace("/", "--")
                    ct2_dir = os.path.join(ct2_cache_root, safe_name)
                    
                    if not ctranslate2.contains_model(ct2_dir):
                        logger.info(f"Converting '{model_ref}' to CTranslate2 format at {ct2_dir}")
                        ct2_converter = ctranslate2.converters.TransformersConverter(
                            local_snapshot,
                            copy_files=["tokenizer.json", "preprocessor_config.json"]
                        )
                        ct2_converter.convert(
                            output_dir=ct2_dir,
                            quantization=COMPUTE_TYPE,
                            force=False,  # skip if already up-to-date
                        )
                    model_to_load = ct2_dir
                    logger.info(f"Using CTranslate2 model from: {ct2_dir}")
            except Exception as e:
                logger.error(f"Error downloading/converting model: {e}")
                raise
    
    logger.info(f"Loading model: {model_to_load}")
    model = WhisperModel(
        model_to_load,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        cpu_threads=PERFORMANCE_CONFIG.get('omp_num_threads', 4),
        num_workers=MODEL_CONFIG.get('num_workers', 2),
        local_files_only=False,
    )
    
    logger.info("Model loaded successfully.")
    return model

def preprocess_audio(audio_data, original_sr):
    """Preprocess audio data to match Whisper requirements (16kHz, mono, float32)."""
    try:
        start_time = time.perf_counter()
        input_samples = len(audio_data) if hasattr(audio_data, "__len__") else None
        resampled = False
        if audio_data.ndim > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        if original_sr != 16000:
            import scipy.signal as signal
            audio_data = signal.resample(audio_data, int(len(audio_data) * 16000 / original_sr))
            resampled = True
        
        output = audio_data.astype(np.float32)
        _trace_duration(
            "preprocess_audio",
            start_time,
            original_sr=original_sr,
            input_samples=input_samples,
            output_samples=len(output),
            resampled=resampled,
        )
        return output
    except Exception as e:
        logger.error(f"Error in audio preprocessing: {e}")
        return np.zeros(16000, dtype=np.float32)

def clean_text(text):
    """Clean up transcribed text with proper spacing."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove space before punctuation
    text = re.sub(r'\s+([.,!?])', r'\1', text)
    
    # Ensure space after punctuation (but not at end)
    text = re.sub(r'([.,!?])([A-Z])', r'\1 \2', text)  # Add space after punctuation before capital letter
    text = re.sub(r'([.,!?])([a-z])', r'\1 \2', text)  # Add space after punctuation before lowercase
    
    text = text.strip()
    return text

def filter_hallucinations(text):
    """Filter out common Whisper hallucinations and repetitions."""
    if not text:
        return ""
    
    # Remove repeated phrases
    words = text.split()
    cleaned_words = []
    for i, word in enumerate(words):
        # Skip if this word starts a repeated sequence
        if i < len(words) - 2:
            if word == words[i+1] == words[i+2]:
                continue
        # Skip if this is part of a repeated sequence
        if i > 0 and i < len(words) - 1:
            if words[i-1] == word == words[i+1]:
                continue
        cleaned_words.append(word)
    
    text = ' '.join(cleaned_words)
    
    # Clean up spacing
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def log_transcription(text, session_id=None):
    """Log transcription text."""
    logger.info(f"Session {session_id}: {text}")

def process_video_to_audio(video_path: str):
    """Extract audio from video file."""
    try:
        start_time = time.perf_counter()
        ffmpeg_start = time.perf_counter()
        out, err = (
            ffmpeg
            .input(video_path)
            .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=SAMPLE_RATE)
            .run(capture_stdout=True, capture_stderr=True)
        )
        _trace_duration(
            "ffmpeg_extract_audio",
            ffmpeg_start,
            file=os.path.basename(video_path),
            stdout_bytes=len(out) if out else 0,
            stderr_bytes=len(err) if err else 0,
        )
        decode_start = time.perf_counter()
        audio_data, sample_rate = sf.read(BytesIO(out))
        _trace_duration(
            "ffmpeg_decode_audio",
            decode_start,
            samples=len(audio_data) if hasattr(audio_data, "__len__") else None,
            sample_rate=sample_rate,
        )
        _trace_duration("process_video_to_audio_total", start_time, file=os.path.basename(video_path))
        return audio_data, sample_rate
    except Exception as e:
        logger.error(f"Error processing video to audio: {e}")
        raise


def _get_flow_app_context() -> Dict[str, Optional[str]]:
    """Derive app name/type for Wispr Flow context."""
    start = time.perf_counter()
    window_info = globals().get("cached_window_info")
    app_class = ""
    app_title = ""
    cached = False
    if window_info:
        cached = True
        app_class = window_info.get('class', '') or window_info.get('initialClass', '')
        app_title = window_info.get('title', '') or window_info.get('initialTitle', '')

    app_name = app_class or None
    app_type = "other"
    app_lower = (app_class or "").lower()
    title_lower = (app_title or "").lower()

    if any(token in title_lower for token in ["chatgpt", "claude", "gemini", "perplexity"]):
        app_type = "ai"
    elif app_lower in ['code', 'windsurf', 'cursor', 'vscode', 'sublime', 'atom', 'vim', 'nvim', 'intellij', 'pycharm']:
        app_type = "code"
    elif app_lower in ['discord', 'slack', 'teams', 'telegram', 'signal', 'whatsapp']:
        app_type = "messaging"
    elif app_lower in ['gmail', 'outlook', 'thunderbird', 'mail']:
        app_type = "email"

    _trace_duration("flow_context_app", start, app_name=app_name, app_type=app_type, cached=cached)
    return {"app_name": app_name, "app_type": app_type}


def _get_flow_dictionary_words(max_words: Optional[int] = None) -> List[str]:
    """Collect a compact list of vocabulary words for Wispr Flow."""
    start = time.perf_counter()
    if max_words is None:
        max_words = FLOW_MAX_DICTIONARY_WORDS
    manager = globals().get("vocabulary_manager")
    if not manager:
        _trace_duration("flow_context_dict", start, count=0, cached="no_manager")
        return []
    try:
        if hasattr(manager, "_prioritize_keywords"):
            words = manager._prioritize_keywords()
        else:
            words = list(manager.active_keywords)
        # Deduplicate while preserving order
        deduped = list(dict.fromkeys(words))
        result = deduped[:max_words]
        _trace_duration("flow_context_dict", start, count=len(result), cached="no")
        return result
    except Exception as e:
        logger.debug(f"Flow dictionary build failed: {e}")
        _trace_duration("flow_context_dict", start, count=0, error=str(e))
        return []


def _get_direct_flow_client():
    """
    Lazy initialization of direct flow client.
    
    Returns the DirectWisprFlowClient instance for direct Baseten API access,
    bypassing the HTTP API server for better performance.
    """
    global _direct_flow_client
    if _direct_flow_client is None and FLOW_DIRECT_MODE and FLOW_MODE:
        try:
            from ...services.wispr_flow_direct import DirectWisprFlowClient
            _direct_flow_client = DirectWisprFlowClient(
                jwt_token=FLOW_JWT_TOKEN,
                api_key=FLOW_BASETEN_API_KEY,
                user_uuid=FLOW_USER_UUID,
            )
            logger.info("✅ Direct Flow client initialized (bypassing API server)")
        except Exception as e:
            logger.error(f"Failed to initialize direct flow client: {e}")
            return None
    return _direct_flow_client


def _get_flow_user_context() -> Dict[str, Optional[str]]:
    """Get user information for transcription context (helps spell names correctly)."""
    start = time.perf_counter()
    # Try to get from environment or config
    user_first_name = os.getenv("WISPR_FLOW_USER_FIRST_NAME")
    user_last_name = os.getenv("WISPR_FLOW_USER_LAST_NAME")

    # Fallback: try to extract from vocabulary manager user context
    if vocabulary_manager and hasattr(vocabulary_manager, 'user_context'):
        ctx = vocabulary_manager.user_context
        if ctx:
            user_first_name = user_first_name or ctx.get('first_name')
            user_last_name = user_last_name or ctx.get('last_name')

    result = {
        "user_first_name": user_first_name,
        "user_last_name": user_last_name,
    }
    _trace_duration("flow_context_user", start, has_first=bool(user_first_name), has_last=bool(user_last_name))
    return result


def _get_flow_text_context() -> Dict[str, Any]:
    """
    Get text context from Hyprland system (clipboard, selected text).

    Uses wl-paste for clipboard content which provides context for:
    - Smart punctuation and capitalization
    - Understanding what the user is working on
    """
    start = time.perf_counter()
    import subprocess

    before_text = ""
    after_text = ""
    selected_text = ""
    content_text = None
    clipboard_time = 0
    primary_time = 0

    # Get current clipboard content as context
    try:
        run_start = time.perf_counter()
        result = subprocess.run(
            ['wl-paste', '--no-newline'],
            capture_output=True,
            text=True,
            timeout=1
        )
        clipboard_time = (time.perf_counter() - run_start) * 1000
        _trace_duration(
            "wl-paste",
            run_start,
            primary=False,
            rc=result.returncode,
            stdout_chars=len(result.stdout) if result.stdout else 0,
        )
        if result.returncode == 0 and result.stdout:
            clipboard_content = result.stdout.strip()
            # Use clipboard as content_text (provides context for transcription)
            if len(clipboard_content) < 2000:
                content_text = clipboard_content
            else:
                # Truncate long clipboard content
                content_text = clipboard_content[:2000]
            logger.debug(f"Got clipboard context: {len(content_text)} chars")
    except subprocess.TimeoutExpired:
        logger.debug("wl-paste timed out")
    except FileNotFoundError:
        logger.debug("wl-paste not available")
    except Exception as e:
        logger.debug(f"Failed to get clipboard: {e}")

    # Try to get primary selection (highlighted text) as selected_text
    try:
        run_start = time.perf_counter()
        result = subprocess.run(
            ['wl-paste', '--primary', '--no-newline'],
            capture_output=True,
            text=True,
            timeout=1
        )
        primary_time = (time.perf_counter() - run_start) * 1000
        _trace_duration(
            "wl-paste",
            run_start,
            primary=True,
            rc=result.returncode,
            stdout_chars=len(result.stdout) if result.stdout else 0,
        )
        if result.returncode == 0 and result.stdout:
            selected = result.stdout.strip()
            if len(selected) < 500:
                selected_text = selected
                logger.debug(f"Got selected text: {len(selected_text)} chars")
    except subprocess.TimeoutExpired:
        pass
    except FileNotFoundError:
        pass
    except Exception as e:
        logger.debug(f"Failed to get primary selection: {e}")

    _trace_duration("flow_context_text", start,
                    clipboard_ms=f"{clipboard_time:.1f}",
                    primary_ms=f"{primary_time:.1f}",
                    content_chars=len(content_text) if content_text else 0,
                    selected_chars=len(selected_text))
    return {
        "before_text": before_text,
        "after_text": after_text,
        "selected_text": selected_text,
        "content_text": content_text,
    }


def _get_flow_code_context() -> Dict[str, List[str]]:
    """
    Get code context (variable names, file names) for better code transcription.

    Extracts from:
    - Vocabulary manager active keywords
    - Shell history (recent commands, file paths)
    - Context manager data
    """
    start = time.perf_counter()
    import re
    variable_names = []
    file_names = []
    source = "none"

    # Try to get from vocabulary manager
    if vocabulary_manager:
        try:
            # Check if context_manager is available
            ctx_mgr = getattr(vocabulary_manager, 'context_manager', None)

            if ctx_mgr:
                source = "ctx_mgr"
                # Get shell history for file paths and variable names
                try:
                    shell_commands = ctx_mgr.get_shell_history(20)
                    for cmd in shell_commands:
                        # Extract file paths
                        paths = re.findall(r'[\w./\-_]+\.\w+', cmd)
                        for path in paths:
                            if path not in file_names:
                                file_names.append(path)

                        # Extract potential variable names (camelCase, snake_case)
                        vars_found = re.findall(r'\b[a-z][a-zA-Z0-9_]*[A-Z][a-zA-Z0-9_]*\b|\b[a-z]+_[a-z_]+\b', cmd)
                        for var in vars_found:
                            if var not in variable_names and len(var) > 2:
                                variable_names.append(var)
                except Exception as e:
                    logger.debug(f"Failed to extract from shell history: {e}")

            # Also extract from active keywords
            if hasattr(vocabulary_manager, 'active_keywords'):
                source = "keywords"
                for kw in vocabulary_manager.active_keywords:
                    # File-like patterns
                    if ('.' in kw and '/' not in kw and len(kw) > 3) or '/' in kw:
                        if kw not in file_names:
                            file_names.append(kw)
                    # Variable-like patterns (camelCase, snake_case, starts with _)
                    elif (kw.startswith('_') or
                          (any(c.isupper() for c in kw[1:]) and kw[0].islower()) or
                          '_' in kw):
                        if kw not in variable_names:
                            variable_names.append(kw)

        except Exception as e:
            logger.debug(f"Failed to get code context: {e}")

    result = {
        "variable_names": variable_names[:25],  # Limit to 25
        "file_names": file_names[:25],
    }
    _trace_duration("flow_context_code", start,
                    vars=len(result["variable_names"]),
                    files=len(result["file_names"]),
                    source=source)
    return result


async def _flow_transcribe_file_direct(
    session,
    file_path: str,
    content_type: Optional[str]
) -> Dict[str, Optional[str]]:
    """
    Direct transcription without API server overhead.
    
    Uses the optimized wisper-flow module for ultra-fast processing:
    - Audio preprocessing < 15ms (vs 500-2000ms with subprocess)
    - No HTTP overhead (saves 50-200ms)
    - Parallel chunk processing built-in
    - Full context support (app, user, text, code context)
    
    Args:
        session: TranscriptionSession with language and context
        file_path: Path to audio file
        content_type: MIME type of the file
        
    Returns:
        Dict with success, text, error keys
    """
    import time
    timings = {}
    total_start = time.perf_counter()
    
    # ⏱️ TIMING: Get client
    client_start = time.perf_counter()
    client = _get_direct_flow_client()
    timings['get_client_ms'] = (time.perf_counter() - client_start) * 1000
    
    if not client:
        logger.warning("Direct flow client not available, falling back to API mode")
        return await _flow_transcribe_file_api(session, file_path, content_type)
    
    # ⏱️ TIMING: Build contexts
    ctx_start = time.perf_counter()
    app_context = _get_flow_app_context()
    timings['app_context_ms'] = (time.perf_counter() - ctx_start) * 1000
    
    dict_start = time.perf_counter()
    dictionary_words = _get_flow_dictionary_words()
    timings['dictionary_ms'] = (time.perf_counter() - dict_start) * 1000
    
    user_start = time.perf_counter()
    user_context = _get_flow_user_context()
    timings['user_context_ms'] = (time.perf_counter() - user_start) * 1000
    
    text_start = time.perf_counter()
    text_context = _get_flow_text_context()
    timings['text_context_ms'] = (time.perf_counter() - text_start) * 1000
    
    code_start = time.perf_counter()
    code_context = _get_flow_code_context()
    timings['code_context_ms'] = (time.perf_counter() - code_start) * 1000
    
    # Get previous text for continuity
    prev_asr_text = ""
    if hasattr(session, 'cumulative_text') and session.cumulative_text:
        prev_asr_text = session.cumulative_text[-2000:]
    
    timings['context_total_ms'] = (time.perf_counter() - ctx_start) * 1000
    
    # Log context gathering timing
    logger.info(
        f"⏱️ CONTEXT GATHERING TIMING:\n"
        f"   🔌 Get client:       {timings['get_client_ms']:6.1f}ms\n"
        f"   📱 App context:      {timings['app_context_ms']:6.1f}ms\n"
        f"   📚 Dictionary:       {timings['dictionary_ms']:6.1f}ms ({len(dictionary_words)} words)\n"
        f"   👤 User context:     {timings['user_context_ms']:6.1f}ms\n"
        f"   📋 Text context:     {timings['text_context_ms']:6.1f}ms\n"
        f"   💻 Code context:     {timings['code_context_ms']:6.1f}ms\n"
        f"   ─────────────────────────────\n"
        f"   ⏱️ Context total:    {timings['context_total_ms']:6.1f}ms"
    )
    
    try:
        logger.info(f"🚀 Using DIRECT mode for transcription: {file_path}")
        logger.debug(
            f"Context: app={app_context.get('app_type')}/{app_context.get('app_name')}, "
            f"dict_words={len(dictionary_words)}, "
            f"user={user_context.get('user_first_name')} {user_context.get('user_last_name')}, "
            f"code_vars={len(code_context.get('variable_names', []))}"
        )
        
        # ⏱️ TIMING: API call
        api_start = time.perf_counter()
        result = await client.transcribe_file(
            audio_path=file_path,
            language=[session.language] if session.language else ["en"],
            # App context
            app_type=app_context.get("app_type", "other"),
            app_name=app_context.get("app_name"),
            # Dictionary (custom vocabulary)
            dictionary_words=dictionary_words,
            # User info (helps spell names correctly)
            user_first_name=user_context.get("user_first_name"),
            user_last_name=user_context.get("user_last_name"),
            # Text context (cursor position, selected text)
            before_text=text_context.get("before_text", ""),
            after_text=text_context.get("after_text", ""),
            selected_text=text_context.get("selected_text", ""),
            content_text=text_context.get("content_text"),
            # Code context (variable names, file names)
            variable_names=code_context.get("variable_names", []),
            file_names=code_context.get("file_names", []),
            # Previous transcription for continuity
            prev_asr_text=prev_asr_text,
        )
        timings['api_call_ms'] = (time.perf_counter() - api_start) * 1000
        
        # ⏱️ TIMING: Post-process with vocabulary manager
        postproc_start = time.perf_counter()
        if result.get("success") and result.get("text") and vocabulary_manager:
            try:
                text = result["text"]
                enhanced_text = vocabulary_manager.post_process_transcription(text)
                if enhanced_text != text:
                    logger.info(f"Vocabulary enhanced: '{text[:50]}...' -> '{enhanced_text[:50]}...'")
                result["text"] = enhanced_text
            except Exception as e:
                logger.debug(f"Vocabulary post-process failed: {e}")
        timings['postprocess_ms'] = (time.perf_counter() - postproc_start) * 1000
        
        # Update cumulative text for session continuity
        if result.get("success") and result.get("text"):
            text = result["text"]
            if hasattr(session, 'cumulative_text'):
                session.cumulative_text = (session.cumulative_text + " " + text).strip()
        
        # Calculate total time
        timings['total_ms'] = (time.perf_counter() - total_start) * 1000
        
        # Log comprehensive timing summary
        meta = result.get("metadata", {})
        logger.info(
            f"⏱️ FULL PIPELINE TIMING SUMMARY:\n"
            f"   ═══════════════════════════════════════════\n"
            f"   📊 CONTEXT GATHERING:   {timings['context_total_ms']:7.1f}ms\n"
            f"      ├─ App context:      {timings['app_context_ms']:7.1f}ms\n"
            f"      ├─ Dictionary:       {timings['dictionary_ms']:7.1f}ms\n"
            f"      ├─ User context:     {timings['user_context_ms']:7.1f}ms\n"
            f"      ├─ Text context:     {timings['text_context_ms']:7.1f}ms\n"
            f"      └─ Code context:     {timings['code_context_ms']:7.1f}ms\n"
            f"   ───────────────────────────────────────────\n"
            f"   🌐 API CALL:            {timings['api_call_ms']:7.1f}ms\n"
            f"      ├─ Preprocess:       {meta.get('preprocess_ms', 0):7.1f}ms\n"
            f"      ├─ Network:          {meta.get('network_ms', 0):7.1f}ms\n"
            f"      └─ Chunks:           {meta.get('chunk_count', 1)}\n"
            f"   ───────────────────────────────────────────\n"
            f"   📝 POST-PROCESS:        {timings['postprocess_ms']:7.1f}ms\n"
            f"   ═══════════════════════════════════════════\n"
            f"   ⏱️ TOTAL PIPELINE:      {timings['total_ms']:7.1f}ms\n"
            f"   ═══════════════════════════════════════════\n"
            f"   📜 Result: {len(result.get('text', '') or '')} chars"
        )
        
        # Add our timings to metadata
        result["metadata"] = {**meta, **timings}
        
        return result
        
    except Exception as e:
        logger.error(f"Direct flow transcription failed: {e}")
        return {
            "success": False,
            "error": f"Direct transcription error: {str(e)}"
        }


def _encode_audio_to_opus(audio_data: np.ndarray, bitrate: str = "24k") -> Optional[bytes]:
    """Convert audio data to Opus format using ffmpeg. Returns None on failure."""
    import subprocess
    import tempfile
    
    try:
        total_start = time.perf_counter()
        # Write WAV to temp file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            sf.write(wav_file.name, audio_data, 16000, format="WAV", subtype="PCM_16")
            wav_path = wav_file.name
        
        opus_path = wav_path.replace('.wav', '.opus')
        
        # Convert to Opus
        ffmpeg_start = time.perf_counter()
        result = subprocess.run([
            'ffmpeg', '-y', '-i', wav_path,
            '-c:a', 'libopus', '-b:a', bitrate, '-ar', '16000', '-ac', '1',
            opus_path
        ], capture_output=True, timeout=10)
        _trace_duration(
            "ffmpeg_opus_encode",
            ffmpeg_start,
            rc=getattr(result, "returncode", None),
            stderr_bytes=len(result.stderr) if result.stderr else 0,
            bitrate=bitrate,
            samples=len(audio_data) if hasattr(audio_data, "__len__") else None,
        )
        
        opus_data = None
        if os.path.exists(opus_path):
            with open(opus_path, 'rb') as f:
                opus_data = f.read()
            os.unlink(opus_path)
        os.unlink(wav_path)
        _trace_duration(
            "opus_encode_total",
            total_start,
            output_bytes=len(opus_data) if opus_data else 0,
        )
        
        return opus_data
    except Exception as e:
        logger.debug(f"Opus encoding failed: {e}")
        return None


def _encode_audio_data_for_flow(audio_data: np.ndarray) -> tuple:
    """Encode preprocessed 16kHz mono audio data to base64 for Flow."""
    encode_start = time.perf_counter()
    # Try Opus encoding first (much smaller, faster upload)
    if FLOW_USE_OPUS:
        opus_data = _encode_audio_to_opus(audio_data, FLOW_OPUS_BITRATE)
        if opus_data:
            b64_start = time.perf_counter()
            audio_base64 = base64.b64encode(opus_data).decode("utf-8")
            _trace_duration(
                "base64_encode_opus",
                b64_start,
                input_bytes=len(opus_data),
                output_chars=len(audio_base64),
            )
            _trace_duration("encode_audio_total", encode_start, encoding="opus")
            logger.debug(f"Opus encoded: {len(audio_data)*2} bytes WAV -> {len(opus_data)} bytes Opus")
            return audio_base64, "opus"

    # Fallback to WAV
    wav_start = time.perf_counter()
    buffer = BytesIO()
    sf.write(buffer, audio_data, 16000, format="WAV", subtype="PCM_16")
    wav_bytes = buffer.getvalue()
    audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")
    _trace_duration(
        "base64_encode_wav",
        wav_start,
        input_bytes=len(wav_bytes),
        output_chars=len(audio_base64),
    )
    _trace_duration("encode_audio_total", encode_start, encoding="wav")
    return audio_base64, "wav"


def _encode_audio_for_flow(file_path: str, content_type: Optional[str]) -> tuple:
    """Load audio and return (base64_data, encoding_type).
    
    Uses Opus encoding if FLOW_USE_OPUS=1 (default) for ~5x faster uploads.
    Falls back to WAV if Opus encoding fails.
    """
    raw_bytes = None
    try:
        with open(file_path, "rb") as f:
            raw_bytes = f.read()
    except Exception:
        raw_bytes = None

    def _wav_is_16k_mono(wav_bytes: bytes) -> bool:
        if len(wav_bytes) < 44:
            return False
        if wav_bytes[:4] != b"RIFF" or wav_bytes[8:12] != b"WAVE":
            return False
        # Walk chunks to find "fmt " chunk
        offset = 12
        while offset + 8 <= len(wav_bytes):
            chunk_id = wav_bytes[offset:offset + 4]
            chunk_size = int.from_bytes(wav_bytes[offset + 4:offset + 8], "little")
            if chunk_id == b"fmt " and offset + 8 + 16 <= len(wav_bytes):
                fmt = wav_bytes[offset + 8:offset + 8 + 16]
                audio_format = int.from_bytes(fmt[0:2], "little")
                channels = int.from_bytes(fmt[2:4], "little")
                sample_rate = int.from_bytes(fmt[4:8], "little")
                bits_per_sample = int.from_bytes(fmt[14:16], "little")
                return audio_format in (1, 3) and channels == 1 and sample_rate == 16000 and bits_per_sample == 16
            offset += 8 + chunk_size
        return False

    # Load and preprocess audio
    try:
        if raw_bytes and _wav_is_16k_mono(raw_bytes):
            # Already 16kHz mono WAV - load it
            audio_data, _ = sf.read(BytesIO(raw_bytes))
        elif content_type and "video" in content_type:
            audio_data, sample_rate = process_video_to_audio(file_path)
            audio_data = preprocess_audio(audio_data, sample_rate)
        else:
            audio_data, sample_rate = sf.read(file_path)
            audio_data = preprocess_audio(audio_data, sample_rate)
    except Exception:
        audio_data, sample_rate = process_video_to_audio(file_path)
        audio_data = preprocess_audio(audio_data, sample_rate)

    # Trim silence if enabled
    if FLOW_TRIM_SILENCE:
        try:
            abs_audio = np.abs(audio_data)
            active = np.where(abs_audio > FLOW_SILENCE_THRESHOLD)[0]
            if active.size > 0:
                pad = int(16000 * (FLOW_SILENCE_PAD_MS / 1000.0))
                start = max(int(active[0]) - pad, 0)
                end = min(int(active[-1]) + pad, len(audio_data))
                audio_data = audio_data[start:end]
        except Exception as e:
            logger.debug(f"Flow silence trim failed: {e}")

    return _encode_audio_data_for_flow(audio_data)


def _audio_to_base64_wav(audio_data: np.ndarray) -> str:
    buffer = BytesIO()
    sf.write(buffer, audio_data, 16000, format="WAV", subtype="PCM_16")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _split_audio_chunks(audio_data: np.ndarray, chunk_seconds: float, overlap_seconds: float) -> List[np.ndarray]:
    chunk_seconds = max(0.2, float(chunk_seconds))
    overlap_seconds = max(0.0, float(overlap_seconds))
    chunk_samples = int(chunk_seconds * 16000)
    overlap_samples = int(overlap_seconds * 16000)
    step = max(1, chunk_samples - overlap_samples)
    chunks = []
    start = 0
    while start < len(audio_data):
        end = min(start + chunk_samples, len(audio_data))
        chunks.append(audio_data[start:end])
        if end >= len(audio_data):
            break
        start += step
    return chunks


def _merge_chunk_text(existing: str, new: str, max_overlap_words: int = 10) -> str:
    """Merge chunk texts with overlap handling. Increased overlap for better continuity."""
    if not existing:
        return new.strip()
    if not new:
        return existing.strip()
    existing_words = existing.strip().split()
    new_words = new.strip().split()
    max_overlap = min(max_overlap_words, len(existing_words), len(new_words))
    overlap = 0
    for i in range(max_overlap, 0, -1):
        if existing_words[-i:] == new_words[:i]:
            overlap = i
            break
    merged = existing_words + new_words[overlap:]
    return " ".join(merged).strip()


def _flow_transcribe_base64_with_retry(session, audio_base64: str, audio_encoding: str = "wav", before_text: Optional[str] = None, max_retries: int = 3) -> Dict[str, Optional[str]]:
    """Transcribe with exponential backoff retry on transient failures."""
    import time
    last_error = None

    for attempt in range(max_retries):
        try:
            result = _flow_transcribe_base64(session, audio_base64, audio_encoding, before_text)
            if result.get("success"):
                return result
            last_error = result.get("error", "Unknown error")
            # Don't retry on client errors (4xx) except 429 (rate limit)
            if "HTTP 4" in last_error and "429" not in last_error:
                return result
        except Exception as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            # Exponential backoff: 2s, 4s, 8s
            wait_time = 2 ** (attempt + 1)
            logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay: {last_error}")
            time.sleep(wait_time)

    return {
        "success": False,
        "error": f"Failed after {max_retries} retries: {last_error}"
    }


async def _flow_transcribe_chunks_parallel(
    chunks: List[np.ndarray],
    session: "TranscriptionSession",
    concurrent_limit: int = 3,
    progress_callback: Optional[Callable[[TranscriptionProgress], None]] = None
) -> Dict[str, Any]:
    """
    Transcribe multiple chunks in parallel with rate limiting.

    Args:
        chunks: List of audio chunks
        session: Transcription session
        concurrent_limit: Max parallel requests (respect 60 req/min limit)
        progress_callback: Optional callback for progress updates

    Returns:
        Merged transcription result
    """
    if not chunks:
        return {"success": False, "error": "No chunks to transcribe"}

    logger.info(f"Starting parallel transcription of {len(chunks)} chunks (concurrent_limit={concurrent_limit})")
    start_time = time.time()

    semaphore = asyncio.Semaphore(concurrent_limit)
    results = [None] * len(chunks)

    def transcribe_chunk(idx: int, chunk: np.ndarray):
        """Encode and transcribe a single chunk."""
        # Encode chunk to Opus or WAV
        audio_base64 = None
        audio_encoding = "wav"
        if FLOW_USE_OPUS:
            opus_data = _encode_audio_to_opus(chunk, FLOW_OPUS_BITRATE)
            if opus_data:
                audio_base64 = base64.b64encode(opus_data).decode("utf-8")
                audio_encoding = "opus"

        if not audio_base64:
            audio_base64 = _audio_to_base64_wav(chunk)
            audio_encoding = "wav"

        # Get previous text for context
        before_text = ""
        if idx > 0 and results[idx - 1] and results[idx - 1].get("success"):
            before_text = results[idx - 1].get("text", "")

        # Transcribe with retry
        result = _flow_transcribe_base64_with_retry(
            session, audio_base64, audio_encoding, before_text
        )

        # Report progress
        if progress_callback and result.get("success"):
            progress = TranscriptionProgress(
                current_chunk=idx + 1,
                total_chunks=len(chunks),
                chunk_text=result.get("text", ""),
                percent_complete=((idx + 1) / len(chunks)) * 100
            )
            try:
                # Run callback in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, progress_callback, progress)
            except Exception as e:
                logger.debug(f"Progress callback failed: {e}")

        return idx, result

    # Use ThreadPoolExecutor for parallel API calls
    from concurrent.futures import ThreadPoolExecutor, as_completed

    with ThreadPoolExecutor(max_workers=concurrent_limit) as executor:
        # Submit all tasks
        future_to_idx = {
            executor.submit(transcribe_chunk, idx, chunk): idx
            for idx, chunk in enumerate(chunks)
        }

        # Collect results as they complete
        for future in as_completed(future_to_idx):
            idx, result = future.result()
            results[idx] = result
            logger.info(f"Chunk {idx + 1}/{len(chunks)} completed: success={result.get('success')}")

    # Merge results
    merged_text = ""
    failed_chunks = 0

    for idx, result in enumerate(results):
        if result and result.get("success") and result.get("text"):
            merged_text = _merge_chunk_text(merged_text, result.get("text", ""))
        else:
            failed_chunks += 1
            logger.warning(f"Chunk {idx + 1} failed: {result.get('error', 'Unknown error') if result else 'No result'}")

    elapsed = time.time() - start_time
    logger.info(
        f"Parallel transcription completed: {len(chunks)} chunks, "
        f"{failed_chunks} failed, {elapsed:.1f}s total, "
        f"{elapsed / len(chunks):.1f}s avg per chunk"
    )

    if failed_chunks > 0:
        return {
            "success": True,
            "text": merged_text,
            "warning": f"{failed_chunks}/{len(chunks)} chunks failed"
        }

    return {"success": True, "text": merged_text}


def _flow_transcribe_base64(session, audio_base64: str, audio_encoding: str = "wav", before_text: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Send base64 audio to Wispr Flow API and return result dict."""
    app_context = _get_flow_app_context()
    dictionary_words = _get_flow_dictionary_words()
    payload_chars = len(audio_base64) if audio_base64 else 0

    # Build payload matching Wispr Flow desktop app structure exactly
    if FLOW_USE_BASETEN:
        # Direct Baseten API - use exact structure from test_wisperv2.py
        payload = {
            "request": {
                "access_token": FLOW_JWT_TOKEN,
                "user": {"uuid": FLOW_USER_UUID},
                "metadata": {
                    "session_id": session.session_id,
                    "environment": "production",
                    "client_platform": "win32",  # Mimic Windows to blend in
                    "client_version": "1.4.205",
                    "transcript_entity_uuid": str(uuid.uuid4()),
                },
                "audio": audio_base64,  # KEY IS 'audio', NOT 'audio_base64'!
                "audio_encoding": audio_encoding,
                "language": [session.language] if session.language else ["en"],
                "context": {
                    "app": {
                        "name": app_context.get("app_name"),
                        "type": app_context.get("app_type", "other"),
                    },
                    "dictionary_context": dictionary_words,
                    "textbox_contents": {
                        "before_text": before_text or "",
                        "selected_text": "",
                        "after_text": "",
                    },
                },
                "prev_asr_text": session.cumulative_text[-2000:] if hasattr(session, 'cumulative_text') and session.cumulative_text else "",
            }
        }
        endpoint_url = FLOW_BASETEN_URL
        headers = {
            "Authorization": f"Api-Key {FLOW_BASETEN_API_KEY}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 WisprFlow/1.4.205",
        }
    else:
        # Local proxy mode - simpler structure
        payload = {
            "audio_base64": audio_base64,
            "audio_encoding": audio_encoding,
            "language": [session.language] if session.language else ["en"],
            "app_type": app_context.get("app_type", "other"),
            "app_name": app_context.get("app_name"),
            "dictionary_words": dictionary_words,
        }
        if hasattr(session, 'cumulative_text') and session.cumulative_text:
            payload["prev_asr_text"] = session.cumulative_text[-2000:]
        if before_text:
            payload["before_text"] = before_text
        endpoint_url = f"{FLOW_SERVER_URL}/transcribe"
        headers = {}

    request_start = time.perf_counter()
    response = _flow_session.post(
        endpoint_url,
        json=payload,
        headers=headers,
        timeout=FLOW_TIMEOUT
    )
    network_ms = _trace_duration(
        "flow_http_post",
        request_start,
        status=response.status_code,
        payload_chars=payload_chars,
        encoding=audio_encoding,
        baseten=FLOW_USE_BASETEN,
    )
    metadata = {
        "network_ms": network_ms,
        "payload_chars": payload_chars,
        "audio_encoding": audio_encoding,
        "baseten": FLOW_USE_BASETEN,
    }

    if response.status_code != 200:
        return {
            "success": False,
            "error": f"Flow server HTTP {response.status_code}: {response.text}",
            "metadata": metadata,
        }

    # Handle Baseten response format vs local proxy format
    if FLOW_USE_BASETEN:
        data = response.json()
        logger.info(f"🔍 Baseten API response: {data}")
        # Baseten wraps response - extract the actual data
        if isinstance(data, dict) and "asr_text" in data:
            text = data.get("asr_text") or data.get("pipeline_text") or data.get("llm_text")
        else:
            text = data.get("text")
    else:
        data = response.json()
        logger.info(f"🔍 Flow proxy response: {data}")
        text = data.get("text")
    
    logger.info(f"📝 Extracted text: '{text}'")
    
    if text:
        text = clean_text(text)
        if vocabulary_manager and text:
            try:
                text = vocabulary_manager.post_process_transcription(text)
            except Exception as e:
                logger.debug(f"Flow vocabulary post-process failed: {e}")
        
        # Update cumulative text for session continuity
        if hasattr(session, 'cumulative_text'):
            session.cumulative_text = (session.cumulative_text + " " + text).strip()
        
        return {
            "success": True,
            "text": text,
            "metadata": metadata,
        }

    return {
        "success": False,
        "error": str(data),
        "metadata": metadata,
    }


async def _flow_transcribe_file(session, file_path: str, content_type: Optional[str], use_parallel: bool = True) -> Dict[str, Optional[str]]:
    """
    Route transcription to direct or API mode based on FLOW_DIRECT_MODE.
    
    Direct mode (default): Ultra-fast in-memory processing via wisper-flow
    API mode (legacy): HTTP to wispr_flow_server.py on port 9095
    
    Args:
        session: TranscriptionSession
        file_path: Path to audio file
        content_type: MIME type
        use_parallel: Whether to use parallel chunk processing (API mode only)
    
    Returns:
        Dict with success, text, error keys
    """
    if FLOW_DIRECT_MODE:
        # Direct mode - no API server overhead
        return await _flow_transcribe_file_direct(session, file_path, content_type)
    
    # Legacy API mode
    return await _flow_transcribe_file_api(session, file_path, content_type, use_parallel)


async def _flow_transcribe_file_api(session, file_path: str, content_type: Optional[str], use_parallel: bool = True) -> Dict[str, Optional[str]]:
    """
    Legacy API mode: Send audio to Wispr Flow API server (port 9095).

    Uses parallel chunk processing for long audio files to improve performance.
    
    Note: Consider using FLOW_DIRECT_MODE=1 for better performance.
    """
    timings: Dict[str, Any] = {}
    total_start = time.perf_counter()

    # Load and preprocess audio
    load_start = time.perf_counter()
    try:
        if content_type and "video" in content_type:
            audio_data, sample_rate = process_video_to_audio(file_path)
        else:
            audio_data, sample_rate = sf.read(file_path)
    except Exception:
        audio_data, sample_rate = process_video_to_audio(file_path)
    timings["load_ms"] = _trace_duration(
        "flow_api_load_audio",
        load_start,
        file=os.path.basename(file_path),
        content_type=content_type,
    )

    preprocess_start = time.perf_counter()
    processed = preprocess_audio(audio_data, sample_rate)
    timings["preprocess_ms"] = _trace_duration(
        "flow_api_preprocess",
        preprocess_start,
        samples=len(processed),
        sample_rate=sample_rate,
    )

    # Trim silence if enabled
    trim_start = time.perf_counter()
    if FLOW_TRIM_SILENCE:
        try:
            abs_audio = np.abs(processed)
            active = np.where(abs_audio > FLOW_SILENCE_THRESHOLD)[0]
            if active.size > 0:
                pad = int(16000 * (FLOW_SILENCE_PAD_MS / 1000.0))
                start = max(int(active[0]) - pad, 0)
                end = min(int(active[-1]) + pad, len(processed))
                processed = processed[start:end]
        except Exception as e:
            logger.debug(f"Flow silence trim failed: {e}")
    timings["trim_ms"] = _trace_duration(
        "flow_api_trim_silence",
        trim_start,
        enabled=FLOW_TRIM_SILENCE,
        samples=len(processed),
    ) if FLOW_TRIM_SILENCE else 0.0

    # Calculate audio duration and estimated base64 size
    audio_duration = len(processed) / 16000
    # Estimate base64 size (Opus is ~1/13th of WAV)
    estimated_base64_mb = (len(processed) * 2) / (1024 * 1024) / 13

    def _finalize_result(result: Dict[str, Any], mode: str, chunk_count: int, audio_encoding: Optional[str] = None) -> Dict[str, Any]:
        timings["total_ms"] = (time.perf_counter() - total_start) * 1000
        timings["mode"] = mode
        timings["chunk_count"] = chunk_count
        timings["audio_seconds"] = audio_duration
        timings["estimated_base64_mb"] = estimated_base64_mb
        if audio_encoding:
            timings["audio_encoding"] = audio_encoding
        meta = result.get("metadata", {}) if isinstance(result, dict) else {}
        if meta.get("network_ms") is not None:
            timings["network_ms"] = meta.get("network_ms")
        result["metadata"] = {**meta, **timings}
        logger.info(
            f"[FLOW API] mode={mode} total={timings['total_ms']:.1f}ms "
            f"load={timings.get('load_ms', 0):.1f}ms preprocess={timings.get('preprocess_ms', 0):.1f}ms "
            f"trim={timings.get('trim_ms', 0):.1f}ms encode={timings.get('encode_ms', 0):.1f}ms "
            f"network={timings.get('network_ms', 0):.1f}ms audio={audio_duration:.2f}s "
            f"chunks={chunk_count} encoding={audio_encoding or meta.get('audio_encoding', 'n/a')}"
        )
        return result

    # Decide whether to use chunking or single request
    if not FLOW_CHUNK_MODE and estimated_base64_mb <= FLOW_MAX_BASE64_MB and audio_duration <= 60:
        # Single request for short audio (no chunking mode, under limits)
        encode_start = time.perf_counter()
        audio_base64, audio_encoding = _encode_audio_data_for_flow(processed)
        timings["encode_ms"] = _trace_duration(
            "flow_api_encode",
            encode_start,
            encoding=audio_encoding,
            audio_seconds=audio_duration,
            samples=len(processed),
        )
        result = _flow_transcribe_base64(session, audio_base64, audio_encoding)
        return _finalize_result(result, "single", 1, audio_encoding)

    # Use parallel chunking for long audio or when chunk mode is enabled
    split_start = time.perf_counter()
    chunks = _split_audio_chunks(processed, FLOW_CHUNK_SECONDS, FLOW_CHUNK_OVERLAP)
    timings["chunk_split_ms"] = _trace_duration(
        "flow_api_split_chunks",
        split_start,
        chunk_count=len(chunks),
        audio_seconds=audio_duration,
    )

    if len(chunks) == 1:
        # Single chunk - no need for parallel processing
        encode_start = time.perf_counter()
        audio_base64, audio_encoding = _encode_audio_data_for_flow(chunks[0])
        timings["encode_ms"] = _trace_duration(
            "flow_api_encode",
            encode_start,
            encoding=audio_encoding,
            audio_seconds=audio_duration,
            samples=len(chunks[0]),
        )
        result = _flow_transcribe_base64(session, audio_base64, audio_encoding)
        return _finalize_result(result, "single_chunk", 1, audio_encoding)

    logger.info(
        f"Using parallel chunking: {len(chunks)} chunks, "
        f"{audio_duration:.1f}s audio, {estimated_base64_mb:.2f}MB estimated"
    )

    # Use parallel processing for multiple chunks
    if use_parallel:
        # Progress callback to update session
        def progress_callback(progress: TranscriptionProgress):
            session.text = f"Processing: {progress.current_chunk}/{progress.total_chunks} chunks ({progress.percent_complete:.0f}%)"
            session.last_active = time.time()

        chunk_start = time.perf_counter()
        # Run parallel transcription (await since we're already in async context)
        result = await _flow_transcribe_chunks_parallel(
            chunks, session, concurrent_limit=3, progress_callback=progress_callback
        )
        timings["chunk_transcribe_ms"] = _trace_duration(
            "flow_api_chunk_transcribe",
            chunk_start,
            chunk_count=len(chunks),
        )

        if result.get("success"):
            session.text = result.get("text", "")
            session.status = "processing"
            session.last_active = time.time()
            if result.get("warning"):
                logger.warning(f"Transcription completed with warning: {result.get('warning')}")

        return _finalize_result(result, "chunk_parallel", len(chunks))
    else:
        # Sequential processing (fallback)
        merged_text = ""
        chunk_start = time.perf_counter()
        for idx, chunk in enumerate(chunks):
            audio_base64 = None
            audio_encoding = "wav"
            if FLOW_USE_OPUS:
                opus_data = _encode_audio_to_opus(chunk, FLOW_OPUS_BITRATE)
                if opus_data:
                    audio_base64 = base64.b64encode(opus_data).decode("utf-8")
                    audio_encoding = "opus"

            if not audio_base64:
                audio_base64 = _audio_to_base64_wav(chunk)
                audio_encoding = "wav"

            result = _flow_transcribe_base64(
                session,
                audio_base64,
                audio_encoding=audio_encoding,
                before_text=merged_text
            )
            if result.get("success") and result.get("text"):
                merged_text = _merge_chunk_text(merged_text, result.get("text", ""))
                session.text = merged_text
                session.status = "processing"
                session.last_active = time.time()
            else:
                return _finalize_result(result, "chunk_sequential", len(chunks), audio_encoding)
        timings["chunk_transcribe_ms"] = _trace_duration(
            "flow_api_chunk_transcribe",
            chunk_start,
            chunk_count=len(chunks),
        )
        return _finalize_result({"success": True, "text": merged_text}, "chunk_sequential", len(chunks))

# ============================================================================
# TRANSCRIPTION SESSION
# ============================================================================
class TranscriptionSession:
    def __init__(self, session_id, language="en", beam_size=3, vad_filter=False):
        self.session_id = session_id
        self.language = language
        self.beam_size = beam_size
        self.vad_filter = vad_filter
        self.audio_queue = queue.Queue(maxsize=200)
        self.results = []
        self.stop_event = threading.Event()
        self.created_at = time.time()
        self.last_active = time.time()
        self.text = ""
        self.worker_thread = None
        self.status = "created"

        self.accumulated_audio = []
        self.accumulated_duration = 0.0

        # Session continuity for Wispr Flow (prev_asr_text)
        self.cumulative_text = ""  # Accumulates all transcribed text for context

        # Perplexity-recommended settings for optimal transcription
        self.min_chunk_size = 1.0  # Process every 1 second (best quality-latency tradeoff)
        self.buffer_trim_threshold = float('inf')  # No buffer trimming - process entire file
        self.max_buffer_duration = float('inf')  # No duration limit - process entire file

        # For WebSocket streaming
        self.max_transcription_wait = 3600.0  # 1 hour for streaming
        self.transcription_start_time = None

        # Audio buffer and history
        self.audio_history = np.array([], dtype=np.float32)
        self.history_duration = 0.0

        # Transcription state
        self.last_transcription = ""
        self.confirmed_text = ""  # Confirmed stable text
        self.previous_transcription = ""  # For LocalAgreement-2 policy
        self.context_words = 200  # Last 200 words for context
        self.transcription_history = []
        self.max_history_segments = 5
        self.last_segment_ids = []

        # Queue monitoring statistics
        self.queue_stats = {
            "puts": 0,
            "gets": 0,
            "blocks": 0,
            "full_drops": 0,
            "audio_drops": 0,
            "max_depth": 0,
            "blocked_time_ms": [],
        }
    
    def start(self, model):
        """Start the transcription worker thread."""
        self.status = "running"
        self.worker_thread = threading.Thread(
            target=self.transcription_worker,
            args=(model,)
        )
        self.worker_thread.daemon = True
        self.worker_thread.start()
        logger.info(f"Started transcription session {self.session_id}")
        return self.session_id
    
    def _get_context_prompt(self):
        """Get last 200 words as context prompt for inter-sentence coherence."""
        if not self.confirmed_text:
            return None
        words = self.confirmed_text.split()
        if len(words) <= self.context_words:
            return self.confirmed_text
        return " ".join(words[-self.context_words:])
    
    def _is_hallucinated(self, segments, threshold: int = 3) -> bool:
        """
        Detect repetitive text indicating hallucination.
        
        Args:
            segments: List of transcription segments
            threshold: Number of consecutive repetitions to detect
        
        Returns:
            True if hallucination detected, False otherwise
        """
        if len(segments) < threshold + 1:
            return False
        
        texts = [seg.text.strip() for seg in segments]
        
        # Check for exact repetition
        for i in range(len(texts) - threshold):
            if texts[i:i+threshold] == texts[i+1:i+threshold+1]:
                return True
        
        return False
    
    def _process_accumulated_audio(self, model, audio_data):
        """Helper method to process accumulated audio data with Perplexity best practices."""
        try:
            process_start = time.perf_counter()
            timings: Dict[str, float] = {}
            # Add to audio history and trim if needed
            self.audio_history = np.concatenate([self.audio_history, audio_data])
            self.history_duration = len(self.audio_history) / 16000.0
            
            # Trim buffer at sentence boundaries if over threshold (for very long sessions)
            # Skip trimming if threshold is infinity
            if not np.isinf(self.buffer_trim_threshold) and self.history_duration > self.buffer_trim_threshold:
                # Keep last 60 seconds (1 minute)
                samples_to_keep = int(60.0 * 16000)
                self.audio_history = self.audio_history[-samples_to_keep:]
                self.history_duration = len(self.audio_history) / 16000.0
                logger.info(f"Session {self.session_id}: Trimmed buffer to {self.history_duration:.2f}s")
            
            # Transcribe entire buffer (use all if max_buffer_duration is infinity)
            if np.isinf(self.max_buffer_duration):
                audio_to_transcribe = self.audio_history
            else:
                audio_to_transcribe = self.audio_history[-int(self.max_buffer_duration * 16000):]
            
            logger.info(f"Session {self.session_id}: Processing audio of {len(audio_to_transcribe)/16000:.2f}s")
            
            # Get contextual prompt (combines recent speech + vocabulary)
            # Research-proven: short context-aware prompts most effective
            enhanced_prompt = ""
            if vocabulary_manager:
                # Use new contextual prompt method
                enhanced_prompt = vocabulary_manager.get_contextual_prompt(
                    previous_text=self.confirmed_text,  # Your recent speech
                    max_words=25,  # Optimal: 15-30 words (research-backed)
                    include_vocabulary=True  # Include custom terms
                )
                if enhanced_prompt:
                    logger.info(f"Session {self.session_id}: Using contextual prompt ({len(enhanced_prompt)} chars): {enhanced_prompt[:150]}...")
                else:
                    # Fallback to context prompt from last 200 words
                    enhanced_prompt = self._get_context_prompt()
                    logger.info(f"Session {self.session_id}: No vocabulary available, using context prompt")
            else:
                # Fallback to context prompt
                enhanced_prompt = self._get_context_prompt()
                logger.info(f"Session {self.session_id}: Vocabulary manager not available, using context prompt")
            
            transcribe_start = time.perf_counter()
            segments_generator, info = model.transcribe(
                audio_to_transcribe,
                language=self.language,
                task="transcribe",
                vad_filter=True,
                initial_prompt=enhanced_prompt,  # Optimized vocabulary prompt
                temperature=0.0,  # Deterministic for consistency
                beam_size=5,  # Increased from 3 for better accuracy
                word_timestamps=False
            )
            
            segments = list(segments_generator)
            timings["transcribe_ms"] = (time.perf_counter() - transcribe_start) * 1000
            logger.info(f"Session {self.session_id}: Transcribed {len(segments)} segments")
            
            # Detect hallucinations (repetitive loops from long prompts)
            if self._is_hallucinated(segments):
                logger.warning(f"Session {self.session_id}: Hallucination detected, retrying without prompt")
                # Retry without prompt
                retry_start = time.perf_counter()
                segments_generator, info = model.transcribe(
                    audio_to_transcribe,
                    language=self.language,
                    task="transcribe",
                    vad_filter=True,
                    temperature=0.0,
                    beam_size=5
                )
                segments = list(segments_generator)
                timings["retry_ms"] = (time.perf_counter() - retry_start) * 1000
                logger.info(f"Session {self.session_id}: Retry completed with {len(segments)} segments")
            
            # Log each segment for debugging
            for i, seg in enumerate(segments):
                logger.debug(f"Session {self.session_id}: Segment {i}: '{seg.text}' (repr: {repr(seg.text)})")
            
            post_start = time.perf_counter()
            # Join segments and filter hallucinations
            raw_text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
            new_text = filter_hallucinations(raw_text)
            timings["post_ms"] = (time.perf_counter() - post_start) * 1000
            
            logger.debug(f"Session {self.session_id}: Raw text: {repr(raw_text)}")
            
            if raw_text != new_text:
                logger.info(f"Session {self.session_id}: Filtered hallucinations - Original: '{raw_text[:100]}...' -> Filtered: '{new_text[:100]}...'" if len(raw_text) > 100 else f"Session {self.session_id}: Filtered - Original: '{raw_text}' -> Filtered: '{new_text}'")
            
            # Apply TCPGen processor first (vocabulary-guided corrections during decoding)
            if tcpgen_processor and TCPGEN_ENABLED and new_text:
                tcpgen_text, tcpgen_info = tcpgen_processor.process_transcription(new_text)
                if tcpgen_info['corrections']:
                    logger.info(
                        f"Session {self.session_id}: ✨ TCPGen corrected {tcpgen_info['correction_count']} words: "
                        f"'{new_text[:80]}...' -> '{tcpgen_text[:80]}...'" if len(new_text) > 80 
                        else f"Session {self.session_id}: ✨ TCPGen: '{new_text}' -> '{tcpgen_text}'"
                    )
                    # Log specific corrections
                    for corr in tcpgen_info['corrections'][:3]:  # Show first 3
                        logger.debug(f"   • '{corr['original']}' → '{corr['corrected']}'")
                    new_text = tcpgen_text
            
            # Apply vocabulary enhancement (additional fuzzy matching)
            if vocabulary_manager and new_text:
                enhanced_text = vocabulary_manager.post_process_transcription(new_text)
                if enhanced_text != new_text:
                    logger.info(f"Session {self.session_id}: Vocabulary enhanced: '{new_text[:100]}...' -> '{enhanced_text[:100]}...'" if len(new_text) > 100 else f"Session {self.session_id}: Vocabulary enhanced: '{new_text}' -> '{enhanced_text}'")
                    new_text = enhanced_text
            
            logger.info(f"Session {self.session_id}: Final text: '{new_text[:100]}...'" if len(new_text) > 100 else f"Session {self.session_id}: Final text: '{new_text}'")
            
            # LocalAgreement-2 Policy: Only output when 2 consecutive chunks agree
            if new_text:
                # Check agreement with previous transcription
                if new_text == self.previous_transcription:
                    # Confirmed! This is stable text
                    # Find what's new compared to confirmed text
                    new_text_clean = clean_text(new_text)
                    
                    if new_text_clean != self.confirmed_text:
                        # Update confirmed text
                        self.confirmed_text = new_text_clean
                        self.text = new_text_clean
                        
                        logger.info(f"Session {self.session_id}: Confirmed text: '{self.text[:200]}...'" if len(self.text) > 200 else f"Session {self.session_id}: Confirmed: '{self.text}'")
                        log_transcription(self.text, self.session_id)
                else:
                    # Not yet confirmed, save for next comparison
                    self.previous_transcription = new_text
                    logger.debug(f"Session {self.session_id}: Waiting for confirmation...")
            elif not new_text:
                logger.debug(f"Session {self.session_id}: No text from transcription")
            
            timings["total_ms"] = (time.perf_counter() - process_start) * 1000
            logger.info(
                f"Session {self.session_id}: Local pipeline timing total={timings['total_ms']:.1f}ms "
                f"transcribe={timings.get('transcribe_ms', 0):.1f}ms "
                f"retry={timings.get('retry_ms', 0):.1f}ms "
                f"post={timings.get('post_ms', 0):.1f}ms "
                f"audio={len(audio_to_transcribe)/16000:.2f}s segments={len(segments)}"
            )
        except Exception as e:
            logger.error(f"Session {self.session_id}: Error processing audio: {e}")
        
        self.accumulated_audio = []
        self.accumulated_duration = 0.0
        gc.collect()
    
    def add_audio(self, audio_data, sample_rate):
        """Add audio data to the session queue."""
        put_start = time.perf_counter()
        self.queue_stats["puts"] += 1
        current_depth = self.audio_queue.qsize()
        if current_depth > self.queue_stats["max_depth"]:
            self.queue_stats["max_depth"] = current_depth

        try:
            processed_audio = preprocess_audio(audio_data, sample_rate)

            try:
                self.audio_queue.put(processed_audio, block=True, timeout=0.1)
            except queue.Full:
                self.queue_stats["blocks"] += 1
                blocked_ms = (time.perf_counter() - put_start) * 1000
                self.queue_stats["blocked_time_ms"].append(blocked_ms)
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put(processed_audio, block=False)
                    self.queue_stats["full_drops"] += 1
                    logger.warning(f"Session {self.session_id}: Queue full, dropping oldest")
                    _trace_duration("audio_queue_put_full", put_start, dropped="oldest", depth=current_depth)
                except (queue.Empty, queue.Full):
                    self.queue_stats["audio_drops"] += 1
                    logger.warning(f"Session {self.session_id}: Queue full, dropping audio")
                    _trace_duration("audio_queue_put_full", put_start, dropped="current", depth=current_depth)
                    return False

            self.last_active = time.time()
            return True
        except Exception as e:
            logger.error(f"Session {self.session_id}: Error adding audio: {e}")
            return False
    
    def clear(self):
        """Release memory-intensive resources."""
        logger.info(f"Clearing resources for session {self.session_id}")
        self.accumulated_audio.clear()
        self.audio_history = np.array([], dtype=np.float32)
        self.transcription_history.clear()
        gc.collect()
    
    def stop(self):
        """Stop the transcription session and clean up resources."""
        if self.status not in ["stopped", "completed", "error"]:
            self.status = "stopped"
        self.stop_event.set()
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)
        self.clear()
        logger.info(f"Stopped session {self.session_id}")
    
    def transcription_worker(self, model):
        """Process audio from queue and transcribe it."""
        self.transcription_start_time = time.time()
        last_activity_time = time.time()
        
        while not self.stop_event.is_set():
            try:
                if time.time() - self.transcription_start_time > self.max_transcription_wait:
                    if self.accumulated_audio and len(self.accumulated_audio) > 0:
                        combined_audio = np.concatenate(self.accumulated_audio)
                        self._process_accumulated_audio(model, combined_audio)
                    break
                
                try:
                    get_start = time.perf_counter()
                    audio_chunk = self.audio_queue.get(timeout=0.5)
                    self.queue_stats["gets"] += 1
                    get_ms = (time.perf_counter() - get_start) * 1000
                    current_depth = self.audio_queue.qsize()
                    if TRACE_ENABLED and get_ms > 10:
                        logger.debug(f"Session {self.session_id}: Queue get took {get_ms:.1f}ms, depth={current_depth}")
                    last_activity_time = time.time()
                except queue.Empty:
                    if (self.accumulated_audio and len(self.accumulated_audio) > 0 and 
                        time.time() - last_activity_time > 2.0):
                        combined_audio = np.concatenate(self.accumulated_audio)
                        self._process_accumulated_audio(model, combined_audio)
                        self.accumulated_audio = []
                        self.accumulated_duration = 0.0
                    continue
                
                if audio_chunk is None:
                    if self.accumulated_audio and len(self.accumulated_audio) > 0:
                        combined_audio = np.concatenate(self.accumulated_audio)
                        self._process_accumulated_audio(model, combined_audio)
                    
                    # Force-confirm any pending transcription when file upload ends
                    if self.previous_transcription and not self.text:
                        self.text = clean_text(self.previous_transcription)
                        self.confirmed_text = self.text
                        logger.info(f"Session {self.session_id}: Force-confirmed final text: '{self.text}'")
                    
                    if self.audio_queue.empty():
                        break
                    else:
                        continue
                
                chunk_duration = len(audio_chunk) / 16000
                self.accumulated_audio.append(audio_chunk)
                self.accumulated_duration += chunk_duration
                
                # Log accumulation progress every second
                if int(self.accumulated_duration) % 1 == 0:
                    logger.debug(f"Session {self.session_id}: Accumulated {self.accumulated_duration:.2f}s of audio (min: {self.min_chunk_size}s)")
                
                # Process every 1 second (Perplexity best practice)
                if self.accumulated_duration < self.min_chunk_size:
                    continue
                
                # Now we have enough audio to process
                combined_audio = np.concatenate(self.accumulated_audio)
                rms = np.sqrt(np.mean(combined_audio ** 2))
                logger.info(f"Session {self.session_id}: Processing buffer - RMS: {rms:.5f}, Duration: {len(combined_audio)/16000:.2f}s")
                
                # Process the audio for transcription
                self._process_accumulated_audio(model, combined_audio)
                
                # Clear accumulator after processing
                self.accumulated_audio = []
                self.accumulated_duration = 0.0
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in transcription worker: {e}")
        
        self.status = "completed"
        logger.info(f"Transcription worker for session {self.session_id} finished")
        # Log queue statistics if tracing is enabled
        if TRACE_ENABLED and self.queue_stats["puts"] > 0:
            blocked_times = self.queue_stats.get("blocked_time_ms", [])
            avg_blocked = sum(blocked_times) / len(blocked_times) if blocked_times else 0
            logger.info(
                f"Session {self.session_id}: Queue stats - "
                f"puts={self.queue_stats['puts']} gets={self.queue_stats['gets']} "
                f"blocks={self.queue_stats['blocks']} "
                f"full_drops={self.queue_stats['full_drops']} audio_drops={self.queue_stats['audio_drops']} "
                f"max_depth={self.queue_stats['max_depth']} avg_blocked={avg_blocked:.1f}ms"
            )

# ============================================================================
# BACKGROUND TASKS
# ============================================================================
async def process_and_transcribe_task_flow(session, file_path, content_type):
    """Background task to transcribe using Wispr Flow API (base64)."""
    try:
        result = await _flow_transcribe_file(session, file_path, content_type)
        if result.get("success"):
            session.text = result.get("text", "")
            session.status = "completed"
            session.last_active = time.time()
            log_transcription(session.text, session.session_id)
        else:
            session.status = "error"
            logger.error(f"[{session.session_id}] Flow transcription error: {result.get('error')}")

    except Exception as e:
        logger.error(f"[{session.session_id}] Flow transcription failed: {e}")
        session.status = "error"
    finally:
        if os.path.exists(file_path):
            shutil.rmtree(os.path.dirname(file_path))


def process_and_transcribe_task(session, file_path, content_type):
    """Background task to process file and add to transcription queue."""
    try:
        load_start = time.perf_counter()
        if "video" in content_type or content_type in ["application/octet-stream", "video/mp4", "video/x-matroska"]:
            logger.info(f"[{session.session_id}] Processing video file...")
            audio_data, sample_rate = process_video_to_audio(file_path)
        else:
            logger.info(f"[{session.session_id}] Processing audio file...")
            audio_data, sample_rate = sf.read(file_path)
        load_ms = _trace_duration(
            "background_file_load",
            load_start,
            file=os.path.basename(file_path),
            content_type=content_type,
        )
        logger.info(f"[{session.session_id}] File loaded in {load_ms:.1f}ms")
        
        logger.info(f"[{session.session_id}] Adding audio to session queue.")
        session.add_audio(audio_data, sample_rate)
        
    except Exception as e:
        logger.error(f"[{session.session_id}] Error in background processing: {e}")
        session.status = "error"
    finally:
        session.audio_queue.put(None)
        if os.path.exists(file_path):
            shutil.rmtree(os.path.dirname(file_path))

# ============================================================================
# VOCABULARY MANAGER INITIALIZATION
# ============================================================================
if VOCABULARY_ENABLED:
    try:
        vocabulary_manager = get_vocabulary_manager()
        logger.info("Vocabulary manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize vocabulary manager: {e}")
        vocabulary_manager = None
        VOCABULARY_ENABLED = False

# ============================================================================
# TCPGEN PROCESSOR INITIALIZATION
# ============================================================================
# TCPGen provides 20-40% improvement on custom vocabulary recognition
# Note: Actual initialization happens after vocabulary is loaded from active window
tcpgen_processor = None
TCPGEN_ENABLED = CONFIG.get('tcpgen_enabled', True)  # Enable by default

logger.info("TCPGen module available, will initialize after vocabulary loads")

# ============================================================================
# APPLICATION DETECTOR INITIALIZATION
# ============================================================================
# Global cache for window information
cached_window_info = None
window_monitor_task = None

if APP_DETECTOR_ENABLED and VOCABULARY_ENABLED:
    try:
        application_detector = ApplicationDetector()
        logger.info("Application detector initialized successfully")
        
        # Get initial window info and update vocabulary
        window_info = application_detector.get_active_window()
        if window_info:
            app_class = window_info.get('class', '') or window_info.get('initialClass', '')
            app_title = window_info.get('title', '') or window_info.get('initialTitle', '')
            logger.info(f"Initial active window: {app_class} - {app_title}")
            vocabulary_manager.update_vocabulary(app_class, app_title)
            cached_window_info = window_info
            
            # Initialize TCPGen now that vocabulary is loaded
            if TCPGEN_ENABLED and not tcpgen_processor:
                try:
                    from ..processors.tcpgen_processor import create_tcpgen_processor
                    tcpgen_processor = create_tcpgen_processor(vocabulary_manager)
                except (ImportError, ValueError):
                    import importlib.util
                    tcpgen_path = _whisper_package_root / "processors" / "tcpgen_processor.py"
                    spec = importlib.util.spec_from_file_location("tcpgen_processor", tcpgen_path)
                    tcpgen_module = importlib.util.module_from_spec(spec)
                    sys.modules["processors.tcpgen_processor"] = tcpgen_module
                    spec.loader.exec_module(tcpgen_module)
                    tcpgen_processor = tcpgen_module.create_tcpgen_processor(vocabulary_manager)
                    if tcpgen_processor:
                        logger.info("✨ TCPGen processor initialized with active vocabulary")
                        logger.info(f"   Loaded {len(vocabulary_manager.active_keywords)} vocabulary terms")
                        logger.info(f"   Expected improvement: 20-40% on custom vocabulary")
                    else:
                        logger.warning("TCPGen processor initialization failed after vocabulary load")
                        TCPGEN_ENABLED = False
                except Exception as e:
                    logger.error(f"Failed to initialize TCPGen after vocabulary load: {e}")
                    TCPGEN_ENABLED = False
            
    except Exception as e:
        logger.error(f"Failed to initialize application detector: {e}")
        application_detector = None
        APP_DETECTOR_ENABLED = False

async def monitor_window_changes():
    """Background task to monitor window changes every 100ms"""
    global cached_window_info, application_detector
    
    if not application_detector:
        return
    
    logger.info("Starting window monitoring at 100ms intervals")
    last_window_signature = None
    
    while True:
        try:
            window_info = application_detector.get_active_window()
            if window_info:
                # Create signature to detect changes
                window_signature = f"{window_info.get('class', '')}:{window_info.get('title', '')}"
                
                if window_signature != last_window_signature:
                    cached_window_info = window_info
                    last_window_signature = window_signature

                    # Log window change
                    app_class = window_info.get('class', '') or window_info.get('initialClass', '')
                    app_title = window_info.get('title', '') or window_info.get('initialTitle', '')
                    logger.info(f"🔄 Window changed: {app_class} - {app_title}")

                    # Update vocabulary immediately when window changes
                    if vocabulary_manager:
                        try:
                            vocabulary_manager.update_vocabulary(app_class, app_title)
                            logger.info(f"✅ Vocabulary updated for {app_class} ({len(vocabulary_manager.active_keywords)} terms)")
                        except Exception as e:
                            logger.error(f"Error updating vocabulary on window change: {e}")
            
            await asyncio.sleep(0.1)  # 100ms update rate
            
        except asyncio.CancelledError:
            logger.info("Window monitoring stopped")
            break
        except Exception as e:
            logger.error(f"Error in window monitoring: {e}")
            await asyncio.sleep(0.1)

# ============================================================================
# FASTAPI APP
# ============================================================================
app = FastAPI(title="Hybrid Whisper Transcription Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=API_CONFIG.get('cors_origins', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# LIFESPAN EVENTS
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Load model on startup."""
    global model, window_monitor_task
    if FLOW_MODE:
        model = None
        if FLOW_DIRECT_MODE:
            logger.info("=" * 60)
            logger.info("🚀 FLOW DIRECT MODE ENABLED")
            logger.info("=" * 60)
            logger.info("Bypassing API server for maximum performance:")
            logger.info("  • Audio preprocessing: < 15ms (vs 500-2000ms)")
            logger.info("  • No HTTP overhead: saves 50-200ms per request")
            logger.info("  • Parallel chunk processing: built-in")
            logger.info("")
            logger.info("To use legacy API mode: set FLOW_DIRECT_MODE=0")
            logger.info("=" * 60)
            # Initialize direct client early
            _get_direct_flow_client()
        else:
            logger.info(f"FLOW mode enabled (API mode). Using Wispr Flow API at {FLOW_SERVER_URL}")
            try:
                resp = requests.get(f"{FLOW_SERVER_URL}/health", timeout=2)
                if resp.status_code == 200:
                    logger.info("Wispr Flow API health check OK")
                else:
                    logger.warning(f"Wispr Flow API health check returned {resp.status_code}")
            except Exception as e:
                logger.warning(f"Wispr Flow API health check failed: {e}")
    else:
        model = load_whisper_model()
        logger.info("Server started and model loaded")
    
    # Start window monitoring task if application detector is available
    if APP_DETECTOR_ENABLED and application_detector:
        window_monitor_task = asyncio.create_task(monitor_window_changes())
        logger.info("Window monitoring task started")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global active_sessions, window_monitor_task
    
    # Stop window monitoring task
    if window_monitor_task:
        window_monitor_task.cancel()
        try:
            await window_monitor_task
        except asyncio.CancelledError:
            pass
        logger.info("Window monitoring task stopped")
    
    for session_id, session in list(active_sessions.items()):
        session.stop()
    active_sessions.clear()
    gc.collect()
    logger.info("Server shutting down")

# ============================================================================
# REST API ENDPOINTS
# ============================================================================
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Hybrid Whisper Transcription Server",
        "mode": "FLOW" if FLOW_MODE else "LOCAL",
        "flow_server": FLOW_SERVER_URL if FLOW_MODE else None,
        "endpoints": {
            "rest_api": "/docs",
            "websocket": "/ws/{session_id}",
            "sessions": "/sessions"
        }
    }

@app.post("/sessions", response_model=TranscriptionResponse)
async def create_session(request: TranscriptionRequest = TranscriptionRequest()):
    """Create a new transcription session."""
    global model, active_sessions
    
    session_id = str(uuid.uuid4())
    
    session = TranscriptionSession(
        session_id=session_id,
        language=request.language,
        beam_size=request.beam_size,
        vad_filter=request.vad_filter
    )
    if FLOW_MODE:
        session.status = "running"
    else:
        session.start(model)
    active_sessions[session_id] = session
    cleanup_sessions()

    await emit_event("WHISPER_SESSION_START", {"session_id": session_id, "language": session.language})
    
    return TranscriptionResponse(
        session_id=session_id,
        status=session.status
    )

@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """List all active transcription sessions."""
    global active_sessions
    cleanup_sessions()
    
    return [
        SessionInfo(
            session_id=session.session_id,
            status=session.status,
            created_at=session.created_at,
            last_active=session.last_active,
            text=session.text
        ) for session in active_sessions.values()
    ]

@app.get("/sessions/{session_id}", response_model=TranscriptionResponse)
async def get_session(session_id: str):
    """Get session status and current transcription."""
    global active_sessions
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    return TranscriptionResponse(
        session_id=session_id,
        status=session.status,
        text=session.text
    )

@app.delete("/sessions/{session_id}", response_model=TranscriptionResponse)
async def delete_session(session_id: str):
    """Stop and delete a transcription session."""
    global active_sessions
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    session.stop()
    
    response = TranscriptionResponse(
        session_id=session_id,
        status="deleted",
        text=session.text
    )
    
    del active_sessions[session_id]
    gc.collect()
    await emit_event("WHISPER_SESSION_END", {"session_id": session_id, "text": session.text})
    
    return response

@app.post("/sessions/{session_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    wait: bool = False
):
    """Add audio to an existing session for transcription."""
    global active_sessions, application_detector, vocabulary_manager
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    # Update vocabulary based on current active window before transcription
    if application_detector and vocabulary_manager:
        try:
            window_info = application_detector.get_active_window()
            if window_info:
                app_class = window_info.get('class', '') or window_info.get('initialClass', '')
                app_title = window_info.get('title', '') or window_info.get('initialTitle', '')
                vocabulary_manager.update_vocabulary(app_class, app_title)
                logger.debug(f"Updated vocabulary for {app_class} before transcription")
        except Exception as e:
            logger.error(f"Error updating vocabulary before transcription: {e}")
    
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, audio_file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        content_type = audio_file.content_type
        if FLOW_MODE and (wait or FLOW_SYNC):
            try:
                result = await _flow_transcribe_file(session, temp_path, content_type)
            finally:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            if result.get("success"):
                session.text = result.get("text", "")
                session.status = "completed"
                session.last_active = time.time()
                log_transcription(session.text, session.session_id)
                return TranscriptionResponse(
                    session_id=session_id,
                    status="completed",
                    text=session.text
                )
            session.status = "error"
            return TranscriptionResponse(
                session_id=session_id,
                status="error",
                text=session.text,
                error=result.get("error")
            )

        if FLOW_MODE:
            background_tasks.add_task(process_and_transcribe_task_flow, session, temp_path, content_type)
        else:
            background_tasks.add_task(process_and_transcribe_task, session, temp_path, content_type)
        session.status = "processing"

        return TranscriptionResponse(
            session_id=session_id,
            status="processing",
            text=session.text
        )
    
    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

@app.get("/api/context")
async def get_context():
    """
    Get live context including current application/window info.
    
    Returns comprehensive context for AI assistance:
    - workspace: Current application and window details
    - recent_activity: Shell commands, clipboard, keywords
    - project_context: Git info, project root
    - hooks: Triggered hooks and context additions
    
    Note: Window info is cached and updated every 100ms by background task
    """
    global cached_window_info, vocabulary_manager
    
    # Initialize context structure
    context = {
        "workspace": {
            "application": "",
            "category": "other",
            "window_title": "",
            "active_file": None,
            "workspace_id": None,
            "workspace_name": None,
            "monitor": None,
            "geometry": {
                "x": None,
                "y": None,
                "width": None,
                "height": None
            },
            "states": {
                "floating": False,
                "fullscreen": False,
                "pinned": False,
                "xwayland": False
            },
            "pid": None,
            "address": None
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
    
    # Get active window information from cache (updated every 100ms)
    if cached_window_info:
        try:
            window_info = cached_window_info
            if window_info:
                app_class = window_info.get('class', '') or window_info.get('initialClass', '')
                app_title = window_info.get('title', '') or window_info.get('initialTitle', '')
                
                # Update basic workspace info
                context["workspace"]["application"] = app_class
                context["workspace"]["window_title"] = app_title
                
                # Categorize application
                app_lower = app_class.lower()
                if app_lower in ['firefox', 'chrome', 'chromium', 'brave', 'safari', 'zen']:
                    context["workspace"]["category"] = "browser"
                elif app_lower in ['code', 'windsurf', 'cursor', 'vscode', 'sublime', 'atom', 'vim', 'nvim']:
                    context["workspace"]["category"] = "development"
                elif app_lower in ['alacritty', 'kitty', 'wezterm', 'konsole', 'gnome-terminal', 'terminator', 'org.wezfurlong.wezterm']:
                    context["workspace"]["category"] = "terminal"
                elif app_lower in ['discord', 'slack', 'teams', 'telegram', 'signal']:
                    context["workspace"]["category"] = "communication"
                elif app_lower in ['spotify', 'vlc', 'mpv', 'rhythmbox']:
                    context["workspace"]["category"] = "media"
                else:
                    context["workspace"]["category"] = "other"
                
                # Extract active file from window title if present
                if ' - ' in app_title:
                    parts = app_title.split(' - ')
                    # Check if first part looks like a filename
                    if '.' in parts[0] and len(parts[0].split()[0]) < 50:
                        context["workspace"]["active_file"] = parts[0].split()[0]
                
                # Workspace information
                workspace_data = window_info.get('workspace', {})
                if workspace_data:
                    context["workspace"]["workspace_id"] = workspace_data.get('id')
                    context["workspace"]["workspace_name"] = workspace_data.get('name')
                
                # Monitor information
                context["workspace"]["monitor"] = window_info.get('monitor')
                
                # Window geometry
                position = window_info.get('at', [])
                size = window_info.get('size', [])
                if len(position) >= 2:
                    context["workspace"]["geometry"]["x"] = position[0]
                    context["workspace"]["geometry"]["y"] = position[1]
                if len(size) >= 2:
                    context["workspace"]["geometry"]["width"] = size[0]
                    context["workspace"]["geometry"]["height"] = size[1]
                
                # Window states
                context["workspace"]["states"]["floating"] = window_info.get('floating', False)
                context["workspace"]["states"]["fullscreen"] = bool(window_info.get('fullscreen', 0))
                context["workspace"]["states"]["pinned"] = window_info.get('pinned', False)
                context["workspace"]["states"]["xwayland"] = window_info.get('xwayland', False)
                
                # Process information
                context["workspace"]["pid"] = window_info.get('pid')
                context["workspace"]["address"] = window_info.get('address')
                
                # Removed: Too verbose, logged on every /api/context request
                # logger.debug(f"Context: {app_class} ({context['workspace']['category']}) - Workspace {context['workspace']['workspace_name']} - {app_title}")
        except Exception as e:
            logger.error(f"Error getting window context: {e}")
    
    # Get vocabulary/context from context manager
    if vocabulary_manager:
        try:
            # Get comprehensive context (commands, clipboard, keywords)
            from core.context_manager import get_context_manager
            ctx_mgr = get_context_manager()
            
            # Get shell history
            commands = ctx_mgr.get_shell_history(10)  # Last 10 commands
            context["recent_activity"]["commands"] = commands
            
            # Get clipboard history
            clipboard = ctx_mgr.get_clipboard_history(5)  # Last 5 entries
            context["recent_activity"]["clipboard"] = clipboard
            
            # Extract keywords from context
            keywords = ctx_mgr.extract_vocabulary_from_context(commands, clipboard)
            context["recent_activity"]["keywords"] = keywords[:20]  # Top 20 keywords
            
        except Exception as e:
            logger.error(f"Error getting vocabulary context: {e}")
    
    return context

# ============================================================================
# WEBSOCKET ENDPOINTS
# ============================================================================
async def send_transcript_updates(websocket: WebSocket, session: TranscriptionSession):
    """Send transcript updates to connected WebSocket client."""
    last_text = ""
    try:
        while True:
            if session.text != last_text:
                try:
                    await websocket.send_json({
                        "session_id": session.session_id,
                        "text": session.text,
                        "status": session.status
                    })
                    last_text = session.text
                except RuntimeError:
                    logger.debug("WebSocket closed while sending update")
                    break
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        logger.debug("Transcript updates task cancelled")
    except Exception as e:
        logger.error(f"Error sending updates: {e}")

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time audio streaming and transcription updates."""
    global active_sessions

    if FLOW_MODE:
        await websocket.accept()
        await websocket.send_json({
            "error": "FLOW mode does not support websocket streaming. Use /sessions/{session_id}/transcribe."
        })
        await websocket.close()
        return

    await websocket.accept()
    
    if session_id not in active_sessions:
        session = TranscriptionSession(
            session_id=session_id,
            language="en",
            beam_size=3,
            vad_filter=False
        )
        session.start(model)
        active_sessions[session_id] = session
    else:
        session = active_sessions[session_id]
    
    update_task = None
    connection_closed = False
    
    try:
        update_task = asyncio.create_task(send_transcript_updates(websocket, session))
        
        while True:
            try:
                data = await websocket.receive_bytes()
                audio_data = np.frombuffer(data, dtype=np.float32)
                session.add_audio(audio_data, SAMPLE_RATE)
            except Exception:
                connection_closed = True
                break
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        if update_task:
            update_task.cancel()
        
        if not connection_closed:
            try:
                await websocket.close()
            except Exception as e:
                logger.debug(f"Error closing websocket: {e}")
        
        logger.info(f"WebSocket disconnected for session: {session_id}")

# ============================================================================
# CLEANUP & UTILITIES
# ============================================================================
def cleanup_sessions():
    """Clean up old, inactive, or completed sessions."""
    global active_sessions, last_gc_time
    current_time = time.time()
    
    if current_time - last_gc_time > GC_INTERVAL:
        gc.collect()
        last_gc_time = current_time
    
    sessions_to_remove = []
    for session_id, session in list(active_sessions.items()):
        if session.status in ["completed", "stopped", "error"]:
            sessions_to_remove.append(session_id)
            continue
        
        if current_time - session.last_active > 1800:
            logger.info(f"Cleaning up inactive session {session_id}")
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        if session_id in active_sessions:
            active_sessions[session_id].stop()
            del active_sessions[session_id]

# ============================================================================
# SERVER STARTUP
# ============================================================================
if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    logger.info(f"Starting Hybrid Whisper Server on {HOST}:{PORT}")
    logger.info(f"Model: {MODEL_SIZE}, Device: {DEVICE}, Compute Type: {COMPUTE_TYPE}")
    logger.info(f"Max Clients: {MAX_CLIENTS}, Max Connection Time: {MAX_CONNECTION_TIME}s")
    
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info"
    )
