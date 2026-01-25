"""
Claude SDK Compatibility Layer
Centralizes imports for the official Claude Agent SDK and the mock implementation.
"""

import logging

logger = logging.getLogger(__name__)

CLAUDE_SDK_AVAILABLE = False
CLAUDE_SDK_MOCK = False

# Initialize symbols as None
ClaudeSDKClient = None
ClaudeAgentOptions = None
AgentDefinition = None
tool = None
sdk_query = None
AssistantMessage = None
TextBlock = None
ResultMessage = None
UserMessage = None
SystemMessage = None
ThinkingBlock = None
ToolUseBlock = None
ToolResultBlock = None
PermissionResultAllow = None
PermissionResultDeny = None
create_sdk_mcp_server = None

try:
    # Attempt to import from official SDK
    from claude_agent_sdk import (
        ClaudeSDKClient,
        ClaudeAgentOptions,
        tool,
        AssistantMessage,
        TextBlock,
        ResultMessage,
        UserMessage,
        SystemMessage,
        ThinkingBlock,
        ToolUseBlock,
        ToolResultBlock
    )

    try:
        from claude_agent_sdk import AgentDefinition
    except (ImportError, AttributeError):
        pass

    try:
        from claude_agent_sdk import query as sdk_query
    except (ImportError, AttributeError):
        pass

    # Permission results might be in a different submodule or not available in older versions
    try:
        from claude_agent_sdk import PermissionResultAllow, PermissionResultDeny
    except (ImportError, AttributeError):
        # Provide robust dummy classes if not available to avoid AttributeErrors
        class PermissionResultAllow:
            def __init__(self, **kwargs): pass
        class PermissionResultDeny:
            def __init__(self, **kwargs): pass

    try:
        from claude_agent_sdk import create_sdk_mcp_server
    except (ImportError, AttributeError):
        pass

    CLAUDE_SDK_AVAILABLE = True
    CLAUDE_SDK_MOCK = False
    logger.info("Official Claude Agent SDK loaded")

except ImportError:
    # Fall back to mock implementation
    try:
        from hypr_voice.services.claude_agent_sdk_mock import (
            ClaudeSDKClient,
            ClaudeAgentOptions,
            tool,
            AssistantMessage,
            TextBlock,
            ResultMessage,
            PermissionResultAllow,
            PermissionResultDeny,
            create_sdk_mcp_server,
            UserMessage,
            SystemMessage,
            ThinkingBlock,
            ToolUseBlock,
            ToolResultBlock
        )
        # Mock implementations for missing SDK symbols
        try:
            from hypr_voice.services.claude_agent_sdk_mock import query as sdk_query
        except ImportError:
            sdk_query = None

        try:
            from hypr_voice.services.claude_agent_sdk_mock import AgentDefinition
        except ImportError:
            AgentDefinition = None

        CLAUDE_SDK_AVAILABLE = True
        CLAUDE_SDK_MOCK = True
        logger.warning("Using mock Claude SDK implementation")
    except ImportError:
        CLAUDE_SDK_AVAILABLE = False
        CLAUDE_SDK_MOCK = False
        logger.error("Neither Claude SDK nor mock implementation available")

def is_sdk_available() -> bool:
    """Check if any SDK implementation is available"""
    return CLAUDE_SDK_AVAILABLE

def is_mock() -> bool:
    """Check if the mock implementation is being used"""
    return CLAUDE_SDK_MOCK
