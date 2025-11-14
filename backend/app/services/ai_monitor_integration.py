"""
AI Monitor Integration Utilities
Utilidades para integrar fácilmente el sistema de monitoreo con servicios existentes
"""

import asyncio
import functools
import time
import logging
from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime

from .ai_monitor import ai_monitor, TaskStatus, TaskMetrics

logger = logging.getLogger(__name__)


# ================================================================
# DECORATORS FOR AUTOMATIC MONITORING
# ================================================================

def monitor_ai_task(task_type: str, model: str = "", 
                   auto_cost_tracking: bool = True,
                   include_metadata: bool = True):
    """
    Decorator para monitorear automáticamente funciones de AI
    
    Args:
        task_type: Tipo de tarea para categorización
        model: Modelo de AI utilizado
        auto_cost_tracking: Si calcular costos automáticamente basado en tokens
        include_metadata: Si incluir metadata adicional
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generar task_id
            task_id = f"{task_type}_{int(time.time() * 1000)}"
            
            # Preparar metadata
            metadata = {}
            if include_metadata:
                metadata.update({
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys()),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Agregar args/kwargs relevantes (primeros valores)
            if include_metadata and args:
                metadata["first_arg_type"] = type(args[0]).__name__
                if hasattr(args[0], '__dict__'):
                    metadata["first_arg_keys"] = list(args[0].__dict__.keys())[:5]
            
            # Iniciar monitoreo
            task_metrics = ai_monitor.start_task(
                task_id=task_id,
                task_type=task_type,
                model=model,
                metadata=metadata
            )
            
            try:
                # Ejecutar función
                result = await func(*args, **kwargs)
                
                # Extraer métricas si están en el resultado
                tokens_used = 0
                cost = 0.0
                
                if auto_cost_tracking and hasattr(result, 'usage'):
                    # OpenAI response format
                    tokens_used = result.usage.total_tokens if result.usage else 0
                    if result.usage and hasattr(result.usage, 'prompt_tokens') and hasattr(result.usage, 'completion_tokens'):
                        # Calcular costo aproximado
                        cost = _calculate_openai_cost(
                            result.usage.prompt_tokens, 
                            result.usage.completion_tokens,
                            model
                        )
                
                # Completar monitoreo exitosamente
                ai_monitor.complete_task(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    tokens_used=tokens_used,
                    cost=cost
                )
                
                return result
                
            except Exception as e:
                # Completar monitoreo con error
                ai_monitor.complete_task(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error_message=str(e)
                )
                raise
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Versión síncrona
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            finally:
                loop.close()
        
        # Retornar wrapper apropiado
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def monitor_api_call(service_name: str, operation: str):
    """
    Decorator específico para monitoreo de llamadas API externas
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            task_id = f"api_{service_name}_{operation}_{int(time.time() * 1000)}"
            
            ai_monitor.start_task(
                task_id=task_id,
                task_type=f"api_{service_name}",
                model="external_api",
                metadata={
                    "operation": operation,
                    "service": service_name,
                    "function": func.__name__
                }
            )
            
            try:
                result = await func(*args, **kwargs)
                ai_monitor.complete_task(task_id, TaskStatus.COMPLETED)
                return result
            except Exception as e:
                ai_monitor.complete_task(
                    task_id, 
                    TaskStatus.FAILED, 
                    error_message=str(e)
                )
                raise
                
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(async_wrapper(*args, **kwargs))
            finally:
                loop.close()
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ================================================================
# COST CALCULATION UTILITIES
# ================================================================

def _calculate_openai_cost(prompt_tokens: int, completion_tokens: int, model: str) -> float:
    """
    Calcular costo aproximado de OpenAI API
    
    Precios basados en: https://openai.com/pricing
    """
    pricing = {
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},  # per 1K tokens
        "gpt-3.5-turbo-16k": {"prompt": 0.003, "completion": 0.004},
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-4-32k": {"prompt": 0.06, "completion": 0.12},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006}
    }
    
    model_pricing = pricing.get(model, pricing["gpt-3.5-turbo"])
    
    prompt_cost = (prompt_tokens / 1000) * model_pricing["prompt"]
    completion_cost = (completion_tokens / 1000) * model_pricing["completion"]
    
    return prompt_cost + completion_cost


def calculate_batch_cost(tokens_by_model: Dict[str, int], model: str) -> float:
    """
    Calcular costo para una lista de tokens
    """
    tokens = tokens_by_model.get(model, 0)
    
    # Estimación simplificada - en práctica esto vendría de la response real
    if "gpt-4" in model:
        cost_per_1k = 0.03  # promedio entre prompt y completion
    elif "gpt-3.5" in model:
        cost_per_1k = 0.002  # promedio
    else:
        cost_per_1k = 0.005  # default
    
    return (tokens / 1000) * cost_per_1k


# ================================================================
# INTEGRATION HELPERS
# ================================================================

def integrate_with_existing_service(service_instance, 
                                   service_name: str,
                                   methods_to_monitor: Optional[list] = None):
    """
    Integrar monitoreo con un servicio existente
    
    Args:
        service_instance: Instancia del servicio
        service_name: Nombre del servicio para categorización
        methods_to_monitor: Lista de métodos a monitorear (None = todos)
    """
    if methods_to_monitor is None:
        methods_to_monitor = [attr for attr in dir(service_instance) 
                            if callable(getattr(service_instance, attr)) 
                            and not attr.startswith('_')]
    
    for method_name in methods_to_monitor:
        if hasattr(service_instance, method_name):
            method = getattr(service_instance, method_name)
            if callable(method):
                # Aplicar decorator
                wrapped_method = monitor_api_call(service_name, method_name)(
                    functools.partial(method, service_instance)
                )
                setattr(service_instance, method_name, wrapped_method)
                logger.info(f"Monitoring enabled for {service_name}.{method_name}")


def create_monitoring_middleware():
    """
    Crear middleware de FastAPI para monitoreo automático
    """
    from fastapi import Request, Response
    from fastapi.responses import JSONResponse
    import time
    
    async def monitoring_middleware(request: Request, call_next):
        # Solo monitorear requests relacionados con AI
        if not any(endpoint in request.url.path.lower() 
                  for endpoint in ['/news', '/ai', '/analysis', '/summary']):
            return await call_next(request)
        
        start_time = time.time()
        task_id = f"request_{int(time.time() * 1000)}"
        
        ai_monitor.start_task(
            task_id=task_id,
            task_type="api_request",
            metadata={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "client_ip": request.client.host if request.client else None
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calcular latencia
            latency = time.time() - start_time
            
            # Completar monitoreo
            ai_monitor.complete_task(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                tokens_used=0,  # Se calcularía basado en response
                cost=0.0
            )
            
            return response
            
        except Exception as e:
            latency = time.time() - start_time
            
            ai_monitor.complete_task(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error_message=str(e)
            )
            raise
    
    return monitoring_middleware


# ================================================================
# BATCH PROCESSING HELPERS
# ================================================================

async def monitor_batch_processing(items: list, 
                                 process_func: Callable,
                                 batch_size: int = 10,
                                 task_type: str = "batch_process") -> list:
    """
    Procesar items en batches con monitoreo automático
    
    Args:
        items: Lista de items a procesar
        process_func: Función para procesar cada item
        batch_size: Tamaño del batch
        task_type: Tipo de tarea para monitoreo
    
    Returns:
        Lista de resultados procesados
    """
    results = []
    total_items = len(items)
    batch_id = f"batch_{task_type}_{int(time.time() * 1000)}"
    
    # Monitorear batch completo
    batch_task = ai_monitor.start_task(
        task_id=batch_id,
        task_type=task_type,
        metadata={
            "total_items": total_items,
            "batch_size": batch_size,
            "estimated_batches": (total_items + batch_size - 1) // batch_size
        }
    )
    
    try:
        for i in range(0, total_items, batch_size):
            batch_items = items[i:i + batch_size]
            batch_number = i // batch_size + 1
            
            # Monitorear cada batch
            batch_task_id = f"{batch_id}_batch_{batch_number}"
            ai_monitor.start_task(
                task_id=batch_task_id,
                task_type=f"{task_type}_batch",
                metadata={
                    "batch_number": batch_number,
                    "items_in_batch": len(batch_items),
                    "batch_start_index": i
                }
            )
            
            # Procesar batch
            batch_results = []
            for item in batch_items:
                try:
                    if asyncio.iscoroutinefunction(process_func):
                        result = await process_func(item)
                    else:
                        result = process_func(item)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Error processing item {item}: {e}")
                    batch_results.append(None)
            
            # Completar batch
            ai_monitor.complete_task(batch_task_id, TaskStatus.COMPLETED)
            results.extend(batch_results)
        
        # Completar batch principal
        ai_monitor.complete_task(
            batch_id, 
            TaskStatus.COMPLETED,
            metadata={
                "total_processed": len(results),
                "success_rate": len([r for r in results if r is not None]) / len(results)
            }
        )
        
        return results
        
    except Exception as e:
        ai_monitor.complete_task(batch_id, TaskStatus.FAILED, error_message=str(e))
        raise


# ================================================================
# MONITORING CONTEXT MANAGERS
# ================================================================

class MonitoringContext:
    """
    Context manager para monitoreo manual de bloques de código
    """
    
    def __init__(self, task_type: str, model: str = "", 
                 metadata: Optional[Dict[str, Any]] = None):
        self.task_type = task_type
        self.model = model
        self.metadata = metadata or {}
        self.task_id = None
        self.start_time = None
    
    def __enter__(self):
        self.task_id = f"{self.task_type}_{int(time.time() * 1000)}"
        self.start_time = time.time()
        
        ai_monitor.start_task(
            task_id=self.task_id,
            task_type=self.task_type,
            model=self.model,
            metadata=self.metadata
        )
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Error occurred
            ai_monitor.complete_task(
                self.task_id,
                TaskStatus.FAILED,
                error_message=str(exc_val)
            )
        else:
            # Success
            duration = time.time() - self.start_time
            ai_monitor.complete_task(
                self.task_id,
                TaskStatus.COMPLETED,
                metadata={
                    **self.metadata,
                    "duration": duration,
                    "manual_context": True
                }
            )
    
    def set_cost(self, cost: float, tokens_used: int = 0):
        """Establecer costo manualmente"""
        if self.task_id and self.start_time:
            ai_monitor.complete_task(
                self.task_id,
                TaskStatus.COMPLETED,
                cost=cost,
                tokens_used=tokens_used
            )


def monitor_context(task_type: str, model: str = "", 
                   metadata: Optional[Dict[str, Any]] = None) -> MonitoringContext:
    """
    Crear context manager para monitoreo
    """
    return MonitoringContext(task_type, model, metadata)


# ================================================================
# ANALYTICS HELPERS
# ================================================================

def get_task_analytics(task_type: str, days: int = 7) -> Dict[str, Any]:
    """
    Obtener analytics detallados para un tipo de tarea específico
    """
    from datetime import datetime, timedelta
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    # Obtener tareas del historial
    tasks = ai_monitor.task_monitor.get_task_history(limit=10000)
    filtered_tasks = [
        t for t in tasks 
        if t.task_type == task_type and t.start_time >= cutoff
    ]
    
    if not filtered_tasks:
        return {
            "task_type": task_type,
            "period_days": days,
            "total_tasks": 0,
            "message": "No tasks found for this period"
        }
    
    # Calcular métricas
    completed_tasks = [t for t in filtered_tasks if t.status == TaskStatus.COMPLETED]
    failed_tasks = [t for t in filtered_tasks if t.status == TaskStatus.FAILED]
    
    durations = [t.duration for t in completed_tasks if t.duration]
    costs = [t.cost for t in completed_tasks if t.cost > 0]
    tokens = [t.tokens_used for t in completed_tasks if t.tokens_used > 0]
    
    import statistics
    
    return {
        "task_type": task_type,
        "period_days": days,
        "total_tasks": len(filtered_tasks),
        "completed_tasks": len(completed_tasks),
        "failed_tasks": len(failed_tasks),
        "success_rate": len(completed_tasks) / len(filtered_tasks) * 100,
        "performance": {
            "average_duration": statistics.mean(durations) if durations else 0,
            "median_duration": statistics.median(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0
        },
        "costs": {
            "total_cost": sum(costs),
            "average_cost": statistics.mean(costs) if costs else 0,
            "total_tokens": sum(tokens)
        },
        "daily_breakdown": _get_daily_breakdown(filtered_tasks)
    }


def _get_daily_breakdown(tasks: list) -> Dict[str, Dict[str, int]]:
    """Obtener breakdown diario de tareas"""
    from collections import defaultdict
    
    daily_stats = defaultdict(lambda: {"completed": 0, "failed": 0, "total": 0})
    
    for task in tasks:
        day = task.start_time.strftime("%Y-%m-%d")
        daily_stats[day]["total"] += 1
        if task.status == TaskStatus.COMPLETED:
            daily_stats[day]["completed"] += 1
        elif task.status == TaskStatus.FAILED:
            daily_stats[day]["failed"] += 1
    
    return dict(daily_stats)


# ================================================================
# EXPORT INTEGRATION FUNCTIONS
# ================================================================

__all__ = [
    "monitor_ai_task", "monitor_api_call", "monitor_context",
    "integrate_with_existing_service", "create_monitoring_middleware",
    "monitor_batch_processing", "get_task_analytics",
    "MonitoringContext", "calculate_batch_cost", "_calculate_openai_cost"
]