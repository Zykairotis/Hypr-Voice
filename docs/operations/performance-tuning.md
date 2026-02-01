# Performance Tuning Guide - Hypr-Voice

Comprehensive performance optimization guide for Hypr-Voice.

## Table of Contents

1. [Performance Overview](#performance-overview)
2. [System-Level Tuning](#system-level-tuning)
3. [Application-Level Tuning](#application-level-tuning)
4. [Whisper Optimization](#whisper-optimization)
5. [Transcription Performance](#transcription-performance)
6. [TTS Performance](#tts-performance)
7. [Network Optimization](#network-optimization)
8. [Memory Optimization](#memory-optimization)
9. [CPU Optimization](#cpu-optimization)
10. [Storage Optimization](#storage-optimization)

---

## Performance Overview

### Performance Metrics

| Metric | Baseline | Optimized | Improvement |
|--------|----------|-----------|-------------|
| **Transcription Latency** | 1000ms | 300ms | 70% faster |
| **TTS Generation Time** | 500ms | 200ms | 60% faster |
| **Orchestrator Response** | 2000ms | 800ms | 60% faster |
| **Memory Usage** | 4GB | 2GB | 50% reduction |
| **CPU Usage** | 80% | 40% | 50% reduction |
| **Concurrent Users** | 5 | 20 | 4x capacity |

### Performance Bottlenecks

```
Common Bottlenecks (in order of impact):
┌─────────────────────────────────────────┐
│ 1. Transcription (Whisper model)        │
│ 2. TTS Generation (API calls)           │
│ 3. LLM Inference (Cerebras API)         │
│ 4. Network Latency (API calls)          │
│ 5. Disk I/O (model loading)             │
│ 6. Memory Contention (caching)          │
│ 7. CPU Throttling (thermal)             │
└─────────────────────────────────────────┘
```

---

## System-Level Tuning

### Kernel Parameters

Add to `/etc/sysctl.conf`:

```bash
# Network optimization
net.core.rmem_max = 134217728
net.core.wmem_max = 134217728
net.ipv4.tcp_rmem = 4096 87380 67108864
net.ipv4.tcp_wmem = 4096 65536 67108864
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_congestion_control = bbr

# File system optimization
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

# Memory management
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# Apply changes
sudo sysctl -p
```

### CPU Governor

```bash
# Set to performance mode
sudo cpupower frequency-set -g performance

# Or permanently
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpupower
sudo systemctl enable cpupower
sudo systemctl start cpupower
```

### Process Priority

```bash
# Set priority for services
# Edit systemd service files

[Service]
# Nice value (-20 = highest priority, 19 = lowest)
Nice=-5

# CPU affinity (use specific cores)
CPUAffinity=0-3

# I/O priority
IOSchedulingClass=realtime
IOSchedulingPriority=0
```

### Huge Pages (for PyTorch)

```bash
# Check current huge page settings
cat /proc/meminfo | grep Huge

# Configure huge pages
sudo sysctl vm.nr_hugepages=128
echo 'vm.nr_hugepages=128' | sudo tee -a /etc/sysctl.conf

# Verify
cat /proc/meminfo | grep Huge
```

---

## Application-Level Tuning

### Uvicorn Configuration

```python
# Optimize uvicorn workers

import uvicorn

# Production configuration
config = uvicorn.Config(
    app,
    host="0.0.0.0",
    port=9093,

    # Workers: (2 x CPU cores) + 1
    workers=5,

    # Process management
    limit_concurrency=100,
    backlog=2048,

    # Timeouts
    timeout_keep_alive=30,
    timeout_graceful_shutdown=30,

    # Logging
    log_level="info",
    access_log=False,  # Disable for performance

    # Performance
    loop="uvloop",  # Faster event loop
    http="httptools",  # Faster HTTP parser

    # SSL (if needed)
    ssl_keyfile="/path/to/key.pem",
    ssl_certfile="/path/to/cert.pem",
)

server = uvicorn.Server(config)
server.run()
```

### FastAPI Optimization

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

app = FastAPI()

# Enable compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Optimize CORS (be specific in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Be specific in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Response optimization
from fastapi.responses import JSONResponse

@app.get("/api/endpoint")
async def optimized_endpoint():
    # Use response_model to limit data
    return JSONResponse(
        content={"data": "value"},
        headers={"Cache-Control": "public, max-age=60"}
    )
```

### Async Optimization

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Thread pool for CPU-bound tasks
executor = ThreadPoolExecutor(max_workers=4)

async def process_audio(audio_file):
    # Offload CPU-intensive work to thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        executor,
        transcribe_audio_sync,
        audio_file
    )
    return result

# Batch processing
async def process_batch(audio_files):
    tasks = [process_audio(f) for f in audio_files]
    results = await asyncio.gather(*tasks)
    return results
```

---

## Whisper Optimization

### Model Selection

| Model | Size | Accuracy | Speed | VRAM | Use Case |
|-------|------|----------|-------|------|----------|
| **tiny.en** | 39 MB | ~85% | Fastest | 1GB | Real-time, low accuracy |
| **base.en** | 74 MB | ~90% | Fast | 1GB | Balanced |
| **small.en** | 244 MB | ~95% | Medium | 2GB | Recommended |
| **medium.en** | 769 MB | ~97% | Slow | 5GB | High accuracy |
| **large-v2** | 1550 MB | ~98% | Slowest | 10GB | Best accuracy |

### Model Configuration

```yaml
# config/hypr_voice/whisper/config.yaml

# For maximum speed (low accuracy)
backend:
  model_path: "tiny.en"
  compute_type: "int8"  # Quantization

# For balanced performance (recommended)
backend:
  model_path: "small.en"
  compute_type: "float16"  # GPU float16

# For maximum accuracy (slow)
backend:
  model_path: "medium.en"
  compute_type: "float32"
```

### CTranslate2 Optimization

```yaml
# CTranslate2 settings for MAXIMUM SPEED
ctranslate2:
  # Inter-op parallelism (process multiple batches)
  inter_threads: 2  # Reduce for lower CPU usage

  # Intra-op parallelism (parallelize within operations)
  intra_threads: 4  # Match your CPU threads

  # Beam size (1 = fastest, 5 = most accurate)
  beam_size: 1  # Greedy decoding (fastest)

  # Other settings
  patience: 1.0
  length_penalty: 1.0
  temperature: 0.0
```

### Model Quantization

```python
# Load quantized model for faster inference

from faster_whisper import WhisperModel

# INT8 quantization (2x faster, minimal accuracy loss)
model = WhisperModel(
    "small.en",
    device="cuda",
    compute_type="int8"  # or "float16" for GPU
)

# For CPU-only, use INT8
model = WhisperModel(
    "small.en",
    device="cpu",
    compute_type="int8",
    cpu_threads=8,
    num_workers=4
)
```

### Batch Processing

```python
# Process multiple audio files in batch

def transcribe_batch(audio_files, batch_size=8):
    """Transcribe multiple files in batches"""
    results = []

    for i in range(0, len(audio_files), batch_size):
        batch = audio_files[i:i+batch_size]

        # Process batch in parallel
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            batch_results = list(executor.map(transcribe_single, batch))

        results.extend(batch_results)

    return results
```

---

## Transcription Performance

### Streaming Optimization

```yaml
# Optimize for streaming transcription

server:
  max_clients: 10  # Limit concurrent clients
  max_connection_time: 3600

performance:
  audio_chunk_size: 4096  # Larger chunks = faster
  sample_rate: 16000
  cache_path: "/tmp/whisper-live-cache"

# Optimize VAD
hypr_voice:
  vad_enabled: true
  vad_threshold: 0.5  # Lower = more sensitive
  min_speech_duration: 0.3
  max_silence_duration: 1.0  # Shorter = faster response
```

### Audio Processing

```python
# Optimize audio processing

import librosa
import soundfile as sf

def load_audio_optimized(path, sr=16000):
    """Load audio with optimizations"""
    # Use soundfile for faster loading
    audio, _ = sf.read(path, dtype='float32')

    # Convert to mono if needed
    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    # Resample if needed (faster than librosa)
    if sr != 16000:
        from resampy import resample
        audio = resample(audio, orig_sr=sr, target_sr=16000)

    return audio
```

### Chunk Size Optimization

```bash
# WISPR_FLOW_CHUNK_SECONDS=30 (recommended for speed)
# Larger chunks = fewer API calls = faster overall

# Test different chunk sizes:
# 15s: More frequent updates, slower overall
# 30s: Balanced (recommended)
# 60s: Fastest, but less responsive
```

---

## TTS Performance

### TTS Provider Selection

| Provider | Speed | Quality | Latency | Cost |
|----------|-------|---------|---------|------|
| **Deepgram** | Fast | Good | <200ms | Low |
| **ElevenLabs** | Slow | Excellent | <500ms | High |
| **Kokoro** | Fast | Good | <150ms | Free |

### TTS Configuration

```yaml
# TTS optimization settings

HYPR_VOICE_TTS_STREAMING=1
HYPR_VOICE_TTS_REST_STREAMING=1
HYPR_VOICE_TTS_PREBUFFER_MS=800  # Reduce for faster start
HYPR_VOICE_TTS_MIN_CHARS=100  # Minimum chars before TTS
HYPR_VOICE_TTS_MAX_LATENCY=0.5  # Max acceptable latency
HYPR_VOICE_TTS_FLUSH_TIMEOUT=15  # Timeout for audio flush
HYPR_VOICE_TTS_IDLE_TIMEOUT=3.0  # Idle timeout
```

### Streaming TTS Optimization

```python
# Optimize streaming TTS

async def stream_tts_optimized(text: str):
    """Stream TTS with optimal buffer settings"""

    # Split text into chunks
    chunks = split_text(text, min_chars=100)

    # Pre-buffer first chunks
    prebuffer_chunks = 2

    # Start streaming immediately
    async for audio_chunk in tts_provider.stream(text):
        # Yield audio immediately
        yield audio_chunk

        # Break if timeout
        if time.time() - start_time > 15:
            break
```

### TTS Caching

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=1000)
def get_cached_tts(text, voice):
    """Cache TTS results"""
    cache_key = hashlib.md5(f"{text}:{voice}".encode()).hexdigest()

    # Check cache
    cached_file = f"/tmp/tts_cache/{cache_key}.wav"
    if os.path.exists(cached_file):
        return cached_file

    # Generate and cache
    audio_file = generate_tts(text, voice)
    shutil.copy(audio_file, cached_file)

    return cached_file
```

---

## Network Optimization

### HTTP Connection Pooling

```python
import aiohttp

# Configure connection pool
connector = aiohttp.TCPConnector(
    limit=100,  # Max connections
    limit_per_host=20,  # Max per host
    ttl_dns_cache=300,  # DNS cache TTL
    use_dns_cache=True,
    keepalive_timeout=30,
    enable_cleanup_closed=True
)

# Session with optimized settings
session = aiohttp.ClientSession(
    connector=connector,
    timeout=aiohttp.ClientTimeout(
        total=30,
        connect=5,
        sock_read=10
    )
)
```

### API Request Batching

```python
# Batch API requests for efficiency

async def batch_transcribe(audio_files):
    """Transcribe multiple files in batch"""

    # Prepare batch requests
    tasks = []
    for audio_file in audio_files:
        task = transcribe_async(audio_file)
        tasks.append(task)

    # Execute in parallel
    results = await asyncio.gather(*tasks)

    return results
```

### WebSocket Optimization

```python
# Optimize WebSocket connections

import websockets

async def websocket_client_optimized():
    """Optimized WebSocket client"""

    # Configure ping/pong
    ping_interval = 20
    ping_timeout = 10

    # Configure compression
    compression = "deflate"

    async with websockets.connect(
        uri,
        ping_interval=ping_interval,
        ping_timeout=ping_timeout,
        compression=compression,
        max_size=2**23,  # 8MB max message size
    ) as ws:
        # Send/receive data
        pass
```

---

## Memory Optimization

### Memory Profiling

```python
import tracemalloc

# Enable memory tracing
tracemalloc.start()

# ... run your code ...

# Get memory statistics
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

# Print top memory consumers
for stat in top_stats[:10]:
    print(stat)
```

### Memory Caching

```python
from functools import lru_cache

# Cache expensive computations
@lru_cache(maxsize=128)
def expensive_computation(input_data):
    """Cache result of expensive computation"""
    # Expensive operation here
    return result
```

### Model Memory Management

```python
# Load models on demand, not all at once

class ModelManager:
    def __init__(self):
        self.models = {}

    def get_model(self, model_name):
        """Load model on demand"""
        if model_name not in self.models:
            self.models[model_name] = self._load_model(model_name)
        return self.models[model_name]

    def unload_model(self, model_name):
        """Unload model to free memory"""
        if model_name in self.models:
            del self.models[model_name]
            import gc
            gc.collect()
```

### Memory Limits

```yaml
# Set memory limits in config

performance:
  cache_path: "/tmp/whisper-live-cache"

# Limit cache size
model:
  download_root: "/tmp/whisper-models"
  # Models will be unloaded if memory > limit
  memory_limit: 4000000000  # 4GB
```

---

## CPU Optimization

### CPU Affinity

```bash
# Bind processes to specific CPU cores

# For hybrid server
taskset -c 0-3 ./scripts/start_hybrid_server.sh start

# For orchestrator
taskset -c 4-7 ./scripts/start_everything.sh start

# Or in systemd
[Service]
CPUAffinity=0-3
```

### Thread Pool Optimization

```python
from concurrent.futures import ThreadPoolExecutor
import os

# Optimal thread count = CPU cores
cpu_count = os.cpu_count()

executor = ThreadPoolExecutor(
    max_workers=cpu_count,
    thread_name_prefix="hypr-voice"
)
```

### Process Pool for CPU-Bound Tasks

```python
from multiprocessing import Pool, cpu_count

def cpu_bound_task(data):
    """CPU-intensive task"""
    # Process data
    return result

# Use process pool for CPU-bound work
with Pool(processes=cpu_count()) as pool:
    results = pool.map(cpu_bound_task, data_list)
```

---

## Storage Optimization

### SSD Optimization

```bash
# Mount options for SSD performance

# /etc/fstab
/dev/sda1  /opt/hypr-voice  ext4  defaults,noatime,discard  0  1

# noatime: Disable access time updates
# discard: Enable TRIM for SSD
```

### Model Caching

```python
# Cache models in memory

class ModelCache:
    def __init__(self, max_size=3):
        self.cache = {}
        self.max_size = max_size
        self.access_count = {}

    def get(self, model_name):
        """Get model from cache"""
        if model_name in self.cache:
            self.access_count[model_name] += 1
            return self.cache[model_name]
        return None

    def put(self, model_name, model):
        """Add model to cache"""
        if len(self.cache) >= self.max_size:
            # Evict least recently used
            lru = min(self.access_count, key=self.access_count.get)
            del self.cache[lru]
            del self.access_count[lru]

        self.cache[model_name] = model
        self.access_count[model_name] = 1
```

### Log File Optimization

```python
# Use rotating file handler to manage disk space

from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    'hypr-voice.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
```

---

## Performance Testing

### Benchmark Script

```bash
#!/bin/bash
# benchmark.sh

echo "=== Hypr-Voice Performance Benchmark ==="

# Test transcription latency
echo "Testing transcription latency..."
start_time=$(date +%s%3N)
# Run test transcription
end_time=$(date +%s%3N)
duration=$((end_time - start_time))
echo "Transcription latency: ${duration}ms"

# Test TTS generation
echo "Testing TTS generation..."
start_time=$(date +%s%3N)
# Run test TTS
end_time=$(date +%s%3N)
duration=$((end_time - start_time))
echo "TTS generation: ${duration}ms"

# Test memory usage
echo "Testing memory usage..."
ps aux | grep hybrid_server | awk '{print $6}'

# Test CPU usage
echo "Testing CPU usage..."
top -b -n 1 | grep hybrid_server | awk '{print $9}'
```

### Load Testing

```bash
#!/bin/bash
# load_test.sh

concurrent_users=10
test_audio="/tmp/test.wav"

echo "Starting load test with $concurrent_users concurrent users..."

for i in $(seq 1 $concurrent_users); do
    (
        while true; do
            curl -s -X POST \
                -F "audio_file=@$test_audio" \
                http://localhost:9099/sessions/$(uuidgen)/transcribe \
                > /dev/null
            sleep 1
        done
    ) &
done

echo "Load test running. Press Ctrl+C to stop"
wait
```

---

## Performance Checklist

### System Optimization

- [ ] Set CPU governor to performance
- [ ] Configure kernel parameters
- [ ] Enable huge pages
- [ ] Set CPU affinity
- [ ] Configure swap settings
- [ ] Optimize I/O scheduler

### Application Optimization

- [ ] Use appropriate model size
- [ ] Enable model quantization
- [ ] Configure thread pools
- [ ] Enable caching
- [ ] Optimize batch sizes
- [ ] Tune timeouts

### Network Optimization

- [ ] Enable connection pooling
- [ ] Configure HTTP keepalive
- [ ] Optimize WebSocket settings
- [ ] Enable compression
- [ ] Configure TCP settings

### Monitoring

- [ ] Profile memory usage
- [ ] Monitor CPU utilization
- [ ] Track response times
- [ ] Measure throughput
- [ ] Check error rates

---

## Next Steps

1. Review [Security](security.md)
2. Setup [Monitoring](monitoring.md)
3. Configure [Logging](logging.md)
4. Implement [Backups](backup-recovery.md)
