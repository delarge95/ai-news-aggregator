"""
AI Monitoring Logger
Sistema de logging especializado para el monitoreo AI que se integra con el logging existente
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import threading
from queue import Queue, Empty

from ..core.config import settings


class AIMonitoringFormatter(logging.Formatter):
    """Formatter especializado para logs de monitoreo AI"""
    
    def format(self, record):
        # Agregar timestamp en formato ISO
        record.iso_timestamp = datetime.utcnow().isoformat()
        
        # Identificar logs de monitoreo AI
        record.is_ai_monitor = hasattr(record, 'task_id') or hasattr(record, 'alert_id')
        
        # Formato JSON para logs de monitoreo
        if record.is_ai_monitor:
            log_data = {
                "timestamp": record.iso_timestamp,
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage()
            }
            
            # Agregar campos específicos de AI monitoring
            if hasattr(record, 'task_id'):
                log_data["task_id"] = record.task_id
            
            if hasattr(record, 'alert_id'):
                log_data["alert_id"] = record.alert_id
            
            if hasattr(record, 'task_type'):
                log_data["task_type"] = record.task_type
            
            if hasattr(record, 'task_status'):
                log_data["task_status"] = record.task_status
            
            if hasattr(record, 'cost'):
                log_data["cost"] = record.cost
            
            if hasattr(record, 'latency'):
                log_data["latency"] = record.latency
            
            if hasattr(record, 'tokens_used'):
                log_data["tokens_used"] = record.tokens_used
            
            if hasattr(record, 'error_message'):
                log_data["error_message"] = record.error_message
            
            if hasattr(record, 'severity'):
                log_data["severity"] = record.severity
            
            if hasattr(record, 'metadata'):
                log_data["metadata"] = record.metadata
            
            # Agregar información de excepción si existe
            if record.exc_info:
                log_data["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_data, ensure_ascii=False)
        
        else:
            # Formato estándar para otros logs
            return super().format(record)


class AIMonitoringHandler(logging.Handler):
    """Handler personalizado para logs de monitoreo AI"""
    
    def __init__(self, log_dir: str = "logs", max_size_mb: int = 100):
        super().__init__()
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.queue = Queue()
        self.writer_thread = None
        self.stop_event = threading.Event()
        
        # Archivos de log especializados
        self.log_files = {
            'tasks': self.log_dir / 'ai_tasks.log',
            'costs': self.log_dir / 'ai_costs.log',
            'alerts': self.log_dir / 'ai_alerts.log',
            'errors': self.log_dir / 'ai_errors.log',
            'performance': self.log_dir / 'ai_performance.log'
        }
        
        # Crear archivos si no existen
        for file_path in self.log_files.values():
            file_path.touch(exist_ok=True)
        
        # Iniciar writer thread
        self.start_writer()
    
    def start_writer(self):
        """Iniciar thread de escritura"""
        if not self.writer_thread or not self.writer_thread.is_alive():
            self.writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
            self.writer_thread.start()
    
    def stop_writer(self):
        """Detener thread de escritura"""
        self.stop_event.set()
        if self.writer_thread and self.writer_thread.is_alive():
            self.writer_thread.join(timeout=5)
    
    def _writer_loop(self):
        """Loop principal del writer thread"""
        while not self.stop_event.is_set():
            try:
                # Procesar logs en cola
                try:
                    log_entry = self.queue.get(timeout=1)
                    self._write_log_entry(log_entry)
                except Empty:
                    continue
            except Exception as e:
                # Log del error pero no morir
                sys.stderr.write(f"Error in AI monitoring writer: {e}\n")
    
    def _write_log_entry(self, log_entry: Dict[str, Any]):
        """Escribir entrada de log al archivo apropiado"""
        try:
            log_file = self._get_log_file(log_entry)
            if not log_file:
                return
            
            # Verificar rotación de archivo
            if log_file.stat().st_size > self.max_size_bytes:
                self._rotate_log_file(log_file)
            
            # Escribir entrada
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry['formatted'] + '\n')
                f.flush()
                
        except Exception as e:
            sys.stderr.write(f"Error writing AI monitoring log: {e}\n")
    
    def _get_log_file(self, log_entry: Dict[str, Any]) -> Optional[Path]:
        """Determinar archivo de log apropiado"""
        level = log_entry.get('level', 'INFO')
        
        # Routing basado en tipo de contenido
        if 'alert_id' in log_entry:
            return self.log_files['alerts']
        elif 'error_message' in log_entry or level == 'ERROR':
            return self.log_files['errors']
        elif 'cost' in log_entry:
            return self.log_files['costs']
        elif 'latency' in log_entry or 'throughput' in log_entry:
            return self.log_files['performance']
        elif 'task_id' in log_entry:
            return self.log_files['tasks']
        else:
            return self.log_files['tasks']  # default
    
    def _rotate_log_file(self, log_file: Path):
        """Rotar archivo de log"""
        try:
            # Mover archivo actual a backup
            backup_file = log_file.with_suffix(f'.backup_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.log')
            log_file.rename(backup_file)
            
            # Crear nuevo archivo
            log_file.touch()
            
            # Limpiar backups antiguos (mantener últimos 5)
            backups = list(log_file.parent.glob(f'{log_file.stem}.backup_*.log'))
            backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for old_backup in backups[5:]:
                old_backup.unlink()
                
        except Exception as e:
            sys.stderr.write(f"Error rotating log file {log_file}: {e}\n")
    
    def emit(self, record):
        """Emitir log record"""
        try:
            # Formatear record
            formatted = self.format(record)
            
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'level': record.levelname,
                'formatted': formatted,
                'task_id': getattr(record, 'task_id', None),
                'alert_id': getattr(record, 'alert_id', None)
            }
            
            # Agregar a cola para escritura asíncrona
            self.queue.put_nowait(log_entry)
            
        except Exception:
            self.handleError(record)
    
    def close(self):
        """Cerrar handler"""
        self.stop_writer()
        super().close()


def setup_ai_monitoring_logging():
    """Configurar logging especializado para monitoreo AI"""
    
    # Configurar logger principal
    ai_monitor_logger = logging.getLogger('app.services.ai_monitor')
    ai_monitor_logger.setLevel(logging.INFO)
    
    # Remover handlers existentes
    for handler in ai_monitor_logger.handlers[:]:
        ai_monitor_logger.removeHandler(handler)
    
    # Agregar console handler con formato simple
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = AIMonitoringFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    ai_monitor_logger.addHandler(console_handler)
    
    # Agregar file handler si está habilitado
    if settings.AI_MONITORING_ENABLED:
        # Crear directorio de logs
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)
        
        file_handler = AIMonitoringHandler(str(log_dir))
        file_handler.setLevel(logging.INFO)
        file_formatter = AIMonitoringFormatter()
        file_handler.setFormatter(file_formatter)
        ai_monitor_logger.addHandler(file_handler)
    
    # Configurar propagate para logs de alertas
    alert_logger = logging.getLogger('app.services.ai_monitor.alerts')
    alert_logger.setLevel(logging.WARNING)
    
    # Configurar propagate para logs de errores
    error_logger = logging.getLogger('app.services.ai_monitor.errors')
    error_logger.setLevel(logging.ERROR)
    
    return ai_monitor_logger


# ================================================================
# SPECIALIZED LOGGING FUNCTIONS
# ================================================================

def log_task_start(task_id: str, task_type: str, model: str = "", **metadata):
    """Log especializado para inicio de tareas"""
    logger = logging.getLogger('app.services.ai_monitor')
    
    extra = {
        'task_id': task_id,
        'task_type': task_type,
        'metadata': metadata
    }
    
    if model:
        extra['model'] = model
    
    logger.info(f"Task started: {task_type} ({task_id})", extra=extra)


def log_task_completion(task_id: str, status: str, duration: float, 
                       cost: float = 0.0, tokens_used: int = 0, **metadata):
    """Log especializado para completación de tareas"""
    logger = logging.getLogger('app.services.ai_monitor')
    
    extra = {
        'task_id': task_id,
        'task_status': status,
        'duration': duration,
        'cost': cost,
        'tokens_used': tokens_used,
        'metadata': metadata
    }
    
    logger.info(f"Task completed: {task_id} ({status}) - "
               f"{duration:.2f}s, ${cost:.4f}, {tokens_used} tokens", extra=extra)


def log_task_error(task_id: str, error_message: str, **metadata):
    """Log especializado para errores de tareas"""
    logger = logging.getLogger('app.services.ai_monitor.errors')
    
    extra = {
        'task_id': task_id,
        'error_message': error_message,
        'metadata': metadata
    }
    
    logger.error(f"Task failed: {task_id} - {error_message}", extra=extra)


def log_alert(alert_id: str, severity: str, title: str, message: str, **metadata):
    """Log especializado para alertas"""
    logger = logging.getLogger('app.services.ai_monitor.alerts')
    
    # Mapear severity a nivel de log
    level_map = {
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level = level_map.get(severity.upper(), logging.INFO)
    
    extra = {
        'alert_id': alert_id,
        'severity': severity,
        'title': title,
        'metadata': metadata
    }
    
    logger.log(log_level, f"Alert: {title} - {message}", extra=extra)


def log_cost_event(task_id: str, cost: float, tokens_used: int, model: str, **metadata):
    """Log especializado para eventos de costo"""
    logger = logging.getLogger('app.services.ai_monitor.costs')
    
    extra = {
        'task_id': task_id,
        'cost': cost,
        'tokens_used': tokens_used,
        'model': model,
        'metadata': metadata
    }
    
    logger.info(f"Cost tracked: {task_id} - ${cost:.4f} "
               f"({tokens_used} tokens, {model})", extra=extra)


def log_performance_metric(metric_name: str, value: float, unit: str = "", **metadata):
    """Log especializado para métricas de performance"""
    logger = logging.getLogger('app.services.ai_monitor.performance')
    
    extra = {
        'metric_name': metric_name,
        'value': value,
        'unit': unit,
        'metadata': metadata
    }
    
    logger.info(f"Performance metric: {metric_name} = {value} {unit}", extra=extra)


# ================================================================
# LOG ANALYSIS FUNCTIONS
# ================================================================

def parse_ai_logs(log_file_path: Path, limit: int = 1000) -> list:
    """
    Parsear logs de AI monitoring desde archivo
    
    Args:
        log_file_path: Ruta al archivo de log
        limit: Número máximo de líneas a leer
    
    Returns:
        Lista de entradas de log parseadas
    """
    logs = []
    
    try:
        with open(log_file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i >= limit:
                    break
                
                try:
                    # Intentar parsear como JSON
                    log_entry = json.loads(line.strip())
                    logs.append(log_entry)
                except json.JSONDecodeError:
                    # Si no es JSON, tratar como log plano
                    logs.append({
                        'raw_line': line.strip(),
                        'line_number': i + 1
                    })
    
    except FileNotFoundError:
        logger.warning(f"Log file not found: {log_file_path}")
    except Exception as e:
        logger.error(f"Error reading log file {log_file_path}: {e}")
    
    return logs


def get_recent_errors(hours: int = 24) -> list:
    """Obtener errores recientes de los logs"""
    log_file = Path('logs/ai_errors.log')
    
    if not log_file.exists():
        return []
    
    cutoff = datetime.utcnow().replace(second=0, microsecond=0)
    cutoff = cutoff.replace(hour=cutoff.hour - hours)
    
    recent_errors = []
    logs = parse_ai_logs(log_file, limit=10000)
    
    for log_entry in logs:
        try:
            if isinstance(log_entry, dict) and 'timestamp' in log_entry:
                log_time = datetime.fromisoformat(log_entry['timestamp'])
                if log_time >= cutoff:
                    recent_errors.append(log_entry)
        except (ValueError, KeyError):
            continue
    
    return recent_errors


def get_task_summary_from_logs(task_id: str) -> Optional[Dict[str, Any]]:
    """Obtener resumen de tarea desde logs"""
    log_file = Path('logs/ai_tasks.log')
    
    if not log_file.exists():
        return None
    
    logs = parse_ai_logs(log_file, limit=10000)
    
    task_events = []
    for log_entry in logs:
        if isinstance(log_entry, dict) and log_entry.get('task_id') == task_id:
            task_events.append(log_entry)
    
    if not task_events:
        return None
    
    # Ordenar por timestamp
    task_events.sort(key=lambda x: x.get('timestamp', ''))
    
    return {
        'task_id': task_id,
        'events': task_events,
        'start_time': task_events[0].get('timestamp'),
        'end_time': task_events[-1].get('timestamp') if len(task_events) > 1 else None,
        'total_events': len(task_events)
    }


# ================================================================
# EXPORT
# ================================================================

# Configurar logging al importar
if settings.AI_MONITORING_ENABLED:
    setup_ai_monitoring_logging()

__all__ = [
    'AIMonitoringFormatter', 'AIMonitoringHandler', 'setup_ai_monitoring_logging',
    'log_task_start', 'log_task_completion', 'log_task_error', 'log_alert',
    'log_cost_event', 'log_performance_metric', 'parse_ai_logs',
    'get_recent_errors', 'get_task_summary_from_logs'
]