# Developer Documentation

Welcome to the Hypr-Voice developer documentation! This section contains comprehensive guides for developing, testing, and contributing to the Hypr-Voice project.

## Quick Links

- [Development Setup](setup.md) - Get your development environment running
- [Code Structure](code-structure.md) - Understand the codebase organization
- [Coding Standards](coding-standards.md) - Learn our coding conventions
- [Testing Guide](testing.md) - How to write and run tests
- [Contributing](contributing.md) - Contribution workflow and guidelines
- [Adding Features](adding-features.md) - Guide for implementing new features
- [Debugging](debugging.md) - Debugging techniques and tools

## Getting Started

### New Developers

If you're new to the project, follow these guides in order:

1. **[Development Setup](setup.md)** - Set up your development environment
2. **[Code Structure](code-structure.md)** - Understand how the code is organized
3. **[Coding Standards](coding-standards.md)** - Learn our coding conventions
4. **[Testing Guide](testing.md)** - Understand our testing approach

### First Contribution

Ready to contribute? Start here:

1. **[Contributing Guidelines](contributing.md)** - Learn the contribution workflow
2. **[Adding Features](adding-features.md)** - How to implement features
3. **[Debugging](debugging.md)** - Debugging techniques when things go wrong

## Documentation Index

### Core Guides

| Document | Description | Audience |
|----------|-------------|----------|
| [Setup](setup.md) | Environment setup and configuration | All developers |
| [Code Structure](code-structure.md) | Codebase organization and architecture | All developers |
| [Coding Standards](coding-standards.md) | Style guide and conventions | All developers |
| [Testing](testing.md) | Testing practices and tools | All developers |
| [Contributing](contributing.md) | Contribution workflow | Contributors |
| [Adding Features](adding-features.md) | Feature development guide | Feature developers |
| [Debugging](debugging.md) | Debugging techniques | All developers |

## Development Workflow

### 1. Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/Hypr-Voice.git
cd Hypr-Voice
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,all]"
```

### 2. Develop

```bash
# Create branch
git checkout -b feature/your-feature

# Make changes
# Format code
black src/ tests/
isort src/ tests/

# Run tests
pytest

# Run with coverage
pytest --cov=src/hypr_voice --cov-report=html
```

### 3. Contribute

```bash
# Commit changes
git add .
git commit -m "feat(scope): description"

# Push and create PR
git push origin feature/your-feature
```

## Key Concepts

### Architecture

Hypr-Voice is built as a **multi-agent voice orchestration system**:

- **FastAPI**: Web framework for REST/WebSocket APIs
- **Async/Await**: Non-blocking I/O throughout
- **Event-Driven**: Agents respond to events and messages
- **Modular Services**: TTS, STT, LLMs as independent services

### Core Components

```
┌─────────────────────────────────────────┐
│         FastAPI Server (server.py)      │
├─────────────────────────────────────────┤
│  ┌──────────────┐  ┌─────────────────┐ │
│  │  Orchestrator│  │ Voice Orch.     │ │
│  └──────────────┘  └─────────────────┘ │
├─────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────────────┐ │
│  │ TTS  │  │ STT  │  │   Agents     │ │
│  └──────┘  └──────┘  └──────────────┘ │
└─────────────────────────────────────────┘
```

### Services

- **TTS**: Text-to-speech (Kokoro, Deepgram, ElevenLabs)
- **STT**: Speech-to-text (Whisper, Whisper-Live)
- **Agents**: AI agents (Claude, Gemini, Custom)
- **Orchestrator**: Coordinates agents and services

## Development Tools

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint
flake8 src/ tests/

# Type check
mypy src/
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/hypr_voice

# Run specific test
pytest tests/test_specific.py

# Run async tests
pytest -m asyncio
```

### Debugging

```bash
# Use pdb
import pdb; pdb.set_trace()

# Use ipdb
import ipdb; ipdb.set_trace()

# Use pudb (visual)
import pudb; pudb.set_trace()
```

## Common Tasks

### Add New TTS Provider

1. Create provider class in `services/voice/providers/`
2. Register in `TTSProvider` enum
3. Implement in `UniversalTTS`
4. Add tests in `tests/test_tts.py`
5. Update documentation

### Add New Agent

1. Create agent in `agents/`
2. Register in `agent_definitions.py`
3. Add to orchestrator
4. Write tests
5. Document usage

### Add API Endpoint

1. Define route in `server.py`
2. Create request/response models
3. Implement handler
4. Add authentication if needed
5. Write tests
6. Update API docs

### Debug Issue

1. Enable debug logging
2. Reproduce issue
3. Add breakpoints
4. Inspect variables
5. Form hypothesis
6. Test hypothesis
7. Implement fix
8. Add tests

## Best Practices

### Code Style

- Follow [PEP 8](https://pep8.org/)
- Use type hints for public APIs
- Write docstrings (Google style)
- Keep functions < 50 lines
- Use async/await for I/O

### Testing

- Write tests before implementation (TDD)
- Aim for >80% coverage
- Test error paths
- Use fixtures for setup
- Mock external dependencies

### Documentation

- Document public APIs
- Add usage examples
- Keep README up to date
- Comment complex logic
- Explain "why" not "what"

## Getting Help

### Resources

- **Documentation**: [Full docs](../)
- **API Reference**: [API docs](../api/)
- **Examples**: [Code examples](../examples/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/Hypr-Voice/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/Hypr-Voice/discussions)

### Asking Questions

1. Search existing issues and docs
2. Check the troubleshooting guides
3. Ask in GitHub Discussions
4. Open an issue with bug report template

### Reporting Bugs

Use the bug report template in GitHub Issues:

- Describe the problem
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Logs and error messages

## Contributing

We welcome contributions! Please read:

1. [Contributing Guidelines](contributing.md)
2. [Coding Standards](coding-standards.md)
3. [Testing Guide](testing.md)

### Contribution Types

- Bug fixes
- New features
- Documentation improvements
- Performance improvements
- Test enhancements
- Code refactoring

## Additional Resources

### Internal

- [Project README](../../README.md)
- [User Guide](../user/)
- [Operations Guide](../operations/)
- [API Documentation](../api/)

### External

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [PyTest Docs](https://docs.pytest.org/)
- [AsyncIO Docs](https://docs.python.org/3/library/asyncio.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

## Changelog

See [CHANGELOG.md](../../CHANGELOG.md) for version history and changes.

## License

See [LICENSE](../../LICENSE) for licensing information.

---

**Happy coding!** 🚀

For questions or feedback, please open an issue or discussion on GitHub.
