"""
News Service Layer with Factory Pattern for AI News Aggregator
Este módulo implementa un service layer que actúa como facade para todos los clientes de noticias,
utilizando el patrón Factory para crear instancias según la configuración.
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib

from ..core.config import settings

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsClientError(Exception):
    """Excepción base para errores de clientes de noticias"""
    pass


class RateLimitError(NewsClientError):
    """Error específico para límites de rate"""
    pass


class APIKeyError(NewsClientError):
    """Error para problemas con API keys"""
    pass


class NewsClient(ABC):
    """Clase base abstracta para todos los clientes de noticias"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.rate_limit_remaining = 100
        self.rate_limit_reset = datetime.now()
        
    @abstractmethod
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener las últimas noticias"""
        pass
    
    @abstractmethod
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Buscar noticias por query"""
        pass
    
    @abstractmethod
    def get_sources(self) -> List[Dict[str, Any]]:
        """Obtener fuentes disponibles"""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """Obtener categorías disponibles"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Obtener nombre del cliente"""
        pass


class NewsAPIClient(NewsClient):
    """Cliente para NewsAPI.org"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://newsapi.org/v2"
        self.name = "NewsAPI"
        
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener últimas noticias de NewsAPI"""
        try:
            import aiohttp
            
            headers = {
                'X-API-Key': self.api_key,
                'User-Agent': 'AI-News-Aggregator/1.0'
            }
            
            params = {
                'pageSize': min(limit, 100),
                'language': 'en',
                'sortBy': 'publishedAt'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/top-headlines",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitError("NewsAPI rate limit exceeded")
                    elif response.status == 401:
                        raise APIKeyError("NewsAPI API key inválida")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('articles', []):
                        processed_article = {
                            'title': article.get('title', ''),
                            'content': article.get('content', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt'),
                            'source_name': article.get('source', {}).get('name', ''),
                            'source_id': article.get('source', {}).get('id', ''),
                            'api_name': 'newsapi',
                            'author': article.get('author'),
                            'description': article.get('description'),
                            'image_url': article.get('urlToImage')
                        }
                        articles.append(processed_article)
                    
                    logger.info(f"NewsAPI: Obtenidas {len(articles)} noticias")
                    return articles[:limit]
                    
        except Exception as e:
            logger.error(f"Error en NewsAPI get_latest_news: {str(e)}")
            raise NewsClientError(f"Error al obtener noticias de NewsAPI: {str(e)}")
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Buscar noticias en NewsAPI"""
        try:
            import aiohttp
            
            headers = {
                'X-API-Key': self.api_key,
                'User-Agent': 'AI-News-Aggregator/1.0'
            }
            
            params = {
                'q': query,
                'pageSize': min(limit, 100),
                'language': 'en',
                'sortBy': 'publishedAt',
                'from': (datetime.now() - timedelta(days=30)).isoformat()
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/everything",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitError("NewsAPI rate limit exceeded")
                    elif response.status == 401:
                        raise APIKeyError("NewsAPI API key inválida")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('articles', []):
                        processed_article = {
                            'title': article.get('title', ''),
                            'content': article.get('content', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('publishedAt'),
                            'source_name': article.get('source', {}).get('name', ''),
                            'source_id': article.get('source', {}).get('id', ''),
                            'api_name': 'newsapi',
                            'author': article.get('author'),
                            'description': article.get('description'),
                            'image_url': article.get('urlToImage')
                        }
                        articles.append(processed_article)
                    
                    logger.info(f"NewsAPI: Búsqueda '{query}' encontró {len(articles)} resultados")
                    return articles[:limit]
                    
        except Exception as e:
            logger.error(f"Error en NewsAPI search_news: {str(e)}")
            raise NewsClientError(f"Error al buscar noticias en NewsAPI: {str(e)}")
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Obtener fuentes de NewsAPI"""
        try:
            # Lista de fuentes comunes de NewsAPI
            return [
                {'id': 'bbc-news', 'name': 'BBC News', 'country': 'gb', 'language': 'en'},
                {'id': 'cnn', 'name': 'CNN', 'country': 'us', 'language': 'en'},
                {'id': 'reuters', 'name': 'Reuters', 'country': 'us', 'language': 'en'},
                {'id': 'the-wall-street-journal', 'name': 'Wall Street Journal', 'country': 'us', 'language': 'en'},
                {'id': 'the-new-york-times', 'name': 'New York Times', 'country': 'us', 'language': 'en'},
                {'id': 'the-guardian-uk', 'name': 'The Guardian', 'country': 'gb', 'language': 'en'},
                {'id': 'associated-press', 'name': 'Associated Press', 'country': 'us', 'language': 'en'},
                {'id': 'abc-news', 'name': 'ABC News', 'country': 'us', 'language': 'en'},
                {'id': 'nbc-news', 'name': 'NBC News', 'country': 'us', 'language': 'en'},
                {'id': 'cbs-news', 'name': 'CBS News', 'country': 'us', 'language': 'en'},
            ]
        except Exception as e:
            logger.error(f"Error obteniendo fuentes de NewsAPI: {str(e)}")
            return []
    
    def get_categories(self) -> List[str]:
        """Obtener categorías de NewsAPI"""
        return [
            'business', 'entertainment', 'general', 'health', 
            'science', 'sports', 'technology'
        ]
    
    def get_name(self) -> str:
        return self.name


class GuardianAPIClient(NewsClient):
    """Cliente para The Guardian API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://content.guardianapis.com"
        self.name = "Guardian"
        
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener últimas noticias de The Guardian"""
        try:
            import aiohttp
            
            headers = {
                'User-Agent': 'AI-News-Aggregator/1.0'
            }
            
            params = {
                'api-key': self.api_key,
                'page-size': min(limit, 200),
                'section': 'news',
                'order-by': 'newest',
                'show-fields': 'headline,bodyText,byline,thumbnail'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitError("Guardian API rate limit exceeded")
                    elif response.status == 401:
                        raise APIKeyError("Guardian API key inválida")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('response', {}).get('results', []):
                        processed_article = {
                            'title': article.get('webTitle', ''),
                            'content': article.get('fields', {}).get('bodyText', ''),
                            'url': article.get('webUrl', ''),
                            'published_at': article.get('webPublicationDate'),
                            'source_name': 'The Guardian',
                            'source_id': article.get('sectionName', '').lower(),
                            'api_name': 'guardian',
                            'author': article.get('fields', {}).get('byline'),
                            'description': article.get('fields', {}).get('headline'),
                            'image_url': article.get('fields', {}).get('thumbnail')
                        }
                        articles.append(processed_article)
                    
                    logger.info(f"Guardian: Obtenidas {len(articles)} noticias")
                    return articles[:limit]
                    
        except Exception as e:
            logger.error(f"Error en Guardian get_latest_news: {str(e)}")
            raise NewsClientError(f"Error al obtener noticias de Guardian: {str(e)}")
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Buscar noticias en The Guardian"""
        try:
            import aiohttp
            
            headers = {
                'User-Agent': 'AI-News-Aggregator/1.0'
            }
            
            params = {
                'api-key': self.api_key,
                'q': query,
                'page-size': min(limit, 200),
                'order-by': 'newest',
                'show-fields': 'headline,bodyText,byline,thumbnail'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitError("Guardian API rate limit exceeded")
                    elif response.status == 401:
                        raise APIKeyError("Guardian API key inválida")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('response', {}).get('results', []):
                        processed_article = {
                            'title': article.get('webTitle', ''),
                            'content': article.get('fields', {}).get('bodyText', ''),
                            'url': article.get('webUrl', ''),
                            'published_at': article.get('webPublicationDate'),
                            'source_name': 'The Guardian',
                            'source_id': article.get('sectionName', '').lower(),
                            'api_name': 'guardian',
                            'author': article.get('fields', {}).get('byline'),
                            'description': article.get('fields', {}).get('headline'),
                            'image_url': article.get('fields', {}).get('thumbnail')
                        }
                        articles.append(processed_article)
                    
                    logger.info(f"Guardian: Búsqueda '{query}' encontró {len(articles)} resultados")
                    return articles[:limit]
                    
        except Exception as e:
            logger.error(f"Error en Guardian search_news: {str(e)}")
            raise NewsClientError(f"Error al buscar noticias en Guardian: {str(e)}")
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Obtener fuentes de The Guardian"""
        return [
            {'id': 'news', 'name': 'Guardian News', 'country': 'gb', 'language': 'en'},
            {'id': 'politics', 'name': 'Politics', 'country': 'gb', 'language': 'en'},
            {'id': 'sport', 'name': 'Sport', 'country': 'gb', 'language': 'en'},
            {'id': 'culture', 'name': 'Culture', 'country': 'gb', 'language': 'en'},
            {'id': 'business', 'name': 'Business', 'country': 'gb', 'language': 'en'},
            {'id': 'technology', 'name': 'Technology', 'country': 'gb', 'language': 'en'},
            {'id': 'science', 'name': 'Science', 'country': 'gb', 'language': 'en'},
            {'id': 'environment', 'name': 'Environment', 'country': 'gb', 'language': 'en'},
        ]
    
    def get_categories(self) -> List[str]:
        """Obtener categorías de The Guardian"""
        return [
            'news', 'politics', 'sport', 'culture', 'business', 
            'technology', 'science', 'environment', 'education',
            'media', 'society', 'law', 'global'
        ]
    
    def get_name(self) -> str:
        return self.name


class NYTimesAPIClient(NewsClient):
    """Cliente para New York Times API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.base_url = "https://api.nytimes.com/svc"
        self.name = "NYTimes"
        
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener últimas noticias de NY Times"""
        try:
            import aiohttp
            
            headers = {
                'User-Agent': 'AI-News-Aggregator/1.0'
            }
            
            params = {
                'api-key': self.api_key
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/news/v3/content/all/all.json",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitError("NYTimes API rate limit exceeded")
                    elif response.status == 401:
                        raise APIKeyError("NYTimes API key inválida")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('results', [])[:limit]:
                        processed_article = {
                            'title': article.get('title', ''),
                            'content': article.get('abstract', ''),
                            'url': article.get('url', ''),
                            'published_at': article.get('published_date'),
                            'source_name': 'New York Times',
                            'source_id': article.get('section', '').lower(),
                            'api_name': 'nytimes',
                            'author': ', '.join(article.get('byline', '').split(', ')[:2]),
                            'description': article.get('abstract', ''),
                            'image_url': article.get('multimedia', [{}])[0].get('url') if article.get('multimedia') else None
                        }
                        articles.append(processed_article)
                    
                    logger.info(f"NYTimes: Obtenidas {len(articles)} noticias")
                    return articles[:limit]
                    
        except Exception as e:
            logger.error(f"Error en NYTimes get_latest_news: {str(e)}")
            raise NewsClientError(f"Error al obtener noticias de NYTimes: {str(e)}")
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Buscar noticias en NY Times"""
        try:
            import aiohttp
            
            headers = {
                'User-Agent': 'AI-News-Aggregator/1.0'
            }
            
            params = {
                'api-key': self.api_key,
                'q': query,
                'page': 0,
                'sort': 'newest'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search/v2/articlesearch.json",
                    headers=headers,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 429:
                        raise RateLimitError("NYTimes API rate limit exceeded")
                    elif response.status == 401:
                        raise APIKeyError("NYTimes API key inválida")
                    
                    response.raise_for_status()
                    data = await response.json()
                    
                    articles = []
                    for article in data.get('response', {}).get('docs', [])[:limit]:
                        processed_article = {
                            'title': article.get('headline', {}).get('main', ''),
                            'content': article.get('abstract', ''),
                            'url': article.get('web_url', ''),
                            'published_at': article.get('pub_date'),
                            'source_name': 'New York Times',
                            'source_id': article.get('section_name', '').lower(),
                            'api_name': 'nytimes',
                            'author': ', '.join(article.get('byline', '').split(', ')[:2]),
                            'description': article.get('abstract', ''),
                            'image_url': None  # NYTimes no proporciona imágenes en search
                        }
                        articles.append(processed_article)
                    
                    logger.info(f"NYTimes: Búsqueda '{query}' encontró {len(articles)} resultados")
                    return articles[:limit]
                    
        except Exception as e:
            logger.error(f"Error en NYTimes search_news: {str(e)}")
            raise NewsClientError(f"Error al buscar noticias en NYTimes: {str(e)}")
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Obtener fuentes de NY Times"""
        return [
            {'id': 'all', 'name': 'All Sections', 'country': 'us', 'language': 'en'},
            {'id': 'world', 'name': 'World', 'country': 'us', 'language': 'en'},
            {'id': 'us', 'name': 'U.S.', 'country': 'us', 'language': 'en'},
            {'id': 'politics', 'name': 'Politics', 'country': 'us', 'language': 'en'},
            {'id': 'business', 'name': 'Business', 'country': 'us', 'language': 'en'},
            {'id': 'technology', 'name': 'Technology', 'country': 'us', 'language': 'en'},
            {'id': 'science', 'name': 'Science', 'country': 'us', 'language': 'en'},
            {'id': 'sports', 'name': 'Sports', 'country': 'us', 'language': 'en'},
        ]
    
    def get_categories(self) -> List[str]:
        """Obtener categorías de NY Times"""
        return [
            'world', 'us', 'politics', 'business', 'technology', 
            'science', 'sports', 'arts', 'books', 'fashion',
            'food', 'health', 'opinion', 'realestate', 'travel'
        ]
    
    def get_name(self) -> str:
        return self.name


class NewsClientFactory:
    """Factory class para crear instancias de clientes de noticias"""
    
    @staticmethod
    def create_client(client_type: str, api_key: Optional[str] = None) -> NewsClient:
        """
        Factory method para crear clientes de noticias
        
        Args:
            client_type: Tipo de cliente ('newsapi', 'guardian', 'nytimes')
            api_key: API key opcional
            
        Returns:
            Instancia del cliente de noticias
            
        Raises:
            NewsClientError: Si el tipo de cliente no es válido
        """
        client_type = client_type.lower()
        
        if client_type == 'newsapi':
            if not api_key and not settings.NEWSAPI_KEY:
                raise APIKeyError("API key de NewsAPI es requerida")
            return NewsAPIClient(api_key or settings.NEWSAPI_KEY)
        
        elif client_type == 'guardian':
            if not api_key and not settings.GUARDIAN_API_KEY:
                raise APIKeyError("API key de Guardian es requerida")
            return GuardianAPIClient(api_key or settings.GUARDIAN_API_KEY)
        
        elif client_type == 'nytimes':
            if not api_key and not settings.NYTIMES_API_KEY:
                raise APIKeyError("API key de NYTimes es requerida")
            return NYTimesAPIClient(api_key or settings.NYTIMES_API_KEY)
        
        else:
            raise NewsClientError(f"Tipo de cliente no válido: {client_type}")
    
    @staticmethod
    def get_available_clients() -> List[str]:
        """Obtener lista de clientes disponibles"""
        return ['newsapi', 'guardian', 'nytimes']
    
    @staticmethod
    def get_configured_clients() -> List[str]:
        """Obtener lista de clientes configurados con API keys válidas"""
        configured = []
        
        if settings.NEWSAPI_KEY:
            configured.append('newsapi')
        if settings.GUARDIAN_API_KEY:
            configured.append('guardian')
        if settings.NYTIMES_API_KEY:
            configured.append('nytimes')
            
        return configured


class NewsService:
    """
    Service layer facade que unifica el acceso a todos los clientes de noticias
    Implementa el patrón Facade para simplificar la interfaz de acceso a las APIs
    """
    
    def __init__(self):
        self.factory = NewsClientFactory()
        self.clients: Dict[str, NewsClient] = {}
        self._initialize_clients()
        self.executor = ThreadPoolExecutor(max_workers=5)
        
    def _initialize_clients(self):
        """Inicializar clientes configurados"""
        configured_clients = self.factory.get_configured_clients()
        
        for client_type in configured_clients:
            try:
                client = self.factory.create_client(client_type)
                self.clients[client_type] = client
                logger.info(f"Cliente {client_type} inicializado correctamente")
            except Exception as e:
                logger.warning(f"No se pudo inicializar cliente {client_type}: {str(e)}")
        
        if not self.clients:
            logger.warning("No se inicializó ningún cliente de noticias")
        else:
            logger.info(f"Clientes inicializados: {list(self.clients.keys())}")
    
    async def get_latest_news(
        self, 
        limit: int = 20, 
        sources: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        client_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtener las últimas noticias de múltiples fuentes
        
        Args:
            limit: Número máximo de artículos
            sources: Lista de fuentes específicas
            categories: Lista de categorías
            client_types: Tipos de clientes a usar
            
        Returns:
            Lista de artículos agregados de todas las fuentes
        """
        try:
            # Determinar qué clientes usar
            if client_types is None:
                client_types = list(self.clients.keys())
            else:
                client_types = [ct for ct in client_types if ct in self.clients]
            
            if not client_types:
                raise NewsClientError("No hay clientes disponibles para obtener noticias")
            
            # Recopilar noticias de todos los clientes en paralelo
            tasks = []
            for client_type in client_types:
                client = self.clients[client_type]
                task = asyncio.create_task(
                    self._safe_client_call(
                        client.get_latest_news, 
                        limit // len(client_types) + 1
                    )
                )
                tasks.append((client_type, task))
            
            # Esperar resultados
            all_articles = []
            for client_type, task in tasks:
                try:
                    articles = await task
                    # Agregar metadata del cliente
                    for article in articles:
                        article['client_type'] = client_type
                    all_articles.extend(articles)
                except Exception as e:
                    logger.warning(f"Error obteniendo noticias de {client_type}: {str(e)}")
                    continue
            
            # Aplicar filtros
            if sources:
                all_articles = [
                    article for article in all_articles
                    if any(source.lower() in article.get('source_name', '').lower() 
                          for source in sources)
                ]
            
            if categories:
                all_articles = [
                    article for article in all_articles
                    if any(category.lower() in article.get('source_id', '').lower() 
                          for category in categories)
                ]
            
            # Ordenar por fecha de publicación y limitar
            all_articles.sort(
                key=lambda x: x.get('published_at', ''), 
                reverse=True
            )
            result = all_articles[:limit]
            
            logger.info(f"get_latest_news: Retornando {len(result)} artículos de {len(client_types)} fuentes")
            return result
            
        except Exception as e:
            logger.error(f"Error en get_latest_news: {str(e)}")
            raise NewsClientError(f"Error obteniendo últimas noticias: {str(e)}")
    
    async def search_news(
        self, 
        query: str, 
        limit: int = 20,
        client_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Buscar noticias en múltiples fuentes
        
        Args:
            query: Término de búsqueda
            limit: Número máximo de resultados
            client_types: Tipos de clientes a usar
            
        Returns:
            Lista de artículos que coinciden con la búsqueda
        """
        try:
            if not query.strip():
                raise ValueError("El término de búsqueda no puede estar vacío")
            
            # Determinar qué clientes usar
            if client_types is None:
                client_types = list(self.clients.keys())
            else:
                client_types = [ct for ct in client_types if ct in self.clients]
            
            if not client_types:
                raise NewsClientError("No hay clientes disponibles para buscar noticias")
            
            # Buscar en paralelo en todos los clientes
            tasks = []
            for client_type in client_types:
                client = self.clients[client_type]
                task = asyncio.create_task(
                    self._safe_client_call(
                        client.search_news, 
                        query, 
                        limit // len(client_types) + 1
                    )
                )
                tasks.append((client_type, task))
            
            # Recopilar resultados
            all_articles = []
            for client_type, task in tasks:
                try:
                    articles = await task
                    # Agregar metadata del cliente
                    for article in articles:
                        article['client_type'] = client_type
                        article['search_query'] = query
                    all_articles.extend(articles)
                except Exception as e:
                    logger.warning(f"Error buscando en {client_type}: {str(e)}")
                    continue
            
            # Eliminar duplicados por URL
            seen_urls = set()
            unique_articles = []
            for article in all_articles:
                url = article.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_articles.append(article)
            
            # Ordenar por relevancia (más recientes primero) y limitar
            unique_articles.sort(
                key=lambda x: x.get('published_at', ''), 
                reverse=True
            )
            result = unique_articles[:limit]
            
            logger.info(f"search_news: '{query}' encontró {len(result)} artículos únicos")
            return result
            
        except Exception as e:
            logger.error(f"Error en search_news: {str(e)}")
            raise NewsClientError(f"Error buscando noticias: {str(e)}")
    
    def get_sources(self, client_types: Optional[List[str]] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Obtener todas las fuentes disponibles
        
        Args:
            client_types: Tipos de clientes a consultar
            
        Returns:
            Diccionario con fuentes por cliente
        """
        try:
            if client_types is None:
                client_types = list(self.clients.keys())
            else:
                client_types = [ct for ct in client_types if ct in self.clients]
            
            all_sources = {}
            for client_type in client_types:
                try:
                    client = self.clients[client_type]
                    sources = client.get_sources()
                    all_sources[client_type] = sources
                    logger.debug(f"Obtenidas {len(sources)} fuentes de {client_type}")
                except Exception as e:
                    logger.warning(f"Error obteniendo fuentes de {client_type}: {str(e)}")
                    all_sources[client_type] = []
            
            total_sources = sum(len(sources) for sources in all_sources.values())
            logger.info(f"get_sources: Total {total_sources} fuentes de {len(client_types)} clientes")
            return all_sources
            
        except Exception as e:
            logger.error(f"Error en get_sources: {str(e)}")
            return {}
    
    def get_categories(self, client_types: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """
        Obtener todas las categorías disponibles
        
        Args:
            client_types: Tipos de clientes a consultar
            
        Returns:
            Diccionario con categorías por cliente
        """
        try:
            if client_types is None:
                client_types = list(self.clients.keys())
            else:
                client_types = [ct for ct in client_types if ct in self.clients]
            
            all_categories = {}
            for client_type in client_types:
                try:
                    client = self.clients[client_type]
                    categories = client.get_categories()
                    all_categories[client_type] = categories
                    logger.debug(f"Obtenidas {len(categories)} categorías de {client_type}")
                except Exception as e:
                    logger.warning(f"Error obteniendo categorías de {client_type}: {str(e)}")
                    all_categories[client_type] = []
            
            logger.info(f"get_categories: Categorías de {len(client_types)} clientes")
            return all_categories
            
        except Exception as e:
            logger.error(f"Error en get_categories: {str(e)}")
            return {}
    
    async def _safe_client_call(self, func, *args, **kwargs):
        """Wrapper seguro para llamadas a clientes con timeout"""
        try:
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(self.executor, lambda: func(*args, **kwargs)),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"Timeout en llamada a {func.__name__}")
            raise NewsClientError(f"Timeout en {func.__name__}")
        except Exception as e:
            logger.error(f"Error en _safe_client_call: {str(e)}")
            raise
    
    def get_client_status(self) -> Dict[str, Dict[str, Any]]:
        """Obtener estado de todos los clientes"""
        status = {}
        for client_type, client in self.clients.items():
            status[client_type] = {
                'name': client.get_name(),
                'api_key_configured': bool(client.api_key),
                'rate_limit_remaining': getattr(client, 'rate_limit_remaining', 'N/A'),
                'rate_limit_reset': getattr(client, 'rate_limit_reset', 'N/A'),
                'available': True
            }
        return status
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar salud del servicio"""
        return {
            'status': 'healthy' if self.clients else 'unhealthy',
            'clients_count': len(self.clients),
            'configured_clients': list(self.clients.keys()),
            'available_clients': self.factory.get_available_clients(),
            'timestamp': datetime.utcnow().isoformat()
        }


# Instancia global del servicio
news_service = NewsService()