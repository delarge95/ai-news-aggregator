# Pipeline de Orquestación de IA

## Descripción General

El `AIPipelineOrchestrator` es un sistema completo de procesamiento de noticias que orquesta tres pipelines especializados:

### 1. PreprocessingPipeline
- **Función**: Limpieza y normalización de texto
- **Características**:
  - Normalización inteligente de datos de múltiples fuentes
  - Validación de integridad de datos
  - Procesamiento paralelo configurable
  - Manejo robusto de errores

### 2. AIAnalysisPipeline  
- **Función**: Análisis secuencial de IA
- **Análisis incluidos**:
  - **Sentiment**: Análisis de sentimiento (-1.0 a 1.0)
  - **Topics**: Extracción de temas principales
  - **Summary**: Resumen automático del contenido
  - **Relevance**: Puntuación de relevancia (0.0 a 1.0)
  - **Bias**: Detección de sesgo (0.0 a 1.0)
- **Características**:
  - Secuencia optimizada de análisis
  - Procesamiento paralelo controlado
  - Timeouts configurables
  - Sistema de retry automático

### 3. PostprocessingPipeline
- **Función**: Formateo final y almacenamiento
- **Características**:
  - Almacenamiento en base de datos
  - Caché de resultados de análisis
  - Actualización de metadatos
  - Transacciones seguras

## Configuración

### ProcessingConfig
```python
config = ProcessingConfig(
    # Batch processing
    batch_size=10,                    # Artículos por lote
    max_concurrent_batches=5,         # Lotes simultáneos
    
    # Individual analysis  
    max_concurrent_analyses=20,       # Análisis simultáneos
    analysis_timeout=30,              # Timeout por análisis
    
    # OpenAI configuration
    openai_model="gpt-3.5-turbo",
    max_tokens=1000,
    temperature=0.3,
    
    # Validation thresholds
    min_content_length=50,
    min_title_length=5,
    max_title_length=500,
    max_content_length=50000,
    
    # Retry configuration
    max_retries=3,
    retry_delay=1.0,
    
    # Feature toggles
    enable_parallel_processing=True,
    enable_caching=True,
    enable_validation=True
)
```

### Configuraciones Predefinidas
```python
# Desarrollo
config = DEFAULT_CONFIGS['development']

# Producción  
config = DEFAULT_CONFIGS['production']

# Alto rendimiento
config = DEFAULT_CONFIGS['high_throughput']
```

## Uso Básico

### Procesamiento por Lotes
```python
import asyncio
from app.services.ai_pipeline import process_news_batch
from sqlalchemy.ext.asyncio import AsyncSession

async def process_news():
    # Datos de entrada
    raw_articles = [
        {
            "title": "Breaking: New AI breakthrough announced",
            "content": "Scientists have achieved...",
            "url": "https://example.com/news/123",
            "source": "Tech News"
        },
        # ... más artículos
    ]
    
    # Procesar lote
    result = await process_news_batch(
        raw_articles=raw_articles,
        source_type='newsapi',
        session=session  # Opcional
    )
    
    print(f"Procesados: {result.total_articles}")
    print(f"Exitosos: {result.successful_analyses}")
    print(f"Fallidos: {result.failed_analyses}")
    print(f"Tiempo: {result.processing_time:.2f}s")

# Ejecutar
asyncio.run(process_news())
```

### Procesamiento Individual
```python
from app.services.ai_pipeline import process_single_news

async def process_single():
    raw_article = {
        "title": "AI Revolution in Healthcare",
        "content": "Artificial intelligence is transforming...",
        "url": "https://example.com/article/456"
    }
    
    result = await process_single_news(
        raw_article=raw_article,
        source_type='guardian',
        session=session
    )
    
    print(f"Análisis: {result.analysis_type.value}")
    print(f"Confianza: {result.confidence_score}")
    print(f"Resultado: {result.result}")

asyncio.run(process_single())
```

### Uso Avanzado con Pipeline Personalizado
```python
from app.services.ai_pipeline import AIPipelineOrchestrator, ProcessingConfig

async def advanced_processing():
    # Configuración personalizada
    config = ProcessingConfig(
        batch_size=15,
        max_concurrent_analyses=30,
        analysis_timeout=45,
        enable_parallel_processing=True
    )
    
    # Crear pipeline
    pipeline = AIPipelineOrchestrator(config)
    
    # Procesar con control total
    result = await pipeline.process_articles_batch(
        raw_articles=articles,
        source_type='generic',
        session=session
    )
    
    # Obtener estadísticas
    stats = pipeline.get_processing_stats()
    print(stats)

asyncio.run(advanced_processing())
```

## Características Avanzadas

### Manejo de Errores Robusto
- **Timeouts configurables** por tipo de análisis
- **Sistema de retry** automático con backoff exponencial
- **Continuidad del procesamiento** aunque fallen análisis individuales
- **Logging detallado** para debugging

### Validación de Datos
- **Validación de entrada** antes del procesamiento
- **Sanitización de contenido** HTML y texto
- **Normalización de URLs** y metadatos
- **Detección de duplicados** por hash de contenido

### Procesamiento Paralelo
- **Control de concurrencia** configurable
- **Semáforos asyncio** para limitar operaciones simultáneas
- **Lotes balanceados** para optimizar rendimiento
- **Manejo de recursos** para evitar sobrecarga

### Métricas y Monitoreo
- **Estadísticas en tiempo real** de procesamiento
- **Tiempo por operación** y throughput
- **Tasas de éxito** por tipo de análisis
- **Configuración de performance** ajustable

## Estructura de Resultados

### BatchResult
```python
@dataclass
class BatchResult:
    batch_id: str                       # ID único del lote
    total_articles: int                 # Total de artículos procesados
    successful_analyses: int            # Análisis exitosos
    failed_analyses: int               # Análisis fallidos
    processing_time: float             # Tiempo total de procesamiento
    results: List[AnalysisResult]      # Lista de resultados detallados
    errors: List[str]                  # Lista de errores
    metadata: Dict[str, Any]           # Metadatos adicionales
```

### AnalysisResult
```python
@dataclass
class AnalysisResult:
    article_id: str                     # ID del artículo
    analysis_type: AnalysisType         # Tipo de análisis
    result: Dict[str, Any]              # Resultado del análisis
    confidence_score: float             # Score de confianza (0.0-1.0)
    model_used: str                     # Modelo de IA utilizado
    processing_time: float              # Tiempo del análisis
    error_message: Optional[str]        # Mensaje de error (si aplica)
    status: ProcessingStatus            # Estado del procesamiento
```

## Tipos de Análisis

### Sentiment Analysis
```python
{
    "sentiment_score": 0.7,           # Score -1.0 a 1.0
    "sentiment_label": "positive",     # positive, negative, neutral
    "explanation": "Análisis del tono..."
}
```

### Topics Extraction
```python
{
    "topics": ["artificial intelligence", "healthcare", "breakthrough"],
    "topic_count": 3,
    "extraction_method": "ai_analysis"
}
```

### Summary Generation
```python
{
    "summary": "Scientists have developed a new AI system...",
    "summary_length": 150,
    "extraction_method": "ai_generated"
}
```

### Relevance Scoring
```python
{
    "relevance_score": 0.85,          # Score 0.0 a 1.0
    "explanation": "Alta relevancia por actualidad e impacto"
}
```

### Bias Detection
```python
{
    "bias_score": 0.2,               # Score 0.0 a 1.0 (0 = sin sesgo)
    "explanation": "Lenguaje objetivo, perspectiva balanceada"
}
```

## Integración con Base de Datos

El pipeline se integra automáticamente con los modelos SQLAlchemy:

### Article Model
- Se actualiza con resultados de análisis
- Se almacena resumen generado
- Se agregan scores de sentiment, relevance y bias
- Se marca timestamp de procesamiento

### ArticleAnalysis Model
- Caché de resultados individuales por tipo
- Metadatos de confianza y modelo utilizado
- Trazabilidad completa del procesamiento

### Source Model
- Gestión automática de fuentes de noticias
- Creación automática de fuentes nuevas

## Mejores Prácticas

### 1. Configuración de Lotes
- Usar `batch_size=10-20` para producción
- `max_concurrent_analyses` no debe exceder 50 para evitar rate limits
- Monitorear tiempos de respuesta y ajustar timeouts

### 2. Manejo de Errores
- Siempre verificar `BatchResult.errors`
- Implementar retry logic para lotes fallidos
- Usar logging para monitoreo en producción

### 3. Gestión de Recursos
- Limitar concurrencia según capacidad del sistema
- Usar pooling de conexiones de base de datos
- Considerar rate limits de APIs externas

### 4. Validación de Datos
- Siempre validar datos de entrada antes del procesamiento
- Usar `enable_validation=True` en producción
- Implementar fallback para datos corruptos

## Limitaciones y Consideraciones

### Dependencias
- Requiere **OpenAI API key** configurada
- Necesita conexión a **base de datos PostgreSQL**
- Conexión **Redis opcional** para cache

### Performance
- Análisis individual toma ~2-5 segundos
- Throughput típico: 10-50 artículos/minuto
- Memoria: ~100MB por 100 artículos en batch

### Rate Limits
- OpenAI tiene límites por minuto/hora
- Implementar backoff automático
- Considerar colas para alto volumen

### Costos
- OpenAI API tiene costo por token
- Estimar ~$0.01-0.05 por artículo completo
- Monitorear usage y configurar alertas

## Troubleshooting

### Problemas Comunes

**1. Timeout en análisis**
```python
# Aumentar timeout en config
config.analysis_timeout = 60  # 60 segundos
```

**2. Rate limit de OpenAI**
```python
# Reducir concurrencia
config.max_concurrent_analyses = 10
```

**3. Errores de validación**
```python
# Deshabilitar validación temporalmente (solo desarrollo)
config.enable_validation = False
```

**4. Problemas de memoria**
```python
# Reducir tamaño de lote
config.batch_size = 5
```

### Debugging
- Habilitar logging detallado: `logging.getLogger('app.services.ai_pipeline').setLevel(logging.DEBUG)`
- Revisar `BatchResult.metadata` para métricas detalladas
- Usar `pipeline.get_processing_stats()` para análisis de performance
