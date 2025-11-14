# Guía de Resolución de Problemas

## Tabla de Contenidos
- [Diagnóstico Rápido](#diagnóstico-rápido)
- [Problemas de Red](#problemas-de-red)
- [Problemas de Base de Datos](#problemas-de-base-de-datos)
- [Problemas de Docker](#problemas-de-docker)
- [Problemas de Performance](#problemas-de-performance)
- [Problemas de Memoria](#problemas-de-memoria)
- [Problemas de Logs](#problemas-de-logs)
- [Problemas de Autenticación](#problemas-de-autenticación)
- [Problemas de SSL/TLS](#problemas-de-ssltls)
- [Herramientas de Diagnóstico](#herramientas-de-diagnóstico)

## Diagnóstico Rápido

### Script de Diagnóstico Completo

```bash
#!/bin/bash
# quick-diagnosis.sh

echo "🔍 Iniciando diagnóstico completo del sistema..."
echo "Fecha: $(date)"
echo "Host: $(hostname)"
echo "Uptime: $(uptime)"
echo ""

# 1. Estado de servicios críticos
echo "=== SERVICIOS ==="
systemctl is-active nginx || echo "❌ Nginx: INACTIVE"
systemctl is-active docker || echo "❌ Docker: INACTIVE"
systemctl is-active fail2ban || echo "❌ Fail2ban: INACTIVE"

# 2. Conectividad de red
echo ""
echo "=== CONECTIVIDAD ==="
if ping -c 1 8.8.8.8 > /dev/null 2>&1; then
    echo "✅ Internet: OK"
else
    echo "❌ Internet: FAIL"
fi

if curl -f -s http://localhost/health > /dev/null 2>&1; then
    echo "✅ API Local: OK"
else
    echo "❌ API Local: FAIL"
fi

# 3. Uso de recursos
echo ""
echo "=== RECURSOS ==="
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')"
echo "Memoria: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2 }')"
echo "Disco: $(df -h / | awk 'NR==2{printf "%s", $5}')"

# 4. Docker containers
echo ""
echo "=== CONTAINERS ==="
if docker-compose ps | grep -q "Up"; then
    echo "✅ Docker containers: RUNNING"
    docker-compose ps
else
    echo "❌ Docker containers: ISSUES DETECTED"
    docker-compose ps
fi

# 5. Logs recientes
echo ""
echo "=== LOGS RECIENTES (últimas 5 líneas) ==="
echo "--- Nginx ---"
tail -n 5 /var/log/nginx/error.log 2>/dev/null || echo "No nginx error logs found"

echo ""
echo "--- Aplicación ---"
tail -n 5 /var/www/ai-news-aggregator/logs/app.log 2>/dev/null || echo "No application logs found"

# 6. Verificación SSL
echo ""
echo "=== SSL CERTIFICADO ==="
if [ -f "/etc/letsencrypt/live/$(hostname)/cert.pem" ]; then
    expiry=$(openssl x509 -enddate -noout -in "/etc/letsencrypt/live/$(hostname)/cert.pem" | cut -d= -f2)
    echo "✅ SSL: Certificate valid until $expiry"
else
    echo "⚠️  SSL: Certificate not found"
fi

echo ""
echo "🔍 Diagnóstico completado"
```

## Problemas de Red

### 1. Conexión no disponible

```bash
# Verificar estado de interfaz de red
ip addr show
ip route show

# Verificar conectividad DNS
nslookup yourdomain.com
dig yourdomain.com

# Verificar resolución local
cat /etc/hosts

# Verificar configuración de firewall
ufw status
iptables -L -n

# Reiniciar servicios de red
systemctl restart networking
systemctl restart systemd-resolved

# Verificar puertos abiertos
netstat -tlnp
ss -tlnp

# Test de conectividad específico
telnet yourdomain.com 443
curl -v https://yourdomain.com
```

**Problema común**: Error de DNS
```bash
# Solución: Configurar DNS correctamente
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 8.8.4.4" >> /etc/resolv.conf
systemctl restart systemd-resolved
```

### 2. Timeout en API

```bash
# Verificar logs de Nginx
tail -f /var/log/nginx/error.log

# Verificar estado del backend
curl http://localhost:8000/health

# Verificar logs del contenedor Docker
docker-compose logs backend

# Verificar conectividad interna
docker exec ai-news-aggregator-backend ping -c 3 database_host
docker exec ai-news-aggregator-backend ping -c 3 redis_host

# Verificar métricas de sistema
htop
iotop
netstat -i
```

### 3. Load Balancer no funciona

```bash
# Verificar configuración de Nginx
nginx -t

# Verificar servicios backend
docker-compose ps
curl http://localhost:8000/health
curl http://localhost:8001/health

# Verificar conectividad entre droplets
ping 10.116.0.11
ping 10.116.0.12

# Verificar reglas de firewall
ufw status numbered

# Reiniciar Nginx
systemctl reload nginx
systemctl restart nginx
```

## Problemas de Base de Datos

### 1. Conexión fallida

```bash
# Verificar estado de PostgreSQL
systemctl status postgresql

# Verificar conectividad
pg_isready -h database_host -p 5432 -U postgres

# Verificar logs de PostgreSQL
tail -f /var/log/postgresql/postgresql-15-main.log

# Verificar configuración
cat /etc/postgresql/15/main/postgresql.conf | grep listen

# Test de conexión manual
psql -h database_host -U postgres -d ai_news_aggregator -c "SELECT version();"

# Verificar usuarios y permisos
psql -h database_host -U postgres -c "\du"
psql -h database_host -U postgres -d ai_news_aggregator -c "\l"
```

**Error común**: "password authentication failed"
```bash
# Solución: Verificar configuración de pg_hba.conf
# Editar: /etc/postgresql/15/main/pg_hba.conf
# Cambiar:
host    all             all             127.0.0.1/32            md5
# Por:
host    all             all             0.0.0.0/0              md5

# Reiniciar PostgreSQL
systemctl restart postgresql
```

### 2. Conexiones agotadas

```sql
-- Ver conexiones activas
SELECT count(*) FROM pg_stat_activity;
SELECT * FROM pg_stat_activity ORDER BY query_start DESC LIMIT 10;

-- Ver conexiones por usuario
SELECT usename, count(*) FROM pg_stat_activity GROUP BY usename;

-- Ver queries lentas
SELECT query, mean_time, calls FROM pg_stat_statements 
ORDER BY mean_time DESC LIMIT 10;

-- Kill conexiones largas
SELECT pg_terminate_backend(pid) FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '1 hour';

-- Ver configuración de conexiones
SHOW max_connections;
SHOW shared_buffers;
SHOW work_mem;
```

**Solución**: Optimizar configuración
```sql
-- Ajustar configuración para más conexiones
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '1GB';
ALTER SYSTEM SET effective_cache_size = '3GB';
SELECT pg_reload_conf();
```

### 3. Queries lentas

```bash
# Activar pg_stat_statements
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

# Ver queries más lentas
SELECT query, mean_time, max_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

# Ver queries más frecuentes
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements
ORDER BY calls DESC
LIMIT 10;

# Verificar índices
SELECT schemaname, tablename, indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public';

# Crear índice faltante
CREATE INDEX CONCURRENTLY idx_articles_published_date 
ON articles(published_date DESC);

# Actualizar estadísticas
ANALYZE articles;
VACUUM ANALYZE articles;
```

### 4. Lock wait timeouts

```sql
-- Ver locks activos
SELECT * FROM pg_locks WHERE NOT granted;

-- Ver transacciones bloqueadas
SELECT 
    a.datname,
    l.relation::regclass,
    l.transactionid,
    l.mode,
    l.GRANTED,
    a.usename,
    a.query,
    a.query_start,
    age(now(), a.query_start) AS query_duration
FROM pg_stat_activity a
JOIN pg_locks l ON l.pid = a.pid
WHERE a.state = 'active';

-- Ver transacciones largas
SELECT 
    pid,
    now() - pg_stat_activity.query_start AS duration,
    query,
    state
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 minutes';
```

**Solución**: Kill transacciones problemáticas
```sql
-- Terminar query específico
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE query LIKE '%problematic_query%';

-- Terminar todas las transacciones inactivas por más de 1 hora
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '1 hour';
```

## Problemas de Docker

### 1. Contenedores no inician

```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs de contenedores
docker-compose logs backend
docker-compose logs frontend
docker-compose logs redis

# Ver logs específicos
docker logs ai-news-aggregator-backend
docker logs ai-news-aggregator-frontend

# Verificar configuración
docker-compose config

# Rebuild y restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Verificar espacio en disco
df -h
docker system df

# Limpiar recursos no utilizados
docker system prune -a
```

**Error común**: "port already in use"
```bash
# Encontrar proceso usando el puerto
lsof -i :8000
netstat -tlnp | grep :8000

# Matar proceso
kill -9 PID

# O cambiar puerto en docker-compose.yml
# ports:
#   - "8001:8000"  # Cambiar puerto externo
```

### 2. Out of Memory

```bash
# Ver uso de memoria por contenedor
docker stats --no-stream

# Ver eventos de Docker
docker events --filter 'type=container' --since '1h'

# Ver logs de OOM killer
dmesg | grep -i "killed process"

# Aumentar memoria en docker-compose
# services:
#   backend:
#     mem_limit: 1g
#     memswap_limit: 1g
```

### 3. Network issues

```bash
# Ver redes de Docker
docker network ls
docker network inspect ai-news-aggregator_app_network

# Ver conectividad entre contenedores
docker exec ai-news-backend ping redis
docker exec ai-news-backend ping database

# Ver DNS resolution
docker exec ai-news-backend nslookup database

# Recrear red
docker network rm ai-news-aggregator_app_network
docker-compose up -d

# Ver configuración de red
docker inspect ai-news-backend | grep -A 10 Networks
```

## Problemas de Performance

### 1. High CPU Usage

```bash
# Identificar procesos que consumen CPU
top -o %CPU

# Verificar por usuario
ps aux --sort=-%cpu | head -10

# Verificar procesos de Python
ps aux | grep python

# Verificar Celery workers
docker exec ai-news-backend celery -A celery_app status

# Verificar logs de Celery
docker exec ai-news-backend tail -f /var/log/celery/worker.log

# Optimizar workers Celery
# En docker-compose.yml:
# celery:
#   environment:
#     - CELERY_WORKER_CONCURRENCY=4
#     - CELERY_WORKER_PREFETCH_MULTIPLIER=1
```

**Solución**: Scaling horizontal
```bash
# Escalar workers Celery
docker-compose up -d --scale celery=3

# Ver estado de workers
docker-compose ps
docker exec ai-news-backend celery -A celery_app inspect active
```

### 2. High Memory Usage

```bash
# Ver uso de memoria detallado
ps aux --sort=-%mem | head -10

# Ver uso por contenedor
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Verificar memory leaks
# Python memory profiler
docker exec ai-news-backend python -m memory_profiler /app/main.py

# Verificar garbage collection
docker exec ai-news-backend python -c "
import gc
import sys
print('GC threshold:', gc.get_threshold())
print('GC counts:', gc.get_count())
gc.collect()
print('After GC:', gc.get_count())
"

# Optimizar configuración de Python
# En start.sh:
# export PYTHONMALLOC=malloc
# export PYTHONMALLOPT=1
# export MALLOC_ARENA_MAX=2
```

### 3. Disk I/O Issues

```bash
# Ver procesos usando disco
iotop -ao

# Ver uso de disco por proceso
lsof +D /var/www/ai-news-aggregator

# Verificar espacio en disco
df -h
du -sh /var/www/ai-news-aggregator/logs
du -sh /var/log/nginx

# Limpiar logs antiguos
find /var/log -name "*.log" -mtime +30 -delete
find /var/www/ai-news-aggregator/logs -name "*.log" -mtime +7 -delete

# Verificar I/O wait time
sar -u 1 5

# Optimizar configuración de Redis
# En redis.conf:
# maxmemory 1gb
# maxmemory-policy allkeys-lru
# save 900 1
# save 300 10
# save 60 10000
```

### 4. Database Performance Issues

```sql
-- Activar extensión para estadísticas
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;

-- Ver queries más lentas
SELECT query, calls, total_time, mean_time, max_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;

-- Ver índices no utilizados
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Ver tablas sin índices
SELECT 
    schemaname,
    tablename,
    seq_scan,
    seq_tup_read,
    idx_scan,
    idx_tup_fetch
FROM pg_stat_user_tables
WHERE seq_scan > 100 AND idx_scan = 0;

-- Verificar bloat en tablas
SELECT 
    schemaname,
    tablename,
    n_tup_ins,
    n_tup_upd,
    n_tup_del,
    n_live_tup,
    n_dead_tup
FROM pg_stat_user_tables
WHERE n_dead_tup > n_live_tup * 0.1;
```

**Optimización**:
```sql
-- Crear índices faltantes
CREATE INDEX CONCURRENTLY idx_articles_category_published 
ON articles(category, published_date DESC);

-- Actualizar estadísticas
ANALYZE;

-- Vacuum para recuperar espacio
VACUUM FULL;

-- Verificar configuration
SHOW shared_buffers;
SHOW effective_cache_size;
SHOW random_page_cost;
SHOW work_mem;
```

## Problemas de Logs

### 1. Logs no se generan

```bash
# Verificar configuración de logging
cat /var/www/ai-news-aggregator/backend/app/core/logging_config.py

# Verificar permisos de directorio de logs
ls -la /var/www/ai-news-aggregator/logs/
chown -R appuser:appuser /var/www/ai-news-aggregator/logs/
chmod 755 /var/www/ai-news-aggregator/logs/

# Verificar configuración de Python
# En main.py:
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/logs/app.log'),
        logging.StreamHandler()
    ]
)

# Test manual de logging
docker exec ai-news-backend python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info('Test log message')
"
```

### 2. Logs muy grandes

```bash
# Ver tamaño de logs
du -sh /var/log/nginx/
du -sh /var/www/ai-news-aggregator/logs/

# Rotar logs manualmente
logrotate -f /etc/logrotate.d/nginx
logrotate -f /etc/logrotate.conf

# Configurar logrotate para la aplicación
cat > /etc/logrotate.d/ai-news-aggregator << 'EOF'
/var/www/ai-news-aggregator/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 appuser appuser
    postrotate
        docker exec ai-news-aggregator-backend sh -c 'pkill -USR1 gunicorn'
    endscript
}
EOF

# Limpiar logs antiguos manualmente
find /var/log -name "*.log" -mtime +30 -delete
```

### 3. Formato de logs incorrecto

```python
# Configurar logging estructurado
# backend/app/core/structured_logging.py
import structlog
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': structlog.stdlib.ProcessorFormatter,
            'processor': structlog.processors.JSONRenderer(),
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/app/logs/app.log',
            'maxBytes': 1024*1024*100,  # 100MB
            'backupCount': 10,
            'formatter': 'json',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'loggers': {
        '': {
            'handlers': ['default', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'uvicorn.error': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False,
        },
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
```

## Problemas de Autenticación

### 1. JWT Token Issues

```python
# Test de generación y verificación de JWT
# test_jwt.py
import jwt
import datetime
from backend.app.core.config import settings

# Generar token
payload = {
    'user_id': 123,
    'email': 'test@example.com',
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
}

token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
print(f"Generated token: {token}")

# Verificar token
try:
    decoded = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
    print(f"Decoded payload: {decoded}")
except jwt.ExpiredSignatureError:
    print("Token has expired")
except jwt.JWTError as e:
    print(f"JWT error: {e}")
```

### 2. Session Issues

```python
# Verificar configuración de sesiones
# backend/app/core/session.py
from fastapi import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test de conexión a base de datos
try:
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    result = db.execute("SELECT 1")
    print("Database connection: OK")
    db.close()
except Exception as e:
    print(f"Database connection failed: {e}")
```

### 3. CORS Issues

```python
# Test de configuración CORS
# test_cors.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/test-cors")
async def test_cors():
    return {"message": "CORS test"}

# Test desde frontend
fetch('https://yourdomain.com/api/test-cors', {
    method: 'GET',
    credentials: 'include'
})
.then(response => response.json())
.then(data => console.log(data));
```

## Problemas de SSL/TLS

### 1. Certificado expirado

```bash
# Verificar expiración de certificado
openssl x509 -enddate -noout -in /etc/letsencrypt/live/yourdomain.com/cert.pem

# Renovación manual
certbot renew --force-renewal

# Verificar renovación automática
crontab -l | grep certbot

# Test de renovación
certbot renew --dry-run

# Verificar configuración de Nginx
nginx -t

# Recargar Nginx
systemctl reload nginx
```

### 2. SSL Configuration Issues

```bash
# Test de configuración SSL
sslscan yourdomain.com
testssl.sh yourdomain.com

# Verificar cipher suites
openssl s_client -connect yourdomain.com:443 -cipher 'ECDHE-RSA-AES256-GCM-SHA384'

# Verificar HSTS header
curl -I https://yourdomain.com | grep -i strict-transport-security

# Verificar certificate chain
openssl s_client -connect yourdomain.com:443 -showcerts

# Debug de handshake SSL
openssl s_client -connect yourdomain.com:443 -verbose
```

### 3. Mixed Content Issues

```bash
# Identificar contenido mixto
curl -s https://yourdomain.com | grep -i "http://"

# Verificar headers de Content Security Policy
curl -I https://yourdomain.com | grep -i content-security-policy

# Actualizar URLs en la aplicación
# Backend: Configurar base URLs correctas
# Frontend: Usar URLs relativas en lugar de absolutas
```

## Herramientas de Diagnóstico

### 1. Monitoreo en tiempo real

```bash
# Monitoreo de recursos
htop

# Monitoreo de I/O
iotop -ao

# Monitoreo de red
iftop -i eth0
nethogs

# Monitoreo de procesos
ps aux --forest | head -50

# Verificar conectividad específica
mtr yourdomain.com
traceroute yourdomain.com
```

### 2. Análisis de logs

```bash
# Tail en tiempo real
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
tail -f /var/www/ai-news-aggregator/logs/app.log

# Análisis de patrones
grep "ERROR" /var/www/ai-news-aggregator/logs/app.log | tail -20
grep "404" /var/log/nginx/access.log | tail -20

# Estadísticas de código de respuesta
awk '{print $9}' /var/log/nginx/access.log | sort | uniq -c

# Top IPs
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -nr | head -10
```

### 3. Análisis de performance

```bash
# Test de carga básico
ab -n 1000 -c 10 https://yourdomain.com/

# Test de endpoints específicos
ab -n 100 -c 5 https://yourdomain.com/api/articles/

# Profiling de aplicación Python
# Instalar py-spy
pip install py-spy

# Profiling de proceso específico
py-spy top --pid $(pgrep -f "python.*main.py")

# Generar flame graph
py-spy record -o profile.svg -- python /app/main.py
```

### 4. Análisis de red

```bash
# Ver conexiones activas
netstat -tuln
ss -tuln

# Ver conexiones por proceso
lsof -i -P -n | grep LISTEN

# Test de conectividad a servicios externos
nc -zv external-api.com 443
curl -v https://external-api.com/health

# Verificar DNS resolution
dig @8.8.8.8 yourdomain.com
nslookup yourdomain.com
```

## Emergency Procedures

### 1. Sistema caído

```bash
#!/bin/bash
# emergency-recovery.sh

echo "🚨 Iniciando procedimiento de emergencia..."

# 1. Parar todos los servicios
docker-compose down
systemctl stop nginx

# 2. Verificar espacio en disco
df -h
if [ $(df / | awk 'NR==2{print $5}' | sed 's/%//') -gt 90 ]; then
    echo "⚠️  Limpiando logs antiguos..."
    find /var/log -name "*.log" -mtime +7 -delete
    find /var/www/ai-news-aggregator/logs -name "*.log" -mtime +3 -delete
fi

# 3. Verificar memoria
free -h
if [ $(free | awk '/^Mem:/ {print $3/$2 * 100.0}') -gt 90 ]; then
    echo "⚠️  Liberando memoria..."
    sync
    echo 3 > /proc/sys/vm/drop_caches
fi

# 4. Reiniciar servicios críticos
systemctl start nginx
docker-compose up -d

# 5. Verificar estado
sleep 30
./quick-diagnosis.sh

echo "✅ Procedimiento de emergencia completado"
```

### 2. Rollback emergency

```bash
#!/bin/bash
# emergency-rollback.sh

echo "🔄 Iniciando rollback de emergencia..."

# 1. Hacer backup del estado actual
cp -r /var/www/ai-news-aggregator /var/www/ai-news-aggregator.backup.$(date +%Y%m%d_%H%M%S)

# 2. Parar servicios
docker-compose down

# 3. Revertir a versión anterior conocida como funcional
git stash
git checkout last-known-good-tag

# 4. Rebuild y restart
docker-compose build --no-cache
docker-compose up -d

# 5. Verificar rollback
sleep 30
curl -f http://localhost/health || {
    echo "❌ Rollback failed"
    exit 1
}

echo "✅ Rollback completado exitosamente"
```

### 3. Database emergency

```sql
-- emergency-db-fixes.sql

-- 1. Verificar conexiones activas
SELECT count(*) as active_connections FROM pg_stat_activity;

-- 2. Terminar conexiones inactivas largas
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '1 hour';

-- 3. Kill transacciones bloqueadas
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE wait_event_type = 'Lock' AND state = 'active';

-- 4. Rebuild índices críticos
REINDEX INDEX CONCURRENTLY idx_articles_published_date;

-- 5. Actualizar estadísticas
ANALYZE;

-- 6. Vacuum para recuperar espacio
VACUUM;

-- 7. Verificar integridad
SELECT pg_size_pretty(pg_database_size('ai_news_aggregator'));
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables 
ORDER BY n_tup_del DESC;
```

## Comandos de Diagnóstico Rápido

```bash
# Health check completo
make health-check

# Ver estado de todos los servicios
make status

# Ver logs recientes
make logs | tail -100

# Ver métricas del sistema
curl http://localhost:9090/metrics | grep -E "(up|cpu|memory)"

# Test de conectividad
make test-connectivity

# Verificar configuración
make config-check

# Test de performance
make benchmark

# Verificar SSL
make ssl-check

# Backup de emergencia
make emergency-backup
```

## Recursos Adicionales

- **Documentación oficial**: https://docs.ai-news-aggregator.com
- **Logs centralizados**: http://kibana.yourdomain.com
- **Métricas**: http://grafana.yourdomain.com
- **Alert management**: http://prometheus.yourdomain.com
- **Database tools**: http://pgadmin.yourdomain.com

---

**Importante**: Siempre documenta los problemas encontrados y sus soluciones para crear una base de conocimiento.