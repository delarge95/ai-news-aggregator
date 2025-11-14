"""
Configuración de escenarios de carga y sistema de reporte automático de métricas
Centraliza la configuración y automatización de tests de performance
"""

import json
import yaml
import logging
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import os
import schedule
import time
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from pathlib import Path

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LoadScenarioConfig:
    """Configuración de un escenario de carga específico"""
    name: str
    description: str
    type: str  # "load", "stress", "endurance", "spike"
    target_rps: int
    duration_minutes: int
    ramp_up_time_minutes: int
    concurrent_users: int
    endpoints: List[str]
    weight_distribution: Dict[str, int]  # endpoint -> weight percentage
    success_criteria: Dict[str, Any]
    failure_criteria: Dict[str, Any]

@dataclass
class MetricThreshold:
    """Threshold para una métrica específica"""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    unit: str
    comparison_operator: str  # ">", "<", ">=", "<="
    aggregation: str  # "avg", "p95", "max"

@dataclass
class AlertConfig:
    """Configuración de alertas"""
    enabled: bool
    email_recipients: List[str]
    slack_webhook: Optional[str]
    webhook_url: Optional[str]
    thresholds: List[MetricThreshold]
    cooldown_minutes: int

@dataclass
class ReportingConfig:
    """Configuración del sistema de reporte"""
    output_formats: List[str]  # ["json", "html", "csv"]
    storage_path: str
    retention_days: int
    auto_archive: bool
    generate_summary_report: bool
    include_charts: bool

@dataclass
class PerformanceTestSuiteConfig:
    """Configuración completa de la suite de tests"""
    test_name: str
    base_environment: str
    environments: Dict[str, Dict[str, Any]]  # env -> config
    load_scenarios: List[LoadScenarioConfig]
    alert_config: AlertConfig
    reporting_config: ReportingConfig
    scheduled_runs: Dict[str, str]  # cron_schedule -> scenario_name

class LoadScenarioManager:
    """Gestor de escenarios de carga"""
    
    def __init__(self, config: PerformanceTestSuiteConfig):
        self.config = config
        self.scenario_configs = self._create_default_scenarios()
    
    def _create_default_scenarios(self) -> List[LoadScenarioConfig]:
        """Crear escenarios de carga por defecto"""
        return [
            # Escenario 1: Carga normal
            LoadScenarioConfig(
                name="Normal Load Test",
                description="Simula tráfico normal durante horas de trabajo",
                type="load",
                target_rps=20,
                duration_minutes=30,
                ramp_up_time_minutes=5,
                concurrent_users=10,
                endpoints=[
                    "/api/v1/articles",
                    "/api/v1/search",
                    "/api/v1/articles/1",
                    "/api/v1/users/1/news",
                    "/health"
                ],
                weight_distribution={
                    "/api/v1/articles": 40,
                    "/api/v1/search": 25,
                    "/api/v1/articles/1": 20,
                    "/api/v1/users/1/news": 10,
                    "/health": 5
                },
                success_criteria={
                    "avg_response_time_ms": 500,
                    "p95_response_time_ms": 1000,
                    "error_rate_percent": 1.0,
                    "success_rate_percent": 99.0
                },
                failure_criteria={
                    "avg_response_time_ms": 1000,
                    "p95_response_time_ms": 2000,
                    "error_rate_percent": 5.0,
                    "success_rate_percent": 95.0
                }
            ),
            
            # Escenario 2: Carga alta
            LoadScenarioConfig(
                name="High Load Test",
                description="Simula pico de tráfico durante eventos importantes",
                type="stress",
                target_rps=100,
                duration_minutes=60,
                ramp_up_time_minutes=10,
                concurrent_users=50,
                endpoints=[
                    "/api/v1/articles",
                    "/api/v1/search",
                    "/api/v1/articles/1",
                    "/api/v1/users/1/news",
                    "/health"
                ],
                weight_distribution={
                    "/api/v1/articles": 45,
                    "/api/v1/search": 30,
                    "/api/v1/articles/1": 15,
                    "/api/v1/users/1/news": 5,
                    "/health": 5
                },
                success_criteria={
                    "avg_response_time_ms": 800,
                    "p95_response_time_ms": 1500,
                    "error_rate_percent": 2.0,
                    "success_rate_percent": 98.0
                },
                failure_criteria={
                    "avg_response_time_ms": 1500,
                    "p95_response_time_ms": 3000,
                    "error_rate_percent": 10.0,
                    "success_rate_percent": 90.0
                }
            ),
            
            # Escenario 3: Endurance test
            LoadScenarioConfig(
                name="Endurance Test",
                description="Test de resistencia prolongada",
                type="endurance",
                target_rps=30,
                duration_minutes=240,  # 4 horas
                ramp_up_time_minutes=15,
                concurrent_users=15,
                endpoints=[
                    "/api/v1/articles",
                    "/api/v1/search",
                    "/api/v1/articles/1"
                ],
                weight_distribution={
                    "/api/v1/articles": 60,
                    "/api/v1/search": 30,
                    "/api/v1/articles/1": 10
                },
                success_criteria={
                    "avg_response_time_ms": 600,
                    "p95_response_time_ms": 1200,
                    "error_rate_percent": 1.5,
                    "memory_leak_percent": 5.0  # Max memory increase
                },
                failure_criteria={
                    "avg_response_time_ms": 1200,
                    "p95_response_time_ms": 2500,
                    "error_rate_percent": 5.0,
                    "memory_leak_percent": 15.0
                }
            ),
            
            # Escenario 4: Spike test
            LoadScenarioConfig(
                name="Spike Test",
                description="Test de respuesta a picos súbitos de tráfico",
                type="spike",
                target_rps=10,
                duration_minutes=15,
                ramp_up_time_minutes=2,
                concurrent_users=100,  # Pico súbito
                endpoints=[
                    "/api/v1/articles",
                    "/api/v1/search",
                    "/health"
                ],
                weight_distribution={
                    "/api/v1/articles": 50,
                    "/api/v1/search": 35,
                    "/health": 15
                },
                success_criteria={
                    "avg_response_time_ms": 1000,
                    "p95_response_time_ms": 2000,
                    "error_rate_percent": 3.0,
                    "recovery_time_seconds": 60
                },
                failure_criteria={
                    "avg_response_time_ms": 2000,
                    "p95_response_time_ms": 4000,
                    "error_rate_percent": 15.0,
                    "recovery_time_seconds": 180
                }
            )
        ]
    
    def get_scenario_config(self, scenario_name: str) -> Optional[LoadScenarioConfig]:
        """Obtener configuración de un escenario específico"""
        for scenario in self.scenario_configs:
            if scenario.name == scenario_name:
                return scenario
        return None
    
    def list_scenarios(self) -> List[str]:
        """Listar todos los escenarios disponibles"""
        return [scenario.name for scenario in self.scenario_configs]
    
    def add_custom_scenario(self, scenario: LoadScenarioConfig):
        """Agregar un escenario personalizado"""
        self.scenario_configs.append(scenario)
        logger.info(f"Escenario personalizado agregado: {scenario.name}")
    
    def validate_scenario(self, scenario: LoadScenarioConfig) -> Dict[str, Any]:
        """Validar configuración de escenario"""
        issues = []
        
        # Validar weights
        total_weight = sum(scenario.weight_distribution.values())
        if abs(total_weight - 100) > 0.01:
            issues.append(f"Suma de weights debe ser 100, actual: {total_weight}")
        
        # Validar endpoints
        if not scenario.endpoints:
            issues.append("Debe especificar al menos un endpoint")
        
        for endpoint in scenario.endpoints:
            if endpoint not in scenario.weight_distribution:
                issues.append(f"Endpoint {endpoint} no tiene weight definido")
        
        # Validar duraciones
        if scenario.ramp_up_time_minutes >= scenario.duration_minutes:
            issues.append("Ramp up time debe ser menor que duración total")
        
        # Validar criterios de éxito/fallo
        required_metrics = ["avg_response_time_ms", "p95_response_time_ms", "error_rate_percent"]
        for metric in required_metrics:
            if metric not in scenario.success_criteria or metric not in scenario.failure_criteria:
                issues.append(f"Métrica {metric} debe estar en success_criteria y failure_criteria")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }


class MetricReporter:
    """Sistema de reporte automático de métricas"""
    
    def __init__(self, config: ReportingConfig):
        self.config = config
        self.storage_path = Path(config.storage_path)
        self.storage_path.mkdir(exist_ok=True)
    
    def generate_test_report(self, test_results: Dict[str, Any], 
                           scenario: LoadScenarioConfig) -> Dict[str, Any]:
        """Generar reporte completo de un test"""
        timestamp = datetime.now()
        
        # Análisis de resultados
        analysis = self._analyze_test_results(test_results, scenario)
        
        # Verificar thresholds
        threshold_violations = self._check_thresholds(test_results, analysis)
        
        # Generar reporte HTML si está habilitado
        html_report = None
        if "html" in self.config.output_formats and self.config.include_charts:
            html_report = self._generate_html_report(test_results, analysis, scenario)
        
        # Generar resumen ejecutivo
        executive_summary = self._generate_executive_summary(analysis, threshold_violations)
        
        report_data = {
            "test_info": {
                "scenario_name": scenario.name,
                "test_type": scenario.type,
                "execution_time": timestamp.isoformat(),
                "duration_minutes": scenario.duration_minutes,
                "target_rps": scenario.target_rps,
                "concurrent_users": scenario.concurrent_users
            },
            "test_results": test_results,
            "analysis": analysis,
            "threshold_violations": threshold_violations,
            "executive_summary": executive_summary,
            "recommendations": self._generate_recommendations(analysis, threshold_violations),
            "html_report": html_report
        }
        
        # Guardar reportes en formatos solicitados
        self._save_reports(report_data, timestamp)
        
        return report_data
    
    def _analyze_test_results(self, test_results: Dict[str, Any], 
                            scenario: LoadScenarioConfig) -> Dict[str, Any]:
        """Analizar resultados de test"""
        analysis = {}
        
        # Métricas de rendimiento
        if "performance_metrics" in test_results:
            perf_metrics = test_results["performance_metrics"]
            
            analysis["performance"] = {
                "avg_response_time_ms": perf_metrics.get("avg_response_time_ms", 0),
                "p95_response_time_ms": perf_metrics.get("p95_response_time_ms", 0),
                "p99_response_time_ms": perf_metrics.get("p99_response_time_ms", 0),
                "max_response_time_ms": perf_metrics.get("max_response_time_ms", 0),
                "throughput_rps": perf_metrics.get("throughput_rps", 0),
                "error_rate_percent": perf_metrics.get("error_rate", 0)
            }
        
        # Análisis de endpoints
        if "endpoint_results" in test_results:
            endpoint_results = test_results["endpoint_results"]
            analysis["endpoint_analysis"] = {}
            
            for endpoint, metrics in endpoint_results.items():
                analysis["endpoint_analysis"][endpoint] = {
                    "avg_response_time": metrics.get("avg_response_time_ms", 0),
                    "success_rate": metrics.get("success_rate_percent", 0),
                    "throughput": metrics.get("throughput_rps", 0)
                }
        
        # Análisis de carga
        analysis["load_analysis"] = {
            "target_rps_achieved": test_results.get("achieved_rps", 0) >= scenario.target_rps * 0.9,
            "ramp_up_successful": self._evaluate_ramp_up(test_results),
            "sustained_load_successful": self._evaluate_sustained_load(test_results, scenario)
        }
        
        # Evaluación general
        overall_score = self._calculate_overall_score(analysis, scenario)
        analysis["overall_score"] = overall_score
        analysis["test_status"] = self._determine_test_status(analysis, scenario)
        
        return analysis
    
    def _evaluate_ramp_up(self, test_results: Dict[str, Any]) -> bool:
        """Evaluar si el ramp up fue exitoso"""
        # En implementación real, analizarías la curva de ramp up
        return test_results.get("ramp_up_errors", 0) < 5
    
    def _evaluate_sustained_load(self, test_results: Dict[str, Any], 
                               scenario: LoadScenarioConfig) -> bool:
        """Evaluar si la carga sostenida fue exitosa"""
        error_rate = test_results.get("performance_metrics", {}).get("error_rate", 100)
        return error_rate <= scenario.success_criteria["error_rate_percent"]
    
    def _calculate_overall_score(self, analysis: Dict[str, Any], 
                               scenario: LoadScenarioConfig) -> int:
        """Calcular score general del test"""
        score = 100
        
        # Penalizar por métricas de performance
        perf = analysis.get("performance", {})
        avg_response = perf.get("avg_response_time_ms", 0)
        p95_response = perf.get("p95_response_time_ms", 0)
        error_rate = perf.get("error_rate_percent", 0)
        
        if avg_response > scenario.success_criteria["avg_response_time_ms"]:
            score -= 20
        
        if p95_response > scenario.success_criteria["p95_response_time_ms"]:
            score -= 30
        
        if error_rate > scenario.success_criteria["error_rate_percent"]:
            score -= min(40, error_rate * 10)
        
        # Penalizar por problemas de endpoints
        endpoint_analysis = analysis.get("endpoint_analysis", {})
        failed_endpoints = sum(1 for metrics in endpoint_analysis.values() 
                             if metrics.get("success_rate", 0) < 95)
        score -= failed_endpoints * 15
        
        return max(0, int(score))
    
    def _determine_test_status(self, analysis: Dict[str, Any], 
                             scenario: LoadScenarioConfig) -> str:
        """Determinar estado general del test"""
        score = analysis["overall_score"]
        perf = analysis.get("performance", {})
        
        error_rate = perf.get("error_rate_percent", 0)
        avg_response = perf.get("avg_response_time_ms", 0)
        
        if score >= 90 and error_rate < 1:
            return "PASSED"
        elif score >= 70 and error_rate < scenario.success_criteria["error_rate_percent"]:
            return "PASSED_WITH_WARNINGS"
        else:
            return "FAILED"
    
    def _check_thresholds(self, test_results: Dict[str, Any], 
                        analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verificar violaciones de thresholds"""
        violations = []
        
        perf = analysis.get("performance", {})
        
        # Verificar response time
        if perf.get("avg_response_time_ms", 0) > 1000:
            violations.append({
                "metric": "avg_response_time_ms",
                "value": perf["avg_response_time_ms"],
                "threshold": 1000,
                "severity": "warning"
            })
        
        # Verificar error rate
        error_rate = perf.get("error_rate_percent", 0)
        if error_rate > 5:
            violations.append({
                "metric": "error_rate_percent",
                "value": error_rate,
                "threshold": 5,
                "severity": "critical"
            })
        
        return violations
    
    def _generate_executive_summary(self, analysis: Dict[str, Any], 
                                  violations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generar resumen ejecutivo"""
        status = analysis["test_status"]
        score = analysis["overall_score"]
        
        summary = {
            "overall_status": status,
            "performance_score": score,
            "summary_text": "",
            "key_metrics": {
                "avg_response_time_ms": analysis.get("performance", {}).get("avg_response_time_ms", 0),
                "error_rate_percent": analysis.get("performance", {}).get("error_rate_percent", 0),
                "throughput_rps": analysis.get("performance", {}).get("throughput_rps", 0)
            },
            "critical_issues": len([v for v in violations if v["severity"] == "critical"]),
            "warnings": len([v for v in violations if v["severity"] == "warning"])
        }
        
        # Generar texto del resumen
        if status == "PASSED":
            summary["summary_text"] = f"El test se completó exitosamente con un score de {score}/100. No se detectaron problemas críticos."
        elif status == "PASSED_WITH_WARNINGS":
            summary["summary_text"] = f"El test se completó con warnings. Score: {score}/100. Se identificaron {len(violations)} violaciones de thresholds."
        else:
            summary["summary_text"] = f"El test falló. Score: {score}/100. Se detectaron problemas críticos que requieren atención."
        
        return summary
    
    def _generate_recommendations(self, analysis: Dict[str, Any], 
                                violations: List[Dict[str, Any]]) -> List[str]:
        """Generar recomendaciones basadas en análisis"""
        recommendations = []
        
        perf = analysis.get("performance", {})
        
        # Recomendaciones basadas en performance
        avg_response = perf.get("avg_response_time_ms", 0)
        if avg_response > 800:
            recommendations.append("Optimizar response time - considerar implementar caching")
        
        error_rate = perf.get("error_rate_percent", 0)
        if error_rate > 2:
            recommendations.append("Reducir error rate - investigar causas de fallos")
        
        throughput = perf.get("throughput_rps", 0)
        if throughput < 10:
            recommendations.append("Mejorar throughput - optimizar queries de base de datos")
        
        # Recomendaciones basadas en violaciones
        for violation in violations:
            if violation["metric"] == "error_rate_percent":
                recommendations.append("Implementar mejor manejo de errores y recovery mechanisms")
            elif violation["metric"] == "avg_response_time_ms":
                recommendations.append("Optimizar endpoints con alta latencia")
        
        if not recommendations:
            recommendations.append("Performance del sistema está dentro de parámetros normales")
        
        return recommendations
    
    def _generate_html_report(self, test_results: Dict[str, Any], 
                            analysis: Dict[str, Any], 
                            scenario: LoadScenarioConfig) -> str:
        """Generar reporte HTML"""
        # En implementación real, usarías templates HTML
        html_template = f"""
        <html>
        <head>
            <title>Performance Test Report - {scenario.name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .metric {{ margin: 10px 0; padding: 10px; background: #fff; border: 1px solid #ddd; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .warning {{ color: orange; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Performance Test Report</h1>
                <h2>{scenario.name}</h2>
                <p>Test Type: {scenario.type}</p>
                <p>Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="metric">
                <h3>Overall Results</h3>
                <p>Status: <span class="{analysis['test_status'].lower()}">{analysis['test_status']}</span></p>
                <p>Score: {analysis['overall_score']}/100</p>
            </div>
            
            <div class="metric">
                <h3>Performance Metrics</h3>
                <p>Avg Response Time: {analysis['performance'].get('avg_response_time_ms', 0)}ms</p>
                <p>P95 Response Time: {analysis['performance'].get('p95_response_time_ms', 0)}ms</p>
                <p>Error Rate: {analysis['performance'].get('error_rate_percent', 0)}%</p>
                <p>Throughput: {analysis['performance'].get('throughput_rps', 0)} RPS</p>
            </div>
        </body>
        </html>
        """
        return html_template
    
    def _save_reports(self, report_data: Dict[str, Any], timestamp: datetime):
        """Guardar reportes en diferentes formatos"""
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        
        # Guardar JSON
        if "json" in self.config.output_formats:
            json_path = self.storage_path / f"report_{timestamp_str}.json"
            with open(json_path, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
        
        # Guardar HTML
        if "html" in self.config.output_formats and report_data.get("html_report"):
            html_path = self.storage_path / f"report_{timestamp_str}.html"
            with open(html_path, 'w') as f:
                f.write(report_data["html_report"])
        
        # Limpiar archivos antiguos
        if self.config.auto_archive:
            self._cleanup_old_reports()
    
    def _cleanup_old_reports(self):
        """Limpiar reportes antiguos"""
        cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
        
        for file_path in self.storage_path.glob("report_*.json"):
            if file_path.stat().st_mtime < cutoff_date.timestamp():
                file_path.unlink()
                logger.info(f"Archivo古老的 eliminado: {file_path}")


class AlertManager:
    """Gestor de alertas basado en thresholds"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
        self.last_alerts = {}
    
    def check_and_send_alerts(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Verificar thresholds y enviar alertas si es necesario"""
        if not self.config.enabled:
            return []
        
        triggered_alerts = []
        current_time = datetime.now()
        
        for threshold in self.config.thresholds:
            # Verificar cooldown
            if self._is_in_cooldown(threshold.metric_name, current_time):
                continue
            
            # Verificar threshold
            current_value = self._get_metric_value(analysis, threshold.metric_name)
            if current_value is None:
                continue
            
            if self._threshold_violated(current_value, threshold):
                alert = {
                    "metric": threshold.metric_name,
                    "value": current_value,
                    "threshold": threshold.critical_threshold,
                    "severity": "critical" if current_value > threshold.critical_threshold else "warning",
                    "timestamp": current_time.isoformat(),
                    "message": self._generate_alert_message(threshold, current_value)
                }
                
                triggered_alerts.append(alert)
                
                # Registrar alerta para cooldown
                self.last_alerts[threshold.metric_name] = current_time
        
        # Enviar alertas
        for alert in triggered_alerts:
            self._send_alert(alert)
        
        return triggered_alerts
    
    def _is_in_cooldown(self, metric_name: str, current_time: datetime) -> bool:
        """Verificar si el metric está en cooldown"""
        if metric_name not in self.last_alerts:
            return False
        
        last_alert_time = self.last_alerts[metric_name]
        cooldown_elapsed = current_time - last_alert_time
        
        return cooldown_elapsed.total_seconds() < (self.config.cooldown_minutes * 60)
    
    def _get_metric_value(self, analysis: Dict[str, Any], metric_name: str) -> Optional[float]:
        """Obtener valor de métrica del análisis"""
        # Mapear nombres de métricas a rutas en el análisis
        metric_paths = {
            "avg_response_time_ms": ["performance", "avg_response_time_ms"],
            "p95_response_time_ms": ["performance", "p95_response_time_ms"],
            "error_rate_percent": ["performance", "error_rate_percent"],
            "throughput_rps": ["performance", "throughput_rps"]
        }
        
        if metric_name not in metric_paths:
            return None
        
        # Navegar a través del análisis
        value = analysis
        for path in metric_paths[metric_name]:
            if isinstance(value, dict) and path in value:
                value = value[path]
            else:
                return None
        
        return float(value) if value is not None else None
    
    def _threshold_violated(self, value: float, threshold: MetricThreshold) -> bool:
        """Verificar si se violó el threshold"""
        if threshold.comparison_operator == ">":
            return value > threshold.critical_threshold
        elif threshold.comparison_operator == ">=":
            return value >= threshold.critical_threshold
        elif threshold.comparison_operator == "<":
            return value < threshold.warning_threshold
        elif threshold.comparison_operator == "<=":
            return value <= threshold.warning_threshold
        return False
    
    def _generate_alert_message(self, threshold: MetricThreshold, value: float) -> str:
        """Generar mensaje de alerta"""
        severity = "CRITICAL" if value > threshold.critical_threshold else "WARNING"
        return f"{severity}: {threshold.metric_name} = {value} {threshold.unit} (threshold: {threshold.critical_threshold} {threshold.unit})"
    
    def _send_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por los medios configurados"""
        # Enviar por email
        if self.config.email_recipients:
            self._send_email_alert(alert)
        
        # Enviar por webhook
        if self.config.webhook_url:
            self._send_webhook_alert(alert)
        
        # Enviar por Slack
        if self.config.slack_webhook:
            self._send_slack_alert(alert)
    
    def _send_email_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por email"""
        # Implementación básica - en producción usarías configuración real
        logger.warning(f"ALERT EMAIL: {alert['message']}")
    
    def _send_webhook_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por webhook"""
        # Implementación básica
        logger.warning(f"ALERT WEBHOOK: {alert['message']}")
    
    def _send_slack_alert(self, alert: Dict[str, Any]):
        """Enviar alerta por Slack"""
        # Implementación básica
        logger.warning(f"ALERT SLACK: {alert['message']}")


class AutomatedTestRunner:
    """Ejecutor automatizado de tests de performance"""
    
    def __init__(self, config: PerformanceTestSuiteConfig):
        self.config = config
        self.scenario_manager = LoadScenarioManager(config)
        self.reporter = MetricReporter(config.reporting_config)
        self.alert_manager = AlertManager(config.alert_config)
    
    def run_scheduled_tests(self):
        """Ejecutar tests programados"""
        logger.info("Iniciando ejecutor automatizado de tests...")
        
        for cron_schedule, scenario_name in self.config.scheduled_runs.items():
            schedule.every().day.at("09:00").do(self._run_scheduled_test, scenario_name)
            logger.info(f"Programado test '{scenario_name}' para cada día a las 09:00")
        
        # Loop principal
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verificar cada minuto
    
    def _run_scheduled_test(self, scenario_name: str):
        """Ejecutar test programado"""
        logger.info(f"Ejecutando test programado: {scenario_name}")
        
        scenario = self.scenario_manager.get_scenario_config(scenario_name)
        if not scenario:
            logger.error(f"Escenario no encontrado: {scenario_name}")
            return
        
        try:
            # Aquí ejecutarías el test real usando los otros módulos
            # test_results = execute_performance_test(scenario, self.config.environments["production"])
            
            # Simulación de resultados para demo
            test_results = {"status": "completed", "score": 85}
            
            # Generar reporte
            report = self.reporter.generate_test_report(test_results, scenario)
            
            # Verificar y enviar alertas
            alerts = self.alert_manager.check_and_send_alerts(report["analysis"])
            
            logger.info(f"Test completado. Score: {report['analysis']['overall_score']}")
            logger.info(f"Alertas enviadas: {len(alerts)}")
            
        except Exception as e:
            logger.error(f"Error ejecutando test programado: {e}")
    
    def save_config(self, file_path: str):
        """Guardar configuración a archivo"""
        with open(file_path, 'w') as f:
            json.dump(asdict(self.config), f, indent=2, default=str)
        logger.info(f"Configuración guardada en {file_path}")
    
    @classmethod
    def load_config(cls, file_path: str) -> 'AutomatedTestRunner':
        """Cargar configuración desde archivo"""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        
        # Reconstruir objetos de configuración
        load_scenarios = [LoadScenarioConfig(**scenario) for scenario in config_dict["load_scenarios"]]
        alert_thresholds = [MetricThreshold(**threshold) for threshold in config_dict["alert_config"]["thresholds"]]
        
        config = PerformanceTestSuiteConfig(
            test_name=config_dict["test_name"],
            base_environment=config_dict["base_environment"],
            environments=config_dict["environments"],
            load_scenarios=load_scenarios,
            alert_config=AlertConfig(
                enabled=config_dict["alert_config"]["enabled"],
                email_recipients=config_dict["alert_config"]["email_recipients"],
                slack_webhook=config_dict["alert_config"].get("slack_webhook"),
                webhook_url=config_dict["alert_config"].get("webhook_url"),
                thresholds=alert_thresholds,
                cooldown_minutes=config_dict["alert_config"]["cooldown_minutes"]
            ),
            reporting_config=ReportingConfig(**config_dict["reporting_config"]),
            scheduled_runs=config_dict["scheduled_runs"]
        )
        
        return cls(config)


def create_default_config() -> PerformanceTestSuiteConfig:
    """Crear configuración por defecto"""
    return PerformanceTestSuiteConfig(
        test_name="AI News Aggregator Performance Tests",
        base_environment="staging",
        environments={
            "development": {
                "api_host": "localhost:8000",
                "frontend_host": "localhost:3000",
                "database_host": "localhost:5432"
            },
            "staging": {
                "api_host": "staging-api.example.com",
                "frontend_host": "staging-frontend.example.com",
                "database_host": "staging-db.example.com"
            },
            "production": {
                "api_host": "api.example.com",
                "frontend_host": "frontend.example.com",
                "database_host": "db.example.com"
            }
        },
        load_scenarios=LoadScenarioManager(PerformanceTestSuiteConfig(
            "dummy", "dev", {}, [], AlertConfig(False, [], None, None, [], 0),
            ReportingConfig(["json"], "reports", 30, True, True, False), {}
        ))._create_default_scenarios(),
        alert_config=AlertConfig(
            enabled=True,
            email_recipients=["admin@example.com", "devops@example.com"],
            slack_webhook="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
            webhook_url="https://alerts.example.com/webhook",
            thresholds=[
                MetricThreshold("avg_response_time_ms", 800, 1200, "ms", ">=", "avg"),
                MetricThreshold("p95_response_time_ms", 1500, 2000, "ms", ">=", "p95"),
                MetricThreshold("error_rate_percent", 2.0, 5.0, "%", ">=", "avg"),
                MetricThreshold("throughput_rps", 50, 20, "rps", "<=", "avg")
            ],
            cooldown_minutes=15
        ),
        reporting_config=ReportingConfig(
            output_formats=["json", "html"],
            storage_path="./reports",
            retention_days=30,
            auto_archive=True,
            generate_summary_report=True,
            include_charts=True
        ),
        scheduled_runs={
            "0 9 * * 1": "Normal Load Test",  # Lunes 9am
            "0 14 * * 3": "High Load Test",   # Miércoles 2pm
            "0 2 * * 6": "Endurance Test"     # Sábado 2am
        }
    )


def main():
    """Función principal para gestión de configuración"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Test Configuration Manager")
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando create-config
    create_parser = subparsers.add_parser('create-config', help='Crear configuración por defecto')
    create_parser.add_argument('--output', default='performance_config.json', help='Archivo de salida')
    
    # Comando run-scheduled
    run_parser = subparsers.add_parser('run-scheduled', help='Ejecutar tests programados')
    run_parser.add_argument('--config', required=True, help='Archivo de configuración')
    
    # Comando list-scenarios
    list_parser = subparsers.add_parser('list-scenarios', help='Listar escenarios disponibles')
    list_parser.add_argument('--config', required=True, help='Archivo de configuración')
    
    args = parser.parse_args()
    
    if args.command == 'create-config':
        config = create_default_config()
        runner = AutomatedTestRunner(config)
        runner.save_config(args.output)
        print(f"Configuración creada en {args.output}")
        
    elif args.command == 'run-scheduled':
        runner = AutomatedTestRunner.load_config(args.config)
        runner.run_scheduled_tests()
        
    elif args.command == 'list-scenarios':
        runner = AutomatedTestRunner.load_config(args.config)
        scenarios = runner.scenario_manager.list_scenarios()
        print("Escenarios disponibles:")
        for scenario in scenarios:
            print(f"  - {scenario}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()