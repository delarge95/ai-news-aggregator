"""
User Factory - Genera usuarios de prueba para testing
"""

import uuid
import random
import string
from datetime import datetime, timedelta
from typing import Optional, List
from factory import SubFactory, Sequence, LazyFunction, Trait, RelatedFactory
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyText, FuzzyEmail, FuzzyDateTime

from app.db.models import User, UserPreference, UserBookmark


class UserFactory(SQLAlchemyModelFactory):
    """Factory para generar usuarios de prueba"""
    
    class Meta:
        model = User
        sqlalchemy_session_persistence = "flush"
    
    # Campos obligatorios
    id = LazyFunction(uuid.uuid4)
    username = Sequence(lambda n: f"usuario{n}")
    email = Sequence(lambda n: f"usuario{n}@test.com")
    full_name = FuzzyText(length=20)
    hashed_password = LazyFunction(lambda: "hashed_password_placeholder")
    
    # Campos booleanos
    is_active = True
    is_superuser = False
    
    # Campos con opciones
    role = FuzzyChoice(['user', 'admin', 'moderator'])
    avatar_url = FuzzyChoice([
        None,
        "https://example.com/avatar1.jpg",
        "https://example.com/avatar2.jpg",
        "https://example.com/avatar3.jpg"
    ])
    
    # Campos de fecha
    last_login = LazyFunction(lambda: datetime.utcnow() - timedelta(
        hours=random.randint(1, 72)
    ))
    
    # Tratos para diferentes tipos de usuarios
    class Params:
        # Usuario administrador
        admin = Trait(
            is_superuser=True,
            role='admin'
        )
        
        # Usuario moderador
        moderator = Trait(
            role='moderator'
        )
        
        # Usuario inactivo
        inactive = Trait(
            is_active=False
        )
        
        # Usuario sin login reciente
        never_logged = Trait(
            last_login=None
        )
        
        # Usuario con avatar
        with_avatar = Trait(
            avatar_url=LazyFunction(lambda: f"https://example.com/avatars/{uuid.uuid4()}.jpg")
        )
        
        # Usuario recién creado
        new_user = Trait(
            created_at=LazyFunction(lambda: datetime.utcnow() - timedelta(hours=1)),
            last_login=None
        )
        
        # Usuario activo frecuente
        active_user = Trait(
            last_login=LazyFunction(lambda: datetime.utcnow() - timedelta(minutes=random.randint(1, 60)))
        )


class UserPreferenceFactory(SQLAlchemyModelFactory):
    """Factory para generar preferencias de usuario"""
    
    class Meta:
        model = UserPreference
        sqlalchemy_session_persistence = "flush"
    
    id = LazyFunction(uuid.uuid4)
    
    # Campos requeridos
    user = SubFactory('tests.factories.user_factory.UserFactory')
    user_id = None  # Establecido automáticamente por la relación
    
    # Arrays de preferencias
    preferred_sources = LazyFunction(lambda: generate_source_preferences())
    blocked_sources = LazyFunction(lambda: generate_blocked_sources())
    preferred_topics = LazyFunction(lambda: generate_topic_preferences())
    ignored_topics = LazyFunction(lambda: generate_ignored_topics())
    
    # Opciones de filtrado
    sentiment_preference = FuzzyChoice(['positive', 'negative', 'neutral', 'all'])
    reading_level = FuzzyChoice(['simple', 'mixed', 'complex'])
    notification_frequency = FuzzyChoice(['realtime', 'hourly', 'daily', 'weekly'])
    
    # Configuración de idioma y zona horaria
    language = FuzzyChoice(['es', 'en', 'fr', 'pt'])
    timezone = FuzzyChoice(['UTC', 'Europe/Madrid', 'America/New_York', 'Asia/Tokyo'])
    
    # Tratos para diferentes tipos de preferencias
    class Params:
        # Usuario con preferencias estrictas
        strict_preferences = Trait(
            preferred_topics=['technology', 'science'],
            ignored_topics=['politics', 'entertainment'],
            sentiment_preference='positive',
            reading_level='complex'
        )
        
        # Usuario casual (preferencias amplias)
        casual_preferences = Trait(
            sentiment_preference='all',
            reading_level='mixed',
            notification_frequency='daily'
        )
        
        # Usuario solo noticias positivas
        positive_only = Trait(
            sentiment_preference='positive',
            preferred_topics=['health', 'technology', 'science']
        )
        
        # Usuario que evita política
        no_politics = Trait(
            ignored_topics=['politics', 'government', 'election']
        )
        
        # Usuario que prefiere noticias complejas
        advanced_reader = Trait(
            reading_level='complex',
            preferred_topics=['science', 'technology', 'economy']
        )
        
        # Usuario que prefiere noticias simples
        simple_reader = Trait(
            reading_level='simple',
            preferred_topics=['sports', 'entertainment', 'health']
        )
        
        # Usuario con muchas fuentes bloqueadas
        selective_reader = Trait(
            blocked_sources=LazyFunction(lambda: generate_blocked_sources(count=5))
        )
        
        # Usuario con muchas fuentes preferidas
        diversified_reader = Trait(
            preferred_sources=LazyFunction(lambda: generate_source_preferences(count=10))
        )


class UserBookmarkFactory(SQLAlchemyModelFactory):
    """Factory para generar marcadores de usuario"""
    
    class Meta:
        model = UserBookmark
        sqlalchemy_session_persistence = "flush"
    
    id = LazyFunction(uuid.uuid4)
    
    # Campos requeridos
    user = SubFactory('tests.factories.user_factory.UserFactory')
    user_id = None  # Establecido automáticamente
    
    article = SubFactory('tests.factories.article_factory.ArticleFactory')
    article_id = None  # Establecido automáticamente
    
    title = FuzzyText(length=100)
    url = LazyFunction(lambda: f"https://example.com/bookmark/{uuid.uuid4()}")
    notes = FuzzyChoice([
        None,
        "Artículo muy interesante",
        "Para leer después",
        "Información importante",
        "Fuente confiable",
        "Tema a investigar más"
    ])
    tags = LazyFunction(lambda: generate_bookmark_tags())
    
    # Tratos para diferentes tipos de marcadores
    class Params:
        # Marcador con notas
        with_notes = Trait(
            notes="Este artículo contiene información muy valiosa para mi investigación."
        )
        
        # Marcador con tags
        with_tags = Trait(
            tags=['important', 'research', 'technology']
        )
        
        # Marcador sin notas
        no_notes = Trait(
            notes=None
        )
        
        # Marcador con muchos tags
        tagged_extensively = Trait(
            tags=['tech', 'AI', 'future', 'innovation', 'important']
        )


# Factory para crear usuarios con preferencias establecidas
class UserWithPreferencesFactory(UserFactory):
    """Factory para usuarios con preferencias ya establecidas"""
    
    preferences = RelatedFactory(
        UserPreferenceFactory,
        factory_related_name='user'
    )


class AdminUserFactory(UserFactory):
    """Factory específico para administradores"""
    
    class Params:
        admin = Trait(
            is_superuser=True,
            role='admin',
            username=Sequence(lambda n: f"admin{n}"),
            email=Sequence(lambda n: f"admin{n}@test.com")
        )


class ModeratorUserFactory(UserFactory):
    """Factory específico para moderadores"""
    
    class Params:
        moderator = Trait(
            role='moderator',
            username=Sequence(lambda n: f"moderator{n}"),
            email=Sequence(lambda n: f"moderator{n}@test.com")
        )


class InactiveUserFactory(UserFactory):
    """Factory específico para usuarios inactivos"""
    
    class Params:
        inactive = Trait(
            is_active=False,
            last_login=LazyFunction(lambda: datetime.utcnow() - timedelta(days=random.randint(30, 365)))
        )


# Funciones auxiliares para generar datos de preferencias

def generate_source_preferences(count: int = 3) -> List[str]:
    """Genera lista de IDs de fuentes preferidas"""
    source_ids = []
    for _ in range(count):
        source_ids.append(str(uuid.uuid4()))
    return source_ids


def generate_blocked_sources(count: int = 2) -> List[str]:
    """Genera lista de IDs de fuentes bloqueadas"""
    blocked_ids = []
    for _ in range(count):
        blocked_ids.append(str(uuid.uuid4()))
    return blocked_ids


def generate_topic_preferences() -> List[str]:
    """Genera lista de temas preferidos"""
    all_topics = [
        'technology', 'science', 'health', 'politics', 'economy',
        'sports', 'entertainment', 'international', 'environment', 'social'
    ]
    
    num_preferences = random.randint(2, 5)
    return random.sample(all_topics, num_preferences)


def generate_ignored_topics() -> List[str]:
    """Genera lista de temas ignorados"""
    all_topics = [
        'technology', 'science', 'health', 'politics', 'economy',
        'sports', 'entertainment', 'international', 'environment', 'social'
    ]
    
    num_ignored = random.randint(0, 3)
    if num_ignored > 0:
        return random.sample(all_topics, num_ignored)
    return []


def generate_bookmark_tags() -> List[str]:
    """Genera tags para marcadores"""
    available_tags = [
        'important', 'research', 'to_read', 'archived', 'reference',
        'inspiring', 'controversial', 'factual', 'opinion', 'breaking_news',
        'technology', 'science', 'health', 'politics', 'economy'
    ]
    
    num_tags = random.randint(0, 4)
    if num_tags > 0:
        return random.sample(available_tags, num_tags)
    return []


# Factory para crear conjuntos de usuarios con diferentes roles
class UserSetFactory:
    """Factory para crear conjuntos de usuarios con diferentes roles"""
    
    @staticmethod
    def create_user_set(
        normal_users: int = 3,
        admins: int = 1,
        moderators: int = 1,
        inactive_users: int = 1
    ) -> List[User]:
        """Crea un conjunto balanceado de usuarios"""
        
        users = []
        
        # Usuarios normales
        for i in range(normal_users):
            user = UserFactory(role='user')
            users.append(user)
        
        # Administradores
        for i in range(admins):
            admin = AdminUserFactory()
            users.append(admin)
        
        # Moderadores
        for i in range(moderators):
            moderator = ModeratorUserFactory()
            users.append(moderator)
        
        # Usuarios inactivos
        for i in range(inactive_users):
            inactive = InactiveUserFactory()
            users.append(inactive)
        
        return users