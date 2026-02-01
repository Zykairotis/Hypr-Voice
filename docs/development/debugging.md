# Debugging Guide

This guide covers debugging techniques, tools, and best practices for Hypr-Voice development.

## Table of Contents

1. [Debugging Philosophy](#debugging-philosophy)
2. [Logging](#logging)
3. [Common Debugging Tools](#common-debugging-tools)
4. [Debugging Techniques](#debugging-techniques)
5. [Specific Scenarios](#specific-scenarios)
6. [Performance Debugging](#performance-debugging)
7. [Remote Debugging](#remote-debugging)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)

## Debugging Philosophy

### Principles

1. **Understand Before Fixing**: Reproduce the issue first
2. **Small Steps**: Make one change at a time
3. **Verify Fixes**: Ensure fix actually resolves the issue
4. **Add Tests**: Prevent regression
5. **Document**: Record findings for future reference

### Systematic Approach

```
1. Reproduce the issue
2. Isolate the cause
3. Form hypothesis
4. Test hypothesis
5. Implement fix
6. Verify fix
7. Add tests
8. Document
```

## Logging

### Configuration

Hypr-Voice uses `loguru` for logging with structured output:

```python
from loguru import logger

# Configure logging
logger.remove()  # Remove default handler

# Add console handler with formatting
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Add file handler with rotation
logger.add(
    "logs/app_{time:YYYY-MM-DD}.log",
    rotation="00:00",  # New file at midnight
    retention="30 days",
    compression="zip",
    level="DEBUG",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
)
```

### Log Levels

```python
# DEBUG: Detailed information for diagnosing problems
logger.debug("Variable value: {}", variable)

# INFO: General information about program execution
logger.info("User logged in", extra={"user_id": 123})

# WARNING: Something unexpected happened
logger.warning("API rate limit approaching", extra={"remaining": 10})

# ERROR: Serious problem occurred
logger.error("Failed to connect to database", exc_info=True)

# CRITICAL: Very serious error
logger.critical("System shutting down due to fatal error")
```

### Structured Logging

```python
# Add extra context to logs
logger.info(
    "TTS synthesis started",
    extra={
        "text": text[:50],  # First 50 chars
        "provider": provider,
        "voice": voice,
        "text_length": len(text)
    }
)

# Output:
# 2025-01-26 10:30:45 | INFO     | services.voice:synthesize:123 - TTS synthesis started
#   extra={"text": "Hello world...", "provider": "kokoro", "voice": "af_bella", "text_length": 12}
```

### Logging Best Practices

```python
# DO: Log at appropriate levels
logger.debug("Processing request with params: {}", params)  # Debug info
logger.info("Request processed successfully")  # Important events
logger.warning("Cache miss for key: {}", key)  # Unexpected but not error
logger.error("Failed to process request", exc_info=True)  # Errors with traceback

# DON'T: Log sensitive information
logger.info("User password: {}", password)  # NEVER DO THIS
logger.debug("API key: {}", api_key)  # NEVER DO THIS

# DO: Use lazy evaluation for expensive operations
logger.debug("Expensive result: {}", lambda: expensive_computation())

# DON'T: Interpolate strings manually
logger.debug(f"Result: {expensive_function()}")  # Evaluated even if debug disabled
logger.debug("Result: {}", lambda: expensive_function())  # Lazy
```

## Common Debugging Tools

### Python Debugger (pdb)

```python
# Insert breakpoint
import pdb; pdb.set_trace()

# Or use breakpoint() (Python 3.7+)
breakpoint()

# Common pdb commands:
# - n (next): Execute next line
# - s (step): Step into function
# - c (continue): Continue execution
# - p variable: Print variable
# - pp variable: Pretty print variable
# - l (list): Show current code
# - w (where): Show stack trace
# - b line: Set breakpoint
# - cl: Clear breakpoints
# - q: Quit
```

### IPython Debugger (ipdb)

```bash
# Install
pip install ipdb

# Use in code
import ipdb; ipdb.set_trace()

# Or configure as default debugger
export PYTHONBREAKPOINT=ipdb.set_trace

# Features:
# - Tab completion
# - Syntax highlighting
# - Better object inspection
# - Color output
```

### pudb (Visual Debugger)

```bash
# Install
pip install pudb

# Use in code
import pudb; pudb.set_trace()

# Or configure
export PYTHONBREAKPOINT=pudb.set_trace

# Features:
# - Visual interface
# - Variable inspection
# - Stack view
# - Breakpoint management
```

### PyCharm Debugger

**Configuration**:
1. Run → Edit Configurations
2. Add Python configuration
3. Set script path to `src/hypr_voice/server.py`
4. Set working directory
5. Enable "Python Debug Server"

**Breakpoints**:
- Click line number to set breakpoint
- Right-click for conditional breakpoint
- Use "Evaluate Expression" to inspect variables

**Remote Debugging**:
```python
# Add to code
import pydevd_pycharm
pydevd_pycharm.settrace('localhost', port=12345, stdoutToServer=True, stderrToServer=True)
```

### VS Code Debugger

**Configuration** (`.vscode/launch.json`):
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "hypr_voice.server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
      ],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    }
  ]
}
```

## Debugging Techniques

### 1. Print Debugging

```python
# Simple but effective
print(f"DEBUG: variable = {variable}")

# Better with context
print(f"DEBUG [process_request]: Input text length = {len(text)}")

# For objects
from pprint import pprint
pprint(object.__dict__)

# For async
print(f"DEBUG: Before await {function_name}")
result = await function_name()
print(f"DEBUG: After await {function_name}, result = {result}")
```

### 2. Assertion Debugging

```python
# Use assertions to catch issues early
assert provider in TTSProvider.__members__, f"Invalid provider: {provider}"
assert len(text) > 0, "Text cannot be empty"
assert isinstance(response, dict), f"Expected dict, got {type(response)}"

# Assertions can be disabled in production with -O flag
# python -O script.py  # Disables assertions
```

### 3. Trace Debugging

```python
# Trace function calls
import sys
import trace

# Create tracer
tracer = trace.Trace(
    trace=True,
    count=False,
    ignoremods=["unittest", "trace"]
)

# Run code with tracing
tracer.run('your_function()')

# Or use sys.setprofile
def trace_calls(frame, event, arg):
    if event == 'call':
        print(f"Calling: {frame.f_code.co_name}")
    return trace_calls

sys.setprofile(trace_calls)
your_function()
sys.setprofile(None)
```

### 4. Exception Debugging

```python
# Catch and examine exceptions
try:
    result = await risky_operation()
except Exception as e:
    # Get full traceback
    import traceback
    traceback.print_exc()

    # Get exception details
    logger.error(
        "Operation failed",
        exc_info=True,
        extra={
            "error_type": type(e).__name__,
            "error_message": str(e),
            "error_args": e.args
        }
    )

    # Re-raise if needed
    raise

# Or use except clause with specific exception
except ValueError as e:
    logger.error(f"Invalid value: {e}")
except ConnectionError as e:
    logger.error(f"Connection failed: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

### 5. Performance Profiling

```python
import time
import cProfile
import pstats

# Simple timing
start = time.time()
result = await slow_function()
duration = time.time() - start
logger.info(f"Function took {duration:.2f} seconds")

# Detailed profiling
profiler = cProfile.Profile()
profiler.enable()

# Run code
result = await slow_function()

profiler.disable()

# Print stats
stats = pstats.Stats(profiler)
stats.strip_dirs()
stats.sort_stats('cumulative')
stats.print_stats(10)  # Top 10 functions

# Or use context manager
from contextlib import contextmanager

@contextmanager
def profile(name):
    profiler = cProfile.Profile()
    profiler.enable()
    yield
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    print(f"--- Profile: {name} ---")
    stats.print_stats(10)

with profile("slow_function"):
    result = await slow_function()
```

## Specific Scenarios

### Debugging Async Code

```python
# Use asyncio debug mode
import asyncio
asyncio.run(main(), debug=True)

# Or enable globally
asyncio.get_event_loop().set_debug(True)

# Check for pending tasks
async def check_pending_tasks():
    tasks = asyncio.all_tasks()
    logger.info(f"Pending tasks: {len(tasks)}")
    for task in tasks:
        logger.debug(f"Task: {task.get_name()}, done: {task.done()}")

# Detect coroutine not being awaited
import warnings
warnings.simplefilter('always', ResourceWarning)
```

### Debugging WebSockets

```python
# Log WebSocket messages
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")

    try:
        while True:
            # Log incoming
            data = await websocket.receive_text()
            logger.debug(f"WebSocket received: {data}")

            # Process
            response = await process_message(data)
            logger.debug(f"WebSocket sending: {response}")

            # Log outgoing
            await websocket.send_json(response)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        await websocket.close()
```

### Debugging TTS Issues

```python
# Test TTS with detailed logging
async def test_tts_with_debug():
    logger.info("Starting TTS test")

    # Log input
    logger.debug(f"Input text: {text}")
    logger.debug(f"Provider: {provider}")
    logger.debug(f"Voice: {voice}")

    # Step-by-step
    try:
        # Step 1: Validate
        logger.debug("Step 1: Validating input")
        if not text:
            raise ValueError("Empty text")
        logger.debug("Input validated")

        # Step 2: Initialize provider
        logger.debug("Step 2: Initializing provider")
        tts = TTSProvider(provider).instantiate()
        logger.debug("Provider initialized")

        # Step 3: Synthesize
        logger.debug("Step 3: Starting synthesis")
        start = time.time()
        result = await tts.synthesize(text, voice)
        duration = time.time() - start
        logger.debug(f"Synthesis completed in {duration:.2f}s")

        # Step 4: Verify
        logger.debug("Step 4: Verifying output")
        if not result["success"]:
            logger.error(f"Synthesis failed: {result.get('error')}")
        else:
            logger.info(f"Success: {result['audio_file']}")

        return result

    except Exception as e:
        logger.error(f"TTS test failed: {e}", exc_info=True)
        raise
```

### Debugging Memory Leaks

```python
import tracemalloc

# Start tracing
tracemalloc.start()

# Run code
result = await function_with_potential_leak()

# Get snapshot
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# Print top memory consumers
print("[Top 10]")
for stat in top_stats[:10]:
    print(stat)

# Compare snapshots
snapshot1 = tracemalloc.take_snapshot()
# ... run code ...
snapshot2 = tracemalloc.take_snapshot()

top_stats = snapshot2.compare_to(snapshot1, 'lineno')
for stat in top_stats[:10]:
    print(stat)
```

## Performance Debugging

### Profiling TTS Synthesis

```python
import time
from functools import wraps

def timing(func):
    """Decorator to time function execution."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result
    return wrapper

@timing
async def synthesize_with_timing(text: str, provider: str):
    """Synthesize speech with timing."""
    # Breakdown timing
    steps = {}

    # Step 1: Validation
    step_start = time.time()
    validate_input(text)
    steps['validation'] = time.time() - step_start

    # Step 2: Provider initialization
    step_start = time.time()
    tts = get_provider(provider)
    steps['init'] = time.time() - step_start

    # Step 3: Synthesis
    step_start = time.time()
    result = await tts.synthesize(text)
    steps['synthesis'] = time.time() - step_start

    # Log breakdown
    logger.info(f"Timing breakdown: {steps}")
    total = sum(steps.values())
    logger.info(f"Total time: {total:.2f}s")

    return result
```

### Memory Profiling

```bash
# Use memory_profiler
pip install memory_profiler

# Decorate function
from memory_profiler import profile

@profile
def memory_intensive_function():
    # Function code
    pass

# Run with profiling
python -m memory_profiler script.py
```

### CPU Profiling

```bash
# Use py-spy for profiling running process
pip install py-spy

# Profile running Python process
py-spy top --pid <PID>

# Record flame graph
py-spy record -o profile.svg --pid <PID>

# Profile specific function
py-spy record -o profile.svg -- python script.py
```

## Remote Debugging

### Debugging Remote Server

```python
# Use rpdb for remote debugging
pip install rpdb

# In your code
import rpdb
rpdb.set_trace(host="0.0.0.0", port=4444)

# Connect from local machine
telnet remote-server 4444

# Or use pdb with SSH
ssh -L 4444:localhost:4444 user@remote-server
# Then connect to localhost:4444
```

### Debugging in Docker

```dockerfile
# Dockerfile
FROM python:3.12

# Install debug tools
RUN pip install ipdb pudb py-spy

# Expose debug port
EXPOSE 4444

# Run with debug mode
CMD ["python", "-m", "ipdb", "script.py"]
```

```bash
# Connect to container
docker exec -it <container_id> bash

# Attach debugger
python -m ipdb -c continue script.py
```

## Troubleshooting Common Issues

### Issue: Port Already in Use

```bash
# Find process using port
lsof -i :8880

# Kill process
kill -9 <PID>

# Or use fuser
fuser -k 8880/tcp
```

### Issue: Import Errors

```python
# Debug import paths
import sys
print("\n".join(sys.path))

# Check where module is imported from
import hypr_voice
print(hypr_voice.__file__)

# Force reload
import importlib
importlib.reload(hypr_voice)
```

### Issue: AsyncIO Event Loop Issues

```python
# Check for running event loop
import asyncio
loop = asyncio.get_event_loop()
print(f"Running: {loop.is_running()}")

# Get all tasks
tasks = asyncio.all_tasks()
for task in tasks:
    print(f"Task: {task.get_name()}, done: {task.done()}")

# Cancel pending tasks
for task in tasks:
    if not task.done():
        task.cancel()
```

### Issue: Database Locks

```python
# Check for locks (SQLite)
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()
cursor.execute("PRAGMA database_list")
cursor.execute("PRAGMA lock_status")
print(cursor.fetchall())

# Close all connections
conn.close()
```

### Issue: Memory Growing Over Time

```python
# Monitor memory usage
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# Get detailed memory info
memory_info = process.memory_info()
print(f"RSS: {memory_info.rss / 1024 / 1024:.2f} MB")
print(f"VMS: {memory_info.vms / 1024 / 1024:.2f} MB")

# Get memory percent
print(f"Memory %: {process.memory_percent()}%")
```

## IDE Debugging Setup

### VS Code Setup

1. Install Python extension
2. Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Hypr-Voice Server",
      "type": "debugpy",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "hypr_voice.server:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload"
      ],
      "cwd": "${workspaceFolder}",
      "envFile": "${workspaceFolder}/.env",
      "console": "integratedTerminal"
    }
  ]
}
```

### PyCharm Setup

1. Run → Edit Configurations
2. Add new Python configuration
3. Script path: `src/hypr_voice/server.py`
4. Working directory: `$ProjectFileDir$`
5. Environment variables: Add from `.env`
6. Enable "Emulate terminal in output console"

## Best Practices

### DO's

1. **Use structured logging** for easy debugging
2. **Set breakpoints** strategically
3. **Examine variables** before modifying
4. **Reproduce issues** before fixing
5. **Add tests** to prevent regression
6. **Document findings** for future reference
7. **Use version control** to isolate changes

### DON'Ts

1. **Don't ignore warnings** - they often signal bugs
2. **Don't debug in production** - use staging
3. **Don't commit debug code** - remove print/breakpoints
4. **Don't guess** - verify hypotheses
5. **Don't over-optimize** - profile first
6. **Don't log sensitive data** - passwords, API keys

## Resources

- [Python Debugging Guide](https://docs.python.org/3/library/pdb.html)
- [Logging Best Practices](https://loguru.readthedocs.io/)
- [AsyncIO Debugging](https://docs.python.org/3/library/asyncio-dev.html)
- [PyCharm Debugger](https://www.jetbrains.com/help/pycharm/debugging-code.html)
- [VS Code Python Debugging](https://code.visualstudio.com/docs/python/debugging)

## Next Steps

- Read [Testing Guide](testing.md)
- Learn [Adding Features](adding-features.md)
- Review [Contributing Guidelines](contributing.md)
