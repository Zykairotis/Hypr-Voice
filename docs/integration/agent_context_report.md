# Hypr-Voice Agent Context & Permissions Report

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Current State](#current-state)
- [Desired Target State](#desired-target-state)
- [Implementation Plan](#proposed-changes-implementation-plan)
- [Risk Assessment](#risk-assessment)
- [Open Questions](#open-questions)
- [Testing Strategy](#suggested-tests)
- [Progress Tracking](#progress-tracking)

---

## Overview
This note captures the current state of context capture, permissions, and `.claude` integrations for the Hypr-Voice agent, plus the desired target state to align with the Claude Agent SDK docs and the product requirements you outlined.

### Key Objectives
| Objective | Priority | Status |
|-----------|----------|--------|
| Safe permission model with approval flow | High | Planned |
| Rich context injection per turn | High | Partial |
| `.claude` project settings integration | Medium | Planned |
| Observability & logging | Medium | Partial |
| Non-Hyprland fallback support | Low | Future |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Interface                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   Voice UI   │  │   Web UI     │  │  Permission Modal    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼─────────────────┼─────────────────────┼───────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Orchestrator (9093)                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Context Assembly Pipeline                   │   │
│  │  [Window] + [Clipboard] + [History] + [Screenshot]      │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐   │
│  │ EnhancedAgent   │  │ VoiceOrchestrator│  │ ClaudeTTSAgent│  │
│  │ (core/)         │  │ (orchestrator/)  │  │ (services/)   │   │
│  └────────┬────────┘  └────────┬────────┘  └───────┬───────┘   │
└───────────┼────────────────────┼───────────────────┼────────────┘
            │                    │                   │
            ▼                    ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Claude Agent SDK Layer                        │
│  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │
│  │ can_use_tool()  │  │ setting_sources │  │ permission_mode│  │
│  │ callback        │  │ [project,user]  │  │ default/plan   │  │
│  └─────────────────┘  └─────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Context Providers                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ HyprlandMon  │  │ ClipboardSvc │  │ TerminalHistorySvc   │  │
│  │ (window/voc) │  │ (wl-paste)   │  │ (zsh/bash/fish)      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current State
- **Agent flavors**
  - `core/orchestrator.py` → `EnhancedAgent` (FastAPI) with optional context-aware Claude Code agent.
  - `orchestrator/orchestrator.py` → voice-focused orchestrator with 5 predefined subagents; can spawn additional agents on demand.
- **Claude Agent SDK**
  - SDK package: `claude_agent_sdk` in `requirements/hypr_voice.txt`.
  - `permission_mode="acceptEdits"` everywhere (auto-approves tools); no `can_use_tool` callback implemented.
  - Working directory and model passed; `setting_sources` not yet set, so `.claude` configs are not auto-loaded.
  - Available permission modes: `"default"` | `"acceptEdits"` | `"plan"` | `"bypassPermissions"`
- **Context signals**
  - Active window + title + vocabulary (Hyprland) via `HyprlandMonitor`; context can be prepended in context-aware path.
  - Window inventory & switching tools: `get_application_context`, `list_open_windows`, `get_hyprland_all_clients`, `switch_to_window`.
  - Screenshots: rich set of Hyprland screenshot tools (`hyprland_ss_ctx.py`), optional copy-to-clipboard; Gemini analysis tools exist.
  - Missing: clipboard text, terminal last command/history, per-prompt automatic screenshot/clipboard injection.
- **.claude project settings**
  - Repo contains config scaffolding (`config/defaults/claude-sdk.yaml`) but SDK options do not set `setting_sources`; Skills/commands/subagents from `.claude/` or `~/.claude/` are not loaded.
- **Permissions UX**
  - No user-facing approval flow; tools run without confirmation because of `acceptEdits`.
- **Voice/TTS**
  - `ClaudeTTSAgent` uses SDK; now passes working directory and system prompt; permissions still default.

## Desired Target State
- **Safe permissions**
  - Use `permission_mode="default"` (or `plan`) and implement `can_use_tool` callback to request approval for sensitive tools (Bash, Write, clipboard, history, screenshots).
  - Emit approval requests over WebSocket so UI can approve/deny; fallback CLI prompt for dev mode.
- **Context-rich prompts each turn**
  - Auto-attach: active app + title + vocabulary, latest clipboard text, last N terminal commands, optional fresh screenshot token/URL.
  - Respect user opt-in/opt-out for clipboard/history capture.
- **.claude integration**
  - Set `setting_sources=["project","user"]` (configurable) in all `ClaudeAgentOptions`.
  - Include `"Skill"`/`"SlashCommand"` in `allowed_tools` so `.claude/skills` and `.claude/commands` are available.
  - Working directory defaults to repo root when running the orchestrator.
- **Observability & routing**
  - Log when context blocks are attached; surface loaded Skills/commands in UI for transparency.
- **Coverage for non-Hyprland users (future)**
  - Fallback context providers (e.g., X11/Wayland generic APIs) or no-op gracefully.

## Proposed Changes (implementation plan)

### Phase 1: Permissions System (Priority: High)

#### 1.1 Implement `can_use_tool` Callback
**Files:** `core/orchestrator.py`, `orchestrator/orchestrator.py`, `services/claude_tts_agent.py`

```python
# Updated implementation using Claude Agent SDK 2025 API
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ToolPermissionContext,
    PermissionResultAllow,
    PermissionResultDeny
)

SENSITIVE_TOOLS = {
    "Bash": "high",
    "Write": "medium", 
    "clipboard_text": "medium",
    "terminal_recent_commands": "medium",
    "screenshot": "low",
}

async def can_use_tool(
    tool_name: str,
    tool_input: dict,
    context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    """Gate sensitive tools through approval flow (SDK 2025 API)."""
    
    # Block writes to sensitive files
    if tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        if "config" in file_path.lower() or ".env" in file_path.lower():
            return PermissionResultDeny(
                behavior="deny",
                message="Cannot write to config/env files without approval",
                interrupt=False
            )
    
    # Add safety flags to dangerous bash commands
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if command.startswith("rm"):
            modified_input = {**tool_input, "command": f"{command} -i"}
            return PermissionResultAllow(
                behavior="allow",
                updated_input=modified_input
            )
    
    # Allow everything else
    return PermissionResultAllow(behavior="allow")

# Usage in ClaudeAgentOptions
options = ClaudeAgentOptions(
    allowed_tools=["Read", "Write", "Bash", "Edit", "Glob", "Grep"],
    permission_mode="default",  # or "acceptEdits" | "plan" | "bypassPermissions"
    can_use_tool=can_use_tool,
    model="claude-sonnet-4-5",
    setting_sources=["user", "project"],
)
```

#### 1.2 PreToolUse/PostToolUse Hooks (SDK 2025)
**Files:** `core/orchestrator.py`, `orchestrator/orchestrator.py`

The SDK provides hooks for intercepting tool calls before and after execution:

```python
from claude_agent_sdk import (
    ClaudeAgentOptions,
    ClaudeSDKClient,
    HookMatcher,
    HookInput,
    HookContext,
    HookJSONOutput
)

async def pre_tool_hook(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext
) -> HookJSONOutput:
    """Validate tool calls before execution."""
    tool_name = input_data["tool_name"]
    tool_input = input_data["tool_input"]
    
    # Block dangerous bash patterns
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        dangerous = ["rm -rf /", "sudo rm", "> /dev/sda"]
        for pattern in dangerous:
            if pattern in command:
                return {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": f"Blocked: {pattern}"
                    }
                }
    return {}

async def post_tool_hook(
    input_data: HookInput,
    tool_use_id: str | None,
    context: HookContext
) -> HookJSONOutput:
    """React to tool execution results."""
    tool_response = input_data.get("tool_response", "")
    
    if "critical" in str(tool_response).lower():
        return {
            "continue_": False,
            "stopReason": "Critical error detected",
            "systemMessage": "Execution stopped for safety"
        }
    return {"continue_": True}

# Configure hooks in options
options = ClaudeAgentOptions(
    hooks={
        "PreToolUse": [HookMatcher(matcher="Bash", hooks=[pre_tool_hook])],
        "PostToolUse": [HookMatcher(matcher=None, hooks=[post_tool_hook])]
    }
)
```

#### 1.3 WebSocket Approval Flow
**Files:** `server.py`, `web-ui/lib/endpoints.ts`

```python
# New WS event types
class WSEventType(str, Enum):
    TOOL_PERMISSION_REQUEST = "tool_permission_request"
    TOOL_PERMISSION_RESPONSE = "tool_permission_response"

# FastAPI handler addition
@app.websocket("/ws/permissions")
async def permission_websocket(websocket: WebSocket):
    await websocket.accept()
    pending_approvals: dict[str, asyncio.Future] = {}
    # ... handle approval requests/responses
```

#### 1.4 Permission Mode Configuration
**Files:** `config/defaults/claude-sdk.yaml`, `AgentConfig`

```yaml
# claude-sdk.yaml additions (2025 SDK)
permissions:
  mode: "default"  # "default" | "acceptEdits" | "plan" | "bypassPermissions"
  auto_approve:
    - Read
    - Glob
    - Grep
    - Edit
  require_approval:
    - Bash
    - Write
  session_allow_list: []  # Tools approved for current session

agent:
  model: "claude-sonnet-4-5"  # Default model
  max_turns: 10
  max_budget_usd: 5.0
  setting_sources: ["project", "user"]  # Load .claude configs
```

---

### Phase 2: Context Bundle Assembly (Priority: High)

#### 2.1 Context Assembly Pipeline
**New file:** `src/hypr_voice/core/context_assembler.py`

```python
from dataclasses import dataclass, field
from typing import Optional
import asyncio

@dataclass
class ContextBundle:
    active_window: Optional[str] = None
    window_title: Optional[str] = None
    vocabulary: list[str] = field(default_factory=list)
    clipboard_text: Optional[str] = None
    terminal_history: list[str] = field(default_factory=list)
    screenshot_path: Optional[str] = None
    timestamp: str = ""

    def to_system_block(self) -> str:
        """Format context as system message block."""
        parts = ["<context>"]
        if self.active_window:
            parts.append(f"  <active_app>{self.active_window}</active_app>")
        if self.window_title:
            parts.append(f"  <window_title>{self.window_title}</window_title>")
        if self.clipboard_text:
            parts.append(f"  <clipboard>{self.clipboard_text[:500]}</clipboard>")
        if self.terminal_history:
            parts.append(f"  <recent_commands>{'; '.join(self.terminal_history[-5:])}</recent_commands>")
        parts.append("</context>")
        return "\n".join(parts)

class ContextAssembler:
    """Gathers context from all providers before each agent turn."""
    
    def __init__(self, config: "ContextConfig"):
        self.config = config
        self.providers = []
    
    async def gather(self) -> ContextBundle:
        """Gather context from all enabled providers concurrently."""
        tasks = [p.get_context() for p in self.providers if p.enabled]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return self._merge_results(results)
```

#### 2.2 Configuration Options
```yaml
# context.yaml
context:
  enabled: true
  providers:
    window:
      enabled: true
      include_vocabulary: true
    clipboard:
      enabled: false  # opt-in for privacy
      max_length: 500
    terminal_history:
      enabled: false  # opt-in for privacy
      max_commands: 5
      shells: ["zsh", "bash", "fish"]
    screenshot:
      enabled: false
      mode: "on_demand"  # "every_turn" | "on_demand"
```

---

### Phase 3: New Context Tools (Priority: Medium)

#### 3.1 Clipboard Tool
**New file:** `src/hypr_voice/services/tools/clipboard_tool.py`

```python
import subprocess
from typing import Optional

async def get_clipboard_text() -> Optional[str]:
    """Get clipboard text content via wl-paste (Wayland) or xclip (X11)."""
    try:
        # Try Wayland first
        result = subprocess.run(
            ["wl-paste", "--no-newline"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    
    try:
        # Fallback to X11
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-o"],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return result.stdout
    except FileNotFoundError:
        pass
    
    return None
```

#### 3.2 Terminal History Tool
**New file:** `src/hypr_voice/services/tools/terminal_history_tool.py`

```python
from pathlib import Path
from typing import Optional

HISTORY_PATHS = {
    "zsh": Path.home() / ".zsh_history",
    "bash": Path.home() / ".bash_history",
    "fish": Path.home() / ".local/share/fish/fish_history",
}

async def get_terminal_history(shell: str = "zsh", count: int = 10) -> list[str]:
    """Read recent commands from shell history file."""
    history_path = HISTORY_PATHS.get(shell)
    if not history_path or not history_path.exists():
        return []
    
    try:
        with open(history_path, "r", errors="ignore") as f:
            lines = f.readlines()
        # Parse based on shell format (zsh uses `: timestamp:0;command`)
        commands = []
        for line in lines[-count * 2:]:  # Read extra for zsh format
            if shell == "zsh" and line.startswith(":"):
                cmd = line.split(";", 1)[-1].strip()
            else:
                cmd = line.strip()
            if cmd:
                commands.append(cmd)
        return commands[-count:]
    except Exception:
        return []
```

---

### Phase 4: `.claude` Integration (Priority: Medium)

#### 4.1 Setting Sources Configuration
**Files:** All agent option builders

```python
from pathlib import Path
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient, HookMatcher

def build_agent_options(config: AgentConfig) -> ClaudeAgentOptions:
    """Build agent options with 2025 SDK API."""
    return ClaudeAgentOptions(
        # Model and limits
        model=config.model or "claude-sonnet-4-5",
        max_turns=config.max_turns or 10,
        max_budget_usd=config.max_budget_usd or 5.0,
        
        # Working directory
        cwd=config.working_dir or Path.cwd(),
        
        # Permissions
        permission_mode=config.permission_mode or "default",
        can_use_tool=config.can_use_tool_callback,
        
        # Settings sources - loads .claude configs
        setting_sources=config.setting_sources or ["project", "user"],
        
        # Tools
        allowed_tools=[
            *config.allowed_tools,
            "Skill",        # Enable .claude/skills
            "SlashCommand", # Enable .claude/commands
        ],
        
        # System prompt
        system_prompt=config.system_prompt,
        
        # Hooks for pre/post tool validation
        hooks=config.hooks or {},
        
        # MCP servers for custom tools
        mcp_servers=config.mcp_servers or {},
    )
```

#### 4.2 Skills Discovery & UI Surface
```typescript
// web-ui/lib/skills.ts
interface LoadedSkill {
  name: string;
  source: "project" | "user";
  description?: string;
}

async function getLoadedSkills(): Promise<LoadedSkill[]> {
  const response = await fetch("/api/agent/skills");
  return response.json();
}
```

---

### Phase 5: Documentation & UI (Priority: Low)

- Document approval flow in `docs/integration/PERMISSIONS.md`
- Add context signal toggles to web-ui settings panel
- Surface loaded Skills/commands in UI sidebar
- Add permission request modal component

## Open Questions
- Which shells should we support for history (zsh, bash, fish) and where are their history files located on this system?
- Should screenshots be captured every prompt or only on demand?
- What’s the preferred approval UI: modal per request, or “always allow for session” toggles per tool category?

## Changes Implemented (this pass)
- Default `permission_mode` set to `default` and permission callback added; emits `permission_request` events and waits up to 30s for a WebSocket response.
- SDK options now carry `allowed_tools` (incl. `Skill`, `SlashCommand`) and `setting_sources` (default `["project"]`) across orchestrators and TTS.
- Context prefix per prompt now includes active window, optional clipboard text, optional recent terminal commands.
- `.claude` loading enabled via `setting_sources` defaults; working directory already propagated.

## Suggested Tests
- Unit: permission callback blocks/updates tool inputs; context bundle formatter.
- Integration: run an agent with `permission_mode=default`, ensure WS approval flow gates Bash/write; verify Skills from `.claude/skills` appear after setting `setting_sources`.
- Manual: invoke `/refactor` from `.claude/commands`, confirm execution; ask “what skills do you see?” and ensure SDK lists them.

---

## Risk Assessment

| Change | Risk Level | Mitigation |
|--------|------------|------------|
| Permission mode switch to `default` | Medium | Gradual rollout; keep `acceptEdits` as fallback config option |
| Clipboard access | High (privacy) | Disabled by default; explicit opt-in; truncate to 500 chars |
| Terminal history access | High (privacy) | Disabled by default; filter sensitive patterns (passwords, tokens) |
| WebSocket approval flow | Medium | Implement timeout fallback; CLI prompt for dev mode |
| `.claude` settings loading | Low | Validate loaded skills; sandbox execution |

### Security Considerations
- **Clipboard sanitization**: Strip potential secrets (regex for API keys, tokens)
- **History filtering**: Exclude commands containing `password`, `secret`, `token`, `key=`
- **Screenshot handling**: Auto-delete after processing; never persist to disk without consent
- **Approval timeout**: Default 30s timeout; configurable per-tool

---

## Progress Tracking

### Phase 1: Permissions System
- [ ] Implement `can_use_tool` callback in `core/orchestrator.py`
- [ ] Implement `can_use_tool` callback in `orchestrator/orchestrator.py`
- [ ] Implement `can_use_tool` callback in `claude_tts_agent.py`
- [ ] Add `TOOL_PERMISSION_REQUEST` WS event type
- [ ] Add WS permission handler in FastAPI
- [ ] Create permission config schema
- [ ] Add UI permission modal component

### Phase 2: Context Bundle
- [ ] Create `ContextBundle` dataclass
- [ ] Implement `ContextAssembler` class
- [ ] Integrate with `execute_instruction` flow
- [ ] Add context config options
- [ ] Add context logging/observability

### Phase 3: New Tools
- [ ] Implement `clipboard_tool.py`
- [ ] Implement `terminal_history_tool.py`
- [ ] Add sensitive data filtering
- [ ] Register tools with agent

### Phase 4: `.claude` Integration
- [ ] Add `setting_sources` to `AgentConfig`
- [ ] Wire through all option builders
- [ ] Add `Skill`/`SlashCommand` to allowed tools
- [ ] Create skills discovery API endpoint

### Phase 5: Documentation & UI
- [ ] Write `docs/integration/PERMISSIONS.md`
- [ ] Add settings panel toggles
- [ ] Add skills sidebar component
- [ ] Update README with new features

---

## References

| Resource | Path/Link |
|----------|-----------|
| Claude Agent SDK Docs | anthropic.com/docs |
| Current Orchestrator | `src/hypr_voice/core/orchestrator.py` |
| Voice Orchestrator | `src/hypr_voice/orchestrator/voice_orchestrator.py` |
| Hyprland Tools | `src/hypr_voice/services/tools/hyprland_tools.py` |
| Screenshot Tools | `src/hypr_voice/services/tools/hyprland_ss_ctx.py` |
| SDK Config | `config/defaults/claude-sdk.yaml` |

---

*Last updated: 2025*
