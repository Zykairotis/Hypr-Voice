"""Tools Service"""

from .hyprland_tools import (
    get_application_context,
    switch_to_window,
    list_open_windows,
    switch_workspace,
    get_workspaces,
    HYPRLAND_TOOLS
)

from .claude_code_integration import (
    ClaudeCodeAgent,
    HyprlandMonitor,
    ApplicationContext,
    create_context_aware_agent
)

from .hypr_whisper_integration import (
    HyprWhisperIntegration,
    ContextAwareRouter
)

from .hyprland_ss_ctx import (
    get_hyprland_all_clients,
    get_hyprland_active_client,
    get_hyprland_clients_by_class,
    get_hyprland_clients_by_title,
    get_hyprland_clients_by_workspace,
    screenshot_hyprland_client,
    screenshot_hyprland_client_by_class,
    screenshot_hyprland_client_by_title,
    screenshot_hyprland_active_window,
    screenshot_hyprland_full_screen,
    screenshot_hyprland_workspace,
    HYPRLAND_SS_CTX_TOOLS
)

__all__ = [
    # Hyprland tools
    'get_application_context',
    'switch_to_window',
    'list_open_windows',
    'switch_workspace',
    'get_workspaces',
    'HYPRLAND_TOOLS',
    
    # Claude integration
    'ClaudeCodeAgent',
    'HyprlandMonitor',
    'ApplicationContext',
    'create_context_aware_agent',
    
    # Hypr-Whisper integration
    'HyprWhisperIntegration',
    'ContextAwareRouter',
    
    # Hyprland Screenshot Context tools
    'get_hyprland_all_clients',
    'get_hyprland_active_client',
    'get_hyprland_clients_by_class',
    'get_hyprland_clients_by_title',
    'get_hyprland_clients_by_workspace',
    'screenshot_hyprland_client',
    'screenshot_hyprland_client_by_class',
    'screenshot_hyprland_client_by_title',
    'screenshot_hyprland_active_window',
    'screenshot_hyprland_full_screen',
    'screenshot_hyprland_workspace',
    'HYPRLAND_SS_CTX_TOOLS'
]
