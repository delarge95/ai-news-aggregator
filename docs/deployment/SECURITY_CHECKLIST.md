# Lista de Verificación de Seguridad

## Tabla de Contenidos
- [Hardening del Sistema](#hardening-del-sistema)
- [Configuración de Red](#configuración-de-red)
- [Seguridad de Aplicación](#seguridad-de-aplicación)
- [Seguridad de Base de Datos](#seguridad-de-base-de-datos)
- [Seguridad de Docker](#seguridad-de-docker)
- [Gestión de Secretos](#gestión-de-secretos)
- [Seguridad de Certificados](#seguridad-de-certificados)
- [Monitoreo de Seguridad](#monitoreo-de-seguridad)
- [Backup Seguro](#backup-seguro)
- [Compliance](#compliance)

## Hardening del Sistema

### 1. Sistema Operativo

```bash
#!/bin/bash
# security-hardening.sh

echo "🔒 Iniciando hardening del sistema..."

# Actualizar sistema
apt update && apt upgrade -y

# Instalar herramientas de seguridad
apt install -y fail2ban ufw rkhunter chkrootkit aide

# Configurar fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
ignoreip = 127.0.0.1/8 ::1

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 7200

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 10

[nginx-noscript]
enabled = true
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6

[nginx-badbots]
enabled = true
filter = nginx-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
EOF

# Configurar fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# Configurar firewall UFW
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow from 10.116.0.0/16 to any port 8000
ufw allow from 10.116.0.0/16 to any port 6379
ufw allow from 10.116.0.0/16 to any port 5432
ufw enable

# Deshabilitar servicios innecesarios
systemctl disable bluetooth
systemctl disable cups
systemctl disable avahi-daemon

# Configurar kernel parameters
cat >> /etc/sysctl.conf << 'EOF'
# Network security
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# IPv6 security
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_source_route = 0
net.ipv6.conf.default.accept_source_route = 0

# Protect against TCP time-wait assassination hazards
net.ipv4.tcp_rfc1337 = 1

# Controls IP packet forwarding
net.ipv4.ip_forward = 0
EOF

sysctl -p

echo "✅ Hardening del sistema completado"
```

### 2. SSH Hardening

```bash
# /etc/ssh/sshd_config
Port 2222
Protocol 2
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
HostKey /etc/ssh/ssh_host_ed25519_key

# Authentication
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PermitEmptyPasswords no
ChallengeResponseAuthentication no
KerberosAuthentication no
GSSAPIAuthentication no

# Timeout
LoginGraceTime 60
MaxAuthTries 3
MaxSessions 2

# Banner
Banner /etc/issue.net

# Subsystem
Subsystem sftp internal-sftp

# Match block for internal users
Match Group sftp-only
    ChrootDirectory /var/www/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no

# Logging
SyslogFacility AUTH
LogLevel INFO

# Allow specific users
AllowUsers deploy

# Client alive configuration
ClientAliveInterval 300
ClientAliveCountMax 2
```

### 3. Configuración de Usuarios

```bash
# Crear usuario deploy con permisos limitados
useradd -m -s /bin/bash -G sudo,docker deploy

# Configurar sudo para deploy
echo 'deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx' > /etc/sudoers.d/deploy

# Configurar shell seguro para usuarios
chsh -s /bin/bash deploy

# Configurar umask seguro
echo 'umask 027' >> /etc/bash.bashrc
echo 'umask 027' >> /etc/profile

# Configurar expire para passwords
chage -M 90 deploy
```

## Configuración de Red

### 1. Nginx Security Headers

```nginx
# /etc/nginx/sites-available/ai-news-aggregator
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Modern SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self' https:; media-src 'self'; object-src 'none'; child-src 'none'; frame-src 'none'" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/m;
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/m;

    # Hide Nginx version
    server_tokens off;

    # Disable server signature
    server_info off;

    # API proxy with security
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        proxy_set_header X-Forwarded-Port $server_port;
        
        # Security proxy headers
        proxy_set_header X-Content-Type-Options nosniff;
        proxy_set_header X-Frame-Options DENY;
        proxy_set_header X-XSS-Protection "1; mode=block";
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Authentication endpoints with stricter limits
    location /api/auth/ {
        limit_req zone=auth burst=5 nodelay;
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint (no auth required)
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ \.(sql|conf|ini)$ {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Allow only specific HTTP methods
    location ~* ^(?!.*auth).* {
        limit_except GET POST PUT DELETE {
            deny all;
        }
    }

    # Rate limiting per client
    location / {
        limit_req zone=login burst=3 nodelay;
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### 2. DDoS Protection

```bash
# Configurar iptables para DDoS protection
#!/bin/bash

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X
iptables -t mangle -F
iptables -t mangle -X

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Rate limiting for incoming connections
iptables -A INPUT -p tcp --dport 80 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -m limit --limit 25/minute --limit-burst 100 -j ACCEPT
iptables -A INPUT -p tcp --dport 2222 -m limit --limit 3/minute --limit-burst 3 -j ACCEPT

# Block suspicious patterns
iptables -A INPUT -m string --string "USER_AGENTBAD" --algo bm -j DROP
iptables -A INPUT -m string --string "bot" --algo bm -j DROP

# Save rules
iptables-save > /etc/iptables/rules.v4
```

## Seguridad de Aplicación

### 1. Configuración de FastAPI

```python
# backend/app/core/security.py
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import jwt
from datetime import datetime, timedelta
import hashlib
import secrets
from typing import Optional, List
import logging

app = FastAPI(title="AI News Aggregator", version="1.0.0")

# Security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["yourdomain.com", "*.yourdomain.com", "localhost"])

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=86400,
)

# Rate limiting middleware
class RateLimitMiddleware:
    def __init__(self, app, calls: int = 100, period: int = 60):
        self.app = app
        self.calls = calls
        self.period = period
        self.clients = {}

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            client_ip = scope["client"][0]
            now = datetime.now()
            
            if client_ip not in self.clients:
                self.clients[client_ip] = []
            
            # Clean old entries
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if now - timestamp < timedelta(seconds=self.period)
            ]
            
            # Check rate limit
            if len(self.clients[client_ip]) >= self.calls:
                response = {
                    "detail": "Rate limit exceeded",
                    "retry_after": self.period
                }
                await send({
                    "type": "http.response.start",
                    "status": status.HTTP_429_TOO_MANY_REQUESTS,
                    "headers": [[b"content-type", b"application/json"]],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps(response).encode(),
                })
                return
            
            # Record this request
            self.clients[client_ip].append(now)
        
        await self.app(scope, receive, send)

app.add_middleware(RateLimitMiddleware, calls=100, period=60)

# JWT Configuration
class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str):
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

# Dependency for authentication
security = HTTPBearer()
jwt_handler = JWTHandler(secret_key="your-secret-key")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = jwt_handler.verify_token(token)
    return payload
```

### 2. Validación de Entrada

```python
# backend/app/core/validation.py
from pydantic import BaseModel, validator, Field, EmailStr
import re
from typing import Optional, List
from datetime import datetime

class ArticleCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=10, max_length=10000)
    url: str = Field(..., max_length=500)
    source_id: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., regex=r'^[a-zA-Z0-9_-]+$')
    
    @validator('title')
    def validate_title(cls, v):
        # Remove potentially dangerous characters
        v = re.sub(r'[<>"\']', '', v)
        return v.strip()
    
    @validator('content')
    def validate_content(cls, v):
        # Remove potentially dangerous HTML
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'on\w+\s*=',
            r'<iframe[^>]*>.*?</iframe>'
        ]
        
        for pattern in dangerous_patterns:
            v = re.sub(pattern, '', v, flags=re.IGNORECASE | re.DOTALL)
        
        return v
    
    @validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        
        # Additional URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        
        return v

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=100)
    
    @validator('password')
    def validate_password(cls, v):
        # Check for strong password requirements
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('full_name')
    def validate_full_name(cls, v):
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r'^[a-zA-Z\s\'\-]+$', v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        return v.strip()

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = Field(None, regex=r'^[a-zA-Z0-9_-]+$')
    limit: int = Field(50, ge=1, le=100)
    
    @validator('query')
    def validate_query(cls, v):
        # Sanitize search query
        v = re.sub(r'[^\w\s\-]', '', v)
        return v.strip()
```

### 3. Content Security Policy

```python
# backend/app/core/csp.py
from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List, Dict
import re

class CSPMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, csp_config: Dict[str, str] = None):
        super().__init__(app)
        self.csp_config = csp_config or {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'",
            'img-src': "'self' data: https:",
            'font-src': "'self' data:",
            'connect-src': "'self' https:",
            'frame-ancestors': "'none'",
            'object-src': "'none'",
            'base-uri': "'self'",
            'form-action': "'self'"
        }
    
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        
        # Build CSP header
        csp_header = '; '.join([f"{k} {v}" for k, v in self.csp_config.items()])
        response.headers['Content-Security-Policy'] = csp_header
        
        return response

# Add CSP to FastAPI app
# app.add_middleware(CSPMiddleware)
```

## Seguridad de Base de Datos

### 1. PostgreSQL Hardening

```sql
-- postgresql-hardening.sql

-- Disable superuser login except for maintenance
ALTER USER postgres WITH PASSWORD 'very_secure_password_here';

-- Create application user with limited privileges
CREATE USER ai_news_app WITH PASSWORD 'app_specific_password';
GRANT CONNECT ON DATABASE ai_news_aggregator TO ai_news_app;
GRANT USAGE ON SCHEMA public TO ai_news_app;

-- Grant only necessary privileges
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ai_news_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ai_news_app;

-- Revoke unnecessary privileges
REVOKE ALL ON DATABASE ai_news_aggregator FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM PUBLIC;

-- Configure PostgreSQL settings
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'mod';
ALTER SYSTEM SET log_checkpoints = on;
ALTER SYSTEM SET log_connections = on;
ALTER SYSTEM SET log_disconnections = on;
ALTER SYSTEM SET log_lock_waits = on;
ALTER SYSTEM SET log_temp_files = 0;
ALTER SYSTEM SET log_autovacuum_min_duration = 0;
ALTER SYSTEM SET log_error_verbosity = default;
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';
ALTER SYSTEM SET log_truncate_on_rotation = on;
ALTER SYSTEM SET log_rotation_age = 1d;
ALTER SYSTEM SET log_rotation_size = 100MB;

-- Security settings
ALTER SYSTEM SET ssl = on;
ALTER SYSTEM SET ssl_cert_file = 'server.crt';
ALTER SYSTEM SET ssl_key_file = 'server.key';
ALTER SYSTEM SET ssl_ca_file = 'root.crt';
ALTER SYSTEM SET password_encryption = 'scram-sha-256';

-- Row level security
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY article_read_policy ON articles
    FOR SELECT USING (true);

CREATE POLICY user_own_data_policy ON users
    FOR ALL USING (auth.uid() = id);

-- Function to check if user can access article
CREATE OR REPLACE FUNCTION can_access_article(article_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- Public articles are accessible to all
    IF EXISTS (
        SELECT 1 FROM articles 
        WHERE id = article_id AND is_public = true
    ) THEN
        RETURN true;
    END IF;
    
    -- Private articles only for authenticated users
    IF auth.uid() IS NOT NULL THEN
        RETURN true;
    END IF;
    
    RETURN false;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Apply RLS policies
CREATE POLICY article_access_policy ON articles
    FOR SELECT USING (can_access_article(id));

SELECT pg_reload_conf();
```

### 2. Redis Security

```bash
# redis-security.conf

# Authentication
requirepass your_redis_password

# Bind to internal network only
bind 127.0.0.1 10.116.0.0/16

# Disable dangerous commands
rename-command FLUSHDB ""
rename-command FLUSHALL ""
rename-command CONFIG "CONFIG_bc7d9e2f"
rename-command SHUTDOWN "SHUTDOWN_a8f3c9d1"
rename-command DEBUG "DEBUG_f4e8b2a6"

# Enable AOF persistence
appendonly yes
appendfsync everysec

# Max memory and eviction policy
maxmemory 1gb
maxmemory-policy allkeys-lru

# Timeout for connections
timeout 300

# TCP keepalive
tcp-keepalive 60

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Save configuration
save 900 1
save 300 10
save 60 10000
```

## Seguridad de Docker

### 1. Dockerfile Seguro

```dockerfile
# backend/Dockerfile.secure
FROM python:3.11-slim as builder

# Install security updates
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Set up virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install security updates and minimal dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get autoremove -y && \
        apt-get clean

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Set file permissions
RUN chmod +x start.sh && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run application
CMD ["./start.sh"]
```

### 2. Docker Compose Seguro

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.secure
    container_name: ai-news-backend
    restart: unless-stopped
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    env_file:
      - .env
    volumes:
      - app_logs:/app/logs
      - ./config:/app/config:ro
    networks:
      - app_network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - DAC_OVERRIDE
      - FOWNER
      - SETGID
      - SETUID
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.secure
    container_name: ai-news-frontend
    restart: unless-stopped
    networks:
      - app_network
    security_opt:
      - no-new-privileges:true
    read_only: true
    volumes:
      - frontend_assets:/app/dist

  redis:
    image: redis:7-alpine
    container_name: ai-news-redis
    restart: unless-stopped
    command: redis-server /etc/redis/redis.conf
    volumes:
      - ./config/redis.conf:/etc/redis/redis.conf:ro
      - redis_data:/data
    networks:
      - app_network
    security_opt:
      - no-new-privileges:true
    user: redis:redis
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m

  nginx:
    image: nginx:1.24-alpine
    container_name: ai-news-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./config/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./config/nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - frontend_assets:/usr/share/nginx/html:ro
    networks:
      - app_network
    security_opt:
      - no-new-privileges:true
    user: nginx:nginx
    read_only: true
    tmpfs:
      - /var/cache/nginx:noexec,nosuid,size=100m
      - /var/log/nginx:noexec,nosuid,size=100m
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID

volumes:
  app_logs:
    driver: local
  frontend_assets:
    driver: local
  redis_data:
    driver: local

networks:
  app_network:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "true"
      com.docker.network.bridge.enable_ip_masquerade: "true"
      com.docker.network.driver.mtu: "1500"
```

## Gestión de Secretos

### 1. Vault Setup

```bash
# Instalar HashiCorp Vault
curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -
sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"
sudo apt-get update && sudo apt-get install vault

# Configurar Vault
sudo mkdir -p /etc/vault
sudo cat > /etc/vault/config.hcl << 'EOF'
storage "file" {
  path = "/var/lib/vault/data"
}

listener "tcp" {
  address     = "127.0.0.1:8200"
  tls_cert_file = "/etc/vault/tls/server.crt"
  tls_key_file  = "/etc/vault/tls/server.key"
}

ui = true
api_addr = "http://127.0.0.1:8200"
cluster_addr = "https://127.0.0.1:8201"
EOF

# Generar TLS certificates
sudo mkdir -p /etc/vault/tls
openssl req -new -x509 -nodes -newkey rsa:4096 -keyout /etc/vault/tls/server.key -out /etc/vault/tls/server.crt -days 365 -subj "/C=US/ST=CA/L=San Francisco/O=Your Company/OU=Your Department/CN=vault.yourdomain.com"

# Configurar systemd
sudo cat > /etc/systemd/system/vault.service << 'EOF'
[Unit]
Description=HashiCorp Vault
Documentation=https://www.vaultproject.io/docs/
After=network.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/vault server -config=/etc/vault/config.hcl
ExecReload=/bin/kill -HUP $MAINPID
KillSignal=SIGTERM
User=vault
Group=vault
Restart=on-failure
RestartSec=5
TimeoutStopSec=30
StartLimitInterval=60
StartLimitBurst=3
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable vault
sudo systemctl start vault
```

### 2. Secret Management Script

```python
# backend/app/core/secrets.py
import hvac
import os
from typing import Dict, Any, Optional

class VaultClient:
    def __init__(self, url: str, token: str, mount_point: str = "ai-news"):
        self.client = hvac.Client(url=url, token=token)
        self.mount_point = mount_point
        self._ensure_authenticated()

    def _ensure_authenticated(self):
        """Ensure client is authenticated"""
        if not self.client.is_authenticated():
            raise Exception("Vault authentication failed")

    def get_secret(self, path: str) -> Dict[str, Any]:
        """Retrieve secret from Vault"""
        full_path = f"{self.mount_point}/{path}"
        try:
            response = self.client.secrets.kv.v2.read_secret_version(path=path, mount_point=self.mount_point)
            return response['data']['data']
        except Exception as e:
            # Fallback to environment variables for local development
            return self._fallback_to_env(path)

    def set_secret(self, path: str, secret: Dict[str, Any]) -> bool:
        """Store secret in Vault"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=secret,
                mount_point=self.mount_point
            )
            return True
        except Exception as e:
            print(f"Failed to store secret: {e}")
            return False

    def _fallback_to_env(self, path: str) -> Dict[str, Any]:
        """Fallback to environment variables"""
        secrets = {}
        for key, value in os.environ.items():
            if key.startswith(f"{path.upper()}_"):
                clean_key = key.lower().replace(f"{path.upper()}_", "")
                secrets[clean_key] = value
        return secrets

class SecretsManager:
    def __init__(self):
        vault_url = os.getenv('VAULT_URL', 'http://127.0.0.1:8200')
        vault_token = os.getenv('VAULT_TOKEN')
        
        if vault_token:
            self.vault = VaultClient(vault_url, vault_token)
        else:
            self.vault = None
            print("Warning: Vault not configured, using environment variables")

    def get_database_config(self) -> Dict[str, str]:
        """Get database configuration"""
        if self.vault:
            return self.vault.get_secret('database')
        else:
            return {
                'url': os.getenv('DATABASE_URL', ''),
                'host': os.getenv('POSTGRES_HOST', ''),
                'port': os.getenv('POSTGRES_PORT', '5432'),
                'name': os.getenv('POSTGRES_DB', ''),
                'user': os.getenv('POSTGRES_USER', ''),
                'password': os.getenv('POSTGRES_PASSWORD', '')
            }

    def get_redis_config(self) -> Dict[str, str]:
        """Get Redis configuration"""
        if self.vault:
            return self.vault.get_secret('redis')
        else:
            return {
                'url': os.getenv('REDIS_URL', ''),
                'host': os.getenv('REDIS_HOST', ''),
                'port': os.getenv('REDIS_PORT', '6379'),
                'password': os.getenv('REDIS_PASSWORD', '')
            }

    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys"""
        if self.vault:
            return self.vault.get_secret('api-keys')
        else:
            return {
                'newsapi': os.getenv('NEWSAPI_KEY', ''),
                'nytimes': os.getenv('NYTIMES_API_KEY', ''),
                'guardian': os.getenv('GUARDIAN_API_KEY', ''),
                'openai': os.getenv('OPENAI_API_KEY', ''),
                'jwt': os.getenv('JWT_SECRET_KEY', ''),
                'secret_key': os.getenv('SECRET_KEY', '')
            }

# Usage
secrets_manager = SecretsManager()
```

## Seguridad de Certificados

### 1. Certificate Management

```bash
#!/bin/bash
# manage-certificates.sh

DOMAIN="yourdomain.com"
EMAIL="admin@yourdomain.com"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

# Install certbot
apt install -y certbot python3-certbot-nginx

# Generate certificate
certbot --nginx \
    --non-interactive \
    --agree-tos \
    --email "${EMAIL}" \
    --domains "${DOMAIN},www.${DOMAIN},api.${DOMAIN}" \
    --expand

# Setup auto-renewal
crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet && /bin/systemctl reload nginx"; } | crontab -

# Test renewal
certbot renew --dry-run

# Backup certificates
tar -czf "/root/certs-backup-$(date +%Y%m%d).tar.gz" "${CERT_DIR}"

# Check certificate expiry
if [ -f "${CERT_DIR}/cert.pem" ]; then
    expiry=$(openssl x509 -enddate -noout -in "${CERT_DIR}/cert.pem" | cut -d= -f2)
    expiry_timestamp=$(date -d "$expiry" +%s)
    current_timestamp=$(date +%s)
    days_until_expiry=$(( (expiry_timestamp - current_timestamp) / 86400 ))
    
    if [ "$days_until_expiry" -lt 30 ]; then
        echo "Warning: Certificate expires in $days_until_expiry days"
        # Send alert
    fi
fi
```

### 2. SSL/TLS Configuration

```nginx
# Strong SSL configuration
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_prefer_server_ciphers off;

# Session settings
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;

# OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Certificate transparency
add_header Expect-CT "max-age=86400, enforce";
```

## Monitoreo de Seguridad

### 1. Security Monitoring Script

```bash
#!/bin/bash
# security-monitor.sh

LOG_FILE="/var/log/security-monitor.log"
ALERT_EMAIL="security@yourdomain.com"

log_security_event() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

send_security_alert() {
    local subject="$1"
    local message="$2"
    
    # Log the event
    log_security_event "ALERT: $subject - $message"
    
    # Send email alert
    echo "$message" | mail -s "Security Alert: $subject" "$ALERT_EMAIL"
    
    # Optional: Send to Slack
    # curl -X POST -H 'Content-type: application/json' \
    #     --data '{"text":"Security Alert: '$subject' - '$message'"}' \
    #     YOUR_SLACK_WEBHOOK_URL
}

# Check for failed SSH login attempts
check_ssh_failures() {
    local failed_attempts=$(grep "Failed password" /var/log/auth.log | tail -10 | wc -l)
    
    if [ "$failed_attempts" -gt 5 ]; then
        send_security_alert "High SSH Failure Rate" "Detected $failed_attempts failed SSH login attempts in the last 10 entries"
    fi
}

# Check for suspicious processes
check_suspicious_processes() {
    # Look for processes running from unusual locations
    local suspicious=$(ps aux | grep -E '/tmp|/dev/shm|/var/tmp' | grep -v -E '(systemd|kthreadd|rcu_)')
    
    if [ -n "$suspicious" ]; then
        send_security_alert "Suspicious Processes" "Processes running from temporary directories:\n$suspicious"
    fi
}

# Check for modified system files
check_file_integrity() {
    local monitored_files=(
        "/etc/passwd"
        "/etc/shadow"
        "/etc/ssh/sshd_config"
        "/etc/sudoers"
    )
    
    for file in "${monitored_files[@]}"; do
        if [ -f "$file" ]; then
            local current_hash=$(md5sum "$file" | cut -d' ' -f1)
            local stored_hash_file="/var/lib/aide/$file.hash"
            
            if [ -f "$stored_hash_file" ]; then
                local stored_hash=$(cat "$stored_hash_file")
                
                if [ "$current_hash" != "$stored_hash" ]; then
                    send_security_alert "File Modified" "File $file has been modified. Current hash: $current_hash, Stored hash: $stored_hash"
                fi
            fi
        fi
    done
}

# Check disk space (DoS prevention)
check_disk_space() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$usage" -gt 90 ]; then
        send_security_alert "High Disk Usage" "Disk usage is at ${usage}%, which may indicate a DoS attack"
    fi
}

# Check for unusual network connections
check_network_connections() {
    local unusual_connections=$(netstat -tuln | grep -E ':[0-9]{5}')
    
    if [ -n "$unusual_connections" ]; then
        send_security_alert "Unusual Network Connections" "Unexpected listening ports:\n$unusual_connections"
    fi
}

# Check fail2ban status
check_fail2ban_status() {
    if ! systemctl is-active --quiet fail2ban; then
        send_security_alert "Fail2Ban Stopped" "Fail2Ban service is not running"
        systemctl restart fail2ban
    fi
}

# Main execution
main() {
    log_security_event "Starting security monitoring check"
    
    check_ssh_failures
    check_suspicious_processes
    check_file_integrity
    check_disk_space
    check_network_connections
    check_fail2ban_status
    
    log_security_event "Security monitoring check completed"
}

# Run main function
main

# Run every 5 minutes via cron
# */5 * * * * /path/to/security-monitor.sh
```

### 2. Log Analysis

```bash
#!/bin/bash
# security-log-analyzer.sh

LOG_DIR="/var/log"
ANALYSIS_LOG="/var/log/security-analysis.log"

analyze_nginx_logs() {
    local error_log="/var/log/nginx/error.log"
    local access_log="/var/log/nginx/access.log"
    
    # SQL injection attempts
    local sql_injection=$(grep -i "union\|select\|insert\|drop\|delete\|update" "$access_log" | wc -l)
    if [ "$sql_injection" -gt 0 ]; then
        echo "$(date) - Potential SQL injection attempts: $sql_injection" >> "$ANALYSIS_LOG"
    fi
    
    # XSS attempts
    local xss_attempts=$(grep -i "<script\|javascript:\|onerror=" "$access_log" | wc -l)
    if [ "$xss_attempts" -gt 0 ]; then
        echo "$(date) - XSS attempts detected: $xss_attempts" >> "$ANALYSIS_LOG"
    fi
    
    # 404 rate analysis
    local four_oh_four=$(grep " 404 " "$access_log" | wc -l)
    if [ "$four_oh_four" -gt 100 ]; then
        echo "$(date) - High 404 rate: $four_oh_four requests" >> "$ANALYSIS_LOG"
    fi
}

analyze_application_logs() {
    local app_log="/var/www/ai-news-aggregator/logs/app.log"
    
    if [ -f "$app_log" ]; then
        # Security-related errors
        local auth_failures=$(grep -i "authentication failed\|unauthorized\|invalid token" "$app_log" | wc -l)
        if [ "$auth_failures" -gt 10 ]; then
            echo "$(date) - Authentication failures: $auth_failures" >> "$ANALYSIS_LOG"
        fi
        
        # Rate limit violations
        local rate_limits=$(grep -i "rate limit" "$app_log" | wc -l)
        if [ "$rate_limits" -gt 50 ]; then
            echo "$(date) - Rate limit violations: $rate_limits" >> "$ANALYSIS_LOG"
        fi
    fi
}

analyze_system_logs() {
    # Kernel security messages
    local kernel_security=$(grep -i "security\|denied\|refused" /var/log/kern.log | wc -l)
    if [ "$kernel_security" -gt 20 ]; then
        echo "$(date) - Kernel security messages: $kernel_security" >> "$ANALYSIS_LOG"
    fi
}

# Execute analysis
analyze_nginx_logs
analyze_application_logs
analyze_system_logs

# Clean old logs
find "$LOG_DIR" -name "*.log" -mtime +30 -delete 2>/dev/null
```

## Backup Seguro

### 1. Encrypted Backup Script

```bash
#!/bin/bash
# secure-backup.sh

BACKUP_DIR="/backup/secure"
GPG_RECIPIENT="backup@yourdomain.com"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL with encryption
pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" | \
gzip | \
gpg --trust-model always --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
    --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric --output "$BACKUP_DIR/db_backup_${DATE}.sql.gz.gpg"

# Backup application files with encryption
tar -czf - /var/www/ai-news-aggregator | \
gpg --trust-model always --cipher-algo AES256 --compress-algo 1 \
    --s2k-mode 3 --s2k-digest-algo SHA512 --s2k-count 65536 --symmetric \
    --output "$BACKUP_DIR/app_backup_${DATE}.tar.gz.gpg"

# Backup Nginx configuration
tar -czf - /etc/nginx | \
gpg --trust-model always --cipher-algo AES256 \
    --output "$BACKUP_DIR/nginx_backup_${DATE}.tar.gz.gpg"

# Backup SSL certificates
tar -czf - /etc/letsencrypt | \
gpg --trust-model always --cipher-algo AES256 \
    --output "$BACKUP_DIR/ssl_backup_${DATE}.tar.gz.gpg"

# Verify backups
for file in "$BACKUP_DIR"/*_${DATE}.*; do
    if [ -f "$file" ]; then
        if gpg --list-packets "$file" >/dev/null 2>&1; then
            echo "$(date) - Backup verified: $(basename "$file")" >> /var/log/backup.log
        else
            echo "$(date) - Backup verification failed: $(basename "$file")" >> /var/log/backup.log
            exit 1
        fi
    fi
done

# Upload to remote storage (AWS S3 example)
aws s3 cp "$BACKUP_DIR" s3://your-backup-bucket/ai-news-$(date +%Y-%m-%d)/ \
    --recursive --storage-class STANDARD_IA

# Clean local backups older than 7 days
find "$BACKUP_DIR" -name "*.gpg" -mtime +7 -delete

echo "$(date) - Secure backup completed successfully"
```

## Compliance

### 1. GDPR Compliance Checklist

```markdown
# GDPR Compliance Checklist for AI News Aggregator

## Data Collection and Processing
- [ ] Document all data processing activities
- [ ] Implement data minimization principles
- [ ] Define lawful basis for processing (Article 6)
- [ ] Obtain explicit consent for non-essential data
- [ ] Document legitimate interests assessment

## Individual Rights (Articles 15-22)
- [ ] Right to information (transparency)
- [ ] Right of access (data portability)
- [ ] Right to rectification
- [ ] Right to erasure ("right to be forgotten")
- [ ] Right to restriction of processing
- [ ] Right to object
- [ ] Right to data portability
- [ ] Rights related to automated decision making

## Technical and Organizational Measures
- [ ] Implement data protection by design and by default
- [ ] Encryption of personal data at rest and in transit
- [ ] Pseudonymization where appropriate
- [ ] Access controls and authentication
- [ ] Regular security assessments
- [ ] Data breach notification procedures
- [ ] Data retention and deletion policies

## Documentation and Governance
- [ ] Data protection impact assessment (DPIA)
- [ ] Data protection officer (DPO) designation
- [ ] Record of processing activities
- [ ] Privacy policy and terms of service
- [ ] Cookie consent management
- [ ] Data transfer agreements

## International Transfers
- [ ] Adequacy decisions compliance
- [ ] Standard contractual clauses (SCCs)
- [ ] Binding corporate rules (BCRs)
- [ ] Certification mechanisms
- [ ] Codes of conduct
```

### 2. OWASP Top 10 Checklist

```markdown
# OWASP Top 10 2021 Security Checklist

## A01 - Broken Access Control
- [ ] Implement proper authentication and session management
- [ ] Enforce access control on every request
- [ ] Use principle of least privilege
- [ ] Disable default accounts and unnecessary functions
- [ ] Implement proper error handling for access control

## A02 - Cryptographic Failures
- [ ] Ensure encryption in transit (HTTPS/TLS)
- [ ] Encrypt sensitive data at rest
- [ ] Use strong cryptographic algorithms
- [ ] Implement proper key management
- [ ] Disable insecure cryptographic protocols

## A03 - Injection
- [ ] Use parameterized queries
- [ ] Input validation and sanitization
- [ ] Use ORM with parameterized queries
- [ ] Implement proper output encoding
- [ ] Limit query length and complexity

## A04 - Insecure Design
- [ ] Threat modeling
- [ ] Secure design patterns
- [ ] Security by design principles
- [ ] Regular security testing
- [ ] Secure defaults

## A05 - Security Misconfiguration
- [ ] Disable unused features
- [ ] Remove default accounts and passwords
- [ ] Keep software updated
- [ ] Disable directory listing
- [ ] Remove unnecessary HTTP methods

## A06 - Vulnerable and Outdated Components
- [ ] Inventory all components
- [ ] Monitor for vulnerabilities
- [ ] Implement security patches promptly
- [ ] Use dependency scanning tools
- [ ] Remove unused dependencies

## A07 - Identification and Authentication Failures
- [ ] Implement multi-factor authentication
- [ ] Use strong password policies
- [ ] Implement account lockout mechanisms
- [ ] Use secure session management
- [ ] Implement proper session timeout

## A08 - Software and Data Integrity Failures
- [ ] Implement integrity checks
- [ ] Use secure CI/CD pipelines
- [ ] Verify software integrity
- [ ] Implement code signing
- [ ] Use secure update mechanisms

## A09 - Security Logging and Monitoring Failures
- [ ] Implement comprehensive logging
- [ ] Monitor for security events
- [ ] Implement alerting mechanisms
- [ ] Secure log storage and transmission
- [ ] Implement log retention policies

## A10 - Server-Side Request Forgery (SSRF)
- [ ] Implement URL validation
- [ ] Use allowlist for outbound requests
- [ ] Disable unnecessary protocols
- [ ] Implement network segmentation
- [ ] Use DNS resolution restrictions
```

## Comandos de Verificación

```bash
# Verificar configuración de seguridad
security-audit.sh

# Verificar certificados SSL
ssl-check.sh yourdomain.com

# Verificar headers de seguridad
curl -I https://yourdomain.com

# Verificar configuraciones de firewall
ufw status verbose
iptables -L -n

# Verificar servicios ejecutándose
systemctl list-units --type=service --state=running

# Verificar archivos con permisos incorrectos
find /var/www -type f -perm 777 -o -perm 666

# Verificar logs de seguridad
tail -f /var/log/auth.log
tail -f /var/log/fail2ban.log

# Verificar integridad de archivos
aide --check

# Verificar SSL/TLS configuration
sslscan yourdomain.com
```

---

**Nota**: Esta lista de verificación debe ser ejecutada regularmente y actualizada según las mejores prácticas de seguridad actuales.