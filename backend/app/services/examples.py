"""
Ejemplo de uso del News Service con Factory Pattern

Este archivo demuestra cómo utilizar el service layer unificado para acceder
a múltiples APIs de noticias de manera consistente.
"""

import asyncio
import logging
from typing import List

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar el service layer
from .news_service import NewsService, NewsClientFactory, news_service


async def ejemplo_uso_basico():
    """Ejemplo básico de uso del news service"""
    
    print("=== Ejemplo de Uso Básico del News Service ===\n")
    
    # 1. Verificar estado del servicio
    health_status = news_service.health_check()
    print(f"Estado del servicio: {health_status}")
    
    # 2. Obtener últimas noticias
    try:
        print("\n1. Obteniendo últimas noticias...")
        latest_news = await news_service.get_latest_news(limit=5)
        
        print(f"Encontradas {len(latest_news)} noticias:")
        for i, article in enumerate(latest_news, 1):
            print(f"   {i}. {article['title'][:60]}...")
            print(f"      Fuente: {article['source_name']} ({article['client_type']})")
            print(f"      URL: {article['url']}")
            
    except Exception as e:
        print(f"Error obteniendo últimas noticias: {e}")
    
    # 3. Buscar noticias
    try:
        print("\n2. Buscando noticias sobre 'artificial intelligence'...")
        search_results = await news_service.search_news(
            query="artificial intelligence", 
            limit=3
        )
        
        print(f"Encontrados {len(search_results)} resultados:")
        for i, article in enumerate(search_results, 1):
            print(f"   {i}. {article['title'][:60]}...")
            print(f"      Búsqueda: {article.get('search_query', 'N/A')}")
            
    except Exception as e:
        print(f"Error buscando noticias: {e}")
    
    # 4. Obtener fuentes
    print("\n3. Obteniendo fuentes disponibles...")
    sources = news_service.get_sources()
    
    for client_type, client_sources in sources.items():
        print(f"   {client_type}: {len(client_sources)} fuentes")
        for source in client_sources[:3]:  # Mostrar solo las primeras 3
            print(f"      - {source.get('name', 'N/A')} ({source.get('country', 'N/A')})")
    
    # 5. Obtener categorías
    print("\n4. Obteniendo categorías disponibles...")
    categories = news_service.get_categories()
    
    for client_type, client_categories in categories.items():
        print(f"   {client_type}: {', '.join(client_categories[:5])}...")
    
    # 6. Estado de clientes
    print("\n5. Estado de clientes...")
    client_status = news_service.get_client_status()
    
    for client_type, status in client_status.items():
        print(f"   {client_type}: {status['name']}")
        print(f"      API Key configurada: {status['api_key_configured']}")
        print(f"      Disponible: {status['available']}")


async def ejemplo_uso_avanzado():
    """Ejemplo avanzado con filtros y configuración específica"""
    
    print("\n=== Ejemplo de Uso Avanzado ===\n")
    
    # 1. Crear instancia personalizada del service
    custom_service = NewsService()
    
    # 2. Obtener noticias de clientes específicos
    try:
        print("1. Obteniendo noticias solo de NewsAPI y Guardian...")
        filtered_news = await custom_service.get_latest_news(
            limit=10,
            client_types=['newsapi', 'guardian'],
            categories=['technology', 'business']
        )
        
        print(f"Encontradas {len(filtered_news)} noticias filtradas:")
        for i, article in enumerate(filtered_news, 1):
            print(f"   {i}. {article['title'][:50]}...")
            print(f"      Cliente: {article['client_type']}, Fuente: {article['source_name']}")
            
    except Exception as e:
        print(f"Error con filtros avanzados: {e}")
    
    # 3. Búsqueda específica por cliente
    try:
        print("\n2. Búsqueda en NYTimes específicamente...")
        nytimes_results = await custom_service.search_news(
            query="machine learning",
            limit=5,
            client_types=['nytimes']
        )
        
        print(f"Resultados de NYTimes: {len(nytimes_results)}")
        for article in nytimes_results:
            print(f"   - {article['title'][:50]}...")
            
    except Exception as e:
        print(f"Error en búsqueda específica: {e}")


def ejemplo_factory_pattern():
    """Ejemplo del Factory Pattern"""
    
    print("\n=== Ejemplo del Factory Pattern ===\n")
    
    # 1. Mostrar clientes disponibles
    available_clients = NewsClientFactory.get_available_clients()
    print(f"Clientes disponibles: {available_clients}")
    
    # 2. Mostrar clientes configurados
    configured_clients = NewsClientFactory.get_configured_clients()
    print(f"Clientes configurados: {configured_clients}")
    
    # 3. Crear cliente específico usando factory
    try:
        if 'newsapi' in configured_clients:
            newsapi_client = NewsClientFactory.create_client('newsapi')
            print(f"Cliente creado: {newsapi_client.get_name()}")
            
            # Obtener fuentes del cliente específico
            sources = newsapi_client.get_sources()
            print(f"Fuentes de NewsAPI: {len(sources)}")
            
            # Obtener categorías
            categories = newsapi_client.get_categories()
            print(f"Categorías de NewsAPI: {', '.join(categories)}")
            
    except Exception as e:
        print(f"Error creando cliente con factory: {e}")


async def main():
    """Función principal para ejecutar todos los ejemplos"""
    
    print("Iniciando ejemplos del News Service Layer...\n")
    
    # Verificar que tenemos al menos un cliente configurado
    if not news_service.clients:
        print("⚠️  No hay clientes de noticias configurados.")
        print("   Configure las API keys en las variables de entorno:")
        print("   - NEWSAPI_KEY")
        print("   - GUARDIAN_API_KEY") 
        print("   - NYTIMES_API_KEY")
        return
    
    # Ejecutar ejemplos
    await ejemplo_uso_basico()
    await ejemplo_uso_avanzado()
    ejemplo_factory_pattern()
    
    print("\n✅ Ejemplos completados exitosamente")


if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(main())