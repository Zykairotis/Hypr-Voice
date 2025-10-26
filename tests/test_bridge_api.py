"""
Test suite for Hypr-Voice Bridge API
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime

# Add the API directory to the path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "api"))

from main import app
from models import RecordingMode, LogType, LogLevel
from unix_client import UnixSocketClient, ProcessManager

# Test client
client = TestClient(app)

class TestRecordingEndpoints:
    """Test recording control endpoints"""

    @patch('main.socket_client')
    def test_start_recording_success(self, mock_socket_client):
        """Test successful recording start"""
        mock_socket_client.is_recording.return_value = False
        mock_socket_client.start_recording.return_value = True

        response = client.post("/api/recording/start", json={"mode": "raw"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Recording started" in data["message"]
        mock_socket_client.start_recording.assert_called_once_with("raw")

    @patch('main.socket_client')
    def test_start_recording_already_recording(self, mock_socket_client):
        """Test start recording when already recording"""
        mock_socket_client.is_recording.return_value = True

        response = client.post("/api/recording/start")

        assert response.status_code == 409
        assert "Already recording" in response.json()["detail"]

    @patch('main.socket_client')
    def test_start_enhanced_recording(self, mock_socket_client):
        """Test enhanced recording start"""
        mock_socket_client.is_recording.return_value = False
        mock_socket_client.start_recording.return_value = True

        response = client.post("/api/recording/enhanced", json={"context": {"app": "vscode"}})

        assert response.status_code == 200
        mock_socket_client.start_recording.assert_called_once_with("enhanced")

    @patch('main.socket_client')
    def test_stop_recording_success(self, mock_socket_client):
        """Test successful recording stop"""
        mock_socket_client.is_recording.return_value = True
        mock_socket_client.stop_recording.return_value = True

        response = client.post("/api/recording/stop")

        assert response.status_code == 200
        assert "Recording stopped" in response.json()["message"]
        mock_socket_client.stop_recording.assert_called_once()

    @patch('main.socket_client')
    def test_stop_recording_not_recording(self, mock_socket_client):
        """Test stop recording when not recording"""
        mock_socket_client.is_recording.return_value = False

        response = client.post("/api/recording/stop")

        assert response.status_code == 409
        assert "Not currently recording" in response.json()["detail"]

    @patch('main.socket_client')
    def test_force_stop_recording(self, mock_socket_client):
        """Test force stop recording"""
        mock_socket_client.force_stop_recording.return_value = True

        response = client.post("/api/recording/force-stop")

        assert response.status_code == 200
        assert "Recording force-stopped" in response.json()["message"]
        mock_socket_client.force_stop_recording.assert_called_once()

    @patch('main.socket_client')
    def test_get_recording_status(self, mock_socket_client):
        """Test get recording status"""
        mock_socket_client.get_status.return_value = {
            "state": "recording",
            "device": "GA102",
            "recording_chunks": 42,
            "total_frames": 86016
        }

        response = client.get("/api/recording/status")

        assert response.status_code == 200
        data = response.json()
        assert data["is_recording"] is True
        assert data["status"] == "recording"
        assert data["device_name"] == "GA102"
        assert data["audio_chunks"] == 42

    @patch('main.socket_client')
    def test_get_recording_status_service_unavailable(self, mock_socket_client):
        """Test get recording status when service unavailable"""
        mock_socket_client.get_status.return_value = None
        mock_socket_client.check_connection.return_value = False

        response = client.get("/api/recording/status")

        assert response.status_code == 503
        assert "Service not running" in response.json()["detail"]


class TestServerEndpoints:
    """Test server management endpoints"""

    @patch('main.process_manager')
    def test_start_server_success(self, mock_process_manager):
        """Test successful server start"""
        mock_process_manager.start_server.return_value = True

        response = client.post("/api/server/start")

        assert response.status_code == 200
        assert "Server started successfully" in response.json()["message"]
        mock_process_manager.start_server.assert_called_once()

    @patch('main.process_manager')
    def test_start_server_failure(self, mock_process_manager):
        """Test server start failure"""
        mock_process_manager.start_server.return_value = False

        response = client.post("/api/server/start")

        assert response.status_code == 500
        assert "Failed to start server" in response.json()["detail"]

    @patch('main.process_manager')
    def test_stop_server(self, mock_process_manager):
        """Test server stop"""
        mock_process_manager.stop_server.return_value = True

        response = client.post("/api/server/stop")

        assert response.status_code == 200
        assert "Server stopped successfully" in response.json()["message"]

    @patch('main.process_manager')
    def test_restart_server(self, mock_process_manager):
        """Test server restart"""
        mock_process_manager.restart_server.return_value = True

        response = client.post("/api/server/restart")

        assert response.status_code == 200
        assert "Server restarted successfully" in response.json()["message"]

    @patch('main.process_manager')
    @patch('main.psutil')
    def test_get_server_status(self, mock_psutil, mock_process_manager):
        """Test get server status"""
        mock_process_manager.get_server_info.return_value = {
            "running": True,
            "script_path": "/path/to/hypr_voice.py",
            "process_name": "hypr-voice"
        }

        mock_process = Mock()
        mock_process.memory_info.return_value.rss = 1024 * 1024 * 50  # 50MB
        mock_process.cpu_percent.return_value = 2.5
        mock_psutil.Process.return_value = mock_process

        response = client.get("/api/server/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["memory_usage_mb"] == 50.0
        assert data["active_connections"] == 0  # log_streamer.get_subscription_count()


class TestConfigEndpoints:
    """Test configuration management endpoints"""

    @patch('main.config_manager')
    def test_get_config_success(self, mock_config_manager):
        """Test successful config get"""
        mock_config_manager.get_config.return_value = {
            "quality": {
                "sample_rate": 48000,
                "channels": 1
            }
        }

        response = client.get("/api/config/audio")

        assert response.status_code == 200
        data = response.json()
        assert data["section"] == "audio"
        assert data["config_data"]["quality"]["sample_rate"] == 48000
        assert data["valid"] is True

    @patch('main.config_manager')
    def test_get_config_not_found(self, mock_config_manager):
        """Test get config section not found"""
        mock_config_manager.get_config.return_value = None

        response = client.get("/api/config/nonexistent")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('main.config_manager')
    def test_update_config_success(self, mock_config_manager):
        """Test successful config update"""
        mock_config_manager.update_config.return_value = (True, [])
        mock_config_manager.get_config.return_value = {
            "quality": {
                "sample_rate": 44100,
                "channels": 1
            }
        }

        update_data = {
            "section": "audio",
            "config_data": {"quality": {"sample_rate": 44100}},
            "validate": True
        }

        response = client.put("/api/config/audio", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["section"] == "audio"
        assert data["config_data"]["quality"]["sample_rate"] == 44100
        assert data["valid"] is True

    @patch('main.config_manager')
    def test_update_config_validation_error(self, mock_config_manager):
        """Test config update with validation error"""
        mock_config_manager.update_config.return_value = (False, ["Invalid sample rate"])

        update_data = {
            "section": "audio",
            "config_data": {"quality": {"sample_rate": 1000}},
            "validate": True
        }

        response = client.put("/api/config/audio", json=update_data)

        assert response.status_code == 400
        error_detail = response.json()["detail"]
        assert "validation failed" in error_detail["message"]
        assert "Invalid sample rate" in error_detail["errors"]


class TestWebSocketEndpoint:
    """Test WebSocket log streaming"""

    def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        with client.websocket_connect("/api/logs/stream?type=all&level=info") as websocket:
            # Test that connection is established
            assert websocket is not None

    @patch('main.log_streamer')
    def test_websocket_subscription(self, mock_log_streamer):
        """Test WebSocket subscription process"""
        mock_log_streamer.subscribe.return_value = "test_subscription_id"
        mock_log_streamer.unsubscribe.return_value = None

        with client.websocket_connect("/api/logs/stream") as websocket:
            # Connection established
            pass

        # Verify subscribe was called
        mock_log_streamer.subscribe.assert_called_once()

    @patch('main.log_streamer')
    async def test_websocket_message_format(self, mock_log_streamer):
        """Test WebSocket message format"""
        # This would require more complex async testing setup
        pass


class TestLogEndpoints:
    """Test log retrieval endpoints"""

    @patch('main.log_streamer')
    @pytest.mark.asyncio
    async def test_get_recent_logs(self, mock_log_streamer):
        """Test get recent logs"""
        from models import LogEntry, LogLevel

        mock_log_entries = [
            LogEntry(
                timestamp=datetime.now(),
                level=LogLevel.INFO,
                message="Test log message",
                source="agent"
            )
        ]
        mock_log_streamer.get_recent_logs.return_value = mock_log_entries

        # Note: This test would need to be adapted for async endpoint testing
        # In a real scenario, you'd use TestClient with async support or
        # call the endpoint function directly


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_healthy(self):
        """Test health check when all services are healthy"""
        with patch('main.socket_client.check_connection', return_value=True), \
             patch('main.log_streamer.running', True):

            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["services"]["socket_client"] is True
            assert data["services"]["log_streamer"] is True

    def test_health_check_degraded(self):
        """Test health check when some services are degraded"""
        with patch('main.socket_client.check_connection', return_value=False), \
             patch('main.log_streamer.running', True):

            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "degraded"
            assert data["services"]["socket_client"] is False


class TestErrorHandling:
    """Test error handling"""

    def test_invalid_recording_mode(self):
        """Test invalid recording mode in request"""
        response = client.post("/api/recording/start", json={"mode": "invalid"})

        # Should be handled by Pydantic validation
        assert response.status_code == 422

    def test_invalid_log_type(self):
        """Test invalid log type parameter"""
        response = client.get("/api/logs/invalid/recent")

        assert response.status_code == 400
        assert "Invalid log type" in response.json()["detail"]

    def test_invalid_config_section(self):
        """Test section mismatch in config update"""
        update_data = {
            "section": "audio",
            "config_data": {},
            "validate": True
        }

        response = client.put("/api/config/different_section", json=update_data)

        assert response.status_code == 400
        assert "Section mismatch" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])