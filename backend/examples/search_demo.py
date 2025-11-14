#!/usr/bin/env python3
"""
Script de demostración del sistema de búsqueda avanzada
Muestra ejemplos de uso de todos los endpoints y funcionalidades
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any
from datetime import datetime


class SearchSystemDemo:
    """Demo del sistema de búsqueda avanzada"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def demo_all_features(self):
        """Demostrar todas las características del sistema"""
        print("🚀 Demo del Sistema de Búsqueda Avanzada")
        print("=" * 50)
        
        demos = [
            ("Filtros Disponibles", self.demo_available_filters),
            ("Búsqueda Básica", self.demo_basic_search),
            ("Búsqueda con Filtros", self.demo_filtered_search),
            ("Búsqueda por Sentimiento", self.demo_sentiment_search),
            ("Búsqueda por Fecha", self.demo_date_filtered_search),
            ("Búsqueda Trending", self.demo_trending_searches),
            ("Sugerencias de Búsqueda", self.demo_search_suggestions),
            ("Búsqueda Semántica", self.demo_semantic_search),
            ("Estadísticas de Búsqueda", self.demo_search_stats),
            ("Health Check", self.demo_health_check)
        ]
        
        for demo_name, demo_func in demos:
            print(f"\n📋 {demo_name}")
            print("-" * 30)
            
            try:
                await demo_func()
                print(f"✅ {demo_name} - Completado")
            except Exception as e:
                print(f"❌ {demo_name} - Error: {str(e)}")
            
            print()
            await asyncio.sleep(1)  # Pausa entre demos
    
    async def demo_available_filters(self):
        """Demostrar obtención de filtros disponibles"""
        url = f"{self.base_url}/search/filters"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                print("Filtros disponibles:")
                print(f"  📰 Fuentes: {len(data['filters']['sources'])} fuentes")
                for source in data['filters']['sources'][:5]:
                    print(f"    - {source}")
                
                print(f"  🏷️ Categorías: {len(data['filters']['categories'])} categorías")
                for category in data['filters']['categories'][:5]:
                    print(f"    - {category}")
                
                print(f"  😊 Sentimientos: {data['filters']['sentiment']}")
                
                # Mostrar rangos de fecha
                date_range = data['filters']['date_range']
                print(f"  📅 Rango de fechas:")
                print(f"    - Desde: {date_range['min']}")
                print(f"    - Hasta: {date_range['max']}")
                
            else:
                print(f"Error: {response.status}")
    
    async def demo_basic_search(self):
        """Demostrar búsqueda básica"""
        search_terms = [
            "artificial intelligence",
            "machine learning", 
            "quantum computing"
        ]
        
        for term in search_terms:
            url = f"{self.base_url}/search"
            params = {
                "q": term,
                "limit": 3
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Búsqueda: '{term}'")
                    print(f"  📊 Total resultados: {data['total']}")
                    print(f"  ⏱️ Tiempo: {data['search_time_ms']:.1f}ms")
                    
                    # Mostrar primeros 3 resultados
                    for i, result in enumerate(data['results'][:3], 1):
                        print(f"  {i}. {result['title'][:60]}...")
                        print(f"     📰 {result['source']} | ⭐ {result['relevance_score']:.2f}")
                        print(f"     😊 {result['sentiment_label']} | 🏷️ {', '.join(result['topic_tags'][:3])}")
                    
                else:
                    print(f"Error en búsqueda '{term}': {response.status}")
                
                await asyncio.sleep(0.5)
    
    async def demo_filtered_search(self):
        """Demostrar búsqueda con filtros avanzados"""
        url = f"{self.base_url}/search"
        params = {
            "q": "AI technology",
            "sentiment": "positive",
            "min_relevance": "0.8",
            "sort": "date",
            "limit": "5"
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                print("Búsqueda con filtros avanzados:")
                print(f"  🔍 Query: {data['query']}")
                print(f"  🔧 Filtros aplicados: {data['filters_applied']}")
                print(f"  📊 Total resultados: {data['total']}")
                
                for i, result in enumerate(data['results'], 1):
                    print(f"  {i}. {result['title']}")
                    print(f"     📅 {result['published_at']}")
                    print(f"     📰 {result['source']} | ⭐ {result['relevance_score']:.2f}")
                
            else:
                print(f"Error: {response.status}")
    
    async def demo_sentiment_search(self):
        """Demostrar búsqueda por sentimiento"""
        sentiments = ["positive", "negative", "neutral"]
        
        for sentiment in sentiments:
            url = f"{self.base_url}/search"
            params = {
                "q": "technology",
                "sentiment": sentiment,
                "limit": 3
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Sentimiento: {sentiment}")
                    print(f"  📊 Resultados: {data['total']}")
                    
                    for result in data['results']:
                        print(f"    - {result['title'][:50]}... (Score: {result['sentiment_score']:.2f})")
                    
                await asyncio.sleep(0.3)
    
    async def demo_date_filtered_search(self):
        """Demostrar búsqueda por rango de fechas"""
        url = f"{self.base_url}/search"
        params = {
            "q": "artificial intelligence",
            "date_from": "2024-11-01",
            "date_to": "2024-11-06",
            "sort": "date",
            "limit": 5
        }
        
        async with self.session.get(url, params=params) as response:
            if response.status == 200:
                data = await response.json()
                
                print("Búsqueda por fecha (última semana):")
                print(f"  📅 Rango: 2024-11-01 a 2024-11-06")
                print(f"  📊 Total resultados: {data['total']}")
                
                for i, result in enumerate(data['results'], 1):
                    pub_date = result['published_at']
                    print(f"  {i}. {result['title'][:60]}...")
                    print(f"     📅 {pub_date}")
                
            else:
                print(f"Error: {response.status}")
    
    async def demo_trending_searches(self):
        """Demostrar búsquedas trending"""
        timeframes = ["1h", "24h", "7d"]
        
        for timeframe in timeframes:
            url = f"{self.base_url}/search/trending"
            params = {
                "timeframe": timeframe,
                "limit": 5,
                "min_count": 1
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Trending ({timeframe}):")
                    for i, search in enumerate(data['searches'], 1):
                        print(f"  {i}. {search['query']} "
                              f"(📊 {search['count']} búsquedas | ⭐ {search['trend_score']:.2f})")
                    
                await asyncio.sleep(0.3)
    
    async def demo_search_suggestions(self):
        """Demostrar sugerencias de búsqueda"""
        partial_terms = ["artificial", "machine", "quantum", "AI", "deep"]
        
        for term in partial_terms:
            url = f"{self.base_url}/search/suggestions"
            params = {
                "q": term,
                "limit": 3
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Sugerencias para '{term}':")
                    for suggestion in data['suggestions']:
                        print(f"  🔹 {suggestion['text']} ({suggestion['type']}) - Score: {suggestion['score']:.2f}")
                    
                await asyncio.sleep(0.3)
    
    async def demo_semantic_search(self):
        """Demostrar búsqueda semántica"""
        semantic_queries = [
            "breakthrough in artificial intelligence",
            "AI applications in healthcare",
            "machine learning for diagnosis"
        ]
        
        for query in semantic_queries:
            url = f"{self.base_url}/search/semantic"
            params = {
                "query": query,
                "limit": 3
            }
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    print(f"Búsqueda semántica: '{query}'")
                    print(f"  📊 Resultados: {data['total']}")
                    print(f"  📈 Similitud promedio: {data['avg_similarity']:.2f}")
                    
                    for result in data['results'][:2]:
                        print(f"  - {result['title'][:50]}...")
                        print(f"    🔗 Similitud: {result.get('similarity_score', 0):.2f}")
                
                await asyncio.sleep(0.5)
    
    async def demo_search_stats(self):
        """Demostrar estadísticas de búsqueda"""
        url = f"{self.base_url}/search/stats"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                print("Estadísticas del sistema:")
                
                stats = data['stats']
                
                # Estadísticas de artículos
                articles = stats['articles']
                print(f"  📰 Artículos:")
                print(f"    - Total: {articles['total']}")
                print(f"    - Con sentimiento: {articles['with_sentiment']}")
                print(f"    - Procesados: {articles['processed']}")
                
                # Estadísticas de fuentes
                sources = stats['sources']
                print(f"  📡 Fuentes:")
                print(f"    - Total: {sources['total']}")
                print(f"    - Activas: {sources['active']}")
                
                # Rango de fechas
                date_range = stats['date_range']
                print(f"  📅 Rango de datos:")
                print(f"    - Desde: {date_range['earliest']}")
                print(f"    - Hasta: {date_range['latest']}")
                print(f"    - Relevancia promedio: {date_range['avg_relevance']:.2f}")
                
            else:
                print(f"Error: {response.status}")
    
    async def demo_health_check(self):
        """Demostrar health check"""
        url = f"{self.base_url}/search/health"
        
        async with self.session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                
                print("Health Check:")
                print(f"  🟢 Estado: {data['status']}")
                print(f"  🕐 Timestamp: {data['timestamp']}")
                
                services = data['health']['services']
                print(f"  🔧 Servicios:")
                for service, status in services.items():
                    status_icon = "✅" if status else "❌"
                    print(f"    {status_icon} {service}")
                
            else:
                print(f"Error: {response.status}")


async def demo_search_workflow():
    """Demostrar flujo completo de búsqueda"""
    print("🔄 Demo: Flujo Completo de Búsqueda")
    print("=" * 40)
    
    async with SearchSystemDemo() as demo:
        # 1. Obtener filtros disponibles
        print("\n1️⃣ Obtener filtros disponibles")
        await demo.demo_available_filters()
        
        # 2. Realizar búsqueda con diferentes parámetros
        print("\n2️⃣ Realizar búsquedas múltiples")
        
        search_scenarios = [
            ("Búsqueda general", {"q": "artificial intelligence", "limit": 3}),
            ("Búsqueda filtrada", {"q": "AI", "sentiment": "positive", "limit": 3}),
            ("Búsqueda reciente", {"q": "technology", "sort": "date", "limit": 3}),
            ("Búsqueda semántica", {"query": "AI breakthrough", "limit": 3})
        ]
        
        for scenario_name, params in search_scenarios:
            print(f"\n{scenario_name}:")
            
            if "query" in params:  # Búsqueda semántica
                url = f"{demo.base_url}/search/semantic"
            else:
                url = f"{demo.base_url}/search"
            
            async with demo.session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"  ✅ Encontrados: {data.get('total', 0)} resultados")
                    print(f"  ⏱️ Tiempo: {data.get('search_time_ms', 0):.1f}ms")
                else:
                    print(f"  ❌ Error: {response.status}")
        
        # 3. Obtener trending topics
        print("\n3️⃣ Obtener temas trending")
        await demo.demo_trending_searches()
        
        # 4. Probar autocompletado
        print("\n4️⃣ Probar autocompletado")
        await demo.demo_search_suggestions()
        
        # 5. Ver estadísticas finales
        print("\n5️⃣ Ver estadísticas finales")
        await demo.demo_search_stats()


async def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Demo del sistema de búsqueda avanzada")
    parser.add_argument("--mode", choices=["full", "workflow", "custom"], 
                       default="full", help="Modo de demo")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="URL base del API")
    parser.add_argument("--delay", type=float, default=1.0,
                       help="Delay entre requests (segundos)")
    
    args = parser.parse_args()
    
    print("🎯 Sistema de Búsqueda Avanzada - Demo")
    print(f"🔗 Conectando a: {args.url}")
    print(f"⏱️ Delay entre requests: {args.delay}s")
    print()
    
    try:
        async with SearchSystemDemo(args.url) as demo:
            if args.mode == "full":
                await demo.demo_all_features()
            elif args.mode == "workflow":
                await demo_search_workflow()
            elif args.mode == "custom":
                print("Demo personalizado - Implementar aquí")
                print("Ejemplos de endpoints:")
                print(f"  GET {args.url}/search")
                print(f"  GET {args.url}/search/suggestions")
                print(f"  GET {args.url}/search/trending")
                print(f"  GET {args.url}/search/filters")
    
    except aiohttp.ClientConnectorError:
        print(f"❌ Error: No se pudo conectar a {args.url}")
        print("Asegúrate de que el servidor esté ejecutándose:")
        print("  cd backend")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    except Exception as e:
        print(f"❌ Error inesperado: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())