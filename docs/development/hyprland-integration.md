# Hyprland IPC Integration Guide

## Overview

Hypr-Voice integrates with Hyprland (Wayland compositor) through IPC (Inter-Process Communication) to provide context-aware voice interactions. This integration allows the voice assistant to understand which application is currently focused, window titles, workspace information, and even control windows directly.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              Hyprland IPC Integration                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         HyprlandMonitor                               │   │
│  │  - Polls hyprctl for window changes                  │   │
│  │  - Maintains application context                     │   │
│  │  - Triggers callbacks on context changes             │   │
│  └─────────────┬────────────────────────────────────────┘   │
│                │                                             │
│         ┌──────┴──────┐                                     │
│         │  hyprctl    │                                     │
│         │  IPC Socket │                                     │
│         └──────┬──────┘                                     │
│                │                                             │
│  ┌─────────────┴────────────────────────────────────────┐   │
│  │              Hyprland Tools                           │   │
│  │  ┌──────────────┐  ┌──────────────┐                 │   │
│  │  │ Get Context  │  │Switch Window │                 │   │
│  │  │List Windows  │  │Switch Workspace│               │   │
│  │  └──────────────┘  └──────────────┘                 │   │
│  └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Setup

```bash
# Required: Hyprland must be running
echo $HYPRLAND_INSTANCE_SIGNATURE

# If not set, try:
export HYPRLAND_INSTANCE_SIGNATURE=$(hyprctl instance)

# Verify Hyprland is running
hyprctl version
hyprctl activewindow -j
```

### Dependencies

```bash
# Hyprland (includes hyprctl)
# Usually installed via package manager:
# yay -S hyprland  # Arch
# or built from source

# Python dependencies (included)
pip install aiohttp asyncio
```

## Usage

### Basic Application Context

```python
from hypr_voice.services.tools.hyprland_tools import get_application_context

async def get_current_app():
    result = await get_application_context({})

    if result['data']['detected']:
        app_class = result['data']['class']
        window_title = result['data']['title']
        workspace = result['data']['workspace']

        print(f"Application: {app_class}")
        print(f"Title: {window_title}")
        print(f"Workspace: {workspace}")
```

### Continuous Monitoring

```python
from hypr_voice.services.tools.claude_code_integration import HyprlandMonitor

async def monitor_applications():
    monitor = HyprlandMonitor(update_interval=0.15)  # 150ms

    # Define callback for context changes
    async def on_context_change(context):
        print(f"App: {context.window_class}")
        print(f"Title: {context.window_title}")
        print(f"Workspace: {context.workspace_id}")

    # Register callback
    monitor.register_callback(on_context_change)

    # Start monitoring
    await monitor.start()

    try:
        # Keep running
        await asyncio.sleep(60)
    finally:
        await monitor.stop()
```

### Window Switching

```python
from hypr_voice.services.tools.hyprland_tools import switch_to_window

async def switch_to_app():
    # Switch by window class
    result = await switch_to_window({
        "window_identifier": "firefox"
    })

    if result['data']['success']:
        print(f"Switched to: {result['data']['switched_to']}")

    # Switch by window title
    result = await switch_to_window({
        "window_identifier": "YouTube"
    })

    # Partial match works
    result = await switch_to_window({
        "window_identifier": "code"  # Matches VSCode
    })
```

### List All Windows

```python
from hypr_voice.services.tools.hyprland_tools import list_open_windows

async def list_windows():
    result = await list_open_windows({})

    if result['data']['success']:
        for window in result['data']['windows']:
            focused = " (focused)" if window['focused'] else ""
            print(f"{window['class']} - {window['title']}{focused}")
```

### Workspace Management

```python
from hypr_voice.services.tools.hyprland_tools import (
    get_workspaces,
    switch_workspace
)

async def manage_workspaces():
    # Get all workspaces
    result = await get_workspaces({})

    if result['data']['success']:
        for ws in result['data']['workspaces']:
            active = " (active)" if ws['active'] else ""
            print(f"Workspace {ws['id']}: {ws['windows']} windows{active}")

    # Switch to workspace 1
    result = await switch_workspace({
        "workspace_id": 1
    })
```

## Context-Aware Features

### Application Context

```python
from hypr_voice.services.tools.claude_code_integration import ApplicationContext

async def get_detailed_context():
    monitor = HyprlandMonitor()
    await monitor.start()

    # Get current context
    context = await monitor.get_current_context()

    print(f"Application: {context.window_class}")
    print(f"Title: {context.window_title}")
    print(f"Workspace: {context.workspace_id}")
    print(f"Executable: {context.window_class}")

    # Get application vocabulary
    print(f"Vocabulary: {context.vocabulary[:10]}")

    await monitor.stop()
```

### Context-Aware Routing

```python
from hypr_voice.services.tools.hypr_whisper_integration import (
    HyprWhisperIntegration,
    ContextAwareRouter
)

async def context_aware_routing():
    integration = HyprWhisperIntegration()
    await integration.start()

    router = ContextAwareRouter(integration)

    # Register handlers for specific apps
    async def vscode_handler(request, context):
        # VS Code-specific commands
        if "open file" in request.lower():
            return {"action": "open_file", "app": "vscode"}
        return {"action": "unknown"}

    async def browser_handler(request, context):
        # Browser-specific commands
        if "search" in request.lower():
            query = request.replace("search", "").strip()
            return {"action": "search", "query": query}
        return {"action": "unknown"}

    router.register_route("code", vscode_handler)
    router.register_route("firefox", browser_handler)
    router.register_route("chrome", browser_handler)

    # Route request based on current app
    result = await router.route_request("Search for Python tutorials")
    print(f"Routed to: {result}")
```

### Vocabulary Extraction

```python
async def extract_vocabulary():
    monitor = HyprlandMonitor()
    await monitor.start()

    context = await monitor.get_current_context()

    # Vocabulary includes:
    # - Application-specific terms
    # - Window title keywords
    # - Common commands for the app
    vocabulary = context.vocabulary

    print(f"Extracted {len(vocabulary)} vocabulary terms:")
    for term in vocabulary[:20]:
        print(f"  - {term}")

    await monitor.stop()
```

## Hyprland Tools

### Available Tools

```python
from hypr_voice.services.tools.hyprland_tools import HYPRLAND_TOOLS

# List all available tools
for tool in HYPRLAND_TOOLS:
    print(f"{tool.name}: {tool.description}")

# Output:
# get_application_context: Get current application context and window information
# switch_to_window: Switch to a specific window by class or title
# list_open_windows: List all open windows in Hyprland
# switch_workspace: Switch to a specific workspace
# get_workspaces: Get all workspaces and their windows
```

### Tool Integration with Claude

```python
from hypr_voice.services.claude_tts_agent import ClaudeTTSAgent

async def claude_with_hyprland():
    # Setup tools
    from hypr_voice.services.tools.hyprland_tools import HYPRLAND_TOOLS

    # Create agent with Hyprland tools
    agent = ClaudeTTSAgent(
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        system_prompt="You have access to Hyprland window management tools"
    )
    await agent.connect()

    # Use Hyprland context
    result = await agent.chat(
        "Switch to Firefox and tell me the current window title",
        # Tools would be passed here
    )

    print(result['response'])

    await agent.close()
```

## Advanced Features

### Context Change Callbacks

```python
async def advanced_monitoring():
    monitor = HyprlandMonitor(update_interval=0.1)

    # Multiple callbacks
    async def log_context(context):
        logger.info(f"Switched to {context.window_class}")

    async def update_vocabulary(context):
        await update_whisper_vocabulary(context)

    async def trigger_action(context):
        if context.window_class == "code":
            await enable_code_mode()
        elif context.window_class == "firefox":
            await enable_browser_mode()

    # Register all callbacks
    monitor.register_callback(log_context)
    monitor.register_callback(update_vocabulary)
    monitor.register_callback(trigger_action)

    await monitor.start()

    # ... do work ...

    await monitor.stop()
```

### Custom Window Actions

```python
async def custom_window_actions():
    import subprocess

    # Focus specific window
    async def focus_window(address):
        await subprocess.run([
            "hyprctl",
            "dispatch",
            "focuswindow",
            f"address:{address}"
        ])

    # Move window to workspace
    async def move_to_workspace(address, workspace_id):
        await subprocess.run([
            "hyprctl",
            "dispatch",
            "movetoworkspace",
            str(workspace_id),
            f"address:{address}"
        ])

    # Toggle fullscreen
    async def toggle_fullscreen(address):
        await subprocess.run([
            "hyprctl",
            "dispatch",
            "togglefullscreen",
            f"address:{address}"
        ])
```

### Window Property Queries

```python
async def query_window_properties():
    import json
    import subprocess

    # Get all clients (windows)
    process = await subprocess.run(
        ["hyprctl", "clients", "-j"],
        capture_output=True
    )

    clients = json.loads(process.stdout.decode())

    for client in clients:
        print(f"Class: {client.get('class')}")
        print(f"Title: {client.get('title')}")
        print(f"Workspace: {client.get('workspace', {}).get('id')}")
        print(f"Focused: {client.get('focusHistoryID', -1) == 0}")
        print(f"Address: {client.get('address')}")
        print(f"Size: {client.get('size', {})}")
        print(f"Position: {client.get('at', {})}")
        print()
```

## Integration Examples

### Voice-Controlled Window Switcher

```python
async def voice_window_switcher():
    from hypr_voice.services.wispr_flow_direct import WisprFlowDirect
    from hypr_voice.services.tools.hyprland_tools import switch_to_window

    wispr = WisprFlowDirect()
    await wispr.connect()

    # Listen for voice command
    transcription = await wispr.transcribe("audio.wav")

    # Extract app name from transcription
    # e.g., "Switch to Firefox" -> "Firefox"
    app_name = extract_app_name(transcription['text'])

    # Switch to window
    result = await switch_to_window({
        "window_identifier": app_name
    })

    if result['data']['success']:
        # Provide feedback
        print(f"Switched to {result['data']['switched_to']}")

    await wispr.close()
```

### Context-Aware Voice Assistant

```python
async def context_aware_assistant():
    from hypr_voice.services.tools.hypr_whisper_integration import HyprWhisperIntegration

    integration = HyprWhisperIntegration()
    await integration.start()

    # Get current context
    context = await integration.get_current_context()

    # Transcribe with context
    transcription = await integration.transcribe_with_context(
        audio_data=b"..."
    )

    # Response is context-aware
    # e.g., in VS Code: knows about code, files, etc.
    # e.g., in browser: knows about tabs, URLs, etc.

    await integration.stop()
```

### Automatic Vocabulary Updates

```python
async def auto_vocabulary_update():
    from hypr_voice.services.tools.hypr_whisper_integration import HyprWhisperIntegration

    integration = HyprWhisperIntegration()

    # This automatically:
    # 1. Monitors Hyprland for window changes
    # 2. Extracts vocabulary from current app
    # 3. Updates Whisper server with new vocabulary
    # 4. Notifies agent system of context change

    await integration.start()

    # Keep running
    await asyncio.sleep(300)  # 5 minutes

    await integration.stop()
```

### Workspace Automation

```python
async def workspace_automation():
    from hypr_voice.services.tools.hyprland_tools import (
        get_workspaces,
        switch_workspace,
        list_open_windows
    )

    # Get workspace info
    ws_result = await get_workspaces({})
    windows_result = await list_open_windows({})

    # Organize windows by workspace
    workspace_map = {}
    for window in windows_result['data']['windows']:
        ws_id = window['workspace']
        if ws_id not in workspace_map:
            workspace_map[ws_id] = []
        workspace_map[ws_id].append(window['class'])

    # Auto-arrange: Move all browser windows to workspace 1
    for window in windows_result['data']['windows']:
        if 'firefox' in window['class'].lower() or 'chrome' in window['class'].lower():
            await move_window_to_workspace(window['address'], 1)
```

## Troubleshooting

### Hyprland Not Detected

**Error**: `Failed to get window information`

**Solution**:
```bash
# Check if Hyprland is running
echo $XDG_CURRENT_DESKTOP  # Should be "Hyprland"
echo $HYPRLAND_INSTANCE_SIGNATURE

# If not set, try:
export HYPRLAND_INSTANCE_SIGNATURE=$(hyprctl instance)

# Test hyprctl
hyprctl activewindow
hyprctl clients
```

### Socket Permission Issues

**Error**: `Permission denied accessing Hyprland socket`

**Solution**:
```bash
# Check socket permissions
ls -la /tmp/hypr/

# Add user to appropriate group if needed
# (This depends on your Hyprland configuration)
```

### Context Updates Not Working

**Error**: Context not updating when switching windows

**Solution**:
```python
# Increase polling interval
monitor = HyprlandMonitor(update_interval=0.5)  # Slower but more reliable

# Check if callbacks are registered
monitor._callbacks

# Manually trigger update
context = await monitor.get_current_context()
```

### Window Not Found

**Error**: `Window not found when trying to switch`

**Solution**:
```python
# List all windows first
result = await list_open_windows({})

for window in result['data']['windows']:
    print(f"{window['class']} - {window['title']}")

# Use exact class name or partial title match
# e.g., "firefox" instead of "Firefox"
```

## Best Practices

### 1. Use Appropriate Polling Intervals

```python
# Fast (150ms) - Good for responsive monitoring
monitor = HyprlandMonitor(update_interval=0.15)

# Slow (1s) - Good for battery/low CPU
monitor = HyprlandMonitor(update_interval=1.0)

# Very slow (5s) - Good for periodic checks
monitor = HyprlandMonitor(update_interval=5.0)
```

### 2. Handle Missing Context Gracefully

```python
async def safe_context_operation():
    monitor = HyprlandMonitor()

    try:
        context = await monitor.get_current_context()
        if context.window_class:
            print(f"Current app: {context.window_class}")
        else:
            print("No window focused")
    except Exception as e:
        logger.error(f"Failed to get context: {e}")
```

### 3. Cache Context When Needed

```python
from functools import lru_cache

class CachedContextMonitor:
    def __init__(self):
        self.monitor = HyprlandMonitor()
        self._cache = None
        self._cache_time = 0
        self._cache_duration = 1.0  # 1 second cache

    async def get_context(self):
        now = time.time()

        if self._cache and (now - self._cache_time) < self._cache_duration:
            return self._cache

        self._cache = await self.monitor.get_current_context()
        self._cache_time = now
        return self._cache
```

### 4. Register Multiple Callbacks

```python
# Organize callbacks by concern
monitor.register_callback(log_context_change)
monitor.register_callback(update_ui)
monitor.register_callback(update_vocabulary)
monitor.register_callback(trigger_automation)
```

### 5. Clean Up Properly

```python
async with monitor:
    # Do work
    pass

# Or use try/finally
try:
    await monitor.start()
    # Do work
finally:
    await monitor.stop()
```

## API Reference

### HyprlandMonitor

**Constructor Parameters**:
- `update_interval (float)`: Polling interval in seconds (default: 0.15)

**Methods**:
- `async start()`: Start monitoring
- `async stop()`: Stop monitoring
- `register_callback(callback)`: Register context change callback
- `async get_current_context()`: Get current context
- `get_context()`: Synchronous get current context

### ApplicationContext

**Properties**:
- `window_class (str)`: Window class (application name)
- `window_title (str)`: Window title
- `workspace_id (int)`: Current workspace ID
- `vocabulary (List[str])`: Application-specific vocabulary

**Methods**:
- `to_dict()`: Convert to dictionary

### Hyprland Tools

**Available Tools**:
- `get_application_context(args)`: Get current application context
- `switch_to_window(args)`: Switch to window by class/title
- `list_open_windows(args)`: List all open windows
- `switch_workspace(args)`: Switch workspace
- `get_workspaces(args)`: Get workspace information

## Related Documentation

- [Claude Integration](./claude-integration.md)
- [Whisper Integration](./whisper-integration.md)
- [Wispr Flow API](../api/wispr-flow-api.md)
- [Architecture Overview](./ARCHITECTURE.md)
