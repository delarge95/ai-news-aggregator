from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
import logging

from app.services.search_service import search_service
from app.db.database import get_db
from sqlalchemy.orm import Session

router = APIRouter()
logger = logging.getLogger(__name__)


# Modelos Pydantic para las requests
class AdvancedSearchRequest(BaseModel):
    query: Optional[str] = ""
    filters: Optional[Dict[str, Any]] = {}
    sort: Optional[str] = "relevance"  # relevance, date, sentiment, source
    limit: int = 20
    offset: int = 0


class SearchFilter(BaseModel):
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    sentiment: Optional[List[str]] = None
    min_relevance: Optional[float] = None
    min_bias_score: Optional[float] = None


class SearchSuggestion(BaseModel):
    text: str
    type: str  # 'term', 'source', 'category', 'topic'
    score: float


class TrendingSearch(BaseModel):
    query: str
    count: int
    trend_score: float
    timeframe: str


# Pydantic models para responses
class SearchResult(BaseModel):
    id: str
    title: str
    content: Optional[str]
    summary: Optional[str]
    url: str
    source: str
    source_id: str
    published_at: Optional[datetime]
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    bias_score: Optional[float]
    topic_tags: Optional[List[str]]
    relevance_score: float
    ai_processed_at: Optional[datetime]
    processing_status: str


class SearchResponse(BaseModel):
    status: str
    message: str
    query: str
    total: int
    results: List[SearchResult]
    filters_applied: Dict[str, Any]
    search_time_ms: float
    facets: Optional[Dict[str, Any]] = None


class SearchSuggestionsResponse(BaseModel):
    status: str
    message: str
    query: str
    suggestions: List[SearchSuggestion]


class TrendingSearchesResponse(BaseModel):
    status: str
    message: str
    searches: List[TrendingSearch]


class SearchFiltersResponse(BaseModel):
    status: str
    message: str
    filters: Dict[str, List[str]]


@router.get("/search", response_model=SearchResponse)
async def advanced_search(
    q: Optional[str] = Query(None, description="Término de búsqueda principal"),
    query: Optional[str] = Query(None, description="Término de búsqueda alternativo"),
    date_from: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    sources: Optional[List[str]] = Query(None, description="Lista de fuentes"),
    categories: Optional[List[str]] = Query(None, description="Lista de categorías"),
    sentiment: Optional[List[str]] = Query(None, description="Sentimientos: positive, negative, neutral"),
    min_relevance: Optional[float] = Query(0.0, ge=0.0, le=1.0, description="Relevancia mínima"),
    min_bias_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Score de sesgo mínimo"),
    sort: str = Query("relevance", description="Orden: relevance, date, sentiment, source"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginación"),
    semantic_search: bool = Query(False, description="Usar búsqueda semántica con IA"),
    include_facets: bool = Query(True, description="Incluir facets de filtrado"),
    db: Session = Depends(get_db)
):
    """
    Búsqueda avanzada con filtros múltiples
    
    - **q**: Término principal de búsqueda
    - **date_from/date_to**: Filtro por rango de fechas
    - **sources**: Filtrar por fuentes específicas
    - **categories**: Filtrar por categorías
    - **sentiment**: Filtrar por sentimiento (positive, negative, neutral)
    - **min_relevance**: Relevancia mínima (0.0-1.0)
    - **sort**: Ordenamiento (relevance, date, sentiment, source)
    - **semantic_search**: Usar búsqueda semántica con IA
    - **include_facets**: Incluir información de facets para UI
    """
    try:
        start_time = datetime.now()
        
        # Determinar el término de búsqueda
        search_term = q or query or ""
        
        # Construir filtros
        filters = {}
        if date_from:
            filters['date_from'] = date_from
        if date_to:
            filters['date_to'] = date_to
        if sources:
            filters['sources'] = sources
        if categories:
            filters['categories'] = categories
        if sentiment:
            filters['sentiment'] = sentiment
        if min_relevance is not None:
            filters['min_relevance'] = min_relevance
        if min_bias_score is not None:
            filters['min_bias_score'] = min_bias_score
        
        # Ejecutar búsqueda
        results = await search_service.advanced_search(
            query=search_term,
            filters=filters,
            sort=sort,
            limit=limit,
            offset=offset,
            semantic_search=semantic_search,
            include_facets=include_facets,
            db=db
        )
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return SearchResponse(
            status="success",
            message=f"Búsqueda completada: {len(results.get('results', []))} resultados encontrados",
            query=search_term,
            total=results.get('total', 0),
            results=results.get('results', []),
            filters_applied=filters,
            search_time_ms=search_time,
            facets=results.get('facets')
        )
        
    except Exception as e:
        logger.error(f"Error en búsqueda avanzada: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


@router.get("/search/suggestions", response_model=SearchSuggestionsResponse)
async def get_search_suggestions(
    q: str = Query(..., description="Término para obtener sugerencias"),
    limit: int = Query(10, ge=1, le=20, description="Número de sugerencias"),
    include_topics: bool = Query(True, description="Incluir temas populares"),
    include_sources: bool = Query(True, description="Incluir nombres de fuentes"),
    db: Session = Depends(get_db)
):
    """
    Obtener sugerencias de búsqueda inteligentes
    
    - **q**: Término parcial para autocompletado
    - **include_topics**: Incluir temas populares
    - **include_sources**: Incluir nombres de fuentes
    """
    try:
        suggestions = await search_service.get_search_suggestions(
            query=q,
            limit=limit,
            include_topics=include_topics,
            include_sources=include_sources,
            db=db
        )
        
        return SearchSuggestionsResponse(
            status="success",
            message=f"Encontradas {len(suggestions)} sugerencias",
            query=q,
            suggestions=suggestions
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo sugerencias: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo sugerencias: {str(e)}")


@router.get("/search/trending", response_model=TrendingSearchesResponse)
async def get_trending_searches(
    timeframe: str = Query("24h", description="Período: 1h, 6h, 24h, 7d"),
    limit: int = Query(20, ge=1, le=50, description="Número de búsquedas populares"),
    min_count: int = Query(2, ge=1, description="Mínimo de búsquedas para considerar trending"),
    db: Session = Depends(get_db)
):
    """
    Obtener búsquedas populares y trending
    
    - **timeframe**: Período de tiempo (1h, 6h, 24h, 7d)
    - **min_count**: Mínimo de búsquedas para incluir
    """
    try:
        trending_searches = await search_service.get_trending_searches(
            timeframe=timeframe,
            limit=limit,
            min_count=min_count,
            db=db
        )
        
        return TrendingSearchesResponse(
            status="success",
            message=f"Encontradas {len(trending_searches)} búsquedas trending",
            searches=trending_searches
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo búsquedas trending: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo búsquedas trending: {str(e)}")


@router.get("/search/filters", response_model=SearchFiltersResponse)
async def get_available_filters(db: Session = Depends(get_db)):
    """
    Obtener filtros disponibles para búsqueda avanzada
    """
    try:
        filters = await search_service.get_available_filters(db=db)
        
        return SearchFiltersResponse(
            status="success",
            message="Filtros obtenidos correctamente",
            filters=filters
        )
        
    except Exception as e:
        logger.error(f"Error obteniendo filtros: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo filtros: {str(e)}")


@router.get("/search/stats")
async def get_search_stats(db: Session = Depends(get_db)):
    """
    Estadísticas del sistema de búsqueda
    """
    try:
        stats = await search_service.get_search_stats(db=db)
        
        return {
            "status": "success",
            "message": "Estadísticas obtenidas correctamente",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@router.post("/search/semantic")
async def semantic_search(
    query: str = Query(..., description="Consulta para búsqueda semántica"),
    context: Optional[str] = Query(None, description="Contexto adicional"),
    limit: int = Query(20, ge=1, le=100, description="Límite de resultados"),
    similarity_threshold: float = Query(0.3, ge=0.0, le=1.0, description="Umbral de similitud"),
    db: Session = Depends(get_db)
):
    """
    Búsqueda semántica avanzada usando IA
    
    - **query**: Consulta en lenguaje natural
    - **context**: Contexto adicional para mejorar la búsqueda
    - **similarity_threshold**: Umbral mínimo de similitud
    """
    try:
        start_time = datetime.now()
        
        results = await search_service.semantic_search(
            query=query,
            context=context,
            limit=limit,
            similarity_threshold=similarity_threshold,
            db=db
        )
        
        search_time = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": "success",
            "message": f"Búsqueda semántica completada: {len(results.get('results', []))} resultados",
            "query": query,
            "context": context,
            "total": results.get('total', 0),
            "results": results.get('results', []),
            "search_time_ms": search_time,
            "avg_similarity": results.get('avg_similarity', 0.0)
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda semántica: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda semántica: {str(e)}")


@router.get("/search/health")
async def search_health_check():
    """
    Health check del servicio de búsqueda
    """
    try:
        health_status = await search_service.health_check()
        
        return {
            "status": "success",
            "service": "search_service",
            "health": health_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "service": "search_service", 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }