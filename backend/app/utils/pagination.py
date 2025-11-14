"""
Sistema de Paginación y Filtrado Avanzado para AI News Aggregator

Este módulo implementa un sistema universal de paginación y filtrado que incluye:
- Clase PaginationParams para parámetros estándar
- Filtros configurables por modelo
- Validación automática de parámetros
- Sorting multi-campo
- Cursors para paginación eficiente
- Middleware para extracción automática de parámetros de query
"""

import base64
import json
import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import (
    Any, Dict, List, Optional, Tuple, Type, Union, Callable, Set
)
from urllib.parse import parse_qs, urlencode

from fastapi import Request, HTTPException
from sqlalchemy import Column, String, DateTime, Float, Integer
from sqlalchemy.orm import Query
from sqlalchemy.sql import func

logger = logging.getLogger(__name__)


class SortOrder(str, Enum):
    """Orden de clasificación"""
    ASC = "asc"
    DESC = "desc"


class FilterOperator(str, Enum):
    """Operadores de filtrado disponibles"""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    BETWEEN = "between"
    DATE_RANGE = "date_range"
    TEXT_SEARCH = "text_search"


@dataclass
class FilterConfig:
    """Configuración de filtro para un campo"""
    field_name: str
    field_type: type
    allowed_operators: List[FilterOperator]
    required: bool = False
    default_value: Any = None
    validation_func: Optional[Callable] = None
    search_fields: Optional[List[str]] = None  # Para búsqueda de texto


@dataclass 
class SortField:
    """Campo de ordenamiento"""
    field: str
    order: SortOrder = SortOrder.DESC
    priority: int = 0  # 0 = más importante


@dataclass
class PaginationResult:
    """Resultado de paginación"""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool
    next_cursor: Optional[str] = None
    prev_cursor: Optional[str] = None
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    sort_applied: List[SortField] = field(default_factory=list)


class ModelFilterConfig:
    """Configuración de filtros por modelo"""
    
    # Mapeo de modelos a sus configuraciones de filtro
    FILTER_CONFIGS = {
        'article': [
            FilterConfig('published_at', datetime, [FilterOperator.DATE_RANGE, FilterOperator.GREATER_THAN, FilterOperator.LESS_THAN]),
            FilterConfig('source_id', str, [FilterOperator.EQUALS, FilterOperator.IN, FilterOperator.NOT_IN]),
            FilterConfig('sentiment_label', str, [FilterOperator.EQUALS, FilterOperator.IN, FilterOperator.NOT_IN]),
            FilterConfig('sentiment_score', float, [FilterOperator.GREATER_THAN_EQUAL, FilterOperator.LESS_THAN_EQUAL, FilterOperator.BETWEEN]),
            FilterConfig('relevance_score', float, [FilterOperator.GREATER_THAN_EQUAL, FilterOperator.LESS_THAN_EQUAL, FilterOperator.BETWEEN]),
            FilterConfig('title', str, [FilterOperator.TEXT_SEARCH, FilterOperator.CONTAINS], search_fields=['title', 'content']),
            FilterConfig('topic_tags', str, [FilterOperator.CONTAINS, FilterOperator.IN]),
            FilterConfig('processing_status', str, [FilterOperator.EQUALS, FilterOperator.IN]),
            FilterConfig('created_at', datetime, [FilterOperator.DATE_RANGE]),
            FilterConfig('url', str, [FilterOperator.EQUALS, FilterOperator.CONTAINS]),
        ],
        'source': [
            FilterConfig('api_name', str, [FilterOperator.EQUALS, FilterOperator.IN]),
            FilterConfig('country', str, [FilterOperator.EQUALS, FilterOperator.CONTAINS]),
            FilterConfig('language', str, [FilterOperator.EQUALS, FilterOperator.CONTAINS]),
            FilterConfig('credibility_score', float, [FilterOperator.GREATER_THAN_EQUAL, FilterOperator.LESS_THAN_EQUAL]),
            FilterConfig('is_active', bool, [FilterOperator.EQUALS]),
            FilterConfig('name', str, [FilterOperator.TEXT_SEARCH, FilterOperator.CONTAINS], search_fields=['name']),
        ],
        'trending_topic': [
            FilterConfig('topic', str, [FilterOperator.TEXT_SEARCH, FilterOperator.CONTAINS]),
            FilterConfig('topic_category', str, [FilterOperator.EQUALS, FilterOperator.CONTAINS]),
            FilterConfig('trend_score', float, [FilterOperator.GREATER_THAN_EQUAL, FilterOperator.LESS_THAN_EQUAL]),
            FilterConfig('time_period', str, [FilterOperator.EQUALS, FilterOperator.IN]),
            FilterConfig('date_recorded', datetime, [FilterOperator.DATE_RANGE]),
        ],
        'analysis_task': [
            FilterConfig('task_type', str, [FilterOperator.EQUALS, FilterOperator.IN]),
            FilterConfig('status', str, [FilterOperator.EQUALS, FilterOperator.IN]),
            FilterConfig('priority', int, [FilterOperator.GREATER_THAN_EQUAL, FilterOperator.LESS_THAN_EQUAL]),
            FilterConfig('scheduled_at', datetime, [FilterOperator.DATE_RANGE]),
            FilterConfig('model_name', str, [FilterOperator.EQUALS, FilterOperator.CONTAINS]),
        ]
    }
    
    @classmethod
    def get_config(cls, model_name: str) -> List[FilterConfig]:
        """Obtener configuración de filtros para un modelo"""
        return cls.FILTER_CONFIGS.get(model_name.lower(), [])
    
    @classmethod
    def get_search_fields(cls, model_name: str) -> List[str]:
        """Obtener campos de búsqueda para un modelo"""
        search_fields = []
        for config in cls.get_config(model_name):
            if config.search_fields:
                search_fields.extend(config.search_fields)
        return list(set(search_fields))  # Eliminar duplicados


class CursorManager:
    """Gestor de cursores para paginación eficiente"""
    
    @staticmethod
    def encode_cursor(data: Dict[str, Any]) -> str:
        """Codificar datos en cursor"""
        try:
            json_str = json.dumps(data, default=str)
            return base64.b64encode(json_str.encode()).decode()
        except Exception as e:
            logger.error(f"Error codificando cursor: {e}")
            return ""
    
    @staticmethod
    def decode_cursor(cursor: str) -> Dict[str, Any]:
        """Decodificar cursor a datos"""
        try:
            json_str = base64.b64decode(cursor.encode()).decode()
            return json.loads(json_str)
        except Exception as e:
            logger.error(f"Error decodificando cursor: {e}")
            return {}


class PaginationParams:
    """Parámetros de paginación y filtrado"""
    
    def __init__(
        self,
        request: Request,
        model_name: str,
        default_page_size: int = 20,
        max_page_size: int = 100
    ):
        self.request = request
        self.model_name = model_name
        self.default_page_size = default_page_size
        self.max_page_size = max_page_size
        
        # Extraer parámetros de la query
        self._extract_query_params()
        
        # Validar parámetros
        self._validate_params()
    
    def _extract_query_params(self):
        """Extraer parámetros de la query string"""
        query_params = self.request.query_params
        
        # Paginación básica
        self.page = int(query_params.get('page', 1))
        self.page_size = int(query_params.get('page_size', self.default_page_size))
        self.limit = int(query_params.get('limit', self.page_size))
        self.offset = int(query_params.get('offset', 0))
        
        # Paginación por cursor
        self.cursor = query_params.get('cursor')
        
        # Ordenamiento
        sort_param = query_params.get('sort', '')
        self.sort = self._parse_sort_param(sort_param)
        
        # Filtros
        self.filters = self._extract_filters(query_params)
        
        # Búsqueda de texto
        self.search = query_params.get('search', '').strip()
        
        # Campos a incluir/excluir
        self.fields = query_params.get('fields', '').split(',') if query_params.get('fields') else []
        self.exclude_fields = query_params.get('exclude', '').split(',') if query_params.get('exclude') else []
    
    def _parse_sort_param(self, sort_param: str) -> List[SortField]:
        """Parsear parámetro de ordenamiento"""
        if not sort_param:
            # Ordenamiento por defecto basado en el modelo
            return self._get_default_sort()
        
        sort_fields = []
        for field_spec in sort_param.split(','):
            field_spec = field_spec.strip()
            if not field_spec:
                continue
                
            if field_spec.startswith('-'):
                field = field_spec[1:]
                order = SortOrder.DESC
            else:
                field = field_spec
                order = SortOrder.ASC
            
            sort_fields.append(SortField(field=field, order=order))
        
        return sort_fields
    
    def _extract_filters(self, query_params) -> Dict[str, Dict[str, Any]]:
        """Extraer filtros de los parámetros"""
        filters = {}
        model_configs = ModelFilterConfig.get_config(self.model_name)
        
        for config in model_configs:
            # Filtro directo (ej: sentiment=positive)
            if config.field_name in query_params:
                value = query_params[config.field_name]
                filters[config.field_name] = {
                    'operator': FilterOperator.EQUALS,
                    'value': self._validate_filter_value(config, value)
                }
            
            # Filtros con operador específico (ej: sentiment__in=positive,neutral)
            for operator in config.allowed_operators:
                param_name = f"{config.field_name}__{operator.value}"
                if param_name in query_params:
                    value = query_params[param_name]
                    filters[config.field_name] = {
                        'operator': operator,
                        'value': self._validate_filter_value(config, value)
                    }
        
        return filters
    
    def _validate_filter_value(self, config: FilterConfig, value: str) -> Any:
        """Validar y convertir valor de filtro"""
        if config.validation_func:
            return config.validation_func(value)
        
        # Conversión básica por tipo
        if config.field_type == datetime:
            try:
                # Soportar múltiples formatos de fecha
                formats = ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']
                for fmt in formats:
                    try:
                        return datetime.strptime(value, fmt)
                    except ValueError:
                        continue
                raise ValueError(f"Formato de fecha no soportado: {value}")
            except Exception:
                raise ValueError(f"Fecha inválida: {value}")
        
        elif config.field_type == int:
            try:
                return int(value)
            except ValueError:
                raise ValueError(f"Entero inválido: {value}")
        
        elif config.field_type == float:
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"Flotante inválido: {value}")
        
        elif config.field_type == bool:
            return value.lower() in ['true', '1', 'yes', 'on']
        
        elif config.field_type == str:
            return value
        
        else:
            return value
    
    def _get_default_sort(self) -> List[SortField]:
        """Obtener ordenamiento por defecto según el modelo"""
        default_sorts = {
            'article': [SortField('published_at', SortOrder.DESC)],
            'source': [SortField('name', SortOrder.ASC)],
            'trending_topic': [SortField('trend_score', SortOrder.DESC)],
            'analysis_task': [SortField('scheduled_at', SortOrder.DESC)]
        }
        return default_sorts.get(self.model_name, [SortField('created_at', SortOrder.DESC)])
    
    def _validate_params(self):
        """Validar parámetros"""
        # Validar página
        if self.page < 1:
            raise HTTPException(status_code=400, detail="Page debe ser mayor a 0")
        
        # Validar tamaño de página
        if self.page_size < 1:
            raise HTTPException(status_code=400, detail="Page size debe ser mayor a 0")
        
        if self.page_size > self.max_page_size:
            raise HTTPException(
                status_code=400, 
                detail=f"Page size no puede exceder {self.max_page_size}"
            )
        
        # Validar filtros
        self._validate_filters()
        
        # Validar campos de ordenamiento
        self._validate_sort_fields()
    
    def _validate_filters(self):
        """Validar filtros aplicados"""
        model_configs = ModelFilterConfig.get_config(self.model_name)
        allowed_fields = {config.field_name for config in model_configs}
        
        for field_name in self.filters.keys():
            if field_name not in allowed_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Campo de filtro no permitido: {field_name}"
                )
    
    def _validate_sort_fields(self):
        """Validar campos de ordenamiento"""
        # Por ahora, permitir cualquier campo. En una implementación real,
        # se debería validar contra los campos del modelo
        pass
    
    def has_filters(self) -> bool:
        """Verificar si hay filtros aplicados"""
        return bool(self.filters or self.search)
    
    def has_sort(self) -> bool:
        """Verificar si hay ordenamiento personalizado"""
        default_sort = self._get_default_sort()
        return self.sort != default_sort


class QueryBuilder:
    """Constructor de consultas SQLAlchemy con filtros y ordenamiento"""
    
    @staticmethod
    def apply_filters(query: Query, model, filters: Dict[str, Dict[str, Any]]) -> Query:
        """Aplicar filtros a la consulta"""
        for field_name, filter_config in filters.items():
            operator = filter_config['operator']
            value = filter_config['value']
            
            # Obtener la columna del modelo
            if hasattr(model, field_name):
                column = getattr(model, field_name)
            else:
                logger.warning(f"Campo {field_name} no encontrado en modelo {model.__name__}")
                continue
            
            # Aplicar operador
            if operator == FilterOperator.EQUALS:
                query = query.filter(column == value)
            
            elif operator == FilterOperator.NOT_EQUALS:
                query = query.filter(column != value)
            
            elif operator == FilterOperator.GREATER_THAN:
                query = query.filter(column > value)
            
            elif operator == FilterOperator.GREATER_THAN_EQUAL:
                query = query.filter(column >= value)
            
            elif operator == FilterOperator.LESS_THAN:
                query = query.filter(column < value)
            
            elif operator == FilterOperator.LESS_THAN_EQUAL:
                query = query.filter(column <= value)
            
            elif operator == FilterOperator.CONTAINS:
                query = query.filter(column.contains(value))
            
            elif operator == FilterOperator.NOT_CONTAINS:
                query = query.filter(~column.contains(value))
            
            elif operator == FilterOperator.IN:
                if isinstance(value, str):
                    value = value.split(',')
                query = query.filter(column.in_(value))
            
            elif operator == FilterOperator.NOT_IN:
                if isinstance(value, str):
                    value = value.split(',')
                query = query.filter(~column.in_(value))
            
            elif operator == FilterOperator.BETWEEN:
                if isinstance(value, str):
                    value = value.split(',')
                if len(value) == 2:
                    query = query.filter(column.between(value[0], value[1]))
            
            elif operator == FilterOperator.DATE_RANGE:
                # Manejar rango de fechas (desde,hasta)
                if isinstance(value, str):
                    value = value.split(',')
                if len(value) >= 1 and value[0]:
                    query = query.filter(column >= value[0])
                if len(value) >= 2 and value[1]:
                    query = query.filter(column <= value[1])
            
            elif operator == FilterOperator.TEXT_SEARCH:
                # Búsqueda de texto en múltiples campos
                search_fields = ModelFilterConfig.get_search_fields(model.__name__.lower())
                search_conditions = []
                
                for field in search_fields:
                    if hasattr(model, field):
                        search_column = getattr(model, field)
                        search_conditions.append(search_column.ilike(f"%{value}%"))
                
                if search_conditions:
                    from sqlalchemy import or_
                    query = query.filter(or_(*search_conditions))
        
        return query
    
    @staticmethod
    def apply_sort(query: Query, model, sort_fields: List[SortField]) -> Query:
        """Aplicar ordenamiento a la consulta"""
        for sort_field in sort_fields:
            if hasattr(model, sort_field.field):
                column = getattr(model, sort_field.field)
                if sort_field.order == SortOrder.ASC:
                    query = query.order_by(column.asc())
                else:
                    query = query.order_by(column.desc())
        
        return query
    
    @staticmethod
    def apply_text_search(query: Query, model, search_term: str) -> Query:
        """Aplicar búsqueda de texto"""
        if not search_term.strip():
            return query
        
        search_fields = ModelFilterConfig.get_search_fields(model.__name__.lower())
        search_conditions = []
        
        for field in search_fields:
            if hasattr(model, field):
                search_column = getattr(model, field)
                search_conditions.append(search_column.ilike(f"%{search_term}%"))
        
        if search_conditions:
            from sqlalchemy import or_
            query = query.filter(or_(*search_conditions))
        
        return query
    
    @staticmethod
    def apply_cursor_pagination(
        query: Query, 
        model, 
        cursor: str, 
        sort_fields: List[SortField]
    ) -> Tuple[Query, Dict[str, Any]]:
        """Aplicar paginación por cursor"""
        if not cursor:
            return query, {}
        
        try:
            cursor_data = CursorManager.decode_cursor(cursor)
            if not cursor_data:
                return query, {}
            
            # Construir condiciones basadas en el cursor
            conditions = []
            for field_name, field_value in cursor_data.items():
                if hasattr(model, field_name):
                    column = getattr(model, field_name)
                    
                    # Determinar el operador basado en la dirección del ordenamiento
                    sort_config = next(
                        (s for s in sort_fields if s.field == field_name), 
                        None
                    )
                    
                    if sort_config and sort_config.order == SortOrder.DESC:
                        # Para ordenamiento DESC, usamos <
                        conditions.append(column < field_value)
                    else:
                        # Para ordenamiento ASC, usamos >
                        conditions.append(column > field_value)
            
            if conditions:
                from sqlalchemy import and_
                query = query.filter(and_(*conditions))
        
        except Exception as e:
            logger.error(f"Error aplicando cursor: {e}")
        
        return query, cursor_data
    
    @staticmethod
    def build_cursor_data(
        items: List[Any], 
        sort_fields: List[SortField]
    ) -> Optional[str]:
        """Construir cursor a partir de los últimos elementos"""
        if not items or not sort_fields:
            return None
        
        # Usar el último elemento para construir el cursor
        last_item = items[-1]
        cursor_data = {}
        
        for sort_field in sort_fields:
            field_value = getattr(last_item, sort_field.field, None)
            if field_value is not None:
                cursor_data[sort_field.field] = field_value
        
        if cursor_data:
            return CursorManager.encode_cursor(cursor_data)
        
        return None


class PaginationService:
    """Servicio principal de paginación"""
    
    def __init__(self):
        self.cursor_manager = CursorManager()
        self.query_builder = QueryBuilder()
    
    def paginate_query(
        self,
        query: Query,
        model: Type,
        pagination_params: PaginationParams,
        additional_filters: Optional[Dict[str, Any]] = None
    ) -> PaginationResult:
        """Ejecutar paginación completa"""
        
        # Aplicar filtros
        if pagination_params.filters or additional_filters:
            # Combinar filtros de parámetros y filtros adicionales
            all_filters = dict(pagination_params.filters)
            if additional_filters:
                all_filters.update(additional_filters)
            
            query = self.query_builder.apply_filters(query, model, all_filters)
        
        # Aplicar búsqueda de texto
        if pagination_params.search:
            query = self.query_builder.apply_text_search(query, model, pagination_params.search)
        
        # Contar total antes de paginar
        total = query.count()
        
        # Aplicar paginación por cursor si está disponible
        if pagination_params.cursor:
            query, cursor_data = self.query_builder.apply_cursor_pagination(
                query, model, pagination_params.cursor, pagination_params.sort
            )
        else:
            cursor_data = {}
        
        # Aplicar ordenamiento
        query = self.query_builder.apply_sort(query, model, pagination_params.sort)
        
        # Aplicar offset y limit para paginación tradicional
        if not pagination_params.cursor:
            query = query.offset(pagination_params.offset).limit(pagination_params.limit)
        
        # Ejecutar consulta
        items = query.all()
        
        # Calcular metadatos de paginación
        page = pagination_params.page
        page_size = pagination_params.page_size
        total_pages = math.ceil(total / page_size) if page_size > 0 else 0
        
        # Construir cursores
        next_cursor = None
        prev_cursor = None
        
        if pagination_params.cursor:
            # Para paginación por cursor
            next_cursor = self.query_builder.build_cursor_data(items, pagination_params.sort)
        else:
            # Para paginación tradicional
            if page < total_pages:
                # Construir cursor para la siguiente página
                cursor_data = {'page': page + 1, 'page_size': page_size}
                next_cursor = self.cursor_manager.encode_cursor(cursor_data)
            
            if page > 1:
                # Construir cursor para la página anterior
                cursor_data = {'page': page - 1, 'page_size': page_size}
                prev_cursor = self.cursor_manager.encode_cursor(cursor_data)
        
        # Construir respuesta
        items_dict = []
        for item in items:
            item_dict = {
                'id': str(getattr(item, 'id', '')),
                'created_at': getattr(item, 'created_at', None),
                'updated_at': getattr(item, 'updated_at', None),
            }
            
            # Agregar todos los atributos del modelo
            for column in model.__table__.columns:
                field_name = column.name
                value = getattr(item, field_name, None)
                
                # Manejar tipos especiales
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'isoformat'):  # UUID, etc.
                    value = str(value)
                
                item_dict[field_name] = value
            
            # Filtrar campos según configuración
            if pagination_params.fields:
                filtered_item = {}
                for field in pagination_params.fields:
                    if field in item_dict:
                        filtered_item[field] = item_dict[field]
                item_dict = filtered_item
            
            if pagination_params.exclude_fields:
                for field in pagination_params.exclude_fields:
                    item_dict.pop(field, None)
            
            items_dict.append(item_dict)
        
        return PaginationResult(
            items=items_dict,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            filters_applied={**pagination_params.filters, **(additional_filters or {})},
            sort_applied=pagination_params.sort
        )
    
    def create_query_builder_url(
        self,
        base_url: str,
        pagination_params: PaginationParams,
        **additional_params
    ) -> str:
        """Crear URL con parámetros de consulta"""
        params = {}
        
        # Agregar parámetros de paginación
        if not pagination_params.cursor:
            params['page'] = pagination_params.page
            params['page_size'] = pagination_params.page_size
        
        # Agregar ordenamiento
        if pagination_params.sort:
            sort_str = ','.join([
                f"-{s.field}" if s.order == SortOrder.DESC else s.field
                for s in pagination_params.sort
            ])
            params['sort'] = sort_str
        
        # Agregar filtros
        for field_name, filter_config in pagination_params.filters.items():
            if filter_config['operator'] == FilterOperator.EQUALS:
                params[field_name] = str(filter_config['value'])
            else:
                param_name = f"{field_name}__{filter_config['operator'].value}"
                params[param_name] = str(filter_config['value'])
        
        # Agregar búsqueda
        if pagination_params.search:
            params['search'] = pagination_params.search
        
        # Agregar parámetros adicionales
        params.update(additional_params)
        
        # Construir URL
        query_string = urlencode(params)
        return f"{base_url}?{query_string}" if query_string else base_url


# Instancia global del servicio
pagination_service = PaginationService()


# Funciones de utilidad para usar en endpoints
def get_pagination_params(
    request: Request,
    model_name: str,
    default_page_size: int = 20,
    max_page_size: int = 100
) -> PaginationParams:
    """Función helper para obtener parámetros de paginación"""
    return PaginationParams(
        request=request,
        model_name=model_name,
        default_page_size=default_page_size,
        max_page_size=max_page_size
    )


def paginate_response(pagination_result: PaginationResult) -> Dict[str, Any]:
    """Formatear resultado de paginación para respuesta API"""
    return {
        'status': 'success',
        'data': pagination_result.items,
        'pagination': {
            'total': pagination_result.total,
            'page': pagination_result.page,
            'page_size': pagination_result.page_size,
            'total_pages': pagination_result.total_pages,
            'has_next': pagination_result.has_next,
            'has_prev': pagination_result.has_prev,
            'next_cursor': pagination_result.next_cursor,
            'prev_cursor': pagination_result.prev_cursor
        },
        'filters_applied': pagination_result.filters_applied,
        'sort_applied': [
            {'field': s.field, 'order': s.order.value} 
            for s in pagination_result.sort_applied
        ]
    }