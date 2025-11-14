"""
Cliente Python para la API de NewsAPI.

Este cliente proporciona métodos para interactuar con NewsAPI.org,
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


class NewsAPIClient:
    """Cliente para NewsAPI.org."""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str, requests_session: Optional[requests.Session] = None):
        """
        Inicializa el cliente de NewsAPI.
        
        Args:
            api_key: API key para NewsAPI
            requests_session: Sesión de requests reutilizable (opcional)
        """
        self.api_key = api_key
        self.session = requests_session or requests.Session()
        self.rate_limiter = RateLimiter()
        
        # Headers por defecto
        self.session.headers.update({
            "X-API-Key": self.api_key,
            "User-Agent": "AI-News-Aggregator/1.0"
        })
    
    def _make_request_sync(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una petición síncrona."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "error":
                raise ValueError(f"NewsAPI Error: {data.get('message')}")
            return data
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError("Rate limit exceeded")
        else:
            response.raise_for_status()
    
    async def _make_request_async(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una petición asíncrona."""
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, 
                params=params,
                headers={"X-API-Key": self.api_key, "User-Agent": "AI-News-Aggregator/1.0"}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get("status") == "error":
                        raise ValueError(f"NewsAPI Error: {data.get('message')}")
                    return data
                elif response.status == 429:
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    response.raise_for_status()
    
    @retry_on_failure()
    def get_top_headlines_sync(
        self, 
        country: str = "us", 
        category: Optional[str] = None,
        q: Optional[str] = None,
        page_size: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las principales noticias de forma síncrona.
        
        Args:
            country: Código de país (us, gb, fr, de, it, es, ru, jp, cn, au, br, mx, ca)
            category: Categoría (business, entertainment, general, health, science, sports, technology)
            q: Término de búsqueda
            page_size: Número de artículos por página
            page: Número de página
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "country": country,
            "pageSize": page_size,
            "page": page
        }
        
        if category:
            params["category"] = category
        if q:
            params["q"] = q
        
        data = self._make_request_sync("top-headlines", params)
        return data.get("articles", [])
    
    @retry_on_failure()
    async def get_top_headlines_async(
        self, 
        country: str = "us", 
        category: Optional[str] = None,
        q: Optional[str] = None,
        page_size: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las principales noticias de forma asíncrona.
        
        Args:
            country: Código de país
            category: Categoría
            q: Término de búsqueda
            page_size: Número de artículos por página
            page: Número de página
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "country": country,
            "pageSize": page_size,
            "page": page
        }
        
        if category:
            params["category"] = category
        if q:
            params["q"] = q
        
        data = await self._make_request_async("top-headlines", params)
        return data.get("articles", [])
    
    @retry_on_failure()
    def search_everything_sync(
        self,
        q: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
        page: int = 1,
        sources: Optional[str] = None,
        domains: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca noticias por término de forma síncrona.
        
        Args:
            q: Término de búsqueda
            from_date: Fecha de inicio (YYYY-MM-DD)
            to_date: Fecha de fin (YYYY-MM-DD)
            language: Idioma (ar, de, en, es, fr, he, it, nl, no, pt, ru, sv, ud, zh)
            sort_by: Ordenamiento (relevancy, popularity, publishedAt)
            page_size: Número de artículos por página
            page: Número de página
            sources: Fuentes separadas por comas
            domains: Dominios separados por comas
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "q": q,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page
        }
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if sources:
            params["sources"] = sources
        if domains:
            params["domains"] = domains
        
        data = self._make_request_sync("everything", params)
        return data.get("articles", [])
    
    @retry_on_failure()
    async def search_everything_async(
        self,
        q: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "en",
        sort_by: str = "publishedAt",
        page_size: int = 20,
        page: int = 1,
        sources: Optional[str] = None,
        domains: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca noticias por término de forma asíncrona.
        
        Args:
            q: Término de búsqueda
            from_date: Fecha de inicio (YYYY-MM-DD)
            to_date: Fecha de fin (YYYY-MM-DD)
            language: Idioma
            sort_by: Ordenamiento
            page_size: Número de artículos por página
            page: Número de página
            sources: Fuentes separadas por comas
            domains: Dominios separados por comas
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "q": q,
            "language": language,
            "sortBy": sort_by,
            "pageSize": page_size,
            "page": page
        }
        
        if from_date:
            params["from"] = from_date
        if to_date:
            params["to"] = to_date
        if sources:
            params["sources"] = sources
        if domains:
            params["domains"] = domains
        
        data = await self._make_request_async("everything", params)
        return data.get("articles", [])
    
    @retry_on_failure()
    def get_sources_sync(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene las fuentes disponibles de forma síncrona.
        
        Args:
            category: Categoría de noticias
            language: Idioma de la fuente
            country: País de la fuente
            
        Returns:
            Lista de fuentes de noticias
        """
        params = {}
        
        if category:
            params["category"] = category
        if language:
            params["language"] = language
        if country:
            params["country"] = country
        
        data = self._make_request_sync("sources", params)
        return data.get("sources", [])
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()


# Funciones de conveniencia
def create_newsapi_client(api_key: str) -> NewsAPIClient:
    """
    Factory function para crear un cliente de NewsAPI.
    
    Args:
        api_key: API key para NewsAPI
        
    Returns:
        Instancia del cliente NewsAPI
    """
    return NewsAPIClient(api_key)