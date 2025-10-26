#!/usr/bin/env python3
"""
Hypr-Voice System Test Script
Tests all major components to ensure proper setup
"""

import asyncio
import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, Tuple

# Add hypr-voice directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "hypr-voice"))

# Color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(message: str, status: str = "INFO"):
    """Print colored status message"""
    color = Colors.BLUE
    if status == "SUCCESS":
        color = Colors.GREEN
    elif status == "WARNING":
        color = Colors.YELLOW
    elif status == "ERROR":
        color = Colors.RED
    
    print(f"{color}[{status}]{Colors.ENDC} {message}")

def check_command(cmd: str) -> bool:
    """Check if a command exists"""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0

def check_python_import(module: str) -> bool:
    """Check if a Python module can be imported"""
    try:
        __import__(module)
        return True
    except ImportError:
        return False

def check_service(host: str, port: int) -> bool:
    """Check if a service is running on host:port"""
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

async def test_ollama() -> Tuple[bool, str]:
    """Test Ollama connectivity"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                return True, f"Available models: {', '.join(model_names) if model_names else 'None'}"
            return False, f"Ollama API returned status {response.status_code}"
    except Exception as e:
        return False, str(e)

async def test_whisper_server() -> Tuple[bool, str]:
    """Test Whisper server connectivity"""
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:9880/sessions")
            if response.status_code == 200:
                return True, "Whisper server is running"
            return False, f"Whisper server returned status {response.status_code}"
    except Exception as e:
        return False, str(e)

async def test_context_engine() -> Tuple[bool, str]:
    """Test Context Engine initialization"""
    try:
        # Use Cognee-based context engine
        from context_engine_cognee import CogneeContextEngine as ContextEngine
        engine = ContextEngine()
        # Try to load profiles
        profiles = engine.get_profiles()
        if profiles:
            return True, f"Loaded {len(profiles)} application profiles (Cognee)"
        return True, "Cognee Context Engine initialized (no profiles found)"
    except Exception as e:
        return False, f"Failed to init Cognee. Check env vars (Voyage/LanceDB keys?). Error: {e}"

async def test_audio_devices() -> Tuple[bool, str]:
    """Test audio device availability"""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        if input_devices:
            return True, f"Found {len(input_devices)} input devices"
        return False, "No input audio devices found"
    except Exception as e:
        return False, str(e)

async def test_hyprland() -> Tuple[bool, str]:
    """Test Hyprland integration"""
    try:
        result = subprocess.run(
            ["hyprctl", "activewindow", "-j"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            window = json.loads(result.stdout)
            return True, f"Active window: {window.get('class', 'Unknown')}"
        return False, "hyprctl command failed"
    except FileNotFoundError:
        return False, "hyprctl not found (Hyprland not installed?)"
    except Exception as e:
        return False, str(e)

async def test_clipboard() -> Tuple[bool, str]:
    """Test clipboard functionality"""
    try:
        # Test wl-copy
        result2 = subprocess.run(["wl-copy"], input=b"test")
        if result2.returncode == 0:
            return True, "Wayland clipboard (wl-copy) is working"
        return False, "wl-copy failed"
    except FileNotFoundError:
        return False, "wl-copy not found"
    except Exception as e:
        return False, str(e)

async def main():
    """Run all system tests"""
    print(f"\n{Colors.BOLD}{'='*50}")
    print("       Hypr-Voice System Test")
    print(f"{'='*50}{Colors.ENDC}\n")
    
    # Check system commands
    print(f"{Colors.BOLD}System Commands:{Colors.ENDC}")
    commands = {
        "python3": "Python interpreter",
        "ffmpeg": "Audio processing",
        "sox": "Audio manipulation", 
        "wl-copy": "Wayland clipboard",
        "notify-send": "Desktop notifications",
        "hyprctl": "Hyprland control",
        "ollama": "Local LLM",
        "redis-cli": "Redis client"
    }
    
    for cmd, desc in commands.items():
        if check_command(cmd):
            print_status(f"✓ {cmd}: {desc}", "SUCCESS")
        else:
            print_status(f"✗ {cmd}: {desc} (not found)", "WARNING")
    
    print()
    
    # Check Python modules
    print(f"{Colors.BOLD}Python Modules:{Colors.ENDC}")
    modules = {
        "sounddevice": "Audio capture",
        "numpy": "Numerical computing",
        "faster_whisper": "Whisper transcription",
        "langchain": "LLM framework",
        "cognee": "Knowledge graph memory",
        "lancedb": "Vector database",
        "pydantic": "Data validation",
        "rich": "Terminal UI",
        "loguru": "Logging"
    }
    
    for module, desc in modules.items():
        if check_python_import(module):
            print_status(f"✓ {module}: {desc}", "SUCCESS")
        else:
            print_status(f"✗ {module}: {desc} (not installed)", "ERROR")
    
    print()
    
    # Check services
    print(f"{Colors.BOLD}Services:{Colors.ENDC}")
    
    # Redis
    if check_service("localhost", 6379):
        print_status("✓ Redis: Running on port 6379", "SUCCESS")
    else:
        print_status("✗ Redis: Not running (optional)", "WARNING")
    
    # Ollama
    success, message = await test_ollama()
    if success:
        print_status(f"✓ Ollama: {message}", "SUCCESS")
    else:
        print_status(f"✗ Ollama: {message}", "WARNING")
    
    # Whisper Server
    success, message = await test_whisper_server()
    if success:
        print_status(f"✓ Whisper Server: {message}", "SUCCESS")
    else:
        print_status(f"✗ Whisper Server: {message} (start with: python whisper_server.py)", "WARNING")
    
    print()
    
    # Component tests
    print(f"{Colors.BOLD}Components:{Colors.ENDC}")
    
    # Context Engine
    success, message = await test_context_engine()
    if success:
        print_status(f"✓ Context Engine: {message}", "SUCCESS")
    else:
        print_status(f"✗ Context Engine: {message}", "ERROR")
    
    # LanceDB
    if check_python_import('lancedb'):
        print_status("✓ LanceDB: Module is installed", "SUCCESS")
    else:
        print_status("✗ LanceDB: Module is not installed", "ERROR")
    
    # Audio Devices
    success, message = await test_audio_devices()
    if success:
        print_status(f"✓ Audio: {message}", "SUCCESS")
    else:
        print_status(f"✗ Audio: {message}", "ERROR")
    
    # Hyprland
    success, message = await test_hyprland()
    if success:
        print_status(f"✓ Hyprland: {message}", "SUCCESS")
    else:
        print_status(f"✗ Hyprland: {message}", "WARNING")
    
    # Clipboard
    success, message = await test_clipboard()
    if success:
        print_status(f"✓ Clipboard: {message}", "SUCCESS")
    else:
        print_status(f"✗ Clipboard: {message}", "WARNING")
    
    print()
    
    # Check configuration files
    print(f"{Colors.BOLD}Configuration:{Colors.ENDC}")
    script_dir = Path(__file__).parent.parent / "hypr-voice"
    config_files = {
        str(script_dir / "config/app_profiles.yaml"): "Application profiles",
        str(script_dir / "config/llm_providers.yaml"): "LLM provider settings",
        str(script_dir / ".env"): "Environment configuration"
    }
    
    for file, desc in config_files.items():
        if Path(file).exists():
            print_status(f"✓ {file}: {desc}", "SUCCESS")
        else:
            print_status(f"✗ {file}: {desc} (not found)", "WARNING")
    
    print()
    print(f"{Colors.BOLD}{'='*50}{Colors.ENDC}")
    print(f"{Colors.GREEN}System test complete!{Colors.ENDC}")
    print()
    print("Next steps:")
    print("1. Create venv and install deps: python3 -m venv .venv && source .venv/bin/activate && pip install -U pip && pip install -r requirements.txt")
    print("2. Start services:")
    print("   - Redis: sudo systemctl start redis")
    print("   - Ollama: ollama serve")
    print("   - Whisper: python3 whisper_server.py")
    print("3. Run the client: python3 hypr_voice.py --push-to-talk")
    print()

if __name__ == "__main__":
    asyncio.run(main())
