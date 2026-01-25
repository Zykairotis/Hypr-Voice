"""
Direct Wispr Flow transcription without API server overhead.
============================================================

Uses the optimized in-memory processing from wisper-flow/transcribe.py
to bypass the HTTP API server (port 9095) and directly call Baseten.

Performance improvements:
- No HTTP overhead (saves 50-200ms per request)
- Audio preprocessing < 15ms (vs 500-2000ms with subprocess)
- Parallel chunk processing built-in
- Single process architecture

Usage:
    from hypr_voice.services.wispr_flow_direct import DirectWisprFlowClient
    
    client = DirectWisprFlowClient()
    result = await client.transcribe_file("audio.wav", language=["en"])
    print(result["text"])

Environment Variables:
    WISPR_FLOW_JWT_TOKEN: JWT authentication token
    WISPR_FLOW_BASETEN_API_KEY: Baseten API key  
    WISPR_FLOW_USER_UUID: User UUID
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any

import numpy as np
import soundfile as sf

# Setup logging
logger = logging.getLogger(__name__)

# Add wisper-flow to path for imports
WISPER_FLOW_PATH = Path(__file__).parents[2] / "wisper-flow"
if str(WISPER_FLOW_PATH) not in sys.path:
    sys.path.insert(0, str(WISPER_FLOW_PATH))

# Import from wisper-flow transcribe module
try:
    from transcribe import (
        transcribe_file_async,
        transcribe_file,
        TranscriptionContext,
        Config as WisprConfig,
    )
    WISPER_FLOW_AVAILABLE = True
    logger.info(f"Loaded wisper-flow from {WISPER_FLOW_PATH}")
except ImportError as e:
    logger.warning(f"wisper-flow not available: {e}")
    WISPER_FLOW_AVAILABLE = False
    TranscriptionContext = None
    WisprConfig = None


class DirectWisprFlowClient:
    """
    Direct transcription client - bypasses HTTP API server.
    
    Uses wisper-flow/transcribe.py for ultra-fast audio processing
    and direct Baseten API communication.
    """
    
    def __init__(
        self,
        jwt_token: Optional[str] = None,
        api_key: Optional[str] = None,
        user_uuid: Optional[str] = None,
    ):
        """
        Initialize the direct Wispr Flow client.
        
        Args:
            jwt_token: JWT authentication token (or from WISPR_FLOW_JWT_TOKEN env)
            api_key: Baseten API key (or from WISPR_FLOW_BASETEN_API_KEY env)
            user_uuid: User UUID (or from WISPR_FLOW_USER_UUID env)
        """
        if not WISPER_FLOW_AVAILABLE:
            raise RuntimeError(
                "wisper-flow module not available. "
                f"Ensure it exists at {WISPER_FLOW_PATH}"
            )
        
        # Load credentials from args or environment
        self.jwt_token = jwt_token or os.getenv("WISPR_FLOW_JWT_TOKEN", "")
        self.api_key = api_key or os.getenv("WISPR_FLOW_BASETEN_API_KEY", "")
        self.user_uuid = user_uuid or os.getenv("WISPR_FLOW_USER_UUID", "")
        
        # Configure the wisper-flow Config class
        if self.jwt_token:
            WisprConfig.JWT_TOKEN = self.jwt_token
        if self.api_key:
            WisprConfig.BASETEN_API_KEY = self.api_key
        if self.user_uuid:
            WisprConfig.USER_UUID = self.user_uuid
        
        # Validate credentials
        if not self.jwt_token or not self.api_key:
            logger.warning(
                "Missing Wispr Flow credentials. Set WISPR_FLOW_JWT_TOKEN "
                "and WISPR_FLOW_BASETEN_API_KEY environment variables."
            )
        
        logger.info("DirectWisprFlowClient initialized")
    
    async def transcribe_file(
        self,
        audio_path: str,
        language: Optional[List[str]] = None,
        app_type: str = "other",
        app_name: Optional[str] = None,
        bundle_id: Optional[str] = None,
        url: Optional[str] = None,
        dictionary_words: Optional[List[str]] = None,
        user_first_name: Optional[str] = None,
        user_last_name: Optional[str] = None,
        user_identifier: Optional[str] = None,
        before_text: str = "",
        after_text: str = "",
        selected_text: str = "",
        content_text: Optional[str] = None,
        variable_names: Optional[List[str]] = None,
        file_names: Optional[List[str]] = None,
        prev_asr_text: str = "",
    ) -> Dict[str, Any]:
        """
        Transcribe an audio file directly without HTTP overhead.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, FLAC, etc.)
            language: Language codes for transcription (default: ["en"])
            app_type: Application type (email, ai, code, messaging, other)
            app_name: Specific application name
            bundle_id: Application bundle ID
            url: Current URL (for browser context)
            dictionary_words: Custom vocabulary words for better recognition
            user_first_name: User's first name (helps spell names correctly)
            user_last_name: User's last name
            user_identifier: User identifier
            before_text: Text before cursor position
            after_text: Text after cursor position
            selected_text: Currently selected text
            content_text: Page/document content for context
            variable_names: Code variable names for context
            file_names: File names for context
            prev_asr_text: Previous transcription for continuity
        
        Returns:
            Dict with keys:
                - success: bool
                - text: str (transcribed text)
                - error: str or None
                - detected_language: str or None
                - metadata: dict with timing info
        """
        import time
        timings = {}
        total_start = time.perf_counter()
        
        if language is None:
            language = ["en"]
        
        # ⏱️ TIMING: Context building
        ctx_start = time.perf_counter()
        ctx = TranscriptionContext(
            language=language,
            app_type=app_type,
            app_name=app_name,
            bundle_id=bundle_id,
            url=url,
            dictionary_words=dictionary_words or [],
            user_first_name=user_first_name,
            user_last_name=user_last_name,
            user_identifier=user_identifier,
            before_text=before_text,
            after_text=after_text,
            selected_text=selected_text,
            content_text=content_text,
            variable_names=variable_names or [],
            file_names=file_names or [],
            prev_asr_text=prev_asr_text,
        )
        timings['context_build_ms'] = (time.perf_counter() - ctx_start) * 1000
        
        try:
            # ⏱️ TIMING: Get audio file info
            file_start = time.perf_counter()
            import os
            file_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            timings['file_check_ms'] = (time.perf_counter() - file_start) * 1000
            
            # ⏱️ TIMING: Call wisper-flow async transcription
            api_start = time.perf_counter()
            result = await transcribe_file_async(audio_path, ctx)
            timings['wispr_flow_api_ms'] = (time.perf_counter() - api_start) * 1000
            
            # ⏱️ TIMING: Extract text from result
            extract_start = time.perf_counter()
            text = (
                result.get("asr_text") or 
                result.get("llm_text") or 
                result.get("pipeline_text") or 
                result.get("text") or 
                ""
            )
            timings['text_extract_ms'] = (time.perf_counter() - extract_start) * 1000
            
            # Total time
            timings['total_ms'] = (time.perf_counter() - total_start) * 1000
            
            # Log detailed timings
            logger.info(
                f"⏱️ DIRECT TRANSCRIPTION TIMING:\n"
                f"   📁 File: {audio_path} ({file_size/1024:.1f}KB)\n"
                f"   🔧 Context build:    {timings['context_build_ms']:6.1f}ms\n"
                f"   📂 File check:       {timings['file_check_ms']:6.1f}ms\n"
                f"   🌐 Wispr Flow API:   {timings['wispr_flow_api_ms']:6.1f}ms\n"
                f"      └─ Preprocess:    {result.get('preprocess_ms', 0):6.1f}ms\n"
                f"      └─ Network:       {result.get('network_ms', 0):6.1f}ms\n"
                f"      └─ Chunks:        {result.get('chunk_count', 1)}\n"
                f"   📝 Text extract:     {timings['text_extract_ms']:6.1f}ms\n"
                f"   ─────────────────────────────\n"
                f"   ⏱️ TOTAL:            {timings['total_ms']:6.1f}ms"
            )
            
            # Check for errors
            if result.get("status") == "error":
                return {
                    "success": False,
                    "text": None,
                    "error": result.get("error_message", "Unknown error"),
                    "detected_language": result.get("detected_language"),
                    "metadata": {
                        "preprocess_ms": result.get("preprocess_ms", 0),
                        "network_ms": result.get("network_ms", 0),
                        "chunk_count": result.get("chunk_count", 1),
                        **timings,
                    }
                }
            
            return {
                "success": True,
                "text": text,
                "error": None,
                "detected_language": result.get("detected_language"),
                "metadata": {
                    "preprocess_ms": result.get("preprocess_ms", 0),
                    "network_ms": result.get("network_ms", 0),
                    "chunk_count": result.get("chunk_count", 1),
                    **timings,
                }
            }
            
        except Exception as e:
            timings['total_ms'] = (time.perf_counter() - total_start) * 1000
            logger.error(f"Direct transcription failed after {timings['total_ms']:.1f}ms: {e}")
            return {
                "success": False,
                "text": None,
                "error": f"Direct transcription failed: {str(e)}",
                "detected_language": None,
                "metadata": timings
            }
    
    def transcribe_file_sync(
        self,
        audio_path: str,
        language: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Synchronous version of transcribe_file.
        
        Useful when called from non-async context.
        """
        if language is None:
            language = ["en"]
        
        # Build context
        ctx = TranscriptionContext(
            language=language,
            app_type=kwargs.get("app_type", "other"),
            app_name=kwargs.get("app_name"),
            dictionary_words=kwargs.get("dictionary_words", []),
            user_first_name=kwargs.get("user_first_name"),
            user_last_name=kwargs.get("user_last_name"),
            before_text=kwargs.get("before_text", ""),
            after_text=kwargs.get("after_text", ""),
            selected_text=kwargs.get("selected_text", ""),
            content_text=kwargs.get("content_text"),
            prev_asr_text=kwargs.get("prev_asr_text", ""),
        )
        
        try:
            # Use sync version from wisper-flow
            result = transcribe_file(audio_path, ctx=ctx)
            
            text = (
                result.get("asr_text") or 
                result.get("llm_text") or 
                result.get("pipeline_text") or 
                ""
            )
            
            if result.get("status") == "error":
                return {
                    "success": False,
                    "text": None,
                    "error": result.get("error_message", "Unknown error"),
                    "detected_language": result.get("detected_language"),
                }
            
            return {
                "success": True,
                "text": text,
                "error": None,
                "detected_language": result.get("detected_language"),
            }
            
        except Exception as e:
            logger.error(f"Sync transcription failed: {e}")
            return {
                "success": False,
                "text": None,
                "error": str(e),
                "detected_language": None,
            }
    
    async def transcribe_audio_data(
        self,
        audio_data: np.ndarray,
        sample_rate: int = 16000,
        language: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe numpy audio data directly.
        
        Args:
            audio_data: Numpy array of audio samples (mono, float32 or int16)
            sample_rate: Sample rate of audio (will resample to 16kHz if needed)
            language: Language codes
            **kwargs: Additional transcription parameters
        
        Returns:
            Dict with transcription result
        """
        import tempfile
        
        # Write audio to temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
            sf.write(tmp.name, audio_data, sample_rate)
            tmp_path = tmp.name
        
        try:
            result = await self.transcribe_file(
                audio_path=tmp_path,
                language=language,
                **kwargs
            )
            return result
        finally:
            # Clean up temp file
            try:
                os.unlink(tmp_path)
            except Exception:
                pass


# Singleton instance for convenience
_direct_client: Optional[DirectWisprFlowClient] = None


def get_direct_client() -> DirectWisprFlowClient:
    """Get or create singleton DirectWisprFlowClient instance."""
    global _direct_client
    if _direct_client is None:
        _direct_client = DirectWisprFlowClient()
    return _direct_client


# Quick test
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python wispr_flow_direct.py <audio_file>")
        sys.exit(1)
    
    async def main():
        client = DirectWisprFlowClient()
        result = await client.transcribe_file(sys.argv[1])
        
        if result["success"]:
            print(f"\n✅ Transcription successful!")
            print(f"Text: {result['text']}")
            if result.get("metadata"):
                meta = result["metadata"]
                print(f"\nPerformance:")
                print(f"  Preprocessing: {meta.get('preprocess_ms', 0):.0f}ms")
                print(f"  Network/API:   {meta.get('network_ms', 0):.0f}ms")
                print(f"  Chunks:        {meta.get('chunk_count', 1)}")
        else:
            print(f"\n❌ Transcription failed: {result['error']}")
    
    asyncio.run(main())
