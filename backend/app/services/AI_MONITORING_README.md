# Sistema de Monitoreo y Gestión de AI Tasks

## Descripción General

El **Sistema de Monitoreo y Gestión de AI Tasks** es una solución completa para trackear, monitorear y analizar el rendimiento de tareas de inteligencia artificial en tiempo real. Proporciona visibilidad completa sobre costos, performance, errores y patrones operativos.

## Características Principales

### 🏗️ Componentes del Sistema

1. **TaskMonitor** - Seguimiento del estado de tareas AI
2. **PerformanceMonitor** - Métricas de throughput y latencia
3. **CostMonitor** - Tracking detallado de costos OpenAI
4. **ErrorAnalyzer** - Análisis de fallos y patrones de error
5. **AlertManager** - Sistema de alertas y notificaciones

### 📊 Funcionalidades Clave

- **Monitoreo en Tiempo Real**: Seguimiento continuo de todas las tareas AI
- **Análisis de Costos**: Tracking detallado de gastos por modelo, tipo y periodo
- **Métricas de Performance**: Throughput, latencia, tasa de éxito
- **Detección de Patrones**: Identificación automática de errores recurrentes
- **Sistema de Alertas**: Notificaciones configurables por severidad
- **Dashboard API**: Endpoints REST para visualización en tiempo real
- **Reporting Automático**: Generación de reportes periódicos
- **Logging Especializado**: Logs estructurados para análisis post-mortem

## Instalación y Configuración

### Dependencias

El sistema utiliza las librerías estándar de Python y FastAPI. No requiere dependencias adicionales específicas.

### Configuración de Variables de Entorno

```bash
# Configuración básica
OPENAI_API_KEY=your_openai_api_key

# Configuración de monitoreo AI
AI_MONITORING_ENABLED=true
AI_MONITORING_RETENTION_DAYS=30
AI_MONITORING_MAX_HISTORY=10000

# Umbrales de costo
AI_COST_DAILY_WARNING=10.0
AI_COST_DAILY_CRITICAL=25.0
AI_COST_TASK_WARNING=0.5
AI_COST_TASK_CRITICAL=1.0

# Umbrales de performance
AI_LATENCY_WARNING=30.0
AI_LATENCY_CRITICAL=60.0
AI_ERROR_RATE_WARNING=10.0
AI_ERROR_RATE_CRITICAL=20.0

# Configuración de alertas
AI_MONITORING_ALERT_EMAIL=admin@company.com
AI_MONITORING_SLACK_WEBHOOK=https://hooks.slack.com/services/...
AI_MONITORING_DASHBOARD_ENABLED=true
```

## Uso Básico

### 1. Uso con Decorators (Recomendado)

```python
from app.services.ai_monitor_integration import monitor_ai_task

@monitor_ai_task(task_type="news_analysis", model="gpt-3.5-turbo")
async def analyze_news_articles(articles):
    """
    Analizar artículos de noticias - automáticamente monitoreado
    """
    # Tu código de AI aquí
    result = await openai.ChatCompletion.acreate(...)
    return result
```

### 2. Uso con Context Manager

```python
from app.services.ai_monitor_integration import monitor_context

async def process_data():
    with monitor_context(task_type="data_processing", model="gpt-4") as ctx:
        # Tu código aquí
        result = process_with_ai()
        
        # Establecer costo manualmente si es necesario
        ctx.set_cost(0.15, 500)
        
        return result
```

### 3. Integración con Servicios Existentes

```python
from app.services.ai_monitor_integration import integrate_with_existing_service

class MyNewsService:
    async def get_news(self):
        # Tu lógica de servicio
        return news_data

# Integrar monitoreo automáticamente
service = MyNewsService()
integrate_with_existing_service(
    service, 
    "news_service", 
    methods_to_monitor=["get_news"]
)
```

## API Endpoints

### Dashboard General

```
GET /api/v1/monitor/dashboard/summary
```
Resumen completo del sistema: tareas activas, métricas de performance, costos, alertas.

```
GET /api/v1/monitor/dashboard/performance?hours=24
```
Métricas de performance en las últimas N horas.

```
GET /api/v1/monitor/dashboard/costs?days=7
```
Análisis de costos por periodo.

```
GET /api/v1/monitor/dashboard/errors?days=7
```
Reporte de errores y patrones detectados.

### Gestión de Tareas

```
GET /api/v1/monitor/tasks/active
```
Listar todas las tareas activas.

```
GET /api/v1/monitor/tasks/history?limit=100&status=completed
```
Historial de tareas con filtros opcionales.

```
GET /api/v1/monitor/tasks/{task_id}
```
Status detallado de una tarea específica.

### Alertas

```
GET /api/v1/monitor/alerts/active?severity=warning
```
Alertas activas con filtro opcional por severidad.

```
POST /api/v1/monitor/alerts/{alert_id}/resolve
```
Resolver una alerta activa.

### Reportes

```
GET /api/v1/monitor/reports/export?format=json&hours=24
```
Exportar métricas en formato JSON o CSV.

```
GET /api/v1/monitor/reports/cost-forecast
```
Predicción de costos mensuales.

### Monitoreo en Tiempo Real

```
GET /api/v1/monitor/realtime/status
```
Status general del sistema en tiempo real.

```
GET /api/v1/monitor/realtime/metrics
```
Métricas detalladas actualizadas continuamente.

## Métricas y Análisis

### Métricas de Performance
- **Throughput**: Tareas procesadas por minuto
- **Latencia**: Tiempo promedio, mediano, P95, P99
- **Tasa de Éxito**: Porcentaje de tareas completadas vs fallidas
- **Utilización de Recursos**: Costos y tokens por hora

### Métricas de Costo
- **Costo Total**: Acumulado por día, semana, mes
- **Breakdown por Modelo**: Distribución de gastos
- **Breakdown por Tipo**: Costos por categoría de tarea
- **Predicción**: Estimación de costos mensuales

### Análisis de Errores
- **Patrones Identificados**: Errores recurrentes con frecuencia
- **Categorización Automática**: Timeout, rate limit, billing, etc.
- **Recomendaciones**: Acciones sugeridas para resolver problemas
- **Análisis de Severidad**: Impacto y prioridad de cada patrón

## Configuración de Alertas

### Tipos de Alertas
- **INFO**: Información general del sistema
- **WARNING**: Advertencias de rendimiento o costo
- **ERROR**: Errores que requieren atención
- **CRITICAL**: Problemas críticos que necesitan acción inmediata

### Handlers Personalizados

```python
from app.services.ai_monitor import ai_monitor, AlertSeverity

def custom_alert_handler(alert):
    """Handler personalizado para alertas críticas"""
    if alert.severity == AlertSeverity.CRITICAL:
        # Enviar email urgente
        send_urgent_email(alert.title, alert.message)
        
        # Notificar via Slack
        send_slack_message(f"🚨 {alert.title}: {alert.message}")

# Registrar handler
ai_monitor.alert_manager.register_handler(
    AlertSeverity.CRITICAL, 
    custom_alert_handler
)
```

## Logging y Análisis

### Logs Estructurados

El sistema genera logs especializados en formato JSON:

```json
{
  "timestamp": "2025-11-06T02:47:53Z",
  "level": "INFO",
  "task_id": "news_analysis_1640995200000",
  "task_type": "news_analysis",
  "task_status": "completed",
  "duration": 3.45,
  "cost": 0.0234,
  "tokens_used": 467,
  "model": "gpt-3.5-turbo",
  "metadata": {
    "function": "analyze_news_articles",
    "articles_count": 5
  }
}
```

### Archivos de Log
- `logs/ai_tasks.log` - Log general de tareas
- `logs/ai_costs.log` - Log específico de costos
- `logs/ai_alerts.log` - Log de alertas
- `logs/ai_errors.log` - Log de errores
- `logs/ai_performance.log` - Log de métricas de performance

### Análisis Post-Mortem

```python
from app.core.ai_logging import get_recent_errors, get_task_summary_from_logs

# Obtener errores recientes
recent_errors = get_recent_errors(hours=24)

# Obtener resumen de tarea específica
task_summary = get_task_summary_from_logs("task_id_123")
```

## Ejemplos de Uso Avanzado

### Batch Processing con Monitoreo

```python
from app.services.ai_monitor_integration import monitor_batch_processing

async def process_articles_batch(articles):
    def analyze_article(article):
        # Procesamiento individual
        return ai_analysis(article)
    
    results = await monitor_batch_processing(
        items=articles,
        process_func=analyze_article,
        batch_size=10,
        task_type="batch_article_analysis"
    )
    
    return results
```

### Middleware de FastAPI

```python
from app.services.ai_monitor_integration import create_monitoring_middleware

app.add_middleware(create_monitoring_middleware())
```

### Analytics Detallado

```python
from app.services.ai_monitor_integration import get_task_analytics

# Obtener analytics para tipo específico
analytics = get_task_analytics("news_analysis", days=7)

print(f"Tasa de éxito: {analytics['success_rate']:.2f}%")
print(f"Costo promedio: ${analytics['costs']['average_cost']:.4f}")
print(f"Duración media: {analytics['performance']['average_duration']:.2f}s")
```

## Integración con Servicios Existentes

### Servicios de Noticias

Los servicios existentes pueden ser fácilmente integrados:

```python
from app.services.news_service import NewsService
from app.services.ai_monitor_integration import integrate_with_existing_service

news_service = NewsService()
integrate_with_existing_service(news_service, "news_service")

# Ahora todas las llamadas se monitorean automáticamente
articles = await news_service.get_latest_news(limit=10)
```

### Celery Tasks

```python
from celery import Celery
from app.services.ai_monitor_integration import monitor_ai_task

app = Celery('news_tasks')

@monitor_ai_task(task_type="celery_news_analysis", model="gpt-3.5-turbo")
@app.task
def analyze_news_task(articles):
    # Tu lógica de análisis
    return analyzed_articles
```

## Monitoreo en Producción

### Métricas Clave a Vigilar
1. **Tasa de Error > 10%**: Indica problemas en la calidad de datos o configuración
2. **Latencia P95 > 30s**: Puede requerir optimización o scaling
3. **Costo Diario > Límite**: Revisar uso y implementar optimizaciones
4. **Tasa de Timeouts**: Posible problema de red o sobrecarga

### Alertas Recomendadas
- Errores críticos de API
- Costos anómalos en 24h
- Latencia sostenida > threshold
- Tasa de éxito < 85%

### Optimizaciones Sugeridas
- Implementar caching para requests similares
- Usar modelos más eficientes para tareas simples
- Implementar retry logic con backoff exponencial
- Configurar rate limiting adaptativo

## Solución de Problemas

### Problemas Comunes

**Q: Las métricas no se actualizan**
A: Verificar que `AI_MONITORING_ENABLED=true` y que el servicio esté corriendo.

**Q: Los logs no se generan**
A: Verificar permisos de escritura en el directorio `logs/` y configuración de logging.

**Q: Los endpoints del dashboard dan error 500**
A: Revisar logs del servidor y verificar que el AI monitor se inicializó correctamente.

**Q: Los costos no se calculan**
A: Verificar que las respuestas de OpenAI incluyan información de `usage` o implementar tracking manual.

### Debug y Troubleshooting

```python
# Verificar estado del sistema
dashboard = ai_monitor.get_dashboard_summary()
print(f"Status: {dashboard['overview']}")

# Revisar logs de errores
from app.core.ai_logging import get_recent_errors
errors = get_recent_errors(hours=1)
print(f"Recent errors: {len(errors)}")
```

## API Reference

### Métodos Principales

#### TaskMonitor
- `start_task(task_id, task_type, model, metadata)`
- `complete_task(task_id, status, tokens_used, cost, error_message)`
- `get_task_status(task_id)`
- `get_active_tasks()`
- `get_task_history(limit, status_filter)`

#### PerformanceMonitor
- `record_completion(metrics)`
- `calculate_throughput(minutes)`
- `calculate_latency_stats()`
- `calculate_success_rate()`
- `get_performance_metrics()`

#### CostMonitor
- `record_cost(task_id, cost, tokens_used, model, task_type)`
- `get_current_day_cost()`
- `get_cost_breakdown_by_model(days)`
- `get_cost_breakdown_by_type(days)`
- `predict_monthly_cost()`

#### ErrorAnalyzer
- `analyze_error(task_metrics)`
- `get_active_patterns()`
- `get_error_summary()`

#### AlertManager
- `create_alert(title, message, severity, metadata)`
- `resolve_alert(alert_id)`
- `get_active_alerts(severity_filter)`
- `register_handler(severity, handler)`

## Contribuir

Para contribuir al sistema:

1. Fork del repositorio
2. Crear branch para nueva feature
3. Implementar tests para nuevas funcionalidades
4. Actualizar documentación
5. Crear pull request

## Licencia

Este sistema es parte del proyecto AI News Aggregator y está bajo la misma licencia del proyecto principal.