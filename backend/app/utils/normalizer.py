"""
Sistema de normalización de datos para el agregador de noticias AI
Unifica el formato de datos de diferentes fuentes y proporciona:
- Limpieza de texto
- Extracción de metadatos
- Validación de datos
- Normalización de formatos
"""

import re
import html
import json
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timezone
from urllib.parse import urlparse
from html.parser import HTMLParser
import hashlib
import logging

from ..db.models import Article, Source


class HTMLTextExtractor(HTMLParser):
    """Extractor de texto limpio de HTML"""
    
    def __init__(self):
        super().__init__()
        self.text_parts = []
        
    def handle_data(self, data):
        if data.strip():
            self.text_parts.append(data.strip())
    
    def get_text(self):
        return ' '.join(self.text_parts)


class NewsNormalizer:
    """Normalizador inteligente para datos de noticias de múltiples fuentes"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Patrones de normalización
        self.cleaning_patterns = {
            'whitespace': re.compile(r'\s+'),
            'html_entities': re.compile(r'&[a-zA-Z0-9#]+;'),
            'special_chars': re.compile(r'[^\w\s\-\.,!?;:()\'"/]'),
            'excessive_newlines': re.compile(r'\n{3,}'),
            'excessive_spaces': re.compile(r' {2,}'),
        }
        
        # Fuentes de noticias soportadas y sus formatos
        self.supported_sources = {
            'newsapi': self._normalize_newsapi,
            'guardian': self._normalize_guardian,
            'nytimes': self._normalize_nytimes,
            'reuters': self._normalize_reuters,
            'bbc': self._normalize_bbc,
            'cnn': self._normalize_cnn,
            'associated_press': self._normalize_associated_press,
            'generic': self._normalize_generic
        }
        
    def normalize_article(self, raw_data: Dict, source_type: str = 'generic') -> Optional[Dict]:
        """
        Normaliza datos de artículo crudo a formato estándar
        
        Args:
            raw_data: Datos crudos del artículo
            source_type: Tipo de fuente ('newsapi', 'guardian', etc.)
            
        Returns:
            Diccionario con datos normalizados o None si hay errores
        """
        try:
            # Validar datos de entrada
            if not self._validate_raw_data(raw_data):
                self.logger.warning("Datos crudos inválidos")
                return None
            
            # Seleccionar normalizador específico por tipo de fuente
            normalizer = self.supported_sources.get(source_type, self._normalize_generic)
            
            # Normalizar según el tipo de fuente
            normalized_data = normalizer(raw_data)
            
            # Aplicar limpieza general de texto
            normalized_data = self._apply_general_cleaning(normalized_data)
            
            # Extraer metadatos adicionales
            normalized_data = self._extract_metadata(normalized_data)
            
            # Validar datos normalizados
            if self._validate_normalized_data(normalized_data):
                return normalized_data
            else:
                self.logger.warning("Datos normalizados no pasaron validación")
                return None
                
        except Exception as e:
            self.logger.error(f"Error normalizando artículo: {str(e)}")
            return None
    
    def _validate_raw_data(self, raw_data: Dict) -> bool:
        """Valida que los datos crudos tengan campos mínimos requeridos"""
        required_fields = ['title']
        
        for field in required_fields:
            if field not in raw_data or not raw_data[field]:
                return False
        
        return True
    
    def _validate_normalized_data(self, data: Dict) -> bool:
        """Valida que los datos normalizados sean correctos"""
        required_fields = ['title', 'url', 'source_name']
        
        for field in required_fields:
            if field not in data or not data[field]:
                return False
        
        # Validar URL
        if not self._is_valid_url(data.get('url', '')):
            return False
        
        # Validar título
        title = data.get('title', '')
        if len(title.strip()) < 5 or len(title.strip()) > 500:
            return False
        
        return True
    
    def _normalize_newsapi(self, raw_data: Dict) -> Dict:
        """Normaliza datos de NewsAPI"""
        return {
            'title': self._clean_text(raw_data.get('title', '')),
            'content': self._clean_text(raw_data.get('content', '')),
            'description': self._clean_text(raw_data.get('description', '')),
            'url': raw_data.get('url', ''),
            'published_at': self._parse_datetime(raw_data.get('publishedAt')),
            'source_name': raw_data.get('source', {}).get('name', ''),
            'author': raw_data.get('author', ''),
            'image_url': raw_data.get('urlToImage', '')
        }
    
    def _normalize_guardian(self, raw_data: Dict) -> Dict:
        """Normaliza datos de The Guardian API"""
        fields = raw_data.get('fields', {})
        
        return {
            'title': self._clean_text(raw_data.get('webTitle', '')),
            'content': self._clean_text(fields.get('bodyText', '')),
            'description': self._clean_text(fields.get('trailText', '')),
            'url': raw_data.get('webUrl', ''),
            'published_at': self._parse_datetime(raw_data.get('webPublicationDate')),
            'source_name': 'The Guardian',
            'author': fields.get('byline', ''),
            'image_url': fields.get('thumbnail', '')
        }
    
    def _normalize_nytimes(self, raw_data: Dict) -> Dict:
        """Normaliza datos de New York Times API"""
        headline = raw_data.get('headline', {})
        pub_date = raw_data.get('pub_date', '')
        
        return {
            'title': self._clean_text(headline.get('main', '')),
            'content': self._extract_text_from_paragraphs(raw_data.get('abstract', '') + ' ' + 
                     raw_data.get('lead_paragraph', '')),
            'description': self._clean_text(raw_data.get('snippet', '')),
            'url': raw_data.get('web_url', ''),
            'published_at': self._parse_datetime(pub_date),
            'source_name': 'The New York Times',
            'author': ', '.join(raw_data.get('byline', {}).get('person', [])),
            'image_url': raw_data.get('multimedia', [{}])[0].get('url', '') if raw_data.get('multimedia') else ''
        }
    
    def _normalize_reuters(self, raw_data: Dict) -> Dict:
        """Normaliza datos de Reuters"""
        content = raw_data.get('content', {})
        
        return {
            'title': self._clean_text(content.get('title', '')),
            'content': self._extract_text_from_paragraphs(content.get('body', '')),
            'description': self._clean_text(raw_data.get('summary', '')),
            'url': raw_data.get('url', ''),
            'published_at': self._parse_datetime(raw_data.get('publishedTime')),
            'source_name': 'Reuters',
            'author': content.get('byline', ''),
            'image_url': content.get('media', [{}])[0].get('url', '') if content.get('media') else ''
        }
    
    def _normalize_bbc(self, raw_data: Dict) -> Dict:
        """Normaliza datos de BBC"""
        fields = raw_data.get('fields', {})
        
        return {
            'title': self._clean_text(raw_data.get('webTitle', '')),
            'content': self._clean_text(fields.get('bodyText', '')),
            'description': self._clean_text(raw_data.get('trailText', '')),
            'url': raw_data.get('webUrl', ''),
            'published_at': self._parse_datetime(raw_data.get('webPublicationDate')),
            'source_name': 'BBC News',
            'author': fields.get('byline', ''),
            'image_url': fields.get('thumbnail', '')
        }
    
    def _normalize_cnn(self, raw_data: Dict) -> Dict:
        """Normaliza datos de CNN"""
        return {
            'title': self._clean_text(raw_data.get('title', '')),
            'content': self._clean_text(raw_data.get('content', '')),
            'description': self._clean_text(raw_data.get('description', '')),
            'url': raw_data.get('url', ''),
            'published_at': self._parse_datetime(raw_data.get('publishedAt')),
            'source_name': 'CNN',
            'author': raw_data.get('author', ''),
            'image_url': raw_data.get('image_url', '')
        }
    
    def _normalize_associated_press(self, raw_data: Dict) -> Dict:
        """Normaliza datos de Associated Press"""
        return {
            'title': self._clean_text(raw_data.get('title', '')),
            'content': self._extract_text_from_paragraphs(raw_data.get('content', {}).get('paragraph', [])),
            'description': self._clean_text(raw_data.get('description', '')),
            'url': raw_data.get('url', ''),
            'published_at': self._parse_datetime(raw_data.get('publishedAt')),
            'source_name': 'Associated Press',
            'author': raw_data.get('author', ''),
            'image_url': raw_data.get('image', {}).get('url', '') if raw_data.get('image') else ''
        }
    
    def _normalize_generic(self, raw_data: Dict) -> Dict:
        """Normalizador genérico para fuentes no específicas"""
        return {
            'title': self._clean_text(raw_data.get('title', '')),
            'content': self._clean_text(raw_data.get('content', '') or raw_data.get('body', '')),
            'description': self._clean_text(raw_data.get('description', '') or raw_data.get('summary', '')),
            'url': raw_data.get('url', ''),
            'published_at': self._parse_datetime(raw_data.get('published_at') or raw_data.get('publishedAt') or 
                                                raw_data.get('date')),
            'source_name': raw_data.get('source', '') or raw_data.get('source_name', ''),
            'author': raw_data.get('author', '') or raw_data.get('byline', ''),
            'image_url': raw_data.get('image', '') or raw_data.get('image_url', '') or 
                        raw_data.get('thumbnail', '')
        }
    
    def _clean_text(self, text: str) -> str:
        """Limpia y normaliza texto"""
        if not text:
            return ""
        
        # Decodificar entidades HTML
        text = html.unescape(text)
        
        # Remover HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Limpiar patrones no deseados
        for pattern_name, pattern in self.cleaning_patterns.items():
            text = pattern.sub(' ', text)
        
        # Limpiar caracteres de control
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\t\n\r')
        
        # Limpiar espacios en blanco extremos
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Remover espacios al inicio y final
        text = text.strip()
        
        return text
    
    def _extract_text_from_paragraphs(self, content) -> str:
        """Extrae texto de diferentes formatos de párrafo"""
        if isinstance(content, list):
            # Lista de párrafos
            return ' '.join(str(p) for p in content)
        elif isinstance(content, str):
            # Ya es texto plano
            return content
        else:
            return str(content) if content else ""
    
    def _parse_datetime(self, date_string: str) -> Optional[datetime]:
        """Convierte diferentes formatos de fecha a datetime"""
        if not date_string:
            return None
        
        # Patrones de fecha comunes
        date_patterns = [
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S.%f%z',
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M:%S',
        ]
        
        for pattern in date_patterns:
            try:
                dt = datetime.strptime(date_string, pattern)
                # Asegurar que la fecha esté en UTC si no tiene zona horaria
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # Intentar parsing automático como último recurso
        try:
            from dateutil import parser
            return parser.parse(date_string)
        except:
            self.logger.warning(f"No se pudo parsear la fecha: {date_string}")
            return None
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida que una URL sea correcta"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def _apply_general_cleaning(self, data: Dict) -> Dict:
        """Aplica limpieza general a todos los campos de texto"""
        text_fields = ['title', 'content', 'description', 'author']
        
        for field in text_fields:
            if field in data and isinstance(data[field], str):
                data[field] = self._clean_text(data[field])
        
        # Normalizar URL
        if 'url' in data and data['url']:
            data['url'] = self._normalize_url(data['url'])
        
        # Asegurar tipos correctos
        if 'image_url' in data and data['image_url'] and not self._is_valid_url(data['image_url']):
            data['image_url'] = ''
        
        return data
    
    def _normalize_url(self, url: str) -> str:
        """Normaliza URL removiendo parámetros innecesarios y estandarizando"""
        if not url:
            return ""
        
        try:
            parsed = urlparse(url)
            
            # Remover fragment
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Remover parámetros específicos que suelen ser tracking
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 'fbclid', 'gclid']
            if parsed.query:
                params = []
                for param in parsed.query.split('&'):
                    key = param.split('=')[0] if '=' in param else param
                    if key.lower() not in tracking_params:
                        params.append(param)
                
                if params:
                    normalized += '?' + '&'.join(params)
            
            # Normalizar trailing slash
            if normalized.endswith('/') and len(parsed.path) > 1:
                normalized = normalized[:-1]
            
            return normalized.lower()
            
        except Exception as e:
            self.logger.warning(f"Error normalizando URL {url}: {str(e)}")
            return url
    
    def _extract_metadata(self, data: Dict) -> Dict:
        """Extrae metadatos adicionales del artículo"""
        # Generar hash único para el artículo
        content_for_hash = f"{data.get('title', '')}{data.get('url', '')}"
        data['content_hash'] = hashlib.md5(content_for_hash.encode()).hexdigest()
        
        # Extraer longitud del contenido
        content = data.get('content', '')
        data['content_length'] = len(content) if content else 0
        
        # Determinar tipo de artículo basado en características del contenido
        data['article_type'] = self._determine_article_type(data)
        
        # Extraer idioma si está disponible (implementación básica)
        data['language'] = self._detect_language(data.get('content', '') or data.get('title', ''))
        
        # Calcular legibilidad básica
        data['readability_score'] = self._calculate_readability(data.get('content', ''))
        
        return data
    
    def _determine_article_type(self, data: Dict) -> str:
        """Determina el tipo de artículo basado en su contenido"""
        title = data.get('title', '').lower()
        content = data.get('content', '').lower()
        
        # Patrones para identificar tipos de artículos
        types = {
            'breaking_news': ['breaking', 'última hora', 'alerta', 'urgent', 'breaking news'],
            'opinion': ['opinion', 'opinión', 'editorial', 'columna', 'commentary'],
            'analysis': ['análisis', 'analysis', 'explica', 'explains', 'deep dive'],
            'interview': ['entrevista', 'interview', 'habla con', 'speaks with'],
            'report': ['informe', 'report', 'estudio', 'study', 'research'],
            'review': ['reseña', 'review', 'crítica', 'critique', 'review'],
            'feature': ['feature', 'destacado', 'especial', 'special report']
        }
        
        text_to_check = f"{title} {content[:500]}"  # Solo primeros 500 caracteres del contenido
        
        for article_type, keywords in types.items():
            if any(keyword in text_to_check for keyword in keywords):
                return article_type
        
        return 'news'  # Tipo por defecto
    
    def _detect_language(self, text: str) -> str:
        """Detecta el idioma del texto (implementación básica)"""
        if not text:
            return 'unknown'
        
        # Palabras comunes en diferentes idiomas
        spanish_words = {'el', 'la', 'de', 'que', 'y', 'en', 'un', 'es', 'se', 'no', 'te', 'lo', 'le', 'da', 'su', 'por', 'son', 'con'}
        english_words = {'the', 'of', 'and', 'a', 'to', 'in', 'is', 'it', 'you', 'that', 'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        word_count = len(words)
        
        if word_count == 0:
            return 'unknown'
        
        spanish_count = sum(1 for word in words if word in spanish_words)
        english_count = sum(1 for word in words if word in english_words)
        
        spanish_ratio = spanish_count / word_count
        english_ratio = english_count / word_count
        
        if spanish_ratio > 0.05:
            return 'es'
        elif english_ratio > 0.05:
            return 'en'
        else:
            return 'unknown'
    
    def _calculate_readability(self, text: str) -> float:
        """Calcula una puntuación de legibilidad básica (0.0 a 1.0)"""
        if not text:
            return 0.0
        
        # Factores que afectan la legibilidad:
        # 1. Longitud de oraciones (párrafos cortos son más legibles)
        # 2. Longitud de palabras (palabras cortas son más legibles)
        # 3. Presencia de números (pueden mejorar comprensión)
        
        sentences = re.split(r'[.!?]+', text)
        sentence_count = len(sentences)
        word_count = len(text.split())
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Puntuación por longitud de oración (ideal: 15-20 palabras)
        sentence_score = 1.0
        if avg_sentence_length < 10:
            sentence_score = 0.7  # Muy corto
        elif avg_sentence_length > 25:
            sentence_score = 0.6  # Muy largo
        elif 15 <= avg_sentence_length <= 20:
            sentence_score = 1.0
        else:
            sentence_score = 0.8
        
        # Puntuación por presencia de números (información más concreta)
        numbers_ratio = len(re.findall(r'\d+', text)) / word_count if word_count > 0 else 0
        number_score = min(1.0, numbers_ratio * 10)  # Máximo 1.0
        
        # Promedio ponderado
        readability = (sentence_score * 0.7) + (number_score * 0.3)
        
        return min(1.0, max(0.0, readability))
    
    def batch_normalize(self, raw_articles: List[Dict], source_type: str = 'generic') -> List[Dict]:
        """Normaliza múltiples artículos en lote"""
        normalized_articles = []
        
        for i, raw_article in enumerate(raw_articles):
            try:
                normalized = self.normalize_article(raw_article, source_type)
                if normalized:
                    normalized_articles.append(normalized)
                else:
                    self.logger.warning(f"Artículo {i+1} no pudo ser normalizado")
            except Exception as e:
                self.logger.error(f"Error normalizando artículo {i+1}: {str(e)}")
                continue
        
        return normalized_articles
    
    def validate_and_clean_batch(self, articles: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Valida y limpia un lote de artículos
        
        Returns:
            Tupla (valid_articles, invalid_articles)
        """
        valid_articles = []
        invalid_articles = []
        
        for article in articles:
            if self._validate_normalized_data(article):
                valid_articles.append(article)
            else:
                invalid_articles.append(article)
        
        return valid_articles, invalid_articles
    
    def get_normalization_stats(self, raw_articles: List[Dict], 
                               normalized_articles: List[Dict]) -> Dict:
        """Obtiene estadísticas del proceso de normalización"""
        stats = {
            'total_input': len(raw_articles),
            'total_normalized': len(normalized_articles),
            'success_rate': len(normalized_articles) / len(raw_articles) * 100 if raw_articles else 0,
            'languages_detected': {},
            'article_types': {},
            'avg_content_length': 0,
            'avg_readability': 0
        }
        
        if normalized_articles:
            # Estadísticas de idioma
            languages = [article.get('language', 'unknown') for article in normalized_articles]
            for lang in languages:
                stats['languages_detected'][lang] = stats['languages_detected'].get(lang, 0) + 1
            
            # Estadísticas de tipo de artículo
            types = [article.get('article_type', 'unknown') for article in normalized_articles]
            for article_type in types:
                stats['article_types'][article_type] = stats['article_types'].get(article_type, 0) + 1
            
            # Estadísticas de contenido
            content_lengths = [article.get('content_length', 0) for article in normalized_articles]
            stats['avg_content_length'] = sum(content_lengths) / len(content_lengths) if content_lengths else 0
            
            readability_scores = [article.get('readability_score', 0) for article in normalized_articles]
            stats['avg_readability'] = sum(readability_scores) / len(readability_scores) if readability_scores else 0
        
        return stats