"""
Dashboard API endpoints para AI Monitor
Endpoints para acceder a métricas, reportes y configuración del sistema de monitoreo
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from app.services.ai_monitor import ai_monitor, TaskStatus, AlertSeverity  # Fixed: was ...services

router = APIRouter()


# ================================================================
# DASHBOARD ENDPOINTS
# ================================================================

@router.get("/dashboard/summary")
async def get_dashboard_summary():
    """
    Obtener resumen completo del dashboard
    
    Returns:
        - Resumen de tareas activas
        - Métricas de performance
        - Estado de costos
        - Alertas activas
        - Tareas recientes
    """
    try:
        summary = ai_monitor.get_dashboard_summary()
        return {
            "status": "success",
            "data": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard summary: {str(e)}")


@router.get("/dashboard/performance")
async def get_performance_metrics(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back (max 168 = 1 week)")
):
    """
    Obtener métricas de performance
    
    - **hours**: Número de horas hacia atrás para analizar
    """
    try:
        report = ai_monitor.get_performance_report(hours)
        return {
            "status": "success",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")


@router.get("/dashboard/costs")
async def get_cost_metrics(
    days: int = Query(default=7, ge=1, le=30, description="Days to look back (max 30)")
):
    """
    Obtener métricas de costos
    
    - **days**: Número de días hacia atrás para analizar
    """
    try:
        report = ai_monitor.get_cost_report(days)
        return {
            "status": "success",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost metrics: {str(e)}")


@router.get("/dashboard/errors")
async def get_error_report(
    days: int = Query(default=7, ge=1, le=30, description="Days to look back (max 30)")
):
    """
    Obtener reporte de errores
    
    - **days**: Número de días hacia atrás para analizar
    """
    try:
        report = ai_monitor.get_error_report(days)
        return {
            "status": "success",
            "data": report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting error report: {str(e)}")


# ================================================================
# TASK MANAGEMENT ENDPOINTS
# ================================================================

@router.get("/tasks/active")
async def get_active_tasks():
    """
    Obtener todas las tareas activas actualmente
    """
    try:
        tasks = ai_monitor.task_monitor.get_active_tasks()
        return {
            "status": "success",
            "data": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active tasks: {str(e)}")


@router.get("/tasks/history")
async def get_task_history(
    limit: int = Query(default=100, ge=1, le=1000, description="Number of tasks to return"),
    status: Optional[TaskStatus] = Query(default=None, description="Filter by task status")
):
    """
    Obtener historial de tareas
    
    - **limit**: Número máximo de tareas a retornar
    - **status**: Filtrar por estado de tarea (opcional)
    """
    try:
        tasks = ai_monitor.task_monitor.get_task_history(limit=limit, status_filter=status)
        return {
            "status": "success",
            "data": tasks,
            "count": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task history: {str(e)}")


@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """
    Obtener status de una tarea específica
    
    - **task_id**: ID de la tarea a consultar
    """
    try:
        task = ai_monitor.task_monitor.get_task_status(task_id)
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
            
        return {
            "status": "success",
            "data": task
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting task status: {str(e)}")


# ================================================================
# ALERTS ENDPOINTS
# ================================================================

@router.get("/alerts/active")
async def get_active_alerts(
    severity: Optional[AlertSeverity] = Query(default=None, description="Filter by severity")
):
    """
    Obtener alertas activas
    
    - **severity**: Filtrar por severidad (opcional)
    """
    try:
        alerts = ai_monitor.alert_manager.get_active_alerts(severity_filter=severity)
        return {
            "status": "success",
            "data": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting active alerts: {str(e)}")


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """
    Resolver una alerta activa
    
    - **alert_id**: ID de la alerta a resolver
    """
    try:
        if alert_id not in ai_monitor.alert_manager.active_alerts:
            raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
            
        ai_monitor.alert_manager.resolve_alert(alert_id)
        
        return {
            "status": "success",
            "message": f"Alert {alert_id} resolved"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving alert: {str(e)}")


@router.get("/alerts/history")
async def get_alert_history(
    limit: int = Query(default=50, ge=1, le=200, description="Number of alerts to return")
):
    """
    Obtener historial de alertas
    
    - **limit**: Número máximo de alertas a retornar
    """
    try:
        # Obtener del historial de alertas
        alerts = list(ai_monitor.alert_manager.alert_history)[-limit:]
        return {
            "status": "success",
            "data": alerts,
            "count": len(alerts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alert history: {str(e)}")


# ================================================================
# REPORTING ENDPOINTS
# ================================================================

@router.get("/reports/export")
async def export_metrics(
    format: str = Query(default="json", regex="^(json|csv)$", description="Export format"),
    hours: int = Query(default=24, ge=1, le=168, description="Hours to include in report")
):
    """
    Exportar métricas en formato especificado
    
    - **format**: Formato de exportación (json, csv)
    - **hours**: Número de horas hacia atrás para incluir
    """
    try:
        export_data = ai_monitor.export_metrics(format=format, hours=hours)
        
        return {
            "status": "success",
            "data": export_data,
            "format": format,
            "period_hours": hours
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting metrics: {str(e)}")


@router.get("/reports/cost-forecast")
async def get_cost_forecast():
    """
    Obtener predicción de costos mensuales
    """
    try:
        current_month_cost = ai_monitor.cost_monitor.get_current_month_cost()
        predicted_cost = ai_monitor.cost_monitor.predict_monthly_cost()
        
        return {
            "status": "success",
            "data": {
                "current_month_cost": current_month_cost,
                "predicted_monthly_cost": predicted_cost,
                "daily_average": current_month_cost / max(datetime.utcnow().day, 1),
                "remaining_days": 30 - datetime.utcnow().day,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cost forecast: {str(e)}")


# ================================================================
# REAL-TIME MONITORING ENDPOINTS
# ================================================================

@router.get("/realtime/status")
async def get_realtime_status():
    """
    Obtener status en tiempo real del sistema
    """
    try:
        active_tasks = ai_monitor.task_monitor.get_active_tasks()
        performance = ai_monitor.performance_monitor.get_performance_metrics()
        active_alerts = ai_monitor.alert_manager.get_active_alerts()
        
        # Calcular métricas adicionales en tiempo real
        system_health = "healthy"
        if any(a.severity == AlertSeverity.CRITICAL for a in active_alerts):
            system_health = "critical"
        elif any(a.severity == AlertSeverity.ERROR for a in active_alerts):
            system_health = "degraded"
        elif len(active_alerts) > 0:
            system_health = "warning"
        
        return {
            "status": "success",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "system_health": system_health,
                "active_tasks": {
                    "count": len(active_tasks),
                    "running": len([t for t in active_tasks if t.status == TaskStatus.RUNNING]),
                    "pending": len([t for t in active_tasks if t.status == TaskStatus.PENDING])
                },
                "performance": {
                    "throughput": performance.throughput,
                    "average_latency": performance.average_latency,
                    "success_rate": performance.success_rate
                },
                "alerts": {
                    "active": len(active_alerts),
                    "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                    "errors": len([a for a in active_alerts if a.severity == AlertSeverity.ERROR])
                },
                "costs": {
                    "today": ai_monitor.cost_monitor.get_current_day_cost(),
                    "predicted_monthly": ai_monitor.cost_monitor.predict_monthly_cost()
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting realtime status: {str(e)}")


@router.get("/realtime/metrics")
async def get_realtime_metrics():
    """
    Obtener métricas detalladas en tiempo real
    """
    try:
        performance = ai_monitor.performance_monitor.get_performance_metrics()
        cost_metrics = ai_monitor.cost_monitor.get_cost_metrics()
        
        # Latencia detallada
        latency_stats = ai_monitor.performance_monitor.calculate_latency_stats()
        
        # Costos por hora (últimas 24 horas)
        hourly_trend = ai_monitor.cost_monitor.get_hourly_cost_trend(24)
        
        return {
            "status": "success",
            "data": {
                "timestamp": datetime.utcnow().isoformat(),
                "performance": {
                    "throughput": performance.throughput,
                    "latency_stats": latency_stats,
                    "success_rate": performance.success_rate,
                    "total_tasks": performance.total_tasks,
                    "failed_tasks": performance.failed_tasks
                },
                "costs": {
                    "hourly_trend": hourly_trend,
                    "by_model": cost_metrics.cost_by_model,
                    "by_type": cost_metrics.cost_by_type,
                    "tokens_usage": cost_metrics.tokens_used
                },
                "alerts": {
                    "active_count": len(ai_monitor.alert_manager.active_alerts),
                    "recent_errors": len([a for a in ai_monitor.alert_manager.active_alerts 
                                        if a.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL]])
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting realtime metrics: {str(e)}")


# ================================================================
# CONFIGURATION ENDPOINTS
# ================================================================

@router.get("/config/thresholds")
async def get_monitoring_thresholds():
    """
    Obtener configuración actual de umbrales de monitoreo
    """
    try:
        # Esta información podría ser configurable en base de datos
        # Por ahora retornamos valores estáticos
        return {
            "status": "success",
            "data": {
                "latency_warning": 30,  # seconds
                "latency_critical": 60,  # seconds
                "error_rate_warning": 10,  # percentage
                "error_rate_critical": 20,  # percentage
                "cost_task_warning": 0.5,  # dollars
                "cost_task_critical": 1.0,  # dollars
                "daily_cost_warning": 10.0,  # dollars
                "daily_cost_critical": 25.0,  # dollars
                "pattern_frequency_threshold": 3  # occurrences
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting thresholds: {str(e)}")


@router.get("/config/alerts")
async def get_alert_configuration():
    """
    Obtener configuración actual de alertas
    """
    try:
        # Información sobre handlers registrados
        handlers = {}
        for severity in AlertSeverity:
            handlers[severity.value] = len(ai_monitor.alert_manager.alert_handlers[severity])
        
        return {
            "status": "success",
            "data": {
                "alert_handlers": handlers,
                "active_alerts": len(ai_monitor.alert_manager.active_alerts),
                "alert_history_size": len(ai_monitor.alert_manager.alert_history),
                "max_history": ai_monitor.alert_manager.alert_history.maxlen
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting alert configuration: {str(e)}")


# ================================================================
# TESTING AND UTILITY ENDPOINTS
# ================================================================

@router.post("/test/generate-sample-task")
async def generate_sample_task(
    task_type: str = "test",
    duration: float = 5.0,
    should_fail: bool = False
):
    """
    Generar tarea de prueba para testing
    
    - **task_type**: Tipo de tarea de prueba
    - **duration**: Duración simulada en segundos
    - **should_fail**: Si la tarea debe fallar
    """
    try:
        import uuid
        
        task_id = f"test_{task_type}_{uuid.uuid4().hex[:8]}"
        model = "gpt-3.5-turbo"
        
        # Iniciar tarea
        ai_monitor.start_task(task_id, task_type, model, {"test": True})
        
        # Simular duración
        import asyncio
        await asyncio.sleep(min(duration, 10))  # Max 10 seconds for safety
        
        # Completar tarea
        if should_fail:
            ai_monitor.complete_task(
                task_id, 
                TaskStatus.FAILED, 
                error_message="Simulated test failure"
            )
        else:
            import random
            cost = random.uniform(0.001, 0.1)
            tokens = random.randint(100, 1000)
            ai_monitor.complete_task(task_id, TaskStatus.COMPLETED, tokens, cost)
        
        return {
            "status": "success",
            "message": f"Sample task {task_id} completed",
            "task_id": task_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample task: {str(e)}")


@router.post("/test/generate-sample-alert")
async def generate_sample_alert(
    severity: AlertSeverity = AlertSeverity.WARNING,
    title: str = "Test Alert"
):
    """
    Generar alerta de prueba
    
    - **severity**: Severidad de la alerta
    - **title**: Título de la alerta
    """
    try:
        alert_id = ai_monitor.alert_manager.create_alert(
            title=title,
            message="This is a test alert generated for testing purposes",
            severity=severity,
            metadata={"test": True}
        )
        
        return {
            "status": "success",
            "message": f"Sample alert {alert_id} created",
            "alert_id": alert_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating sample alert: {str(e)}")


@router.post("/test/reset-monitor")
async def reset_monitor():
    """
    Resetear todos los datos del monitor (solo para testing)
    """
    try:
        # Resetear monitores
        ai_monitor.task_monitor.active_tasks.clear()
        ai_monitor.task_monitor.task_history.clear()
        ai_monitor.task_monitor.task_callbacks.clear()
        
        ai_monitor.performance_monitor.throughput_window.clear()
        ai_monitor.performance_monitor.latency_window.clear()
        ai_monitor.performance_monitor.error_window.clear()
        ai_monitor.performance_monitor.cost_window.clear()
        
        ai_monitor.cost_monitor.cost_data.clear()
        ai_monitor.cost_monitor.daily_totals.clear()
        ai_monitor.cost_monitor.monthly_totals.clear()
        ai_monitor.cost_monitor.cost_by_model.clear()
        ai_monitor.cost_monitor.cost_by_type.clear()
        ai_monitor.cost_monitor.tokens_by_model.clear()
        
        ai_monitor.error_analyzer.error_patterns.clear()
        ai_monitor.error_analyzer.recent_errors.clear()
        
        ai_monitor.alert_manager.active_alerts.clear()
        ai_monitor.alert_manager.alert_history.clear()
        
        return {
            "status": "success",
            "message": "Monitor data reset successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting monitor: {str(e)}")
