# AI Processor Service

Servicio avanzado de procesamiento de noticias con OpenAI GPT que proporciona análisis de sentimiento, clasificación de temas, generación de resúmenes y scoring de relevancia.

## 🚀 Características Principales

### ✅ Funcionalidades Implementadas

- **📊 Análisis de Sentimiento**: Análisis detallado con puntuación de -1 a 1 y etiquetas de emoción
- **🏷️ Clasificación de Temas**: Clasificación automática en 12 categorías predefinidas
- **📝 Generación de Resúmenes**: Resúmenes inteligentes con puntos clave
- **⭐ Scoring de Relevancia**: Evaluación de relevancia basada en múltiples factores
- **🔄 Procesamiento Síncrono y Asíncrono**: Soporte completo para ambos modos
- **⚡ Rate Limit Handling**: Manejo robusto de límites de API
- **🔄 Retry Logic**: Reintentos automáticos con backoff exponencial
- **💰 Optimización de Costos**: Selección automática de modelos y cálculo de costos
- **🗃️ Cache Inteligente**: Cache en memoria con TTL configurable
- **📈 Monitoreo**: Logging detallado y métricas de performance
- **🔧 Fallbacks**: Sistemas de respaldo para cuando OpenAI no está disponible

## 🏗️ Arquitectura

```
ai_processor.py
├── RateLimitHandler          # Manejo de límites de rate
├── RetryHandler              # Lógica de reintentos
├── CostOptimizer             # Optimización de costos
├── CacheManager              # Gestión de cache
├── SentimentAnalyzer         # Análisis de sentimiento
├── TopicClassifier           # Clasificación de temas
├── Summarizer               # Generación de resúmenes
├── RelevanceScorer          # Scoring de relevancia
├── ComprehensiveAnalyzer    # Analizador unificado
└── Factory Functions        # Funciones de creación
```

## 📦 Instalación y Configuración

### Dependencias

El sistema requiere las siguientes dependencias (ya incluidas en requirements.txt):

```bash
# OpenAI SDK
openai>=1.3.7

# Utilidades de async y concurrencia
asyncio
concurrent.futures

# Procesamiento de texto
re
hashlib
json
```

### Variables de Entorno

```bash
export OPENAI_API_KEY="tu-api-key-aqui"
```

## 🎯 Uso Básico

### 1. Crear Analizador Comprehensivo

```python
from app.services.ai_processor import create_ai_processor

# Crear instancia con configuración por defecto
analyzer = create_ai_processor(openai_api_key="tu-api-key")

# Con configuración personalizada
analyzer = create_ai_processor(
    openai_api_key="tu-api-key",
    default_model="gpt-3.5-turbo",
    requests_per_minute=50,
    cache_ttl=3600  # 1 hora
)
```

### 2. Análisis Completo de Artículo

```python
article = {
    "id": "article_001",
    "title": "Nueva tecnología de IA revoluciona la industria médica",
    "content": "Una revolucionaria tecnología de inteligencia artificial...",
    "description": "Nueva IA desarrollada por MIT mejora el diagnóstico médico"
}

# Análisis síncrono
result = analyzer.analyze_article(
    article_id=article["id"],
    content=article["title"] + " " + article["content"],
    user_preferences={
        "technology": 0.8,
        "health": 0.9,
        "science": 0.7
    },
    max_summary_words=150
)

# Acceder a resultados
print(f"Sentimiento: {result.sentiment.sentiment.value}")
print(f"Tema: {result.topic.primary_topic.value}")
print(f"Relevancia: {result.relevance.relevance_score:.2f}")
print(f"Costo total: ${result.total_cost:.4f}")
```

### 3. Análisis Asíncrono

```python
import asyncio

async def analyze_news_batch():
    articles = [
        {"id": "tech_001", "title": "Apple lanza nuevo iPhone", "content": "..."},
        {"id": "pol_001", "title": "Elecciones 2024", "content": "..."},
        {"id": "health_001", "title": "Nueva vacuna COVID-19", "content": "..."}
    ]
    
    results, errors = await analyzer.batch_analyze_async(
        articles=articles,
        max_concurrent=3
    )
    
    print(f"Análisis completados: {len(results)}")
    print(f"Errores: {len(errors)}")

# Ejecutar
asyncio.run(analyze_news_batch())
```

## 🔧 Uso Avanzado

### Analizadores Individuales

```python
from app.services.ai_processor import (
    SentimentAnalyzer, TopicClassifier, Summarizer, RelevanceScorer
)

# Análisis de sentimiento individual
sentiment_analyzer = SentimentAnalyzer(openai_api_key="tu-api-key")
sentiment_result = sentiment_analyzer.analyze_sentiment(text)

# Clasificación de tema individual
topic_classifier = TopicClassifier(openai_api_key="tu-api-key")
topic_result = topic_classifier.classify_topic(text)

# Resumen individual
summarizer = Summarizer(openai_api_key="tu-api-key")
summary_result = summarizer.summarize(text, max_words=100)

# Scoring de relevancia individual
relevance_scorer = RelevanceScorer(openai_api_key="tu-api-key")
relevance_result = relevance_scorer.score_relevance(
    text, 
    user_preferences={"economy": 0.9}
)
```

### Configuraciones por Entorno

```python
# Desarrollo (económico)
dev_analyzer = create_ai_processor(
    default_model="gpt-3.5-turbo",
    requests_per_minute=30,
    cache_ttl=7200  # 2 horas
)

# Producción (robusto)
prod_analyzer = create_ai_processor(
    default_model="gpt-4",
    requests_per_minute=60,
    cache_ttl=3600  # 1 hora
)

# Tiempo real (rápido)
realtime_analyzer = create_ai_processor(
    default_model="gpt-3.5-turbo",
    requests_per_minute=100,
    cache_ttl=1800  # 30 minutos
)
```

## 📊 Tipos de Resultados

### SentimentResult
```python
{
    "sentiment": SentimentType.POSITIVE,  # POSITIVE, NEGATIVE, NEUTRAL, MIXED
    "sentiment_score": 0.75,              # -1 a 1
    "confidence": 0.85,                   # 0 a 1
    "emotion_tags": ["optimism", "hope"], # Lista de emociones
    "processing_time": 1.2,              # segundos
    "cost": 0.002,                       # costo en dólares
    "model": "gpt-3.5-turbo"
}
```

### TopicResult
```python
{
    "primary_topic": TopicCategory.TECHNOLOGY,
    "topic_probability": 0.92,           # 0 a 1
    "secondary_topics": [                # Top 3 temas secundarios
        (TopicCategory.SCIENCE, 0.65),
        (TopicCategory.HEALTH, 0.43)
    ],
    "topic_keywords": ["AI", "machine learning", "technology"],
    "processing_time": 0.8,
    "cost": 0.001
}
```

### SummaryResult
```python
{
    "summary": "Resumen conciso del artículo...",
    "key_points": [
        "Punto clave 1",
        "Punto clave 2", 
        "Punto clave 3"
    ],
    "word_count": 120,
    "reading_time_minutes": 0.6,         # basado en 200 WPM
    "processing_time": 2.1,
    "cost": 0.008
}
```

### RelevanceResult
```python
{
    "relevance_score": 0.78,             # 0 a 1
    "importance_score": 0.85,            # 0 a 1
    "trending_score": 0.72,              # 0 a 1
    "relevance_factors": {
        "current_events": 0.8,
        "topic_importance": 0.9,
        "celebrity_involvement": 0.3,
        "financial_impact": 0.6
    },
    "processing_time": 1.5,
    "cost": 0.003
}
```

## 💰 Gestión de Costos

### Precios por Token (USD)
- **GPT-3.5-turbo**: $0.5/1M tokens entrada, $1.5/1M tokens salida
- **GPT-4**: $30/1M tokens entrada, $60/1M tokens salida

### Selección Automática de Modelos
```python
models = {
    "sentiment": "gpt-3.5-turbo",           # Tareas simples
    "topic_classification": "gpt-3.5-turbo", # Tareas simples  
    "summary": "gpt-4",                      # Tareas complejas
    "relevance": "gpt-3.5-turbo"             # Tareas simples
}
```

### Cálculo de Costos
```python
# Función de utilidad
from app.services.ai_processor import analyze_cost_breakdown

results = [analysis_result_1, analysis_result_2, ...]
cost_breakdown = analyze_cost_breakdown(results)

print(f"Costo total: ${cost_breakdown['total_cost']:.4f}")
print(f"Costo promedio: ${cost_breakdown['average_cost']:.4f}")
```

## ⚡ Rate Limiting

### Configuración de Límites
```python
analyzer = create_ai_processor(
    requests_per_minute=60,    # Límite por minuto
    requests_per_day=10000     # Límite por día
)
```

### Comportamiento Automático
- ✅ Espera automática cuando se alcanza el límite
- ✅ Limpieza automática de historial antiguo
- ✅ Cálculo dinámico de tiempo de espera
- ✅ Monitoreo en logs

## 🔄 Retry Logic

### Configuración
```python
retry_handler = RetryHandler(
    max_retries=3,        # Máximo número de reintentos
    base_delay=1.0,       # Delay inicial (segundos)
    max_delay=60.0        # Delay máximo (segundos)
)
```

### Backoff Exponencial
```
Intento 1: wait 1s
Intento 2: wait 2s  
Intento 3: wait 4s
Intento 4: wait 8s (máximo)
```

## 🗃️ Sistema de Cache

### Configuración
```python
cache_manager = CacheManager(ttl_seconds=3600)  # 1 hora por defecto
```

### Características
- **TTL configurable**: Tiempo de vida personalizable
- **Generación de claves**: Hash MD5 de contenido + tipo de análisis
- **Limpieza automática**: Elimina entradas expiradas
- **Límite de memoria**: Control de tamaño de cache

## 🧪 Testing

### Ejecutar Tests Básicos
```bash
python app/services/test_ai_processor.py
```

### Ejecutar Tests Completos con Pytest
```bash
pytest app/services/test_ai_processor.py -v
```

### Tests Incluidos
- ✅ Inicialización de componentes
- ✅ Preparación y limpieza de contenido
- ✅ Estimación de tokens
- ✅ Fallbacks sin API key
- ✅ Análisis síncrono y asíncrono
- ✅ Cálculo de scores combinados
- ✅ Análisis de costos
- ✅ Tests de integración

## 📝 Ejemplos Completos

### Ejemplo con Manejo de Errores
```python
try:
    result = analyzer.analyze_article("article_001", content)
    print(f"Análisis exitoso: {result.combined_score:.2f}")
    
except RateLimitError as e:
    print(f"Límite de rate alcanzado: {e}")
    # Implementar estrategia de reintento
    
except Exception as e:
    print(f"Error en análisis: {e}")
    # Usar fallback local
```

### Ejemplo de Análisis en Tiempo Real
```python
async def real_time_analysis():
    articles_stream = get_news_stream()  # Generator de artículos
    
    semaphore = asyncio.Semaphore(5)  # Máximo 5 concurrentes
    async with semaphore:
        for article in articles_stream:
            try:
                result = await analyzer.analyze_article_async(
                    article["id"], 
                    article["content"],
                    max_summary_words=75  # Resúmenes más cortos
                )
                yield result
                
            except Exception as e:
                logger.error(f"Error procesando {article['id']}: {e}")
                continue
```

## 🔧 Configuración de Producción

### Variables de Entorno
```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Rate Limits
AI_REQUESTS_PER_MINUTE=60
AI_REQUESTS_PER_DAY=10000

# Cache
AI_CACHE_TTL=3600  # 1 hora

# Logging
LOG_LEVEL=INFO
```

### Configuración de Celery (Opcional)
```python
# Tareas en background
from app.services.ai_processor import celery_app

# Enviar análisis a queue
celery_app.send_task(
    'analyze_article_async',
    args=['article_id', 'content'],
    kwargs={'openai_api_key': os.getenv('OPENAI_API_KEY')}
)
```

## 📈 Monitoreo y Métricas

### Logs Incluidos
- ✅ Inicialización de componentes
- ✅ Rate limit warnings
- ✅ Retry attempts
- ✅ Resultados de análisis
- ✅ Cálculos de costos
- ✅ Errores y fallbacks

### Métricas Disponibles
- Tiempo de procesamiento
- Tokens utilizados
- Costos por análisis
- Tasa de aciertos del cache
- Distribución de temas
- Patrones de sentimiento

## 🤝 Compatibilidad

### Backward Compatibility
- ✅ Mantiene compatibilidad con el `AIProcessor` legacy
- ✅ Métodos heredados marcados como deprecated
- ✅ Estructuras de datos compatibles
- ✅ Importaciones existentes funcionan

### Python Compatibility
- ✅ Python 3.8+
- ✅ Compatible con FastAPI
- ✅ Compatible con Celery
- ✅ Compatible con Redis (opcional)

## 🐛 Solución de Problemas

### Error: "Cliente OpenAI no inicializado"
```python
# Verificar que la API key esté configurada
import os
print(f"API Key configurada: {bool(os.getenv('OPENAI_API_KEY'))}")

# Usar fallback local
analyzer = create_ai_processor()  # Sin API key
```

### Error: "Rate limit alcanzado"
```python
# El sistema esperará automáticamente
# Para configurar límites más altos:
analyzer = create_ai_processor(
    requests_per_minute=100,
    requests_per_day=50000
)
```

### Costos altos
```python
# Usar modelo más económico
analyzer = create_ai_processor(
    default_model="gpt-3.5-turbo"
)

# Aumentar cache TTL
analyzer = create_ai_processor(
    cache_ttl=7200  # 2 horas
)
```

## 📞 Soporte

Para problemas o preguntas:

1. **Logs**: Revisar logs detallados del sistema
2. **Tests**: Ejecutar `test_ai_processor.py` para verificar funcionalidad
3. **Ejemplos**: Revisar `examples_ai_processor.py` para casos de uso
4. **Configuración**: Verificar variables de entorno y configuración

## 🎉 Conclusión

El AI Processor Service proporciona una solución robusta, escalable y eficiente para el análisis inteligente de noticias. Con características avanzadas como rate limiting, retry logic, optimización de costos y fallbacks, está diseñado para uso en producción con alta confiabilidad.