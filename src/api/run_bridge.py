#!/usr/bin/env python3
"""
Startup script for Hypr-Voice Bridge API Service
"""

import sys
import os
import argparse
import asyncio
from pathlib import Path
from loguru import logger

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

def setup_logging():
    """Setup logging configuration"""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import websockets
        import aiofiles
        import yaml
        import psutil
        import loguru
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Dependencies should be installed. Using system Python...")
        # Try to import from system if venv is not active
        import subprocess
        import sys
        try:
            # Use pip from the virtual environment if available
            venv_python = Path(__file__).parent.parent.parent / ".venv" / "bin" / "python3"
            if venv_python.exists():
                logger.info(f"Using virtual environment Python: {venv_python}")
                result = subprocess.run([str(venv_python), "-c", "import fastapi; import uvicorn; import pydantic; import websockets; import aiofiles; import yaml; import psutil; import loguru"],
                                      capture_output=True, text=True)
                return result.returncode == 0
        except Exception:
            pass
        return False

def check_hypr_voice():
    """Check if Hypr-Voice is available"""
    # Check if main script exists
    hypr_voice_path = Path(__file__).parent.parent.parent / "hypr-voice" / "src" / "core" / "hypr_voice.py"
    if hypr_voice_path.exists():
        logger.info(f"Found Hypr-Voice at: {hypr_voice_path}")
        return True

    # Check common installation locations
    possible_paths = [
        Path("/usr/local/bin/hypr-voice"),
        Path.home() / ".local" / "bin" / "hypr-voice"
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Found Hypr-Voice at: {path}")
            return True

    logger.warning("Hypr-Voice installation not found")
    logger.info("The bridge service can run without Hypr-Voice, but functionality will be limited")
    return False

def create_directories():
    """Create necessary directories"""
    directories = [
        "/tmp/hypr-voice-logs",
        "/tmp/hypr-voice-recordings"
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {directory}")

def start_server(host: str = "0.0.0.0", port: int = 8435, reload: bool = False):
    """Start the FastAPI server"""
    import uvicorn
    from main import app

    logger.info(f"Starting Hypr-Voice Bridge API on {host}:{port}")
    logger.info(f"API documentation available at: http://{host}:{port}/docs")
    logger.info(f"WebSocket logs endpoint: ws://{host}:{port}/api/logs/stream")

    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Hypr-Voice Bridge API Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_bridge.py                          # Start with default settings
  python run_bridge.py --host 127.0.0.1         # Listen on localhost only
  python run_bridge.py --port 8080              # Use different port
  python run_bridge.py --reload                  # Enable auto-reload for development
  python run_bridge.py --check                  # Check dependencies and exit
        """
    )

    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind to (default: 0.0.0.0)"
    )

    parser.add_argument(
        "--port",
        type=int,
        default=8435,
        help="Port to bind to (default: 8435)"
    )

    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check dependencies and exit"
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Log level (default: info)"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging()
    logger.remove()  # Remove default to add with specified level
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=args.log_level.upper()
    )

    logger.info("Hypr-Voice Bridge API Service")
    logger.info("=" * 40)

    # Check dependencies
    logger.info("Checking dependencies...")
    if not check_dependencies():
        sys.exit(1)

    # Check Hypr-Voice installation
    logger.info("Checking Hypr-Voice installation...")
    hypr_voice_available = check_hypr_voice()

    # Create necessary directories
    logger.info("Creating directories...")
    create_directories()

    if args.check:
        logger.info("✅ All checks passed")
        if hypr_voice_available:
            logger.info("✅ Hypr-Voice installation found")
        else:
            logger.warning("⚠️  Hypr-Voice installation not found (optional)")
        sys.exit(0)

    # Start server
    try:
        start_server(args.host, args.port, args.reload)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()