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
import re

# ============================================================================
# CONFIG LOADING
# ============================================================================
def load_config(config_path="config.yaml"):
    """Load configuration from YAML file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    return config

# Load config
try:
    CONFIG = load_config()
except Exception as e:
    print(f"Error loading config: {e}")
    CONFIG = {}

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

MODEL_SIZE = BACKEND_CONFIG.get('model_path', 'small')
DEVICE = BACKEND_CONFIG.get('device', 'cuda')
COMPUTE_TYPE = BACKEND_CONFIG.get('compute_type', 'int8')
SAMPLE_RATE = PERFORMANCE_CONFIG.get('sample_rate', 16000)
CACHE_PATH = PERFORMANCE_CONFIG.get('cache_path', '/tmp/whisper-live-cache')

# ============================================================================
# LOGGING SETUP
# ============================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

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
        "cuda": ["float16", "int8"]
    }
    
    if COMPUTE_TYPE not in valid_compute_types[DEVICE]:
        logger.warning(f"{COMPUTE_TYPE} is not valid for {DEVICE}. Using default.")
        COMPUTE_TYPE = valid_compute_types[DEVICE][0]
    
    logger.info(f"Loading model: {MODEL_SIZE} ({DEVICE}, {COMPUTE_TYPE})")
    gc.collect()
    
    cache_dir = os.path.expanduser(CACHE_PATH)
    os.makedirs(cache_dir, exist_ok=True)
    
    model = WhisperModel(
        MODEL_SIZE,
        device=DEVICE,
        compute_type=COMPUTE_TYPE,
        cpu_threads=MODEL_CONFIG.get('cpu_threads', 4),
        num_workers=MODEL_CONFIG.get('num_workers', 2),
        download_root=cache_dir
    )
    
    logger.info("Model loaded successfully.")
    return model

def preprocess_audio(audio_data, original_sr):
    """Preprocess audio data to match Whisper requirements (16kHz, mono, float32)."""
    try:
        if audio_data.ndim > 1 and audio_data.shape[1] > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        if original_sr != 16000:
            target_length = int(len(audio_data) * 16000 / original_sr)
            indices = np.linspace(0, len(audio_data) - 1, target_length)
            audio_data = np.interp(indices, np.arange(len(audio_data)), audio_data)
        
        return audio_data.astype(np.float32)
    except Exception as e:
        logger.error(f"Error in audio preprocessing: {e}")
        return np.zeros(16000, dtype=np.float32)

def clean_text(text):
    """Clean up transcription text."""
    text = re.sub(r'([.,!?])\1+', r'\1', text)
    text = re.sub(r'([.,!?])(\w)', r'\1 \2', text)
    text = re.sub(r'(\b[\w\']+\b(?: \b[\w\']+\b)*) \1', r'\1', text, flags=re.IGNORECASE)
    text = ' '.join(text.split())
    return text.strip()

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
        self.min_audio_duration = 0.5
        
        self.max_transcription_wait = 10.0
        self.transcription_start_time = None
        self.silence_threshold = 0.01
        self.min_speech_duration = 0.3
        
        self.buffer_duration = 8.0
        self.overlap_duration = 3.0
        self.audio_history = np.array([], dtype=np.float32)
        self.history_duration = 0.0
        self.max_history_duration = 10.0
        self.last_transcription = ""
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
    
    def has_speech_content(self, audio_data):
        """Check if audio data contains speech above silence threshold."""
        if len(audio_data) == 0:
            return False
        
        rms = np.sqrt(np.mean(audio_data ** 2))
        
        if rms < self.silence_threshold:
            return False
        
        duration = len(audio_data) / 16000.0
        return duration >= self.min_speech_duration
    
    def _process_accumulated_audio(self, model, audio_data):
        """Helper method to process accumulated audio data."""
        try:
            overlap_samples = int(self.overlap_duration * 16000)
            prepended_history = self.audio_history[-overlap_samples:] if len(self.audio_history) > overlap_samples else self.audio_history
            audio_to_transcribe = np.concatenate([prepended_history, audio_data])
            
            logger.info(f"Session {self.session_id}: Processing audio of {len(audio_to_transcribe)/16000:.2f}s")
            
            vad_params = dict(
                min_silence_duration_ms=200,
                speech_pad_ms=300,
                threshold=0.3
            )
            
            segments_generator, info = model.transcribe(
                audio_to_transcribe,
                beam_size=self.beam_size,
                language=self.language,
                vad_filter=self.vad_filter,
                vad_parameters=vad_params,
                temperature=0
            )
            
            new_text = " ".join([seg.text.strip() for seg in segments_generator if seg.text.strip()])
            
            if len(new_text) > 5 and new_text != self.last_transcription:
                current_full_text = self.text
                current_lower = current_full_text.lower()
                new_lower = new_text.lower()
                overlap_length = 0
                min_overlap = min(len(current_lower), len(new_lower))
                
                for i in range(min_overlap, 0, -1):
                    if current_lower[-i:] == new_lower[:i]:
                        overlap_length = i
                        break
                
                if overlap_length > 0:
                    merged_text = current_full_text + new_text[overlap_length:]
                else:
                    if current_full_text and not current_full_text.endswith((' ', '.', '!', '?')) and not new_text.startswith((' ', '.', ',', '!', '?')):
                        merged_text = current_full_text + " " + new_text
                    else:
                        merged_text = current_full_text + new_text
                
                merged_text = clean_text(merged_text)
                self.text = merged_text
                self.last_transcription = new_text
                log_transcription(self.text, self.session_id)
            
            updated_history = np.concatenate([self.audio_history, audio_data])
            max_samples = int(self.max_history_duration * 16000)
            if len(updated_history) > max_samples:
                self.audio_history = updated_history[-max_samples:]
            else:
                self.audio_history = updated_history
            self.history_duration = len(self.audio_history) / 16000.0
            
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
                        if self.has_speech_content(combined_audio):
                            self._process_accumulated_audio(model, combined_audio)
                    break
                
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.5)
                    last_activity_time = time.time()
                except queue.Empty:
                    if (self.accumulated_audio and len(self.accumulated_audio) > 0 and 
                        time.time() - last_activity_time > 2.0):
                        combined_audio = np.concatenate(self.accumulated_audio)
                        if self.has_speech_content(combined_audio):
                            self._process_accumulated_audio(model, combined_audio)
                        self.accumulated_audio = []
                        self.accumulated_duration = 0.0
                    continue
                
                if audio_chunk is None:
                    if self.accumulated_audio and len(self.accumulated_audio) > 0:
                        combined_audio = np.concatenate(self.accumulated_audio)
                        if self.has_speech_content(combined_audio):
                            self._process_accumulated_audio(model, combined_audio)
                    if self.audio_queue.empty():
                        break
                    else:
                        continue
                
                chunk_duration = len(audio_chunk) / 16000
                self.accumulated_audio.append(audio_chunk)
                self.accumulated_duration += chunk_duration
                
                if self.accumulated_duration < self.buffer_duration and not self.audio_queue.empty():
                    continue
                
                combined_audio = np.concatenate(self.accumulated_audio)
                if self.has_speech_content(combined_audio):
                    self._process_accumulated_audio(model, combined_audio)
                else:
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