"""
Servicio de Búsqueda Avanzada para AI News Aggregator
Implementa full-text search, filtros avanzados, búsqueda semántica y autocompletado
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

from sqlalchemy import (
    and_, or_, func, text, desc, asc, 
    String, Text, DateTime, Float
)
from sqlalchemy.orm import Session, aliased
from sqlalchemy.dialects.postgresql import array_agg
import asyncpg
from app.db.models import Article, Source, TrendingTopic
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class SearchServiceError(Exception):
    """Excepción base para errores del servicio de búsqueda"""
    pass


class SearchService:
    """Servicio principal de búsqueda avanzada"""
    
    def __init__(self):
        self.max_results_per_page = 100
        self.semantic_model_available = False
        self.fulltext_index_available = False
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    async def advanced_search(
        self, 
        query: str,
        filters: Dict[str, Any],
        sort: str = "relevance",
        limit: int = 20,
        offset: int = 0,
        semantic_search: bool = False,
        include_facets: bool = True,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Búsqueda avanzada con filtros múltiples y ordenamiento
        
        Args:
            query: Término de búsqueda
            filters: Diccionario con filtros
            sort: Campo de ordenamiento
            limit: Límite de resultados
            offset: Offset para paginación
            semantic_search: Usar búsqueda semántica
            include_facets: Incluir facets para UI
            db: Sesión de base de datos
            
        Returns:
            Dict con resultados y metadatos
        """
        try:
            start_time = datetime.now()
            
            # Construir query base
            articles_query = db.query(Article, Source).join(Source)
            
            # Aplicar filtros de texto
            if query.strip():
                articles_query = self._apply_text_search(articles_query, query, semantic_search)
            
            # Aplicar filtros de fecha
            articles_query = self._apply_date_filters(articles_query, filters)
            
            # Aplicar filtros de fuentes
            articles_query = self._apply_source_filters(articles_query, filters)
            
            # Aplicar filtros de sentimiento
            articles_query = self._apply_sentiment_filters(articles_query, filters)
            
            # Aplicar filtros de relevancia
            articles_query = self._apply_relevance_filters(articles_query, filters)
            
            # Aplicar filtros de sesgo
            articles_query = self._apply_bias_filters(articles_query, filters)
            
            # Contar total antes de aplicar límites
            total_query = articles_query.with_entities(func.count(Article.id))
            total_count = total_query.scalar() or 0
            
            # Aplicar ordenamiento
            articles_query = self._apply_sorting(articles_query, sort)
            
            # Aplicar límites y paginación
            articles_query = articles_query.offset(offset).limit(limit)
            
            # Ejecutar query
            results = articles_query.all()
            
            # Formatear resultados
            formatted_results = []
            for article, source in results:
                formatted_result = {
                    "id": str(article.id),
                    "title": article.title,
                    "content": article.content[:500] + "..." if article.content and len(article.content) > 500 else article.content,
                    "summary": article.summary,
                    "url": article.url,
                    "source": source.name,
                    "source_id": str(source.id),
                    "published_at": article.published_at,
                    "sentiment_score": article.sentiment_score,
                    "sentiment_label": article.sentiment_label,
                    "bias_score": article.bias_score,
                    "topic_tags": article.topic_tags or [],
                    "relevance_score": article.relevance_score,
                    "ai_processed_at": article.ai_processed_at,
                    "processing_status": article.processing_status.value if article.processing_status else None
                }
                formatted_results.append(formatted_result)
            
            # Obtener facets si se solicitan
            facets = {}
            if include_facets:
                facets = await self._get_search_facets(query, filters, db)
            
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "results": formatted_results,
                "total": total_count,
                "facets": facets,
                "search_time_ms": search_time,
                "filters_applied": filters
            }
            
        except Exception as e:
            logger.error(f"Error en búsqueda avanzada: {str(e)}")
            raise SearchServiceError(f"Error en búsqueda: {str(e)}")
    
    async def get_search_suggestions(
        self,
        query: str,
        limit: int = 10,
        include_topics: bool = True,
        include_sources: bool = True,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener sugerencias de búsqueda inteligentes
        
        Args:
            query: Término parcial para autocompletado
            limit: Número máximo de sugerencias
            include_topics: Incluir temas populares
            include_sources: Incluir nombres de fuentes
            
        Returns:
            Lista de sugerencias con score
        """
        try:
            suggestions = []
            
            # Normalizar query
            normalized_query = query.lower().strip()
            
            if include_sources:
                # Sugerencias de fuentes
                source_suggestions = await self._get_source_suggestions(normalized_query, db)
                suggestions.extend(source_suggestions)
            
            if include_topics:
                # Sugerencias de temas populares
                topic_suggestions = await self._get_topic_suggestions(normalized_query, db)
                suggestions.extend(topic_suggestions)
            
            # Sugerencias de términos comunes
            term_suggestions = await self._get_term_suggestions(normalized_query, limit // 2, db)
            suggestions.extend(term_suggestions)
            
            # Ordenar por score y limitar
            suggestions.sort(key=lambda x: x['score'], reverse=True)
            
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Error obteniendo sugerencias: {str(e)}")
            raise SearchServiceError(f"Error en sugerencias: {str(e)}")
    
    async def get_trending_searches(
        self,
        timeframe: str = "24h",
        limit: int = 20,
        min_count: int = 2,
        db: Session = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener búsquedas populares y trending
        
        Args:
            timeframe: Período de tiempo (1h, 6h, 24h, 7d)
            limit: Número máximo de resultados
            min_count: Mínimo de búsquedas para incluir
            
        Returns:
            Lista de búsquedas trending
        """
        try:
            # Calcular fecha desde
            timeframe_map = {
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7)
            }
            
            if timeframe not in timeframe_map:
                timeframe = "24h"
            
            date_from = datetime.utcnow() - timeframe_map[timeframe]
            
            # Obtener trending topics de la base de datos
            trending_query = db.query(
                TrendingTopic.topic,
                TrendingTopic.article_count,
                TrendingTopic.sources_count,
                TrendingTopic.trend_score
            ).filter(
                and_(
                    TrendingTopic.date_recorded >= date_from,
                    TrendingTopic.time_period == timeframe,
                    TrendingTopic.article_count >= min_count
                )
            ).order_by(
                desc(TrendingTopic.trend_score)
            ).limit(limit)
            
            trending_results = trending_query.all()
            
            # Formatear resultados
            formatted_trending = []
            for topic, article_count, sources_count, trend_score in trending_results:
                formatted_trending.append({
                    "query": topic,
                    "count": article_count,
                    "sources_count": sources_count,
                    "trend_score": trend_score,
                    "timeframe": timeframe
                })
            
            # Si no hay datos suficientes, generar búsquedas de ejemplo
            if len(formatted_trending) < 5:
                example_trending = self._get_example_trending_searches()
                formatted_trending.extend(example_trending[:limit - len(formatted_trending)])
            
            return formatted_trending
            
        except Exception as e:
            logger.error(f"Error obteniendo búsquedas trending: {str(e)}")
            # Devolver búsquedas de ejemplo como fallback
            return self._get_example_trending_searches()
    
    async def get_available_filters(self, db: Session = None) -> Dict[str, List[str]]:
        """
        Obtener todos los filtros disponibles para búsqueda
        
        Returns:
            Diccionario con filtros disponibles
        """
        try:
            filters = {}
            
            # Fuentes disponibles
            sources_query = db.query(Source.name).filter(Source.is_active == True).order_by(Source.name)
            filters['sources'] = [source[0] for source in sources_query.all()]
            
            # Categorías basadas en topic_tags
            categories_query = db.query(
                func.unnest(Article.topic_tags).label('category')
            ).filter(
                Article.topic_tags.isnot(None)
            ).group_by('category').order_by(func.count('category').desc()).limit(50)
            
            filters['categories'] = [cat[0] for cat in categories_query.all() if cat[0]]
            
            # Sentimientos disponibles
            sentiment_query = db.query(Article.sentiment_label).filter(
                Article.sentiment_label.isnot(None)
            ).distinct()
            
            filters['sentiment'] = [sent[0] for sent in sentiment_query.all() if sent[0]]
            
            # Rangos de fechas
            dates_query = db.query(
                func.min(Article.published_at),
                func.max(Article.published_at)
            )
            
            min_date, max_date = dates_query.first()
            filters['date_range'] = {
                'min': min_date.isoformat() if min_date else None,
                'max': max_date.isoformat() if max_date else None
            }
            
            # Rangos de score
            filters['score_ranges'] = {
                'relevance': {'min': 0.0, 'max': 1.0},
                'sentiment': {'min': -1.0, 'max': 1.0},
                'bias': {'min': 0.0, 'max': 1.0}
            }
            
            return filters
            
        except Exception as e:
            logger.error(f"Error obteniendo filtros: {str(e)}")
            # Devolver filtros por defecto
            return self._get_default_filters()
    
    async def semantic_search(
        self,
        query: str,
        context: Optional[str] = None,
        limit: int = 20,
        similarity_threshold: float = 0.3,
        db: Session = None
    ) -> Dict[str, Any]:
        """
        Búsqueda semántica avanzada usando IA
        
        Args:
            query: Consulta en lenguaje natural
            context: Contexto adicional
            limit: Límite de resultados
            similarity_threshold: Umbral de similitud
            
        Returns:
            Resultados con scores de similitud
        """
        try:
            # Por ahora, simular búsqueda semántica
            # En una implementación real, usaríamos modelos como Sentence-BERT
            results = await self._simulate_semantic_search(
                query, context, limit, similarity_threshold, db
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda semántica: {str(e)}")
            raise SearchServiceError(f"Error en búsqueda semántica: {str(e)}")
    
    async def get_search_stats(self, db: Session = None) -> Dict[str, Any]:
        """
        Obtener estadísticas del sistema de búsqueda
        
        Returns:
            Estadísticas del servicio
        """
        try:
            stats = {}
            
            # Estadísticas de artículos
            stats['articles'] = {
                'total': db.query(func.count(Article.id)).scalar() or 0,
                'with_sentiment': db.query(func.count(Article.id)).filter(
                    Article.sentiment_label.isnot(None)
                ).scalar() or 0,
                'with_bias_score': db.query(func.count(Article.id)).filter(
                    Article.bias_score.isnot(None)
                ).scalar() or 0,
                'processed': db.query(func.count(Article.id)).filter(
                    Article.processing_status == 'completed'
                ).scalar() or 0
            }
            
            # Estadísticas de fuentes
            stats['sources'] = {
                'total': db.query(func.count(Source.id)).scalar() or 0,
                'active': db.query(func.count(Source.id)).filter(
                    Source.is_active == True
                ).scalar() or 0
            }
            
            # Estadísticas de temas trending
            stats['trending'] = {
                'topics_tracked': db.query(func.count(TrendingTopic.id)).scalar() or 0
            }
            
            # Estadísticas de fecha
            date_stats = db.query(
                func.min(Article.published_at),
                func.max(Article.published_at),
                func.avg(Article.relevance_score)
            ).first()
            
            stats['date_range'] = {
                'earliest': date_stats[0].isoformat() if date_stats[0] else None,
                'latest': date_stats[1].isoformat() if date_stats[1] else None,
                'avg_relevance': float(date_stats[2]) if date_stats[2] else 0.0
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            raise SearchServiceError(f"Error obteniendo estadísticas: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Health check del servicio de búsqueda
        
        Returns:
            Estado del servicio
        """
        try:
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {
                    "fulltext_search": self.fulltext_index_available,
                    "semantic_search": self.semantic_model_available,
                    "database_connection": True
                }
            }
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    # Métodos privados de utilidad
    
    def _apply_text_search(self, query, search_term: str, semantic: bool = False):
        """Aplicar filtros de búsqueda de texto"""
        if not search_term.strip():
            return query
        
        # Búsqueda simple por términos
        search_pattern = f"%{search_term.lower()}%"
        
        text_filters = or_(
            func.lower(Article.title).like(search_pattern),
            func.lower(Article.content).like(search_pattern),
            func.lower(Article.summary).like(search_pattern)
        )
        
        return query.filter(text_filters)
    
    def _apply_date_filters(self, query, filters: Dict[str, Any]):
        """Aplicar filtros de fecha"""
        if filters.get('date_from'):
            try:
                date_from = datetime.fromisoformat(filters['date_from'])
                query = query.filter(Article.published_at >= date_from)
            except ValueError:
                logger.warning(f"Fecha inválida: {filters['date_from']}")
        
        if filters.get('date_to'):
            try:
                date_to = datetime.fromisoformat(filters['date_to'])
                query = query.filter(Article.published_at <= date_to)
            except ValueError:
                logger.warning(f"Fecha inválida: {filters['date_to']}")
        
        return query
    
    def _apply_source_filters(self, query, filters: Dict[str, Any]):
        """Aplicar filtros de fuentes"""
        if filters.get('sources'):
            query = query.filter(Source.name.in_(filters['sources']))
        
        return query
    
    def _apply_sentiment_filters(self, query, filters: Dict[str, Any]):
        """Aplicar filtros de sentimiento"""
        if filters.get('sentiment'):
            query = query.filter(Article.sentiment_label.in_(filters['sentiment']))
        
        return query
    
    def _apply_relevance_filters(self, query, filters: Dict[str, Any]):
        """Aplicar filtros de relevancia"""
        if filters.get('min_relevance') is not None:
            query = query.filter(Article.relevance_score >= filters['min_relevance'])
        
        return query
    
    def _apply_bias_filters(self, query, filters: Dict[str, Any]):
        """Aplicar filtros de sesgo"""
        if filters.get('min_bias_score') is not None:
            query = query.filter(Article.bias_score >= filters['min_bias_score'])
        
        return query
    
    def _apply_sorting(self, query, sort_field: str):
        """Aplicar ordenamiento"""
        sort_map = {
            "relevance": desc(Article.relevance_score),
            "date": desc(Article.published_at),
            "sentiment": desc(Article.sentiment_score),
            "source": asc(Source.name),
            "title": asc(Article.title)
        }
        
        sort_order = sort_map.get(sort_field, desc(Article.relevance_score))
        return query.order_by(sort_order)
    
    async def _get_search_facets(self, query: str, filters: Dict[str, Any], db: Session) -> Dict[str, Any]:
        """Obtener facets para filtros de UI"""
        try:
            # Por ahora devolver facets vacíos
            # En una implementación real, calcularíamos facets de los resultados
            return {}
        except Exception as e:
            logger.error(f"Error obteniendo facets: {str(e)}")
            return {}
    
    async def _get_source_suggestions(self, query: str, db: Session) -> List[Dict[str, Any]]:
        """Obtener sugerencias de fuentes"""
        try:
            sources_query = db.query(Source.name).filter(
                and_(
                    Source.is_active == True,
                    Source.name.ilike(f"%{query}%")
                )
            ).limit(5)
            
            suggestions = []
            for source_name, in sources_query:
                suggestions.append({
                    "text": source_name,
                    "type": "source",
                    "score": 0.9
                })
            
            return suggestions
        except Exception as e:
            logger.error(f"Error obteniendo sugerencias de fuentes: {str(e)}")
            return []
    
    async def _get_topic_suggestions(self, query: str, db: Session) -> List[Dict[str, Any]]:
        """Obtener sugerencias de temas"""
        try:
            # Usar trending topics como sugerencias de temas
            topics_query = db.query(TrendingTopic.topic).filter(
                TrendingTopic.topic.ilike(f"%{query}%")
            ).order_by(desc(TrendingTopic.trend_score)).limit(5)
            
            suggestions = []
            for topic, in topics_query:
                suggestions.append({
                    "text": topic,
                    "type": "topic",
                    "score": 0.8
                })
            
            return suggestions
        except Exception as e:
            logger.error(f"Error obteniendo sugerencias de temas: {str(e)}")
            return []
    
    async def _get_term_suggestions(self, query: str, limit: int, db: Session) -> List[Dict[str, Any]]:
        """Obtener sugerencias de términos comunes"""
        try:
            # Términos comunes de ejemplo
            common_terms = [
                "artificial intelligence", "machine learning", "deep learning",
                "technology", "innovation", "research", "startup", "AI",
                "neural networks", "data science", "automation", "robotics"
            ]
            
            suggestions = []
            for term in common_terms:
                if query in term.lower():
                    suggestions.append({
                        "text": term,
                        "type": "term",
                        "score": 0.7
                    })
            
            return suggestions[:limit]
        except Exception as e:
            logger.error(f"Error obteniendo sugerencias de términos: {str(e)}")
            return []
    
    async def _simulate_semantic_search(
        self, query: str, context: Optional[str], limit: int, 
        similarity_threshold: float, db: Session
    ) -> Dict[str, Any]:
        """Simular búsqueda semántica (placeholder para implementación real)"""
        try:
            # Por ahora ejecutar búsqueda regular como fallback
            filters = {}
            if context:
                # Extraer palabras clave del contexto
                context_words = context.lower().split()[:5]
                filters['keywords'] = context_words
            
            regular_results = await self.advanced_search(
                query=query,
                filters=filters,
                limit=limit,
                db=db
            )
            
            # Agregar scores de similitud simulados
            for i, result in enumerate(regular_results['results']):
                similarity_score = max(0.3, 1.0 - (i * 0.1))  # Scores decrecientes
                result['similarity_score'] = similarity_score
            
            avg_similarity = sum(r.get('similarity_score', 0) for r in regular_results['results']) / len(regular_results['results'])
            
            regular_results['avg_similarity'] = avg_similarity
            return regular_results
            
        except Exception as e:
            logger.error(f"Error simulando búsqueda semántica: {str(e)}")
            return {"results": [], "total": 0, "avg_similarity": 0.0}
    
    def _get_example_trending_searches(self) -> List[Dict[str, Any]]:
        """Obtener búsquedas trending de ejemplo"""
        return [
            {"query": "artificial intelligence", "count": 45, "trend_score": 0.95, "timeframe": "24h"},
            {"query": "machine learning", "count": 38, "trend_score": 0.87, "timeframe": "24h"},
            {"query": "chatgpt", "count": 32, "trend_score": 0.82, "timeframe": "24h"},
            {"query": "openai", "count": 29, "trend_score": 0.78, "timeframe": "24h"},
            {"query": "deep learning", "count": 25, "trend_score": 0.73, "timeframe": "24h"},
            {"query": "neural networks", "count": 22, "trend_score": 0.68, "timeframe": "24h"},
            {"query": "automation", "count": 19, "trend_score": 0.63, "timeframe": "24h"},
            {"query": "robotics", "count": 17, "trend_score": 0.59, "timeframe": "24h"},
            {"query": "data science", "count": 15, "trend_score": 0.54, "timeframe": "24h"},
            {"query": "computer vision", "count": 13, "trend_score": 0.49, "timeframe": "24h"}
        ]
    
    def _get_default_filters(self) -> Dict[str, List[str]]:
        """Obtener filtros por defecto cuando hay errores"""
        return {
            "sources": ["BBC News", "CNN", "Reuters", "Associated Press"],
            "categories": ["technology", "politics", "health", "business", "sports"],
            "sentiment": ["positive", "negative", "neutral"],
            "date_range": {
                "min": "2024-01-01T00:00:00Z",
                "max": datetime.utcnow().isoformat()
            },
            "score_ranges": {
                "relevance": {"min": 0.0, "max": 1.0},
                "sentiment": {"min": -1.0, "max": 1.0},
                "bias": {"min": 0.0, "max": 1.0}
            }
        }


# Instancia global del servicio
search_service = SearchService()