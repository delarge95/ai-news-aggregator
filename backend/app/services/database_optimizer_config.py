"""
Configuración e integración del Database Optimizer

Este archivo proporciona la configuración centralizada para el sistema
de optimización de base de datos y su integración con la aplicación.
"""

import os
from typing import Optional, Dict, Any
from datetime import timedelta
import redis
from sqlalchemy import create_engine

# Configuración del Optimizador
DATABASE_OPTIMIZER_CONFIG = {
    # Cache Configuration
    'cache': {
        'default_ttl': 300,  # 5 minutos
        'max_memory_items': 1000,
        'memory_cache_enabled': True,
        'redis_enabled': True
    },
    
    # Performance Monitoring
    'monitoring': {
        'slow_query_threshold_ms': 1000,
        'enable_performance_tracking': True,
        'enable_slow_query_logging': True,
        'performance_metrics_retention_days': 7
    },
    
    # Materialized Views
    'materialized_views': {
        'auto_create': True,
        'auto_refresh': True,
        'refresh_interval_minutes': 60,
        'concurrent_refresh': True
    },
    
    # Indexes
    'indexes': {
        'auto_create': True,
        'concurrent_creation': True,
        'optimize_queries': True
    },
    
    # Pagination
    'pagination': {
        'default_limit': 20,
        'max_limit': 100,
        'cursor_based_default': True
    },
    
    # Search Configuration
    'search': {
        'full_text_enabled': True,
        'search_cache_ttl': 180,  # 3 minutos
        'min_search_length': 3
    }
}

# TTL específicos por tipo de consulta
QUERY_TTL_CONFIG = {
    'list_articles': 300,        # 5 minutos
    'search_articles': 180,      # 3 minutos  
    'get_trending': 600,         # 10 minutos
    'dashboard_stats': 120,      # 2 minutos
    'user_preferences': 1800,    # 30 minutos
    'analysis_results': 3600,    # 1 hora
    'source_performance': 900,   # 15 minutos
    'duplicate_detection': 600   # 10 minutos
}

# Configuración de índices compuestos optimizados
OPTIMIZED_INDEXES_CONFIG = {
    # Índices para artículos
    'articles': [
        {
            'name': 'idx_articles_source_date_processed',
            'columns': ['source_id', 'published_at', 'processing_status'],
            'conditions': 'published_at IS NOT NULL',
            'unique': False
        },
        {
            'name': 'idx_articles_sentiment_relevance_date',
            'columns': ['sentiment_label', 'relevance_score DESC', 'published_at DESC'],
            'conditions': 'sentiment_label IS NOT NULL AND relevance_score IS NOT NULL',
            'unique': False
        },
        {
            'name': 'idx_articles_trending',
            'columns': ['processing_status', 'relevance_score DESC', 'created_at'],
            'conditions': "processing_status = 'completed' AND created_at > NOW() - INTERVAL '7 days'",
            'unique': False
        },
        {
            'name': 'idx_articles_duplicate_hash',
            'columns': ['content_hash', 'processing_status', 'duplicate_group_id'],
            'conditions': 'content_hash IS NOT NULL',
            'unique': False
        }
    ],
    
    # Índices para análisis de tareas
    'analysis_tasks': [
        {
            'name': 'idx_analysis_tasks_queue',
            'columns': ['status', 'priority', 'scheduled_at'],
            'conditions': "status = 'pending'",
            'unique': False
        },
        {
            'name': 'idx_analysis_tasks_article_type',
            'columns': ['article_id', 'task_type', 'status'],
            'conditions': 'article_id IS NOT NULL',
            'unique': False
        },
        {
            'name': 'idx_analysis_tasks_performance',
            'columns': ['task_type', 'started_at', 'completed_at', 'processing_duration_ms'],
            'conditions': 'started_at IS NOT NULL',
            'unique': False
        }
    ],
    
    # Índices para trending topics
    'trending_topics': [
        {
            'name': 'idx_trending_topics_category_time',
            'columns': ['topic_category', 'date_recorded DESC', 'trend_score DESC'],
            'conditions': 'date_recorded > NOW() - INTERVAL \'30 days\'',
            'unique': False
        },
        {
            'name': 'idx_trending_topics_article_count',
            'columns': ['topic_category', 'article_count DESC', 'sources_count DESC'],
            'conditions': 'topic_category IS NOT NULL',
            'unique': False
        }
    ]
}

# Configuración de vistas materializadas
MATERIALIZED_VIEWS_CONFIG = {
    'article_statistics': {
        'sql': '''
            CREATE MATERIALIZED VIEW IF NOT EXISTS article_statistics AS
            SELECT 
                s.id as source_id,
                s.name as source_name,
                s.api_name,
                s.credibility_score,
                COUNT(a.id) as total_articles,
                COUNT(CASE WHEN a.processing_status = 'completed' THEN 1 END) as processed_articles,
                COUNT(CASE WHEN a.processing_status = 'failed' THEN 1 END) as failed_articles,
                COUNT(CASE WHEN a.processing_status = 'pending' THEN 1 END) as pending_articles,
                ROUND(AVG(a.sentiment_score), 3) as avg_sentiment,
                ROUND(AVG(a.relevance_score), 3) as avg_relevance,
                MAX(a.published_at) as last_article_date,
                COUNT(CASE WHEN a.created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as articles_last_24h,
                COUNT(CASE WHEN a.created_at > NOW() - INTERVAL '7 days' THEN 1 END) as articles_last_7d,
                COUNT(DISTINCT CASE WHEN a.sentiment_label = 'positive' THEN a.id END) as positive_articles,
                COUNT(DISTINCT CASE WHEN a.sentiment_label = 'negative' THEN a.id END) as negative_articles,
                COUNT(DISTINCT CASE WHEN a.sentiment_label = 'neutral' THEN a.id END) as neutral_articles
            FROM sources s
            LEFT JOIN articles a ON s.id = a.source_id
            WHERE s.is_active = true
            GROUP BY s.id, s.name, s.api_name, s.credibility_score;
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS idx_article_statistics_source_id ON article_statistics(source_id)',
            'CREATE INDEX IF NOT EXISTS idx_article_statistics_api_name ON article_statistics(api_name)',
            'CREATE INDEX IF NOT EXISTS idx_article_statistics_credibility ON article_statistics(credibility_score DESC)',
            'CREATE INDEX IF NOT EXISTS idx_article_statistics_last_article ON article_statistics(last_article_date DESC)'
        ],
        'refresh_interval': 3600  # 1 hora
    },
    
    'trending_topics_detailed': {
        'sql': '''
            CREATE MATERIALIZED VIEW IF NOT EXISTS trending_topics_detailed AS
            SELECT 
                topic_tags.tag as topic,
                COALESCE(a.topic_tags_categories->>0, 'general') as topic_category,
                COUNT(DISTINCT a.id) as article_count,
                COUNT(DISTINCT a.source_id) as sources_count,
                ROUND(AVG(a.relevance_score), 3) as avg_relevance,
                ROUND(AVG(a.sentiment_score), 3) as avg_sentiment,
                array_agg(DISTINCT t.topic) FILTER (WHERE t.topic != topic_tags.tag) as related_topics,
                MIN(a.published_at) as first_appearance,
                MAX(a.published_at) as last_appearance,
                (COUNT(DISTINCT a.id) * AVG(a.relevance_score)) as trending_score
            FROM articles a
            CROSS JOIN LATERAL jsonb_array_elements_text(a.topic_tags) WITH ORDINALITY as topic_tags(tag, pos)
            LEFT JOIN (
                SELECT 
                    jsonb_array_elements_text(topic_tags) as topic,
                    array_agg(DISTINCT topic_category) as topic_tags_categories
                FROM articles 
                WHERE topic_tags IS NOT NULL
                GROUP BY jsonb_array_elements_text(topic_tags)
            ) t ON t.topic = topic_tags.tag
            WHERE a.created_at > NOW() - INTERVAL '14 days'
            AND a.processing_status = 'completed'
            GROUP BY topic_tags.tag, topic_tags.pos
            HAVING COUNT(DISTINCT a.id) >= 3  -- Al menos 3 artículos para ser trending
            ORDER BY trending_score DESC, article_count DESC;
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS idx_trending_topics_detailed_category ON trending_topics_detailed(topic_category)',
            'CREATE INDEX IF NOT EXISTS idx_trending_topics_detailed_score ON trending_topics_detailed(trending_score DESC)',
            'CREATE INDEX IF NOT EXISTS idx_trending_topics_detailed_article_count ON trending_topics_detailed(article_count DESC)',
            'CREATE INDEX IF NOT EXISTS idx_trending_topics_detailed_sources ON trending_topics_detailed(sources_count DESC)'
        ],
        'refresh_interval': 1800  # 30 minutos
    },
    
    'daily_metrics_enhanced': {
        'sql': '''
            CREATE MATERIALIZED VIEW IF NOT EXISTS daily_metrics_enhanced AS
            SELECT 
                DATE_TRUNC('day', a.created_at) as metric_date,
                DATE_TRUNC('hour', a.created_at) as metric_hour,
                COUNT(*) as articles_created,
                COUNT(CASE WHEN a.processing_status = 'completed' THEN 1 END) as articles_processed,
                COUNT(CASE WHEN a.processing_status = 'failed' THEN 1 END) as articles_failed,
                COUNT(CASE WHEN a.processing_status = 'pending' THEN 1 END) as articles_pending,
                ROUND(AVG(a.relevance_score), 3) as avg_relevance_score,
                ROUND(AVG(a.sentiment_score), 3) as avg_sentiment_score,
                COUNT(DISTINCT a.source_id) as active_sources,
                COUNT(DISTINCT a.duplicate_group_id) as unique_articles,
                COUNT(DISTINCT a.duplicate_group_id) FILTER (WHERE a.duplicate_group_id IS NOT NULL) as duplicate_groups,
                ROUND(COUNT(DISTINCT a.duplicate_group_id) FILTER (WHERE a.duplicate_group_id IS NOT NULL) * 100.0 / NULLIF(COUNT(*), 0), 2) as duplicate_percentage
            FROM articles a
            WHERE a.created_at > NOW() - INTERVAL '60 days'
            GROUP BY DATE_TRUNC('day', a.created_at), DATE_TRUNC('hour', a.created_at)
            ORDER BY metric_date DESC, metric_hour DESC;
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS idx_daily_metrics_enhanced_date ON daily_metrics_enhanced(metric_date DESC)',
            'CREATE INDEX IF NOT EXISTS idx_daily_metrics_enhanced_hour ON daily_metrics_enhanced(metric_hour DESC)',
            'CREATE INDEX IF NOT EXISTS idx_daily_metrics_enhanced_processed ON daily_metrics_enhanced(metric_date, articles_processed)'
        ],
        'refresh_interval': 3600  # 1 hora
    },
    
    'performance_analytics': {
        'sql': '''
            CREATE MATERIALIZED VIEW IF NOT EXISTS performance_analytics AS
            SELECT 
                at.task_type,
                DATE_TRUNC('day', at.scheduled_at) as analysis_date,
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN at.status = 'completed' THEN 1 END) as completed_tasks,
                COUNT(CASE WHEN at.status = 'failed' THEN 1 END) as failed_tasks,
                ROUND(AVG(at.processing_duration_ms), 2) as avg_processing_time,
                ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY at.processing_duration_ms), 2) as median_processing_time,
                ROUND(PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY at.processing_duration_ms), 2) as p90_processing_time,
                MAX(at.processing_duration_ms) as max_processing_time,
                COUNT(CASE WHEN at.retry_count > 0 THEN 1 END) as retried_tasks,
                ROUND(COUNT(CASE WHEN at.retry_count > 0 THEN 1 END) * 100.0 / COUNT(*), 2) as retry_percentage
            FROM analysis_tasks at
            WHERE at.scheduled_at > NOW() - INTERVAL '30 days'
            GROUP BY at.task_type, DATE_TRUNC('day', at.scheduled_at)
            ORDER BY analysis_date DESC, at.task_type;
        ''',
        'indexes': [
            'CREATE INDEX IF NOT EXISTS idx_performance_analytics_task_type ON performance_analytics(task_type)',
            'CREATE INDEX IF NOT EXISTS idx_performance_analytics_date ON performance_analytics(analysis_date DESC)',
            'CREATE INDEX IF NOT EXISTS idx_performance_analytics_completion ON performance_analytics(completed_tasks DESC)'
        ],
        'refresh_interval': 900  # 15 minutos
    }
}

# Configuración de alertas
ALERT_CONFIG = {
    'performance_alerts': {
        'slow_query_threshold': 2000,  # ms
        'cache_hit_ratio_threshold': 0.7,  # 70%
        'high_memory_usage_threshold': 500,  # MB
        'failed_queries_threshold': 10  # per minute
    },
    
    'notification_channels': {
        'log': True,
        'email': False,
        'slack': False,
        'webhook': False
    },
    
    'alert_cooldown': 300  # 5 minutos entre alertas del mismo tipo
}

# Configuración de logs
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': 'logs/database_optimizer.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'database_optimizer': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


def get_redis_client(config: Optional[Dict[str, Any]] = None) -> redis.Redis:
    """
    Crea y configura el cliente Redis optimizado
    
    Args:
        config: Configuración personalizada opcional
        
    Returns:
        Cliente Redis configurado
    """
    redis_config = config or {}
    
    # Configuración por defecto
    default_config = {
        'host': os.getenv('REDIS_HOST', 'localhost'),
        'port': int(os.getenv('REDIS_PORT', 6379)),
        'db': int(os.getenv('REDIS_DB', 0)),
        'decode_responses': True,
        'socket_timeout': 5,
        'socket_connect_timeout': 5,
        'retry_on_timeout': True,
        'health_check_interval': 30,
        'max_connections': 20,
        'connection_pool_kwargs': {
            'retry_on_timeout': True,
            'socket_timeout': 5,
            'socket_connect_timeout': 5
        }
    }
    
    # Combinar configuraciones
    final_config = {**default_config, **redis_config}
    
    try:
        client = redis.Redis(**final_config)
        # Test connection
        client.ping()
        return client
    except redis.ConnectionError as e:
        raise ConnectionError(f"Error conectando a Redis: {e}")


def create_optimized_engine(database_url: str) -> Any:
    """
    Crea un engine SQLAlchemy optimizado
    
    Args:
        database_url: URL de la base de datos
        
    Returns:
        Engine SQLAlchemy configurado
    """
    from sqlalchemy import create_engine
    
    # Configuración optimizada para PostgreSQL
    engine_kwargs = {
        'pool_size': 20,
        'max_overflow': 30,
        'pool_pre_ping': True,
        'pool_recycle': 3600,  # 1 hora
        'pool_timeout': 30,
        'echo': False,  # Cambiar a True para debugging
        'echo_pool': False
    }
    
    # Configuración específica para PostgreSQL
    if 'postgresql' in database_url:
        engine_kwargs.update({
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'ai_news_aggregator'
            },
            'server_side_cursors': True  # Para cursors grandes
        })
    
    return create_engine(database_url, **engine_kwargs)


def setup_database_optimizer(redis_client: redis.Redis, engine) -> 'DatabaseOptimizer':
    """
    Configura e inicializa el optimizador de base de datos
    
    Args:
        redis_client: Cliente Redis configurado
        engine: Engine SQLAlchemy
        
    Returns:
        Instancia del optimizador configurado
    """
    from .database_optimizer import init_database_optimizer
    
    # Configurar logging
    import logging.config
    logging.config.dictConfig(LOGGING_CONFIG)
    
    # Inicializar optimizador
    optimizer = init_database_optimizer(redis_client, engine)
    
    logger = logging.getLogger(__name__)
    logger.info("Database Optimizer configured and initialized")
    
    return optimizer


# Factory function para facilitar la integración
def create_database_optimizer_service(
    database_url: Optional[str] = None,
    redis_config: Optional[Dict[str, Any]] = None
) -> 'DatabaseOptimizer':
    """
    Factory function para crear el servicio completo de optimización
    
    Args:
        database_url: URL de base de datos (opcional)
        redis_config: Configuración de Redis (opcional)
        
    Returns:
        Servicio de optimización configurado
    """
    # Configuración por defecto desde variables de entorno
    if not database_url:
        database_url = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/ai_news')
    
    # Crear clientes
    redis_client = get_redis_client(redis_config)
    engine = create_optimized_engine(database_url)
    
    # Crear optimizador
    optimizer = setup_database_optimizer(redis_client, engine)
    
    return optimizer


# Configuración para diferentes entornos
ENVIRONMENT_CONFIGS = {
    'development': {
        'cache': {
            'default_ttl': 60,  # Cache más corto en desarrollo
            'max_memory_items': 100
        },
        'monitoring': {
            'slow_query_threshold_ms': 500,
            'enable_performance_tracking': True
        },
        'indexes': {
            'concurrent_creation': False  # Más seguro en desarrollo
        }
    },
    
    'testing': {
        'cache': {
            'default_ttl': 5,
            'max_memory_items': 10
        },
        'monitoring': {
            'enable_performance_tracking': False
        },
        'materialized_views': {
            'auto_create': False,
            'auto_refresh': False
        }
    },
    
    'production': {
        'cache': {
            'default_ttl': 300,
            'max_memory_items': 1000
        },
        'monitoring': {
            'slow_query_threshold_ms': 2000,
            'enable_performance_tracking': True
        },
        'indexes': {
            'concurrent_creation': True
        },
        'materialized_views': {
            'auto_create': True,
            'auto_refresh': True
        }
    }
}


def get_config_for_environment(env: str = None) -> Dict[str, Any]:
    """
    Obtiene configuración específica para el entorno
    
    Args:
        env: Nombre del entorno ('development', 'testing', 'production')
        
    Returns:
        Configuración del entorno
    """
    if not env:
        env = os.getenv('ENVIRONMENT', 'development')
    
    env_config = ENVIRONMENT_CONFIGS.get(env, ENVIRONMENT_CONFIGS['development'])
    
    # Combinar con configuración base
    config = DATABASE_OPTIMIZER_CONFIG.copy()
    config.update(env_config)
    
    return config