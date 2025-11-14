#!/usr/bin/env python3
"""
Script de inicialización de datos para el sistema de búsqueda avanzada
Puebla la base de datos con datos de ejemplo para testing y demo
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import uuid

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from app.db.models import Article, Source, TrendingTopic, UserPreference, ArticleAnalysis
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SearchDataInitializer:
    """Inicializador de datos para el sistema de búsqueda"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url or settings.DATABASE_URL
        self.engine = create_engine(self.db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def initialize_data(self):
        """Inicializar todos los datos de ejemplo"""
        db = self.SessionLocal()
        
        try:
            logger.info("Iniciando población de datos para búsqueda avanzada")
            
            # Crear fuentes de ejemplo
            sources = self._create_sample_sources(db)
            
            # Crear artículos de ejemplo
            articles = self._create_sample_articles(db, sources)
            
            # Crear trending topics de ejemplo
            self._create_sample_trending_topics(db)
            
            # Crear análisis de ejemplo
            self._create_sample_analysis(db, articles)
            
            # Crear preferencias de usuario de ejemplo
            self._create_sample_user_preferences(db)
            
            db.commit()
            
            logger.info("Datos inicializados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error inicializando datos: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()
    
    def _create_sample_sources(self, db) -> List[Source]:
        """Crear fuentes de noticias de ejemplo"""
        logger.info("Creando fuentes de ejemplo")
        
        sample_sources = [
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com",
                "api_name": "techcrunch",
                "api_source_id": "techcrunch",
                "country": "US",
                "language": "en",
                "credibility_score": 0.85
            },
            {
                "name": "MIT Technology Review",
                "url": "https://technologyreview.com",
                "api_name": "mit_tech_review",
                "api_source_id": "mit_tech_review",
                "country": "US",
                "language": "en",
                "credibility_score": 0.92
            },
            {
                "name": "Wired",
                "url": "https://wired.com",
                "api_name": "wired",
                "api_source_id": "wired",
                "country": "US",
                "language": "en",
                "credibility_score": 0.88
            },
            {
                "name": "The Verge",
                "url": "https://theverge.com",
                "api_name": "the_verge",
                "api_source_id": "the_verge",
                "country": "US",
                "language": "en",
                "credibility_score": 0.82
            },
            {
                "name": "Ars Technica",
                "url": "https://arstechnica.com",
                "api_name": "ars_technica",
                "api_source_id": "ars_technica",
                "country": "US",
                "language": "en",
                "credibility_score": 0.90
            },
            {
                "name": "BBC Technology",
                "url": "https://bbc.com/technology",
                "api_name": "bbc",
                "api_source_id": "bbc-technology",
                "country": "UK",
                "language": "en",
                "credibility_score": 0.94
            },
            {
                "name": "CNN Technology",
                "url": "https://cnn.com/tech",
                "api_name": "cnn",
                "api_source_id": "cnn-tech",
                "country": "US",
                "language": "en",
                "credibility_score": 0.80
            }
        ]
        
        created_sources = []
        
        for source_data in sample_sources:
            # Verificar si ya existe
            existing = db.query(Source).filter(Source.name == source_data["name"]).first()
            if not existing:
                source = Source(**source_data)
                db.add(source)
                created_sources.append(source)
                logger.info(f"Creada fuente: {source_data['name']}")
            else:
                created_sources.append(existing)
        
        return created_sources
    
    def _create_sample_articles(self, db, sources: List[Source]) -> List[Article]:
        """Crear artículos de ejemplo"""
        logger.info("Creando artículos de ejemplo")
        
        sample_articles = [
            {
                "title": "OpenAI Announces GPT-5 with Revolutionary Multimodal Capabilities",
                "content": "OpenAI has unveiled GPT-5, its most advanced language model yet, featuring unprecedented multimodal capabilities that can process text, images, audio, and video simultaneously. The new model demonstrates remarkable improvements in reasoning, creativity, and real-world application understanding.",
                "summary": "OpenAI reveals GPT-5 with advanced multimodal AI capabilities for comprehensive content processing.",
                "url": "https://techcrunch.com/openai-gpt5-multimodal",
                "published_at": datetime.utcnow() - timedelta(hours=2),
                "sentiment_score": 0.75,
                "sentiment_label": "positive",
                "bias_score": 0.3,
                "topic_tags": ["artificial-intelligence", "openai", "gpt", "language-models"],
                "relevance_score": 0.95,
                "processing_status": "completed"
            },
            {
                "title": "Google's Gemini Ultra Achieves Human-Level Performance on Complex Reasoning",
                "content": "Google's latest AI model, Gemini Ultra, has achieved human-level performance on complex reasoning tasks, marking a significant milestone in artificial intelligence development. The model excels in mathematics, programming, and logical reasoning benchmarks.",
                "summary": "Google's Gemini Ultra reaches human-level reasoning capabilities across multiple domains.",
                "url": "https://technologyreview.com/google-gemini-ultra",
                "published_at": datetime.utcnow() - timedelta(hours=4),
                "sentiment_score": 0.85,
                "sentiment_label": "positive",
                "bias_score": 0.25,
                "topic_tags": ["google", "gemini", "reasoning", "artificial-intelligence"],
                "relevance_score": 0.92,
                "processing_status": "completed"
            },
            {
                "title": "Meta's AI Research Breakthrough in Neural Network Architecture",
                "content": "Meta researchers have developed a novel neural network architecture that reduces computational requirements by 80% while maintaining performance. This breakthrough could democratize access to advanced AI capabilities on consumer hardware.",
                "summary": "Meta's new neural architecture reduces AI computational costs by 80% for better accessibility.",
                "url": "https://wired.com/meta-ai-breakthrough",
                "published_at": datetime.utcnow() - timedelta(hours=6),
                "sentiment_score": 0.80,
                "sentiment_label": "positive",
                "bias_score": 0.35,
                "topic_tags": ["meta", "neural-networks", "efficiency", "ai-research"],
                "relevance_score": 0.88,
                "processing_status": "completed"
            },
            {
                "title": "Tesla's Full Self-Driving AI Vision System Receives Regulatory Approval",
                "content": "Tesla's Full Self-Driving (FSD) vision system has received regulatory approval for testing on public roads in multiple states. The advanced AI system uses a novel approach combining neural networks, computer vision, and real-time decision making.",
                "summary": "Tesla's FSD AI system gets regulatory approval for expanded testing in public roads.",
                "url": "https://theverge.com/tesla-fsd-approval",
                "published_at": datetime.utcnow() - timedelta(hours=8),
                "sentiment_score": 0.70,
                "sentiment_label": "positive",
                "bias_score": 0.40,
                "topic_tags": ["tesla", "self-driving", "computer-vision", "autonomous-vehicles"],
                "relevance_score": 0.85,
                "processing_status": "completed"
            },
            {
                "title": "Anthropic's Claude 3.5 Excels in Medical Diagnosis and Healthcare AI",
                "content": "Anthropic's Claude 3.5 model demonstrates exceptional performance in medical diagnosis, achieving 95% accuracy in preliminary assessments. Healthcare institutions are implementing the AI system for triage and diagnostic support.",
                "summary": "Claude 3.5 achieves 95% accuracy in medical diagnosis, transforming healthcare AI applications.",
                "url": "https://arstechnica.com/anthropic-claude-healthcare",
                "published_at": datetime.utcnow() - timedelta(hours=10),
                "sentiment_score": 0.65,
                "sentiment_label": "positive",
                "bias_score": 0.30,
                "topic_tags": ["anthropic", "claude", "healthcare", "medical-ai"],
                "relevance_score": 0.90,
                "processing_status": "completed"
            },
            {
                "title": "Microsoft's AI Copilot Integrates Advanced Robotics Control",
                "content": "Microsoft has integrated its AI Copilot system with advanced robotics control, enabling natural language commands for complex robotic tasks. The system shows promise in manufacturing and industrial automation applications.",
                "summary": "Microsoft Copilot expands to robotics control through natural language interface integration.",
                "url": "https://bbc.com/technology/microsoft-copilot-robotics",
                "published_at": datetime.utcnow() - timedelta(hours=12),
                "sentiment_score": 0.60,
                "sentiment_label": "positive",
                "bias_score": 0.35,
                "topic_tags": ["microsoft", "copilot", "robotics", "automation"],
                "relevance_score": 0.82,
                "processing_status": "completed"
            },
            {
                "title": "Breakthrough in Quantum Computing: IBM's 1000-Qubit Processor",
                "content": "IBM has unveiled a 1000-qubit quantum processor, representing a major breakthrough in quantum computing. The system promises to revolutionize cryptography, drug discovery, and complex optimization problems.",
                "summary": "IBM's 1000-qubit quantum processor opens new possibilities in computing and scientific research.",
                "url": "https://cnn.com/tech/ibm-quantum-processor",
                "published_at": datetime.utcnow() - timedelta(hours=14),
                "sentiment_score": 0.90,
                "sentiment_label": "positive",
                "bias_score": 0.20,
                "topic_tags": ["ibm", "quantum-computing", "breakthrough", "hardware"],
                "relevance_score": 0.95,
                "processing_status": "completed"
            }
        ]
        
        created_articles = []
        
        for i, article_data in enumerate(sample_articles):
            # Usar fuente en rotación
            source = sources[i % len(sources)]
            
            # Verificar si ya existe
            existing = db.query(Article).filter(Article.url == article_data["url"]).first()
            if not existing:
                article = Article(
                    source_id=source.id,
                    **article_data
                )
                db.add(article)
                created_articles.append(article)
                logger.info(f"Creado artículo: {article_data['title'][:50]}...")
        
        return created_articles
    
    def _create_sample_trending_topics(self, db):
        """Crear trending topics de ejemplo"""
        logger.info("Creando trending topics de ejemplo")
        
        trending_topics = [
            {
                "topic": "GPT-5",
                "topic_category": "artificial-intelligence",
                "trend_score": 0.95,
                "article_count": 156,
                "sources_count": 12,
                "time_period": "24h"
            },
            {
                "topic": "Gemini Ultra",
                "topic_category": "artificial-intelligence", 
                "trend_score": 0.88,
                "article_count": 134,
                "sources_count": 10,
                "time_period": "24h"
            },
            {
                "topic": "Claude 3.5",
                "topic_category": "artificial-intelligence",
                "trend_score": 0.82,
                "article_count": 98,
                "sources_count": 8,
                "time_period": "24h"
            },
            {
                "topic": "quantum computing",
                "topic_category": "technology",
                "trend_score": 0.78,
                "article_count": 87,
                "sources_count": 7,
                "time_period": "24h"
            },
            {
                "topic": "self-driving cars",
                "topic_category": "transportation",
                "trend_score": 0.75,
                "article_count": 76,
                "sources_count": 9,
                "time_period": "24h"
            },
            {
                "topic": "neural networks",
                "topic_category": "artificial-intelligence",
                "trend_score": 0.72,
                "article_count": 65,
                "sources_count": 6,
                "time_period": "24h"
            },
            {
                "topic": "robotics automation",
                "topic_category": "technology",
                "trend_score": 0.68,
                "article_count": 54,
                "sources_count": 8,
                "time_period": "24h"
            },
            {
                "topic": "healthcare AI",
                "topic_category": "health",
                "trend_score": 0.65,
                "article_count": 48,
                "sources_count": 7,
                "time_period": "24h"
            },
            {
                "topic": "machine learning",
                "topic_category": "artificial-intelligence",
                "trend_score": 0.62,
                "article_count": 89,
                "sources_count": 11,
                "time_period": "24h"
            },
            {
                "topic": "deep learning",
                "topic_category": "artificial-intelligence",
                "trend_score": 0.60,
                "article_count": 67,
                "sources_count": 9,
                "time_period": "24h"
            }
        ]
        
        for topic_data in trending_topics:
            # Verificar si ya existe
            existing = db.query(TrendingTopic).filter(
                and_(
                    TrendingTopic.topic == topic_data["topic"],
                    TrendingTopic.time_period == topic_data["time_period"]
                )
            ).first()
            
            if not existing:
                trending_topic = TrendingTopic(
                    date_recorded=datetime.utcnow(),
                    metadata={
                        "initial_data": True,
                        "sample_data": True
                    },
                    **topic_data
                )
                db.add(trending_topic)
                logger.info(f"Creado trending topic: {topic_data['topic']}")
    
    def _create_sample_analysis(self, db, articles: List[Article]):
        """Crear análisis de ejemplo para artículos"""
        logger.info("Creando análisis de ejemplo")
        
        analysis_types = [
            "sentiment",
            "summary", 
            "topics",
            "relevance",
            "bias"
        ]
        
        for article in articles[:5]:  # Solo primeros 5 artículos
            for analysis_type in analysis_types:
                existing = db.query(ArticleAnalysis).filter(
                    and_(
                        ArticleAnalysis.article_id == article.id,
                        ArticleAnalysis.analysis_type == analysis_type
                    )
                ).first()
                
                if not existing:
                    analysis_data = self._get_sample_analysis_data(article, analysis_type)
                    
                    analysis = ArticleAnalysis(
                        article_id=article.id,
                        analysis_type=analysis_type,
                        analysis_data=analysis_data,
                        model_used=f"sample_model_{analysis_type}",
                        confidence_score=0.85,
                        processed_at=datetime.utcnow()
                    )
                    db.add(analysis)
        
        logger.info("Análisis de ejemplo creados")
    
    def _get_sample_analysis_data(self, article: Article, analysis_type: str) -> Dict[str, Any]:
        """Generar datos de análisis de ejemplo"""
        if analysis_type == "sentiment":
            return {
                "sentiment": article.sentiment_label,
                "score": article.sentiment_score,
                "confidence": 0.85
            }
        elif analysis_type == "summary":
            return {
                "summary": article.summary,
                "key_points": [
                    "Main development in AI technology",
                    "Significant performance improvements",
                    "Potential industry applications"
                ],
                "word_count": len(article.summary.split()) if article.summary else 0
            }
        elif analysis_type == "topics":
            return {
                "topics": article.topic_tags or [],
                "topic_scores": {tag: 0.8 for tag in (article.topic_tags or [])},
                "primary_topic": (article.topic_tags[0] if article.topic_tags else "general")
            }
        elif analysis_type == "relevance":
            return {
                "score": article.relevance_score,
                "factors": ["recency", "source_authority", "topic_match"],
                "explanation": f"High relevance due to current date and authoritative source"
            }
        elif analysis_type == "bias":
            return {
                "bias_score": article.bias_score,
                "bias_factors": ["source_perspective", "language_analysis"],
                "interpretation": "Low to moderate bias detected",
                "confidence": 0.75
            }
        
        return {}
    
    def _create_sample_user_preferences(self, db):
        """Crear preferencias de usuario de ejemplo"""
        logger.info("Creando preferencias de usuario de ejemplo")
        
        sample_users = [
            {
                "user_id": "demo_user_1",
                "preferred_sources": ["TechCrunch", "MIT Technology Review", "Wired"],
                "preferred_topics": ["artificial-intelligence", "machine-learning", "startup"],
                "sentiment_preference": "positive",
                "reading_level": "mixed",
                "notification_frequency": "daily"
            },
            {
                "user_id": "demo_user_2", 
                "preferred_sources": ["BBC Technology", "Ars Technica"],
                "preferred_topics": ["quantum-computing", "hardware", "research"],
                "sentiment_preference": "all",
                "reading_level": "complex",
                "notification_frequency": "weekly"
            }
        ]
        
        for user_data in sample_users:
            # Verificar si ya existe
            existing = db.query(UserPreference).filter(
                UserPreference.user_id == user_data["user_id"]
            ).first()
            
            if not existing:
                preference = UserPreference(**user_data)
                db.add(preference)
                logger.info(f"Creada preferencia para usuario: {user_data['user_id']}")
    
    def clear_search_data(self):
        """Limpiar datos de búsqueda (para resets)"""
        db = self.SessionLocal()
        
        try:
            logger.info("Limpiando datos de búsqueda")
            
            # Eliminar trending topics
            db.query(TrendingTopic).delete()
            logger.info("Trending topics eliminados")
            
            # Eliminar análisis
            db.query(ArticleAnalysis).delete()
            logger.info("Análisis eliminados")
            
            # Eliminar preferencias
            db.query(UserPreference).delete()
            logger.info("Preferencias eliminadas")
            
            # Eliminar artículos de ejemplo
            sample_urls = [
                "https://techcrunch.com/openai-gpt5-multimodal",
                "https://technologyreview.com/google-gemini-ultra",
                "https://wired.com/meta-ai-breakthrough",
                "https://theverge.com/tesla-fsd-approval",
                "https://arstechnica.com/anthropic-claude-healthcare",
                "https://bbc.com/technology/microsoft-copilot-robotics",
                "https://cnn.com/tech/ibm-quantum-processor"
            ]
            
            deleted_articles = db.query(Article).filter(Article.url.in_(sample_urls)).delete(synchronize_session=False)
            logger.info(f"Artículos eliminados: {deleted_articles}")
            
            db.commit()
            logger.info("Datos de búsqueda limpiados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"Error limpiando datos: {str(e)}")
            db.rollback()
            return False
        finally:
            db.close()


def main():
    """Función principal para ejecutar desde línea de comandos"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Inicializar datos para sistema de búsqueda")
    parser.add_argument("--clear", action="store_true", help="Limpiar datos existentes")
    parser.add_argument("--db-url", help="URL de base de datos personalizada")
    
    args = parser.parse_args()
    
    initializer = SearchDataInitializer(args.db_url)
    
    if args.clear:
        success = initializer.clear_search_data()
        if success:
            print("Datos limpiados correctamente")
            return
        else:
            print("Error limpiando datos")
            return
    
    success = initializer.initialize_data()
    
    if success:
        print("Datos inicializados correctamente para el sistema de búsqueda")
        print("\nEndpoints disponibles:")
        print("- GET /search - Búsqueda avanzada")
        print("- GET /search/suggestions - Sugerencias de búsqueda")
        print("- GET /search/trending - Búsquedas populares")
        print("- GET /search/filters - Filtros disponibles")
        print("- GET /search/semantic - Búsqueda semántica")
        print("\nEjemplos de queries:")
        print("- /search?q=artificial intelligence&sentiment=positive")
        print("- /search?q=quantum&min_relevance=0.8&sort=date")
        print("- /search/trending?timeframe=24h&limit=10")
    else:
        print("Error inicializando datos")


if __name__ == "__main__":
    main()