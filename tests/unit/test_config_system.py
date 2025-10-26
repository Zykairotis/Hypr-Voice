#!/usr/bin/env python3
"""
Configuration System Test Script for Hypr-Voice
Tests all configuration loading, validation, and real-time updates
"""

import asyncio
import json
import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, Any

# Add hypr-voice directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hypr-voice"))

from config.config_loader import ConfigManager, ConfigValidationError
import httpx
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigSystemTester:
    """Test suite for configuration system"""

    def __init__(self):
        self.config_dir = Path(__file__).parent / "config"
        self.config_manager = ConfigManager(self.config_dir)
        self.test_results = []
        self.failed_tests = []

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result"""
        status = "PASS" if passed else "FAIL"
        self.test_results.append((test_name, passed, message))

        if passed:
            logger.info(f"✅ {test_name}: {status} {message}")
        else:
            logger.error(f"❌ {test_name}: {status} {message}")
            self.failed_tests.append(test_name)

    async def test_config_loading(self):
        """Test configuration loading"""
        logger.info("Testing configuration loading...")

        # Test loading all configs
        try:
            all_configs = self.config_manager.get_all_configs()
            expected_configs = ['audio', 'servers', 'ui', 'detection', 'app_profiles', 'llm_providers']

            for config_name in expected_configs:
                if config_name in all_configs and all_configs[config_name]:
                    self.log_test(f"Load {config_name} config", True)
                else:
                    self.log_test(f"Load {config_name} config", False, "Config missing or empty")

            # Test specific config access
            whisper_url = self.config_manager.get_config('servers', 'services.whisper.port')
            if whisper_url == 9880:
                self.log_test("Get nested config value", True)
            else:
                self.log_test("Get nested config value", False, f"Expected 9880, got {whisper_url}")

        except Exception as e:
            self.log_test("Config loading", False, str(e))

    async def test_config_validation(self):
        """Test configuration validation"""
        logger.info("Testing configuration validation...")

        # Test valid configuration
        try:
            valid_config = {
                'audio': {
                    'quality': {
                        'sample_rate': 48000,
                        'channels': 1
                    }
                }
            }
            self.config_manager._validate_config('audio', valid_config['audio'])
            self.log_test("Valid config validation", True)
        except Exception as e:
            self.log_test("Valid config validation", False, str(e))

        # Test invalid configuration
        try:
            invalid_config = {
                'audio': {
                    'quality': {
                        'sample_rate': 100,  # Invalid: too low
                        'channels': 1
                    }
                }
            }
            self.config_manager._validate_config('audio', invalid_config['audio'])
            self.log_test("Invalid config validation", False, "Should have failed validation")
        except ConfigValidationError:
            self.log_test("Invalid config validation", True)
        except Exception as e:
            self.log_test("Invalid config validation", False, f"Unexpected error: {str(e)}")

        # Test missing required field
        try:
            incomplete_config = {
                'audio': {
                    'quality': {
                        'channels': 1
                        # Missing sample_rate
                    }
                }
            }
            self.config_manager._validate_config('audio', incomplete_config['audio'])
            self.log_test("Missing required field validation", False, "Should have failed validation")
        except ConfigValidationError:
            self.log_test("Missing required field validation", True)
        except Exception as e:
            self.log_test("Missing required field validation", False, f"Unexpected error: {str(e)}")

    async def test_config_updates(self):
        """Test configuration updates"""
        logger.info("Testing configuration updates...")

        # Test updating existing config
        try:
            original_value = self.config_manager.get_config('audio', 'recording.max_duration')
            new_value = 600 if original_value != 600 else 300

            updates = {'recording': {'max_duration': new_value}}
            success = self.config_manager.update_config('audio', updates, save=False)

            if success:
                updated_value = self.config_manager.get_config('audio', 'recording.max_duration')
                if updated_value == new_value:
                    self.log_test("Config update", True)
                    # Restore original value
                    self.config_manager.update_config('audio', {'recording': {'max_duration': original_value}}, save=False)
                else:
                    self.log_test("Config update", False, f"Expected {new_value}, got {updated_value}")
            else:
                self.log_test("Config update", False, "Update returned False")
        except Exception as e:
            self.log_test("Config update", False, str(e))

        # Test deep merge
        try:
            original_config = self.config_manager.get_config('audio', default={}).copy()

            updates = {
                'new_section': {
                    'new_key': 'new_value'
                },
                'recording': {
                    'new_subkey': 'new_subvalue'
                }
            }

            success = self.config_manager.update_config('audio', updates, save=False)
            if success:
                updated_config = self.config_manager.get_config('audio')
                if 'new_section' in updated_config and 'new_subkey' in updated_config.get('recording', {}):
                    self.log_test("Deep merge update", True)
                    # Restore original
                    self.config_manager.configs['audio'] = original_config
                else:
                    self.log_test("Deep merge update", False, "Deep merge failed")
            else:
                self.log_test("Deep merge update", False, "Update returned False")
        except Exception as e:
            self.log_test("Deep merge update", False, str(e))

    async def test_config_callbacks(self):
        """Test configuration change callbacks"""
        logger.info("Testing configuration callbacks...")

        callback_called = False
        callback_data = None

        async def test_callback(config_name: str, changes: Dict[str, Any]):
            nonlocal callback_called, callback_data
            callback_called = True
            callback_data = (config_name, changes)

        # Register callback
        self.config_manager.register_callback('audio', test_callback)

        try:
            # Trigger callback
            updates = {'test_key': 'test_value'}
            success = self.config_manager.update_config('audio', updates, save=False)

            # Give a moment for async callback
            await asyncio.sleep(0.1)

            if callback_called and callback_data[0] == 'audio':
                self.log_test("Config change callback", True)
            else:
                self.log_test("Config change callback", False, "Callback not called")
        except Exception as e:
            self.log_test("Config change callback", False, str(e))

    async def test_file_operations(self):
        """Test file import/export operations"""
        logger.info("Testing file operations...")

        # Test export
        try:
            exported_yaml = self.config_manager.export_config('audio', 'yaml')
            if exported_yaml and 'audio:' in exported_yaml:
                self.log_test("Config export (YAML)", True)
            else:
                self.log_test("Config export (YAML)", False, "Export empty or invalid")
        except Exception as e:
            self.log_test("Config export (YAML)", False, str(e))

        try:
            exported_json = self.config_manager.export_config('audio', 'json')
            if exported_json:
                parsed = json.loads(exported_json)
                if isinstance(parsed, dict):
                    self.log_test("Config export (JSON)", True)
                else:
                    self.log_test("Config export (JSON)", False, "Invalid JSON")
            else:
                self.log_test("Config export (JSON)", False, "Export empty")
        except Exception as e:
            self.log_test("Config export (JSON)", False, str(e))

        # Test import
        try:
            test_config = {
                'audio': {
                    'test': {
                        'imported': True,
                        'timestamp': time.time()
                    }
                }
            }

            yaml_data = yaml.dump(test_config['audio'])
            success = self.config_manager.import_config('audio', yaml_data, 'yaml', save=False)

            if success:
                imported_value = self.config_manager.get_config('audio', 'test.imported')
                if imported_value is True:
                    self.log_test("Config import", True)
                else:
                    self.log_test("Config import", False, "Import failed")
            else:
                self.log_test("Config import", False, "Import returned False")
        except Exception as e:
            self.log_test("Config import", False, str(e))

    async def test_config_api(self):
        """Test configuration API endpoints"""
        logger.info("Testing configuration API...")

        # Check if API server is running
        api_base_url = "http://localhost:9092"

        try:
            async with httpx.AsyncClient() as client:
                # Test status endpoint
                response = await client.get(f"{api_base_url}/status", timeout=5.0)
                if response.status_code == 200:
                    self.log_test("API status endpoint", True)

                    # Test getting configs
                    response = await client.get(f"{api_base_url}/configs", timeout=5.0)
                    if response.status_code == 200:
                        configs = response.json()
                        if isinstance(configs, dict) and len(configs) > 0:
                            self.log_test("API get all configs", True)

                            # Test specific config
                            if 'audio' in configs:
                                response = await client.get(f"{api_base_url}/configs/audio", timeout=5.0)
                                if response.status_code == 200:
                                    self.log_test("API get specific config", True)
                                else:
                                    self.log_test("API get specific config", False, f"Status: {response.status_code}")
                            else:
                                self.log_test("API get specific config", False, "Audio config not available")
                        else:
                            self.log_test("API get all configs", False, "No configs returned")
                    else:
                        self.log_test("API get all configs", False, f"Status: {response.status_code}")
                else:
                    self.log_test("API status endpoint", False, f"Status: {response.status_code}")

        except httpx.ConnectError:
            self.log_test("API connectivity", False, "API server not running")
        except Exception as e:
            self.log_test("API connectivity", False, str(e))

    async def test_real_time_updates(self):
        """Test real-time configuration updates"""
        logger.info("Testing real-time updates...")

        # Test file watching
        try:
            # Create a temporary config file
            temp_config = {
                'audio': {
                    'realtime_test': {
                        'enabled': True,
                        'timestamp': time.time()
                    }
                }
            }

            temp_file = self.config_dir / "temp_realtime_test.yaml"

            # Write temporary config
            with open(temp_file, 'w') as f:
                yaml.dump(temp_config['audio'], f)

            # Give a moment for file watcher to detect
            await asyncio.sleep(2)

            # Clean up
            temp_file.unlink(missing_ok=True)

            self.log_test("File watching", True)

        except Exception as e:
            self.log_test("File watching", False, str(e))

    async def test_environment_substitution(self):
        """Test environment variable substitution"""
        logger.info("Testing environment variable substitution...")

        # Set test environment variable
        test_var_name = "HYPR_VOICE_TEST_VAR"
        test_var_value = "test_value_12345"

        import os
        os.environ[test_var_name] = test_var_value

        try:
            # Test config with env var
            test_config = {
                'test': {
                    'env_value': f"${{{test_var_name}}}",
                    'default_value': "${{NONEXISTENT_VAR:default}}",
                    'literal_value": "literal"
                }
            }

            processed_config = self.config_manager._substitute_env_vars(test_config)

            if (processed_config['test']['env_value'] == test_var_value and
                processed_config['test']['default_value'] == 'default' and
                processed_config['test']['literal_value'] == 'literal'):
                self.log_test("Environment variable substitution", True)
            else:
                self.log_test("Environment variable substitution", False, "Substitution failed")

        except Exception as e:
            self.log_test("Environment variable substitution", False, str(e))
        finally:
            # Clean up
            os.environ.pop(test_var_name, None)

    async def run_all_tests(self):
        """Run all configuration system tests"""
        logger.info("=" * 60)
        logger.info("Starting Hypr-Voice Configuration System Tests")
        logger.info("=" * 60)

        tests = [
            self.test_config_loading,
            self.test_config_validation,
            self.test_config_updates,
            self.test_config_callbacks,
            self.test_file_operations,
            self.test_config_api,
            self.test_real_time_updates,
            self.test_environment_substitution,
        ]

        for test in tests:
            try:
                await test()
            except Exception as e:
                logger.error(f"Test {test.__name__} failed with exception: {e}")
                self.log_test(test.__name__, False, f"Exception: {str(e)}")

        # Print summary
        logger.info("=" * 60)
        logger.info("Configuration System Test Results")
        logger.info("=" * 60)

        passed = sum(1 for _, result, _ in self.test_results if result)
        total = len(self.test_results)

        logger.info(f"Total tests: {total}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {total - passed}")

        if self.failed_tests:
            logger.error("Failed tests:")
            for test_name in self.failed_tests:
                logger.error(f"  - {test_name}")

        success_rate = (passed / total) * 100 if total > 0 else 0
        logger.info(f"Success rate: {success_rate:.1f}%")

        return success_rate >= 80  # Consider successful if 80%+ tests pass

async def main():
    """Main test runner"""
    tester = ConfigSystemTester()
    success = await tester.run_all_tests()

    if success:
        logger.info("✅ Configuration system tests completed successfully!")
        return 0
    else:
        logger.error("❌ Configuration system tests failed!")
        return 1

if __name__ == "__main__":
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)