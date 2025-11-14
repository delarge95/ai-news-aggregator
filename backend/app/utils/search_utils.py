"""
Utilidades de procesamiento de texto y búsqueda semántica para AI News Aggregator
Incluye funciones para tokenización, análisis de texto y búsqueda semántica
"""

import re
import logging
from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime
import math
import hashlib

logger = logging.getLogger(__name__)


class TextProcessor:
    """Procesador de texto para búsqueda avanzada"""
    
    def __init__(self):
        # Palabras comunes a ignorar
        self.stopwords = {
            'english': {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
                'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 
                'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 
                'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 
                'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'what', 'which', 
                'who', 'when', 'where', 'why', 'how', 'not', 'no', 'yes', 'all', 'any', 'some', 
                'many', 'much', 'few', 'little', 'more', 'most', 'other', 'another', 'such', 'only'
            },
            'spanish': {
                'el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'pero', 'en', 
                'con', 'de', 'del', 'para', 'por', 'sin', 'sobre', 'es', 'son', 'está', 'están', 
                'era', 'eran', 'ser', 'sido', 'tener', 'tiene', 'tenía', 'había', 'hacer', 'hace', 
                'hizo', 'podría', 'debe', 'deben', 'puede', 'pueden', 'este', 'esta', 'estos', 
                'estas', 'ese', 'esa', 'esos', 'esas', 'aquel', 'aquella', 'aquellos', 'aquellas'
            }
        }
        
        # Patrones de URLs y emails
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\S+@\S+')
        
        # Patrones de hashtags y menciones
        self.hashtag_pattern = re.compile(r'#\w+')
        self.mention_pattern = re.compile(r'@\w+')
        
        # Patrones de fechas
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}\s+\w+\s+\d{4}',  # DD Month YYYY
        ]
    
    def preprocess_text(self, text: str, language: str = 'english') -> str:
        """
        Preprocesar texto para búsqueda
        
        Args:
            text: Texto a procesar
            language: Idioma del texto
            
        Returns:
            Texto preprocesado
        """
        if not text:
            return ""
        
        # Normalizar encoding
        text = text.lower().strip()
        
        # Remover URLs
        text = self.url_pattern.sub('', text)
        
        # Remover emails
        text = self.email_pattern.sub('', text)
        
        # Remover hashtags y menciones para búsqueda general
        text = self.hashtag_pattern.sub('', text)
        text = self.mention_pattern.sub('', text)
        
        # Remover caracteres especiales pero mantener espacios
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def tokenize(self, text: str, remove_stopwords: bool = True, language: str = 'english') -> List[str]:
        """
        Tokenizar texto en palabras
        
        Args:
            text: Texto a tokenizar
            remove_stopwords: Si remover palabras comunes
            language: Idioma del texto
            
        Returns:
            Lista de tokens
        """
        if not text:
            return []
        
        # Preprocesar
        processed_text = self.preprocess_text(text, language)
        
        # Split en palabras
        tokens = processed_text.split()
        
        # Remover stopwords
        if remove_stopwords and language in self.stopwords:
            stopwords = self.stopwords[language]
            tokens = [token for token in tokens if token not in stopwords]
        
        # Filtrar tokens muy cortos
        tokens = [token for token in tokens if len(token) >= 2]
        
        return tokens
    
    def extract_keywords(self, text: str, max_keywords: int = 10, language: str = 'english') -> List[str]:
        """
        Extraer keywords principales del texto
        
        Args:
            text: Texto a analizar
            max_keywords: Número máximo de keywords
            language: Idioma del texto
            
        Returns:
            Lista de keywords principales
        """
        tokens = self.tokenize(text, remove_stopwords=True, language=language)
        
        # Contar frecuencia
        from collections import Counter
        token_freq = Counter(tokens)
        
        # Obtener top keywords
        top_keywords = token_freq.most_common(max_keywords)
        
        return [keyword for keyword, freq in top_keywords]
    
    def calculate_text_similarity(self, text1: str, text2: str, method: str = 'cosine') -> float:
        """
        Calcular similitud entre dos textos
        
        Args:
            text1: Primer texto
            text2: Segundo texto
            method: Método de similitud ('cosine', 'jaccard', 'levenshtein')
            
        Returns:
            Score de similitud (0.0 a 1.0)
        """
        if method == 'cosine':
            return self._cosine_similarity(text1, text2)
        elif method == 'jaccard':
            return self._jaccard_similarity(text1, text2)
        elif method == 'levenshtein':
            return self._levenshtein_similarity(text1, text2)
        else:
            raise ValueError(f"Método de similitud no soportado: {method}")
    
    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Similitud coseno usando TF-IDF simple"""
        try:
            from collections import Counter
            
            # Tokenizar
            tokens1 = self.tokenize(text1)
            tokens2 = self.tokenize(text2)
            
            # Crear vectores de frecuencia
            all_tokens = set(tokens1 + tokens2)
            vector1 = [tokens1.count(token) for token in all_tokens]
            vector2 = [tokens2.count(token) for token in all_tokens]
            
            # Calcular coseno
            dot_product = sum(a * b for a, b in zip(vector1, vector2))
            norm1 = math.sqrt(sum(a * a for a in vector1))
            norm2 = math.sqrt(sum(a * a for a in vector2))
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error(f"Error calculando similitud coseno: {str(e)}")
            return 0.0
    
    def _jaccard_similarity(self, text1: str, text2: str) -> float:
        """Similitud Jaccard"""
        try:
            tokens1 = set(self.tokenize(text1))
            tokens2 = set(self.tokenize(text2))
            
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            
            if len(union) == 0:
                return 0.0
            
            return len(intersection) / len(union)
            
        except Exception as e:
            logger.error(f"Error calculando similitud Jaccard: {str(e)}")
            return 0.0
    
    def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """Similitud basada en distancia de Levenshtein"""
        try:
            # Implementación simple de Levenshtein
            if len(text1) == 0 or len(text2) == 0:
                return 0.0
            
            max_len = max(len(text1), len(text2))
            if max_len == 0:
                return 1.0
            
            # Calcular distancia
            from collections import deque
            
            previous_row = list(range(len(text2) + 1))
            for i, c1 in enumerate(text1):
                current_row = [i + 1]
                for j, c2 in enumerate(text2):
                    insertions = previous_row[j + 1] + 1
                    deletions = current_row[j] + 1
                    substitutions = previous_row[j] + (c1 != c2)
                    current_row.append(min(insertions, deletions, substitutions))
                previous_row = current_row
            
            distance = previous_row[-1]
            similarity = 1 - (distance / max_len)
            
            return max(0.0, similarity)
            
        except Exception as e:
            logger.error(f"Error calculando similitud Levenshtein: {str(e)}")
            return 0.0
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extraer entidades del texto (personas, organizaciones, lugares)
        
        Args:
            text: Texto a analizar
            
        Returns:
            Diccionario con entidades por tipo
        """
        entities = {
            'persons': [],
            'organizations': [],
            'locations': [],
            'dates': []
        }
        
        try:
            # Detectar fechas
            for pattern in self.date_patterns:
                dates = re.findall(pattern, text)
                entities['dates'].extend(dates)
            
            # Detectar organizaciones (palabras con mayúsculas)
            org_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|Ltd|Company|Corporation|Technologies|Tech|Systems|Labs)\b'
            orgs = re.findall(org_pattern, text)
            entities['organizations'].extend(orgs)
            
            # Detectar lugares (palabras con mayúsculas seguidas de preposiciones)
            location_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:in|at|on|from|to|of|for)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
            locations = re.findall(location_pattern, text)
            entities['locations'].extend(locations)
            
            # Detectar personas (nombres con patrón común)
            person_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
            persons = re.findall(person_pattern, text)
            # Filtrar personas de organizaciones y lugares
            persons = [p for p in persons if p not in entities['organizations'] + entities['locations']]
            entities['persons'] = persons
            
            return entities
            
        except Exception as e:
            logger.error(f"Error extrayendo entidades: {str(e)}")
            return entities
    
    def generate_text_hash(self, text: str) -> str:
        """
        Generar hash del texto para deduplicación
        
        Args:
            text: Texto a hashear
            
        Returns:
            Hash SHA-256 del texto
        """
        try:
            # Normalizar texto para hashing
            normalized_text = self.preprocess_text(text)
            return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.error(f"Error generando hash: {str(e)}")
            return hashlib.sha256(text.encode('utf-8')).hexdigest()


class SemanticSearchHelper:
    """Helper para búsqueda semántica con IA"""
    
    def __init__(self):
        self.model_available = False
        self.embedding_dim = 768  # Dimensión típica de embeddings
        
        # Diccionario de sinónimos para mejorar búsqueda semántica
        self.synonyms = {
            'artificial intelligence': ['AI', 'machine intelligence', 'cognitive computing'],
            'machine learning': ['ML', 'algorithmic learning', 'statistical learning'],
            'deep learning': ['neural networks', 'deep neural networks', 'DL'],
            'neural network': ['ANN', 'artificial neural network', 'neural net'],
            'computer vision': ['image processing', 'visual recognition', 'CV'],
            'natural language processing': ['NLP', 'text mining', 'computational linguistics'],
            'robotics': ['automation', 'automated systems', 'robotic systems'],
            'blockchain': ['distributed ledger', 'cryptocurrency', 'digital ledger'],
            'cryptocurrency': ['digital currency', 'crypto', 'virtual currency'],
            'fintech': ['financial technology', 'financial innovation', 'banking tech']
        }
    
    async def expand_query(self, query: str) -> List[str]:
        """
        Expandir query con sinónimos para búsqueda semántica
        
        Args:
            query: Consulta original
            
        Returns:
            Lista de consultas expandidas
        """
        try:
            expanded_queries = [query]
            
            query_lower = query.lower()
            
            # Expandir con sinónimos
            for term, synonyms in self.synonyms.items():
                if term in query_lower:
                    for synonym in synonyms:
                        new_query = query_lower.replace(term, synonym)
                        if new_query != query_lower:
                            expanded_queries.append(new_query)
            
            # Expandir con variaciones comunes
            common_expansions = {
                'ai': ['artificial intelligence', 'AI'],
                'ml': ['machine learning'],
                'dl': ['deep learning'],
                'nlp': ['natural language processing'],
                'cv': ['computer vision'],
                'ann': ['artificial neural network'],
                'cnn': ['convolutional neural network'],
                'rnn': ['recurrent neural network'],
                'gan': ['generative adversarial network']
            }
            
            query_words = query_lower.split()
            for word in query_words:
                if word in common_expansions:
                    for expansion in common_expansions[word]:
                        if expansion not in expanded_queries:
                            expanded_queries.append(expansion)
            
            return list(set(expanded_queries))  # Eliminar duplicados
            
        except Exception as e:
            logger.error(f"Error expandiendo query: {str(e)}")
            return [query]
    
    async def semantic_rerank(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Reordenar documentos basado en similitud semántica
        
        Args:
            query: Consulta de búsqueda
            documents: Lista de documentos
            
        Returns:
            Documentos reordenados con scores de similitud
        """
        try:
            # Por ahora usar similitud simple basada en tokens
            # En implementación real usaríamos embeddings precomputados
            
            processed_query = TextProcessor().preprocess_text(query)
            
            for doc in documents:
                # Combinar título, contenido y summary
                doc_text = f"{doc.get('title', '')} {doc.get('content', '')} {doc.get('summary', '')}"
                processed_doc = TextProcessor().preprocess_text(doc_text)
                
                # Calcular similitud
                similarity = TextProcessor().calculate_text_similarity(processed_query, processed_doc, 'cosine')
                
                # Combinar con score de relevancia existente
                existing_score = doc.get('relevance_score', 0.0)
                doc['semantic_score'] = similarity
                doc['combined_score'] = (existing_score * 0.6) + (similarity * 0.4)
            
            # Reordenar por combined score
            reranked = sorted(documents, key=lambda x: x.get('combined_score', 0), reverse=True)
            
            return reranked
            
        except Exception as e:
            logger.error(f"Error en reranking semántico: {str(e)}")
            return documents
    
    async def find_similar_articles(self, article_text: str, articles: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """
        Encontrar artículos similares basado en contenido
        
        Args:
            article_text: Texto del artículo de referencia
            articles: Lista de artículos para buscar similitudes
            limit: Límite de resultados
            
        Returns:
            Artículos ordenados por similitud
        """
        try:
            similarities = []
            
            for article in articles:
                # Combinar campos de texto del artículo
                article_combined = f"{article.get('title', '')} {article.get('content', '')}"
                
                # Calcular similitud
                similarity = TextProcessor().calculate_text_similarity(article_text, article_combined, 'cosine')
                
                similarities.append({
                    'article': article,
                    'similarity': similarity
                })
            
            # Ordenar por similitud
            similarities.sort(key=lambda x: x['similarity'], reverse=True)
            
            return similarities[:limit]
            
        except Exception as e:
            logger.error(f"Error encontrando artículos similares: {str(e)}")
            return []


# Instancias globales
text_processor = TextProcessor()
semantic_helper = SemanticSearchHelper()


# Funciones de utilidad
def preprocess_search_query(query: str, language: str = 'english') -> str:
    """
    Preprocesar query de búsqueda
    
    Args:
        query: Consulta de búsqueda
        language: Idioma del texto
        
    Returns:
        Query preprocesada
    """
    return text_processor.preprocess_text(query, language)


def extract_search_keywords(query: str, max_keywords: int = 10, language: str = 'english') -> List[str]:
    """
    Extraer keywords de consulta de búsqueda
    
    Args:
        query: Consulta de búsqueda
        max_keywords: Número máximo de keywords
        language: Idioma del texto
        
    Returns:
        Lista de keywords
    """
    return text_processor.extract_keywords(query, max_keywords, language)


def calculate_query_similarity(query1: str, query2: str, method: str = 'cosine') -> float:
    """
    Calcular similitud entre dos consultas
    
    Args:
        query1: Primera consulta
        query2: Segunda consulta
        method: Método de similitud
        
    Returns:
        Score de similitud
    """
    return text_processor.calculate_text_similarity(query1, query2, method)


if __name__ == "__main__":
    # Ejemplo de uso
    processor = TextProcessor()
    
    text = "Artificial intelligence and machine learning are transforming technology companies in 2025."
    keywords = processor.extract_keywords(text)
    print(f"Keywords: {keywords}")
    
    entities = processor.extract_entities(text)
    print(f"Entities: {entities}")
    
    similarity = processor.calculate_text_similarity(
        "AI and ML", 
        "artificial intelligence and machine learning"
    )
    print(f"Similarity: {similarity}")