"""
Configuración para el sistema de deduplicación y normalización
Permite ajustar parámetros del sistema sin modificar código
"""

from typing import Dict, Any
import os


class DeduplicationConfig:
    """Configuración para el sistema de deduplicación"""
    
    # Umbrales de similaridad
    SIMILARITY_THRESHOLDS = {
        'title_exact': 1.0,           # Coincidencia exacta de título
        'title_high': 0.95,           # Alta similitud de título
        'title_medium': 0.85,         # Similitud media de título
        'title_low': 0.75,            # Baja similitud de título
        'content': 0.70,              # Similitud de contenido
        'url_normalized': 1.0,        # URL normalizada idéntica
    }
    
    # Configuraciones de limpieza de texto
    TEXT_CLEANING = {
        'min_title_length': 10,
        'min_content_length': 50,
        'max_content_length': 50000,
        'remove_stopwords': True,
        'normalize_case': True,
        'remove_special_chars': True,
    }
    
    # Configuración de ventana temporal
    TEMPORAL_CONFIG = {
        'max_age_days': 7,            # Días de antigüedad máxima para considerar duplicados
        'window_hours': 24,           # Ventana temporal en horas para análisis
    }
    
    # Configuración de fuzzy matching
    FUZZY_MATCHING = {
        'algorithm': 'best',          # 'ratio', 'partial', 'token_sort', 'best'
        'use_multiple_algorithms': True,
        'weight_title': 0.7,          # Peso del título en la similitud total
        'weight_content': 0.3,        # Peso del contenido en la similitud total
    }
    
    # Configuración de contenido
    CONTENT_ANALYSIS = {
        'extract_sentences': 5,       # Número de oraciones para análisis
        'min_sentence_length': 3,     # Palabras mínimas por oración
        'hash_algorithm': 'md5',      # Algoritmo para hash de contenido
        'feature_similarity_threshold': 0.6,
    }
    
    @classmethod
    def get_similarity_threshold(cls, level: str = 'medium') -> float:
        """Obtiene umbral de similaridad por nivel"""
        return cls.SIMILARITY_THRESHOLDS.get(f'title_{level}', 0.85)
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Obtiene toda la configuración como diccionario"""
        return {
            'similarity_thresholds': cls.SIMILARITY_THRESHOLDS,
            'text_cleaning': cls.TEXT_CLEANING,
            'temporal': cls.TEMPORAL_CONFIG,
            'fuzzy_matching': cls.FUZZY_MATCHING,
            'content_analysis': cls.CONTENT_ANALYSIS,
        }


class NormalizationConfig:
    """Configuración para el sistema de normalización"""
    
    # Fuentes soportadas
    SUPPORTED_SOURCES = [
        'newsapi',
        'guardian', 
        'nytimes',
        'reuters',
        'bbc',
        'cnn',
        'associated_press',
        'generic'
    ]
    
    # Configuración de limpieza HTML
    HTML_CLEANING = {
        'remove_tags': True,
        'decode_entities': True,
        'remove_styles': True,
        'remove_scripts': True,
        'normalize_whitespace': True,
    }
    
    # Configuración de validación
    VALIDATION_RULES = {
        'min_title_length': 5,
        'max_title_length': 500,
        'min_content_length': 10,
        'max_content_length': 100000,
        'require_url': True,
        'validate_url_format': True,
        'max_age_days': 30,  # Artículos más antiguos son rechazados
    }
    
    # Configuración de normalización de URLs
    URL_NORMALIZATION = {
        'remove_tracking_params': True,
        'tracking_params': [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_content',
            'fbclid', 'gclid', 'ref', 'referrer', 'source'
        ],
        'normalize_case': True,
        'remove_trailing_slash': True,
        'preserve_query_params': False,
    }
    
    # Configuración de detección de idioma
    LANGUAGE_DETECTION = {
        'supported_languages': ['es', 'en', 'fr', 'de', 'it', 'pt'],
        'min_text_length': 50,
        'confidence_threshold': 0.1,
    }
    
    # Configuración de cálculo de legibilidad
    READABILITY = {
        'ideal_sentence_length': 17,
        'max_sentence_length': 25,
        'min_sentence_length': 8,
        'weight_sentence_score': 0.7,
        'weight_number_score': 0.3,
    }
    
    # Configuración de tipos de artículos
    ARTICLE_TYPES = {
        'breaking_news': ['breaking', 'última hora', 'alerta', 'urgent'],
        'opinion': ['opinion', 'opinión', 'editorial', 'columna'],
        'analysis': ['análisis', 'analysis', 'explica', 'deep dive'],
        'interview': ['entrevista', 'interview', 'habla con'],
        'report': ['informe', 'report', 'estudio', 'research'],
        'review': ['reseña', 'review', 'crítica', 'critique'],
        'feature': ['feature', 'destacado', 'especial'],
    }
    
    @classmethod
    def is_supported_source(cls, source_type: str) -> bool:
        """Verifica si la fuente está soportada"""
        return source_type.lower() in cls.SUPPORTED_SOURCES
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Obtiene toda la configuración como diccionario"""
        return {
            'supported_sources': cls.SUPPORTED_SOURCES,
            'html_cleaning': cls.HTML_CLEANING,
            'validation_rules': cls.VALIDATION_RULES,
            'url_normalization': cls.URL_NORMALIZATION,
            'language_detection': cls.LANGUAGE_DETECTION,
            'readability': cls.READABILITY,
            'article_types': cls.ARTICLE_TYPES,
        }


class SystemConfig:
    """Configuración general del sistema"""
    
    # Configuración de logging
    LOGGING = {
        'level': os.getenv('LOG_LEVEL', 'INFO'),
        'enable_file_logging': True,
        'log_file': 'logs/news_processor.log',
        'max_file_size': '10MB',
        'backup_count': 5,
    }
    
    # Configuración de base de datos
    DATABASE = {
        'batch_size': 100,
        'connection_timeout': 30,
        'max_retries': 3,
    }
    
    # Configuración de rendimiento
    PERFORMANCE = {
        'max_concurrent_processing': 10,
        'cache_similarity_results': True,
        'cache_ttl_seconds': 3600,
        'enable_parallel_processing': True,
    }
    
    # Configuración de métricas
    METRICS = {
        'track_processing_time': True,
        'track_success_rate': True,
        'track_deduplication_rate': True,
        'export_stats_interval': 3600,  # segundos
    }
    
    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """Obtiene toda la configuración del sistema"""
        return {
            'deduplication': DeduplicationConfig.get_config(),
            'normalization': NormalizationConfig.get_config(),
            'system': {
                'logging': cls.LOGGING,
                'database': cls.DATABASE,
                'performance': cls.PERFORMANCE,
                'metrics': cls.METRICS,
            }
        }


# Configuración por entorno
ENVIRONMENT_CONFIGS = {
    'development': {
        'deduplication': {'similarity_thresholds': {'title_medium': 0.80}},
        'system': {'performance': {'max_concurrent_processing': 5}}
    },
    'testing': {
        'deduplication': {'similarity_thresholds': {'title_medium': 0.90}},
        'system': {'performance': {'max_concurrent_processing': 2}}
    },
    'production': {
        'deduplication': {'similarity_thresholds': {'title_medium': 0.85}},
        'system': {'performance': {'max_concurrent_processing': 20}}
    }
}


def get_environment_config() -> Dict[str, Any]:
    """Obtiene configuración basada en el entorno actual"""
    env = os.getenv('ENVIRONMENT', 'development')
    env_config = ENVIRONMENT_CONFIGS.get(env, {})
    
    # Combinar configuración base con configuración de entorno
    base_config = SystemConfig.get_all_config()
    
    def deep_merge(base, override):
        """Combina diccionarios recursivamente"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    return deep_merge(base_config, env_config)


# Configuración activa del sistema
ACTIVE_CONFIG = get_environment_config()