"""
Sistema de deduplicación inteligente para artículos de noticias
Implementa algoritmos para detectar artículos duplicados por:
- Similaridad del título (fuzzy matching)
- URL
- Contenido
"""

import re
import hashlib
from typing import List, Dict, Optional, Tuple, Set
from datetime import datetime, timedelta
from urllib.parse import urlparse, urljoin
from difflib import SequenceMatcher

from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func
from loguru import logger

from ..db.models import Article, Source


class DuplicateDetector:
    """Detector inteligente de artículos duplicados"""
    
    def __init__(self, similarity_threshold: float = 0.85, max_age_days: int = 7):
        """
        Inicializar el detector de duplicados
        
        Args:
            similarity_threshold: Umbral de similaridad (0.0 a 1.0)
            max_age_days: Días máximo a considerar para deduplicación
        """
        self.similarity_threshold = similarity_threshold
        self.max_age_days = max_age_days
        self.min_title_length = 10
        
    def detect_duplicates(self, db: Session, new_article: Dict) -> List[Dict]:
        """
        Detecta artículos duplicados en la base de datos
        
        Args:
            db: Sesión de base de datos
            new_article: Diccionario con datos del nuevo artículo
            
        Returns:
            Lista de artículos duplicados encontrados
        """
        duplicates = []
        
        try:
            # 1. Verificar duplicados por URL exacta
            url_duplicates = self._find_url_duplicates(db, new_article.get('url', ''))
            duplicates.extend(url_duplicates)
            
            # 2. Verificar duplicados por título similar
            title_duplicates = self._find_title_duplicates(db, new_article.get('title', ''))
            duplicates.extend(title_duplicates)
            
            # 3. Verificar duplicados por contenido similar (solo si no hay coincidencias fuertes)
            if len(duplicates) < 2:
                content_duplicates = self._find_content_duplicates(db, new_article.get('content', ''))
                duplicates.extend(content_duplicates)
            
            # 4. Eliminar duplicados de la lista final
            final_duplicates = self._deduplicate_results(duplicates)
            
            logger.info(f"Encontrados {len(final_duplicates)} artículos duplicados")
            return final_duplicates
            
        except Exception as e:
            logger.error(f"Error detectando duplicados: {str(e)}")
            return []
    
    def _find_url_duplicates(self, db: Session, url: str) -> List[Dict]:
        """Encuentra duplicados por URL exacta"""
        if not url:
            return []
            
        articles = db.query(Article).filter(
            and_(
                Article.url == url,
                Article.created_at >= datetime.utcnow() - timedelta(days=self.max_age_days)
            )
        ).all()
        
        return [
            {
                'article': article,
                'duplicate_type': 'url_exact',
                'similarity_score': 1.0,
                'match_reason': 'URL idéntica'
            }
            for article in articles
        ]
    
    def _find_title_duplicates(self, db: Session, title: str) -> List[Dict]:
        """Encuentra duplicados por título similar usando fuzzy matching"""
        if not title or len(title.strip()) < self.min_title_length:
            return []
            
        # Buscar artículos recientes
        recent_articles = db.query(Article).filter(
            and_(
                Article.created_at >= datetime.utcnow() - timedelta(days=self.max_age_days),
                Article.title.isnot(None)
            )
        ).all()
        
        title_duplicates = []
        clean_title = self._clean_text_for_comparison(title)
        
        for article in recent_articles:
            if not article.title:
                continue
                
            article_clean_title = self._clean_text_for_comparison(article.title)
            
            # Usar múltiples algoritmos de fuzzy matching
            ratio_score = fuzz.ratio(clean_title, article_clean_title) / 100.0
            partial_score = fuzz.partial_ratio(clean_title, article_clean_title) / 100.0
            token_sort_score = fuzz.token_sort_ratio(clean_title, article_clean_title) / 100.0
            
            # Usar el mejor score
            max_score = max(ratio_score, partial_score, token_sort_score)
            
            if max_score >= self.similarity_threshold:
                title_duplicates.append({
                    'article': article,
                    'duplicate_type': 'title_similar',
                    'similarity_score': max_score,
                    'match_reason': f'Título similar ({max_score:.2f})'
                })
        
        return title_duplicates
    
    def _find_content_duplicates(self, db: Session, content: str) -> List[Dict]:
        """Encuentra duplicados por contenido similar"""
        if not content or len(content.strip()) < 100:
            return []
            
        # Extraer características del contenido (primeras oraciones)
        content_features = self._extract_content_features(content)
        if len(content_features) < 10:
            return []
            
        # Buscar artículos con contenido sustancial
        recent_articles = db.query(Article).filter(
            and_(
                Article.created_at >= datetime.utcnow() - timedelta(days=self.max_age_days),
                func.length(Article.content) >= 100  # Solo artículos con contenido sustancial
            )
        ).all()
        
        content_duplicates = []
        new_article_hash = self._generate_content_hash(content_features)
        
        for article in recent_articles:
            if not article.content or len(article.content.strip()) < 100:
                continue
                
            article_features = self._extract_content_features(article.content)
            if len(article_features) < 10:
                continue
                
            article_hash = self._generate_content_hash(article_features)
            
            # Comparar características del contenido
            similarity = self._calculate_content_similarity(content_features, article_features)
            
            if similarity >= 0.7:  # Umbral más bajo para contenido
                content_duplicates.append({
                    'article': article,
                    'duplicate_type': 'content_similar',
                    'similarity_score': similarity,
                    'match_reason': f'Contenido similar ({similarity:.2f})'
                })
        
        return content_duplicates
    
    def _deduplicate_results(self, duplicates: List[Dict]) -> List[Dict]:
        """Elimina duplicados de los resultados de detección"""
        seen_article_ids = set()
        final_duplicates = []
        
        # Ordenar por similarity_score (descendente)
        duplicates.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        for duplicate in duplicates:
            article_id = duplicate['article'].id
            if article_id not in seen_article_ids:
                seen_article_ids.add(article_id)
                final_duplicates.append(duplicate)
        
        return final_duplicates
    
    def _clean_text_for_comparison(self, text: str) -> str:
        """Limpia texto para comparación fuzzy"""
        if not text:
            return ""
            
        # Convertir a minúsculas
        text = text.lower()
        
        # Remover caracteres especiales y normalizar espacios
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remover palabras muy comunes (stopwords básicas)
        stopwords = {'el', 'la', 'de', 'que', 'y', 'a', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 
                    'le', 'da', 'su', 'por', 'son', 'con', 'para', 'al', 'del', 'los', 'las', 'the', 
                    'of', 'and', 'a', 'in', 'to', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on',
                    'are', 'as', 'with', 'his', 'they', 'i', 'at', 'be', 'this', 'have', 'from'}
        
        words = text.split()
        words = [word for word in words if word not in stopwords and len(word) > 2]
        
        return ' '.join(words)
    
    def _extract_content_features(self, content: str) -> List[str]:
        """Extrae características del contenido para comparación"""
        if not content:
            return []
            
        # Tomar las primeras oraciones como características
        sentences = re.split(r'[.!?]+', content.strip())
        features = []
        
        for sentence in sentences[:5]:  # Primeras 5 oraciones
            # Limpiar y extraer palabras clave
            clean_sentence = self._clean_text_for_comparison(sentence)
            if len(clean_sentence.split()) >= 3:
                features.append(clean_sentence)
        
        return features
    
    def _generate_content_hash(self, features: List[str]) -> str:
        """Genera hash de características del contenido"""
        # Concatenar características y generar hash
        features_text = '|'.join(sorted(features))
        return hashlib.md5(features_text.encode()).hexdigest()
    
    def _calculate_content_similarity(self, features1: List[str], features2: List[str]) -> float:
        """Calcula similitud entre características de contenido"""
        if not features1 or not features2:
            return 0.0
            
        # Comparar oraciones usando fuzzy matching
        similarities = []
        
        for f1 in features1:
            best_similarity = 0.0
            for f2 in features2:
                similarity = fuzz.ratio(f1, f2) / 100.0
                best_similarity = max(best_similarity, similarity)
            similarities.append(best_similarity)
        
        # Retornar promedio de similitudes
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _normalize_url(self, url: str) -> str:
        """Normaliza URL para comparación más precisa"""
        if not url:
            return ""
            
        try:
            parsed = urlparse(url)
            
            # Remover parámetros de query y fragmentos
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Normalizar trailing slash
            if normalized.endswith('/') and len(parsed.path) > 1:
                normalized = normalized[:-1]
                
            # Convertir a minúsculas
            return normalized.lower()
            
        except Exception:
            return url.lower()
    
    def is_duplicate(self, db: Session, new_article: Dict) -> Tuple[bool, Optional[str]]:
        """
        Determina si un artículo es duplicado y devuelve el motivo
        
        Returns:
            Tupla (is_duplicate, reason)
        """
        duplicates = self.detect_duplicates(db, new_article)
        
        if not duplicates:
            return False, None
            
        # Si hay duplicados con alta confianza
        high_confidence_duplicates = [d for d in duplicates if d['similarity_score'] > 0.9]
        if high_confidence_duplicates:
            return True, f"Duplicado confirmado: {high_confidence_duplicates[0]['match_reason']}"
            
        # Si hay múltiples duplicados de menor confianza
        if len(duplicates) > 1:
            avg_score = sum(d['similarity_score'] for d in duplicates) / len(duplicates)
            if avg_score > 0.8:
                return True, f"Posible duplicado: {len(duplicates)} artículos similares (promedio: {avg_score:.2f})"
        
        return False, None
    
    def merge_articles(self, db: Session, primary_article: Article, 
                      duplicate_articles: List[Dict]) -> Article:
        """
        Fusiona artículos duplicados manteniendo la mejor información
        
        Args:
            db: Sesión de base de datos
            primary_article: Artículo principal (no duplicado)
            duplicate_articles: Lista de artículos duplicados a fusionar
            
        Returns:
            Artículo fusionado
        """
        try:
            # Combinar contenido: tomar el más completo
            content_sources = [primary_article.content] + [
                d['article'].content for d in duplicate_articles 
                if d['article'].content and len(d['article'].content) > len(primary_article.content or "")
            ]
            
            if content_sources:
                # Tomar el contenido más largo (asumiendo que es más completo)
                primary_article.content = max(content_sources, key=len)
            
            # Actualizar título si hay uno mejor (más descriptivo)
            for duplicate_data in duplicate_articles:
                duplicate = duplicate_data['article']
                if self._is_title_better(duplicate.title, primary_article.title):
                    primary_article.title = duplicate.title
            
            # Combinar metadatos si existen
            if not primary_article.summary and any(d['article'].summary for d in duplicate_articles):
                summaries = [d['article'].summary for d in duplicate_articles if d['article'].summary]
                primary_article.summary = max(summaries, key=len)
            
            # Marcar artículos fusionados como duplicados (soft delete)
            for duplicate_data in duplicate_articles:
                duplicate_article = duplicate_data['article']
                duplicate_article.title = f"[DUPLICADO] {duplicate_article.title}"
                duplicate_article.url = f"{duplicate_article.url}?duplicate_of={primary_article.id}"
            
            db.commit()
            logger.info(f"Fusionados {len(duplicate_articles)} artículos duplicados")
            
        except Exception as e:
            logger.error(f"Error fusionando artículos: {str(e)}")
            db.rollback()
            raise
        
        return primary_article
    
    def _is_title_better(self, title1: str, title2: str) -> bool:
        """Determina si un título es mejor que otro"""
        if not title1:
            return False
        if not title2:
            return True
            
        # Criterios para determinar mejor título:
        # 1. Más largo (más descriptivo)
        # 2. Menos palabras de relleno
        # 3. Contiene más información específica
        
        score1 = self._calculate_title_quality(title1)
        score2 = self._calculate_title_quality(title2)
        
        return score1 > score2
    
    def _calculate_title_quality(self, title: str) -> float:
        """Calcula calidad del título (0.0 a 1.0)"""
        if not title:
            return 0.0
            
        score = 0.0
        
        # Longitud: títulos muy cortos (< 20 chars) son menos informativos
        length = len(title)
        if 30 <= length <= 100:
            score += 0.3
        elif 20 <= length < 30 or 100 < length <= 150:
            score += 0.2
        elif 10 <= length < 20:
            score += 0.1
        
        # Presencia de números (más específico)
        if re.search(r'\d', title):
            score += 0.1
        
        # Presencia de palabras específicas vs genéricas
        specific_words = ['anuncia', 'revelar', 'descubre', 'estudia', 'informe', 
                         'study', 'research', 'report', 'announces', 'reveals']
        word_score = sum(1 for word in specific_words if word.lower() in title.lower()) / len(specific_words)
        score += word_score * 0.3
        
        # Evitar títulos muy genéricos
        generic_patterns = ['sin título', 'sin titulo', 'untitled', 'no title', 'undefined']
        if any(pattern in title.lower() for pattern in generic_patterns):
            score -= 0.5
        
        return max(0.0, min(1.0, score))