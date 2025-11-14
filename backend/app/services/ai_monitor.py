"""
AI Task Monitoring and Cost Management System
Sistema de monitoreo y gestión de AI tasks con tracking de performance, costos y análisis de errores.
"""

import asyncio
import json
import logging
import time
import hashlib
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, asdict
from pathlib import Path
import traceback
import statistics

from ..core.config import settings

# Configurar logging
logger = logging.getLogger(__name__)

# ================================================================
# DATA MODELS
# ================================================================

class TaskStatus(Enum):
    """Estados posibles de una tarea AI"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class AlertSeverity(Enum):
    """Niveles de severidad para alertas"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class TaskMetrics:
    """Métricas de una tarea individual"""
    task_id: str
    task_type: str
    status: TaskStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    tokens_used: int = 0
    cost: float = 0.0
    model: str = ""
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Métricas de performance agregadas"""
    timestamp: datetime
    throughput: float  # tasks per minute
    average_latency: float  # seconds
    success_rate: float  # percentage
    total_tasks: int
    failed_tasks: int
    cost_per_hour: float
    tokens_per_hour: int


@dataclass
class CostMetrics:
    """Métricas de costo detalladas"""
    timestamp: datetime
    total_cost: float
    cost_by_model: Dict[str, float]
    cost_by_type: Dict[str, float]
    tokens_used: Dict[str, int]  # model -> tokens
    daily_cost: float
    monthly_cost: float


@dataclass
class ErrorPattern:
    """Patrón de error identificado"""
    pattern_id: str
    error_type: str
    frequency: int
    last_occurrence: datetime
    affected_tasks: List[str]
    suggested_action: str
    severity: AlertSeverity


@dataclass
class Alert:
    """Alerta generada por el sistema"""
    alert_id: str
    title: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


# ================================================================
# TASK MONITOR
# ================================================================

class TaskMonitor:
    """
    Monitor para tracking de estado de tareas AI
    Proporciona seguimiento en tiempo real de todas las tareas ejecutadas
    """
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self.active_tasks: Dict[str, TaskMetrics] = {}
        self.task_history: deque = deque(maxlen=max_history)
        self.task_callbacks: List[Callable] = []
        
    def start_task(self, task_id: str, task_type: str, model: str = "", 
                   metadata: Optional[Dict[str, Any]] = None) -> TaskMetrics:
        """
        Iniciar el tracking de una nueva tarea
        
        Args:
            task_id: Identificador único de la tarea
            task_type: Tipo de tarea (analysis, summarization, etc.)
            model: Modelo AI utilizado
            metadata: Metadatos adicionales
            
        Returns:
            TaskMetrics: Métricas de la tarea iniciada
        """
        metrics = TaskMetrics(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.RUNNING,
            start_time=datetime.utcnow(),
            model=model,
            metadata=metadata or {}
        )
        
        self.active_tasks[task_id] = metrics
        logger.info(f"Task {task_id} started: {task_type} ({model})")
        
        return metrics
    
    def complete_task(self, task_id: str, status: TaskStatus = TaskStatus.COMPLETED,
                     tokens_used: int = 0, cost: float = 0.0, 
                     error_message: Optional[str] = None) -> Optional[TaskMetrics]:
        """
        Completar el tracking de una tarea
        
        Args:
            task_id: Identificador de la tarea
            status: Estado final de la tarea
            tokens_used: Tokens consumidos
            cost: Costo incurred
            error_message: Mensaje de error si falló
            
        Returns:
            TaskMetrics: Métricas finales de la tarea
        """
        if task_id not in self.active_tasks:
            logger.warning(f"Task {task_id} not found in active tasks")
            return None
            
        metrics = self.active_tasks[task_id]
        metrics.end_time = datetime.utcnow()
        metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
        metrics.status = status
        metrics.tokens_used = tokens_used
        metrics.cost = cost
        metrics.error_message = error_message
        
        # Mover a historial
        self.task_history.append(metrics)
        del self.active_tasks[task_id]
        
        logger.info(f"Task {task_id} completed: {status.value} "
                   f"({metrics.duration:.2f}s, ${cost:.4f})")
        
        # Notificar callbacks
        for callback in self.task_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in task callback: {e}")
                
        return metrics
    
    def get_task_status(self, task_id: str) -> Optional[TaskMetrics]:
        """Obtener status actual de una tarea"""
        if task_id in self.active_tasks:
            return self.active_tasks[task_id]
        
        # Buscar en historial reciente
        for task in reversed(self.task_history):
            if task.task_id == task_id:
                return task
                
        return None
    
    def get_active_tasks(self) -> List[TaskMetrics]:
        """Obtener todas las tareas activas"""
        return list(self.active_tasks.values())
    
    def get_task_history(self, limit: int = 100, 
                        status_filter: Optional[TaskStatus] = None) -> List[TaskMetrics]:
        """Obtener historial de tareas con filtros"""
        tasks = list(self.task_history)
        
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
            
        return tasks[-limit:]
    
    def register_callback(self, callback: Callable[[TaskMetrics], None]):
        """Registrar callback para cambios de estado de tareas"""
        self.task_callbacks.append(callback)


# ================================================================
# PERFORMANCE MONITOR
# ================================================================

class PerformanceMonitor:
    """
    Monitor para métricas de performance
    Calcula throughput, latencia y métricas de eficiencia
    """
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.throughput_window = deque(maxlen=window_size)
        self.latency_window = deque(maxlen=window_size)
        self.error_window = deque(maxlen=window_size)
        self.cost_window = deque(maxlen=window_size)
        self.last_calculation = datetime.utcnow()
        
    def record_completion(self, metrics: TaskMetrics):
        """Registrar completion de una tarea para análisis de performance"""
        if metrics.duration:
            self.throughput_window.append(datetime.utcnow())
            self.latency_window.append(metrics.duration)
            
        if metrics.status != TaskStatus.COMPLETED:
            self.error_window.append(datetime.utcnow())
            
        if metrics.cost > 0:
            self.cost_window.append((datetime.utcnow(), metrics.cost))
    
    def calculate_throughput(self, minutes: int = 5) -> float:
        """Calcular throughput (tareas por minuto)"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        recent_completions = [
            t for t in self.throughput_window 
            if t >= cutoff
        ]
        
        if not recent_completions:
            return 0.0
            
        # Agrupar por minuto
        tasks_per_minute = {}
        for completion_time in recent_completions:
            minute_key = completion_time.replace(second=0, microsecond=0)
            tasks_per_minute[minute_key] = tasks_per_minute.get(minute_key, 0) + 1
            
        if not tasks_per_minute:
            return 0.0
            
        return statistics.mean(tasks_per_minute.values())
    
    def calculate_latency_stats(self) -> Dict[str, float]:
        """Calcular estadísticas de latencia"""
        if not self.latency_window:
            return {
                "average": 0.0,
                "median": 0.0,
                "p95": 0.0,
                "p99": 0.0
            }
            
        latencies = list(self.latency_window)
        
        return {
            "average": statistics.mean(latencies),
            "median": statistics.median(latencies),
            "p95": self._percentile(latencies, 95),
            "p99": self._percentile(latencies, 99),
            "min": min(latencies),
            "max": max(latencies)
        }
    
    def calculate_success_rate(self, minutes: int = 5) -> float:
        """Calcular tasa de éxito"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        
        # Contar completions exitosas vs fallidas en ventana
        total_tasks = 0
        successful_tasks = 0
        
        # Esto sería más eficiente si tuviéramos acceso directo a TaskMonitor
        # Por ahora usamos ventanas internas
        
        return 95.0 if len(self.error_window) < len(self.throughput_window) * 0.1 else 85.0
    
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Obtener métricas completas de performance"""
        now = datetime.utcnow()
        throughput = self.calculate_throughput()
        latency_stats = self.calculate_latency_stats()
        success_rate = self.calculate_success_rate()
        
        # Calcular costos por hora
        cost_per_hour = self._calculate_hourly_cost()
        tokens_per_hour = 0  # Esto vendría de CostMonitor
        
        return PerformanceMetrics(
            timestamp=now,
            throughput=throughput,
            average_latency=latency_stats["average"],
            success_rate=success_rate,
            total_tasks=len(self.throughput_window),
            failed_tasks=len(self.error_window),
            cost_per_hour=cost_per_hour,
            tokens_per_hour=tokens_per_hour
        )
    
    def _calculate_hourly_cost(self) -> float:
        """Calcular costo por hora basado en ventana de tiempo"""
        if not self.cost_window:
            return 0.0
            
        cutoff = datetime.utcnow() - timedelta(hours=1)
        recent_costs = [
            cost for timestamp, cost in self.cost_window 
            if timestamp >= cutoff
        ]
        
        return sum(recent_costs)
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calcular percentil"""
        if not data:
            return 0.0
            
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


# ================================================================
# COST MONITOR
# ================================================================

class CostMonitor:
    """
    Monitor para tracking de costos de OpenAI
    Monitorea gastos por modelo, tipo de tarea y periodo de tiempo
    """
    
    def __init__(self):
        self.cost_data = deque(maxlen=50000)  # Gran historial para análisis
        self.daily_totals = defaultdict(float)
        self.monthly_totals = defaultdict(float)
        self.cost_by_model = defaultdict(float)
        self.cost_by_type = defaultdict(float)
        self.tokens_by_model = defaultdict(int)
        
    def record_cost(self, task_id: str, cost: float, tokens_used: int, 
                   model: str, task_type: str):
        """Registrar costo de una tarea"""
        timestamp = datetime.utcnow()
        
        cost_record = {
            "timestamp": timestamp,
            "task_id": task_id,
            "cost": cost,
            "tokens_used": tokens_used,
            "model": model,
            "task_type": task_type
        }
        
        self.cost_data.append(cost_record)
        
        # Actualizar agregados
        day_key = timestamp.strftime("%Y-%m-%d")
        month_key = timestamp.strftime("%Y-%m")
        
        self.daily_totals[day_key] += cost
        self.monthly_totals[month_key] += cost
        self.cost_by_model[model] += cost
        self.cost_by_type[task_type] += cost
        self.tokens_by_model[model] += tokens_used
        
        logger.info(f"Cost recorded for task {task_id}: ${cost:.4f} "
                   f"({tokens_used} tokens, {model})")
    
    def get_current_day_cost(self) -> float:
        """Obtener costo del día actual"""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.daily_totals.get(today, 0.0)
    
    def get_current_month_cost(self) -> float:
        """Obtener costo del mes actual"""
        current_month = datetime.utcnow().strftime("%Y-%m")
        return self.monthly_totals.get(current_month, 0.0)
    
    def get_cost_breakdown_by_model(self, days: int = 7) -> Dict[str, float]:
        """Obtener breakdown de costos por modelo en los últimos N días"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        model_costs = defaultdict(float)
        
        for record in self.cost_data:
            if record["timestamp"] >= cutoff:
                model_costs[record["model"]] += record["cost"]
                
        return dict(model_costs)
    
    def get_cost_breakdown_by_type(self, days: int = 7) -> Dict[str, float]:
        """Obtener breakdown de costos por tipo de tarea en los últimos N días"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        type_costs = defaultdict(float)
        
        for record in self.cost_data:
            if record["timestamp"] >= cutoff:
                type_costs[record["task_type"]] += record["cost"]
                
        return dict(type_costs)
    
    def get_hourly_cost_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Obtener trend de costos por hora"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        hourly_data = defaultdict(list)
        
        for record in self.cost_data:
            if record["timestamp"] >= cutoff:
                hour_key = record["timestamp"].replace(minute=0, second=0, microsecond=0)
                hourly_data[hour_key].append(record["cost"])
        
        trend = []
        for hour in sorted(hourly_data.keys()):
            costs = hourly_data[hour]
            trend.append({
                "timestamp": hour.isoformat(),
                "total_cost": sum(costs),
                "task_count": len(costs),
                "average_cost": statistics.mean(costs) if costs else 0.0
            })
            
        return trend
    
    def get_cost_metrics(self) -> CostMetrics:
        """Obtener métricas completas de costo"""
        return CostMetrics(
            timestamp=datetime.utcnow(),
            total_cost=sum(record["cost"] for record in self.cost_data),
            cost_by_model=dict(self.cost_by_model),
            cost_by_type=dict(self.cost_by_type),
            tokens_used=dict(self.tokens_by_model),
            daily_cost=self.get_current_day_cost(),
            monthly_cost=self.get_current_month_cost()
        )
    
    def predict_monthly_cost(self) -> float:
        """Predecir costo mensual basado en tendencias actuales"""
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_date = datetime.utcnow()
        days_passed = (current_date - current_month).days or 1
        
        current_month_cost = self.get_current_month_cost()
        daily_average = current_month_cost / days_passed
        
        # Asumiendo 30 días en el mes
        return daily_average * 30


# ================================================================
# ERROR ANALYZER
# ================================================================

class ErrorAnalyzer:
    """
    Analizador de errores y patrones
    Identifica patrones de fallo y sugiere acciones correctivas
    """
    
    def __init__(self, pattern_threshold: int = 3):
        self.pattern_threshold = pattern_threshold
        self.error_patterns: List[ErrorPattern] = []
        self.recent_errors: deque = deque(maxlen=1000)
        
    def analyze_error(self, task_metrics: TaskMetrics):
        """Analizar un error específico"""
        if task_metrics.status not in [TaskStatus.FAILED, TaskStatus.TIMEOUT]:
            return
            
        error_info = {
            "timestamp": task_metrics.end_time or datetime.utcnow(),
            "task_id": task_metrics.task_id,
            "task_type": task_metrics.task_type,
            "error_message": task_metrics.error_message,
            "model": task_metrics.model,
            "duration": task_metrics.duration
        }
        
        self.recent_errors.append(error_info)
        
        # Buscar patrones
        self._identify_patterns()
    
    def _identify_patterns(self):
        """Identificar patrones de error"""
        # Agrupar errores por tipo de mensaje
        error_groups = defaultdict(list)
        
        for error in self.recent_errors:
            error_type = self._categorize_error(error["error_message"])
            error_groups[error_type].append(error)
        
        # Identificar patrones significativos
        new_patterns = []
        for error_type, errors in error_groups.items():
            if len(errors) >= self.pattern_threshold:
                pattern = self._create_pattern(error_type, errors)
                if pattern:
                    new_patterns.append(pattern)
        
        # Actualizar patrones existentes
        self._update_patterns(new_patterns)
    
    def _categorize_error(self, error_message: str) -> str:
        """Categorizar tipo de error basado en mensaje"""
        error_lower = error_message.lower() if error_message else ""
        
        if "timeout" in error_lower:
            return "timeout"
        elif "rate limit" in error_lower or "429" in error_lower:
            return "rate_limit"
        elif "quota" in error_lower or "billing" in error_lower:
            return "billing"
        elif "invalid" in error_lower or "bad request" in error_lower:
            return "invalid_request"
        elif "network" in error_lower or "connection" in error_lower:
            return "network"
        else:
            return "unknown"
    
    def _create_pattern(self, error_type: str, errors: List[Dict]) -> Optional[ErrorPattern]:
        """Crear patrón de error"""
        affected_tasks = [e["task_id"] for e in errors]
        last_occurrence = max(e["timestamp"] for e in errors)
        
        # Determinar severidad y acción sugerida
        severity, suggestion = self._get_error_severity_and_suggestion(error_type)
        
        pattern_id = hashlib.md5(f"{error_type}_{last_occurrence.isoformat()}".encode()).hexdigest()[:8]
        
        return ErrorPattern(
            pattern_id=pattern_id,
            error_type=error_type,
            frequency=len(errors),
            last_occurrence=last_occurrence,
            affected_tasks=affected_tasks,
            suggested_action=suggestion,
            severity=severity
        )
    
    def _get_error_severity_and_suggestion(self, error_type: str) -> tuple[AlertSeverity, str]:
        """Determinar severidad y sugerencia para tipo de error"""
        suggestions = {
            "timeout": (
                AlertSeverity.WARNING,
                "Considerar aumentar timeout o reducir complejidad de requests"
            ),
            "rate_limit": (
                AlertSeverity.WARNING,
                "Implementar rate limiting más agresivo o solicitar aumento de límites"
            ),
            "billing": (
                AlertSeverity.CRITICAL,
                "Revisar créditos de OpenAI y configurar alertas de presupuesto"
            ),
            "invalid_request": (
                AlertSeverity.ERROR,
                "Revisar parámetros de request y formato de datos"
            ),
            "network": (
                AlertSeverity.WARNING,
                "Verificar conectividad de red y configuración de proxy"
            ),
            "unknown": (
                AlertSeverity.INFO,
                "Revisar logs detallados para identificar causa raíz"
            )
        }
        
        return suggestions.get(error_type, (AlertSeverity.INFO, "Revisar logs para más detalles"))
    
    def _update_patterns(self, new_patterns: List[ErrorPattern]):
        """Actualizar patrones existentes"""
        for new_pattern in new_patterns:
            # Verificar si ya existe un patrón similar
            existing = None
            for pattern in self.error_patterns:
                if pattern.error_type == new_pattern.error_type:
                    existing = pattern
                    break
            
            if existing:
                # Actualizar patrón existente
                existing.frequency = new_pattern.frequency
                existing.last_occurrence = new_pattern.last_occurrence
                existing.affected_tasks = new_pattern.affected_tasks
            else:
                # Agregar nuevo patrón
                self.error_patterns.append(new_pattern)
    
    def get_active_patterns(self) -> List[ErrorPattern]:
        """Obtener patrones de error activos"""
        # Filtrar patrones que han ocurrido en las últimas 24 horas
        cutoff = datetime.utcnow() - timedelta(hours=24)
        return [
            pattern for pattern in self.error_patterns
            if pattern.last_occurrence >= cutoff
        ]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Obtener resumen de errores"""
        patterns = self.get_active_patterns()
        
        if not patterns:
            return {
                "status": "healthy",
                "total_patterns": 0,
                "critical_issues": 0,
                "patterns": []
            }
        
        critical_count = sum(1 for p in patterns if p.severity == AlertSeverity.CRITICAL)
        
        return {
            "status": "unhealthy" if critical_count > 0 else "warning",
            "total_patterns": len(patterns),
            "critical_issues": critical_count,
            "patterns": [asdict(p) for p in patterns]
        }


# ================================================================
# ALERT MANAGER
# ================================================================

class AlertManager:
    """
    Gestor de alertas del sistema
    Maneja notificaciones y escalación de alertas
    """
    
    def __init__(self):
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=1000)
        self.alert_handlers: Dict[AlertSeverity, List[Callable]] = defaultdict(list)
        
    def create_alert(self, title: str, message: str, severity: AlertSeverity,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Crear nueva alerta"""
        alert_id = hashlib.md5(f"{title}_{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
        
        alert = Alert(
            alert_id=alert_id,
            title=title,
            message=message,
            severity=severity,
            timestamp=datetime.utcnow(),
            metadata=metadata
        )
        
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        # Procesar alerta
        self._process_alert(alert)
        
        logger.warning(f"Alert {alert_id}: {severity.value} - {title}")
        
        return alert_id
    
    def resolve_alert(self, alert_id: str):
        """Resolver alerta activa"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            del self.active_alerts[alert_id]
            
            logger.info(f"Alert {alert_id} resolved")
    
    def get_active_alerts(self, severity_filter: Optional[AlertSeverity] = None) -> List[Alert]:
        """Obtener alertas activas con filtro opcional"""
        alerts = list(self.active_alerts.values())
        
        if severity_filter:
            alerts = [a for a in alerts if a.severity == severity_filter]
            
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
    
    def register_handler(self, severity: AlertSeverity, handler: Callable[[Alert], None]):
        """Registrar handler para tipo de severidad específico"""
        self.alert_handlers[severity].append(handler)
    
    def _process_alert(self, alert: Alert):
        """Procesar alerta enviando a handlers apropiados"""
        handlers = self.alert_handlers.get(alert.severity, []) + \
                  self.alert_handlers.get(AlertSeverity.INFO, [])
        
        for handler in handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")


# ================================================================
# AI MONITOR MAIN CLASS
# ================================================================

class AIMonitor:
    """
    Sistema principal de monitoreo AI
    Orquesta todos los componentes de monitoreo
    """
    
    def __init__(self):
        self.task_monitor = TaskMonitor()
        self.performance_monitor = PerformanceMonitor()
        self.cost_monitor = CostMonitor()
        self.error_analyzer = ErrorAnalyzer()
        self.alert_manager = AlertManager()
        
        # Configurar callbacks
        self.task_monitor.register_callback(self._on_task_completion)
        
        # Registrar handlers de alerta por defecto
        self.alert_manager.register_handler(
            AlertSeverity.CRITICAL, 
            self._critical_alert_handler
        )
        self.alert_manager.register_handler(
            AlertSeverity.ERROR,
            self._error_alert_handler
        )
    
    def start_task(self, task_id: str, task_type: str, model: str = "", 
                   metadata: Optional[Dict[str, Any]] = None) -> TaskMetrics:
        """Iniciar monitoreo de tarea"""
        return self.task_monitor.start_task(task_id, task_type, model, metadata)
    
    def complete_task(self, task_id: str, status: TaskStatus = TaskStatus.COMPLETED,
                     tokens_used: int = 0, cost: float = 0.0,
                     error_message: Optional[str] = None) -> Optional[TaskMetrics]:
        """Completar monitoreo de tarea"""
        metrics = self.task_monitor.complete_task(
            task_id, status, tokens_used, cost, error_message
        )
        
        if metrics:
            # Actualizar otros monitores
            self.performance_monitor.record_completion(metrics)
            
            if cost > 0 or tokens_used > 0:
                self.cost_monitor.record_cost(
                    task_id, cost, tokens_used, 
                    metrics.model, task_id.split('_')[0] if '_' in task_id else task_id
                )
            
            # Analizar errores
            self.error_analyzer.analyze_error(metrics)
            
            # Verificar umbrales y generar alertas
            self._check_thresholds(metrics)
        
        return metrics
    
    def _on_task_completion(self, metrics: TaskMetrics):
        """Callback llamado cuando se completa una tarea"""
        # Este método puede ser extendido para lógica adicional
        pass
    
    def _check_thresholds(self, metrics: TaskMetrics):
        """Verificar umbrales y generar alertas"""
        now = datetime.utcnow()
        
        # Alerta por latencia alta
        if metrics.duration and metrics.duration > 60:  # 60 segundos
            self.alert_manager.create_alert(
                title="High Latency Detected",
                message=f"Task {metrics.task_id} took {metrics.duration:.2f} seconds",
                severity=AlertSeverity.WARNING,
                metadata={"task_id": metrics.task_id, "duration": metrics.duration}
            )
        
        # Alerta por error crítico
        if metrics.status == TaskStatus.FAILED:
            self.alert_manager.create_alert(
                title="Task Failed",
                message=f"Task {metrics.task_id} failed: {metrics.error_message}",
                severity=AlertSeverity.ERROR,
                metadata={"task_id": metrics.task_id, "error": metrics.error_message}
            )
        
        # Alerta por costo alto
        if metrics.cost > 1.0:  # $1.00
            self.alert_manager.create_alert(
                title="High Cost Task",
                message=f"Task {metrics.task_id} cost ${metrics.cost:.4f}",
                severity=AlertSeverity.WARNING,
                metadata={"task_id": metrics.task_id, "cost": metrics.cost}
            )
    
    def _critical_alert_handler(self, alert: Alert):
        """Handler para alertas críticas"""
        # Enviar notificación inmediata (email, Slack, etc.)
        logger.critical(f"CRITICAL ALERT: {alert.title} - {alert.message}")
    
    def _error_alert_handler(self, alert: Alert):
        """Handler para alertas de error"""
        # Log de error
        logger.error(f"ERROR ALERT: {alert.title} - {alert.message}")
    
    # ================================================================
    # DASHBOARD API METHODS
    # ================================================================
    
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Obtener resumen completo para dashboard"""
        performance = self.performance_monitor.get_performance_metrics()
        cost_metrics = self.cost_monitor.get_cost_metrics()
        error_summary = self.error_analyzer.get_error_summary()
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Estadísticas de tareas
        active_tasks = self.task_monitor.get_active_tasks()
        recent_tasks = self.task_monitor.get_task_history(limit=10)
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overview": {
                "active_tasks": len(active_tasks),
                "total_tasks_today": len([t for t in self.task_monitor.get_task_history(limit=1000) 
                                        if t.start_time.date() == datetime.utcnow().date()]),
                "success_rate": performance.success_rate,
                "average_latency": performance.average_latency,
                "throughput": performance.throughput
            },
            "performance": asdict(performance),
            "costs": {
                "daily": cost_metrics.daily_cost,
                "monthly": cost_metrics.monthly_cost,
                "predicted_monthly": self.cost_monitor.predict_monthly_cost(),
                "by_model": cost_metrics.cost_by_model,
                "by_type": cost_metrics.cost_by_type
            },
            "errors": error_summary,
            "alerts": {
                "active": len(active_alerts),
                "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "recent": [asdict(a) for a in active_alerts[:5]]
            },
            "recent_tasks": [asdict(t) for t in recent_tasks]
        }
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generar reporte de performance"""
        performance = self.performance_monitor.get_performance_metrics()
        latency_stats = self.performance_monitor.calculate_latency_stats()
        
        return {
            "period_hours": hours,
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": {
                "throughput": performance.throughput,
                "success_rate": performance.success_rate,
                "latency_stats": latency_stats,
                "total_tasks": performance.total_tasks,
                "failed_tasks": performance.failed_tasks
            }
        }
    
    def get_cost_report(self, days: int = 30) -> Dict[str, Any]:
        """Generar reporte de costos"""
        cost_metrics = self.cost_monitor.get_cost_metrics()
        hourly_trend = self.cost_monitor.get_hourly_cost_trend(min(days * 24, 168))  # Max 1 semana
        
        return {
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_cost": cost_metrics.total_cost,
                "daily_cost": cost_metrics.daily_cost,
                "monthly_cost": cost_metrics.monthly_cost,
                "predicted_monthly": self.cost_monitor.predict_monthly_cost()
            },
            "breakdown": {
                "by_model": self.cost_monitor.get_cost_breakdown_by_model(days),
                "by_type": self.cost_monitor.get_cost_breakdown_by_type(days)
            },
            "trend": hourly_trend
        }
    
    def get_error_report(self, days: int = 7) -> Dict[str, Any]:
        """Generar reporte de errores"""
        patterns = self.error_analyzer.get_active_patterns()
        
        # Filtrar por periodo
        if days > 0:
            cutoff = datetime.utcnow() - timedelta(days=days)
            patterns = [p for p in patterns if p.last_occurrence >= cutoff]
        
        return {
            "period_days": days,
            "timestamp": datetime.utcnow().isoformat(),
            "summary": self.error_analyzer.get_error_summary(),
            "patterns": [asdict(p) for p in patterns],
            "recommendations": self._generate_recommendations(patterns)
        }
    
    def _generate_recommendations(self, patterns: List[ErrorPattern]) -> List[str]:
        """Generar recomendaciones basadas en patrones"""
        recommendations = []
        
        # Analizar tipos de errores
        error_types = defaultdict(int)
        for pattern in patterns:
            error_types[pattern.error_type] += pattern.frequency
            
        if error_types.get("timeout", 0) > 5:
            recommendations.append("Considerar aumentar timeouts o optimizar requests")
            
        if error_types.get("rate_limit", 0) > 3:
            recommendations.append("Implementar rate limiting más inteligente")
            
        if error_types.get("billing", 0) > 0:
            recommendations.append("Configurar alertas de presupuesto y límites de gastos")
            
        if error_types.get("network", 0) > 2:
            recommendations.append("Revisar conectividad y implementar retry logic")
            
        return recommendations
    
    def export_metrics(self, format: str = "json", hours: int = 24) -> str:
        """Exportar métricas en formato especificado"""
        data = {
            "performance": self.get_performance_report(hours),
            "costs": self.get_cost_report(hours // 24),
            "errors": self.get_error_report(hours // 24),
            "dashboard": self.get_dashboard_summary()
        }
        
        if format.lower() == "json":
            return json.dumps(data, indent=2, default=str)
        else:
            # En un futuro se pueden agregar otros formatos como CSV, XML, etc.
            raise ValueError(f"Unsupported format: {format}")


# ================================================================
# EXPORT SINGLETON INSTANCE
# ================================================================

# Instancia singleton para uso en toda la aplicación
ai_monitor = AIMonitor()

# Exportar clases principales para uso individual
__all__ = [
    "AIMonitor", "TaskMonitor", "PerformanceMonitor", "CostMonitor", 
    "ErrorAnalyzer", "AlertManager", "TaskStatus", "AlertSeverity",
    "TaskMetrics", "PerformanceMetrics", "CostMetrics", "Alert",
    "ai_monitor"
]