"""
Tareas de Celery para procesamiento en lote de artículos
Maneja el análisis de múltiples artículos de forma eficiente
"""

import time
import asyncio
from typing import List, Dict, Any, Optional
from celery import Task
from loguru import logger

from celery_app import celery_app
from app.core.config import settings
from app.services.news_service import NewsClientError


class BatchAnalysisTask(Task):
    """Task base para análisis en lote con retry y manejo de errores"""
    
    autoretry_for = (NewsClientError, Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 120}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler de falla para logging y monitoreo"""
        logger.error(f"💥 Error en análisis en lote {task_id}: {exc}")
        logger.debug(f"Detalles del error: {einfo}")


@celery_app.task(
    bind=True,
    name='app.tasks.batch_tasks.batch_analyze_articles',
    base=BatchAnalysisTask,
    queue='ai_analysis',
    rate_limit='5/m'
)
def batch_analyze_articles(
    self, 
    articles: List[Dict[str, Any]], 
    analysis_type: str = 'comprehensive',
    batch_size: int = 5,
    max_workers: int = 3
) -> Dict[str, Any]:
    """
    Analizar múltiples artículos en lotes usando análisis asíncrono
    
    Args:
        articles: Lista de artículos a analizar
        analysis_type: Tipo de análisis a aplicar
        batch_size: Tamaño del lote para procesamiento
        max_workers: Máximo número de workers concurrentes
        
    Returns:
        Dict con resultados del procesamiento en lote
    """
    start_time = time.time()
    
    try:
        logger.info(f"📊 Iniciando análisis en lote de {len(articles)} artículos con tipo: {analysis_type}")
        
        if not articles:
            return {
                'status': 'empty',
                'message': 'No hay artículos para procesar',
                'total_processed': 0,
                'processing_time': time.time() - start_time
            }
        
        # Dividir artículos en lotes
        batches = _create_batches(articles, batch_size)
        total_batches = len(batches)
        
        logger.info(f"🔄 Procesando {total_batches} lotes de hasta {batch_size} artículos cada uno")
        
        # Procesar cada lote secuencialmente para evitar sobrecarga
        all_results = []
        failed_articles = []
        
        for batch_num, batch in enumerate(batches, 1):
            logger.info(f"🔄 Procesando lote {batch_num}/{total_batches} ({len(batch)} artículos)")
            
            try:
                batch_result = _process_single_batch(batch, analysis_type, max_workers)
                all_results.extend(batch_result['successful'])
                failed_articles.extend(batch_result['failed'])
                
                logger.debug(f"✅ Lote {batch_num} completado: {len(batch_result['successful'])} exitosos, {len(batch_result['failed'])} fallidos")
                
            except Exception as e:
                logger.error(f"❌ Error procesando lote {batch_num}: {str(e)}")
                # Marcar todos los artículos del lote como fallidos
                failed_articles.extend([{'article': article, 'error': str(e)} for article in batch])
        
        # Preparar resumen de resultados
        total_processed = len(all_results)
        total_failed = len(failed_articles)
        processing_time = time.time() - start_time
        
        result_summary = {
            'status': 'completed',
            'total_articles': len(articles),
            'total_processed': total_processed,
            'total_failed': total_failed,
            'success_rate': (total_processed / len(articles)) * 100 if articles else 0,
            'processing_time': processing_time,
            'average_time_per_article': processing_time / len(articles) if articles else 0,
            'batch_size_used': batch_size,
            'analysis_type': analysis_type,
            'task_id': self.request.id,
            'completed_at': time.time()
        }
        
        # Agregar resultados detallados si no son demasiados
        if len(articles) <= 50:  # Solo incluir detalles para lotes pequeños
            result_summary.update({
                'successful_results': all_results,
                'failed_articles': failed_articles
            })
        
        logger.info(f"✅ Análisis en lote completado: {total_processed}/{len(articles)} exitosos en {processing_time:.2f}s")
        
        return result_summary
        
    except Exception as e:
        logger.error(f"❌ Error crítico en análisis en lote: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'total_articles': len(articles) if articles else 0,
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


def _create_batches(items: List[Any], batch_size: int) -> List[List[Any]]:
    """Crear lotes de artículos para procesamiento"""
    batches = []
    for i in range(0, len(items), batch_size):
        batches.append(items[i:i + batch_size])
    return batches


def _process_single_batch(
    batch: List[Dict[str, Any]], 
    analysis_type: str, 
    max_workers: int
) -> Dict[str, Any]:
    """Procesar un solo lote de artículos"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    successful_results = []
    failed_articles = []
    
    # Ejecutar análisis para cada artículo en el lote
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Enviar tareas de análisis
        future_to_article = {
            executor.submit(_analyze_single_article_sync, article, analysis_type): article 
            for article in batch
        }
        
        # Recopilar resultados
        for future in as_completed(future_to_article):
            article = future_to_article[future]
            
            try:
                result = future.result(timeout=60)  # Timeout de 60 segundos por artículo
                if result.get('status') == 'completed':
                    successful_results.append(result)
                else:
                    failed_articles.append({
                        'article': article, 
                        'error': result.get('error_message', 'Error desconocido')
                    })
            except Exception as e:
                logger.warning(f"❌ Error analizando artículo: {str(e)}")
                failed_articles.append({
                    'article': article,
                    'error': str(e)
                })
    
    return {
        'successful': successful_results,
        'failed': failed_articles
    }


def _analyze_single_article_sync(article: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """Análisis síncrono de un artículo (wrapper para usar en ThreadPoolExecutor)"""
    try:
        # Importar la tarea de análisis individual
        from app.tasks.article_tasks import analyze_article_async
        
        # Ejecutar de forma síncrona (blocking)
        result = analyze_article_sync(article, analysis_type)
        return result
        
    except Exception as e:
        logger.error(f"Error en análisis síncrono de artículo: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e),
            'article_id': article.get('id'),
            'analysis_type': analysis_type
        }


def analyze_article_sync(article: Dict[str, Any], analysis_type: str) -> Dict[str, Any]:
    """Versión síncrona del análisis para usar en ThreadPoolExecutor"""
    import time
    start_time = time.time()
    
    try:
        logger.debug(f"🔍 Analizando artículo síncrono: {article.get('title', 'Sin título')[:30]}...")
        
        # Validar datos del artículo
        if not article.get('content') and not article.get('description'):
            raise ValueError("El artículo debe tener contenido o descripción para analizar")
        
        # Preparar el texto a analizar
        text_to_analyze = f"""
        Título: {article.get('title', '')}
        Descripción: {article.get('description', '')}
        Contenido: {article.get('content', '')[:2000]}...
        Fuente: {article.get('source_name', '')}
        """
        
        # Realizar el análisis según el tipo
        if analysis_type == 'basic':
            analysis_result = _sync_basic_analysis(text_to_analyze)
        elif analysis_type == 'sentiment':
            analysis_result = _sync_sentiment_analysis(text_to_analyze)
        else:  # comprehensive
            analysis_result = _sync_comprehensive_analysis(text_to_analyze)
        
        # Agregar metadata al resultado
        analysis_result.update({
            'article_id': article.get('id'),
            'article_url': article.get('url'),
            'analysis_type': analysis_type,
            'analysis_timestamp': time.time(),
            'processing_time': time.time() - start_time,
            'status': 'completed',
            'sync_mode': True
        })
        
        logger.debug(f"✅ Análisis síncrono completado en {analysis_result['processing_time']:.2f}s")
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Error en análisis síncrono: {str(e)}")
        return {
            'status': 'error',
            'error_message': str(e),
            'article_id': article.get('id'),
            'analysis_type': analysis_type,
            'analysis_timestamp': time.time(),
            'processing_time': time.time() - start_time,
            'sync_mode': True
        }


def _sync_basic_analysis(text: str) -> Dict[str, Any]:
    """Análisis básico síncrono"""
    # Usar las funciones de fallback para análisis síncrono
    return _sync_fallback_analysis(text, 'basic')


def _sync_comprehensive_analysis(text: str) -> Dict[str, Any]:
    """Análisis comprensivo síncrono"""
    return _sync_fallback_analysis(text, 'comprehensive')


def _sync_sentiment_analysis(text: str) -> Dict[str, Any]:
    """Análisis de sentimiento síncrono"""
    return _sync_fallback_analysis(text, 'sentiment')


def _sync_fallback_analysis(text: str, analysis_type: str) -> Dict[str, Any]:
    """Análisis de fallback síncrono usando técnicas tradicionales"""
    import re
    from collections import Counter
    
    # Análisis básico por palabras clave
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = Counter(words)
    
    if analysis_type == 'basic':
        # Análisis básico
        categories = {
            'tecnología': ['technology', 'tech', 'software', 'digital', 'ai', 'artificial intelligence'],
            'política': ['government', 'political', 'policy', 'election', 'parliament'],
            'economía': ['economic', 'economy', 'market', 'financial', 'business'],
            'deportes': ['sport', 'football', 'basketball', 'soccer', 'tennis'],
            'salud': ['health', 'medical', 'hospital', 'disease', 'treatment']
        }
        
        scores = {}
        for category, keywords in categories.items():
            score = sum(word_freq.get(keyword, 0) for keyword in keywords)
            if score > 0:
                scores[category] = score
        
        main_category = max(scores, key=scores.get) if scores else 'general'
        
        return {
            'summary': text[:200] + '...' if len(text) > 200 else text,
            'topics': list(scores.keys())[:4],
            'category': main_category,
            'urgency': 'media',
            'language': 'es',
            'analysis_method': 'sync_fallback'
        }
        
    elif analysis_type == 'sentiment':
        # Análisis de sentimiento
        positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'win']
        negative_words = ['bad', 'terrible', 'negative', 'fail', 'loss', 'crisis']
        
        text_lower = text.lower()
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment = 'positive'
            score = 0.6
        elif neg_count > pos_count:
            sentiment = 'negative'
            score = -0.6
        else:
            sentiment = 'neutral'
            score = 0.0
        
        return {
            'overall_sentiment': sentiment,
            'sentiment_score': score,
            'emotional_tone': 'neutral',
            'emotional_intensity': 'media',
            'confidence_level': 70,
            'analysis_method': 'sync_fallback'
        }
        
    else:  # comprehensive
        # Análisis comprensivo
        basic_result = _sync_fallback_analysis(text, 'basic')
        
        return {
            **basic_result,
            'key_points': basic_result.get('topics', [])[:5],
            'subcategories': [],
            'sentiment': 'neutral',
            'impact_level': 'local',
            'entities': [],
            'reading_time_minutes': max(1, len(text) // 200),
            'credibility_score': 7,
            'analysis_method': 'sync_comprehensive'
        }


@celery_app.task(
    bind=True,
    name='app.tasks.batch_tasks.process_pending_analyses',
    queue='ai_analysis',
    rate_limit='2/m'
)
def process_pending_analyses(self, batch_size: int = 10) -> Dict[str, Any]:
    """
    Procesar análisis pendientes de artículos en la base de datos
    
    Args:
        batch_size: Tamaño del lote para procesamiento
        
    Returns:
        Dict con información del procesamiento
    """
    start_time = time.time()
    
    try:
        logger.info(f"📋 Iniciando procesamiento de análisis pendientes (batch_size: {batch_size})")
        
        # TODO: Implementar lógica para obtener artículos pendientes de análisis
        # Esta es una implementación placeholder que debería integrarse con la base de datos
        
        # Simulación de artículos pendientes
        pending_articles = []  # Aquí iría la lógica real de BD
        
        if not pending_articles:
            return {
                'status': 'no_pending',
                'message': 'No hay análisis pendientes',
                'processing_time': time.time() - start_time
            }
        
        # Dividir en lotes y procesar
        batches = _create_batches(pending_articles, batch_size)
        
        total_processed = 0
        total_failed = 0
        
        for batch in batches:
            try:
                # Procesar lote
                result = batch_analyze_articles.delay(batch, 'comprehensive')
                
                # Esperar resultado (en implementación real sería asíncrono)
                batch_result = result.get(timeout=300)  # 5 minutos timeout
                
                total_processed += batch_result.get('total_processed', 0)
                total_failed += batch_result.get('total_failed', 0)
                
                logger.info(f"✅ Lote procesado: {batch_result.get('total_processed', 0)} exitosos")
                
            except Exception as e:
                logger.error(f"❌ Error procesando lote: {str(e)}")
                total_failed += len(batch)
        
        return {
            'status': 'completed',
            'total_processed': total_processed,
            'total_failed': total_failed,
            'processing_time': time.time() - start_time,
            'batches_processed': len(batches)
        }
        
    except Exception as e:
        logger.error(f"❌ Error en procesamiento de pendientes: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time
        }