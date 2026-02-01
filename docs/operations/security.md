# Security Hardening Guide - Hypr-Voice

Comprehensive security hardening procedures for Hypr-Voice deployments.

## Table of Contents

1. [Security Overview](#security-overview)
2. [API Key Management](#api-key-management)
3. [Network Security](#network-security)
4. [Application Security](#application-security)
5. [Authentication & Authorization](#authentication--authorization)
6. [Data Protection](#data-protection)
7. [System Security](#system-security)
8. [Audit Logging](#audit-logging)
9. [Vulnerability Management](#vulnerability-management)
10. [Compliance](#compliance)

---

## Security Overview

### Security Principles

| Principle | Implementation |
|-----------|----------------|
| **Defense in Depth** | Multiple security layers |
| **Least Privilege** | Minimal access required |
| **Fail Securely** | Secure defaults |
| **Encrypt Everywhere** | Data at rest and in transit |
| **Audit Everything** | Comprehensive logging |

### Security Architecture

```
┌─────────────────────────────────────────────────┐
│                 Security Layers                 │
├─────────────────────────────────────────────────┤
│                                                   │
│  ┌──────────────────────────────────────────┐  │
│  │ 7. Application Security (Auth, RBAC)     │  │
│  ├──────────────────────────────────────────┤  │
│  │ 6. API Security (Rate limiting, Headers) │  │
│  ├──────────────────────────────────────────┤  │
│  │ 5. Network Security (Firewall, TLS)      │  │
│  ├──────────────────────────────────────────┤  │
│  │ 4. System Security (Hardening, Patches)  │  │
│  ├──────────────────────────────────────────┤  │
│  │ 3. Data Security (Encryption, Keys)      │  │
│  ├──────────────────────────────────────────┤  │
│  │ 2. Infrastructure Security (Isolation)   │  │
│  ├──────────────────────────────────────────┤  │
│  │ 1. Physical Security (Access Control)    │  │
│  └──────────────────────────────────────────┘  │
│                                                   │
└─────────────────────────────────────────────────┘
```

---

## API Key Management

### Environment Variable Security

```bash
# NEVER commit .env file
echo ".env" >> .gitignore

# Set proper permissions
chmod 600 .env
chown $USER:$USER .env

# Validate .env before starting
if [ -f .env ]; then
    source .env
    if [ -z "$CEREBRAS_API_KEY_ONE" ]; then
        echo "Error: Required API keys not set"
        exit 1
    fi
fi
```

### Key Rotation Strategy

```bash
#!/bin/bash
# rotate_keys.sh

# Backup current .env
cp .env .env.backup

# Generate new keys (placeholder)
NEW_KEY=$(openssl rand -hex 32)

# Update .env
sed -i "s/CEREBRAS_API_KEY_ONE=.*/CEREBRAS_API_KEY_ONE=$NEW_KEY/" .env

# Restart services
./scripts/start_everything.sh restart

echo "Key rotated. Backup saved as .env.backup"
```

### Secrets Management

#### Using HashiCorp Vault

```bash
# Install Vault
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | \
    sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install vault

# Configure Vault
vault login token=<your-token>

# Store secrets
vault kv put secret/hypr-voice \
    cerebras_api_key="$CEREBRAS_API_KEY_ONE" \
    deepgram_api_key="$DEEPGRAM_API_KEY"

# Retrieve secrets in application
export CEREBRAS_API_KEY_ONE=$(vault kv get -field=cerebras_api_key secret/hypr-voice)
```

#### Using AWS Secrets Manager

```python
import boto3
import json

client = boto3.client('secretsmanager')

def get_secret(secret_name):
    """Get secret from AWS Secrets Manager"""
    response = client.get_secret_value(SecretId=secret_name)
    secret = json.loads(response['SecretString'])
    return secret

# Usage
secrets = get_secret('hypr-voice/prod')
CEREBRAS_API_KEY_ONE = secrets['cerebras_api_key']
```

---

## Network Security

### Firewall Configuration

```bash
# UFW (Uncomplicated Firewall)

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow application ports (restrict to specific IPs if possible)
sudo ufw allow from 192.168.1.0/24 to any port 9099  # Hybrid server
sudo ufw allow from 192.168.1.0/24 to any port 9093  # Orchestrator

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Reverse Proxy with NGINX

```nginx
# /etc/nginx/sites-available/hypr-voice

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=ws_limit:10m rate=5r/s;

server {
    listen 443 ssl http2;
    server_name hypr-voice.example.com;

    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/hypr-voice.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hypr-voice.example.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://localhost:9099/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 300s;
    }

    # WebSocket
    location /ws {
        limit_req zone=ws_limit burst=10 nodelay;

        proxy_pass http://localhost:9099/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;

        # WebSocket timeouts
        proxy_connect_timeout 7d;
        proxy_send_timeout 7d;
        proxy_read_timeout 7d;
    }

    # File upload limits
    client_max_body_size 500M;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    server_name hypr-voice.example.com;
    return 301 https://$server_name$request_uri;
}
```

### SSL/TLS Configuration

```bash
# Let's Encrypt certificate
sudo apt install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d hypr-voice.example.com

# Auto-renewal (already configured)
sudo certbot renew --dry-run

# Strong SSL configuration
sudo cat > /etc/nginx/conf.d/ssl.conf <<'EOF'
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_session_tickets off;

# Modern configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers off;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
EOF
```

---

## Application Security

### Input Validation

```python
from pydantic import BaseModel, validator, Field
import re

class TranscriptionRequest(BaseModel):
    audio_data: bytes
    language: str = "en"
    model: str = "small.en"

    @validator('language')
    def validate_language(cls, v):
        """Validate language code"""
        allowed = ['en', 'es', 'fr', 'de', 'it']
        if v not in allowed:
            raise ValueError(f'Language must be one of {allowed}')
        return v

    @validator('model')
    def validate_model(cls, v):
        """Validate model name"""
        allowed = ['tiny.en', 'base.en', 'small.en', 'medium.en']
        if v not in allowed:
            raise ValueError(f'Model must be one of {allowed}')
        return v
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/transcribe")
@limiter.limit("10/minute")  # 10 requests per minute
async def transcribe(
    request: Request,
    audio: UploadFile
):
    # Transcription logic
    pass
```

### SQL Injection Prevention

```python
# Use parameterized queries (if using database)

import sqlite3

def save_transcription(session_id: str, text: str):
    """Save transcription to database"""
    conn = sqlite3.connect('hypr_voice.db')
    cursor = conn.cursor()

    # SAFE: Parameterized query
    cursor.execute(
        "INSERT INTO transcriptions (session_id, text) VALUES (?, ?)",
        (session_id, text)
    )

    conn.commit()
    conn.close()
```

### XSS Prevention

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import html

@app.post("/api/process")
async def process_text(text: str):
    """Sanitize user input"""
    # Escape HTML entities
    sanitized = html.escape(text)

    # Return as JSON (not HTML)
    return JSONResponse({
        "result": sanitized
    })
```

---

## Authentication & Authorization

### JWT Authentication

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key"  # Use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token"""
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile,
    token: dict = Depends(verify_token)
):
    """Protected endpoint"""
    # Transcription logic
    pass
```

### API Key Authentication

```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key"""
    valid_keys = os.getenv("VALID_API_KEYS", "").split(",")

    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return x_api_key

@app.post("/api/transcribe")
async def transcribe(
    audio: UploadFile,
    api_key: str = Depends(verify_api_key)
):
    """Protected endpoint"""
    pass
```

### Role-Based Access Control (RBAC)

```python
from enum import Enum

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class User:
    def __init__(self, username: str, role: Role):
        self.username = username
        self.role = role

def require_role(required_role: Role):
    """Decorator to require specific role"""
    def decorator(func):
        async def wrapper(*args, user: User = Depends(get_current_user), **kwargs):
            if user.role != required_role and user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=403,
                    detail=f"Requires {required_role} role"
                )
            return await func(*args, user=user, **kwargs)
        return wrapper
    return decorator

@app.delete("/api/users/{user_id}")
@require_role(Role.ADMIN)
async def delete_user(user_id: str, user: User = Depends(get_current_user)):
    """Admin-only endpoint"""
    pass
```

---

## Data Protection

### Encryption at Rest

```python
from cryptography.fernet import Fernet
import base64

def generate_key():
    """Generate encryption key"""
    return Fernet.generate_key()

def encrypt_data(data: str, key: bytes) -> bytes:
    """Encrypt data"""
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    """Decrypt data"""
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()

# Usage
key = os.getenv("ENCRYPTION_KEY")  # Store in environment
sensitive_data = "user_conversation_text"
encrypted = encrypt_data(sensitive_data, key)
```

### Encryption in Transit

```python
# Enforce HTTPS
from fastapi import FastAPI
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

app = FastAPI()

# Redirect HTTP to HTTPS
app.add_middleware(HTTPSRedirectMiddleware)

# Or use HSTS
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["hypr-voice.example.com"]
)
```

### PII Redaction

```python
import re

def redact_pii(text: str) -> str:
    """Redact personally identifiable information"""

    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)

    # Phone numbers
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)

    # Credit card numbers
    text = re.sub(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]', text)

    # SSN
    text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)

    return text
```

---

## System Security

### System Hardening

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Remove unnecessary packages
sudo apt autoremove -y

# 3. Disable unused services
sudo systemctl disable bluetooth
sudo systemctl stop bluetooth

# 4. Secure SSH
sudo cat > /etc/ssh/sshd_config.d/hypr-voice.conf <<'EOF'
# Disable root login
PermitRootLogin no

# Disable password authentication (use keys only)
PasswordAuthentication no

# Limit users
AllowUsers hyprvoice

# Change port (optional)
Port 2222
EOF

sudo systemctl restart sshd

# 5. Configure automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### File Permissions

```bash
# Set proper ownership
sudo chown -R hyprvoice:hyprvoice /opt/hypr-voice

# Set restrictive permissions
find /opt/hypr-voice -type d -exec chmod 750 {} \;
find /opt/hypr-voice -type f -exec chmod 640 {} \;

# Exception: Executable scripts
find /opt/hypr-voice/scripts -type f -exec chmod 750 {} \;

# Protect sensitive files
chmod 600 /opt/hypr-voice/.env
chmod 600 /opt/hypr-voice/config/hypr_voice/whisper/config.yaml

# Protect logs
chmod 640 /opt/hypr-voice/logs/*.log
chown hyprvoice:adm /opt/hypr-voice/logs/*.log
```

### AppArmor/SELinux

```bash
# Install AppArmor
sudo apt install apparmor apparmor-utils

# Create profile for Hypr-Voice
sudo cat > /etc/apparmor.d/opt.hypr-voice.hybrid-server <<'EOF'
#include <tunables/global>

/opt/hypr-voice/.venv/bin/python {
  #include <abstractions/base>
  #include <abstractions/python>

  /opt/hypr-voice/** r,
  /opt/hypr-voice/.venv/** rix,
  /tmp/whisper-* rw,
  /tmp/hypr-voice* rw,
  /var/log/hypr-voice/** w,

  deny /root/** rw,
  deny /home/** rw,
}
EOF

# Load profile
sudo aa-enforce /etc/apparmor.d/opt.hypr-voice.hybrid-server
```

---

## Audit Logging

### Security Event Logging

```python
import logging
from datetime import datetime

audit_logger = logging.getLogger('security')

def log_security_event(event_type: str, details: dict):
    """Log security event"""
    audit_logger.info(json.dumps({
        "timestamp": datetime.utcnow().isoformat(),
        "event_type": event_type,
        "details": details,
        "source_ip": details.get("source_ip"),
        "user": details.get("user", "anonymous")
    }))

# Usage
log_security_event("auth_success", {
    "user": "admin",
    "source_ip": "192.168.1.100"
})

log_security_event("auth_failure", {
    "user": "unknown",
    "source_ip": "192.168.1.200",
    "reason": "invalid_api_key"
})
```

### Audit Log Review

```bash
#!/bin/bash
# review_audit_logs.sh

audit_log="/var/log/hypr-voice/security.log"

echo "=== Security Audit Report ==="
echo "Generated: $(date)"
echo ""

# Failed authentication attempts
echo "Failed Authentication Attempts:"
grep "auth_failure" "$audit_log" | tail -10

echo ""
echo "Unauthorized Access Attempts:"
grep "unauthorized" "$audit_log" | tail -10

echo ""
echo "High-Risk Events:"
grep -E "auth_failure|unauthorized|rate_limit" "$audit_log" | wc -l

echo ""
echo "Unique Source IPs:"
grep "source_ip" "$audit_log" | grep -oP '"source_ip": "\K[^"]+' | sort -u
```

---

## Vulnerability Management

### Dependency Scanning

```bash
# Install safety
pip install safety

# Scan for vulnerabilities
safety check --file requirements.txt

# Automatic scanning in CI/CD
echo "pip install safety && safety check --file requirements.txt" >> .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### Bandit (Security Linter)

```bash
# Install Bandit
pip install bandit

# Scan code
bandit -r src/hypr_voice/

# Exclude test files
bandit -r src/hypr_voice/ - skips "*/tests/*"
```

### OWASP ZAP (Security Testing)

```bash
# Install OWASP ZAP
sudo apt install zaproxy

# Run security scan
zap-cli quick-scan --self-contained \
    --start-options '-config api.disablekey=true' \
    http://localhost:9099
```

### Regular Updates

```bash
#!/bin/bash
# security_updates.sh

# Update system packages
sudo apt update
sudo apt upgrade -y

# Update Python dependencies
pip list --outdated

# Security update
pip install --upgrade pip
pip install --upgrade safety
safety check --upgrade
```

---

## Compliance

### GDPR Compliance

```python
# Data deletion (Right to be Forgotten)

def delete_user_data(user_id: str):
    """Delete all user data"""
    # Delete from database
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # Delete conversation history
    db.execute("DELETE FROM conversations WHERE user_id = ?", (user_id,))

    # Delete audio recordings
    import os
    recordings_dir = f"/opt/hypr-voice/recordings/{user_id}"
    if os.path.exists(recordings_dir):
        import shutil
        shutil.rmtree(recordings_dir)

    # Log deletion
    log_security_event("data_deletion", {"user_id": user_id})
```

### SOC 2 Considerations

```python
# Access logging
def log_access(user_id: str, resource: str, action: str):
    """Log all access to sensitive resources"""
    log_security_event("resource_access", {
        "user_id": user_id,
        "resource": resource,
        "action": action,
        "timestamp": datetime.utcnow().isoformat()
    })

# Data encryption at rest
def encrypt_sensitive_data(data: str):
    """Encrypt sensitive data"""
    key = os.getenv("ENCRYPTION_KEY")
    return encrypt_data(data, key)
```

---

## Security Checklist

### Initial Setup

- [ ] Change default passwords
- [ ] Set up firewall rules
- [ ] Configure SSL/TLS
- [ ] Set up reverse proxy
- [ ] Implement rate limiting
- [ ] Configure audit logging
- [ ] Set up automated backups
- [ ] Enable intrusion detection

### Ongoing Maintenance

- [ ] Regular security updates
- [ ] Dependency vulnerability scans
- [ ] Log review and analysis
- [ ] Access audit
- [ ] Penetration testing
- [ ] Security training
- [ ] Incident response drills

### Monitoring

- [ ] Failed login attempts
- [ ] Unusual API usage
- [ ] Rate limit violations
- [ ] Data access patterns
- [ ] System resource anomalies
- [ ] Network traffic analysis

---

## Next Steps

1. Implement [Monitoring](monitoring.md)
2. Configure [Logging](logging.md)
3. Setup [Backups](backup-recovery.md)
4. Optimize [Performance](performance-tuning.md)
