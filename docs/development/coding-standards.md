# Coding Standards and Conventions

This document defines the coding standards, conventions, and best practices for contributing to Hypr-Voice.

## Table of Contents

1. [Python Style Guide](#python-style-guide)
2. [Code Organization](#code-organization)
3. [Naming Conventions](#naming-conventions)
4. [Type Hints](#type-hints)
5. [Documentation](#documentation)
6. [Error Handling](#error-handling)
7. [Testing Standards](#testing-standards)
8. [Git Conventions](#git-conventions)
9. [Code Review](#code-review)

## Python Style Guide

We follow [PEP 8](https://pep8.org/) with customizations enforced by tools:

### Line Length

- **Maximum**: 100 characters (enforced by Black)
- **Soft limit**: 80 characters for readability
- **Exceptions**: URLs, long strings, imports

```python
# Good
result = some_function(
    param1=value1,
    param2=value2,
    param3=value3
)

# Bad (exceeds 100 chars)
result = some_function(param1=value1, param2=value2, param3=value3, param4=value4, param5=value5)
```

### Imports

Order imports alphabetically within groups:

```python
# 1. Standard library imports
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional

# 2. Third-party imports
from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from anthropic import Anthropic

# 3. Local imports
from hypr_voice.orchestrator import HyprVoiceOrchestrator
from hypr_voice.services.voice import TTSProvider
```

Use `isort` to automatically sort imports:

```bash
isort src/ tests/
```

### String Quotes

Use double quotes for strings, single quotes only for nested quotes:

```python
# Good
message = "Hello, world"
nested = 'He said "Hello" to me'

# Bad
message = 'Hello, world'
```

### Whitespace

```python
# Good - spaces around operators
x = 1 + 2
result = func(arg1, arg2)

# Good - no spaces for keyword arguments
result = func(arg1=value1, arg2=value2)

# Good - blank line between functions
def func1():
    pass


def func2():
    pass
```

## Code Organization

### File Structure

Each Python file should follow this structure:

```python
#!/usr/bin/env python3
"""
Module docstring: Brief description of module purpose.

More detailed explanation if needed.
"""

# 1. Standard library imports
import asyncio
from typing import Optional

# 2. Third-party imports
from fastapi import HTTPException
from pydantic import BaseModel

# 3. Local imports
from hypr_voice.core import BaseClass

# 4. Module-level constants
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3

# 5. Custom exceptions (if any)
class CustomError(Exception):
    """Exception raised for specific errors."""

# 6. Classes
class MyClass:
    """Brief class description."""

    def __init__(self):
        """Initialize instance."""
        self.value = None

    def method(self):
        """Brief method description."""
        pass

# 7. Standalone functions
def standalone_function():
    """Brief function description."""
    pass

# 8. Main block (if script)
if __name__ == "__main__":
    # Execution code
    pass
```

### Class Organization

```python
class VoiceOrchestrator:
    """
    Orchestrates voice synthesis and recognition.

    This class coordinates TTS and STT services...
    """

    # 1. Class attributes
    DEFAULT_PROVIDER: TTSProvider = TTSProvider.KOKORO
    MAX_CONCURRENT: int = 5

    def __init__(self, config: OrchestratorConfig):
        """
        Initialize the voice orchestrator.

        Args:
            config: Configuration object

        Raises:
            ConfigurationError: If config is invalid
        """
        self.config = config
        self._initialize()

    # 2. Public properties
    @property
    def provider(self) -> TTSProvider:
        """Get current TTS provider."""
        return self.config.provider

    # 3. Public methods
    async def synthesize(self, text: str) -> dict:
        """
        Synthesize speech from text.

        Args:
            text: Text to synthesize

        Returns:
            dict with keys: success, audio_file, voice_used

        Raises:
            SynthesisError: If synthesis fails
        """
        # Implementation
        pass

    # 4. Private methods
    async def _initialize(self):
        """Initialize internal state."""
        pass

    # 5. Magic methods (dunder)
    def __repr__(self) -> str:
        """String representation."""
        return f"VoiceOrchestrator(provider={self.provider})"
```

## Naming Conventions

### Variables and Functions

Use `snake_case` for variables and functions:

```python
# Good
user_name = "John"
def calculate_total(items: List[Item]) -> float:
    pass

# Bad
userName = "John"
def CalculateTotal(items):
    pass
```

### Constants

Use `UPPER_SNAKE_CASE` for constants:

```python
# Good
MAX_CONNECTIONS = 100
DEFAULT_TIMEOUT = 30
API_BASE_URL = "https://api.example.com"

# Bad
max_connections = 100
default_timeout = 30
```

### Classes

Use `PascalCase` for classes:

```python
# Good
class VoiceOrchestrator:
    pass

class TTSProvider(Enum):
    pass

# Bad
class voice_orchestrator:
    pass
```

### Private Members

Prefix with single underscore for protected, double for private:

```python
class MyClass:
    def __init__(self):
        self.public_var = 1      # Public
        self._protected_var = 2   # Protected (use with care)
        self.__private_var = 3    # Private (name mangling)

    def public_method(self):
        pass

    def _protected_method(self):
        pass

    def __private_method(self):
        pass
```

## Type Hints

Use type hints for all public functions and methods:

```python
from typing import List, Dict, Optional, Union, Callable

# Function with return type
def process_text(text: str) -> str:
    return text.upper()

# Optional return type
def get_user(user_id: int) -> Optional[Dict[str, any]]:
    if user_id in database:
        return database[user_id]
    return None

# Complex types
from typing import Dict, List

def batch_process(items: List[str]) -> Dict[str, int]:
    return {item: len(item) for item in items}

# Async functions
async def fetch_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            return await response.json()

# Type aliases
Processor = Callable[[str], str]
 processors: List[Processor] = [str.upper, str.lower]
```

### Type Hint Best Practices

```python
# Good - specific types
def process(items: List[str]) -> Dict[str, int]:
    pass

# Bad - too generic
def process(items) -> dict:
    pass

# Good - use Optional for nullable
def get_name(user_id: int) -> Optional[str]:
    pass

# Good - use Union for multiple types
def process_input(data: Union[str, bytes]) -> str:
    pass

# Good - use TypedDict for structured data
from typing import TypedDict

class UserProfile(TypedDict):
    name: str
    email: str
    age: int

def get_profile(user_id: int) -> UserProfile:
    pass
```

## Documentation

### Docstrings

Use Google-style docstrings:

```python
def synthesize_speech(
    text: str,
    voice: str = "default",
    speed: float = 1.0
) -> Dict[str, any]:
    """
    Synthesize speech from text using TTS.

    This function sends text to the configured TTS provider
    and returns the synthesized audio.

    Args:
        text: The text to synthesize into speech
        voice: Voice ID to use (default: "default")
        speed: Speech speed multiplier (default: 1.0)

    Returns:
        A dictionary containing:
            - success (bool): Whether synthesis succeeded
            - audio_file (str): Path to generated audio file
            - voice_used (str): Voice ID that was used
            - error (str, optional): Error message if failed

    Raises:
        ValueError: If text is empty or speed is invalid
        SynthesisError: If TTS provider fails

    Example:
        >>> result = synthesize_speech("Hello world")
        >>> print(result['audio_file'])
        '/path/to/audio.wav'
    """
    if not text:
        raise ValueError("Text cannot be empty")
    # Implementation
```

### Module Docstrings

```python
"""
Hypr-Voice TTS Manager

This module provides a unified interface for text-to-speech synthesis
across multiple providers (Kokoro, Deepgram, ElevenLabs).

Example:
    >>> from hypr_voice.services.voice import UniversalTTS
    >>> tts = UniversalTTS()
    >>> result = await tts.speak("Hello world")
"""
```

### Comments

Use comments sparingly; code should be self-documenting:

```python
# Good - explains WHY
# Use exponential backoff to avoid overwhelming the API
await asyncio.sleep(2 ** attempt)

# Bad - explains WHAT (obvious from code)
# Increment the counter
count += 1

# Good - explains complex logic
# Calculate weighted average with bias toward recent values
weighted_avg = (recent * 0.7) + (historical * 0.3)

# Good - TODO marker
# TODO: Add support for streaming synthesis
```

## Error Handling

### Custom Exceptions

Define exceptions for specific error conditions:

```python
class HyprVoiceError(Exception):
    """Base exception for Hypr-Voice errors."""

class ConfigurationError(HyprVoiceError):
    """Raised when configuration is invalid."""

class SynthesisError(HyprVoiceError):
    """Raised when TTS synthesis fails."""

class ValidationError(HyprVoiceError):
    """Raised when input validation fails."""
```

### Exception Handling

```python
# Good - specific exception handling
try:
    result = await tts.speak(text)
except ConfigurationError as e:
    logger.error(f"Configuration error: {e}")
    raise
except SynthesisError as e:
    logger.warning(f"Synthesis failed: {e}, retrying...")
    await retry_synthesis(text)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise

# Bad - bare except
try:
    result = await tts.speak(text)
except:
    pass  # Never do this!

# Good - cleanup in finally
async with aiohttp.ClientSession() as session:
    try:
        response = await session.get(url)
        data = await response.json()
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error: {e}")
        raise
    finally:
        # Cleanup happens automatically via context manager
        pass
```

### Logging

Use `loguru` for logging:

```python
from loguru import logger

# Configure logging
logger.add(
    "logs/app_{time}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO"
)

# Usage
logger.debug("Detailed debug information")
logger.info("User logged in", extra={"user_id": 123})
logger.warning("API rate limit approaching")
logger.error("Database connection failed", exc_info=True)
logger.critical("System shutting down")
```

## Testing Standards

### Test Structure

```python
import pytest
from hypr_voice.services.voice import UniversalTTS

class TestTTSSynthesis:
    """Test suite for TTS synthesis."""

    @pytest.fixture
    async def tts(self):
        """Fixture providing TTS instance."""
        config = TTSConfig(provider=TTSProvider.KOKORO)
        return UniversalTTS(config)

    @pytest.mark.asyncio
    async def test_basic_synthesis(self, tts):
        """Test basic text synthesis."""
        result = await tts.speak("Hello world")
        assert result["success"] is True
        assert "audio_file" in result
        assert Path(result["audio_file"]).exists()

    @pytest.mark.asyncio
    async def test_empty_text_raises_error(self, tts):
        """Test that empty text raises ValueError."""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await tts.speak("")

    @pytest.mark.parametrize("text,expected_length", [
        ("Hi", 2),
        ("Hello", 5),
        ("Hello world", 11),
    ])
    async def test_text_lengths(self, tts, text, expected_length):
        """Test synthesis with various text lengths."""
        result = await tts.speak(text)
        assert result["success"] is True
```

### Test Naming

```python
# Good - descriptive test names
def test_user_authentication_with_valid_credentials():
    pass

def test_user_authentication_with_invalid_password():
    pass

# Bad - vague test names
def test_auth():
    pass

def test_it_works():
    pass
```

## Git Conventions

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Maintenance tasks

**Examples**:

```bash
feat(voice): add ElevenLabs TTS provider

Implement support for ElevenLabs API with fallback to Kokoro.
Closes #123

fix(tts): handle empty text gracefully

Raise ValueError instead of crashing when empty text is provided.

docs(orchestrator): update API documentation

Add examples for new WebSocket endpoints.

refactor(agent): simplify context management

Remove redundant state tracking and use single source of truth.
```

### Branch Naming

```bash
feature/add-gemini-integration
fix/whisper-timeout-error
docs/update-contributing-guide
refactor/optimize-tts-streaming
hotfix/critical-security-patch
```

## Code Review

### Review Checklist

- [ ] Code follows style guide
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] No hardcoded credentials
- [ ] Error handling appropriate
- [ ] Logging added where needed
- [ ] Type hints correct
- [ ] No unnecessary dependencies
- [ ] Performance considered
- [ ] Security reviewed

### Review Process

1. **Self-Review**: Review your own code before submitting
2. **Automated Checks**: Ensure linting and tests pass
3. **Peer Review**: Request review from at least one peer
4. **Address Feedback**: Respond to all comments
5. **Approval**: Get approval before merging

## Best Practices Summary

### Do's

- Write clear, self-documenting code
- Use type hints for public APIs
- Add docstrings to all public functions/classes
- Handle errors gracefully
- Log important events
- Write tests for new features
- Keep functions focused and small
- Use async/await for I/O operations
- Follow semantic versioning
- Update documentation

### Don'ts

- Don't use bare `except:` clauses
- Don't hardcode credentials or paths
- Don't ignore type hints
- Don't write functions >50 lines
- Don't use global variables
- Don't commit untested code
- Don't skip error handling
- Don't use `print()` for logging
- Don't ignore linting errors
- Don't break backward compatibility without major version bump

## Tools and Automation

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run manually
pre-commit run --all-files
```

Example `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.7.0
    hooks:
      - id: mypy
```

### IDE Integration

Configure your IDE to:
- Run Black on save
- Show type hints
- Flag linting errors
- Auto-sort imports
- Run tests on save

## Resources

- [PEP 8 Style Guide](https://pep8.org/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Type Hints Documentation](https://docs.python.org/3/library/typing.html)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [PyTest Documentation](https://docs.pytest.org/)

## Next Steps

- Learn about [Testing Guide](testing.md)
- Read [Contributing Guidelines](contributing.md)
- See [Adding Features](adding-features.md)
