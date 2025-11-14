# Sistema de Deduplicación y Normalización

## Descripción General

Este módulo implementa un sistema inteligente de deduplicación y normalización para el agregador de noticias AI. El sistema está diseñado para procesar artículos de múltiples fuentes, normalizar su formato y eliminar contenido duplicado de manera eficiente.

## Componentes Principales

### 1. Normalizador (`normalizer.py`)

Unifica el formato de datos de diferentes fuentes de noticias:

#### Características:
- **Normalización multi-fuente**: Soporte para NewsAPI, Guardian, NYT, Reuters, BBC, CNN, AP
- **Limpieza de texto**: Remoción de HTML, entidades, caracteres especiales
- **Validación de datos**: Verificación de campos requeridos y formatos
- **Extracción de metadatos**: Detección de idioma, tipo de artículo, legibilidad
- **Normalización de URLs**: Eliminación de parámetros de tracking

#### Fuentes Soportadas:
```python
SUPPORTED_SOURCES = [
    'newsapi',      # NewsAPI.org
    'guardian',     # The Guardian API
    'nytimes',      # New York Times API
    'reuters',      # Reuters API
    'bbc',          # BBC News
    'cnn',          # CNN API
    'associated_press', # Associated Press
    'generic'       # Formato genérico
]
```

#### Funciones Principales:

```python
# Normalizar un artículo individual
normalized = normalizer.normalize_article(raw_data, source_type='newsapi')

# Procesar múltiples artículos en lote
normalized_batch = normalizer.batch_normalize(raw_articles, 'newsapi')

# Validar y limpiar lote
valid_articles, invalid_articles = normalizer.validate_and_clean_batch(articles)

# Obtener estadísticas del proceso
stats = normalizer.get_normalization_stats(raw_articles, normalized_articles)
```

### 2. Detector de Duplicados (`deduplication.py`)

Sistema inteligente para detectar artículos duplicados usando múltiples técnicas:

#### Técnicas de Detección:

1. **URL Exacta**: Coincidencia directa de URLs normalizadas
2. **Fuzzy Matching de Títulos**: 
   - Algoritmo Ratio (similitud exacta)
   - Algoritmo Partial Ratio (subcadenas)
   - Token Sort Ratio (palabras reordenadas)
3. **Similitud de Contenido**: Comparación de características extraídas del texto
4. **Análisis Temporal**: Consideración de ventanas de tiempo para deduplicación

#### Configuración:
```python
duplicator = DuplicateDetector(
    similarity_threshold=0.85,  # Umbral de similaridad (0.0-1.0)
    max_age_days=7             # Días máximos para considerar duplicados
)
```

#### Funciones Principales:

```python
# Detectar duplicados
duplicates = duplicator.detect_duplicates(db, new_article)

# Verificar si es duplicado
is_duplicate, reason = duplicator.is_duplicate(db, new_article)

# Fusionar artículos duplicados
merged_article = duplicator.merge_articles(db, primary, duplicates)
```

### 3. Configuración (`config.py`)

Sistema de configuración flexible para ajustar parámetros sin modificar código:

#### Configuraciones Disponibles:

- **Deduplicación**: Umbrales de similaridad, limpieza de texto, análisis temporal
- **Normalización**: Validación, limpieza HTML, detección de idioma
- **Sistema**: Logging, base de datos, rendimiento, métricas

#### Configuración por Entorno:

```python
# development: Umbrales más permisivos
# testing: Configuración estricta para pruebas
# production: Configuración optimizada para producción
```

## Instalación y Configuración

### 1. Dependencias

Agregar al `requirements.txt`:
```bash
fuzzywuzzy==0.18.0
python-Levenshtein==0.23.0
python-dateutil==2.8.2
```

### 2. Importar Módulos

```python
from app.utils.normalizer import NewsNormalizer
from app.utils.deduplication import DuplicateDetector
from app.utils.config import SystemConfig
```

## Uso

### Ejemplo Básico

```python
from app.utils.demo import NewsProcessor

# Crear procesador integrado
processor = NewsProcessor()

# Procesar artículos crudos
raw_articles = [...]  # Lista de artículos en formato crudo
processed_articles = processor.process_raw_articles(
    raw_articles, 
    source_type='newsapi'
)

print(f"Procesados: {len(processed_articles)} artículos únicos")
```

### Uso Avanzado

```python
from app.utils.normalizer import NewsNormalizer
from app.utils.deduplication import DuplicateDetector

# Normalización
normalizer = NewsNormalizer()
normalized = normalizer.normalize_article(raw_data, 'newsapi')

# Deduplicación
db = SessionLocal()
duplicator = DuplicateDetector(similarity_threshold=0.9)
is_duplicate, reason = duplicator.is_duplicate(db, normalized)

if not is_duplicate:
    # Guardar artículo único
    save_article(normalized)
else:
    print(f"Duplicado encontrado: {reason}")
```

## Características Técnicas

### Normalización

#### Limpieza de Texto:
- Decodificación de entidades HTML
- Remoción de tags HTML
- Normalización de espacios en blanco
- Limpieza de caracteres de control

#### Extracción de Metadatos:
- **Hash de contenido**: Identificador único MD5
- **Detección de idioma**: Análisis de palabras comunes
- **Cálculo de legibilidad**: Basado en longitud de oraciones y complejidad
- **Tipo de artículo**: Identificación automática por patrones de texto

#### Validación:
- Verificación de campos requeridos
- Validación de formato URL
- Control de longitud de texto
- Filtrado por antigüedad

### Deduplicación

#### Algoritmos de Similaridad:
```python
# Ejemplo de scores de similaridad
ratio_score = fuzz.ratio(text1, text2) / 100.0          # 0.0-1.0
partial_score = fuzz.partial_ratio(text1, text2) / 100.0 # 0.0-1.0  
token_sort_score = fuzz.token_sort_ratio(text1, text2) / 100.0 # 0.0-1.0
```

#### Características del Contenido:
- Extracción de oraciones clave
- Generación de hash de características
- Comparación de similitud de características
- Análisis de ventana temporal

#### Fusión de Artículos:
- Selección del contenido más completo
- Mejora de títulos y metadatos
- Soft-delete de artículos duplicados
- Preservación de información única

## Métricas y Monitoreo

### Estadísticas de Normalización:
```python
{
    'total_input': 100,           # Artículos de entrada
    'total_normalized': 95,       # Artículos normalizados
    'success_rate': 95.0,         # Tasa de éxito (%)
    'languages_detected': {       # Distribución de idiomas
        'en': 70,
        'es': 20,
        'unknown': 5
    },
    'article_types': {            # Tipos de artículos
        'news': 60,
        'breaking_news': 15,
        'analysis': 10,
        'opinion': 5
    },
    'avg_content_length': 1500,   # Longitud promedio
    'avg_readability': 0.75       # Legibilidad promedio
}
```

### Estadísticas de Deduplicación:
- Tasa de duplicación detectada
- Tipos de duplicados encontrados
- Tiempo de procesamiento
- Precisión de detección

## Rendimiento

### Optimizaciones:
- **Batch processing**: Procesamiento en lote para eficiencia
- **Cache de resultados**: Caché de similaridades calculadas
- **Índices de base de datos**: Optimización de consultas
- **Procesamiento paralelo**: Soporte para múltiples workers

### Configuración de Rendimiento:
```python
# En config.py
PERFORMANCE = {
    'max_concurrent_processing': 10,
    'cache_similarity_results': True,
    'cache_ttl_seconds': 3600,
    'enable_parallel_processing': True,
}
```

## Pruebas y Validación

### Ejecutar Demostración:
```bash
python app/utils/demo.py
```

### Casos de Uso de Prueba:
1. Normalización de múltiples formatos de API
2. Detección de duplicados por título similar
3. Fusión automática de artículos
4. Manejo de errores y casos edge

## Integración

### En el Flujo Principal:
```python
# En el procesador principal de noticias
from app.utils.normalizer import NewsNormalizer
from app.utils.deduplication import DuplicateDetector

class NewsAggregator:
    def __init__(self):
        self.normalizer = NewsNormalizer()
        self.deduplicator = DuplicateDetector()
    
    async def process_articles(self, raw_articles):
        # 1. Normalizar
        normalized = self.normalizer.batch_normalize(raw_articles)
        
        # 2. Eliminar duplicados
        unique_articles = []
        for article in normalized:
            if not self.deduplicator.is_duplicate(db, article)[0]:
                unique_articles.append(article)
        
        # 3. Guardar en base de datos
        return self.save_articles(unique_articles)
```

### En Tareas Asíncronas:
```python
# Para Celery/Redis
from app.utils.deduplication import DuplicateDetector

@celery.task
def deduplicate_article_batch(article_ids):
    db = SessionLocal()
    duplicator = DuplicateDetector()
    
    for article_id in article_ids:
        article = get_article(article_id)
        duplicates = duplicator.detect_duplicates(db, article_data)
        if duplicates:
            duplicator.merge_articles(db, article, duplicates)
```

## Consideraciones Futuras

### Mejoras Planificadas:
1. **Machine Learning**: Modelos de ML para mejor detección de duplicados
2. **Análisis Semántico**: Vectorización de texto para similaridad semántica
3. **Cache Distribuido**: Redis cluster para cache distribuido
4. **API REST**: Endpoints para procesamiento externo
5. **Dashboard**: Interfaz web para monitoreo y configuración

### Escalabilidad:
- Sharding de base de datos para grandes volúmenes
- Microservicios independientes para normalización y deduplicación
- Queue systems para procesamiento asíncrono
- Load balancing para distribución de carga

## Dependencias

### Principales:
- `fuzzywuzzy`: Algoritmos de similaridad fuzzy
- `python-Levenshtein`: Cálculo eficiente de distancia de Levenshtein
- `python-dateutil`: Parsing avanzado de fechas
- `sqlalchemy`: ORM para base de datos
- `loguru`: Logging avanzado

### Opcionales:
- `transformers`: Para análisis semántico futuro
- `scikit-learn`: Para métricas de ML
- `redis`: Para cache distribuido
- `celery`: Para tareas asíncronas

## Contribución

### Estructura de Archivos:
```
backend/app/utils/
├── __init__.py           # Paquete utils
├── normalizer.py         # Sistema de normalización
├── deduplication.py      # Sistema de deduplicación  
├── config.py             # Configuración del sistema
├── demo.py              # Demostración y ejemplos
└── README.md            # Esta documentación
```

### Estándares de Código:
- Documentación completa de funciones
- Type hints para todos los parámetros
- Logging estructurado
- Manejo de errores robusto
- Tests unitarios (próximamente)

---

**Desarrollado para AI News Aggregator**  
*Sistema de deduplicación y normalización inteligente para agregadores de noticias*