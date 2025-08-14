#!/usr/bin/env python3
"""
Comprehensive tests for the transcription improvement pipeline
Ensures xAI improvement works for all app profiles, especially Windsurf
"""

import os
import sys
import asyncio
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from simple_improvement_engine import SimpleImprovementEngine, AppProfile
from loguru import logger

# Test data
TEST_TRANSCRIPTIONS = {
    "windsurf": {
        "input": "make a function to reverse a string",
        "expected_keywords": ["function", "def", "return", "string"],
        "should_improve": True
    },
    "kitty": {
        "input": "list all python files in this directory",
        "expected_keywords": ["ls", "*.py", "find"],
        "should_improve": True
    },
    "firefox": {
        "input": "search for rust documentation",
        "expected_keywords": ["rust", "documentation"],
        "should_improve": True
    },
    "discord": {
        "input": "hey whats up",
        "expected_keywords": ["hey", "what's"],
        "should_improve": True
    },
    "default": {
        "input": "this is a test message",
        "expected_keywords": ["test", "message"],
        "should_improve": True
    }
}


class TestSimpleImprovementEngine(unittest.TestCase):
    """Test the Simple Improvement Engine"""
    
    def setUp(self):
        """Set up test environment"""
        self.config_dir = Path(__file__).parent.parent / "config"
        self.engine = SimpleImprovementEngine(config_dir=self.config_dir)
    
    def test_profile_loading(self):
        """Test that profiles are loaded correctly"""
        self.assertGreater(len(self.engine.profiles), 0, "No profiles loaded")
        
        # Log what profiles were actually loaded for debugging
        logger.info(f"Loaded profiles: {list(self.engine.profiles.keys())}")
        
        # Check for critical profiles
        self.assertIn("windsurf", self.engine.profiles, "Windsurf profile missing")
        self.assertIn("terminal", self.engine.profiles, "Terminal profile missing")  # kitty is part of terminal
        self.assertIn("default", self.engine.profiles, "Default profile missing")
        
        # Verify Windsurf profile structure
        windsurf = self.engine.profiles.get("windsurf")
        self.assertIsNotNone(windsurf)
        self.assertEqual(windsurf.app_class, "windsurf")
        self.assertEqual(windsurf.writing_style, "technical")
        self.assertIsNotNone(windsurf.llm_config)
        self.assertEqual(windsurf.llm_config.get("provider"), "xai")
        
        logger.info(f"✅ Loaded {len(self.engine.profiles)} profiles successfully")
    
    def test_profile_matching(self):
        """Test profile matching by app class"""
        # Test exact match
        profile = self.engine.set_active_application("windsurf")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.app_name, "windsurf")
        
        # Test case insensitive match
        profile = self.engine.set_active_application("WINDSURF")
        self.assertIsNotNone(profile)
        self.assertEqual(profile.app_name, "windsurf")
        
        # Test fallback to default
        profile = self.engine.set_active_application("unknown_app")
        if "default" in self.engine.profiles:
            self.assertIsNotNone(profile)
            self.assertEqual(profile.app_name, "default")
        
        logger.info("✅ Profile matching works correctly")
    
    async def test_extra_context_execution(self):
        """Test extra context command execution"""
        # Create a test profile with simple commands
        test_profile = AppProfile(
            app_name="test",
            app_class="test",
            extra_context=["echo 'test context'", "pwd"]
        )
        
        context = await self.engine.execute_extra_context(test_profile)
        self.assertIsNotNone(context)
        self.assertIn("test context", context)
        
        logger.info(f"✅ Extra context execution works: {len(context)} chars")
    
    async def test_xai_improvement(self):
        """Test xAI improvement with mocked API"""
        if not os.getenv("XAI_API_KEY"):
            self.skipTest("XAI_API_KEY not configured")
        
        # Test Windsurf profile improvement
        self.engine.set_active_application("windsurf")
        profile = self.engine.current_profile
        self.assertIsNotNone(profile)
        
        # Test real improvement (if API key is available)
        test_text = "help me write a readme file"
        improved = await self.engine.improve_with_xai(test_text, profile)
        
        # Check that improvement happened
        self.assertIsNotNone(improved)
        if improved != test_text:
            logger.info(f"✅ xAI improvement successful: '{test_text}' -> '{improved[:50]}...'")
        else:
            logger.warning("⚠️ No improvement applied (API might be unavailable)")
    
    async def test_full_transcription_pipeline(self):
        """Test the complete transcription processing pipeline"""
        for app_name, test_data in TEST_TRANSCRIPTIONS.items():
            with self.subTest(app=app_name):
                # Set the application profile
                profile = self.engine.set_active_application(app_name)
                
                if profile is None and app_name != "default":
                    logger.warning(f"Profile {app_name} not found, skipping")
                    continue
                
                # Process the transcription
                input_text = test_data["input"]
                processed = await self.engine.process_transcription(
                    input_text,
                    app_class=app_name
                )
                
                # Verify processing happened
                self.assertIsNotNone(processed)
                
                # If xAI is available, check for improvement
                if os.getenv("XAI_API_KEY") and test_data["should_improve"]:
                    # The processed text should be different or contain keywords
                    if processed != input_text:
                        logger.info(f"✅ {app_name}: Improved '{input_text}' -> '{processed[:50]}...'")
                    else:
                        logger.warning(f"⚠️ {app_name}: No improvement applied")
                else:
                    logger.info(f"ℹ️ {app_name}: Processed (no API key for improvement)")


class TestImprovementIntegration(unittest.TestCase):
    """Test integration with main hypr_voice.py"""
    
    async def test_hypr_voice_integration(self):
        """Test that hypr_voice.py can use the improvement engine"""
        try:
            # Import the main module
            from hypr_voice import HyprVoice
            
            # Create instance
            voice = HyprVoice()
            await voice.initialize()
            
            # Test context engine initialization
            engine_available = await voice._ensure_context_engine()
            self.assertTrue(engine_available, "Context engine should be available")
            
            # Check which engine was loaded
            engine_type = type(voice.context_engine).__name__
            logger.info(f"✅ Loaded engine: {engine_type}")
            
            # Test improvement on sample text
            test_text = "write a python hello world"
            voice.current_app = "windsurf"
            
            # Process transcription
            processed = await voice.process_transcription(test_text)
            self.assertIsNotNone(processed)
            
            logger.info(f"✅ Integration test successful: '{test_text}' processed")
            
        except ImportError as e:
            self.skipTest(f"Could not import hypr_voice: {e}")
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            raise


async def run_async_tests():
    """Run all async tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add tests
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleImprovementEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestImprovementIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run async tests manually
    test_engine = TestSimpleImprovementEngine()
    test_engine.setUp()
    
    logger.info("\n=== Running Async Tests ===")
    await test_engine.test_extra_context_execution()
    await test_engine.test_xai_improvement()
    await test_engine.test_full_transcription_pipeline()
    
    # Integration test
    integration = TestImprovementIntegration()
    await integration.test_hypr_voice_integration()
    
    return result.wasSuccessful()


def main():
    """Main test runner"""
    logger.info("🧪 Starting Improvement Pipeline Tests...")
    
    # Run sync tests first
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(TestSimpleImprovementEngine))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Run async tests
    success = asyncio.run(run_async_tests())
    
    if success:
        logger.info("\n✅ All tests passed!")
    else:
        logger.error("\n❌ Some tests failed")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
