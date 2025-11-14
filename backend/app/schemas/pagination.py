"""
Pagination schemas for AI News Aggregator
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Union, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, validator, root_validator, field_serializer
from pydantic.generics import GenericModel


T = TypeVar('T')


class PaginationParams(BaseModel):
    """
    Base pagination parameters
    """
    page: int = Field(1, ge=1, description="Page number")
    per_page: int = Field(20, ge=1, le=100, description="Items per page")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field('desc', regex='^(asc|desc)$', description="Sort order")
    
    # Additional pagination options
    include_total: bool = Field(True, description="Include total count in response")
    max_per_page: int = Field(100, ge=1, le=1000, description="Maximum items per page")
    
    # Cursor-based pagination support
    cursor: Optional[str] = Field(None, description="Cursor for cursor-based pagination")
    cursor_field: Optional[str] = Field(None, description="Field to use for cursor pagination")
    
    @validator('per_page')
    def validate_per_page(cls, v, values):
        """Validate per_page against max_per_page"""
        max_per_page = values.get('max_per_page', 100)
        if v > max_per_page:
            raise ValueError(f'per_page cannot exceed {max_per_page}')
        return v
    
    @validator('page')
    def validate_page(cls, v):
        """Validate page number"""
        if v < 1:
            raise ValueError('page must be at least 1')
        if v > 10000:
            raise ValueError('page cannot exceed 10000')
        return v
    
    def get_offset(self) -> int:
        """Calculate offset for SQL queries"""
        return (self.page - 1) * self.per_page
    
    def get_limit(self) -> int:
        """Get limit for SQL queries"""
        return self.per_page


class CursorPaginationParams(BaseModel):
    """
    Cursor-based pagination parameters
    """
    cursor: Optional[str] = Field(None, description="Cursor token")
    limit: int = Field(20, ge=1, le=100, description="Number of items to return")
    sort_by: Optional[str] = Field(None, description="Field to sort by")
    sort_order: str = Field('desc', regex='^(asc|desc)$', description="Sort order")
    
    @validator('limit')
    def validate_limit(cls, v):
        """Validate limit bounds"""
        if v > 100:
            raise ValueError('limit cannot exceed 100')
        return v
    
    def get_sql_params(self) -> Dict[str, Any]:
        """Get parameters for SQL cursor pagination"""
        return {
            'limit': self.limit,
            'cursor': self.cursor,
            'sort_by': self.sort_by or 'created_at',
            'sort_order': self.sort_order
        }


class Meta(BaseModel):
    """
    Metadata for paginated responses
    """
    # Basic pagination info
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Items per page")
    total: Optional[int] = Field(None, description="Total number of items")
    total_pages: Optional[int] = Field(None, description="Total number of pages")
    
    # Navigation flags
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    is_first: bool = Field(..., description="Whether this is the first page")
    is_last: bool = Field(..., description="Whether this is the last page")
    
    # Current page info
    current_count: int = Field(..., ge=0, description="Number of items on current page")
    
    # Range info
    start_index: Optional[int] = Field(None, description="1-based index of first item")
    end_index: Optional[int] = Field(None, description="1-based index of last item")
    
    # Navigation links
    next_url: Optional[str] = Field(None, description="URL for next page")
    prev_url: Optional[str] = Field(None, description="URL for previous page")
    first_url: Optional[str] = Field(None, description="URL for first page")
    last_url: Optional[str] = Field(None, description="URL for last page")
    
    # Performance metrics
    query_time_ms: Optional[float] = Field(None, ge=0.0, description="Query execution time in milliseconds")
    cache_hit: Optional[bool] = Field(None, description="Whether response was served from cache")
    
    # Cursor info (for cursor-based pagination)
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    prev_cursor: Optional[str] = Field(None, description="Cursor for previous page")
    has_more: bool = Field(False, description="Whether there are more items")
    
    @validator('per_page', 'page', 'current_count')
    def validate_positive_integers(cls, v):
        """Validate positive integers"""
        if v < 0:
            raise ValueError('Value must be non-negative')
        return v
    
    @validator('total')
    def validate_total(cls, v, values):
        """Validate total is consistent with current page info"""
        if v is not None and v < 0:
            raise ValueError('Total cannot be negative')
        return v
    
    @validator('start_index', 'end_index')
    def validate_indices(cls, v, values):
        """Validate indices are valid"""
        if v is not None and v < 1:
            raise ValueError('Indices must be at least 1')
        return v
    
    @root_validator
    def validate_meta_consistency(cls, values):
        """Validate metadata consistency"""
        page = values.get('page', 1)
        per_page = values.get('per_page', 20)
        total = values.get('total')
        current_count = values.get('current_count', 0)
        total_pages = values.get('total_pages')
        
        # Calculate total_pages if not provided
        if total is not None and total_pages is None:
            total_pages = (total + per_page - 1) // per_page
            values['total_pages'] = total_pages
        
        # Calculate pagination flags
        if total is not None and total_pages is not None:
            values['has_next'] = page < total_pages
            values['has_prev'] = page > 1
            values['is_first'] = page == 1
            values['is_last'] = page >= total_pages
            
            # Calculate indices
            start_index = (page - 1) * per_page + 1
            end_index = min(start_index + current_count - 1, total)
            values['start_index'] = start_index
            values['end_index'] = end_index
        else:
            # For cursor-based pagination
            values['has_next'] = values.get('has_more', False)
            values['has_prev'] = values.get('prev_cursor') is not None
            values['is_first'] = not values.get('prev_cursor')
            values['is_last'] = not values.get('has_more')
            values['start_index'] = None
            values['end_index'] = None
        
        return values


class Links(BaseModel):
    """
    Navigation links for API responses
    """
    self: str = Field(..., description="URL for current page")
    first: Optional[str] = Field(None, description="URL for first page")
    last: Optional[str] = Field(None, description="URL for last page")
    next: Optional[str] = Field(None, description="URL for next page")
    prev: Optional[str] = Field(None, description="URL for previous page")
    
    # Additional navigation links
    related: Optional[str] = Field(None, description="URL for related resource")
    search: Optional[str] = Field(None, description="URL for search interface")


class PaginatedResponse(GenericModel, Generic[T]):
    """
    Generic paginated response schema
    """
    data: List[T] = Field(..., description="Paginated data")
    meta: Meta = Field(..., description="Pagination metadata")
    links: Optional[Links] = Field(None, description="Navigation links")
    
    # Additional response metadata
    message: Optional[str] = Field(None, description="Response message")
    status: str = Field('success', description="Response status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Error information (for error responses)
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Validation errors")
    
    class Config:
        # Enable generic type parsing
        smart_union = True
    
    @field_serializer('timestamp')
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize datetime to ISO format"""
        return value.isoformat()
    
    @classmethod
    def create(
        cls,
        data: List[T],
        total: Optional[int] = None,
        page: int = 1,
        per_page: int = 20,
        **kwargs
    ) -> 'PaginatedResponse[T]':
        """Create paginated response with calculated metadata"""
        current_count = len(data)
        
        # Calculate total_pages if total is provided
        total_pages = None
        if total is not None:
            total_pages = (total + per_page - 1) // per_page
        
        # Create metadata
        meta = Meta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=total_pages,
            current_count=current_count,
            **kwargs
        )
        
        return cls(
            data=data,
            meta=meta,
            **kwargs
        )
    
    @classmethod
    def create_cursor_based(
        cls,
        data: List[T],
        next_cursor: Optional[str] = None,
        prev_cursor: Optional[str] = None,
        has_more: bool = False,
        limit: int = 20,
        **kwargs
    ) -> 'PaginatedResponse[T]':
        """Create cursor-based paginated response"""
        meta = Meta(
            page=1,  # Not applicable for cursor pagination
            per_page=limit,
            total=None,  # Not available for cursor pagination
            total_pages=None,
            current_count=len(data),
            next_cursor=next_cursor,
            prev_cursor=prev_cursor,
            has_more=has_more,
            **kwargs
        )
        
        return cls(
            data=data,
            meta=meta,
            **kwargs
        )


class BulkResponse(BaseModel):
    """
    Response for bulk operations
    """
    success_count: int = Field(ge=0, description="Number of successful operations")
    error_count: int = Field(ge=0, description="Number of failed operations")
    total_count: int = Field(ge=0, description="Total number of operations")
    
    # Results
    results: List[Dict[str, Any]] = Field(default_factory=list, description="Operation results")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="Operation errors")
    
    # Metadata
    processing_time_ms: Optional[float] = Field(None, ge=0.0, description="Processing time in milliseconds")
    batch_id: Optional[str] = Field(None, description="Batch operation ID")
    
    @validator('total_count')
    def validate_counts(cls, v, values):
        """Validate total count consistency"""
        success_count = values.get('success_count', 0)
        error_count = values.get('error_count', 0)
        
        if success_count + error_count != v:
            raise ValueError('success_count + error_count must equal total_count')
        
        return v
    
    @validator('error_count', 'success_count')
    def validate_non_negative(cls, v):
        """Validate counts are non-negative"""
        if v < 0:
            raise ValueError('Counts cannot be negative')
        return v


class StreamResponse(BaseModel):
    """
    Response for streaming data
    """
    stream_id: str = Field(..., description="Stream identifier")
    status: str = Field(..., description="Stream status")
    total_items: Optional[int] = Field(None, description="Total items to stream")
    streamed_items: int = Field(0, ge=0, description="Items streamed so far")
    
    # Current data
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Current stream data")
    
    # Stream control
    is_complete: bool = Field(False, description="Whether streaming is complete")
    has_more: bool = Field(True, description="Whether more data is available")
    next_cursor: Optional[str] = Field(None, description="Cursor for next batch")
    
    # Performance metrics
    items_per_second: Optional[float] = Field(None, ge=0.0, description="Streaming rate")
    estimated_time_remaining: Optional[float] = Field(None, ge=0.0, description="Estimated remaining time in seconds")
    
    @validator('streamed_items')
    def validate_streamed_items(cls, v, values):
        """Validate streamed items count"""
        total_items = values.get('total_items')
        if total_items is not None and v > total_items:
            raise ValueError('streamed_items cannot exceed total_items')
        return v
    
    @validator('estimated_time_remaining')
    def validate_time_remaining(cls, v):
        """Validate time remaining is non-negative"""
        if v is not None and v < 0:
            raise ValueError('Estimated time remaining cannot be negative')
        return v


class ExportResponse(BaseModel):
    """
    Response for data export operations
    """
    export_id: str = Field(..., description="Export identifier")
    export_type: str = Field(..., description="Type of export")
    status: str = Field(..., description="Export status")
    
    # File information
    filename: Optional[str] = Field(None, description="Generated filename")
    file_size_bytes: Optional[int] = Field(None, ge=0, description="File size in bytes")
    file_format: Optional[str] = Field(None, description="Export format")
    download_url: Optional[str] = Field(None, description="Download URL")
    
    # Export metadata
    total_records: int = Field(ge=0, description="Total records exported")
    exported_records: int = Field(ge=0, description="Records exported so far")
    
    # Progress tracking
    progress_percentage: float = Field(0.0, ge=0.0, le=100.0, description="Export progress percentage")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    
    # Error handling
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    @field_serializer('estimated_completion')
    def serialize_datetime(self, value: Optional[datetime]) -> Optional[str]:
        """Serialize datetime to ISO format"""
        if value is None:
            return None
        return value.isoformat()
    
    @validator('progress_percentage')
    def validate_progress(cls, v):
        """Validate progress is between 0 and 100"""
        if not 0.0 <= v <= 100.0:
            raise ValueError('Progress must be between 0.0 and 100.0')
        return v
    
    @validator('exported_records')
    def validate_exported_records(cls, v, values):
        """Validate exported records count"""
        total_records = values.get('total_records', 0)
        if v > total_records:
            raise ValueError('exported_records cannot exceed total_records')
        return v


# Utility functions for pagination
def calculate_page_bounds(page: int, per_page: int, total: int) -> tuple[int, int, int, int]:
    """
    Calculate pagination bounds
    
    Returns:
        (start_index, end_index, total_pages, has_next, has_prev)
    """
    total_pages = (total + per_page - 1) // per_page
    start_index = (page - 1) * per_page + 1
    end_index = min(start_index + per_page - 1, total)
    has_next = page < total_pages
    has_prev = page > 1
    
    return start_index, end_index, total_pages, has_next, has_prev


def generate_cursor(values: List[Any], field: str = 'id') -> Optional[str]:
    """
    Generate cursor token from values
    """
    if not values:
        return None
    
    # Use last value as cursor
    cursor_value = values[-1]
    if hasattr(cursor_value, field):
        cursor_value = getattr(cursor_value, field)
    
    # Encode cursor value (simple base64 encoding for demo)
    import base64
    cursor_str = str(cursor_value)
    return base64.b64encode(cursor_str.encode()).decode()


def parse_cursor(cursor: str) -> str:
    """
    Parse cursor token back to value
    """
    import base64
    try:
        return base64.b64decode(cursor.encode()).decode()
    except Exception:
        return cursor


def get_pagination_info(page: int, per_page: int, total: int) -> Dict[str, Any]:
    """
    Get comprehensive pagination information
    """
    start_index, end_index, total_pages, has_next, has_prev = calculate_page_bounds(page, per_page, total)
    
    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'start_index': start_index,
        'end_index': end_index,
        'has_next': has_next,
        'has_prev': has_prev,
        'is_first': page == 1,
        'is_last': page >= total_pages,
        'current_count': min(per_page, total - start_index + 1) if total > 0 else 0
    }


def optimize_per_page(per_page: int, max_per_page: int = 100) -> int:
    """
    Optimize per_page parameter for performance
    """
    if per_page <= 0:
        return 20  # Default
    
    if per_page > max_per_page:
        return max_per_page
    
    # Suggest optimal per_page for common values
    optimal_values = [10, 20, 25, 50, 100]
    for optimal in optimal_values:
        if per_page <= optimal:
            return optimal
    
    return min(per_page, max_per_page)


def create_pagination_links(
    base_url: str,
    params: PaginationParams,
    total_pages: Optional[int] = None,
    query_params: Optional[Dict[str, Any]] = None
) -> Links:
    """
    Create pagination links for API responses
    """
    if query_params is None:
        query_params = {}
    
    # Create base query string
    base_params = {**query_params}
    
    # Current page link
    current_params = {**base_params, 'page': params.page, 'per_page': params.per_page}
    self_url = f"{base_url}?{urllib.parse.urlencode(current_params)}"
    
    links = Links(self=self_url)
    
    # First page link
    if params.page > 1:
        first_params = {**base_params, 'page': 1, 'per_page': params.per_page}
        links.first = f"{base_url}?{urllib.parse.urlencode(first_params)}"
    
    # Last page link
    if total_pages and params.page < total_pages:
        last_params = {**base_params, 'page': total_pages, 'per_page': params.per_page}
        links.last = f"{base_url}?{urllib.parse.urlencode(last_params)}"
    
    # Next page link
    if params.page < (total_pages or params.page + 1):
        next_params = {**base_params, 'page': params.page + 1, 'per_page': params.per_page}
        links.next = f"{base_url}?{urllib.parse.urlencode(next_params)}"
    
    # Previous page link
    if params.page > 1:
        prev_params = {**base_params, 'page': params.page - 1, 'per_page': params.per_page}
        links.prev = f"{base_url}?{urllib.parse.urlencode(prev_params)}"
    
    return links


# Import required for URL encoding
import urllib.parse