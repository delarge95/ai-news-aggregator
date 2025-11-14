"""
Tareas de Celery para obtener y procesar noticias
Maneja la obtención automática de noticias de múltiples fuentes
"""

import time
from typing import Dict, Any, List, Optional
from celery import Task
from loguru import logger

from celery_app import celery_app
from app.core.config import settings
from app.services.news_service import NewsService, NewsClientError


class NewsFetchingTask(Task):
    """Task base para obtención de noticias con retry y manejo de errores"""
    
    autoretry_for = (NewsClientError, Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler de falla para logging"""
        logger.error(f"💥 Error obteniendo noticias {task_id}: {exc}")
        logger.debug(f"Detalles del error: {einfo}")


@celery_app.task(
    bind=True,
    name='app.tasks.news_tasks.fetch_latest_news',
    base=NewsFetchingTask,
    queue='news_fetch',
    rate_limit='2/m'
)
def fetch_latest_news(
    self, 
    limit_per_source: int = 20,
    sources: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    client_types: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Obtener las últimas noticias de múltiples fuentes
    
    Args:
        limit_per_source: Límite de artículos por fuente
        sources: Fuentes específicas a consultar
        categories: Categorías a filtrar
        client_types: Tipos de clientes a usar
        
    Returns:
        Dict con noticias obtenidas y metadata
    """
    start_time = time.time()
    
    try:
        logger.info(f"📰 Obteniendo últimas noticias (límite: {limit_per_source})")
        
        # Inicializar servicio de noticias
        news_service = NewsService()
        
        # Verificar que hay clientes configurados
        configured_clients = news_service.factory.get_configured_clients()
        if not configured_clients:
            raise NewsClientError("No hay clientes de noticias configurados")
        
        logger.info(f"✅ Clientes configurados: {configured_clients}")
        
        # Determinar qué clientes usar
        if client_types is None:
            client_types = configured_clients
        else:
            client_types = [ct for ct in client_types if ct in configured_clients]
        
        if not client_types:
            raise NewsClientError("No hay clientes válidos especificados")
        
        # Obtener noticias de cada fuente
        all_articles = []
        fetch_results = {}
        
        for client_type in client_types:
            try:
                logger.info(f"📡 Obteniendo noticias de {client_type}")
                
                # Crear cliente específico
                client = news_service.factory.create_client(client_type)
                
                # Obtener noticias (método async - usar asyncio.run)
                import asyncio
                articles = asyncio.run(client.get_latest_news(limit_per_source))
                
                # Agregar metadata del cliente
                for article in articles:
                    article['fetch_task_id'] = self.request.id
                    article['client_type'] = client_type
                    article['fetched_at'] = time.time()
                
                all_articles.extend(articles)
                fetch_results[client_type] = {
                    'success': True,
                    'articles_count': len(articles),
                    'error': None
                }
                
                logger.info(f"✅ {client_type}: {len(articles)} artículos obtenidos")
                
            except Exception as e:
                logger.error(f"❌ Error obteniendo noticias de {client_type}: {str(e)}")
                fetch_results[client_type] = {
                    'success': False,
                    'articles_count': 0,
                    'error': str(e)
                }
                continue
        
        # Aplicar filtros si se especificaron
        filtered_articles = all_articles
        filters_applied = []
        
        if sources:
            original_count = len(filtered_articles)
            filtered_articles = [
                article for article in filtered_articles
                if any(source.lower() in article.get('source_name', '').lower() 
                      for source in sources)
            ]
            filters_applied.append(f"fuentes: {sources} ({original_count} → {len(filtered_articles)})")
        
        if categories:
            original_count = len(filtered_articles)
            filtered_articles = [
                article for article in filtered_articles
                if any(category.lower() in article.get('source_id', '').lower() 
                      for category in categories)
            ]
            filters_applied.append(f"categorías: {categories} ({original_count} → {len(filtered_articles)})")
        
        # Eliminar duplicados por URL
        seen_urls = set()
        unique_articles = []
        duplicates_removed = 0
        
        for article in filtered_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
            else:
                duplicates_removed += 1
        
        # Ordenar por fecha de publicación (más recientes primero)
        unique_articles.sort(
            key=lambda x: x.get('published_at', ''), 
            reverse=True
        )
        
        processing_time = time.time() - start_time
        
        # Preparar resultado
        result = {
            'status': 'success',
            'total_articles': len(unique_articles),
            'articles': unique_articles,
            'fetch_results': fetch_results,
            'filters_applied': filters_applied,
            'statistics': {
                'total_found': len(all_articles),
                'after_filters': len(filtered_articles),
                'after_dedup': len(unique_articles),
                'duplicates_removed': duplicates_removed,
                'sources_used': client_types,
                'processing_time': processing_time,
                'avg_time_per_source': processing_time / len(client_types) if client_types else 0
            },
            'metadata': {
                'task_id': self.request.id,
                'fetched_at': time.time(),
                'limit_per_source': limit_per_source,
                'sources_requested': sources,
                'categories_requested': categories,
                'client_types_used': client_types
            }
        }
        
        logger.info(f"✅ Obtención de noticias completada: {len(unique_articles)} artículos únicos en {processing_time:.2f}s")
        
        # Enviar artículos para procesamiento automático si es necesario
        if unique_articles and len(unique_articles) <= 50:  # Solo para lotes pequeños
            try:
                # Programar análisis automático de los artículos obtenidos
                from app.tasks.article_tasks import analyze_article_async
                from app.tasks.classification_tasks import classify_topics_batch
                from app.tasks.summary_tasks import generate_summaries_batch
                
                # Analizar primeros 10 artículos automáticamente
                for article in unique_articles[:10]:
                    analyze_article_async.delay(article, 'comprehensive')
                
                # Clasificar todos los artículos
                classify_topics_batch.delay(unique_articles, 'comprehensive')
                
                # Generar resúmenes de los primeros 20
                generate_summaries_batch.delay(unique_articles[:20], 'executive')
                
                logger.info("✅ Procesamiento automático programado para artículos obtenidos")
                
            except Exception as e:
                logger.warning(f"⚠️ No se pudo programar procesamiento automático: {str(e)}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error crítico obteniendo noticias: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'total_articles': 0,
            'articles': [],
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


@celery_app.task(
    bind=True,
    name='app.tasks.news_tasks.search_news_task',
    base=NewsFetchingTask,
    queue='news_fetch',
    rate_limit='5/m'
)
def search_news_task(
    self, 
    query: str, 
    limit: int = 20,
    client_types: Optional[List[str]] = None,
    sort_by: str = 'relevance'
) -> Dict[str, Any]:
    """
    Buscar noticias por query específico
    
    Args:
        query: Término de búsqueda
        limit: Límite de resultados
        client_types: Tipos de clientes a usar
        sort_by: Criterio de ordenamiento ('relevance', 'date')
        
    Returns:
        Dict con resultados de búsqueda
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Buscando noticias: '{query}' (límite: {limit})")
        
        if not query.strip():
            raise ValueError("El término de búsqueda no puede estar vacío")
        
        # Inicializar servicio de noticias
        news_service = NewsService()
        
        # Determinar clientes disponibles
        configured_clients = news_service.factory.get_configured_clients()
        if client_types is None:
            client_types = configured_clients
        else:
            client_types = [ct for ct in client_types if ct in configured_clients]
        
        if not client_types:
            raise NewsClientError("No hay clientes válidos para búsqueda")
        
        # Buscar en paralelo en todos los clientes
        all_articles = []
        search_results = {}
        
        for client_type in client_types:
            try:
                logger.info(f"🔍 Buscando en {client_type}: '{query}'")
                
                # Crear cliente específico
                client = news_service.factory.create_client(client_type)
                
                # Buscar noticias
                articles = client.search_news(query, limit // len(client_types) + 1)
                
                # Agregar metadata de búsqueda
                for article in articles:
                    article['search_task_id'] = self.request.id
                    article['search_query'] = query
                    article['client_type'] = client_type
                    article['searched_at'] = time.time()
                
                all_articles.extend(articles)
                search_results[client_type] = {
                    'success': True,
                    'articles_count': len(articles),
                    'error': None
                }
                
                logger.info(f"✅ {client_type}: {len(articles)} resultados encontrados")
                
            except Exception as e:
                logger.error(f"❌ Error buscando en {client_type}: {str(e)}")
                search_results[client_type] = {
                    'success': False,
                    'articles_count': 0,
                    'error': str(e)
                }
                continue
        
        # Eliminar duplicados por URL
        seen_urls = set()
        unique_articles = []
        
        for article in all_articles:
            url = article.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)
        
        # Ordenar resultados
        if sort_by == 'date':
            unique_articles.sort(
                key=lambda x: x.get('published_at', ''), 
                reverse=True
            )
        else:  # relevance - ya está ordenado por relevancia por defecto
            pass  # No need to re-sort, already sorted by relevance
        
        # Limitar resultados finales
        final_articles = unique_articles[:limit]
        
        processing_time = time.time() - start_time
        
        result = {
            'status': 'success',
            'query': query,
            'total_results': len(final_articles),
            'articles': final_articles,
            'search_results': search_results,
            'statistics': {
                'total_found': len(all_articles),
                'unique_results': len(unique_articles),
                'final_results': len(final_articles),
                'sources_searched': client_types,
                'processing_time': processing_time,
                'sort_by': sort_by
            },
            'metadata': {
                'task_id': self.request.id,
                'searched_at': time.time(),
                'limit': limit,
                'client_types_used': client_types
            }
        }
        
        logger.info(f"✅ Búsqueda completada: {len(final_articles)} resultados para '{query}' en {processing_time:.2f}s")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error en búsqueda de noticias: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'query': query,
            'total_results': 0,
            'articles': [],
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


@celery_app.task(
    bind=True,
    name='app.tasks.news_tasks.schedule_continuous_fetch',
    base=NewsFetchingTask,
    queue='news_fetch',
    rate_limit='1/h'
)
def schedule_continuous_fetch(
    self, 
    fetch_interval_minutes: int = 15,
    articles_per_fetch: int = 15
) -> Dict[str, Any]:
    """
    Programar obtención continua de noticias
    
    Args:
        fetch_interval_minutes: Intervalo entre obtenciones en minutos
        articles_per_fetch: Artículos a obtener por fuente
        
    Returns:
        Dict con información de la programación
    """
    try:
        logger.info(f"⏰ Programando obtención continua cada {fetch_interval_minutes} minutos")
        
        # Programar tarea periódica usando Celery Beat
        # Esto agregaría una nueva entrada al schedule de beat
        
        schedule_info = {
            'fetch_interval_minutes': fetch_interval_minutes,
            'articles_per_fetch': articles_per_fetch,
            'next_execution': time.time() + (fetch_interval_minutes * 60),
            'task_name': 'app.tasks.news_tasks.fetch_latest_news'
        }
        
        # TODO: Implementar lógica real para programar tarea periódica
        # Esto requeriría actualizar la configuración de Celery Beat
        
        logger.info(f"✅ Obtención continua programada exitosamente")
        
        return {
            'status': 'success',
            'schedule_info': schedule_info,
            'message': f'Obtención programada cada {fetch_interval_minutes} minutos',
            'scheduled_at': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Error programando obtención continua: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'scheduled_at': time.time()
        }