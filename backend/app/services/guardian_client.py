"""
Cliente Python para Guardian API.

Este cliente proporciona métodos para interactuar con The Guardian API,
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
    
    def __init__(self, calls_per_minute: int = 200):
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


class GuardianAPIClient:
    """Cliente para The Guardian API."""
    
    BASE_URL = "https://content.guardianapis.com"
    
    # Categorías disponibles en Guardian
    CATEGORIES = [
        "world", "politics", "business", "technology", "sport", 
        "football", "culture", "lifeandstyle", "science", "environment",
        "education", "media", "stage", "film", "music", "books",
        "artanddesign", "tv-and-radio"
    ]
    
    def __init__(self, api_key: str, requests_session: Optional[requests.Session] = None):
        """
        Inicializa el cliente de Guardian API.
        
        Args:
            api_key: API key para Guardian API
            requests_session: Sesión de requests reutilizable (opcional)
        """
        self.api_key = api_key
        self.session = requests_session or requests.Session()
        self.rate_limiter = RateLimiter()
        
        # Headers por defecto
        self.session.headers.update({
            "User-Agent": "AI-News-Aggregator/1.0"
        })
    
    def _make_request_sync(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una petición síncrona."""
        self.rate_limiter.wait_if_needed()
        
        params["api-key"] = self.api_key
        url = f"{self.BASE_URL}/{endpoint}"
        response = self.session.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if "response" in data:
                if not data["response"].get("status", "ok") == "ok":
                    raise ValueError(f"Guardian API Error: {data['response'].get('message', 'Unknown error')}")
                return data["response"]
            else:
                return data
        elif response.status_code == 429:
            raise requests.exceptions.HTTPError("Rate limit exceeded")
        else:
            response.raise_for_status()
    
    async def _make_request_async(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza una petición asíncrona."""
        self.rate_limiter.wait_if_needed()
        
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
                    if "response" in data:
                        if not data["response"].get("status", "ok") == "ok":
                            raise ValueError(f"Guardian API Error: {data['response'].get('message', 'Unknown error')}")
                        return data["response"]
                    else:
                        return data
                elif response.status == 429:
                    raise aiohttp.ClientError("Rate limit exceeded")
                else:
                    response.raise_for_status()
    
    @retry_on_failure()
    def search_content_sync(
        self,
        q: Optional[str] = None,
        section: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: str = "newest",
        page_size: int = 20,
        page: int = 1,
        show_fields: Optional[List[str]] = None,
        show_tags: Optional[List[str]] = None,
        show_blocked: str = "none"
    ) -> List[Dict[str, Any]]:
        """
        Busca contenido en Guardian de forma síncrona.
        
        Args:
            q: Término de búsqueda
            section: Sección específica (world, politics, business, etc.)
            from_date: Fecha de inicio (YYYY-MM-DD)
            to_date: Fecha de fin (YYYY-MM-DD)
            order_by: Ordenamiento (newest, oldest, relevance)
            page_size: Número de artículos por página
            page: Número de página
            show_fields: Campos adicionales a mostrar
            show_tags: Tags a mostrar
            show_blocked: Qué contenido bloqueado mostrar
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "order-by": order_by,
            "page-size": page_size,
            "page": page,
            "show-blocked": show_blocked
        }
        
        if q:
            params["q"] = q
        if section:
            params["section"] = section
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date
        if show_fields:
            params["show-fields"] = ",".join(show_fields)
        if show_tags:
            params["show-tags"] = ",".join(show_tags)
        
        data = self._make_request_sync("search", params)
        return data.get("results", [])
    
    @retry_on_failure()
    async def search_content_async(
        self,
        q: Optional[str] = None,
        section: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: str = "newest",
        page_size: int = 20,
        page: int = 1,
        show_fields: Optional[List[str]] = None,
        show_tags: Optional[List[str]] = None,
        show_blocked: str = "none"
    ) -> List[Dict[str, Any]]:
        """
        Busca contenido en Guardian de forma asíncrona.
        
        Args:
            q: Término de búsqueda
            section: Sección específica
            from_date: Fecha de inicio
            to_date: Fecha de fin
            order_by: Ordenamiento
            page_size: Número de artículos por página
            page: Número de página
            show_fields: Campos adicionales a mostrar
            show_tags: Tags a mostrar
            show_blocked: Qué contenido bloqueado mostrar
            
        Returns:
            Lista de artículos de noticias
        """
        params = {
            "order-by": order_by,
            "page-size": page_size,
            "page": page,
            "show-blocked": show_blocked
        }
        
        if q:
            params["q"] = q
        if section:
            params["section"] = section
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date
        if show_fields:
            params["show-fields"] = ",".join(show_fields)
        if show_tags:
            params["show-tags"] = ",".join(show_tags)
        
        data = await self._make_request_async("search", params)
        return data.get("results", [])
    
    @retry_on_failure()
    def get_content_by_category_sync(
        self,
        section: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: str = "newest",
        page_size: int = 20,
        page: int = 1,
        show_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene contenido por categoría de forma síncrona.
        
        Args:
            section: Categoría (world, politics, business, technology, sport, etc.)
            from_date: Fecha de inicio
            to_date: Fecha de fin
            order_by: Ordenamiento
            page_size: Número de artículos por página
            page: Número de página
            show_fields: Campos adicionales a mostrar
            
        Returns:
            Lista de artículos de noticias
        """
        default_fields = ["headline", "trailText", "byline", "thumbnail", "shortUrl"]
        
        if show_fields is None:
            show_fields = default_fields
        else:
            show_fields = list(set(show_fields + default_fields))
        
        params = {
            "order-by": order_by,
            "page-size": page_size,
            "page": page,
            "section": section,
            "show-fields": ",".join(show_fields)
        }
        
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date
        
        data = self._make_request_sync("search", params)
        return data.get("results", [])
    
    @retry_on_failure()
    async def get_content_by_category_async(
        self,
        section: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        order_by: str = "newest",
        page_size: int = 20,
        page: int = 1,
        show_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene contenido por categoría de forma asíncrona.
        
        Args:
            section: Categoría
            from_date: Fecha de inicio
            to_date: Fecha de fin
            order_by: Ordenamiento
            page_size: Número de artículos por página
            page: Número de página
            show_fields: Campos adicionales a mostrar
            
        Returns:
            Lista de artículos de noticias
        """
        default_fields = ["headline", "trailText", "byline", "thumbnail", "shortUrl"]
        
        if show_fields is None:
            show_fields = default_fields
        else:
            show_fields = list(set(show_fields + default_fields))
        
        params = {
            "order-by": order_by,
            "page-size": page_size,
            "page": page,
            "section": section,
            "show-fields": ",".join(show_fields)
        }
        
        if from_date:
            params["from-date"] = from_date
        if to_date:
            params["to-date"] = to_date
        
        data = await self._make_request_async("search", params)
        return data.get("results", [])
    
    @retry_on_failure()
    def get_content_by_id_sync(
        self,
        content_id: str,
        show_fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene contenido específico por ID de forma síncrona.
        
        Args:
            content_id: ID del contenido
            show_fields: Campos adicionales a mostrar
            
        Returns:
            Detalles del contenido o None si no se encuentra
        """
        default_fields = ["headline", "trailText", "byline", "thumbnail", "shortUrl", 
                         "body", "bodyText", "publication", "webPublicationDate", "webUrl"]
        
        if show_fields is None:
            show_fields = default_fields
        else:
            show_fields = list(set(show_fields + default_fields))
        
        params = {
            "show-fields": ",".join(show_fields)
        }
        
        data = self._make_request_sync(f"search/{content_id}", params)
        return data.get("content")
    
    @retry_on_failure()
    async def get_content_by_id_async(
        self,
        content_id: str,
        show_fields: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene contenido específico por ID de forma asíncrona.
        
        Args:
            content_id: ID del contenido
            show_fields: Campos adicionales a mostrar
            
        Returns:
            Detalles del contenido o None si no se encuentra
        """
        default_fields = ["headline", "trailText", "byline", "thumbnail", "shortUrl", 
                         "body", "bodyText", "publication", "webPublicationDate", "webUrl"]
        
        if show_fields is None:
            show_fields = default_fields
        else:
            show_fields = list(set(show_fields + default_fields))
        
        params = {
            "show-fields": ",".join(show_fields)
        }
        
        data = await self._make_request_async(f"search/{content_id}", params)
        return data.get("content")
    
    @retry_on_failure()
    def get_tags_sync(
        self,
        tag_type: Optional[str] = None,
        q: Optional[str] = None,
        page_size: int = 20,
        page: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Obtiene tags disponibles de forma síncrona.
        
        Args:
            tag_type: Tipo de tag (keyword, contributor, series, etc.)
            q: Término de búsqueda para tags
            page_size: Número de tags por página
            page: Número de página
            
        Returns:
            Lista de tags
        """
        params = {
            "page-size": page_size,
            "page": page
        }
        
        if tag_type:
            params["type"] = tag_type
        if q:
            params["q"] = q
        
        data = self._make_request_sync("tags", params)
        return data.get("results", [])
    
    def get_available_categories(self) -> List[str]:
        """Retorna la lista de categorías disponibles."""
        return self.CATEGORIES.copy()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()


# Funciones de conveniencia
def create_guardian_client(api_key: str) -> GuardianAPIClient:
    """
    Factory function para crear un cliente de Guardian API.
    
    Args:
        api_key: API key para Guardian API
        
    Returns:
        Instancia del cliente Guardian API
    """
    return GuardianAPIClient(api_key)