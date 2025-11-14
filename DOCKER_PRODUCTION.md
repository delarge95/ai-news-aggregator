# Docker Compose - Configuración de Producción

Esta configuración de Docker Compose está optimizada para el despliegue en producción del proyecto AI News Aggregator, con todas las características necesarias para un entorno de producción robusto.

## 🚀 Características de Producción

### 📦 Servicios Incluidos

- **PostgreSQL 15**: Base de datos principal con configuraciones optimizadas
- **Redis 7**: Cache y message broker para Celery
- **Backend FastAPI**: API REST con workers de Celery escalables
- **Frontend React**: Interfaz de usuario con build optimizado
- **Nginx**: Reverse proxy con configuraciones de seguridad y rendimiento

### 🔧 Características Técnicas

- **Multi-stage Dockerfiles**: Imágenes optimizadas y de menor tamaño
- **Health Checks**: Verificación de salud en todos los servicios
- **Resource Limits**: Control de recursos por contenedor
- **Logging Centralizado**: Configuración de logs estructurados
- **Networks Seguras**: Redes aisladas entre frontend y backend
- **Persistent Volumes**: Almacenamiento persistente para datos
- **Restart Policies**: Políticas de reinicio automático
- **Rate Limiting**: Limitación de requests en nginx

## 📁 Estructura de Archivos

```
ai-news-aggregator/
├── docker-compose.prod.yml          # Configuración principal de producción
├── docker-compose.override.yml      # Configuración de desarrollo
├── docker/
│   └── nginx/
│       ├── nginx.conf              # Configuración principal de nginx
│       ├── default.conf            # Configuración del servidor frontend
│       ├── nginx.dev.conf          # Configuración de desarrollo
│       └── frontend.conf           # Configuración standalone del frontend
├── backend/
│   ├── Dockerfile.prod             # Dockerfile optimizado con multi-stage
│   └── .dockerignore               # Archivos ignorados
├── frontend/
│   └── ai-news-frontend/
│       ├── Dockerfile.prod         # Dockerfile del frontend optimizado
│       └── .dockerignore           # Archivos ignorados del frontend
├── init-docker-prod.sh             # Script de inicialización
├── deploy-prod.sh                  # Script de despliegue completo
├── .env.prod.example               # Variables de entorno de producción
└── data/                           # Directorio para volúmenes persistentes
    ├── postgres/
    ├── redis/
    ├── logs/
    └── frontend/
```

## 🚀 Inicio Rápido

### 1. Configuración Inicial

```bash
# Hacer ejecutables los scripts
chmod +x init-docker-prod.sh deploy-prod.sh

# Inicializar el entorno de producción
./init-docker-prod.sh

# Copiar y configurar variables de entorno
cp .env.prod.example .env
# Editar .env con tus valores de producción
```

### 2. Despliegue Completo

```bash
# Despliegue completo (recomendado para primera instalación)
./deploy-prod.sh deploy

# O usando Makefile
make prod-deploy
```

### 3. Verificación

```bash
# Verificar estado de los servicios
./deploy-prod.sh status

# Verificar salud del sistema
./deploy-prod.sh health

# Ver logs
./deploy-prod.sh logs
```

## 🛠️ Comandos Disponibles

### Scripts de Despliegue

```bash
# Inicializar entorno
./init-docker-prod.sh

# Despliegue completo
./deploy-prod.sh deploy

# Solo construir imágenes
./deploy-prod.sh build

# Solo iniciar servicios
./deploy-prod.sh start

# Ver estado
./deploy-prod.sh status

# Ver logs
./deploy-prod.sh logs

# Verificar salud
./deploy-prod.sh health

# Detener servicios
./deploy-prod.sh stop

# Limpiar recursos
./deploy-prod.sh cleanup
```

### Makefile

```bash
# Inicializar producción
make prod-init

# Despliegue completo
make prod-deploy

# Construcción
make prod-build

# Iniciar/Detener
make prod-start
make prod-stop

# Estado y logs
make prod-status
make prod-logs

# Desarrollo
make dev-up
make dev-down
make dev-logs

# Comandos rápidos
make prod-quick    # Build + Start + Health check
make dev-quick     # Development setup
```

## ⚙️ Configuración de Variables de Entorno

### Variables Principales

```bash
# Base de Datos
DB_USER=postgres
DB_PASSWORD=tu_password_seguro
DB_PORT=5432

# Redis
REDIS_PASSWORD=tu_password_redis_seguro
REDIS_PORT=6379

# Aplicación
ENVIRONMENT=production
LOG_LEVEL=INFO
API_WORKERS=4

# Puertos
BACKEND_PORT=8000
HTTP_PORT=80
HTTPS_PORT=443

# Seguridad
SECRET_KEY=tu_clave_secreta_super_segura
ALLOWED_HOSTS=localhost,127.0.0.1,tu-dominio.com
```

### APIs Externas (Opcional)

```bash
NEWSAPI_KEY=tu_newsapi_key
GUARDIAN_API_KEY=tu_guardian_key
NYTIMES_API_KEY=tu_nytimes_key
OPENAI_API_KEY=tu_openai_key
```

## 🔧 Configuración Avanzada

### Escalado de Servicios

```bash
# Escalar workers de Celery
docker-compose -f docker-compose.prod.yml up -d --scale celery_worker=4

# Verificar contenedores
docker-compose -f docker-compose.prod.yml ps
```

### Monitoreo de Recursos

```bash
# Ver uso de recursos
docker stats

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# Ver logs específicos
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Backup y Restore

```bash
# Backup de PostgreSQL
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres ai_news_db > backup.sql

# Backup de Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli BGSAVE
docker cp ai_news_redis_prod:/data/dump.rdb ./backup.rdb

# Restore de PostgreSQL
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres ai_news_db < backup.sql
```

## 🔒 Seguridad

### Headers de Seguridad
- X-Frame-Options: SAMEORIGIN
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin

### Rate Limiting
- API endpoints: 10 requests/second
- Auth endpoints: 1 request/second
- Nginx: Protección DDoS básica

### Usuarios No-Root
- Todos los contenedores ejecutan con usuarios no-root
- Permisos de archivos optimizados
- Directorios de datos con permisos controlados

## 📊 Monitoreo y Logs

### Ubicación de Logs

```
data/logs/
├── backend/
│   └── app.log              # Logs de la aplicación
├── nginx/
│   ├── access.log           # Logs de acceso
│   └── error.log            # Logs de errores
└── celery/
    ├── worker.log           # Logs de Celery workers
    └── beat.log             # Logs de Celery beat
```

### Health Checks

- **Backend**: `http://localhost:8000/health`
- **Frontend**: `http://localhost/health`
- **Database**: Verificación automática con pg_isready
- **Redis**: Verificación automática con redis-cli ping

### Configuración de Logs

```yaml
logging:
  driver: "json-file"
  options:
    max-size: "20m"
    max-file: "5"
```

## 🚦 Entorno de Desarrollo

### Inicio Rápido

```bash
# Desarrollo completo
make dev-up

# Solo backend
make dev-backend

# Solo frontend  
make dev-frontend

# Ver logs de desarrollo
make dev-logs
```

### Diferencias con Producción

- Hot reload habilitado
- Logs más detallados (DEBUG level)
- Puertos diferentes (8001, 3001)
- Sin HTTPS
- Variables de desarrollo
- Volúmenes montados para desarrollo

## 🛡️ Troubleshooting

### Problemas Comunes

#### Servicios no inician
```bash
# Verificar logs
./deploy-prod.sh logs

# Verificar health checks
./deploy-prod.sh health

# Reiniciar servicios
./deploy-prod.sh restart
```

#### Problemas de Base de Datos
```bash
# Verificar conexión
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d ai_news_db

# Verificar migraciones
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

#### Problemas de Memoria
```bash
# Ver uso de memoria
docker stats --no-stream

# Ajustar límites en docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 1G
```

### Comandos de Diagnóstico

```bash
# Estado general
make prod-status

# Logs recientes
make prod-logs

# Verificar conectividad
curl -f http://localhost/health

# Verificar base de datos
docker-compose -f docker-compose.prod.yml exec postgres pg_isready

# Verificar Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

## 📈 Rendimiento

### Optimizaciones Incluidas

- **Nginx**: Gzip compression, keep-alive, buffer optimization
- **PostgreSQL**: Configuración optimizada para producción
- **Redis**: Configuración de memoria optimizada
- **Docker**: Multi-stage builds para imágenes más pequeñas
- **Caching**: Headers de cache configurados

### Métricas de Rendimiento

- **Backend**: Workers configurables (default: 4)
- **Celery**: Workers escalables (default: 2, escalable)
- **Nginx**: Worker processes auto-scaling
- **Database**: Conexiones optimizadas

## 🔄 Actualizaciones

### Actualizar Aplicación

```bash
# Detener servicios
./deploy-prod.sh stop

# Construir nuevas imágenes
./deploy-prod.sh build

# Iniciar servicios
./deploy-prod.sh start

# Verificar
./deploy-prod.sh health
```

### Actualizar Base de Datos

```bash
# Ejecutar migraciones
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
```

## 📞 Soporte

Para problemas específicos:

1. Revisar logs: `./deploy-prod.sh logs`
2. Verificar health: `./deploy-prod.sh health`
3. Consultar troubleshooting section
4. Verificar configuración de variables de entorno

---

**Nota**: Esta configuración está optimizada para producción. Para desarrollo, usar `docker-compose.override.yml` o los comandos de desarrollo del Makefile.