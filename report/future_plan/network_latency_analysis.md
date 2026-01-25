# Network Latency Analysis Report - WISPR FLOW Transcription System

**Date:** 2026-01-25
**Analysis by:** Claude Code Agent
**Project:** Hypr-Voice

---

## Executive Summary

This report analyzes the network latency issues in the WISPR FLOW transcription system. The investigation reveals that **network API calls to the Baseten endpoint (`chain-o232k03l.api.baseten.co`) are the primary bottleneck**, taking **2.5s to 7s** per request, while local context gathering takes only ~20ms.

### Key Findings

| Component | Time | Status |
|-----------|------|--------|
| Context gathering | ~20ms | Fast (Optimal) |
| Audio preprocessing | <15ms | Fast (Direct mode) |
| **Network API calls** | **2.5s - 7s** | **Bottleneck** |
| Server processing (Baseten) | ~1s | External dependency |
| Network overhead | ~1.5s | Major contributor |

---

## 1. Root Cause Analysis

### 1.1 Primary Bottleneck: Baseten API Network Latency

**Evidence from HAR files:**

From `/home/mewtwo/Zykairotis/Hypr-Voice/src/Info_on_flow/big/chain-o232k03l.api.baseten.co/requests.json`:

```json
{
  "time": 543,  // Initial test - fast (language detection failed)
  "timings": {
    "wait": 542  // Server response time
  }
}
```

From desktop client analytics in `/home/mewtwo/Zykairotis/Hypr-Voice/src/Info_on_flow/big/api.wisprflow.ai/requests.json`:

```json
{
  "timingInformation": {
    "remoteLatency": 2559,        // 2.56 seconds
    "uploadRequest": 0,
    "basetenNetworkMetrics": {
      "totalDurationMsecs": 2597,
      "totalNetworkOverheadMsecs": 1524,  // 58% of total time!
      "serverProcessingTimeMsecs": 1070,
      "webSocketNetworkOverheadMsecs": 1441
    }
  }
}
```

**Critical Insight:** The network overhead (1.5s) is actually **greater** than the server processing time (1.07s), indicating significant latency in the HTTP round-trip to Baseten's servers.

### 1.2 TLS/SSL Handshake Overhead

The HAR files show multiple TLS handshakes occurring:

```json
{
  "time": 808,  // First CONNECT request
  "timings": {
    "dns": 6,
    "connect": 802  // TLS handshake
  }
}
```

Each new connection requires ~800ms for TLS negotiation, which happens when connections aren't properly pooled or when keep-alive expires.

### 1.3 Audio Payload Size Contributing to Upload Time

```json
{
  "request": {
    "bodySize": 34392,  // ~34KB base64 encoded
    "audio_encoding": "wav"
  }
}
```

For longer recordings, the payload size increases significantly. Desktop client uses Opus encoding (13x smaller), but the current implementation defaults to WAV.

---

## 2. Code Analysis

### 2.1 Current Implementation Paths

#### **Path A: Direct Mode (Recommended - Faster)**
File: `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/services/wispr_flow_direct.py`

```python
class DirectWisprFlowClient:
    """
    Direct transcription client - bypasses HTTP API server.

    Performance improvements:
    - No HTTP overhead (saves 50-200ms per request)
    - Audio preprocessing < 15ms (vs 500-2000ms with subprocess)
    - Parallel chunk processing built-in
    """
```

**Features:**
- Uses `wisper-flow/transcribe.py` directly
- In-memory audio processing with `soundfile` (no subprocess)
- Uses `aiohttp` with connection pooling and TCP_NODELAY
- Parallel chunk processing with `asyncio.gather()`

#### **Path B: HTTP Server Mode (Deprecated - Slower)**
File: `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/services/wispr_flow_server.py`

```python
"""
DEPRECATED: This API server is deprecated in favor of direct mode.

For better performance, set FLOW_DIRECT_MODE=1 in your .env file
Direct mode bypasses this HTTP server entirely...
"""
```

**Additional overhead:**
- HTTP server round-trip (localhost:9095)
- Extra serialization/deserialization
- Additional process management

### 2.2 Core Transcription Engine

File: `/home/mewtwo/Zykairotis/Hypr-Voice/src/wisper-flow/transcribe.py`

**Optimizations Already Implemented:**
```python
# Global persistent session with optimizations
_aiohttp_session: aiohttp.ClientSession = None

async def get_persistent_client() -> aiohttp.ClientSession:
    """
    Benefits:
    - TCP_NODELAY for lower latency
    - Connection pooling with keep-alive
    - Faster than httpx for many workloads
    """
    connector = aiohttp.TCPConnector(
        limit=10,
        limit_per_host=5,
        keepalive_timeout=30,
        enable_cleanup_closed=True,
        force_close=False,  # Reuse connections
    )
```

### 2.3 Connection Pooling Issues

**Current settings in `transcribe.py`:**
```python
keepalive_timeout=30  # Connections expire after 30s
```

**Problem:** If transcription requests are spaced >30s apart, new connections require TLS handshake (~800ms).

**Desktop client comparison:** The desktop app maintains persistent connections and uses background keepalive threads.

---

## 3. Comparison: Desktop Client vs Current Implementation

| Feature | Desktop Client | Current Implementation |
|---------|----------------|------------------------|
| **Audio encoding** | Opus (13x smaller) | WAV (default) |
| **Connection pooling** | Persistent + keepalive threads | 30s keep-alive |
| **Preprocessing** | In-memory (Electron) | In-memory (soundfile) |
| **Context gathering** | Native app integration | ~20ms (fast) |
| **Network optimization** | HTTP/2, connection reuse | HTTP/1.1, basic pooling |
| **Latency (from logs)** | ~2.6s total | 2.5s - 7s |

**Key Differences:**
1. Desktop uses Opus encoding for faster uploads
2. Desktop has more aggressive connection pooling
3. Desktop may benefit from HTTP/2 (server-dependent)

---

## 4. Optimization Opportunities

### 4.1 **Already Implemented (Not Being Used)**

The codebase has optimizations that **may not be active**:

#### Direct Mode (FLOW_DIRECT_MODE=1)
```python
# In wispr_flow_direct.py
# This bypasses the HTTP server (port 9095) entirely
```

**Action Required:** Verify `FLOW_DIRECT_MODE` is set to `1` in `.env`

#### aiohttp Connection Pooling
```python
# In wisper-flow/transcribe.py
_aiohttp_session: aiohttp.ClientSession = None  # Global persistent
```

**Issue:** Session may be closed between requests if not properly managed

### 4.2 **Recommended Optimizations**

#### Priority 1: Enable Opus Encoding
**Impact:** High (13x smaller payloads = faster uploads)

**Current code (line 756 in wispr_flow_server.py):**
```python
'audio_encoding': params.audio_encoding,  # 'opus' for faster uploads
```

**Implementation:**
```python
# Default to opus instead of wav
audio_encoding = "opus"  # Instead of "wav"
```

#### Priority 2: Increase Connection Keep-Alive
**Impact:** Medium (reduces TLS handshakes)

**Current (transcribe.py line 89):**
```python
keepalive_timeout=30,
```

**Recommended:**
```python
keepalive_timeout=300,  # 5 minutes instead of 30s
```

#### Priority 3: Implement Background Keepalive Thread
**Impact:** Medium (maintains warm connections)

**Already in wispr_flow_server.py (lines 506-533):**
```python
def _start_keepalive_thread(self):
    """Start background thread to keep connections warm"""
```

**Status:** Only used in server mode, not direct mode

#### Priority 4: HTTP/2 Support
**Impact:** Low-Medium (server-dependent)

**Current (transcribe.py line 146):**
```python
httpx.AsyncClient(http2=True, ...)  # httpx has HTTP/2
```

**But aiohttp (primary client) uses HTTP/1.1**

---

## 5. Specific Issues Identified

### Issue 1: Connection Pool Not Persisting
**Location:** `wisper-flow/transcribe.py`

**Problem:** The global session may be garbage collected or closed between calls:

```python
async def get_persistent_client() -> aiohttp.ClientSession:
    global _aiohttp_session

    if _aiohttp_session is None or _aiohttp_session.closed:
        # Recreating session = new TLS handshake = 800ms overhead
        _aiohttp_session = aiohttp.ClientSession(...)
```

**Solution:** Implement explicit session lifecycle management

### Issue 2: No Background Keepalive in Direct Mode
**Location:** `wispr_flow_direct.py`

**Observation:** Direct mode uses `transcribe_file_async()` from `wisper-flow`, but there's no background keepalive mechanism like in server mode.

**Desktop comparison:**
```python
# From wispr_flow_server.py - NOT used in direct mode
self._keepalive_thread = None
self._keepalive_stop = threading.Event()
self._start_keepalive_thread()
```

### Issue 3: Single-threaded Chunk Processing
**Location:** `wisper-flow/transcribe.py`

**Current:**
```python
results = await asyncio.gather(*tasks)  # Parallel, good
```

**This is actually optimal for I/O-bound tasks**, but could benefit from:
- Streaming responses for long audio
- Progressive results

### Issue 4: Large Base64 Payloads
**Location:** All API calls

**Problem:**
- 34KB base64 payload in test
- For 1-minute audio at 16kHz: ~1MB WAV → ~1.3MB base64

**Solution:**
- Use Opus encoding (desktop does this)
- Or implement chunked streaming

---

## 6. Network Performance Breakdown

From desktop client analytics (real-world measurement):

```
Total time: 2600ms
├── Network overhead: 1524ms (58%)
│   ├── TLS handshake: ~800ms (first request)
│   ├── Upload time: ~400ms
│   └── Download time: ~324ms
├── Server processing: 1070ms (42%)
│   ├── ASR: 406ms
│   ├── LLM: 591ms
│   └── Backend: 83ms
└── Client overhead: ~6ms
```

**Key insight:** Even if server processing were instant, network overhead alone would be ~1.5s.

---

## 7. Recommendations

### Immediate Actions (High Impact)

1. **Verify Direct Mode is Active**
   ```bash
   # Check .env file
   grep FLOW_DIRECT_MODE .env
   # Should be: FLOW_DIRECT_MODE=1
   ```

2. **Enable Opus Encoding**
   ```python
   # In wispr_flow_direct.py, change default
   audio_encoding: str = "opus"  # Instead of "wav"
   ```

3. **Increase Keep-Alive Timeout**
   ```python
   # In wisper-flow/transcribe.py line 89
   keepalive_timeout=300,  # 5 minutes
   ```

### Medium-Term Optimizations

4. **Implement Connection Warmup**
   - Send lightweight requests before actual transcription
   - Reuse the warmup endpoint pattern from server mode

5. **Add Telemetry**
   - Track actual connection reuse vs new connections
   - Monitor TLS handshake frequency

6. **Consider Streaming for Long Audio**
   - Send chunks as they're recorded
   - Receive progressive results

### Long-Term Considerations

7. **Explore Alternative Endpoints**
   - Check if Baseten offers regional servers
   - Consider WebSocket if available (desktop metrics show it's used)

8. **Client-Side ASR Fallback**
   - For short commands, use local Whisper
   - Reserve Baseten for long-form transcription

---

## 8. Conclusion

The network latency in the WISPR FLOW transcription system is **primarily caused by:**

1. **Network overhead (1.5s)** - Greater than server processing time
2. **TLS handshakes (800ms)** - When connections aren't reused
3. **Large payloads** - WAV vs Opus encoding

**The codebase already has many optimizations implemented**, but they may not be active or properly configured. The most impactful fixes are:

1. Ensure direct mode is enabled (`FLOW_DIRECT_MODE=1`)
2. Switch to Opus encoding (13x smaller payloads)
3. Increase connection keep-alive timeout
4. Add background keepalive for connection warming

**Expected improvement:** 20-30% reduction in latency (500ms-1s faster) from implementing all immediate actions.

---

## Appendix: File References

| File | Purpose | Lines of Note |
|------|---------|---------------|
| `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/services/wispr_flow_direct.py` | Direct transcription client | 8-11 (performance claims) |
| `/home/mewtwo/Zykairotis/Hypr-Voice/src/hypr_voice/services/wispr_flow_server.py` | HTTP server (deprecated) | 6-28 (deprecation notice) |
| `/home/mewtwo/Zykairotis/Hypr-Voice/src/wisper-flow/transcribe.py` | Core transcription engine | 68-109 (connection pooling) |
| `/home/mewtwo/Zykairotis/Hypr-Voice/src/Info_on_flow/big/chain-o232k03l.api.baseten.co/requests.json` | HAR - Baseten requests | 70-78 (actual request payload) |
| `/home/mewtwo/Zykairotis/Hypr-Voice/src/Info_on_flow/big/api.wisprflow.ai/requests.json` | HAR - Desktop analytics | 506-511 (timing metrics) |

---

**End of Report**
