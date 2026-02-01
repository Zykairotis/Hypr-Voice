# Hypr-Voice Authentication & Authorization

## Overview

Hypr-Voice currently implements an open API architecture with no mandatory authentication for local development. This document describes the current authentication state and patterns for implementing authentication when deploying to production environments.

**Current Status**: No authentication required (default)

**Recommended**: Implement authentication for production deployments

---

## Table of Contents

- [Current Authentication State](#current-authentication-state)
- [Environment Variables](#environment-variables)
- [API Key Configuration](#api-key-configuration)
- [Permission System](#permission-system)
- [Rate Limiting](#rate-limiting)
- [Security Best Practices](#security-best-practices)
- [Production Deployment](#production-deployment)

---

## Current Authentication State

### Development Mode (Default)

In the default configuration, the Hypr-Voice API:

1. **No authentication required** on any endpoint
2. **CORS enabled** for all origins (`allow_origins=["*"]`)
3. **No rate limiting** enforced
4. **Open WebSocket** connections

This configuration is suitable for:
- Local development
- Private network deployments
- Behind a reverse proxy with external authentication
- Testing and demonstration

### Example Request (No Auth)

```bash
curl -X POST http://localhost:9091/voice/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, world!", "speak_response": true}'
```

---

## Environment Variables

### API Keys

Configure API keys for external services:

```bash
# Anthropic Claude API
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Deepgram TTS
export DEEPGRAM_API_KEY="your-deepgram-api-key"

# ElevenLabs TTS (optional)
export ELEVENLABS_API_KEY="your-elevenlabs-api-key"

# Wispr Flow (optional transcription)
export WISPR_FLOW_JWT_TOKEN="your-wispr-jwt-token"
export WISPR_FLOW_BASETEN_API_KEY="your-baseten-api-key"

# Cerebras Router (optional)
export CEREBRAS_API_KEY="your-cerebras-api-key"

# GitHub (for MCP tools)
export GITHUB_TOKEN="your-github-token"

# Brave Search (for MCP tools)
export BRAVE_API_KEY="your-brave-api-key"
```

### Service Configuration

```bash
# Server Configuration
export HYPR_VOICE_HOST="0.0.0.0"
export HYPR_VOICE_PORT="9091"

# Model Configuration
export HYPR_VOICE_MODEL="claude-sonnet-4-5"
export HYPR_VOICE_MAX_TURNS="20"

# TTS Configuration
export HYPR_VOICE_TTS_PROVIDER="deepgram"
export HYPR_VOICE_TTS_VOICE="aura-luna-en"

# Working Directory
export HYPR_VOICE_WORKING_DIR="/path/to/workspace"
```

---

## API Key Configuration

### Adding Authentication (Custom Implementation)

To add authentication to your Hypr-Voice deployment, implement a FastAPI middleware:

```python
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader

API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

VALID_API_KEYS = {
    "your-api-key-here": "app-name",
    "another-key": "another-app"
}

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header in VALID_API_KEYS:
        return api_key_header
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing API Key"
    )

# Use in endpoints
@app.post("/voice/process", dependencies=[Depends(get_api_key)])
async def voice_process(request: VoiceProcessRequest):
    ...
```

### Environment-based API Keys

```python
import os

VALID_API_KEYS = os.getenv("HYPR_API_KEYS", "").split(",")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if not VALID_API_KEYS or api_key in VALID_API_KEYS:
        return api_key
    raise HTTPException(status_code=401, detail="Invalid API key")
```

---

## Permission System

### Agent Tool Permissions

Hypr-Voice implements a permission system for agent tool usage:

#### Permission Modes

```python
class PermissionMode(str, Enum):
    AUTO = "auto"           # Automatically approve all tools
    MANUAL = "manual"       # Require approval for each tool use
    DEFAULT = "default"     # Auto-approve safe tools, manual for risky
```

#### Configuration

```python
class AgentConfig(BaseModel):
    permission_mode: str = "default"
    permission_timeout: int = 30  # seconds
    allowed_tools: List[str] = [
        "Read", "Write", "Edit", "Grep", "Glob",
        "Bash", "Skill", "SlashCommand"
    ]
```

#### Permission Callback

When an agent attempts to use a tool, a permission request event is emitted:

```json
{
  "event_type": "tool_execution",
  "agent_id": "uuid",
  "timestamp": "2026-01-26T12:00:00Z",
  "data": {
    "type": "permission_request",
    "request_id": "uuid",
    "tool_name": "Bash",
    "tool_input": {
      "command": "rm -rf /"
    }
  }
}
```

#### Responding to Permission Requests

Via WebSocket:

```json
{
  "type": "permission_response",
  "request_id": "uuid",
  "agent_id": "target-agent-id",
  "allow": false,
  "reason": "Dangerous command detected"
}
```

Or with modified input:

```json
{
  "type": "permission_response",
  "request_id": "uuid",
  "agent_id": "target-agent-id",
  "allow": true,
  "updated_input": {
    "command": "ls -la"
  }
}
```

---

## Rate Limiting

### Current Implementation

Rate limiting is not enforced by default. Implement custom rate limiting for production:

### Using SlowAPI (FastAPI)

```python
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/voice/process")
@limiter.limit("10/minute")
async def voice_process(request: Request, ...):
    ...
```

### Using Redis-backed Rate Limiting

```python
import redis
from fastapi import Request

redis_client = redis.Redis(host='localhost', port=6379, db=0)

async def check_rate_limit(client_id: str, limit: int = 60):
    key = f"rate_limit:{client_id}"
    current = redis_client.incr(key)
    if current == 1:
        redis_client.expire(key, 60)
    if current > limit:
        return False
    return True

@app.post("/voice/process")
async def voice_process(request: Request, ...):
    client_id = get_remote_address(request)
    if not await check_rate_limit(client_id, limit=60):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    ...
```

---

## Security Best Practices

### 1. Reverse Proxy Authentication

Place Hypr-Voice behind a reverse proxy that handles authentication:

#### Nginx Example

```nginx
server {
    listen 443 ssl;
    server_name voice.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Basic Auth
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;

    location / {
        proxy_pass http://localhost:9091;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### OAuth2 with Nginx

```nginx
# Use oauth2_proxy
auth_request /oauth2/auth;
error_page 401 = /oauth2/sign_in;

location /oauth2/sign_in {
    proxy_pass https://oauth2-proxy.example.com;
}

location /oauth2/auth {
    proxy_pass https://oauth2-proxy.example.com/auth;
}
```

### 2. Network Isolation

- Bind to `127.0.0.1` for local-only access
- Use firewall rules to restrict access
- Deploy in private VPC subnets
- Use VPN for remote access

### 3. CORS Configuration

Restrict CORS origins in production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
```

### 4. Input Validation

Always validate and sanitize inputs:

```python
from pydantic import validator, constr

class VoiceProcessRequest(BaseModel):
    text: constr(max_length=10000)  # Limit text length

    @validator('text')
    def validate_text(cls, v):
        # Sanitize input
        if not v or not v.strip():
            raise ValueError('Text cannot be empty')
        return v.strip()
```

### 5. File Upload Security

For transcription endpoints:

```python
ALLOWED_EXTENSIONS = {'.wav', '.mp3', '.ogg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_audio_file(file: UploadFile):
    # Check extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid file type")

    # Check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(400, "File too large")

    await file.seek(0)
    return file
```

---

## Production Deployment

### Docker Compose with Traefik

```yaml
version: '3.8'

services:
  hypr-voice:
    image: hypr-voice:latest
    environment:
      - HYPR_VOICE_HOST=0.0.0.0
      - HYPR_VOICE_PORT=9091
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.hypr-voice.rule=Host(`voice.example.com`)"
      - "traefik.http.routers.hypr-voice.tls=true"
      - "traefik.http.routers.hypr-voice.tls.certresolver=letsencrypt"
      - "traefik.http.middlewares.hypr-auth.basicauth.users=${HTTP_AUTH_USERS}"
      - "traefik.http.routers.hypr-voice.middlewares=hypr-auth"
    networks:
      - web

  traefik:
    image: traefik:v2.10
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik/acme.json:/acme.json
    networks:
      - web

networks:
  web:
    external: true
```

### Environment Configuration for Production

```bash
# .env.production
HYPR_VOICE_ENV=production
HYPR_VOICE_HOST=127.0.0.1  # Local only, behind proxy
HYPR_VOICE_PORT=9091

# API Keys (secure, from secret manager)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
DEEPGRAM_API_KEY=${DEEPGRAM_API_KEY}

# Security
HYPR_ENABLE_AUTH=true
HYPR_API_KEYS=${API_KEYS_FROM_SECRET_MANAGER}
HYPR_RATE_LIMIT=100
HYPR_RATE_WINDOW=60

# Logging
HYPR_LOG_LEVEL=INFO
HYPR_LOG_REQUESTS=true
```

---

## WebSocket Security

### Origin Validation

```python
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    origin = websocket.headers.get("origin")
    allowed_origins = ["https://your-domain.com"]

    if origin not in allowed_origins:
        await websocket.close(code=1008)
        return

    await websocket.accept()
```

### Token-based WebSocket Auth

```python
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    # Validate token
    if not validate_token(token):
        await websocket.close(code=4008, reason="Invalid token")
        return

    await websocket.accept()
```

---

## Auditing and Logging

### Enable Request Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_requests.log'),
        logging.StreamHandler()
    ]
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Status: {response.status_code}")
    return response
```

### Audit Sensitive Operations

```python
async def audit_log(event_type: str, details: dict):
    logger.info(f"AUDIT: {event_type} - {json.dumps(details)}")

# Log permission requests
await audit_log("permission_request", {
    "agent_id": agent_id,
    "tool": tool_name,
    "input": tool_input,
    "decision": "approved" if allow else "denied"
})
```

---

## Summary

- **Current**: No authentication required (development mode)
- **Production**: Implement authentication via reverse proxy or custom middleware
- **Permissions**: Built-in permission system for agent tool usage
- **Security**: Use rate limiting, CORS restrictions, input validation
- **Deployment**: Place behind secure reverse proxy with TLS

For production deployments, always:
1. Enable authentication
2. Use HTTPS/TLS
3. Implement rate limiting
4. Restrict CORS origins
5. Monitor and audit access
6. Keep API keys secure
7. Regular security updates
