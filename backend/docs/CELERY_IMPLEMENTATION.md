# Sistema de Procesamiento Asíncrono con Celery

## 📋 Resumen

Este documento describe la implementación completa del sistema de procesamiento asíncrono con Celery para el proyecto AI News Aggregator. El sistema maneja tareas de análisis de artículos, clasificación temática, generación de resúmenes y obtención automática de noticias.

## 🏗️ Arquitectura del Sistema

### Componentes Principales

1. **Celery Application** (`celery_app.py`)
   - Configuración centralizada de Celery
   - Definición de colas y routing de tareas
   - Configuración de retry y monitoreo
   - Manejo de señales para logging

2. **Workers Especializados**
   - `ai_analysis`: Análisis de artículos con OpenAI
   - `ai_classification`: Clasificación temática
   - `ai_summaries`: Generación de resúmenes
   - `news_fetch`: Obtención de noticias
   - `general`: Tareas generales y mantenimiento

3. **Sistema de Colas**
   - Queue separada por tipo de tarea
   - Rate limiting por cola
   - Priorización de tareas

4. **Monitoreo y Mantenimiento**
   - Tareas de limpieza automática
   - Métricas del sistema
   - Health checks
   - Reportes semanales

## 🚀 Tareas Implementadas

### 1. Análisis de Artículos (`article_tasks.py`)

#### `analyze_article_async()`
- **Propósito**: Analizar un artículo individual usando OpenAI
- **Tipos de análisis**: 
  - `basic`: Análisis básico con resumen y categorización
  - `comprehensive`: Análisis completo con entidades y credibilidad
  - `sentiment`: Análisis específico de sentimiento
- **Rate limit**: 10/minuto
- **Queue**: `ai_analysis`
- **Retry**: 3 intentos con backoff exponencial
- **Fallback**: Análisis tradicional sin OpenAI

#### Características:
- Manejo robusto de errores
- Logging detallado
- Timeouts configurables
- Resultados estructurados en JSON

### 2. Procesamiento en Lote (`batch_tasks.py`)

#### `batch_analyze_articles()`
- **Propósito**: Analizar múltiples artículos en lotes
- **Paralelización**: ThreadPoolExecutor con workers configurables
- **Batch size**: Configurable (default: 5)
- **Rate limit**: 5/minuto
- **Queue**: `ai_analysis`
- **Características**:
  - Procesamiento secuencial de lotes para evitar sobrecarga
  - Estadísticas detalladas de rendimiento
  - Manejo de artículos fallidos

#### `process_pending_analyses()`
- **Propósito**: Procesar análisis pendientes de la base de datos
- **Scheduler**: Cada 10 minutos vía Celery Beat
- **Rate limit**: 2/minuto
- **Queue**: `ai_analysis`

### 3. Clasificación de Temas (`classification_tasks.py`)

#### `classify_topics_batch()`
- **Propósito**: Clasificar temas de múltiples artículos
- **Sistemas de clasificación**:
  - `basic`: 5 categorías principales
  - `comprehensive`: 8 categorías extendidas
  - `custom`: Sistema personalizable
- **Rate limit**: 8/minuto
- **Queue**: `ai_classification`
- **Características**:
  - Algoritmo basado en palabras clave
  - Scores de confianza normalizados
  - Distribución temática global

#### `update_classification_model()`
- **Propósito**: Actualizar modelo de clasificación
- **Rate limit**: 1/hora
- **Queue**: `ai_classification`

### 4. Generación de Resúmenes (`summary_tasks.py`)

#### `generate_summaries_batch()`
- **Propósito**: Generar resúmenes de múltiples artículos
- **Tipos de resumen**:
  - `brief`: Muy conciso (<100 caracteres)
  - `executive`: Balanceado (150-200 caracteres)
  - `comprehensive`: Detallado (250-300 caracteres)
- **Rate limit**: 6/minuto
- **Queue**: `ai_summaries`
- **Características**:
  - Filtrado de artículos válidos
  - Compresión inteligente del texto
  - Métodos extractivos como fallback

#### `generate_article_digest()`
- **Propósito**: Crear digest consolidado de múltiples artículos
- **Tipos**: `hourly`, `daily`, `weekly`
- **Rate limit**: 10/hora
- **Queue**: `ai_summaries`

### 5. Obtención de Noticias (`news_tasks.py`)

#### `fetch_latest_news()`
- **Propósito**: Obtener noticias de múltiples fuentes
- **Fuentes soportadas**: NewsAPI, The Guardian, NYTimes
- **Rate limit**: 2/minuto
- **Queue**: `news_fetch`
- **Características**:
  - Obtención paralela de fuentes
  - Eliminación de duplicados
  - Filtros por fuente y categoría
  - Procesamiento automático encadenado

#### `search_news_task()`
- **Propósito**: Buscar noticias por query específico
- **Rate limit**: 5/minuto
- **Queue**: `news_fetch`

#### `schedule_continuous_fetch()`
- **Propósito**: Programar obtención continua
- **Rate limit**: 1/hora
- **Queue**: `news_fetch`

### 6. Monitoreo y Mantenimiento (`monitoring.py`)

#### `clean_old_task_results()`
- **Propósito**: Limpiar resultados antiguos
- **Retention**: Configurable (default: 7 días)
- **Rate limit**: 1/hora
- **Queue**: `maintenance`

#### `get_system_metrics()`
- **Propósito**: Recopilar métricas del sistema
- **Métricas incluidas**:
  - Estado de workers de Celery
  - Estadísticas de Redis
  - Uso de CPU y memoria
  - Tareas activas y pendientes
- **Rate limit**: 5/hora
- **Queue**: `maintenance`

#### `check_task_health()`
- **Propósito**: Verificar salud del sistema
- **Rate limit**: 10/hora
- **Queue**: `maintenance`

#### `generate_weekly_report()`
- **Propósito**: Generar reporte semanal
- **Rate limit**: 1/semana
- **Queue**: `maintenance`

## ⚙️ Configuración

### Variables de Entorno

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379
CELERY_BROKER_URL=redis://localhost:6379
CELERY_RESULT_BACKEND=redis://localhost:6379

# OpenAI Configuration (opcional)
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-3.5-turbo

# API Keys para noticias
NEWSAPI_KEY=your_newsapi_key
GUARDIAN_API_KEY=your_guardian_api_key
NYTIMES_API_KEY=your_nytimes_api_key
```

### Configuración de Cola en `celery_app.py`

```python
# Definición de colas
task_queues=(
    Queue('default', routing_key='default'),
    Queue('ai_analysis', routing_key='ai_analysis'),
    Queue('ai_classification', routing_key='ai_classification'),
    Queue('ai_summaries', routing_key='ai_summaries'),
    Queue('news_fetch', routing_key='news_fetch'),
    Queue('maintenance', routing_key='maintenance')
)

# Rate limiting por tarea
task_annotations={
    'app.tasks.article_tasks.analyze_article_async': {'rate_limit': '10/m'},
    'app.tasks.batch_tasks.batch_analyze_articles': {'rate_limit': '5/m'},
    'app.tasks.classification_tasks.classify_topics_batch': {'rate_limit': '8/m'},
    'app.tasks.summary_tasks.generate_summaries_batch': {'rate_limit': '6/m'},
}
```

## 📊 Scripts de Gestión

### `start_celery.sh`
Inicia todos los workers y servicios:
- Workers especializados por tipo de tarea
- Celery Beat para tareas programadas
- Flower para monitoreo web (puerto 5555)
- Logging detallado por componente

### `stop_celery.sh`
Detiene todos los servicios de forma segura:
- Terminación graceful de procesos
- Limpieza de archivos PID
- Forzado de procesos estancados

### `status_celery.sh`
Muestra estado completo del sistema:
- Estado de workers y procesos
- Uso de memoria y recursos
- Logs recientes
- Métricas de colas

## 🔧 Uso y Ejemplos

### Ejecutar Análisis Individual

```python
from app.tasks import analyze_article_async

# Analizar un artículo
result = analyze_article_async.delay(article_data, 'comprehensive')
analysis_result = result.get(timeout=300)  # 5 minutos timeout
```

### Procesar Lote de Artículos

```python
from app.tasks import batch_analyze_articles

# Analizar múltiples artículos
result = batch_analyze_articles.delay(articles, 'comprehensive', batch_size=5)
batch_result = result.get(timeout=1800)  # 30 minutos timeout
```

### Clasificar Temas

```python
from app.tasks import classify_topics_batch

# Clasificar artículos por temas
result = classify_topics_batch.delay(articles, 'comprehensive')
classification_result = result.get(timeout=600)
```

### Generar Resúmenes

```python
from app.tasks import generate_summaries_batch

# Generar resúmenes ejecutivos
result = generate_summaries_batch.delay(articles, 'executive')
summary_result = result.get(timeout=900)
```

### Obtener Noticias

```python
from app.tasks import fetch_latest_news

# Obtener últimas noticias
result = fetch_latest_news.delay(limit_per_source=20)
news_result = result.get(timeout=300)
```

## 📈 Monitoreo

### Flower (Monitoreo Web)
- **URL**: http://localhost:5555
- **Características**:
  - Dashboard en tiempo real
  - Lista de tareas activas/pendientes/completadas
  - Métricas de workers
  - Gráficos de rendimiento

### Logs Estructurados
```
logs/
├── ai_analysis.log
├── ai_classification.log
├── ai_summaries.log
├── news_fetch.log
├── general.log
├── beat.log
└── flower.log
```

### Métricas de Sistema
- **CPU y Memoria**: Monitoreo continuo con psutil
- **Redis**: Métricas de conexión y memoria
- **Celery**: Tareas activas, pendientes y completadas
- **Rate Limiting**: Estadísticas de uso por cola

## 🛡️ Manejo de Errores

### Estrategias de Retry
- **Exponencial backoff**: 1min → 2min → 4min → 7min
- **Máximo 3 intentos** por tarea
- **Jitter deshabilitado** para consistencia
- **Rate limiting** por tipo de tarea

### Fallbacks
- **Análisis sin OpenAI**: Métodos extractivos tradicionales
- **Redis desconectado**: Modo degradado con logging
- **API keys faltantes**: Funcionalidad básica sin AI

### Logging y Alertas
- **Niveles**: INFO, WARNING, ERROR, CRITICAL
- **Correlación**: Task ID en todos los logs
- **Contexto**: Información detallada de errores
- **Rotación**: Logs rotativos automáticos

## 🔄 Tareas Programadas (Celery Beat)

```python
celery_app.conf.beat_schedule = {
    'fetch-latest-news': {
        'task': 'app.tasks.news_tasks.fetch_latest_news',
        'schedule': 300.0,  # cada 5 minutos
        'options': {'queue': 'news_fetch'}
    },
    'analyze-pending-articles': {
        'task': 'app.tasks.batch_tasks.process_pending_analyses',
        'schedule': 600.0,  # cada 10 minutos
        'options': {'queue': 'ai_analysis'}
    },
    'clean-old-results': {
        'task': 'app.tasks.monitoring.clean_old_task_results',
        'schedule': 3600.0,  # cada hora
        'options': {'queue': 'maintenance'}
    }
}
```

## 📋 Dependencias

### Core Requirements
```
celery[redis]==5.3.4
kombu==5.3.4
billiard==4.2.0
redis==5.0.1
openai==1.3.7
```

### Monitoreo
```
flower==1.0.0
psutil==5.9.0
```

### Procesamiento de Texto
```
nltk==3.8.1
textblob==0.17.1
```

## 🚀 Mejores Prácticas

### 1. **Gestión de Memoria**
- Workers con `max_tasks_per_child=1000`
- Procesamiento en lotes pequeños
- Limpieza periódica de resultados

### 2. **Rate Limiting**
- Límites conservadores por API
- Backoff exponencial en fallas
- Monitoreo de uso de cuotas

### 3. **Escalabilidad**
- Workers especializados por cola
- Concurrencia configurable
- Horizontal scaling por tipo de tarea

### 4. **Observabilidad**
- Logging estructurado con correlaciones
- Métricas de sistema en tiempo real
- Health checks automáticos
- Reportes de rendimiento

### 5. **Mantenimiento**
- Limpieza automática de datos antiguos
- Verificación de salud periódica
- Actualizaciones de modelos de clasificación
- Optimización de consultas

## 🔧 Troubleshooting

### Problemas Comunes

1. **Workers no se inician**
   - Verificar Redis esté ejecutándose
   - Revisar variables de entorno
   - Validar configuración de Celery

2. **Tareas fallan constantemente**
   - Verificar API keys
   - Revisar límites de rate
   - Analizar logs de error

3. **Alta latencia**
   - Reducir concurrencia
   - Optimizar parámetros de retry
   - Escalar horizontalmente

4. **Redis sin memoria**
   - Aumentar configuración de Redis
   - Reducir retención de resultados
   - Implementar limpieza más frecuente

### Comandos de Diagnóstico

```bash
# Verificar estado
./status_celery.sh

# Monitorear logs en tiempo real
tail -f logs/ai_analysis.log

# Verificar tareas en Flower
curl http://localhost:5555/api/tasks

# Verificar colas de Redis
redis-cli LLEN celery
```

## 📈 Métricas de Rendimiento

### Benchmarks Típicos
- **Análisis individual**: 2-5 segundos
- **Procesamiento en lote**: 10-15 segundos por artículo
- **Clasificación**: 0.5-2 segundos por artículo
- **Generación de resúmenes**: 1-3 segundos por artículo

### Throughput Esperado
- **Análisis**: 100-200 artículos/hora por worker
- **Clasificación**: 300-500 artículos/hora por worker
- **Resúmenes**: 200-400 artículos/hora por worker

## 🔮 Extensiones Futuras

1. **Machine Learning Models**
   - Modelos propios de clasificación
   - Análisis de sentimiento avanzado
   - Detección de fake news

2. **Integraciones Adicionales**
   - Más fuentes de noticias
   - Notificaciones push
   - APIs de terceros

3. **Optimización**
   - Cache de resultados
   - Compresión de datos
   - Paralelización avanzada

4. **Analytics**
   - Dashboards interactivos
   - Métricas de usuario
   - Análisis de tendencias

---

*Documentación generada para AI News Aggregator v1.0*
*Última actualización: 2025-11-06*