# Performance Tuning Guide

Optimize Hypr-Voice for speed, efficiency, and resource usage.

## Table of Contents

- [Overview](#overview)
- [Agent Performance](#agent-performance)
- [TTS Performance](#tts-performance)
- [STT Performance](#stt-performance)
- [System Optimization](#system-optimization)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

Performance optimization areas:

| Component | Optimization | Impact |
|-----------|--------------|--------|
| **Agents** | Caching, parallel execution | High |
| **TTS** | Provider selection, streaming | Medium |
| **STT** | Opus encoding, chunking | High |
| **System** | Resource limits, cleanup | Medium |

---

## Agent Performance

### Use Appropriate Models

```yaml
# For speed (lower quality)
defaults:
  model: "claude-3-5-haiku-20241022"  # Faster
  max_tokens: 2048

# For balance
defaults:
  model: "claude-3-5-sonnet-20241022"
  max_tokens: 4096

# For quality (slower)
defaults:
  model: "claude-3-5-opus-20241022"
  max_tokens: 8096
```

### Adjust Temperature

```yaml
# Lower temperature = faster, more deterministic
defaults:
  temperature: 0.3  # Faster
  # vs
  temperature: 1.0  # More creative
```

### Use Caching

```python
config = AgentConfig(
    name="cached-agent",
    working_directory="/tmp/agents/cached",
    enable_cache=True,
    cache_ttl=3600,  # Cache for 1 hour
    skills=["file_operations"]
)
```

### Parallel Agents

```python
import asyncio

async def parallel_agents():
    """Run multiple agents in parallel"""

    tasks = []

    # Create multiple agents
    for i in range(5):
        config = AgentConfig(
            name=f"agent-{i}",
            working_directory=f"/tmp/agents/parallel-{i}",
            skills=["file_operations"]
        )

        agent_id = await client.create_agent(config)

        # Run in parallel
        task = client.instruct(agent_id, f"Task {i}")
        tasks.append(task)

    # Execute all in parallel
    results = await asyncio.gather(*tasks)
    return results
```

### Agent Pools

```python
class AgentPool:
    """Pool of reusable agents"""

    def __init__(self, pool_size: int = 5):
        self.pool_size = pool_size
        self.agents = []
        self.available = []

    async def initialize(self):
        """Initialize agent pool"""
        for i in range(self.pool_size):
            config = AgentConfig(
                name=f"pool-agent-{i}",
                working_directory=f"/tmp/agents/pool-{i}",
                skills=["file_operations", "bash_execution"]
            )
            agent_id = await client.create_agent(config)
            self.agents.append(agent_id)
            self.available.append(agent_id)

    async def acquire(self) -> str:
        """Get agent from pool"""
        while not self.available:
            await asyncio.sleep(0.1)
        return self.available.pop()

    async def release(self, agent_id: str):
        """Return agent to pool"""
        self.available.append(agent_id)

# Use agent pool
pool = AgentPool(pool_size=5)
await pool.initialize()

agent_id = await pool.acquire()
await client.instruct(agent_id, "Do work")
await pool.release(agent_id)
```

---

## TTS Performance

### Provider Selection

```python
# For speed (local)
provider = "kokoro"     # ~50ms latency

# For quality (cloud)
provider = "deepgram"    # ~100ms latency
provider = "elevenlabs"  # ~200ms latency
```

### Use Streaming

```yaml
# Enable TTS streaming
tts:
  streaming:
    enabled: true
    prebuffer_ms: 300        # Low latency
    min_chars: 50            # Stream early
    max_latency: 0.3         # 300ms max
```

### Audio Encoding

```yaml
voice:
  deepgram:
    encoding: "mp3"          # Good compression
    # vs
    encoding: "opus"         # Best compression
    # vs
    encoding: "wav"          # No compression (fastest)

  sample_rate: 24000         # Lower rate = faster
```

### Cache TTS Output

```yaml
voice:
  kokoro:
    cache_enabled: true
    cache_dir: "/tmp/kokoro_cache"

  deepgram:
    cache_enabled: true
    cache_dir: "/tmp/deepgram_cache"
```

### Batch TTS

```python
async def batch_tts():
    """Generate multiple TTS files in parallel"""

    texts = [
        "First text",
        "Second text",
        "Third text"
    ]

    # Parallel TTS generation
    tasks = [
        manager.synthesize(text, provider="kokoro")
        for text in texts
    ]

    results = await asyncio.gather(*tasks)
    return results
```

---

## STT Performance

### Use Opus Encoding

```bash
# Enable Opus for 10x faster uploads
export WISPR_FLOW_USE_OPUS=1
export WISPR_FLOW_OPUS_BITRATE=24k
```

### Optimize Chunk Size

```bash
# For speed (larger chunks)
export WISPR_FLOW_CHUNK_SECONDS=30

# For accuracy (smaller chunks)
export WISPR_FLOW_CHUNK_SECONDS=15
```

### Enable Streaming Mode

```bash
# For long recordings (60s+)
export FLOW_STREAMING_MODE=1
```

### Use Local Whisper

```python
# Configure for speed
backend:
  type: "faster_whisper"
  model_path: "tiny.en"       # Fastest
  device: "cuda"              # GPU if available

  # Faster decoding
ctranslate2:
  beam_size: 1                # Greedy (fastest)
  inter_threads: 2
  intra_threads: 4
```

### Configure for Accuracy

```python
# Configure for quality
backend:
  type: "faster_whisper"
  model_path: "medium.en"     # Better accuracy
  device: "cuda"

  # Better decoding
ctranslate2:
  beam_size: 5                # Beam search
  patience: 2.0
  inter_threads: 4
  intra_threads: 8
```

---

## System Optimization

### Resource Limits

```yaml
limits:
  max_agents: 50              # Limit concurrent agents
  max_conversation_length: 100 # Limit conversation history
  max_parallel_executions: 5   # Limit parallel tasks
```

### Cleanup Configuration

```yaml
storage:
  cleanup_after_hours: 24     # Auto-cleanup interval

  agent_data_dir: "/tmp/agents/data"
  session_dir: "/tmp/agents/sessions"
  logs_dir: "/tmp/agents/logs"
```

### Worker Configuration

```yaml
server:
  workers: 4                  # Match CPU cores
  log_level: "INFO"           # Reduce logging overhead
```

### Memory Management

```python
# Periodic cleanup
async def cleanup_agent(agent_id):
    """Clean up agent resources"""

    # Clear conversation history
    await client.clear_conversation(agent_id)

    # Delete old files
    await client.cleanup_working_directory(agent_id)

    # Remove agent if done
    await client.delete_agent(agent_id)
```

---

## Monitoring

### Performance Metrics

```python
from hypr_voice.client import RichMonitor

async def monitor_performance():
    """Monitor agent performance"""

    client = AgentClient()
    monitor = RichMonitor(client)

    # Start monitoring
    await monitor.start()

    # Get performance stats
    stats = await monitor.get_performance_stats()

    print(f"CPU: {stats['cpu_usage']}%")
    print(f"Memory: {stats['memory_usage']}MB")
    print(f"Active agents: {stats['active_agents']}")
    print(f"Queue size: {stats['queue_size']}")
```

### Custom Metrics

```python
class PerformanceTracker:
    """Track custom performance metrics"""

    def __init__(self):
        self.metrics = {}

    async def track_operation(self, name: str, operation):
        """Track operation performance"""

        start = time.time()

        try:
            result = await operation
            success = True
        except Exception as e:
            result = e
            success = False

        duration = time.time() - start

        # Record metrics
        self.metrics[name] = {
            "duration": duration,
            "success": success,
            "timestamp": time.time()
        }

        return result

# Use tracker
tracker = PerformanceTracker()

result = await tracker.track_operation(
    "agent_task",
    client.instruct(agent_id, "Do work")
)

print(f"Duration: {tracker.metrics['agent_task']['duration']}s")
```

### Profiling

```python
import cProfile
import pstats

def profile_agent():
    """Profile agent execution"""

    profiler = cProfile.Profile()
    profiler.enable()

    # Run agent
    asyncio.run(agent_task())

    profiler.disable()

    # Print stats
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

---

## Troubleshooting

### Slow Agents

**Symptoms:**
- Agents take long to respond
- High CPU usage
- Memory growth

**Solutions:**

```python
# Reduce max tokens
config = AgentConfig(
    max_tokens=2048,  # Reduce from default
    temperature=0.3   # Lower temperature
)

# Use smaller model
config = AgentConfig(
    model="claude-3-5-haiku-20241022"  # Faster model
)

# Enable caching
config = AgentConfig(
    enable_cache=True,
    cache_ttl=3600
)
```

### Memory Issues

**Symptoms:**
- Out of memory errors
- Slow performance
- System freezing

**Solutions:**

```yaml
# Reduce limits
limits:
  max_agents: 10              # Reduce from 50
  max_conversation_length: 50  # Reduce from 100

# More aggressive cleanup
storage:
  cleanup_after_hours: 6       # More frequent

# Reduce worker count
server:
  workers: 2                  # Reduce from 4
```

### TTS Latency

**Symptoms:**
- Delayed audio output
- Choppy audio
- Long waits

**Solutions:**

```yaml
# Use faster provider
voice:
  default_provider: "kokoro"  # Local, fast

# Reduce prebuffer
tts:
  streaming:
    prebuffer_ms: 300        # Reduce from 800

# Lower sample rate
voice:
  kokoro:
    sample_rate: 22050        # Reduce from 24000
```

### STT Latency

**Symptoms:**
- Delayed transcription
- Long wait times
- Timeout errors

**Solutions:**

```bash
# Enable Opus
export WISPR_FLOW_USE_OPUS=1
export WISPR_FLOW_OPUS_BITRATE=24k

# Larger chunks
export WISPR_FLOW_CHUNK_SECONDS=30

# Streaming mode
export FLOW_STREAMING_MODE=1
```

---

## Performance Benchmarks

### Agent Performance

| Configuration | Response Time | Token/s | Memory |
|---------------|---------------|---------|---------|
| Haiku (2048 tokens) | ~2s | 1024 | ~200MB |
| Sonnet (4096 tokens) | ~4s | 1024 | ~400MB |
| Opus (8096 tokens) | ~8s | 1012 | ~800MB |

### TTS Performance

| Provider | Latency | Quality | Cost |
|----------|---------|---------|------|
| Kokoro | ~50ms | Good | Free |
| Deepgram | ~100ms | Very Good | Paid |
| ElevenLabs | ~200ms | Excellent | Paid |

### STT Performance

| Mode | Latency | Accuracy | Cost |
|------|---------|----------|------|
| FLOW + Opus | ~1-2s | 97-99% | Paid |
| FLOW + WAV | ~5-10s | 97-99% | Paid |
| LOCAL (tiny) | ~1-2s | 85-90% | Free |
| LOCAL (small) | ~2-5s | 92-95% | Free |

---

## Best Practices

### For Speed

```yaml
# Use fast models
defaults:
  model: "claude-3-5-haiku-20241022"
  max_tokens: 2048
  temperature: 0.3

# Use local TTS
voice:
  default_provider: "kokoro"

# Enable Opus
WISPR_FLOW_USE_OPUS=1
```

### For Quality

```yaml
# Use quality models
defaults:
  model: "claude-3-5-opus-20241022"
  max_tokens: 8096
  temperature: 0.7

# Use premium TTS
voice:
  default_provider: "elevenlabs"

# Use FLOW STT
MODE=FLOW
```

### For Cost Efficiency

```yaml
# Use free local options
voice:
  default_provider: "kokoro"

MODE=LOCAL  # Free Whisper

# Enable caching
cache_enabled: true
```

---

## See Also

- [Configuration Reference](../../development/configuration-reference.md)
- [Voice Configuration](../../development/voice-config.md)
- [Whisper Configuration](../../development/whisper-config.md)
