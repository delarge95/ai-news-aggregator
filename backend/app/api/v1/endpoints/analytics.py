from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum as PyEnum
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_
import json

from app.db.database import get_db
from app.db.models import Article, Source, TrendingTopic, AnalysisTask, ProcessingStatus
from app.core.config import get_settings

router = APIRouter()
settings = get_settings()

class TimeFrameEnum(str, PyEnum):
    """Frames de tiempo para analytics"""
    HOUR = "1h"
    SIX_HOURS = "6h"
    DAY = "24h"
    WEEK = "7d"
    MONTH = "30d"
    QUARTER = "90d"

class AggregationEnum(str, PyEnum):
    """Tipos de agregación de datos"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class ExportFormatEnum(str, PyEnum):
    """Formatos de exportación"""
    JSON = "json"
    CSV = "csv"
    EXCEL = "xlsx"

def get_timeframe_range(timeframe: TimeFrameEnum) -> tuple[datetime, datetime]:
    """Calcular rango de tiempo basado en timeframe"""
    now = datetime.utcnow()
    
    if timeframe == TimeFrameEnum.HOUR:
        start_time = now - timedelta(hours=1)
    elif timeframe == TimeFrameEnum.SIX_HOURS:
        start_time = now - timedelta(hours=6)
    elif timeframe == TimeFrameEnum.DAY:
        start_time = now - timedelta(days=1)
    elif timeframe == TimeFrameEnum.WEEK:
        start_time = now - timedelta(weeks=1)
    elif timeframe == TimeFrameEnum.MONTH:
        start_time = now - timedelta(days=30)
    elif timeframe == TimeFrameEnum.QUARTER:
        start_time = now - timedelta(days=90)
    else:
        start_time = now - timedelta(days=1)
    
    return start_time, now

@router.get("/analytics/dashboard")
async def get_dashboard_analytics(
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.DAY, description="Período de tiempo para el análisis"),
    aggregation: Optional[AggregationEnum] = Query(AggregationEnum.DAILY, description="Tipo de agregación de datos"),
    export_format: Optional[ExportFormatEnum] = Query(None, description="Formato de exportación"),
    db: Session = Depends(get_db)
):
    """
    Obtener resumen general de analytics del dashboard
    
    - **timeframe**: Período de tiempo (1h, 6h, 24h, 7d, 30d, 90d)
    - **aggregation**: Tipo de agregación (hourly, daily, weekly, monthly)
    - **export_format**: Formato de exportación (json, csv, xlsx)
    """
    try:
        start_time, end_time = get_timeframe_range(timeframe)
        
        # Métricas generales
        total_articles_query = db.query(func.count(Article.id)).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        )
        total_articles = total_articles_query.scalar()
        
        # Artículos procesados por IA
        processed_articles_query = db.query(func.count(Article.id)).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.processing_status == ProcessingStatus.COMPLETED
        )
        processed_articles = processed_articles_query.scalar()
        
        # Análisis de sentimientos
        sentiment_stats = db.query(
            func.count(Article.id).label('count'),
            func.avg(Article.sentiment_score).label('avg_score')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.sentiment_score.isnot(None)
        ).group_by(Article.sentiment_label).all()
        
        # Fuentes más activas
        source_stats = db.query(
            Source.name,
            func.count(Article.id).label('article_count')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        ).group_by(Source.id, Source.name).order_by(desc('article_count')).limit(5).all()
        
        # Tendencias de topics
        top_topics_query = db.query(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic'),
            func.count(Article.id).label('count')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.topic_tags.isnot(None)
        ).group_by('topic').order_by(desc('count')).limit(10)
        
        # Ejecutar consulta con todos los elementos en la lista de selección
        top_topics_result = db.execute(top_topics_query.with_only_columns(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic'),
            func.count(Article.id).label('count')
        )).fetchall()
        
        # Tareas de análisis activas
        active_tasks_query = db.query(func.count(AnalysisTask.id)).filter(
            AnalysisTask.status.in_(['pending', 'running'])
        )
        active_tasks = active_tasks_query.scalar()
        
        # Calcular métricas adicionales
        processing_rate = (processed_articles / total_articles * 100) if total_articles > 0 else 0
        
        dashboard_data = {
            "timeframe": timeframe,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "metrics": {
                "total_articles": total_articles,
                "processed_articles": processed_articles,
                "processing_rate": round(processing_rate, 2),
                "active_tasks": active_tasks,
                "unique_sources": len(source_stats)
            },
            "sentiment_breakdown": [
                {
                    "label": stat.sentiment_label or "unknown",
                    "count": stat.count,
                    "avg_score": round(stat.avg_score or 0, 3)
                }
                for stat in sentiment_stats
            ],
            "top_sources": [
                {
                    "name": source.name,
                    "article_count": source.article_count
                }
                for source in source_stats
            ],
            "trending_topics": [
                {
                    "topic": topic.topic,
                    "mentions": topic.count
                }
                for topic in top_topics_result
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        # Manejar exportación si se solicita
        if export_format:
            if export_format == ExportFormatEnum.JSON:
                return dashboard_data
            elif export_format == ExportFormatEnum.CSV:
                # TODO: Implementar exportación CSV
                pass
            elif export_format == ExportFormatEnum.EXCEL:
                # TODO: Implementar exportación Excel
                pass
        
        return {
            "status": "success",
            "message": f"Dashboard analytics generado para período {timeframe}",
            "data": dashboard_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando dashboard analytics: {str(e)}")

@router.get("/analytics/trends")
async def get_trends_analytics(
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.DAY, description="Período de tiempo para análisis"),
    aggregation: AggregationEnum = Query(AggregationEnum.HOURLY, description="Tipo de agregación temporal"),
    topic_filter: Optional[str] = Query(None, description="Filtrar por tema específico"),
    export_format: Optional[ExportFormatEnum] = Query(None, description="Formato de exportación"),
    db: Session = Depends(get_db)
):
    """
    Obtener análisis de tendencias temporales
    
    - **timeframe**: Período de tiempo (1h, 6h, 24h, 7d, 30d, 90d)
    - **aggregation**: Agregación temporal (hourly, daily, weekly, monthly)
    - **topic_filter**: Filtrar por tema específico
    - **export_format**: Formato de exportación
    """
    try:
        start_time, end_time = get_timeframe_range(timeframe)
        
        # Tendencias de volumen de artículos por período
        if aggregation == AggregationEnum.HOURLY:
            time_group = func.date_trunc('hour', Article.created_at)
        elif aggregation == AggregationEnum.DAILY:
            time_group = func.date_trunc('day', Article.created_at)
        elif aggregation == AggregationEnum.WEEKLY:
            time_group = func.date_trunc('week', Article.created_at)
        else:  # MONTHLY
            time_group = func.date_trunc('month', Article.created_at)
        
        # Consulta base para tendencias temporales
        volume_trends_query = db.query(
            time_group.label('period'),
            func.count(Article.id).label('article_count'),
            func.avg(Article.relevance_score).label('avg_relevance'),
            func.avg(Article.sentiment_score).label('avg_sentiment')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        )
        
        if topic_filter:
            volume_trends_query = volume_trends_query.filter(
                Article.topic_tags.contains([topic_filter])
            )
        
        volume_trends = volume_trends_query.group_by('period').order_by('period').all()
        
        # Tendencias por fuente
        source_trends_query = db.query(
            Source.name.label('source_name'),
            time_group.label('period'),
            func.count(Article.id).label('article_count')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        ).group_by(Source.name, 'period').order_by('period').all()
        
        # Tendencias de sentimientos
        sentiment_trends_query = db.query(
            time_group.label('period'),
            Article.sentiment_label,
            func.count(Article.id).label('count')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.sentiment_label.isnot(None)
        ).group_by('period', Article.sentiment_label).order_by('period').all()
        
        trends_data = {
            "timeframe": timeframe,
            "aggregation": aggregation,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "volume_trends": [
                {
                    "period": trend.period.isoformat(),
                    "article_count": trend.article_count,
                    "avg_relevance": round(trend.avg_relevance or 0, 3),
                    "avg_sentiment": round(trend.avg_sentiment or 0, 3)
                }
                for trend in volume_trends
            ],
            "source_trends": [
                {
                    "source": trend.source_name,
                    "period": trend.period.isoformat(),
                    "article_count": trend.article_count
                }
                for trend in source_trends
            ],
            "sentiment_trends": [
                {
                    "period": trend.period.isoformat(),
                    "sentiment": trend.sentiment_label,
                    "count": trend.count
                }
                for trend in sentiment_trends
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if export_format:
            if export_format == ExportFormatEnum.JSON:
                return trends_data
        
        return {
            "status": "success",
            "message": f"Trends analytics generado para período {timeframe}",
            "data": trends_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando trends analytics: {str(e)}")

@router.get("/analytics/topics")
async def get_topics_analytics(
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.WEEK, description="Período de tiempo para análisis"),
    min_mentions: int = Query(1, ge=1, description="Mínimo de menciones para incluir un tema"),
    export_format: Optional[ExportFormatEnum] = Query(None, description="Formato de exportación"),
    db: Session = Depends(get_db)
):
    """
    Obtener análisis detallado de temas y tópicos
    
    - **timeframe**: Período de tiempo para el análisis
    - **min_mentions**: Mínimo de menciones para incluir un tema
    - **export_format**: Formato de exportación
    """
    try:
        start_time, end_time = get_timeframe_range(timeframe)
        
        # Análisis de topics más mencionados
        topics_query = db.query(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic'),
            func.count(Article.id).label('article_count'),
            func.avg(Article.relevance_score).label('avg_relevance'),
            func.avg(Article.sentiment_score).label('avg_sentiment'),
            func.count(func.distinct(Article.source_id)).label('unique_sources')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.topic_tags.isnot(None)
        ).group_by('topic').having(
            func.count(Article.id) >= min_mentions
        ).order_by(desc('article_count')).limit(50)
        
        # Ejecutar consulta
        top_topics_result = db.execute(topics_query.with_only_columns(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic'),
            func.count(Article.id).label('article_count'),
            func.avg(Article.relevance_score).label('avg_relevance'),
            func.avg(Article.sentiment_score).label('avg_sentiment'),
            func.count(func.distinct(Article.source_id)).label('unique_sources')
        )).fetchall()
        
        # Evolución temporal de topics (últimos 7 días)
        evolution_start = datetime.utcnow() - timedelta(days=7)
        topic_evolution_query = db.query(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic'),
            func.date_trunc('day', Article.created_at).label('day'),
            func.count(Article.id).label('daily_count')
        ).filter(
            Article.created_at >= evolution_start,
            Article.created_at <= end_time,
            Article.topic_tags.isnot(None)
        ).group_by('topic', 'day').order_by('day').all()
        
        # Co-ocurrencia de topics (temas que aparecen juntos)
        cooccurrence_query = db.query(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic1'),
            func.jsonb_array_elements_text(Article.topic_tags).label('topic2'),
            func.count(Article.id).label('cooccurrence_count')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.topic_tags.isnot(None),
            func.jsonb_array_length(Article.topic_tags) > 1
        ).group_by('topic1', 'topic2').having(
            func.count(Article.id) >= min_mentions
        ).order_by(desc('cooccurrence_count')).limit(20)
        
        # Ejecutar consulta de co-ocurrencia
        cooccurrence_result = db.execute(cooccurrence_query.with_only_columns(
            func.jsonb_array_elements_text(Article.topic_tags).label('topic1'),
            func.jsonb_array_elements_text(Article.topic_tags).label('topic2'),
            func.count(Article.id).label('cooccurrence_count')
        )).fetchall()
        
        topics_data = {
            "timeframe": timeframe,
            "min_mentions": min_mentions,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "top_topics": [
                {
                    "topic": topic.topic,
                    "mentions": topic.article_count,
                    "avg_relevance": round(topic.avg_relevance or 0, 3),
                    "avg_sentiment": round(topic.avg_sentiment or 0, 3),
                    "unique_sources": topic.unique_sources
                }
                for topic in top_topics_result
            ],
            "topic_evolution": [
                {
                    "topic": evolution.topic,
                    "date": evolution.day.isoformat(),
                    "daily_count": evolution.daily_count
                }
                for evolution in topic_evolution_query
            ],
            "topic_cooccurrence": [
                {
                    "topic1": cooc.topic1,
                    "topic2": cooc.topic2,
                    "cooccurrence_count": cooc.cooccurrence_count
                }
                for cooc in cooccurrence_result
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if export_format:
            if export_format == ExportFormatEnum.JSON:
                return topics_data
        
        return {
            "status": "success",
            "message": f"Topics analytics generado para período {timeframe}",
            "data": topics_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando topics analytics: {str(e)}")

@router.get("/analytics/sentiment")
async def get_sentiment_analytics(
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.DAY, description="Período de tiempo para análisis"),
    source_filter: Optional[str] = Query(None, description="Filtrar por fuente específica"),
    aggregation: AggregationEnum = Query(AggregationEnum.HOURLY, description="Agregación temporal"),
    export_format: Optional[ExportFormatEnum] = Query(None, description="Formato de exportación"),
    db: Session = Depends(get_db)
):
    """
    Obtener análisis detallado de sentimientos
    
    - **timeframe**: Período de tiempo para el análisis
    - **source_filter**: Filtrar por fuente específica
    - **aggregation**: Agregación temporal
    - **export_format**: Formato de exportación
    """
    try:
        start_time, end_time = get_timeframe_range(timeframe)
        
        # Configurar group by temporal
        if aggregation == AggregationEnum.HOURLY:
            time_group = func.date_trunc('hour', Article.created_at)
        elif aggregation == AggregationEnum.DAILY:
            time_group = func.date_trunc('day', Article.created_at)
        elif aggregation == AggregationEnum.WEEKLY:
            time_group = func.date_trunc('week', Article.created_at)
        else:  # MONTHLY
            time_group = func.date_trunc('month', Article.created_at)
        
        # Análisis general de sentimientos
        sentiment_base_query = db.query(
            Article.sentiment_label,
            func.count(Article.id).label('count'),
            func.avg(Article.sentiment_score).label('avg_score'),
            func.min(Article.sentiment_score).label('min_score'),
            func.max(Article.sentiment_score).label('max_score'),
            func.stddev(Article.sentiment_score).label('stddev_score')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.sentiment_score.isnot(None)
        )
        
        if source_filter:
            sentiment_base_query = sentiment_base_query.join(
                Source, Article.source_id == Source.id
            ).filter(Source.name == source_filter)
        
        sentiment_overall = sentiment_base_query.group_by(
            Article.sentiment_label
        ).all()
        
        # Evolución temporal de sentimientos
        sentiment_trends_query = db.query(
            time_group.label('period'),
            Article.sentiment_label,
            func.count(Article.id).label('count'),
            func.avg(Article.sentiment_score).label('avg_score')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.sentiment_score.isnot(None)
        ).group_by('period', Article.sentiment_label).order_by('period').all()
        
        # Sentimientos por fuente
        sentiment_by_source_query = db.query(
            Source.name.label('source_name'),
            Article.sentiment_label,
            func.count(Article.id).label('count'),
            func.avg(Article.sentiment_score).label('avg_score')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.sentiment_score.isnot(None)
        ).group_by(Source.name, Article.sentiment_label).order_by(Source.name).all()
        
        # Distribución de scores de sentimientos
        sentiment_distribution_query = db.query(
            func.width_bucket(Article.sentiment_score, -1.0, 1.0, 20).label('bucket'),
            func.count(Article.id).label('count'),
            func.avg(Article.sentiment_score).label('avg_score_in_bucket')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Article.sentiment_score.isnot(None)
        ).group_by('bucket').order_by('bucket').all()
        
        sentiment_data = {
            "timeframe": timeframe,
            "source_filter": source_filter,
            "aggregation": aggregation,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "overall_sentiment": [
                {
                    "label": sentiment.sentiment_label or "unknown",
                    "count": sentiment.count,
                    "avg_score": round(sentiment.avg_score or 0, 3),
                    "min_score": round(sentiment.min_score or 0, 3),
                    "max_score": round(sentiment.max_score or 0, 3),
                    "stddev_score": round(sentiment.stddev_score or 0, 3)
                }
                for sentiment in sentiment_overall
            ],
            "sentiment_trends": [
                {
                    "period": trend.period.isoformat(),
                    "sentiment": trend.sentiment_label,
                    "count": trend.count,
                    "avg_score": round(trend.avg_score or 0, 3)
                }
                for trend in sentiment_trends_query
            ],
            "sentiment_by_source": [
                {
                    "source": source.source_name,
                    "sentiment": source.sentiment_label,
                    "count": source.count,
                    "avg_score": round(source.avg_score or 0, 3)
                }
                for source in sentiment_by_source_query
            ],
            "sentiment_distribution": [
                {
                    "bucket": dist.bucket,
                    "count": dist.count,
                    "avg_score": round(dist.avg_score_in_bucket or 0, 3)
                }
                for dist in sentiment_distribution_query
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if export_format:
            if export_format == ExportFormatEnum.JSON:
                return sentiment_data
        
        return {
            "status": "success",
            "message": f"Sentiment analytics generado para período {timeframe}",
            "data": sentiment_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando sentiment analytics: {str(e)}")

@router.get("/analytics/sources")
async def get_sources_analytics(
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.WEEK, description="Período de tiempo para análisis"),
    min_articles: int = Query(1, ge=1, description="Mínimo de artículos por fuente"),
    include_inactive: bool = Query(False, description="Incluir fuentes inactivas"),
    export_format: Optional[ExportFormatEnum] = Query(None, description="Formato de exportación"),
    db: Session = Depends(get_db)
):
    """
    Obtener estadísticas detalladas por fuente
    
    - **timeframe**: Período de tiempo para el análisis
    - **min_articles**: Mínimo de artículos por fuente para incluir
    - **include_inactive**: Incluir fuentes inactivas
    - **export_format**: Formato de exportación
    """
    try:
        start_time, end_time = get_timeframe_range(timeframe)
        
        # Estadísticas generales por fuente
        source_stats_query = db.query(
            Source.name.label('source_name'),
            Source.api_name.label('api_name'),
            Source.credibility_score,
            Source.is_active,
            func.count(Article.id).label('article_count'),
            func.avg(Article.relevance_score).label('avg_relevance'),
            func.avg(Article.sentiment_score).label('avg_sentiment'),
            func.count(func.distinct(Article.topic_tags)).label('unique_topics'),
            func.min(Article.published_at).label('first_article'),
            func.max(Article.published_at).label('last_article')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        ).group_by(Source.id, Source.name, Source.api_name, Source.credibility_score, Source.is_active).having(
            func.count(Article.id) >= min_articles
        ).order_by(desc('article_count'))
        
        if not include_inactive:
            source_stats_query = source_stats_query.filter(Source.is_active == True)
        
        source_stats = source_stats_query.all()
        
        # Rendimiento por API
        api_performance_query = db.query(
            Source.api_name,
            func.count(Article.id).label('total_articles'),
            func.avg(Article.relevance_score).label('avg_relevance'),
            func.count(func.distinct(Source.id)).label('active_sources'),
            func.avg(Source.credibility_score).label('avg_credibility')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time,
            Source.is_active == True
        ).group_by(Source.api_name).all()
        
        # Evolución temporal por fuente (últimos 7 días)
        evolution_start = datetime.utcnow() - timedelta(days=7)
        source_evolution_query = db.query(
            Source.name.label('source_name'),
            func.date_trunc('day', Article.created_at).label('day'),
            func.count(Article.id).label('daily_count'),
            func.avg(Article.relevance_score).label('daily_avg_relevance'),
            func.avg(Article.sentiment_score).label('daily_avg_sentiment')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= evolution_start,
            Article.created_at <= end_time
        ).group_by(Source.name, 'day').order_by('day').all()
        
        # Calidad de contenido por fuente
        quality_metrics_query = db.query(
            Source.name.label('source_name'),
            func.count(Article.id).filter(Article.sentiment_score > 0.1).label('positive_count'),
            func.count(Article.id).filter(Article.sentiment_score < -0.1).label('negative_count'),
            func.count(Article.id).filter(Article.relevance_score > 0.7).label('high_relevance_count'),
            func.count(Article.id).filter(Article.processing_status == ProcessingStatus.COMPLETED).label('processed_count')
        ).join(Article, Source.id == Article.source_id).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        ).group_by(Source.id, Source.name).all()
        
        sources_data = {
            "timeframe": timeframe,
            "min_articles": min_articles,
            "include_inactive": include_inactive,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "source_statistics": [
                {
                    "name": source.source_name,
                    "api_name": source.api_name,
                    "credibility_score": round(source.credibility_score or 0, 3),
                    "is_active": source.is_active,
                    "article_count": source.article_count,
                    "avg_relevance": round(source.avg_relevance or 0, 3),
                    "avg_sentiment": round(source.avg_sentiment or 0, 3),
                    "unique_topics": source.unique_topics,
                    "first_article": source.first_article.isoformat() if source.first_article else None,
                    "last_article": source.last_article.isoformat() if source.last_article else None
                }
                for source in source_stats
            ],
            "api_performance": [
                {
                    "api_name": api.api_name,
                    "total_articles": api.total_articles,
                    "avg_relevance": round(api.avg_relevance or 0, 3),
                    "active_sources": api.active_sources,
                    "avg_credibility": round(api.avg_credibility or 0, 3)
                }
                for api in api_performance_query
            ],
            "source_evolution": [
                {
                    "source": evolution.source_name,
                    "date": evolution.day.isoformat(),
                    "daily_count": evolution.daily_count,
                    "daily_avg_relevance": round(evolution.daily_avg_relevance or 0, 3),
                    "daily_avg_sentiment": round(evolution.daily_avg_sentiment or 0, 3)
                }
                for evolution in source_evolution_query
            ],
            "quality_metrics": [
                {
                    "source": quality.source_name,
                    "positive_count": quality.positive_count,
                    "negative_count": quality.negative_count,
                    "high_relevance_count": quality.high_relevance_count,
                    "processed_count": quality.processed_count,
                    "processing_rate": round((quality.processed_count / max(quality.positive_count + quality.negative_count, 1)) * 100, 2)
                }
                for quality in quality_metrics_query
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        if export_format:
            if export_format == ExportFormatEnum.JSON:
                return sources_data
        
        return {
            "status": "success",
            "message": f"Sources analytics generado para período {timeframe}",
            "data": sources_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando sources analytics: {str(e)}")

@router.get("/analytics/traffic")
async def get_traffic_analytics(
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.DAY, description="Período de tiempo para análisis"),
    aggregation: AggregationEnum = Query(AggregationEnum.HOURLY, description="Agregación temporal"),
    metric_type: str = Query("all", description="Tipo de métrica (all, processing, api_calls, errors)"),
    export_format: Optional[ExportFormatEnum] = Query(None, description="Formato de exportación"),
    db: Session = Depends(get_db)
):
    """
    Obtener métricas de tráfico y rendimiento
    
    - **timeframe**: Período de tiempo para análisis
    - **aggregation**: Agregación temporal
    - **metric_type**: Tipo de métrica (all, processing, api_calls, errors)
    - **export_format**: Formato de exportación
    """
    try:
        start_time, end_time = get_timeframe_range(timeframe)
        
        # Configurar group by temporal
        if aggregation == AggregationEnum.HOURLY:
            time_group = func.date_trunc('hour', Article.created_at)
        elif aggregation == AggregationEnum.DAILY:
            time_group = func.date_trunc('day', Article.created_at)
        elif aggregation == AggregationEnum.WEEKLY:
            time_group = func.date_trunc('week', Article.created_at)
        else:  # MONTHLY
            time_group = func.date_trunc('month', Article.created_at)
        
        traffic_data = {}
        
        # Métricas de procesamiento de artículos
        if metric_type in ["all", "processing"]:
            processing_stats = db.query(
                time_group.label('period'),
                func.count(Article.id).label('total_articles'),
                func.count(Article.id).filter(Article.processing_status == ProcessingStatus.COMPLETED).label('processed'),
                func.count(Article.id).filter(Article.processing_status == ProcessingStatus.PROCESSING).label('processing'),
                func.count(Article.id).filter(Article.processing_status == ProcessingStatus.PENDING).label('pending'),
                func.count(Article.id).filter(Article.processing_status == ProcessingStatus.FAILED).label('failed'),
                func.avg(Article.ai_processed_at - Article.created_at).label('avg_processing_time')
            ).filter(
                Article.created_at >= start_time,
                Article.created_at <= end_time
            ).group_by('period').order_by('period').all()
            
            traffic_data["processing_metrics"] = [
                {
                    "period": stat.period.isoformat(),
                    "total_articles": stat.total_articles,
                    "processed": stat.processed,
                    "processing": stat.processing,
                    "pending": stat.pending,
                    "failed": stat.failed,
                    "processing_rate": round((stat.processed / max(stat.total_articles, 1)) * 100, 2),
                    "avg_processing_time_seconds": round(stat.avg_processing_time.total_seconds() if stat.avg_processing_time else 0, 2)
                }
                for stat in processing_stats
            ]
        
        # Métricas de tareas de análisis
        if metric_type in ["all", "processing"]:
            task_stats = db.query(
                time_group.label('period'),
                func.count(AnalysisTask.id).label('total_tasks'),
                func.count(AnalysisTask.id).filter(AnalysisTask.status == 'completed').label('completed_tasks'),
                func.count(AnalysisTask.id).filter(AnalysisTask.status == 'running').label('running_tasks'),
                func.count(AnalysisTask.id).filter(AnalysisTask.status == 'failed').label('failed_tasks'),
                func.avg(AnalysisTask.processing_duration_ms).label('avg_duration_ms')
            ).filter(
                AnalysisTask.created_at >= start_time,
                AnalysisTask.created_at <= end_time
            ).group_by('period').order_by('period').all()
            
            traffic_data["task_metrics"] = [
                {
                    "period": stat.period.isoformat(),
                    "total_tasks": stat.total_tasks,
                    "completed_tasks": stat.completed_tasks,
                    "running_tasks": stat.running_tasks,
                    "failed_tasks": stat.failed_tasks,
                    "completion_rate": round((stat.completed_tasks / max(stat.total_tasks, 1)) * 100, 2),
                    "avg_duration_ms": round(stat.avg_duration_ms or 0, 2)
                }
                for stat in task_stats
            ]
        
        # Métricas de rendimiento por fuente
        if metric_type in ["all", "api_calls"]:
            api_performance = db.query(
                Source.api_name.label('api_name'),
                func.count(Article.id).label('total_calls'),
                func.count(Article.id).filter(Article.created_at >= start_time).label('successful_calls'),
                func.avg(func.extract('epoch', Article.created_at - func.cast(Article.created_at, func.DateTime))).label('avg_response_time')
            ).join(Article, Source.id == Article.source_id).filter(
                Article.created_at >= start_time,
                Article.created_at <= end_time
            ).group_by(Source.api_name).all()
            
            traffic_data["api_performance"] = [
                {
                    "api_name": perf.api_name,
                    "total_calls": perf.total_calls,
                    "successful_calls": perf.successful_calls,
                    "success_rate": round((perf.successful_calls / max(perf.total_calls, 1)) * 100, 2),
                    "avg_response_time_seconds": round(perf.avg_response_time or 0, 2)
                }
                for perf in api_performance
            ]
        
        # Métricas de errores
        if metric_type in ["all", "errors"]:
            error_stats = db.query(
                time_group.label('period'),
                func.count(Article.id).filter(Article.processing_status == ProcessingStatus.FAILED).label('failed_articles'),
                func.count(AnalysisTask.id).filter(AnalysisTask.status == 'failed').label('failed_tasks')
            ).outerjoin(
                Article, AnalysisTask.article_id == Article.id
            ).filter(
                AnalysisTask.created_at >= start_time if AnalysisTask.created_at else True,
                Article.created_at >= start_time if Article.created_at else True
            ).group_by('period').order_by('period').all()
            
            traffic_data["error_metrics"] = [
                {
                    "period": error.period.isoformat(),
                    "failed_articles": error.failed_articles,
                    "failed_tasks": error.failed_tasks,
                    "total_failures": error.failed_articles + error.failed_tasks
                }
                for error in error_stats
            ]
        
        # Resumen de métricas generales
        overall_summary = db.query(
            func.count(Article.id).label('total_articles'),
            func.count(Article.id).filter(Article.processing_status == ProcessingStatus.COMPLETED).label('processed_articles'),
            func.count(Article.id).filter(Article.processing_status == ProcessingStatus.FAILED).label('failed_articles'),
            func.avg(Article.relevance_score).label('avg_relevance'),
            func.count(AnalysisTask.id).filter(AnalysisTask.status == 'failed').label('failed_tasks')
        ).filter(
            Article.created_at >= start_time,
            Article.created_at <= end_time
        ).first()
        
        traffic_data.update({
            "timeframe": timeframe,
            "aggregation": aggregation,
            "metric_type": metric_type,
            "period": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat()
            },
            "overall_summary": {
                "total_articles": overall_summary.total_articles or 0,
                "processed_articles": overall_summary.processed_articles or 0,
                "failed_articles": overall_summary.failed_articles or 0,
                "failed_tasks": overall_summary.failed_tasks or 0,
                "avg_relevance": round(overall_summary.avg_relevance or 0, 3),
                "overall_success_rate": round(
                    (overall_summary.processed_articles / max(overall_summary.total_articles, 1)) * 100, 2
                )
            },
            "generated_at": datetime.utcnow().isoformat()
        })
        
        if export_format:
            if export_format == ExportFormatEnum.JSON:
                return traffic_data
        
        return {
            "status": "success",
            "message": f"Traffic analytics generado para período {timeframe}",
            "data": traffic_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generando traffic analytics: {str(e)}")

@router.get("/analytics/export")
async def export_analytics_report(
    report_type: str = Query("dashboard", description="Tipo de reporte a exportar"),
    timeframe: TimeFrameEnum = Query(TimeFrameEnum.WEEK, description="Período de tiempo"),
    format: ExportFormatEnum = Query(ExportFormatEnum.JSON, description="Formato de exportación"),
    custom_params: Optional[str] = Query(None, description="Parámetros adicionales en JSON")
):
    """
    Exportar reportes de analytics en diferentes formatos
    
    - **report_type**: Tipo de reporte (dashboard, trends, topics, sentiment, sources, traffic)
    - **timeframe**: Período de tiempo
    - **format**: Formato de exportación (json, csv, xlsx)
    - **custom_params**: Parámetros adicionales en formato JSON
    """
    try:
        # TODO: Implementar lógica de exportación avanzada
        # Por ahora retornamos información sobre el endpoint de exportación
        
        export_info = {
            "report_type": report_type,
            "timeframe": timeframe,
            "format": format,
            "custom_params": json.loads(custom_params) if custom_params else None,
            "status": "export_prepared",
            "message": f"Reporte de {report_type} preparado para exportación en formato {format}",
            "download_url": f"/api/v1/analytics/download/{report_type}_{timeframe}_{format}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
        }
        
        return {
            "status": "success",
            "message": "Reporte preparado para descarga",
            "data": export_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error preparando exportación: {str(e)}")

@router.get("/analytics/summary")
async def get_analytics_summary():
    """
    Obtener resumen general de todas las métricas disponibles
    """
    try:
        summary = {
            "available_endpoints": {
                "dashboard": "Resumen general de métricas",
                "trends": "Tendencias temporales de artículos y sentimientos",
                "topics": "Análisis detallado de temas y tópicos",
                "sentiment": "Análisis de sentimientos y polaridad",
                "sources": "Estadísticas por fuente de noticias",
                "traffic": "Métricas de tráfico y rendimiento"
            },
            "timeframes_available": [
                {"value": tf.value, "description": f"{tf.value} ({tf.name.replace('_', ' ').lower()})"}
                for tf in TimeFrameEnum
            ],
            "aggregation_options": [
                {"value": agg.value, "description": f"Agregación {agg.value}"}
                for agg in AggregationEnum
            ],
            "export_formats": [
                {"value": fmt.value, "description": f"Formato {fmt.value.upper()}"}
                for fmt in ExportFormatEnum
            ],
            "features": [
                "Parámetros de timeframe configurables",
                "Agregación de datos temporal",
                "Exportación de reportes",
                "Filtros avanzados por fuente y tema",
                "Métricas de rendimiento y calidad",
                "Análisis de tendencias y co-ocurrencias"
            ],
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "success",
            "message": "Resumen de analytics obtenido exitosamente",
            "data": summary
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo resumen: {str(e)}")