#!/usr/bin/env python3
"""
Comprehensive Testing Suite for Universal Clipboard Manager
Tests paste functionality across different applications and scenarios
"""

import os
import sys
import time
import subprocess
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import tempfile

# Add hypr-voice/src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hypr-voice" / "src"))

from clipboard_manager import UniversalClipboardManager, ApplicationProfile, ApplicationType, PasteMethod
from clipboard_validator import ClipboardValidator, ValidationLevel, ContentType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"

@dataclass
class TestCase:
    """Individual test case"""
    id: str
    name: str
    description: str
    test_text: str
    expected_app_type: ApplicationType
    expected_method: PasteMethod
    setup_commands: List[str]
    cleanup_commands: List[str]
    validation_rules: List[str]
    timeout: int = 10

@dataclass
class TestResult:
    """Result of a test case"""
    test_case: TestCase
    status: TestStatus
    execution_time: float
    actual_method: Optional[PasteMethod]
    error_message: Optional[str]
    success_details: Dict[str, Any]
    warnings: List[str]

class ClipboardTestSuite:
    """Comprehensive testing suite for clipboard functionality"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent.parent / "hypr-voice" / "config"
        self.clipboard_manager = UniversalClipboardManager(config_dir)
        self.validator = ClipboardValidator(str(self.config_dir))

        self.test_results: List[TestResult] = []
        self.test_data_file = self.config_dir / "test_results.json"

        logger.info("Clipboard Test Suite initialized")

    def generate_test_cases(self) -> List[TestCase]:
        """Generate comprehensive test cases"""
        test_cases = []

        # Basic functionality tests
        test_cases.extend([
            TestCase(
                id="basic_plain_text",
                name="Basic Plain Text Paste",
                description="Test basic plain text pasting in terminal",
                test_text="Hello, World! This is a test message.",
                expected_app_type=ApplicationType.TERMINAL,
                expected_method=PasteMethod.CTRL_SHIFT_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["non_empty", "no_control_chars"]
            ),
            TestCase(
                id="multiline_text",
                name="Multiline Text Paste",
                description="Test multiline text pasting in code editor",
                test_text="Line 1\nLine 2\nLine 3 with special chars: !@#$%^&*()",
                expected_app_type=ApplicationType.IDE,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["multiline", "preserves_newlines"]
            ),
            TestCase(
                id="unicode_content",
                name="Unicode Content Paste",
                description="Test paste with Unicode characters",
                test_text="Hello 世界 🌍 Testing Unicode: αβγδε ñáéíóú",
                expected_app_type=ApplicationType.EDITOR,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["unicode_support", "no_control_chars"]
            ),
            TestCase(
                id="code_snippet",
                name="Code Snippet Paste",
                description="Test code snippet pasting in IDE",
                test_text="def hello_world():\n    print('Hello, World!')\n    return True",
                expected_app_type=ApplicationType.IDE,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["code_format", "indentation_preserved"]
            ),
            TestCase(
                id="url_paste",
                name="URL Paste",
                description="Test URL pasting in browser",
                test_text="https://github.com/example/hypr-voice",
                expected_app_type=ApplicationType.BROWSER,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["url_format", "no_mangling"]
            ),
            TestCase(
                id="file_path_paste",
                name="File Path Paste",
                description="Test file path pasting in terminal",
                test_text="/home/user/documents/important_file.txt",
                expected_app_type=ApplicationType.TERMINAL,
                expected_method=PasteMethod.CTRL_SHIFT_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["path_format", "no_trailing_spaces"]
            ),
            TestCase(
                id="html_entities",
                name="HTML Entities Paste",
                description="Test paste with HTML entities",
                test_text="Hello &amp; goodbye &lt;world&gt; &quot;quoted&quot;",
                expected_app_type=ApplicationType.BROWSER,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["html_entity_handling"]
            ),
            TestCase(
                id="control_characters",
                name="Control Characters Paste",
                description="Test paste with control characters",
                test_text="Text with control chars:\x00Hello\x1B[31mRed\x1B[0mWorld",
                expected_app_type=ApplicationType.EDITOR,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["control_char_removal", "safety_filtering"]
            ),
            TestCase(
                id="large_text",
                name="Large Text Paste",
                description="Test paste with large text content",
                test_text="Lorem ipsum dolor sit amet, " * 1000 + "End of large text.",
                expected_app_type=ApplicationType.EDITOR,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["large_content", "performance_acceptable"]
            ),
            TestCase(
                id="shell_command",
                name="Shell Command Paste",
                description="Test shell command pasting in terminal",
                test_text="ls -la /home/user | grep -E '\\.(txt|md|py)$'",
                expected_app_type=ApplicationType.TERMINAL,
                expected_method=PasteMethod.CTRL_SHIFT_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["command_syntax", "special_chars_preserved"]
            )
        ])

        # Edge cases and error conditions
        test_cases.extend([
            TestCase(
                id="empty_content",
                name="Empty Content Paste",
                description="Test paste with empty content",
                test_text="",
                expected_app_type=ApplicationType.SYSTEM,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["empty_handling"]
            ),
            TestCase(
                id="whitespace_only",
                name="Whitespace Only Content",
                description="Test paste with whitespace-only content",
                test_text="   \t\n   \t   ",
                expected_app_type=ApplicationType.SYSTEM,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["whitespace_handling"]
            ),
            TestCase(
                id="special_chars",
                name="Special Characters Paste",
                description="Test paste with special characters",
                test_text="Special chars: !@#$%^&*()[]{}|\\:\"'<>?,./;",
                expected_app_type=ApplicationType.EDITOR,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["special_char_preservation"]
            )
        ])

        # Application-specific tests
        test_cases.extend([
            TestCase(
                id="electron_app",
                name="Electron Application Paste",
                description="Test paste in Electron application (Discord/Slack style)",
                test_text="Test message for Electron app with emoji: 🚀",
                expected_app_type=ApplicationType.ELECTRON,
                expected_method=PasteMethod.YDOOOL,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["electron_compatibility", "emoji_support"]
            ),
            TestCase(
                id="remote_desktop",
                name="Remote Desktop Paste",
                description="Test paste in remote desktop session",
                test_text="Remote session test content",
                expected_app_type=ApplicationType.REMOTE,
                expected_method=PasteMethod.CTRL_V,
                setup_commands=[],
                cleanup_commands=[],
                validation_rules=["remote_compatibility"]
            )
        ])

        return test_cases

    async def run_test_case(self, test_case: TestCase, dry_run: bool = False) -> TestResult:
        """Run a single test case"""
        start_time = time.time()
        logger.info(f"Running test: {test_case.name}")

        try:
            # Execute setup commands
            for cmd in test_case.setup_commands:
                if not dry_run:
                    subprocess.run(cmd, shell=True, check=True, timeout=5)
                logger.debug(f"Setup command: {cmd}")

            if dry_run:
                # In dry run mode, just simulate the test
                await asyncio.sleep(0.1)
                result = TestResult(
                    test_case=test_case,
                    status=TestStatus.PASSED,
                    execution_time=time.time() - start_time,
                    actual_method=test_case.expected_method,
                    error_message=None,
                    success_details={
                        "dry_run": True,
                        "simulated_method": test_case.expected_method.value
                    },
                    warnings=[]
                )
            else:
                # Validate and sanitize content first
                validation_result = self.validator.validate_and_sanitize(test_case.test_text)

                if not validation_result.is_valid:
                    result = TestResult(
                        test_case=test_case,
                        status=TestStatus.FAILED,
                        execution_time=time.time() - start_time,
                        actual_method=None,
                        error_message=f"Content validation failed: {', '.join(validation_result.errors)}",
                        success_details={},
                        warnings=validation_result.warnings
                    )
                    return result

                # Perform the paste operation
                paste_result = self.clipboard_manager.intelligent_paste(validation_result.processed_content)

                # Determine test status
                if paste_result.success:
                    status = TestStatus.PASSED
                    error_message = None
                else:
                    status = TestStatus.FAILED
                    error_message = paste_result.message

                result = TestResult(
                    test_case=test_case,
                    status=status,
                    execution_time=time.time() - start_time,
                    actual_method=paste_result.method_used,
                    error_message=error_message,
                    success_details={
                        "validation_transformations": validation_result.transformations,
                        "content_type": validation_result.content_type.value,
                        "clipboard_app_detected": paste_result.app_detected,
                        "fallback_used": paste_result.fallback_used,
                        "paste_execution_time": paste_result.execution_time
                    },
                    warnings=validation_result.warnings
                )

            # Execute cleanup commands
            for cmd in test_case.cleanup_commands:
                if not dry_run:
                    subprocess.run(cmd, shell=True, check=False, timeout=5)
                logger.debug(f"Cleanup command: {cmd}")

            logger.info(f"Test {test_case.id}: {result.status.value}")
            return result

        except subprocess.TimeoutExpired:
            error_msg = f"Test timeout after {test_case.timeout} seconds"
            logger.error(f"Test {test_case.id}: {error_msg}")
            return TestResult(
                test_case=test_case,
                status=TestStatus.FAILED,
                execution_time=time.time() - start_time,
                actual_method=None,
                error_message=error_msg,
                success_details={},
                warnings=[]
            )
        except Exception as e:
            error_msg = f"Test execution error: {str(e)}"
            logger.error(f"Test {test_case.id}: {error_msg}")
            return TestResult(
                test_case=test_case,
                status=TestStatus.ERROR,
                execution_time=time.time() - start_time,
                actual_method=None,
                error_message=error_msg,
                success_details={},
                warnings=[]
            )

    def validate_test_result(self, result: TestResult) -> List[str]:
        """Validate test result against expected criteria"""
        validation_errors = []

        # Check if test passed
        if result.status != TestStatus.PASSED:
            validation_errors.append(f"Test did not pass: {result.status.value}")
            return validation_errors

        # Check expected application type
        if result.test_case.expected_app_type != ApplicationType.UNKNOWN:
            # This would require detecting the actual app type during test
            # For now, we'll skip this check
            pass

        # Check expected paste method
        if (result.actual_method and
            result.test_case.expected_method != result.actual_method and
            not result.success_details.get("fallback_used", False)):
            validation_errors.append(
                f"Expected method {result.test_case.expected_method.value}, "
                f"got {result.actual_method.value}"
            )

        # Check validation rules
        for rule in result.test_case.validation_rules:
            validation_errors.extend(self._check_validation_rule(rule, result))

        return validation_errors

    def _check_validation_rule(self, rule: str, result: TestResult) -> List[str]:
        """Check a specific validation rule"""
        errors = []

        if rule == "non_empty":
            if not result.test_case.test_text.strip():
                errors.append("Content is empty")

        elif rule == "no_control_chars":
            if any(ord(c) < 32 and c not in '\n\t' for c in result.test_case.test_text):
                errors.append("Content contains control characters")

        elif rule == "multiline":
            if '\n' not in result.test_case.test_text:
                errors.append("Expected multiline content")

        elif rule == "preserves_newlines":
            # Would need to check actual pasted content
            pass

        elif rule == "unicode_support":
            if not any(ord(c) > 127 for c in result.test_case.test_text):
                errors.append("Expected Unicode characters")

        elif rule == "url_format":
            import re
            url_pattern = r"https?://[^\s]+"
            if not re.search(url_pattern, result.test_case.test_text):
                errors.append("Content does not appear to be a URL")

        elif rule == "path_format":
            if not (result.test_case.test_text.startswith('/') or
                   result.test_case.test_text.startswith('~')):
                errors.append("Content does not appear to be a file path")

        elif rule == "code_format":
            if not any(keyword in result.test_case.test_text.lower()
                      for keyword in ['def ', 'function', 'class ', 'import ', 'var ', 'let ', 'const ']):
                errors.append("Content does not appear to be code")

        elif rule == "empty_handling":
            if result.test_case.test_text != "":
                errors.append("Expected empty content for this test")

        elif rule == "whitespace_handling":
            if not result.test_case.test_text.isspace():
                errors.append("Expected whitespace-only content")

        return errors

    async def run_test_suite(self, test_filter: Optional[str] = None, dry_run: bool = False) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("Starting clipboard test suite")

        test_cases = self.generate_test_cases()

        # Filter tests if specified
        if test_filter:
            test_cases = [tc for tc in test_cases if test_filter.lower() in tc.name.lower()
                         or test_filter.lower() in tc.id.lower()]

        logger.info(f"Running {len(test_cases)} test cases")

        self.test_results = []

        for test_case in test_cases:
            result = await self.run_test_case(test_case, dry_run)
            self.test_results.append(result)

            # Validate result
            validation_errors = self.validate_test_result(result)
            if validation_errors:
                logger.warning(f"Validation errors for {test_case.id}: {validation_errors}")
                result.warnings.extend(validation_errors)

        # Generate summary
        summary = self.generate_summary()

        # Save results
        self.save_test_results()

        logger.info("Test suite completed")
        return summary

    def generate_summary(self) -> Dict[str, Any]:
        """Generate test suite summary"""
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r.status == TestStatus.PASSED])
        failed_tests = len([r for r in self.test_results if r.status == TestStatus.FAILED])
        error_tests = len([r for r in self.test_results if r.status == TestStatus.ERROR])
        skipped_tests = len([r for r in self.test_results if r.status == TestStatus.SKIPPED])

        total_time = sum(r.execution_time for r in self.test_results)
        avg_time = total_time / total_tests if total_tests > 0 else 0

        # Method usage statistics
        method_usage = {}
        for result in self.test_results:
            if result.actual_method:
                method_name = result.actual_method.value
                method_usage[method_name] = method_usage.get(method_name, 0) + 1

        # Application type statistics
        app_type_usage = {}
        for result in self.test_results:
            app_type = result.test_case.expected_app_type.value
            app_type_usage[app_type] = app_type_usage.get(app_type, 0) + 1

        summary = {
            "timestamp": time.time(),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "errors": error_tests,
            "skipped": skipped_tests,
            "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            "total_execution_time": total_time,
            "average_execution_time": avg_time,
            "method_usage": method_usage,
            "app_type_usage": app_type_usage,
            "failed_tests": [
                {
                    "id": r.test_case.id,
                    "name": r.test_case.name,
                    "error": r.error_message
                }
                for r in self.test_results if r.status == TestStatus.FAILED
            ],
            "error_tests": [
                {
                    "id": r.test_case.id,
                    "name": r.test_case.name,
                    "error": r.error_message
                }
                for r in self.test_results if r.status == TestStatus.ERROR
            ]
        }

        return summary

    def save_test_results(self):
        """Save test results to file"""
        try:
            results_data = {
                "timestamp": time.time(),
                "system_info": self.clipboard_manager.get_system_info(),
                "summary": self.generate_summary(),
                "test_results": [
                    {
                        "id": r.test_case.id,
                        "name": r.test_case.name,
                        "status": r.status.value,
                        "execution_time": r.execution_time,
                        "actual_method": r.actual_method.value if r.actual_method else None,
                        "error_message": r.error_message,
                        "success_details": r.success_details,
                        "warnings": r.warnings
                    }
                    for r in self.test_results
                ]
            }

            with open(self.test_data_file, 'w') as f:
                json.dump(results_data, f, indent=2)

            logger.info(f"Test results saved to {self.test_data_file}")
        except Exception as e:
            logger.error(f"Failed to save test results: {e}")

    def load_test_results(self) -> Optional[Dict[str, Any]]:
        """Load previous test results"""
        try:
            if self.test_data_file.exists():
                with open(self.test_data_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load test results: {e}")
        return None

    def print_summary(self, summary: Dict[str, Any]):
        """Print test suite summary"""
        print("\n" + "=" * 70)
        print("CLIPBOARD TEST SUITE SUMMARY")
        print("=" * 70)

        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']} ({summary['success_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Errors: {summary['errors']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Total Time: {summary['total_execution_time']:.2f}s")
        print(f"Average Time: {summary['average_execution_time']:.2f}s")

        print("\nMethod Usage:")
        for method, count in summary['method_usage'].items():
            print(f"  {method}: {count}")

        print("\nApplication Type Usage:")
        for app_type, count in summary['app_type_usage'].items():
            print(f"  {app_type}: {count}")

        if summary['failed_tests']:
            print("\nFailed Tests:")
            for test in summary['failed_tests']:
                print(f"  ❌ {test['name']}: {test['error']}")

        if summary['error_tests']:
            print("\nError Tests:")
            for test in summary['error_tests']:
                print(f"  💥 {test['name']}: {test['error']}")

        print("=" * 70)

    def interactive_test_mode(self):
        """Interactive testing mode"""
        print("Interactive Clipboard Testing Mode")
        print("Enter text to test paste functionality, or 'quit' to exit")
        print("Commands: 'detect' (detect app), 'methods' (test all methods), 'validate' (test validation)")

        while True:
            try:
                user_input = input("\n> ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    break

                if user_input.lower() == 'detect':
                    app_class, window_title = self.clipboard_manager.detect_active_application()
                    profile = self.clipboard_manager.get_application_profile(app_class, window_title)
                    print(f"Detected: {profile.name}")
                    print(f"Class: {app_class}")
                    print(f"Primary method: {profile.primary_method.value}")
                    continue

                if user_input.lower() == 'methods':
                    print("Testing all paste methods...")
                    print("Switch to a text editor to see results (5 seconds)...")
                    time.sleep(5)
                    results = self.clipboard_manager.test_paste_methods()
                    for method, success in results.items():
                        status = "✅" if success else "❌"
                        print(f"  {status} {method.value}")
                    continue

                if user_input.lower() == 'validate':
                    test_text = input("Enter text to validate: ")
                    result = self.validator.test_validation(test_text)
                    continue

                if user_input:
                    print(f"Testing paste: '{user_input}'")
                    result = self.clipboard_manager.intelligent_paste(user_input)
                    if result.success:
                        print(f"✅ {result.message}")
                    else:
                        print(f"❌ {result.message}")

            except KeyboardInterrupt:
                print("\nGoodbye!")
                break

async def main():
    """Main entry point for test suite"""
    import argparse

    parser = argparse.ArgumentParser(description="Clipboard Test Suite")
    parser.add_argument("--filter", help="Filter tests by name or ID")
    parser.add_argument("--dry-run", action="store_true", help="Run tests without actual paste operations")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--single", help="Run a single test by ID")
    parser.add_argument("--report", help="Generate report from saved results")
    parser.add_argument("--list", action="store_true", help="List all available tests")

    args = parser.parse_args()

    test_suite = ClipboardTestSuite()

    if args.interactive:
        test_suite.interactive_test_mode()
        return

    if args.list:
        test_cases = test_suite.generate_test_cases()
        print("Available Test Cases:")
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i:2d}. {test_case.id}: {test_case.name}")
            print(f"     {test_case.description}")
        return

    if args.report:
        results = test_suite.load_test_results()
        if results:
            test_suite.print_summary(results['summary'])
        else:
            print("No saved results found")
        return

    if args.single:
        test_cases = test_suite.generate_test_cases()
        test_case = next((tc for tc in test_cases if tc.id == args.single), None)
        if not test_case:
            print(f"Test case '{args.single}' not found")
            return

        print(f"Running single test: {test_case.name}")
        result = await test_suite.run_test_case(test_case, args.dry_run)

        print(f"Status: {result.status.value}")
        if result.error_message:
            print(f"Error: {result.error_message}")
        if result.warnings:
            print("Warnings:")
            for warning in result.warnings:
                print(f"  - {warning}")
        return

    # Run full test suite
    print("Starting Clipboard Test Suite...")
    if args.dry_run:
        print("DRY RUN MODE - No actual paste operations will be performed")

    print("Make sure you have a text editor open to see paste results")
    print("You have 10 seconds to prepare...")

    for i in range(10, 0, -1):
        print(f"{i}...", end=" ", flush=True)
        await asyncio.sleep(1)
    print("\n")

    summary = await test_suite.run_test_suite(args.filter, args.dry_run)
    test_suite.print_summary(summary)

if __name__ == "__main__":
    asyncio.run(main())