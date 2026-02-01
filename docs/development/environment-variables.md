# Environment Variables Reference

Complete reference for all environment variables used in Hypr-Voice.

## Table of Contents

- [Overview](#overview)
- [Required Variables](#required-variables)
- [Voice Transcription](#voice-transcription)
- [Text-to-Speech](#text-to-speech)
- [AI Providers](#ai-providers)
- [Backend Services](#backend-services)
- [Observability](#observability)
- [Development](#development)
- [Configuration Template](#configuration-template)

---

## Overview

Hypr-Voice uses environment variables for configuration, API keys, and runtime settings. Environment variables override default values in configuration files.

### Priority Order

1. **Environment variables** (highest priority)
2. **User configuration** (`~/.config/hypr-voice/`)
3. **System configuration** (`/etc/hypr-voice/`)
4. **Default configuration** (`config/hypr_voice/`)

---

## Required Variables

### Minimum Required Setup

```bash
# Required for basic operation
export CEREBRAS_API_KEY_ONE="your_key_here"
export WISPR_FLOW_JWT_TOKEN="your_jwt_token_here"
export WISPR_FLOW_BASETEN_API_KEY="your_baseten_key_here"
export WISPR_FLOW_USER_UUID="your_uuid_here"

# At least one TTS provider
export DEEPGRAM_API_KEY="your_deepgram_key_here"
# OR
export ELEVENLABS_API_KEY="your_elevenlabs_key_here"
```

### Variable Descriptions

| Variable | Description | How to Get |
|----------|-------------|------------|
| `CEREBRAS_API_KEY_ONE` | Cerebras AI API key | https://cloud.cerebras.ai |
| `WISPR_FLOW_JWT_TOKEN` | Wispr Flow JWT token | https://wispr-flow.baseten.co |
| `WISPR_FLOW_BASETEN_API_KEY` | Baseten API key | Baseten dashboard |
| `WISPR_FLOW_USER_UUID` | User UUID | Wispr Flow settings |
| `DEEPGRAM_API_KEY` | Deepgram TTS key | https://deepgram.com |
| `ELEVENLABS_API_KEY` | ElevenLabs TTS key | https://elevenlabs.io |

---

## Voice Transcription

### Wispr Flow Configuration

```bash
# Transcription mode
export MODE="FLOW"                  # FLOW or LOCAL

# Wispr Flow API
export WISPR_FLOW_BASETEN_URL="https://chain-o232k03l.api.baseten.co/environments/production/run_remote"
export WISPR_FLOW_PORT="9095"
export WISPR_FLOW_TIMEOUT="600"

# Performance
export WISPR_FLOW_CHUNK_SECONDS="30"
export WISPR_FLOW_USE_OPUS="1"     # 1 = enabled, 0 = disabled
export WISPR_FLOW_OPUS_BITRATE="24k"

# Chunking
export WISPR_FLOW_AUTO_CHUNK="1"
export WISPR_FLOW_CHUNK_OVERLAP="0.5"
export WISPR_FLOW_MAX_BASE64_MB="50"
export WISPR_FLOW_MAX_DICTIONARY_WORDS="50"

# Streaming (for 60s+ recordings)
export FLOW_STREAMING_MODE="1"

# User Info (optional)
export WISPR_FLOW_USER_FIRST_NAME="YourName"
export WISPR_FLOW_USER_LAST_NAME="YourLastName"
```

### Wispr Flow Options

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `MODE` | string | `"FLOW"` | Transcription mode (FLOW/LOCAL) |
| `WISPR_FLOW_BASETEN_URL` | string | - | Wispr Flow API URL |
| `WISPR_FLOW_PORT` | integer | `9095` | Wispr Flow port |
| `WISPR_FLOW_TIMEOUT` | integer | `600` | Request timeout (seconds) |
| `WISPR_FLOW_CHUNK_SECONDS` | integer | `30` | Chunk size (seconds) |
| `WISPR_FLOW_USE_OPUS` | boolean | `1` | Use Opus encoding |
| `WISPR_FLOW_OPUS_BITRATE` | string | `"24k"` | Opus bitrate |
| `WISPR_FLOW_AUTO_CHUNK` | boolean | `1` | Auto-chunking |
| `WISPR_FLOW_CHUNK_OVERLAP` | float | `0.5` | Chunk overlap (0-1) |
| `WISPR_FLOW_MAX_BASE64_MB` | integer | `50` | Max chunk size (MB) |
| `WISPR_FLOW_MAX_DICTIONARY_WORDS` | integer | `50` | Max dictionary words |
| `FLOW_STREAMING_MODE` | boolean | `1` | Streaming mode |

---

## Text-to-Speech

### TTS Configuration

```bash
# TTS Streaming
export HYPR_VOICE_TTS_STREAMING="1"
export HYPR_VOICE_TTS_REST_STREAMING="1"
export HYPR_VOICE_TTS_PREBUFFER_MS="800"
export HYPR_VOICE_TTS_MIN_CHARS="100"
export HYPR_VOICE_TTS_MAX_LATENCY="0.5"
export HYPR_VOICE_TTS_FLUSH_TIMEOUT="15"
export HYPR_VOICE_TTS_IDLE_TIMEOUT="3.0"

# Provider Selection
export HYPR_VOICE_TTS_PROVIDER="kokoro"  # kokoro, deepgram, elevenlabs
```

### TTS API Keys

```bash
# Deepgram
export DEEPGRAM_API_KEY="your_deepgram_key_here"

# ElevenLabs
export ELEVENLABS_API_KEY="your_elevenlabs_key_here"
```

### TTS Options

| Variable | Type | Default | Description |
|--------|------|---------|-------------|
| `HYPR_VOICE_TTS_PROVIDER` | string | `"kokoro"` | TTS provider |
| `HYPR_VOICE_TTS_STREAMING` | boolean | `1` | Enable streaming |
| `HYPR_VOICE_TTS_PREBUFFER_MS` | integer | `800` | Prebuffer (ms) |
| `HYPR_VOICE_TTS_MIN_CHARS` | integer | `100` | Min chars for streaming |
| `HYPR_VOICE_TTS_MAX_LATENCY` | float | `0.5` | Max latency (seconds) |
| `HYPR_VOICE_TTS_FLUSH_TIMEOUT` | integer | `15` | Flush timeout (seconds) |
| `HYPR_VOICE_TTS_IDLE_TIMEOUT` | float | `3.0` | Idle timeout (seconds) |

---

## AI Providers

### Cerebras Configuration

```bash
# Cerebras API Keys (rotating)
export CEREBRAS_API_KEY_ONE="your_key_1_here"
export CEREBRAS_API_KEY_TWO="your_key_2_here"
export CEREBRAS_API_KEY_THREE="your_key_3_here"

# Cerebras Settings
export CEREBRAS_PREFERRED_MODELS="gpt-oss-120b,llama-3.3-70b,qwen-3-235b-a22b-thinking-2507"
export CEREBRAS_TIMEOUT="60"
export CEREBRAS_MAX_RETRIES="3"
export CEREBRAS_DEBUG="false"
```

### Cerebras Options

| Variable | Type | Default | Description |
|--------|------|---------|-------------|
| `CEREBRAS_API_KEY_*` | string | - | API keys (rotating) |
| `CEREBRAS_PREFERRED_MODELS` | string | - | Comma-separated model list |
| `CEREBRAS_TIMEOUT` | integer | `60` | Request timeout (seconds) |
| `CEREBRAS_MAX_RETRIES` | integer | `3` | Max retry attempts |
| `CEREBRAS_DEBUG` | boolean | `false` | Debug logging |

### Anthropic / Claude (Z.ai Proxy)

```bash
export ANTHROPIC_AUTH_TOKEN="your_z_ai_token_here"
export ANTHROPIC_BASE_URL="https://api.z.ai/api/anthropic"
export ANTHROPIC_DEFAULT_SONNET_MODEL="GLM-4.6"
```

### Google Gemini

```bash
export GEMINI_API_KEY="your_gemini_key_here"
```

### CFS Image Generation

```bash
export CFS_API_KEY="your_cfs_key_here"
```

---

## Backend Services

### Backend URLs

```bash
# Backend Services
export NEXT_PUBLIC_BACKEND_URL="http://localhost:8934"
export NEXT_PUBLIC_ORCHESTRATOR_URL="http://localhost:9093"
export NEXT_PUBLIC_HYBRID_URL="http://localhost:9099"

# WebSocket Services
export NEXT_PUBLIC_CONTEXT_WS="ws://localhost:9091/ws"
export NEXT_PUBLIC_ORCHESTRATOR_WS="ws://localhost:9093/ws"
```

### Backend Options

| Variable | Type | Default | Description |
|--------|------|---------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | string | - | Backend API URL |
| `NEXT_PUBLIC_ORCHESTRATOR_URL` | string | - | Orchestrator URL |
| `NEXT_PUBLIC_HYBRID_URL` | string | - | Hybrid server URL |
| `NEXT_PUBLIC_CONTEXT_WS` | string | - | Context WebSocket URL |
| `NEXT_PUBLIC_ORCHESTRATOR_WS` | string | - | Orchestrator WebSocket URL |

---

## Observability

### Claude Hooks

```bash
# Claude Hooks
export CLAUDE_HOOKS_ENABLED="1"
export CLAUDE_HOOKS_SOURCE_APP="hypr-voice"
export CLAUDE_HOOKS_OBS_URL="http://localhost:8787"

# Observability WebSockets
export NEXT_PUBLIC_OBS_WS="ws://localhost:8787/ws"
export NEXT_PUBLIC_OBS_HTTP="http://localhost:8787"

# Optional Alerts
export CLAUDE_TTS_ALERTS="0"
export CLAUDE_STATUS_LINE="0"
```

### Observability Options

| Variable | Type | Default | Description |
|--------|------|---------|-------------|
| `CLAUDE_HOOKS_ENABLED` | boolean | `1` | Enable Claude hooks |
| `CLAUDE_HOOKS_SOURCE_APP` | string | `"hypr-voice"` | Source app name |
| `CLAUDE_HOOKS_OBS_URL` | string | - | Observability URL |
| `NEXT_PUBLIC_OBS_WS` | string | - | Obs WebSocket URL |
| `NEXT_PUBLIC_OBS_HTTP` | string | - | Obs HTTP URL |
| `CLAUDE_TTS_ALERTS` | boolean | `0` | TTS alerts |
| `CLAUDE_STATUS_LINE` | boolean | `0` | Status line |

---

## Development

### Sandbox Configuration

```bash
# E2B Sandbox
export HYPR_VOICE_E2B_ENABLED="1"
export HYPR_VOICE_E2B_TEMPLATE="agent-sandbox-dev-node22"
```

### Timeouts and Limits

```bash
# Agent Timeout
export HYPR_AGENT_TIMEOUT="900"

# Wispr Flow Keepalive
export WISPR_FLOW_KEEPALIVE_INTERVAL="30"
export WISPR_FLOW_ASYNC_WARMUP="True"
export WISPR_FLOW_CHUNK_MODE="1"
```

### Debugging

```bash
# Enable detailed logging
export HYPR_VOICE_TRACE="1"
export HYPR_VOICE_FLOW_TRACE="1"
export HYPR_VOICE_TRACE_CONTEXT="1"
export HYPR_VOICE_TRACE_TCPGEN="1"
export HYPR_VOICE_TRACE_QUEUE="1"
```

### Debug Options

| Variable | Type | Default | Description |
|--------|------|---------|-------------|
| `HYPR_VOICE_TRACE` | boolean | `1` | General tracing |
| `HYPR_VOICE_FLOW_TRACE` | boolean | `1` | Flow tracing |
| `HYPR_VOICE_TRACE_CONTEXT` | boolean | `1` | Context tracing |
| `HYPR_VOICE_TRACE_TCPGEN` | boolean | `1` | TCPGen tracing |
| `HYPR_VOICE_TRACE_QUEUE` | boolean | `1` | Queue tracing |

### MCP Server Environment Variables

```bash
# GitHub MCP Server
export GITHUB_TOKEN="your_github_token_here"

# Brave Search MCP Server
export BRAVE_API_KEY="your_brave_api_key_here"

# PostgreSQL MCP Server
export DATABASE_URL="postgresql://user:password@localhost/dbname"

# Custom API Keys
export API_KEY="your_custom_api_key_here"
```

---

## Configuration Template

### Complete .env Template

```bash
# ==============================================================================
# HYPR-VOICE CONFIGURATION TEMPLATE
# ==============================================================================
# Copy this file to .env and fill in your actual values

# ==============================================================================
# REQUIRED - API KEYS
# ==============================================================================

# CEREBRAS API - Primary LLM Provider
CEREBRAS_API_KEY_ONE=your_key_here
CEREBRAS_API_KEY_TWO=your_key_here
CEREBRAS_API_KEY_THREE=your_key_here

# WISPR FLOW - Transcription Service
WISPR_FLOW_JWT_TOKEN=your_jwt_token_here
WISPR_FLOW_BASETEN_API_KEY=your_baseten_key_here
WISPR_FLOW_USER_UUID=your_uuid_here

# TTS Providers (at least one required)
DEEPGRAM_API_KEY=your_deepgram_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# ==============================================================================
# VOICE TRANSCRIPTION
# ==============================================================================

MODE=FLOW
WISPR_FLOW_BASETEN_URL=https://chain-o232k03l.api.baseten.co/environments/production/run_remote
WISPR_FLOW_PORT=9095
WISPR_FLOW_TIMEOUT=600
WISPR_FLOW_CHUNK_SECONDS=30
WISPR_FLOW_USE_OPUS=1
WISPR_FLOW_OPUS_BITRATE=24k
WISPR_FLOW_AUTO_CHUNK=1
WISPR_FLOW_CHUNK_OVERLAP=0.5
FLOW_STREAMING_MODE=1

# ==============================================================================
# TEXT-TO-SPEECH
# ==============================================================================

HYPR_VOICE_TTS_STREAMING=1
HYPR_VOICE_TTS_REST_STREAMING=1
HYPR_VOICE_TTS_PREBUFFER_MS=800
HYPR_VOICE_TTS_MIN_CHARS=100
HYPR_VOICE_TTS_MAX_LATENCY=0.5

# ==============================================================================
# AI PROVIDERS
# ==============================================================================

CEREBRAS_PREFERRED_MODELS=gpt-oss-120b,llama-3.3-70b
CEREBRAS_TIMEOUT=60
CEREBRAS_MAX_RETRIES=3

ANTHROPIC_AUTH_TOKEN=your_z_ai_token_here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic

# ==============================================================================
# BACKEND SERVICES
# ==============================================================================

NEXT_PUBLIC_BACKEND_URL=http://localhost:8934
NEXT_PUBLIC_ORCHESTRATOR_URL=http://localhost:9093
NEXT_PUBLIC_HYBRID_URL=http://localhost:9099

# ==============================================================================
# OBSERVABILITY
# ==============================================================================

CLAUDE_HOOKS_ENABLED=1
CLAUDE_HOOKS_OBS_URL=http://localhost:8787
NEXT_PUBLIC_OBS_WS=ws://localhost:8787/ws

# ==============================================================================
# DEBUGGING (set to 0 in production)
# ==============================================================================

HYPR_VOICE_TRACE=1
HYPR_VOICE_FLOW_TRACE=1
```

---

## Best Practices

### Security

1. **Never commit .env files** to version control
2. **Use different keys** for development and production
3. **Rotate keys regularly** (especially for production)
4. **Use key management services** for production deployments

### Performance

1. **Enable Opus encoding** for 10x faster uploads
2. **Use streaming mode** for long recordings (60s+)
3. **Adjust chunk size** based on your needs (30s recommended)
4. **Enable auto-chunking** for automatic optimization

### Development

1. **Enable trace logging** during development
2. **Disable in production** for better performance
3. **Use environment-specific** .env files (`.env.development`, `.env.production`)

---

## See Also

- [Configuration Reference](configuration-reference.md)
- [Whisper Configuration](whisper-config.md)
- [Voice Configuration](voice-config.md)
- [Development Setup](../README.md)
