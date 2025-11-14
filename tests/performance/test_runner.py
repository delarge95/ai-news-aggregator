#!/usr/bin/env python3
"""
Test Runner Principal - Ejecutor de todos los tests de performance con thresholds y alertas
Integra todos los módulos de testing y proporciona interfaz unificada
"""

import asyncio
import sys
import os
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import argparse
import subprocess

# Agregar el directorio actual al path para importaciones
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar todos los módulos de testing
from load_test import NewsApiUser, AdminUser, CrawlerUser
from performance_test import CriticalEndpointsTest
from api_stress_test import StressTestSuite
from database_performance import DatabasePerformanceTestSuite
from frontend_performance import FrontendPerformanceTestSuite, FrontendTestConfig
from load_scenarios_config import (
    create_default_config, AutomatedTestRunner, 
    MetricThreshold, AlertConfig, ReportingConfig
)

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('performance_tests.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class PerformanceTestOrchestrator:
    """Orquestador principal de todos los tests de performance"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.test_results = {}
        self.alerts_triggered = []
        self.start_time = None
        self.end_time = None
        
        # Configurar thresholds de alerta
        self.alert_thresholds = {
            "response_time_p95_ms": 1000,
            "error_rate_percent": 2.0,
            "success_rate_percent": 95.0,
            "throughput_rps": 10.0,
            "database_query_time_ms": 500,
            "frontend_lcp_ms": 2500,
            "frontend_fid_ms": 100,
            "frontend_cls_score": 0.1
        }
    
    async def run_all_tests(self, environment: str = "staging") -> Dict[str, Any]:
        """Ejecutar suite completa de tests de performance"""
        logger.info(f"Iniciando suite completa de performance tests para ambiente: {environment}")
        self.start_time = datetime.now()
        
        try:
            # Test 1: Load Tests con Locust
            logger.info("Ejecutando Load Tests...")
            load_test_results = await self._run_load_tests(environment)
            self.test_results["load_tests"] = load_test_results
            
            # Test 2: Performance Tests de endpoints críticos
            logger.info("Ejecutando Performance Tests de endpoints...")
            performance_results = await self._run_performance_tests(environment)
            self.test_results["performance_tests"] = performance_results
            
            # Test 3: Stress Tests y Rate Limiting
            logger.info("Ejecutando Stress Tests...")
            stress_results = await self._run_stress_tests(environment)
            self.test_results["stress_tests"] = stress_results
            
            # Test 4: Database Performance Tests
            logger.info("Ejecutando Database Performance Tests...")
            db_results = await self._run_database_tests(environment)
            self.test_results["database_tests"] = db_results
            
            # Test 5: Frontend Performance Tests
            logger.info("Ejecutando Frontend Performance Tests...")
            frontend_results = await self._run_frontend_tests(environment)
            self.test_results["frontend_tests"] = frontend_results
            
            # Análisis integral
            overall_analysis = self._analyze_all_results()
            self.test_results["overall_analysis"] = overall_analysis
            
            # Verificar thresholds y generar alertas
            self._check_all_thresholds()
            
            # Generar reporte final
            final_report = self._generate_final_report()
            
            self.end_time = datetime.now()
            execution_time = (self.end_time - self.start_time).total_seconds()
            
            logger.info(f"Suite completa de tests finalizada en {execution_time:.2f} segundos")
            logger.info(f"Alertas generadas: {len(self.alerts_triggered)}")
            
            return {
                "execution_info": {
                    "start_time": self.start_time.isoformat(),
                    "end_time": self.end_time.isoformat(),
                    "total_duration_seconds": execution_time,
                    "environment": environment
                },
                "test_results": self.test_results,
                "alerts_triggered": self.alerts_triggered,
                "overall_status": self._determine_overall_status(),
                "final_report": final_report
            }
            
        except Exception as e:
            logger.error(f"Error durante ejecución de tests: {e}")
            self.end_time = datetime.now()
            return {
                "execution_info": {
                    "start_time": self.start_time.isoformat() if self.start_time else None,
                    "end_time": datetime.now().isoformat(),
                    "error": str(e)
                },
                "overall_status": "FAILED",
                "test_results": self.test_results,
                "alerts_triggered": self.alerts_triggered
            }
    
    async def _run_load_tests(self, environment: str) -> Dict[str, Any]:
        """Ejecutar load tests con Locust"""
        logger.info("Ejecutando load tests...")
        
        # Configuración de ambiente
        env_config = self.config.get("environments", {}).get(environment, {})
        api_host = env_config.get("api_host", "localhost:8000")
        
        # Generar comando locust
        locust_command = [
            "locust",
            "-f", "load_test.py",
            "--host", f"http://{api_host}",
            "--headless",
            "--users", "20",
            "--spawn-rate", "2",
            "--run-time", "5m",
            "--html", f"reports/load_test_{environment}.html",
            "--csv", f"reports/load_test_{environment}"
        ]
        
        try:
            # Ejecutar locust
            result = subprocess.run(
                locust_command,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutos timeout
            )
            
            # Procesar resultados
            load_results = {
                "command_executed": " ".join(locust_command),
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "status": "PASSED" if result.returncode == 0 else "FAILED",
                "execution_time": 300,  # 5 minutos
                "files_generated": [
                    f"reports/load_test_{environment}.html",
                    f"reports/load_test_{environment}_requests.csv",
                    f"reports/load_test_{environment}_failures.csv",
                    f"reports/load_test_{environment}_stats.csv",
                    f"reports/load_test_{environment}_stats_history.csv"
                ]
            }
            
            # Parsear resultados de Locust si están disponibles
            try:
                # Leer archivo CSV de estadísticas si existe
                stats_file = f"reports/load_test_{environment}_stats.csv"
                if os.path.exists(stats_file):
                    with open(stats_file, 'r') as f:
                        # Procesar CSV básico para extraer métricas
                        lines = f.readlines()
                        if len(lines) > 1:
                            headers = lines[0].strip().split(',')
                            values = lines[1].strip().split(',')
                            
                            stats_dict = dict(zip(headers, values))
                            load_results["parsed_stats"] = {
                                "total_requests": stats_dict.get("Request Count", "0"),
                                "avg_response_time": stats_dict.get("Average Response Time", "0"),
                                "min_response_time": stats_dict.get("Min Response Time", "0"),
                                "max_response_time": stats_dict.get("Max Response Time", "0"),
                                "requests_per_second": stats_dict.get("Requests/s", "0")
                            }
            except Exception as e:
                logger.warning(f"Error parseando estadísticas de load test: {e}")
            
            return load_results
            
        except subprocess.TimeoutExpired:
            logger.error("Load test timeout después de 10 minutos")
            return {
                "status": "TIMEOUT",
                "error": "Test timeout después de 10 minutos"
            }
        except Exception as e:
            logger.error(f"Error ejecutando load test: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def _run_performance_tests(self, environment: str) -> Dict[str, Any]:
        """Ejecutar performance tests de endpoints críticos"""
        logger.info("Ejecutando performance tests...")
        
        env_config = self.config.get("environments", {}).get(environment, {})
        api_host = env_config.get("api_host", "localhost:8000")
        
        try:
            # Importar y ejecutar tests de performance
            test_suite = CriticalEndpointsTest(f"http://{api_host}")
            results = await test_suite.run_all_tests()
            
            # Agregar información de configuración
            results["configuration"] = {
                "api_host": api_host,
                "concurrent_users": 10,
                "requests_per_user": 50,
                "timeout": 30
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Error en performance tests: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def _run_stress_tests(self, environment: str) -> Dict[str, Any]:
        """Ejecutar stress tests"""
        logger.info("Ejecutando stress tests...")
        
        env_config = self.config.get("environments", {}).get(environment, {})
        api_host = env_config.get("api_host", "localhost:8000")
        
        try:
            test_suite = StressTestSuite(f"http://{api_host}")
            results = await test_suite.run_all_stress_tests()
            
            return results
            
        except Exception as e:
            logger.error(f"Error en stress tests: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def _run_database_tests(self, environment: str) -> Dict[str, Any]:
        """Ejecutar database performance tests"""
        logger.info("Ejecutando database performance tests...")
        
        env_config = self.config.get("environments", {}).get(environment, {})
        db_config = env_config.get("database", {})
        
        try:
            test_suite = DatabasePerformanceTestSuite()
            
            # Actualizar configuración de base de datos
            if db_config:
                test_suite.config.host = db_config.get("host", "localhost")
                test_suite.config.port = db_config.get("port", 5432)
                test_suite.config.database = db_config.get("database", "ai_news_db")
                test_suite.config.user = db_config.get("user", "postgres")
                test_suite.config.password = db_config.get("password", "password")
            
            results = test_suite.run_comprehensive_db_test()
            
            return results
            
        except Exception as e:
            logger.error(f"Error en database tests: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    async def _run_frontend_tests(self, environment: str) -> Dict[str, Any]:
        """Ejecutar frontend performance tests"""
        logger.info("Ejecutando frontend performance tests...")
        
        env_config = self.config.get("environments", {}).get(environment, {})
        frontend_host = env_config.get("frontend_host", "localhost:3000")
        
        # Páginas a testear
        pages = ["/", "/articles", "/search", "/dashboard", "/articles/1"]
        
        try:
            config = FrontendTestConfig(
                name="Frontend Performance Test",
                base_url=f"http://{frontend_host}",
                pages_to_test=pages,
                concurrent_users=3,
                iterations_per_page=2
            )
            
            test_suite = FrontendPerformanceTestSuite(config)
            results = await test_suite.run_frontend_performance_tests()
            
            return results
            
        except Exception as e:
            logger.error(f"Error en frontend tests: {e}")
            return {
                "status": "FAILED",
                "error": str(e)
            }
    
    def _analyze_all_results(self) -> Dict[str, Any]:
        """Análisis integral de todos los resultados"""
        logger.info("Realizando análisis integral...")
        
        analysis = {
            "total_tests_run": len(self.test_results),
            "passed_tests": 0,
            "failed_tests": 0,
            "critical_issues": [],
            "performance_summary": {},
            "overall_score": 0
        }
        
        # Analizar load tests
        load_results = self.test_results.get("load_tests", {})
        if load_results.get("status") == "PASSED":
            analysis["passed_tests"] += 1
        else:
            analysis["failed_tests"] += 1
            analysis["critical_issues"].append(f"Load tests failed: {load_results.get('error', 'Unknown error')}")
        
        # Analizar performance tests
        perf_results = self.test_results.get("performance_tests", {})
        if "error" not in perf_results:
            analysis["passed_tests"] += 1
            perf_score = perf_results.get("overall_performance_score", 0)
            analysis["performance_summary"]["endpoint_performance"] = perf_score
        else:
            analysis["failed_tests"] += 1
            analysis["critical_issues"].append(f"Performance tests failed: {perf_results['error']}")
        
        # Analizar stress tests
        stress_results = self.test_results.get("stress_tests", {})
        if "error" not in stress_results:
            analysis["passed_tests"] += 1
            resilience_score = stress_results.get("analysis", {}).get("system_resilience", {}).get("resilience_score", 0)
            analysis["performance_summary"]["system_resilience"] = resilience_score
        else:
            analysis["failed_tests"] += 1
            analysis["critical_issues"].append(f"Stress tests failed: {stress_results['error']}")
        
        # Analizar database tests
        db_results = self.test_results.get("database_tests", {})
        if "error" not in db_results:
            analysis["passed_tests"] += 1
            db_score = db_results.get("health_evaluation", {}).get("overall_health_score", 0)
            analysis["performance_summary"]["database_health"] = db_score
        else:
            analysis["failed_tests"] += 1
            analysis["critical_issues"].append(f"Database tests failed: {db_results['error']}")
        
        # Analizar frontend tests
        frontend_results = self.test_results.get("frontend_tests", {})
        if "error" not in frontend_results:
            analysis["passed_tests"] += 1
            frontend_score = frontend_results.get("analysis", {}).get("overall_performance_score", 0)
            analysis["performance_summary"]["frontend_performance"] = frontend_score
        else:
            analysis["failed_tests"] += 1
            analysis["critical_issues"].append(f"Frontend tests failed: {frontend_results['error']}")
        
        # Calcular overall score
        perf_scores = [score for score in analysis["performance_summary"].values() if isinstance(score, (int, float))]
        if perf_scores:
            analysis["overall_score"] = round(sum(perf_scores) / len(perf_scores), 2)
        
        # Evaluar status general
        if analysis["failed_tests"] == 0 and analysis["overall_score"] >= 80:
            analysis["overall_status"] = "EXCELLENT"
        elif analysis["failed_tests"] <= 1 and analysis["overall_score"] >= 70:
            analysis["overall_status"] = "GOOD"
        elif analysis["failed_tests"] <= 2 and analysis["overall_score"] >= 60:
            analysis["overall_status"] = "FAIR"
        else:
            analysis["overall_status"] = "POOR"
        
        return analysis
    
    def _check_all_thresholds(self):
        """Verificar todos los thresholds y generar alertas"""
        logger.info("Verificando thresholds...")
        
        # Verificar load tests
        load_results = self.test_results.get("load_tests", {})
        if load_results.get("status") == "PASSED":
            # Verificar parsed stats si están disponibles
            parsed_stats = load_results.get("parsed_stats", {})
            avg_response_time = float(parsed_stats.get("avg_response_time", "0"))
            
            if avg_response_time > self.alert_thresholds["response_time_p95_ms"]:
                self.alerts_triggered.append({
                    "type": "response_time",
                    "test": "load_tests",
                    "value": avg_response_time,
                    "threshold": self.alert_thresholds["response_time_p95_ms"],
                    "severity": "warning" if avg_response_time < 2000 else "critical"
                })
        
        # Verificar performance tests
        perf_results = self.test_results.get("performance_tests", {})
        if "error" not in perf_results:
            evaluations = perf_results.get("evaluations", [])
            for evaluation in evaluations:
                if not evaluation.get("passed", True):
                    for issue in evaluation.get("issues", []):
                        if "response time" in issue.lower():
                            self.alerts_triggered.append({
                                "type": "endpoint_performance",
                                "test": "performance_tests",
                                "issue": issue,
                                "severity": "warning"
                            })
        
        # Verificar stress tests
        stress_results = self.test_results.get("stress_tests", {})
        if "error" not in stress_results:
            analysis = stress_results.get("analysis", {})
            if analysis.get("rate_limiting_triggered", 0) > 2:
                self.alerts_triggered.append({
                    "type": "rate_limiting",
                    "test": "stress_tests",
                    "message": f"Rate limiting triggered {analysis['rate_limiting_triggered']} times",
                    "severity": "warning"
                })
        
        # Verificar database tests
        db_results = self.test_results.get("database_tests", {})
        if "error" not in db_results:
            health = db_results.get("health_evaluation", {})
            if health.get("overall_health_score", 100) < 70:
                self.alerts_triggered.append({
                    "type": "database_health",
                    "test": "database_tests",
                    "value": health.get("overall_health_score", 0),
                    "threshold": 70,
                    "severity": "warning"
                })
        
        # Verificar frontend tests
        frontend_results = self.test_results.get("frontend_tests", {})
        if "error" not in frontend_results:
            cwv = frontend_results.get("analysis", {}).get("core_web_vitals_averages", {})
            if cwv.get("lcp", 0) > self.alert_thresholds["frontend_lcp_ms"]:
                self.alerts_triggered.append({
                    "type": "frontend_lcp",
                    "test": "frontend_tests",
                    "value": cwv.get("lcp", 0),
                    "threshold": self.alert_thresholds["frontend_lcp_ms"],
                    "severity": "warning"
                })
        
        logger.info(f"Se generaron {len(self.alerts_triggered)} alertas")
    
    def _determine_overall_status(self) -> str:
        """Determinar status general de los tests"""
        analysis = self.test_results.get("overall_analysis", {})
        overall_status = analysis.get("overall_status", "UNKNOWN")
        
        # Considerar alertas críticas
        critical_alerts = [alert for alert in self.alerts_triggered if alert.get("severity") == "critical"]
        if critical_alerts and overall_status == "EXCELLENT":
            overall_status = "GOOD"
        elif critical_alerts and overall_status in ["GOOD", "FAIR"]:
            overall_status = "POOR"
        
        return overall_status
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generar reporte final"""
        analysis = self.test_results.get("overall_analysis", {})
        
        # Resumen ejecutivo
        summary = {
            "test_suite_name": "AI News Aggregator Performance Tests",
            "execution_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "overall_status": self._determine_overall_status(),
            "total_tests": analysis.get("total_tests_run", 0),
            "passed_tests": analysis.get("passed_tests", 0),
            "failed_tests": analysis.get("failed_tests", 0),
            "overall_score": analysis.get("overall_score", 0),
            "alerts_generated": len(self.alerts_triggered),
            "execution_duration": (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        }
        
        # Métricas clave
        key_metrics = {}
        
        # Load test metrics
        load_results = self.test_results.get("load_tests", {})
        if load_results.get("parsed_stats"):
            stats = load_results["parsed_stats"]
            key_metrics["load_tests"] = {
                "total_requests": stats.get("total_requests", "0"),
                "avg_response_time": stats.get("avg_response_time", "0"),
                "requests_per_second": stats.get("requests_per_second", "0")
            }
        
        # Performance test metrics
        perf_results = self.test_results.get("performance_tests", {})
        if "error" not in perf_results:
            key_metrics["performance_tests"] = {
                "endpoints_tested": perf_results.get("total_endpoints_tested", 0),
                "performance_score": perf_results.get("overall_performance_score", 0)
            }
        
        # Database test metrics
        db_results = self.test_results.get("database_tests", {})
        if "error" not in db_results:
            health = db_results.get("health_evaluation", {})
            key_metrics["database_tests"] = {
                "health_score": health.get("overall_health_score", 0),
                "average_response_time": health.get("average_response_time_ms", 0)
            }
        
        # Frontend test metrics
        frontend_results = self.test_results.get("frontend_tests", {})
        if "error" not in frontend_results:
            analysis = frontend_results.get("analysis", {})
            key_metrics["frontend_tests"] = {
                "performance_score": analysis.get("overall_performance_score", 0),
                "core_web_vitals": analysis.get("core_web_vitals_averages", {})
            }
        
        summary["key_metrics"] = key_metrics
        
        # Recomendaciones
        recommendations = self._generate_recommendations()
        summary["recommendations"] = recommendations
        
        # Siguientes pasos
        next_steps = self._generate_next_steps()
        summary["next_steps"] = next_steps
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generar recomendaciones basadas en resultados"""
        recommendations = []
        
        analysis = self.test_results.get("overall_analysis", {})
        overall_score = analysis.get("overall_score", 0)
        
        # Recomendaciones basadas en score general
        if overall_score < 60:
            recommendations.append("Priorizar optimización de performance - score general bajo")
        
        # Recomendaciones basadas en alertas
        alert_types = set(alert["type"] for alert in self.alerts_triggered)
        
        if "response_time" in alert_types:
            recommendations.append("Implementar caching para reducir latencia de respuesta")
        
        if "database_health" in alert_types:
            recommendations.append("Optimizar queries de base de datos y agregar índices")
        
        if "frontend_lcp" in alert_types:
            recommendations.append("Optimizar imágenes y recursos críticos para mejorar LCP")
        
        if "rate_limiting" in alert_types:
            recommendations.append("Revisar configuración de rate limiting para mejor UX")
        
        # Recomendaciones específicas por test
        perf_results = self.test_results.get("performance_tests", {})
        if "error" not in perf_results:
            recommendations_list = perf_results.get("recommendations", [])
            recommendations.extend(recommendations_list[:3])  # Top 3
        
        if not recommendations:
            recommendations.append("Performance del sistema está en buen estado - mantener monitoreo")
        
        return recommendations
    
    def _generate_next_steps(self) -> List[str]:
        """Generar próximos pasos sugeridos"""
        steps = []
        
        if self.alerts_triggered:
            critical_alerts = [a for a in self.alerts_triggered if a.get("severity") == "critical"]
            if critical_alerts:
                steps.append("Resolver alertas críticas identificadas")
        
        if len(self.alerts_triggered) > 0:
            steps.append("Monitorear métricas de performance en producción")
        
        steps.append("Ejecutar tests de performance semanalmente")
        steps.append("Configurar alertas automáticas para métricas críticas")
        
        failed_tests = self.test_results.get("overall_analysis", {}).get("failed_tests", 0)
        if failed_tests > 0:
            steps.append("Repetir tests fallidos después de implementar fixes")
        
        return steps


def load_test_config(config_file: str) -> Dict[str, Any]:
    """Cargar configuración desde archivo"""
    if not os.path.exists(config_file):
        logger.warning(f"Archivo de configuración no encontrado: {config_file}")
        logger.info("Usando configuración por defecto...")
        return create_default_config_dict()
    
    try:
        with open(config_file, 'r') as f:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                import yaml
                config = yaml.safe_load(f)
            else:
                config = json.load(f)
        
        logger.info(f"Configuración cargada desde {config_file}")
        return config
        
    except Exception as e:
        logger.error(f"Error cargando configuración: {e}")
        return create_default_config_dict()


def create_default_config_dict() -> Dict[str, Any]:
    """Crear configuración por defecto en formato dict"""
    return {
        "test_name": "AI News Aggregator Performance Tests",
        "environments": {
            "development": {
                "api_host": "localhost:8000",
                "frontend_host": "localhost:3000",
                "database": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "ai_news_db",
                    "user": "postgres",
                    "password": "password"
                }
            },
            "staging": {
                "api_host": "staging-api.example.com",
                "frontend_host": "staging-frontend.example.com",
                "database": {
                    "host": "staging-db.example.com",
                    "port": 5432,
                    "database": "ai_news_staging",
                    "user": "staging_user",
                    "password": "staging_password"
                }
            },
            "production": {
                "api_host": "api.example.com",
                "frontend_host": "frontend.example.com",
                "database": {
                    "host": "db.example.com",
                    "port": 5432,
                    "database": "ai_news_prod",
                    "user": "prod_user",
                    "password": "prod_password"
                }
            }
        },
        "thresholds": {
            "response_time_p95_ms": 1000,
            "error_rate_percent": 2.0,
            "success_rate_percent": 95.0,
            "throughput_rps": 10.0,
            "database_query_time_ms": 500,
            "frontend_lcp_ms": 2500
        },
        "notifications": {
            "email": {
                "enabled": True,
                "recipients": ["admin@example.com", "devops@example.com"]
            },
            "slack": {
                "enabled": False,
                "webhook_url": ""
            }
        }
    }


async def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description="Performance Test Runner para AI News Aggregator")
    parser.add_argument("--config", default="performance_config.json", help="Archivo de configuración")
    parser.add_argument("--environment", default="staging", choices=["development", "staging", "production"],
                       help="Ambiente a testear")
    parser.add_argument("--output", default="performance_test_results.json", help="Archivo de salida de resultados")
    parser.add_argument("--create-reports-dir", action="store_true", help="Crear directorio de reportes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Output verbose")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Crear directorio de reportes
    if args.create_reports_dir:
        os.makedirs("reports", exist_ok=True)
        logger.info("Directorio de reportes creado")
    
    # Cargar configuración
    config = load_test_config(args.config)
    
    # Crear y ejecutar orquestador
    orchestrator = PerformanceTestOrchestrator(config)
    
    logger.info(f"Ejecutando suite completa de tests para ambiente: {args.environment}")
    
    try:
        results = await orchestrator.run_all_tests(args.environment)
        
        # Guardar resultados
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Resultados guardados en {args.output}")
        
        # Mostrar resumen
        print("\n" + "="*80)
        print("RESUMEN DE TESTS DE PERFORMANCE")
        print("="*80)
        
        execution_info = results.get("execution_info", {})
        print(f"Ambiente: {execution_info.get('environment', 'N/A')}")
        print(f"Inicio: {execution_info.get('start_time', 'N/A')}")
        print(f"Fin: {execution_info.get('end_time', 'N/A')}")
        print(f"Duración: {execution_info.get('total_duration_seconds', 0):.2f} segundos")
        
        overall_analysis = results.get("overall_analysis", {})
        print(f"\nStatus General: {results.get('overall_status', 'N/A')}")
        print(f"Tests Pasados: {overall_analysis.get('passed_tests', 0)}")
        print(f"Tests Fallidos: {overall_analysis.get('failed_tests', 0)}")
        print(f"Score General: {overall_analysis.get('overall_score', 0)}/100")
        
        alerts = results.get("alerts_triggered", [])
        print(f"Alertas Generadas: {len(alerts)}")
        
        if alerts:
            print("\nALERTAS:")
            for alert in alerts:
                severity_icon = "🔴" if alert.get("severity") == "critical" else "🟡"
                print(f"  {severity_icon} {alert.get('type', 'N/A')}: {alert.get('message', alert.get('issue', 'N/A'))}")
        
        final_report = results.get("final_report", {})
        recommendations = final_report.get("recommendations", [])
        if recommendations:
            print("\nRECOMENDACIONES:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        next_steps = final_report.get("next_steps", [])
        if next_steps:
            print("\nPRÓXIMOS PASOS:")
            for i, step in enumerate(next_steps, 1):
                print(f"  {i}. {step}")
        
        print("\n" + "="*80)
        
        # Determinar exit code
        overall_status = results.get("overall_status", "UNKNOWN")
        if overall_status in ["EXCELLENT", "GOOD"]:
            exit_code = 0
        elif overall_status == "FAIR":
            exit_code = 1
        else:
            exit_code = 2
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        logger.info("Tests interrumpidos por el usuario")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Error durante ejecución: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())