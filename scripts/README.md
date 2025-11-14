# Scripts de Deployment y Rollback - AI News Aggregator

Este directorio contiene un sistema completo de scripts para el deployment, mantenimiento y operaciones del AI News Aggregator.

## 📋 Scripts Disponibles

### 🚀 Scripts Principales

| Script | Descripción | Uso Principal |
|--------|-------------|---------------|
| [`ops.sh`](ops.sh) | Script maestro de operaciones | Punto de entrada centralizado |
| [`logger.sh`](logger.sh) | Sistema de logging centralizado | Importar en todos los scripts |
| [`deploy.sh`](deploy.sh) | Deployment automatizado | Deploy completo con verificaciones |
| [`rollback.sh`](rollback.sh) | Rollback rápido | Revertir a versiones anteriores |
| [`health-check.sh`](health-check.sh) | Verificaciones post-deploy | Validar estado del sistema |

### 🔧 Scripts Especializados

| Script | Descripción | Uso Principal |
|--------|-------------|---------------|
| [`migrate-database.sh`](migrate-database.sh) | Migraciones de BD | Gestión de esquemas |
| [`scale-services.sh`](scale-services.sh) | Auto-scaling | Escalado dinámico |
| [`backup-restore.sh`](backup-restore.sh) | Gestión de backups | Respaldos y restauración |
| [`maintenance.sh`](maintenance.sh) | Modo mantenimiento | Páginas de mantenimiento |
| [`update-certificates.sh`](update-certificates.sh) | Certificados SSL | Renovación SSL |

## 🚀 Uso Rápido

### Script Maestro - ops.sh

```bash
# Ver ayuda completa
./ops.sh help

# Deploy completo
./ops.sh deploy

# Verificación de salud
./ops.sh health

# Rollback al último backup
./ops.sh rollback

# Activar modo mantenimiento
./ops.sh maintenance on

# Crear backup
./ops.sh backup

# Ver estado del sistema
./ops.sh status

# Monitoreo en tiempo real
./ops.sh monitor
```

### Comandos Específicos

```bash
# Deployment con opciones
./ops.sh deploy --dry-run          # Simulación
./ops.sh deploy --backend-only     # Solo backend

# Health checks específicos
./ops.sh health services           # Solo servicios
./ops.sh health endpoints          # Solo endpoints
./ops.sh health --json            # Salida JSON

# Escalado de servicios
./ops.sh scale auto               # Auto-scaling
./ops.sh scale up celery_worker 2 # Escalar +2
./ops.sh scale down backend 1     # Escalar -1

# Gestión de mantenimiento
./ops.sh maintenance schedule "02:00" "1h"    # Programar
./ops.sh maintenance off             # Desactivar

# Certificados SSL
./ops.sh certificates renew         # Renovar
./ops.sh certificates status        # Estado
```

## 🔧 Instalación y Configuración

### Prerrequisitos

```bash
# Herramientas requeridas
- Docker & Docker Compose
- OpenSSL (para certificados)
- Certbot (opcional, para SSL)
- jq (opcional, para JSON)
- netcat (nc) para verificaciones
```

### Configuración Inicial

```bash
# 1. Configurar variables de entorno
cp .env.example .env
vim .env

# 2. Verificar configuración
./ops.sh config

# 3. Probar scripts
./ops.sh health

# 4. Crear backup inicial
./ops.sh backup
```

### Variables de Entorno

```bash
# Entorno de deployment
export DEPLOY_ENV=production

# Servidor web
export WEB_SERVER=nginx

# Configuración de backup
export BACKUP_ENABLED=true
export RETENTION_DAYS=30

# SSL/TLS
export CERT_RENEWAL_THRESHOLD=30
export EMAIL=admin@example.com

# Logging
export LOG_LEVEL=INFO
export LOG_DIR=./logs

# Auto-rollback
export AUTO_ROLLBACK=true
```

## 📊 Workflows Principales

### 1. Workflow de Deployment Completo

```bash
# Pre-deployment
./ops.sh status                    # Verificar estado
./ops.sh config                    # Verificar configuración
./ops.sh backup                    # Backup pre-deploy

# Deployment
./ops.sh deploy                    # Deploy completo
./ops.sh health                    # Verificar salud
./ops.sh migrate                   # Ejecutar migraciones si necesario

# Post-deployment
./ops.sh scale status             # Verificar escalado
./ops.sh certificates status       # Verificar SSL
./ops.sh monitor                   # Monitoreo inicial
```

### 2. Workflow de Mantenimiento

```bash
# Preparación
./ops.sh backup                   # Backup completo
./ops.sh maintenance schedule "02:00" "1h" "Actualización"

# Activar mantenimiento
./ops.sh maintenance on "Mantenimiento" "Actualizando sistema" "30 min"

# Realizar trabajos
./ops.sh migrate
./ops.sh deploy --backend-only
./ops.sh health

# Desactivar
./ops.sh maintenance off
./ops.sh health
```

### 3. Workflow de Rollback

```bash
# Identificar problema
./ops.sh health

# Listar backups disponibles
./ops.sh rollback --list

# Ejecutar rollback
./ops.sh rollback 20241106_041606

# Verificar
./ops.sh health
./ops.sh status
```

### 4. Workflow de Escalado

```bash
# Ver estado actual
./ops.sh scale status
./ops.sh scale metrics

# Escalado manual
./ops.sh scale up celery_worker 2
./ops.sh scale set frontend 3

# Auto-scaling
./ops.sh scale auto

# Monitoreo
./ops.sh scale test up
./ops.sh monitor
```

## 🔐 Gestión de Certificados SSL

### Let's Encrypt (Producción)

```bash
# Configurar dominios
export DOMAINS="ai-news.example.com,www.ai-news.example.com"
export EMAIL="admin@ai-news.example.com"

# Instalar certbot
apt-get install certbot

# Obtener certificados
./ops.sh certificates renew

# Verificar estado
./ops.sh certificates status
```

### Certificados Auto-firmados (Desarrollo)

```bash
# Generar para desarrollo
./ops.sh certificates generate development

# Para staging
./ops.sh certificates generate staging

# Verificar
./ops.sh certificates check
```

## 💾 Gestión de Backups

### Tipos de Backup

```bash
# Backup completo
./ops.sh backup

# Solo base de datos
./ops.sh backup database

# Solo código
./ops.sh backup code

# Solo configuraciones
./ops.sh backup configs
```

### Restauración

```bash
# Listar backups
./ops.sh backup --list

# Restaurar backup específico
./ops.sh backup --restore backup_20241106_041606.tar.gz

# Verificar después de restaurar
./ops.sh health
```

## 🔧 Monitoreo y Logs

### Ver Logs

```bash
# Logs de servicio específico
./ops.sh logs backend
./ops.sh logs frontend
./ops.sh logs database

# Logs de todos los servicios
./ops.sh logs all
```

### Monitoreo en Tiempo Real

```bash
# Monitor continuo
./ops.sh monitor

# Health checks específicos
./ops.sh health services
./ops.sh health performance
./ops.sh health resources
```

## 📈 Configuración de Auto-Scaling

### Configuración Personalizada

```bash
# Crear archivo de configuración
cat > scaling-config.json << EOF
{
    "services": {
        "celery_worker": {
            "min": 1,
            "max": 10,
            "step": 2,
            "target_cpu": 70,
            "target_memory": 80
        },
        "backend": {
            "min": 1,
            "max": 5,
            "step": 1,
            "target_cpu": 75,
            "target_memory": 85
        }
    }
}
EOF
```

### Uso del Auto-Scaling

```bash
# Activar auto-scaling
./ops.sh scale auto

# Configuración manual
./ops.sh scale set celery_worker 5

# Ver métricas
./ops.sh scale metrics
```

## 🏥 Health Checks

### Tipos de Verificación

```bash
# Verificación completa
./ops.sh health all

# Verificaciones específicas
./ops.sh health services      # Servicios Docker
./ops.sh health endpoints     # Endpoints HTTP
./ops.sh health database      # Base de datos
./ops.sh health cache         # Redis
./ops.sh health performance   # Rendimiento
./ops.sh health resources     # Recursos del sistema
./ops.sh health external      # APIs externas
```

### Formatos de Salida

```bash
# Consola (default)
./ops.sh health

# JSON
./ops.sh health --json

# HTML
./ops.sh health --html
```

## 🔄 Migraciones de Base de Datos

### Gestión de Migraciones

```bash
# Ejecutar migraciones pendientes
./ops.sh migrate

# Crear nueva migración
./ops.sh migrate --create "add_user_preferences"

# Ver estado
./ops.sh migrate --status

# Rollback
./ops.sh migrate --rollback

# Validar migraciones
./ops.sh migrate --validate
```

### Estructura de Migraciones

```
database/migrations/
├── 001_add_users_table.sql
├── 002_add_articles_table.sql
├── 003_add_analytics_table.sql
└── rollback/
    ├── 001_rollback_add_users.sql
    ├── 002_rollback_add_articles.sql
    └── 003_rollback_add_analytics.sql
```

## 🛠️ Scripts Individuales

Todos los scripts pueden ejecutarse independientemente:

```bash
# Deployment directo
bash scripts/deploy.sh deploy

# Health check directo
bash scripts/health-check.sh all

# Backup directo
bash scripts/backup-restore.sh create full

# Rollback directo
bash scripts/rollback.sh latest

# Verificar ayuda individual
bash scripts/logger.sh --help
bash scripts/deploy.sh --help
```

## 📝 Logging y Auditoría

### Sistema de Logging Centralizado

```bash
# Los logs se almacenan en:
./logs/
├── 2024-11-06.log           # Logs diarios
├── 2024-11-06.log.1.gz      # Logs rotados
├── deployment-20241106.log  # Logs de deployment
└── health-check-20241106.log # Logs de health checks
```

### Métricas y Métricas

```bash
# Las métricas se registran automáticamente:
- Tiempo de deployment
- Tiempo de health check
- Número de réplicas escaladas
- Tamaño de backups
- Duración de migraciones
```

## 🚨 Troubleshooting

### Problemas Comunes

```bash
# 1. Contenedor no inicia
./ops.sh logs <servicio>
docker-compose restart <servicio>

# 2. Problemas de base de datos
./ops.sh health database
./ops.sh migrate --rollback

# 3. Certificados SSL expirados
./ops.sh certificates renew --force

# 4. Alto uso de recursos
./ops.sh scale down <servicio> 1
./ops.sh health performance

# 5. Servicios no responden
./ops.sh health endpoints
./ops.sh restart
```

### Logs de Debug

```bash
# Habilitar debug logging
export LOG_LEVEL=DEBUG
./ops.sh health

# Ver logs específicos
tail -f ./logs/$(date +%Y-%m-%d).log
```

## 🔒 Seguridad

### Mejores Prácticas

```bash
# 1. Nunca exponer credenciales en scripts
export DATABASE_PASSWORD=$(cat /secure/path/password)

# 2. Usar variables de entorno para secretos
export API_KEY="secret_key_here"

# 3. Backup antes de operaciones críticas
./ops.sh backup

# 4. Verificar integridad post-operación
./ops.sh health

# 5. Logs de auditoría
./ops.sh deploy | tee ./logs/deployment-$(date +%Y%m%d).log
```

## 📚 Documentación Adicional

### Recursos

- `README.md` - Documentación principal
- `docs/` - Documentación técnica
- `scripts/*.sh --help` - Ayuda específica de cada script
- `.env.example` - Plantilla de configuración

### Soporte

- **Email**: devops@company.com
- **Slack**: #ai-news-devops
- **Issues**: GitHub Issues
- **Wiki**: Documentación interna

## 🎯 Roadmap

### Funcionalidades Futuras

- [ ] Integración con Kubernetes
- [ ] Métricas con Prometheus/Grafana
- [ ] Alertas automáticas
- [ ] Deployment blue-green
- [ ] Circuit breakers
- [ ] Load testing automático
- [ ] Integración con GitOps
- [ ] Dashboard web de operaciones

### Contribuciones

Para contribuir con nuevos scripts o mejoras:

1. Fork el repositorio
2. Crear una rama feature
3. Seguir el patrón de logging
4. Incluir tests
5. Documentar en README
6. Crear PR

---

**Última actualización**: Noviembre 2024
**Versión**: 1.0.0
**Mantenido por**: Equipo DevOps