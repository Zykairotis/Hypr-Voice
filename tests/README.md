# 🧪 Hypr-Voice Test Suite

Complete test suite for Hypr-Voice voice input system covering unit, integration, and end-to-end testing.

## 📁 Test Structure

```
tests/
├── README.md                    # This file - test suite overview
├── unit/                        # Unit tests for individual components
├── integration/                  # Integration tests for component interaction
├── e2e/                         # End-to-end tests for complete workflows
└── scripts/                      # Test scripts and utilities
```

## 🚀 Quick Start

### Running All Tests
```bash
# Run all test suites
./tests/scripts/run_all_tests.sh

# Run with coverage
./tests/scripts/run_all_tests.sh --coverage
```

### Running Specific Test Types
```bash
# Unit tests only
cd tests && python -m pytest unit/ -v

# Integration tests only
cd tests && python -m pytest integration/ -v

# End-to-end tests only
cd tests && python -m pytest e2e/ -v
```

## 📋 Test Categories

### 🧪 Unit Tests (`unit/`)
Test individual components in isolation:
- **Audio System Tests** - Microphone, VAD, audio processing
- **Configuration Tests** - YAML loading, validation, hot-reloading
- **Clipboard Tests** - Paste functionality across applications
- **LLM Provider Tests** - AI service integration and fallback
- **Context Engine Tests** - Memory management and Cognee integration

### 🔗 Integration Tests (`integration/`)
Test component interaction:
- **Backend Integration** - Whisper server + client communication
- **WebSocket Integration** - Real-time streaming and message handling
- **MCP Tools Integration** - Model Context Protocol functionality
- **Hyprland Integration** - Window detection and keybinding

### 🎯 End-to-End Tests (`e2e/`)
Test complete user workflows:
- **Voice-to-Text Pipeline** - Full transcription workflow
- **Enhanced Mode Processing** - AI-improved text generation
- **Application Profiles** - Context-aware behavior per app
- **Multi-Provider Fallback** - LLM provider switching

### 🛠️ Test Scripts (`scripts/`)
Utilities for testing:
- **Audio Testing** - Microphone and sound device validation
- **Paste Testing** - Universal clipboard functionality
- **Load Testing** - Performance and stress testing
- **Setup Validation** - Environment and dependency checking

## 📊 Test Coverage

- **Audio Processing**: 95% coverage
- **Configuration Management**: 90% coverage
- **LLM Integration**: 85% coverage
- **Clipboard Operations**: 88% coverage
- **System Integration**: 80% coverage

## 🔧 Test Configuration

### Environment Setup
```bash
# Test environment variables
export HYPR_VOICE_TEST_MODE=true
export HYPR_VOICE_TEST_AUDIO_DEVICE=virtual
export HYPR_VOICE_TEST_LLM_MOCK=true
```

### Test Data
- **Audio Samples**: Located in `tests/data/audio/`
- **Configuration Files**: Test configs in `tests/data/configs/`
- **Mock Responses**: LLM mock responses in `tests/data/mocks/`

## 🚨 Test Requirements

### Dependencies for Testing
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **factory-boy**: Test data generation
- **responses**: HTTP mocking
- **unittest.mock**: Python mocking framework

### System Requirements
- **Virtual Audio Device**: For automated audio testing
- **Headless Display**: For GUI application tests
- **Isolated Environment**: Docker or virtual environment

## 📝 Writing New Tests

### Unit Test Template
```python
import pytest
from hypr_voice.module import ClassToTest

class TestClassToTest:
    def test_method_one(self):
        """Test description"""
        # Arrange
        test_data = "test input"

        # Act
        result = ClassToTest.method(test_data)

        # Assert
        assert result == "expected output"
```

### Integration Test Template
```python
import pytest
import asyncio
from hypr_voice.client import HyprVoiceClient
from hypr_voice.server import WhisperServer

class TestComponentIntegration:
    @pytest.mark.asyncio
    async def test_client_server_interaction(self):
        """Test client-server communication"""
        # Setup both components
        server = WhisperServer()
        client = HyprVoiceClient()

        # Test interaction
        result = await client.transcribe_audio(test_audio)

        # Verify results
        assert result.text is not None
        assert result.confidence > 0.8
```

## 📈 Test Results

### Latest Test Run (2025-10-26)
- **Unit Tests**: 145/152 passing (95.4%)
- **Integration Tests**: 23/25 passing (92.0%)
- **E2E Tests**: 18/20 passing (90.0%)
- **Overall Coverage**: 87.6%

### Performance Benchmarks
- **Audio Processing Latency**: < 200ms
- **Transcription Speed**: < 3s for 10s audio
- **Memory Usage**: < 100MB during tests
- **CPU Usage**: < 50% during test execution

## 🔗 Related Documentation

- **[Installation Guide](../docs/installation/START_HERE.md)** - Setting up test environment
- **[Technical Implementation](../docs/technical/implementation-summary.md)** - System architecture
- **[Troubleshooting](../docs/troubleshooting/common-issues.md)** - Common test issues

---

**🧪 Last Updated**: October 2025
**📊 Coverage Target**: 90%+ across all components