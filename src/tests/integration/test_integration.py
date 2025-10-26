#!/usr/bin/env python3
"""
Integration Test Script for Hypr-Voice Backend
Tests audio monitoring, model detection, WebSocket communication, and API endpoints
"""

import asyncio
import websockets
import json
import requests
import time
import logging
from typing import Dict, Any, List
import threading
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Integration testing for Hypr-Voice backend"""

    def __init__(self):
        self.base_url = "http://localhost:9091"
        self.ws_url = "ws://localhost:9091/ws/monitor"
        self.test_results = []
        self.ws_messages = queue.Queue()

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        result = f"[{status}] {test_name}"
        if message:
            result += f": {message}"
        logger.info(result)
        self.test_results.append({
            'test': test_name,
            'passed': passed,
            'message': message
        })

    async def test_api_endpoints(self):
        """Test all API endpoints"""
        logger.info("Testing API endpoints...")

        # Test system status
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_model = 'model_size' in data and 'device' in data
                self.log_test("System Status API", has_model,
                           f"Model: {data.get('model_size', 'missing')}, Device: {data.get('device', 'missing')}")
            else:
                self.log_test("System Status API", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("System Status API", False, str(e))

        # Test models endpoint
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_models = 'available_models' in data and 'current_model' in data
                self.log_test("Models API", has_models,
                           f"Current: {data.get('current_model', 'missing')}")
            else:
                self.log_test("Models API", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Models API", False, str(e))

        # Test audio devices
        try:
            response = requests.get(f"{self.base_url}/api/audio/devices", timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_devices = 'devices' in data and len(data['devices']) > 0
                self.log_test("Audio Devices API", has_devices,
                           f"Found {len(data.get('devices', []))} devices")
            else:
                self.log_test("Audio Devices API", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Audio Devices API", False, str(e))

        # Test audio status
        try:
            response = requests.get(f"{self.base_url}/api/audio/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_status = data.get('status') == 'success'
                self.log_test("Audio Status API", has_status)
            else:
                self.log_test("Audio Status API", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Audio Status API", False, str(e))

        # Test model status
        try:
            response = requests.get(f"{self.base_url}/api/model/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                has_status = data.get('status') == 'success'
                self.log_test("Model Status API", has_status)
            else:
                self.log_test("Model Status API", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Model Status API", False, str(e))

    async def test_audio_monitoring(self):
        """Test audio monitoring functionality"""
        logger.info("Testing audio monitoring...")

        # Test start audio monitoring
        try:
            response = requests.post(f"{self.base_url}/api/audio/start", timeout=5)
            if response.status_code == 200:
                data = response.json()
                started = data.get('status') == 'success'
                self.log_test("Start Audio Monitoring", started)
            else:
                self.log_test("Start Audio Monitoring", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Start Audio Monitoring", False, str(e))

        # Wait a moment for monitoring to start
        await asyncio.sleep(2)

        # Test audio status after starting
        try:
            response = requests.get(f"{self.base_url}/api/audio/status", timeout=5)
            if response.status_code == 200:
                data = response.json()
                is_monitoring = data.get('audio_monitor', {}).get('is_connected', False)
                self.log_test("Audio Monitoring Active", is_monitoring)
            else:
                self.log_test("Audio Monitoring Active", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Audio Monitoring Active", False, str(e))

        # Test reset peak
        try:
            response = requests.post(f"{self.base_url}/api/audio/reset_peak", timeout=5)
            if response.status_code == 200:
                data = response.json()
                reset = data.get('status') == 'success'
                self.log_test("Reset Audio Peak", reset)
            else:
                self.log_test("Reset Audio Peak", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Reset Audio Peak", False, str(e))

        # Test stop audio monitoring
        try:
            response = requests.post(f"{self.base_url}/api/audio/stop", timeout=5)
            if response.status_code == 200:
                data = response.json()
                stopped = data.get('status') == 'success'
                self.log_test("Stop Audio Monitoring", stopped)
            else:
                self.log_test("Stop Audio Monitoring", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Stop Audio Monitoring", False, str(e))

    async def test_model_management(self):
        """Test model management functionality"""
        logger.info("Testing model management...")

        # Test auto-configure
        try:
            response = requests.post(f"{self.base_url}/api/model/auto_configure", timeout=5)
            if response.status_code == 200:
                data = response.json()
                configured = data.get('status') == 'success'
                self.log_test("Auto-Configure Model", configured)
            else:
                self.log_test("Auto-Configure Model", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Configure Model", False, str(e))

        # Get current model
        current_model = None
        try:
            response = requests.get(f"{self.base_url}/api/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                current_model = data.get('current_model')
                self.log_test("Get Current Model", current_model is not None, f"Model: {current_model}")
            else:
                self.log_test("Get Current Model", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Get Current Model", False, str(e))

        # Test model switch (if we have a current model)
        if current_model:
            try:
                # Try to switch to a different model
                other_models = ['tiny', 'base', 'small', 'medium', 'large']
                other_models.remove(current_model) if current_model in other_models else None
                if other_models:
                    new_model = other_models[0]
                    response = requests.post(f"{self.base_url}/api/model/switch",
                                          json={"model_size": new_model, "device": "auto"}, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        switched = data.get('status') == 'success'
                        self.log_test("Switch Model", switched, f"Switched to {new_model}")
                    else:
                        self.log_test("Switch Model", False, f"Status code: {response.status_code}")
                else:
                    self.log_test("Switch Model", False, "No alternative models available")
            except Exception as e:
                self.log_test("Switch Model", False, str(e))

    async def websocket_listener(self):
        """WebSocket listener for testing"""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                logger.info("WebSocket connected for testing")

                # Send a test message
                await websocket.send("test_connection")

                # Listen for messages
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        self.ws_messages.put(data)
                        logger.info(f"Received WebSocket message: {data.get('type', 'unknown')}")
                    except json.JSONDecodeError:
                        logger.warning(f"Received non-JSON WebSocket message: {message}")

        except Exception as e:
            logger.error(f"WebSocket error: {e}")

    async def test_websocket_communication(self):
        """Test WebSocket communication"""
        logger.info("Testing WebSocket communication...")

        # Start WebSocket listener in background
        ws_task = asyncio.create_task(self.websocket_listener())

        # Wait for connection and some messages
        await asyncio.sleep(5)

        # Check if we received any messages
        messages_received = []
        while not self.ws_messages.empty():
            try:
                messages_received.append(self.ws_messages.get_nowait())
            except queue.Empty:
                break

        # Test different message types
        system_status_received = any(msg.get('type') == 'system_status' for msg in messages_received)
        audio_level_received = any(msg.get('type') == 'audio_level' for msg in messages_received)

        self.log_test("WebSocket Connection", len(messages_received) > 0,
                    f"Received {len(messages_received)} messages")
        self.log_test("WebSocket System Status", system_status_received)
        self.log_test("WebSocket Audio Levels", audio_level_received)

        # Cancel WebSocket task
        ws_task.cancel()
        try:
            await ws_task
        except asyncio.CancelledError:
            pass

    async def test_cors_configuration(self):
        """Test CORS configuration"""
        logger.info("Testing CORS configuration...")

        # Test preflight request
        try:
            response = requests.options(f"{self.base_url}/api/status",
                                      headers={
                                          "Origin": "http://localhost:3001",
                                          "Access-Control-Request-Method": "GET",
                                          "Access-Control-Request-Headers": "Content-Type"
                                      }, timeout=5)

            cors_headers = {
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            }

            has_cors = all(header in response.headers for header in cors_headers)
            self.log_test("CORS Configuration", has_cors,
                        f"CORS headers present: {has_cors}")
        except Exception as e:
            self.log_test("CORS Configuration", False, str(e))

    async def run_all_tests(self):
        """Run all integration tests"""
        logger.info("Starting Hypr-Voice integration tests...")
        logger.info("=" * 50)

        # Test basic connectivity
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            server_running = response.status_code == 200
            self.log_test("Server Connectivity", server_running,
                        f"Server status code: {response.status_code}")
        except Exception as e:
            self.log_test("Server Connectivity", False, str(e))
            return

        # Run all test suites
        await self.test_api_endpoints()
        await self.test_audio_monitoring()
        await self.test_model_management()
        await self.test_websocket_communication()
        await self.test_cors_configuration()

        # Print summary
        self.print_summary()

    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 50)
        logger.info("Integration Test Summary")
        logger.info("=" * 50)

        passed = sum(1 for result in self.test_results if result['passed'])
        total = len(self.test_results)

        for result in self.test_results:
            status = "✓" if result['passed'] else "✗"
            message = f": {result['message']}" if result['message'] else ""
            logger.info(f"{status} {result['test']}{message}")

        logger.info("=" * 50)
        logger.info(f"Tests Passed: {passed}/{total}")

        if passed == total:
            logger.info("🎉 All tests passed! Integration is working correctly.")
        else:
            logger.warning(f"⚠️  {total - passed} tests failed. Check the issues above.")

        logger.info("=" * 50)

async def main():
    """Main function"""
    tester = IntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())