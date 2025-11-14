# Quick Start Guide - Deployment Rápido

## Descripción General
Esta guía proporciona instrucciones rápidas para desplegar el AI News Aggregator en producción en menos de 30 minutos.

## Prerrequisitos
- Cuenta en DigitalOcean o AWS
- Docker y Docker Compose instalados
- Git configurado
- Dominio configurado (opcional para desarrollo)

## Deployment Rápido en 3 Pasos

### Paso 1: Configuración Inicial (5 minutos)

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/ai-news-aggregator.git
cd ai-news-aggregator

# Copiar archivo de configuración
cp .env.example .env

# Editar variables críticas
nano .env
```

**Variables mínimas requeridas:**
```bash
# Base de datos
DATABASE_URL=postgresql://user:password@db:5432/ai_news_aggregator
REDIS_URL=redis://redis:6379/0

# Claves API
OPENAI_API_KEY=tu_openai_api_key
ANTHROPIC_API_KEY=tu_anthropic_api_key
NEWSAPI_KEY=tu_newsapi_key

# Seguridad
SECRET_KEY=tu_secret_key_super_seguro_aqui

# URLs externas
FRONTEND_URL=http://localhost:3000
BACKEND_URL=http://localhost:8000
```

### Paso 2: Deployment con Docker (10 minutos)

```bash
# Build y start de todos los servicios
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar que todos los contenedores estén corriendo
docker-compose -f docker-compose.prod.yml ps

# Ejecutar migraciones de base de datos
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# Crear usuario admin
docker-compose -f docker-compose.prod.yml exec backend python create_admin.py
```

**Comandos de verificación rápida:**
```bash
# Verificar logs
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f frontend

# Verificar conectividad
curl http://localhost:8000/health
curl http://localhost:3000
```

### Paso 3: Configuración de Dominio y SSL (15 minutos)

```bash
# Instalar Certbot
sudo apt-get install certbot

# Obtener certificado SSL
sudo certbot certonly --standalone -d tu-dominio.com

# Configurar nginx
sudo cp nginx/nginx.prod.conf /etc/nginx/sites-available/ai-news-aggregator
sudo ln -s /etc/nginx/sites-available/ai-news-aggregator /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**Configuración nginx básica:**
```nginx
server {
    listen 80;
    server_name tu-dominio.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Configuración Rápida de Servicios en la Nube

### DigitalOcean App Platform

1. **Crear aplicación:**
```bash
# Conectar repositorio
doctl apps create --spec .do/app.yaml
```

2. **Configurar variables de entorno:**
```bash
doctl apps create-variable ai-news-aggregator --key DATABASE_URL --value "postgresql://..."
doctl apps create-variable ai-news-aggregator --key REDIS_URL --value "redis://..."
```

3. **Desplegar:**
```bash
doctl apps deploy ai-news-aggregator
```

### AWS ECS con Fargate

1. **Configurar task definition:**
```bash
aws ecs register-task-definition --cli-input-json file://aws/task-definition.json
```

2. **Crear servicio:**
```bash
aws ecs create-service \
    --cluster ai-news-cluster \
    --service-name ai-news-service \
    --task-definition ai-news-task:1 \
    --desired-count 2
```

## Configuración de Base de Datos

### PostgreSQL en la Nube

**DigitalOcean Managed Database:**
```bash
# Crear instancia
doctl databases create ai-news-db \
    --engine pg \
    --version 15 \
    --size db-s-1vcpu-1gb \
    --region nyc1

# Obtener connection string
doctl databases connection-pool ai-news-db
```

**AWS RDS:**
```bash
# Crear instancia
aws rds create-db-instance \
    --db-instance-identifier ai-news-db \
    --db-instance-class db.t3.micro \
    --engine postgres \
    --master-username admin \
    --master-user-password tu_password_seguro \
    --allocated-storage 20
```

## Configuración de Redis

### Redis Cloud
1. Registrarse en Redis Cloud
2. Crear base de datos gratuita
3. Copiar URL de conexión al .env

### Redis en DigitalOcean
```bash
# Crear managed Redis
doctl databases create ai-news-redis \
    --engine redis \
    --version "7" \
    --size db-s-1vcpu-1gb \
    --region nyc1
```

## Configuración de Monitoreo Básico

### Prometheus + Grafana (Docker)

```bash
# Crear docker-compose específico para monitoreo
cat > docker-compose.monitoring.yml << EOF
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
EOF

# Ejecutar monitoreo
docker-compose -f docker-compose.monitoring.yml up -d
```

### Configuración Prometheus básica:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ai-news-backend'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
  
  - job_name: 'ai-news-redis'
    static_configs:
      - targets: ['localhost:9121']
```

## Configuración de Backup Automático

### Backup de Base de Datos

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Crear backup
docker-compose exec -T db pg_dump -U ai_news_user ai_news_aggregator > "$BACKUP_DIR/backup_$DATE.sql"

# Comprimir
gzip "$BACKUP_DIR/backup_$DATE.sql"

# Mantener solo últimos 7 días
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +7 -delete

echo "Backup completado: backup_$DATE.sql.gz"
```

### Configurar cron job:
```bash
# Hacer ejecutable
chmod +x backup.sh

# Agregar al crontab (backup diario a las 2 AM)
crontab -e
# 0 2 * * * /path/to/backup.sh
```

## Verificación Post-Deployment

### Checklist de Verificación

```bash
# 1. Verificar contenedores
docker-compose -f docker-compose.prod.yml ps

# 2. Verificar conectividad de servicios
curl http://localhost:8000/health
curl http://localhost:3000

# 3. Verificar base de datos
docker-compose exec backend python -c "from app.core.database import engine; print('DB OK' if engine else 'DB FAIL')"

# 4. Verificar Redis
docker-compose exec redis redis-cli ping

# 5. Verificar logs por errores
docker-compose -f docker-compose.prod.yml logs --tail=100 backend | grep -i error

# 6. Verificar métricas
curl http://localhost:9090/api/v1/query?query=up

# 7. Test de funcionalidad básica
curl -X POST http://localhost:8000/api/v1/news/scrape \
  -H "Content-Type: application/json" \
  -d '{"sources": ["test-source"]}'
```

### URLs de Verificación

- **Backend Health**: http://tu-dominio.com/health
- **API Documentation**: http://tu-dominio.com/docs
- **Frontend**: http://tu-dominio.com
- **Grafana**: http://tu-dominio.com:3001 (admin/admin123)
- **Prometheus**: http://tu-dominio.com:9090

## Comandos de Gestión Rápida

### Gestión de Servicios
```bash
# Reiniciar servicio específico
docker-compose restart backend

# Ver logs en tiempo real
docker-compose logs -f --tail=50

# Escalar backend a 3 instancias
docker-compose up -d --scale backend=3

# Actualizar código
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

### Gestión de Base de Datos
```bash
# Backup manual
docker-compose exec db pg_dump -U ai_news_user ai_news_aggregator > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U ai_news_user ai_news_aggregator < backup.sql

# Ejecutar migración específica
docker-compose exec backend alembic upgrade <revision_id>
```

### Limpieza y Mantenimiento
```bash
# Limpiar logs de Docker
docker system prune -f

# Limpiar imágenes no utilizadas
docker image prune -a -f

# Reiniciar Redis (limpiar cache)
docker-compose restart redis

# Ver uso de disco
docker system df
```

## Resolución de Problemas Comunes

### Error de Conexión a Base de Datos
```bash
# Verificar que la base de datos esté corriendo
docker-compose exec db pg_isready -U ai_news_user

# Verificar variables de entorno
docker-compose exec backend env | grep DATABASE

# Reiniciar servicios de base de datos
docker-compose restart db
```

### Error de Redis
```bash
# Verificar Redis
docker-compose exec redis redis-cli ping

# Limpiar Redis
docker-compose exec redis redis-cli FLUSHALL

# Reiniciar Redis
docker-compose restart redis
```

### Error de Puertos
```bash
# Verificar puertos en uso
netstat -tulpn | grep :8000
netstat -tulpn | grep :3000

# Matar proceso en puerto específico
sudo lsof -t -i:8000 | xargs kill -9
```

### Problemas de Memoria
```bash
# Ver uso de memoria
docker stats

# Aumentar memoria disponible
# Editar docker-compose.prod.yml y agregar:
# deploy:
#   resources:
#     limits:
#       memory: 2G
```

## Configuración de Producción Rápida

### Variables de Entorno de Producción
```bash
# Seguridad
SECRET_KEY=clave_super_secreta_de_al_menos_32_caracteres
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Base de datos
DATABASE_URL=postgresql://usuario:pass@host:5432/db
REDIS_URL=redis://host:6379/0

# APIs Externas
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
NEWSAPI_KEY=...

# URLs
FRONTEND_URL=https://tu-dominio.com
BACKEND_URL=https://api.tu-dominio.com

# Monitoreo
SENTRY_DSN=https://...
PROMETHEUS_ENABLED=true

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Cache
CACHE_TTL=3600
CACHE_MAX_SIZE=1000
```

### Configuración SSL/HTTPS
```bash
# Con Let's Encrypt
sudo certbot --nginx -d tu-dominio.com

# Verificar renovación automática
sudo crontab -l | grep certbot
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## Métricas de Performance Inicial

### KPIs a Monitorear
- **Tiempo de respuesta**: < 200ms para endpoints principales
- **Uptime**: > 99.9%
- **Uso de CPU**: < 70% promedio
- **Uso de memoria**: < 80%
- **Errores**: < 0.1%
- **Throughput**: > 1000 requests/minuto

### Configuración de Alertas Básicas
```bash
# Script de monitoreo simple
cat > monitor.sh << 'EOF'
#!/bin/bash

# Verificar uptime
UPTIME=$(curl -s http://localhost:8000/health)
if [[ $UPTIME != *"healthy"* ]]; then
    echo "ALERT: Backend no responde"
    # Enviar notificación
fi

# Verificar uso de disco
DISK_USAGE=$(df / | grep -vE '^Filesystem|tmpfs|cdrom' | awk '{ print $5 }' | head -1 | cut -d'%' -f1)
if [ $DISK_USAGE -gt 80 ]; then
    echo "ALERT: Uso de disco alto: $DISK_USAGE%"
fi

# Verificar memoria
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ $MEM_USAGE -gt 80 ]; then
    echo "ALERT: Uso de memoria alto: $MEM_USAGE%"
fi
EOF

chmod +x monitor.sh

# Ejecutar cada 5 minutos
crontab -e
# */5 * * * * /path/to/monitor.sh
```

## Escalamiento Básico

### Horizontal Scaling
```bash
# Escalar backend
docker-compose up -d --scale backend=3

# Escalar workers de Celery
docker-compose up -d --scale celery-worker=2
```

### Load Balancer con Nginx
```nginx
upstream backend {
    server localhost:8001;
    server localhost:8002;
    server localhost:8003;
}

server {
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Próximos Pasos

1. **Configurar CI/CD**: GitHub Actions o GitLab CI
2. **Implementar monitoring avanzado**: Prometheus + Grafana completo
3. **Configurar logging centralizado**: ELK stack
4. **Implementar backup automático**: Estrategia de backup completa
5. **Configurar alertas**: Notificaciones por email/Slack
6. **Implementar rate limiting**: Protección contra ataques
7. **Configurar CDN**: Cloudflare para contenido estático
8. **Implementar tests de carga**: Verificar performance bajo estrés

## Comandos de Emergencia

```bash
# Parar todo rápidamente
docker-compose -f docker-compose.prod.yml down

# Reiniciar todo
docker-compose -f docker-compose.prod.yml restart

# Ver estado crítico
docker-compose -f docker-compose.prod.yml ps

# Logs de errores recientes
docker-compose -f docker-compose.prod.yml logs --since=5m | grep ERROR

# Rollback a versión anterior
git checkout HEAD~1
docker-compose -f docker-compose.prod.yml up -d --build
```

## Contacto y Soporte

- **Documentación completa**: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
- **Monitoreo**: [MONITORING_SETUP.md](./MONITORING_SETUP.md)
- **Seguridad**: [SECURITY_CHECKLIST.md](./SECURITY_CHECKLIST.md)

**¿Problemas?** Consulta primero [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) para soluciones rápidas.