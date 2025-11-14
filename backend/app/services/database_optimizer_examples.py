"""
Ejemplos de uso del Database Optimizer

Este archivo demuestra cómo utilizar el sistema de optimización
de consultas SQLAlchemy para mejorar el performance de la aplicación.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
import redis

# Importar el optimizador
from .database_optimizer import (
    DatabaseOptimizer, 
    init_database_optimizer, 
    QueryType,
    PerformanceMetrics
)


async def ejemplo_optimizacion_articulos():
    """Ejemplo de optimización de consultas de artículos"""
    
    # Configuración inicial
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    
    # Inicializar optimizador
    optimizer = init_database_optimizer(redis_client, engine)
    
    # Ejemplo 1: Listado optimizado con filtros
    with engine.connect() as conn:
        session = Session(conn)
        
        try:
            # Definir filtros y paginación
            filters = {
                'sentiment': 'positive',
                'min_relevance': 0.7,
                'date_from': datetime.utcnow() - timedelta(days=7),
                'source_ids': ['uuid1', 'uuid2', 'uuid3']
            }
            
            pagination = {
                'limit': 20,
                'offset': 0
            }
            
            # Obtener artículos optimizados
            articles, metadata = optimizer.optimize_articles_list(
                session, filters, pagination
            )
            
            print(f"📰 Encontrados {len(articles)} artículos")
            print(f"📊 Total: {metadata['total_count']} artículos")
            print(f"⚡ Cache hit: {'Sí' if metadata.get('cache_ttl') else 'No'}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            session.close()


async def ejemplo_busqueda_optimizada():
    """Ejemplo de búsqueda de artículos optimizada"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    with engine.connect() as conn:
        session = Session(conn)
        
        try:
            # Búsqueda con texto completo
            search_term = "inteligencia artificial machine learning"
            filters = {
                'sentiment': 'positive',
                'min_relevance': 0.5
            }
            pagination = {'limit': 15}
            
            articles, metadata = optimizer.optimize_search(
                session, search_term, filters, pagination
            )
            
            print(f"🔍 Búsqueda: '{search_term}'")
            print(f"📰 Resultados: {len(articles)}")
            print(f"⏱️ Tiempo: {metadata.get('cache_ttl', 'N/A')}s de cache")
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
        finally:
            session.close()


async def ejemplo_tendencias_optimizadas():
    """Ejemplo de consulta de tendencias optimizada"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    with engine.connect() as conn:
        session = Session(conn)
        
        try:
            # Obtener tendencias usando vista materializada
            trending = optimizer.get_trending_optimized(session, limit=10)
            
            print("🔥 Temas en Tendencia:")
            for i, topic in enumerate(trending, 1):
                print(f"{i}. {topic['topic']} "
                     f"({topic['article_count']} artículos, "
                     f"{topic['sources_count']} fuentes)")
            
        except Exception as e:
            print(f"❌ Error en tendencias: {e}")
        finally:
            session.close()


async def ejemplo_dashboard_optimizado():
    """Ejemplo de estadísticas de dashboard optimizadas"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    with engine.connect() as conn:
        session = Session(conn)
        
        try:
            # Obtener estadísticas del dashboard
            stats = optimizer.get_dashboard_stats(session)
            
            print("📊 Estadísticas del Dashboard:")
            print(f"  • Cache hit ratio: {stats['cache_stats']['hit_ratio']:.2%}")
            print(f"  • Items en cache: {stats['cache_stats']['items_cached']}")
            print(f"  • Memory usage: {stats['cache_stats']['memory_usage']} KB")
            
            # Mostrar métricas de performance
            perf_summary = stats['performance_summary']
            if perf_summary:
                print("\n⚡ Performance por tipo de consulta:")
                for query_type, metrics in perf_summary.items():
                    print(f"  • {query_type}:")
                    print(f"    - Consultas: {metrics['total_queries']}")
                    print(f"    - Tiempo promedio: {metrics['avg_time_ms']:.2f}ms")
                    print(f"    - Cache hit ratio: {metrics['cache_hit_ratio']:.2%}")
            
        except Exception as e:
            print(f"❌ Error en dashboard: {e}")
        finally:
            session.close()


async def ejemplo_monitoreo_performance():
    """Ejemplo de monitoreo de performance"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    try:
        # Obtener reporte completo de performance
        performance_report = optimizer.get_performance_report()
        
        print("📈 Reporte de Performance:")
        
        # Estadísticas de cache
        cache_stats = performance_report['cache_stats']
        print(f"\n💾 Cache Stats:")
        print(f"  • Hit ratio: {cache_stats['hit_ratio']:.2%}")
        print(f"  • Memory usage: {cache_stats['memory_usage']} KB")
        print(f"  • Items cached: {cache_stats['items_cached']}")
        
        # Consultas lentas
        slow_queries = performance_report['slow_queries']
        if slow_queries:
            print(f"\n🐌 Consultas Lentas ({len(slow_queries)}):")
            for query in slow_queries[:5]:  # Top 5
                print(f"  • {query['execution_time']:.2f}ms: {query['query']}")
        
        # Resumen de performance
        perf_summary = performance_report['performance_summary']
        if perf_summary:
            print(f"\n⚡ Resumen de Performance:")
            for query_type, metrics in perf_summary.items():
                avg_time = metrics['avg_time_ms']
                status = "🟢" if avg_time < 100 else "🟡" if avg_time < 500 else "🔴"
                print(f"  {status} {query_type}: {avg_time:.2f}ms promedio")
        
    except Exception as e:
        print(f"❌ Error en monitoreo: {e}")


async def ejemplo_analisis_indices():
    """Ejemplo de análisis de índices y performance"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    with engine.connect() as conn:
        try:
            # Analizar performance de una consulta específica
            query = """
                SELECT a.id, a.title, a.published_at, s.name as source_name
                FROM articles a
                JOIN sources s ON a.source_id = s.id
                WHERE a.processing_status = 'completed'
                AND a.published_at >= NOW() - INTERVAL '7 days'
                ORDER BY a.published_at DESC
                LIMIT 100
            """
            
            performance_analysis = optimizer.index_optimizer.analyze_query_performance(query)
            
            print("🔍 Análisis de Performance:")
            print(f"  • Tiempo de ejecución: {performance_analysis['execution_time_ms']:.2f}ms")
            print(f"  • Tiempo de planificación: {performance_analysis['planning_time_ms']:.2f}ms")
            print(f"  • Costo total: {performance_analysis['total_cost']:.2f}")
            print(f"  • Filas estimadas: {performance_analysis['estimated_rows']}")
            
        except Exception as e:
            print(f"❌ Error en análisis: {e}")


async def ejemplo_uso_continuo():
    """Ejemplo de uso continuo con invalidación de cache"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    # Simular uso continuo
    for i in range(5):
        print(f"\n🔄 Iteración {i+1}:")
        
        with engine.connect() as conn:
            session = Session(conn)
            
            try:
                # Diferentes tipos de consultas
                if i % 2 == 0:
                    # Listado de artículos
                    filters = {'min_relevance': 0.5}
                    articles, _ = optimizer.optimize_articles_list(session, filters, {})
                    print(f"  📰 Artículos cargados: {len(articles)}")
                    
                else:
                    # Tendencias
                    trending = optimizer.get_trending_optimized(session, 5)
                    print(f"  🔥 Tendencias cargadas: {len(trending)}")
                
            except Exception as e:
                print(f"  ❌ Error: {e}")
            finally:
                session.close()
    
    # Mostrar estadísticas finales
    cache_stats = optimizer.cache.get_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"  • Hit ratio: {cache_stats.hit_ratio:.2%}")
    print(f"  • Items in memory: {cache_stats.items_cached}")


async def ejemplo_cursor_pagination():
    """Ejemplo de paginación con cursor"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    with engine.connect() as conn:
        session = Session(conn)
        
        try:
            # Primera página
            filters = {'min_relevance': 0.3}
            first_query = optimizer.query_builder.build_cursor_pagination_query(
                session, filters, None, 5
            )
            first_page = first_query.all()
            
            if first_page:
                # Crear cursor con el último elemento
                last_article = first_page[-1]
                cursor_data = {
                    'id': str(last_article.id),
                    'date': last_article.published_at.isoformat() if last_article.published_at else None
                }
                cursor = str(cursor_data).replace("'", '"')  # Simple JSON string
                
                print(f"📄 Primera página: {len(first_page)} artículos")
                print(f"📍 Cursor: {cursor}")
                
                # Segunda página con cursor
                second_query = optimizer.query_builder.build_cursor_pagination_query(
                    session, filters, cursor, 5
                )
                second_page = second_query.all()
                
                print(f"📄 Segunda página: {len(second_page)} artículos")
                print(f"🔗 Cursor pagination funcionando correctamente")
            
        except Exception as e:
            print(f"❌ Error en cursor pagination: {e}")
        finally:
            session.close()


async def ejemplo_reporte_admin():
    """Ejemplo de reporte administrativo"""
    
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    engine = create_engine('postgresql://user:pass@localhost/ai_news')
    optimizer = init_database_optimizer(redis_client, engine)
    
    print("🔧 REPORTE ADMINISTRATIVO - DATABASE OPTIMIZER")
    print("=" * 60)
    
    try:
        # 1. Estado del sistema
        print("\n1️⃣ ESTADO DEL SISTEMA")
        cache_stats = optimizer.cache.get_stats()
        print(f"   Cache Hit Ratio: {cache_stats.hit_ratio:.2%}")
        print(f"   Items en Memoria: {cache_stats.items_cached}")
        print(f"   Uso de Memoria: {cache_stats.memory_usage} KB")
        
        # 2. Performance summary
        print("\n2️⃣ PERFORMANCE SUMMARY")
        perf_report = optimizer.get_performance_report()
        
        if perf_report['performance_summary']:
            for query_type, metrics in perf_report['performance_summary'].items():
                avg_time = metrics['avg_time_ms']
                status = "✅" if avg_time < 100 else "⚠️" if avg_time < 500 else "❌"
                print(f"   {status} {query_type}: {avg_time:.2f}ms avg ({metrics['total_queries']} queries)")
        else:
            print("   📊 No hay métricas disponibles aún")
        
        # 3. Consultas lentas
        print("\n3️⃣ CONSULTAS LENTAS")
        slow_queries = perf_report['slow_queries']
        if slow_queries:
            for i, query in enumerate(slow_queries[:3], 1):
                print(f"   {i}. {query['execution_time']:.2f}ms - {query['query']}")
        else:
            print("   ✅ No hay consultas lentas registradas")
        
        # 4. Recomendaciones
        print("\n4️⃣ RECOMENDACIONES")
        
        if cache_stats.hit_ratio < 0.7:
            print("   💡 Considera aumentar el TTL del cache para mejorar el hit ratio")
        
        if slow_queries:
            print("   🔧 Revisa los índices para las consultas más lentas")
        
        if cache_stats.memory_usage > 10000:  # 10MB
            print("   💾 Considera reducir el tamaño máximo del cache en memoria")
        
        print("   🔄 Programa un refresh regular de las vistas materializadas")
        
    except Exception as e:
        print(f"❌ Error generando reporte: {e}")


async def main():
    """Función principal para ejecutar todos los ejemplos"""
    
    print("🚀 DATABASE OPTIMIZER - EJEMPLOS DE USO")
    print("=" * 50)
    
    # Los ejemplos requieren una base de datos real
    # En un entorno de producción, esto se ejecutaría con las configuraciones reales
    
    examples = [
        ("Artículos Optimizados", ejemplo_optimizacion_articulos),
        ("Búsqueda Optimizada", ejemplo_busqueda_optimizada),
        ("Tendencias Optimizadas", ejemplo_tendencias_optimizadas),
        ("Dashboard Optimizado", ejemplo_dashboard_optimizado),
        ("Monitoreo Performance", ejemplo_monitoreo_performance),
        ("Análisis de Índices", ejemplo_analisis_indices),
        ("Cursor Pagination", ejemplo_cursor_pagination),
        ("Uso Continuo", ejemplo_uso_continuo),
        ("Reporte Administrativo", ejemplo_reporte_admin)
    ]
    
    print("\n📋 EJEMPLOS DISPONIBLES:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"   {i}. {name}")
    
    print("\n💡 Para ejecutar un ejemplo específico:")
    print("   await ejemplo_optimizacion_articulos()")
    print("   await ejemplo_busqueda_optimizada()")
    print("   # etc...")


if __name__ == "__main__":
    asyncio.run(main())