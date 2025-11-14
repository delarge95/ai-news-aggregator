"""
Analysis Factory - Genera datos de análisis IA de prueba para testing
"""

import uuid
import random
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from factory import SubFactory, Sequence, LazyFunction, Trait
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText, FuzzyFloat, FuzzyInteger, FuzzyJSON

from app.db.models import ArticleAnalysis, AnalysisTask, ProcessingStatus, AnalysisTaskStatus


class ArticleAnalysisFactory(SQLAlchemyModelFactory):
    """Factory para generar análisis de artículos de prueba"""
    
    class Meta:
        model = ArticleAnalysis
        sqlalchemy_session_persistence = "flush"
    
    # Campos obligatorios
    id = LazyFunction(uuid.uuid4)
    article = SubFactory('tests.factories.article_factory.ArticleFactory')
    article_id = None  # Establecido automáticamente
    
    analysis_type = FuzzyChoice(['summary', 'sentiment', 'bias', 'topics', 'relevance', 'entities'])
    analysis_data = LazyFunction(lambda: generate_analysis_data_for_type('summary'))
    
    # Campos de AI
    model_used = FuzzyChoice([
        'gpt-3.5-turbo',
        'gpt-4',
        'text-davinci-003',
        'bert-base-uncased',
        'roberta-base',
        'custom-sentiment-model-v1'
    ])
    
    confidence_score = FuzzyFloat(low=0.6, high=0.99)
    processed_at = LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 120)))
    
    # Tratos para diferentes tipos de análisis
    class Params:
        # Análisis de resumen
        summary = Trait(
            analysis_type='summary',
            analysis_data=LazyFunction(lambda: generate_analysis_data_for_type('summary'))
        )
        
        # Análisis de sentimiento
        sentiment = Trait(
            analysis_type='sentiment',
            analysis_data=LazyFunction(lambda: generate_analysis_data_for_type('sentiment'))
        )
        
        # Análisis de sesgo
        bias = Trait(
            analysis_type='bias',
            analysis_data=LazyFunction(lambda: generate_analysis_data_for_type('bias'))
        )
        
        # Análisis de temas
        topics = Trait(
            analysis_type='topics',
            analysis_data=LazyFunction(lambda: generate_analysis_data_for_type('topics'))
        )
        
        # Análisis de relevancia
        relevance = Trait(
            analysis_type='relevance',
            analysis_data=LazyFunction(lambda: generate_analysis_data_for_type('relevance'))
        )
        
        # Análisis de entidades
        entities = Trait(
            analysis_type='entities',
            analysis_data=LazyFunction(lambda: generate_analysis_data_for_type('entities'))
        )
        
        # Análisis de alta confianza
        high_confidence = Trait(
            confidence_score=FuzzyFloat(low=0.9, high=0.99)
        )
        
        # Análisis de baja confianza
        low_confidence = Trait(
            confidence_score=FuzzyFloat(low=0.5, high=0.7)
        )
        
        # Análisis reciente
        recent = Trait(
            processed_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 30)))
        )
        
        # Análisis antiguo
        old = Trait(
            processed_at=LazyFunction(lambda: datetime.utcnow() - timedelta(hours=random.randint(1, 72)))
        )


class AnalysisTaskFactory(SQLAlchemyModelFactory):
    """Factory para generar tareas de análisis de prueba"""
    
    class Meta:
        model = AnalysisTask
        sqlalchemy_session_persistence = "flush"
    
    # Campos obligatorios
    id = LazyFunction(uuid.uuid4)
    task_type = FuzzyChoice(['sentiment', 'summary', 'topics', 'relevance', 'bias', 'entities', 'full_analysis'])
    task_name = LazyFunction(lambda: generate_task_name())
    
    # Campos opcionales
    article = SubFactory('tests.factories.article_factory.ArticleFactory')
    article_id = None  # Establecido automáticamente
    
    source_article_url = LazyFunction(lambda: f"https://example.com/article/{uuid.uuid4()}")
    
    # Estados de la tarea
    status = FuzzyChoice([
        AnalysisTaskStatus.PENDING,
        AnalysisTaskStatus.RUNNING,
        AnalysisTaskStatus.COMPLETED,
        AnalysisTaskStatus.FAILED,
        AnalysisTaskStatus.CANCELLED
    ])
    
    priority = FuzzyInteger(low=1, high=10)
    retry_count = FuzzyInteger(low=0, high=3)
    max_retries = 3
    
    # Información del modelo AI
    model_name = FuzzyChoice(['gpt-3.5-turbo', 'gpt-4', 'bert-base-uncased', 'custom-model'])
    model_version = FuzzyChoice(['v1.0', 'v1.1', 'v2.0', 'latest'])
    
    # Datos de entrada y salida
    input_data = LazyFunction(lambda: generate_input_data())
    output_data = None  # Solo si la tarea está completada
    
    # Tiempos
    scheduled_at = LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 60)))
    started_at = None  # Solo si la tarea ha comenzado
    completed_at = None  # Solo si la tarea está completada
    processing_duration_ms = None  # Solo si la tarea está completada
    
    # Manejo de errores
    error_message = None  # Solo si hay error
    error_code = None  # Solo si hay error
    stack_trace = None  # Solo si hay error
    
    # Metadata
    worker_id = LazyFunction(lambda: f"worker_{random.randint(1, 5)}")
    task_metadata = LazyFunction(lambda: generate_task_metadata())
    
    # Tratos para diferentes estados de tareas
    class Params:
        # Tarea pendiente
        pending = Trait(
            status=AnalysisTaskStatus.PENDING,
            started_at=None,
            completed_at=None,
            output_data=None,
            processing_duration_ms=None
        )
        
        # Tarea en ejecución
        running = Trait(
            status=AnalysisTaskStatus.RUNNING,
            started_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 10))),
            completed_at=None,
            output_data=None,
            processing_duration_ms=None
        )
        
        # Tarea completada exitosamente
        completed = Trait(
            status=AnalysisTaskStatus.COMPLETED,
            started_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(5, 30))),
            completed_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 20))),
            output_data=LazyFunction(lambda: generate_output_data()),
            processing_duration_ms=FuzzyInteger(low=1000, high=30000)
        )
        
        # Tarea con error
        failed = Trait(
            status=AnalysisTaskStatus.FAILED,
            started_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 10))),
            completed_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 5))),
            output_data=None,
            processing_duration_ms=FuzzyInteger(low=500, high=5000),
            error_message=LazyFunction(lambda: generate_error_message()),
            error_code=FuzzyChoice(['TIMEOUT', 'MODEL_ERROR', 'API_RATE_LIMIT', 'INVALID_INPUT'])
        )
        
        # Tarea cancelada
        cancelled = Trait(
            status=AnalysisTaskStatus.CANCELLED,
            started_at=None,
            completed_at=None,
            output_data=None,
            error_message="Tarea cancelada por el usuario"
        )
        
        # Tarea de alta prioridad
        high_priority = Trait(
            priority=FuzzyInteger(low=1, high=3)
        )
        
        # Tarea de baja prioridad
        low_priority = Trait(
            priority=FuzzyInteger(low=8, high=10)
        )
        
        # Tarea con reintentos
        with_retries = Trait(
            retry_count=FuzzyInteger(low=1, high=3)
        )
        
        # Tarea de análisis completo
        full_analysis = Trait(
            task_type='full_analysis',
            task_name='Análisis completo del artículo',
            model_name='gpt-4',
            input_data=LazyFunction(lambda: generate_input_data_for_full_analysis())
        )


# Funciones auxiliares para generar datos de análisis

def generate_analysis_data_for_type(analysis_type: str) -> Dict[str, Any]:
    """Genera datos de análisis específicos por tipo"""
    
    data_generators = {
        'summary': lambda: {
            'summary_text': generate_summary_text(),
            'key_points': generate_key_points(),
            'word_count': random.randint(100, 500),
            'readability_score': random.uniform(0.6, 0.9),
            'language': 'es'
        },
        
        'sentiment': lambda: {
            'sentiment_label': random.choice(['positive', 'negative', 'neutral']),
            'sentiment_score': random.uniform(-1.0, 1.0),
            'confidence': random.uniform(0.6, 0.95),
            'emotions': generate_emotions(),
            'subjectivity': random.uniform(0.3, 0.8)
        },
        
        'bias': lambda: {
            'bias_score': random.uniform(0.0, 1.0),
            'bias_direction': random.choice(['left', 'center', 'right']),
            'political_leaning': random.uniform(-1.0, 1.0),
            'confidence': random.uniform(0.5, 0.9),
            'bias_indicators': generate_bias_indicators()
        },
        
        'topics': lambda: {
            'topics': generate_topics(),
            'topic_distribution': generate_topic_distribution(),
            'primary_topic': generate_primary_topic(),
            'topic_confidence': random.uniform(0.6, 0.95)
        },
        
        'relevance': lambda: {
            'relevance_score': random.uniform(0.0, 1.0),
            'relevance_factors': generate_relevance_factors(),
            'importance_level': random.choice(['low', 'medium', 'high', 'critical']),
            ' timeliness': random.uniform(0.5, 1.0)
        },
        
        'entities': lambda: {
            'persons': generate_persons(),
            'organizations': generate_organizations(),
            'locations': generate_locations(),
            'events': generate_events(),
            'entities_count': random.randint(5, 25)
        }
    }
    
    generator = data_generators.get(analysis_type, lambda: {})
    return generator()


def generate_summary_text() -> str:
    """Genera texto de resumen"""
    summaries = [
        "Las autoridades han anunciado nuevas medidas que prometen cambiar el panorama actual.",
        "Un estudio reciente revela información importante sobre el tema en debate.",
        "El evento más esperado del año finalmente ha llegado con gran expectativa.",
        "Los expertos señalan que estos cambios podrían tener impacto significativo.",
        "La decisión inesperada promete generar reacciones divididas entre los ciudadanos.",
        "Los organizadores han trabajado incansablemente para asegurar el éxito del evento."
    ]
    return random.choice(summaries)


def generate_key_points() -> List[str]:
    """Genera puntos clave"""
    all_points = [
        "Nuevas medidas implementadas por las autoridades",
        "Estudio revela información importante",
        "Evento histórico genera gran expectativa",
        "Cambios podrían tener impacto significativo",
        "Decisión inesperada genera reacciones divididas",
        "Organizadores trabajan para asegurar el éxito",
        "Expertos proporcionan nueva perspectiva",
        "Implicaciones de largo alcance esperadas"
    ]
    
    num_points = random.randint(2, 4)
    return random.sample(all_points, num_points)


def generate_emotions() -> Dict[str, float]:
    """Genera análisis emocional"""
    emotions = ['joy', 'anger', 'sadness', 'fear', 'surprise', 'trust', 'anticipation']
    return {emotion: random.uniform(0.1, 0.8) for emotion in random.sample(emotions, 4)}


def generate_bias_indicators() -> List[Dict[str, Any]]:
    """Genera indicadores de sesgo"""
    indicators = [
        {'type': 'loaded_language', 'confidence': random.uniform(0.3, 0.8)},
        {'type': 'source_citation', 'confidence': random.uniform(0.6, 0.9)},
        {'type': 'word_choice', 'confidence': random.uniform(0.4, 0.7)},
        {'type': 'framing', 'confidence': random.uniform(0.5, 0.8)}
    ]
    return random.sample(indicators, random.randint(1, 3))


def generate_topics() -> List[str]:
    """Genera lista de temas"""
    all_topics = [
        'technology', 'politics', 'health', 'economy', 'sports',
        'entertainment', 'science', 'international', 'environment', 'social'
    ]
    return random.sample(all_topics, random.randint(2, 5))


def generate_topic_distribution() -> Dict[str, float]:
    """Genera distribución de temas"""
    topics = generate_topics()
    distribution = {}
    remaining = 1.0
    
    for i, topic in enumerate(topics):
        if i == len(topics) - 1:
            distribution[topic] = remaining
        else:
            weight = random.uniform(0.1, remaining / 2)
            distribution[topic] = weight
            remaining -= weight
    
    return distribution


def generate_primary_topic() -> str:
    """Genera tema principal"""
    topics = ['technology', 'politics', 'health', 'economy', 'sports', 'science']
    return random.choice(topics)


def generate_relevance_factors() -> List[str]:
    """Genera factores de relevancia"""
    factors = [
        'timeliness', 'importance', 'credibility', 'novelty', 'impact',
        'public_interest', 'factual_accuracy', 'source_authority'
    ]
    return random.sample(factors, random.randint(2, 4))


def generate_persons() -> List[str]:
    """Genera lista de personas"""
    persons = [
        'Juan Pérez', 'María García', 'Carlos López', 'Ana Martín',
        'David Smith', 'Sarah Johnson', 'Michael Brown', 'Emma Davis',
        'Presidente García', 'Ministro López', 'Dr. Smith', 'Prof. Johnson'
    ]
    return random.sample(persons, random.randint(2, 6))


def generate_organizations() -> List[str]:
    """Genera lista de organizaciones"""
    orgs = [
        'Gobierno Central', 'Universidad Nacional', 'Hospital General',
        'TechCorp Inc.', 'Global Solutions', 'European Union',
        'World Health Organization', 'NASA', 'European Central Bank'
    ]
    return random.sample(orgs, random.randint(2, 5))


def generate_locations() -> List[str]:
    """Genera lista de ubicaciones"""
    locations = [
        'Madrid', 'Barcelona', 'Valencia', 'Sevilla',
        'Nueva York', 'Londres', 'París', 'Berlín',
        'España', 'Estados Unidos', 'Francia', 'Alemania'
    ]
    return random.sample(locations, random.randint(2, 5))


def generate_events() -> List[str]:
    """Genera lista de eventos"""
    events = [
        'Conferencia Anual', 'Elecciones 2024', 'Lanzamiento de Producto',
        'Cumbre Internacional', 'Festival Cultural', 'Maratón de Madrid',
        'Crisis Económica', 'Reforma Legislativa'
    ]
    return random.sample(events, random.randint(1, 3))


def generate_task_name() -> str:
    """Genera nombre descriptivo para la tarea"""
    task_names = [
        'Análisis de sentimiento',
        'Generación de resumen',
        'Extracción de temas',
        'Evaluación de relevancia',
        'Detección de sesgo',
        'Reconocimiento de entidades',
        'Análisis completo de IA'
    ]
    return random.choice(task_names)


def generate_input_data() -> Dict[str, Any]:
    """Genera datos de entrada para la tarea"""
    return {
        'article_id': str(uuid.uuid4()),
        'text': 'Texto del artículo para analizar...',
        'options': {
            'language': 'es',
            'model_version': 'v1.0',
            'confidence_threshold': 0.7
        },
        'timestamp': datetime.utcnow().isoformat()
    }


def generate_input_data_for_full_analysis() -> Dict[str, Any]:
    """Genera datos de entrada para análisis completo"""
    return {
        'article_id': str(uuid.uuid4()),
        'text': 'Texto del artículo para análisis completo...',
        'analysis_types': ['sentiment', 'summary', 'topics', 'relevance'],
        'options': {
            'language': 'es',
            'model_version': 'v2.0',
            'confidence_threshold': 0.6,
            'include_entities': True,
            'include_bias_analysis': True
        },
        'timestamp': datetime.utcnow().isoformat()
    }


def generate_output_data() -> Dict[str, Any]:
    """Genera datos de salida para tarea completada"""
    return {
        'analysis_results': {
            'sentiment': generate_analysis_data_for_type('sentiment'),
            'summary': generate_analysis_data_for_type('summary'),
            'topics': generate_analysis_data_for_type('topics')
        },
        'processing_time_ms': random.randint(1000, 10000),
        'model_version': 'v1.0',
        'confidence_average': random.uniform(0.7, 0.95)
    }


def generate_error_message() -> str:
    """Genera mensaje de error realista"""
    error_messages = [
        'Timeout al procesar la solicitud',
        'Modelo AI no disponible temporalmente',
        'Límite de rate limit excedido',
        'Datos de entrada inválidos',
        'Error de conexión con el servicio AI',
        'Memoria insuficiente para procesar la solicitud',
        'Formato de respuesta inesperado del modelo'
    ]
    return random.choice(error_messages)


def generate_task_metadata() -> Dict[str, Any]:
    """Genera metadata de la tarea"""
    return {
        'processing_node': random.choice(['node-1', 'node-2', 'node-3']),
        'cpu_usage': random.uniform(0.1, 0.8),
        'memory_usage': random.uniform(0.2, 0.9),
        'queue_position': random.randint(0, 50),
        'estimated_completion': (datetime.utcnow() + timedelta(minutes=random.randint(1, 30))).isoformat()
    }


# Factory para conjuntos de análisis
class AnalysisSetFactory:
    """Factory para crear conjuntos de análisis relacionados"""
    
    @staticmethod
    def create_complete_article_analysis(article, include_failed: bool = False) -> List[ArticleAnalysis]:
        """Crea análisis completo para un artículo"""
        
        analysis_types = ['summary', 'sentiment', 'bias', 'topics', 'relevance', 'entities']
        analyses = []
        
        for analysis_type in analysis_types:
            analysis = ArticleAnalysisFactory(
                article=article,
                analysis_type=analysis_type
            )
            analyses.append(analysis)
        
        # Opcionalmente, crear uno fallido
        if include_failed:
            failed_analysis = ArticleAnalysisFactory(
                article=article,
                analysis_type='sentiment',
                status=AnalysisTaskStatus.FAILED,
                error_message="Modelo AI no disponible"
            )
            analyses.append(failed_analysis)
        
        return analyses


class TaskSetFactory:
    """Factory para crear conjuntos de tareas de análisis"""
    
    @staticmethod
    def create_analysis_queue(
        total_tasks: int = 20,
        pending_ratio: float = 0.4,
        running_ratio: float = 0.2,
        completed_ratio: float = 0.3,
        failed_ratio: float = 0.1
    ) -> List[AnalysisTask]:
        """Crea una cola de análisis realista"""
        
        tasks = []
        
        # Calcular distribución
        pending_count = int(total_tasks * pending_ratio)
        running_count = int(total_tasks * running_ratio)
        completed_count = int(total_tasks * completed_ratio)
        failed_count = total_tasks - pending_count - running_count - completed_count
        
        # Tareas pendientes
        for _ in range(pending_count):
            task = AnalysisTaskFactory(status=AnalysisTaskStatus.PENDING)
            tasks.append(task)
        
        # Tareas en ejecución
        for _ in range(running_count):
            task = AnalysisTaskFactory(status=AnalysisTaskStatus.RUNNING)
            tasks.append(task)
        
        # Tareas completadas
        for _ in range(completed_count):
            task = AnalysisTaskFactory(status=AnalysisTaskStatus.COMPLETED)
            tasks.append(task)
        
        # Tareas fallidas
        for _ in range(failed_count):
            task = AnalysisTaskFactory(status=AnalysisTaskStatus.FAILED)
            tasks.append(task)
        
        return tasks