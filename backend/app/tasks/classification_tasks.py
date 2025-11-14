"""
Tareas de Celery para clasificación asíncrona de temas
Maneja la clasificación temática en lote de artículos
"""

import time
from typing import List, Dict, Any, Optional, Set
from celery import Task
from loguru import logger

from celery_app import celery_app
from app.core.config import settings
from app.services.news_service import NewsClientError


class TopicClassificationTask(Task):
    """Task base para clasificación de temas con retry y manejo de errores"""
    
    autoretry_for = (NewsClientError, Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 60}
    retry_backoff = True
    retry_backoff_max = 700
    retry_jitter = False
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler de falla para logging y monitoreo"""
        logger.error(f"💥 Error en clasificación de temas {task_id}: {exc}")
        logger.debug(f"Detalles del error: {einfo}")


@celery_app.task(
    bind=True,
    name='app.tasks.classification_tasks.classify_topics_batch',
    base=TopicClassificationTask,
    queue='ai_classification',
    rate_limit='8/m'
)
def classify_topics_batch(
    self, 
    articles: List[Dict[str, Any]], 
    classification_system: str = 'comprehensive',
    min_confidence: float = 0.6,
    max_categories_per_article: int = 5
) -> Dict[str, Any]:
    """
    Clasificar temas de múltiples artículos en lotes
    
    Args:
        articles: Lista de artículos a clasificar
        classification_system: Sistema de clasificación ('basic', 'comprehensive', 'custom')
        min_confidence: Confianza mínima para aceptar una clasificación
        max_categories_per_article: Máximo número de categorías por artículo
        
    Returns:
        Dict con resultados de clasificación en lote
    """
    start_time = time.time()
    
    try:
        logger.info(f"🏷️ Iniciando clasificación temática de {len(articles)} artículos")
        
        if not articles:
            return {
                'status': 'empty',
                'message': 'No hay artículos para clasificar',
                'total_processed': 0,
                'processing_time': time.time() - start_time
            }
        
        # Obtener definiciones de categorías
        category_definitions = _get_category_definitions(classification_system)
        
        # Clasificar cada artículo
        classification_results = []
        global_topic_stats = {cat: 0 for cat in category_definitions.keys()}
        
        for article_num, article in enumerate(articles, 1):
            try:
                logger.debug(f"🏷️ Clasificando artículo {article_num}/{len(articles)}")
                
                result = _classify_single_article(
                    article, 
                    category_definitions, 
                    min_confidence, 
                    max_categories_per_article
                )
                
                if result['status'] == 'success':
                    classification_results.append(result)
                    
                    # Actualizar estadísticas globales
                    for category in result['topics']:
                        global_topic_stats[category['name']] += 1
                else:
                    logger.warning(f"⚠️ No se pudo clasificar artículo {article_num}: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"❌ Error clasificando artículo {article_num}: {str(e)}")
                continue
        
        # Calcular métricas de clasificación
        total_articles = len(articles)
        classified_articles = len(classification_results)
        success_rate = (classified_articles / total_articles) * 100 if total_articles > 0 else 0
        
        processing_time = time.time() - start_time
        
        # Preparar estadísticas finales
        final_stats = {
            'total_articles': total_articles,
            'classified_articles': classified_articles,
            'success_rate': success_rate,
            'processing_time': processing_time,
            'avg_time_per_article': processing_time / total_articles if total_articles > 0 else 0,
            'classification_system': classification_system,
            'min_confidence': min_confidence,
            'max_categories_per_article': max_categories_per_article
        }
        
        # Agregar distribución de temas
        topic_distribution = {
            cat: count for cat, count in global_topic_stats.items() if count > 0
        }
        
        result_summary = {
            'status': 'completed',
            'classification_results': classification_results,
            'topic_distribution': topic_distribution,
            'statistics': final_stats,
            'task_id': self.request.id,
            'completed_at': time.time()
        }
        
        logger.info(f"✅ Clasificación completada: {classified_articles}/{total_articles} artículos clasificados ({success_rate:.1f}%)")
        logger.info(f"📊 Distribución de temas: {topic_distribution}")
        
        return result_summary
        
    except Exception as e:
        logger.error(f"❌ Error crítico en clasificación de temas: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'total_articles': len(articles) if articles else 0,
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


def _get_category_definitions(classification_system: str) -> Dict[str, Dict[str, Any]]:
    """
    Obtener definiciones de categorías según el sistema de clasificación
    
    Args:
        classification_system: Tipo de sistema de clasificación
        
    Returns:
        Diccionario con definiciones de categorías
    """
    
    if classification_system == 'basic':
        return {
            'tecnología': {
                'keywords': ['technology', 'tech', 'software', 'digital', 'ai', 'artificial intelligence', 'internet', 'computer', 'cyber'],
                'description': 'Tecnología y sistemas digitales'
            },
            'política': {
                'keywords': ['government', 'political', 'policy', 'election', 'parliament', 'congress', 'democracy', 'vote'],
                'description': 'Política y gobierno'
            },
            'economía': {
                'keywords': ['economic', 'economy', 'market', 'financial', 'business', 'trade', 'finance', 'stock'],
                'description': 'Economía y finanzas'
            },
            'deportes': {
                'keywords': ['sport', 'football', 'basketball', 'soccer', 'tennis', 'olympic', 'game', 'team'],
                'description': 'Deportes y competencias'
            },
            'salud': {
                'keywords': ['health', 'medical', 'hospital', 'disease', 'treatment', 'doctor', 'patient', 'medicine'],
                'description': 'Salud y medicina'
            }
        }
    
    elif classification_system == 'comprehensive':
        return {
            'tecnología': {
                'keywords': ['technology', 'tech', 'software', 'digital', 'ai', 'artificial intelligence', 'internet', 'computer', 'cyber', 'startup', 'innovation'],
                'description': 'Tecnología, innovación digital e IA'
            },
            'política': {
                'keywords': ['government', 'political', 'policy', 'election', 'parliament', 'congress', 'democracy', 'vote', 'politician', 'legislation'],
                'description': 'Política, gobierno y legislación'
            },
            'economía': {
                'keywords': ['economic', 'economy', 'market', 'financial', 'business', 'trade', 'finance', 'stock', 'investment', 'company'],
                'description': 'Economía, negocios y finanzas'
            },
            'deportes': {
                'keywords': ['sport', 'football', 'basketball', 'soccer', 'tennis', 'olympic', 'game', 'team', 'player', 'championship'],
                'description': 'Deportes y actividades físicas'
            },
            'salud': {
                'keywords': ['health', 'medical', 'hospital', 'disease', 'treatment', 'doctor', 'patient', 'medicine', 'clinical', 'research'],
                'description': 'Salud, medicina e investigación médica'
            },
            'ciencia': {
                'keywords': ['science', 'research', 'study', 'discovery', 'scientist', 'laboratory', 'experiment', 'theory'],
                'description': 'Ciencia e investigación'
            },
            'entretenimiento': {
                'keywords': ['entertainment', 'movie', 'music', 'celebrity', 'film', 'show', 'actor', 'artist'],
                'description': 'Entretenimiento y cultura'
            },
            'educación': {
                'keywords': ['education', 'school', 'university', 'student', 'teacher', 'learning', 'academic', 'course'],
                'description': 'Educación y aprendizaje'
            }
        }
    
    else:  # custom - usar sistema comprensivo como base
        return _get_category_definitions('comprehensive')


def _classify_single_article(
    article: Dict[str, Any], 
    category_definitions: Dict[str, Dict[str, Any]],
    min_confidence: float,
    max_categories_per_article: int
) -> Dict[str, Any]:
    """
    Clasificar un solo artículo en las categorías definidas
    
    Args:
        article: Artículo a clasificar
        category_definitions: Definiciones de categorías
        min_confidence: Confianza mínima
        max_categories_per_article: Máximo número de categorías
        
    Returns:
        Dict con resultado de clasificación
    """
    try:
        # Preparar texto para análisis
        title = article.get('title', '')
        description = article.get('description', '')
        content = article.get('content', '')
        
        text = f"{title} {description} {content}".lower()
        
        if not text.strip():
            return {
                'status': 'error',
                'error': 'Artículo sin contenido textual',
                'article_id': article.get('id')
            }
        
        # Calcular scores para cada categoría
        category_scores = {}
        
        for category, definition in category_definitions.items():
            score = _calculate_category_score(text, definition['keywords'])
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return {
                'status': 'no_match',
                'message': 'No se encontraron categorías relevantes',
                'article_id': article.get('id')
            }
        
        # Normalizar scores y convertir a confidencias
        total_score = sum(category_scores.values())
        normalized_scores = {
            cat: score / total_score 
            for cat, score in category_scores.items()
        }
        
        # Filtrar por confianza mínima
        qualified_categories = [
            {'name': cat, 'confidence': conf}
            for cat, conf in normalized_scores.items()
            if conf >= min_confidence
        ]
        
        # Ordenar por confianza y limitar
        qualified_categories.sort(key=lambda x: x['confidence'], reverse=True)
        final_categories = qualified_categories[:max_categories_per_article]
        
        if not final_categories:
            # Si ninguna categoría califica, tomar la de mayor score
            best_category = max(normalized_scores.items(), key=lambda x: x[1])
            final_categories = [{'name': best_category[0], 'confidence': best_category[1]}]
        
        # Preparar resultado
        result = {
            'status': 'success',
            'article_id': article.get('id'),
            'article_title': title[:100] + '...' if len(title) > 100 else title,
            'topics': final_categories,
            'primary_topic': final_categories[0]['name'] if final_categories else None,
            'confidence_score': final_categories[0]['confidence'] if final_categories else 0,
            'total_categories_found': len(category_scores),
            'analysis_metadata': {
                'method': 'keyword_based',
                'classification_system': list(category_definitions.keys()),
                'text_length': len(text),
                'keywords_matched': sum(1 for scores in category_scores.values() for _ in [scores])
            }
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error clasificando artículo: {str(e)}")
        return {
            'status': 'error',
            'error': str(e),
            'article_id': article.get('id')
        }


def _calculate_category_score(text: str, keywords: List[str]) -> float:
    """
    Calcular score de relevancia para una categoría
    
    Args:
        text: Texto a analizar
        keywords: Palabras clave de la categoría
        
    Returns:
        Score de relevancia (float)
    """
    score = 0.0
    words = text.split()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        
        # Buscar coincidencia exacta de palabra
        exact_matches = words.count(keyword_lower)
        score += exact_matches * 2.0  # Peso mayor para coincidencia exacta
        
        # Buscar coincidencia parcial
        partial_matches = sum(1 for word in words if keyword_lower in word)
        score += partial_matches * 0.5  # Peso menor para coincidencia parcial
        
        # Bonificación por título (apalabras en el título tienen más peso)
        if keyword_lower in text[:200]:  # Primeros 200 caracteres (generalmente título)
            score += 1.0
    
    return score


@celery_app.task(
    bind=True,
    name='app.tasks.classification_tasks.update_classification_model',
    queue='ai_classification',
    rate_limit='1/h'
)
def update_classification_model(self, new_categories: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Actualizar el modelo de clasificación con nuevas categorías o keywords
    
    Args:
        new_categories: Nuevas categorías a agregar o actualizar
        
    Returns:
        Dict con información de la actualización
    """
    start_time = time.time()
    
    try:
        logger.info("🔄 Actualizando modelo de clasificación de temas")
        
        # TODO: Implementar lógica para persistir nuevas categorías
        # Esta implementación placeholder debería guardar en BD o archivo de configuración
        
        current_categories = _get_category_definitions('comprehensive')
        
        if new_categories:
            # Agregar o actualizar categorías
            current_categories.update(new_categories)
            logger.info(f"✅ Actualizadas {len(new_categories)} categorías")
        
        # Validar categorías
        validation_results = _validate_categories(current_categories)
        
        return {
            'status': 'success',
            'total_categories': len(current_categories),
            'categories': list(current_categories.keys()),
            'validation_results': validation_results,
            'processing_time': time.time() - start_time,
            'updated_at': time.time()
        }
        
    except Exception as e:
        logger.error(f"❌ Error actualizando modelo de clasificación: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time
        }


def _validate_categories(categories: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Validar la consistencia de las categorías definidas"""
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': []
    }
    
    for category_name, category_def in categories.items():
        # Validar que tenga keywords
        if 'keywords' not in category_def:
            validation_results['errors'].append(f"Categoría '{category_name}'缺少关键词")
            validation_results['valid'] = False
        
        # Validar que tenga description
        if 'description' not in category_def:
            validation_results['warnings'].append(f"Categoría '{category_name}'缺少描述")
        
        # Validar keywords
        if 'keywords' in category_def:
            keywords = category_def['keywords']
            if not isinstance(keywords, list) or not keywords:
                validation_results['errors'].append(f"Categoría '{category_name}'的关键词格式不正确")
                validation_results['valid'] = False
    
    return validation_results