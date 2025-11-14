# Guía de Deployment - AI News Aggregator

## Tabla de Contenidos
- [Prerequisites](#prerequisites)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Configuración de Entorno](#configuración-de-entorno)
- [Deployment por Fases](#deployment-por-fases)
- [Verificación Post-Deployment](#verificación-post-deployment)
- [Rollback](#rollback)
- [Monitoreo](#monitoreo)

## Prerequisites

### Herramientas Requeridas
```bash
# Instalar herramientas básicas
curl -fsSL https://get.docker.com/ | sh
sudo apt-get update
sudo apt-get install -y git make docker-compose nginx certbot python3-certbot-nginx

# Verificar instalación
docker --version
docker-compose --version
nginx -v
```

### Cuentas y Servicios
- [ ] DigitalOcean Account (Droplets, Managed Databases, Load Balancers)
- [ ] Cloudflare (DNS y SSL)
- [ ] SendGrid (Email notifications)
- [ ] New York Times API Key
- [ ] Guardian API Key
- [ ] NewsAPI Key

## Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx         │    │   Frontend      │    │   Load Balancer │
│   (Reverse      │    │   (React/Vite)  │    │   (DigitalOcean)│
│    Proxy)       │    │                 │    │                 │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          │              ┌───────┴───────┐              │
          └──────────────┤ API Gateway    ├──────────────┘
                         │ (Nginx)        │
                         └───────┬───────┘
                                 │
          ┌──────────────────────┼──────────────────────┐
          │                      │                      │
┌─────────▼───────┐    ┌─────────▼───────┐    ┌─────────▼───────┐
│   Backend       │    │   Redis         │    │   Celery        │
│   (FastAPI)     │    │   (Cache)       │    │   (Tasks)       │
│   Port: 8000    │    │   Port: 6379    │    │   Port: 5555    │
└─────────┬───────┘    └─────────┬───────┘    └─────────┬───────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 │
                     ┌───────────▼───────────┐
                     │   PostgreSQL          │
                     │   (Managed Database)  │
                     │   Port: 5432          │
                     └───────────────────────┘
```

## Configuración de Entorno

### 1. Variables de Entorno

Crear archivo `.env` en la raíz del proyecto:

```bash
# ==============================================
# AI NEWS AGGREGATOR - PRODUCTION ENVIRONMENT
# ==============================================

# Application Settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
SECRET_KEY=your-super-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://username:password@host:5432/database
POSTGRES_DB=ai_news_aggregator
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=your_db_host
POSTGRES_PORT=5432

# Redis Configuration
REDIS_URL=redis://username:password@host:6379
REDIS_HOST=your_redis_host
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password

# API Keys
NEWSAPI_KEY=your_newsapi_key
NYTIMES_API_KEY=your_nytimes_api_key
GUARDIAN_API_KEY=your_guardian_api_key

# AI Configuration
OPENAI_API_KEY=your_openai_api_key
AI_MODEL=gpt-3.5-turbo
AI_MAX_TOKENS=1000
AI_TEMPERATURE=0.7

# Email Configuration
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
EMAIL_FROM=noreply@yourdomain.com

# Security Settings
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
CORS_ORIGINS=https://yourdomain.com
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000

# Performance Settings
WORKERS=4
MAX_CONNECTIONS=100
TIMEOUT=30

# Monitoring
SENTRY_DSN=your_sentry_dsn
PROMETHEUS_ENABLED=true
GRAFANA_ADMIN_PASSWORD=your_grafana_password

# Backup Configuration
BACKUP_S3_BUCKET=your-backup-bucket
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
```

### 2. Configuración de Nginx

Crear `/etc/nginx/sites-available/ai-news-aggregator`:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

    # Frontend (React App)
    location / {
        root /var/www/ai-news-aggregator/frontend;
        try_files $uri $uri/ /index.html;
        
        # Cache static assets
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API Routes
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Auth endpoints with stricter limits
    location /api/auth/ {
        limit_req zone=auth burst=5 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Celery Flower monitoring
    location /flower/ {
        proxy_pass http://localhost:5555;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Basic Auth for Flower
        auth_basic "Celery Monitor";
        auth_basic_user_file /etc/nginx/.htpasswd;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }

    # Security
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ ~$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

## Deployment por Fases

### Fase 1: Preparación del Servidor

```bash
# 1. Conectar al servidor
ssh root@your-server-ip

# 2. Actualizar sistema
apt update && apt upgrade -y

# 3. Crear usuario no-root
adduser deploy
usermod -aG sudo deploy
usermod -aG docker deploy

# 4. Configurar firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow 443
ufw enable

# 5. Instalar Docker
curl -fsSL https://get.docker.com/ | sh
systemctl enable docker
usermod -aG docker deploy

# 6. Configurar SSH keys (recomendado)
mkdir -p /home/deploy/.ssh
cp your-public-key.pub /home/deploy/.ssh/authorized_keys
chmod 700 /home/deploy/.ssh
chmod 600 /home/deploy/.ssh/authorized_keys
chown -R deploy:deploy /home/deploy/.ssh

# 7. Deshabilitar password authentication
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl reload sshd
```

### Fase 2: Configuración de Infraestructura

```bash
# 1. Crear directorios del proyecto
sudo mkdir -p /var/www/ai-news-aggregator
sudo chown deploy:deploy /var/www/ai-news-aggregator
cd /var/www/ai-news-aggregator

# 2. Clonar repositorio
git clone https://github.com/yourusername/ai-news-aggregator.git .
git checkout production

# 3. Configurar variables de entorno
cp .env.example .env
nano .env  # Editar con valores reales

# 4. Configurar permisos
chmod +x start.sh
chmod +x backend/start_celery.sh
```

### Fase 3: Build y Deploy

```bash
# 1. Build de imágenes Docker
make build

# 2. Ejecutar migraciones de base de datos
make migrate

# 3. Iniciar servicios
make up

# 4. Verificar estado de contenedores
make ps

# 5. Ejecutar health checks
make health-check
```

### Fase 4: SSL y Dominio

```bash
# 1. Instalar certbot
apt install -y certbot python3-certbot-nginx

# 2. Obtener certificado SSL
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 3. Configurar renovación automática
crontab -e
# Agregar: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Verificación Post-Deployment

### Health Checks Automáticos

```bash
#!/bin/bash
# health-check.sh

echo "🔍 Verificando servicios..."

# 1. Verificar contenedores
if docker-compose ps | grep -q "Up"; then
    echo "✅ Contenedores ejecutándose"
else
    echo "❌ Error en contenedores"
    exit 1
fi

# 2. Verificar conectividad a base de datos
if docker exec ai-news-aggregator-backend python -c "import psycopg2; psycopg2.connect('$DATABASE_URL').close()"; then
    echo "✅ Base de datos conectada"
else
    echo "❌ Error conectando a base de datos"
    exit 1
fi

# 3. Verificar API endpoints
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ API respondiendo"
else
    echo "❌ API no responde"
    exit 1
fi

# 4. Verificar Redis
if docker exec ai-news-aggregator-redis redis-cli ping | grep -q PONG; then
    echo "✅ Redis conectado"
else
    echo "❌ Error conectando a Redis"
    exit 1
fi

# 5. Verificar Celery
if docker exec ai-news-aggregator-backend python -c "from celery_app import app; print(app.control.inspect().active())" > /dev/null 2>&1; then
    echo "✅ Celery ejecutándose"
else
    echo "❌ Error con Celery"
    exit 1
fi

echo "✅ Todos los servicios están funcionando correctamente"
```

### Tests Post-Deployment

```bash
# 1. Ejecutar tests de integración
make test-integration

# 2. Verificar performance
make test-performance

# 3. Verificar cobertura de código
make test-coverage

# 4. Verificar funcionalidades clave
./verify_testing_setup.sh
```

## Rollback

### Rollback Automático

```bash
#!/bin/bash
# rollback.sh

echo "🔄 Iniciando rollback..."

# 1. Hacer backup del estado actual
make backup

# 2. Parar servicios actuales
make down

# 3. Revertir a versión anterior
git checkout previous-stable-tag

# 4. Rebuild con versión anterior
make build
make migrate
make up

# 5. Verificar rollback
./health-check.sh

echo "✅ Rollback completado"
```

### Rollback Manual

```bash
# 1. Identificar problemas
make logs

# 2. Revertir cambios
git revert HEAD

# 3. Rebuild y redesplegar
make build-prod
make down
make up-prod

# 4. Verificar restauración
make health-check
```

## Monitoreo

### Métricas Clave a Monitorear

1. **Performance**
   - Response time (p95 < 500ms)
   - Throughput (requests/second)
   - Error rate (< 1%)

2. **Infraestructura**
   - CPU usage (< 80%)
   - Memory usage (< 85%)
   - Disk usage (< 90%)
   - Network I/O

3. **Base de Datos**
   - Connection pool usage
   - Query execution time
   - Index efficiency
   - Replication lag

4. **Cache (Redis)**
   - Hit rate (> 90%)
   - Memory usage
   - Eviction rate
   - Connection count

### Configuración de Alertas

```yaml
# alerts.yml
groups:
- name: ai-news-aggregator
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.01
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
      description: "Error rate is {{ $value }} for {{ $labels.instance }}"

  - alert: DatabaseConnectionPoolExhausted
    expr: database_connections_active / database_connections_max > 0.9
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: Database connection pool near exhaustion
```

### Logs Estructurados

```python
# Ejemplo de logging estructurado
import structlog

logger = structlog.get_logger()

# En el código
logger.info(
    "API request processed",
    endpoint="/api/news",
    method="GET",
    status_code=200,
    response_time_ms=45.2,
    user_id=user.id if user else None
)
```

## Comandos Útiles

```bash
# Gestión de servicios
make up              # Iniciar todos los servicios
make down            # Parar todos los servicios
make restart         # Reiniciar servicios
make logs            # Ver logs en tiempo real
make logs-backend    # Ver logs del backend
make logs-frontend   # Ver logs del frontend
make logs-celery     # Ver logs de Celery

# Base de datos
make migrate         # Ejecutar migraciones
make migrate-rollback # Revertir migraciones
make db-backup       # Backup de BD
make db-restore      # Restaurar BD

# Performance
make benchmark       # Ejecutar benchmarks
make profile         # Profiling de aplicación
make optimize        # Optimizar BD

# Testing
make test            # Ejecutar todos los tests
make test-unit       # Tests unitarios
make test-integration # Tests de integración
make test-e2e        # Tests end-to-end

# Monitoreo
make metrics         # Ver métricas
make health          # Health check
make status          # Estado general del sistema
```

## Troubleshooting

Si encuentras problemas durante el deployment:

1. **Revisar logs**: `make logs`
2. **Verificar configuración**: `make config-check`
3. **Validar base de datos**: `make db-check`
4. **Verificar conectividad**: `make network-check`
5. **Consultar troubleshooting**: Ver [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)

## Próximos Pasos

Una vez completado el deployment:

1. Configurar monitoreo avanzado (ver [MONITORING_SETUP.md](./MONITORING_SETUP.md))
2. Implementar security hardening (ver [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md))
3. Configurar backups automatizados (ver [BACKUP_RECOVERY.md](./BACKUP_RECOVERY.md))
4. Optimizar performance (ver [PERFORMANCE_TUNING.md](./PERFORMANCE_TUNING.md))

---

**Nota**: Esta guía asume un ambiente de producción en DigitalOcean. Para otros proveedores de cloud, ajustar las instrucciones según corresponda.