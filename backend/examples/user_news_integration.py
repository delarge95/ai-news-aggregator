"""
Ejemplo de integración entre endpoints de usuarios y servicio de noticias
Demuestra cómo usar las preferencias del usuario para personalizar las noticias
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.services import news_service
from app.db.models import User, UserPreference, Article
from app.api.v1.endpoints.users import get_current_user
from app.db.database import get_db

router = APIRouter()


@router.get("/personalized-news")
async def get_personalized_news(
    limit: Optional[int] = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener noticias personalizadas basadas en las preferencias del usuario
    """
    # Obtener preferencias del usuario
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    if not preferences:
        # Usar preferencias por defecto si no existen
        preferences = UserPreference(
            preferred_sources=[],
            blocked_sources=[],
            preferred_topics=[],
            ignored_topics=[],
            sentiment_preference='all',
            reading_level='mixed'
        )
    
    # Configurar filtros basados en preferencias
    filters = {
        'preferred_sources': preferences.preferred_sources or [],
        'blocked_sources': preferences.blocked_sources or [],
        'preferred_topics': preferences.preferred_topics or [],
        'ignored_topics': preferences.ignored_topics or [],
        'sentiment_preference': preferences.sentiment_preference,
        'reading_level': preferences.reading_level,
        'limit': limit
    }
    
    try:
        # Obtener noticias usando el servicio con filtros personalizados
        articles = await news_service.get_personalized_news(
            user_id=current_user.id,
            **filters
        )
        
        return {
            "status": "success",
            "message": f"Personalized news for user {current_user.username}",
            "total": len(articles),
            "preferences_applied": {
                "preferred_sources": filters['preferred_sources'],
                "preferred_topics": filters['preferred_topics'],
                "sentiment_filter": filters['sentiment_preference'],
                "reading_level": filters['reading_level']
            },
            "articles": articles
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching personalized news: {str(e)}")


@router.get("/recommended-news")
async def get_recommended_news(
    limit: Optional[int] = 10,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Obtener noticias recomendadas basadas en:
    1. Preferencias del usuario
    2. Artículos que ha marcado como favoritos
    3. Análisis de patrones de lectura
    """
    
    # Obtener preferencias del usuario
    result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = result.scalar_one_or_none()
    
    # Obtener temas de artículos guardados (bookmarks)
    from app.db.models import UserBookmark
    bookmarks_result = await db.execute(
        select(UserBookmark).where(UserBookmark.user_id == current_user.id)
    )
    bookmarks = bookmarks_result.scalars().all()
    
    # Analizar temas de interés basados en bookmarks
    interest_topics = set()
    for bookmark in bookmarks:
        if bookmark.tags:
            interest_topics.update(bookmark.tags)
    
    # Combinar temas de preferencias con temas de bookmarks
    all_topics = set()
    if preferences and preferences.preferred_topics:
        all_topics.update(preferences.preferred_topics)
    all_topics.update(interest_topics)
    
    try:
        # Obtener noticias recomendadas
        recommended_articles = await news_service.get_recommended_news(
            user_id=current_user.id,
            interest_topics=list(all_topics),
            limit=limit,
            exclude_bookmarked=True  # No incluir artículos ya guardados
        )
        
        return {
            "status": "success",
            "message": f"Recommended news for user {current_user.username}",
            "total": len(recommended_articles),
            "recommendation_basis": {
                "user_preferences": preferences.preferred_topics if preferences else [],
                "bookmark_topics": list(interest_topics),
                "combined_interests": list(all_topics)
            },
            "articles": recommended_articles
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommended news: {str(e)}")


@router.post("/news/{article_id}/bookmark")
async def bookmark_article(
    article_id: str,
    notes: Optional[str] = None,
    tags: Optional[List[str]] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Guardar un artículo con análisis automático de temas
    """
    # Obtener información del artículo
    article_result = await db.execute(
        select(Article).where(Article.id == article_id)
    )
    article = article_result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    # Analizar automáticamente tags del artículo si no se proporcionan
    if not tags:
        tags = []
        # Agregar tags del análisis de IA del artículo
        if article.topic_tags:
            tags.extend(article.topic_tags)
        
        # Agregar tags basados en el sentimiento
        if article.sentiment_label:
            tags.append(f"sentiment_{article.sentiment_label}")
        
        # Agregar tags basados en el título (ejemplo simple)
        title_lower = article.title.lower()
        if 'ai' in title_lower or 'inteligencia artificial' in title_lower:
            tags.append('artificial-intelligence')
        if 'machine learning' in title_lower or 'machine-learning' in title_lower:
            tags.append('machine-learning')
        if 'tecnolog' in title_lower:
            tags.append('technology')
    
    # Crear bookmark
    from app.db.models import UserBookmark
    bookmark = UserBookmark(
        user_id=current_user.id,
        article_id=article_id,
        title=article.title,
        url=article.url,
        notes=notes,
        tags=tags
    )
    
    # Verificar si ya existe
    existing = await db.execute(
        select(UserBookmark).where(
            UserBookmark.user_id == current_user.id,
            UserBookmark.article_id == article_id
        )
    )
    
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Article already bookmarked")
    
    db.add(bookmark)
    await db.commit()
    await db.refresh(bookmark)
    
    return {
        "status": "success",
        "message": "Article bookmarked successfully",
        "bookmark": {
            "id": str(bookmark.id),
            "title": bookmark.title,
            "tags": bookmark.tags,
            "auto_generated_tags": len(tags) > (len(article.topic_tags) if article.topic_tags else 0)
        }
    }


@router.get("/news/preferences-analysis")
async def analyze_user_news_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analizar las preferencias de noticias del usuario y sugerir mejoras
    """
    # Obtener preferencias actuales
    preferences_result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = preferences_result.scalar_one_or_none()
    
    # Obtener bookmarks para análisis
    bookmarks_result = await db.execute(
        select(UserBookmark).where(UserBookmark.user_id == current_user.id)
    )
    bookmarks = bookmarks_result.scalars().all()
    
    # Analizar patrones
    analysis = {
        "user_profile": {
            "username": current_user.username,
            "account_age_days": (current_user.created_at).days if current_user.created_at else 0,
            "total_bookmarks": len(bookmarks),
            "last_activity": current_user.last_login
        },
        "preferences_analysis": {
            "has_preferred_sources": bool(preferences.preferred_sources if preferences else False),
            "has_blocked_sources": bool(preferences.blocked_sources if preferences else False),
            "preferred_topics_count": len(preferences.preferred_topics) if preferences and preferences.preferred_topics else 0,
            "sentiment_preference": preferences.sentiment_preference if preferences else "all",
            "reading_level": preferences.reading_level if preferences else "mixed"
        },
        "bookmark_analysis": {
            "most_common_tags": {},
            "reading_patterns": {},
            "source_distribution": {}
        },
        "suggestions": []
    }
    
    # Analizar tags de bookmarks
    from collections import Counter
    all_tags = []
    for bookmark in bookmarks:
        if bookmark.tags:
            all_tags.extend(bookmark.tags)
    
    if all_tags:
        tag_counts = Counter(all_tags)
        analysis["bookmark_analysis"]["most_common_tags"] = dict(tag_counts.most_common(10))
    
    # Generar sugerencias
    suggestions = []
    
    if len(bookmarks) < 5:
        suggestions.append("Start bookmarking articles you find interesting to improve recommendations")
    
    if not preferences or not preferences.preferred_topics:
        suggestions.append("Set your preferred topics to get more relevant news recommendations")
    
    if preferences and len(preferences.preferred_sources) < 2:
        suggestions.append("Consider adding more news sources to diversify your news feed")
    
    if all_tags:
        top_tags = list(Counter(all_tags).keys())[:5]
        if not preferences or not set(top_tags).intersection(set(preferences.preferred_topics or [])):
            suggestions.append(f"Your bookmarked articles often cover: {', '.join(top_tags[:3])}. Consider adding these topics to your preferences")
    
    analysis["suggestions"] = suggestions
    
    return {
        "status": "success",
        "analysis": analysis
    }


@router.post("/news/preferences/optimize")
async def optimize_user_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Optimizar automáticamente las preferencias del usuario basado en sus bookmarks
    """
    # Obtener bookmarks
    bookmarks_result = await db.execute(
        select(UserBookmark).where(UserBookmark.user_id == current_user.id)
    )
    bookmarks = bookmarks_result.scalars().all()
    
    if len(bookmarks) < 3:
        raise HTTPException(
            status_code=400, 
            detail="Need at least 3 bookmarks to optimize preferences"
        )
    
    # Analizar patrones
    from collections import Counter
    
    # Recopilar todos los tags
    all_tags = []
    for bookmark in bookmarks:
        if bookmark.tags:
            all_tags.extend(bookmark.tags)
    
    if not all_tags:
        return {"message": "No tags found in bookmarks to optimize preferences"}
    
    # Obtener tags más frecuentes
    tag_counts = Counter(all_tags)
    frequent_tags = [tag for tag, count in tag_counts.most_common(10) if count >= 2]
    
    # Obtener preferencias actuales
    preferences_result = await db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    )
    preferences = preferences_result.scalar_one_or_none()
    
    if not preferences:
        preferences = UserPreference(user_id=current_user.id)
        db.add(preferences)
    
    # Optimizar preferencias
    current_topics = set(preferences.preferred_topics or [])
    optimized_topics = list(current_topics.union(set(frequent_tags)))
    
    preferences.preferred_topics = optimized_topics[:15]  # Límite de 15 temas
    preferences.updated_at = current_user.updated_at
    
    await db.commit()
    
    return {
        "status": "success",
        "message": "Preferences optimized based on your bookmarks",
        "optimization_details": {
            "previous_topics_count": len(current_topics),
            "new_topics_count": len(optimized_topics),
            "added_topics": list(set(optimized_topics) - current_topics),
            "total_bookmarks_analyzed": len(bookmarks)
        }
    }