"""
Performance tests para endpoints críticos del sistema
Evalúa latencia, throughput y estabilidad bajo carga moderada
"""

import asyncio
import aiohttp
import time
import statistics
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import concurrent.futures
import requests
from collections import defaultdict

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Métricas de performance para un endpoint"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    min_response_time: float
    max_response_time: float
    p50_response_time: float
    p90_response_time: float
    p95_response_time: float
    p99_response_time: float
    throughput_rps: float
    error_rate: float
    test_duration: float
    timestamp: str

@dataclass
class TestConfig:
    """Configuración para test de performance"""
    name: str
    base_url: str
    concurrent_users: int
    requests_per_user: int
    timeout: int
    threshold_p95_ms: int
    threshold_p99_ms: int
    threshold_error_rate: float

class PerformanceTestRunner:
    """Ejecutor principal de tests de performance"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results: List[PerformanceMetrics] = []
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "PerformanceTest/1.0"
        })
    
    async def test_endpoint_performance(self, endpoint: str, method: str = "GET", 
                                      data: Optional[Dict] = None, 
                                      params: Optional[Dict] = None) -> PerformanceMetrics:
        """Test de performance para un endpoint específico"""
        
        logger.info(f"Testing {method} {endpoint}")
        
        # Preparar headers y datos
        headers = dict(self.session.headers)
        json_data = None
        if data:
            json_data = json.dumps(data)
        
        # Lista para almacenar tiempos de respuesta
        response_times = []
        errors = []
        successful_requests = 0
        
        start_time = time.time()
        
        # Ejecutar requests concurrentemente
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.concurrent_users) as executor:
            futures = []
            
            for _ in range(self.config.concurrent_users * self.config.requests_per_user):
                future = executor.submit(
                    self._make_request, 
                    endpoint, method, json_data, params, headers
                )
                futures.append(future)
            
            # Recopilar resultados
            for future in concurrent.futures.as_completed(futures):
                try:
                    response_time, status_code, success = future.result()
                    response_times.append(response_time)
                    
                    if success:
                        successful_requests += 1
                    else:
                        errors.append(f"Status {status_code}")
                        
                except Exception as e:
                    errors.append(str(e))
        
        test_duration = time.time() - start_time
        total_requests = len(response_times)
        
        # Calcular métricas
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            p50_response_time = statistics.median(response_times)
            p90_response_time = self._percentile(response_times, 90)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
            throughput_rps = total_requests / test_duration
        else:
            avg_response_time = min_response_time = max_response_time = 0
            p50_response_time = p90_response_time = p95_response_time = p99_response_time = 0
            throughput_rps = 0
        
        error_rate = len(errors) / total_requests if total_requests > 0 else 0
        
        metrics = PerformanceMetrics(
            endpoint=endpoint,
            method=method,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=len(errors),
            avg_response_time=round(avg_response_time * 1000, 2),  # ms
            min_response_time=round(min_response_time * 1000, 2),
            max_response_time=round(max_response_time * 1000, 2),
            p50_response_time=round(p50_response_time * 1000, 2),
            p90_response_time=round(p90_response_time * 1000, 2),
            p95_response_time=round(p95_response_time * 1000, 2),
            p99_response_time=round(p99_response_time * 1000, 2),
            throughput_rps=round(throughput_rps, 2),
            error_rate=round(error_rate * 100, 2),
            test_duration=round(test_duration, 2),
            timestamp=datetime.now().isoformat()
        )
        
        return metrics
    
    def _make_request(self, endpoint: str, method: str, json_data: Optional[str], 
                     params: Optional[Dict], headers: Dict) -> tuple:
        """Realizar una request HTTP individual"""
        url = f"{self.config.base_url}{endpoint}"
        
        try:
            start = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url, params=params, headers=headers, 
                                          timeout=self.config.timeout)
            elif method.upper() == "POST":
                response = self.session.post(url, data=json_data, params=params, 
                                           headers=headers, timeout=self.config.timeout)
            elif method.upper() == "PUT":
                response = self.session.put(url, data=json_data, params=params, 
                                          headers=headers, timeout=self.config.timeout)
            elif method.upper() == "DELETE":
                response = self.session.delete(url, params=params, headers=headers, 
                                             timeout=self.config.timeout)
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
            
            end = time.time()
            response_time = end - start
            success = 200 <= response.status_code < 400
            
            return response_time, response.status_code, success
            
        except requests.exceptions.Timeout:
            return 0, 408, False
        except requests.exceptions.RequestException as e:
            return 0, 500, False
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil de una lista de datos"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]
    
    def evaluate_thresholds(self, metrics: PerformanceMetrics) -> Dict[str, Any]:
        """Evaluar si las métricas cumplen los thresholds establecidos"""
        issues = []
        
        if metrics.p95_response_time > self.config.threshold_p95_ms:
            issues.append(f"P95 response time {metrics.p95_response_time}ms exceeds threshold {self.config.threshold_p95_ms}ms")
        
        if metrics.p99_response_time > self.config.threshold_p99_ms:
            issues.append(f"P99 response time {metrics.p99_response_time}ms exceeds threshold {self.config.threshold_p99_ms}ms")
        
        if metrics.error_rate > self.config.threshold_error_rate:
            issues.append(f"Error rate {metrics.error_rate}% exceeds threshold {self.config.threshold_error_rate}%")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "performance_score": self._calculate_performance_score(metrics)
        }
    
    def _calculate_performance_score(self, metrics: PerformanceMetrics) -> int:
        """Calcular score de performance (0-100)"""
        score = 100
        
        # Penalizar por p95 response time
        if metrics.p95_response_time > self.config.threshold_p95_ms:
            score -= min(30, (metrics.p95_response_time - self.config.threshold_p95_ms) / 10)
        
        # Penalizar por error rate
        if metrics.error_rate > 0:
            score -= min(40, metrics.error_rate * 10)
        
        # Penalizar por throughput bajo
        if metrics.throughput_rps < 10:  # Bajo umbral mínimo
            score -= 20
        
        return max(0, int(score))


class CriticalEndpointsTest:
    """Tests específicos para endpoints críticos del sistema"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_config = TestConfig(
            name="Critical Endpoints Test",
            base_url=base_url,
            concurrent_users=10,
            requests_per_user=50,
            timeout=30,
            threshold_p95_ms=500,  # 500ms threshold
            threshold_p99_ms=1000,  # 1s threshold
            threshold_error_rate=1.0  # 1% error rate
        )
        self.runner = PerformanceTestRunner(self.test_config)
    
    async def test_article_endpoints(self):
        """Test endpoints relacionados con artículos"""
        logger.info("Testing article endpoints...")
        
        # Test 1: GET artículos paginados
        metrics1 = await self.runner.test_endpoint_performance(
            "/api/v1/articles", "GET", params={"page": 1, "size": 20}
        )
        self.runner.results.append(metrics1)
        
        # Test 2: GET artículo específico
        metrics2 = await self.runner.test_endpoint_performance(
            "/api/v1/articles/1", "GET"
        )
        self.runner.results.append(metrics2)
        
        # Test 3: GET artículos con filtros
        metrics3 = await self.runner.test_endpoint_performance(
            "/api/v1/articles", "GET", params={"category": "technology", "size": 50}
        )
        self.runner.results.append(metrics3)
        
        return [metrics1, metrics2, metrics3]
    
    async def test_search_endpoints(self):
        """Test endpoints de búsqueda"""
        logger.info("Testing search endpoints...")
        
        search_queries = [
            {"query": "artificial intelligence", "limit": 10},
            {"query": "machine learning", "limit": 20},
            {"query": "technology trends", "limit": 30}
        ]
        
        search_metrics = []
        for query in search_queries:
            metrics = await self.runner.test_endpoint_performance(
                "/api/v1/search", "GET", params=query
            )
            search_metrics.append(metrics)
            self.runner.results.append(metrics)
        
        return search_metrics
    
    async def test_user_endpoints(self):
        """Test endpoints de usuario"""
        logger.info("Testing user endpoints...")
        
        # Nota: Estos tests asumirían autenticación previa
        user_endpoints = [
            "/api/v1/users/1/news",
            "/api/v1/users/1/analytics",
            "/api/v1/users/1/preferences"
        ]
        
        user_metrics = []
        for endpoint in user_endpoints:
            metrics = await self.runner.test_endpoint_performance(endpoint, "GET")
            user_metrics.append(metrics)
            self.runner.results.append(metrics)
        
        return user_metrics
    
    async def test_admin_endpoints(self):
        """Test endpoints administrativos"""
        logger.info("Testing admin endpoints...")
        
        admin_endpoints = [
            "/api/v1/admin/metrics",
            "/api/v1/admin/articles/stats",
            "/api/v1/admin/users/stats"
        ]
        
        admin_metrics = []
        for endpoint in admin_endpoints:
            metrics = await self.runner.test_endpoint_performance(endpoint, "GET")
            admin_metrics.append(metrics)
            self.runner.results.append(metrics)
        
        return admin_metrics
    
    async def test_health_endpoints(self):
        """Test endpoints de health check"""
        logger.info("Testing health endpoints...")
        
        health_endpoints = [
            "/health",
            "/health/db",
            "/health/cache",
            "/health/search"
        ]
        
        health_metrics = []
        for endpoint in health_endpoints:
            metrics = await self.runner.test_endpoint_performance(endpoint, "GET")
            health_metrics.append(metrics)
            self.runner.results.append(metrics)
        
        return health_metrics
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Ejecutar todos los tests de endpoints críticos"""
        logger.info("Iniciando tests de endpoints críticos...")
        
        start_time = time.time()
        
        try:
            # Ejecutar todos los tests
            article_results = await self.test_article_endpoints()
            search_results = await self.test_search_endpoints()
            user_results = await self.test_user_endpoints()
            admin_results = await self.test_admin_endpoints()
            health_results = await self.test_health_endpoints()
            
            total_time = time.time() - start_time
            
            # Evaluar thresholds para todos los resultados
            evaluation_results = []
            for metrics in self.runner.results:
                evaluation = self.runner.evaluate_thresholds(metrics)
                evaluation_results.append(evaluation)
            
            # Calcular estadísticas generales
            overall_score = statistics.mean([
                eval_result["performance_score"] 
                for eval_result in evaluation_results
            ])
            
            failed_tests = sum(1 for eval_result in evaluation_results 
                             if not eval_result["passed"])
            
            return {
                "test_name": "Critical Endpoints Performance Test",
                "execution_time": round(total_time, 2),
                "total_endpoints_tested": len(self.runner.results),
                "passed_endpoints": len(self.runner.results) - failed_tests,
                "failed_endpoints": failed_tests,
                "overall_performance_score": round(overall_score, 2),
                "results": [asdict(metrics) for metrics in self.runner.results],
                "evaluations": evaluation_results,
                "recommendations": self._generate_recommendations(evaluation_results)
            }
        
        except Exception as e:
            logger.error(f"Error durante los tests: {e}")
            return {
                "error": str(e),
                "test_status": "failed"
            }
    
    def _generate_recommendations(self, evaluations: List[Dict]) -> List[str]:
        """Generar recomendaciones basadas en los resultados"""
        recommendations = []
        
        slow_endpoints = []
        high_error_endpoints = []
        
        for i, eval_result in enumerate(evaluations):
            if not eval_result["passed"]:
                metrics = self.runner.results[i]
                for issue in eval_result["issues"]:
                    if "response time" in issue.lower():
                        slow_endpoints.append(metrics.endpoint)
                    elif "error rate" in issue.lower():
                        high_error_endpoints.append(metrics.endpoint)
        
        if slow_endpoints:
            recommendations.append(f"Optimizar performance en endpoints: {', '.join(set(slow_endpoints))}")
        
        if high_error_endpoints:
            recommendations.append(f"Investigar errores en endpoints: {', '.join(set(high_error_endpoints))}")
        
        # Recomendaciones generales
        avg_p95 = statistics.mean([result.p95_response_time for result in self.runner.results])
        if avg_p95 > 300:
            recommendations.append("Considerar implementar caching para reducir latencia")
        
        avg_error_rate = statistics.mean([result.error_rate for result in self.runner.results])
        if avg_error_rate > 0.5:
            recommendations.append("Revisar manejo de errores y robustez del sistema")
        
        return recommendations


def main():
    """Función principal para ejecutar los tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Tests for AI News Aggregator")
    parser.add_argument("--host", default="localhost:8000", help="API host to test")
    parser.add_argument("--output", default="performance_report.json", help="Output file for results")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}"
    
    # Ejecutar tests
    test_suite = CriticalEndpointsTest(base_url)
    results = asyncio.run(test_suite.run_all_tests())
    
    # Guardar resultados
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Resultados guardados en {args.output}")
    
    # Mostrar resumen
    if "error" not in results:
        print(f"\n=== RESUMEN DE PERFORMANCE ===")
        print(f"Endpoints testados: {results['total_endpoints_tested']}")
        print(f"Tests pasados: {results['passed_endpoints']}")
        print(f"Tests fallidos: {results['failed_endpoints']}")
        print(f"Score general: {results['overall_performance_score']}/100")
        print(f"Tiempo de ejecución: {results['execution_time']}s")
        
        if results['recommendations']:
            print("\n=== RECOMENDACIONES ===")
            for rec in results['recommendations']:
                print(f"- {rec}")
    else:
        print(f"Error en los tests: {results['error']}")


if __name__ == "__main__":
    main()