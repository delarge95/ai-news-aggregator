"""
Article Factory - Genera artículos de prueba para testing
"""

import uuid
import random
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from factory import SubFactory, Sequence, LazyFunction, Trait
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText, FuzzyFloat

from app.db.models import Article, Source, ProcessingStatus


class ArticleFactory(SQLAlchemyModelFactory):
    """Factory para generar artículos de prueba"""
    
    class Meta:
        model = Article
        sqlalchemy_session_persistence = "flush"  # Flush to DB but don't commit
    
    # Campos obligatorios
    id = LazyFunction(uuid.uuid4)
    title = FuzzyText(length=50, suffix=" - Noticia de Prueba")
    content = LazyFunction(lambda: generate_sample_content())
    url = LazyFunction(lambda: f"https://example.com/article/{uuid.uuid4()}")
    
    # Campos de Source (requerido)
    source = SubFactory('tests.factories.source_factory.SourceFactory')
    source_id = None  # Será establecido automáticamente por la relación
    
    # Campos de fecha
    published_at = LazyFunction(
        lambda: datetime.utcnow() - timedelta(
            hours=random.randint(0, 72),
            minutes=random.randint(0, 59)
        )
    )
    
    # Campos de duplicado detection
    duplicate_group_id = None  # None significa que no es duplicado
    content_hash = LazyFunction(lambda: hashlib.sha256(
        generate_sample_content().encode()
    ).hexdigest())
    
    # Campos de AI Analysis (algunos con valores por defecto)
    sentiment_score = FuzzyFloat(low=-1.0, high=1.0)
    sentiment_label = FuzzyChoice(['positive', 'negative', 'neutral'])
    bias_score = FuzzyFloat(low=0.0, high=1.0)
    relevance_score = FuzzyFloat(low=0.0, high=1.0)
    summary = LazyFunction(lambda: generate_summary())
    topic_tags = LazyFunction(lambda: generate_topic_tags())
    
    # Campos de procesamiento
    processed_at = LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 60)))
    ai_processed_at = LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 30)))
    processing_status = FuzzyChoice([ProcessingStatus.COMPLETED, ProcessingStatus.PROCESSING, ProcessingStatus.PENDING])
    
    # Tratos para diferentes tipos de artículos
    class Params:
        # Artículo procesado completamente
        processed = Trait(
            processing_status=ProcessingStatus.COMPLETED,
            processed_at=datetime.utcnow() - timedelta(hours=1),
            ai_processed_at=datetime.utcnow() - timedelta(minutes=30),
            sentiment_score=FuzzyFloat(low=-1.0, high=1.0),
            sentiment_label=FuzzyChoice(['positive', 'negative', 'neutral']),
            bias_score=FuzzyFloat(low=0.0, high=1.0),
            relevance_score=FuzzyFloat(low=0.0, high=1.0),
            summary=LazyFunction(lambda: generate_summary())
        )
        
        # Artículo sin procesar
        unprocessed = Trait(
            processing_status=ProcessingStatus.PENDING,
            processed_at=None,
            ai_processed_at=None,
            sentiment_score=None,
            sentiment_label=None,
            bias_score=None,
            relevance_score=0.0,
            summary=None
        )
        
        # Artículo con error en procesamiento
        failed = Trait(
            processing_status=ProcessingStatus.FAILED,
            processed_at=datetime.utcnow() - timedelta(hours=1),
            ai_processed_at=None
        )
        
        # Artículo sobre tecnología
        tech_related = Trait(
            topic_tags=[{"tag": "technology", "confidence": 0.9}, {"tag": "AI", "confidence": 0.8}]
        )
        
        # Artículo político
        politics_related = Trait(
            topic_tags=[{"tag": "politics", "confidence": 0.9}, {"tag": "government", "confidence": 0.7}]
        )
        
        # Artículo de salud
        health_related = Trait(
            topic_tags=[{"tag": "health", "confidence": 0.9}, {"tag": "medicine", "confidence": 0.8}]
        )
        
        # Artículo muy reciente (últimas 2 horas)
        recent = Trait(
            published_at=LazyFunction(lambda: datetime.utcnow() - timedelta(hours=random.randint(0, 120)))
        )
        
        # Artículo antiguo (más de 7 días)
        old = Trait(
            published_at=LazyFunction(lambda: datetime.utcnow() - timedelta(days=random.randint(8, 365)))
        )
        
        # Artículo con sentimiento positivo
        positive_sentiment = Trait(
            sentiment_score=FuzzyFloat(low=0.1, high=1.0),
            sentiment_label='positive'
        )
        
        # Artículo con sentimiento negativo
        negative_sentiment = Trait(
            sentiment_score=FuzzyFloat(low=-1.0, high=-0.1),
            sentiment_label='negative'
        )
        
        # Artículo con sentimiento neutral
        neutral_sentiment = Trait(
            sentiment_score=FuzzyFloat(low=-0.1, high=0.1),
            sentiment_label='neutral'
        )


def generate_sample_content() -> str:
    """Genera contenido de muestra realista para artículos"""
    content_templates = [
        """
        En una decisión inesperada, las autoridades han anunciado nuevas medidas 
        que prometen cambiar el panorama actual. Los expertos señalan que estos 
        cambios podrían tener un impacto significativo en el futuro próximo.
        
        Según fuentes oficiales, la implementación comenzará el próximo mes y 
        abarcará múltiples sectores. La medida ha generado reacciones divididas 
        entre los ciudadanos, algunos de quienes apoyan la iniciativa mientras 
        otros expresan sus preocupaciones.
        
        Los analistas sugieren que será importante monitorear los desarrollos 
        en los próximos días para comprender completamente las implicaciones 
        de esta decisión.
        """,
        
        """
        Una investigación reciente ha revelado información importante sobre 
        un tema que ha estado en debate durante meses. Los resultados del 
        estudio proporcionan nueva perspectiva sobre la situación actual.
        
        Los investigadores encontraron evidencia que sugiere que las 
        aproximaciones anteriores al problema podrían no haber sido las 
        más efectivas. Este descubrimiento podría llevar a cambios importantes 
        en las estrategias empleadas hasta ahora.
        
        Se espera que estos hallazgos tengan implicaciones de largo alcance 
        y generen discusión en la comunidad científica y política.
        """,
        
        """
        El evento más esperado del año finalmente ha llegado, trayendo consigo 
        gran expectativa y emoción. Miles de personas se han congregado para 
        presenciar este momento histórico.
        
        Los organizadores han trabajado incansablemente para asegurar que todo 
        salga según lo planeado. Las medidas de seguridad son estrictas y el 
        ambiente es de gran anticipación.
        
        Los asistentes expresan su entusiasmo por participar en este evento 
        único, que promete ser memorable para todos los involucrados.
        """
    ]
    
    return random.choice(content_templates)


def generate_summary() -> str:
    """Genera un resumen de muestra para artículos"""
    summaries = [
        "Autoridades anuncian nuevas medidas que prometen cambiar el panorama actual.",
        "Investigación reciente revela información importante sobre tema en debate.",
        "Evento histórico genera gran expectativa entre los asistentes.",
        "Decisión inesperada podría tener impacto significativo en el futuro.",
        "Nuevos hallazgos sugieren cambios importantes en estrategias actuales.",
        "Gran congregación de personas presenciará momento histórico único."
    ]
    return random.choice(summaries)


def generate_topic_tags() -> List[Dict[str, Any]]:
    """Genera tags de temas con puntuaciones de confianza"""
    all_topics = [
        {"tag": "technology", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "politics", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "health", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "economy", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "sports", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "entertainment", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "science", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "international", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "environment", "confidence": random.uniform(0.6, 0.95)},
        {"tag": "social", "confidence": random.uniform(0.6, 0.95)}
    ]
    
    # Seleccionar entre 1-3 tags aleatorios
    num_tags = random.randint(1, 3)
    selected_topics = random.sample(all_topics, num_tags)
    
    return selected_topics


class DuplicateArticleFactory(ArticleFactory):
    """Factory especializado para crear artículos duplicados"""
    
    def __init__(self, *args, **kwargs):
        # Si se proporciona un content_hash, usar ese, sino generar uno
        if 'content_hash' not in kwargs:
            kwargs['content_hash'] = hashlib.sha256(b"duplicate content").hexdigest()
        
        # Asignar el mismo duplicate_group_id a todos los duplicados
        if 'duplicate_group_id' not in kwargs:
            kwargs['duplicate_group_id'] = uuid.uuid4()
            
        super().__init__(*args, **kwargs)
    
    class Params:
        # Crear conjunto de duplicados
        duplicate_group = Trait()
        
        # Variación del contenido (pero mismo hash)
        varied_content = Trait(
            content=LazyFunction(lambda: generate_sample_content())  # Contenido diferente
        )


class FeaturedArticleFactory(ArticleFactory):
    """Factory para artículos destacados (alta relevancia)"""
    
    relevance_score = FuzzyFloat(low=0.8, high=1.0)
    bias_score = FuzzyFloat(low=0.0, high=0.3)  # Baja polarización
    sentiment_score = FuzzyFloat(low=0.2, high=0.8)  # Sentimiento positivo
    
    class Params:
        viral = Trait(
            relevance_score=1.0,
            topic_tags=[{"tag": "viral", "confidence": 0.95}]
        )
        
        breaking_news = Trait(
            published_at=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(5, 60))),
            relevance_score=0.9
        )


class ControversialArticleFactory(ArticleFactory):
    """Factory para artículos controversiales (alta polarización)"""
    
    bias_score = FuzzyFloat(low=0.7, high=1.0)
    sentiment_score = FuzzyChoice([-0.9, 0.9])  # Extremadamente positivo o negativo
    
    class Params:
        highly_positive = Trait(
            sentiment_score=FuzzyFloat(low=0.7, high=1.0),
            sentiment_label='positive'
        )
        
        highly_negative = Trait(
            sentiment_score=FuzzyFloat(low=-1.0, high=-0.7),
            sentiment_label='negative'
        )