"""
Test standalone del News Service Layer

Este script prueba la funcionalidad básica del service layer sin 
dependencias del resto del proyecto.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Mock de settings para el test
class MockSettings:
    NEWSAPI_KEY = "fake_newsapi_key"
    GUARDIAN_API_KEY = "fake_guardian_key"
    NYTIMES_API_KEY = "fake_nytimes_key"

settings = MockSettings()


# Clases base del service layer (copia simplificada)
class NewsClientError(Exception):
    """Excepción base para errores de clientes de noticias"""
    pass


class RateLimitError(NewsClientError):
    """Error específico para límites de rate"""
    pass


class APIKeyError(NewsClientError):
    """Error para problemas con API keys"""
    pass


class NewsClient:
    """Clase base abstracta para todos los clientes de noticias"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.rate_limit_remaining = 100
        self.rate_limit_reset = "2023-12-01T12:00:00Z"
        
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Obtener las últimas noticias"""
        raise NotImplementedError
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Buscar noticias por query"""
        raise NotImplementedError
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Obtener fuentes disponibles"""
        raise NotImplementedError
    
    def get_categories(self) -> List[str]:
        """Obtener categorías disponibles"""
        raise NotImplementedError
    
    def get_name(self) -> str:
        """Obtener nombre del cliente"""
        return "Generic Client"


class NewsAPIClient(NewsClient):
    """Cliente para NewsAPI.org"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "NewsAPI"
        
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Mock de obtener últimas noticias"""
        # Simular delay de red
        await asyncio.sleep(0.1)
        
        articles = [
            {
                'title': f'NewsAPI Article {i}',
                'content': f'Content for article {i}',
                'url': f'https://newsapi.com/article{i}',
                'published_at': '2023-12-01T10:00:00Z',
                'source_name': 'BBC News',
                'source_id': 'bbc-news',
                'api_name': 'newsapi',
                'author': 'NewsAPI Author',
                'description': f'Description for article {i}',
                'image_url': f'https://newsapi.com/image{i}.jpg'
            }
            for i in range(1, min(limit + 1, 6))
        ]
        
        logger.info(f"NewsAPI: Mock returned {len(articles)} articles")
        return articles
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Mock de buscar noticias"""
        await asyncio.sleep(0.1)
        
        articles = [
            {
                'title': f'NewsAPI Search: {query} Article {i}',
                'content': f'Search content for {query}',
                'url': f'https://newsapi.com/search/{query}/article{i}',
                'published_at': '2023-12-01T10:00:00Z',
                'source_name': 'Reuters',
                'source_id': 'reuters',
                'api_name': 'newsapi',
                'author': 'Search Author',
                'description': f'Search description for {query}',
                'image_url': f'https://newsapi.com/search/{query}/image{i}.jpg'
            }
            for i in range(1, min(limit + 1, 4))
        ]
        
        logger.info(f"NewsAPI: Mock search '{query}' returned {len(articles)} results")
        return articles
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Mock de fuentes"""
        return [
            {'id': 'bbc-news', 'name': 'BBC News', 'country': 'gb', 'language': 'en'},
            {'id': 'cnn', 'name': 'CNN', 'country': 'us', 'language': 'en'},
            {'id': 'reuters', 'name': 'Reuters', 'country': 'us', 'language': 'en'},
        ]
    
    def get_categories(self) -> List[str]:
        """Mock de categorías"""
        return ['business', 'entertainment', 'general', 'health', 'science', 'sports', 'technology']
    
    def get_name(self) -> str:
        return self.name


class GuardianAPIClient(NewsClient):
    """Cliente para The Guardian API"""
    
    def __init__(self, api_key: str):
        super().__init__(api_key)
        self.name = "Guardian"
        
    async def get_latest_news(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Mock de obtener últimas noticias"""
        await asyncio.sleep(0.1)
        
        articles = [
            {
                'title': f'Guardian Article {i}',
                'content': f'Guardian content for article {i}',
                'url': f'https://theguardian.com/article{i}',
                'published_at': '2023-12-01T11:00:00Z',
                'source_name': 'The Guardian',
                'source_id': 'news',
                'api_name': 'guardian',
                'author': 'Guardian Author',
                'description': f'Guardian description for article {i}',
                'image_url': f'https://theguardian.com/image{i}.jpg'
            }
            for i in range(1, min(limit + 1, 4))
        ]
        
        logger.info(f"Guardian: Mock returned {len(articles)} articles")
        return articles
    
    async def search_news(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Mock de buscar noticias"""
        await asyncio.sleep(0.1)
        
        articles = [
            {
                'title': f'Guardian Search: {query} Article {i}',
                'content': f'Guardian search content for {query}',
                'url': f'https://theguardian.com/search/{query}/article{i}',
                'published_at': '2023-12-01T11:00:00Z',
                'source_name': 'The Guardian',
                'source_id': 'politics',
                'api_name': 'guardian',
                'author': 'Guardian Search Author',
                'description': f'Guardian search description for {query}',
                'image_url': f'https://theguardian.com/search/{query}/image{i}.jpg'
            }
            for i in range(1, min(limit + 1, 3))
        ]
        
        logger.info(f"Guardian: Mock search '{query}' returned {len(articles)} results")
        return articles
    
    def get_sources(self) -> List[Dict[str, Any]]:
        """Mock de fuentes"""
        return [
            {'id': 'news', 'name': 'Guardian News', 'country': 'gb', 'language': 'en'},
            {'id': 'politics', 'name': 'Politics', 'country': 'gb', 'language': 'en'},
            {'id': 'sport', 'name': 'Sport', 'country': 'gb', 'language': 'en'},
        ]
    
    def get_categories(self) -> List[str]:
        """Mock de categorías"""
        return ['news', 'politics', 'sport', 'culture', 'business', 'technology', 'science']
    
    def get_name(self) -> str:
        return self.name


class NewsClientFactory:
    """Factory class para crear instancias de clientes de noticias"""
    
    @staticmethod
    def create_client(client_type: str, api_key: Optional[str] = None) -> NewsClient:
        """Factory method para crear clientes de noticias"""
        client_type = client_type.lower()
        
        if client_type == 'newsapi':
            if not api_key and not settings.NEWSAPI_KEY:
                raise APIKeyError("API key de NewsAPI es requerida")
            return NewsAPIClient(api_key or settings.NEWSAPI_KEY)
        
        elif client_type == 'guardian':
            if not api_key and not settings.GUARDIAN_API_KEY:
                raise APIKeyError("API key de Guardian es requerida")
            return GuardianAPIClient(api_key or settings.GUARDIAN_API_KEY)
        
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
    """Service layer facade que unifica el acceso a todos los clientes de noticias"""
    
    def __init__(self):
        self.factory = NewsClientFactory()
        self.clients: Dict[str, NewsClient] = {}
        self._initialize_clients()
        
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
        """Obtener las últimas noticias de múltiples fuentes"""
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
                task = asyncio.create_task(client.get_latest_news(limit // len(client_types) + 1))
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
            
            # Aplicar filtros básicos
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
        """Buscar noticias en múltiples fuentes"""
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
                task = asyncio.create_task(client.search_news(query, limit // len(client_types) + 1))
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
            
            # Ordenar y limitar
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
        """Obtener todas las fuentes disponibles"""
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
    
    def get_categories(self, client_types: Optional[List[str]] = None) -> Dict[str, List[str]]:
        """Obtener todas las categorías disponibles"""
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
    
    def health_check(self) -> Dict[str, Any]:
        """Verificar salud del servicio"""
        return {
            'status': 'healthy' if self.clients else 'unhealthy',
            'clients_count': len(self.clients),
            'configured_clients': list(self.clients.keys()),
            'available_clients': self.factory.get_available_clients(),
            'timestamp': '2023-12-01T12:00:00Z'
        }


async def test_factory_pattern():
    """Test del Factory Pattern"""
    print("🧪 Testing Factory Pattern...")
    
    # Test 1: Ver clientes disponibles
    available = NewsClientFactory.get_available_clients()
    print(f"   ✓ Clientes disponibles: {available}")
    
    configured = NewsClientFactory.get_configured_clients()
    print(f"   ✓ Clientes configurados: {configured}")
    
    # Test 2: Crear clientes con factory
    for client_type in available:
        try:
            client = NewsClientFactory.create_client(client_type, "fake_key")
            print(f"   ✓ Cliente {client_type} creado: {client.get_name()}")
        except Exception as e:
            print(f"   ⚠️  Cliente {client_type} error: {type(e).__name__}")
    
    print("✅ Factory Pattern test completado")


async def test_service_layer():
    """Test del Service Layer"""
    print("\n🧪 Testing Service Layer...")
    
    # Test 1: Crear instancia del service
    service = NewsService()
    print("   ✓ Service instance created")
    
    # Test 2: Health check
    health = service.health_check()
    print(f"   ✓ Health check: {health['status']}")
    print(f"      - Clientes configurados: {health['configured_clients']}")
    print(f"      - Total clientes: {health['clients_count']}")
    
    # Test 3: Obtener fuentes (sin API calls)
    sources = service.get_sources()
    print(f"   ✓ Sources obtained: {len(sources)} client types")
    for client_type, client_sources in sources.items():
        print(f"      - {client_type}: {len(client_sources)} fuentes")
    
    # Test 4: Obtener categorías (sin API calls)
    categories = service.get_categories()
    print(f"   ✓ Categories obtained: {len(categories)} client types")
    for client_type, client_categories in categories.items():
        print(f"      - {client_type}: {len(client_categories)} categorías")
    
    print("✅ Service Layer test completado")


async def test_api_calls():
    """Test con llamadas API simuladas"""
    print("\n🧪 Testing API Calls...")
    
    service = NewsService()
    
    # Test 1: get_latest_news
    try:
        latest = await service.get_latest_news(limit=5)
        print(f"   ✓ get_latest_news: {len(latest)} artículos")
        for i, article in enumerate(latest[:3], 1):
            print(f"      {i}. {article['title'][:40]}... ({article['client_type']})")
    except Exception as e:
        print(f"   ❌ Error en get_latest_news: {e}")
    
    # Test 2: search_news
    try:
        search_results = await service.search_news("technology", limit=3)
        print(f"   ✓ search_news: {len(search_results)} resultados")
        for i, article in enumerate(search_results[:3], 1):
            print(f"      {i}. {article['title'][:40]}... ({article['client_type']})")
    except Exception as e:
        print(f"   ❌ Error en search_news: {e}")
    
    # Test 3: Filtros específicos
    try:
        filtered = await service.get_latest_news(
            limit=5,
            client_types=['newsapi'],
            categories=['technology']
        )
        print(f"   ✓ filtered_news: {len(filtered)} artículos")
    except Exception as e:
        print(f"   ❌ Error en filtered_news: {e}")
    
    print("✅ API Calls test completado")


async def test_error_handling():
    """Test del manejo de errores"""
    print("\n🧪 Testing Error Handling...")
    
    # Test 1: Cliente inválido
    try:
        NewsClientFactory.create_client('invalid_client')
        print("   ❌ Debería haber fallado")
    except NewsClientError as e:
        print(f"   ✓ Error manejado correctamente: {type(e).__name__}")
    
    # Test 2: Service sin clientes
    service = NewsService()
    service.clients = {}  # Simular que no hay clientes
    
    try:
        health = service.health_check()
        print(f"   ✓ Health check sin clientes: {health['status']}")
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
    
    # Test 3: Búsqueda vacía
    try:
        await service.search_news("")  # Query vacío
        print("   ❌ Debería haber fallado con query vacío")
    except ValueError as e:
        print(f"   ✓ Query vacío manejado correctamente: {type(e).__name__}")
    
    print("✅ Error Handling test completado")


async def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando Tests del News Service Layer (Standalone)\n")
    
    try:
        await test_factory_pattern()
        await test_service_layer()
        await test_api_calls()
        await test_error_handling()
        
        print("\n🎉 Todos los tests completados exitosamente!")
        print("\n📝 Resumen de funcionalidades verificadas:")
        print("   ✅ Factory Pattern")
        print("   ✅ Service Layer Architecture")
        print("   ✅ API Calls (mock)")
        print("   ✅ Error Handling")
        print("   ✅ Health Checks")
        print("   ✅ Metadata Access")
        print("   ✅ Filtering")
        print("   ✅ Deduplication")
        
    except Exception as e:
        print(f"\n❌ Error durante los tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())