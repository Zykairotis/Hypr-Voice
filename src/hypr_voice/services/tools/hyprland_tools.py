"""
Hyprland Tools Module
Tools for interacting with Hyprland window manager
"""

import asyncio
import json
import logging
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

from ..sdk_compat import tool


@tool(
    name="get_application_context",
    description="Get current application context and window information",
    input_schema={}
)
async def get_application_context(args: dict) -> Dict:
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
            result = {
                "class": data.get("class", ""),
                "title": data.get("title", ""),
                "workspace": data.get("workspace", {}).get("id", -1),
                "detected": True
            }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": False,
                "data": result,
            }
    except Exception as e:
        logger.error(f"Error getting application context: {e}")
    
    result = {"detected": False, "error": "Failed to get window information"}
    return {
        "content": [{"type": "text", "text": json.dumps(result)}],
        "is_error": True,
        "data": result,
    }


@tool(
    name="switch_to_window",
    description="Switch to a specific window by class or title",
    input_schema={"window_identifier": str}
)
async def switch_to_window(args: dict) -> Dict:
    """Switch to a window using Hyprland"""
    window_identifier = (args or {}).get("window_identifier", "")
    if not window_identifier:
        result = {"success": False, "error": "window_identifier is required"}
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }
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
                        
                        result = {
                            "success": True,
                            "switched_to": client.get("class", ""),
                            "title": client.get("title", "")
                        }
                        return {
                            "content": [{"type": "text", "text": json.dumps(result)}],
                            "is_error": False,
                            "data": result,
                        }
            
            result = {"success": False, "error": "Window not found"}
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": True,
                "data": result,
            }
            
    except Exception as e:
        result = {"success": False, "error": str(e)}
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="list_open_windows",
    description="List all open windows in Hyprland",
    input_schema={}
)
async def list_open_windows(args: dict) -> Dict:
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
            
            result = {
                "success": True,
                "windows": windows,
                "count": len(windows)
            }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": False,
                "data": result,
            }
            
    except Exception as e:
        result = {"success": False, "error": str(e)}
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="switch_workspace",
    description="Switch to a specific workspace",
    input_schema={"workspace_id": int}
)
async def switch_workspace(args: dict) -> Dict:
    """Switch to a workspace in Hyprland"""
    workspace_id = (args or {}).get("workspace_id")
    if workspace_id is None:
        result = {"success": False, "error": "workspace_id is required"}
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }
    try:
        process = await asyncio.create_subprocess_exec(
            'hyprctl', 'dispatch', 'workspace', str(workspace_id),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            result = {
                "success": True,
                "workspace": workspace_id
            }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": False,
                "data": result,
            }
        else:
            result = {
                "success": False,
                "error": stderr.decode()
            }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": True,
                "data": result,
            }
            
    except Exception as e:
        result = {"success": False, "error": str(e)}
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="get_workspaces",
    description="Get all workspaces and their windows",
    input_schema={}
)
async def get_workspaces(args: dict) -> Dict:
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
            
            result = {
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
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": False,
                "data": result,
            }
            
    except Exception as e:
        result = {"success": False, "error": str(e)}
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


# Export all tools
HYPRLAND_TOOLS = [
    get_application_context,
    switch_to_window,
    list_open_windows,
    switch_workspace,
    get_workspaces
]
