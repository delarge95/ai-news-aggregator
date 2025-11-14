"""
Tareas de Celery para generación asíncrona de resúmenes
Maneja la generación de resúmenes en lote de artículos
"""

import time
from typing import List, Dict, Any, Optional
from celery import Task
from loguru import logger

from celery_app import celery_app
from app.core.config import settings
from app.services.news_service import NewsClientError


class SummaryGenerationTask(Task):
    """Task base para generación de resúmenes con retry y manejo de errores"""
    
    autoretry_for = (NewsClientError, Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 90}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler de falla para logging y monitoreo"""
        logger.error(f"💥 Error en generación de resúmenes {task_id}: {exc}")
        logger.debug(f"Detalles del error: {einfo}")


@celery_app.task(
    bind=True,
    name='app.tasks.summary_tasks.generate_summaries_batch',
    base=SummaryGenerationTask,
    queue='ai_summaries',
    rate_limit='6/m'
)
def generate_summaries_batch(
    self, 
    articles: List[Dict[str, Any]], 
    summary_type: str = 'executive',
    max_summary_length: int = 200,
    min_article_length: int = 100,
    include_key_points: bool = True
) -> Dict[str, Any]:
    """
    Generar resúmenes de múltiples artículos en lotes
    
    Args:
        articles: Lista de artículos a resumir
        summary_type: Tipo de resumen ('brief', 'executive', 'comprehensive')
        max_summary_length: Longitud máxima del resumen en caracteres
        min_article_length: Longitud mínima del artículo para generar resumen
        include_key_points: Si incluir puntos clave en el resumen
        
    Returns:
        Dict con resultados de generación de resúmenes
    """
    start_time = time.time()
    
    try:
        logger.info(f"📝 Iniciando generación de resúmenes de {len(articles)} artículos (tipo: {summary_type})")
        
        if not articles:
            return {
                'status': 'empty',
                'message': 'No hay artículos para resumir',
                'total_processed': 0,
                'processing_time': time.time() - start_time
            }
        
        # Filtrar artículos válidos
        valid_articles = []
        skipped_articles = []
        
        for article_num, article in enumerate(articles, 1):
            if _is_article_valid_for_summary(article, min_article_length):
                valid_articles.append((article_num, article))
            else:
                skipped_articles.append({
                    'article_num': article_num,
                    'reason': 'Contenido insuficiente' if len(article.get('content', '') + article.get('description', '')) < min_article_length else 'Falta de título',
                    'article': article
                })
        
        logger.info(f"✅ Filtrados {len(valid_articles)} artículos válidos, {len(skipped_articles)} omitidos")
        
        # Generar resúmenes
        summary_results = []
        failed_summaries = []
        
        for article_num, article in valid_articles:
            try:
                logger.debug(f"📝 Generando resumen {article_num}/{len(valid_articles)}")
                
                result = _generate_single_summary(
                    article, 
                    summary_type, 
                    max_summary_length, 
                    include_key_points
                )
                
                if result['status'] == 'success':
                    summary_results.append(result)
                else:
                    failed_summaries.append({
                        'article_num': article_num,
                        'error': result.get('error'),
                        'article': article
                    })
                
            except Exception as e:
                logger.error(f"❌ Error generando resumen para artículo {article_num}: {str(e)}")
                failed_summaries.append({
                    'article_num': article_num,
                    'error': str(e),
                    'article': article
                })
        
        # Calcular métricas
        total_articles = len(articles)
        processed_articles = len(summary_results)
        failed_articles = len(failed_summaries)
        skipped_articles_count = len(skipped_articles)
        
        success_rate = (processed_articles / total_articles) * 100 if total_articles > 0 else 0
        
        processing_time = time.time() - start_time
        
        # Calcular estadísticas de longitud de resúmenes
        summary_lengths = [len(result['summary']) for result in summary_results]
        avg_summary_length = sum(summary_lengths) / len(summary_lengths) if summary_lengths else 0
        
        result_summary = {
            'status': 'completed',
            'summary_type': summary_type,
            'processing_time': processing_time,
            'statistics': {
                'total_articles': total_articles,
                'processed_articles': processed_articles,
                'failed_articles': failed_articles,
                'skipped_articles': skipped_articles_count,
                'success_rate': success_rate,
                'avg_summary_length': avg_summary_length,
                'max_summary_length_used': max_summary_length,
                'include_key_points': include_key_points
            },
            'task_id': self.request.id,
            'completed_at': time.time()
        }
        
        # Agregar resultados detallados para lotes pequeños
        if total_articles <= 30:
            result_summary.update({
                'successful_summaries': summary_results,
                'failed_summaries': failed_summaries,
                'skipped_articles': skipped_articles
            })
        
        logger.info(f"✅ Generación de resúmenes completada: {processed_articles}/{total_articles} exitosos ({success_rate:.1f}%)")
        logger.info(f"📊 Tiempo promedio por resumen: {processing_time / total_articles:.2f}s")
        
        return result_summary
        
    except Exception as e:
        logger.error(f"❌ Error crítico en generación de resúmenes: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'total_articles': len(articles) if articles else 0,
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


def _is_article_valid_for_summary(article: Dict[str, Any], min_length: int) -> bool:
    """Verificar si un artículo es válido para generar resumen"""
    title = article.get('title', '').strip()
    content = article.get('content', '').strip()
    description = article.get('description', '').strip()
    
    # Debe tener título
    if not title:
        return False
    
    # Debe tener contenido suficiente
    total_text = content + ' ' + description
    if len(total_text) < min_length:
        return False
    
    return True


def _generate_single_summary(
    article: Dict[str, Any], 
    summary_type: str, 
    max_length: int, 
    include_key_points: bool
) -> Dict[str, Any]:
    """
    Generar resumen para un solo artículo
    
    Args:
        article: Artículo a resumir
        summary_type: Tipo de resumen
        max_length: Longitud máxima
        include_key_points: Si incluir puntos clave
        
    Returns:
        Dict con resultado del resumen
    """
    try:
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')
        
        # Preparar texto base para el resumen
        base_text = f"{title} {description} {content}".strip()
        
        if not base_text:
            return {
                'status': 'error',
                'error': 'Artículo sin contenido',
                'article_id': article.get('id')
            }
        
        # Generar resumen según el tipo
        if summary_type == 'brief':
            summary_result = _generate_brief_summary(base_text, max_length)
        elif summary_type == 'comprehensive':
            summary_result = _generate_comprehensive_summary(base_text, max_length, include_key_points)
        else:  # executive
            summary_result = _generate_executive_summary(base_text, max_length, include_key_points)
        
        # Agregar metadata
        summary_result.update({
            'article_id': article.get('id'),
            'article_url': article.get('url'),
            'article_title': title,
            'summary_type': summary_type,
            'original_length': len(base_text),
            'summary_length': len(summary_result['summary']),
            'compression_ratio': len(summary_result['summary']) / len(base_text) if base_text else 0,
            'generated_at': time.time(),
            'method': summary_result.get('method', 'extractive')
        })
        
        return summary_result
        
    except Exception as e:
        logger.error(f"Error generando resumen: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'article_id': article.get('id')
        }


def _generate_executive_summary(text: str, max_length: int, include_key_points: bool) -> Dict[str, Any]:
    """Generar resumen ejecutivo (balance entre brevedad y completitud)"""
    try:
        # Usar OpenAI si está disponible
        if settings.OPENAI_API_KEY:
            return _generate_ai_summary(text, max_length, 'executive', include_key_points)
        else:
            return _generate_extractive_summary(text, max_length, 'executive')
    except Exception as e:
        logger.warning(f"Error en resumen ejecutivo: {str(e)}")
        return _generate_extractive_summary(text, max_length, 'executive')


def _generate_brief_summary(text: str, max_length: int) -> Dict[str, Any]:
    """Generar resumen breve (muy conciso)"""
    try:
        # Usar OpenAI si está disponible
        if settings.OPENAI_API_KEY:
            return _generate_ai_summary(text, max_length // 2, 'brief', False)
        else:
            return _generate_extractive_summary(text, max_length // 2, 'brief')
    except Exception as e:
        logger.warning(f"Error en resumen breve: {str(e)}")
        return _generate_extractive_summary(text, max_length // 2, 'brief')


def _generate_comprehensive_summary(text: str, max_length: int, include_key_points: bool) -> Dict[str, Any]:
    """Generar resumen comprensivo (más detallado)"""
    try:
        # Usar OpenAI si está disponible
        if settings.OPENAI_API_KEY:
            return _generate_ai_summary(text, max_length * 1.5, 'comprehensive', include_key_points)
        else:
            return _generate_extractive_summary(text, max_length, 'comprehensive')
    except Exception as e:
        logger.warning(f"Error en resumen comprensivo: {str(e)}")
        return _generate_extractive_summary(text, max_length, 'comprehensive')


def _generate_ai_summary(text: str, max_length: int, summary_type: str, include_key_points: bool) -> Dict[str, Any]:
    """Generar resumen usando OpenAI"""
    try:
        import openai
        
        openai.api_key = settings.OPENAI_MODEL
        
        # Configurar prompt según el tipo
        if summary_type == 'brief':
            prompt = f"Genera un resumen muy breve (máximo {max_length} caracteres) del siguiente artículo:\n\n{text[:1500]}"
            max_tokens = 100
        elif summary_type == 'comprehensive':
            key_points_instruction = "\n- Incluye 3-5 puntos clave" if include_key_points else ""
            prompt = f"Genera un resumen comprensivo del siguiente artículo:{key_points_instruction}\n\n{text[:2000]}"
            max_tokens = 300
        else:  # executive
            key_points_instruction = "\n- Incluye 2-3 puntos clave importantes" if include_key_points else ""
            prompt = f"Genera un resumen ejecutivo del siguiente artículo:{key_points_instruction}\n\n{text[:1800]}"
            max_tokens = 200
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Eres un experto en resumir noticias. Proporciona resúmenes claros, concisos e informativos."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=0.3
        )
        
        summary = response.choices[0].message.content.strip()
        
        # Asegurar que no exceda la longitud máxima
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return {
            'status': 'success',
            'summary': summary,
            'method': 'ai_generated',
            'model_used': settings.OPENAI_MODEL
        }
        
    except Exception as e:
        logger.warning(f"Error en generación AI: {str(e)}")
        raise


def _generate_extractive_summary(text: str, max_length: int, summary_type: str) -> Dict[str, Any]:
    """Generar resumen usando técnicas extractivas (sin AI)"""
    import re
    from collections import Counter
    
    # Dividir en oraciones
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return {
            'status': 'error',
            'error': 'No se pudo procesar el texto'
        }
    
    # Eliminar palabras vacías y calcular frecuencias
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
    
    word_freq = Counter()
    for sentence in sentences:
        words = re.findall(r'\b\w+\b', sentence.lower())
        for word in words:
            if word not in stop_words and len(word) > 2:
                word_freq[word] += 1
    
    # Puntuación de oraciones basada en frecuencia de palabras
    sentence_scores = []
    for i, sentence in enumerate(sentences):
        score = 0
        words = re.findall(r'\b\w+\b', sentence.lower())
        for word in words:
            score += word_freq.get(word, 0)
        
        # Bonificación por posición (primeras oraciones son más importantes)
        position_bonus = max(0, 10 - i)
        sentence_scores.append((score + position_bonus, i, sentence))
    
    # Seleccionar oraciones según el tipo de resumen
    if summary_type == 'brief':
        num_sentences = 1
    elif summary_type == 'comprehensive':
        num_sentences = min(5, len(sentences))
    else:  # executive
        num_sentences = min(3, len(sentences))
    
    # Ordenar por score y seleccionar las mejores
    sentence_scores.sort(reverse=True, key=lambda x: x[0])
    selected_sentences = sentence_scores[:num_sentences]
    
    # Ordenar por posición original para mantener coherencia
    selected_sentences.sort(key=lambda x: x[1])
    summary = '. '.join([s[2] for s in selected_sentences])
    
    # Asegurar que no exceda la longitud máxima
    if len(summary) > max_length:
        # Truncar de manera inteligente
        summary = summary[:max_length-3] + "..."
    
    return {
        'status': 'success',
        'summary': summary,
        'method': 'extractive',
        'sentences_used': len(selected_sentences),
        'key_words': [word for word, count in word_freq.most_common(5)]
    }


@celery_app.task(
    bind=True,
    name='app.tasks.summary_tasks.generate_article_digest',
    queue='ai_summaries',
    rate_limit='10/h'
)
def generate_article_digest(
    self, 
    articles: List[Dict[str, Any]], 
    digest_type: str = 'daily',
    max_articles: int = 20
) -> Dict[str, Any]:
    """
    Generar un digest/resumen consolidado de múltiples artículos
    
    Args:
        articles: Lista de artículos para el digest
        digest_type: Tipo de digest ('hourly', 'daily', 'weekly')
        max_articles: Máximo número de artículos a incluir
        
    Returns:
        Dict con el digest generado
    """
    start_time = time.time()
    
    try:
        logger.info(f"📋 Generando digest {digest_type} de {len(articles)} artículos")
        
        # Seleccionar los artículos más relevantes
        selected_articles = _select_most_relevant_articles(articles, max_articles)
        
        # Generar resúmenes para cada artículo
        individual_summaries = []
        for article in selected_articles:
            summary_result = _generate_single_summary(article, 'executive', 150, True)
            if summary_result['status'] == 'success':
                individual_summaries.append(summary_result)
        
        # Generar digest consolidado
        digest_content = _create_consolidated_digest(individual_summaries, digest_type)
        
        processing_time = time.time() - start_time
        
        return {
            'status': 'success',
            'digest_type': digest_type,
            'digest': digest_content,
            'articles_included': len(individual_summaries),
            'original_article_count': len(articles),
            'processing_time': processing_time,
            'generated_at': time.time(),
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando digest: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time
        }


def _select_most_relevant_articles(articles: List[Dict[str, Any]], max_articles: int) -> List[Dict[str, Any]]:
    """Seleccionar los artículos más relevantes para el digest"""
    import time
    
    # Puntuar artículos por relevancia
    scored_articles = []
    
    for article in articles:
        score = 0
        
        # Bonificación por tener contenido
        if article.get('content'):
            score += 10
        if article.get('description'):
            score += 5
        
        # Bonificación por título informativo
        title = article.get('title', '')
        if len(title) > 20:  # Títulos más informativos
            score += 5
        
        # Bonificación por fuente conocida
        source_name = article.get('source_name', '').lower()
        known_sources = ['bbc', 'reuters', 'cnn', 'guardian', 'nytimes', 'associated press']
        if any(known in source_name for known in known_sources):
            score += 8
        
        # Penalización por antigüedad (artículos más recientes tienen más valor)
        published_at = article.get('published_at')
        if published_at:
            try:
                # Convertir a timestamp si es posible
                if isinstance(published_at, str):
                    pub_time = time.mktime(time.strptime(published_at[:19], "%Y-%m-%dT%H:%M:%S"))
                    age_hours = (time.time() - pub_time) / 3600
                    score += max(0, 10 - age_hours)  # Decrecer score con la edad
            except:
                pass  # Si no se puede parsear la fecha, no penalizar
        
        scored_articles.append((score, article))
    
    # Ordenar por score y seleccionar los mejores
    scored_articles.sort(reverse=True, key=lambda x: x[0])
    selected = [article for score, article in scored_articles[:max_articles]]
    
    return selected


def _create_consolidated_digest(summaries: List[Dict[str, Any]], digest_type: str) -> str:
    """Crear un digest consolidado de los resúmenes individuales"""
    if not summaries:
        return "No hay artículos disponibles para el digest."
    
    # Organizar artículos por tema/tipo
    topics = {}
    for summary in summaries:
        # Simular clasificación por palabras clave en títulos
        title = summary.get('article_title', '').lower()
        
        if any(word in title for word in ['tech', 'digital', 'ai', 'software']):
            topic = 'Tecnología'
        elif any(word in title for word in ['political', 'government', 'election']):
            topic = 'Política'
        elif any(word in title for word in ['economic', 'market', 'business']):
            topic = 'Economía'
        elif any(word in title for word in ['sport', 'game', 'team']):
            topic = 'Deportes'
        else:
            topic = 'General'
        
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(summary)
    
    # Crear el digest
    digest_lines = []
    
    # Header
    if digest_type == 'hourly':
        digest_lines.append("📰 **DIGEST HORARIO**")
    elif digest_type == 'daily':
        digest_lines.append("📰 **RESUMEN DIARIO**")
    else:
        digest_lines.append("📰 **RESUMEN SEMANAL**")
    
    digest_lines.append("")
    digest_lines.append(f"*{len(summaries)} artículos destacados*")
    digest_lines.append("")
    
    # Contenido por temas
    for topic, topic_summaries in topics.items():
        if len(topic_summaries) > 0:
            digest_lines.append(f"## {topic}")
            digest_lines.append("")
            
            for i, summary in enumerate(topic_summaries[:3], 1):  # Max 3 por tema
                digest_lines.append(f"**{i}.** {summary['article_title']}")
                digest_lines.append(f"   {summary['summary']}")
                digest_lines.append("")
    
    # Footer
    digest_lines.append("---")
    digest_lines.append("*Generado automáticamente por AI News Aggregator*")
    
    return '\n'.join(digest_lines)