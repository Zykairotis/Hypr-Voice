"""Gemini Live Service - Multimodal AI Integration"""

# Screen service (legacy)
from .gemini_screen import (
    GeminiScreenService,
    analyze_screen_tool,
    describe_ui_tool,
    extract_screen_text_tool,
    identify_active_app_tool,
    GEMINI_TOOLS
)

# New Gemini Live API client and integration
from .gemini_client import (
    GeminiClient,
    GeminiConfig,
    DEFAULT_MODEL,
    LIVE_MODELS,
    MODEL_MAX_OUTPUT_TOKENS,
    MODEL_MAX_INPUT_TOKENS,
    WEBSOCKET_MODELS,
)

from .integration import (
    GeminiIntegration,
    GeminiChatSession,
)

__all__ = [
    # Screen service (legacy)
    'GeminiScreenService',
    'analyze_screen_tool',
    'describe_ui_tool',
    'extract_screen_text_tool',
    'identify_active_app_tool',
    'GEMINI_TOOLS',
    
    # Gemini Live client
    'GeminiClient',
    'GeminiConfig',
    'DEFAULT_MODEL',
    'LIVE_MODELS',
    'MODEL_MAX_OUTPUT_TOKENS',
    'MODEL_MAX_INPUT_TOKENS',
    'WEBSOCKET_MODELS',
    
    # Integration helpers
    'GeminiIntegration',
    'GeminiChatSession',
]
