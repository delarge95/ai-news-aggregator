"""
Test Data Loader - Sistema para cargar y gestionar datos de prueba

Proporciona funcionalidad para cargar sets de datos de prueba de manera
consistente y reutilizable para testing del sistema.
"""

import uuid
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Type
from sqlalchemy.orm import Session

from app.db.models import (
    User, Source, Article, ArticleAnalysis, AnalysisTask,
    UserPreference, UserBookmark, TrendingTopic
)
from tests.factories.article_factory import ArticleFactory
from tests.factories.user_factory import UserFactory, UserPreferenceFactory, UserBookmarkFactory
from tests.factories.source_factory import SourceFactory
from tests.factories.analysis_factory import ArticleAnalysisFactory, AnalysisTaskFactory


class TestDataLoader:
    """Clase principal para cargar datos de prueba en la base de datos"""
    
    def __init__(self, db_session: Session):
        """
        Inicializa el loader con una sesión de base de datos
        
        Args:
            db_session: Sesión activa de la base de datos
        """
        self.db = db_session
        self.loaded_data = {
            'users': [],
            'sources': [],
            'articles': [],
            'analysis_results': [],
            'analysis_tasks': [],
            'user_preferences': [],
            'user_bookmarks': [],
            'trending_topics': []
        }
    
    def clear_all_data(self) -> None:
        """Limpia todos los datos de prueba cargados"""
        try:
            # Eliminar en orden inverso a las dependencias
            self.db.query(UserBookmark).delete()
            self.db.query(UserPreference).delete()
            self.db.query(AnalysisTask).delete()
            self.db.query(ArticleAnalysis).delete()
            self.db.query(Article).delete()
            self.db.query(Source).delete()
            self.db.query(User).delete()
            self.db.query(TrendingTopic).delete()
            
            self.db.commit()
            
            # Limpiar tracking de datos cargados
            for key in self.loaded_data:
                self.loaded_data[key] = []
                
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error limpiando datos de prueba: {str(e)}")
    
    def load_basic_data(
        self,
        num_users: int = 10,
        num_sources: int = 15,
        num_articles_per_source: int = 5
    ) -> Dict[str, Any]:
        """
        Carga datos básicos para testing
        
        Args:
            num_users: Número de usuarios a crear
            num_sources: Número de fuentes a crear
            num_articles_per_source: Número de artículos por fuente
            
        Returns:
            Dict con información de los datos cargados
        """
        try:
            # Cargar fuentes
            sources = self.load_sources(num_sources)
            
            # Cargar usuarios
            users = self.load_users(num_users)
            
            # Cargar artículos
            articles = self.load_articles(sources, num_articles_per_source)
            
            # Guardar cambios
            self.db.commit()
            
            return {
                'sources_count': len(sources),
                'users_count': len(users),
                'articles_count': len(articles),
                'data_loaded_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error cargando datos básicos: {str(e)}")
    
    def load_sources(self, count: int = 10, include_specialized: bool = True) -> List[Source]:
        """Carga fuentes de noticias"""
        sources = []
        
        for i in range(count):
            if include_specialized and i % 5 == 0:
                # Cada 5ta fuente es especializada
                source_type = random.choice(['spanish', 'english', 'tech', 'sports'])
                if source_type == 'spanish':
                    source = SourceFactory(spanish=True)
                elif source_type == 'english':
                    source = SourceFactory(english=True)
                elif source_type == 'tech':
                    source = SourceFactory(tech_focused=True)
                else:
                    source = SourceFactory(sports_focused=True)
            else:
                source = SourceFactory()
            
            sources.append(source)
        
        self.loaded_data['sources'].extend(sources)
        return sources
    
    def load_users(
        self,
        count: int = 10,
        include_preferences: bool = True,
        include_bookmarks: bool = False
    ) -> List[User]:
        """Carga usuarios con sus preferencias opcionales"""
        users = []
        
        for i in range(count):
            # Crear usuario
            if i == 0:
                # Primer usuario como admin
                user = UserFactory(admin=True)
            else:
                user = UserFactory()
            
            users.append(user)
            
            # Crear preferencias si se solicita
            if include_preferences and i % 3 == 0:
                # 1 de cada 3 usuarios tiene preferencias
                preferences = UserPreferenceFactory(user=user)
                self.loaded_data['user_preferences'].append(preferences)
            
            # Crear marcadores si se solicita
            if include_bookmarks and i % 2 == 0:
                # 1 de cada 2 usuarios tiene marcadores
                bookmark = UserBookmarkFactory(user=user)
                self.loaded_data['user_bookmarks'].append(bookmark)
        
        self.loaded_data['users'].extend(users)
        return users
    
    def load_articles(
        self,
        sources: List[Source],
        articles_per_source: int = 3,
        include_analysis: bool = False,
        include_processing_status: bool = True
    ) -> List[Article]:
        """Carga artículos con diferentes características"""
        articles = []
        
        for source in sources:
            for i in range(articles_per_source):
                # Varía el tipo de artículo
                traits = []
                
                if include_processing_status:
                    if i % 4 == 0:
                        traits.append('processed')
                    elif i % 4 == 1:
                        traits.append('unprocessed')
                    elif i % 4 == 2:
                        traits.append('failed')
                    else:
                        traits.append('recent')
                
                # Añade variación temática
                if i % 3 == 0:
                    traits.append('tech_related')
                elif i % 3 == 1:
                    traits.append('politics_related')
                else:
                    traits.append('health_related')
                
                # Crear artículo
                article = ArticleFactory(
                    source=source,
                    **{trait: True for trait in traits}
                )
                
                articles.append(article)
                
                # Añadir análisis si se solicita
                if include_analysis and article.processing_status.value == 'completed':
                    # Solo artículos procesados tienen análisis
                    analysis_types = ['summary', 'sentiment', 'topics']
                    for analysis_type in analysis_types:
                        analysis = ArticleAnalysisFactory(
                            article=article,
                            analysis_type=analysis_type
                        )
                        self.loaded_data['analysis_results'].append(analysis)
        
        self.loaded_data['articles'].extend(articles)
        return articles
    
    def load_advanced_test_data(self) -> Dict[str, Any]:
        """Carga datos avanzados para testing complejo"""
        try:
            # Datos básicos primero
            basic_result = self.load_basic_data(
                num_users=20,
                num_sources=15,
                num_articles_per_source=8
            )
            
            # Cargar análisis avanzado
            self.load_advanced_analysis()
            
            # Cargar trending topics
            self.load_trending_topics()
            
            # Cargar tareas de análisis
            self.load_analysis_tasks()
            
            # Crear marcadores para usuarios
            self.create_user_bookmarks()
            
            self.db.commit()
            
            return {
                **basic_result,
                'advanced_data_loaded_at': datetime.utcnow().isoformat(),
                'total_analysis_results': len(self.loaded_data['analysis_results']),
                'total_trending_topics': len(self.loaded_data['trending_topics']),
                'total_analysis_tasks': len(self.loaded_data['analysis_tasks']),
                'total_user_bookmarks': len(self.loaded_data['user_bookmarks'])
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error cargando datos avanzados: {str(e)}")
    
    def load_advanced_analysis(self) -> None:
        """Carga análisis avanzado para artículos"""
        articles = self.db.query(Article).filter(
            Article.processing_status == 'completed'
        ).all()
        
        for article in articles:
            # Crear análisis completo
            analysis_types = ['summary', 'sentiment', 'bias', 'topics', 'relevance', 'entities']
            
            for analysis_type in analysis_types:
                analysis = ArticleAnalysisFactory(
                    article=article,
                    analysis_type=analysis_type
                )
                self.loaded_data['analysis_results'].append(analysis)
    
    def load_trending_topics(self, count: int = 20) -> None:
        """Carga topics trending"""
        topics_data = [
            {'topic': 'Inteligencia Artificial', 'category': 'technology', 'score': 0.95},
            {'topic': 'Cambio Climático', 'category': 'environment', 'score': 0.88},
            {'topic': 'Elecciones 2024', 'category': 'politics', 'score': 0.92},
            {'topic': 'Crisis Económica', 'category': 'economy', 'score': 0.85},
            {'topic': 'Vacuna COVID-19', 'category': 'health', 'score': 0.78},
            {'topic': 'Copa del Mundo', 'category': 'sports', 'score': 0.90},
            {'topic': 'Festival de Cannes', 'category': 'entertainment', 'score': 0.82},
            {'topic': 'Exploración Espacial', 'category': 'science', 'score': 0.86},
            {'topic': 'Guerra en Ucrania', 'category': 'international', 'score': 0.94},
            {'topic': 'Derechos Humanos', 'category': 'social', 'score': 0.81}
        ]
        
        for i in range(min(count, len(topics_data))):
            topic_data = topics_data[i % len(topics_data)]
            
            trending_topic = TrendingTopic(
                topic=topic_data['topic'],
                topic_category=topic_data['category'],
                trend_score=topic_data['score'] * random.uniform(0.8, 1.0),
                article_count=random.randint(50, 500),
                sources_count=random.randint(5, 25),
                time_period='24h',
                date_recorded=datetime.utcnow() - timedelta(hours=random.randint(1, 12)),
                trend_metadata={
                    'growth_rate': random.uniform(0.1, 0.5),
                    'mentions_count': random.randint(1000, 50000),
                    'sentiment_average': random.uniform(-0.2, 0.3)
                }
            )
            
            self.db.add(trending_topic)
            self.loaded_data['trending_topics'].append(trending_topic)
    
    def load_analysis_tasks(self, count: int = 30) -> None:
        """Carga tareas de análisis con diferentes estados"""
        states = ['pending', 'running', 'completed', 'failed']
        weights = [0.4, 0.2, 0.3, 0.1]  # Distribución realista
        
        for i in range(count):
            state = random.choices(states, weights=weights)[0]
            
            if state == 'pending':
                task = AnalysisTaskFactory(pending=True)
            elif state == 'running':
                task = AnalysisTaskFactory(running=True)
            elif state == 'completed':
                task = AnalysisTaskFactory(completed=True)
            else:
                task = AnalysisTaskFactory(failed=True)
            
            self.loaded_data['analysis_tasks'].append(task)
    
    def create_user_bookmarks(self) -> None:
        """Crea marcadores para usuarios existentes"""
        users = self.db.query(User).filter(User.is_active == True).all()
        articles = self.db.query(Article).limit(50).all()  # Limitar para evitar demasiados bookmarks
        
        for user in users:
            # Cada usuario crea entre 0-5 marcadores
            num_bookmarks = random.randint(0, 5)
            
            if num_bookmarks > 0 and articles:
                selected_articles = random.sample(articles, min(num_bookmarks, len(articles)))
                
                for article in selected_articles:
                    bookmark = UserBookmarkFactory(
                        user=user,
                        article=article,
                        title=article.title[:100],  # Usar título del artículo
                        url=article.url
                    )
                    self.loaded_data['user_bookmarks'].append(bookmark)
    
    def create_duplicate_articles(self, source: Source, num_duplicates: int = 3) -> List[Article]:
        """Crea conjunto de artículos duplicados"""
        # Crear artículo original
        original = ArticleFactory(source=source, processed=True)
        
        # Crear duplicados con mismo content_hash y duplicate_group_id
        duplicates = []
        duplicate_group_id = uuid.uuid4()
        content_hash = original.content_hash
        
        for i in range(num_duplicates):
            duplicate = ArticleFactory(
                source=source,
                duplicate_group_id=duplicate_group_id,
                content_hash=content_hash,
                processed=True
            )
            duplicates.append(duplicate)
        
        self.loaded_data['articles'].extend(duplicates)
        return [original] + duplicates
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Retorna resumen de datos cargados"""
        return {
            'users': len(self.loaded_data['users']),
            'sources': len(self.loaded_data['sources']),
            'articles': len(self.loaded_data['articles']),
            'analysis_results': len(self.loaded_data['analysis_results']),
            'analysis_tasks': len(self.loaded_data['analysis_tasks']),
            'user_preferences': len(self.loaded_data['user_preferences']),
            'user_bookmarks': len(self.loaded_data['user_bookmarks']),
            'trending_topics': len(self.loaded_data['trending_topics']),
            'loaded_at': datetime.utcnow().isoformat()
        }
    
    def export_test_data(self, filepath: str) -> None:
        """Exporta datos de prueba a archivo JSON"""
        export_data = {
            'metadata': {
                'exported_at': datetime.utcnow().isoformat(),
                'total_records': sum(len(data) for data in self.loaded_data.values())
            },
            'data': {}
        }
        
        # Convertir objetos SQLAlchemy a diccionarios
        for data_type, objects in self.loaded_data.items():
            export_data['data'][data_type] = []
            
            for obj in objects:
                if hasattr(obj, '__dict__'):
                    obj_dict = {k: v for k, v in obj.__dict__.items() 
                              if not k.startswith('_') and k != 'metadata'}
                    export_data['data'][data_type].append(obj_dict)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)


# Funciones de conveniencia para testing rápido

def quick_test_data(db_session: Session) -> Dict[str, Any]:
    """Carga datos mínimos para testing rápido"""
    loader = TestDataLoader(db_session)
    return loader.load_basic_data(num_users=5, num_sources=5, num_articles_per_source=3)


def comprehensive_test_data(db_session: Session) -> Dict[str, Any]:
    """Carga datos completos para testing exhaustivo"""
    loader = TestDataLoader(db_session)
    return loader.load_advanced_test_data()


def cleanup_test_data(db_session: Session) -> None:
    """Limpia todos los datos de prueba"""
    loader = TestDataLoader(db_session)
    loader.clear_all_data()


# Context manager para manejo automático de datos de prueba
class TestDataContext:
    """Context manager para datos de prueba"""
    
    def __init__(self, db_session: Session, data_level: str = 'basic'):
        """
        Args:
            db_session: Sesión de base de datos
            data_level: 'basic', 'advanced', o 'minimal'
        """
        self.db = db_session
        self.data_level = data_level
        self.loader = None
    
    def __enter__(self):
        self.loader = TestDataLoader(self.db)
        
        if self.data_level == 'minimal':
            return self.loader.load_basic_data(num_users=2, num_sources=2, num_articles_per_source=1)
        elif self.data_level == 'basic':
            return self.loader.load_basic_data()
        elif self.data_level == 'advanced':
            return self.loader.load_advanced_test_data()
        else:
            raise ValueError(f"Nivel de datos no reconocido: {self.data_level}")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # Sin errores, limpiar datos
            self.loader.clear_all_data()
        else:
            # Con errores, hacer rollback
            self.db.rollback()