# Configuración de Infraestructura - DigitalOcean

## Tabla de Contenidos
- [Arquitectura en DigitalOcean](#arquitectura-en-digitalocean)
- [Droplets Configuration](#droplets-configuration)
- [Managed Database Setup](#managed-database-setup)
- [Load Balancer Configuration](#load-balancer-configuration)
- [Networking y DNS](#networking-y-dns)
- [Storage y Backup](#storage-y-backup)
- [Security Groups](#security-groups)
- [Monitoring Setup](#monitoring-setup)
- [Cost Estimation](#cost-estimation)

## Arquitectura en DigitalOcean

```
┌─────────────────────────────────────────────────────────────────┐
│                          DigitalOcean Cloud                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Load         │    │   Web        │    │   Worker     │     │
│  │ Balancer     │    │   Server     │    │   Server     │     │
│  │ (Droplet)    │    │   (Droplet)  │    │   (Droplet)  │     │
│  │ 4GB RAM      │    │   8GB RAM    │    │   4GB RAM    │     │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘     │
│         │                   │                   │               │
│         └───────────────────┼───────────────────┘               │
│                             │                                   │
│                    ┌────────▼────────┐                          │
│                    │   Managed DB    │                          │
│                    │   PostgreSQL    │                          │
│                    │   4GB RAM       │                          │
│                    └─────────────────┘                          │
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐                          │
│  │   Redis      │    │   Monitoring │                          │
│  │   Cluster    │    │   (Droplet)  │                          │
│  │   (2GB)      │    │   2GB RAM    │                          │
│  └──────────────┘    └──────────────┘                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Cloudflare    │
                    │   (DNS + SSL)   │
                    └─────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Internet      │
                    └─────────────────┘
```

## Droplets Configuration

### 1. Load Balancer Droplet

**Especificaciones:**
```yaml
Name: ai-news-lb
Region: San Francisco 3 (SF03)
Size: Basic - 2 CPU, 4GB RAM, 80GB SSD
Image: Ubuntu 22.04 LTS x64
SSH Keys: [your-ssh-key]
Private Networking: Enabled
Monitoring: Enabled
User Data: nginx-load-balancer.sh
```

**Script de inicialización:**

```bash
#!/bin/bash
# nginx-load-balancer.sh

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Nginx
apt install -y nginx

# Configurar Nginx como load balancer
cat > /etc/nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server web1.internal:80 weight=1 max_fails=3 fail_timeout=30s;
        server web2.internal:80 weight=1 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }

    server {
        listen 80;
        server_name yourdomain.com;

        location / {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            proxy_connect_timeout 5s;
            proxy_send_timeout 10s;
            proxy_read_timeout 10s;
        }
    }
}
EOF

systemctl enable nginx
systemctl start nginx
```

### 2. Web Server Droplets

**Especificaciones:**
```yaml
Name: ai-news-web-{1,2}
Region: San Francisco 3 (SF03)
Size: Basic - 4 CPU, 8GB RAM, 160GB SSD
Image: Ubuntu 22.04 LTS x64
SSH Keys: [your-ssh-key]
Private Networking: Enabled
Monitoring: Enabled
User Data: web-server.sh
```

**Script de inicialización:**

```bash
#!/bin/bash
# web-server.sh

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com/ | sh
usermod -aG docker $USER

# Instalar Docker Compose
apt install -y docker-compose

# Crear directorios del proyecto
mkdir -p /var/www/ai-news-aggregator
cd /var/www/ai-news-aggregator

# Clonar repositorio
git clone https://github.com/yourusername/ai-news-aggregator.git .

# Configurar variables de entorno
cp .env.example .env

# Hacer scripts ejecutables
chmod +x start.sh
chmod +x backend/start_celery.sh

# Configurar firewall básico
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80
ufw allow from 10.116.0.0/20
ufw allow from 10.244.0.0/16
ufw enable
```

### 3. Worker Server Droplet

**Especificaciones:**
```yaml
Name: ai-news-worker
Region: San Francisco 3 (SF03)
Size: Basic - 2 CPU, 4GB RAM, 80GB SSD
Image: Ubuntu 22.04 LTS x64
SSH Keys: [your-ssh-key]
Private Networking: Enabled
Monitoring: Enabled
User Data: worker-server.sh
```

**Script de inicialización:**

```bash
#!/bin/bash
# worker-server.sh

# Actualizar sistema
apt update && apt upgrade -y

# Instalar Docker y Python
curl -fsSL https://get.docker.com/ | sh
apt install -y python3-pip python3-venv

# Configurar Python virtual environment
mkdir -p /opt/ai-news
python3 -m venv /opt/ai-news/venv

# Instalar dependencias Celery
/opt/ai-news/venv/bin/pip install celery[redis] redis psutil

# Configurar systemd service para Celery
cat > /etc/systemd/system/ai-news-celery.service << 'EOF'
[Unit]
Description=AI News Aggregator Celery Worker
After=network.target

[Service]
Type=forking
User=root
Group=root
WorkingDirectory=/var/www/ai-news-aggregator
Environment=PATH=/opt/ai-news/venv/bin
ExecStart=/opt/ai-news/venv/bin/celery multi start worker -A celery_app --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n.log
ExecStop=/opt/ai-news/venv/bin/celery multi stopwait worker --pidfile=/var/run/celery/%n.pid
ExecReload=/opt/ai-news/venv/bin/celery multi restart worker -A celery_app --pidfile=/var/run/celery/%n.pid --logfile=/var/log/celery/%n.log
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Crear directorios necesarios
mkdir -p /var/run/celery /var/log/celery

systemctl daemon-reload
systemctl enable ai-news-celery
```

## Managed Database Setup

### PostgreSQL Configuration

**Especificaciones:**
```yaml
Name: ai-news-db
Engine: PostgreSQL 15
Version: 15.4
Region: San Francisco 3 (SF03)
Size: db-s-2vcpu-4gb (2 vCPUs, 4GB RAM, 80GB SSD)
Storage: 80GB SSD
Database: ai_news_aggregator
Username: ai_news_user
Password: [secure-password]
SSL Mode: Require
Connection Pool: 25 connections
```

**Configuración inicial:**
```sql
-- Conectar a la base de datos
\c ai_news_aggregator

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Crear índices para performance
CREATE INDEX CONCURRENTLY idx_articles_published_date ON articles(published_date DESC);
CREATE INDEX CONCURRENTLY idx_articles_source_id ON articles(source_id);
CREATE INDEX CONCURRENTLY idx_articles_category ON articles USING GIN(category);
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);
CREATE INDEX CONCURRENTLY idx_user_preferences_user_id ON user_preferences(user_id);

-- Configurar optimizaciones
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

SELECT pg_reload_conf();
```

### Redis Configuration

**Especificaciones:**
```yaml
Name: ai-news-redis
Region: San Francisco 3 (SF03)
Size: db-s-1vcpu-2gb (1 vCPU, 2GB RAM, 25GB SSD)
Persistence: RDB snapshot every 6 hours
Eviction Policy: allkeys-lru
Max Memory Policy: allkeys-lru
```

## Load Balancer Configuration

### Nginx como Reverse Proxy

**Instalación y configuración:**

```bash
# Instalar Nginx
apt update && apt install -y nginx

# Configurar como load balancer
cat > /etc/nginx/sites-available/ai-news-lb << 'EOF'
upstream backend_servers {
    least_conn;
    server 10.116.0.11:80 max_fails=3 fail_timeout=30s;
    server 10.116.0.12:80 max_fails=3 fail_timeout=30s backup;
    
    keepalive 32;
}

upstream websocket_servers {
    server 10.116.0.11:8001;
    server 10.116.0.12:8001;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # Security Headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=1r/s;

    # Main application
    location / {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # WebSocket support for real-time features
    location /ws/ {
        proxy_pass http://websocket_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Health check endpoint
    location /health {
        access_log off;
        proxy_pass http://backend_servers;
    }
}
EOF

# Habilitar configuración
ln -s /etc/nginx/sites-available/ai-news-lb /etc/nginx/sites-enabled/

# Verificar configuración
nginx -t

# Recargar Nginx
systemctl reload nginx
```

## Networking y DNS

### 1. VPC Configuration

```bash
# Crear VPC personalizada para aislamiento
# Via DigitalOcean Control Panel
# Network: 10.116.0.0/16
# Region: San Francisco 3
# Attach droplets: web-1, web-2, worker-1
```

### 2. Cloudflare DNS Setup

**Registros DNS:**
```yaml
A Record: yourdomain.com -> Load Balancer IP
A Record: www.yourdomain.com -> Load Balancer IP
CNAME: api.yourdomain.com -> yourdomain.com
TXT: _acme-challenge.yourdomain.com -> ACME challenge token
TXT: _acme-challenge.www.yourdomain.com -> ACME challenge token
```

**Configuración Cloudflare:**
- SSL/TLS: Full (strict)
- Edge Certificates: Enabled
- Always Use HTTPS: Enabled
- HSTS: Enabled (max-age=31536000)
- Minimum TLS Version: 1.2

### 3. Firewall Rules

```bash
# En cada droplet
ufw status

# Reglas configuradas:
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
80/tcp                     ALLOW       Anywhere
443/tcp                    ALLOW       Anywhere
8000/tcp                   ALLOW       10.116.0.0/16
6379/tcp                   ALLOW       10.116.0.0/16
5432/tcp                   ALLOW       10.116.0.0/16
```

## Storage y Backup

### 1. Volume Setup para Datos

```bash
# Crear volume para backups
# Via DigitalOcean Control Panel: 50GB SSD, Region: SF03
# Attach to Load Balancer droplet

# Formatear y montar
mkfs.ext4 /dev/disk/by-id/scsi-0DO_Volume_volume-nyc1-01
mkdir -p /mnt/backups
echo '/dev/disk/by-id/scsi-0DO_Volume_volume-nyc1-01 /mnt/backups ext4 defaults,nofail,discard 0 2' >> /etc/fstab
mount -a
```

### 2. Backup Script

```bash
#!/bin/bash
# backup-digitalocean.sh

BACKUP_DIR="/mnt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
PROJECT_DIR="/var/www/ai-news-aggregator"

# Backup PostgreSQL
pg_dump -h your-db-host -U ai_news_user -d ai_news_aggregator | gzip > "${BACKUP_DIR}/db_backup_${DATE}.sql.gz"

# Backup application files
tar -czf "${BACKUP_DIR}/app_backup_${DATE}.tar.gz" "${PROJECT_DIR}"

# Backup Nginx configuration
cp -r /etc/nginx "${BACKUP_DIR}/nginx_config_${DATE}/"

# Backup Docker volumes
docker run --rm -v ai_news_aggregator_data:/data -v "${BACKUP_DIR}:/backup" \
  alpine tar -czf "/backup/docker_volume_${DATE}.tar.gz" /data

# Limpiar backups antiguos (mantener últimos 7 días)
find "${BACKUP_DIR}" -name "*.gz" -mtime +7 -delete
find "${BACKUP_DIR}" -name "*.sql.gz" -mtime +7 -delete

echo "Backup completado: ${DATE}"
```

### 3. Scheduled Backups

```bash
# Agregar a crontab
crontab -e

# Backup diario a las 2 AM
0 2 * * * /var/www/ai-news-aggregator/scripts/backup-digitalocean.sh

# Backup de logs semanal
0 3 * * 0 /var/www/ai-news-aggregator/scripts/backup-logs.sh
```

## Security Groups

### 1. Network Security

```bash
# Configurar fail2ban
apt install -y fail2ban

# Configurar fail2ban para Nginx
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

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
EOF

systemctl enable fail2ban
systemctl start fail2ban
```

### 2. SSH Hardening

```bash
# /etc/ssh/sshd_config
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
MaxAuthTries 3
ClientAliveInterval 300
ClientAliveCountMax 2
AllowUsers deploy
```

## Monitoring Setup

### 1. DigitalOcean Monitoring

**Métricas clave a configurar:**
- CPU Usage > 80% por 5 minutos
- Memory Usage > 85% por 5 minutos
- Disk Usage > 90% por 10 minutos
- Network traffic spikes
- Load average > number of cores

### 2. Custom Monitoring Script

```bash
#!/bin/bash
# monitor-digitalocean.sh

# Verificar servicios
check_service() {
    local service=$1
    if systemctl is-active --quiet $service; then
        echo "✅ $service está funcionando"
    else
        echo "❌ $service no está funcionando"
        systemctl restart $service
    fi
}

# Verificar Docker containers
check_containers() {
    cd /var/www/ai-news-aggregator
    if docker-compose ps | grep -q "Up"; then
        echo "✅ Todos los contenedores están funcionando"
    else
        echo "❌ Algunos contenedores han caído"
        docker-compose restart
    fi
}

# Verificar disco
check_disk() {
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $usage -gt 90 ]; then
        echo "⚠️  Uso de disco alto: ${usage}%"
        # Enviar alerta
    else
        echo "✅ Uso de disco normal: ${usage}%"
    fi
}

# Ejecutar checks
echo "🔍 Iniciando monitoreo del sistema..."
check_service nginx
check_containers
check_disk

# Verificar conectividad a servicios externos
check_external_connectivity() {
    # Database
    if pg_isready -h your-db-host -p 5432 > /dev/null; then
        echo "✅ Base de datos accesible"
    else
        echo "❌ Base de datos no accesible"
    fi
    
    # Redis
    if nc -z your-redis-host 6379 > /dev/null; then
        echo "✅ Redis accesible"
    else
        echo "❌ Redis no accesible"
    fi
}

check_external_connectivity
```

## Cost Estimation

### Estimación Mensual (USD)

| Servicio | Especificación | Costo Mensual |
|----------|----------------|---------------|
| **Load Balancer** | 2 CPU, 4GB RAM, 80GB SSD | $24 |
| **Web Servers (2)** | 4 CPU, 8GB RAM, 160GB SSD x2 | $96 |
| **Worker Server** | 2 CPU, 4GB RAM, 80GB SSD | $24 |
| **Monitoring Server** | 2 CPU, 4GB RAM, 80GB SSD | $24 |
| **Managed Database** | PostgreSQL 2 vCPU, 4GB RAM, 80GB SSD | $25 |
| **Redis Cluster** | 1 vCPU, 2GB RAM, 25GB SSD | $15 |
| **Backup Volume** | 50GB SSD | $5 |
| **Bandwidth** | 2TB transfer | $18 |
| **Load Balancer Traffic** | 1TB transfer | $12 |
| **SSL Certificates** | Let's Encrypt (free) | $0 |
| **DNS** | Cloudflare (free) | $0 |
| **Monitoring** | DigitalOcean Monitoring (free) | $0 |

**Total estimado: $243/mes**

### Optimizaciones de Costo

1. **Reserved Instances**: Descuento del 20% con compromiso anual
2. **Autoscaling**: Escalar horizontalmente según demanda
3. **Spot Instances**: Para workers no críticos
4. **Storage Optimization**: Limpiar volúmenes no utilizados
5. **Bandwidth Optimization**: Compresión y CDN

## Escalabilidad

### Horizontal Scaling

```bash
# Agregar nuevo web server
# 1. Crear droplet con misma configuración
# 2. Ejecutar script de inicialización
# 3. Actualizar load balancer config

# Actualizar /etc/nginx/nginx.conf en load balancer
upstream backend_servers {
    server 10.116.0.11:80 weight=1 max_fails=3 fail_timeout=30s;
    server 10.116.0.12:80 weight=1 max_fails=3 fail_timeout=30s;
    server 10.116.0.13:80 weight=1 max_fails=3 fail_timeout=30s;  # Nuevo servidor
    keepalive 32;
}

# Recargar configuración
nginx -s reload
```

### Vertical Scaling

```yaml
# Upgrade droplets según necesidades
# Web Servers: 4 CPU -> 8 CPU, 8GB RAM -> 16GB RAM
# Worker: 2 CPU -> 4 CPU, 4GB RAM -> 8GB RAM
# Database: 2 vCPU -> 4 vCPU, 4GB RAM -> 8GB RAM
```

## Comandos de Administración

```bash
# Gestión de droplets
doctl compute droplet list
doctl compute droplet create ai-news-web-3 --image ubuntu-22-04-x64 --size s-4vcpu-8gb --region sfo3 --ssh-keys your-ssh-key

# Gestión de volúmenes
doctl storage volume list
doctl storage volume create backup-volume-2 --size 100GiB --region sfo3

# Monitoreo
doctl compute droplet metrics cpu --percentage --start-time $(date -d '1 hour ago' -Iseconds) --end-time $(date -Iseconds) ai-news-web-1
doctl databases list
doctl databases backups list database-id

# Snapshot de droplets
doctl compute droplet-action snapshot ai-news-web-1 --name "pre-update-snapshot"
```

## Próximos Pasos

Después de configurar la infraestructura:

1. **Implementar CI/CD**: Ver `testing/CI_CD_SETUP.md`
2. **Configurar monitoreo avanzado**: Ver `MONITORING_SETUP.md`
3. **Aplicar seguridad**: Ver `SECURITY_CHECKLIST.md`
4. **Configurar backups**: Ver `BACKUP_RECOVERY.md`

---

**Notas importantes:**
- Todas las IPs privadas están en el rango 10.116.0.0/16
- Usar SSL/TLS en todas las comunicaciones
- Monitorear costos mensualmente
- Realizar backups antes de cambios importantes
- Documentar todos los cambios de configuración