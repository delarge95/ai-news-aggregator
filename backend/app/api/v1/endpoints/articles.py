from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from sqlalchemy import (
    select, delete, update, func, and_, or_, desc, asc, text,
    String, DateTime, Float
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from uuid import UUID
import hashlib

from app.db.database import get_database
from app.db.models import Article, Source  # Removido ProcessingStatus ya que no se usa más
from app.core.config import get_settings
from app.core.redis_cache import get_cache

router = APIRouter()
settings = get_settings()

# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

from pydantic import BaseModel, Field, HttpUrl, validator


class ArticleBase(BaseModel):
    """Esquema base para artículos"""
    title: str = Field(..., min_length=1, max_length=500, description="Título del artículo")
    content: Optional[str] = Field(None, description="Contenido completo del artículo")
    summary: Optional[str] = Field(None, description="Resumen del artículo")
    url: HttpUrl = Field(..., description="URL del artículo")
    published_at: Optional[datetime] = Field(None, description="Fecha de publicación")
    source_id: UUID = Field(..., description="ID de la fuente")
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Puntuación de sentimiento (-1.0 a 1.0)")
    sentiment_label: Optional[str] = Field(None, description="Etiqueta de sentimiento")
    bias_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Puntuación de sesgo (0.0 a 1.0)")
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Puntuación de relevancia (0.0 a 1.0)")
    topic_tags: Optional[List[str]] = Field(default_factory=list, description="Etiquetas de temas")


class ArticleCreate(ArticleBase):
    """Esquema para crear artículo"""
    content_hash: Optional[str] = Field(None, description="Hash del contenido para detección de duplicados")
    duplicate_group_id: Optional[UUID] = Field(None, description="ID del grupo de duplicados")


class ArticleUpdate(BaseModel):
    """Esquema para actualizar artículo"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[HttpUrl] = None
    published_at: Optional[datetime] = None
    sentiment_score: Optional[float] = Field(None, ge=-1.0, le=1.0)
    sentiment_label: Optional[str] = None
    bias_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    relevance_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    topic_tags: Optional[List[str]] = None
    processing_status: Optional[str] = None  # Cambiado de ProcessingStatus enum a str
    ai_processed_at: Optional[datetime] = None


class ArticleResponse(ArticleBase):
    """Esquema para respuesta de artículo"""
    id: UUID
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime] = None
    ai_processed_at: Optional[datetime] = None
    processing_status: str  # Cambiado de ProcessingStatus enum a str para compatibilidad con DB
    duplicate_group_id: Optional[UUID] = None
    content_hash: Optional[str] = None
    source_name: Optional[str] = None
    source_url: Optional[str] = None
    view_count: Optional[int] = Field(0, description="Número de visualizaciones")
    
    class Config:
        from_attributes = True


class SourceResponse(BaseModel):
    """Esquema para respuesta de fuente"""
    id: UUID
    name: str
    url: str
    country: Optional[str] = None
    language: str
    credibility_score: float
    
    class Config:
        from_attributes = True


class PaginatedArticlesResponse(BaseModel):
    """Esquema para respuesta paginada de artículos"""
    articles: List[ArticleResponse]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool
    filters_applied: Dict[str, Any] = {}
    sort_info: Dict[str, str] = {}


# =============================================================================
# QUERY PARAMETERS AND FILTERS
# =============================================================================

class ArticleFilters(BaseModel):
    """Filtros para búsqueda de artículos"""
    search: Optional[str] = Field(None, description="Término de búsqueda en título y contenido")
    source_ids: Optional[List[UUID]] = Field(default_factory=list, description="IDs de fuentes")
    source_names: Optional[List[str]] = Field(default_factory=list, description="Nombres de fuentes")
    categories: Optional[List[str]] = Field(default_factory=list, description="Categorías")
    sentiment_labels: Optional[List[str]] = Field(default_factory=list, description="Etiquetas de sentimiento")
    sentiment_score_min: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Puntuación mínima de sentimiento")
    sentiment_score_max: Optional[float] = Field(None, ge=-1.0, le=1.0, description="Puntuación máxima de sentimiento")
    date_from: Optional[date] = Field(None, description="Fecha desde")
    date_to: Optional[date] = Field(None, description="Fecha hasta")
    relevance_score_min: Optional[float] = Field(None, ge=0.0, le=1.0, description="Puntuación mínima de relevancia")
    processing_statuses: Optional[List[str]] = Field(default_factory=list, description="Estados de procesamiento")  # Cambiado de ProcessingStatus enum a str
    topic_tags: Optional[List[str]] = Field(default_factory=list, description="Etiquetas de temas")
    has_duplicate: Optional[bool] = Field(None, description="Tiene duplicados")
    is_featured: Optional[bool] = Field(None, description="Es destacado")
    is_popular: Optional[bool] = Field(None, description="Es popular")


class ArticleSort(BaseModel):
    """Ordenamiento para artículos"""
    sort_by: Optional[str] = Field("published_at", description="Campo de ordenamiento")
    sort_order: Optional[str] = Field("desc", description="Dirección del ordenamiento (asc/desc)")
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = [
            'published_at', 'created_at', 'updated_at', 'relevance_score',
            'sentiment_score', 'bias_score', 'view_count', 'title'
        ]
        if v not in allowed_fields:
            raise ValueError(f"Campo de ordenamiento no válido. Permitidos: {', '.join(allowed_fields)}")
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError("La dirección del ordenamiento debe ser 'asc' o 'desc'")
        return v


class PaginationParams(BaseModel):
    """Parámetros de paginación"""
    page: int = Field(1, ge=1, description="Número de página")
    per_page: int = Field(20, ge=1, le=100, description="Artículos por página")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def check_article_exists(session: AsyncSession, article_id: UUID) -> bool:
    """Verificar si un artículo existe"""
    result = await session.execute(
        select(func.count()).select_from(Article).where(Article.id == article_id)
    )
    return result.scalar() > 0


async def get_article_by_id(session: AsyncSession, article_id: UUID) -> Optional[Article]:
    """Obtener artículo por ID con información de fuente"""
    query = (
        select(Article)
        .options(selectinload(Article.source))
        .where(Article.id == article_id)
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def check_url_exists(session: AsyncSession, url: str) -> bool:
    """Verificar si ya existe un artículo con la misma URL"""
    result = await session.execute(
        select(func.count()).select_from(Article).where(Article.url == url)
    )
    return result.scalar() > 0


def build_filters_query(filters: ArticleFilters):
    """Construir query de filtros para SQLAlchemy"""
    conditions = []
    
    if filters.search:
        search_term = f"%{filters.search}%"
        conditions.append(
            or_(
                Article.title.ilike(search_term),
                Article.content.ilike(search_term),
                Article.summary.ilike(search_term)
            )
        )
    
    if filters.source_ids:
        conditions.append(Article.source_id.in_(filters.source_ids))
    
    if filters.source_names:
        conditions.append(Article.source.has(Source.name.in_(filters.source_names)))
    
    if filters.categories:
        # Asumimos que las categorías se almacenan en topic_tags como JSON
        # Esta implementación puede variar según cómo almacenes las categorías
        for category in filters.categories:
            conditions.append(Article.topic_tags.contains([category]))
    
    if filters.sentiment_labels:
        conditions.append(Article.sentiment_label.in_(filters.sentiment_labels))
    
    if filters.sentiment_score_min is not None:
        conditions.append(Article.sentiment_score >= filters.sentiment_score_min)
    
    if filters.sentiment_score_max is not None:
        conditions.append(Article.sentiment_score <= filters.sentiment_score_max)
    
    if filters.date_from:
        conditions.append(Article.published_at >= filters.date_from)
    
    if filters.date_to:
        conditions.append(Article.published_at <= filters.date_to)
    
    if filters.relevance_score_min is not None:
        conditions.append(Article.relevance_score >= filters.relevance_score_min)
    
    if filters.processing_statuses:
        conditions.append(Article.processing_status.in_(filters.processing_statuses))
    
    if filters.topic_tags:
        conditions.append(Article.topic_tags.contains(filters.topic_tags))
    
    if filters.has_duplicate is not None:
        if filters.has_duplicate:
            conditions.append(Article.duplicate_group_id.isnot(None))
        else:
            conditions.append(Article.duplicate_group_id.is_(None))
    
    return conditions


def build_sort_expression(sort: ArticleSort):
    """Construir expresión de ordenamiento para SQLAlchemy"""
    sort_field_map = {
        'published_at': Article.published_at,
        'created_at': Article.created_at,
        'updated_at': Article.updated_at,
        'relevance_score': Article.relevance_score,
        'sentiment_score': Article.sentiment_score,
        'bias_score': Article.bias_score,
        'view_count': text('0'),  # Placeholder para view_count
        'title': Article.title
    }
    
    sort_field = sort_field_map.get(sort.sort_by, Article.published_at)
    
    if sort.sort_order == 'desc':
        return desc(sort_field)
    else:
        return asc(sort_field)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/articles", response_model=PaginatedArticlesResponse)
async def get_articles(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(20, ge=1, le=100, description="Artículos por página"),
    search: Optional[str] = Query(None, description="Término de búsqueda"),
    source_ids: Optional[str] = Query(None, description="IDs de fuentes (separados por coma)"),
    source_names: Optional[str] = Query(None, description="Nombres de fuentes (separados por coma)"),
    categories: Optional[str] = Query(None, description="Categorías (separadas por coma)"),
    sentiment_labels: Optional[str] = Query(None, description="Etiquetas de sentimiento (separadas por coma)"),
    sentiment_score_min: Optional[float] = Query(None, ge=-1.0, le=1.0),
    sentiment_score_max: Optional[float] = Query(None, ge=-1.0, le=1.0),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    relevance_score_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    processing_statuses: Optional[str] = Query(None, description="Estados de procesamiento (separados por coma)"),
    topic_tags: Optional[str] = Query(None, description="Etiquetas de temas (separadas por coma)"),
    sort_by: str = Query("published_at", description="Campo de ordenamiento"),
    sort_order: str = Query("desc", description="Dirección del ordenamiento (asc/desc)"),
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Obtener lista paginada de artículos con filtros avanzados y ordenamiento múltiple
    """
    try:
        # Parsear parámetros de lista
        source_ids_list = [UUID(x.strip()) for x in source_ids.split(",")] if source_ids else []
        source_names_list = [x.strip() for x in source_names.split(",")] if source_names else []
        categories_list = [x.strip() for x in categories.split(",")] if categories else []
        sentiment_labels_list = [x.strip() for x in sentiment_labels.split(",")] if sentiment_labels else []
        processing_statuses_list = [x.strip() for x in processing_statuses.split(",")] if processing_statuses else []  # Cambiado: ya no convierte a enum
        topic_tags_list = [x.strip() for x in topic_tags.split(",")] if topic_tags else []
        
        # Construir filtros
        filters = ArticleFilters(
            search=search,
            source_ids=source_ids_list,
            source_names=source_names_list,
            categories=categories_list,
            sentiment_labels=sentiment_labels_list,
            sentiment_score_min=sentiment_score_min,
            sentiment_score_max=sentiment_score_max,
            date_from=date_from,
            date_to=date_to,
            relevance_score_min=relevance_score_min,
            processing_statuses=processing_statuses_list,
            topic_tags=topic_tags_list
        )
        
        # Construir ordenamiento
        sort = ArticleSort(sort_by=sort_by, sort_order=sort_order)
        
        # Construir condiciones de filtro
        conditions = build_filters_query(filters)
        
        # Contar total de registros
        count_query = select(func.count(Article.id)).where(and_(*conditions)) if conditions else select(func.count(Article.id))
        total_result = await session.execute(count_query)
        total = total_result.scalar()
        
        # Calcular paginación
        offset = (page - 1) * per_page
        
        # Construir query principal
        query = select(Article).options(selectinload(Article.source))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(build_sort_expression(sort)).limit(per_page).offset(offset)
        
        # Ejecutar query
        result = await session.execute(query)
        articles = result.scalars().all()
        
        # Convertir a response format
        articles_response = []
        for article in articles:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "url": str(article.url),
                "published_at": article.published_at,
                "source_id": article.source_id,
                "created_at": article.created_at,
                "updated_at": article.updated_at,
                "processed_at": article.processed_at,
                "ai_processed_at": article.ai_processed_at,
                "processing_status": article.processing_status,
                "duplicate_group_id": article.duplicate_group_id,
                "content_hash": article.content_hash,
                "sentiment_score": article.sentiment_score,
                "sentiment_label": article.sentiment_label,
                "bias_score": article.bias_score,
                "relevance_score": article.relevance_score,
                "topic_tags": article.topic_tags.get('tags', []) if isinstance(article.topic_tags, dict) else (article.topic_tags or []),
                "source_name": article.source.name if article.source else None,
                "source_url": article.source.url if article.source else None,
                "view_count": 0  # Placeholder
            }
            articles_response.append(article_dict)
        
        # Calcular información de paginación
        pages = (total + per_page - 1) // per_page
        has_next = page < pages
        has_prev = page > 1
        
        # Preparar información de filtros aplicados
        filters_applied = {
            "search": search,
            "source_ids": source_ids_list,
            "source_names": source_names_list,
            "categories": categories_list,
            "sentiment_labels": sentiment_labels_list,
            "sentiment_score_range": [sentiment_score_min, sentiment_score_max],
            "date_range": [date_from, date_to],
            "relevance_score_min": relevance_score_min,
            "processing_statuses": processing_statuses_list,
            "topic_tags": topic_tags_list
        }
        
        return PaginatedArticlesResponse(
            articles=articles_response,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            filters_applied=filters_applied,
            sort_info={"sort_by": sort_by, "sort_order": sort_order}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener artículos: {str(e)}"
        )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: UUID,
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Obtener detalle de un artículo específico
    """
    try:
        article = await get_article_by_id(session, article_id)
        
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artículo no encontrado"
            )
        
        # Incrementar view count (placeholder)
        # await increment_article_views(session, article_id)
        
        return ArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            url=str(article.url),
            published_at=article.published_at,
            source_id=article.source_id,
            created_at=article.created_at,
            updated_at=article.updated_at,
            processed_at=article.processed_at,
            ai_processed_at=article.ai_processed_at,
            processing_status=article.processing_status,
            duplicate_group_id=article.duplicate_group_id,
            content_hash=article.content_hash,
            sentiment_score=article.sentiment_score,
            sentiment_label=article.sentiment_label,
            bias_score=article.bias_score,
            relevance_score=article.relevance_score,
            topic_tags=article.topic_tags or [],
            source_name=article.source.name if article.source else None,
            source_url=article.source.url if article.source else None,
            view_count=0  # Placeholder
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener artículo: {str(e)}"
        )


@router.post("/articles", response_model=ArticleResponse, status_code=status.HTTP_201_CREATED)
async def create_article(
    article_data: ArticleCreate,
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Crear un nuevo artículo
    """
    try:
        # Verificar que la fuente existe
        source_result = await session.execute(
            select(Source).where(Source.id == article_data.source_id)
        )
        source = source_result.scalar_one_or_none()
        
        if not source:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Fuente no encontrada"
            )
        
        # Verificar que la URL no existe
        if await check_url_exists(session, str(article_data.url)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe un artículo con esta URL"
            )
        
        # Generar hash del contenido si no se proporciona
        if not article_data.content_hash and article_data.content:
            article_data.content_hash = hashlib.sha256(
                article_data.content.encode('utf-8')
            ).hexdigest()
        
        # Crear artículo
        db_article = Article(**article_data.dict())
        session.add(db_article)
        await session.commit()
        await session.refresh(db_article)
        
        # Refrescar con información de fuente
        db_article = await get_article_by_id(session, db_article.id)
        
        return ArticleResponse(
            id=db_article.id,
            title=db_article.title,
            content=db_article.content,
            summary=db_article.summary,
            url=str(db_article.url),
            published_at=db_article.published_at,
            source_id=db_article.source_id,
            created_at=db_article.created_at,
            updated_at=db_article.updated_at,
            processed_at=db_article.processed_at,
            ai_processed_at=db_article.ai_processed_at,
            processing_status=db_article.processing_status,
            duplicate_group_id=db_article.duplicate_group_id,
            content_hash=db_article.content_hash,
            sentiment_score=db_article.sentiment_score,
            sentiment_label=db_article.sentiment_label,
            bias_score=db_article.bias_score,
            relevance_score=db_article.relevance_score,
            topic_tags=db_article.topic_tags or [],
            source_name=db_article.source.name if db_article.source else None,
            source_url=db_article.source.url if db_article.source else None,
            view_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear artículo: {str(e)}"
        )


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: UUID,
    article_data: ArticleUpdate,
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Actualizar un artículo existente
    """
    try:
        # Verificar que el artículo existe
        if not await check_article_exists(session, article_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artículo no encontrado"
            )
        
        # Construir datos de actualización
        update_data = {k: v for k, v in article_data.dict(exclude_unset=True).items() if v is not None}
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No hay datos para actualizar"
            )
        
        # Actualizar artículo
        await session.execute(
            update(Article).where(Article.id == article_id).values(**update_data)
        )
        await session.commit()
        
        # Obtener artículo actualizado
        article = await get_article_by_id(session, article_id)
        
        return ArticleResponse(
            id=article.id,
            title=article.title,
            content=article.content,
            summary=article.summary,
            url=str(article.url),
            published_at=article.published_at,
            source_id=article.source_id,
            created_at=article.created_at,
            updated_at=article.updated_at,
            processed_at=article.processed_at,
            ai_processed_at=article.ai_processed_at,
            processing_status=article.processing_status,
            duplicate_group_id=article.duplicate_group_id,
            content_hash=article.content_hash,
            sentiment_score=article.sentiment_score,
            sentiment_label=article.sentiment_label,
            bias_score=article.bias_score,
            relevance_score=article.relevance_score,
            topic_tags=article.topic_tags or [],
            source_name=article.source.name if article.source else None,
            source_url=article.source.url if article.source else None,
            view_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al actualizar artículo: {str(e)}"
        )


@router.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_article(
    article_id: UUID,
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Eliminar un artículo
    """
    try:
        # Verificar que el artículo existe
        if not await check_article_exists(session, article_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Artículo no encontrado"
            )
        
        # Eliminar artículo
        await session.execute(
            delete(Article).where(Article.id == article_id)
        )
        await session.commit()
        
        return None
        
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error al eliminar artículo: {str(e)}"
        )


@router.get("/articles/featured", response_model=PaginatedArticlesResponse)
async def get_featured_articles(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=50, description="Artículos por página"),
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Obtener artículos destacados (alta relevancia y sentimiento positivo)
    """
    try:
        # Definir criterios para artículos destacados
        # Articles with high relevance score (>0.7) and positive sentiment
        conditions = [
            Article.relevance_score >= 0.7,
            Article.sentiment_label == 'positive'
        ]
        
        # Contar total
        total_result = await session.execute(
            select(func.count(Article.id)).where(and_(*conditions))
        )
        total = total_result.scalar()
        
        # Obtener artículos
        offset = (page - 1) * per_page
        
        query = (
            select(Article)
            .options(selectinload(Article.source))
            .where(and_(*conditions))
            .order_by(desc(Article.relevance_score), desc(Article.sentiment_score))
            .limit(per_page)
            .offset(offset)
        )
        
        result = await session.execute(query)
        articles = result.scalars().all()
        
        # Convertir a response format
        articles_response = []
        for article in articles:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "url": str(article.url),
                "published_at": article.published_at,
                "source_id": article.source_id,
                "created_at": article.created_at,
                "updated_at": article.updated_at,
                "processed_at": article.processed_at,
                "ai_processed_at": article.ai_processed_at,
                "processing_status": article.processing_status,
                "duplicate_group_id": article.duplicate_group_id,
                "content_hash": article.content_hash,
                "sentiment_score": article.sentiment_score,
                "sentiment_label": article.sentiment_label,
                "bias_score": article.bias_score,
                "relevance_score": article.relevance_score,
                "topic_tags": article.topic_tags or [],
                "source_name": article.source.name if article.source else None,
                "source_url": article.source.url if article.source else None,
                "view_count": 0
            }
            articles_response.append(article_dict)
        
        # Calcular paginación
        pages = (total + per_page - 1) // per_page
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedArticlesResponse(
            articles=articles_response,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            filters_applied={"featured_criteria": "relevance >= 0.7 and sentiment = positive"},
            sort_info={"sort_by": "relevance_score", "sort_order": "desc"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener artículos destacados: {str(e)}"
        )


@router.get("/articles/popular", response_model=PaginatedArticlesResponse)
async def get_popular_articles(
    page: int = Query(1, ge=1, description="Número de página"),
    per_page: int = Query(10, ge=1, le=50, description="Artículos por página"),
    time_period: str = Query("7d", description="Período de tiempo (1d, 7d, 30d)"),
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Obtener artículos populares (más vistos) basados en el período especificado
    """
    try:
        # Definir fecha límite basada en el período
        from datetime import timedelta
        now = datetime.utcnow()
        
        if time_period == "1d":
            date_limit = now - timedelta(days=1)
        elif time_period == "7d":
            date_limit = now - timedelta(days=7)
        elif time_period == "30d":
            date_limit = now - timedelta(days=30)
        else:
            date_limit = now - timedelta(days=7)  # Default to 7 days
        
        # Artículos populares basados en fecha de publicación reciente y relevancia
        conditions = [
            Article.published_at >= date_limit,
            Article.relevance_score >= 0.5
        ]
        
        # Contar total
        total_result = await session.execute(
            select(func.count(Article.id)).where(and_(*conditions))
        )
        total = total_result.scalar()
        
        # Obtener artículos
        offset = (page - 1) * per_page
        
        query = (
            select(Article)
            .options(selectinload(Article.source))
            .where(and_(*conditions))
            .order_by(desc(Article.published_at), desc(Article.relevance_score))
            .limit(per_page)
            .offset(offset)
        )
        
        result = await session.execute(query)
        articles = result.scalars().all()
        
        # Convertir a response format
        articles_response = []
        for article in articles:
            article_dict = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "url": str(article.url),
                "published_at": article.published_at,
                "source_id": article.source_id,
                "created_at": article.created_at,
                "updated_at": article.updated_at,
                "processed_at": article.processed_at,
                "ai_processed_at": article.ai_processed_at,
                "processing_status": article.processing_status,
                "duplicate_group_id": article.duplicate_group_id,
                "content_hash": article.content_hash,
                "sentiment_score": article.sentiment_score,
                "sentiment_label": article.sentiment_label,
                "bias_score": article.bias_score,
                "relevance_score": article.relevance_score,
                "topic_tags": article.topic_tags or [],
                "source_name": article.source.name if article.source else None,
                "source_url": article.source.url if article.source else None,
                "view_count": 0
            }
            articles_response.append(article_dict)
        
        # Calcular paginación
        pages = (total + per_page - 1) // per_page
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedArticlesResponse(
            articles=articles_response,
            total=total,
            page=page,
            per_page=per_page,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            filters_applied={
                "time_period": time_period,
                "date_from": date_limit.isoformat(),
                "popularity_criteria": "recent_publication_and_relevance"
            },
            sort_info={"sort_by": "published_at", "sort_order": "desc"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener artículos populares: {str(e)}"
        )


# =============================================================================
# ADDITIONAL UTILITY ENDPOINTS
# =============================================================================

@router.get("/articles/stats/summary", response_model=Dict[str, Any])
async def get_articles_summary_stats(
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Obtener estadísticas resumen de artículos
    """
    try:
        # Obtener contadores básicos
        total_result = await session.execute(select(func.count(Article.id)))
        total_articles = total_result.scalar()
        
        # Artículos por estado de procesamiento
        processing_stats_result = await session.execute(
            select(Article.processing_status, func.count(Article.id))
            .group_by(Article.processing_status)
        )
        processing_stats = dict(processing_stats_result.all())
        
        # Artículos por sentimiento
        sentiment_stats_result = await session.execute(
            select(Article.sentiment_label, func.count(Article.id))
            .where(Article.sentiment_label.isnot(None))
            .group_by(Article.sentiment_label)
        )
        sentiment_stats = dict(sentiment_stats_result.all())
        
        # Promedio de relevancia
        relevance_avg_result = await session.execute(
            select(func.avg(Article.relevance_score))
            .where(Article.relevance_score.isnot(None))
        )
        avg_relevance = relevance_avg_result.scalar() or 0.0
        
        # Artículos con IA procesada
        ai_processed_result = await session.execute(
            select(func.count(Article.id))
            .where(Article.ai_processed_at.isnot(None))
        )
        ai_processed_count = ai_processed_result.scalar()
        
        # Artículos únicos vs duplicados
        unique_result = await session.execute(
            select(func.count(Article.id))
            .where(Article.duplicate_group_id.is_(None))
        )
        unique_count = unique_result.scalar()
        
        duplicate_count = total_articles - unique_count
        
        return {
            "total_articles": total_articles,
            "processing_status_distribution": processing_stats,
            "sentiment_distribution": sentiment_stats,
            "average_relevance_score": round(avg_relevance, 3),
            "ai_processed_articles": ai_processed_count,
            "unique_articles": unique_count,
            "duplicate_articles": duplicate_count,
            "duplicate_rate": round(duplicate_count / total_articles * 100, 2) if total_articles > 0 else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/sources", response_model=List[SourceResponse])
async def get_sources(
    active_only: bool = Query(True, description="Solo fuentes activas"),
    session: AsyncSession = Depends(get_database),
    cache = Depends(get_cache)
):
    """
    Obtener lista de fuentes de noticias
    """
    try:
        query = select(Source)
        
        # ⚠️ Columna is_active no existe en DB
        # if active_only:
        #     query = query.where(Source.is_active == True)
        
        query = query.order_by(Source.name)
        
        result = await session.execute(query)
        sources = result.scalars().all()
        
        return [
            SourceResponse(
                id=source.id,
                name=source.name,
                url=source.url,
                country=source.country,
                language=source.language,
                credibility_score=source.credibility_score
            )
            for source in sources
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener fuentes: {str(e)}"
        )