# AI News Aggregator - Sistema de Monitoring y Alertas

Este directorio contiene un sistema completo de monitoring y alertas para el proyecto AI News Aggregator, incluyendo métricas, visualización, alertas, logging y verificaciones de salud.

## 🏗️ Arquitectura del Sistema de Monitoring

El sistema está compuesto por:

- **Prometheus** - Recolección y almacenamiento de métricas
- **Grafana** - Visualización y dashboards
- **AlertManager** - Gestión y enrutamiento de alertas
- **ELK Stack** (Elasticsearch, Logstash, Kibana) - Logging centralizado
- **Uptime Kuma** - Monitoring de uptime y status page
- **Health Check System** - Verificaciones automatizadas de salud

## 📁 Estructura de Directorios

```
monitoring/
├── prometheus/           # Configuración de Prometheus
│   ├── prometheus.yml    # Configuración principal
│   └── blackbox.yml      # Configuración blackbox exporter
├── grafana/              # Dashboards y configuración de Grafana
│   ├── dashboards/       # Dashboards JSON
│   └── provisioning/     # Configuración automática
├── alertmanager/         # Configuración de alertas
│   └── alertmanager.yml  # Reglas de alertas y notificaciones
├── elk/                  # Stack de logging ELK
│   ├── logstash/         # Configuración de Logstash
│   ├── config/           # Configuraciones adicionales
│   └── ai-news-logs-template.json  # Template de Elasticsearch
├── uptime/               # Sistema de uptime monitoring
│   └── setup_monitors.sh # Script de configuración automática
├── health/               # Sistema de health checks
│   ├── health_checker.py # Verificaciones de salud principales
│   ├── health_cron.py    # Scheduler de health checks
│   ├── Dockerfile        # Contenedor para health checks
│   └── requirements.txt  # Dependencias Python
├── config/               # Configuraciones adicionales
├── docker-compose.monitoring.yml  # Orquestación de servicios
└── setup_monitoring.sh   # Script de configuración completa
```

## 🚀 Inicio Rápido

### 1. Configuración Automática

```bash
# Ejecutar setup completo
chmod +x monitoring/setup_monitoring.sh
./monitoring/setup_monitoring.sh
```

Este script realizará:
- Verificación de dependencias
- Construcción de imágenes Docker
- Inicio de todos los servicios
- Configuración de dashboards
- Configuración de monitors en Uptime Kuma

### 2. Inicio Manual de Servicios

```bash
# Iniciar servicios de monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml up -d

# Ver logs
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f [servicio]

# Ver estado
docker-compose -f monitoring/docker-compose.monitoring.yml ps
```

## 📊 Servicios y Puertos

| Servicio | Puerto | Descripción |
|----------|--------|-------------|
| **Prometheus** | 9090 | Métricas y monitoring |
| **Grafana** | 3000 | Dashboards y visualización |
| **AlertManager** | 9093 | Gestión de alertas |
| **Elasticsearch** | 9200 | Motor de búsqueda para logs |
| **Kibana** | 5601 | Visualización de logs |
| **Uptime Kuma** | 3001 | Uptime monitoring |
| **cAdvisor** | 8080 | Métricas de contenedores |
| **Node Exporter** | 9100 | Métricas del sistema |
| **Blackbox Exporter** | 9115 | Monitoring blackbox |

## 🎯 Dashboards Disponibles

### 1. System Overview
- **URL**: http://localhost:3000/d/ai-news-overview
- **Descripción**: Vista general del sistema con métricas principales
- **Métricas**: Status de servicios, latencia, errores, uso de recursos

### 2. Backend API Dashboard
- **URL**: http://localhost:3000/d/ai-news-backend
- **Descripción**: Métricas específicas del backend API
- **Métricas**: Request rate, response time, error rate, status de Celery

### 3. Uptime & Availability
- **URL**: http://localhost:3000/d/ai-news-uptime
- **Descripción**: Estado de uptime y disponibilidad de servicios
- **Métricas**: Status de servicios, response times, probe failures

## 🚨 Sistema de Alertas

### Configuración de Alertas

Las alertas se configuran en `alertmanager/alertmanager.yml` y `prometheus/alert_rules.yml`.

### Tipos de Alertas

#### Críticas
- **BackendAPIUnreachable**: Backend API no disponible
- **DatabaseUnreachable**: Base de datos no disponible
- **RedisUnreachable**: Redis no disponible
- **HighServerErrorRate**: Alta tasa de errores 5xx

#### Advertencias
- **HighAPILatency**: Alta latencia en API
- **HighMemoryUsage**: Alto uso de memoria
- **DiskSpaceLow**: Espacio en disco bajo
- **CeleryTaskBacklog**: Muchas tareas en cola

#### Negocio
- **NoNewArticles**: No hay noticias nuevas
- **AIPipelineErrors**: Errores en pipeline de AI
- **SearchFailures**: Búsquedas fallando

### Canales de Notificación

#### Email
Configurar en `alertmanager.yml`:
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_auth_username: 'your-email@gmail.com'
  smtp_auth_password: 'your-password'
```

#### Slack
```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    channel: '#alerts'
```

#### Discord
```yaml
discord_configs:
  - webhook_url: 'https://discord.com/api/webhooks/YOUR/DISCORD/WEBHOOK'
```

## 📋 Sistema de Health Checks

### Verificación Manual

```bash
# Ejecutar health check manual
docker-compose -f monitoring/docker-compose.monitoring.yml exec health-checker python health_checker.py

# Ver logs de health checks
docker-compose -f monitoring/docker-compose.monitoring.yml logs health-checker
```

### Verificaciones Automáticas

El sistema ejecuta verificaciones automáticamente cada:
- 5 minutos: Verificación rápida de servicios
- 1 hora: Verificación completa del sistema
- 2 AM diario: Limpieza y mantenimiento

### Servicios Verificados

- **HTTP Endpoints**: /health, /api/v1/health, /metrics
- **Database**: PostgreSQL (conexión y consultas)
- **Cache**: Redis (ping y operaciones)
- **Monitoring Stack**: Prometheus, Grafana, AlertManager
- **Infrastructure**: cAdvisor, Node Exporter, Elasticsearch
- **Containers**: Estado de Docker containers
- **Processes**: Celery workers, Gunicorn

## 📈 Métricas Recolectadas

### Aplicación
- Request rate y latencia
- Response time percentiles (p50, p95, p99)
- Error rates por código de estado
- Status de tareas Celery
- Longitud de cola de Redis

### Sistema
- Uso de CPU y memoria
- Espacio en disco
- Red y tráfico de red
- Estadísticas de contenedores

### Base de Datos
- Conexiones activas
- Latencia de queries
- Estadísticas de performance

## 🔍 Logging Centralizado

### Configuración de Logstash

Los logs se procesan automáticamente:
- **Backend logs**: Parseo de logs de FastAPI
- **Celery logs**: Tracking de tareas
- **Container logs**: Logs de Docker
- **Error logs**: Detección automática de errores

### Índices de Elasticsearch

- `ai-news-logs-YYYY.MM.DD`: Logs generales
- `ai-news-backend-YYYY.MM.DD`: Logs del backend
- `ai-news-celery-YYYY.MM.DD`: Logs de Celery
- `ai-news-containers-YYYY.MM.DD`: Logs de contenedores

### Búsqueda de Logs

Acceder a Kibana en http://localhost:5601 para:
- Buscar logs específicos
- Crear visualizaciones
- Configurar alertas de logging

## 🏃‍♂️ Uptime Monitoring

### Configuración Automática

El script `uptime/setup_monitors.sh` configura automáticamente:

- **API Endpoints**: /health, /api/v1/health, /metrics
- **Frontend**: Aplicación web
- **Database**: PostgreSQL (puerto 5432)
- **Cache**: Redis (puerto 6379)
- **Monitoring**: Prometheus, Grafana, AlertManager

### Verificaciones Adicionales

Se pueden agregar más monitors manualmente en Uptime Kuma:
- **URL**: http://localhost:3001
- **Configurar** → **Add New Monitor**
- **Tipos**: HTTP, TCP Port, Keyword, DNS

## 🛠️ Comandos Útiles

### Verificar Estado
```bash
# Estado de contenedores
docker-compose -f monitoring/docker-compose.monitoring.yml ps

# Logs de un servicio específico
docker-compose -f monitoring/docker-compose.monitoring.yml logs -f [servicio]

# Recursos del sistema
docker stats
```

### Reiniciar Servicios
```bash
# Reiniciar un servicio específico
docker-compose -f monitoring/docker-compose.monitoring.yml restart [servicio]

# Reiniciar todo
docker-compose -f monitoring/docker-compose.monitoring.yml down && up -d
```

### Gestión de Datos
```bash
# Limpiar datos de Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml exec prometheus rm -rf /prometheus/*

# Backup de Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml exec grafana tar czf /tmp/grafana_backup.tar.gz /var/lib/grafana

# Restaurar Grafana
docker-compose -f monitoring/docker-compose.monitoring.yml exec grafana tar xzf /tmp/grafana_backup.tar.gz -C /
```

### Health Checks
```bash
# Ejecutar health check individual
python monitoring/health/health_checker.py

# Ver health check logs
tail -f /var/log/health_checks.log

# Ver últimas 10 verificaciones
docker-compose -f monitoring/docker-compose.monitoring.yml exec health-checker ls -la /var/log/
```

## 🔧 Configuración Avanzada

### Personalizar Alertas

Editar `prometheus/alert_rules.yml` para agregar nuevas alertas:

```yaml
- alert: CustomAlert
  expr: custom_metric > threshold
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Descripción de la alerta"
    description: "Detalles de la alerta"
```

### Agregar Métricas

Para agregar nuevas métricas al backend, crear endpoints en `app/main.py`:

```python
@app.get("/metrics")
async def metrics():
    return prometheus_client.generate_latest()
```

### Configurar Retention

En `prometheus/prometheus.yml` ajustar retención:

```yaml
storage.tsdb.retention.time=30d  # 30 días de retención
```

## 📞 Soporte y Troubleshooting

### Problemas Comunes

#### Servicios no inician
```bash
# Verificar logs
docker-compose -f monitoring/docker-compose.monitoring.yml logs

# Verificar puertos en uso
netstat -tlnp | grep :port
```

#### Métricas no aparecen
```bash
# Verificar targets en Prometheus
curl http://localhost:9090/api/v1/targets

# Verificar configuración
docker-compose -f monitoring/docker-compose.monitoring.yml exec prometheus cat /etc/prometheus/prometheus.yml
```

#### Alertas no se envían
```bash
# Verificar configuración de AlertManager
curl http://localhost:9093/api/v1/status

# Ver configuración de alertas
docker-compose -f monitoring/docker-compose.monitoring.yml exec alertmanager cat /etc/alertmanager/alertmanager.yml
```

### Logs de Sistema

- **Prometheus**: `/var/log/prometheus.log`
- **Grafana**: `/var/log/grafana.log`
- **Health Checks**: `/var/log/health_checks.log`
- **Monitoring Setup**: `/var/log/monitoring_setup.log`

### URLs de Diagnóstico

- **Prometheus targets**: http://localhost:9090/targets
- **Prometheus rules**: http://localhost:9090/rules
- **AlertManager status**: http://localhost:9093/api/v1/status
- **Elasticsearch health**: http://localhost:9200/_cluster/health

## 🚀 Roadmap

### Mejoras Futuras

- [ ] Integración con Sentry para error tracking
- [ ] Dashboard específico para Celery workers
- [ ] Métricas de business (artículos procesados, usuarios activos)
- [ ] Alertas predictivas con machine learning
- [ ] Integración con Slack/Discord para alertas en tiempo real
- [ ] Dashboard móvil responsive
- [ ] Backup automático de configuraciones
- [ ] Testing automatizado de alertas

## 🤝 Contribuciones

Para contribuir al sistema de monitoring:

1. Agregar nuevos dashboards en `grafana/dashboards/`
2. Crear nuevas alertas en `prometheus/alert_rules.yml`
3. Extender health checks en `health/health_checker.py`
4. Actualizar documentación

---

**Nota**: Este sistema de monitoring está diseñado para producción. Asegúrate de configurar adecuadamente las credenciales y endpoints antes del despliegue.