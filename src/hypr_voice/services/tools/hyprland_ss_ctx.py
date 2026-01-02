"""
Hyprland Screenshot Context Integration Module
Provides comprehensive Hyprland client data and ultra-fast screenshot capabilities
using grim-hyprland for window screenshots (<100ms).
"""

import asyncio
import json
import logging
import os
import shutil
from pathlib import Path
from typing import Dict, Optional, List, Any
from datetime import datetime
from functools import lru_cache

logger = logging.getLogger(__name__)

from ..sdk_compat import tool

# Cache for client data (short duration to avoid redundant calls)
_client_cache: Optional[Dict] = None
_cache_timestamp: float = 0
_cache_ttl: float = 0.1  # 100ms cache


async def _execute_command(cmd: List[str]) -> tuple[int, bytes, bytes]:
    """Execute a command and return returncode, stdout, stderr"""
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        logger.error(f"Error executing command {cmd}: {e}")
        return -1, b"", str(e).encode()


async def _get_all_clients_raw() -> List[Dict]:
    """Get raw client data from hyprctl (with caching)"""
    import time
    global _client_cache, _cache_timestamp
    
    current_time = time.time()
    
    # Use cache if still valid
    if _client_cache is not None and (current_time - _cache_timestamp) < _cache_ttl:
        return _client_cache
    
    returncode, stdout, stderr = await _execute_command(['hyprctl', 'clients', '-j'])
    
    if returncode == 0:
        try:
            clients = json.loads(stdout.decode())
            _client_cache = clients
            _cache_timestamp = current_time
            return clients
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing hyprctl output: {e}")
            return []
    else:
        logger.error(f"hyprctl failed: {stderr.decode()}")
        return []


def _enrich_client_data(client: Dict) -> Dict:
    """Enrich client data with computed fields"""
    workspace = client.get("workspace", {})
    geometry = client.get("geometry", {})
    
    return {
        # Core identifiers
        "address": client.get("address", ""),
        "class": client.get("class", ""),
        "title": client.get("title", ""),
        "pid": client.get("pid", -1),
        
        # Workspace information
        "workspace": {
            "id": workspace.get("id", -1),
            "name": workspace.get("name", ""),
        },
        
        # Geometry
        "geometry": {
            "x": geometry.get("x", 0),
            "y": geometry.get("y", 0),
            "width": geometry.get("width", 0),
            "height": geometry.get("height", 0),
        },
        
        # Focus and state
        "focusHistoryID": client.get("focusHistoryID", -1),
        "is_focused": client.get("focusHistoryID", -1) == 0,
        "is_active": client.get("focusHistoryID", -1) == 0,
        "mapped": client.get("mapped", False),
        "hidden": client.get("hidden", False),
        "floating": client.get("floating", False),
        "pinned": client.get("pinned", False),
        
        # Additional metadata
        "size": client.get("size", {}),
        "at": client.get("at", []),
        "grouped": client.get("grouped", []),
        "swallowing": client.get("swallowing", ""),
    }


def _check_tool_available(tool_name: str) -> bool:
    """Check if a command-line tool is available"""
    return shutil.which(tool_name) is not None


async def _ensure_screenshot_dir(path: Optional[str] = None) -> Path:
    """Ensure screenshot directory exists, return Path"""
    if path:
        dir_path = Path(path).parent if path.endswith('.png') else Path(path)
    else:
        dir_path = Path.home() / "screenshots"
    
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def _generate_filename(prefix: str = "screenshot") -> str:
    """Generate timestamped filename"""
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return f"{prefix}_{timestamp}.png"


# ============================================================================
# CLIENT DATA TOOLS
# ============================================================================

@tool(
    name="get_hyprland_all_clients",
    description="Get comprehensive data for all Hyprland clients including address, class, title, workspace, geometry, focus state, and metadata. Returns enriched client information optimized for AI agent consumption.",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
        "description": "No arguments required to retrieve all client data."
    }
)
async def get_hyprland_all_clients(args: dict) -> Dict:
    """Get all Hyprland clients with enriched data"""
    try:
        clients_raw = await _get_all_clients_raw()
        clients_enriched = [_enrich_client_data(client) for client in clients_raw]
        
        result = {
            "success": True,
            "clients": clients_enriched,
            "count": len(clients_enriched),
            "timestamp": datetime.now().isoformat()
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": False,
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error getting all clients: {e}")
        result = {
            "success": False,
            "error": str(e),
            "clients": [],
            "count": 0
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="get_hyprland_active_client",
    description="Get detailed data for the currently active/focused window in Hyprland. Returns comprehensive information including address, class, title, workspace, geometry, and state.",
    input_schema={
        "type": "object",
        "properties": {},
        "additionalProperties": False,
        "description": "No arguments required to retrieve active client data."
    }
)
async def get_hyprland_active_client(args: dict) -> Dict:
    """Get the currently active/focused client"""
    try:
        # Get active window directly
        returncode, stdout, stderr = await _execute_command(['hyprctl', 'activewindow', '-j'])
        
        if returncode == 0:
            client_data = json.loads(stdout.decode())
            enriched = _enrich_client_data(client_data)
            
            result = {
                "success": True,
                "client": enriched,
                "timestamp": datetime.now().isoformat()
            }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": False,
                "data": result,
            }
        else:
            # Fallback: find focused client from all clients
            clients_raw = await _get_all_clients_raw()
            for client in clients_raw:
                if client.get("focusHistoryID", -1) == 0:
                    enriched = _enrich_client_data(client)
                    result = {
                        "success": True,
                        "client": enriched,
                        "timestamp": datetime.now().isoformat()
                    }
                    return {
                        "content": [{"type": "text", "text": json.dumps(result)}],
                        "is_error": False,
                        "data": result,
                    }
            
            result = {
                "success": False,
                "error": "No active window found",
                "client": None
            }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
                "is_error": True,
                "data": result,
            }
            
    except Exception as e:
        logger.error(f"Error getting active client: {e}")
        result = {
            "success": False,
            "error": str(e),
            "client": None
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="get_hyprland_clients_by_class",
    description="Filter Hyprland clients by window class name. Returns all matching clients with comprehensive data.",
    input_schema={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "The window class name to filter by (e.g., 'kitty', 'firefox', 'Code'). Search is case-insensitive substring match."
            }
        },
        "required": ["class_name"]
    }
)
async def get_hyprland_clients_by_class(args: dict) -> Dict:
    """Get clients filtered by window class"""
    class_name = (args or {}).get("class_name", "")
    if not class_name:
        result = {"success": False, "error": "class_name is required", "clients": [], "count": 0}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
    try:
        clients_raw = await _get_all_clients_raw()
        matched = [
            _enrich_client_data(client) 
            for client in clients_raw 
            if class_name.lower() in client.get("class", "").lower()
        ]
        
        result = {
            "success": True,
            "class_filter": class_name,
            "clients": matched,
            "count": len(matched),
            "timestamp": datetime.now().isoformat()
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": False,
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error filtering clients by class: {e}")
        result = {
            "success": False,
            "error": str(e),
            "clients": [],
            "count": 0
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="get_hyprland_clients_by_title",
    description="Filter Hyprland clients by window title pattern (substring match). Returns all matching clients with comprehensive data.",
    input_schema={
        "type": "object",
        "properties": {
            "title_pattern": {
                "type": "string",
                "description": "The window title substring to match (e.g., 'GitHub', 'Project'). Search is case-insensitive."
            }
        },
        "required": ["title_pattern"]
    }
)
async def get_hyprland_clients_by_title(args: dict) -> Dict:
    """Get clients filtered by title pattern"""
    title_pattern = (args or {}).get("title_pattern", "")
    if not title_pattern:
        result = {"success": False, "error": "title_pattern is required", "clients": [], "count": 0}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
    try:
        clients_raw = await _get_all_clients_raw()
        matched = [
            _enrich_client_data(client) 
            for client in clients_raw 
            if title_pattern.lower() in client.get("title", "").lower()
        ]
        
        result = {
            "success": True,
            "title_filter": title_pattern,
            "clients": matched,
            "count": len(matched),
            "timestamp": datetime.now().isoformat()
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": False,
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error filtering clients by title: {e}")
        result = {
            "success": False,
            "error": str(e),
            "clients": [],
            "count": 0
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


@tool(
    name="get_hyprland_clients_by_workspace",
    description="Get all clients in a specific workspace. Returns comprehensive data for all windows in the specified workspace.",
    input_schema={
        "type": "object",
        "properties": {
            "workspace_id": {
                "type": "integer",
                "description": "The numeric ID of the workspace (e.g., 1, 2, 10)."
            }
        },
        "required": ["workspace_id"]
    }
)
async def get_hyprland_clients_by_workspace(args: dict) -> Dict:
    """Get all clients in a workspace"""
    workspace_id = (args or {}).get("workspace_id")
    if workspace_id is None:
        result = {"success": False, "error": "workspace_id is required", "clients": [], "count": 0}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
    try:
        clients_raw = await _get_all_clients_raw()
        matched = [
            _enrich_client_data(client) 
            for client in clients_raw 
            if client.get("workspace", {}).get("id", -1) == workspace_id
        ]
        
        result = {
            "success": True,
            "workspace_id": workspace_id,
            "clients": matched,
            "count": len(matched),
            "timestamp": datetime.now().isoformat()
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": False,
            "data": result,
        }
    except Exception as e:
        logger.error(f"Error filtering clients by workspace: {e}")
        result = {
            "success": False,
            "error": str(e),
            "clients": [],
            "count": 0
        }
        return {
            "content": [{"type": "text", "text": json.dumps(result)}],
            "is_error": True,
            "data": result,
        }


# ============================================================================
# SCREENSHOT TOOLS
# ============================================================================

@tool(
    name="screenshot_hyprland_client",
    description="Take a screenshot of a specific Hyprland client window by address. Uses grim-hyprland for ultra-fast capture (<100ms). Can save to file and/or copy to clipboard.",
    input_schema={
        "type": "object",
        "properties": {
            "address": {
                "type": "string",
                "description": "The hex address of the window (e.g., '0x55d68892f3b0') as returned by client enumeration tools."
            },
            "output_path": {
                "type": "string",
                "description": "Optional absolute path where to save the PNG file. If not provided, saves to ~/screenshots with a timestamped name."
            },
            "copy_to_clipboard": {
                "type": "boolean",
                "description": "Whether to copy the screenshot to the system clipboard using wl-copy.",
                "default": False
            }
        },
        "required": ["address"]
    }
)
async def screenshot_hyprland_client(args: dict) -> Dict:
    """Screenshot a specific client by address"""
    address = (args or {}).get("address", "")
    output_path = (args or {}).get("output_path")
    copy_to_clipboard = bool((args or {}).get("copy_to_clipboard", False))
    
    if not address:
        result = {"success": False, "error": "address is required"}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
    
    try:
        # Check if grim is available
        grim_cmd = "grim"
        if not _check_tool_available(grim_cmd):
            result = {
                "success": False,
                "error": f"{grim_cmd} not found. Please install grim or grim-hyprland."
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        # Validate address exists
        clients_raw = await _get_all_clients_raw()
        address_exists = any(client.get("address", "") == address for client in clients_raw)
        
        if not address_exists:
            result = {
                "success": False,
                "error": f"Window with address {address} not found"
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        # Determine output
        if output_path:
            output_file = Path(output_path)
            await _ensure_screenshot_dir(str(output_file))
        elif copy_to_clipboard:
            output_file = None
        else:
            # Default: save to screenshots directory
            screenshots_dir = await _ensure_screenshot_dir()
            output_file = screenshots_dir / _generate_filename("client")
        
        result: Dict[str, Any]
        # Take screenshot using grim -w for window capture
        if output_file:
            returncode, stdout, stderr = await _execute_command([
                grim_cmd, '-w', address, str(output_file)
            ])
            
            if returncode == 0:
                result = {
                    "success": True,
                    "address": address,
                    "output_path": str(output_file),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Also copy to clipboard if requested
                if copy_to_clipboard and _check_tool_available("wl-copy"):
                    process = await asyncio.create_subprocess_exec(
                        grim_cmd, '-w', address, '-',
                        stdout=asyncio.subprocess.PIPE
                    )
                    screenshot_data, _ = await process.communicate()
                    if process.returncode == 0:
                        process2 = await asyncio.create_subprocess_exec(
                            'wl-copy', '--type', 'image/png',
                            stdin=asyncio.subprocess.PIPE
                        )
                        await process2.communicate(input=screenshot_data)
                        if process2.returncode == 0:
                            result["copied_to_clipboard"] = True
                
                return {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "is_error": False,
                    "data": result,
                }
            else:
                result = {
                    "success": False,
                    "error": f"Screenshot failed: {stderr.decode()}",
                    "address": address
                }
                return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        else:
            # Copy to clipboard only
            if not _check_tool_available("wl-copy"):
                result = {
                    "success": False,
                    "error": "wl-copy not found. Please install wl-clipboard."
                }
                return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
            
            # Use pipeline to copy to clipboard
            process1 = await asyncio.create_subprocess_exec(
                grim_cmd, '-w', address, '-',
                stdout=asyncio.subprocess.PIPE
            )
            screenshot_data, _ = await process1.communicate()
            
            if process1.returncode == 0:
                process2 = await asyncio.create_subprocess_exec(
                    'wl-copy', '--type', 'image/png',
                    stdin=asyncio.subprocess.PIPE
                )
                await process2.communicate(input=screenshot_data)
                
                if process2.returncode == 0:
                    result = {
                        "success": True,
                        "address": address,
                        "copied_to_clipboard": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": False, "data": result}
            
            result = {
                "success": False,
                "error": "Failed to copy screenshot to clipboard",
                "address": address
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
            
    except Exception as e:
        logger.error(f"Error taking screenshot: {e}")
        result = {
            "success": False,
            "error": str(e),
            "address": address
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


@tool(
    name="screenshot_hyprland_client_by_class",
    description="Take a screenshot of a Hyprland client window by class name. If multiple windows match, takes the first one. Uses grim-hyprland for ultra-fast capture.",
    input_schema={
        "type": "object",
        "properties": {
            "class_name": {
                "type": "string",
                "description": "The window class name (e.g., 'firefox', 'Code'). Case-insensitive."
            },
            "output_path": {
                "type": "string",
                "description": "Optional absolute path for the output PNG file."
            },
            "copy_to_clipboard": {
                "type": "boolean",
                "description": "Whether to copy the screenshot to the system clipboard.",
                "default": False
            }
        },
        "required": ["class_name"]
    }
)
async def screenshot_hyprland_client_by_class(args: dict) -> Dict:
    """Screenshot a client by class name"""
    class_name = (args or {}).get("class_name", "")
    output_path = (args or {}).get("output_path")
    copy_to_clipboard = bool((args or {}).get("copy_to_clipboard", False))
    try:
        clients_raw = await _get_all_clients_raw()
        
        # Find first matching client
        matching_client = None
        for client in clients_raw:
            if class_name.lower() in client.get("class", "").lower():
                matching_client = client
                break
        
        if not matching_client:
            result = {
                "success": False,
                "error": f"No window with class '{class_name}' found",
                "class_name": class_name
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        address = matching_client.get("address", "")
        return await screenshot_hyprland_client({
            "address": address,
            "output_path": output_path,
            "copy_to_clipboard": copy_to_clipboard
        })
        
    except Exception as e:
        logger.error(f"Error taking screenshot by class: {e}")
        result = {
            "success": False,
            "error": str(e),
            "class_name": class_name
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


@tool(
    name="screenshot_hyprland_client_by_title",
    description="Take a screenshot of a Hyprland client window by title pattern. If multiple windows match, takes the first one. Uses grim-hyprland for ultra-fast capture.",
    input_schema={
        "type": "object",
        "properties": {
            "title_pattern": {
                "type": "string",
                "description": "The window title pattern/substring to match. Case-insensitive."
            },
            "output_path": {
                "type": "string",
                "description": "Optional absolute path for the output PNG file."
            },
            "copy_to_clipboard": {
                "type": "boolean",
                "description": "Whether to copy the screenshot to the system clipboard.",
                "default": False
            }
        },
        "required": ["title_pattern"]
    }
)
async def screenshot_hyprland_client_by_title(args: dict) -> Dict:
    """Screenshot a client by title pattern"""
    title_pattern = (args or {}).get("title_pattern", "")
    output_path = (args or {}).get("output_path")
    copy_to_clipboard = bool((args or {}).get("copy_to_clipboard", False))
    try:
        clients_raw = await _get_all_clients_raw()
        
        # Find first matching client
        matching_client = None
        for client in clients_raw:
            if title_pattern.lower() in client.get("title", "").lower():
                matching_client = client
                break
        
        if not matching_client:
            result = {
                "success": False,
                "error": f"No window matching title pattern '{title_pattern}' found",
                "title_pattern": title_pattern
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        address = matching_client.get("address", "")
        return await screenshot_hyprland_client({
            "address": address,
            "output_path": output_path,
            "copy_to_clipboard": copy_to_clipboard
        })
        
    except Exception as e:
        logger.error(f"Error taking screenshot by title: {e}")
        result = {
            "success": False,
            "error": str(e),
            "title_pattern": title_pattern
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


@tool(
    name="screenshot_hyprland_active_window",
    description="Take a screenshot of the currently active/focused window in Hyprland. Uses grim-hyprland for ultra-fast capture (<100ms). This is the fastest method for capturing the active window.",
    input_schema={
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Optional absolute path for the output PNG file."
            },
            "copy_to_clipboard": {
                "type": "boolean",
                "description": "Whether to copy the screenshot to the system clipboard.",
                "default": False
            }
        }
    }
)
async def screenshot_hyprland_active_window(args: dict) -> Dict:
    """Screenshot the currently active window (fastest method)"""
    output_path = (args or {}).get("output_path")
    copy_to_clipboard = bool((args or {}).get("copy_to_clipboard", False))
    try:
        # Get active window address directly
        returncode, stdout, stderr = await _execute_command(['hyprctl', 'activewindow', '-j'])
        
        if returncode == 0:
            client_data = json.loads(stdout.decode())
            address = client_data.get("address", "")
            
            if not address:
                result = {
                    "success": False,
                    "error": "Active window has no address"
                }
                return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
            
            result = await screenshot_hyprland_client({
                "address": address,
                "output_path": output_path,
                "copy_to_clipboard": copy_to_clipboard
            })
            # result already contains content/data; augment data if present
            if isinstance(result, dict) and "data" in result and isinstance(result["data"], dict):
                result["data"]["window_class"] = client_data.get("class", "")
                result["data"]["window_title"] = client_data.get("title", "")
                # update rendered text
                result["content"] = [{"type": "text", "text": json.dumps(result["data"])}]
            return result
        else:
            result = {
                "success": False,
                "error": f"Failed to get active window: {stderr.decode()}"
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
            
    except Exception as e:
        logger.error(f"Error taking active window screenshot: {e}")
        result = {
            "success": False,
            "error": str(e)
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


@tool(
    name="screenshot_hyprland_full_screen",
    description="Take a screenshot of the entire screen/display. Uses grim for full screen capture. Can save to file and/or copy to clipboard.",
    input_schema={
        "type": "object",
        "properties": {
            "output_path": {
                "type": "string",
                "description": "Optional absolute path for the output PNG file."
            },
            "copy_to_clipboard": {
                "type": "boolean",
                "description": "Whether to copy the screenshot to the system clipboard.",
                "default": False
            }
        }
    }
)
async def screenshot_hyprland_full_screen(args: dict) -> Dict:
    """Screenshot the entire screen"""
    output_path = (args or {}).get("output_path")
    copy_to_clipboard = bool((args or {}).get("copy_to_clipboard", False))
    try:
        # Check if grim is available
        grim_cmd = "grim"
        if not _check_tool_available(grim_cmd):
            result = {
                "success": False,
                "error": f"{grim_cmd} not found. Please install grim."
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        # Determine output
        if output_path:
            output_file = Path(output_path)
            await _ensure_screenshot_dir(str(output_file))
        elif copy_to_clipboard:
            output_file = None
        else:
            # Default: save to screenshots directory
            screenshots_dir = await _ensure_screenshot_dir()
            output_file = screenshots_dir / _generate_filename("fullscreen")
        
        # Take screenshot (no -w flag for full screen)
        if output_file:
            returncode, stdout, stderr = await _execute_command([
                grim_cmd, str(output_file)
            ])
            
            if returncode == 0:
                result = {
                    "success": True,
                    "output_path": str(output_file),
                    "timestamp": datetime.now().isoformat()
                }
                
                # Also copy to clipboard if requested
                if copy_to_clipboard and _check_tool_available("wl-copy"):
                    process = await asyncio.create_subprocess_exec(
                        grim_cmd, '-',
                        stdout=asyncio.subprocess.PIPE
                    )
                    screenshot_data, _ = await process.communicate()
                    
                    if process.returncode == 0:
                        process2 = await asyncio.create_subprocess_exec(
                            'wl-copy', '--type', 'image/png',
                            stdin=asyncio.subprocess.PIPE
                        )
                        await process2.communicate(input=screenshot_data)
                        result["copied_to_clipboard"] = True
                
                return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": False, "data": result}
            else:
                result = {
                    "success": False,
                    "error": f"Screenshot failed: {stderr.decode()}"
                }
                return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        else:
            # Copy to clipboard only
            if not _check_tool_available("wl-copy"):
                result = {
                    "success": False,
                    "error": "wl-copy not found. Please install wl-clipboard."
                }
                return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
            
            process1 = await asyncio.create_subprocess_exec(
                grim_cmd, '-',
                stdout=asyncio.subprocess.PIPE
            )
            screenshot_data, _ = await process1.communicate()
            
            if process1.returncode == 0:
                process2 = await asyncio.create_subprocess_exec(
                    'wl-copy', '--type', 'image/png',
                    stdin=asyncio.subprocess.PIPE
                )
                await process2.communicate(input=screenshot_data)
                
                if process2.returncode == 0:
                    result = {
                        "success": True,
                        "copied_to_clipboard": True,
                        "timestamp": datetime.now().isoformat()
                    }
                    return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": False, "data": result}
            
            result = {
                "success": False,
                "error": "Failed to copy screenshot to clipboard"
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
            
    except Exception as e:
        logger.error(f"Error taking full screen screenshot: {e}")
        result = {
            "success": False,
            "error": str(e)
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


@tool(
    name="screenshot_hyprland_workspace",
    description="Take screenshots of all windows in a specific workspace. Returns paths to all captured screenshots.",
    input_schema={
        "type": "object",
        "properties": {
            "workspace_id": {
                "type": "integer",
                "description": "The numeric ID of the workspace (e.g., 1, 2)."
            },
            "output_dir": {
                "type": "string",
                "description": "Optional directory path to store the screenshots. If not provided, creates a sub-directory in ~/screenshots."
            }
        },
        "required": ["workspace_id"]
    }
)
async def screenshot_hyprland_workspace(args: dict) -> Dict:
    """Screenshot all windows in a workspace"""
    workspace_id = (args or {}).get("workspace_id")
    output_dir = (args or {}).get("output_dir")
    if workspace_id is None:
        result = {"success": False, "error": "workspace_id is required"}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
    try:
        # Get all clients in workspace
        clients_result = await get_hyprland_clients_by_workspace({"workspace_id": workspace_id})
        
        if not clients_result.get("data", {}).get("success") and not clients_result.get("success"):
            # If downstream returns SDK-style dict, handle accordingly
            data = clients_result.get("data", clients_result)
            result = {
                "success": False,
                "error": data.get("error", f"No windows found in workspace {workspace_id}"),
                "workspace_id": workspace_id
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        clients = clients_result.get("data", {}).get("clients") or clients_result.get("clients", [])
        count = clients_result.get("data", {}).get("count") or clients_result.get("count", 0)
        if count == 0:
            result = {
                "success": False,
                "error": f"No windows found in workspace {workspace_id}",
                "workspace_id": workspace_id
            }
            return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}
        
        # Determine output directory
        if output_dir:
            output_directory = Path(output_dir)
        else:
            screenshots_dir = await _ensure_screenshot_dir()
            output_directory = screenshots_dir / f"workspace_{workspace_id}"
        
        output_directory.mkdir(parents=True, exist_ok=True)
        
        # Screenshot each client
        results = []
        for client in clients:
            address = client.get("address", "")
            class_name = client.get("class", "")
            
            # Generate filename based on class and timestamp
            safe_class = "".join(c if c.isalnum() or c in ('-', '_') else '_' for c in class_name)
            filename = f"ws{workspace_id}_{safe_class}_{datetime.now().strftime('%H%M%S')}.png"
            output_path = output_directory / filename
            
            result = await screenshot_hyprland_client({
                "address": address,
                "output_path": str(output_path),
                "copy_to_clipboard": False
            })
            results.append({
                "address": address,
                "class": class_name,
                "title": client.get("title", ""),
                "result": result
            })
        
        successful = sum(1 for r in results if r["result"].get("data", {}).get("success", r["result"].get("success", False)))
        
        result = {
            "success": True,
            "workspace_id": workspace_id,
            "output_dir": str(output_directory),
            "screenshots": results,
            "total": len(results),
            "successful": successful,
            "timestamp": datetime.now().isoformat()
        }
        
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": False, "data": result}
        
    except Exception as e:
        logger.error(f"Error taking workspace screenshots: {e}")
        result = {
            "success": False,
            "error": str(e),
            "workspace_id": workspace_id
        }
        return {"content": [{"type": "text", "text": json.dumps(result)}], "is_error": True, "data": result}


# Export all tools
HYPRLAND_SS_CTX_TOOLS = [
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
]
