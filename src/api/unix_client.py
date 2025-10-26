"""
Unix socket client for communicating with Hypr-Voice
"""

import socket
import json
import asyncio
import time
from typing import Optional, Dict, Any
from pathlib import Path
from loguru import logger


class UnixSocketClient:
    """Client for communicating with Hypr-Voice via Unix socket"""

    def __init__(self, socket_path: str = "/tmp/hypr-voice.sock"):
        self.socket_path = socket_path
        self.timeout = 5.0  # Default timeout

    def _create_socket(self) -> socket.socket:
        """Create and configure Unix socket"""
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        return sock

    def send_command(self, command: str, timeout: Optional[float] = None) -> Optional[str]:
        """Send command to Unix socket and return response"""
        if timeout:
            self.timeout = timeout

        try:
            # Check if socket file exists
            if not Path(self.socket_path).exists():
                logger.error(f"Socket file does not exist: {self.socket_path}")
                return None

            sock = self._create_socket()
            sock.connect(self.socket_path)

            # Send command
            sock.sendall(command.encode('utf-8'))

            # Receive response (only for status commands)
            response = None
            if command.upper() == "STATUS":
                try:
                    response = sock.recv(4096).decode('utf-8', errors='ignore')
                except socket.timeout:
                    logger.warning("Timeout waiting for STATUS response")
                    response = None
                except Exception as e:
                    logger.warning(f"Error receiving STATUS response: {e}")
                    response = None

            sock.close()
            logger.debug(f"Sent command '{command}' to {self.socket_path}")
            return response

        except socket.timeout:
            logger.error(f"Timeout connecting to socket: {self.socket_path}")
            return None
        except ConnectionRefusedError:
            logger.error(f"Connection refused to socket: {self.socket_path}")
            return None
        except Exception as e:
            logger.error(f"Error sending command '{command}' to socket: {e}")
            return None

    def send_command_async(self, command: str, timeout: Optional[float] = None) -> Optional[str]:
        """Async version of send_command"""
        loop = asyncio.get_event_loop()
        return loop.run_in_executor(None, self.send_command, command, timeout)

    def check_connection(self) -> bool:
        """Check if socket connection is available"""
        try:
            if not Path(self.socket_path).exists():
                return False

            sock = self._create_socket()
            sock.connect(self.socket_path)
            sock.close()
            return True
        except:
            return False

    def get_status(self) -> Optional[Dict[str, Any]]:
        """Get current status from Hypr-Voice"""
        response = self.send_command("STATUS", timeout=2.0)
        if response:
            try:
                return json.loads(response)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse status response: {e}")
                return None
        return None

    def start_recording(self, mode: str = "raw") -> bool:
        """Start recording"""
        if mode.lower() == "enhanced":
            command = "START_ENHANCED"
        else:
            command = "START"

        response = self.send_command(command, timeout=1.0)
        if response:
            return response.strip().upper() == "OK"
        return False

    def stop_recording(self) -> bool:
        """Stop recording"""
        response = self.send_command("STOP", timeout=1.0)
        if response:
            return response.strip().upper() == "OK"
        return False

    def force_stop_recording(self) -> bool:
        """Force stop recording"""
        response = self.send_command("FORCE_STOP", timeout=1.0)
        if response:
            return response.strip().upper() == "OK"
        return False

    def is_recording(self) -> bool:
        """Check if currently recording"""
        status = self.get_status()
        if status:
            return status.get("state", "").lower() == "recording"
        return False


class ProcessManager:
    """Manager for Hypr-Voice server processes"""

    def __init__(self):
        self.process_name = "hypr-voice"
        self.script_path = None

    def _find_script_path(self) -> Optional[Path]:
        """Find the Hypr-Voice main script"""
        possible_paths = [
            Path(__file__).parent.parent.parent / "hypr-voice" / "src" / "core" / "hypr_voice.py",
            Path(__file__).parent.parent.parent / "hypr-voice" / "src" / "core" / "hypr_voice.py",
            Path("/usr/local/bin/hypr-voice"),
            Path.home() / ".local" / "bin" / "hypr-voice"
        ]

        for path in possible_paths:
            if path.exists():
                return path

        return None

    def is_running(self) -> bool:
        """Check if Hypr-Voice server is running"""
        try:
            import subprocess
            result = subprocess.run(
                ["pgrep", "-f", self.process_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0 and result.stdout.strip()
        except Exception as e:
            logger.error(f"Error checking if server is running: {e}")
            return False

    def start_server(self) -> bool:
        """Start Hypr-Voice server"""
        if self.is_running():
            logger.info("Hypr-Voice server is already running")
            return True

        script_path = self._find_script_path()
        if not script_path:
            logger.error("Could not find Hypr-Voice script")
            return False

        try:
            import subprocess
            # Start in background with push-to-talk mode
            subprocess.Popen(
                ["python3", str(script_path), "--push-to-talk"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # Wait a moment for server to start
            time.sleep(2)
            return self.is_running()

        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False

    def stop_server(self) -> bool:
        """Stop Hypr-Voice server"""
        try:
            import subprocess
            result = subprocess.run(
                ["pkill", "-f", self.process_name],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to stop server: {e}")
            return False

    def restart_server(self) -> bool:
        """Restart Hypr-Voice server"""
        stopped = self.stop_server()
        if stopped:
            time.sleep(1)
            return self.start_server()
        return False

    def get_server_info(self) -> Dict[str, Any]:
        """Get server information"""
        return {
            "running": self.is_running(),
            "script_path": str(self._find_script_path()) if self._find_script_path() else None,
            "process_name": self.process_name
        }