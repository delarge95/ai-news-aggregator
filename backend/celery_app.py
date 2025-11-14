"""
Configuración principal de Celery para procesamiento asíncrono
AI News Aggregator - Sistema de Background Tasks
"""

import os
from celery import Celery, signals
from kombu import Queue
from app.core.config import settings

# Configuración de Celery
celery_app = Celery(
    'ai_news_aggregator',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Configuración de Celery
celery_app.conf.update(
    # Configuración de tareas
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Configuración de resultado
    result_expires=3600,  # 1 hora
    result_persistent=True,
    
    # Configuración de routing
    task_routes={
        'app.tasks.article_tasks.analyze_article_async': {'queue': 'ai_analysis'},
        'app.tasks.batch_tasks.batch_analyze_articles': {'queue': 'ai_analysis'},
        'app.tasks.classification_tasks.classify_topics_batch': {'queue': 'ai_classification'},
        'app.tasks.summary_tasks.generate_summaries_batch': {'queue': 'ai_summaries'},
    },
    
    # Configuración de colas
    task_default_queue='default',
    task_queues=(
        Queue('default', routing_key='default'),
        Queue('ai_analysis', routing_key='ai_analysis'),
        Queue('ai_classification', routing_key='ai_classification'),
        Queue('ai_summaries', routing_key='ai_summaries'),
    ),
    
    # Configuración de worker
    worker_prefetch_multiplier=1,
    task_acks_late=False,
    worker_max_tasks_per_child=1000,
    
    # Configuración de monitoreo
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Configuración de retries
    task_autoretry_for=(Exception,),
    task_retry_kwargs={'max_retries': 3},
    task_retry_backoff=True,
    task_retry_backoff_max=700,
    task_retry_jitter=False,
    
    # Configuración de rate limiting
    task_annotations={
        'app.tasks.article_tasks.analyze_article_async': {'rate_limit': '10/m'},
        'app.tasks.batch_tasks.batch_analyze_articles': {'rate_limit': '5/m'},
        'app.tasks.classification_tasks.classify_topics_batch': {'rate_limit': '8/m'},
        'app.tasks.summary_tasks.generate_summaries_batch': {'rate_limit': '6/m'},
    }
)

# Configuración específica para beat (scheduled tasks)
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

# Extensiones de Celery
if os.getenv('CELERY_FLOWER_USER') and os.getenv('CELERY_FLOWER_PASSWORD'):
    celery_app.conf.update(
        broker_url=settings.CELERY_BROKER_URL,
        result_backend=settings.CELERY_RESULT_BACKEND,
        accept_content=['json'],
        task_serializer='json',
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )

# Signal handlers para logging y monitoreo
@signals.task_prerun.connect
def task_prerun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, **kwds):
    """Handler ejecutado antes de cada tarea"""
    from loguru import logger
    logger.info(f"🔄 Iniciando tarea {task.name} [{task_id}]")
    logger.debug(f"Args: {args}, Kwargs: {kwargs}")

@signals.task_postrun.connect
def task_postrun_handler(sender=None, task_id=None, task=None, args=None, kwargs=None, retval=None, state=None, **kwds):
    """Handler ejecutado después de cada tarea"""
    from loguru import logger
    logger.info(f"✅ Tarea completada {task.name} [{task_id}] - Estado: {state}")
    logger.debug(f"Resultado: {retval}")

@signals.task_failure.connect
def task_failure_handler(sender=None, task_id=None, exception=None, traceback=None, **kwds):
    """Handler ejecutado cuando una tarea falla"""
    from loguru import logger
    logger.error(f"💥 Falla de tarea {sender.name} [{task_id}]: {exception}")
    logger.debug(f"Traceback: {traceback}")

@signals.worker_process_init.connect
def worker_process_init_handler(sender=None, **kwds):
    """Handler ejecutado al inicializar cada proceso worker"""
    from loguru import logger
    logger.info(f"🚀 Worker process {sender.pid} inicializado")

@signals.worker_process_shutdown.connect
def worker_process_shutdown_handler(sender=None, **kwds):
    """Handler ejecutado al shutdown de cada proceso worker"""
    from loguru import logger
    logger.info(f"🛑 Worker process {sender.pid} cerrado")

if __name__ == '__main__':
    celery_app.start()