"""
Pipeline de Orquestación de IA para AI News Aggregator

Este módulo implementa un pipeline completo de procesamiento de IA que orquesta:
1. PreprocessingPipeline - limpieza y normalización de texto
2. AIAnalysisPipeline - análisis secuencial (sentiment → topics → summary → relevance)
3. PostprocessingPipeline - formateo final y almacenamiento

Características:
- Procesamiento paralelo con configuración de batch sizes y concurrency
- Manejo robusto de errores
- Validación de datos
- Monitoreo de performance
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
import uuid
import hashlib
import json
from collections import defaultdict, Counter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from openai import AsyncOpenAI

from ..db.models import Article, Source, ArticleAnalysis
from ..utils.normalizer import NewsNormalizer
from ..core.config import settings


class AnalysisType(Enum):
    """Tipos de análisis soportados"""
    SENTIMENT = "sentiment"
    TOPICS = "topics"
    SUMMARY = "summary"
    RELEVANCE = "relevance"
    BIAS = "bias"


class ProcessingStatus(Enum):
    """Estados del procesamiento"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ProcessingConfig:
    """Configuración del procesamiento"""
    # Batch processing
    batch_size: int = 10
    max_concurrent_batches: int = 5
    
    # Individual analysis
    max_concurrent_analyses: int = 20
    analysis_timeout: int = 30
    
    # OpenAI configuration
    openai_model: str = settings.OPENAI_MODEL
    max_tokens: int = 1000
    temperature: float = 0.3
    
    # Validation thresholds
    min_content_length: int = 50
    min_title_length: int = 5
    max_title_length: int = 500
    max_content_length: int = 50000
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Feature toggles
    enable_parallel_processing: bool = True
    enable_caching: bool = True
    enable_validation: bool = True


@dataclass
class AnalysisResult:
    """Resultado de análisis individual"""
    article_id: str
    analysis_type: AnalysisType
    result: Dict[str, Any]
    confidence_score: float
    model_used: str
    processing_time: float
    error_message: Optional[str] = None
    status: ProcessingStatus = ProcessingStatus.COMPLETED


@dataclass
class BatchResult:
    """Resultado de procesamiento por lotes"""
    batch_id: str
    total_articles: int
    successful_analyses: int
    failed_analyses: int
    processing_time: float
    results: List[AnalysisResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataValidator:
    """Validador de datos para artículos"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def validate_article_data(self, article_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Valida datos de artículo
        
        Returns:
            Tuple de (is_valid, list_of_errors)
        """
        errors = []
        
        # Validar campos requeridos
        if not article_data.get('title'):
            errors.append("Título es requerido")
        elif len(article_data['title'].strip()) < self.config.min_title_length:
            errors.append(f"Título muy corto (mínimo {self.config.min_title_length} caracteres)")
        elif len(article_data['title']) > self.config.max_title_length:
            errors.append(f"Título muy largo (máximo {self.config.max_title_length} caracteres)")
        
        if not article_data.get('url'):
            errors.append("URL es requerida")
        elif not self._is_valid_url(article_data['url']):
            errors.append("URL inválida")
        
        # Validar contenido
        content = article_data.get('content', '')
        if content and len(content) > self.config.max_content_length:
            errors.append(f"Contenido muy largo (máximo {self.config.max_content_length} caracteres)")
        elif not content and not article_data.get('description'):
            errors.append("Contenido o descripción requerida")
        
        # Validar campos opcionales pero esperados
        source_name = article_data.get('source_name', '')
        if not source_name:
            errors.append("Nombre de fuente recomendado pero opcional")
        
        return len(errors) == 0, errors
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida formato de URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def batch_validate(self, articles_data: List[Dict[str, Any]]) -> Tuple[List[Dict], List[Dict]]:
        """
        Valida lote de artículos
        
        Returns:
            Tuple de (valid_articles, invalid_articles)
        """
        valid_articles = []
        invalid_articles = []
        
        for article_data in articles_data:
            is_valid, errors = self.validate_article_data(article_data)
            if is_valid:
                valid_articles.append(article_data)
            else:
                invalid_articles.append({
                    'article': article_data,
                    'errors': errors
                })
        
        return valid_articles, invalid_articles


class PreprocessingPipeline:
    """Pipeline de preprocesamiento - limpieza y normalización de texto"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.normalizer = NewsNormalizer()
        self.validator = DataValidator(config)
        self.logger = logging.getLogger(__name__)
    
    async def process_articles(self, raw_articles: List[Dict[str, Any]], 
                             source_type: str = 'generic') -> Tuple[List[Dict], List[Dict]]:
        """
        Procesa lote de artículos crudos
        
        Returns:
            Tuple de (processed_articles, failed_articles)
        """
        self.logger.info(f"Iniciando preprocesamiento de {len(raw_articles)} artículos")
        
        processed_articles = []
        failed_articles = []
        
        # Normalizar artículos
        if self.config.enable_parallel_processing:
            processed_articles = await self._process_batch_parallel(raw_articles, source_type)
        else:
            processed_articles = await self._process_batch_sequential(raw_articles, source_type)
        
        # Validar artículos procesados
        if self.config.enable_validation:
            valid_articles, invalid_articles = self.validator.batch_validate(processed_articles)
            
            self.logger.info(f"Preprocesamiento completado: {len(valid_articles)} válidos, "
                           f"{len(invalid_articles)} inválidos")
            
            return valid_articles, invalid_articles
        else:
            return processed_articles, failed_articles
    
    async def _process_batch_parallel(self, raw_articles: List[Dict], 
                                    source_type: str) -> List[Dict]:
        """Procesamiento paralelo por lotes"""
        processed_articles = []
        
        # Dividir en lotes
        batches = [raw_articles[i:i + self.config.batch_size] 
                  for i in range(0, len(raw_articles), self.config.batch_size)]
        
        # Procesar lotes en paralelo
        tasks = []
        for batch in batches:
            task = asyncio.create_task(self._process_single_batch(batch, source_type))
            tasks.append(task)
        
        # Recopilar resultados
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in batch_results:
            if isinstance(result, Exception):
                self.logger.error(f"Error en lote: {str(result)}")
            else:
                processed_articles.extend(result)
        
        return processed_articles
    
    async def _process_batch_sequential(self, raw_articles: List[Dict], 
                                      source_type: str) -> List[Dict]:
        """Procesamiento secuencial por lotes"""
        processed_articles = []
        
        # Dividir en lotes
        batches = [raw_articles[i:i + self.config.batch_size] 
                  for i in range(0, len(raw_articles), self.config.batch_size)]
        
        for batch in batches:
            batch_result = await self._process_single_batch(batch, source_type)
            processed_articles.extend(batch_result)
        
        return processed_articles
    
    async def _process_single_batch(self, batch: List[Dict], 
                                  source_type: str) -> List[Dict]:
        """Procesa un solo lote"""
        try:
            processed = self.normalizer.batch_normalize(batch, source_type)
            self.logger.debug(f"Lote procesado: {len(processed)}/{len(batch)} artículos")
            return processed
        except Exception as e:
            self.logger.error(f"Error procesando lote: {str(e)}")
            return []


class AIAnalysisPipeline:
    """Pipeline de análisis de IA - análisis secuencial"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None
        self.logger = logging.getLogger(__name__)
        
        # Prompts específicos para cada tipo de análisis
        self.prompts = {
            AnalysisType.SENTIMENT: self._get_sentiment_prompt(),
            AnalysisType.TOPICS: self._get_topics_prompt(),
            AnalysisType.SUMMARY: self._get_summary_prompt(),
            AnalysisType.RELEVANCE: self._get_relevance_prompt(),
            AnalysisType.BIAS: self._get_bias_prompt()
        }
    
    async def analyze_articles(self, articles: List[Dict[str, Any]]) -> List[AnalysisResult]:
        """
        Analiza lote de artículos con análisis secuencial
        
        Args:
            articles: Lista de artículos procesados
            
        Returns:
            Lista de resultados de análisis
        """
        if not self.openai_client:
            self.logger.warning("OpenAI client no configurado, saltando análisis")
            return []
        
        self.logger.info(f"Iniciando análisis IA de {len(articles)} artículos")
        
        # Análisis secuencial para cada artículo
        all_results = []
        
        if self.config.enable_parallel_processing:
            # Procesar en paralelo con límite de concurrencia
            semaphore = asyncio.Semaphore(self.config.max_concurrent_analyses)
            tasks = [self._analyze_single_article_semaphore(article, semaphore) for article in articles]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"Error en análisis: {str(result)}")
                else:
                    all_results.extend(result)
        else:
            # Procesamiento secuencial
            for article in articles:
                try:
                    results = await self._analyze_single_article(article)
                    all_results.extend(results)
                except Exception as e:
                    self.logger.error(f"Error analizando artículo {article.get('title', 'unknown')}: {str(e)}")
        
        self.logger.info(f"Análisis completado: {len(all_results)} resultados")
        return all_results
    
    async def _analyze_single_article_semaphore(self, article: Dict, semaphore: asyncio.Semaphore) -> List[AnalysisResult]:
        """Analiza un artículo con control de semáforo"""
        async with semaphore:
            return await self._analyze_single_article(article)
    
    async def _analyze_single_article(self, article: Dict[str, Any]) -> List[AnalysisResult]:
        """
        Analiza un artículo individual con secuencia de análisis
        
        Análisis secuencial: sentiment → topics → summary → relevance → bias
        """
        article_id = str(uuid.uuid4())
        results = []
        
        try:
            # Preparar contenido del artículo
            title = article.get('title', '')
            content = article.get('content', '') or article.get('description', '')
            
            if not content:
                self.logger.warning(f"Sin contenido para artículo: {title}")
                return []
            
            # Análisis secuencial
            analysis_sequence = [
                AnalysisType.SENTIMENT,
                AnalysisType.TOPICS,
                AnalysisType.SUMMARY,
                AnalysisType.RELEVANCE,
                AnalysisType.BIAS
            ]
            
            for analysis_type in analysis_sequence:
                try:
                    start_time = asyncio.get_event_loop().time()
                    result = await self._perform_analysis(
                        article_id, title, content, analysis_type
                    )
                    end_time = asyncio.get_event_loop().time()
                    
                    result.processing_time = end_time - start_time
                    results.append(result)
                    
                    self.logger.debug(f"Completado {analysis_type.value} para artículo {article_id[:8]}")
                    
                except Exception as e:
                    self.logger.error(f"Error en {analysis_type.value} para {article_id[:8]}: {str(e)}")
                    
                    # Agregar resultado de error
                    error_result = AnalysisResult(
                        article_id=article_id,
                        analysis_type=analysis_type,
                        result={},
                        confidence_score=0.0,
                        model_used=self.config.openai_model,
                        processing_time=0.0,
                        error_message=str(e),
                        status=ProcessingStatus.FAILED
                    )
                    results.append(error_result)
        
        except Exception as e:
            self.logger.error(f"Error general analizando artículo {article_id[:8]}: {str(e)}")
        
        return results
    
    async def _perform_analysis(self, article_id: str, title: str, 
                               content: str, analysis_type: AnalysisType) -> AnalysisResult:
        """Realiza análisis específico usando OpenAI"""
        try:
            # Construir prompt
            prompt = self._build_prompt(analysis_type, title, content)
            
            # Configurar parámetros de la API
            max_tokens_map = {
                AnalysisType.SENTIMENT: 100,
                AnalysisType.TOPICS: 200,
                AnalysisType.SUMMARY: 300,
                AnalysisType.RELEVANCE: 150,
                AnalysisType.BIAS: 200
            }
            
            max_tokens = max_tokens_map.get(analysis_type, 200)
            
            # Realizar llamada a OpenAI con timeout
            response = await asyncio.wait_for(
                self.openai_client.chat.completions.create(
                    model=self.config.openai_model,
                    messages=[
                        {"role": "system", "content": "You are a professional news analyst."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=self.config.temperature
                ),
                timeout=self.config.analysis_timeout
            )
            
            # Procesar respuesta
            response_text = response.choices[0].message.content.strip()
            parsed_result = self._parse_ai_response(analysis_type, response_text)
            
            return AnalysisResult(
                article_id=article_id,
                analysis_type=analysis_type,
                result=parsed_result,
                confidence_score=self._calculate_confidence(analysis_type, response_text),
                model_used=self.config.openai_model,
                processing_time=0.0,  # Se calculará externamente
                status=ProcessingStatus.COMPLETED
            )
            
        except asyncio.TimeoutError:
            raise Exception(f"Timeout en análisis {analysis_type.value}")
        except Exception as e:
            raise Exception(f"Error en análisis {analysis_type.value}: {str(e)}")
    
    def _build_prompt(self, analysis_type: AnalysisType, title: str, content: str) -> str:
        """Construye prompt específico para cada tipo de análisis"""
        base_prompt = f"""
Título: {title}
Contenido: {content[:2000]}{'...' if len(content) > 2000 else ''}

"""
        
        return base_prompt + self.prompts[analysis_type]
    
    def _parse_ai_response(self, analysis_type: AnalysisType, response: str) -> Dict[str, Any]:
        """Parsea respuesta de IA según el tipo de análisis"""
        try:
            # Intentar parsear como JSON primero
            if response.strip().startswith('{'):
                return json.loads(response)
            
            # Parseo específico por tipo
            if analysis_type == AnalysisType.SENTIMENT:
                return self._parse_sentiment_response(response)
            elif analysis_type == AnalysisType.TOPICS:
                return self._parse_topics_response(response)
            elif analysis_type == AnalysisType.SUMMARY:
                return self._parse_summary_response(response)
            elif analysis_type == AnalysisType.RELEVANCE:
                return self._parse_relevance_response(response)
            elif analysis_type == AnalysisType.BIAS:
                return self._parse_bias_response(response)
            else:
                return {"raw_response": response}
                
        except Exception as e:
            self.logger.warning(f"Error parseando respuesta {analysis_type.value}: {str(e)}")
            return {"raw_response": response, "parse_error": str(e)}
    
    def _calculate_confidence(self, analysis_type: AnalysisType, response: str) -> float:
        """Calcula score de confianza basado en la respuesta"""
        # Factores que indican confianza
        confidence_factors = [
            len(response) > 20,  # Respuesta sustancial
            not response.lower().startswith('i cannot'),  # No es una negativa
            not response.lower().startswith('i\'m sorry'),  # No es una disculpa
            not response.count('?') > len(response.split()) / 10,  # No demasiadas preguntas
        ]
        
        # Calcular confianza base
        base_confidence = sum(confidence_factors) / len(confidence_factors)
        
        # Ajustes específicos por tipo
        if analysis_type == AnalysisType.SUMMARY:
            base_confidence += 0.1  # Resúmenes tienden a ser más confiables
        elif analysis_type == AnalysisType.SENTIMENT:
            base_confidence += 0.05
        
        return min(1.0, max(0.0, base_confidence))
    
    def _parse_sentiment_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta de análisis de sentimiento"""
        # Buscar score numérico
        import re
        
        # Buscar patrones como "score: 0.7" o "positive (0.8)"
        score_patterns = [
            r'score[:\s]+(-?\d+\.?\d*)',
            r'positive[:\s]+(\d+\.?\d*)',
            r'negative[:\s]+(\d+\.?\d*)',
            r'neutral[:\s]+(\d+\.?\d*)',
            r'([0-1]\.?\d*)'
        ]
        
        score = 0.0
        label = "neutral"
        
        for pattern in score_patterns:
            match = re.search(pattern, response.lower())
            if match:
                score = float(match.group(1))
                break
        
        # Determinar etiqueta
        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"
        
        return {
            "sentiment_score": max(-1.0, min(1.0, score)),
            "sentiment_label": label,
            "explanation": response
        }
    
    def _parse_topics_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta de análisis de topics"""
        # Extraer topics de la respuesta
        topics = []
        if ',' in response:
            topics = [topic.strip() for topic in response.split(',')[:10]]
        else:
            # Buscar líneas que parezcan topics
            lines = response.split('\n')
            for line in lines:
                if line.strip() and len(line.strip()) < 50:
                    topics.append(line.strip())
        
        return {
            "topics": topics[:10],  # Máximo 10 topics
            "topic_count": len(topics),
            "extraction_method": "ai_analysis"
        }
    
    def _parse_summary_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta de resumen"""
        return {
            "summary": response,
            "summary_length": len(response),
            "extraction_method": "ai_generated"
        }
    
    def _parse_relevance_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta de relevancia"""
        import re
        
        # Buscar score numérico
        score_patterns = [
            r'relevance[:\s]+(\d+\.?\d*)',
            r'score[:\s]+(\d+\.?\d*)',
            r'([0-1]\.?\d*)'
        ]
        
        score = 0.5  # Score por defecto
        
        for pattern in score_patterns:
            match = re.search(pattern, response.lower())
            if match:
                score = float(match.group(1))
                break
        
        # Asegurar que el score esté en rango 0-1
        score = max(0.0, min(1.0, score))
        
        return {
            "relevance_score": score,
            "explanation": response
        }
    
    def _parse_bias_response(self, response: str) -> Dict[str, Any]:
        """Parsea respuesta de análisis de sesgo"""
        import re
        
        # Buscar score numérico
        score_patterns = [
            r'bias[:\s]+(\d+\.?\d*)',
            r'score[:\s]+(\d+\.?\d*)',
            r'([0-1]\.?\d*)'
        ]
        
        score = 0.0  # Por defecto sin sesgo
        
        for pattern in score_patterns:
            match = re.search(pattern, response.lower())
            if match:
                score = float(match.group(1))
                break
        
        return {
            "bias_score": max(0.0, min(1.0, score)),
            "explanation": response
        }
    
    def _get_sentiment_prompt(self) -> str:
        return """Analiza el sentimiento de esta noticia y proporciona:
1. Un score numérico entre -1.0 (muy negativo) y 1.0 (muy positivo)
2. Una etiqueta: positive, negative, o neutral
3. Una explicación breve del análisis

Responde en formato JSON:
{
    "sentiment_score": 0.7,
    "sentiment_label": "positive", 
    "explanation": "Análisis del tono..."
}"""
    
    def _get_topics_prompt(self) -> str:
        return """Identifica los temas principales de esta noticia:
1. Extrae 3-8 temas específicos (palabras clave o frases)
2. Los temas deben ser relevantes y específicos
3. Evita temas muy genéricos

Responde como lista separada por comas: tema1, tema2, tema3"""
    
    def _get_summary_prompt(self) -> str:
        return """Crea un resumen conciso de esta noticia en 2-3 oraciones:
1. Incluye los puntos principales
2. Mantén el contexto y significado
3. Sé objetivo y preciso

Responde solo con el resumen:"""
    
    def _get_relevance_prompt(self) -> str:
        return """Evalúa la relevancia de esta noticia:
1. Score entre 0.0 (no relevante) y 1.0 (muy relevante)
2. Considera: actualidad, impacto, importancia
3. Una explicación breve

Responde en formato JSON:
{
    "relevance_score": 0.8,
    "explanation": "Razones de la relevancia..."
}"""
    
    def _get_bias_prompt(self) -> str:
        return """Analiza el sesgo en esta noticia:
1. Score entre 0.0 (sin sesgo) y 1.0 (muy sesgada)
2. Considera: tono, selección de palabras, perspectiva
3. Una explicación del análisis

Responde en formato JSON:
{
    "bias_score": 0.2,
    "explanation": "Análisis del sesgo..."
}"""


class PostprocessingPipeline:
    """Pipeline de postprocesamiento - formateo final y almacenamiento"""
    
    def __init__(self, config: ProcessingConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    async def process_results(self, articles: List[Dict[str, Any]], 
                            analysis_results: List[AnalysisResult],
                            session: AsyncSession) -> Tuple[List[Article], List[str]]:
        """
        Procesa resultados finales y almacena en base de datos
        
        Args:
            articles: Artículos procesados
            analysis_results: Resultados de análisis
            session: Sesión de base de datos
            
        Returns:
            Tuple de (saved_articles, error_messages)
        """
        self.logger.info(f"Iniciando postprocesamiento de {len(articles)} artículos")
        
        saved_articles = []
        error_messages = []
        
        # Agrupar resultados por artículo
        results_by_article = defaultdict(list)
        for result in analysis_results:
            results_by_article[result.article_id].append(result)
        
        # Procesar cada artículo
        for article_data in articles:
            try:
                article_id = str(uuid.uuid4())
                
                # Crear objeto Article
                article = await self._create_article_from_data(article_data, article_id, session)
                
                # Agregar resultados de análisis
                if article_id in results_by_article:
                    article = await self._add_analysis_to_article(
                        article, results_by_article[article_id], session
                    )
                
                saved_articles.append(article)
                
            except Exception as e:
                error_msg = f"Error guardando artículo {article_data.get('title', 'unknown')}: {str(e)}"
                error_messages.append(error_msg)
                self.logger.error(error_msg)
        
        # Confirmar cambios en base de datos
        try:
            await session.commit()
            self.logger.info(f"Postprocesamiento completado: {len(saved_articles)} artículos guardados")
        except Exception as e:
            await session.rollback()
            error_msg = f"Error confirmando transacción: {str(e)}"
            error_messages.append(error_msg)
            self.logger.error(error_msg)
        
        return saved_articles, error_messages
    
    async def _create_article_from_data(self, article_data: Dict[str, Any], 
                                      article_id: str, session: AsyncSession) -> Article:
        """Crea objeto Article desde datos normalizados"""
        
        # Buscar o crear fuente
        source_name = article_data.get('source_name', 'Unknown')
        source = await self._get_or_create_source(source_name, session)
        
        # Crear artículo
        article = Article(
            id=article_id,
            title=article_data.get('title', ''),
            content=article_data.get('content', ''),
            summary=article_data.get('description', ''),
            url=article_data.get('url', ''),
            published_at=article_data.get('published_at'),
            source_id=source.id,
            content_hash=article_data.get('content_hash', ''),
            created_at=datetime.now(timezone.utc)
        )
        
        session.add(article)
        return article
    
    async def _get_or_create_source(self, source_name: str, session: AsyncSession) -> Source:
        """Obtiene o crea fuente"""
        # Buscar fuente existente
        result = await session.execute(
            select(Source).where(Source.name == source_name)
        )
        source = result.scalar_one_or_none()
        
        if not source:
            # Crear nueva fuente
            source = Source(
                id=str(uuid.uuid4()),
                name=source_name,
                url=f"https://{source_name.lower().replace(' ', '')}.com",
                api_name='unknown',
                is_active=True,
                created_at=datetime.now(timezone.utc)
            )
            session.add(source)
        
        return source
    
    async def _add_analysis_to_article(self, article: Article, 
                                     analysis_results: List[AnalysisResult], 
                                     session: AsyncSession) -> Article:
        """Agrega resultados de análisis al artículo"""
        
        for result in analysis_results:
            if result.status != ProcessingStatus.COMPLETED:
                continue
            
            # Crear registro de análisis
            analysis_record = ArticleAnalysis(
                id=str(uuid.uuid4()),
                article_id=article.id,
                analysis_type=result.analysis_type.value,
                analysis_data=result.result,
                model_used=result.model_used,
                confidence_score=result.confidence_score,
                processed_at=datetime.now(timezone.utc)
            )
            session.add(analysis_record)
            
            # Actualizar campos específicos del artículo
            if result.analysis_type == AnalysisType.SUMMARY:
                summary_data = result.result.get('summary', '')
                if summary_data:
                    article.summary = summary_data
            
            elif result.analysis_type == AnalysisType.SENTIMENT:
                sentiment_data = result.result
                article.sentiment_score = sentiment_data.get('sentiment_score')
            
            elif result.analysis_type == AnalysisType.RELEVANCE:
                relevance_data = result.result
                article.relevance_score = relevance_data.get('relevance_score', 0.0)
            
            elif result.analysis_type == AnalysisType.BIAS:
                bias_data = result.result
                article.bias_score = bias_data.get('bias_score', 0.0)
        
        # Marcar artículo como procesado
        article.processed_at = datetime.now(timezone.utc)
        
        return article


class AIPipelineOrchestrator:
    """Orquestador principal del pipeline de IA"""
    
    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        
        # Inicializar pipelines
        self.preprocessing_pipeline = PreprocessingPipeline(self.config)
        self.ai_analysis_pipeline = AIAnalysisPipeline(self.config)
        self.postprocessing_pipeline = PostprocessingPipeline(self.config)
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
        # Estadísticas
        self.stats = defaultdict(int)
    
    async def process_articles_batch(self, raw_articles: List[Dict[str, Any]], 
                                   source_type: str = 'generic',
                                   session: AsyncSession = None) -> BatchResult:
        """
        Procesa lote completo de artículos a través del pipeline completo
        
        Args:
            raw_articles: Lista de artículos crudos
            source_type: Tipo de fuente ('newsapi', 'guardian', etc.)
            session: Sesión de base de datos opcional
            
        Returns:
            Resultado del procesamiento por lotes
        """
        batch_id = str(uuid.uuid4())
        start_time = asyncio.get_event_loop().time()
        
        self.logger.info(f"Iniciando procesamiento de lote {batch_id[:8]} con {len(raw_articles)} artículos")
        
        try:
            # FASE 1: Preprocesamiento
            self.logger.info("FASE 1: Preprocesamiento")
            processed_articles, failed_articles = await self.preprocessing_pipeline.process_articles(
                raw_articles, source_type
            )
            
            self.stats['total_processed_preprocessing'] += len(processed_articles)
            self.stats['total_failed_preprocessing'] += len(failed_articles)
            
            if not processed_articles:
                raise Exception("No se pudieron procesar artículos en preprocesamiento")
            
            # FASE 2: Análisis de IA
            self.logger.info("FASE 2: Análisis de IA")
            analysis_results = await self.ai_analysis_pipeline.analyze_articles(processed_articles)
            
            successful_analyses = sum(1 for r in analysis_results if r.status == ProcessingStatus.COMPLETED)
            failed_analyses = len(analysis_results) - successful_analyses
            
            self.stats['total_successful_analyses'] += successful_analyses
            self.stats['total_failed_analyses'] += failed_analyses
            
            # FASE 3: Postprocesamiento y almacenamiento
            if session:
                self.logger.info("FASE 3: Postprocesamiento y almacenamiento")
                saved_articles, error_messages = await self.postprocessing_pipeline.process_results(
                    processed_articles, analysis_results, session
                )
                
                self.stats['total_saved_articles'] += len(saved_articles)
                self.stats['total_storage_errors'] += len(error_messages)
            else:
                saved_articles = []
                error_messages = ["No hay sesión de base de datos disponible"]
            
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            # Crear resultado final
            result = BatchResult(
                batch_id=batch_id,
                total_articles=len(raw_articles),
                successful_analyses=len(analysis_results),
                failed_analyses=failed_analyses,
                processing_time=processing_time,
                results=analysis_results,
                errors=error_messages,
                metadata={
                    'preprocessing_stats': {
                        'processed': len(processed_articles),
                        'failed': len(failed_articles)
                    },
                    'analysis_stats': {
                        'total_results': len(analysis_results),
                        'success_rate': successful_analyses / len(analysis_results) if analysis_results else 0
                    },
                    'storage_stats': {
                        'saved_articles': len(saved_articles),
                        'storage_errors': len(error_messages)
                    }
                }
            )
            
            self.logger.info(f"Lote {batch_id[:8]} completado en {processing_time:.2f}s")
            return result
            
        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            processing_time = end_time - start_time
            
            error_result = BatchResult(
                batch_id=batch_id,
                total_articles=len(raw_articles),
                successful_analyses=0,
                failed_analyses=len(raw_articles),
                processing_time=processing_time,
                errors=[str(e)],
                metadata={'error': str(e)}
            )
            
            self.logger.error(f"Error en lote {batch_id[:8]}: {str(e)}")
            self.stats['total_batch_errors'] += 1
            
            return error_result
    
    async def process_single_article(self, raw_article: Dict[str, Any], 
                                   source_type: str = 'generic',
                                   session: AsyncSession = None) -> AnalysisResult:
        """
        Procesa un artículo individual
        
        Args:
            raw_article: Artículo crudo
            source_type: Tipo de fuente
            session: Sesión de base de datos
            
        Returns:
            Resultado del análisis
        """
        # Procesar como lote de un elemento
        results = await self.process_articles_batch(
            [raw_article], source_type, session
        )
        
        # Retornar el primer resultado de análisis exitoso
        if results.results:
            return results.results[0]
        else:
            # Crear resultado de error
            return AnalysisResult(
                article_id="",
                analysis_type=AnalysisType.SENTIMENT,
                result={},
                confidence_score=0.0,
                model_used="",
                processing_time=0.0,
                error_message="No se pudo procesar el artículo",
                status=ProcessingStatus.FAILED
            )
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de procesamiento"""
        return {
            'config': {
                'batch_size': self.config.batch_size,
                'max_concurrent_batches': self.config.max_concurrent_batches,
                'max_concurrent_analyses': self.config.max_concurrent_analyses,
                'enable_parallel_processing': self.config.enable_parallel_processing
            },
            'stats': dict(self.stats),
            'performance_metrics': {
                'avg_processing_time_per_article': (
                    self.stats.get('total_processing_time', 0) / 
                    max(1, self.stats.get('total_processed_articles', 1))
                )
            }
        }
    
    def reset_stats(self):
        """Reinicia estadísticas"""
        self.stats.clear()
        self.logger.info("Estadísticas reiniciadas")


# Funciones de utilidad para uso externo

async def create_pipeline(config: ProcessingConfig = None) -> AIPipelineOrchestrator:
    """Factory function para crear pipeline"""
    return AIPipelineOrchestrator(config)


async def process_news_batch(raw_articles: List[Dict[str, Any]], 
                           source_type: str = 'generic',
                           config: ProcessingConfig = None,
                           session: AsyncSession = None) -> BatchResult:
    """
    Función de conveniencia para procesar lote de noticias
    
    Args:
        raw_articles: Lista de artículos crudos
        source_type: Tipo de fuente
        config: Configuración personalizada
        session: Sesión de base de datos
        
    Returns:
        Resultado del procesamiento
    """
    pipeline = await create_pipeline(config)
    return await pipeline.process_articles_batch(raw_articles, source_type, session)


async def process_single_news(raw_article: Dict[str, Any], 
                            source_type: str = 'generic',
                            config: ProcessingConfig = None,
                            session: AsyncSession = None) -> AnalysisResult:
    """
    Función de conveniencia para procesar noticia individual
    
    Args:
        raw_article: Artículo crudo
        source_type: Tipo de fuente  
        config: Configuración personalizada
        session: Sesión de base de datos
        
    Returns:
        Resultado del análisis
    """
    pipeline = await create_pipeline(config)
    return await pipeline.process_single_article(raw_article, source_type, session)


# Configuración por defecto para diferentes casos de uso
DEFAULT_CONFIGS = {
    'development': ProcessingConfig(
        batch_size=5,
        max_concurrent_batches=2,
        max_concurrent_analyses=5,
        analysis_timeout=20
    ),
    'production': ProcessingConfig(
        batch_size=20,
        max_concurrent_batches=10,
        max_concurrent_analyses=25,
        analysis_timeout=45
    ),
    'high_throughput': ProcessingConfig(
        batch_size=50,
        max_concurrent_batches=20,
        max_concurrent_analyses=50,
        analysis_timeout=60,
        enable_parallel_processing=True
    )
}