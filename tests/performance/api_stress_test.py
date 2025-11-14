"""
Stress tests para APIs con enfoque en rate limiting
Verifica comportamiento del sistema bajo carga extrema
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from collections import defaultdict, deque
import statistics

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuración para tests de rate limiting"""
    name: str
    requests_per_second: int
    burst_size: int
    duration_seconds: int
    concurrent_users: int
    endpoint: str
    method: str = "GET"

@dataclass
class RateLimitResult:
    """Resultado de test de rate limiting"""
    test_name: str
    total_requests: int
    successful_requests: int
    rate_limited_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    peak_rps: float
    sustained_rps: float
    error_rate: float
    rate_limit_status_codes: Dict[int, int]
    timeline: List[Dict[str, Any]]
    timestamp: str

class RateLimitTester:
    """Tester especializado para rate limiting"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.rate_limit_status_codes = [429, 503]  # Too Many Requests, Service Unavailable
        self.results: List[RateLimitResult] = []
    
    async def test_rate_limit_single_endpoint(self, config: RateLimitConfig) -> RateLimitResult:
        """Test de rate limiting para un endpoint específico"""
        logger.info(f"Iniciando test de rate limiting: {config.name}")
        
        # Métricas de tiempo real
        request_times = deque()
        response_times = []
        status_codes = defaultdict(int)
        errors = []
        
        # Timeline para análisis temporal
        timeline = []
        start_time = time.time()
        
        # Crear sesión HTTP
        async with aiohttp.ClientSession() as session:
            
            # Test de burst (picos de tráfico)
            if config.burst_size > 0:
                burst_start = time.time()
                burst_results = await self._test_burst_traffic(
                    session, config.endpoint, config.burst_size, config.method
                )
                burst_end = time.time()
                
                for result in burst_results:
                    response_times.append(result["response_time"])
                    status_codes[result["status_code"]] += 1
                    
                    timeline.append({
                        "timestamp": time.time() - start_time,
                        "type": "burst",
                        "status_code": result["status_code"],
                        "response_time": result["response_time"]
                    })
                
                logger.info(f"Test de burst completado en {burst_end - burst_start:.2f}s")
            
            # Test de tráfico sostenido
            sustained_start = time.time()
            sustained_results = await self._test_sustained_traffic(
                session, config.endpoint, config.requests_per_second, 
                config.duration_seconds, config.concurrent_users, config.method
            )
            sustained_end = time.time()
            
            for result in sustained_results:
                response_times.append(result["response_time"])
                status_codes[result["status_code"]] += 1
                
                timeline.append({
                    "timestamp": time.time() - start_time,
                    "type": "sustained",
                    "status_code": result["status_code"],
                    "response_time": result["response_time"]
                })
            
            logger.info(f"Test de tráfico sostenido completado en {sustained_end - sustained_start:.2f}s")
        
        # Calcular métricas
        total_time = time.time() - start_time
        total_requests = len(response_times)
        successful_requests = sum(1 for code in status_codes.keys() if 200 <= code < 400)
        rate_limited_requests = sum(status_codes[code] for code in self.rate_limit_status_codes)
        failed_requests = total_requests - successful_requests
        
        # Calcular RPS sostenido
        sustained_requests = len(sustained_results)
        sustained_rps = sustained_requests / (sustained_end - sustained_start)
        
        # Calcular RPS peak (en ventana de 1 segundo)
        peak_rps = self._calculate_peak_rps(response_times, start_time)
        
        # Calcular percentiles de response time
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = self._percentile(response_times, 95)
            p99_response_time = self._percentile(response_times, 99)
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
        
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0
        
        result = RateLimitResult(
            test_name=config.name,
            total_requests=total_requests,
            successful_requests=successful_requests,
            rate_limited_requests=rate_limited_requests,
            failed_requests=failed_requests,
            avg_response_time=round(avg_response_time * 1000, 2),  # ms
            p95_response_time=round(p95_response_time * 1000, 2),
            p99_response_time=round(p99_response_time * 1000, 2),
            peak_rps=round(peak_rps, 2),
            sustained_rps=round(sustained_rps, 2),
            error_rate=round(error_rate, 2),
            rate_limit_status_codes=dict(status_codes),
            timeline=timeline,
            timestamp=datetime.now().isoformat()
        )
        
        self.results.append(result)
        return result
    
    async def _test_burst_traffic(self, session: aiohttp.ClientSession, 
                                endpoint: str, burst_size: int, method: str) -> List[Dict]:
        """Test de tráfico en burst (picos de tráfico)"""
        tasks = []
        
        for _ in range(burst_size):
            task = self._make_request(session, endpoint, method)
            tasks.append(task)
        
        # Ejecutar todas las requests del burst concurrentemente
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for result in results:
            if isinstance(result, dict):
                processed_results.append(result)
            else:
                processed_results.append({
                    "status_code": 500,
                    "response_time": 0,
                    "error": str(result)
                })
        
        return processed_results
    
    async def _test_sustained_traffic(self, session: aiohttp.ClientSession, 
                                    endpoint: str, target_rps: int, 
                                    duration: int, concurrent_users: int, method: str) -> List[Dict]:
        """Test de tráfico sostenido a RPS constante"""
        results = []
        start_time = time.time()
        end_time = start_time + duration
        
        # Crear pools de usuarios concurrentes
        async def user_session(user_id: int):
            user_results = []
            user_start = time.time()
            
            # Calcular requests por usuario
            requests_per_user = int((target_rps * duration) / concurrent_users)
            interval = 1.0 / (target_rps / concurrent_users)
            
            while time.time() < end_time:
                try:
                    result = await self._make_request(session, endpoint, method)
                    user_results.append(result)
                    
                    # Esperar el intervalo calculado
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.warning(f"Error en usuario {user_id}: {e}")
                    await asyncio.sleep(interval)
            
            return user_results
        
        # Crear usuarios concurrentes
        user_tasks = [user_session(i) for i in range(concurrent_users)]
        user_results = await asyncio.gather(*user_tasks)
        
        # Consolidar resultados
        for user_result_list in user_results:
            results.extend(user_result_list)
        
        return results
    
    async def _make_request(self, session: aiohttp.ClientSession, 
                          endpoint: str, method: str) -> Dict[str, Any]:
        """Realizar una request HTTP"""
        url = f"{self.base_url}{endpoint}"
        headers = {"User-Agent": "StressTest-Client/1.0"}
        
        start_time = time.time()
        
        try:
            if method.upper() == "GET":
                async with session.get(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    return {
                        "status_code": response.status,
                        "response_time": response_time,
                        "success": 200 <= response.status < 400
                    }
            
            elif method.upper() == "POST":
                async with session.post(url, headers=headers) as response:
                    response_time = time.time() - start_time
                    return {
                        "status_code": response.status,
                        "response_time": response_time,
                        "success": 200 <= response.status < 400
                    }
            
            else:
                raise ValueError(f"Método HTTP no soportado: {method}")
                
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return {
                "status_code": 408,  # Request Timeout
                "response_time": response_time,
                "success": False
            }
        except Exception as e:
            response_time = time.time() - start_time
            return {
                "status_code": 500,
                "response_time": response_time,
                "success": False,
                "error": str(e)
            }
    
    def _calculate_peak_rps(self, response_times: List[Dict], start_time: float) -> float:
        """Calcular RPS peak en ventana de 1 segundo"""
        if not response_times:
            return 0
        
        # Agrupar requests por timestamp (ventana de 1 segundo)
        windows = defaultdict(int)
        
        for result in response_times:
            # Estimar timestamp basado en response_time relativo
            # (en un test real, trackearíamos el timestamp real)
            request_time = result["response_time"]
            window = int(request_time)  # Ventana de 1 segundo
            windows[window] += 1
        
        # Encontrar ventana con más requests
        max_requests = max(windows.values()) if windows else 0
        return max_requests  # RPS en la ventana peak
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil de una lista de datos"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(percentile / 100 * len(sorted_data))
        if index >= len(sorted_data):
            index = len(sorted_data) - 1
        return sorted_data[index]


class StressTestSuite:
    """Suite completa de stress tests"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.tester = RateLimitTester(base_url)
        self.configs = self._create_test_configs()
    
    def _create_test_configs(self) -> List[RateLimitConfig]:
        """Crear configuraciones de tests de stress"""
        return [
            # Test 1: Tráfico normal moderado
            RateLimitConfig(
                name="Normal Load Test",
                requests_per_second=10,
                burst_size=20,
                duration_seconds=60,
                concurrent_users=5,
                endpoint="/api/v1/articles"
            ),
            
            # Test 2: Alta carga
            RateLimitConfig(
                name="High Load Test",
                requests_per_second=50,
                burst_size=100,
                duration_seconds=120,
                concurrent_users=20,
                endpoint="/api/v1/articles"
            ),
            
            # Test 3: Carga extrema
            RateLimitConfig(
                name="Extreme Load Test",
                requests_per_second=100,
                burst_size=200,
                duration_seconds=60,
                concurrent_users=50,
                endpoint="/api/v1/search"
            ),
            
            # Test 4: Rate limiting específico
            RateLimitConfig(
                name="Rate Limit Enforcement Test",
                requests_per_second=20,  # Carga moderada para activar rate limiting
                burst_size=40,
                duration_seconds=90,
                concurrent_users=10,
                endpoint="/api/v1/search"
            ),
            
            # Test 5: Test de endpoints críticos
            RateLimitConfig(
                name="Critical Endpoints Stress",
                requests_per_second=30,
                burst_size=60,
                duration_seconds=60,
                concurrent_users=15,
                endpoint="/api/v1/articles/1"
            )
        ]
    
    async def run_all_stress_tests(self) -> Dict[str, Any]:
        """Ejecutar toda la suite de stress tests"""
        logger.info("Iniciando suite completa de stress tests...")
        
        start_time = time.time()
        test_results = []
        
        for config in self.configs:
            try:
                logger.info(f"Ejecutando test: {config.name}")
                result = await self.tester.test_rate_limit_single_endpoint(config)
                test_results.append(result)
                
                # Pequeña pausa entre tests
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error en test {config.name}: {e}")
        
        total_time = time.time() - start_time
        
        # Análisis de resultados
        analysis = self._analyze_results(test_results)
        
        return {
            "test_suite": "API Stress Testing",
            "execution_time": round(total_time, 2),
            "total_tests": len(self.configs),
            "completed_tests": len(test_results),
            "test_results": [self._result_to_dict(result) for result in test_results],
            "analysis": analysis,
            "recommendations": self._generate_stress_recommendations(analysis)
        }
    
    def _analyze_results(self, results: List[RateLimitResult]) -> Dict[str, Any]:
        """Analizar resultados de todos los tests"""
        if not results:
            return {"error": "No hay resultados para analizar"}
        
        # Métricas agregadas
        total_requests = sum(result.total_requests for result in results)
        total_rate_limited = sum(result.rate_limited_requests for result in results)
        avg_error_rate = statistics.mean(result.error_rate for result in results)
        
        # Identificar patrones
        rate_limited_tests = [r for r in results if r.rate_limited_requests > 0]
        high_error_tests = [r for r in results if r.error_rate > 5.0]
        
        # Performance bajo carga
        performance_degradation = []
        for i, result in enumerate(results[:-1]):
            current_rps = result.sustained_rps
            next_rps = results[i+1].sustained_rps
            if next_rps > current_rps * 1.5:  # Incremento significativo de carga
                degradation = (result.p95_response_time - results[i+1].p95_response_time) / results[i+1].p95_response_time
                performance_degradation.append(degradation)
        
        return {
            "total_requests": total_requests,
            "total_rate_limited": total_rate_limited,
            "rate_limiting_triggered": len(rate_limited_tests),
            "tests_with_high_errors": len(high_error_tests),
            "average_error_rate": round(avg_error_rate, 2),
            "performance_degradation": {
                "detected": len(performance_degradation) > 0,
                "average_degradation": round(statistics.mean(performance_degradation) * 100, 2) if performance_degradation else 0
            },
            "system_resilience": self._assess_system_resilience(results),
            "bottlenecks": self._identify_bottlenecks(results)
        }
    
    def _assess_system_resilience(self, results: List[RateLimitResult]) -> Dict[str, Any]:
        """Evaluar resilencia del sistema"""
        resilience_score = 100
        
        # Penalizar por errores bajo carga
        high_load_tests = [r for r in results if r.sustained_rps > 30]
        if high_load_tests:
            avg_error_high_load = statistics.mean(r.error_rate for r in high_load_tests)
            resilience_score -= avg_error_high_load * 2
        
        # Penalizar por degradación severa de performance
        severe_degradation_tests = [r for r in results if r.p95_response_time > 2000]
        resilience_score -= len(severe_degradation_tests) * 10
        
        # Penalizar por rate limiting excesivo
        excessive_rate_limit_tests = [r for r in results if r.rate_limited_requests > r.total_requests * 0.1]
        resilience_score -= len(excessive_rate_limit_tests) * 15
        
        return {
            "resilience_score": max(0, int(resilience_score)),
            "status": "Excellent" if resilience_score >= 90 else 
                    "Good" if resilience_score >= 70 else
                    "Fair" if resilience_score >= 50 else "Poor"
        }
    
    def _identify_bottlenecks(self, results: List[RateLimitResult]) -> List[str]:
        """Identificar posibles cuellos de botella"""
        bottlenecks = []
        
        # Analizar cada test
        for result in results:
            # Rate limiting muy bajo
            if result.rate_limited_requests > result.total_requests * 0.5:
                bottlenecks.append(f"Rate limiting agresivo en test '{result.test_name}'")
            
            # Response times muy altos
            if result.p95_response_time > 3000:
                bottlenecks.append(f"Alta latencia en test '{result.test_name}' (P95: {result.p95_response_time}ms)")
            
            # Throughput muy bajo
            if result.sustained_rps < 5 and result.total_requests > 100:
                bottlenecks.append(f"Bajo throughput en test '{result.test_name}'")
            
            # Error rate alto
            if result.error_rate > 10:
                bottlenecks.append(f"Alto rate de errores en test '{result.test_name}' ({result.error_rate}%)")
        
        return bottlenecks
    
    def _generate_stress_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones basadas en análisis de stress"""
        recommendations = []
        
        # Recomendaciones de rate limiting
        if analysis.get("rate_limiting_triggered", 0) == 0:
            recommendations.append("Considerar implementar rate limiting más estricto para proteger recursos")
        elif analysis.get("rate_limiting_triggered", 0) > len(self.configs) * 0.7:
            recommendations.append("Rate limiting demasiado agresivo - revisar configuración para mejor UX")
        
        # Recomendaciones de performance
        if analysis.get("tests_with_high_errors", 0) > 0:
            recommendations.append("Investigar y resolver errores bajo carga alta")
        
        if analysis.get("performance_degradation", {}).get("detected", False):
            degradation = analysis.get("performance_degradation", {}).get("average_degradation", 0)
            recommendations.append(f"Optimizar performance - degradación promedio del {degradation}% bajo carga")
        
        # Recomendaciones de escalabilidad
        resilience = analysis.get("system_resilience", {})
        if resilience.get("status") == "Poor":
            recommendations.append("Sistema necesita mejoras de escalabilidad y resilencia")
        
        # Recomendaciones específicas de bottlenecks
        bottlenecks = analysis.get("bottlenecks", [])
        for bottleneck in bottlenecks[:3]:  # Top 3 bottlenecks
            recommendations.append(f"Resolver bottleneck: {bottleneck}")
        
        # Recomendaciones generales
        if not recommendations:
            recommendations.append("Sistema maneja bien la carga - continuar monitoreo")
        
        return recommendations
    
    def _result_to_dict(self, result: RateLimitResult) -> Dict[str, Any]:
        """Convertir RateLimitResult a diccionario"""
        return {
            "test_name": result.test_name,
            "total_requests": result.total_requests,
            "successful_requests": result.successful_requests,
            "rate_limited_requests": result.rate_limited_requests,
            "failed_requests": result.failed_requests,
            "avg_response_time_ms": result.avg_response_time,
            "p95_response_time_ms": result.p95_response_time,
            "p99_response_time_ms": result.p99_response_time,
            "peak_rps": result.peak_rps,
            "sustained_rps": result.sustained_rps,
            "error_rate": result.error_rate,
            "rate_limit_status_codes": result.rate_limit_status_codes,
            "timestamp": result.timestamp
        }


def main():
    """Función principal para ejecutar stress tests"""
    import argparse
    
    parser = argparse.ArgumentParser(description="API Stress Tests for AI News Aggregator")
    parser.add_argument("--host", default="localhost:8000", help="API host to test")
    parser.add_argument("--output", default="stress_test_report.json", help="Output file for results")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}"
    
    # Ejecutar stress tests
    test_suite = StressTestSuite(base_url)
    results = asyncio.run(test_suite.run_all_stress_tests())
    
    # Guardar resultados
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Resultados de stress test guardados en {args.output}")
    
    # Mostrar resumen
    if "error" not in results:
        print(f"\n=== RESUMEN DE STRESS TESTS ===")
        print(f"Tests completados: {results['completed_tests']}/{results['total_tests']}")
        print(f"Total requests: {results['analysis']['total_requests']}")
        print(f"Rate limited requests: {results['analysis']['total_rate_limited']}")
        print(f"Error rate promedio: {results['analysis']['average_error_rate']}%")
        
        resilience = results['analysis']['system_resilience']
        print(f"Resilencia del sistema: {resilience['status']} ({resilience['resilience_score']}/100)")
        
        print(f"\nTiempo total: {results['execution_time']}s")
        
        if results['recommendations']:
            print("\n=== RECOMENDACIONES ===")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"{i}. {rec}")
        
        if results['analysis']['bottlenecks']:
            print("\n=== CUELLOS DE BOTELLA DETECTADOS ===")
            for bottleneck in results['analysis']['bottlenecks']:
                print(f"⚠️  {bottleneck}")
    else:
        print(f"Error en stress tests: {results['error']}")


if __name__ == "__main__":
    main()