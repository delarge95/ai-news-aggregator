"""
Ejemplo de uso del Pipeline de IA en AI News Aggregator

Este archivo demuestra cómo integrar el AIPipelineOrchestrator
con los servicios existentes y el flujo de la aplicación.
"""

import asyncio
import logging
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_pipeline import (
    AIPipelineOrchestrator, 
    ProcessingConfig, 
    process_news_batch,
    DEFAULT_CONFIGS
)
from app.services.newsapi_client import NewsAPIClient
from app.services.guardian_client import GuardianAPIClient
from app.services.nytimes_client import NYTimesClient
from app.db.database import get_db_session
from app.core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsProcessingService:
    """Servicio principal para procesamiento de noticias con IA"""
    
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or DEFAULT_CONFIGS['production']
        self.pipeline = AIPipelineOrchestrator(self.config)
        
        # Inicializar clientes de noticias
        self.newsapi_client = NewsAPIClient() if settings.NEWSAPI_KEY else None
        self.guardian_client = GuardianAPIClient() if settings.GUARDIAN_API_KEY else None
        self.nytimes_client = NYTimesClient() if settings.NYTimes_API_KEY else None
    
    async def process_latest_news(self, topic: str = "technology", 
                                max_articles: int = 50) -> Dict[str, Any]:
        """
        Obtiene y procesa las últimas noticias sobre un tema específico
        
        Args:
            topic: Tema de búsqueda
            max_articles: Máximo número de artículos a procesar
            
        Returns:
            Dict con estadísticas del procesamiento
        """
        logger.info(f"Iniciando procesamiento de noticias sobre: {topic}")
        
        # Obtener artículos de múltiples fuentes
        all_articles = []
        
        if self.newsapi_client:
            try:
                articles = await self.newsapi_client.get_top_headlines(
                    q=topic, 
                    page_size=min(max_articles // 3, 20)
                )
                all_articles.extend(articles)
                logger.info(f"NewsAPI: {len(articles)} artículos obtenidos")
            except Exception as e:
                logger.error(f"Error obteniendo artículos de NewsAPI: {e}")
        
        if self.guardian_client:
            try:
                articles = await self.guardian_client.search_articles(
                    q=topic,
                    page_size=min(max_articles // 3, 20)
                )
                all_articles.extend(articles)
                logger.info(f"Guardian: {len(articles)} artículos obtenidos")
            except Exception as e:
                logger.error(f"Error obteniendo artículos de Guardian: {e}")
        
        if self.nytimes_client:
            try:
                articles = await self.nytimes_client.search_articles(
                    query=topic,
                    limit=min(max_articles // 3, 20)
                )
                all_articles.extend(articles)
                logger.info(f"NYTimes: {len(articles)} artículos obtenidos")
            except Exception as e:
                logger.error(f"Error obteniendo artículos de NYTimes: {e}")
        
        if not all_articles:
            logger.warning("No se obtuvieron artículos de ninguna fuente")
            return {"status": "error", "message": "No se obtuvieron artículos"}
        
        # Obtener sesión de base de datos
        async with get_db_session() as session:
            # Procesar artículos con pipeline de IA
            result = await process_news_batch(
                raw_articles=all_articles,
                source_type='multi_source',
                session=session
            )
        
        # Compilar estadísticas
        stats = {
            "status": "success",
            "topic": topic,
            "total_articles_found": len(all_articles),
            "processing_result": {
                "total_processed": result.total_articles,
                "successful_analyses": result.successful_analyses,
                "failed_analyses": result.failed_analyses,
                "processing_time_seconds": result.processing_time,
                "articles_per_second": result.total_articles / result.processing_time if result.processing_time > 0 else 0
            },
            "metadata": result.metadata,
            "errors": result.errors[:5]  # Primeros 5 errores
        }
        
        logger.info(f"Procesamiento completado: {stats['processing_result']}")
        return stats
    
    async def process_single_article_url(self, url: str) -> Dict[str, Any]:
        """
        Procesa un artículo específico por URL
        
        Args:
            url: URL del artículo a procesar
            
        Returns:
            Dict con resultado del procesamiento
        """
        logger.info(f"Procesando artículo: {url}")
        
        # Crear artículo crudo desde URL (simulado)
        # En un caso real, necesitarías scraping o API específica
        raw_article = {
            "title": "Sample Article from URL",
            "content": "This would be the actual content extracted from the URL...",
            "url": url,
            "source_name": "Unknown Source"
        }
        
        async with get_db_session() as session:
            result = await process_news_batch(
                raw_articles=[raw_article],
                source_type='generic',
                session=session
            )
        
        return {
            "status": "success" if result.successful_analyses > 0 else "failed",
            "url": url,
            "processing_time": result.processing_time,
            "analyses_completed": result.successful_analyses,
            "results": result.results
        }
    
    async def batch_process_scheduled_news(self, sources: List[str] = None) -> Dict[str, Any]:
        """
        Procesa noticias programadas desde fuentes específicas
        
        Args:
            sources: Lista de fuentes específicas ('newsapi', 'guardian', 'nytimes')
            
        Returns:
            Dict con estadísticas del procesamiento
        """
        logger.info("Iniciando procesamiento programado de noticias")
        
        if not sources:
            sources = ['newsapi', 'guardian', 'nytimes']
        
        async with get_db_session() as session:
            # Procesar cada fuente por separado
            source_results = {}
            
            for source in sources:
                try:
                    if source == 'newsapi' and self.newsapi_client:
                        articles = await self.newsapi_client.get_top_headlines(page_size=20)
                        result = await process_news_batch(
                            raw_articles=articles,
                            source_type='newsapi',
                            session=session
                        )
                        source_results['newsapi'] = result
                        
                    elif source == 'guardian' and self.guardian_client:
                        articles = await self.guardian_client.get_latest_articles(page_size=20)
                        result = await process_news_batch(
                            raw_articles=articles,
                            source_type='guardian',
                            session=session
                        )
                        source_results['guardian'] = result
                        
                    elif source == 'nytimes' and self.nytimes_client:
                        articles = await self.nytimes_client.get_latest_articles(limit=20)
                        result = await process_news_batch(
                            raw_articles=articles,
                            source_type='nytimes',
                            session=session
                        )
                        source_results['nytimes'] = result
                        
                except Exception as e:
                    logger.error(f"Error procesando fuente {source}: {e}")
                    source_results[source] = {"error": str(e)}
            
            # Compilar estadísticas generales
            total_processed = sum(r.total_articles for r in source_results.values() if hasattr(r, 'total_articles'))
            total_successful = sum(r.successful_analyses for r in source_results.values() if hasattr(r, 'successful_analyses'))
            
            return {
                "status": "completed",
                "sources_processed": len([s for s in sources if s in source_results]),
                "total_articles": total_processed,
                "total_successful_analyses": total_successful,
                "source_results": {k: v.__dict__ if hasattr(v, '__dict__') else v 
                                 for k, v in source_results.items()}
            }


async def example_usage():
    """Ejemplo de uso completo del servicio de procesamiento"""
    
    # Configurar servicio con configuración de producción
    config = DEFAULT_CONFIGS['production']
    news_service = NewsProcessingService(config)
    
    print("=== Ejemplo de Uso del Pipeline de IA ===\n")
    
    # Ejemplo 1: Procesar últimas noticias
    print("1. Procesando últimas noticias sobre tecnología...")
    result1 = await news_service.process_latest_news(
        topic="artificial intelligence", 
        max_articles=30
    )
    print(f"Estado: {result1['status']}")
    print(f"Artículos procesados: {result1['processing_result']['total_processed']}")
    print(f"Análisis exitosos: {result1['processing_result']['successful_analyses']}")
    print(f"Tiempo de procesamiento: {result1['processing_result']['processing_time_seconds']:.2f}s")
    print()
    
    # Ejemplo 2: Procesamiento programado
    print("2. Procesamiento programado de múltiples fuentes...")
    result2 = await news_service.batch_process_scheduled_news(
        sources=['newsapi', 'guardian']
    )
    print(f"Estado: {result2['status']}")
    print(f"Fuentes procesadas: {result2['sources_processed']}")
    print(f"Total artículos: {result2['total_articles']}")
    print()
    
    # Ejemplo 3: Artículo individual
    print("3. Procesando artículo individual...")
    result3 = await news_service.process_single_article_url(
        url="https://example.com/article/123"
    )
    print(f"Estado: {result3['status']}")
    print(f"Análisis completados: {result3['analyses_completed']}")
    print(f"Tiempo: {result3['processing_time']:.2f}s")
    print()


# Función para uso en tareas programadas (Celery)
async def scheduled_news_processor():
    """
    Función para tareas programadas (Celery, cron, etc.)
    
    Usage:
    - Celery: @celery_app.task
    - Cron: ejecutando este script
    - Docker: como scheduled job
    """
    try:
        news_service = NewsProcessingService(DEFAULT_CONFIGS['production'])
        
        # Procesar noticias sobre múltiples temas
        topics = ["technology", "science", "health", "business"]
        results = []
        
        for topic in topics:
            logger.info(f"Procesando tema: {topic}")
            result = await news_service.process_latest_news(
                topic=topic, 
                max_articles=20
            )
            results.append(result)
        
        # Compilar reporte final
        total_articles = sum(r['processing_result']['total_processed'] for r in results)
        total_successful = sum(r['processing_result']['successful_analyses'] for r in results)
        
        logger.info(f"Tarea programada completada: {total_articles} artículos, "
                   f"{total_successful} análisis exitosos")
        
        return {
            "status": "completed",
            "topics_processed": len(topics),
            "total_articles": total_articles,
            "total_successful_analyses": total_successful,
            "topic_results": results
        }
        
    except Exception as e:
        logger.error(f"Error en tarea programada: {e}")
        return {"status": "error", "message": str(e)}


# Función para testing y desarrollo
async def test_pipeline():
    """Función de testing para desarrollo"""
    
    print("=== Testing Pipeline de IA ===\n")
    
    # Configuración de desarrollo
    config = DEFAULT_CONFIGS['development']
    
    # Artículos de prueba
    test_articles = [
        {
            "title": "AI Breakthrough in Medical Diagnosis",
            "content": "Scientists have developed a new AI system that can detect diseases with 95% accuracy. The system uses advanced machine learning algorithms to analyze medical images and identify patterns that human doctors might miss. This breakthrough could revolutionize healthcare worldwide.",
            "url": "https://example.com/ai-medical-1",
            "source_name": "Tech Medical News",
            "published_at": "2025-01-15T10:00:00Z"
        },
        {
            "title": "Climate Change Report Shows Urgent Action Needed",
            "content": "The latest climate report indicates that immediate action is required to prevent catastrophic environmental changes. Rising temperatures, melting ice caps, and extreme weather patterns demand global cooperation and innovative solutions.",
            "url": "https://example.com/climate-report-1",
            "source_name": "Environmental Daily",
            "published_at": "2025-01-15T09:30:00Z"
        }
    ]
    
    async with get_db_session() as session:
        # Procesar artículos de prueba
        result = await process_news_batch(
            raw_articles=test_articles,
            source_type='test',
            session=session
        )
    
    print(f"Lote procesado:")
    print(f"  - ID: {result.batch_id[:8]}...")
    print(f"  - Artículos totales: {result.total_articles}")
    print(f"  - Análisis exitosos: {result.successful_analyses}")
    print(f"  - Análisis fallidos: {result.failed_analyses}")
    print(f"  - Tiempo: {result.processing_time:.2f}s")
    
    if result.results:
        print(f"\nPrimeros resultados:")
        for i, analysis in enumerate(result.results[:3]):
            print(f"  {i+1}. {analysis.analysis_type.value} - "
                  f"Confianza: {analysis.confidence_score:.2f}")
    
    return result


if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(example_usage())
    # asyncio.run(test_pipeline())  # Descomentar para testing
    # asyncio.run(scheduled_news_processor())  # Para tareas programadas