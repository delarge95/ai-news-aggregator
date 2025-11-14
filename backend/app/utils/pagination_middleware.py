"""
Middleware de Extracción Automática de Parámetros de Query

Este middleware automáticamente extrae y valida parámetros de paginación y filtrado
de las requests HTTP, haciendo el sistema más eficiente y fácil de usar.
"""

import logging
from typing import Dict, Any, Optional, Set
from urllib.parse import parse_qs

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .pagination import PaginationParams, FilterConfig, ModelFilterConfig

logger = logging.getLogger(__name__)


class QueryParamExtractionMiddleware(BaseHTTPMiddleware):
    """
    Middleware para extracción automática de parámetros de query
    
    Este middleware:
    - Extrae parámetros de paginación y filtrado automáticamente
    - Valida parámetros contra la configuración del modelo
    - Proporciona defaults inteligentes
    - Registra métricas de uso
    """
    
    # Endpoints que deben excluirse del procesamiento automático
    EXCLUDED_ENDPOINTS: Set[str] = {
        '/health',
        '/docs',
        '/redoc',
        '/openapi.json',
        '/favicon.ico'
    }
    
    # Modelos permitidos para extracción automática
    ALLOWED_MODELS: Set[str] = {
        'article', 'source', 'trending_topic', 'analysis_task', 'user_preference'
    }
    
    def __init__(
        self,
        app: ASGIApp,
        enable_auto_extraction: bool = True,
        log_extractions: bool = True,
        default_models: Dict[str, str] = None
    ):
        """
        Inicializar middleware
        
        Args:
            app: aplicación ASGI
            enable_auto_extraction: si habilitar extracción automática
            log_extractions: si registrar extracciones en logs
            default_models: mapeo de paths a modelos por defecto
        """
        super().__init__(app)
        self.enable_auto_extraction = enable_auto_extraction
        self.log_extractions = log_extractions
        self.default_models = default_models or {}
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Procesar request y extraer parámetros automáticamente"""
        
        # Verificar si el endpoint debe ser excluido
        if self._should_exclude_endpoint(request.url.path):
            return await call_next(request)
        
        # Extraer modelo desde la URL o headers
        model_name = self._extract_model_from_request(request)
        
        if model_name and self.enable_auto_extraction:
            try:
                # Intentar extraer parámetros de paginación
                pagination_params = self._extract_pagination_params(request, model_name)
                
                # Almacenar en el estado de la request para uso posterior
                request.state.pagination_params = pagination_params
                request.state.model_name = model_name
                
                # Registrar extracción si está habilitado
                if self.log_extractions:
                    self._log_extraction(request, model_name, pagination_params)
                    
            except Exception as e:
                logger.warning(
                    f"Error extrayendo parámetros para modelo {model_name} "
                    f"en endpoint {request.url.path}: {e}"
                )
                # No fallar la request, solo no extraer parámetros
        
        response = await call_next(request)
        return response
    
    def _should_exclude_endpoint(self, path: str) -> bool:
        """Verificar si un endpoint debe ser excluido"""
        return any(path.startswith(excluded) for excluded in self.EXCLUDED_ENDPOINTS)
    
    def _extract_model_from_request(self, request: Request) -> Optional[str]:
        """
        Extraer nombre del modelo desde la URL, headers o configuración
        
        Priority:
        1. Header 'X-Model-Name'
        2. Path parameter 'model'
        3. Default mapping por endpoint
        4. Detección automática desde el path
        """
        # 1. Verificar header personalizado
        model_header = request.headers.get('X-Model-Name')
        if model_header and model_header.lower() in self.ALLOWED_MODELS:
            return model_header.lower()
        
        # 2. Verificar path parameter
        if hasattr(request, 'path_params') and 'model' in request.path_params:
            model_param = request.path_params['model'].lower()
            if model_param in self.ALLOWED_MODELS:
                return model_param
        
        # 3. Verificar mapeo por defecto
        path = request.url.path
        if path in self.default_models:
            default_model = self.default_models[path].lower()
            if default_model in self.ALLOWED_MODELS:
                return default_model
        
        # 4. Detección automática desde el path
        return self._detect_model_from_path(path)
    
    def _detect_model_from_path(self, path: str) -> Optional[str]:
        """Detectar modelo desde la URL"""
        path_lower = path.lower()
        
        # Mapeo directo de paths a modelos
        path_to_model = {
            '/api/v1/news': 'article',
            '/api/v1/news/sources': 'source',
            '/api/v1/news/categories': 'trending_topic',
            '/api/v1/ai/monitor': 'analysis_task',
            '/api/v1/ai/tasks': 'analysis_task',
        }
        
        # Buscar coincidencias exactas
        if path in path_to_model:
            return path_to_model[path]
        
        # Buscar coincidencias parciales
        for path_pattern, model in path_to_model.items():
            if path_pattern in path_lower:
                return model
        
        # Detección basada en palabras clave en el path
        if 'news' in path_lower or 'article' in path_lower:
            return 'article'
        elif 'source' in path_lower:
            return 'source'
        elif 'topic' in path_lower or 'trend' in path_lower:
            return 'trending_topic'
        elif 'task' in path_lower or 'analysis' in path_lower or 'ai' in path_lower:
            return 'analysis_task'
        
        return None
    
    def _extract_pagination_params(self, request: Request, model_name: str) -> PaginationParams:
        """Extraer parámetros de paginación para el modelo especificado"""
        try:
            return PaginationParams(
                request=request,
                model_name=model_name,
                default_page_size=self._get_default_page_size(model_name),
                max_page_size=self._get_max_page_size(model_name)
            )
        except Exception as e:
            logger.error(f"Error creando PaginationParams: {e}")
            raise
    
    def _get_default_page_size(self, model_name: str) -> int:
        """Obtener tamaño de página por defecto según el modelo"""
        defaults = {
            'article': 20,
            'source': 50,
            'trending_topic': 30,
            'analysis_task': 25,
            'user_preference': 10,
        }
        return defaults.get(model_name, 20)
    
    def _get_max_page_size(self, model_name: str) -> int:
        """Obtener tamaño máximo de página según el modelo"""
        limits = {
            'article': 100,
            'source': 200,
            'trending_topic': 50,
            'analysis_task': 100,
            'user_preference': 50,
        }
        return limits.get(model_name, 100)
    
    def _log_extraction(self, request: Request, model_name: str, pagination_params: PaginationParams):
        """Registrar extracción de parámetros en logs"""
        query_params = dict(request.query_params)
        
        # Información básica
        log_data = {
            'endpoint': request.url.path,
            'method': request.method,
            'model': model_name,
            'page': pagination_params.page,
            'page_size': pagination_params.page_size,
            'has_filters': pagination_params.has_filters(),
            'has_sort': pagination_params.has_sort(),
            'search': pagination_params.search or None,
            'total_query_params': len(query_params),
        }
        
        # Agregar filtros si existen
        if pagination_params.filters:
            log_data['filters_count'] = len(pagination_params.filters)
            log_data['filters'] = list(pagination_params.filters.keys())
        
        # Agregar ordenamiento si existe
        if pagination_params.sort:
            log_data['sort_fields'] = [s.field for s in pagination_params.sort]
        
        logger.info(f"Query params extracted: {log_data}")


class PaginationMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware para recopilar métricas de uso de paginación
    
    Este middleware recopila estadísticas sobre:
    - Uso de filtros más comunes
    - Tamaños de página preferidos
    - Rendimiento de queries
    - Errores de validación
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.metrics = {
            'total_requests': 0,
            'pagination_requests': 0,
            'filter_usage': {},
            'sort_usage': {},
            'page_size_distribution': {},
            'error_count': 0,
            'model_usage': {}
        }
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Procesar request y recopilar métricas"""
        self.metrics['total_requests'] += 1
        
        start_time = None
        model_name = None
        
        # Verificar si es una request de paginación
        if hasattr(request.state, 'pagination_params'):
            pagination_params = request.state.pagination_params
            model_name = getattr(request.state, 'model_name', None)
            
            self.metrics['pagination_requests'] += 1
            start_time = self._get_current_time()
            
            # Recopilar métricas de uso
            self._collect_usage_metrics(pagination_params, model_name)
        
        try:
            response = await call_next(request)
            
            # Si hubo un error, registrarlo
            if response.status_code >= 400:
                self.metrics['error_count'] += 1
            
            return response
            
        except Exception as e:
            self.metrics['error_count'] += 1
            logger.error(f"Error processing request: {e}")
            raise
        
        finally:
            # Calcular tiempo de procesamiento si corresponde
            if start_time:
                processing_time = self._get_current_time() - start_time
                self._record_processing_time(model_name, processing_time)
    
    def _collect_usage_metrics(self, pagination_params: PaginationParams, model_name: str):
        """Recopilar métricas de uso de paginación"""
        
        # Uso por modelo
        if model_name:
            self.metrics['model_usage'][model_name] = \
                self.metrics['model_usage'].get(model_name, 0) + 1
        
        # Distribución de tamaños de página
        page_size = pagination_params.page_size
        self.metrics['page_size_distribution'][page_size] = \
            self.metrics['page_size_distribution'].get(page_size, 0) + 1
        
        # Uso de filtros
        for field_name, filter_config in pagination_params.filters.items():
            operator = filter_config['operator'].value
            filter_key = f"{field_name}__{operator}"
            self.metrics['filter_usage'][filter_key] = \
                self.metrics['filter_usage'].get(filter_key, 0) + 1
        
        # Uso de ordenamiento
        for sort_field in pagination_params.sort:
            sort_key = f"{sort_field.field}_{sort_field.order.value}"
            self.metrics['sort_usage'][sort_key] = \
                self.metrics['sort_usage'].get(sort_key, 0) + 1
    
    def _record_processing_time(self, model_name: str, processing_time: float):
        """Registrar tiempo de procesamiento"""
        # Por simplicidad, solo registramos en logs por ahora
        # En una implementación real, se podría almacenar en una base de datos
        if processing_time > 1.0:  # Solo registrar si toma más de 1 segundo
            logger.warning(
                f"Slow query for model {model_name}: {processing_time:.2f}s"
            )
    
    def _get_current_time(self) -> float:
        """Obtener tiempo actual en segundos"""
        import time
        return time.time()
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """Obtener resumen de métricas"""
        total_reqs = self.metrics['total_requests']
        pagination_reqs = self.metrics['pagination_requests']
        
        return {
            'total_requests': total_reqs,
            'pagination_requests': pagination_reqs,
            'pagination_rate': pagination_reqs / total_reqs if total_reqs > 0 else 0,
            'error_rate': self.metrics['error_count'] / total_reqs if total_reqs > 0 else 0,
            'most_used_models': dict(sorted(
                self.metrics['model_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            'most_used_filters': dict(sorted(
                self.metrics['filter_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]),
            'popular_page_sizes': dict(sorted(
                self.metrics['page_size_distribution'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]),
            'sort_preferences': dict(sorted(
                self.metrics['sort_usage'].items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])
        }


class CORSHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware para agregar headers CORS optimizados para APIs paginadas
    
    Incluye información útil sobre límites de paginación y filtros disponibles.
    """
    
    def __init__(self, app: ASGIApp, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or ["*"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Procesar request y agregar headers CORS"""
        
        response = await call_next(request)
        
        # Headers CORS básicos
        response.headers["Access-Control-Allow-Origin"] = ", ".join(self.allowed_origins)
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, X-Model-Name, "
            "X-Filter-Format, X-Custom-Headers"
        )
        response.headers["Access-Control-Max-Age"] = "86400"
        
        # Headers informativos para APIs paginadas
        if hasattr(request.state, 'pagination_params'):
            pagination_params = request.state.pagination_params
            
            # Agregar información sobre límites
            response.headers["X-Max-Page-Size"] = str(pagination_params.max_page_size)
            response.headers["X-Default-Page-Size"] = str(pagination_params.default_page_size)
            
            # Agregar información sobre filtros disponibles
            if hasattr(request.state, 'model_name'):
                model_name = request.state.model_name
                available_filters = ModelFilterConfig.get_config(model_name)
                filter_fields = [f.field_name for f in available_filters]
                response.headers["X-Available-Filters"] = ", ".join(filter_fields)
            
            # Indicar si se aplicaron filtros
            if pagination_params.has_filters():
                response.headers["X-Filters-Applied"] = "true"
            else:
                response.headers["X-Filters-Applied"] = "false"
        
        return response


# Función de utilidad para configurar middleware en la aplicación
def setup_pagination_middleware(
    app,
    enable_auto_extraction: bool = True,
    enable_metrics: bool = True,
    enable_cors: bool = True,
    allowed_origins: list = None
):
    """
    Configurar middleware de paginación para la aplicación FastAPI
    
    Args:
        app: aplicación FastAPI
        enable_auto_extraction: habilitar extracción automática
        enable_metrics: habilitar recopilación de métricas
        enable_cors: habilitar headers CORS
        allowed_origins: orígenes permitidos para CORS
    """
    
    # Middleware de extracción automática (debe ser el primero)
    if enable_auto_extraction:
        app.add_middleware(
            QueryParamExtractionMiddleware,
            enable_auto_extraction=enable_auto_extraction,
            log_extractions=True
        )
    
    # Middleware de métricas
    if enable_metrics:
        app.add_middleware(PaginationMetricsMiddleware)
    
    # Middleware CORS
    if enable_cors:
        app.add_middleware(
            CORSHeadersMiddleware,
            allowed_origins=allowed_origins or ["*"]
        )
    
    logger.info("Pagination middleware configured successfully")