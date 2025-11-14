"""
Database Performance Tests para queries críticas del sistema
Evalúa performance de base de datos bajo diferentes condiciones de carga
"""

import asyncio
import asyncpg
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import psycopg2
import psycopg2.extras

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DBQueryMetrics:
    """Métricas para una query específica"""
    query_name: str
    query_type: str  # SELECT, INSERT, UPDATE, DELETE, COMPLEX
    avg_execution_time: float
    min_execution_time: float
    max_execution_time: float
    p95_execution_time: float
    p99_execution_time: float
    total_executions: int
    successful_executions: int
    failed_executions: int
    error_rate: float
    throughput_qps: float
    connection_pool_utilization: float
    lock_wait_time: float
    timestamp: str

@dataclass
class DatabaseTestConfig:
    """Configuración para tests de base de datos"""
    name: str
    host: str
    port: int
    database: str
    user: str
    password: str
    concurrent_connections: int
    queries_per_connection: int
    query_timeout: int

class DatabasePerformanceTester:
    """Tester de performance para base de datos"""
    
    def __init__(self, config: DatabaseTestConfig):
        self.config = config
        self.results: List[DBQueryMetrics] = []
        self.connection_string = f"postgresql://{config.user}:{config.password}@{config.host}:{config.port}/{config.database}"
    
    async def test_query_performance(self, query_name: str, query: str, 
                                   query_type: str = "SELECT", 
                                   parameters: Optional[List] = None) -> DBQueryMetrics:
        """Test de performance para una query específica"""
        logger.info(f"Testing query performance: {query_name}")
        
        execution_times = []
        errors = []
        successful_executions = 0
        connection_pool_stats = []
        lock_wait_times = []
        
        # Pool de conexiones
        pool = await asyncpg.create_pool(
            self.connection_string,
            min_size=5,
            max_size=self.config.concurrent_connections,
            command_timeout=self.config.query_timeout
        )
        
        start_time = time.time()
        
        try:
            async with pool.acquire() as connection:
                # Test individual de conexión
                connection_test_start = time.time()
                await connection.execute("SELECT 1")
                connection_test_time = time.time() - connection_test_start
                
                logger.info(f"Connection test time: {connection_test_time:.3f}s")
            
            # Ejecutar queries concurrentemente
            tasks = []
            for i in range(self.config.concurrent_connections * self.config.queries_per_connection):
                task = self._execute_query_with_timing(
                    pool, query, parameters, query_name
                )
                tasks.append(task)
            
            # Ejecutar todas las tasks
            query_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Procesar resultados
            for result in query_results:
                if isinstance(result, dict):
                    execution_times.append(result["execution_time"])
                    if result.get("lock_wait_time"):
                        lock_wait_times.append(result["lock_wait_time"])
                    
                    if result.get("success"):
                        successful_executions += 1
                    else:
                        errors.append(result.get("error", "Unknown error"))
                else:
                    errors.append(str(result))
            
            pool_test_time = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Error durante test de pool: {e}")
            raise
        finally:
            await pool.close()
        
        # Calcular métricas
        total_executions = len(execution_times)
        if execution_times:
            avg_execution_time = statistics.mean(execution_times)
            min_execution_time = min(execution_times)
            max_execution_time = max(execution_times)
            p95_execution_time = self._percentile(execution_times, 95)
            p99_execution_time = self._percentile(execution_times, 99)
            throughput_qps = total_executions / pool_test_time
        else:
            avg_execution_time = min_execution_time = max_execution_time = 0
            p95_execution_time = p99_execution_time = throughput_qps = 0
        
        failed_executions = len(errors)
        error_rate = (failed_executions / total_executions * 100) if total_executions > 0 else 0
        
        # Utilización de connection pool
        connection_pool_utilization = (total_executions / 
                                     (self.config.concurrent_connections * self.config.queries_per_connection)) * 100
        
        # Tiempo promedio de espera de locks
        avg_lock_wait_time = statistics.mean(lock_wait_times) if lock_wait_times else 0
        
        metrics = DBQueryMetrics(
            query_name=query_name,
            query_type=query_type,
            avg_execution_time=round(avg_execution_time * 1000, 2),  # ms
            min_execution_time=round(min_execution_time * 1000, 2),
            max_execution_time=round(max_execution_time * 1000, 2),
            p95_execution_time=round(p95_execution_time * 1000, 2),
            p99_execution_time=round(p99_execution_time * 1000, 2),
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            error_rate=round(error_rate, 2),
            throughput_qps=round(throughput_qps, 2),
            connection_pool_utilization=round(connection_pool_utilization, 2),
            avg_lock_wait_time=round(avg_lock_wait_time * 1000, 2),  # ms
            timestamp=datetime.now().isoformat()
        )
        
        self.results.append(metrics)
        return metrics
    
    async def _execute_query_with_timing(self, pool, query: str, parameters: Optional[List], 
                                       query_name: str) -> Dict[str, Any]:
        """Ejecutar una query individual con timing"""
        start_time = time.time()
        lock_wait_start = time.time()
        
        try:
            async with pool.acquire() as connection:
                lock_wait_time = time.time() - lock_wait_start
                
                # Ejecutar query
                if parameters:
                    result = await connection.fetchrow(query, *parameters)
                else:
                    result = await connection.fetchrow(query)
                
                execution_time = time.time() - start_time
                
                return {
                    "success": True,
                    "execution_time": execution_time,
                    "lock_wait_time": lock_wait_time,
                    "query_name": query_name
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            
            return {
                "success": False,
                "execution_time": execution_time,
                "error": str(e),
                "query_name": query_name
            }
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil de una lista de datos"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    async def analyze_database_performance(self) -> Dict[str, Any]:
        """Análisis completo de performance de base de datos"""
        logger.info("Iniciando análisis de performance de base de datos...")
        
        analysis_results = {}
        
        # Test 1: Queries de artículos
        article_queries = [
            {
                "name": "Get Articles Pagination",
                "query": "SELECT id, title, content, published_at, created_at FROM articles ORDER BY created_at DESC LIMIT $1 OFFSET $2",
                "type": "SELECT",
                "params": [20, 0]
            },
            {
                "name": "Get Article by ID",
                "query": "SELECT * FROM articles WHERE id = $1",
                "type": "SELECT",
                "params": [1]
            },
            {
                "name": "Get Articles by Category",
                "query": "SELECT id, title, category, published_at FROM articles WHERE category = $1 ORDER BY published_at DESC LIMIT $2",
                "type": "SELECT",
                "params": ["technology", 50]
            },
            {
                "name": "Search Articles by Text",
                "query": "SELECT id, title, content, published_at FROM articles WHERE title ILIKE $1 OR content ILIKE $1 ORDER BY published_at DESC LIMIT $2",
                "type": "SELECT",
                "params": ["%artificial intelligence%", 20]
            }
        ]
        
        # Ejecutar tests de artículos
        for query_config in article_queries:
            try:
                metrics = await self.test_query_performance(
                    query_config["name"],
                    query_config["query"],
                    query_config["type"],
                    query_config["params"]
                )
                analysis_results[query_config["name"]] = asdict(metrics)
            except Exception as e:
                logger.error(f"Error testing {query_config['name']}: {e}")
                analysis_results[query_config["name"]] = {"error": str(e)}
        
        # Test 2: Queries de usuarios
        user_queries = [
            {
                "name": "Get User by ID",
                "query": "SELECT id, email, full_name, preferences FROM users WHERE id = $1",
                "type": "SELECT",
                "params": [1]
            },
            {
                "name": "Get User Preferences",
                "query": "SELECT preferences FROM users WHERE id = $1",
                "type": "SELECT",
                "params": [1]
            },
            {
                "name": "Get User Analytics",
                "query": "SELECT COUNT(*) as total_reads, AVG(session_duration) as avg_session FROM user_analytics WHERE user_id = $1",
                "type": "SELECT",
                "params": [1]
            }
        ]
        
        # Ejecutar tests de usuarios
        for query_config in user_queries:
            try:
                metrics = await self.test_query_performance(
                    query_config["name"],
                    query_config["query"],
                    query_config["type"],
                    query_config["params"]
                )
                analysis_results[query_config["name"]] = asdict(metrics)
            except Exception as e:
                logger.error(f"Error testing {query_config['name']}: {e}")
                analysis_results[query_config["name"]] = {"error": str(e)}
        
        # Test 3: Queries de analytics
        analytics_queries = [
            {
                "name": "Get System Metrics",
                "query": "SELECT COUNT(*) as total_articles, COUNT(DISTINCT category) as total_categories, AVG(EXTRACT(EPOCH FROM (NOW() - published_at))/3600) as avg_age_hours FROM articles",
                "type": "SELECT",
                "params": []
            },
            {
                "name": "Get User Activity Stats",
                "query": "SELECT DATE(created_at) as date, COUNT(*) as articles_count FROM articles WHERE created_at >= NOW() - INTERVAL '7 days' GROUP BY DATE(created_at) ORDER BY date",
                "type": "SELECT",
                "params": []
            },
            {
                "name": "Get Popular Categories",
                "query": "SELECT category, COUNT(*) as article_count FROM articles WHERE published_at >= NOW() - INTERVAL '30 days' GROUP BY category ORDER BY article_count DESC LIMIT 10",
                "type": "SELECT",
                "params": []
            }
        ]
        
        # Ejecutar tests de analytics
        for query_config in analytics_queries:
            try:
                metrics = await self.test_query_performance(
                    query_config["name"],
                    query_config["query"],
                    query_config["type"],
                    query_config["params"]
                )
                analysis_results[query_config["name"]] = asdict(metrics)
            except Exception as e:
                logger.error(f"Error testing {query_config['name']}: {e}")
                analysis_results[query_config["name"]] = {"error": str(e)}
        
        # Test 4: Test de conexión y pool
        await self.test_connection_pool_performance()
        
        # Test 5: Test de locks y concurrencia
        await self.test_concurrent_writes()
        
        return analysis_results
    
    async def test_connection_pool_performance(self):
        """Test específico para connection pool"""
        logger.info("Testing connection pool performance...")
        
        # Test de creación de conexiones
        connection_times = []
        
        for i in range(50):
            start_time = time.time()
            try:
                conn = await asyncpg.connect(self.connection_string)
                await conn.execute("SELECT 1")
                await conn.close()
                connection_time = time.time() - start_time
                connection_times.append(connection_time)
            except Exception as e:
                logger.warning(f"Connection test {i} failed: {e}")
        
        if connection_times:
            avg_connection_time = statistics.mean(connection_times)
            pool_metrics = DBQueryMetrics(
                query_name="Connection Pool Performance",
                query_type="CONNECTION",
                avg_execution_time=round(avg_connection_time * 1000, 2),
                min_execution_time=round(min(connection_times) * 1000, 2),
                max_execution_time=round(max(connection_times) * 1000, 2),
                p95_execution_time=round(self._percentile(connection_times, 95) * 1000, 2),
                p99_execution_time=round(self._percentile(connection_times, 99) * 1000, 2),
                total_executions=len(connection_times),
                successful_executions=len(connection_times),
                failed_executions=0,
                error_rate=0,
                throughput_qps=len(connection_times) / sum(connection_times),
                connection_pool_utilization=0,  # No applicable for direct connections
                avg_lock_wait_time=0,
                timestamp=datetime.now().isoformat()
            )
            
            self.results.append(pool_metrics)
            logger.info(f"Connection pool avg time: {avg_connection_time:.3f}s")
    
    async def test_concurrent_writes(self):
        """Test de escrituras concurrentes para detectar locks"""
        logger.info("Testing concurrent writes...")
        
        # Esta prueba requiere que existan las tablas correspondientes
        # En un entorno real, se crearían datos de test temporales
        
        try:
            # Test de actualización de artículos (si existe)
            update_query = "UPDATE articles SET view_count = view_count + 1 WHERE id = $1"
            
            pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=1,
                max_size=10
            )
            
            tasks = []
            for i in range(20):
                task = self._execute_query_with_timing(
                    pool, update_query, [1], "Concurrent Update"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            successful_updates = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
            logger.info(f"Concurrent updates: {successful_updates}/20 successful")
            
            await pool.close()
            
        except Exception as e:
            logger.warning(f"Concurrent write test failed: {e}")
    
    def evaluate_database_health(self) -> Dict[str, Any]:
        """Evaluar salud general de la base de datos"""
        if not self.results:
            return {"error": "No hay resultados para evaluar"}
        
        # Métricas agregadas
        avg_response_time = statistics.mean([r.avg_execution_time for r in self.results])
        avg_error_rate = statistics.mean([r.error_rate for r in self.results])
        avg_pool_utilization = statistics.mean([r.connection_pool_utilization for r in self.results])
        
        # Identificar queries problemáticas
        slow_queries = [r for r in self.results if r.avg_execution_time > 100]  # > 100ms
        error_prone_queries = [r for r in self.results if r.error_rate > 5]    # > 5% error
        
        # Score de salud general
        health_score = 100
        
        # Penalizar por queries lentas
        if slow_queries:
            health_score -= len(slow_queries) * 15
        
        # Penalizar por queries con errores
        if error_prone_queries:
            health_score -= len(error_prone_queries) * 20
        
        # Penalizar por alta utilización de pool
        if avg_pool_utilization > 80:
            health_score -= 20
        
        health_score = max(0, int(health_score))
        
        return {
            "overall_health_score": health_score,
            "average_response_time_ms": round(avg_response_time, 2),
            "average_error_rate": round(avg_error_rate, 2),
            "average_pool_utilization": round(avg_pool_utilization, 2),
            "problematic_queries": {
                "slow_queries": [r.query_name for r in slow_queries],
                "error_prone_queries": [r.query_name for r in error_prone_queries]
            },
            "status": "Excellent" if health_score >= 90 else
                    "Good" if health_score >= 75 else
                    "Fair" if health_score >= 60 else "Poor"
        }


class DatabasePerformanceTestSuite:
    """Suite completa de tests de performance de base de datos"""
    
    def __init__(self):
        self.config = DatabaseTestConfig(
            name="DB Performance Test",
            host="localhost",
            port=5432,
            database="ai_news_db",
            user="postgres",
            password="password",
            concurrent_connections=10,
            queries_per_connection=20,
            query_timeout=30
        )
        
        self.tester = DatabasePerformanceTester(self.config)
    
    def run_comprehensive_db_test(self) -> Dict[str, Any]:
        """Ejecutar suite completa de tests de base de datos"""
        logger.info("Iniciando suite completa de performance de base de datos...")
        
        start_time = time.time()
        
        try:
            # Ejecutar análisis
            analysis_results = asyncio.run(self.tester.analyze_database_performance())
            
            # Evaluar salud de la base de datos
            health_evaluation = self.tester.evaluate_database_health()
            
            total_time = time.time() - start_time
            
            # Generar recomendaciones
            recommendations = self._generate_db_recommendations(health_evaluation)
            
            return {
                "test_suite": "Database Performance Testing",
                "execution_time": round(total_time, 2),
                "database_config": asdict(self.config),
                "query_results": analysis_results,
                "health_evaluation": health_evaluation,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error durante tests de base de datos: {e}")
            return {
                "test_suite": "Database Performance Testing",
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_db_recommendations(self, health_evaluation: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones para performance de base de datos"""
        recommendations = []
        
        score = health_evaluation.get("overall_health_score", 0)
        
        if score < 60:
            recommendations.append("Performance de base de datos necesita optimización urgente")
        
        # Recomendaciones específicas
        problematic = health_evaluation.get("problematic_queries", {})
        
        if problematic.get("slow_queries"):
            recommendations.append(f"Optimizar queries lentas: {', '.join(problematic['slow_queries'])}")
        
        if problematic.get("error_prone_queries"):
            recommendations.append(f"Investigar queries con errores: {', '.join(problematic['error_prone_queries'])}")
        
        avg_response_time = health_evaluation.get("average_response_time_ms", 0)
        if avg_response_time > 100:
            recommendations.append("Considerar agregar índices para mejorar velocidad de consultas")
        
        pool_utilization = health_evaluation.get("average_pool_utilization", 0)
        if pool_utilization > 80:
            recommendations.append("Aumentar tamaño del connection pool o optimizar uso de conexiones")
        
        avg_error_rate = health_evaluation.get("average_error_rate", 0)
        if avg_error_rate > 2:
            recommendations.append("Investigar y resolver errores en queries de base de datos")
        
        if not recommendations:
            recommendations.append("Performance de base de datos está en buen estado")
        
        return recommendations


def main():
    """Función principal para ejecutar tests de base de datos"""
    import argparse
    import os
    
    parser = argparse.ArgumentParser(description="Database Performance Tests for AI News Aggregator")
    parser.add_argument("--host", default="localhost", help="Database host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="ai_news_db", help="Database name")
    parser.add_argument("--user", default="postgres", help="Database user")
    parser.add_argument("--password", default="password", help="Database password")
    parser.add_argument("--output", default="database_performance_report.json", help="Output file")
    
    args = parser.parse_args()
    
    # Crear suite de tests
    test_suite = DatabasePerformanceTestSuite()
    
    # Actualizar configuración con argumentos
    test_suite.config.host = args.host
    test_suite.config.port = args.port
    test_suite.config.database = args.database
    test_suite.config.user = args.user
    test_suite.config.password = args.password
    
    # Ejecutar tests
    results = test_suite.run_comprehensive_db_test()
    
    # Guardar resultados
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Resultados guardados en {args.output}")
    
    # Mostrar resumen
    if "error" not in results:
        print(f"\n=== RESUMEN DE PERFORMANCE DE BASE DE DATOS ===")
        print(f"Tiempo de ejecución: {results['execution_time']}s")
        
        health = results['health_evaluation']
        print(f"Score de salud general: {health['overall_health_score']}/100")
        print(f"Estado: {health['status']}")
        print(f"Tiempo de respuesta promedio: {health['average_response_time_ms']}ms")
        print(f"Tasa de error promedio: {health['average_error_rate']}%")
        print(f"Utilización de pool: {health['average_pool_utilization']}%")
        
        if results['recommendations']:
            print("\n=== RECOMENDACIONES ===")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"{i}. {rec}")
    else:
        print(f"Error en tests de base de datos: {results['error']}")


if __name__ == "__main__":
    main()