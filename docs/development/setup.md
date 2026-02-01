# Development Environment Setup

This guide will help you set up a complete development environment for Hypr-Voice, including all dependencies, tools, and configurations needed for active development.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Python Environment](#python-environment)
4. [Frontend Setup](#frontend-setup)
5. [Development Tools](#development-tools)
6. [Configuration](#configuration)
7. [Verification](#verification)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Arch, Ubuntu, Debian) or macOS
- **Python**: 3.10 or higher (3.12 recommended)
- **Node.js**: 18.x or higher (for frontend)
- **Memory**: Minimum 8GB RAM (16GB recommended for ML workloads)
- **Storage**: 10GB free space for models and dependencies

### Required System Packages

#### Arch Linux
```bash
sudo pacman -S python python-pip python-virtualenv nodejs npm \
    ffmpeg pulseaudio alsa-utils portaudio git \
    base-devel cmake gcc gcc-libs
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv nodejs npm \
    ffmpeg pulseaudio-utils alsa-utils portaudio19-dev git \
    build-essential cmake gcc g++
```

#### macOS
```bash
brew install python@3.12 node ffmpeg portaudio git cmake
```

### Optional but Recommended

- **CUDA/ROCm**: For GPU acceleration with PyTorch
- **Docker**: For containerized development
- **CodeQL**: For security analysis
- **shellcheck**: For script linting

## Initial Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Hypr-Voice.git
cd Hypr-Voice
```

### 2. Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional (for enhanced features)
OPENAI_API_KEY=your_openai_api_key_here
DEEPGRAM_API_KEY=your_deepgram_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Development settings
HYPR_VOICE_LOG_LEVEL=DEBUG
HYPR_VOICE_RUNTIME_DIR=./runtime
```

### 3. Runtime Directories

Create runtime directories:

```bash
python -c "from src.hypr_voice.paths import ensure_runtime_directories; ensure_runtime_directories()"
```

Or manually:

```bash
mkdir -p runtime/{logs,audio,tts,databases,cache}
```

## Python Environment

### Option 1: Using Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install in development mode
pip install -e ".[dev,all]"
```

### Option 2: Using pip Directly

```bash
# Install core dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -e ".[dev]"
```

### Option 3: Using Poetry (Alternative)

```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install project
poetry install --all-extras

# Activate shell
poetry shell
```

## Frontend Setup

The web UI is built with Next.js 13+ and requires Node.js.

```bash
cd web-ui

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local

# Build for development
npm run dev
```

For production builds:

```bash
npm run build
npm start
```

## Development Tools

### Code Formatting

```bash
# Install formatters
pip install black isort

# Format code
black src/ tests/
isort src/ tests/
```

### Linting

```bash
# Run flake8
flake8 src/ tests/

# Run mypy for type checking
mypy src/

# Run all checks together
npm run lint  # or
python -m flake8 && python -m mypy src/
```

### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock

# Run all tests
pytest

# Run specific test file
pytest tests/test_specific.py

# Run with coverage
pytest --cov=src/hypr_voice --cov-report=html

# Run specific test
pytest tests/test_specific.py::test_function_name
```

## Configuration

### Python Configuration

Edit `pyproject.toml` for project-level settings:

```toml
[tool.black]
line-length = 100
target-version = ["py310", "py311", "py312"]

[tool.isort]
profile = "black"
line_length = 100

[tool.mypy]
python_version = "3.10"
ignore_missing_imports = true
```

### Application Configuration

Main config file: `config/hypr_voice/config.yaml`

```yaml
# Example configuration
agent:
  model: claude-sonnet-4-5
  max_turns: 20
  timeout: 120

voice:
  tts_provider: kokoro  # or deepgram, elevenlabs
  tts_voice: af_bella
  whisper_url: http://localhost:9099

logging:
  level: INFO
  format: json
```

### IDE Configuration

#### VS Code

Create `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm

1. Settings → Project → Python Interpreter
2. Add `.venv` as project interpreter
3. Enable Black and isort in Settings → Tools → External Tools

## Verification

### Verify Python Installation

```bash
python -c "import hypr_voice; print(hypr_voice.__version__)"
```

### Verify Dependencies

```bash
pip list | grep -E "(fastapi|anthropic|pydantic|torch)"
```

### Run Health Check

```bash
python -c "
from hypr_voice.paths import ensure_runtime_directories
ensure_runtime_directories()
print('✅ Runtime directories ready')

from hypr_voice.server import app
print('✅ Server imports successfully')
"
```

### Run Tests

```bash
# Quick smoke test
pytest tests/ -v -k "test_basic" --maxfail=3

# Full test suite
pytest --cov
```

## Troubleshooting

### Port Already in Use

If port 8880 (Kokoro TTS) or 9099 (Whisper) is in use:

```bash
# Find process using port
lsof -i :8880

# Kill process
kill -9 <PID>
```

### Audio Device Issues

```bash
# Test audio device
aplay -l  # List playback devices
arecord -l  # List recording devices

# Test audio playback
speaker-test -t wav -c 2

# Fix permissions
usermod -a -G audio $USER  # Add to audio group
```

### CUDA/GPU Issues

```bash
# Check CUDA availability
python -c "import torch; print(torch.cuda.is_available())"

# Install specific CUDA version
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

### Import Errors

```bash
# Reinstall in editable mode
pip install -e ".[dev,all]"

# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name '*.pyc' -delete
```

### Frontend Build Issues

```bash
# Clear Next.js cache
cd web-ui
rm -rf .next node_modules
npm install
npm run dev
```

## Development Workflow

### Daily Development

```bash
# Activate environment
source .venv/bin/activate

# Pull latest changes
git pull origin main

# Update dependencies
pip install -e ".[dev,all]"

# Run tests
pytest

# Start development server
python -m hypr_voice.server
```

### Running Services

```bash
# Terminal 1: Kokoro TTS server
python Kokoro-FastAPI/server.py --host 0.0.0.0 --port 8880

# Terminal 2: Whisper server
python -m wisper_flow.server --port 9099

# Terminal 3: Hypr-Voice orchestrator
python -m hypr_voice.server

# Terminal 4: Web UI
cd web-ui && npm run dev
```

## Next Steps

- Read [Code Structure](code-structure.md) to understand the project layout
- Review [Coding Standards](coding-standards.md) for contribution guidelines
- Check [Testing Guide](testing.md) to learn how to write tests
- See [Adding Features](adding-features.md) for feature development

## Additional Resources

- [Project README](../../README.md)
- [API Documentation](../api/)
- [User Guide](../user/)
- [Operations Guide](../operations/)
