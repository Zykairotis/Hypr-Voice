"""
LogGurl - Centralized logging for Hypr-Voice

All components log to a single file with consistent formatting.
Use the viewer script: scripts/loggurl.sh
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional
import json

# Single log file location
LOG_DIR = Path(os.getenv("HYPR_VOICE_LOG_DIR", "/tmp/hypr-voice"))
LOG_FILE = LOG_DIR / "hypr-voice.log"
LOG_LEVEL = os.getenv("HYPR_VOICE_LOG_LEVEL", "INFO").upper()

# Ensure log directory exists
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Component colors for terminal output (ANSI codes)
COLORS = {
    "agent": "\033[36m",      # Cyan
    "orchestrator": "\033[35m", # Magenta
    "voice": "\033[33m",      # Yellow
    "tts": "\033[32m",        # Green
    "whisper": "\033[34m",    # Blue
    "router": "\033[95m",     # Light magenta
    "llm": "\033[93m",        # Light yellow
    "server": "\033[96m",     # Light cyan
    "default": "\033[37m",    # White
    "reset": "\033[0m",
    "bold": "\033[1m",
    "dim": "\033[2m",
}

# Log level colors
LEVEL_COLORS = {
    "DEBUG": "\033[2m",       # Dim
    "INFO": "\033[0m",        # Normal
    "WARNING": "\033[33m",    # Yellow
    "ERROR": "\033[31m",      # Red
    "CRITICAL": "\033[1;31m", # Bold red
}


class LogGurlFormatter(logging.Formatter):
    """Custom formatter with component tags and colors."""
    
    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors
    
    def format(self, record: logging.LogRecord) -> str:
        # Extract component from logger name or record
        component = getattr(record, 'component', None)
        if not component:
            # Try to extract from logger name (e.g., "hypr_voice.orchestrator")
            parts = record.name.split('.')
            if len(parts) > 1:
                component = parts[-1][:12]  # Last part, max 12 chars
            else:
                component = "main"
        
        # Timestamp
        ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S.%f")[:-3]
        
        # Build message
        if self.use_colors:
            color = COLORS.get(component.lower(), COLORS["default"])
            level_color = LEVEL_COLORS.get(record.levelname, "")
            reset = COLORS["reset"]
            
            # Format: [HH:MM:SS.mmm] [COMPONENT] [LEVEL] message
            return (
                f"{COLORS['dim']}{ts}{reset} "
                f"{color}[{component:>12}]{reset} "
                f"{level_color}[{record.levelname:>5}]{reset} "
                f"{record.getMessage()}"
            )
        else:
            # Plain format for file
            return f"{ts} [{component:>12}] [{record.levelname:>5}] {record.getMessage()}"


class LogGurl:
    """
    Centralized logger for Hypr-Voice components.
    
    Usage:
        from hypr_voice.core.loggurl import LogGurl
        log = LogGurl("orchestrator")
        log.info("Processing query")
        log.routing("general-conversation", 0.85, "casual greeting")
    """
    
    _file_handler: Optional[logging.FileHandler] = None
    _initialized: bool = False
    
    @classmethod
    def _ensure_initialized(cls):
        """Initialize the shared file handler once."""
        if cls._initialized:
            return
        
        # Create file handler (shared across all LogGurl instances)
        cls._file_handler = logging.FileHandler(LOG_FILE, mode='a', encoding='utf-8')
        cls._file_handler.setFormatter(LogGurlFormatter(use_colors=False))
        cls._file_handler.setLevel(logging.DEBUG)  # File gets everything
        
        cls._initialized = True
    
    def __init__(self, component: str):
        """
        Create a logger for a component.
        
        Args:
            component: Component name (e.g., "orchestrator", "tts", "whisper")
        """
        self.component = component
        self._ensure_initialized()
        
        # Create logger
        self.logger = logging.getLogger(f"loggurl.{component}")
        self.logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
        
        # Add file handler if not already added
        if self._file_handler not in self.logger.handlers:
            self.logger.addHandler(self._file_handler)
        
        # Add stderr handler for terminal output (with colors)
        if not any(isinstance(h, logging.StreamHandler) and h.stream == sys.stderr 
                   for h in self.logger.handlers):
            stderr_handler = logging.StreamHandler(sys.stderr)
            stderr_handler.setFormatter(LogGurlFormatter(use_colors=True))
            stderr_handler.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
            self.logger.addHandler(stderr_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def _log(self, level: int, msg: str, **kwargs):
        """Log with component context."""
        extra = {'component': self.component}
        self.logger.log(level, msg, extra=extra)
    
    # Standard log levels
    def debug(self, msg: str): self._log(logging.DEBUG, msg)
    def info(self, msg: str): self._log(logging.INFO, msg)
    def warning(self, msg: str): self._log(logging.WARNING, msg)
    def error(self, msg: str): self._log(logging.ERROR, msg)
    def critical(self, msg: str): self._log(logging.CRITICAL, msg)
    
    # Semantic logging methods for common events
    def start(self, msg: str = ""):
        """Log start of an operation."""
        self._log(logging.INFO, f"━━━ START ━━━ {msg}")
    
    def complete(self, msg: str = "", duration_ms: Optional[float] = None):
        """Log completion of an operation."""
        dur = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        self._log(logging.INFO, f"━━━ COMPLETE{dur} ━━━ {msg}")
    
    def routing(self, agent: str, confidence: float, reason: str = ""):
        """Log a routing decision."""
        self._log(logging.INFO, f"ROUTE → {agent} (conf={confidence:.2f}) {reason[:80]}")
    
    def llm_start(self, model: str, prompt_preview: str = ""):
        """Log LLM call start."""
        self._log(logging.INFO, f"LLM → {model} | {prompt_preview[:60]}...")
    
    def llm_complete(self, chars: int, duration_ms: float):
        """Log LLM call completion."""
        self._log(logging.INFO, f"LLM ← {chars} chars in {duration_ms:.0f}ms")
    
    def tts_start(self, provider: str, text_len: int):
        """Log TTS start."""
        self._log(logging.INFO, f"TTS → {provider} | {text_len} chars")
    
    def tts_complete(self, duration_ms: float, audio_file: Optional[str] = None):
        """Log TTS completion."""
        file_info = f" → {audio_file}" if audio_file else " (streamed)"
        self._log(logging.INFO, f"TTS ← {duration_ms:.0f}ms{file_info}")
    
    def transcription(self, text: str, duration_ms: Optional[float] = None):
        """Log transcription result."""
        dur = f" ({duration_ms:.0f}ms)" if duration_ms else ""
        self._log(logging.INFO, f"STT{dur}: \"{text[:100]}{'...' if len(text) > 100 else ''}\"")
    
    def request(self, endpoint: str, method: str = "POST"):
        """Log incoming request."""
        self._log(logging.INFO, f"REQ {method} {endpoint}")
    
    def response(self, status: int, duration_ms: float):
        """Log response."""
        self._log(logging.INFO, f"RES {status} ({duration_ms:.0f}ms)")
    
    def event(self, event_type: str, data: dict = None):
        """Log a generic event with optional data."""
        data_str = f" | {json.dumps(data)[:100]}" if data else ""
        self._log(logging.INFO, f"EVENT: {event_type}{data_str}")


# Convenience function to get a logger
def get_logger(component: str) -> LogGurl:
    """Get a LogGurl instance for a component."""
    return LogGurl(component)


# Pre-configured loggers for common components
agent_log = LogGurl("agent")
orchestrator_log = LogGurl("orchestrator")
voice_log = LogGurl("voice")
tts_log = LogGurl("tts")
whisper_log = LogGurl("whisper")
router_log = LogGurl("router")
llm_log = LogGurl("llm")
server_log = LogGurl("server")
