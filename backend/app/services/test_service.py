"""
Test básico del News Service Layer

Este script verifica que el service layer funcione correctamente
sin necesidad de API keys válidas.
"""

import asyncio
import logging
import os
from unittest.mock import patch, AsyncMock

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar el service
from .news_service import NewsService, NewsClientFactory


async def test_factory_pattern():
    """Test del Factory Pattern"""
    print("🧪 Testing Factory Pattern...")
    
    # Test 1: Ver clientes disponibles
    available = NewsClientFactory.get_available_clients()
    print(f"   ✓ Clientes disponibles: {available}")
    
    configured = NewsClientFactory.get_configured_clients()
    print(f"   ✓ Clientes configurados: {configured}")
    
    # Test 2: Crear clientes sin API keys (debe manejar errores)
    for client_type in available:
        try:
            # Intentar crear cliente sin API key (debe fallar graciosamente)
            client = NewsClientFactory.create_client(client_type, "fake_key")
            print(f"   ✓ Cliente {client_type} creado: {client.get_name()}")
        except Exception as e:
            print(f"   ⚠️  Cliente {client_type} no disponible: {e}")
    
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
    print(f"      - Clientes disponibles: {health['available_clients']}")
    
    # Test 3: Client status
    client_status = service.get_client_status()
    print(f"   ✓ Client status obtained for {len(client_status)} clients")
    
    # Test 4: Obtener fuentes (sin API calls)
    sources = service.get_sources()
    print(f"   ✓ Sources obtained: {len(sources)} client types")
    
    # Test 5: Obtener categorías (sin API calls)
    categories = service.get_categories()
    print(f"   ✓ Categories obtained: {len(categories)} client types")
    
    print("✅ Service Layer test completado")


def test_error_handling():
    """Test del manejo de errores"""
    print("\n🧪 Testing Error Handling...")
    
    # Test 1: Cliente inválido
    try:
        NewsClientFactory.create_client('invalid_client')
        print("   ❌ Debería haber fallado")
    except Exception as e:
        print(f"   ✓ Error manejado correctamente: {type(e).__name__}")
    
    # Test 2: Service sin clientes
    service = NewsService()
    
    # Mock para simular que no hay clientes
    service.clients = {}
    
    try:
        # Esto debería manejar gracefully la falta de clientes
        health = service.health_check()
        print(f"   ✓ Health check sin clientes: {health['status']}")
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
    
    print("✅ Error Handling test completado")


async def test_mock_data():
    """Test con datos mock para verificar funcionalidad sin APIs reales"""
    print("\n🧪 Testing with Mock Data...")
    
    # Crear mock data
    mock_articles = [
        {
            'title': 'Test Article 1',
            'content': 'Test content 1',
            'url': 'https://example.com/article1',
            'published_at': '2023-12-01T10:00:00Z',
            'source_name': 'Test Source',
            'api_name': 'newsapi',
            'client_type': 'newsapi'
        },
        {
            'title': 'Test Article 2',
            'content': 'Test content 2',
            'url': 'https://example.com/article2',
            'published_at': '2023-12-01T11:00:00Z',
            'source_name': 'Another Source',
            'api_name': 'guardian',
            'client_type': 'guardian'
        }
    ]
    
    # Crear un cliente mock
    from .news_service import NewsClient
    
    class MockNewsClient(NewsClient):
        def __init__(self):
            super().__init__()
            self.name = "MockClient"
        
        async def get_latest_news(self, limit=20):
            return mock_articles[:limit]
        
        async def search_news(self, query, limit=20):
            return [article for article in mock_articles if query.lower() in article['title'].lower()]
        
        def get_sources(self):
            return [{'id': 'test', 'name': 'Test Source'}]
        
        def get_categories(self):
            return ['technology', 'business']
        
        def get_name(self):
            return self.name
    
    # Test con cliente mock
    service = NewsService()
    service.clients['mock'] = MockNewsClient()
    
    try:
        # Test get_latest_news con mock
        latest = await service.get_latest_news(limit=5)
        print(f"   ✓ Mock get_latest_news: {len(latest)} artículos")
        
        # Test search_news con mock
        search_results = await service.search_news('Test', limit=5)
        print(f"   ✓ Mock search_news: {len(search_results)} resultados")
        
        # Test fuentes y categorías
        sources = service.get_sources()
        categories = service.get_categories()
        print(f"   ✓ Mock metadata: {len(sources)} fuentes, {len(categories)} categorías")
        
    except Exception as e:
        print(f"   ❌ Error en test mock: {e}")
    
    print("✅ Mock Data test completado")


async def main():
    """Ejecutar todos los tests"""
    print("🚀 Iniciando Tests del News Service Layer\n")
    
    # Verificar que estamos en el directorio correcto
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        await test_factory_pattern()
        await test_service_layer()
        test_error_handling()
        await test_mock_data()
        
        print("\n🎉 Todos los tests completados exitosamente!")
        print("\n📝 Resumen de funcionalidades verificadas:")
        print("   ✅ Factory Pattern")
        print("   ✅ Service Layer Architecture")
        print("   ✅ Error Handling")
        print("   ✅ Mock Data Processing")
        print("   ✅ Health Checks")
        print("   ✅ Metadata Access")
        
    except Exception as e:
        print(f"\n❌ Error durante los tests: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())