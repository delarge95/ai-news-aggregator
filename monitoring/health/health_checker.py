#!/usr/bin/env python3
"""
Health Check System para AI News Aggregator
Sistema automatizado de verificaciones de salud para todos los componentes
"""

import asyncio
import aiohttp
import time
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import redis
import psycopg2
from urllib.parse import urlparse

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/health_checks.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class HealthCheckResult:
    component: str
    status: HealthStatus
    response_time: Optional[float] = None
    message: str = ""
    details: Optional[Dict[str, Any]] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class HealthChecker:
    """Clase principal para verificaciones de salud"""
    
    def __init__(self):
        self.results: List[HealthCheckResult] = []
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def check_http_endpoint(self, name: str, url: str, 
                                expected_status: int = 200,
                                timeout: int = 30) -> HealthCheckResult:
        """Verificar endpoint HTTP"""
        start_time = time.time()
        
        try:
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status == expected_status:
                    message = f"HTTP {response.status} - {name} está saludable"
                    status = HealthStatus.HEALTHY
                else:
                    message = f"HTTP {response.status} - Estado inesperado en {name}"
                    status = HealthStatus.WARNING
                
                details = {
                    "status_code": response.status,
                    "url": str(response.url),
                    "headers": dict(response.headers)
                }
                
                return HealthCheckResult(
                    component=name,
                    status=status,
                    response_time=response_time,
                    message=message,
                    details=details
                )
                
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.CRITICAL,
                response_time=timeout,
                message=f"Timeout - {name} no respondió en {timeout}s",
                details={"timeout": timeout}
            )
        except Exception as e:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                message=f"Error - {name}: {str(e)}",
                details={"error": str(e)}
            )

    async def check_tcp_port(self, name: str, host: str, port: int) -> HealthCheckResult:
        """Verificar puerto TCP"""
        start_time = time.time()
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=10
            )
            writer.close()
            await writer.wait_closed()
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                component=name,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message=f"Puerto TCP {port} en {host} está accesible",
                details={"host": host, "port": port}
            )
            
        except asyncio.TimeoutError:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.CRITICAL,
                response_time=10,
                message=f"Timeout - Puerto TCP {port} en {host} no accesible",
                details={"host": host, "port": port}
            )
        except Exception as e:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                message=f"Error - Puerto TCP {port} en {host}: {str(e)}",
                details={"error": str(e), "host": host, "port": port}
            )

    async def check_redis(self, name: str, host: str = "localhost", port: int = 6379) -> HealthCheckResult:
        """Verificar conexión Redis"""
        start_time = time.time()
        
        try:
            r = redis.Redis(host=host, port=port, socket_connect_timeout=5)
            r.ping()
            response_time = time.time() - start_time
            
            info = r.info()
            
            return HealthCheckResult(
                component=name,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message=f"Redis en {host}:{port} está accesible",
                details={
                    "redis_version": info.get("redis_version"),
                    "used_memory": info.get("used_memory"),
                    "connected_clients": info.get("connected_clients")
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                message=f"Error - Redis {host}:{port}: {str(e)}",
                details={"error": str(e)}
            )

    async def check_postgresql(self, name: str, host: str = "localhost", 
                             port: int = 5432, database: str = "ai_news",
                             user: str = "postgres", password: str = "password") -> HealthCheckResult:
        """Verificar conexión PostgreSQL"""
        start_time = time.time()
        
        try:
            conn = psycopg2.connect(
                host=host, port=port, database=database,
                user=user, password=password, connect_timeout=5
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            
            response_time = time.time() - start_time
            
            return HealthCheckResult(
                component=name,
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message=f"PostgreSQL en {host}:{port} está accesible",
                details={
                    "host": host,
                    "port": port,
                    "database": database
                }
            )
            
        except Exception as e:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.CRITICAL,
                response_time=time.time() - start_time,
                message=f"Error - PostgreSQL {host}:{port}: {str(e)}",
                details={"error": str(e)}
            )

    async def check_docker_container(self, name: str, container_name: str) -> HealthCheckResult:
        """Verificar estado de contenedor Docker"""
        try:
            result = subprocess.run(
                ["docker", "inspect", "--format={{.State.Health.Status}}", container_name],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                health_status = result.stdout.strip()
                
                if health_status == "healthy":
                    status = HealthStatus.HEALTHY
                    message = f"Contenedor {container_name} está saludable"
                elif health_status == "unhealthy":
                    status = HealthStatus.CRITICAL
                    message = f"Contenedor {container_name} no es saludable"
                else:
                    status = HealthStatus.WARNING
                    message = f"Contenedor {container_name} tiene estado: {health_status}"
                
                return HealthCheckResult(
                    component=name,
                    status=status,
                    message=message,
                    details={"container": container_name, "health": health_status}
                )
            else:
                return HealthCheckResult(
                    component=name,
                    status=HealthStatus.UNKNOWN,
                    message=f"Contenedor {container_name} no encontrado",
                    details={"error": result.stderr}
                )
                
        except Exception as e:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.UNKNOWN,
                message=f"Error verificando contenedor {container_name}: {str(e)}",
                details={"error": str(e)}
            )

    async def check_process(self, name: str, process_name: str) -> HealthCheckResult:
        """Verificar si un proceso está corriendo"""
        try:
            result = subprocess.run(
                ["pgrep", "-f", process_name],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                return HealthCheckResult(
                    component=name,
                    status=HealthStatus.HEALTHY,
                    message=f"Proceso {process_name} está corriendo",
                    details={"process": process_name, "pids": result.stdout.strip().split()}
                )
            else:
                return HealthCheckResult(
                    component=name,
                    status=HealthStatus.CRITICAL,
                    message=f"Proceso {process_name} no está corriendo",
                    details={"process": process_name}
                )
                
        except Exception as e:
            return HealthCheckResult(
                component=name,
                status=HealthStatus.UNKNOWN,
                message=f"Error verificando proceso {process_name}: {str(e)}",
                details={"error": str(e)}
            )

    async def run_all_checks(self) -> List[HealthCheckResult]:
        """Ejecutar todas las verificaciones de salud"""
        logger.info("Iniciando verificaciones de salud completas...")
        
        checks = [
            # Backend API
            self.check_http_endpoint("Backend Health", "http://backend:8000/health"),
            self.check_http_endpoint("Backend API", "http://backend:8000/api/v1/health"),
            self.check_http_endpoint("Backend Metrics", "http://backend:8000/metrics"),
            
            # Frontend
            self.check_http_endpoint("Frontend", "http://frontend:3000"),
            
            # Database
            self.check_postgresql("PostgreSQL", "postgres", 5432, "ai_news"),
            
            # Cache
            self.check_redis("Redis", "redis", 6379),
            
            # Monitoring Services
            self.check_http_endpoint("Prometheus", "http://prometheus:9090/-/healthy"),
            self.check_http_endpoint("Grafana", "http://grafana:3000/api/health"),
            self.check_http_endpoint("AlertManager", "http://alertmanager:9093/-/healthy"),
            
            # Infrastructure
            self.check_http_endpoint("cAdvisor", "http://cadvisor:8080/healthz"),
            self.check_tcp_port("Node Exporter", "node-exporter", 9100),
            
            # Elasticsearch
            self.check_http_endpoint("Elasticsearch", "http://elasticsearch:9200/_cluster/health"),
            self.check_http_endpoint("Kibana", "http://kibana:5601/api/status"),
            
            # Uptime Kuma
            self.check_http_endpoint("Uptime Kuma", "http://uptime-kuma:3001/api/heartbeat"),
            
            # Docker containers
            self.check_docker_container("Backend Container", "ai-news-aggregator-backend-1"),
            self.check_docker_container("Frontend Container", "ai-news-aggregator-frontend-1"),
            
            # Processes
            self.check_process("Celery Worker", "celery"),
            self.check_process("Gunicorn", "gunicorn"),
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        # Manejar excepciones
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Error en health check: {result}")
                self.results.append(HealthCheckResult(
                    component="Unknown",
                    status=HealthStatus.UNKNOWN,
                    message=f"Error en verificación: {str(result)}",
                    details={"error": str(result)}
                ))
            else:
                self.results.append(result)
        
        return self.results

    def generate_report(self) -> Dict[str, Any]:
        """Generar reporte de salud"""
        healthy = sum(1 for r in self.results if r.status == HealthStatus.HEALTHY)
        warning = sum(1 for r in self.results if r.status == HealthStatus.WARNING)
        critical = sum(1 for r in self.results if r.status == HealthStatus.CRITICAL)
        unknown = sum(1 for r in self.results if r.status == HealthStatus.UNKNOWN)
        
        total = len(self.results)
        overall_status = HealthStatus.HEALTHY
        
        if critical > 0:
            overall_status = HealthStatus.CRITICAL
        elif warning > 0:
            overall_status = HealthStatus.WARNING
        elif unknown == total:
            overall_status = HealthStatus.UNKNOWN
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": overall_status.value,
            "summary": {
                "total": total,
                "healthy": healthy,
                "warning": warning,
                "critical": critical,
                "unknown": unknown
            },
            "checks": [asdict(result) for result in self.results]
        }
        
        return report

    async def save_report(self, filename: str = "health_report.json"):
        """Guardar reporte en archivo"""
        report = self.generate_report()
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Reporte guardado en {filename}")

    def log_summary(self):
        """Log resumen de verificaciones"""
        healthy = sum(1 for r in self.results if r.status == HealthStatus.HEALTHY)
        warning = sum(1 for r in self.results if r.status == HealthStatus.WARNING)
        critical = sum(1 for r in self.results if r.status == HealthStatus.CRITICAL)
        unknown = sum(1 for r in self.results if r.status == HealthStatus.UNKNOWN)
        
        logger.info(f"Health Check Summary: {healthy} healthy, {warning} warning, {critical} critical, {unknown} unknown")
        
        # Log detalles de problemas
        for result in self.results:
            if result.status in [HealthStatus.WARNING, HealthStatus.CRITICAL]:
                logger.warning(f"{result.status.value.upper()}: {result.component} - {result.message}")

async def main():
    """Función principal"""
    async with HealthChecker() as checker:
        results = await checker.run_all_checks()
        checker.log_summary()
        await checker.save_report("/var/log/health_checks_report.json")
        
        # Devolver código de salida basado en resultados
        critical_count = sum(1 for r in results if r.status == HealthStatus.CRITICAL)
        return 1 if critical_count > 0 else 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)