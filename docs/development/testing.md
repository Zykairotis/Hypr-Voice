# Testing Guide

This guide covers testing practices, tools, and conventions for the Hypr-Voice project.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Testing Tools](#testing-tools)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Structure](#test-structure)
6. [Async Testing](#async-testing)
7. [Mocking](#mocking)
8. [Coverage](#coverage)
9. [CI/CD Integration](#cicd-integration)
10. [Best Practices](#best-practices)

## Testing Philosophy

We follow these principles:

1. **Test-First Development**: Write tests before implementation (TDD)
2. **Pyramid Strategy**: Many unit tests, fewer integration tests, minimal E2E tests
3. **Fast Feedback**: Tests should run quickly
4. **Isolation**: Each test should be independent
5. **Clarity**: Tests should be readable and maintainable

### Test Categories

- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test interaction between components
- **End-to-End Tests**: Test complete workflows
- **Performance Tests**: Validate performance characteristics

## Testing Tools

### Core Tools

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist
```

**Tools Used**:
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **pytest-xdist**: Parallel test execution

### Configuration

`pyproject.toml`:

```toml
[tool.pytest.ini_options]
minversion = "7.0"
asyncio_mode = "auto"
testpaths = ["tests", "src/hypr_voice/tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = "-v --tb=short"

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*.py",
    "*/__pycache__/*",
    "*/site-packages/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_specific.py

# Run specific test function
pytest tests/test_specific.py::test_function_name

# Run tests matching pattern
pytest -k "test_tts"

# Run tests in parallel
pytest -n auto

# Stop on first failure
pytest -x

# Fail fast (stop after N failures)
pytest --maxfail=3
```

### With Coverage

```bash
# Run with coverage report
pytest --cov=src/hypr_voice --cov-report=term-missing

# Generate HTML coverage report
pytest --cov=src/hypr_voice --cov-report=html
open htmlcov/index.html

# Generate XML coverage (for CI)
pytest --cov=src/hypr_voice --cov-report=xml
```

### Async Tests

```bash
# Run async tests (pytest-asyncio)
pytest -v

# Run only async tests
pytest -m asyncio

# Run with asyncio_mode
pytest --asyncio-mode=auto
```

## Writing Tests

### Basic Test Structure

```python
import pytest
from hypr_voice.services.voice import UniversalTTS, TTSProvider, TTSConfig

class TestTTSSynthesis:
    """Test suite for TTS synthesis."""

    @pytest.fixture
    async def tts_instance(self):
        """Create TTS instance for testing."""
        config = TTSConfig(
            provider=TTSProvider.KOKORO,
            voice="af_bella"
        )
        return UniversalTTS(config)

    @pytest.mark.asyncio
    async def test_basic_synthesis(self, tts_instance):
        """Test basic text synthesis."""
        result = await tts_instance.speak("Hello world")

        assert result["success"] is True
        assert "audio_file" in result
        assert Path(result["audio_file"]).exists()

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, tts_instance):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await tts_instance.speak("")
```

### Test Fixtures

```python
import pytest
from pathlib import Path
import tempfile

# Function-scoped fixture (default)
@pytest.fixture
def temp_file():
    """Create temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    # Cleanup happens automatically

# Class-scoped fixture
@pytest.fixture(scope="class")
def class_resource():
    """Resource shared across tests in class."""
    resource = setup_resource()
    yield resource
    cleanup_resource(resource)

# Session-scoped fixture
@pytest.fixture(scope="session")
def database():
    """Database for entire test session."""
    db = setup_test_database()
    yield db
    teardown_test_database(db)

# Async fixture
@pytest.fixture
async def async_client():
    """Async HTTP client."""
    client = await create_client()
    yield client
    await client.close()

# Fixture with parameters
@pytest.fixture(params=["kokoro", "deepgram", "elevenlabs"])
async def tts_provider(request):
    """Parametrized TTS provider."""
    return TTSProvider(request.param)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("text,expected_words", [
    ("Hello world", 2),
    ("Hi", 1),
    ("", 0),
])
def test_word_count(text, expected_words):
    """Test word counting with various inputs."""
    assert count_words(text) == expected_words

# Multiple parameters
@pytest.mark.parametrize("provider,voice", [
    ("kokoro", "af_bella"),
    ("kokoro", "am_adam"),
    ("deepgram", "aura-luna-en"),
])
async def test_provider_voices(provider, voice):
    """Test different provider and voice combinations."""
    result = await test_synthesis(provider, voice)
    assert result["success"] is True
```

### Marking Tests

```python
# Mark slow tests
@pytest.mark.slow
async def test_long_running_operation():
    await long_operation()

# Mark integration tests
@pytest.mark.integration
async def test_database_integration():
    # Requires database
    pass

# Mark tests that require API keys
@pytest.mark.requires_api_key
async def test_openai_integration():
    # Requires OPENAI_API_KEY
    pass

# Run specific marks
pytest -m "not slow"  # Skip slow tests
pytest -m integration  # Only integration tests
pytest -m "slow and integration"  # Both marks
```

## Test Structure

### Directory Layout

```
tests/                          # Integration tests
├── integration/
│   ├── test_ws.py             # WebSocket integration
│   └── test_database.py       # Database integration
├── unit/
│   ├── test_tts.py            # TTS unit tests
│   └── test_whisper.py        # Whisper unit tests
├── conftest.py                # Shared fixtures
└── __init__.py

src/hypr_voice/tests/          # Package-level tests
├── test_claude_tts_agent.py
└── test_orchestrator.py
```

### conftest.py

Shared fixtures for all tests:

```python
# tests/conftest.py
import pytest
import asyncio
from hypr_voice.orchestrator import HyprVoiceOrchestrator, OrchestratorConfig

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def orchestrator():
    """Create orchestrator instance."""
    config = OrchestratorConfig(
        model="claude-sonnet-4-5",
        max_turns=5
    )
    orchestrator = HyprVoiceOrchestrator(config)
    yield orchestrator
    await orchestrator.cleanup()

@pytest.fixture
def mock_api_key(monkeypatch):
    """Mock API key for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key_123")
```

## Async Testing

### Async Test Patterns

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None

@pytest.mark.asyncio
async def test_async_context_manager():
    """Test async context manager."""
    async with AsyncResource() as resource:
        assert resource.is_ready
        result = await resource.process()
        assert result.success

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent async operations."""
    tasks = [
        process_item(item)
        for item in range(10)
    ]
    results = await asyncio.gather(*tasks)
    assert len(results) == 10
```

### Async Fixtures

```python
@pytest.fixture
async def async_resource():
    """Async fixture that yields resource."""
    resource = await AsyncResource.create()
    yield resource
    await resource.cleanup()

@pytest.mark.asyncio
async def test_with_async_fixture(async_resource):
    """Test using async fixture."""
    result = await async_resource.do_something()
    assert result is not None
```

## Mocking

### Basic Mocking

```python
from unittest.mock import Mock, patch, AsyncMock
import pytest

def test_with_mock():
    """Test with mock object."""
    mock_service = Mock()
    mock_service.process.return_value = {"success": True}

    result = my_function(mock_service)
    assert result == {"success": True}
    mock_service.process.assert_called_once()

def test_with_patch():
    """Test with patch decorator."""
    with patch('hypr_voice.services.voice.api_call') as mock_call:
        mock_call.return_value = {"status": "ok"}

        result = call_external_api()
        assert result["status"] == "ok"
        mock_call.assert_called_once()
```

### Async Mocking

```python
@pytest.mark.asyncio
async def test_async_mock():
    """Test with async mock."""
    mock_client = AsyncMock()
    mock_client.fetch.return_value = {"data": "test"}

    result = await fetch_data(mock_client)
    assert result == {"data": "test"}
    mock_client.fetch.assert_called_once_with()

@pytest.mark.asyncio
async def test_patch_async():
    """Test patching async function."""
    with patch('hypr_voice.services.voice.async_api_call', new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"result": "success"}

        result = await async_function()
        assert result == {"result": "success"}
```

### Mocking External APIs

```python
@pytest.mark.asyncio
async def test_anthropic_api(mock_anthropic):
    """Test Anthropic API integration with mock."""
    mock_response = Mock()
    mock_response.content = [Mock(text="Hello!")]

    mock_anthropic.messages.create.return_value = mock_response

    result = await call_claude("Hi")
    assert result == "Hello!"
    mock_anthropic.messages.create.assert_called_once()

# Fixture in conftest.py
@pytest.fixture
def mock_anthropic(monkeypatch):
    """Mock Anthropic client."""
    mock = Mock()
    monkeypatch.setattr("anthropic.Anthropic", return_value=mock)
    return mock
```

## Coverage

### Coverage Goals

- **Overall Coverage**: Target 80%+
- **Critical Paths**: 95%+ (e.g., agent logic, TTS, STT)
- **Utility Functions**: 90%+
- **Configuration**: 70%+ (some paths hard to test)

### Running Coverage

```bash
# Generate terminal report
pytest --cov=src/hypr_voice --cov-report=term-missing

# Generate HTML report
pytest --cov=src/hypr_voice --cov-report=html

# Combine coverage from multiple runs
pytest --cov=src/hypr_voice --cov-append
pytest --cov=src/hypr_voice --cov-append
coverage html
```

### Coverage Configuration

```toml
[tool.coverage.run]
source = ["src"]
branch = true  # Enable branch coverage
omit = [
    "*/tests/*",
    "*/test_*.py",
]

[tool.coverage.report]
precision = 2
show_missing = true
skip_covered = false
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
    "@abstractmethod",
]
```

## CI/CD Integration

### GitHub Actions Example

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev,all]"

      - name: Run linting
        run: |
          flake8 src/ tests/
          mypy src/

      - name: Run tests
        run: |
          pytest --cov=src/hypr_voice --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

## Best Practices

### DO's

- **DO** write descriptive test names
  ```python
  def test_user_authentication_with_valid_credentials():
      pass
  ```

- **DO** use fixtures for setup
  ```python
  @pytest.fixture
  def user():
      return create_test_user()
  ```

- **DO** test error cases
  ```python
  def test_invalid_input_raises_error():
      with pytest.raises(ValueError):
          process_input("")
  ```

- **DO** keep tests independent
  ```python
  # Each test should work in isolation
  def test_one():
      assert function() == 1

  def test_two():
      assert function() == 2
  ```

- **DO** use assertions effectively
  ```python
  # Good - specific assertion
  assert result["success"] is True
  assert "error" not in result

  # Bad - generic
  assert result  # What does this prove?
  ```

### DON'Ts

- **DON'T** test external libraries
  ```python
  # Bad - testing pytest
  def test_pytest_works():
      assert True
  ```

- **DON'T** write brittle tests
  ```python
  # Bad - depends on exact timing
  def test_duration():
      start = time.time()
      process()
      assert time.time() - start == 1.0  # Will fail
  ```

- **DON'T** test private methods directly
  ```python
  # Bad - testing implementation detail
  def test_private_method():
      obj = MyClass()
      obj._private_method()  # Don't do this
  ```

- **DON'T** use shared state
  ```python
  # Bad - tests affect each other
  global_counter = 0

  def test_increment():
      global global_counter
      global_counter += 1
      assert global_counter == 1
  ```

## Advanced Patterns

### Test Factories

```python
def create_test_tts_config(provider="kokoro", voice="af_bella"):
    """Factory for creating test TTS configs."""
    return TTSConfig(
        provider=TTSProvider(provider),
        voice=voice
    )

@pytest.mark.parametrize("config", [
    create_test_tts_config("kokoro", "af_bella"),
    create_test_tts_config("deepgram", "aura-luna-en"),
])
async def test_multiple_configs(config):
    """Test with multiple configurations."""
    tts = UniversalTTS(config)
    result = await tts.speak("Test")
    assert result["success"]
```

### Custom Markers

```python
# conftest.py
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

# Usage
@pytest.mark.slow
async def test_slow_operation():
    await asyncio.sleep(10)

@pytest.mark.integration
async def test_full_workflow():
    # Test complete system
    pass
```

## Troubleshooting

### Common Issues

**Issue**: Async tests hang
```python
# Solution: Use pytest-asyncio correctly
@pytest.mark.asyncio
async def test_hanging():
    result = await async_function()
    assert result
```

**Issue**: Fixtures not found
```python
# Solution: Check fixture scope and location
# - Fixtures in conftest.py are available to all tests in that directory
# - Fixtures in parent directories are inherited
```

**Issue**: Tests pass individually but fail together
```python
# Solution: Tests are sharing state - make them independent
@pytest.fixture(autouse=True)
async def reset_state():
    """Reset state between tests."""
    yield
    await cleanup()
```

## Resources

- [PyTest Documentation](https://docs.pytest.org/)
- [PyTest Asyncio](https://pytest-asyncio.readthedocs.io/)
- [PyTest Mocking](https://docs.pytest.org/en/stable/how-to/mock.html)
- [Effective Python Testing](https://docs.pytest.org/en/stable/)

## Next Steps

- Read [Contributing Guidelines](contributing.md)
- Learn [Debugging Guide](debugging.md)
- See [Adding Features](adding-features.md)
