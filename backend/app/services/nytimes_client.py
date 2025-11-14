"""
Cliente Python para NYTimes API.

Este cliente proporciona métodos para interactuar con The New York Times API,
incluyendo obtener noticias por categoría, búsqueda por término,
manejo de errores, rate limiting y retry logic.
"""

import aiohttp
import requests
import asyncio
import logging
from typing import Dict, List, Optional, Any
from time import time, sleep
from functools import wraps
from urllib.parse import quote


logger = logging.getLogger(__name__)


class RateLimiter:
    """Implementa rate limiting usando token bucket algorithm."""
    
    def __init__(self, calls_per_minute: int = 100):
        self.calls_per_minute = calls_per_minute
        self.calls = []
    
    def wait_if_needed(self):
        """Espera si es necesario para respetar el rate limit."""
        now = time()
        # Remover calls más antiguos que 1 minuto
        self.calls = [call_time for call_time in self.calls if now - call_time < 60]
        
        if len(self.calls) >= self.calls_per_minute:
            sleep_time = 60 - (now - self.calls[0]) + 1
            if sleep_time > 0:
                logger.info(f"Rate limit alcanzado, esperando {sleep_time:.2f} segundos")
                sleep(sleep_time)
        
        self.calls.append(now)


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator para implementar retry logic."""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(self, *args, **kwargs)
                except (aiohttp.ClientError, requests.exceptions.RequestError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(f"Intento {attempt + 1} falló: {e}. Reintentando en {wait_time} segundos...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Todos los intentos fallaron después de {max_retries + 1} intentos")
            
            raise last_exception
        
        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(self, *args, **kwargs)
                except (aiohttp.ClientError, requests.exceptions.RequestError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        wait_time = delay * (backoff_factor ** attempt)
                        logger.warning(f"Intento {attempt + 1} falló: {e}. Reintentando en {wait_time} segundos...")
                        sleep(wait_time)
                    else:
                        logger.error(f"Todos los intentos fallaron después de {max_retries + 1} intentos")
            
            raise last_exception
        
        # Determinar si es método async o sync basado en la función original
        if asyncio.iscoroutinefunction(func):
            return wrapper
        else:
            return sync_wrapper
    
    return decorator


class NYTimesAPIClient:
    """Cliente para The New York Times API."""
    
    BASE_URL = "https://api.nytimes.com/svc"
    
    # Endpoints disponibles
    ENDPOINTS = {
        "top_stories": "topstories/v2/{section}.json",
        "most_popular": "mostpopular/v2/{period}.json",
        "article_search": "search/v2/articlesearch.json",
        "books": "books/v3/lists/{date}.json",
        "movie_reviews": "movies/v2/reviews/{review_type}.json"
    }
    
    # Categorías para top stories
    SECTIONS = [
        "home", "world", "national", "politics", "business", "technology",
        "science", "health", "sports", "arts", "books", "movies",
        "theater", "fashion", "food", "travel", "opinion"
    ]
    
    def __init__(self, api_key: str, requests_session: Optional[requests.Session] = None):
        """
        Inicializa el cliente de NYTimes API.
        
        Args:
            api_key: API key para NYTimes API
            requests_session: Sesión de requests reutilizable (opcional)
        """
        self.api_key = api_key
        self.session = requests_session or requests.Session()
        self.rate_limiter = RateLimiter()
        
        # Headers por defecto
        self.session.headers.update({
            "User-Agent": "AI-News-Aggregator/1.0"
        })
    
    def _make_request_sync(self, endpoint_template: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Realiza una petición síncrona."""
        self.rate_limiter.wait_if_needed()
        
        # Formatear el endpoint con parámetros adicionales
        endpoint = endpoint_template.format(**kwargs)
        
        params["api-key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "ERROR":
                raise ValueError(f"NYTimes API Error: {data.get('message', 'Unknown error')}")
            return data
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError("Rate limit exceeded")
        else:
            response.raise_for_status()
    
    async def _make_request_async(self, endpoint_template: str, params: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Realiza una petición asíncrona."""
        self.rate_limiter.wait_if_needed()
        
        # Formatear el endpoint con parámetros adicionales
        endpoint = endpoint_template.format(**kwargs)
        
        params["api-key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                params=params,
                headers={"User-Agent": "AI-News-Aggregator/1.0"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "ERROR":
                        raise ValueError(f"NYTimes API Error: {data.get('message', 'Unknown error')}")
                    return data
                elif response.status == 429:
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    response.raise_for_status()
    
    @retry_on_failure()
    def get_top_stories_sync(
        self,
        section: str = "home",
        date_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historias destacadas de forma síncrona.
        
        Args:
            section: Sección (home, world, national, politics, etc.)
            date_range: Rango de fechas opcional (YYYYMMDD-YYYYMMDD)
            
        Returns:
            Lista de artículos de noticias destacadas
        """
        params = {}
        
        if date_range:
            params["date"] = date_range
        
        data = self._make_request_sync(
            self.ENDPOINTS["top_stories"], 
            params, 
            section=section
        )
        return data.get("results", [])
    
    @retry_on_failure()
    async def get_top_stories_async(
        self,
        section: str = "home",
        date_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene historias destacadas de forma asíncrona.
        
        Args:
            section: Sección
            date_range: Rango de fechas opcional
            
        Returns:
            Lista de artículos de noticias destacadas
        """
        params = {}
        
        if date_range:
            params["date"] = date_range
        
        data = await self._make_request_async(
            self.ENDPOINTS["top_stories"], 
            params, 
            section=section
        )
        return data.get("results", [])
    
    @retry_on_failure()
    def get_most_popular_sync(
        self,
        period: int = 1,
        date_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene artículos más populares de forma síncrona.
        
        Args:
            period: Período (1=1 día, 7=7 días, 30=30 días)
            date_range: Rango de fechas opcional (YYYYMMDD-YYYYMMDD)
            
        Returns:
            Lista de artículos populares
        """
        params = {}
        
        if date_range:
            params["date"] = date_range
        
        data = self._make_request_sync(
            self.ENDPOINTS["most_popular"], 
            params, 
            period=str(period)
        )
        return data.get("results", [])
    
    @retry_on_failure()
    async def get_most_popular_async(
        self,
        period: int = 1,
        date_range: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene artículos más populares de forma asíncrona.
        
        Args:
            period: Período
            date_range: Rango de fechas opcional
            
        Returns:
            Lista de artículos populares
        """
        params = {}
        
        if date_range:
            params["date"] = date_range
        
        data = await self._make_request_async(
            self.ENDPOINTS["most_popular"], 
            params, 
            period=str(period)
        )
        return data.get("results", [])
    
    @retry_on_failure()
    def search_articles_sync(
        self,
        q: str,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: str = "newest",
        page: int = 0,
        fl: Optional[List[str]] = None,
        fq: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca artículos por término de forma síncrona.
        
        Args:
            q: Término de búsqueda
            begin_date: Fecha de inicio (YYYYMMDD)
            end_date: Fecha de fin (YYYYMMDD)
            sort: Ordenamiento (newest, oldest, relevance)
            page: Número de página
            fl: Campos a retornar
            fq: Filtros adicionales (fq syntax)
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "q": q,
            "sort": sort,
            "page": page
        }
        
        if begin_date:
            params["begin_date"] = begin_date
        if end_date:
            params["end_date"] = end_date
        if fl:
            params["fl"] = ",".join(fl)
        if fq:
            params["fq"] = fq
        
        data = self._make_request_sync(
            self.ENDPOINTS["article_search"], 
            params
        )
        return data.get("response", {}).get("docs", [])
    
    @retry_on_failure()
    async def search_articles_async(
        self,
        q: str,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: str = "newest",
        page: int = 0,
        fl: Optional[List[str]] = None,
        fq: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca artículos por término de forma asíncrona.
        
        Args:
            q: Término de búsqueda
            begin_date: Fecha de inicio
            end_date: Fecha de fin
            sort: Ordenamiento
            page: Número de página
            fl: Campos a retornar
            fq: Filtros adicionales
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "q": q,
            "sort": sort,
            "page": page
        }
        
        if begin_date:
            params["begin_date"] = begin_date
        if end_date:
            params["end_date"] = end_date
        if fl:
            params["fl"] = ",".join(fl)
        if fq:
            params["fq"] = fq
        
        data = await self._make_request_async(
            self.ENDPOINTS["article_search"], 
            params
        )
        return data.get("response", {}).get("docs", [])
    
    @retry_on_failure()
    def get_articles_by_category_sync(
        self,
        section: str,
        date_range: Optional[str] = None,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene artículos por categoría de forma síncrona.
        
        Args:
            section: Sección (home, world, politics, etc.)
            date_range: Rango de fechas opcional
            page_size: Número de artículos
            
        Returns:
            Lista de artículos de noticias
        """
        # Para categorías, usamos top stories de la sección específica
        params = {}
        
        if date_range:
            params["date"] = date_range
        
        data = self._make_request_sync(
            self.ENDPOINTS["top_stories"], 
            params, 
            section=section
        )
        results = data.get("results", [])
        
        # Limitar el número de resultados si es necesario
        if page_size < len(results):
            return results[:page_size]
        
        return results
    
    @retry_on_failure()
    async def get_articles_by_category_async(
        self,
        section: str,
        date_range: Optional[str] = None,
        page_size: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Obtiene artículos por categoría de forma asíncrona.
        
        Args:
            section: Sección
            date_range: Rango de fechas opcional
            page_size: Número de artículos
            
        Returns:
            Lista de artículos de noticias
        """
        # Para categorías, usamos top stories de la sección específica
        params = {}
        
        if date_range:
            params["date"] = date_range
        
        data = await self._make_request_async(
            self.ENDPOINTS["top_stories"], 
            params, 
            section=section
        )
        results = data.get("results", [])
        
        # Limitar el número de resultados si es necesario
        if page_size < len(results):
            return results[:page_size]
        
        return results
    
    @retry_on_failure()
    def get_article_by_uri_sync(
        self,
        uri: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un artículo específico por URI de forma síncrona.
        
        Args:
            uri: URI del artículo
            
        Returns:
            Detalles del artículo o None si no se encuentra
        """
        # Los URIs tienen formato: "/2024/01/15/world/europe/ukraine"
        # Para obtener un artículo específico, necesitamos usar search con fq
        fq = f'uri:("{uri}")'
        
        params = {
            "fq": fq,
            "fl": "headline,abstract,lead_paragraph,web_url,pub_date,section_name,byline"
        }
        
        data = self._make_request_sync(
            self.ENDPOINTS["article_search"], 
            params
        )
        results = data.get("response", {}).get("docs", [])
        
        return results[0] if results else None
    
    @retry_on_failure()
    async def get_article_by_uri_async(
        self,
        uri: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un artículo específico por URI de forma asíncrona.
        
        Args:
            uri: URI del artículo
            
        Returns:
            Detalles del artículo o None si no se encuentra
        """
        # Los URIs tienen formato: "/2024/01/15/world/europe/ukraine"
        # Para obtener un artículo específico, necesitamos usar search con fq
        fq = f'uri:("{uri}")'
        
        params = {
            "fq": fq,
            "fl": "headline,abstract,lead_paragraph,web_url,pub_date,section_name,byline"
        }
        
        data = await self._make_request_async(
            self.ENDPOINTS["article_search"], 
            params
        )
        results = data.get("response", {}).get("docs", [])
        
        return results[0] if results else None
    
    def get_available_sections(self) -> List[str]:
        """Retorna la lista de secciones disponibles."""
        return self.SECTIONS.copy()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()


# Funciones de conveniencia
def create_nytimes_client(api_key: str) -> NYTimesAPIClient:
    """
    Factory function para crear un cliente de NYTimes API.
    
    Args:
        api_key: API key para NYTimes API
        
    Returns:
        Instancia del cliente NYTimes API
    """
    return NYTimesAPIClient(api_key)