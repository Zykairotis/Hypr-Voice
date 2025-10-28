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
from typing import Optional, Dict, List
from io import BytesIO
import tempfile
import shutil

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

# ============================================================================
# CONFIG LOADING
# ============================================================================
def load_config(config_path="config/config.yaml"):
    """Load configuration from YAML file."""
    # Try different paths
    paths_to_try = [
        config_path,
        os.path.join(os.path.dirname(__file__), config_path),
        os.path.join(os.path.dirname(__file__), "config", "config.yaml"),
        "config.yaml"
    ]
    
    for path in paths_to_try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                config = yaml.safe_load(f)
                logging.info(f"Loaded config from: {path}")
                return config
    
    logging.warning(f"Config file not found, using defaults")
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

HOST = SERVER_CONFIG.get('host', 'localhost')
PORT = SERVER_CONFIG.get('port', 9090)
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
# PYDANTIC MODELS
# ============================================================================
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
        if audio_data.ndim > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        if original_sr != 16000:
            import scipy.signal as signal
            audio_data = signal.resample(audio_data, int(len(audio_data) * 16000 / original_sr))
        
        return audio_data.astype(np.float32)
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
    
    # Common hallucination patterns from YouTube training data
    hallucination_patterns = [
        r'(thank you|thanks|okay|ok|bye|goodbye|subscribe|like|comment|share|bell|notification|video|channel)\s*[.!?]*\s*',
        r'(music|applause|\[.*?\]|\(.*?\))',  # Sound annotations
        r'(\b\w+\b)(\s+\1){2,}',  # Word repeated 3+ times
        r'(\.{3,}|!{2,}|\?{2,})',  # Multiple punctuation
    ]
    
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
    
    # Remove hallucination patterns (case-insensitive)
    for pattern in hallucination_patterns:
        text = re.sub(pattern, ' ', text, flags=re.IGNORECASE)
    
    # Clean up spacing
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def log_transcription(text, session_id=None):
    """Log transcription text."""
    logger.info(f"Session {session_id}: {text}")

def process_video_to_audio(video_path: str):
    """Extract audio from video file."""
    try:
        out, err = (
            ffmpeg
            .input(video_path)
            .output('pipe:', format='wav', acodec='pcm_s16le', ac=1, ar=SAMPLE_RATE)
            .run(capture_stdout=True, capture_stderr=True)
        )
        audio_data, sample_rate = sf.read(BytesIO(out))
        return audio_data, sample_rate
    except Exception as e:
        logger.error(f"Error processing video to audio: {e}")
        raise

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
    
    def _process_accumulated_audio(self, model, audio_data):
        """Helper method to process accumulated audio data with Perplexity best practices."""
        try:
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
            
            # Get context prompt from last 200 words (Perplexity best practice)
            context_prompt = self._get_context_prompt()
            
            # Transcribe with context for inter-sentence coherence
            segments_generator, info = model.transcribe(
                audio_to_transcribe,
                language=self.language,
                task="transcribe",
                vad_filter=True,  # Enable VAD with default parameters
                initial_prompt=context_prompt  # Context for coherence
            )
            
            segments = list(segments_generator)
            logger.info(f"Session {self.session_id}: Transcribed {len(segments)} segments")
            
            # Join segments and filter hallucinations
            raw_text = " ".join([seg.text.strip() for seg in segments if seg.text.strip()])
            new_text = filter_hallucinations(raw_text)
            
            if raw_text != new_text:
                logger.info(f"Session {self.session_id}: Filtered hallucinations - Original: '{raw_text[:100]}...' -> Filtered: '{new_text[:100]}...'" if len(raw_text) > 100 else f"Session {self.session_id}: Filtered - Original: '{raw_text}' -> Filtered: '{new_text}'")
            else:
                logger.info(f"Session {self.session_id}: New text: '{new_text[:100]}...'" if len(new_text) > 100 else f"Session {self.session_id}: New text: '{new_text}'")
            
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
            
        except Exception as e:
            logger.error(f"Session {self.session_id}: Error processing audio: {e}")
        
        self.accumulated_audio = []
        self.accumulated_duration = 0.0
        gc.collect()
    
    def add_audio(self, audio_data, sample_rate):
        """Add audio data to the session queue."""
        try:
            processed_audio = preprocess_audio(audio_data, sample_rate)
            
            try:
                self.audio_queue.put(processed_audio, block=True, timeout=0.1)
            except queue.Full:
                try:
                    self.audio_queue.get_nowait()
                    self.audio_queue.put(processed_audio, block=False)
                    logger.warning(f"Session {self.session_id}: Queue full, dropping oldest")
                except (queue.Empty, queue.Full):
                    logger.warning(f"Session {self.session_id}: Queue full, dropping audio")
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
                    audio_chunk = self.audio_queue.get(timeout=0.5)
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

# ============================================================================
# BACKGROUND TASKS
# ============================================================================
def process_and_transcribe_task(session, file_path, content_type):
    """Background task to process file and add to transcription queue."""
    try:
        if "video" in content_type or content_type in ["application/octet-stream", "video/mp4", "video/x-matroska"]:
            logger.info(f"[{session.session_id}] Processing video file...")
            audio_data, sample_rate = process_video_to_audio(file_path)
        else:
            logger.info(f"[{session.session_id}] Processing audio file...")
            audio_data, sample_rate = sf.read(file_path)
        
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
    global model
    model = load_whisper_model()
    logger.info("Server started and model loaded")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown."""
    global active_sessions
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
        "endpoints": {
            "rest_api": "/docs",
            "websocket": "/ws/{session_id}",
            "sessions": "/sessions"
        }
    }

@app.post("/sessions", response_model=TranscriptionResponse)
async def create_session(request: TranscriptionRequest):
    """Create a new transcription session."""
    global model, active_sessions
    
    session_id = str(uuid.uuid4())
    
    session = TranscriptionSession(
        session_id=session_id,
        language=request.language,
        beam_size=request.beam_size,
        vad_filter=request.vad_filter
    )
    
    session.start(model)
    active_sessions[session_id] = session
    cleanup_sessions()
    
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
    
    return response

@app.post("/sessions/{session_id}/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    session_id: str,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
):
    """Add audio to an existing session for transcription."""
    global active_sessions
    
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    session = active_sessions[session_id]
    
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, audio_file.filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
        
        content_type = audio_file.content_type
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
