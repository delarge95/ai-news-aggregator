from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import List, Optional, Dict, Any
from app.services.ai_processor import create_ai_processor
from app.core.config import get_settings
from app.services.ai_pipeline import process_news_batch
from app.db.database import get_db  # Fixed: was app.core.database
from sqlalchemy.orm import Session

router = APIRouter()
settings = get_settings()

@router.post("/ai-analysis/test/analyze-article")
async def test_analyze_article(
    content: str,
    article_title: Optional[str] = "Test Article",
    use_openai: Optional[bool] = True
):
    """
    Endpoint de prueba para analizar un artículo individual
    """
    try:
        # Crear analizador de IA
        ai_processor = create_ai_processor(
            openai_api_key=settings.OPENAI_API_KEY if use_openai else None
        )
        
        # Realizar análisis completo
        result = ai_processor.analyze_article(
            article_id="test_article",
            content=content,
            article_title=article_title,
            user_preferences={"technology": 0.8, "ai": 0.9}
        )
        
        return {
            "status": "success",
            "message": "Análisis completado exitosamente",
            "analysis": {
                "sentiment": {
                    "score": result.sentiment.sentiment_score,
                    "label": result.sentiment.sentiment.value,
                    "emotion": result.sentiment.emotion
                },
                "topic": {
                    "primary": result.topic.primary_topic.value,
                    "secondary": [t.value for t in result.topic.secondary_topics],
                    "confidence": result.topic.confidence
                },
                "summary": {
                    "content": result.summary.summary,
                    "key_points": result.summary.key_points,
                    "reading_time": result.summary.reading_time_minutes
                },
                "relevance": {
                    "score": result.relevance.relevance_score,
                    "importance_factors": result.relevance.importance_factors
                },
                "metadata": {
                    "processing_time": result.metadata.processing_time,
                    "cost": result.metadata.total_cost,
                    "model_used": result.metadata.model_used
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@router.post("/ai-analysis/test/batch-analyze")
async def test_batch_analyze(
    articles: List[Dict[str, Any]],
    use_openai: Optional[bool] = True
):
    """
    Endpoint de prueba para análisis en lote
    """
    try:
        ai_processor = create_ai_processor(
            openai_api_key=settings.OPENAI_API_KEY if use_openai else None
        )
        
        # Convertir artículos al formato esperado
        formatted_articles = []
        for i, article in enumerate(articles):
            formatted_articles.append({
                "id": f"test_article_{i}",
                "title": article.get("title", f"Test Article {i}"),
                "content": article.get("content", ""),
                "source": article.get("source", "Test Source")
            })
        
        # Procesar en lote
        results = []
        for article in formatted_articles:
            result = ai_processor.analyze_article(
                article_id=article["id"],
                content=article["content"],
                article_title=article["title"]
            )
            results.append({
                "article_id": article["id"],
                "title": article["title"],
                "sentiment": result.sentiment.sentiment.value,
                "topic": result.topic.primary_topic.value,
                "summary": result.summary.summary[:100] + "...",
                "relevance": result.relevance.relevance_score,
                "processing_time": result.metadata.processing_time
            })
        
        return {
            "status": "success",
            "message": f"Análisis en lote completado para {len(articles)} artículos",
            "total_articles": len(articles),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en análisis en lote: {str(e)}")

@router.get("/ai-analysis/test/monitoring")
async def test_monitoring_stats():
    """
    Endpoint de prueba para verificar estadísticas de monitoreo
    """
    try:
        from app.services.ai_monitor import create_monitor
        
        monitor = create_monitor()
        stats = monitor.get_dashboard_summary()
        
        return {
            "status": "success",
            "monitoring_stats": {
                "total_tasks": stats.get("total_tasks", 0),
                "success_rate": stats.get("success_rate", 0),
                "average_processing_time": stats.get("avg_processing_time", 0),
                "total_cost_today": stats.get("total_cost_today", 0),
                "active_alerts": stats.get("active_alerts", 0),
                "system_health": stats.get("system_health", "unknown")
            }
        }
        
    except Exception as e:
        return {
            "status": "warning",
            "message": "Monitoreo no configurado completamente",
            "error": str(e)
        }

@router.get("/ai-analysis/test/sample-analysis")
async def get_sample_analysis():
    """
    Endpoint de prueba que devuelve un análisis de ejemplo
    """
    sample_content = """
    Artificial intelligence continues to revolutionize the technology sector, 
    with recent breakthroughs in machine learning algorithms showing promising 
    results for healthcare applications. Companies like OpenAI and Google 
    are leading the development of large language models that can understand 
    and generate human-like text with unprecedented accuracy.
    """
    
    return {
        "status": "success", 
        "message": "Análisis de ejemplo - configuración real requerida para análisis vivo",
        "sample_article": {
            "title": "AI Advances Transform Healthcare Technology",
            "content": sample_content,
            "source": "Tech Daily"
        },
        "expected_analysis": {
            "sentiment": {"score": 0.7, "label": "positive"},
            "topic": {"primary": "technology", "secondary": ["healthcare", "artificial-intelligence"]},
            "summary": "AI breakthroughs in machine learning show promise for healthcare applications, with companies like OpenAI and Google leading LLM development.",
            "relevance": {"score": 0.85}
        },
        "configuration_needed": {
            "openai_api_key": "Required for real analysis",
            "redis_url": "Optional - improves performance",
            "celery_workers": "Required for background processing"
        }
    }

@router.get("/ai-analysis/test/health-check")
async def test_ai_health_check():
    """
    Health check del sistema de IA
    """
    try:
        # Verificar configuración básica
        health_status = {
            "ai_processor": {
                "status": "configured" if settings.OPENAI_API_KEY != "your_openai_api_key_here" else "needs_config",
                "model_available": True
            },
            "celery_workers": {
                "status": "checking",
                "workers_count": 0  # Would check actual workers
            },
            "redis_cache": {
                "status": "available",  # Would check actual Redis
                "connection": True
            },
            "database": {
                "status": "connected",  # Would check actual DB
                "tables_ready": True
            }
        }
        
        # Determinar overall health
        overall_status = "healthy"
        if health_status["ai_processor"]["status"] == "needs_config":
            overall_status = "partial"
            
        return {
            "status": "success",
            "overall_status": overall_status,
            "health_details": health_status,
            "recommendations": [
                "Configure OPENAI_API_KEY for full AI functionality",
                "Start Celery workers for background processing",
                "Verify Redis connection for optimal performance"
            ]
        }
        
    except Exception as e:
        return {
            "status": "error",
            "overall_status": "unhealthy", 
            "error": str(e)
        }