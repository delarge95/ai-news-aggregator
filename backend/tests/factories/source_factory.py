"""
Source Factory - Genera fuentes de noticias de prueba para testing
"""

import uuid
import random
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from factory import SubFactory, Sequence, LazyFunction, Trait
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText, FuzzyFloat, FuzzyInteger

from app.db.models import Source


class SourceFactory(SQLAlchemyModelFactory):
    """Factory para generar fuentes de noticias de prueba"""
    
    class Meta:
        model = Source
        sqlalchemy_session_persistence = "flush"
    
    # Campos obligatorios
    id = LazyFunction(uuid.uuid4)
    name = Sequence(lambda n: f"Fuente de Noticias {n}")
    url = LazyFunction(lambda: f"https://news{n}.example.com")
    api_name = FuzzyChoice(['newsapi', 'guardian', 'nytimes', 'reuters', 'bbc'])
    api_source_id = Sequence(lambda n: f"source_{n}")
    
    # Campos opcionales pero realistas
    country = FuzzyChoice([
        'España', 'Estados Unidos', 'Reino Unido', 'Francia', 'Alemania',
        'Italia', 'Brasil', 'Argentina', 'México', 'Canadá', 'Australia', 'Japón'
    ])
    language = FuzzyChoice(['es', 'en', 'fr', 'de', 'it', 'pt'])
    
    # Configuración de credibilidad y límites
    credibility_score = FuzzyFloat(low=0.3, high=1.0)
    is_active = True
    rate_limit_per_hour = FuzzyInteger(low=50, high=500)
    rate_limit_info = LazyFunction(lambda: generate_rate_limit_info())
    
    # Tratos para diferentes tipos de fuentes
    class Params:
        # Fuente muy creíble
        highly_credible = Trait(
            credibility_score=FuzzyFloat(low=0.8, high=1.0)
        )
        
        # Fuente poco creíble
        low_credibility = Trait(
            credibility_score=FuzzyFloat(low=0.1, high=0.4)
        )
        
        # Fuente inactiva
        inactive = Trait(
            is_active=False
        )
        
        # Fuente con límites estrictos
        strict_limits = Trait(
            rate_limit_per_hour=FuzzyInteger(low=10, high=50)
        )
        
        # Fuente con límites generosos
        generous_limits = Trait(
            rate_limit_per_hour=FuzzyInteger(low=200, high=500)
        )
        
        # Fuente española
        spanish = Trait(
            country='España',
            language='es',
            name=FuzzyChoice([
                'El País', 'El Mundo', 'ABC', 'La Vanguardia', 'El Periódico',
                'El Confidencial', 'Marca', 'AS', 'COPE', 'RTVE'
            ])
        )
        
        # Fuente inglesa
        english = Trait(
            country='Estados Unidos',
            language='en',
            name=FuzzyChoice([
                'CNN', 'BBC', 'Reuters', 'Associated Press', 'The Guardian',
                'The New York Times', 'The Washington Post', 'The Wall Street Journal',
                'NBC News', 'ABC News'
            ])
        )
        
        # Fuente francesa
        french = Trait(
            country='Francia',
            language='fr',
            name=FuzzyChoice([
                'Le Figaro', 'Le Monde', 'Le Parisien', 'France 24', 'Radio France'
            ])
        )
        
        # Fuente alemana
        german = Trait(
            country='Alemania',
            language='de',
            name=FuzzyChoice([
                'Der Spiegel', 'Die Zeit', 'Frankfurter Allgemeine', 'Süddeutsche Zeitung'
            ])
        )
        
        # Fuente tecnológica
        tech_focused = Trait(
            name=FuzzyChoice([
                'TechCrunch', 'Wired', 'The Verge', 'Ars Technica', 'MIT Technology Review'
            ]),
            country=FuzzyChoice(['Estados Unidos', 'Reino Unido'])
        )
        
        # Fuente deportiva
        sports_focused = Trait(
            name=FuzzyChoice([
                'ESPN', 'Sky Sports', 'Marca', 'AS', 'L\'Équipe'
            ]),
            country=FuzzyChoice(['España', 'Estados Unidos', 'Francia'])
        )
        
        # Fuente política
        politics_focused = Trait(
            name=FuzzyChoice([
                'The Political', 'Política News', 'Congress Today', 'Government Gazette'
            ])
        )


# Factories especializados para diferentes tipos de fuentes
class HighCredibilitySourceFactory(SourceFactory):
    """Factory para fuentes de alta credibilidad"""
    
    class Params:
        highly_credible = Trait(
            credibility_score=FuzzyFloat(low=0.9, high=1.0),
            name=FuzzyChoice([
                'Reuters', 'Associated Press', 'BBC', 'Der Spiegel', 'Le Monde'
            ])
        )


class LowCredibilitySourceFactory(SourceFactory):
    """Factory para fuentes de baja credibilidad"""
    
    class Params:
        low_credibility = Trait(
            credibility_score=FuzzyFloat(low=0.1, high=0.3),
            name=Sequence(lambda n: f"Blog de Noticias {n}")
        )


class InactiveSourceFactory(SourceFactory):
    """Factory para fuentes inactivas"""
    
    class Params:
        inactive = Trait(
            is_active=False,
            name=Sequence(lambda n: f"Fuente Inactiva {n}")
        )


class SpanishSourceFactory(SourceFactory):
    """Factory específico para fuentes españolas"""
    
    class Params:
        spanish = Trait(
            country='España',
            language='es',
            url=LazyFunction(lambda: f"https://{random.choice(['elpais', 'elmundo', 'abc', 'lavanguardia'])}.com"),
            name=FuzzyChoice([
                'El País', 'El Mundo', 'ABC', 'La Vanguardia', 'El Periódico',
                'El Confidencial', 'Marca', 'AS', 'COPE', 'RTVE'
            ])
        )


class EnglishSourceFactory(SourceFactory):
    """Factory específico para fuentes inglesas"""
    
    class Params:
        english = Trait(
            country='Estados Unidos',
            language='en',
            url=LazyFunction(lambda: f"https://{random.choice(['cnn', 'bbc', 'reuters', 'nytimes'])}.com"),
            name=FuzzyChoice([
                'CNN', 'BBC', 'Reuters', 'The Guardian', 'The New York Times',
                'The Washington Post', 'The Wall Street Journal', 'NBC News'
            ])
        )


class TechSourceFactory(SourceFactory):
    """Factory específico para fuentes tecnológicas"""
    
    class Params:
        tech_focused = Trait(
            name=FuzzyChoice([
                'TechCrunch', 'Wired', 'The Verge', 'Ars Technica', 'MIT Technology Review'
            ]),
            country=FuzzyChoice(['Estados Unidos', 'Reino Unido']),
            credibility_score=FuzzyFloat(low=0.6, high=0.9)
        )


class SportsSourceFactory(SourceFactory):
    """Factory específico para fuentes deportivas"""
    
    class Params:
        sports_focused = Trait(
            name=FuzzyChoice([
                'ESPN', 'Sky Sports', 'Marca', 'AS', 'L\'Équipe', 'Gazzetta dello Sport'
            ]),
            country=FuzzyChoice(['España', 'Estados Unidos', 'Francia', 'Italia']),
            credibility_score=FuzzyFloat(low=0.5, high=0.8)
        )


# Factory para conjunto de fuentes balanceadas
class SourceSetFactory:
    """Factory para crear conjuntos de fuentes balanceadas"""
    
    @staticmethod
    def create_news_source_set(
        high_credibility: int = 3,
        medium_credibility: int = 4,
        low_credibility: int = 2,
        inactive: int = 1,
        include_spanish: bool = True,
        include_english: bool = True,
        include_tech: bool = True,
        include_sports: bool = True
    ) -> List[Source]:
        """Crea un conjunto balanceado de fuentes"""
        
        sources = []
        
        # Fuentes de alta credibilidad
        for i in range(high_credibility):
            source = HighCredibilitySourceFactory()
            sources.append(source)
        
        # Fuentes de credibilidad media
        for i in range(medium_credibility):
            source = SourceFactory(
                credibility_score=FuzzyFloat(low=0.5, high=0.8)
            )
            sources.append(source)
        
        # Fuentes de baja credibilidad
        for i in range(low_credibility):
            source = LowCredibilitySourceFactory()
            sources.append(source)
        
        # Fuentes inactivas
        for i in range(inactive):
            source = InactiveSourceFactory()
            sources.append(source)
        
        # Fuentes especializadas por idioma
        if include_spanish:
            for i in range(2):
                source = SpanishSourceFactory()
                sources.append(source)
        
        if include_english:
            for i in range(2):
                source = EnglishSourceFactory()
                sources.append(source)
        
        # Fuentes especializadas por tema
        if include_tech:
            for i in range(1):
                source = TechSourceFactory()
                sources.append(source)
        
        if include_sports:
            for i in range(1):
                source = SportsSourceFactory()
                sources.append(source)
        
        return sources


# Factory para simular APIs externas específicas
class NewsAPISourceFactory(SourceFactory):
    """Factory para fuentes que usan NewsAPI"""
    
    class Meta:
        pass
    
    def __init__(self, *args, **kwargs):
        kwargs['api_name'] = 'newsapi'
        super().__init__(*args, **kwargs)
    
    class Params:
        newsapi_official = Trait(
            name=FuzzyChoice(['BBC News', 'CNN', 'Reuters', 'The Guardian', 'The Verge']),
            url=LazyFunction(lambda: f"https://{random.choice(['bbc', 'cnn', 'reuters', 'guardian'])}.com"),
            api_source_id=FuzzyChoice(['bbc-news', 'cnn', 'reuters', 'the-guardian-uk', 'the-verge'])
        )


class GuardianSourceFactory(SourceFactory):
    """Factory para fuentes que usan The Guardian API"""
    
    class Meta:
        pass
    
    def __init__(self, *args, **kwargs):
        kwargs['api_name'] = 'guardian'
        super().__init__(*args, **kwargs)
    
    class Params:
        guardian_official = Trait(
            name='The Guardian',
            url='https://theguardian.com',
            api_source_id='the-guardian'
        )


class NYTimesSourceFactory(SourceFactory):
    """Factory para fuentes que usan New York Times API"""
    
    class Meta:
        pass
    
    def __init__(self, *args, **kwargs):
        kwargs['api_name'] = 'nytimes'
        super().__init__(*args, **kwargs)
    
    class Params:
        nyt_official = Trait(
            name='The New York Times',
            url='https://nytimes.com',
            api_source_id='new-york-times'
        )


# Funciones auxiliares
def generate_rate_limit_info() -> Dict[str, Any]:
    """Genera información realista sobre rate limits"""
    return {
        'requests_made_last_hour': random.randint(0, 50),
        'requests_remaining': random.randint(0, 100),
        'reset_time': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        'api_quota_exceeded': False,
        'last_request_at': (datetime.utcnow() - timedelta(minutes=random.randint(1, 60))).isoformat(),
        'consecutive_failures': random.randint(0, 3),
        'total_requests_today': random.randint(0, 500)
    }


class APIMockSourceFactory(SourceFactory):
    """Factory para fuentes específicamente diseñadas para mock de APIs"""
    
    class Params:
        # Fuente que siempre está disponible
        always_available = Trait(
            rate_limit_info=LazyFunction(lambda: {
                'requests_made_last_hour': 0,
                'requests_remaining': 100,
                'api_quota_exceeded': False,
                'consecutive_failures': 0
            })
        )
        
        # Fuente cerca del límite
        near_limit = Trait(
            rate_limit_per_hour=50,
            rate_limit_info=LazyFunction(lambda: {
                'requests_made_last_hour': 45,
                'requests_remaining': 5,
                'api_quota_exceeded': False,
                'consecutive_failures': 0
            })
        )
        
        # Fuente que excedió el límite
        exceeded_limit = Trait(
            rate_limit_info=LazyFunction(lambda: {
                'requests_made_last_hour': 100,
                'requests_remaining': 0,
                'api_quota_exceeded': True,
                'consecutive_failures': 2
            })
        )