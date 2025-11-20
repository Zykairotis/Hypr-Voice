"""
Hyprland Tools Module
Tools for interacting with Hyprland window manager
"""

import asyncio
import json
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

try:
    from claude_agent_sdk import tool
except ImportError:
    from claude_agent_sdk_mock import tool


@tool(
    name="get_application_context",
    description="Get current application context and window information"
)
async def get_application_context() -> Dict:
    """Get current application context from Hyprland"""
    try:
        process = await asyncio.create_subprocess_exec(
            'hyprctl', 'activewindow', '-j',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            data = json.loads(stdout.decode())
            return {
                "class": data.get("class", ""),
                "title": data.get("title", ""),
                "workspace": data.get("workspace", {}).get("id", -1),
                "detected": True
            }
    except Exception as e:
        logger.error(f"Error getting application context: {e}")
    
    return {"detected": False, "error": "Failed to get window information"}


@tool(
    name="switch_to_window",
    description="Switch to a specific window by class or title"
)
async def switch_to_window(window_identifier: str) -> Dict:
    """Switch to a window using Hyprland"""
    try:
        # Get all clients
        process = await asyncio.create_subprocess_exec(
            'hyprctl', 'clients', '-j',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            clients = json.loads(stdout.decode())
            
            # Find matching window
            for client in clients:
                if (window_identifier.lower() in client.get("class", "").lower() or
                    window_identifier.lower() in client.get("title", "").lower()):
                    
                    # Switch to window
                    address = client.get("address", "")
                    if address:
                        process = await asyncio.create_subprocess_exec(
                            'hyprctl', 'dispatch', 'focuswindow', f'address:{address}',
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE
                        )
                        await process.communicate()
                        
                        return {
                            "success": True,
                            "switched_to": client.get("class", ""),
                            "title": client.get("title", "")
                        }
            
            return {"success": False, "error": "Window not found"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool(
    name="list_open_windows",
    description="List all open windows in Hyprland"
)
async def list_open_windows() -> Dict:
    """List all open windows"""
    try:
        process = await asyncio.create_subprocess_exec(
            'hyprctl', 'clients', '-j',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            clients = json.loads(stdout.decode())
            
            windows = []
            for client in clients:
                windows.append({
                    "class": client.get("class", ""),
                    "title": client.get("title", ""),
                    "workspace": client.get("workspace", {}).get("id", -1),
                    "focused": client.get("focusHistoryID", -1) == 0,
                    "address": client.get("address", "")
                })
            
            return {
                "success": True,
                "windows": windows,
                "count": len(windows)
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool(
    name="switch_workspace",
    description="Switch to a specific workspace"
)
async def switch_workspace(workspace_id: int) -> Dict:
    """Switch to a workspace in Hyprland"""
    try:
        process = await asyncio.create_subprocess_exec(
            'hyprctl', 'dispatch', 'workspace', str(workspace_id),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            return {
                "success": True,
                "workspace": workspace_id
            }
        else:
            return {
                "success": False,
                "error": stderr.decode()
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@tool(
    name="get_workspaces",
    description="Get all workspaces and their windows"
)
async def get_workspaces() -> Dict:
    """Get workspace information from Hyprland"""
    try:
        process = await asyncio.create_subprocess_exec(
            'hyprctl', 'workspaces', '-j',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            workspaces = json.loads(stdout.decode())
            
            return {
                "success": True,
                "workspaces": [
                    {
                        "id": ws.get("id", -1),
                        "name": ws.get("name", ""),
                        "windows": ws.get("windows", 0),
                        "active": ws.get("lastwindow", "") != ""
                    }
                    for ws in workspaces
                ],
                "count": len(workspaces)
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


# Export all tools
HYPRLAND_TOOLS = [
    get_application_context,
    switch_to_window,
    list_open_windows,
    switch_workspace,
    get_workspaces
]
