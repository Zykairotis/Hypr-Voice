# Hypr-Voice Comprehensive Optimization Plan

**Generated:** 2026-01-25
**Based on:** Flow mode analysis, reorganization report, and optimization summary
**Target:** Sub-second latency with high accuracy

---

## Executive Summary

Hypr-Voice has achieved impressive performance with RAW mode (2s latency), but significant optimization opportunities remain. This plan synthesizes findings from three major areas:

1. **Flow Mode Integration**: Direct mode bypasses HTTP server for 50-200ms savings
2. **Codebase Reorganization**: Proper Python package structure enables better caching
3. **Existing Optimizations**: VAD trimming, hallucination filtering, context engine improvements

**Current Performance Baseline:**
- RAW Mode: ~2s (release-to-paste)
- Flow Mode: ~2-5s (network-dependent)
- First recording: ~15s → ~2s (7.5x improvement already achieved)

**Target Performance:**
- **Target 1**: <500ms for cached/common phrases
- **Target 2**: <1s for standard transcriptions
- **Target 3**: <2s for long-form content (>30s)

**Projected Overall Improvement: 2-4x faster across the board**

---

## Quick Wins (Week 1) - Easy, High Impact

### 1. Enable Direct Flow Mode by Default ⚡
**Impact:** 50-200ms reduction per transcription
**Complexity:** Trivial (already implemented, just verify enabled)
**Risk:** Low

**Current State:** Direct mode (`FLOW_DIRECT_MODE=1`) is already default but may not be consistently used

**Implementation:**
```bash
# Verify .env has this setting
grep FLOW_DIRECT_MODE .env
# Should output: FLOW_DIRECT_MODE=1 (or unset, which defaults to 1)
```

**Verification:**
```python
# Check logs for direct mode usage
grep "Direct Wispr Flow" logs/hybrid_server.log
```

**Expected Savings:** 50-200ms per request

---

### 2. Implement Request Coalescing for Sequential Audio 🎯
**Impact:** 30-50% reduction for back-to-back recordings
**Complexity:** Low (add queue/debounce logic)
**Risk:** Low

**Problem:** When users make quick corrections, each transcription fires a separate API call

**Solution:** Implement a 200-300ms coalescing window

```python
# In hybrid_server.py
class AudioRequestCoalescer:
    def __init__(self, debounce_ms=250):
        self.pending_requests = []
        self.debounce_ms = debounce_ms
        self.timer = None

    async def add_request(self, audio_data):
        self.pending_requests.append(audio_data)
        if self.timer:
            self.timer.cancel()
        self.timer = asyncio.create_task(self._process_after_delay())

    async def _process_after_delay(self):
        await asyncio.sleep(self.debounce_ms / 1000)
        # Merge audio chunks and transcribe once
        merged = self._merge_audio(self.pending_requests)
        result = await transcribe(merged)
        self.pending_requests.clear()
        return result
```

**Expected Savings:** 30-50% for rapid-fire dictation

---

### 3. Aggressive Silence Pre-Trimming 🎙️
**Impact:** 10-20% faster for recordings with leading/trailing silence
**Complexity:** Low (VAD already implemented, just make more aggressive)
**Risk:** Medium (may cut off soft speech)

**Current State:** VAD level 2 (balanced)

**Optimization:**
```python
# In hybrid_server.py - enhance VAD trimming
def aggressive_trim_silence(audio, sample_rate=16000):
    """
    Aggressively trim silence using VAD level 3.

    Returns trimmed audio with minimal padding (50ms vs 200ms).
    """
    vad = webrtcvad.Vad(3)  # Level 3 - aggressive
    padding_samples = int(0.05 * sample_rate)  # 50ms padding

    # Trim silence with tight padding
    # ... implementation ...
```

**Environment Variable:**
```bash
# Add to .env
WISPR_FLOW_SILENCE_PAD_MS=50  # Reduce from 200ms default
```

**Expected Savings:** 100-500ms for typical recordings

---

### 4. Cache Warmup on Startup 🔥
**Impact:** 200-500ms faster first request
**Complexity:** Low
**Risk:** Low

**Current State:** First request pays cold-start penalty

**Solution:** Pre-warm connections on server start

```python
# In hybrid_server.py startup sequence
async def warmup_transcription_service():
    """Fire a warmup request during server initialization"""
    logger.info("Warming up transcription service...")

    # Create minimal test audio (1 second of silence)
    test_audio = generate_test_audio(duration=1.0)

    # Fire and forget warmup
    asyncio.create_task(transcribe_warmup(test_audio))

# Call this in server startup
@app.on_event("startup")
async def startup_event():
    await warmup_transcription_service()
```

**Expected Savings:** 200-500ms on first request

---

### 5. Optimize Audio Chunk Size 📊
**Impact:** 15-25% fewer API calls for long audio
**Complexity:** Low (configuration change)
**Risk:** Low

**Current State:** 30-second chunks (already optimized)

**Further Optimization:**
```bash
# In .env - slightly larger chunks
WISPR_FLOW_CHUNK_SECONDS=35  # Up from 30
WISPR_FLOW_CHUNK_OVERLAP=0.3  # Reduce overlap from 0.5
```

**Expected Savings:** 10-15% for long recordings (>60s)

---

## Medium-Term Improvements (Weeks 2-4) - Moderate Complexity

### 6. Implement Response Streaming 🌊
**Impact:** 300-800ms perceived latency improvement
**Complexity:** Medium (API changes)
**Risk:** Medium

**Problem:** Users wait for full transcription before seeing any text

**Solution:** Stream results as they arrive

```python
# In hybrid_server.py
async def transcribe_streaming(audio_data):
    """
    Stream transcription results as they arrive.
    Returns async generator yielding partial results.
    """
    async for chunk in flow_client.transcribe_stream(audio_data):
        yield {
            "text": chunk["text"],
            "is_final": chunk["is_final"],
            "confidence": chunk.get("confidence", 0.0)
        }

# WebSocket endpoint for streaming
@websocket.websocket("/ws/transcribe/stream")
async def websocket_stream(websocket: WebSocket):
    await websocket.accept()
    audio_data = await websocket.receive_bytes()

    async for result in transcribe_streaming(audio_data):
        await websocket.send_json(result)
```

**Frontend Integration:**
```typescript
// Display text as it streams in
ws.onmessage = (event) => {
  const result = JSON.parse(event.data);
  displayText(result.text);  // Show partial results
  if (result.is_final) {
    finalizeText(result.text);
  }
};
```

**Expected Savings:** 300-800ms perceived latency

---

### 7. Implement Vocabulary Caching 💾
**Impact:** 20-40% faster for repeated technical terms
**Complexity:** Medium
**Risk:** Low

**Problem:** Custom vocabulary is reprocessed on every request

**Solution:** Cache vocabulary-enhanced prompts

```python
class VocabularyCache:
    def __init__(self, max_size=1000):
        self.cache = LRUCache(max_size)
        self.stats = {"hits": 0, "misses": 0}

    def get_enhanced_prompt(self, vocabulary_words, app_context):
        """Get cached prompt or compute and cache"""
        key = self._make_key(vocabulary_words, app_context)

        if key in self.cache:
            self.stats["hits"] += 1
            return self.cache[key]

        self.stats["misses"] += 1
        prompt = self._build_prompt(vocabulary_words, app_context)
        self.cache[key] = prompt
        return prompt

# Use in transcription flow
vocab_cache = VocabularyCache()
enhanced_prompt = vocab_cache.get_enhanced_prompt(
    dictionary_words,
    app_type
)
```

**Expected Savings:** 50-150ms for technical content

---

### 8. Parallel Audio Processing 🔀
**Impact:** 40-60% faster for long recordings
**Complexity:** Medium
**Risk:** Medium (resource intensive)

**Problem:** Long audio files process sequentially

**Solution:** Split and process chunks in parallel

```python
# Already implemented in wisper-flow/transcribe.py
# Just need to ensure it's being used consistently

async def transcribe_parallel(audio_path, max_workers=3):
    """
    Split audio into overlapping chunks and transcribe in parallel.
    """
    duration = get_audio_duration(audio_path)

    if duration < MAX_CHUNK_DURATION:
        return await transcribe_single(audio_path)

    # Split into chunks
    chunks = split_audio_with_overlap(
        audio_path,
        chunk_duration=MAX_CHUNK_DURATION,
        overlap=OVERLAP_DURATION
    )

    # Process in parallel
    tasks = [transcribe_single(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    # Merge results
    return merge_transcripts(results)
```

**Configuration:**
```bash
# In .env
WISPR_FLOW_PARALLEL_CHUNKS=3  # Max parallel workers
```

**Expected Savings:** 40-60% for audio >60s

---

### 9. Optimize Model Loading Strategy 🧠
**Impact:** 1-2s faster startup, 200MB RAM savings
**Complexity:** Medium
**Risk:** Low

**Problem:** Whisper model loads even in FLOW mode (wastes RAM)

**Current State:** Model already skipped in FLOW mode (good!)

**Additional Optimization:** Lazy load local model

```python
# In hybrid_server.py
class LazyWhisperModel:
    def __init__(self):
        self._model = None
        self._model_lock = asyncio.Lock()

    async def get_model(self):
        """Load model on first use"""
        if self._model is None:
            async with self._model_lock:
                # Double-check pattern
                if self._model is None:
                    logger.info("Loading Whisper model...")
                    self._model = WhisperModel(
                        model_size="small.en",
                        device="cuda" if torch.cuda.is_available() else "cpu"
                    )
        return self._model

# Use lazy model
whisper = LazyWhisperModel()
model = await whisper.get_model()  # Only loads when needed
```

**Expected Savings:** 1-2s startup in LOCAL mode

---

### 10. Implement Audio Format Optimization 🎵
**Impact:** 50-70% faster uploads
**Complexity:** Medium
**Risk:** Low

**Current State:** Opus encoding already enabled (5x faster)

**Additional Optimization:** Use更低 bitrate

```bash
# In .env - optimize Opus settings
WISPR_FLOW_OPUS_BITRATE=16k  # Down from 24k (smaller payload)
WISPR_FLOW_USE_OPUS=1        # Already enabled
```

**Expected Savings:** 50-100ms upload time

---

## Long-Term Architectural Changes (Month 2+) - High Impact

### 11. Implement Edge Caching for Common Phrases 🗄️
**Impact:** <100ms for 80% of common phrases
**Complexity:** High
**Risk:** High (privacy concerns)

**Problem:** Common phrases ("yes", "no", "ok", "thank you") are re-transcribed

**Solution:** Pre-compute and cache locally

```python
class PhraseCache:
    """Local cache for common phrases"""

    def __init__(self):
        self.common_phrases = {
            "yes": "Yes",
            "no": "No",
            "ok": "OK",
            "thank you": "Thank you",
            # ... pre-seeded with 100-200 common phrases
        }

    async def recognize(self, audio):
        """
        Check audio against common phrase fingerprints.
        Returns cached result if match found.
        """
        fingerprint = self._fingerprint(audio)
        if fingerprint in self.common_phrases:
            return self.common_phrases[fingerprint]

        # Fall back to full transcription
        return await self._transcribe_full(audio)

    def _fingerprint(self, audio):
        """Generate audio fingerprint for matching"""
        # Use fast MFCC or similar
        return compute_mfcc(audio)
```

**Privacy Consideration:** Store only fingerprints, not audio

**Expected Savings:** 200-400ms for common phrases

---

### 12. Implement Hybrid Local/Cloud Routing 🔄
**Impact:** 30-50% faster overall (intelligent routing)
**Complexity:** High
**Risk:** Medium

**Problem:** All audio goes to cloud, even simple local transcriptions

**Solution:** Route simple audio locally, complex to cloud

```python
class HybridRouter:
    """Intelligently route between local and cloud transcription"""

    async def route(self, audio, context):
        """
        Decide whether to use local Whisper or cloud Flow.

        Factors:
        - Audio duration (<5s → local)
        - Vocabulary complexity (low → local)
        - Network latency (high → local)
        - User preference (accuracy vs speed)
        """

        # Short and simple → local
        if duration < 5 and not context.has_complex_vocab:
            return await self._transcribe_local(audio)

        # Long or complex → cloud
        return await self._transcribe_flow(audio, context)
```

**Routing Heuristics:**
- Duration <5s AND no custom vocabulary → Local
- Network latency >200ms → Local
- Custom vocabulary OR app_type=code → Cloud
- User explicitly requested accuracy → Cloud

**Expected Savings:** 200-500ms average

---

### 13. Implement Predictive Prefetching 🔮
**Impact:** 0ms perceived latency (results ready before release)
**Complexity:** High
**Risk:** High (may waste API calls)

**Problem:** User waits after releasing record button

**Solution:** Start transcription while user is still speaking

```python
class PredictiveTranscriber:
    """Start transcription before user finishes speaking"""

    def __init__(self):
        self.prefetch_window = 1.0  # Start 1s before expected end
        self.buffer = AudioBuffer()

    async def on_audio_chunk(self, chunk):
        """Called as audio is being recorded"""
        self.buffer.append(chunk)

        # If we have enough audio and user likely finishing
        if self.buffer.duration > self.prefetch_window:
            if self._detect_ending_soon():
                # Start transcription in background
                audio_so_far = self.buffer.get_audio()
                asyncio.create_task(
                    self._prefetch_transcription(audio_so_far)
                )

    def _detect_ending_soon(self):
        """
        Heuristics to detect user likely finishing:
        - Long pause (>500ms)
        - Falling intonation
        - Typical phrase length reached
        """
        # ... implementation ...
```

**Expected Savings:** 500-1000ms perceived latency

---

### 14. Implement Multi-Model Ensemble 🎯
**Impact:** 5-10% accuracy improvement, 10-20% latency reduction
**Complexity:** High
**Risk:** High (complexity)

**Problem:** Single model may not be optimal for all audio types

**Solution:** Use multiple models and pick best result

```python
class EnsembleTranscriber:
    """Run multiple models, pick best result"""

    async def transcribe(self, audio):
        """
        Run local Whisper and cloud Flow in parallel.
        Pick best result based on confidence and heuristics.
        """
        results = await asyncio.gather(
            self._transcribe_local(audio),
            self._transcribe_flow(audio),
            return_exceptions=True
        )

        # Pick best result
        best = self._select_best(results)
        return best

    def _select_best(self, results):
        """
        Select best result based on:
        - Confidence score
        - Vocabulary match
        - Length合理性
        - Punctuation quality
        """
        # ... implementation ...
```

**Expected Savings:** 10-20% latency (parallel processing), 5-10% accuracy

---

### 15. Implement Continuous Learning Loop 📚
**Impact:** 5-15% accuracy improvement over time
**Complexity:** Very High
**Risk:** Very High (privacy, complexity)

**Problem:** System doesn't learn from user corrections

**Solution:** Learn from user edits

```python
class LearningFeedbackLoop:
    """Learn from user corrections to improve accuracy"""

    async def on_user_edit(self, original, corrected):
        """
        User edited transcription → learn from correction.

        Update:
        - Vocabulary preferences
        - Phrase frequency
        - Common mistakes
        """
        # Extract differences
        edits = self._diff(original, corrected)

        # Update vocabulary
        for edit in edits.new_words:
            self.vocabulary.increment_frequency(edit)

        # Learn common corrections
        self.correction_model.learn(original, corrected)

    async def suggest_vocabulary(self, context):
        """
        Suggest vocabulary words based on learning.
        """
        return self.vocabulary.get_top_words(context, limit=50)
```

**Privacy Consideration:** All learning stays local, never sent to cloud

**Expected Savings:** 5-15% accuracy → fewer corrections needed

---

## Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
**Target:** 20-30% overall latency reduction

- [x] Verify Direct Flow Mode enabled
- [ ] Implement request coalescing (Day 1-2)
- [ ] Aggressive silence trimming (Day 2-3)
- [ ] Cache warmup on startup (Day 3-4)
- [ ] Optimize chunk sizes (Day 4-5)

**Success Metrics:**
- Average latency: 2s → 1.5s
- P95 latency: 3s → 2.2s
- First request: 2s → 1.5s

---

### Phase 2: Medium-Term (Weeks 2-4)
**Target:** 40-50% total latency reduction from baseline

- [ ] Response streaming (Week 2)
- [ ] Vocabulary caching (Week 2)
- [ ] Parallel processing (Week 3)
- [ ] Lazy model loading (Week 3)
- [ ] Audio format optimization (Week 4)

**Success Metrics:**
- Average latency: 1.5s → 1s
- P95 latency: 2.2s → 1.5s
- Long audio (>60s): 5s → 2s

---

### Phase 3: Long-Term (Month 2+)
**Target:** Sub-second latency for 80% of requests

- [ ] Edge caching for common phrases (Month 2)
- [ ] Hybrid local/cloud routing (Month 2-3)
- [ ] Predictive prefetching (Month 3)
- [ ] Multi-model ensemble (Month 3-4)
- [ ] Continuous learning (Month 4+)

**Success Metrics:**
- Average latency: 1s → 600ms
- P95 latency: 1.5s → 1s
- Common phrases: 1s → 100ms

---

## Performance Targets Summary

| Metric | Current | Phase 1 | Phase 2 | Phase 3 | Improvement |
|--------|---------|---------|---------|---------|-------------|
| **Average Latency** | 2000ms | 1500ms | 1000ms | 600ms | **3.3x faster** |
| **P95 Latency** | 3000ms | 2200ms | 1500ms | 1000ms | **3x faster** |
| **First Request** | 2000ms | 1500ms | 1000ms | 600ms | **3.3x faster** |
| **Common Phrases** | 2000ms | 1500ms | 1000ms | 100ms | **20x faster** |
| **Long Audio (>60s)** | 5000ms | 4000ms | 2000ms | 1200ms | **4.2x faster** |

---

## Risk Matrix

| Optimization | Impact | Complexity | Risk | Priority |
|--------------|--------|------------|------|----------|
| Direct Flow Mode | High | Low | Low | **P0** |
| Request Coalescing | High | Low | Low | **P0** |
| Aggressive VAD | Medium | Low | Medium | **P1** |
| Cache Warmup | Medium | Low | Low | **P0** |
| Chunk Optimization | Medium | Low | Low | **P1** |
| Response Streaming | High | Medium | Medium | **P1** |
| Vocabulary Cache | Medium | Medium | Low | **P1** |
| Parallel Processing | High | Medium | Medium | **P1** |
| Lazy Model Load | Medium | Medium | Low | **P2** |
| Audio Optimization | Low | Medium | Low | **P2** |
| Edge Caching | High | High | High | **P2** |
| Hybrid Routing | High | High | Medium | **P2** |
| Predictive Prefetch | Very High | High | High | **P3** |
| Model Ensemble | Medium | High | High | **P3** |
| Learning Loop | Medium | Very High | Very High | **P3** |

**Legend:**
- **P0**: Implement immediately (Week 1)
- **P1**: Implement in short-term (Weeks 2-4)
- **P2**: Implement in medium-term (Month 2)
- **P3**: Implement in long-term (Month 3+)

---

## Monitoring & Metrics

### Key Performance Indicators (KPIs)

```python
# Add to hybrid_server.py
class PerformanceMetrics:
    """Track transcription performance metrics"""

    def __init__(self):
        self.metrics = {
            "latency_ms": [],
            "audio_duration_sec": [],
            "processing_time_ms": [],
            "cache_hit_rate": 0.0,
            "error_rate": 0.0,
            "vocabulary_usage": [],
        }

    def record_transcription(self, duration, processing_time, cache_hit):
        """Record metrics for each transcription"""
        self.metrics["latency_ms"].append(processing_time)
        self.metrics["audio_duration_sec"].append(duration)

        if cache_hit:
            self.metrics["cache_hit_rate"] = (
                self.metrics["cache_hit_rate"] * 0.9 + 1.0 * 0.1
            )
        else:
            self.metrics["cache_hit_rate"] *= 0.9

    def get_summary(self):
        """Get performance summary"""
        return {
            "avg_latency_ms": np.mean(self.metrics["latency_ms"]),
            "p95_latency_ms": np.percentile(self.metrics["latency_ms"], 95),
            "p99_latency_ms": np.percentile(self.metrics["latency_ms"], 99),
            "cache_hit_rate": self.metrics["cache_hit_rate"],
            "total_transcriptions": len(self.metrics["latency_ms"]),
        }
```

### Prometheus Integration (Optional)

```python
# Expose metrics for Prometheus
from prometheus_client import Histogram, Gauge

TRANSCRIPTION_LATENCY = Histogram(
    'hypr_voice_transcription_latency_ms',
    'Transcription latency in milliseconds',
    ['mode', 'app_type']
)

CACHE_HIT_RATE = Gauge(
    'hypr_voice_cache_hit_rate',
    'Vocabulary cache hit rate'
)

# Use in code
TRANSCRIPTION_LATENCY.labels(mode='flow', app_type='code').observe(processing_time)
CACHE_HIT_RATE.set(metrics.cache_hit_rate)
```

---

## Configuration Checklist

### .env Optimizations
```bash
# ==============================================================================
# OPTIMIZATION SETTINGS
# ==============================================================================

# Direct mode (already default, verify)
FLOW_DIRECT_MODE=1

# Silence trimming (more aggressive)
WISPR_FLOW_SILENCE_PAD_MS=50  # Default 200
WISPR_FLOW_SILENCE_THRESHOLD=0.015  # Default 0.01

# Chunk optimization
WISPR_FLOW_CHUNK_SECONDS=35  # Default 30
WISPR_FLOW_CHUNK_OVERLAP=0.3  # Default 0.5

# Opus encoding (lower bitrate)
WISPR_FLOW_OPUS_BITRATE=16k  # Default 24k

# Parallel processing
WISPR_FLOW_PARALLEL_CHUNKS=3  # New setting

# Cache settings
VOCABULARY_CACHE_SIZE=1000  # New setting
VOCABULARY_CACHE_TTL=3600  # 1 hour

# Streaming
ENABLE_STREAMING_RESPONSE=1  # New setting

# Predictive mode (experimental)
PREFETCH_ENABLED=0  # Disabled by default
PREFETCH_WINDOW_MS=1000  # 1 second before expected end
```

---

## Testing Strategy

### Performance Benchmarks

```python
# test/benchmarks/test_latency.py
import pytest
import time
from hypr_voice.whisper.core.hybrid_server import transcribe

@pytest.mark.benchmark
def test_short_audio_latency():
    """Test latency for short audio (<5s)"""
    audio = load_test_audio("short_3s.wav")

    start = time.time()
    result = transcribe(audio)
    latency = (time.time() - start) * 1000

    assert latency < 1000, f"Latency {latency}ms exceeds target 1000ms"
    print(f"Short audio latency: {latency:.0f}ms")

@pytest.mark.benchmark
def test_medium_audio_latency():
    """Test latency for medium audio (5-30s)"""
    audio = load_test_audio("medium_15s.wav")

    start = time.time()
    result = transcribe(audio)
    latency = (time.time() - start) * 1000

    assert latency < 2000, f"Latency {latency}ms exceeds target 2000ms"
    print(f"Medium audio latency: {latency:.0f}ms")

@pytest.mark.benchmark
def test_long_audio_latency():
    """Test latency for long audio (>30s)"""
    audio = load_test_audio("long_60s.wav")

    start = time.time()
    result = transcribe(audio)
    latency = (time.time() - start) * 1000

    assert latency < 3000, f"Latency {latency}ms exceeds target 3000ms"
    print(f"Long audio latency: {latency:.0f}ms")
```

### Load Testing

```bash
# Run load tests with k6 or similar
k6 run --vus 10 --duration 30s tests/load/transcription_load_test.js
```

---

## Rollback Plan

Each optimization includes a rollback strategy:

```python
# Feature flags for easy rollback
FEATURE_FLAGS = {
    "request_coalescing": os.getenv("ENABLE_COALESCING", "1") == "1",
    "aggressive_vad": os.getenv("ENABLE_AGGRESSIVE_VAD", "1") == "1",
    "streaming_response": os.getenv("ENABLE_STREAMING", "0") == "1",
    "parallel_chunks": os.getenv("ENABLE_PARALLEL", "1") == "1",
}

# Use feature flags in code
if FEATURE_FLAGS["request_coalescing"]:
    result = await coalesce_and_transcribe(audio)
else:
    result = await transcribe(audio)
```

---

## Success Criteria

### Phase 1 Success (Week 1)
- [ ] 20% reduction in average latency
- [ ] No increase in error rate
- [ ] No degradation in transcription accuracy
- [ ] All tests passing

### Phase 2 Success (Weeks 2-4)
- [ ] 50% total reduction in latency
- [ ] Streaming functional for 90% of requests
- [ ] Cache hit rate >30%
- [ ] User satisfaction >4/5

### Phase 3 Success (Month 2+)
- [ ] Sub-second latency for 80% of requests
- [ ] <100ms for common phrases
- [ ] No regressions in accuracy
- [ ] System stability >99.5%

---

## Appendix: Code Snippets

### A. Request Coalescing Implementation
```python
class RequestCoalescer:
    """Coalesce sequential transcription requests"""

    def __init__(self, debounce_ms=250):
        self.queue = asyncio.Queue()
        self.debounce_ms = debounce_ms
        self.pending_task = None
        self.lock = asyncio.Lock()

    async def submit(self, audio_data):
        """Submit audio for coalesced transcription"""
        async with self.lock:
            await self.queue.put(audio_data)

            if self.pending_task is None or self.pending_task.done():
                self.pending_task = asyncio.create_task(
                    self._process_after_delay()
                )

    async def _process_after_delay(self):
        """Process queued audio after debounce delay"""
        await asyncio.sleep(self.debounce_ms / 1000)

        # Collect all queued audio
        chunks = []
        while not self.queue.empty():
            chunks.append(await self.queue.get())

        # Merge and transcribe
        merged = merge_audio_chunks(chunks)
        result = await transcribe(merged)
        return result
```

### B. Streaming Response Implementation
```python
from fastapi import WebSocket

@app.websocket("/ws/transcribe/stream")
async def websocket_stream_transcribe(websocket: WebSocket):
    await websocket.accept()

    try:
        # Receive audio
        audio_data = await websocket.receive_bytes()

        # Stream transcription results
        async for chunk in flow_client.transcribe_stream(audio_data):
            await websocket.send_json({
                "text": chunk["text"],
                "is_final": chunk["is_final"],
                "confidence": chunk.get("confidence", 0.0),
                "timestamp": time.time()
            })

            if chunk["is_final"]:
                break

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        await websocket.close(code=1011, reason=str(e))
```

### C. Vocabulary Cache Implementation
```python
from functools import lru_cache
from hashlib import sha256

class VocabularyCache:
    """Cache vocabulary-enhanced prompts"""

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self.stats = {"hits": 0, "misses": 0}

    def _make_key(self, vocabulary_words, app_context):
        """Create cache key from vocabulary and context"""
        data = f"{sorted(vocabulary_words)}|{app_context}"
        return sha256(data.encode()).hexdigest()[:16]

    @lru_cache(maxsize=1000)
    def get_enhanced_prompt(self, vocabulary_words, app_context):
        """Get or build enhanced prompt with caching"""
        key = self._make_key(vocabulary_words, app_context)

        # Check cache (using lru_cache decorator)
        prompt = self._build_prompt(vocabulary_words, app_context)

        # Update stats
        # Note: lru_cache handles hit/miss tracking internally

        return prompt

    def _build_prompt(self, vocabulary_words, app_context):
        """Build vocabulary-enhanced prompt"""
        if not vocabulary_words:
            return ""

        # Comma-separated format (research-proven best)
        prompt = ", ".join(vocabulary_words)
        return prompt
```

---

## Conclusion

This optimization plan provides a roadmap to achieve **3-4x overall performance improvement** while maintaining or improving transcription accuracy. The phased approach allows for incremental wins while managing risk.

**Key Takeaways:**
1. **Quick wins** can deliver 20-30% improvement in Week 1
2. **Medium-term improvements** can achieve 50% total reduction
3. **Long-term architectural changes** can deliver sub-second latency
4. **Monitoring and metrics** are critical for success
5. **Feature flags** enable safe rollout and easy rollback

**Next Steps:**
1. Review and prioritize optimizations with team
2. Set up performance monitoring
3. Implement Phase 1 quick wins
4. Measure and iterate
5. Proceed to Phase 2 and 3 based on results

**Expected Final Performance:**
- Average latency: **600ms** (from 2000ms)
- P95 latency: **1000ms** (from 3000ms)
- Common phrases: **100ms** (from 2000ms)
- **Overall: 3.3x faster** while maintaining accuracy
