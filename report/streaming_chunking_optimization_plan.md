# Streaming Chunking Optimization Plan for Long Audio Recordings

**Date:** January 26, 2026  
**Objective:** Implement background streaming chunking during audio recording to eliminate post-recording processing delays for long audio (2-3+ minutes)

---

## 🎯 Problem Statement

**Current Flow:**
1. User records 2-3 minute audio → Finish recording
2. **THEN** start processing: Load entire file → Split into chunks → Encode → Send to API
3. User waits ~6-8 seconds after recording ends to see results

**Performance Impact:**
- 60-180s recording = ~8s post-recording delay
- User perceives system as "slow" despite fast API
- Most delay is in chunking/encoding AFTER recording completes

---

## 💡 Proposed Solution: Streaming Background Chunking

### Core Concept
**Process chunks WHILE recording is happening, not AFTER**

```
Current (Sequential):
Recording [============================] → Process [====] → Results
         0s -------------------- 120s     120s --- 128s

Proposed (Parallel):
Recording [============================]
          [Chunk1] [Chunk2] [Chunk3] [Chunk4] [Final]
               ↓       ↓        ↓        ↓       ↓
          Transcribing in parallel...
         0s -------------------- 120s → Results (near-instant!)
```

### Key Strategy
- **27-second chunks** with **3-second overlap** (existing optimal settings)
- As soon as 27 seconds of audio is recorded → immediately chunk, encode, and send to API
- Continue recording while transcription happens in background
- By the time recording ends, most/all chunks are already transcribed!

---

## 📁 Files to Modify

### 1. **Primary: `src/hypr_voice/whisper/integration/hypr_voice_type.py`**
   - **Location:** Recording entry point
   - **Current State:** Records to buffer, saves to file when done
   - **Modifications Needed:**
     - Add streaming chunker to `VoiceRecorder` class
     - Monitor audio buffer during recording
     - When buffer reaches 27s → trigger chunk processing
     - Keep overlap for continuity

   **Key Functions:**
   - `VoiceRecorder.__init__()` - Add chunking state variables
   - `VoiceRecorder._record_audio()` - Add real-time chunking logic
   - `VoiceRecorder._process_recording()` - Modify to use streaming mode

### 2. **Core: `src/wisper-flow/transcribe.py`**
   - **Location:** Audio processing and transcription logic
   - **Current State:** Takes complete file, splits, processes
   - **Modifications Needed:**
     - Add `transcribe_chunk_streaming()` method
     - Support incremental chunk submission
     - Return partial results as chunks complete

   **Key Functions:**
   - `split_audio_memory()` (lines 275-293) - Already handles chunking
   - `transcribe_file_async()` (lines 523-654) - Adapt for streaming
   - **NEW:** `transcribe_streaming()` - Stream chunks as they arrive

### 3. **Integration: `src/hypr_voice/whisper/core/hybrid_server.py`**
   - **Location:** Server endpoints and session management
   - **Current State:** File upload → process → return
   - **Modifications Needed:**
     - Add streaming transcription endpoint
     - Manage partial results accumulation
     - Support WebSocket for live progress updates

   **Key Components:**
   - `TranscriptionSession` class (lines 1902-2332) - Add streaming state
   - `_flow_transcribe_file_direct()` (lines 835-1021) - Add streaming path
   - **NEW:** `/ws/transcribe/stream` endpoint for live updates

### 4. **Support: `src/hypr_voice/services/wispr_flow_direct.py`**
   - **Location:** Direct API client
   - **Current State:** Single file transcription
   - **Modifications Needed:**
     - Add `transcribe_chunk_async()` method
     - Support chunk-by-chunk processing
     - Handle partial result merging

   **Key Functions:**
   - `DirectWisprFlowClient.transcribe_file()` (lines 125-224) - Add streaming mode
   - **NEW:** `DirectWisprFlowClient.transcribe_chunk()` - Single chunk processing

---

## 🔧 Implementation Steps

### **Phase 1: Streaming Chunker (Core Logic)**

#### Step 1.1: Add Streaming State to VoiceRecorder
**File:** `src/hypr_voice/whisper/integration/hypr_voice_type.py`

**Add to `VoiceRecorder.__init__()`:**
```python
# Streaming chunking state
self.streaming_mode = True  # Enable by default for long recordings
self.chunk_size_seconds = 27.0  # Match Wispr Flow optimal size
self.overlap_seconds = 3.0      # Overlap for continuity
self.chunk_buffer = []           # Current chunk being built
self.chunk_start_time = None     # Track chunk timing
self.pending_chunks = []         # Chunks ready to process
self.transcription_results = []  # Partial results
self.chunk_processor_task = None # Background processing task
```

#### Step 1.2: Implement Real-Time Chunking in Recording Loop
**File:** `src/hypr_voice/whisper/integration/hypr_voice_type.py`

**Modify `_record_audio()` method:**
```python
async def _record_audio(self):
    """Record audio with real-time chunking for streaming transcription"""
    
    # Start background chunk processor
    if self.streaming_mode:
        self.chunk_processor_task = asyncio.create_task(
            self._background_chunk_processor()
        )
    
    while self.is_recording:
        # Read audio frame (existing logic)
        audio_data = self.stream.read(self.chunk_size)
        self.frames.append(audio_data)
        
        # NEW: Real-time chunking logic
        if self.streaming_mode:
            # Convert to numpy array for duration calculation
            audio_np = np.frombuffer(audio_data, dtype=np.int16)
            self.chunk_buffer.extend(audio_np)
            
            # Calculate current chunk duration
            if self.chunk_start_time is None:
                self.chunk_start_time = time.time()
            
            chunk_duration = len(self.chunk_buffer) / self.sample_rate
            
            # When chunk reaches 27 seconds, process it
            if chunk_duration >= self.chunk_size_seconds:
                logger.info(f"Chunk ready: {chunk_duration:.1f}s")
                
                # Extract chunk with overlap for next chunk
                samples_per_chunk = int(self.chunk_size_seconds * self.sample_rate)
                overlap_samples = int(self.overlap_seconds * self.sample_rate)
                
                # Get full chunk
                chunk = np.array(self.chunk_buffer[:samples_per_chunk], dtype=np.int16)
                
                # Queue for processing
                self.pending_chunks.append(chunk)
                
                # Keep overlap for next chunk
                self.chunk_buffer = self.chunk_buffer[samples_per_chunk - overlap_samples:]
                self.chunk_start_time = time.time()
```

#### Step 1.3: Background Chunk Processor
**File:** `src/hypr_voice/whisper/integration/hypr_voice_type.py`

**Add new method:**
```python
async def _background_chunk_processor(self):
    """Process chunks in background while recording continues"""
    chunk_index = 0
    
    while self.is_recording or len(self.pending_chunks) > 0:
        if len(self.pending_chunks) > 0:
            chunk = self.pending_chunks.pop(0)
            
            logger.info(f"Processing chunk {chunk_index} in background...")
            
            # Encode chunk (Opus/WAV)
            chunk_file = await self._encode_chunk(chunk, chunk_index)
            
            # Send to transcription API
            result = await self._transcribe_chunk(chunk_file, chunk_index)
            
            if result.get("success"):
                self.transcription_results.append({
                    "index": chunk_index,
                    "text": result.get("text", ""),
                    "timestamp": time.time()
                })
                logger.info(f"Chunk {chunk_index} transcribed: {result.get('text', '')[:50]}...")
            
            chunk_index += 1
        else:
            # Wait for new chunks
            await asyncio.sleep(0.1)
    
    logger.info("Background chunk processor finished")
```

---

### **Phase 2: Streaming API Support**

#### Step 2.1: Add Streaming Transcription Method
**File:** `src/wisper-flow/transcribe.py`

**Add new function:**
```python
async def transcribe_chunk_streaming(
    audio_chunk: np.ndarray,
    chunk_index: int,
    ctx: TranscriptionContext,
    prev_text: str = ""
) -> dict:
    """
    Transcribe a single chunk as part of streaming workflow.
    
    Optimized for low latency - processes immediately without waiting.
    """
    timings = {}
    start = time.perf_counter()
    
    # Encode chunk (Opus preferred for speed)
    encode_start = time.perf_counter()
    audio_bytes, encoding = encode_audio_smart(audio_chunk, 16000)
    timings['encode_ms'] = (time.perf_counter() - encode_start) * 1000
    
    # Get persistent session
    session = await get_persistent_client()
    
    # Transcribe
    api_start = time.perf_counter()
    result = await transcribe_chunk_async(
        session, audio_bytes, encoding, ctx, chunk_id=chunk_index
    )
    timings['api_ms'] = (time.perf_counter() - api_start) * 1000
    
    timings['total_ms'] = (time.perf_counter() - start) * 1000
    
    logger.info(
        f"Chunk {chunk_index} streaming: "
        f"encode={timings['encode_ms']:.0f}ms "
        f"api={timings['api_ms']:.0f}ms "
        f"total={timings['total_ms']:.0f}ms"
    )
    
    return result
```

#### Step 2.2: Add Streaming Endpoint
**File:** `src/hypr_voice/whisper/core/hybrid_server.py`

**Add new WebSocket endpoint:**
```python
@app.websocket("/ws/transcribe/stream")
async def websocket_streaming_transcribe(websocket: WebSocket):
    """
    WebSocket endpoint for streaming chunk transcription.
    
    Protocol:
    - Client sends: {"chunk_index": 0, "audio_data": base64, "is_final": false}
    - Server responds: {"chunk_index": 0, "text": "...", "success": true}
    """
    await websocket.accept()
    
    session = TranscriptionSession(
        session_id=str(uuid.uuid4()),
        language="en"
    )
    
    accumulated_text = ""
    
    try:
        while True:
            # Receive chunk
            data = await websocket.receive_json()
            
            chunk_index = data.get("chunk_index", 0)
            audio_b64 = data.get("audio_data")
            is_final = data.get("is_final", False)
            
            if not audio_b64:
                break
            
            # Decode audio
            audio_bytes = base64.b64decode(audio_b64)
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Transcribe chunk
            result = await _flow_transcribe_chunk_direct(
                session, audio_np, chunk_index, accumulated_text
            )
            
            if result.get("success"):
                chunk_text = result.get("text", "")
                accumulated_text = _merge_chunk_text(accumulated_text, chunk_text)
                
                # Send result back
                await websocket.send_json({
                    "chunk_index": chunk_index,
                    "text": chunk_text,
                    "accumulated_text": accumulated_text,
                    "success": True,
                    "is_final": is_final
                })
            else:
                await websocket.send_json({
                    "chunk_index": chunk_index,
                    "error": result.get("error"),
                    "success": False
                })
            
            if is_final:
                break
                
    except Exception as e:
        logger.error(f"Streaming transcription error: {e}")
        await websocket.send_json({"error": str(e), "success": False})
    finally:
        await websocket.close()
```

---

### **Phase 3: Integration and Testing**

#### Step 3.1: Modify Recording Stop to Handle Partial Results
**File:** `src/hypr_voice/whisper/integration/hypr_voice_type.py`

**Modify `stop_recording()`:**
```python
def stop_recording(self):
    """Stop recording and finalize any pending chunks"""
    self.is_recording = False
    
    if self.streaming_mode:
        # Process final partial chunk if exists
        if len(self.chunk_buffer) > 0:
            final_chunk = np.array(self.chunk_buffer, dtype=np.int16)
            self.pending_chunks.append(final_chunk)
            logger.info(f"Added final chunk: {len(final_chunk)/self.sample_rate:.1f}s")
        
        # Wait for chunk processor to finish
        if self.chunk_processor_task:
            asyncio.run(self._wait_for_chunks())
```

#### Step 3.2: Add Environment Variable Controls
**File:** `.env` (user configuration)

```bash
# Streaming chunking configuration
FLOW_STREAMING_MODE=1              # Enable streaming chunking
FLOW_STREAMING_CHUNK_SIZE=27.0     # Chunk size in seconds
FLOW_STREAMING_OVERLAP=3.0         # Overlap in seconds
FLOW_STREAMING_MIN_DURATION=20.0   # Minimum recording duration to enable streaming
```

---

## 🧪 Testing Strategy

### Test Cases

1. **Short Recording (< 20s)**
   - Should NOT use streaming (overhead not worth it)
   - Single chunk processing (existing behavior)

2. **Medium Recording (20-60s)**
   - 2-3 chunks processed in background
   - Results available within 1-2s of recording end

3. **Long Recording (60-180s)**
   - 4-7 chunks processed in parallel
   - Results available immediately or within 0.5s of recording end
   - **Expected improvement: 6-8s → < 1s**

4. **Very Long Recording (180s+)**
   - 7+ chunks
   - Continuous background processing
   - **Expected improvement: 10-15s → < 2s**

### Performance Metrics

| Recording Length | Current Delay | Target Delay | Expected Improvement |
|-----------------|---------------|--------------|---------------------|
| 20-30s | ~2s | ~0.5s | **75% faster** |
| 30-60s | ~4s | ~0.8s | **80% faster** |
| 60-120s | ~8s | ~1.0s | **87% faster** |
| 120-180s | ~12s | ~1.5s | **87% faster** |

---

## ⚠️ Edge Cases & Considerations

### 1. **Network Latency**
- If API response takes longer than 27s, chunks may queue up
- **Solution:** Add semaphore to limit concurrent API calls (max 3-5)

### 2. **Context Continuity**
- Each chunk needs context from previous chunks for accuracy
- **Solution:** Pass `prev_text` parameter with last transcription

### 3. **Chunk Merging**
- Overlapping audio needs smart merging to avoid duplicate words
- **Solution:** Use existing `merge_transcriptions()` logic with difflib

### 4. **Memory Management**
- Long recordings may accumulate many chunks in memory
- **Solution:** Clear processed chunks, keep only overlap buffer

### 5. **Error Handling**
- What if a chunk transcription fails mid-recording?
- **Solution:** Retry failed chunks, continue with next chunks

---

## 📊 Variables and Functions Reference

### Key Variables

**VoiceRecorder (hypr_voice_type.py):**
- `streaming_mode: bool` - Enable/disable streaming
- `chunk_size_seconds: float` - Size of each chunk (27s)
- `overlap_seconds: float` - Overlap between chunks (3s)
- `chunk_buffer: List[np.ndarray]` - Current chunk being built
- `pending_chunks: List[np.ndarray]` - Chunks ready to process
- `transcription_results: List[dict]` - Partial results
- `chunk_processor_task: asyncio.Task` - Background processor

**wisper-flow/transcribe.py:**
- `MAX_CHUNK_DURATION = 27` - Chunk size (existing)
- `OVERLAP_DURATION = 3` - Overlap (existing)
- `split_audio_memory()` - Chunk splitter (existing)
- `merge_transcriptions()` - Result merger (existing)

**Environment Variables:**
- `FLOW_STREAMING_MODE` - Enable feature
- `FLOW_STREAMING_CHUNK_SIZE` - Chunk duration
- `FLOW_STREAMING_OVERLAP` - Overlap duration
- `FLOW_STREAMING_MIN_DURATION` - Minimum duration to activate

### Key Functions to Modify

1. `VoiceRecorder._record_audio()` - Add real-time chunking
2. `VoiceRecorder._process_recording()` - Use streaming results
3. `VoiceRecorder.stop_recording()` - Handle partial chunks
4. **NEW:** `VoiceRecorder._background_chunk_processor()` - Process chunks
5. **NEW:** `VoiceRecorder._encode_chunk()` - Encode single chunk
6. **NEW:** `VoiceRecorder._transcribe_chunk()` - Transcribe single chunk
7. **NEW:** `transcribe_chunk_streaming()` (transcribe.py) - Streaming API
8. **NEW:** `websocket_streaming_transcribe()` (hybrid_server.py) - WS endpoint

---

## 🎯 Success Criteria

✅ **Performance:**
- 60s+ recordings: Results within 1s of recording end (vs 6-8s currently)
- 120s+ recordings: Results within 2s (vs 10-12s currently)

✅ **Reliability:**
- No degradation in transcription accuracy
- Proper handling of network failures
- Graceful fallback to sequential mode if needed

✅ **User Experience:**
- Near-instant results for long recordings
- Optional progress indicators showing chunks being processed
- No blocking during recording

---

## 🚀 Next Steps

1. **Review this plan** with user
2. **Implement Phase 1** - Core streaming chunker
3. **Test with 60s+ recordings** - Validate performance gains
4. **Implement Phase 2** - API integration
5. **Integration testing** - End-to-end workflow
6. **Documentation** - Update user guides

---

**End of Plan**
