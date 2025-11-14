"""
Tareas de Celery para análisis asíncrono de artículos
Maneja el análisis individual de artículos usando OpenAI
"""

import asyncio
from typing import Dict, Any, Optional
from celery import Task
from loguru import logger

from celery_app import celery_app
from app.core.config import settings
from app.services.news_service import NewsClientError


class ArticleAnalysisTask(Task):
    """Task base para análisis de artículos con retry y manejo de errores"""
    
    autoretry_for = (NewsClientError, Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler de falla para logging y monitoreo"""
        logger.error(f"💥 Error en análisis de artículo {task_id}: {exc}")
        logger.debug(f"Detalles del error: {einfo}")


@celery_app.task(
    bind=True,
    name='app.tasks.article_tasks.analyze_article_async',
    base=ArticleAnalysisTask,
    queue='ai_analysis',
    rate_limit='10/m'
)
def analyze_article_async(self, article_data: Dict[str, Any], analysis_type: str = 'comprehensive') -> Dict[str, Any]:
    """
    Analizar un artículo de forma asíncrona usando OpenAI
    
    Args:
        article_data: Datos del artículo a analizar
        analysis_type: Tipo de análisis ('basic', 'comprehensive', 'sentiment')
        
    Returns:
        Dict con resultados del análisis
        
    Raises:
        NewsClientError: Si hay problemas con la API de OpenAI
    """
    import time
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Iniciando análisis {analysis_type} del artículo: {article_data.get('title', 'Sin título')[:50]}...")
        
        # Validar datos del artículo
        if not article_data.get('content') and not article_data.get('description'):
            raise ValueError("El artículo debe tener contenido o descripción para analizar")
        
        # Preparar el texto a analizar
        text_to_analyze = f"""
        Título: {article_data.get('title', '')}
        Descripción: {article_data.get('description', '')}
        Contenido: {article_data.get('content', '')[:2000]}...
        Fuente: {article_data.get('source_name', '')}
        """
        
        # Realizar el análisis según el tipo
        if analysis_type == 'basic':
            analysis_result = _perform_basic_analysis(text_to_analyze)
        elif analysis_type == 'sentiment':
            analysis_result = _perform_sentiment_analysis(text_to_analyze)
        else:  # comprehensive
            analysis_result = _perform_comprehensive_analysis(text_to_analyze)
        
        # Agregar metadata al resultado
        analysis_result.update({
            'article_id': article_data.get('id'),
            'article_url': article_data.get('url'),
            'analysis_type': analysis_type,
            'analysis_timestamp': time.time(),
            'processing_time': time.time() - start_time,
            'task_id': self.request.id,
            'status': 'completed'
        })
        
        logger.info(f"✅ Análisis {analysis_type} completado en {analysis_result['processing_time']:.2f}s")
        return analysis_result
        
    except Exception as e:
        logger.error(f"❌ Error en análisis de artículo: {str(e)}")
        
        # Retornar resultado de error para evitar que la tarea falle completamente
        return {
            'status': 'error',
            'error_message': str(e),
            'article_id': article_data.get('id'),
            'analysis_type': analysis_type,
            'analysis_timestamp': time.time(),
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


def _perform_basic_analysis(text: str) -> Dict[str, Any]:
    """Realizar análisis básico del texto"""
    try:
        if not settings.OPENAI_API_KEY:
            return _fallback_basic_analysis(text)
        
        import openai
        
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Analiza el siguiente artículo y proporciona un resumen básico y clasificación temática:
        
        {text[:1500]}
        
        Responde en formato JSON con:
        - summary: Resumen en 2-3 líneas
        - topics: Lista de 2-4 temas principales
        - category: Categoría principal (tecnología, política, deportes, etc.)
        - urgency: Nivel de urgencia (baja, media, alta)
        - language: idioma detectado
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Eres un experto analista de noticias. Responde siempre en formato JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        import json
        return json.loads(result_text)
        
    except Exception as e:
        logger.warning(f"Error en OpenAI basic analysis: {str(e)}")
        return _fallback_basic_analysis(text)


def _perform_comprehensive_analysis(text: str) -> Dict[str, Any]:
    """Realizar análisis comprensivo del texto"""
    try:
        if not settings.OPENAI_API_KEY:
            return _fallback_comprehensive_analysis(text)
        
        import openai
        
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Realiza un análisis comprensivo del siguiente artículo:
        
        {text[:2000]}
        
        Responde en formato JSON con:
        - summary: Resumen ejecutivo de 3-4 líneas
        - key_points: Lista de 5-7 puntos clave
        - topics: Lista de temas principales (mínimo 3)
        - category: Categoría principal
        - subcategories: Lista de subcategorías
        - sentiment: Análisis de sentimiento (positivo, negativo, neutral)
        - urgency: Nivel de urgencia (baja, media, alta)
        - impact_level: Nivel de impacto (local, nacional, internacional)
        - entities: Lista de entidades mencionadas (personas, organizaciones, lugares)
        - language: idioma detectado
        - reading_time_minutes: tiempo estimado de lectura
        - credibility_score: puntuación de credibilidad (1-10)
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Eres un analista profesional de noticias. Responde siempre en formato JSON válido y preciso."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=800,
            temperature=0.2
        )
        
        result_text = response.choices[0].message.content
        import json
        return json.loads(result_text)
        
    except Exception as e:
        logger.warning(f"Error en OpenAI comprehensive analysis: {str(e)}")
        return _fallback_comprehensive_analysis(text)


def _perform_sentiment_analysis(text: str) -> Dict[str, Any]:
    """Realizar análisis de sentimiento específico"""
    try:
        if not settings.OPENAI_API_KEY:
            return _fallback_sentiment_analysis(text)
        
        import openai
        
        openai.api_key = settings.OPENAI_API_KEY
        
        prompt = f"""
        Realiza un análisis detallado de sentimiento del siguiente artículo:
        
        {text[:1500]}
        
        Responde en formato JSON con:
        - overall_sentiment: sentimiento general (positivo, negativo, neutral)
        - sentiment_score: puntuación de -1 a 1
        - emotional_tone: tono emocional principal
        - emotional_intensity: intensidad emocional (baja, media, alta)
        - tone_description: descripción textual del tono
        - key_emotions: lista de emociones detectadas
        - confidence_level: nivel de confianza del análisis (0-100)
        - language: idioma detectado
        """
        
        response = openai.ChatCompletion.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "Eres un experto en análisis de sentimiento y emociones en textos. Responde siempre en formato JSON válido."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.3
        )
        
        result_text = response.choices[0].message.content
        import json
        return json.loads(result_text)
        
    except Exception as e:
        logger.warning(f"Error en OpenAI sentiment analysis: {str(e)}")
        return _fallback_sentiment_analysis(text)


# Funciones de fallback cuando OpenAI no está disponible
def _fallback_basic_analysis(text: str) -> Dict[str, Any]:
    """Análisis básico de fallback usando técnicas tradicionales"""
    import re
    from collections import Counter
    
    # Análisis básico por palabras clave
    words = re.findall(r'\b\w+\b', text.lower())
    word_freq = Counter(words)
    
    # Palabras clave comunes por categoría
    categories = {
        'tecnología': ['technology', 'tech', 'software', 'digital', 'ai', 'artificial intelligence', 'internet'],
        'política': ['government', 'political', 'policy', 'election', 'parliament', 'congress'],
        'economía': ['economic', 'economy', 'market', 'financial', 'business', 'trade'],
        'deportes': ['sport', 'football', 'basketball', 'soccer', 'tennis', 'olympic'],
        'salud': ['health', 'medical', 'hospital', 'disease', 'treatment', 'doctor']
    }
    
    scores = {}
    for category, keywords in categories.items():
        score = sum(word_freq.get(keyword, 0) for keyword in keywords)
        if score > 0:
            scores[category] = score
    
    main_category = max(scores, key=scores.get) if scores else 'general'
    
    # Extracción de puntos clave (primeras oraciones)
    sentences = re.split(r'[.!?]+', text)
    key_points = [s.strip() for s in sentences[:3] if len(s.strip()) > 20]
    
    return {
        'summary': text[:200] + '...' if len(text) > 200 else text,
        'topics': list(scores.keys())[:4],
        'category': main_category,
        'urgency': 'media',
        'language': 'es',
        'analysis_method': 'fallback'
    }


def _fallback_comprehensive_analysis(text: str) -> Dict[str, Any]:
    """Análisis comprensivo de fallback"""
    basic_result = _fallback_basic_analysis(text)
    
    return {
        **basic_result,
        'key_points': basic_result.get('topics', [])[:5],
        'subcategories': [],
        'sentiment': 'neutral',
        'impact_level': 'local',
        'entities': [],
        'reading_time_minutes': max(1, len(text) // 200),
        'credibility_score': 7,
        'analysis_method': 'fallback_comprehensive'
    }


def _fallback_sentiment_analysis(text: str) -> Dict[str, Any]:
    """Análisis de sentimiento de fallback"""
    positive_words = ['good', 'great', 'excellent', 'positive', 'success', 'win', 'achieve']
    negative_words = ['bad', 'terrible', 'negative', 'fail', 'loss', 'crisis', 'problem']
    
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
        'tone_description': f'Tono {sentiment} detectado',
        'key_emotions': [sentiment],
        'confidence_level': 70,
        'language': 'es',
        'analysis_method': 'fallback_sentiment'
    }