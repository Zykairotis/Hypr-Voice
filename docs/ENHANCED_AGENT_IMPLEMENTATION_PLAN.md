# Enhanced Agent Implementation Plan
**Context-Aware AI Assistant with Claude Agent SDK**

## Executive Summary

Create a dedicated Claude Agent SDK-based backend for the enhanced agent mode (Right Ctrl + F9) that provides fast, context-aware AI responses with proper tool access and conversation memory.

---

## 1. Current State Analysis

### What We Have

#### Existing Infrastructure
1. **Basic Orchestrator** (`src/hypr_voice/orchestrator/orchestrator.py`)
   - Uses direct Anthropic API (fallback mode)
   - Routes queries to specialized agent types
   - No Claude SDK integration currently active
   - Fast but limited (3s response time)

2. **Voice Orchestrator** (`src/hypr_voice/orchestrator/voice_orchestrator.py`)
   - Handles TTS/STT integration
   - Uses basic orchestrator under the hood
   - Provides `/voice/process` endpoint

3. **Enhanced Agent Script** (`scripts/hypr-agent-enhanced.sh`)
   - Gathers rich context (active window, clipboard)
   - Currently sends to `/voice/process` endpoint
   - Context is included in request but not fully utilized

### What's Missing

1. **No Claude Agent SDK Backend**
   - Current orchestrator has `CLAUDE_SDK_AVAILABLE = True` but `enable_subagents = False`
   - SDK query path exists but is bypassed
   - No custom tools registered

2. **Context Not Fully Utilized**
   - Context is gathered but only passed as JSON in request
   - No specialized context-aware prompts
   - No Hyprland tools integration

3. **No Dedicated Enhanced Agent Type**
   - Using generic "general-conversation" agent
   - No specialized prompts for context-aware assistance
   - Missing Hyprland-specific capabilities

---

## 2. Solution Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────────┐
│  Right Ctrl + F9 (Enhanced Agent Mode)                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  hypr-agent-enhanced.sh                                          │
│  • Gather context (window, clipboard, workspace)                │
│  • Record & transcribe audio                                    │
│  • Call enhanced API endpoint                                   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  NEW: /voice/process/enhanced (FastAPI endpoint)                │
│  • Validates enhanced context                                   │
│  • Routes to EnhancedContextAgent                               │
│  • Streams response with TTS                                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  NEW: EnhancedContextAgent (Claude SDK Agent)                   │
│  • Built with ClaudeSDKClient                                   │
│  • Custom tools: Hyprland context tools                         │
│  • Specialized system prompt                                    │
│  • Session persistence for follow-ups                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Claude Agent SDK with Custom Tools                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Built-in Tools:                                           │  │
│  │ • Read, Write, Edit (file operations)                    │  │
│  │ • Bash (system commands)                                 │  │
│  │ • WebSearch, WebFetch (research)                         │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Custom MCP Tools (NEW):                                  │  │
│  │ • get_hyprland_active_client                             │  │
│  │ • get_hyprland_all_clients                               │  │
│  │ • switch_to_window                                       │  │
│  │ • screenshot_active_window                               │  │
│  │ • get_clipboard_content                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Key Components

#### Component 1: Enhanced Context Agent Class
**File**: `src/hypr_voice/agents/enhanced_context_agent.py` (NEW)

**Purpose**: Dedicated Claude SDK agent for context-aware assistance

**Features**:
- Uses `ClaudeSDKClient` for full SDK capabilities
- Custom Hyprland tools integration
- Specialized system prompt for context awareness
- Session management for conversation continuity
- Streaming support for real-time TTS

#### Component 2: Enhanced Voice Endpoint
**File**: `src/hypr_voice/server.py` (MODIFY)

**Purpose**: New API endpoint specifically for enhanced mode

**Endpoint**: `POST /voice/process/enhanced`

**Features**:
- Validates enhanced context structure
- Routes to EnhancedContextAgent
- Streams response with TTS
- Returns conversation ID for follow-ups

#### Component 3: Hyprland MCP Tools
**File**: `src/hypr_voice/tools/hyprland_mcp_tools.py` (NEW)

**Purpose**: Claude SDK-compatible MCP tools for Hyprland

**Tools**:
- Window management (focus, switch, list)
- Screenshot capture
- Clipboard operations
- Workspace queries

#### Component 4: Enhanced Script Updates
**File**: `scripts/hypr-agent-enhanced.sh` (MODIFY)

**Purpose**: Use new enhanced endpoint

**Changes**:
- Call `/voice/process/enhanced` instead of `/voice/process`
- Enhanced request format with structured context
- Better error handling

---

## 3. Implementation Plan

### Phase 1: Create Hyprland MCP Tools (1-2 hours)

**File**: `src/hypr_voice/tools/hyprland_mcp_tools.py`

**Tasks**:
1. Create SDK-compatible tool wrappers
2. Import existing Hyprland functions
3. Create MCP server with tools
4. Test tools individually

**Code Structure**:
```python
from claude_agent_sdk import tool, create_sdk_mcp_server
from hypr_voice.services.tools.hyprland_ss_ctx import (
    get_hyprland_active_client,
    get_hyprland_all_clients,
)

@tool(
    "get_active_window_context",
    "Get current active window information including class, title, and workspace",
    {}
)
async def get_active_window_context(args):
    result = await get_hyprland_active_client({})
    return result

@tool(
    "get_clipboard",
    "Get current clipboard content",
    {}
)
async def get_clipboard(args):
    # Implement clipboard reading
    pass

hyprland_tools_server = create_sdk_mcp_server(
    name="hyprland-context",
    version="1.0.0",
    tools=[get_active_window_context, get_clipboard]
)
```

**Testing**:
```bash
python -c "from hypr_voice.tools.hyprland_mcp_tools import test_tools; test_tools()"
```

---

### Phase 2: Create Enhanced Context Agent (2-3 hours)

**File**: `src/hypr_voice/agents/enhanced_context_agent.py`

**Tasks**:
1. Create `EnhancedContextAgent` class
2. Implement Claude SDK client initialization
3. Register Hyprland MCP tools
4. Create specialized system prompt
5. Implement session management
6. Add streaming support

**Code Structure**:
```python
import asyncio
from typing import AsyncIterator, Optional
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
from ..tools.hyprland_mcp_tools import hyprland_tools_server

class EnhancedContextAgent:
    """Context-aware AI agent using Claude Agent SDK."""

    def __init__(self):
        self.sessions = {}
        self.tools_server = hyprland_tools_server

    async def process(
        self,
        query: str,
        context: dict,
        conversation_id: Optional[str] = None
    ) -> AsyncIterator[dict]:
        """Process query with full context awareness."""

        # Build enhanced system prompt
        system_prompt = self._build_system_prompt(context)

        # Configure Claude SDK
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"hyprland": self.tools_server},
            allowed_tools=[
                "Read", "Write", "Edit",
                "Bash", "WebSearch", "WebFetch",
                "mcp__hyprland__get_active_window_context",
                "mcp__hyprland__get_clipboard"
            ],
            permission_mode="bypassPermissions",
            max_turns=5,
            resume=conversation_id  # Resume existing conversation
        )

        # Process with SDK
        async with ClaudeSDKClient(options=options) as client:
            await client.query(query)

            async for message in client.receive_response():
                # Stream responses
                yield self._format_message(message)

    def _build_system_prompt(self, context: dict) -> str:
        """Build context-aware system prompt."""
        window = context.get("window", {})
        clipboard = context.get("clipboard", "")

        return f"""You are an intelligent context-aware assistant with access to the user's current environment.

CURRENT CONTEXT:
- Active Application: {window.get('class', 'unknown')}
- Window Title: {window.get('title', 'unknown')}
- Workspace: {window.get('workspace', {}).get('id', 'unknown')}
- Clipboard: {clipboard[:200] if clipboard else 'empty'}

CAPABILITIES:
You have access to:
1. Hyprland window management (switch windows, get info)
2. File operations (read, write, edit)
3. System commands (bash)
4. Web research (search, fetch)
5. Screenshot capabilities
6. Clipboard access

INSTRUCTIONS:
- Use the context to provide relevant, application-specific assistance
- When the user asks about "this window" or "current app", use the context above
- If clipboard contains relevant data, reference it naturally
- Be concise and helpful
- Prefer showing over telling (use tools when appropriate)

RESPONSE STYLE:
- Keep responses conversational and natural for voice output
- Avoid bullet points in voice responses
- Speak in complete, flowing sentences
- Be friendly and helpful"""
```

**Testing**:
```python
# Test basic processing
async def test():
    agent = EnhancedContextAgent()
    context = {
        "window": {"class": "Code", "title": "main.py"},
        "clipboard": "def hello(): pass"
    }

    async for chunk in agent.process("What's in my clipboard?", context):
        print(chunk)

asyncio.run(test())
```

---

### Phase 3: Create Enhanced API Endpoint (1 hour)

**File**: `src/hypr_voice/server.py` (MODIFY)

**Tasks**:
1. Import EnhancedContextAgent
2. Create `/voice/process/enhanced` endpoint
3. Validate context structure
4. Integrate with TTS
5. Return conversation ID

**Code Addition**:
```python
from .agents.enhanced_context_agent import EnhancedContextAgent

# Global instance
enhanced_agent: Optional[EnhancedContextAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global enhanced_agent
    # ... existing code ...

    # Initialize enhanced agent
    enhanced_agent = EnhancedContextAgent()
    logger.info("Enhanced Context Agent initialized")

    yield

    # ... shutdown code ...

class EnhancedProcessRequest(BaseModel):
    text: str
    context: dict  # {window: {...}, clipboard: str, timestamp: str}
    conversation_id: Optional[str] = None
    speak_response: bool = True

@app.post("/voice/process/enhanced")
async def voice_process_enhanced(request: EnhancedProcessRequest):
    """
    Process text with enhanced context awareness using Claude Agent SDK.

    This endpoint provides:
    - Full context awareness (active window, clipboard, etc.)
    - Claude SDK with custom Hyprland tools
    - Session persistence for follow-ups
    - TTS spoken responses
    """
    if not enhanced_agent:
        raise HTTPException(status_code=503, detail="Enhanced agent not initialized")

    if not voice_orchestrator:
        raise HTTPException(status_code=503, detail="Voice orchestrator not initialized")

    try:
        # Process with enhanced agent
        response_text = ""
        conversation_id = request.conversation_id

        async for chunk in enhanced_agent.process(
            request.text,
            request.context,
            conversation_id
        ):
            if chunk.get("type") == "text":
                response_text += chunk.get("content", "")
            elif chunk.get("type") == "conversation_id":
                conversation_id = chunk.get("id")

        # Speak response if requested
        audio_file = None
        if request.speak_response and response_text:
            tts_result = await voice_orchestrator.speak(response_text)
            if tts_result.get("success"):
                audio_file = tts_result.get("audio_file")

        return {
            "success": True,
            "response_text": response_text,
            "conversation_id": conversation_id,
            "audio_file": audio_file,
            "context_used": True,
            "agent_type": "enhanced-context"
        }

    except Exception as e:
        logger.error(f"Enhanced processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Phase 4: Update Enhanced Script (30 minutes)

**File**: `scripts/hypr-agent-enhanced.sh` (MODIFY)

**Tasks**:
1. Change endpoint to `/voice/process/enhanced`
2. Update request payload format
3. Add conversation ID persistence
4. Improve error handling

**Changes**:
```bash
# Send enhanced query to orchestrator
send_enhanced_query() {
    local transcription="$1"
    local context_json="$2"

    # ... existing validation ...

    # Build enhanced payload with structured context
    local payload
    if [[ -n "$conv_id" ]]; then
        payload=$(jq -nc \
            --arg text "$transcription" \
            --arg conv "$conv_id" \
            --argjson ctx "$context_json" \
            '{
                text: $text,
                conversation_id: $conv,
                context: $ctx,
                speak_response: true
            }')
    else
        payload=$(jq -nc \
            --arg text "$transcription" \
            --argjson ctx "$context_json" \
            '{
                text: $text,
                context: $ctx,
                speak_response: true
            }')
    fi

    # Call ENHANCED endpoint
    response=$(curl -s -X POST "http://localhost:$ORCHESTRATOR_PORT/voice/process/enhanced" \
        -H "Content-Type: application/json" \
        -d "$payload" \
        --max-time "$AGENT_TIMEOUT" 2>&1)

    # ... rest of handling ...
}
```

---

### Phase 5: Testing & Validation (2 hours)

#### Unit Tests
**File**: `tests/test_enhanced_agent.py` (NEW)

```python
import pytest
import asyncio
from hypr_voice.agents.enhanced_context_agent import EnhancedContextAgent

@pytest.mark.asyncio
async def test_basic_query():
    agent = EnhancedContextAgent()
    context = {
        "window": {"class": "kitty", "title": "bash"},
        "clipboard": ""
    }

    chunks = []
    async for chunk in agent.process("What time is it?", context):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert any(c.get("type") == "text" for c in chunks)

@pytest.mark.asyncio
async def test_context_awareness():
    agent = EnhancedContextAgent()
    context = {
        "window": {"class": "Code", "title": "main.py - VSCode"},
        "clipboard": "def hello():\n    print('world')"
    }

    async for chunk in agent.process("What's in my clipboard?", context):
        if chunk.get("type") == "text":
            text = chunk.get("content", "")
            assert "hello" in text.lower() or "function" in text.lower()

@pytest.mark.asyncio
async def test_conversation_continuity():
    agent = EnhancedContextAgent()
    context = {"window": {}, "clipboard": ""}

    # First query
    conv_id = None
    async for chunk in agent.process("What's 2+2?", context):
        if chunk.get("type") == "conversation_id":
            conv_id = chunk.get("id")

    assert conv_id is not None

    # Follow-up query
    async for chunk in agent.process("Multiply that by 3", context, conv_id):
        if chunk.get("type") == "text":
            assert "12" in chunk.get("content", "")
```

#### Integration Tests
```bash
# Test endpoint
curl -X POST http://localhost:9093/voice/process/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What application am I using?",
    "context": {
      "window": {"class": "brave", "title": "GitHub"},
      "clipboard": ""
    },
    "speak_response": true
  }'

# Test enhanced script
/home/mewtwo/Zykairotis/Hypr-Voice/scripts/hypr-agent-enhanced.sh status
```

#### Manual Testing
1. Open VSCode
2. Press Right Ctrl + F9
3. Say: "What file am I editing?"
4. Verify AI knows the window context

---

## 4. Implementation Checklist

### Prerequisites
- [ ] Claude Agent SDK installed: `pip install claude-agent-sdk`
- [ ] Claude Code CLI available: `claude --version`
- [ ] Anthropic API key configured
- [ ] Orchestrator running on port 9093
- [ ] Whisper server running on port 9099

### Phase 1: Hyprland MCP Tools
- [ ] Create `src/hypr_voice/tools/hyprland_mcp_tools.py`
- [ ] Implement tool wrappers
- [ ] Create MCP server
- [ ] Test tools individually
- [ ] Verify tool discovery

### Phase 2: Enhanced Context Agent
- [ ] Create `src/hypr_voice/agents/enhanced_context_agent.py`
- [ ] Implement `EnhancedContextAgent` class
- [ ] Configure Claude SDK options
- [ ] Create context-aware system prompt
- [ ] Implement streaming support
- [ ] Test basic queries

### Phase 3: Enhanced API Endpoint
- [ ] Import `EnhancedContextAgent` in `server.py`
- [ ] Create global instance
- [ ] Implement `/voice/process/enhanced` endpoint
- [ ] Add request validation
- [ ] Integrate with TTS
- [ ] Test endpoint with curl

### Phase 4: Update Enhanced Script
- [ ] Update endpoint URL
- [ ] Modify request payload format
- [ ] Add conversation ID handling
- [ ] Improve logging
- [ ] Test script manually

### Phase 5: Testing
- [ ] Create unit tests
- [ ] Run integration tests
- [ ] Manual testing with real scenarios
- [ ] Performance testing
- [ ] Error handling verification

### Phase 6: Documentation
- [ ] Update API documentation
- [ ] Add usage examples
- [ ] Create troubleshooting guide
- [ ] Update README

---

## 5. Performance Targets

### Response Time Breakdown
| Stage | Target | Notes |
|-------|--------|-------|
| Context gathering | < 100ms | Hyprland query + clipboard read |
| Transcription | < 2s | Whisper server processing |
| LLM first token | < 500ms | Claude SDK with streaming |
| TTS generation | < 1s | Deepgram WebSocket |
| Total end-to-end | < 4s | From key release to audio start |

### Optimization Strategies
1. **Parallel Processing**: Gather context while recording
2. **Streaming**: Start TTS as soon as first tokens arrive
3. **Caching**: Cache Hyprland client data (100ms TTL)
4. **Model Selection**: Use Haiku for simple queries, Sonnet for complex
5. **Token Limits**: Limit to 1024 tokens for voice responses

---

## 6. Error Handling

### Fallback Strategy
```
1. Try Enhanced Agent with Claude SDK
   ↓ (if fails)
2. Try Basic Orchestrator (direct API)
   ↓ (if fails)
3. Return error + copy transcription to clipboard
```

### Error Scenarios
| Error | Handling | User Experience |
|-------|----------|-----------------|
| Claude SDK timeout | Fallback to direct API | Slightly slower response |
| Hyprland tool error | Continue without context | Generic response |
| TTS failure | Return text only | No voice output |
| Whisper timeout | Retry once | 2s delay |
| No orchestrator | Clipboard fallback | Text in clipboard |

---

## 7. Configuration

### Environment Variables
```bash
# Enhanced Agent Configuration
export ENHANCED_AGENT_MODEL="claude-sonnet-4-5"  # or claude-haiku-4
export ENHANCED_AGENT_MAX_TURNS=5
export ENHANCED_AGENT_TIMEOUT=300  # seconds
export ENHANCED_AGENT_TOOLS="hyprland,websearch,bash"

# Claude SDK Configuration
export CLAUDE_SDK_PERMISSION_MODE="bypassPermissions"
export CLAUDE_SDK_WORKING_DIR="/home/mewtwo/Zykairotis/Hypr-Voice"
```

### Feature Flags
```python
# In server.py
config = {
    "enable_enhanced_agent": True,
    "enable_hyprland_tools": True,
    "enable_streaming_tts": True,
    "use_haiku_for_simple_queries": True,
}
```

---

## 8. Future Enhancements

### Phase 2 Features (Post-MVP)
1. **Screen OCR**: Extract text from screenshots
2. **Smart Caching**: Cache common responses
3. **Multi-Window Context**: Track multiple windows
4. **Code Awareness**: Detect language, provide syntax help
5. **Project Detection**: Recognize current project context
6. **Custom Vocabulary**: Learn user-specific terms

### Advanced Capabilities
1. **Proactive Suggestions**: Offer help based on context
2. **Tool Learning**: Improve tool selection over time
3. **Multi-Modal Input**: Screenshot + voice
4. **Agent Swarms**: Multiple agents collaborating
5. **Memory Persistence**: Long-term conversation memory

---

## 9. Success Metrics

### Key Performance Indicators
- **Response Time**: < 4s end-to-end (95th percentile)
- **Context Accuracy**: > 95% correct window detection
- **Tool Usage**: > 50% of queries use context tools
- **User Satisfaction**: Subjective improvement over basic mode
- **Error Rate**: < 5% failures

### Monitoring
```python
# Metrics to track
metrics = {
    "total_requests": 0,
    "avg_response_time": 0,
    "context_tools_used": 0,
    "fallback_count": 0,
    "error_count": 0,
    "conversation_continuity": 0  # % with follow-ups
}
```

---

## 10. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Claude SDK bugs | Medium | High | Fallback to direct API |
| Context gathering slow | Low | Medium | Async + caching |
| Tool permission issues | Low | Low | Bypass permissions mode |
| Memory leaks | Low | Medium | Session cleanup + limits |
| API rate limits | Low | High | Request queuing |

---

## 11. Next Steps

### Immediate Actions
1. ✅ Review this plan document
2. ⏳ Get user approval on approach
3. ⏳ Set up development environment
4. ⏳ Begin Phase 1 implementation

### Questions for User
1. Do you prefer Haiku or Sonnet as default model?
2. Should we limit conversation memory (e.g., last 5 exchanges)?
3. Do you want screenshot capability in Phase 1?
4. Any specific Hyprland tools you need prioritized?
5. Preferred error handling strategy?

---

## Appendix A: File Structure

```
Hypr-Voice/
├── src/hypr_voice/
│   ├── agents/
│   │   ├── __init__.py
│   │   └── enhanced_context_agent.py        # NEW - Phase 2
│   ├── tools/
│   │   ├── __init__.py
│   │   └── hyprland_mcp_tools.py            # NEW - Phase 1
│   ├── orchestrator/
│   │   └── orchestrator.py                  # EXISTING
│   ├── server.py                            # MODIFY - Phase 3
│   └── ...
├── scripts/
│   └── hypr-agent-enhanced.sh               # MODIFY - Phase 4
├── tests/
│   └── test_enhanced_agent.py               # NEW - Phase 5
└── docs/
    ├── ENHANCED_AGENT_MODE.md               # EXISTING
    └── ENHANCED_AGENT_IMPLEMENTATION_PLAN.md # THIS FILE
```

---

## Appendix B: API Contract

### Request Format
```json
{
  "text": "What file am I editing?",
  "context": {
    "window": {
      "class": "Code",
      "title": "main.py - VSCode",
      "workspace": {"id": 1, "name": "1"}
    },
    "clipboard": "def hello():\n    print('world')",
    "timestamp": "2025-01-02T12:34:56Z"
  },
  "conversation_id": "uuid-here-or-null",
  "speak_response": true
}
```

### Response Format
```json
{
  "success": true,
  "response_text": "You're editing main.py in VSCode. The file contains a hello function that prints 'world'.",
  "conversation_id": "new-uuid-here",
  "audio_file": "/tmp/response-uuid.wav",
  "context_used": true,
  "agent_type": "enhanced-context",
  "tools_used": ["mcp__hyprland__get_active_window_context"],
  "response_time_ms": 3421
}
```

---

**Document Version**: 1.0
**Last Updated**: 2025-01-02
**Status**: Ready for Review
**Next Review**: After user approval
