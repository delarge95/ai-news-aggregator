"""
AI Processor Service para análisis de noticias con OpenAI GPT

Este módulo implementa un servicio de procesamiento de noticias que utiliza
OpenAI GPT para análisis de sentimiento, clasificación de temas, 
generación de resúmenes y scoring de relevancia.

Características:
- Manejo robusto de rate limits y retry logic
- Soporte para llamadas síncronas y asíncronas
- Optimización de costos con caching inteligente
- Logging detallado y monitoreo de performance
"""

import logging
import asyncio
import time
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor

# OpenAI imports
try:
    import openai
    from openai import AsyncOpenAI, OpenAI
except ImportError:
    openai = None
    AsyncOpenAI = None
    OpenAI = None

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SentimentType(Enum):
    """Tipos de sentimiento soportados"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class TopicCategory(Enum):
    """Categorías de temas de noticias"""
    POLITICS = "politics"
    ECONOMY = "economy"
    TECHNOLOGY = "technology"
    HEALTH = "health"
    SPORTS = "sports"
    ENTERTAINMENT = "entertainment"
    SCIENCE = "science"
    ENVIRONMENT = "environment"
    INTERNATIONAL = "international"
    CRIME = "crime"
    EDUCATION = "education"
    WEATHER = "weather"
    OTHER = "other"


@dataclass
class AnalysisResult:
    """Resultado base de análisis"""
    timestamp: datetime
    confidence: float
    processing_time: float
    tokens_used: int
    cost: float
    model: str


@dataclass
class SentimentResult(AnalysisResult):
    """Resultado de análisis de sentimiento"""
    sentiment: SentimentType
    sentiment_score: float  # -1 to 1
    emotion_tags: List[str]


@dataclass
class TopicResult(AnalysisResult):
    """Resultado de clasificación de tema"""
    primary_topic: TopicCategory
    topic_probability: float
    secondary_topics: List[Tuple[TopicCategory, float]]
    topic_keywords: List[str]


@dataclass
class SummaryResult(AnalysisResult):
    """Resultado de generación de resumen"""
    summary: str
    key_points: List[str]
    word_count: int
    reading_time_minutes: float


@dataclass
class RelevanceResult(AnalysisResult):
    """Resultado de scoring de relevancia"""
    relevance_score: float  # 0 to 1
    relevance_factors: Dict[str, float]
    trending_score: float
    importance_score: float


@dataclass
class AIAnalysisResult:
    """Resultado completo de análisis de AI"""
    article_id: str
    content: str
    sentiment: Optional[SentimentResult] = None
    topic: Optional[TopicResult] = None
    summary: Optional[SummaryResult] = None
    relevance: Optional[RelevanceResult] = None
    processing_time: float = 0.0
    total_cost: float = 0.0
    combined_score: float = 0.0
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


# Mantener compatibilidad con el enum anterior
class SentimentLabel(Enum):
    """Legacy sentiment labels for backward compatibility"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class RateLimitHandler:
    """Manejador de rate limits para OpenAI API"""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_day: int = 10000):
        self.requests_per_minute = requests_per_minute
        self.requests_per_day = requests_per_day
        self.minute_requests = []
        self.day_requests = []
        
    def can_make_request(self) -> bool:
        """Verifica si se puede hacer una nueva request"""
        now = datetime.now()
        
        # Limpiar requests antiguos (último minuto)
        self.minute_requests = [
            req_time for req_time in self.minute_requests 
            if now - req_time < timedelta(minutes=1)
        ]
        
        # Limpiar requests antiguos (último día)
        self.day_requests = [
            req_time for req_time in self.day_requests 
            if now - req_time < timedelta(days=1)
        ]
        
        return (
            len(self.minute_requests) < self.requests_per_minute and
            len(self.day_requests) < self.requests_per_day
        )
    
    def record_request(self):
        """Registra una nueva request"""
        now = datetime.now()
        self.minute_requests.append(now)
        self.day_requests.append(now)
    
    def get_wait_time(self) -> float:
        """Calcula tiempo de espera hasta poder hacer request"""
        if self.can_make_request():
            return 0.0
        
        now = datetime.now()
        wait_times = []
        
        if len(self.minute_requests) >= self.requests_per_minute:
            oldest_request = min(self.minute_requests)
            wait_times.append((oldest_request + timedelta(minutes=1) - now).total_seconds())
        
        if len(self.day_requests) >= self.requests_per_day:
            oldest_request = min(self.day_requests)
            wait_times.append((oldest_request + timedelta(days=1) - now).total_seconds())
        
        return max(wait_times) if wait_times else 0.0


class RetryHandler:
    """Manejador de reintentos con backoff exponencial"""
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute_with_retry(self, func, *args, **kwargs) -> Any:
        """Ejecuta función con reintentos automáticos"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Máximo número de reintentos alcanzado: {str(e)}")
                    raise last_exception
                
                delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                logger.warning(f"Reintento {attempt + 1} después de {delay}s: {str(e)}")
                await asyncio.sleep(delay)
        
        raise last_exception


class CostOptimizer:
    """Optimizador de costos para API calls"""
    
    # Precios por token (dólares) - GPT-3.5-turbo
    PRICING = {
        "gpt-3.5-turbo": {
            "input": 0.0005,  # $0.5 por 1M tokens
            "output": 0.0015  # $1.5 por 1M tokens
        },
        "gpt-4": {
            "input": 0.03,    # $30 por 1M tokens
            "output": 0.06    # $60 por 1M tokens
        }
    }
    
    @staticmethod
    def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Calcula costo de una llamada a la API"""
        if model not in CostOptimizer.PRICING:
            return 0.0
        
        pricing = CostOptimizer.PRICING[model]
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        
        return input_cost + output_cost
    
    @staticmethod
    def select_optimal_model(task_type: str) -> str:
        """Selecciona modelo óptimo según tipo de tarea"""
        models = {
            "sentiment": "gpt-3.5-turbo",
            "topic_classification": "gpt-3.5-turbo", 
            "summary": "gpt-4",
            "relevance": "gpt-3.5-turbo"
        }
        
        return models.get(task_type, "gpt-3.5-turbo")


class CacheManager:
    """Gestor de cache para optimizar requests"""
    
    def __init__(self, ttl_seconds: int = 3600):  # 1 hora por defecto
        self.cache = {}
        self.ttl = ttl_seconds
    
    def _generate_key(self, content: str, analysis_type: str) -> str:
        """Genera clave única para cache"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return f"{analysis_type}:{content_hash}"
    
    def get(self, content: str, analysis_type: str) -> Optional[Any]:
        """Obtiene resultado del cache"""
        key = self._generate_key(content, analysis_type)
        
        if key in self.cache:
            cached_data = self.cache[key]
            if datetime.now() - cached_data["timestamp"] < timedelta(seconds=self.ttl):
                return cached_data["result"]
            else:
                del self.cache[key]
        
        return None
    
    def set(self, content: str, analysis_type: str, result: Any):
        """Guarda resultado en cache"""
        key = self._generate_key(content, analysis_type)
        self.cache[key] = {
            "result": result,
            "timestamp": datetime.now()
        }
    
    def clear(self):
        """Limpia cache"""
        self.cache.clear()


class SentimentAnalyzer:
    """Analizador de sentimiento mejorado de artículos de noticias"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 default_model: str = "gpt-3.5-turbo",
                 requests_per_minute: int = 60,
                 requests_per_day: int = 10000,
                 cache_ttl: int = 3600):
        
        self.default_model = default_model
        self.rate_limiter = RateLimitHandler(requests_per_minute, requests_per_day)
        self.retry_handler = RetryHandler()
        self.cost_optimizer = CostOptimizer()
        self.cache = CacheManager(cache_ttl)
        
        # Inicializar clientes OpenAI
        if openai_api_key:
            self.sync_client = OpenAI(api_key=openai_api_key)
            self.async_client = AsyncOpenAI(api_key=openai_api_key)
            logger.info("Clientes OpenAI inicializados para análisis de sentimiento")
        else:
            self.sync_client = None
            self.async_client = None
            logger.warning("API key de OpenAI no proporcionada para sentiment analysis")
        
        # Legacy support
        self._pipeline = None
        
        logger.info(f"SentimentAnalyzer inicializado con modelo: {default_model}")
        
    def _prepare_content(self, text: str) -> str:
        """Prepara contenido para análisis"""
        # Limpiar HTML y caracteres especiales
        cleaned_text = re.sub(r'<[^>]+>', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimación básica de tokens (4 caracteres por token aprox)"""
        return len(text) // 4 + 100  # +100 para overhead del prompt
    
    async def analyze_sentiment_async(self, text: str) -> SentimentResult:
        """Análisis de sentimiento asíncrono"""
        start_time = time.time()
        
        # Verificar cache
        content = self._prepare_content(text)
        cached_result = self.cache.get(content, "sentiment")
        if cached_result:
            logger.info("Usando resultado de sentiment del cache")
            return cached_result
        
        if not self.async_client:
            logger.warning("Cliente OpenAI no disponible, usando análisis básico local")
            return await self._basic_sentiment_analysis_async(content, start_time)
        
        # Verificar rate limits
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            logger.info(f"Rate limit alcanzado en sentiment, esperando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        prompt = f"""
Analiza el sentimiento de este artículo de noticias y proporciona:
1. Sentimiento principal (positive, negative, neutral, mixed)
2. Puntuación de sentimiento (-1 a 1, donde -1 es muy negativo, 1 es muy positivo)
3. Etiquetas de emoción relevantes (máximo 3)

Artículo:
{content[:2000]}  # Limitar a 2000 caracteres

Responde en formato JSON con las claves: sentiment, score, emotions
"""
        
        def make_request():
            return self.async_client.chat.completions.create(
                model=self.cost_optimizer.select_optimal_model("sentiment"),
                messages=[
                    {"role": "system", "content": "Eres un experto analista de sentimientos especializado en noticias."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.1
            )
        
        try:
            response = await self.retry_handler.execute_with_retry(make_request)
            
            # Procesar respuesta
            result_text = response.choices[0].message.content.strip()
            result_data = json.loads(result_text)
            
            sentiment = SentimentType(result_data.get("sentiment", "neutral"))
            sentiment_score = float(result_data.get("score", 0.0))
            emotion_tags = result_data.get("emotions", [])
            
            # Calcular métricas
            processing_time = time.time() - start_time
            input_tokens = self._estimate_tokens(content)
            output_tokens = response.usage.completion_tokens if response.usage else 150
            cost = self.cost_optimizer.calculate_cost(
                response.model, input_tokens, output_tokens
            )
            
            # Mantener compatibilidad con el formato anterior
            legacy_label = SentimentLabel.POSITIVE if sentiment_score > 0.1 else (
                SentimentLabel.NEGATIVE if sentiment_score < -0.1 else SentimentLabel.NEUTRAL
            )
            
            result = SentimentResult(
                timestamp=datetime.now(),
                confidence=min(abs(sentiment_score), 1.0),
                processing_time=processing_time,
                tokens_used=input_tokens + output_tokens,
                cost=cost,
                model=response.model,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                emotion_tags=emotion_tags
            )
            
            # Guardar en cache
            self.cache.set(content, "sentiment", result)
            self.rate_limiter.record_request()
            
            logger.info(f"Análisis de sentimiento completado: {sentiment.value} (score: {sentiment_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis de sentimiento: {str(e)}")
            # Fallback a análisis básico
            return await self._basic_sentiment_analysis_async(content, start_time)
    
    async def _basic_sentiment_analysis_async(self, content: str, start_time: float) -> SentimentResult:
        """Análisis básico de sentimiento sin OpenAI"""
        
        # Análisis simple basado en palabras clave
        content_lower = content.lower()
        
        # Palabras positivas y negativas
        positive_words = [
            'excelente', 'bueno', 'positivo', 'optimista', 'mejor', 'avance',
            'progreso', 'éxito', 'triunfo', 'logro', 'beneficio', 'ventaja',
            'innovación', 'revolucionario', 'prometedor', 'eficaz'
        ]
        
        negative_words = [
            'malo', 'negativo', 'pesimista', 'empeoramiento', 'crisis',
            'problema', 'error', 'fracaso', 'pérdida', 'desventaja',
            'crítico', 'peligroso', 'amenaza', 'alarma', 'preocupante'
        ]
        
        # Contar coincidencias
        positive_score = sum(1 for word in positive_words if word in content_lower)
        negative_score = sum(1 for word in negative_words if word in content_lower)
        
        # Determinar sentimiento
        if positive_score > negative_score:
            sentiment = SentimentType.POSITIVE
            sentiment_score = min(positive_score / 5, 1.0)  # Normalizar
        elif negative_score > positive_score:
            sentiment = SentimentType.NEGATIVE
            sentiment_score = -min(negative_score / 5, 1.0)  # Normalizar
        else:
            sentiment = SentimentType.NEUTRAL
            sentiment_score = 0.0
        
        # Generar etiquetas de emoción básicas
        emotion_tags = []
        if sentiment_score > 0.3:
            emotion_tags.append("optimism")
        if sentiment_score < -0.3:
            emotion_tags.append("concern")
        
        processing_time = time.time() - start_time
        
        return SentimentResult(
            timestamp=datetime.now(),
            confidence=min(abs(sentiment_score) + 0.3, 1.0),  # Confianza moderada para análisis básico
            processing_time=processing_time,
            tokens_used=0,  # No se usaron tokens reales
            cost=0.0,  # Sin costo
            model="basic-analysis",
            sentiment=sentiment,
            sentiment_score=sentiment_score,
            emotion_tags=emotion_tags
        )
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """Análisis de sentimiento síncrono"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.analyze_sentiment_async(text))
        finally:
            loop.close()
    
    # Legacy method for backward compatibility
    async def analyze(self, text: str, use_openai: bool = False) -> SentimentResult:
        """Legacy method for backward compatibility"""
        return await self.analyze_sentiment_async(text)


class TopicClassifier:
    """Clasificador automático mejorado de temas de noticias"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 default_model: str = "gpt-3.5-turbo",
                 requests_per_minute: int = 60,
                 requests_per_day: int = 10000,
                 cache_ttl: int = 3600):
        
        self.default_model = default_model
        self.rate_limiter = RateLimitHandler(requests_per_minute, requests_per_day)
        self.retry_handler = RetryHandler()
        self.cost_optimizer = CostOptimizer()
        self.cache = CacheManager(cache_ttl)
        
        # Inicializar clientes OpenAI
        if openai_api_key:
            self.sync_client = OpenAI(api_key=openai_api_key)
            self.async_client = AsyncOpenAI(api_key=openai_api_key)
            logger.info("Clientes OpenAI inicializados para clasificación de temas")
        else:
            self.sync_client = None
            self.async_client = None
            logger.warning("API key de OpenAI no proporcionada para topic classification")
        
        self.categories = list(TopicCategory)
        
        logger.info(f"TopicClassifier inicializado con modelo: {default_model}")
    
    def _prepare_content(self, text: str) -> str:
        """Prepara contenido para análisis"""
        cleaned_text = re.sub(r'<[^>]+>', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimación básica de tokens"""
        return len(text) // 4 + 100
    
    async def classify_topic_async(self, text: str) -> TopicResult:
        """Clasificación de tema asíncrona"""
        start_time = time.time()
        
        # Verificar cache
        content = self._prepare_content(text)
        cached_result = self.cache.get(content, "topic")
        if cached_result:
            logger.info("Usando resultado de topic classification del cache")
            return cached_result
        
        if not self.async_client:
            logger.warning("Cliente OpenAI no disponible, usando clasificación por reglas")
            return await self._classify_with_rules_async(content, start_time)
        
        # Verificar rate limits
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            logger.info(f"Rate limit alcanzado en topic classification, esperando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        prompt = f"""
Clasifica el tema principal de este artículo de noticias en una de estas categorías:
- politics: Política, gobierno, elecciones
- economy: Economía, finanzas, mercados
- technology: Tecnología, innovación digital
- health: Salud, medicina, bienestar
- sports: Deportes, competencia
- entertainment: Entretenimiento, celebridades
- science: Ciencia, investigación
- environment: Medio ambiente, cambio climático
- international: Noticias internacionales
- crime: Crimen, seguridad, justicia
- education: Educación, universidades
- weather: Clima, meteorología
- other: Otros temas

Artículo:
{content[:2000]}

Responde en formato JSON con las claves: primary_topic, probability, secondary_topics (array de arrays con [topic, probability]), keywords (array)
"""
        
        def make_request():
            return self.async_client.chat.completions.create(
                model=self.cost_optimizer.select_optimal_model("topic_classification"),
                messages=[
                    {"role": "system", "content": "Eres un experto clasificador de noticias especializado en categorización de contenido."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.1
            )
        
        try:
            response = await self.retry_handler.execute_with_retry(make_request)
            
            # Procesar respuesta
            result_text = response.choices[0].message.content.strip()
            result_data = json.loads(result_text)
            
            primary_topic = TopicCategory(result_data.get("primary_topic", "other"))
            topic_probability = float(result_data.get("probability", 0.5))
            
            # Procesar temas secundarios
            secondary_topics_data = result_data.get("secondary_topics", [])
            secondary_topics = [
                (TopicCategory(topic), prob) 
                for topic, prob in secondary_topics_data[:3]  # Top 3
            ]
            
            topic_keywords = result_data.get("keywords", [])
            
            # Calcular métricas
            processing_time = time.time() - start_time
            input_tokens = self._estimate_tokens(content)
            output_tokens = response.usage.completion_tokens if response.usage else 200
            cost = self.cost_optimizer.calculate_cost(
                response.model, input_tokens, output_tokens
            )
            
            result = TopicResult(
                timestamp=datetime.now(),
                confidence=topic_probability,
                processing_time=processing_time,
                tokens_used=input_tokens + output_tokens,
                cost=cost,
                model=response.model,
                primary_topic=primary_topic,
                topic_probability=topic_probability,
                secondary_topics=secondary_topics,
                topic_keywords=topic_keywords
            )
            
            # Guardar en cache
            self.cache.set(content, "topic", result)
            self.rate_limiter.record_request()
            
            logger.info(f"Clasificación de tema completada: {primary_topic.value} (prob: {topic_probability:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error en clasificación de tema: {str(e)}")
            # Fallback a clasificación por reglas
            return await self._classify_with_rules_async(content, start_time)
    
    def classify_topic(self, text: str) -> TopicResult:
        """Clasificación de tema síncrona"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.classify_topic_async(text))
        finally:
            loop.close()
    
    async def _classify_with_rules_async(self, text: str, start_time: float) -> TopicResult:
        """Clasificación por reglas como fallback"""
        text_lower = text.lower()
        
        # Palabras clave expandidas para cada categoría
        category_keywords = {
            TopicCategory.POLITICS: [
                'government', 'politics', 'election', 'president', 'minister',
                'policy', 'law', 'legislation', 'congress', 'senate', 'parliament',
                'democracy', 'vote', 'campaign', 'party', 'political', 'senator',
                'representative', 'governor', 'mayor', 'prime minister', 'chancellor'
            ],
            TopicCategory.ECONOMY: [
                'economy', 'financial', 'market', 'stock', 'economy', 'trade',
                'company', 'corporation', 'revenue', 'profit', 'merger',
                'acquisition', 'investment', 'banking', 'finance', 'dollar',
                'inflation', 'recession', 'growth', 'gdp', 'unemployment'
            ],
            TopicCategory.TECHNOLOGY: [
                'tech', 'technology', 'software', 'ai', 'artificial intelligence',
                'machine learning', 'blockchain', 'crypto', 'startup', 'app',
                'digital', 'cyber', 'computer', 'internet', 'online', 'platform',
                'tech company', 'innovation', 'algorithm', 'data'
            ],
            TopicCategory.HEALTH: [
                'health', 'medical', 'hospital', 'doctor', 'patient', 'disease',
                'treatment', 'medicine', 'drug', 'vaccine', 'therapy', 'surgery',
                'mental health', 'fitness', 'nutrition', 'wellness', 'covid',
                'pandemic', 'epidemic', 'healthcare'
            ],
            TopicCategory.SPORTS: [
                'sports', 'football', 'soccer', 'basketball', 'baseball', 'tennis',
                'golf', 'olympics', 'championship', 'tournament', 'player', 'team',
                'match', 'game', 'athlete', 'coach', 'season', 'league'
            ],
            TopicCategory.ENTERTAINMENT: [
                'entertainment', 'movie', 'film', 'music', 'celebrity', 'actor',
                'actress', 'director', 'concert', 'tv', 'television', 'show',
                'series', 'drama', 'comedy', 'awards', 'festival', 'hollywood'
            ],
            TopicCategory.SCIENCE: [
                'science', 'research', 'study', 'discovery', 'experiment',
                'university', 'laboratory', 'scientist', 'researcher', 'academic',
                'publication', 'journal', 'medical', 'climate', 'environment'
            ],
            TopicCategory.ENVIRONMENT: [
                'environment', 'climate', 'global warming', 'pollution', 'sustainability',
                'renewable energy', 'conservation', 'ecosystem', 'biodiversity'
            ],
            TopicCategory.INTERNATIONAL: [
                'international', 'world', 'global', 'country', 'nation',
                'foreign', 'diplomacy', 'embassy', 'trade deal', 'war',
                'conflict', 'international', 'overseas', 'abroad', 'UN'
            ],
            TopicCategory.CRIME: [
                'crime', 'criminal', 'police', 'arrest', 'trial', 'court',
                'justice', 'investigation', 'suspect', 'victim', 'robbery',
                'murder', 'theft', 'fraud', 'corruption'
            ],
            TopicCategory.EDUCATION: [
                'education', 'school', 'university', 'college', 'student',
                'teacher', 'professor', 'curriculum', 'academic', 'degree'
            ],
            TopicCategory.WEATHER: [
                'weather', 'storm', 'rain', 'snow', 'temperature', 'climate',
                'meteorological', 'hurricane', 'tornado', 'flood', 'drought'
            ]
        }
        
        scores = {}
        keyword_matches = {}
        
        for category, keywords in category_keywords.items():
            score = 0
            matched_keywords = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            scores[category] = score
            keyword_matches[category] = matched_keywords
        
        # Encontrar categoría con mayor puntaje
        if not scores or max(scores.values()) == 0:
            primary_topic = TopicCategory.OTHER
            topic_probability = 0.1
            secondary_topics = []
        else:
            primary_topic = max(scores.items(), key=lambda x: x[1])[0]
            total_matches = sum(scores.values())
            topic_probability = scores[primary_topic] / total_matches if total_matches > 0 else 0.1
            
            # Top 3 temas secundarios
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            secondary_topics = [
                (topic, scores[topic] / total_matches if total_matches > 0 else 0.0)
                for topic, score in sorted_scores[1:4] if score > 0
            ]
        
        processing_time = time.time() - start_time
        
        return TopicResult(
            timestamp=datetime.now(),
            confidence=min(topic_probability, 1.0),
            processing_time=processing_time,
            tokens_used=0,
            cost=0.0,
            model="rule-based",
            primary_topic=primary_topic,
            topic_probability=topic_probability,
            secondary_topics=secondary_topics,
            topic_keywords=keyword_matches.get(primary_topic, [])
        )
    
    # Legacy method for backward compatibility
    async def classify(self, text: str, use_openai: bool = False) -> TopicResult:
        """Legacy method for backward compatibility"""
        return await self.classify_topic_async(text)


class Summarizer:
    """Generador de resúmenes inteligentes de artículos"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 default_model: str = "gpt-4",
                 requests_per_minute: int = 60,
                 requests_per_day: int = 10000,
                 cache_ttl: int = 3600):
        
        self.default_model = default_model
        self.rate_limiter = RateLimitHandler(requests_per_minute, requests_per_day)
        self.retry_handler = RetryHandler()
        self.cost_optimizer = CostOptimizer()
        self.cache = CacheManager(cache_ttl)
        
        # Inicializar clientes OpenAI
        if openai_api_key:
            self.sync_client = OpenAI(api_key=openai_api_key)
            self.async_client = AsyncOpenAI(api_key=openai_api_key)
            logger.info("Clientes OpenAI inicializados para summarización")
        else:
            self.sync_client = None
            self.async_client = None
            logger.warning("API key de OpenAI no proporcionada para summarization")
        
        # Legacy support
        self._pipeline = None
        
        logger.info(f"Summarizer inicializado con modelo: {default_model}")
    
    def _prepare_content(self, text: str) -> str:
        """Prepara contenido para análisis"""
        cleaned_text = re.sub(r'<[^>]+>', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimación básica de tokens"""
        return len(text) // 4 + 100
    
    async def summarize_async(self, text: str, max_words: int = 150) -> SummaryResult:
        """Generación de resumen asíncrona"""
        start_time = time.time()
        
        # Verificar cache
        content = self._prepare_content(text)
        cache_key = f"{content[:100]}:{max_words}"  # Incluir longitud en clave
        cached_result = self.cache.get(cache_key, "summary")
        if cached_result:
            logger.info("Usando resultado de summary del cache")
            return cached_result
        
        if not self.async_client:
            logger.warning("Cliente OpenAI no disponible, usando resumen básico")
            return self._create_simple_summary(content, start_time, max_words)
        
        # Verificar rate limits
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            logger.info(f"Rate limit alcanzado en summarization, esperando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        prompt = f"""
Genera un resumen conciso y completo de este artículo de noticias con las siguientes especificaciones:

1. Un resumen principal de máximo {max_words} palabras
2. Lista de 3-5 puntos clave principales
3. El resumen debe mantener los datos y cifras importantes
4. Mantener un tono neutral y informativo

Artículo:
{content[:3000]}  # Limitar a 3000 caracteres para mejor procesamiento

Responde en formato JSON con las claves: 
- summary: string con el resumen principal
- key_points: array de strings con los puntos clave
- word_count: número de palabras del resumen
"""
        
        def make_request():
            return self.async_client.chat.completions.create(
                model=self.cost_optimizer.select_optimal_model("summary"),
                messages=[
                    {"role": "system", "content": "Eres un experto redactor de resúmenes de noticias. Tu trabajo es crear resúmenes claros, precisos y concisos."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.3
            )
        
        try:
            response = await self.retry_handler.execute_with_retry(make_request)
            
            # Procesar respuesta
            result_text = response.choices[0].message.content.strip()
            result_data = json.loads(result_text)
            
            summary = result_data.get("summary", "")
            key_points = result_data.get("key_points", [])
            word_count = int(result_data.get("word_count", len(summary.split())))
            reading_time = word_count / 200  # 200 palabras por minuto
            
            # Calcular métricas
            processing_time = time.time() - start_time
            input_tokens = self._estimate_tokens(content)
            output_tokens = response.usage.completion_tokens if response.usage else 400
            cost = self.cost_optimizer.calculate_cost(
                response.model, input_tokens, output_tokens
            )
            
            result = SummaryResult(
                timestamp=datetime.now(),
                confidence=0.9,  # Alta confianza para resúmenes bien generados
                processing_time=processing_time,
                tokens_used=input_tokens + output_tokens,
                cost=cost,
                model=response.model,
                summary=summary,
                key_points=key_points,
                word_count=word_count,
                reading_time_minutes=reading_time
            )
            
            # Guardar en cache
            self.cache.set(cache_key, "summary", result)
            self.rate_limiter.record_request()
            
            logger.info(f"Resumen generado: {word_count} palabras en {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error en generación de resumen: {str(e)}")
            # Fallback a resumen simple
            return self._create_simple_summary(content, start_time, max_words)
    
    def summarize(self, text: str, max_words: int = 150) -> SummaryResult:
        """Generación de resumen síncrona"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.summarize_async(text, max_words))
        finally:
            loop.close()
    
    def _create_simple_summary(self, content: str, start_time: float, max_words: int) -> SummaryResult:
        """Crea un resumen simple como fallback"""
        # Truncar contenido
        words = content.split()
        if len(words) > max_words:
            summary_text = " ".join(words[:max_words]) + "..."
        else:
            summary_text = content
        
        # Extraer puntos clave simples (primeras oraciones)
        sentences = content.split('. ')
        key_points = [sent.strip() for sent in sentences[:3] if sent.strip()]
        
        word_count = len(summary_text.split())
        reading_time = word_count / 200
        
        return SummaryResult(
            timestamp=datetime.now(),
            confidence=0.5,  # Menor confianza para fallback
            processing_time=time.time() - start_time,
            tokens_used=0,
            cost=0.0,
            model="simple-fallback",
            summary=summary_text,
            key_points=key_points,
            word_count=word_count,
            reading_time_minutes=reading_time
        )
    
    # Legacy method for backward compatibility
    async def summarize_legacy(self, text: str, max_length: int = 150, use_openai: bool = False) -> SummaryResult:
        """Legacy method for backward compatibility"""
        # Mapear parámetros antiguos a nuevos
        max_words = max_length
        if use_openai:
            return await self.summarize_async(text, max_words)
        else:
            return self._create_simple_summary(text, time.time(), max_words)
    
    def _extract_keywords(self, text: str, num_keywords: int = 5) -> List[str]:
        """Extrae palabras clave del texto"""
        import re
        from collections import Counter
        
        # Remover puntuación y convertir a minúsculas
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        
        # Lista de stop words expandida
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 
            'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 'him', 'his', 
            'how', 'man', 'new', 'now', 'old', 'see', 'two', 'who', 'boy', 'did', 
            'its', 'let', 'put', 'say', 'she', 'too', 'use', 'have', 'they', 'been',
            'their', 'said', 'each', 'which', 'do', 'will', 'what', 'when', 'would',
            'there', 'could', 'this', 'that', 'from', 'more', 'some', 'time', 'very'
        }
        
        # Filtrar stop words y contar frecuencias
        word_freq = Counter(word for word in words if word not in stop_words)
        
        # Retornar palabras más comunes
        return [word for word, freq in word_freq.most_common(num_keywords)]


class RelevanceScorer:
    """Scorer de relevancia de artículos para priorización"""
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 default_model: str = "gpt-3.5-turbo",
                 requests_per_minute: int = 60,
                 requests_per_day: int = 10000,
                 cache_ttl: int = 3600):
        
        self.default_model = default_model
        self.rate_limiter = RateLimitHandler(requests_per_minute, requests_per_day)
        self.retry_handler = RetryHandler()
        self.cost_optimizer = CostOptimizer()
        self.cache = CacheManager(cache_ttl)
        
        # Inicializar clientes OpenAI
        if openai_api_key:
            self.sync_client = OpenAI(api_key=openai_api_key)
            self.async_client = AsyncOpenAI(api_key=openai_api_key)
            logger.info("Clientes OpenAI inicializados para relevance scoring")
        else:
            self.sync_client = None
            self.async_client = None
            logger.warning("API key de OpenAI no proporcionada para relevance scoring")
        
        logger.info(f"RelevanceScorer inicializado con modelo: {default_model}")
    
    def _prepare_content(self, text: str) -> str:
        """Prepara contenido para análisis"""
        cleaned_text = re.sub(r'<[^>]+>', '', text)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        return cleaned_text
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimación básica de tokens"""
        return len(text) // 4 + 100
    
    async def score_relevance_async(self, 
                                  text: str, 
                                  user_preferences: Optional[Dict[str, float]] = None) -> RelevanceResult:
        """Scoring de relevancia asíncrono"""
        start_time = time.time()
        
        # Verificar cache
        content = self._prepare_content(text)
        preferences_hash = hashlib.md5(str(user_preferences or {}).encode()).hexdigest()
        cache_key = f"{content[:100]}:{preferences_hash}"
        cached_result = self.cache.get(cache_key, "relevance")
        if cached_result:
            logger.info("Usando resultado de relevance scoring del cache")
            return cached_result
        
        if not self.async_client:
            logger.warning("Cliente OpenAI no disponible, usando scoring básico")
            return self._create_simple_relevance_score(content, start_time)
        
        # Verificar rate limits
        if not self.rate_limiter.can_make_request():
            wait_time = self.rate_limiter.get_wait_time()
            logger.info(f"Rate limit alcanzado en relevance scoring, esperando {wait_time:.2f}s")
            await asyncio.sleep(wait_time)
        
        # Construir prompt con preferencias del usuario
        preferences_text = ""
        if user_preferences:
            preferences_text = f"\n\nPreferencias del usuario (peso 0-1): {json.dumps(user_preferences)}"
        
        prompt = f"""
Evalúa la relevancia de este artículo de noticias basándote en:

1. Relevancia general del contenido (0-1)
2. Importancia/notoriedad del evento (0-1)
3. Potencial de trending/engagement (0-1)
4. Factores que afectan la relevancia:
   - current_events: Eventos actuales o breaking news
   - location_relevance: Proximidad geográfica al usuario
   - topic_importance: Importancia del tema para la audiencia
   - celebrity_involvement: Participación de figuras públicas
   - financial_impact: Impacto económico
   - political_significance: Significado político
   - public_interest: Interés del público general

{preferences_text}

Artículo:
{content[:2000]}

Responde en formato JSON con las claves:
- relevance_score: puntuación general (0-1)
- importance_score: importancia del evento (0-1)
- trending_score: potencial de trending (0-1)
- relevance_factors: objeto con factores individuales (0-1)
"""
        
        def make_request():
            return self.async_client.chat.completions.create(
                model=self.cost_optimizer.select_optimal_model("relevance"),
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de relevancia de noticias y engagement metrics."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.2
            )
        
        try:
            response = await self.retry_handler.execute_with_retry(make_request)
            
            # Procesar respuesta
            result_text = response.choices[0].message.content.strip()
            result_data = json.loads(result_text)
            
            relevance_score = float(result_data.get("relevance_score", 0.5))
            importance_score = float(result_data.get("importance_score", 0.5))
            trending_score = float(result_data.get("trending_score", 0.5))
            relevance_factors = result_data.get("relevance_factors", {})
            
            # Ajustar por preferencias del usuario si existen
            if user_preferences:
                for factor, user_weight in user_preferences.items():
                    if factor in relevance_factors:
                        relevance_score += (relevance_factors[factor] - 0.5) * user_weight * 0.2
                
                relevance_score = max(0.0, min(1.0, relevance_score))
            
            # Calcular métricas
            processing_time = time.time() - start_time
            input_tokens = self._estimate_tokens(content)
            output_tokens = response.usage.completion_tokens if response.usage else 250
            cost = self.cost_optimizer.calculate_cost(
                response.model, input_tokens, output_tokens
            )
            
            result = RelevanceResult(
                timestamp=datetime.now(),
                confidence=relevance_score,
                processing_time=processing_time,
                tokens_used=input_tokens + output_tokens,
                cost=cost,
                model=response.model,
                relevance_score=relevance_score,
                relevance_factors=relevance_factors,
                trending_score=trending_score,
                importance_score=importance_score
            )
            
            # Guardar en cache
            self.cache.set(cache_key, "relevance", result)
            self.rate_limiter.record_request()
            
            logger.info(f"Relevance scoring completado: {relevance_score:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Error en relevance scoring: {str(e)}")
            # Fallback a scoring simple
            return self._create_simple_relevance_score(content, start_time)
    
    def score_relevance(self, 
                       text: str, 
                       user_preferences: Optional[Dict[str, float]] = None) -> RelevanceResult:
        """Scoring de relevancia síncrono"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.score_relevance_async(text, user_preferences))
        finally:
            loop.close()
    
    def _create_simple_relevance_score(self, content: str, start_time: float) -> RelevanceResult:
        """Crea un scoring simple como fallback"""
        # Scoring básico basado en longitud y palabras clave importantes
        content_lower = content.lower()
        
        # Palabras clave de alta relevancia
        high_relevance_keywords = [
            'breaking', 'urgent', 'exclusive', 'alert', 'latest', 'breaking news',
            'urgent news', 'developing', 'urgent update'
        ]
        
        medium_relevance_keywords = [
            'important', 'significant', 'major', 'critical', 'key', 'essential'
        ]
        
        score = 0.3  # Base score
        
        # Ajustar por palabras clave
        for keyword in high_relevance_keywords:
            if keyword in content_lower:
                score += 0.3
        
        for keyword in medium_relevance_keywords:
            if keyword in content_lower:
                score += 0.1
        
        # Ajustar por longitud (artículos muy cortos menos relevantes)
        content_length = len(content.split())
        if 50 <= content_length <= 1000:
            score += 0.2
        elif content_length < 50:
            score -= 0.1
        
        score = max(0.0, min(1.0, score))
        
        return RelevanceResult(
            timestamp=datetime.now(),
            confidence=score,
            processing_time=time.time() - start_time,
            tokens_used=0,
            cost=0.0,
            model="simple-fallback",
            relevance_score=score,
            relevance_factors={
                "length_factor": min(content_length / 1000, 1.0),
                "keyword_factor": score - 0.3
            },
            trending_score=score * 0.8,
            importance_score=score * 0.9
        )


class ComprehensiveAnalyzer:
    """Analizador comprehensivo que combina todos los análisis"""
    
    def __init__(self, openai_api_key: Optional[str] = None, **kwargs):
        # Inicializar todos los analizadores
        self.sentiment_analyzer = SentimentAnalyzer(openai_api_key, **kwargs)
        self.topic_classifier = TopicClassifier(openai_api_key, **kwargs)
        self.summarizer = Summarizer(openai_api_key, **kwargs)
        self.relevance_scorer = RelevanceScorer(openai_api_key, **kwargs)
        
        logger.info("ComprehensiveAnalyzer inicializado")
    
    async def analyze_article_async(self, 
                                  article_id: str,
                                  content: str,
                                  user_preferences: Optional[Dict[str, float]] = None,
                                  max_summary_words: int = 150) -> AIAnalysisResult:
        """Análisis comprehensivo asíncrono de un artículo"""
        logger.info(f"Iniciando análisis comprehensivo para artículo {article_id}")
        
        result = AIAnalysisResult(
            article_id=article_id,
            content=content
        )
        
        start_time = time.time()
        
        try:
            # Ejecutar todos los análisis en paralelo
            sentiment_task = self.sentiment_analyzer.analyze_sentiment_async(content)
            topic_task = self.topic_classifier.classify_topic_async(content)
            summary_task = self.summarizer.summarize_async(content, max_summary_words)
            relevance_task = self.relevance_scorer.score_relevance_async(content, user_preferences)
            
            # Esperar a que todos terminen
            sentiment_result, topic_result, summary_result, relevance_result = await asyncio.gather(
                sentiment_task, topic_task, summary_task, relevance_task
            )
            
            result.sentiment = sentiment_result
            result.topic = topic_result
            result.summary = summary_result
            result.relevance = relevance_result
            
            # Compilar métricas finales
            total_time = time.time() - start_time
            total_cost = sum([
                sentiment_result.cost,
                topic_result.cost,
                summary_result.cost,
                relevance_result.cost
            ])
            
            result.processing_time = total_time
            result.total_cost = total_cost
            result.combined_score = self._calculate_combined_score(
                sentiment_result, topic_result, summary_result, relevance_result
            )
            
            logger.info(f"Análisis comprehensivo completado para {article_id} en {total_time:.2f}s con costo ${total_cost:.4f}")
            return result
            
        except Exception as e:
            logger.error(f"Error en análisis comprehensivo para {article_id}: {str(e)}")
            raise
    
    def analyze_article(self, 
                      article_id: str,
                      content: str,
                      user_preferences: Optional[Dict[str, float]] = None,
                      max_summary_words: int = 150) -> AIAnalysisResult:
        """Análisis comprehensivo síncrono de un artículo"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.analyze_article_async(article_id, content, user_preferences, max_summary_words)
            )
        finally:
            loop.close()
    
    def _calculate_combined_score(self, sentiment: SentimentResult, topic: TopicResult,
                                summary: SummaryResult, relevance: RelevanceResult) -> float:
        """Calcula un score combinado de calidad del artículo"""
        # Pesos para diferentes factores
        weights = {
            "relevance": 0.3,
            "confidence": 0.2,
            "topic_relevance": 0.2,
            "summary_quality": 0.15,
            "sentiment_clarity": 0.15
        }
        
        scores = {
            "relevance": relevance.relevance_score,
            "confidence": (sentiment.confidence + topic.confidence) / 2,
            "topic_relevance": topic.topic_probability,
            "summary_quality": min(summary.word_count / 200, 1.0),  # Normalizar por longitud óptima
            "sentiment_clarity": abs(sentiment.sentiment_score)
        }
        
        combined = sum(score * weights[factor] for factor, score in scores.items())
        return max(0.0, min(1.0, combined))
    
    async def batch_analyze_async(self, 
                                articles: List[Dict[str, Any]], 
                                max_concurrent: int = 5,
                                **kwargs) -> Tuple[List[AIAnalysisResult], List[Dict[str, Any]]]:
        """Análisis en lote de múltiples artículos"""
        
        # Crear semaphore para limitar concurrencia
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def analyze_with_semaphore(article):
            async with semaphore:
                article_id = article.get('id', 'unknown')
                content = article.get('content', '')
                return await self.analyze_article_async(article_id, content, **kwargs)
        
        # Ejecutar análisis en paralelo con límite de concurrencia
        tasks = [analyze_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrar resultados y errores
        successful_results = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append({
                    "index": i, 
                    "article_id": articles[i].get('id', 'unknown'),
                    "error": str(result)
                })
            else:
                successful_results.append(result)
        
        logger.info(f"Análisis en lote completado: {len(successful_results)} exitosos, {len(errors)} errores")
        return successful_results, errors


# Factory function para fácil inicialización
def create_ai_processor(openai_api_key: Optional[str] = None, **kwargs) -> ComprehensiveAnalyzer:
    """Factory function para crear una instancia del analizador comprehensivo"""
    return ComprehensiveAnalyzer(openai_api_key, **kwargs)


# Funciones de utilidad para estadísticas
def analyze_cost_breakdown(analysis_results: List[AIAnalysisResult]) -> Dict[str, Any]:
    """Analiza el breakdown de costos de múltiples análisis"""
    total_cost = sum(result.total_cost for result in analysis_results if result.total_cost)
    total_articles = len(analysis_results)
    
    if total_articles == 0:
        return {"total_cost": 0, "average_cost": 0, "total_articles": 0}
    
    return {
        "total_cost": total_cost,
        "average_cost": total_cost / total_articles,
        "total_articles": total_articles,
        "cost_per_article": total_cost / total_articles
    }


# Mantener compatibilidad con el AIProcessor legacy
class AIProcessor(ComprehensiveAnalyzer):
    """Legacy AIProcessor para compatibilidad hacia atrás"""
    
    def __init__(self, redis_client=None, openai_api_key=None):
        # Inicializar con parámetros legacy
        kwargs = {}
        if openai_api_key:
            kwargs['openai_api_key'] = openai_api_key
            
        super().__init__(**kwargs)
        self.redis_client = redis_client
        logger.info("AIProcessor legacy inicializado para compatibilidad")
    
    async def analyze_article_legacy(self, article_id: str, content: str, 
                                   use_openai: bool = False) -> AIAnalysisResult:
        """Legacy method para compatibilidad"""
        # Para compatibilidad, no usar OpenAI si use_openai=False
        if not use_openai:
            logger.warning("Legacy AIProcessor: usando solo fallbacks cuando use_openai=False")
            # Crear resultados simples sin OpenAI
            return AIAnalysisResult(
                article_id=article_id,
                content=content,
                processing_time=0.1
            )
        
        return await self.analyze_article_async(article_id, content)


# Celery tasks para procesamiento en background
try:
    from celery import Celery
    celery_app = Celery('ai_processor')
    
    @celery_app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3})
    def analyze_article_async(self, article_id: str, content: str, openai_api_key: str = None):
        """Celery task para análisis asíncrono de artículos"""
        try:
            analyzer = create_ai_processor(openai_api_key)
            result = asyncio.run(analyzer.analyze_article_async(article_id, content))
            
            return {
                'status': 'completed',
                'article_id': article_id,
                'sentiment': result.sentiment.sentiment.value if result.sentiment else None,
                'topic': result.topic.primary_topic.value if result.topic else None,
                'relevance_score': result.relevance.relevance_score if result.relevance else None,
                'processing_time': result.processing_time,
                'cost': result.total_cost
            }
            
        except Exception as exc:
            logger.error(f"Análisis asíncrono falló para artículo {article_id}: {exc}")
            raise self.retry(countdown=60, exc=exc)
    
    @celery_app.task
    def batch_analyze_articles(article_data: List[Dict[str, str]], openai_api_key: str = None):
        """Celery task para análisis en lote de artículos"""
        analyzer = create_ai_processor(openai_api_key)
        results = []
        
        for article in article_data:
            try:
                result = asyncio.run(analyzer.analyze_article_async(
                    article['id'], 
                    article['content']
                ))
                results.append({
                    'article_id': article['id'],
                    'status': 'completed',
                    'sentiment': result.sentiment.sentiment.value if result.sentiment else None,
                    'topic': result.topic.primary_topic.value if result.topic else None,
                    'relevance_score': result.relevance.relevance_score if result.relevance else None
                })
            except Exception as e:
                results.append({
                    'article_id': article['id'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results

except ImportError:
    logger.info("Celery no disponible, tareas en background deshabilitadas")


# Exportar clases principales
__all__ = [
    'SentimentAnalyzer',
    'TopicClassifier', 
    'Summarizer',
    'RelevanceScorer',
    'ComprehensiveAnalyzer',
    'AIProcessor',
    'create_ai_processor',
    'analyze_cost_breakdown',
    'SentimentType',
    'TopicCategory',
    'SentimentLabel',
    'SentimentResult',
    'TopicResult',
    'SummaryResult',
    'RelevanceResult',
    'AIAnalysisResult'
]