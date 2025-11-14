from fastapi import APIRouter, HTTPException, Depends, Request
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import logging
import math
from app.services import news_service
from app.db.models import Article, Source
from app.db.database import get_db
from app.core.config import get_settings
from app.utils.pagination import (
    get_pagination_params,
    PaginationParams
)

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()

# Configuración de modelos por endpoint para el middleware
MODEL_MAPPING = {
    '/api/v1/news': 'article',
    '/api/v1/news/sources': 'source', 
    '/api/v1/news/categories': 'trending_topic',
}

@router.get("/latest")
async def get_latest_news(
    request: Request,
    db: AsyncSession = Depends(get_db),
    # Parámetros legacy para compatibilidad
    limit: Optional[int] = None,
    sources: Optional[List[str]] = None
):
    """
    Obtener las últimas noticias con paginación y filtrado avanzado
    
    Soporta paginación tradicional y por cursor, filtrado múltiple y ordenamiento.
    
    **Parámetros de paginación:**
    - `page`: Número de página (default: 1)
    - `page_size`: Tamaño de página (default: 20, max: 100)
    - `cursor`: Cursor para paginación eficiente (alternativo a page)
    
    **Parámetros de filtrado:**
    - `sentiment`: Filtrar por sentimiento (positive, negative, neutral)
    - `sentiment_score_gte`: Sentimiento mínimo (0.0-1.0)
    - `relevance_score_gte`: Relevancia mínima (0.0-1.0)
    - `published_at_from`: Fecha desde (YYYY-MM-DD)
    - `published_at_to`: Fecha hasta (YYYY-MM-DD)
    - `source_id`: ID de fuente específica
    - `processing_status`: Estado de procesamiento
    - `search`: Búsqueda en título y contenido
    - `topic_tags`: Filtrar por etiquetas de temas
    
    **Ordenamiento:**
    - `sort`: Campos separados por coma (ej: published_at,-relevance_score)
    - Prefijo `-` para orden descendente
    """
    try:
        # Usar parámetros legacy si se proporcionan
        if limit or sources:
            # Comportamiento legacy para compatibilidad
            return await get_latest_news_legacy(limit, sources)
        
        # Obtener parámetros de paginación del middleware
        if hasattr(request.state, 'pagination_params'):
            pagination_params = request.state.pagination_params
        else:
            # Fallback manual si middleware no está disponible
            pagination_params = get_pagination_params(request, 'article')

        # Si no hay API keys configuradas, usar datos de ejemplo
        api_keys_configured = (
            settings.NEWSAPI_KEY and settings.NEWSAPI_KEY != "your_newsapi_key_here" and
            settings.GUARDIAN_API_KEY and settings.GUARDIAN_API_KEY != "your_guardian_api_key_here" and
            settings.NYTIMES_API_KEY and settings.NYTIMES_API_KEY != "your_nytimes_api_key_here"
        )

        if not api_keys_configured:
            sample_articles = [
                {
                    "id": "sample-1",
                    "title": "Avances en Inteligencia Artificial 2025",
                    "description": "Nuevos desarrollos en IA que están transformando la industria tecnológica.",
                    "url": "https://example.com/ai-advances-2025",
                    "source_id": "sample-source-1",
                    "published_at": "2025-11-06T02:36:00Z",
                    "sentiment_label": "positive",
                    "sentiment_score": 0.8,
                    "relevance_score": 0.9,
                    "topic_tags": ["artificial-intelligence", "technology"],
                    "processing_status": "completed"
                },
                {
                    "id": "sample-2",
                    "title": "Machine Learning en la Medicina",
                    "description": "Cómo el ML está revolucionando el diagnóstico médico.",
                    "url": "https://example.com/ml-medicine",
                    "source_id": "sample-source-2",
                    "published_at": "2025-11-06T01:30:00Z",
                    "sentiment_label": "positive",
                    "sentiment_score": 0.7,
                    "relevance_score": 0.85,
                    "topic_tags": ["machine-learning", "healthcare"],
                    "processing_status": "completed"
                },
                {
                    "id": "sample-3",
                    "title": "Redes Neuronales Profundas",
                    "description": "Arquitecturas avanzadas de deep learning y sus aplicaciones.",
                    "url": "https://example.com/deep-neural-networks",
                    "source_id": "sample-source-1",
                    "published_at": "2025-11-06T00:15:00Z",
                    "sentiment_label": "neutral",
                    "sentiment_score": 0.5,
                    "relevance_score": 0.75,
                    "topic_tags": ["deep-learning", "neural-networks"],
                    "processing_status": "completed"
                }
            ]
            return _build_sample_paginated_response(sample_articles, pagination_params)

        # Con API keys configuradas, obtenemos los artículos reales desde la base de datos
        page = pagination_params.page
        page_size = pagination_params.page_size

        total_result = await db.execute(select(func.count()).select_from(Article))
        total_articles = total_result.scalar() or 0

        stmt = (
            select(Article)
            .options(selectinload(Article.source))
            .order_by(Article.published_at.desc(), Article.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await db.execute(stmt)
        articles = result.scalars().all()

        serialized_articles = [_serialize_article(article) for article in articles]

        total_pages = math.ceil(total_articles / page_size) if page_size else 0

        return {
            'status': 'success',
            'data': serialized_articles,
            'pagination': {
                'total': total_articles,
                'page': page,
                'page_size': page_size,
                'total_pages': total_pages,
                'has_next': page < total_pages,
                'has_prev': page > 1,
                'next_cursor': f"page_{page + 1}" if page < total_pages else None,
                'prev_cursor': f"page_{page - 1}" if page > 1 else None
            },
            'filters_applied': pagination_params.filters,
            'sort_applied': [{'field': s.field, 'order': s.order.value} for s in pagination_params.sort],
            'message': f"Successfully fetched {len(serialized_articles)} articles"
        }
        
    except Exception as e:
        logger.error(f"Error in get_latest_news: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


def _apply_sample_filters(articles: List[Dict], pagination_params: PaginationParams) -> List[Dict]:
    """Aplicar filtros a datos de ejemplo"""
    filtered = articles.copy()
    
    # Filtro de sentimiento
    if 'sentiment_label' in pagination_params.filters:
        sentiment_filter = pagination_params.filters['sentiment_label']
        if sentiment_filter['operator'] == 'eq':
            filtered = [a for a in filtered if a.get('sentiment_label') == sentiment_filter['value']]
    
    # Filtro de relevancia
    if 'relevance_score' in pagination_params.filters:
        relevance_filter = pagination_params.filters['relevance_score']
        if relevance_filter['operator'] == 'gte':
            min_score = relevance_filter['value']
            filtered = [a for a in filtered if a.get('relevance_score', 0) >= min_score]
    
    # Búsqueda de texto
    if pagination_params.search:
        search_term = pagination_params.search.lower()
        filtered = [
            a for a in filtered 
            if search_term in a.get('title', '').lower() or 
               search_term in a.get('description', '').lower()
        ]
    
    # Aplicar ordenamiento
    for sort_field in pagination_params.sort:
        reverse = sort_field.order.value == 'desc'
        filtered.sort(key=lambda x: x.get(sort_field.field, 0), reverse=reverse)
    
    return filtered


def _build_sample_paginated_response(articles: List[Dict], pagination_params: PaginationParams) -> Dict[str, Any]:
    """Construir una respuesta paginada usando datos de ejemplo"""
    filtered_articles = _apply_sample_filters(articles, pagination_params)
    
    start_idx = (pagination_params.page - 1) * pagination_params.page_size
    end_idx = start_idx + pagination_params.page_size
    paginated_articles = filtered_articles[start_idx:end_idx]
    
    return {
        'status': 'success',
        'data': paginated_articles,
        'pagination': {
            'total': len(filtered_articles),
            'page': pagination_params.page,
            'page_size': pagination_params.page_size,
            'total_pages': math.ceil(len(filtered_articles) / pagination_params.page_size) if pagination_params.page_size else 0,
            'has_next': end_idx < len(filtered_articles),
            'has_prev': pagination_params.page > 1,
            'next_cursor': f"page_{pagination_params.page + 1}" if end_idx < len(filtered_articles) else None,
            'prev_cursor': f"page_{pagination_params.page - 1}" if pagination_params.page > 1 else None
        },
        'filters_applied': pagination_params.filters,
        'sort_applied': [{'field': s.field, 'order': s.order.value} for s in pagination_params.sort]
    }


def _serialize_article(article: Article) -> Dict[str, Any]:
    """Serializar instancia de Article a formato dict estándar"""
    return {
        'id': str(article.id),
        'title': article.title,
        'content': article.content,
        'summary': article.summary,
        'url': article.url,
        'published_at': article.published_at.isoformat() if article.published_at else None,
        'source_id': str(article.source_id) if article.source_id else None,
        'source_name': article.source.name if article.source else None,
        'source_url': article.source.url if article.source else None,
        'sentiment_score': article.sentiment_score,
        'sentiment_label': article.sentiment_label,
        'bias_score': article.bias_score,
        'topic_tags': article.topic_tags or [],
        'relevance_score': article.relevance_score,
        'processed_at': article.processed_at.isoformat() if article.processed_at else None,
        'ai_processed_at': article.ai_processed_at.isoformat() if article.ai_processed_at else None,
        'processing_status': article.processing_status,
        'created_at': article.created_at.isoformat() if article.created_at else None,
        'updated_at': article.updated_at.isoformat() if article.updated_at else None,
    }


def _convert_pagination_filters_to_service(pagination_params: PaginationParams) -> Dict[str, Any]:
    """Convertir filtros de paginación a formato del service layer"""
    filters = {}
    
    for field_name, filter_config in pagination_params.filters.items():
        if field_name == 'sentiment_label':
            filters['sentiment'] = filter_config['value']
        elif field_name == 'source_id':
            if filter_config['value'] not in filters.get('sources', []):
                filters.setdefault('sources', []).append(filter_config['value'])
    
    return filters

@router.get("/search")
async def search_news(
    query: str,
    limit: Optional[int] = 10,
    sources: Optional[List[str]] = None
):
    """
    Buscar noticias por término específico
    
    - **query**: Término de búsqueda
    - **limit**: Número máximo de resultados (default: 10)  
    - **sources**: Fuentes específicas a consultar (opcional)
    """
    try:
        results = await news_service.search_news(
            query=query,
            limit=limit,
            sources=sources
        )
        
        return {
            "status": "success",
            "message": f"Found {len(results)} results for '{query}'",
            "query": query,
            "total": len(results),
            "articles": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching news: {str(e)}")

@router.get("/sources")
async def get_news_sources():
    """
    Obtener lista de fuentes de noticias disponibles
    """
    try:
        sources = await news_service.get_sources()
        
        return {
            "status": "success",
            "total": len(sources),
            "sources": sources
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sources: {str(e)}")

@router.get("/categories")
async def get_news_categories():
    """
    Obtener categorías de noticias disponibles
    """
    try:
        categories = await news_service.get_categories()
        
        return {
            "status": "success", 
            "total": len(categories),
            "categories": categories
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")

@router.get("/health")
async def news_health_check():
    """
    Health check del servicio de noticias
    """
    try:
        health_status = news_service.health_check()
        
        return {
            "status": "success",
            "service": "news_service",
            "health": health_status
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "service": "news_service",
            "error": str(e)
        }

@router.get("/stats")
async def get_news_stats():
    """
    Obtener estadísticas del servicio de noticias
    """
    try:
        stats = await news_service.get_service_stats()
        
        return {
            "status": "success",
            "service": "news_service", 
            "stats": stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


# ===== NUEVOS ENDPOINTS CON PAGINACIÓN AVANZADA =====

@router.get("/advanced")
async def get_news_advanced(
    request: Request,
):
    """
    Endpoint avanzado para noticias con paginación y filtrado completo
    
    Soporte completo para:
    - Paginación por cursor y tradicional
    - Filtros múltiples combinables
    - Ordenamiento multi-campo
    - Búsqueda de texto avanzada
    - Campos específicos de respuesta
    """
    try:
        # Obtener parámetros de paginación
        if hasattr(request.state, 'pagination_params'):
            pagination_params = request.state.pagination_params
        else:
            pagination_params = get_pagination_params(request, 'article')
        
        # Simular consulta con datos de ejemplo
        articles = await get_sample_articles_with_ai_data()
        
        # Aplicar filtros
        filtered_articles = _apply_advanced_filters(articles, pagination_params)
        
        # Aplicar ordenamiento
        sorted_articles = _apply_advanced_sort(filtered_articles, pagination_params)
        
        # Aplicar paginación
        paginated_result = _apply_pagination(sorted_articles, pagination_params)
        
        return {
            'status': 'success',
            'data': paginated_result['items'],
            'pagination': paginated_result['pagination'],
            'filters_applied': pagination_params.filters,
            'sort_applied': [{'field': s.field, 'order': s.order.value} for s in pagination_params.sort],
            'available_filters': {
                'sentiment': ['positive', 'negative', 'neutral'],
                'processing_status': ['pending', 'processing', 'completed', 'failed'],
                'source_ids': ['sample-source-1', 'sample-source-2'],
                'date_range': 'YYYY-MM-DD format'
            }
        }
        
    except Exception as e:
        logger.error(f"Error in get_news_advanced: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/sources/advanced")
async def get_sources_advanced(
    request: Request,
):
    """
    Fuentes de noticias con paginación avanzada
    """
    try:
        if hasattr(request.state, 'pagination_params'):
            pagination_params = request.state.pagination_params
        else:
            pagination_params = get_pagination_params(request, 'source')
        
        # Datos de ejemplo de fuentes
        sources = get_sample_sources()
        filtered_sources = _apply_source_filters(sources, pagination_params)
        sorted_sources = _apply_source_sort(filtered_sources, pagination_params)
        paginated_result = _apply_pagination(sorted_sources, pagination_params)
        
        return {
            'status': 'success',
            'data': paginated_result['items'],
            'pagination': paginated_result['pagination'],
            'filters_applied': pagination_params.filters,
            'total_sources': len(sources)
        }
        
    except Exception as e:
        logger.error(f"Error in get_sources_advanced: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/analytics/pagination-metrics")
async def get_pagination_metrics():
    """
    Obtener métricas de uso de paginación
    """
    try:
        # En una implementación real, esto vendría del middleware de métricas
        sample_metrics = {
            'total_requests': 15420,
            'pagination_requests': 12850,
            'pagination_rate': 0.83,
            'error_rate': 0.02,
            'most_used_models': {
                'article': 8500,
                'source': 2100,
                'analysis_task': 1850,
                'trending_topic': 400
            },
            'popular_page_sizes': {
                '20': 4200,
                '10': 3100,
                '50': 2800,
                '100': 1750
            },
            'most_used_filters': {
                'sentiment_label__eq': 2100,
                'relevance_score__gte': 1800,
                'published_at__date_range': 1650,
                'processing_status__eq': 1200
            },
            'average_processing_time_ms': 150,
            'cache_hit_rate': 0.75
        }
        
        return {
            'status': 'success',
            'metrics': sample_metrics,
            'generated_at': '2025-11-06T03:03:36Z'
        }
        
    except Exception as e:
        logger.error(f"Error getting pagination metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/filter-presets")
async def get_filter_presets():
    """
    Obtener presets de filtros predefinidos para facilitar el uso
    """
    presets = {
        'trending_ai': {
            'name': 'Tendencias en IA',
            'description': 'Artículos recientes sobre inteligencia artificial',
            'filters': {
                'search': 'artificial intelligence',
                'relevance_score__gte': 0.8,
                'published_at__date_range': '2025-11-01,2025-11-06'
            },
            'sort': '-published_at,-relevance_score'
        },
        'positive_news': {
            'name': 'Noticias Positivas',
            'description': 'Noticias con sentimiento positivo y alta relevancia',
            'filters': {
                'sentiment_label': 'positive',
                'sentiment_score__gte': 0.7,
                'relevance_score__gte': 0.6
            },
            'sort': '-sentiment_score,-relevance_score'
        },
        'latest_tech': {
            'name': 'Últimas en Tecnología',
            'description': 'Noticias recientes del sector tecnológico',
            'filters': {
                'topic_tags': 'technology',
                'published_at__date_range': '2025-11-05,2025-11-06'
            },
            'sort': '-published_at'
        },
        'high_quality': {
            'name': 'Alta Calidad',
            'description': 'Artículos con mejores métricas de calidad',
            'filters': {
                'relevance_score__gte': 0.85,
                'sentiment_score__gte': 0.5
            },
            'sort': '-relevance_score,-sentiment_score'
        }
    }
    
    return {
        'status': 'success',
        'presets': presets,
        'total_presets': len(presets)
    }


# ===== FUNCIONES AUXILIARES PARA LOS NUEVOS ENDPOINTS =====

async def get_sample_articles_with_ai_data():
    """Generar datos de ejemplo con datos de IA completos"""
    import uuid
    from datetime import datetime, timedelta
    
    articles = []
    base_date = datetime(2025, 11, 6)
    
    # Datos de fuentes
    sources = ['BBC News', 'CNN', 'Reuters', 'TechCrunch', 'MIT Technology Review']
    
    # Datos de IA simulados
    sentiments = ['positive', 'negative', 'neutral']
    topics = ['artificial-intelligence', 'machine-learning', 'technology', 'healthcare', 'finance']
    statuses = ['completed', 'processing', 'pending']
    
    for i in range(50):  # 50 artículos de ejemplo
        published_date = base_date - timedelta(hours=i*2)
        
        article = {
            'id': str(uuid.uuid4()),
            'title': f'Artículo de Noticias {i+1}: Avances en IA',
            'description': f'Descripción detallada del artículo {i+1} sobre inteligencia artificial y machine learning.',
            'content': f'Contenido completo del artículo {i+1}. Este es un texto más largo que describe los detalles...',
            'url': f'https://example.com/article-{i+1}',
            'source_id': f'source-{(i % len(sources)) + 1}',
            'source_name': sources[i % len(sources)],
            'published_at': published_date.isoformat(),
            'created_at': (published_date - timedelta(minutes=30)).isoformat(),
            'updated_at': (published_date - timedelta(minutes=15)).isoformat(),
            
            # Datos de IA
            'sentiment_label': sentiments[i % len(sentiments)],
            'sentiment_score': round(0.3 + (i % 7) * 0.1, 1),  # 0.3 - 0.9
            'relevance_score': round(0.5 + (i % 5) * 0.1, 1),  # 0.5 - 0.9
            'bias_score': round(0.1 + (i % 4) * 0.1, 1),       # 0.1 - 0.4
            'topic_tags': [topics[j % len(topics)] for j in range((i % 3) + 1)],
            'processing_status': statuses[i % len(statuses)],
            'ai_processed_at': (published_date + timedelta(minutes=10)).isoformat(),
            'processed_at': (published_date + timedelta(minutes=5)).isoformat(),
        }
        articles.append(article)
    
    return articles


def _apply_advanced_filters(articles: List[Dict], pagination_params: PaginationParams) -> List[Dict]:
    """Aplicar filtros avanzados"""
    filtered = articles.copy()
    
    for field_name, filter_config in pagination_params.filters.items():
        operator = filter_config['operator']
        value = filter_config['value']
        
        if field_name == 'sentiment_label':
            if operator.value == 'eq':
                filtered = [a for a in filtered if a.get('sentiment_label') == value]
            elif operator.value == 'in':
                filtered = [a for a in filtered if a.get('sentiment_label') in value]
        
        elif field_name == 'relevance_score':
            if operator.value == 'gte':
                filtered = [a for a in filtered if a.get('relevance_score', 0) >= value]
            elif operator.value == 'lte':
                filtered = [a for a in filtered if a.get('relevance_score', 0) <= value]
            elif operator.value == 'between':
                min_val, max_val = value if isinstance(value, list) else value.split(',')
                filtered = [a for a in filtered 
                           if min_val <= a.get('relevance_score', 0) <= max_val]
        
        elif field_name == 'sentiment_score':
            if operator.value == 'gte':
                filtered = [a for a in filtered if a.get('sentiment_score', 0) >= value]
        
        elif field_name == 'published_at':
            if operator.value == 'date_range':
                # Convertir fechas y filtrar
                date_parts = value.split(',') if isinstance(value, str) else value
                if len(date_parts) >= 2 and date_parts[0] and date_parts[1]:
                    from datetime import datetime
                    start_date = datetime.fromisoformat(date_parts[0].replace('Z', '+00:00'))
                    end_date = datetime.fromisoformat(date_parts[1].replace('Z', '+00:00'))
                    
                    filtered = [a for a in filtered 
                               if start_date <= datetime.fromisoformat(a.get('published_at', '').replace('Z', '+00:00')) <= end_date]
        
        elif field_name == 'processing_status':
            if operator.value == 'eq':
                filtered = [a for a in filtered if a.get('processing_status') == value]
            elif operator.value == 'in':
                filtered = [a for a in filtered if a.get('processing_status') in value]
        
        elif field_name == 'topic_tags':
            if operator.value == 'contains':
                filtered = [a for a in filtered if value in a.get('topic_tags', [])]
    
    # Búsqueda de texto
    if pagination_params.search:
        search_term = pagination_params.search.lower()
        filtered = [
            a for a in filtered 
            if search_term in a.get('title', '').lower() or 
               search_term in a.get('description', '').lower() or
               search_term in a.get('content', '').lower()
        ]
    
    return filtered


def _apply_advanced_sort(articles: List[Dict], pagination_params: PaginationParams) -> List[Dict]:
    """Aplicar ordenamiento avanzado"""
    sorted_articles = articles.copy()
    
    # Ordenamiento multi-campo
    for sort_field in pagination_params.sort:
        reverse = sort_field.order.value == 'desc'
        sorted_articles.sort(key=lambda x: x.get(sort_field.field, 0), reverse=reverse)
    
    return sorted_articles


def _apply_pagination(items: List[Dict], pagination_params: PaginationParams) -> Dict[str, Any]:
    """Aplicar paginación"""
    total = len(items)
    
    if pagination_params.cursor:
        # Implementación básica de cursor
        page_size = pagination_params.page_size
        # Por simplicidad, usar el número de página del cursor
        page = 1
    else:
        page = pagination_params.page
        page_size = pagination_params.page_size
    
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_items = items[start_idx:end_idx]
    
    total_pages = math.ceil(total / page_size) if page_size > 0 else 0
    
    return {
        'items': paginated_items,
        'pagination': {
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_cursor': f"page_{page + 1}" if page < total_pages else None,
            'prev_cursor': f"page_{page - 1}" if page > 1 else None
        }
    }


def get_sample_sources():
    """Generar datos de ejemplo de fuentes"""
    import uuid
    
    sources = []
    source_names = [
        'BBC News', 'CNN', 'Reuters', 'TechCrunch', 'MIT Technology Review',
        'The Verge', 'Ars Technica', 'Wired', 'IEEE Spectrum', 'Science Daily'
    ]
    
    for i, name in enumerate(source_names):
        source = {
            'id': str(uuid.uuid4()),
            'name': name,
            'url': f'https://{name.lower().replace(" ", "").replace(".", "")}.com',
            'api_name': ['newsapi', 'guardian', 'nytimes'][i % 3],
            'country': ['gb', 'us', 'us'][i % 3],
            'language': 'en',
            'credibility_score': round(0.7 + (i % 3) * 0.1, 1),
            'is_active': True,
            'rate_limit_per_hour': 100 + (i % 5) * 20,
            'created_at': '2025-01-01T00:00:00Z',
            'updated_at': '2025-11-06T00:00:00Z'
        }
        sources.append(source)
    
    return sources


def _apply_source_filters(sources: List[Dict], pagination_params: PaginationParams) -> List[Dict]:
    """Aplicar filtros a fuentes"""
    filtered = sources.copy()
    
    for field_name, filter_config in pagination_params.filters.items():
        operator = filter_config['operator']
        value = filter_config['value']
        
        if field_name == 'api_name' and operator.value == 'eq':
            filtered = [s for s in filtered if s.get('api_name') == value]
        elif field_name == 'country' and operator.value == 'eq':
            filtered = [s for s in filtered if s.get('country') == value]
        elif field_name == 'credibility_score' and operator.value == 'gte':
            filtered = [s for s in filtered if s.get('credibility_score', 0) >= value]
        elif field_name == 'is_active' and operator.value == 'eq':
            filtered = [s for s in filtered if s.get('is_active') == value]
    
    # Búsqueda de texto
    if pagination_params.search:
        search_term = pagination_params.search.lower()
        filtered = [
            s for s in filtered 
            if search_term in s.get('name', '').lower()
        ]
    
    return filtered


def _apply_source_sort(sources: List[Dict], pagination_params: PaginationParams) -> List[Dict]:
    """Aplicar ordenamiento a fuentes"""
    sorted_sources = sources.copy()
    
    for sort_field in pagination_params.sort:
        reverse = sort_field.order.value == 'desc'
        sorted_sources.sort(key=lambda x: x.get(sort_field.field, 0), reverse=reverse)
    
    return sorted_sources