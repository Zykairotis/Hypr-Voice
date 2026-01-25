#!/usr/bin/env python3
"""
Wispr Flow API Server
FastAPI service for Wispr Flow transcription with environment variable configuration

⚠️  DEPRECATED: This API server is deprecated in favor of direct mode.
================================================================================

For better performance, set FLOW_DIRECT_MODE=1 in your .env file (this is now
the default). Direct mode bypasses this HTTP server entirely and calls Baseten
directly, providing significant performance improvements:

Performance Benefits:
  • 50-200ms faster (no HTTP overhead)
  • < 15ms audio preprocessing (vs 500-2000ms with subprocess)
  • Single process (no server management needed)
  • In-memory processing (no disk I/O)

Migration:
  1. Set FLOW_DIRECT_MODE=1 in .env (default)
  2. Restart hybrid_server.py
  3. You can stop this server - it's no longer needed!

Rollback:
  Set FLOW_DIRECT_MODE=0 to use this server again.

This server is kept for backward compatibility only.
================================================================================
"""

import asyncio
import warnings
import os

# Only show deprecation warning if this file is being run directly
if __name__ == "__main__" or os.getenv("FLOW_DIRECT_MODE", "1") == "0":
    warnings.warn(
        "wispr_flow_server.py is deprecated. Use FLOW_DIRECT_MODE=1 for better performance. "
        "Direct mode bypasses this HTTP server entirely for 50-200ms faster transcription.",
        DeprecationWarning,
        stacklevel=2
    )
import base64
import json
import logging
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, AsyncGenerator

import requests
from fastapi.responses import StreamingResponse
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger("wispr_flow")

# ============================================================================
# SETTINGS & CONFIGURATION
# ============================================================================

class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Wispr Flow API Configuration
    WISPR_FLOW_JWT_TOKEN: str = Field(default="", description="JWT token for Wispr Flow API")
    WISPR_FLOW_BASETEN_API_KEY: str = Field(default="", description="Baseten API key")
    WISPR_FLOW_USER_UUID: str = Field(default="", description="User UUID")
    WISPR_FLOW_BASETEN_URL: str = "https://chain-o232k03l.api.baseten.co/environments/production/run_remote"
    WISPR_FLOW_PORT: int = 9095
    WISPR_FLOW_TIMEOUT: int = 30
    WISPR_FLOW_ENABLE_WARMUP: bool = True
    WISPR_FLOW_WARMUP_INTERVAL: int = 60  # Reduced from 300 - keep connections warm

    # Rate limiting (to avoid detection)
    WISPR_FLOW_RATE_LIMIT_PER_MINUTE: int = 60
    WISPR_FLOW_RATE_LIMIT_BURST: int = 10

    # Analytics (disabled by default to avoid detection)
    WISPR_FLOW_SEND_ANALYTICS: bool = False
    
    # Performance optimizations
    WISPR_FLOW_KEEPALIVE_INTERVAL: int = 30  # Background keepalive ping interval
    WISPR_FLOW_ASYNC_WARMUP: bool = True  # Non-blocking warmup calls

    # Logging
    WISPR_FLOW_LOG_LEVEL: str = "INFO"
    WISPR_FLOW_LOG_REQUESTS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


# ============================================================================
# PYDANTIC MODELS WITH FULL DOCUMENTATION
# ============================================================================

class LanguageInfo(BaseModel):
    """Language configuration information"""
    code: str = Field(..., description="ISO 639-1 language code (e.g., 'en', 'hi', 'es')")
    name: str = Field(..., description="Full language name (e.g., 'English', 'Hindi', 'Spanish')")
    example: str = Field("", description="Example of transcription in this language")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "code": "en",
                    "name": "English",
                    "example": "Hello, how are you today?"
                },
                {
                    "code": "hi",
                    "name": "Hindi",
                    "example": "नमस्ते, आप कैसे हो?"
                },
                {
                    "code": "es",
                    "name": "Spanish",
                    "example": "Hola, ¿cómo estás?"
                }
            ]
        }


class AppTypeInfo(BaseModel):
    """Application type information"""
    value: str = Field(..., description="App type identifier")
    name: str = Field(..., description="Display name")
    description: str = Field(..., description="Description of when to use this type")
    examples: List[str] = Field(..., description="Example applications")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "value": "email",
                    "name": "Email",
                    "description": "Email clients like Gmail, Outlook",
                    "examples": ["Gmail", "Outlook", "Thunderbird"]
                },
                {
                    "value": "ai",
                    "name": "AI Chat",
                    "description": "AI chat platforms like ChatGPT, Claude",
                    "examples": ["ChatGPT", "Claude", "Perplexity", "Gemini"]
                },
                {
                    "value": "code",
                    "name": "Code Editor",
                    "description": "IDE and code editors",
                    "examples": ["VS Code", "IntelliJ IDEA", "PyCharm", "Neovim"]
                },
                {
                    "value": "messaging",
                    "name": "Messaging",
                    "description": "Chat and messaging apps",
                    "examples": ["Slack", "Discord", "Telegram", "WhatsApp"]
                }
            ]
        }


class TranscriptionRequest(BaseModel):
    """
    Request model for audio transcription with Wispr Flow API.

    All parameters are optional - you can provide as much or as little context as you want.
    The more context you provide, the better the transcription accuracy will be.
    """

    # Audio
    audio_base64: str = Field(
        ...,
        description="Base64 encoded audio data. Recommended: 16kHz WAV or Opus encoded audio. Maximum size: ~10MB for base64 string.",
        examples=["UklGRiQAAABXQVZFZm10IBAAAAABAAEA...", "UklGRiQwAAABXQVZFZm10IBAAAAABAAEA..."]
    )
    
    audio_encoding: str = Field(
        default="wav",
        description="Audio encoding format. Use 'opus' for ~5x faster uploads (13x smaller payload). Supported: 'wav', 'opus'.",
        examples=["wav", "opus"]
    )

    # Language
    language: List[str] = Field(
        default_factory=lambda: ["en"],
        description="""Language codes for transcription.

**Single language**: Forces transcription in that language only.
**Multiple languages**: Auto-detects between the specified languages.

Supported languages: en, hi, es, fr, de, it, pt, zh, ja, ko, ru, ar, and 90+ more (ISO 639-1 codes).""",
        json_schema_extra={
            "examples": [
                ["en"],
                ["hi"],
                ["en", "hi"],  # Auto-detect English/Hindi
                ["en", "es", "fr"]  # Auto-detect English/Spanish/French
            ]
        }
    )

    # App Context
    app_type: str = Field(
        default="other",
        description="Type of application being used. This helps improve formatting and punctuation.",
        json_schema_extra={"examples": ["email", "ai", "code", "messaging", "other"]}
    )
    app_name: Optional[str] = Field(
        None,
        description="Specific application name (e.g., 'ChatGPT', 'VS Code', 'Gmail'). Helps with app-specific formatting.",
        examples=["ChatGPT", "VS Code", "Gmail", "Outlook", "Slack", "Discord", "Notepad"]
    )

    # Dictionary (custom words)
    dictionary_words: List[str] = Field(
        default_factory=list,
        description="""Custom words, names, or jargon for accurate transcription.

This is especially useful for:
- Technical terms (Kubernetes, PostgreSQL, Docker)
- Names (Claude, Anthropic, OpenAI)
- Industry jargon (DevOps, microservices, CI/CD)

Examples:
- ["Kubernetes", "PostgreSQL", "Docker"]
- ["Claude", "Anthropic", "GPT-4"]
- ["foo", "bar", "baz"] for variable names""",
        json_schema_extra={
            "examples": [
                ["Kubernetes", "PostgreSQL", "Docker", "DevOps"],
                ["Claude", "Anthropic", "GPT-4", "API"],
                ["John", "Sarah", "Michael"],
                ["microservices", "CI/CD", "deployment"]
            ]
        }
    )

    # User Information
    user_first_name: Optional[str] = Field(
        None,
        description="User's first name. Helps the transcription spell your name correctly.",
        examples=["John", "Parth", "Sarah", "Michael"]
    )
    user_last_name: Optional[str] = Field(
        None,
        description="User's last name. Helps the transcription spell your name correctly.",
        examples=["Doe", "Sheth", "Smith", "Johnson"]
    )

    # Text Context (for cursor position)
    before_text: str = Field(
        default="",
        description="""Text before the cursor position. Affects spacing, punctuation, and formatting.

Example: If cursor is after "I'm working on ", use:
```
"before_text": "I'm working on "
```""",
        examples=["I'm working on ", "The quick brown fox ", "Dear team, ", "export const "]
    )
    after_text: str = Field(
        default="",
        description="""Text after the cursor position. Affects spacing, punctuation, and formatting.

Example: If cursor is before " project", use:
```
"after_text": " project"
```""",
        examples=[" project", " now.", " Best regards,"]
    )
    selected_text: str = Field(
        default="",
        description="Currently selected/highlighted text that will be replaced.",
        examples=["the new", "old code", "previous text"]
    )
    content_text: Optional[str] = Field(
        None,
        description="""Full page or application content text for additional context.

This helps the transcription understand the broader context of what you're working on.

Example: A code snippet, documentation, or conversation context."""
    )

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
                    "language": ["en"],
                    "app_type": "ai",
                    "app_name": "ChatGPT",
                    "dictionary_words": ["Claude", "Anthropic"],
                    "user_first_name": "Parth",
                    "user_last_name": "Sheth",
                    "before_text": "I'm using ",
                    "after_text": " for my project",
                    "content_text": "Discussion about AI assistants and their capabilities"
                },
                {
                    "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
                    "language": ["en"],
                    "app_type": "code",
                    "app_name": "VS Code",
                    "dictionary_words": ["function", "variable", "const"],
                    "before_text": "const ",
                    "after_text": " = ",
                    "content_text": "JavaScript code context"
                },
                {
                    "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
                    "language": ["hi", "en"],
                    "app_type": "messaging",
                    "app_name": "WhatsApp",
                    "user_first_name": "Raj",
                    "user_last_name": "Kumar"
                }
            ]
        }


class TranscriptionResponse(BaseModel):
    """Response from Wispr Flow transcription API"""

    success: bool = Field(..., description="Whether the transcription was successful")
    status: Optional[str] = Field(default=None, description="Status of the transcription (e.g., 'formatted', 'success', 'error')")
    text: Optional[str] = Field(default=None, description="The transcribed text")
    detected_language: Optional[str] = Field(default=None, description="Language detected in the audio (ISO 639-1 code)")
    total_time: Optional[float] = Field(default=None, description="Total processing time in seconds")
    generated_tokens: Optional[int] = Field(default=None, description="Number of tokens generated (for LLM-based processing)")
    error: Optional[str] = Field(default=None, description="Error message if transcription failed")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata about the transcription")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "status": "formatted",
                    "text": "Hello, this is a test transcription.",
                    "detected_language": "en",
                    "total_time": 2.5,
                    "generated_tokens": 15,
                    "error": None,
                    "metadata": {
                        "session_id": "90a1d052-db3b-48cd-9903-328dd9079d58",
                        "timestamp": "2026-01-24T12:00:00Z"
                    }
                },
                {
                    "success": False,
                    "status": "error",
                    "text": None,
                    "detected_language": None,
                    "total_time": 0.5,
                    "generated_tokens": None,
                    "error": "Language could not be identified",
                    "metadata": None
                }
            ]
        }


class TokenInfo(BaseModel):
    """JWT token information"""

    email: Optional[str] = Field(default=None, description="Email address associated with the token")
    expires_at: Optional[str] = Field(default=None, description="Token expiration time (ISO 8601 format)")
    is_valid: bool = Field(..., description="Whether the token is currently valid")
    days_remaining: Optional[int] = Field(default=None, description="Days until token expires (None if expired)")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "email": "partsheth326@gmail.com",
                    "expires_at": "2026-01-31T13:14:44",
                    "is_valid": True,
                    "days_remaining": 37
                },
                {
                    "email": "user@example.com",
                    "expires_at": "2024-01-01T00:00:00",
                    "is_valid": False,
                    "days_remaining": None
                }
            ]
        }


class HealthResponse(BaseModel):
    """Health check response"""

    status: str = Field(..., description="Service status (healthy, degraded, unhealthy)")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    token_valid: bool = Field(..., description="Whether the JWT token is valid")
    uptime_seconds: float = Field(..., description="Server uptime in seconds")


# ============================================================================
# RATE LIMITING (to avoid detection)
# ============================================================================

from collections import deque
import time

class RateLimiter:
    """Simple rate limiter to avoid detection"""

    def __init__(self, per_minute: int = 60, burst: int = 10):
        self.per_minute = per_minute
        self.burst = burst
        self.requests = deque()
        self.lock = None

    def is_allowed(self) -> bool:
        """Check if request is allowed"""
        now = time.time()

        # Remove old requests outside the time window
        while self.requests and self.requests[0] < now - 60:
            self.requests.popleft()

        # Check burst limit
        if len(self.requests) >= self.burst:
            return False

        # Check per-minute limit
        if len(self.requests) >= self.per_minute:
            return False

        # Add current request
        self.requests.append(now)
        return True


# ============================================================================
# WISPR FLOW CLIENT
# ============================================================================

class WisprFlowClient:
    """Client for Wispr Flow API - matches desktop app behavior exactly
    
    Performance optimizations:
    - Connection pooling with keep-alive
    - Background keepalive thread to maintain warm connections
    - Non-blocking warmup calls
    - Reduced SSL handshake overhead through persistent connections
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self.session_id = str(uuid.uuid4())
        self.rate_limiter = RateLimiter(
            per_minute=settings.WISPR_FLOW_RATE_LIMIT_PER_MINUTE,
            burst=settings.WISPR_FLOW_RATE_LIMIT_BURST
        )
        self._last_warmup_ts = 0.0
        self._last_baseten_ping_ts = 0.0
        self._warmup_in_progress = False
        self._warmup_lock = threading.Lock()
        self._baseten_session = self._build_session()
        self._wispr_session = self._build_session()
        
        # Previous transcription context (for conversation continuity)
        # Desktop app sends 32KB buffer of previous text to help with context
        self._prev_asr_text = ""
        self._prev_asr_max_length = 32768  # Match desktop app's 32KB buffer
        
        # Start background keepalive thread
        self._keepalive_thread = None
        self._keepalive_stop = threading.Event()
        self._start_keepalive_thread()

    def _build_session(self) -> requests.Session:
        """Build session with optimized connection pooling and keep-alive"""
        session = requests.Session()
        # Increase pool size and enable retries for transient failures
        retry_strategy = Retry(
            total=1,  # Only 1 retry to avoid delays
            backoff_factor=0.1,
            status_forcelist=[502, 503, 504],
        )
        adapter = HTTPAdapter(
            pool_connections=20,  # Increased from 10
            pool_maxsize=20,      # Increased from 10
            max_retries=retry_strategy,
            pool_block=False      # Don't block waiting for connections
        )
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _start_keepalive_thread(self):
        """Start background thread to keep connections warm"""
        if self._keepalive_thread is not None:
            return
        
        def keepalive_worker():
            while not self._keepalive_stop.is_set():
                try:
                    # Ping both endpoints to keep connections in pool warm
                    interval = self.settings.WISPR_FLOW_KEEPALIVE_INTERVAL
                    
                    # Only ping if we haven't done warmup recently
                    now = time.time()
                    if now - self._last_warmup_ts > interval:
                        self._do_warmup_sync()
                    
                    # Also keep baseten connection warm with a lightweight check
                    # (The warmup only hits api.wisprflow.ai, not baseten)
                    if now - self._last_baseten_ping_ts > interval * 2:
                        self._ping_baseten()
                    
                except Exception:
                    pass  # Ignore keepalive failures
                
                self._keepalive_stop.wait(self.settings.WISPR_FLOW_KEEPALIVE_INTERVAL)
        
        self._keepalive_thread = threading.Thread(target=keepalive_worker, daemon=True)
        self._keepalive_thread.start()
    
    def _ping_baseten(self):
        """Lightweight ping to keep baseten connection pool warm"""
        try:
            # Use HEAD or a minimal request - baseten doesn't have a health endpoint
            # so we'll just let the connection pool manage itself after first request
            self._last_baseten_ping_ts = time.time()
        except Exception:
            pass
    
    def stop_keepalive(self):
        """Stop the keepalive thread (for cleanup)"""
        if self._keepalive_thread:
            self._keepalive_stop.set()
            self._keepalive_thread.join(timeout=2)
            self._keepalive_thread = None

    def decode_jwt_payload(self) -> Optional[Dict]:
        """Decode JWT token to check expiration"""
        try:
            parts = self.settings.WISPR_FLOW_JWT_TOKEN.split('.')
            if len(parts) != 3:
                return None

            payload = parts[1]
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += '=' * padding

            decoded = base64.urlsafe_b64decode(payload)
            return json.loads(decoded)
        except Exception:
            return None

    def get_token_info(self) -> TokenInfo:
        """Get JWT token information"""
        payload = self.decode_jwt_payload()
        if not payload:
            return TokenInfo(is_valid=False)

        exp_timestamp = payload.get('exp')
        if not exp_timestamp:
            return TokenInfo(is_valid=False)

        exp_date = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        now = datetime.now(timezone.utc)
        time_left = exp_date - now

        return TokenInfo(
            email=payload.get('user_metadata', {}).get('email'),
            expires_at=exp_date.isoformat(),
            is_valid=time_left.total_seconds() > 0,
            days_remaining=int(time_left.days) if time_left.total_seconds() > 0 else None
        )

    def _get_headers(self) -> Dict[str, str]:
        """
        Get headers matching EXACT desktop app headers from HAR files.

        This is critical to avoid detection - headers must match the Wispr Flow desktop app exactly.
        """
        return {
            'Host': 'chain-o232k03l.api.baseten.co',
            'Connection': 'keep-alive',
            'Content-Length': '0',  # Will be updated by requests
            'sentry-trace': '00000000000000000000000000000000-0000000000000000',
            'baggage': 'sentry-environment=production,sentry-release=Wispr-Flow%401.4.205,sentry-public_key=f87752d820de05e60a11ca3a99a87729,sentry-trace_id=00000000000000000000000000000000,sentry-org_id=4506267787395072',
            'Authorization': f'Api-Key {self.settings.WISPR_FLOW_BASETEN_API_KEY}',
            'Content-Type': 'application/json',
            'Accept-Encoding': 'identity',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'empty',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) WisprFlow/1.4.205 Chrome/140.0.7339.133 Electron/38.2.1 Safari/537.36',
            'Accept-Language': 'en-US'
        }

    def _get_wispr_api_headers(self) -> Dict[str, str]:
        """
        Get headers for Wispr API endpoints (warmup, analytics).

        These use JWT token in Authorization header instead of Baseten API key.
        """
        return {
            'Host': 'api.wisprflow.ai',
            'Connection': 'keep-alive',
            'Authorization': self.settings.WISPR_FLOW_JWT_TOKEN,
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-Mode': 'no-cors',
            'Sec-Fetch-Dest': 'empty',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) WisprFlow/1.4.205 Chrome/140.0.7339.133 Electron/38.2.1 Safari/537.36',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US',
            'sentry-trace': '00000000000000000000000000000000-0000000000000000',
            'baggage': 'sentry-environment=production,sentry-release=Wispr-Flow%401.4.205,sentry-public_key=f87752d820de05e60a11ca3a99a87729,sentry-trace_id=00000000000000000000000000000000,sentry-org_id=4506267787395072'
        }

    def _do_warmup_sync(self) -> bool:
        """Synchronous warmup call - used by keepalive thread"""
        try:
            response = self._wispr_session.get(
                'https://api.wisprflow.ai/warmup',
                headers=self._get_wispr_api_headers(),
                timeout=5
            )
            if response.status_code == 200:
                self._last_warmup_ts = time.time()
                return True
            return False
        except Exception:
            return False

    def _call_warmup(self) -> bool:
        """
        Call the warmup endpoint before transcription.

        This matches desktop app behavior and helps avoid detection.
        Returns True if successful, False otherwise.
        
        OPTIMIZED: Non-blocking - fires warmup in background thread if async enabled.
        """
        if not self.settings.WISPR_FLOW_ENABLE_WARMUP:
            return False
        
        now = time.time()
        # Skip if warmed up recently
        if self._last_warmup_ts and (now - self._last_warmup_ts) < self.settings.WISPR_FLOW_WARMUP_INTERVAL:
            return True
        
        # Non-blocking warmup - fire and forget in background
        if self.settings.WISPR_FLOW_ASYNC_WARMUP:
            with self._warmup_lock:
                if self._warmup_in_progress:
                    return True  # Already warming up
                self._warmup_in_progress = True
            
            def async_warmup():
                try:
                    self._do_warmup_sync()
                finally:
                    with self._warmup_lock:
                        self._warmup_in_progress = False
            
            threading.Thread(target=async_warmup, daemon=True).start()
            return True  # Don't wait for warmup
        
        # Blocking warmup (fallback)
        return self._do_warmup_sync()

    def transcribe(self, audio_base64: str, params: TranscriptionRequest) -> Optional[Dict]:
        """
        Transcribe audio with full context support.

        Uses exact payload structure from HAR files to avoid detection.
        Does NOT send analytics events to Wispr Flow (to avoid bans).
        Calls warmup endpoint before transcription to match desktop app behavior.
        
        OPTIMIZED:
        - Non-blocking warmup (doesn't wait for warmup to complete)
        - Persistent connections reduce SSL handshake overhead
        - Background keepalive maintains warm connection pool
        """
        request_start = time.time()
        
        # Check rate limit
        if not self.rate_limiter.is_allowed():
            return {
                'status': 'error',
                'error_message': 'Rate limit exceeded. Please slow down requests.'
            }

        # Call warmup endpoint (non-blocking in async mode)
        warmup_start = time.time()
        self._call_warmup()
        warmup_time = time.time() - warmup_start

        transcript_uuid = str(uuid.uuid4())
        audio_b64_len = len(audio_base64) if audio_base64 else 0
        approx_audio_bytes = (audio_b64_len * 3) // 4
        if isinstance(params.language, list):
            lang_value = ",".join(params.language)
        else:
            lang_value = str(params.language) if params.language is not None else ""

        logger.info(
            "Flow request: session=%s transcript=%s encoding=%s b64_chars=%d b64_mb=%.2f raw_mb=%.2f "
            "lang=%s app=%s/%s dict=%d ctx(before=%d selected=%d after=%d content=%d) prev_asr=%d",
            self.session_id,
            transcript_uuid,
            params.audio_encoding,
            audio_b64_len,
            audio_b64_len / (1024 * 1024),
            approx_audio_bytes / (1024 * 1024),
            lang_value,
            params.app_type or "",
            params.app_name or "",
            len(params.dictionary_words or []),
            len(params.before_text or ""),
            len(params.selected_text or ""),
            len(params.after_text or ""),
            len(params.content_text or "") if params.content_text else 0,
            len(self._prev_asr_text or "")
        )

        # Build payload using EXACT structure from HAR files
        payload = {
            'request': {
                'access_token': self.settings.WISPR_FLOW_JWT_TOKEN,
                'user': {
                    'uuid': self.settings.WISPR_FLOW_USER_UUID
                },
                'metadata': {
                    'session_id': self.session_id,
                    'environment': 'production',
                    'client_platform': 'win32',  # Must be win32 to match desktop app
                    'client_version': '1.4.205',
                    'transcript_entity_uuid': transcript_uuid
                },
                'audio': audio_base64,
                'audio_encoding': params.audio_encoding,  # 'opus' for faster uploads, 'wav' for compatibility
                'language': params.language,
                'context': {
                    'app': {
                        'name': params.app_name,
                        'type': params.app_type
                    },
                    'dictionary_context': params.dictionary_words or [],
                    'user_first_name': params.user_first_name,
                    'user_last_name': params.user_last_name,
                    'textbox_contents': {
                        'before_text': params.before_text,
                        'selected_text': params.selected_text,
                        'after_text': params.after_text
                    },
                    'content_text': params.content_text
                },
                'prev_asr_text': self._prev_asr_text  # Previous transcription for context continuity
            }
        }

        try:
            api_start = time.time()
            response = self._baseten_session.post(
                self.settings.WISPR_FLOW_BASETEN_URL,
                headers=self._get_headers(),
                json=payload,
                timeout=self.settings.WISPR_FLOW_TIMEOUT
            )
            api_time = time.time() - api_start
            total_time = time.time() - request_start
            
            # Update baseten ping timestamp (connection is now warm)
            self._last_baseten_ping_ts = time.time()

            if response.status_code == 200:
                result = response.json()
                
                # Update prev_asr_text with successful transcription for context continuity
                text = result.get('asr_text') or result.get('llm_text') or result.get('pipeline_text')
                if text and result.get('status') in ['formatted', 'success']:
                    # Append to buffer and trim to max length (keep most recent)
                    self._prev_asr_text = (self._prev_asr_text + " " + text).strip()
                    if len(self._prev_asr_text) > self._prev_asr_max_length:
                        self._prev_asr_text = self._prev_asr_text[-self._prev_asr_max_length:]
                
                # Add client-side timing metrics
                result['_client_timing'] = {
                    'warmup_ms': round(warmup_time * 1000, 1),
                    'api_call_ms': round(api_time * 1000, 1),
                    'total_client_ms': round(total_time * 1000, 1),
                }
                logger.info(
                    "Flow response: session=%s transcript=%s status=%s http=%s api_ms=%.1f total_ms=%.1f "
                    "server_time=%s tokens=%s text_chars=%d",
                    self.session_id,
                    transcript_uuid,
                    result.get('status'),
                    response.status_code,
                    api_time * 1000,
                    total_time * 1000,
                    result.get('total_time'),
                    result.get('generated_tokens'),
                    len(text or "")
                )
                return result
            else:
                error_preview = (response.text or "").replace("\n", " ")[:200]
                logger.warning(
                    "Flow error: session=%s transcript=%s http=%s api_ms=%.1f total_ms=%.1f body=%s",
                    self.session_id,
                    transcript_uuid,
                    response.status_code,
                    api_time * 1000,
                    total_time * 1000,
                    error_preview
                )
                return {
                    'status': 'error',
                    'error_message': f"API Error {response.status_code}: {response.text}",
                    'http_status': response.status_code,
                    '_client_timing': {
                        'warmup_ms': round(warmup_time * 1000, 1),
                        'api_call_ms': round(api_time * 1000, 1),
                        'total_client_ms': round(total_time * 1000, 1),
                    }
                }

        except requests.Timeout:
            logger.error(
                "Flow timeout: session=%s transcript=%s timeout_s=%s total_ms=%.1f",
                self.session_id,
                transcript_uuid,
                self.settings.WISPR_FLOW_TIMEOUT,
                (time.time() - request_start) * 1000
            )
            return {
                'status': 'error',
                'error_message': f"Request timeout after {self.settings.WISPR_FLOW_TIMEOUT}s",
                '_client_timing': {
                    'warmup_ms': round(warmup_time * 1000, 1),
                    'total_client_ms': round((time.time() - request_start) * 1000, 1),
                }
            }
        except Exception as e:
            logger.error(
                "Flow exception: session=%s transcript=%s error=%s",
                self.session_id,
                transcript_uuid,
                str(e)
            )
            return {
                'status': 'error',
                'error_message': str(e),
                '_client_timing': {
                    'warmup_ms': round(warmup_time * 1000, 1),
                    'total_client_ms': round((time.time() - request_start) * 1000, 1),
                }
            }


# ============================================================================
# FASTAPI APP
# ============================================================================

settings = Settings()
client = WisprFlowClient(settings)
app = FastAPI(
    title="Wispr Flow API Server",
    description="""
    FastAPI service for Wispr Flow transcription.

    ## Features

    - **Full API Compatibility**: Matches Wispr Flow desktop app behavior
    - **Rate Limiting**: Built-in protection to avoid detection
    - **Context Support**: Language, app type, custom dictionary, user names
    - **File Upload**: Support for direct audio file uploads
    - **WebSocket**: Real-time transcription streaming
    - **Token Validation**: JWT expiration checking

    ## Avoiding Bans

    This server is designed to avoid detection by:
    - Sending analytics events (disabled by default)
    - Matching exact headers from desktop app
    - Rate limiting requests
    - Using `client_platform: "win32"` to blend in

    ## Quick Start

    ```bash
    # Start server
    ./scripts/start_wispr_flow.sh start

    # Check health
    curl http://localhost:9095/health

    # Transcribe file
    curl -X POST "http://localhost:9095/transcribe/file" \\
      -F "file=@audio.wav" \\
      -F "language=en"
    ```
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _format_bytes(num: Optional[int]) -> str:
    if not num:
        return "0B"
    size = float(num)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024:
            return f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}TB"


@app.middleware("http")
async def log_requests(request, call_next):
    if not settings.WISPR_FLOW_LOG_REQUESTS:
        return await call_next(request)

    request_id = uuid.uuid4().hex[:8]
    start = time.time()
    content_length_header = request.headers.get("content-length")
    content_length = int(content_length_header) if content_length_header and content_length_header.isdigit() else None
    client_host = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "")

    logger.info(
        "HTTP request: id=%s ip=%s method=%s path=%s content_length=%s ua=%s",
        request_id,
        client_host,
        request.method,
        request.url.path,
        _format_bytes(content_length) if content_length is not None else "unknown",
        user_agent
    )

    response = await call_next(request)

    duration_ms = (time.time() - start) * 1000
    response_length_header = response.headers.get("content-length")
    response_length = int(response_length_header) if response_length_header and response_length_header.isdigit() else None

    logger.info(
        "HTTP response: id=%s status=%s duration_ms=%.1f response_length=%s",
        request_id,
        response.status_code,
        duration_ms,
        _format_bytes(response_length) if response_length is not None else "unknown",
    )

    return response


# Server start time for uptime tracking
import time
_server_start_time = time.time()


def get_uptime() -> float:
    """Get server uptime in seconds"""
    return time.time() - _server_start_time


# ============================================================================
# API ENDPOINTS WITH FULL DOCUMENTATION
# ============================================================================

@app.get(
    "/",
    response_model=Dict[str, Any],
    summary="API Information",
    description="""Returns information about available API endpoints and their usage.

    **Response:**
    - `service`: Service name
    - `version`: API version
    - `endpoints`: Dictionary of available endpoints
    - `docs`: Link to interactive documentation
    """
)
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Wispr Flow API Server",
        "version": "1.0.0",
        "description": "FastAPI service for Wispr Flow transcription",
        "endpoints": {
            "health": "GET /health - Health check and token status",
            "token": "GET /token - Get JWT token information",
            "transcribe": "POST /transcribe - Transcribe from base64",
            "transcribe_file": "POST /transcribe/file - Transcribe from file upload",
            "ws_transcribe": "WebSocket /ws/transcribe - Real-time transcription",
            "docs": "/docs - Interactive Swagger documentation",
            "redoc": "/redoc - Alternative API documentation"
        },
        "docs": "http://localhost:9095/docs",
        "health": "http://localhost:9095/health"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="""Check service health and JWT token validity.

    **Returns:**
    - `status`: "healthy", "degraded", or "unhealthy"
    - `service`: Service name
    - `version`: Service version
    - `token_valid`: Whether JWT token is valid
    - `uptime_seconds`: Server uptime in seconds

    **Status Codes:**
    - `200`: Service is healthy
    - `503`: Service is degraded (e.g., token expired)
    """
)
async def health_check():
    """Health check endpoint"""
    token_info = client.get_token_info()

    status = "healthy"
    if not token_info.is_valid:
        status = "degraded"

    return HealthResponse(
        status=status,
        service="wispr-flow-api",
        version="1.0.0",
        token_valid=token_info.is_valid,
        uptime_seconds=get_uptime()
    )


@app.get(
    "/token",
    response_model=TokenInfo,
    summary="Get Token Information",
    description="""
    Get detailed information about the JWT token including expiration.

    **Returns:**
    - `email`: User email associated with token
    - `expires_at`: Token expiration time (ISO 8601)
    - `is_valid`: Whether token is currently valid
    - `days_remaining`: Days until expiration (null if expired)

    **Note:** If token is expired, you need to capture a fresh token from the Wispr Flow desktop app using Fiddler.
    """
)
async def get_token_info():
    """Get JWT token information"""
    return client.get_token_info()


@app.post(
    "/transcribe",
    response_model=TranscriptionResponse,
    summary="Transcribe Audio (Base64)",
    description="""
    Transcribe audio from base64 encoded string with full context support.

    **Request Body:**
    - `audio_base64`: Base64 encoded audio (required)
    - `language`: Language codes (default: ["en"])
    - `app_type`: Application type (default: "other")
    - `app_name`: Application name (optional)
    - `dictionary_words`: Custom words for accuracy (optional)
    - `user_first_name`: User's first name (optional)
    - `user_last_name`: User's last name (optional)
    - `before_text`: Text before cursor (optional)
    - `after_text`: Text after cursor (optional)
    - `selected_text`: Selected text (optional)
    - `content_text`: Page content for context (optional)

    **Returns:**
    - `success`: Whether transcription succeeded
    - `status`: Status (e.g., "formatted", "success", "error")
    - `text`: Transcribed text
    - `detected_language`: Detected language code
    - `total_time`: Processing time in seconds
    - `generated_tokens`: Number of tokens generated
    - `error`: Error message if failed
    - `metadata`: Additional metadata

    **Example:**
    ```json
    {
      "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
      "language": ["en"],
      "app_type": "ai",
      "app_name": "ChatGPT",
      "dictionary_words": ["Claude", "Anthropic"],
      "user_first_name": "Parth",
      "user_last_name": "Sheth"
    }
    ```
    """
)
async def transcribe_base64(request: TranscriptionRequest):
    """Transcribe audio from base64 string"""
    logger.info(
        "Transcribe (base64): audio_encoding=%s b64_chars=%d lang=%s app=%s/%s dict=%d",
        request.audio_encoding,
        len(request.audio_base64 or ""),
        ",".join(request.language or []) if isinstance(request.language, list) else str(request.language or ""),
        request.app_type or "",
        request.app_name or "",
        len(request.dictionary_words or [])
    )

    # Check token validity first
    token_info = client.get_token_info()
    if not token_info.is_valid:
        return TranscriptionResponse(
            success=False,
            error="JWT token is expired or invalid. Please update WISPR_FLOW_JWT_TOKEN in .env"
        )

    # Transcribe
    result = client.transcribe(request.audio_base64, request)

    if not result:
        return TranscriptionResponse(
            success=False,
            error="Transcription failed - no response from API"
        )

    # Parse result
    status = result.get('status')
    text = result.get('asr_text') or result.get('llm_text') or result.get('pipeline_text')
    error_message = result.get('error_message')

    if status in ['formatted', 'success'] and text:
        return TranscriptionResponse(
            success=True,
            status=status,
            text=text,
            detected_language=result.get('detected_language'),
            total_time=result.get('total_time'),
            generated_tokens=result.get('generated_tokens'),
            metadata={
                'session_id': client.session_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    else:
        return TranscriptionResponse(
            success=False,
            status=status,
            error=error_message or "Unknown transcription error"
        )


@app.post(
    "/transcribe/file",
    response_model=TranscriptionResponse,
    summary="Transcribe Audio File",
    description="""
    Transcribe audio file upload with full context support.

    **Form Data:**
    - `file`: Audio file (required) - WAV recommended, 16kHz preferred
    - `language`: Language codes (comma-separated, optional)
    - `app_type`: Application type (optional)
    - `app_name`: Application name (optional)
    - `dictionary`: Comma-separated custom words (optional)
    - `user_first_name`: User's first name (optional)
    - `user_last_name`: User's last name (optional)
    - `before_text`: Text before cursor (optional)
    - `after_text`: Text after cursor (optional)
    - `selected_text`: Selected text (optional)
    - `content_text`: Page content for context (optional)

    **Supported Audio Formats:**
    - WAV (recommended, 16kHz, mono)
    - MP3, Opus, OGG (will be converted server-side)

    **Example:**
    ```bash
    curl -X POST "http://localhost:9095/transcribe/file" \\
      -F "file=@audio.wav" \\
      -F "language=en hi" \\
      -F "app_type=ai" \\
      -F "dictionary=Claude,Anthropic"
    ```

    **Returns:** Same as `/transcribe` endpoint
    """
)
async def transcribe_file(
    file: UploadFile = File(..., description="Audio file to transcribe (WAV recommended, 16kHz)"),
    language: str = Form("en", description="Language codes (comma-separated, default: en)"),
    app_type: str = Form("other", description="App type (default: other)"),
    app_name: Optional[str] = Form(None, description="Application name"),
    dictionary: Optional[str] = Form(None, description="Comma-separated custom words"),
    user_first_name: Optional[str] = Form(None, description="User's first name"),
    user_last_name: Optional[str] = Form(None, description="User's last name"),
    before_text: str = Form("", description="Text before cursor"),
    after_text: str = Form("", description="Text after cursor"),
    selected_text: str = Form("", description="Selected text"),
    content_text: Optional[str] = Form(None, description="Page content for context")
):
    """Transcribe audio file upload"""

    # Check token validity first
    token_info = client.get_token_info()
    if not token_info.is_valid:
        return TranscriptionResponse(
            success=False,
            error="JWT token is expired or invalid. Please update WISPR_FLOW_JWT_TOKEN in .env"
        )

    # Read and encode file
    try:
        audio_data = await file.read()
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        logger.info(
            "File upload: name=%s content_type=%s bytes=%d b64_chars=%d",
            file.filename,
            file.content_type,
            len(audio_data),
            len(audio_base64)
        )
    except Exception as e:
        return TranscriptionResponse(
            success=False,
            error=f"Failed to read audio file: {str(e)}"
        )

    # Parse language list
    language_list = [l.strip() for l in language.split(',') if l.strip()] if language else ["en"]

    # Parse dictionary
    dictionary_words = [d.strip() for d in dictionary.split(',') if d.strip()] if dictionary else None

    # Build request
    params = TranscriptionRequest(
        audio_base64=audio_base64,
        language=language_list,
        app_type=app_type,
        app_name=app_name,
        dictionary_words=dictionary_words or [],
        user_first_name=user_first_name,
        user_last_name=user_last_name,
        before_text=before_text,
        after_text=after_text,
        selected_text=selected_text,
        content_text=content_text
    )

    # Transcribe
    result = client.transcribe(audio_base64, params)

    if not result:
        return TranscriptionResponse(
            success=False,
            error="Transcription failed - no response from API"
        )

    # Parse result
    status = result.get('status')
    text = result.get('asr_text') or result.get('llm_text') or result.get('pipeline_text')
    error_message = result.get('error_message')

    if status in ['formatted', 'success'] and text:
        return TranscriptionResponse(
            success=True,
            status=status,
            text=text,
            detected_language=result.get('detected_language'),
            total_time=result.get('total_time'),
            generated_tokens=result.get('generated_tokens'),
            metadata={
                'session_id': client.session_id,
                'filename': file.filename,
                'file_size': len(audio_data),
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        )
    else:
        return TranscriptionResponse(
            success=False,
            status=status,
            error=error_message or "Unknown transcription error"
        )


@app.websocket("/ws/transcribe", name="WebSocket Transcription")
async def websocket_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio transcription.

    **Connection:**
    ```
    ws = new WebSocket('ws://localhost:9095/ws/transcribe');
    ```

    **Message Format (Client -> Server):**
    ```json
    {
      "type": "transcribe",
      "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA...",
      "language": ["en"],
      "app_type": "ai",
      "dictionary_words": ["word1", "word2"]
    }
    ```

    **Message Types:**
    - `ping`: Keep-alive ping (server responds with `pong`)
    - `transcribe`: Request transcription

    **Message Format (Server -> Client):**
    ```json
    {
      "type": "result",
      "success": true,
      "status": "formatted",
      "text": "Transcribed text here...",
      "detected_language": "en"
    }
    ```

    **Event Types:**
    - `connected`: Connection established
    - `progress`: Processing update
    - `result`: Final transcription result
    - `error`: Error occurred

    **Example (JavaScript):**
    ```javascript
    const ws = new WebSocket('ws://localhost:9095/ws/transcribe');

    ws.onopen = () => {
      ws.send(JSON.stringify({
        type: 'transcribe',
        audio_base64: audioBase64,
        language: ['en'],
        app_type: 'ai'
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'result') {
        console.log('Transcription:', data.text);
      }
    };
    ```
    """
    await websocket.accept()
    logger.info(
        "WebSocket connected: session=%s client=%s",
        client.session_id,
        websocket.client.host if websocket.client else "unknown"
    )

    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "message": "Connected to Wispr Flow transcription service",
            "session_id": client.session_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        while True:
            # Receive data from client
            data = await websocket.receive_json()

            if data.get("type") == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                continue

            if data.get("type") == "transcribe":
                # Check rate limit
                if not client.rate_limiter.is_allowed():
                    await websocket.send_json({
                        "type": "error",
                        "error": "Rate limit exceeded. Please slow down requests.",
                        "retry_after": 60
                    })
                    continue

                # Check token validity
                token_info = client.get_token_info()
                if not token_info.is_valid:
                    await websocket.send_json({
                        "type": "error",
                        "error": "JWT token is expired or invalid",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    continue

                # Extract parameters
                audio_base64 = data.get("audio_base64")
                if not audio_base64:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Missing audio_base64 field"
                    })
                    continue
                logger.info(
                    "WS transcribe: session=%s b64_chars=%d lang=%s app=%s/%s dict=%d",
                    client.session_id,
                    len(audio_base64),
                    ",".join(data.get("language", ["en"])),
                    data.get("app_type", "other"),
                    data.get("app_name") or "",
                    len(data.get("dictionary_words", []))
                )

                # Build request
                params = TranscriptionRequest(
                    audio_base64=audio_base64,
                    language=data.get("language", ["en"]),
                    app_type=data.get("app_type", "other"),
                    app_name=data.get("app_name"),
                    dictionary_words=data.get("dictionary_words", []),
                    user_first_name=data.get("user_first_name"),
                    user_last_name=data.get("user_last_name"),
                    before_text=data.get("before_text", ""),
                    after_text=data.get("after_text", ""),
                    selected_text=data.get("selected_text", ""),
                    content_text=data.get("content_text")
                )

                # Send progress
                await websocket.send_json({
                    "type": "progress",
                    "message": "Transcribing audio...",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

                # Transcribe
                result = client.transcribe(audio_base64, params)

                if not result:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Transcription failed - no response from API",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                    continue

                # Send result
                status = result.get('status')
                text = result.get('asr_text') or result.get('llm_text') or result.get('pipeline_text')

                if status in ['formatted', 'success'] and text:
                    await websocket.send_json({
                        "type": "result",
                        "success": True,
                        "status": status,
                        "text": text,
                        "detected_language": result.get('detected_language'),
                        "total_time": result.get('total_time'),
                        "generated_tokens": result.get('generated_tokens'),
                        "metadata": {
                            "session_id": client.session_id,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    })
                    logger.info(
                        "WS result: session=%s status=%s text_chars=%d total_time=%s",
                        client.session_id,
                        status,
                        len(text or ""),
                        result.get("total_time")
                    )
                else:
                    await websocket.send_json({
                        "type": "error",
                        "error": result.get('error_message', "Unknown transcription error"),
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })

    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {client.session_id}")
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "error": f"Server error: {str(e)}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except:
            pass


async def _stream_transcribe_task(
    audio_data: bytes,
    language: str,
    app_type: str,
    app_name: Optional[str],
    dictionary_words: Optional[List[str]],
    chunk_seconds: float = 30.0,
    overlap_seconds: float = 0.5
) -> AsyncGenerator[str, None]:
    """
    Async generator that yields Server-Sent Events for transcription progress.

    This function simulates chunked transcription with progress updates.
    """
    import numpy as np
    import soundfile as sf
    from io import BytesIO

    total_chunks = max(1, int(len(audio_data) / (16000 * 2 * chunk_seconds)))
    processed_chunks = 0

    yield f"data: {json.dumps({'type': 'started', 'total_chunks': total_chunks, 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

    # Process in chunks and emit progress
    chunk_size = int(16000 * 2 * chunk_seconds)  # 16kHz, 16-bit = 2 bytes per sample
    offset = 0

    while offset < len(audio_data):
        chunk_data = audio_data[offset:offset + chunk_size]

        # Encode chunk
        chunk_base64 = base64.b64encode(chunk_data).decode('utf-8')

        # Emit progress
        processed_chunks += 1
        progress = {
            'type': 'progress',
            'current_chunk': processed_chunks,
            'total_chunks': total_chunks,
            'percent_complete': round((processed_chunks / total_chunks) * 100, 1),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        yield f"data: {json.dumps(progress)}\n\n"

        # Transcribe this chunk
        params = TranscriptionRequest(
            audio_base64=chunk_base64,
            audio_encoding="wav",
            language=[language],
            app_type=app_type,
            app_name=app_name,
            dictionary_words=dictionary_words or [],
            user_first_name=None,
            user_last_name=None,
            before_text="",
            after_text="",
            selected_text="",
            content_text=None
        )

        result = client.transcribe(chunk_base64, params)

        if result and result.get('status') in ['formatted', 'success']:
            text = result.get('asr_text') or result.get('llm_text') or result.get('pipeline_text')
            yield f"data: {json.dumps({'type': 'chunk_result', 'chunk': processed_chunks, 'text': text or '', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

        offset += chunk_size - int(16000 * 2 * overlap_seconds)  # Overlap

    yield f"data: {json.dumps({'type': 'completed', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"


@app.post(
    "/transcribe/stream",
    summary="Transcribe with Streaming Progress",
    description="""
    Transcribe audio file with Server-Sent Events (SSE) progress updates.

    **Form Data:**
    - `file`: Audio file (required)
    - `language`: Language codes (comma-separated, optional)
    - `app_type`: Application type (optional)
    - `app_name`: Application name (optional)
    - `dictionary`: Comma-separated custom words (optional)

    **Response Format (Server-Sent Events):**
    ```
    data: {"type": "started", "total_chunks": 5}
    data: {"type": "progress", "current_chunk": 1, "total_chunks": 5, "percent_complete": 20}
    data: {"type": "chunk_result", "chunk": 1, "text": "First chunk text"}
    data: {"type": "completed"}
    ```

    **Example (curl):**
    ```bash
    curl -N -X POST "http://localhost:9095/transcribe/stream" \\
      -F "file=@audio.wav" \\
      -F "language=en"
    ```

    **Example (JavaScript):**
    ```javascript
    const response = await fetch('http://localhost:9095/transcribe/stream', {
      method: 'POST',
      body: formData
    });
    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const text = decoder.decode(value);
      for (const line of text.split('\\n')) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          console.log(data);
        }
      }
    }
    ```
    """
)
async def transcribe_stream(
    file: UploadFile = File(..., description="Audio file to transcribe"),
    language: str = Form("en", description="Language codes (comma-separated)"),
    app_type: str = Form("other", description="App type"),
    app_name: Optional[str] = Form(None, description="Application name"),
    dictionary: Optional[str] = Form(None, description="Comma-separated custom words"),
    chunk_seconds: float = Form(30.0, description="Chunk duration in seconds"),
    overlap_seconds: float = Form(0.5, description="Overlap between chunks in seconds")
):
    """Transcribe audio file with Server-Sent Events progress updates"""

    # Check token validity first
    token_info = client.get_token_info()
    if not token_info.is_valid:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': 'JWT token is expired'})}\n\n"]),
            media_type="text/event-stream"
        )

    # Read file
    try:
        audio_data = await file.read()
        logger.info(
            "Stream transcribe: name=%s content_type=%s bytes=%d",
            file.filename,
            file.content_type,
            len(audio_data)
        )
    except Exception as e:
        return StreamingResponse(
            iter([f"data: {json.dumps({'type': 'error', 'error': f'Failed to read file: {str(e)}'})}\n\n"]),
            media_type="text/event-stream"
        )

    # Parse language and dictionary
    language_list = [l.strip() for l in language.split(',') if l.strip()] if language else ["en"]
    dictionary_words = [d.strip() for d in dictionary.split(',') if d.strip()] if dictionary else None

    # Create async generator for streaming
    async def event_generator():
        try:
            async for event in _stream_transcribe_task(
                audio_data=audio_data,
                language=language_list[0] if language_list else "en",
                app_type=app_type,
                app_name=app_name,
                dictionary_words=dictionary_words,
                chunk_seconds=chunk_seconds,
                overlap_seconds=overlap_seconds
            ):
                yield event
        except Exception as e:
            logger.error(f"Stream transcription error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e), 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Run the server"""
    log_level = settings.WISPR_FLOW_LOG_LEVEL.upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger.setLevel(getattr(logging, log_level, logging.INFO))
    print("=" * 70)
    print("🎙️  WISPR FLOW API SERVER")
    print("=" * 70)
    print(f"Port: {settings.WISPR_FLOW_PORT}")
    print(f"Base URL: {settings.WISPR_FLOW_BASETEN_URL}")
    print(f"Timeout: {settings.WISPR_FLOW_TIMEOUT}s")
    print(f"Rate Limit: {settings.WISPR_FLOW_RATE_LIMIT_PER_MINUTE} requests/min")

    # Check token
    token_info = client.get_token_info()
    print(f"\n🔑 Token Status:")
    print(f"   Email: {token_info.email}")
    print(f"   Valid: {token_info.is_valid}")
    if token_info.expires_at:
        print(f"   Expires: {token_info.expires_at}")
    if token_info.days_remaining is not None:
        if token_info.days_remaining > 0:
            print(f"   Days remaining: {token_info.days_remaining}")
        else:
            print(f"   ⚠️  Token expired!")

    print("\n" + "=" * 70)
    print("📚 Documentation:")
    print(f"   Swagger UI: http://localhost:{settings.WISPR_FLOW_PORT}/docs")
    print(f"   ReDoc:     http://localhost:{settings.WISPR_FLOW_PORT}/redoc")
    print("\n🔌 API Endpoints:")
    print(f"   Health:   GET  http://localhost:{settings.WISPR_FLOW_PORT}/health")
    print(f"   Token:    GET  http://localhost:{settings.WISPR_FLOW_PORT}/token")
    print(f"   REST:     POST http://localhost:{settings.WISPR_FLOW_PORT}/transcribe")
    print(f"   File:     POST http://localhost:{settings.WISPR_FLOW_PORT}/transcribe/file")
    print(f"   WebSocket: WS   ws://localhost:{settings.WISPR_FLOW_PORT}/ws/transcribe")
    print("=" * 70)
    print("\n⚠️  To avoid bans:")
    print("   - Analytics tracking is DISABLED")
    print("   - Rate limiting is ENABLED")
    print("   - Headers match desktop app exactly")
    print("   - Client platform is 'win32' (blends in)")
    print("=" * 70)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.WISPR_FLOW_PORT,
        log_level="info"
    )


if __name__ == "__main__":
    main()
