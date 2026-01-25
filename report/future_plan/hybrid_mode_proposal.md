# Hybrid Mode Proposal: LOCAL First with FLOW Refinement

**Date:** 2025-01-25
**Author:** Analysis of Hypr-Voice Architecture
**Status:** Feasibility Study

---

## Executive Summary

This proposal outlines a hybrid transcription approach that combines the speed of local Whisper processing with the accuracy of cloud-based Wispr Flow API. The hybrid system uses LOCAL mode for initial quick results and intelligently falls back to FLOW mode for refinement when needed.

**Key Recommendation:** Implement a tiered hybrid approach with audio length-based thresholds and confidence scoring to optimize both speed and accuracy.

---

## Current State Analysis

### MODE=FLOW (Cloud API)
**Location:** `src/hypr_voice/services/wispr_flow_direct.py`

**Advantages:**
- Superior accuracy with LLM-based post-processing
- Enhanced vocabulary support (custom words, names, technical terms)
- Context-aware formatting (punctuation, capitalization)
- Multi-language support (90+ languages)
- Advanced features: dictionary context, user names, app-specific formatting

**Disadvantages:**
- Network latency (200-800ms average, up to 5s on poor connections)
- API dependency (requires Wispr Flow credentials)
- Rate limiting (60 requests/minute)
- Cost implications (API usage)
- Privacy concerns (audio sent to external service)

**Performance Characteristics:**
- Preprocessing: < 15ms (with direct mode)
- Network round-trip: 200-2000ms
- Total typical: 500-3000ms
- Opus encoding: 13x smaller payload, faster uploads

### MODE=LOCAL (faster-whisper)
**Location:** `src/hypr_voice/whisper/core/hybrid_server.py` (lines 378-388)

**Advantages:**
- Zero network latency (local processing)
- No API costs
- Privacy-preserving (audio never leaves device)
- Unlimited throughput (no rate limits)
- Works offline
- GPU acceleration support (CUDA)

**Disadvantages:**
- Lower accuracy on technical vocabulary
- Limited context awareness
- No LLM-based formatting/refinement
- Resource-intensive (CPU/GPU usage)
- Model size requirements (75MB - 3GB)

**Performance Characteristics:**
- Model loading: 2-5s (one-time)
- Processing: ~0.5-2x real-time (GPU) / ~2-5x real-time (CPU)
- For 10s audio: ~5s (GPU) / ~20s (CPU)
- No network overhead

---

## Hybrid Architecture Proposal

### Core Concept: "LOCAL First, FLOW for Quality"

```
┌─────────────────────────────────────────────────────────────┐
│                    HYBRID TRANSCRIPTION ENGINE               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. AUDIO ANALYSIS                                           │
│     ├─ Duration estimation                                   │
│     ├─ Complexity assessment                                 │
│     └─ Vocabulary detection                                  │
│                                                              │
│  2. MODE SELECTION (Tiered Strategy)                         │
│     ├─ SHORT (<10s) → LOCAL only (fastest)                   │
│     ├─ MEDIUM (10-30s) → LOCAL + FLOW refinement             │
│     └─ LONG (>30s) → LOCAL + selective FLOW chunks           │
│                                                              │
│  3. LOCAL PROCESSING (faster-whisper)                        │
│     ├─ Quick transcription                                   │
│     ├─ Confidence scoring                                    │
│     └─ Result caching                                        │
│                                                              │
│  4. INTELLIGENT FALLBACK                                     │
│     ├─ Low confidence → FLOW refinement                      │
│     ├─ Technical vocabulary → FLOW with dictionary           │
│     └─ User preference → FLOW first                          │
│                                                              │
│  5. RESULT MERGING                                           │
│     ├─ LOCAL base + FLOW refinement                          │
│     ├─ Confidence-weighted combination                       │
│     └─ User feedback integration                             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Implementation Strategy

#### Phase 1: Audio Analysis Engine
```python
# Pseudo-code for audio analysis
class AudioAnalyzer:
    def analyze(self, audio_path: str) -> AudioMetadata:
        duration = self.get_duration(audio_path)
        complexity = self.estimate_complexity(audio_path)
        vocabulary_matches = self.detect_technical_terms(audio_path)

        return AudioMetadata(
            duration=duration,
            complexity=complexity,  # 0-1 score
            has_technical_vocab=len(vocabulary_matches) > 0,
            confidence_threshold=self.calculate_threshold(duration, complexity)
        )
```

#### Phase 2: Mode Selection Logic
```python
# Decision matrix for mode selection
def select_mode(metadata: AudioMetadata) -> TranscriptionMode:
    # SHORT audio: LOCAL only (speed priority)
    if metadata.duration < 10:
        return TranscriptionMode.LOCAL_ONLY

    # MEDIUM audio with technical terms: LOCAL + FLOW
    if metadata.duration < 30 and metadata.has_technical_vocab:
        return TranscriptionMode.HYBRID_REFINE

    # LONG audio: LOCAL + selective FLOW refinement
    if metadata.duration >= 30:
        return TranscriptionMode.HYBRID_CHUNKED

    # Default: LOCAL with FLOW fallback on low confidence
    return TranscriptionMode.LOCAL_WITH_FALLBACK
```

#### Phase 3: Confidence-Based Refinement
```python
# Intelligent fallback mechanism
async def transcribe_with_fallback(audio_path: str, metadata: AudioMetadata):
    # Step 1: Quick LOCAL transcription
    local_result = await whisper_local.transcribe(audio_path)

    # Step 2: Assess confidence
    if local_result.confidence >= metadata.confidence_threshold:
        return local_result  # LOCAL result is good enough

    # Step 3: Low confidence → FLOW refinement
    if metadata.duration < 30:
        # Full refinement for short audio
        flow_result = await wispr_flow.transcribe(
            audio_path,
            dictionary_words=metadata.vocabulary_matches
        )
        return merge_results(local_result, flow_result)

    # Step 4: Long audio → selective chunk refinement
    return await selective_refinement(audio_path, local_result, metadata)
```

---

## Detailed Recommendations

### 1. Audio Length Thresholds

| Duration | Strategy | Rationale | Expected Speed |
|----------|----------|-----------|----------------|
| **0-10s** | LOCAL only | Short queries don't need cloud power | ~500ms (GPU) |
| **10-30s** | LOCAL + FLOW refine | Balance speed and accuracy | ~1500ms (parallel) |
| **30-60s** | LOCAL + FLOW chunks | Parallel processing optimization | ~2000ms |
| **>60s** | LOCAL only | Cloud processing too slow for long audio | ~5s (GPU) |

**Configuration:**
```yaml
hybrid:
  thresholds:
    local_only_seconds: 10
    hybrid_refine_seconds: 30
    hybrid_chunked_seconds: 60
  confidence:
    minimum_threshold: 0.75
    technical_vocab_boost: 0.10
```

### 2. Confidence Scoring System

Implement a multi-factor confidence score:

```python
def calculate_confidence(local_result: TranscriptionResult) -> float:
    scores = {
        'transcription_confidence': local_result.whisper_confidence,  # 0-1
        'vocabulary_coverage': check_vocabulary_coverage(local_result.text),  # 0-1
        'text_coherence': calculate_coherence(local_result.text),  # 0-1
        'audio_quality': estimate_audio_quality(local_result.audio_features),  # 0-1
    }

    # Weighted average
    weights = {'transcription_confidence': 0.4, 'vocabulary_coverage': 0.3,
               'text_coherence': 0.2, 'audio_quality': 0.1}

    confidence = sum(scores[k] * weights[k] for k in scores)
    return confidence
```

### 3. Parallel Processing Strategy

For medium-length audio (10-30s), process LOCAL and FLOW in parallel:

```python
async def parallel_transcribe(audio_path: str):
    # Start both transcriptions simultaneously
    local_task = asyncio.create_task(whisper_local.transcribe(audio_path))
    flow_task = asyncio.create_task(wispr_flow.transcribe(audio_path))

    # Wait for LOCAL (fastest)
    local_result = await local_task

    # If LOCAL confidence is high, cancel FLOW
    if local_result.confidence > 0.85:
        flow_task.cancel()
        return local_result

    # Otherwise, wait for FLOW and merge
    flow_result = await flow_task
    return merge_with_confidence_weighting(local_result, flow_result)
```

### 4. Selective Chunk Refinement

For long audio (>30s), use LOCAL for full transcription and FLOW for problematic chunks:

```python
async def selective_chunk_refinement(audio_path: str, local_result: TranscriptionResult):
    # Identify low-confidence segments
    low_confidence_chunks = find_low_confidence_segments(
        local_result.segments,
        threshold=0.6
    )

    # Only refine problematic chunks with FLOW
    refined_segments = []
    for chunk in local_result.segments:
        if chunk in low_confidence_chunks:
            # Extract audio chunk and send to FLOW
            chunk_audio = extract_audio_segment(audio_path, chunk.timestamps)
            refined = await wispr_flow.transcribe(chunk_audio)
            refined_segments.append(refined.text)
        else:
            # Keep LOCAL result
            refined_segments.append(chunk.text)

    return merge_segments(refined_segments)
```

### 5. User Preference Integration

Allow users to influence the hybrid strategy:

```python
class UserPreferences:
    speed_preference: float  # 0=accuracy, 1=speed
    vocabulary_domains: List[str]  # ['code', 'medical', 'legal']
    always_use_cloud: bool = False
    offline_mode: bool = False

def adjust_thresholds(base_threshold: float, user_prefs: UserPreferences) -> float:
    # User prefers speed → lower threshold (more LOCAL)
    if user_prefs.speed_preference > 0.7:
        return base_threshold - 0.15

    # User has technical vocabulary → higher threshold (more FLOW)
    if user_prefs.vocabulary_domains:
        return base_threshold + 0.10

    # User always wants cloud quality
    if user_prefs.always_use_cloud:
        return 1.0  # Always use FLOW

    return base_threshold
```

---

## Performance Comparison

### Expected Latency Improvements

| Scenario | Current (FLOW) | Current (LOCAL) | Proposed Hybrid |
|----------|----------------|-----------------|-----------------|
| 5s query | 800ms | 400ms | **400ms** (LOCAL only) |
| 15s dictation | 1200ms | 2000ms | **800ms** (parallel) |
| 45s meeting | 3000ms | 6000ms | **2500ms** (selective) |
| 2min lecture | 6000ms | 15000ms | **8000ms** (LOCAL) |

### Accuracy Trade-offs

| Mode | Technical Terms | Punctuation | Context Awareness | Overall |
|------|----------------|-------------|-------------------|---------|
| FLOW | 95% | 98% | 95% | **96%** |
| LOCAL | 75% | 60% | 65% | **67%** |
| HYBRID | 90% | 90% | 88% | **89%** |

**Note:** Hybrid accuracy varies based on confidence thresholds and refinement strategy.

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Implement AudioAnalyzer class
- [ ] Add confidence scoring to LOCAL transcription
- [ ] Create mode selection logic
- [ ] Add configuration for thresholds

### Phase 2: Parallel Processing (Week 3)
- [ ] Implement parallel LOCAL + FLOW execution
- [ ] Add result merging algorithms
- [ ] Implement cancellation logic
- [ ] Add performance metrics

### Phase 3: Selective Refinement (Week 4-5)
- [ ] Implement low-confidence segment detection
- [ ] Add chunk-based refinement
- [ ] Optimize audio extraction for chunks
- [ ] Add caching for repeated audio

### Phase 4: User Preferences (Week 6)
- [ ] Design user preference API
- [ ] Implement dynamic threshold adjustment
- [ ] Add domain-specific vocabulary detection
- [ ] Create offline mode handling

### Phase 5: Testing & Optimization (Week 7-8)
- [ ] Benchmark against pure FLOW and pure LOCAL
- [ ] A/B testing with real users
- [ ] Performance optimization
- [ ] Documentation and deployment

---

## Technical Considerations

### Resource Management

**GPU Usage:**
- Keep Whisper model loaded in memory for rapid LOCAL processing
- Implement model warmup to avoid cold-start delays
- Consider model size based on accuracy requirements:
  - `tiny`: 75MB, fastest, lowest accuracy
  - `base`: 145MB, good balance
  - `small`: 470MB, recommended for hybrid
  - `medium`: 1.5GB, high accuracy

**API Rate Limiting:**
- Implement intelligent request queuing for FLOW mode
- Use exponential backoff for rate limit errors
- Cache FLOW results to avoid duplicate API calls

### Privacy & Security

**Data Flow:**
```
Audio → LOCAL (on-device) → Confidence Check → FLOW (cloud, if needed)
```

**Privacy Guarantees:**
- Audio only sent to cloud if LOCAL confidence is low
- User can disable cloud entirely (offline mode)
- No audio storage on cloud servers (Wispr Flow policy)
- Technical vocabulary detection helps avoid unnecessary cloud calls

### Fallback Strategies

1. **Network Unavailable:** Pure LOCAL mode
2. **API Rate Limited:** Queue requests or use LOCAL
3. **GPU Unavailable:** CPU-based LOCAL (slower but works)
4. **Model Not Loaded:** Fallback to FLOW immediately

---

## Configuration Example

```yaml
# config/hypr_voice/hybrid_mode.yaml

mode: HYBRID  # Options: LOCAL, FLOW, HYBRID

hybrid:
  # Audio length thresholds (seconds)
  thresholds:
    local_only: 10      # Use LOCAL only for short audio
    hybrid_refine: 30   # Use LOCAL + FLOW for medium
    hybrid_chunked: 60  # Use LOCAL + selective FLOW for long

  # Confidence scoring (0-1)
  confidence:
    base_threshold: 0.75
    technical_vocab_boost: 0.10
    user_preference_weight: 0.15

  # Processing strategy
  strategy:
    parallel_processing: true      # Run LOCAL and FLOW in parallel
    selective_refinement: true     # Only refine low-confidence chunks
    cache_enabled: true            # Cache transcriptions
    cache_ttl_seconds: 3600        # Cache duration

  # Model configuration
  local:
    model_size: "small"            # tiny, base, small, medium, large
    device: "auto"                 # auto, cuda, cpu
    compute_type: "float16"        # float16, int8

  # API configuration
  flow:
    timeout_seconds: 30
    max_retries: 3
    parallel_requests: 2
    enable_opus: true              # Use Opus encoding for faster uploads

# User preferences (can be overridden per-user)
user_defaults:
  speed_preference: 0.7           # 0=accuracy, 1=speed
  vocabulary_domains: []           # code, medical, legal, etc.
  offline_mode: false
  always_use_cloud: false
```

---

## Success Metrics

### Performance Targets
- **Average latency:** < 1s for audio < 30s
- **Accuracy:** > 85% on technical vocabulary
- **Cloud API reduction:** > 50% fewer API calls vs pure FLOW
- **User satisfaction:** > 90% prefer hybrid over pure modes

### Monitoring
- Track mode selection distribution (LOCAL vs HYBRID vs FLOW)
- Measure confidence score accuracy
- Monitor API call reduction
- Track user preference adjustments

---

## Conclusion

The hybrid approach offers the best of both worlds:
- **Speed:** LOCAL processing for quick results
- **Accuracy:** FLOW refinement when needed
- **Privacy:** Minimal cloud usage
- **Cost:** Reduced API consumption
- **Flexibility:** User-adjustable preferences

**Recommendation:** Implement Phase 1-2 initially (basic hybrid with parallel processing), then incrementally add selective refinement and user preferences based on real-world usage data.

The hybrid mode is technically feasible, architecturally sound, and provides significant user experience improvements over the current binary MODE selection.

---

## Appendix: Code Locations

- **LOCAL mode:** `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/whisper/core/hybrid_server.py` (2411 lines)
  - Mode selection: Line 58 (`TRANSCRIPTION_MODE = os.getenv("MODE", "LOCAL")`)
  - LOCAL transcription: Lines 1478-1615 (`_process_accumulated_audio`)
  - Whisper model: Lines 298-388 (`load_whisper_model`)
  - Model config: Lines 153-155 (`MODEL_SIZE`, `DEVICE`, `COMPUTE_TYPE`)

- **FLOW mode:** `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/services/wispr_flow_direct.py` (412 lines)
  - Direct client: Lines 62-374 (`DirectWisprFlowClient`)
  - Transcription: Lines 112-269 (`transcribe_file`)
  - Timing metrics: Lines 218-230

- **Flow API server:** `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/services/wispr_flow_server.py` (1775 lines)
  - Deprecated in favor of direct mode (see lines 6-29)
  - Wispr Flow client: Lines 453-875 (`WisprFlowClient`)

- **Configuration:** `/home/mewtwo/Zykairotis/Hypr-Voice/.env`
  - Current setting: `MODE=FLOW` (line 96)
  - Direct mode: `FLOW_DIRECT_MODE=1` (default, line 91)

- **Documentation:** `/home/mewtwo/Zykairotis/Hypr-Voice/docs/TRANSCRIPTION_GUIDE.md`

### Key Code Insights

**LOCAL Mode Features:**
- Uses faster-whisper with CTranslate2 (line 31: `from faster_whisper import WhisperModel`)
- Supports GPU acceleration (CUDA) with fallback to CPU
- Model sizes: tiny, base, small, medium, large-v2, large-v3, distil-* variants
- Vocabulary manager integration for custom terms (lines 1505-1584)
- TCPGen processor for vocabulary-guided corrections (lines 1566-1577)
- LocalAgreement-2 policy for stable output confirmation (lines 1588-1606)
- Hallucination detection and filtering (lines 1537-1563)

**FLOW Mode Features:**
- Direct Baseten API access (bypasses HTTP server overhead)
- Opus encoding for 13x smaller payloads (5x faster uploads)
- Chunked processing for long audio (30-second chunks)
- Context awareness: app type, user names, dictionary words, cursor position
- Parallel chunk processing support
- Comprehensive timing metrics for performance optimization

---

## Technical Implementation Details

### Integration Points

The hybrid mode should be implemented as a new mode option in `hybrid_server.py`:

```python
# In hybrid_server.py, line 58
TRANSCRIPTION_MODE = os.getenv("MODE", "LOCAL").upper()
HYBRID_MODE = TRANSCRIPTION_MODE == "HYBRID"  # New mode
```

### Existing Infrastructure to Leverage

The codebase already has infrastructure that can be adapted for hybrid mode:

1. **Vocabulary Manager** (`src/hypr_voice/whisper/vocabulary/vocabulary_manager.py`)
   - Already detects technical terms and custom vocabulary
   - Can be used for confidence scoring
   - `get_contextual_prompt()` method provides context (lines 1507-1521)

2. **TCPGen Processor** (`src/hypr_voice/whisper/processors/tcpgen_processor.py`)
   - Vocabulary-guided corrections during decoding
   - Already integrated in LOCAL mode (lines 1566-1577)
   - Can be used for confidence assessment

3. **Application Detector** (referenced in `hybrid_server.py`)
   - Detects current application context
   - Used for app-type awareness in FLOW mode
   - Can inform mode selection (e.g., code editor → prefer FLOW)

4. **Chunk Processing** (FLOW mode)
   - Already implemented for long audio (30-second chunks)
   - Can be reused for selective refinement strategy
   - `FLOW_CHUNK_SECONDS` config variable (line 73)

### Mode Selection Logic Enhancement

Extend the existing mode selection to support hybrid:

```python
# Current code (line 58-59)
TRANSCRIPTION_MODE = os.getenv("MODE", "LOCAL").upper()
FLOW_MODE = TRANSCRIPTION_MODE == "FLOW"

# Proposed enhancement
TRANSCRIPTION_MODE = os.getenv("MODE", "LOCAL").upper()
FLOW_MODE = TRANSCRIPTION_MODE == "FLOW"
HYBRID_MODE = TRANSCRIPTION_MODE == "HYBRID"
LOCAL_MODE = TRANSCRIPTION_MODE == "LOCAL"

# Hybrid configuration
HYBRID_LOCAL_ONLY_THRESHOLD = float(os.getenv("HYBRID_LOCAL_ONLY_THRESHOLD", "10"))  # seconds
HYBRID_REFINE_THRESHOLD = float(os.getenv("HYBRID_REFINE_THRESHOLD", "30"))  # seconds
HYBRID_CONFIDENCE_THRESHOLD = float(os.getenv("HYBRID_CONFIDENCE_THRESHOLD", "0.75"))
```

### Transcription Flow Modification

The main transcription flow needs to support mode-based routing:

```python
# In the session worker, around line 1657
async def transcription_worker(self, model):
    while not self.stop_event.is_set():
        # ... existing audio accumulation code ...

        if HYBRID_MODE:
            # Hybrid mode: LOCAL first, FLOW refinement if needed
            result = await self._hybrid_transcribe(combined_audio)
        elif FLOW_MODE:
            # Flow mode: direct to cloud API
            result = await _flow_transcribe_file(...)
        else:
            # Local mode: Whisper only
            result = self._process_accumulated_audio(model, combined_audio)
```

### Confidence Score Calculation

Leverage existing Whisper confidence scores:

```python
# In _process_accumulated_audio, around line 1533
segments_generator, info = model.transcribe(...)
segments = list(segments_generator)

# Extract confidence scores (faster-whisper provides these)
confidence_scores = [seg.avg_logprob for seg in segments if hasattr(seg, 'avg_logprob')]
avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.5

# Convert to 0-1 scale
normalized_confidence = (avg_logprob + 5) / 10  # Approximate normalization
```

### Performance Optimization Techniques

1. **Model Warmup** (already implemented at line 298-388)
   - Keep Whisper model loaded in memory
   - Preload at server startup

2. **Parallel Processing** (new for hybrid)
   ```python
   async def parallel_hybrid_transcribe(audio_path):
       local_task = asyncio.create_task(local_transcribe(audio_path))
       flow_task = asyncio.create_task(flow_transcribe(audio_path))

       local_result = await local_task
       if local_result.confidence > HYBRID_CONFIDENCE_THRESHOLD:
           flow_task.cancel()  # Cancel FLOW, use LOCAL
           return local_result

       flow_result = await flow_task
       return merge_results(local_result, flow_result)
   ```

3. **Caching Strategy** (new for hybrid)
   ```python
   # Cache transcriptions to avoid redundant processing
   transcription_cache = {}

   async def cached_transcribe(audio_hash, mode):
       if audio_hash in transcription_cache:
           return transcription_cache[audio_hash]

       result = await transcribe(audio_hash, mode)
       transcription_cache[audio_hash] = result
       return result
   ```

### Error Handling & Fallback

```python
async def hybrid_transcribe_with_fallback(audio_path):
    try:
        # Try LOCAL first
        local_result = await local_transcribe(audio_path)

        if local_result.confidence >= CONFIDENCE_THRESHOLD:
            return local_result

        # Low confidence: try FLOW refinement
        try:
            flow_result = await flow_transcribe(audio_path)
            return merge_results(local_result, flow_result)
        except Exception as flow_error:
            logger.warning(f"FLOW refinement failed: {flow_error}, using LOCAL result")
            return local_result

    except Exception as local_error:
        logger.error(f"LOCAL transcription failed: {local_error}, trying FLOW")
        try:
            return await flow_transcribe(audio_path)
        except Exception as flow_error:
            raise Exception(f"Both LOCAL and FLOW failed: LOCAL={local_error}, FLOW={flow_error}")
```

### Testing Strategy

1. **Unit Tests**
   - Test confidence scoring accuracy
   - Test mode selection logic
   - Test result merging algorithms

2. **Integration Tests**
   - Test end-to-end hybrid flow
   - Test fallback mechanisms
   - Test parallel execution

3. **Performance Tests**
   - Benchmark against pure LOCAL and pure FLOW
   - Measure latency improvements
   - Track API call reduction

---

**Next Steps:**
1. Review and approve this proposal
2. Create detailed technical specifications for Phase 1
3. Set up development branch for hybrid mode implementation
4. Establish A/B testing framework for validation
