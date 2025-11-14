"""
Tareas de Celery para monitoreo y mantenimiento del sistema
Maneja el monitoreo de tareas, limpieza de datos antiguos y métricas
"""

import time
from typing import Dict, Any, List, Optional
from celery import Task
from loguru import logger

from celery_app import celery_app
from app.core.config import settings


class MonitoringTask(Task):
    """Task base para tareas de monitoreo y mantenimiento"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 2, 'countdown': 30}
    retry_backoff = True
    retry_backoff_max = 300
    retry_jitter = False
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Handler de falla para logging"""
        logger.error(f"💥 Error en tarea de monitoreo {task_id}: {exc}")


@celery_app.task(
    bind=True,
    name='app.tasks.monitoring.clean_old_task_results',
    base=MonitoringTask,
    queue='maintenance',
    rate_limit='1/h'
)
def clean_old_task_results(self, retention_days: int = 7) -> Dict[str, Any]:
    """
    Limpiar resultados de tareas antiguos para liberar espacio
    
    Args:
        retention_days: Días de retención de resultados
        
    Returns:
        Dict con información de la limpieza
    """
    start_time = time.time()
    
    try:
        logger.info(f"🧹 Iniciando limpieza de resultados antiguos (retención: {retention_days} días)")
        
        # TODO: Implementar lógica real de limpieza en Redis/BD
        # Esta implementación placeholder debería conectarse con Redis/BD
        
        # Simular limpieza
        cleaned_count = 0
        errors = []
        
        # En implementación real, aquí irían queries para eliminar resultados antiguos
        # Por ejemplo:
        # - Limpiar resultados de Celery en Redis
        # - Eliminar análisis antiguos de la BD
        # - Limpiar resúmenes caducados
        
        cleaning_results = {
            'task_results_cleaned': 0,
            'analysis_results_cleaned': 0,
            'summary_results_cleaned': 0,
            'redis_keys_removed': 0,
            'total_space_freed_mb': 0
        }
        
        processing_time = time.time() - start_time
        
        return {
            'status': 'success',
            'retention_days': retention_days,
            'cleaning_results': cleaning_results,
            'processing_time': processing_time,
            'cleaned_at': time.time(),
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"❌ Error en limpieza de resultados: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


@celery_app.task(
    bind=True,
    name='app.tasks.monitoring.get_system_metrics',
    base=MonitoringTask,
    queue='maintenance',
    rate_limit='5/h'
)
def get_system_metrics(self) -> Dict[str, Any]:
    """
    Obtener métricas del sistema y workers de Celery
    
    Returns:
        Dict con métricas del sistema
    """
    start_time = time.time()
    
    try:
        logger.info("📊 Recopilando métricas del sistema")
        
        # Métricas de Celery
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            
            # Métricas de workers
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            reserved_tasks = inspect.reserved()
            
            # Métricas de estadísticas
            stats = inspect.stats()
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener métricas de Celery: {str(e)}")
            active_tasks = {}
            scheduled_tasks = {}
            reserved_tasks = {}
            stats = {}
        
        # Métricas de Redis (si está disponible)
        try:
            import redis
            r = redis.from_url(settings.REDIS_URL)
            
            redis_info = r.info()
            redis_metrics = {
                'connected_clients': redis_info.get('connected_clients', 0),
                'used_memory': redis_info.get('used_memory', 0),
                'used_memory_human': redis_info.get('used_memory_human', '0B'),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0)
            }
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener métricas de Redis: {str(e)}")
            redis_metrics = {}
        
        # Métricas del sistema (CPU, memoria)
        try:
            import psutil
            
            system_metrics = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'load_average': psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
            }
            
        except Exception as e:
            logger.warning(f"No se pudieron obtener métricas del sistema: {str(e)}")
            system_metrics = {}
        
        # Compilar todas las métricas
        processing_time = time.time() - start_time
        
        system_metrics_result = {
            'timestamp': time.time(),
            'processing_time': processing_time,
            'celery_metrics': {
                'active_workers': len(stats),
                'worker_stats': stats,
                'active_tasks_count': sum(len(tasks) for tasks in (active_tasks or {}).values()),
                'scheduled_tasks_count': sum(len(tasks) for tasks in (scheduled_tasks or {}).values()),
                'reserved_tasks_count': sum(len(tasks) for tasks in (reserved_tasks or {}).values())
            },
            'redis_metrics': redis_metrics,
            'system_metrics': system_metrics,
            'task_id': self.request.id
        }
        
        logger.info("✅ Métricas del sistema recopiladas exitosamente")
        
        return {
            'status': 'success',
            'metrics': system_metrics_result
        }
        
    except Exception as e:
        logger.error(f"❌ Error obteniendo métricas del sistema: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


@celery_app.task(
    bind=True,
    name='app.tasks.monitoring.check_task_health',
    base=MonitoringTask,
    queue='maintenance',
    rate_limit='10/h'
)
def check_task_health(self) -> Dict[str, Any]:
    """
    Verificar la salud de las tareas y workers
    
    Returns:
        Dict con información de salud del sistema
    """
    start_time = time.time()
    
    try:
        logger.info("🏥 Verificando salud de tareas y workers")
        
        health_status = {
            'overall_status': 'healthy',
            'workers': {},
            'queues': {},
            'recent_failures': [],
            'recommendations': []
        }
        
        # Verificar estado de workers
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            
            # Obtener estadísticas de workers
            stats = inspect.stats()
            active = inspect.active()
            
            if not stats:
                health_status['overall_status'] = 'unhealthy'
                health_status['recommendations'].append("No hay workers activos")
            else:
                for worker_name, worker_stats in stats.items():
                    worker_active_tasks = active.get(worker_name, [])
                    
                    health_status['workers'][worker_name] = {
                        'status': 'active',
                        'total_tasks_processed': worker_stats.get('total', {}).get('task_received', 0),
                        'active_tasks': len(worker_active_tasks),
                        'pool_processes': worker_stats.get('pool', {}).get('processes', 0),
                        'memory_usage': worker_stats.get('rusage', {}).get('maxrss', 0)
                    }
                    
                    # Verificar si el worker está sobrecargado
                    if len(worker_active_tasks) > 10:
                        health_status['workers'][worker_name]['status'] = 'overloaded'
                        health_status['recommendations'].append(f"Worker {worker_name} está sobrecargado")
        
        except Exception as e:
            logger.warning(f"Error verificando workers: {str(e)}")
            health_status['recommendations'].append("No se pudo verificar el estado de los workers")
        
        # Verificar colas
        try:
            # Verificar longitud de colas (esto requeriría acceso directo a Redis)
            # Por ahora simulamos
            health_status['queues'] = {
                'ai_analysis': {'length': 0, 'status': 'healthy'},
                'ai_classification': {'length': 0, 'status': 'healthy'},
                'ai_summaries': {'length': 0, 'status': 'healthy'},
                'default': {'length': 0, 'status': 'healthy'}
            }
            
        except Exception as e:
            logger.warning(f"Error verificando colas: {str(e)}")
            health_status['recommendations'].append("No se pudo verificar el estado de las colas")
        
        # Verificar tareas fallidas recientes
        try:
            # TODO: Implementar verificación real de tareas fallidas
            # Esto requeriría consultar los resultados en Redis/BD
            health_status['recent_failures'] = []
            
        except Exception as e:
            logger.warning(f"Error verificando fallas recientes: {str(e)}")
        
        # Determinar estado general
        critical_issues = len([rec for rec in health_status['recommendations'] if 'sobrecargado' in rec or 'No hay workers' in rec])
        
        if critical_issues > 0:
            health_status['overall_status'] = 'critical'
        elif len(health_status['recommendations']) > 2:
            health_status['overall_status'] = 'warning'
        
        processing_time = time.time() - start_time
        
        return {
            'status': 'success',
            'health_check': {
                **health_status,
                'checked_at': time.time(),
                'processing_time': processing_time,
                'task_id': self.request.id
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error en verificación de salud: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }


@celery_app.task(
    bind=True,
    name='app.tasks.monitoring.generate_weekly_report',
    base=MonitoringTask,
    queue='maintenance',
    rate_limit='1/h'  # Changed from '1/w' (unsupported) - Celery 5.3.4 only supports s/m/h
)
def generate_weekly_report(self) -> Dict[str, Any]:
    """
    Generar reporte semanal del sistema
    
    Returns:
        Dict con el reporte semanal
    """
    start_time = time.time()
    
    try:
        logger.info("📈 Generando reporte semanal del sistema")
        
        # Recopilar métricas de la semana
        system_metrics = get_system_metrics.delay().get(timeout=30)
        
        # TODO: Implementar recopilación real de métricas semanales
        # Por ahora simulamos datos
        
        weekly_stats = {
            'total_tasks_processed': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'average_processing_time': 0,
            'top_performing_workers': [],
            'most_used_queues': [],
            'error_patterns': []
        }
        
        # Generar reporte en formato texto
        report_lines = []
        report_lines.append("# 📊 REPORTE SEMANAL - AI NEWS AGGREGATOR")
        report_lines.append(f"*Generado el: {time.strftime('%Y-%m-%d %H:%M:%S')}*")
        report_lines.append("")
        
        report_lines.append("## 📈 Resumen General")
        report_lines.append(f"- Total de tareas procesadas: {weekly_stats['total_tasks_processed']}")
        report_lines.append(f"- Tareas exitosas: {weekly_stats['successful_tasks']}")
        report_lines.append(f"- Tareas fallidas: {weekly_stats['failed_tasks']}")
        report_lines.append(f"- Tasa de éxito: {(weekly_stats['successful_tasks'] / max(weekly_stats['total_tasks_processed'], 1)) * 100:.1f}%")
        report_lines.append("")
        
        report_lines.append("## ⚡ Rendimiento")
        report_lines.append(f"- Tiempo promedio de procesamiento: {weekly_stats['average_processing_time']:.2f}s")
        report_lines.append(f"- Workers más activos: {', '.join(weekly_stats['top_performing_workers'])}")
        report_lines.append("")
        
        report_lines.append("## 🚨 Issues y Recomendaciones")
        if weekly_stats['error_patterns']:
            for error in weekly_stats['error_patterns']:
                report_lines.append(f"- {error}")
        else:
            report_lines.append("No se detectaron patrones de error significativos.")
        report_lines.append("")
        
        report_lines.append("## 📋 Próximas Acciones")
        report_lines.append("- Revisar configuración de workers si es necesario")
        report_lines.append("- Monitorear uso de recursos del sistema")
        report_lines.append("- Optimizar consultas de base de datos")
        
        report_content = '\n'.join(report_lines)
        
        processing_time = time.time() - start_time
        
        return {
            'status': 'success',
            'report': report_content,
            'weekly_stats': weekly_stats,
            'system_metrics': system_metrics,
            'generated_at': time.time(),
            'processing_time': processing_time,
            'task_id': self.request.id
        }
        
    except Exception as e:
        logger.error(f"❌ Error generando reporte semanal: {str(e)}")
        
        return {
            'status': 'error',
            'error_message': str(e),
            'processing_time': time.time() - start_time,
            'task_id': self.request.id
        }