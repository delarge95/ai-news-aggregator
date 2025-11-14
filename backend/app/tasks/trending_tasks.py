"""
Tareas de actualización de trending topics para el sistema de búsqueda
Este módulo actualiza automáticamente las búsquedas populares y trending topics
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func, text

from app.db.models import Article, Source, TrendingTopic, UserPreference
from app.tasks.monitoring import monitor_task

logger = logging.getLogger(__name__)


@monitor_task(task_type="trending_update")
async def update_trending_topics(db: Session = None):
    """
    Actualizar tópicos trending basado en artículos recientes
    
    Analiza los últimos artículos para identificar temas populares
    y actualiza la tabla TrendingTopic con los scores de trending
    """
    try:
        logger.info("Iniciando actualización de trending topics")
        
        timeframes = ["1h", "6h", "24h", "7d"]
        
        for timeframe in timeframes:
            await update_timeframe_trending(timeframe, db)
        
        logger.info("Trending topics actualizados correctamente")
        
    except Exception as e:
        logger.error(f"Error actualizando trending topics: {str(e)}")
        raise


async def update_timeframe_trending(timeframe: str, db: Session):
    """
    Actualizar trending topics para un timeframe específico
    
    Args:
        timeframe: Período de tiempo (1h, 6h, 24h, 7d)
        db: Sesión de base de datos
    """
    try:
        # Calcular ventana de tiempo
        timeframe_map = {
            "1h": timedelta(hours=1),
            "6h": timedelta(hours=6),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7)
        }
        
        if timeframe not in timeframe_map:
            logger.warning(f"Timeframe inválido: {timeframe}")
            return
        
        date_from = datetime.utcnow() - timeframe_map[timeframe]
        
        # Obtener artículos del período
        articles_query = db.query(
            Article.topic_tags,
            Source.name.label('source_name'),
            Article.published_at,
            Article.sentiment_score
        ).join(Source).filter(
            and_(
                Article.published_at >= date_from,
                Article.topic_tags.isnot(None)
            )
        )
        
        articles = articles_query.all()
        
        # Procesar y agrupar topics
        topic_stats = {}
        
        for article in articles:
            topic_tags = article.topic_tags or []
            source_name = article.source_name
            
            for topic in topic_tags:
                if topic not in topic_stats:
                    topic_stats[topic] = {
                        'articles': set(),
                        'sources': set(),
                        'sentiment_sum': 0.0,
                        'sentiment_count': 0
                    }
                
                topic_stats[topic]['articles'].add(str(article.published_at.date()))  # Unique day
                topic_stats[topic]['sources'].add(source_name)
                
                if article.sentiment_score is not None:
                    topic_stats[topic]['sentiment_sum'] += article.sentiment_score
                    topic_stats[topic]['sentiment_count'] += 1
        
        # Calcular trending scores y actualizar base de datos
        for topic, stats in topic_stats.items():
            article_count = len(stats['articles'])
            sources_count = len(stats['sources'])
            
            # Calcular trend score
            avg_sentiment = (
                stats['sentiment_sum'] / stats['sentiment_count'] 
                if stats['sentiment_count'] > 0 else 0.0
            )
            
            # Fórmula de trending: combinación de frecuencia y diversidad
            trend_score = calculate_trend_score(article_count, sources_count, avg_sentiment)
            
            # Obtener o crear trending topic
            trending_topic = db.query(TrendingTopic).filter(
                and_(
                    TrendingTopic.topic == topic,
                    TrendingTopic.time_period == timeframe
                )
            ).first()
            
            if trending_topic:
                # Actualizar existente
                trending_topic.article_count = article_count
                trending_topic.sources_count = sources_count
                trending_topic.trend_score = trend_score
                trending_topic.date_recorded = datetime.utcnow()
                trending_topic.metadata = {
                    'avg_sentiment': avg_sentiment,
                    'sources_list': list(stats['sources'])
                }
            else:
                # Crear nuevo
                trending_topic = TrendingTopic(
                    topic=topic,
                    topic_category=classify_topic_category(topic),
                    article_count=article_count,
                    sources_count=sources_count,
                    trend_score=trend_score,
                    time_period=timeframe,
                    date_recorded=datetime.utcnow(),
                    metadata={
                        'avg_sentiment': avg_sentiment,
                        'sources_list': list(stats['sources'])
                    }
                )
                db.add(trending_topic)
        
        # Limpiar trending topics antiguos para este timeframe
        cleanup_old_trending_topics(timeframe, db)
        
        # Commit cambios
        db.commit()
        
        logger.info(f"Trending topics actualizados para timeframe {timeframe}: {len(topic_stats)} topics")
        
    except Exception as e:
        logger.error(f"Error actualizando trending para {timeframe}: {str(e)}")
        db.rollback()
        raise


def calculate_trend_score(article_count: int, sources_count: int, avg_sentiment: float) -> float:
    """
    Calcular trend score basado en métricas
    
    Args:
        article_count: Número de artículos
        sources_count: Número de fuentes diferentes
        avg_sentiment: Sentimiento promedio (-1.0 a 1.0)
        
    Returns:
        Score de trending (0.0 a 1.0)
    """
    try:
        # Normalizar article count (logarítmico para evitar sesgo)
        import math
        article_score = min(1.0, math.log10(max(1, article_count)) / 2.0)
        
        # Score de diversidad de fuentes
        source_score = min(1.0, sources_count / 10.0)
        
        # Score de sentimiento (valores extremos son más "trending")
        sentiment_score = abs(avg_sentiment)
        
        # Combinar scores
        trend_score = (article_score * 0.4 + source_score * 0.4 + sentiment_score * 0.2)
        
        return round(trend_score, 3)
        
    except Exception as e:
        logger.error(f"Error calculando trend score: {str(e)}")
        return 0.0


def classify_topic_category(topic: str) -> str:
    """
    Clasificar topic en categoría general
    
    Args:
        topic: Término del topic
        
    Returns:
        Categoría general
    """
    topic_lower = topic.lower()
    
    # Mapeo de términos a categorías
    category_map = {
        'politics': ['politics', 'government', 'election', 'president', 'congress'],
        'technology': ['technology', 'tech', 'ai', 'artificial intelligence', 'software', 'hardware'],
        'business': ['business', 'economy', 'market', 'finance', 'stock', 'company'],
        'health': ['health', 'medical', 'medicine', 'hospital', 'doctor', 'treatment'],
        'science': ['science', 'research', 'study', 'discovery', 'experiment'],
        'sports': ['sports', 'football', 'basketball', 'soccer', 'baseball', 'tennis'],
        'entertainment': ['entertainment', 'movie', 'music', 'celebrity', 'celebrity'],
        'international': ['international', 'global', 'world', 'foreign', 'country']
    }
    
    for category, keywords in category_map.items():
        if any(keyword in topic_lower for keyword in keywords):
            return category
    
    return 'general'


def cleanup_old_trending_topics(timeframe: str, db: Session):
    """
    Limpiar trending topics antiguos para un timeframe
    
    Args:
        timeframe: Período de tiempo
        db: Sesión de base de datos
    """
    try:
        # Mantener solo los últimos 100 entries por timeframe
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        old_topics = db.query(TrendingTopic).filter(
            and_(
                TrendingTopic.time_period == timeframe,
                TrendingTopic.date_recorded < cutoff_date
            )
        )
        
        old_topics.delete()
        
        logger.info(f"Limpieza de trending topics completada para {timeframe}")
        
    except Exception as e:
        logger.error(f"Error limpiando trending topics: {str(e)}")


async def get_search_analytics(db: Session) -> Dict[str, Any]:
    """
    Obtener analytics de búsquedas para análisis de tendencias
    
    Args:
        db: Sesión de base de datos
        
    Returns:
        Diccionario con analytics de búsqueda
    """
    try:
        analytics = {}
        
        # Analytics por timeframe
        timeframes = ["1h", "6h", "24h", "7d"]
        
        for timeframe in timeframes:
            # Top trending topics
            trending_query = db.query(
                TrendingTopic.topic,
                TrendingTopic.article_count,
                TrendingTopic.sources_count,
                TrendingTopic.trend_score
            ).filter(
                TrendingTopic.time_period == timeframe
            ).order_by(
                desc(TrendingTopic.trend_score)
            ).limit(10)
            
            top_topics = [
                {
                    'topic': topic,
                    'articles': article_count,
                    'sources': sources_count,
                    'score': trend_score
                }
                for topic, article_count, sources_count, trend_score in trending_query.all()
            ]
            
            analytics[f'top_topics_{timeframe}'] = top_topics
        
        # Analytics por categoría
        category_stats = db.query(
            TrendingTopic.topic_category,
            func.count(TrendingTopic.id).label('topic_count'),
            func.avg(TrendingTopic.trend_score).label('avg_score')
        ).group_by(TrendingTopic.topic_category).all()
        
        analytics['by_category'] = [
            {
                'category': category,
                'topic_count': topic_count,
                'avg_score': float(avg_score) if avg_score else 0.0
            }
            for category, topic_count, avg_score in category_stats
        ]
        
        return analytics
        
    except Exception as e:
        logger.error(f"Error obteniendo analytics: {str(e)}")
        return {}


# Tarea programada para ejecutar cada hora
async def scheduled_trending_update():
    """
    Tarea programada para actualizar trending topics cada hora
    """
    logger.info("Ejecutando actualización programada de trending topics")
    
    try:
        # Importar aquí para evitar circular imports
        from app.db.database import get_db
        from sqlalchemy.orm import sessionmaker
        
        # Esta función sería llamada por Celery u otro scheduler
        # Por ahora solo log
        logger.info("Trending topics update scheduled task executed")
        
    except Exception as e:
        logger.error(f"Error en scheduled trending update: {str(e)}")


if __name__ == "__main__":
    # Script para ejecutar manualmente
    import asyncio
    from app.db.database import get_db
    
    async def main():
        # Crear sesión de prueba
        from app.db.database import engine
        from sqlalchemy.orm import sessionmaker
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        try:
            await update_trending_topics(db)
            print("Trending topics actualizados correctamente")
        except Exception as e:
            print(f"Error: {str(e)}")
        finally:
            db.close()
    
    asyncio.run(main())