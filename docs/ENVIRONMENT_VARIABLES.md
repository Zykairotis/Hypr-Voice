# Environment Variables Guide

A comprehensive guide to configuring Hypr-Voice through environment variables.

---

## 🎯 Quick Start - Minimum Required

To get started, you only need **5 variables**:

```bash
# 1. LLM Provider
CEREBRAS_API_KEY_ONE=your_key_here

# 2-4. Transcription Service
WISPR_FLOW_JWT_TOKEN=your_jwt_token_here
WISPR_FLOW_BASETEN_API_KEY=your_baseten_key_here
WISPR_FLOW_USER_UUID=your_uuid_here

# 5. Text-to-Speech
DEEPGRAM_API_KEY=your_deepgram_key_here
# OR
ELEVENLABS_API_KEY=your_elevenlabs_key_here
```

**Everything else has sensible defaults!**

---

## 📋 All Variables by Category

### 🔑 API Keys - Required

| Variable | Required | Description | Where to Get |
|----------|----------|-------------|--------------|
| `CEREBRAS_API_KEY_ONE` | ✅ Yes | Primary Cerebras LLM API key | https://cloud.cerebras.ai |
| `CEREBRAS_API_KEY_TWO` | ❌ Optional | Backup Cerebras key | https://cloud.cerebras.ai |
| `CEREBRAS_API_KEY_THREE` | ❌ Optional | Backup Cerebras key | https://cloud.cerebras.ai |
| `WISPR_FLOW_JWT_TOKEN` | ✅ Yes | Wispr Flow authentication | https://wispr-flow.baseten.co |
| `WISPR_FLOW_BASETEN_API_KEY` | ✅ Yes | Baseten API key | https://baseten.co |
| `WISPR_FLOW_USER_UUID` | ✅ Yes | Your user UUID | From Wispr Flow dashboard |
| `DEEPGRAM_API_KEY` | ⚠️ One required | Deepgram TTS API key | https://deepgram.com |
| `ELEVENLABS_API_KEY` | ⚠️ One required | ElevenLabs TTS API key | https://elevenlabs.io |

### 🎤 Voice Transcription - Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MODE` | `FLOW` | Transcription mode: `FLOW` (cloud) or `LOCAL` (hybrid) |
| `WISPR_FLOW_PORT` | `9095` | Port for Wispr Flow server |
| `WISPR_FLOW_TIMEOUT` | `600` | API timeout in seconds |
| `WISPR_FLOW_CHUNK_SECONDS` | `30` | Chunk size for long audio (seconds) |
| `WISPR_FLOW_AUTO_CHUNK` | `1` | Automatically chunk long audio |
| `WISPR_FLOW_CHUNK_OVERLAP` | `0.5` | Overlap between chunks (seconds) |
| `WISPR_FLOW_MAX_BASE64_MB` | `50` | Maximum base64 audio size (MB) |
| `WISPR_FLOW_MAX_DICTIONARY_WORDS` | `50` | Maximum context vocabulary words |

### 🚀 Performance Optimization - NEW!

| Variable | Default | Description | Impact |
|----------|---------|-------------|--------|
| `WISPR_FLOW_USE_OPUS` | `1` | Use Opus encoding (vs WAV) | **10x smaller uploads** ✨ |
| `WISPR_FLOW_OPUS_BITRATE` | `24k` | Opus encoding bitrate | Balance quality/size |
| `FLOW_STREAMING_MODE` | `1` | Stream chunks during recording | **85% faster for 60s+ audio** 🚀 |

**Performance Impact:**
- `WISPR_FLOW_USE_OPUS=1`: 3MB WAV → 300KB Opus (10x smaller)
- `FLOW_STREAMING_MODE=1`: 8s delay → 1s delay for 2-minute recordings

### 🗣️ Text-to-Speech Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HYPR_VOICE_TTS_STREAMING` | `1` | Enable streaming TTS |
| `HYPR_VOICE_TTS_REST_STREAMING` | `1` | REST API streaming |
| `HYPR_VOICE_TTS_PREBUFFER_MS` | `800` | Pre-buffer time (ms) |
| `HYPR_VOICE_TTS_MIN_CHARS` | `100` | Minimum chars before speaking |
| `HYPR_VOICE_TTS_MAX_LATENCY` | `0.5` | Maximum latency (seconds) |
| `HYPR_VOICE_TTS_FLUSH_TIMEOUT` | `15` | Flush buffer timeout (seconds) |
| `HYPR_VOICE_TTS_IDLE_TIMEOUT` | `3.0` | Idle timeout (seconds) |

### 🤖 AI Providers - Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `CEREBRAS_PREFERRED_MODELS` | `gpt-oss-120b,llama-3.3-70b,...` | Comma-separated model list |
| `CEREBRAS_TIMEOUT` | `60` | LLM API timeout (seconds) |
| `CEREBRAS_MAX_RETRIES` | `3` | Maximum retry attempts |
| `CEREBRAS_DEBUG` | `false` | Enable debug logging |
| `ANTHROPIC_AUTH_TOKEN` | - | Claude API token (via Z.ai) |
| `ANTHROPIC_BASE_URL` | `https://api.z.ai/api/anthropic` | Anthropic proxy URL |
| `ANTHROPIC_DEFAULT_SONNET_MODEL` | `GLM-4.6` | Default Claude model |
| `GEMINI_API_KEY` | - | Google Gemini API key |

### 🌐 Backend Services

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | `http://localhost:8934` | Main backend API |
| `NEXT_PUBLIC_ORCHESTRATOR_URL` | `http://localhost:9093` | Orchestrator service |
| `NEXT_PUBLIC_HYBRID_URL` | `http://localhost:9099` | Hybrid Whisper server |
| `NEXT_PUBLIC_CONTEXT_WS` | `ws://localhost:9091/ws` | Context WebSocket |
| `NEXT_PUBLIC_ORCHESTRATOR_WS` | `ws://localhost:9093/ws` | Orchestrator WebSocket |

### 📊 Observability & Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAUDE_HOOKS_ENABLED` | `1` | Enable event tracking |
| `CLAUDE_HOOKS_SOURCE_APP` | `hypr-voice` | Source app identifier |
| `CLAUDE_HOOKS_OBS_URL` | `http://localhost:8787` | Observability server URL |
| `NEXT_PUBLIC_OBS_WS` | `ws://localhost:8787/ws` | Observability WebSocket |
| `NEXT_PUBLIC_OBS_HTTP` | `http://localhost:8787` | Observability HTTP endpoint |
| `CLAUDE_TTS_ALERTS` | `0` | Enable TTS alerts |
| `CLAUDE_STATUS_LINE` | `0` | Show status line |

### 🔍 Debugging & Logging

| Variable | Default | Production | Description |
|----------|---------|------------|-------------|
| `HYPR_VOICE_TRACE` | `1` | `0` | General tracing |
| `HYPR_VOICE_FLOW_TRACE` | `1` | `0` | Wispr Flow API tracing |
| `HYPR_VOICE_TRACE_CONTEXT` | `1` | `0` | Context system tracing |
| `HYPR_VOICE_TRACE_TCPGEN` | `1` | `0` | TCP generator tracing |
| `HYPR_VOICE_TRACE_QUEUE` | `1` | `0` | Queue tracing |

---

## 🎯 Recommended Configurations

### 🏃 Maximum Performance

For fastest transcription and TTS:

```bash
# Transcription
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_OPUS_BITRATE=24k
FLOW_STREAMING_MODE=1
WISPR_FLOW_CHUNK_SECONDS=30
WISPR_FLOW_AUTO_CHUNK=1

# TTS
HYPR_VOICE_TTS_STREAMING=1
HYPR_VOICE_TTS_REST_STREAMING=1
HYPR_VOICE_TTS_PREBUFFER_MS=800

# Logging (disable in production)
HYPR_VOICE_TRACE=0
HYPR_VOICE_FLOW_TRACE=0
```

**Expected Results:**
- 2-minute recordings: ~1s delay (vs 8s)
- Upload size: 300KB (vs 3MB)
- Near-instant audio streaming

### 🐛 Debugging Mode

For troubleshooting issues:

```bash
# Enable all logging
HYPR_VOICE_TRACE=1
HYPR_VOICE_FLOW_TRACE=1
HYPR_VOICE_TRACE_CONTEXT=1
HYPR_VOICE_TRACE_TCPGEN=1
HYPR_VOICE_TRACE_QUEUE=1

# Extended timeouts
WISPR_FLOW_TIMEOUT=900
CEREBRAS_TIMEOUT=120

# Debug mode
CEREBRAS_DEBUG=true
```

### 🔒 Production Mode

For stable production deployment:

```bash
# Disable debug logging
HYPR_VOICE_TRACE=0
HYPR_VOICE_FLOW_TRACE=0
CEREBRAS_DEBUG=false

# Conservative settings
WISPR_FLOW_CHUNK_SECONDS=27
CEREBRAS_MAX_RETRIES=5

# Keep optimizations
WISPR_FLOW_USE_OPUS=1
FLOW_STREAMING_MODE=1
```

---

## 🔧 Advanced Configuration

### Streaming Chunking Internals

The streaming chunking system uses these **internal defaults** (no env vars needed):

```python
# Automatically calculated from WISPR_FLOW_CHUNK_SECONDS
chunk_size_seconds = 27.0  # Optimal for Wispr Flow API
overlap_seconds = 3.0      # Fixed optimal overlap
min_duration = 20.0        # Activation threshold
```

**How it works:**
1. Records normally until 20 seconds
2. Activates streaming mode
3. Every 27 seconds → chunk sent to API in background
4. Results merge when recording stops

**To disable:** Set `FLOW_STREAMING_MODE=0`

### Connection Pooling

Wispr Flow uses persistent connections:

```bash
WISPR_FLOW_KEEPALIVE_INTERVAL=30  # Keepalive ping (seconds)
WISPR_FLOW_ASYNC_WARMUP=True      # Non-blocking connection warmup
WISPR_FLOW_CHUNK_MODE=1           # Enable chunk mode
```

---

## 📝 Configuration Tips

### 1. **Start Minimal**
Only set the 5 required API keys. Use defaults for everything else.

### 2. **Enable Performance Optimizations**
```bash
WISPR_FLOW_USE_OPUS=1
FLOW_STREAMING_MODE=1
```

### 3. **Disable Logging in Production**
```bash
HYPR_VOICE_TRACE=0
HYPR_VOICE_FLOW_TRACE=0
```

### 4. **Adjust Chunk Size for Your Use Case**
- **Longer chunks** (30s): Fewer API calls, faster for long recordings
- **Shorter chunks** (15s): More responsive, better for real-time

### 5. **Monitor Resource Usage**
Watch memory usage if processing very long recordings (10+ minutes).

---

## 🚨 Troubleshooting

### Transcription is Slow

**Check:**
```bash
WISPR_FLOW_USE_OPUS=1  # Should be enabled
FLOW_STREAMING_MODE=1   # Should be enabled
```

**Verify:**
```bash
# Look for these log messages:
✨ Streaming mode enabled: 27.0s chunks, 3.0s overlap
📦 Chunk ready: 27.1s (queue: 1)
⚡ Processing chunk 0 in background (27.0s)...
```

### Long Recordings Have Delays

**Check:**
```bash
FLOW_STREAMING_MODE=1
WISPR_FLOW_CHUNK_SECONDS=30
```

**Verify streaming is active:**
```bash
# You should see:
🚀 Background chunk processor started
⚡ Processing chunk 0 in background...
✅ Chunk 0 transcribed: ...
```

### API Timeouts

**Increase timeouts:**
```bash
WISPR_FLOW_TIMEOUT=900
CEREBRAS_TIMEOUT=120
HYPR_AGENT_TIMEOUT=1200
```

### Upload Failures

**Check encoding:**
```bash
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_MAX_BASE64_MB=50  # Increase if needed
```

---

## 📚 See Also

- [Quick Start Guide](../README.md)
- [Performance Optimization Plan](../report/streaming_chunking_optimization_plan.md)
- [Wispr Flow API Documentation](../src/hypr_voice/services/WISPR_FLOW_API.md)
- [TTS Configuration Guide](../src/hypr_voice/services/voice/docs/VOICE_CONFIG_GUIDE.md)

---

**Questions?** Check the logs with `HYPR_VOICE_TRACE=1` enabled!
