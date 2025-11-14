"""
AI Analysis endpoints for AI News Aggregator
Provides article analysis, batch processing, and task management
"""

import uuid
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, asc

# Importar servicios y modelos
from app.core.config import get_settings
from app.core.redis_cache import get_redis_client
from app.core.rate_limiter import RateLimiter
from app.services.ai_processor import AIProcessor, AIAnalysisResult
from app.db.models import Article, ArticleAnalysis, AnalysisTask, ProcessingStatus, AnalysisTaskStatus
from app.db.database import get_db

# Configuración
logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()

# Rate limiter para endpoints de AI Analysis
# rate_limiter = RateLimiter()  # Abstract class - commented out for now
rate_limiter = None  # TODO: Implement concrete RateLimiter class

# ========== ESQUEMAS PYDANTIC ==========

class AnalyzeArticleRequest(BaseModel):
    """Request para análisis individual de artículo"""
    article_id: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    content: str = Field(..., min_length=10, max_length=50000, description="Contenido del artículo a analizar")
    use_openai: bool = Field(default=False, description="Usar OpenAI para análisis")
    force_reprocess: bool = Field(default=False, description="Forzar reprocesamiento incluso si ya existe análisis")
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('El contenido debe tener al menos 10 caracteres')
        if len(v) > 50000:
            raise ValueError('El contenido no puede exceder 50,000 caracteres')
        return v.strip()
    
    @validator('article_id', 'url')
    def validate_identifiers(cls, v, values):
        # Al menos uno de article_id o url debe estar presente
        if not v and not values.get('url'):
            if 'article_id' not in values or not values['article_id']:
                if 'url' not in values or not values['url']:
                    raise ValueError('Se requiere al menos article_id o url')
        return v


class BatchAnalyzeRequest(BaseModel):
    """Request para análisis en lote de artículos"""
    articles: List[Dict[str, str]] = Field(..., min_items=1, max_items=100, description="Lista de artículos a procesar")
    use_openai: bool = Field(default=False, description="Usar OpenAI para análisis")
    priority: int = Field(default=5, ge=1, le=10, description="Prioridad del lote (1=alta, 10=baja)")
    batch_name: Optional[str] = Field(default=None, max_length=255, description="Nombre descriptivo del lote")
    
    @validator('articles')
    def validate_articles(cls, v):
        if not v:
            raise ValueError('La lista de artículos no puede estar vacía')
        
        for i, article in enumerate(v):
            if not isinstance(article, dict):
                raise ValueError(f'Article {i} debe ser un diccionario')
            
            # Validar campos requeridos
            if not article.get('content'):
                raise ValueError(f'Article {i} debe tener campo "content"')
            
            if len(article['content']) < 10:
                raise ValueError(f'Article {i} content debe tener al menos 10 caracteres')
            
            if len(article['content']) > 50000:
                raise ValueError(f'Article {i} content no puede exceder 50,000 caracteres')
        
        return v


class ReprocessRequest(BaseModel):
    """Request para reprocesamiento de artículos"""
    article_ids: Optional[List[str]] = None
    source_urls: Optional[List[str]] = None
    status_filter: Optional[str] = Field(default=None, description="Filtrar por estado: pending, failed, completed")
    use_openai: bool = Field(default=False, description="Usar OpenAI para análisis")
    max_articles: Optional[int] = Field(default=None, ge=1, le=1000, description="Máximo número de artículos a reprocesar")
    
    @validator('status_filter')
    def validate_status_filter(cls, v):
        if v and v not in ['pending', 'failed', 'completed']:
            raise ValueError('status_filter debe ser: pending, failed, o completed')
        return v
    
    @validator('article_ids', 'source_urls')
    def validate_identifiers(cls, v, values):
        # Al menos uno de article_ids o source_urls debe estar presente
        if not v and not values.get('article_ids'):
            if 'source_urls' not in values or not values['source_urls']:
                if 'article_ids' not in values or not values['article_ids']:
                    raise ValueError('Se requiere al menos article_ids o source_urls')
        return v


class PaginatedAnalysisResponse(BaseModel):
    """Response con paginación para resultados de análisis"""
    status: str = "success"
    total: int
    page: int = 1
    page_size: int = 10
    total_pages: int
    results: List[Dict[str, Any]]


class TaskStatusResponse(BaseModel):
    """Response para estado de tarea"""
    task_id: str
    task_type: str
    status: str
    progress: float = 0.0
    message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    processing_duration_ms: Optional[int] = None
    article_count: Optional[int] = None
    processed_count: Optional[int] = None
    failed_count: Optional[int] = None


class AnalysisResult(BaseModel):
    """Resultado de análisis individual"""
    article_id: str
    sentiment: Optional[Dict[str, Any]] = None
    topic: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    processing_time: float
    timestamp: float
    cached: bool = False


# ========== DEPENDENCIAS ==========

async def get_ai_processor():
    """Dependency para obtener AI Processor"""
    redis_client = get_redis_client()
    return AIProcessor(
        redis_client=redis_client,
        openai_api_key=settings.OPENAI_API_KEY if settings.OPENAI_API_KEY != "your_openai_key_here" else None
    )


async def check_rate_limit(limit_type: str = "ai_analysis"):
    """Dependency para verificar rate limiting"""
    redis_client = get_redis_client()
    
    # Determinar límites según el tipo
    limits = {
        "ai_analysis": {"max_requests": 100, "time_window": 3600},  # 100 requests per hour
        "batch_analysis": {"max_requests": 10, "time_window": 3600},  # 10 batch requests per hour
        "reprocess": {"max_requests": 50, "time_window": 3600}  # 50 reprocess requests per hour
    }
    
    config = limits.get(limit_type, limits["ai_analysis"])
    
    if not await rate_limiter.check_rate_limit(redis_client, "ai_analysis", **config):
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {limit_type}. Try again later."
        )


# ========== ENDPOINTS ==========

@router.post("/analyze-article", response_model=AnalysisResult)
async def analyze_article(
    request: AnalyzeArticleRequest,
    processor: AIProcessor = Depends(get_ai_processor),
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Analizar un artículo específico usando IA
    
    - **article_id**: ID único del artículo (opcional si se proporciona url)
    - **url**: URL del artículo (opcional si se proporciona article_id)  
    - **title**: Título del artículo (opcional)
    - **content**: Contenido completo del artículo a analizar (requerido)
    - **use_openai**: Usar OpenAI en lugar de modelos locales
    - **force_reprocess**: Forzar reprocesamiento aunque ya exista análisis
    """
    try:
        article_identifier = request.article_id or request.url or f"manual_{uuid.uuid4()}"
        
        # Verificar si ya existe análisis (a menos que se force reprocess)
        if not request.force_reprocess:
            # Verificar en cache
            cached_result = await processor.get_cached_analysis(article_identifier)
            if cached_result:
                return AnalysisResult(
                    article_id=article_identifier,
                    sentiment=cached_result.sentiment.__dict__ if cached_result.sentiment else None,
                    topic=cached_result.topic.__dict__ if cached_result.topic else None,
                    summary=cached_result.summary.__dict__ if cached_result.summary else None,
                    processing_time=cached_result.processing_time,
                    timestamp=cached_result.timestamp,
                    cached=True
                )
            
            # Verificar en base de datos si es un artículo conocido
            if request.article_id:
                db_article = db.query(Article).filter(Article.id == request.article_id).first()
                if db_article and db_article.processing_status == ProcessingStatus.COMPLETED:
                    # Convertir datos de la BD a formato de respuesta
                    result_data = {
                        'article_id': request.article_id,
                        'sentiment': {
                            'label': db_article.sentiment_label,
                            'score': db_article.sentiment_score,
                            'confidence': 0.8  # Valor por defecto
                        } if db_article.sentiment_label else None,
                        'topic': {
                            'category': 'unknown',
                            'confidence': 0.5,
                            'keywords': db_article.topic_tags or []
                        },
                        'summary': {
                            'text': db_article.summary,
                            'word_count': len(db_article.summary.split()) if db_article.summary else 0
                        } if db_article.summary else None,
                        'processing_time': 0.0,
                        'timestamp': db_article.ai_processed_at.timestamp() if db_article.ai_processed_at else datetime.utcnow().timestamp(),
                        'cached': False
                    }
                    return AnalysisResult(**result_data)
        
        # Crear tarea de análisis asíncrona
        task = AnalysisTask(
            task_type="single_analysis",
            task_name=f"Análisis de artículo: {article_identifier[:50]}",
            article_id=request.article_id,
            source_article_url=request.url,
            status=AnalysisTaskStatus.PENDING,
            model_name="openai" if request.use_openai else "local_models",
            input_data={
                "content_length": len(request.content),
                "use_openai": request.use_openai,
                "force_reprocess": request.force_reprocess
            }
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Marcar tarea como en progreso
        task.status = AnalysisTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Realizar análisis
        result = await processor.analyze_article(
            article_id=article_identifier,
            content=request.content,
            use_openai=request.use_openai
        )
        
        # Actualizar tarea como completada
        task.status = AnalysisTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.processing_duration_ms = int(result.processing_time * 1000)
        task.output_data = {
            "sentiment": result.sentiment.__dict__ if result.sentiment else None,
            "topic": result.topic.__dict__ if result.topic else None,
            "summary": result.summary.__dict__ if result.summary else None
        }
        db.commit()
        
        return AnalysisResult(
            article_id=article_identifier,
            sentiment=result.sentiment.__dict__ if result.sentiment else None,
            topic=result.topic.__dict__ if result.topic else None,
            summary=result.summary.__dict__ if result.summary else None,
            processing_time=result.processing_time,
            timestamp=result.timestamp,
            cached=False
        )
        
    except Exception as e:
        logger.error(f"Error en análisis de artículo {article_identifier}: {e}")
        
        # Marcar tarea como fallida si existe
        if 'task' in locals():
            task.status = AnalysisTaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al analizar artículo: {str(e)}"
        )


@router.post("/batch-analyze", response_model=Dict[str, Any])
async def batch_analyze_articles(
    request: BatchAnalyzeRequest,
    processor: AIProcessor = Depends(get_ai_processor),
    db: Session = Depends(get_db),
    _: None = Depends(lambda: check_rate_limit("batch_analysis"))
):
    """
    Procesar lote de artículos usando procesamiento asíncrono
    
    - **articles**: Lista de artículos con estructura {id, title, content}
    - **use_openai**: Usar OpenAI para análisis
    - **priority**: Prioridad del lote (1-10)
    - **batch_name**: Nombre descriptivo del lote
    """
    try:
        batch_id = str(uuid.uuid4())
        
        # Crear tarea de lote
        task = AnalysisTask(
            task_type="batch_analysis",
            task_name=request.batch_name or f"Lote {len(request.articles)} artículos",
            status=AnalysisTaskStatus.PENDING,
            priority=request.priority,
            model_name="openai" if request.use_openai else "local_models",
            input_data={
                "batch_id": batch_id,
                "article_count": len(request.articles),
                "use_openai": request.use_openai
            }
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Marcar tarea como en progreso
        task.status = AnalysisTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Procesar artículos en lotes pequeños para evitar sobrecarga
        batch_size = 5
        results = []
        
        for i in range(0, len(request.articles), batch_size):
            batch_slice = request.articles[i:i + batch_size]
            
            # Procesar cada artículo del lote actual
            batch_results = []
            
            for article in batch_slice:
                try:
                    result = await processor.analyze_article(
                        article_id=article.get('id', f"batch_{batch_id}_{len(batch_results)}"),
                        content=article['content'],
                        use_openai=request.use_openai
                    )
                    
                    batch_results.append({
                        'article_id': result.article_id,
                        'status': 'completed',
                        'sentiment': result.sentiment.label.value if result.sentiment else None,
                        'topic': result.topic.category.value if result.topic else None,
                        'processing_time': result.processing_time
                    })
                    
                except Exception as e:
                    batch_results.append({
                        'article_id': article.get('id', 'unknown'),
                        'status': 'failed',
                        'error': str(e)
                    })
                    logger.error(f"Error procesando artículo en lote: {e}")
            
            results.extend(batch_results)
            
            # Actualizar progreso de la tarea
            progress = min(1.0, (i + len(batch_slice)) / len(request.articles))
            task.output_data = {
                "progress": progress,
                "processed": i + len(batch_slice),
                "total": len(request.articles),
                "results": results
            }
            db.commit()
        
        # Marcar tarea como completada
        task.status = AnalysisTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.processing_duration_ms = int((task.completed_at - task.started_at).total_seconds() * 1000)
        task.output_data = {
            "progress": 1.0,
            "processed": len(request.articles),
            "total": len(request.articles),
            "completed_count": len([r for r in results if r['status'] == 'completed']),
            "failed_count": len([r for r in results if r['status'] == 'failed']),
            "results": results
        }
        db.commit()
        
        return {
            "status": "success",
            "task_id": task.id,
            "batch_id": batch_id,
            "message": f"Lote procesado: {len(request.articles)} artículos",
            "total_articles": len(request.articles),
            "completed": len([r for r in results if r['status'] == 'completed']),
            "failed": len([r for r in results if r['status'] == 'failed']),
            "progress": 1.0,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error en análisis por lotes: {e}")
        
        # Marcar tarea como fallida si existe
        if 'task' in locals():
            task.status = AnalysisTaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar lote: {str(e)}"
        )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Obtener estado de una tarea asíncrona de análisis
    
    - **task_id**: ID de la tarea a consultar
    """
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Calcular progreso si está en progreso
        progress = 0.0
        processed_count = None
        failed_count = None
        article_count = None
        
        if task.output_data:
            progress = task.output_data.get('progress', 0.0)
            processed_count = task.output_data.get('processed')
            failed_count = task.output_data.get('failed_count')
            article_count = task.output_data.get('total')
        
        return TaskStatusResponse(
            task_id=str(task.id),
            task_type=task.task_type,
            status=task.status.value,
            progress=progress,
            message=task.error_message or f"Tarea {task.task_type} - {task.status.value}",
            created_at=task.created_at,
            updated_at=task.updated_at,
            started_at=task.started_at,
            completed_at=task.completed_at,
            error_message=task.error_message,
            processing_duration_ms=task.processing_duration_ms,
            article_count=article_count,
            processed_count=processed_count,
            failed_count=failed_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado de tarea {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estado de tarea: {str(e)}"
        )


@router.get("/article/{article_id}/analysis", response_model=Dict[str, Any])
async def get_article_analysis(
    article_id: str,
    include_cache: bool = Query(default=True, description="Incluir resultados en cache"),
    db: Session = Depends(get_db),
    processor: AIProcessor = Depends(get_ai_processor),
    _: None = Depends(check_rate_limit)
):
    """
    Obtener análisis existente de un artículo específico
    
    - **article_id**: ID del artículo a consultar
    - **include_cache**: Incluir resultados de cache si están disponibles
    """
    try:
        # Buscar en base de datos
        article = db.query(Article).filter(Article.id == article_id).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Artículo no encontrado")
        
        result = {
            "article_id": article_id,
            "title": article.title,
            "url": article.url,
            "published_at": article.published_at,
            "sentiment": None,
            "topic": None,
            "summary": None,
            "analysis_timestamp": None,
            "processing_status": article.processing_status.value,
            "relevance_score": article.relevance_score,
            "cached": False
        }
        
        # Obtener datos de sentimiento de la BD
        if article.sentiment_label and article.sentiment_score is not None:
            result["sentiment"] = {
                "label": article.sentiment_label,
                "score": article.sentiment_score,
                "confidence": 0.8  # Valor por defecto
            }
        
        # Obtener datos de topic de la BD
        if article.topic_tags:
            result["topic"] = {
                "category": "unknown",
                "confidence": 0.5,
                "keywords": article.topic_tags
            }
        
        # Obtener resumen de la BD
        if article.summary:
            result["summary"] = {
                "text": article.summary,
                "word_count": len(article.summary.split())
            }
            result["analysis_timestamp"] = article.ai_processed_at
        
        # Buscar análisis detallado en tabla de cache
        detailed_analyses = db.query(ArticleAnalysis).filter(
            ArticleAnalysis.article_id == article_id
        ).all()
        
        if detailed_analyses:
            for analysis in detailed_analyses:
                if analysis.analysis_type == "sentiment" and result["sentiment"] is None:
                    result["sentiment"] = analysis.analysis_data
                elif analysis.analysis_type == "topics" and result["topic"] is None:
                    result["topic"] = analysis.analysis_data
                elif analysis.analysis_type == "summary" and result["summary"] is None:
                    result["summary"] = analysis.analysis_data
        
        # Intentar obtener de cache si se solicita
        if include_cache:
            cached_result = await processor.get_cached_analysis(article_id)
            if cached_result:
                if not result["sentiment"] and cached_result.sentiment:
                    result["sentiment"] = cached_result.sentiment.__dict__
                if not result["topic"] and cached_result.topic:
                    result["topic"] = cached_result.topic.__dict__
                if not result["summary"] and cached_result.summary:
                    result["summary"] = cached_result.summary.__dict__
                result["cached"] = True
        
        # Calcular scores si no están disponibles
        if result["sentiment"] is None and article.content:
            # Análisis básico basado en contenido
            positive_words = ['bueno', 'excelente', 'positivo', 'éxito', 'triunfo', 'buenas noticias']
            negative_words = ['malo', 'terrible', 'negativo', 'problema', 'error', 'crisis']
            
            text_lower = article.content.lower()
            pos_count = sum(1 for word in positive_words if word in text_lower)
            neg_count = sum(1 for word in negative_words if word in text_lower)
            
            if pos_count > neg_count:
                result["sentiment"] = {"label": "positive", "score": 0.6, "confidence": 0.3}
            elif neg_count > pos_count:
                result["sentiment"] = {"label": "negative", "score": -0.6, "confidence": 0.3}
            else:
                result["sentiment"] = {"label": "neutral", "score": 0.0, "confidence": 0.5}
        
        return {
            "status": "success",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo análisis de artículo {article_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo análisis: {str(e)}"
        )


@router.post("/reprocess", response_model=Dict[str, Any])
async def reprocess_articles(
    request: ReprocessRequest,
    processor: AIProcessor = Depends(get_ai_processor),
    db: Session = Depends(get_db),
    _: None = Depends(lambda: check_rate_limit("reprocess"))
):
    """
    Reprocesar artículos existentes con nuevos parámetros de análisis
    
    - **article_ids**: Lista de IDs de artículos específicos a reprocesar
    - **source_urls**: Lista de URLs de artículos a reprocesar  
    - **status_filter**: Filtrar por estado (pending, failed, completed)
    - **use_openai**: Usar OpenAI para reprocesamiento
    - **max_articles**: Límite máximo de artículos a reprocesar
    """
    try:
        # Construir query base
        query = db.query(Article)
        
        # Aplic filtros específicos
        if request.article_ids:
            query = query.filter(Article.id.in_(request.article_ids))
        
        if request.source_urls:
            query = query.filter(Article.url.in_(request.source_urls))
        
        if request.status_filter:
            if request.status_filter == "pending":
                query = query.filter(Article.processing_status == ProcessingStatus.PENDING)
            elif request.status_filter == "failed":
                query = query.filter(Article.processing_status == ProcessingStatus.FAILED)
            elif request.status_filter == "completed":
                query = query.filter(Article.processing_status == ProcessingStatus.COMPLETED)
        
        # Obtener artículos
        articles = query.limit(request.max_articles or 100).all()
        
        if not articles:
            return {
                "status": "warning",
                "message": "No se encontraron artículos para reprocesar",
                "articles_found": 0
            }
        
        # Crear tarea de reprocesamiento
        task = AnalysisTask(
            task_type="reprocess",
            task_name=f"Reprocesamiento de {len(articles)} artículos",
            status=AnalysisTaskStatus.PENDING,
            model_name="openai" if request.use_openai else "local_models",
            input_data={
                "article_ids": [str(a.id) for a in articles],
                "status_filter": request.status_filter,
                "use_openai": request.use_openai,
                "max_articles": request.max_articles
            }
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        
        # Marcar tarea como en progreso
        task.status = AnalysisTaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        db.commit()
        
        # Procesar artículos
        results = []
        processed_count = 0
        failed_count = 0
        
        for article in articles:
            try:
                # Actualizar estado del artículo
                article.processing_status = ProcessingStatus.PROCESSING
                db.commit()
                
                # Realizar análisis
                result = await processor.analyze_article(
                    article_id=str(article.id),
                    content=article.content or article.title,
                    use_openai=request.use_openai
                )
                
                # Actualizar artículo con nuevos resultados
                if result.sentiment:
                    article.sentiment_label = result.sentiment.label.value
                    article.sentiment_score = result.sentiment.score
                
                if result.topic:
                    article.topic_tags = result.topic.keywords
                
                if result.summary:
                    article.summary = result.summary.summary
                
                article.processing_status = ProcessingStatus.COMPLETED
                article.ai_processed_at = datetime.utcnow()
                db.commit()
                
                processed_count += 1
                
                results.append({
                    'article_id': str(article.id),
                    'status': 'completed',
                    'processing_time': result.processing_time
                })
                
            except Exception as e:
                failed_count += 1
                article.processing_status = ProcessingStatus.FAILED
                db.commit()
                
                results.append({
                    'article_id': str(article.id),
                    'status': 'failed',
                    'error': str(e)
                })
                logger.error(f"Error reprocesando artículo {article.id}: {e}")
            
            # Actualizar progreso
            progress = processed_count + failed_count / len(articles)
            task.output_data = {
                "progress": progress,
                "processed": processed_count,
                "failed": failed_count,
                "total": len(articles)
            }
            db.commit()
        
        # Marcar tarea como completada
        task.status = AnalysisTaskStatus.COMPLETED
        task.completed_at = datetime.utcnow()
        task.processing_duration_ms = int((task.completed_at - task.started_at).total_seconds() * 1000)
        task.output_data = {
            "progress": 1.0,
            "processed": processed_count,
            "failed": failed_count,
            "total": len(articles),
            "results": results
        }
        db.commit()
        
        return {
            "status": "success",
            "task_id": task.id,
            "message": f"Reprocesamiento completado: {processed_count} exitosos, {failed_count} fallidos",
            "total_articles": len(articles),
            "processed": processed_count,
            "failed": failed_count,
            "progress": 1.0,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error en reprocesamiento: {e}")
        
        # Marcar tarea como fallida si existe
        if 'task' in locals():
            task.status = AnalysisTaskStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            db.commit()
        
        raise HTTPException(
            status_code=500,
            detail=f"Error en reprocesamiento: {str(e)}"
        )


@router.get("/analytics/summary", response_model=Dict[str, Any])
async def get_analysis_analytics(
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Obtener estadísticas y resumen de análisis de IA
    """
    try:
        # Estadísticas de tareas
        total_tasks = db.query(AnalysisTask).count()
        pending_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == AnalysisTaskStatus.PENDING).count()
        running_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == AnalysisTaskStatus.RUNNING).count()
        completed_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == AnalysisTaskStatus.COMPLETED).count()
        failed_tasks = db.query(AnalysisTask).filter(AnalysisTask.status == AnalysisTaskStatus.FAILED).count()
        
        # Estadísticas de artículos analizados
        total_articles = db.query(Article).count()
        analyzed_articles = db.query(Article).filter(
            Article.processing_status == ProcessingStatus.COMPLETED
        ).count()
        
        # Distribución de sentimientos
        sentiment_stats = db.query(
            Article.sentiment_label,
            db.func.count(Article.id).label('count')
        ).filter(
            Article.sentiment_label.isnot(None)
        ).group_by(Article.sentiment_label).all()
        
        sentiment_distribution = {stat.sentiment_label: stat.count for stat in sentiment_stats}
        
        # Promedio de scores
        avg_sentiment_score = db.query(db.func.avg(Article.sentiment_score)).filter(
            Article.sentiment_score.isnot(None)
        ).scalar() or 0.0
        
        avg_relevance_score = db.query(db.func.avg(Article.relevance_score)).filter(
            Article.relevance_score.isnot(None)
        ).scalar() or 0.0
        
        # Tareas recientes (últimas 24 horas)
        recent_tasks = db.query(AnalysisTask).filter(
            AnalysisTask.created_at >= datetime.utcnow() - timedelta(days=1)
        ).count()
        
        return {
            "status": "success",
            "data": {
                "tasks": {
                    "total": total_tasks,
                    "pending": pending_tasks,
                    "running": running_tasks,
                    "completed": completed_tasks,
                    "failed": failed_tasks,
                    "success_rate": completed_tasks / total_tasks * 100 if total_tasks > 0 else 0
                },
                "articles": {
                    "total": total_articles,
                    "analyzed": analyzed_articles,
                    "analysis_rate": analyzed_articles / total_articles * 100 if total_articles > 0 else 0
                },
                "sentiment": {
                    "distribution": sentiment_distribution,
                    "average_score": round(avg_sentiment_score, 3)
                },
                "relevance": {
                    "average_score": round(avg_relevance_score, 3)
                },
                "activity": {
                    "recent_tasks_24h": recent_tasks
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo estadísticas: {str(e)}"
        )


@router.get("/tasks/list", response_model=PaginatedAnalysisResponse)
async def list_tasks(
    page: int = Query(default=1, ge=1, description="Número de página"),
    page_size: int = Query(default=20, ge=1, le=100, description="Tamaño de página"),
    status: Optional[str] = Query(default=None, description="Filtrar por estado"),
    task_type: Optional[str] = Query(default=None, description="Filtrar por tipo de tarea"),
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Listar tareas de análisis con paginación
    
    - **page**: Número de página (default: 1)
    - **page_size**: Tamaño de página (default: 20, max: 100)
    - **status**: Filtrar por estado (pending, running, completed, failed)
    - **task_type**: Filtrar por tipo de tarea (single_analysis, batch_analysis, reprocess)
    """
    try:
        # Construir query base
        query = db.query(AnalysisTask)
        
        # Aplicar filtros
        if status:
            query = query.filter(AnalysisTask.status == status)
        
        if task_type:
            query = query.filter(AnalysisTask.task_type == task_type)
        
        # Contar total
        total = query.count()
        
        # Calcular paginación
        total_pages = (total + page_size - 1) // page_size
        offset = (page - 1) * page_size
        
        # Obtener resultados
        tasks = query.order_by(desc(AnalysisTask.created_at)).offset(offset).limit(page_size).all()
        
        # Formatear resultados
        results = []
        for task in tasks:
            results.append({
                "task_id": str(task.id),
                "task_type": task.task_type,
                "task_name": task.task_name,
                "status": task.status.value,
                "priority": task.priority,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "processing_duration_ms": task.processing_duration_ms,
                "error_message": task.error_message,
                "output_data": {
                    "progress": task.output_data.get("progress", 0.0) if task.output_data else None,
                    "total": task.output_data.get("total") if task.output_data else None,
                    "processed": task.output_data.get("processed") if task.output_data else None,
                    "failed": task.output_data.get("failed") if task.output_data else None
                }
            })
        
        return PaginatedAnalysisResponse(
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error listando tareas: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error listando tareas: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    db: Session = Depends(get_db),
    _: None = Depends(check_rate_limit)
):
    """
    Eliminar una tarea de análisis (solo tareas completadas o fallidas)
    
    - **task_id**: ID de la tarea a eliminar
    """
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.id == task_id).first()
        
        if not task:
            raise HTTPException(status_code=404, detail="Tarea no encontrada")
        
        # Solo permitir eliminar tareas completadas o fallidas
        if task.status in [AnalysisTaskStatus.PENDING, AnalysisTaskStatus.RUNNING]:
            raise HTTPException(
                status_code=400,
                detail="No se pueden eliminar tareas en progreso. Cancele la tarea primero."
            )
        
        db.delete(task)
        db.commit()
        
        return {
            "status": "success",
            "message": f"Tarea {task_id} eliminada exitosamente"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando tarea {task_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error eliminando tarea: {str(e)}"
        )