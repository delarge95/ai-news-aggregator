"""
Services package for AI News Aggregator

Este paquete contiene el service layer y factory pattern para el agregador de noticias.
Incluye clientes unificados para múltiples APIs de noticias con logging y error handling.
"""

from .news_service import (
    NewsService,
    NewsClient,
    NewsClientFactory,
    NewsClientError,
    RateLimitError,
    APIKeyError,
    news_service
)

# AI Processor imports
from .ai_processor import (
    SentimentAnalyzer,
    TopicClassifier,
    Summarizer,
    RelevanceScorer,
    ComprehensiveAnalyzer,
    AIProcessor,
    create_ai_processor,
    analyze_cost_breakdown,
    SentimentType,
    SentimentLabel,
    TopicCategory,
    SentimentResult,
    TopicResult,
    SummaryResult,
    RelevanceResult,
    AIAnalysisResult
)

# AI Monitoring System imports
from .ai_monitor import (
    AIMonitor,
    TaskMonitor,
    PerformanceMonitor,
    CostMonitor,
    ErrorAnalyzer,
    AlertManager,
    TaskStatus,
    AlertSeverity,
    TaskMetrics,
    PerformanceMetrics,
    CostMetrics,
    Alert,
    ai_monitor
)

# AI Monitoring Integration imports
from .ai_monitor_integration import (
    monitor_ai_task,
    monitor_api_call,
    monitor_context,
    integrate_with_existing_service,
    create_monitoring_middleware,
    monitor_batch_processing,
    get_task_analytics,
    MonitoringContext,
    calculate_batch_cost
)

# Legacy imports for backward compatibility
legacy_imports = []
try:
    from .newsapi_client import NewsAPIClient
    legacy_imports.append("NewsAPIClient")
except ImportError:
    pass

try:
    from .guardian_client import GuardianAPIClient
    legacy_imports.append("GuardianAPIClient")
except ImportError:
    pass

try:
    from .nytimes_client import NYTimesAPIClient
    legacy_imports.append("NYTimesAPIClient")
except ImportError:
    pass

__all__ = [
    # News service
    'NewsService',
    'NewsClient', 
    'NewsClientFactory',
    'NewsClientError',
    'RateLimitError',
    'APIKeyError',
    'news_service',
    # AI Processor
    'SentimentAnalyzer',
    'TopicClassifier',
    'Summarizer', 
    'RelevanceScorer',
    'ComprehensiveAnalyzer',
    'AIProcessor',
    'create_ai_processor',
    'analyze_cost_breakdown',
    'SentimentType',
    'SentimentLabel',
    'TopicCategory',
    'SentimentResult',
    'TopicResult',
    'SummaryResult',
    'RelevanceResult',
    'AIAnalysisResult',
    # AI Monitoring System
    'AIMonitor',
    'TaskMonitor',
    'PerformanceMonitor',
    'CostMonitor',
    'ErrorAnalyzer',
    'AlertManager',
    'TaskStatus',
    'AlertSeverity',
    'TaskMetrics',
    'PerformanceMetrics',
    'CostMetrics',
    'Alert',
    'ai_monitor',
    # AI Monitoring Integration
    'monitor_ai_task',
    'monitor_api_call',
    'monitor_context',
    'integrate_with_existing_service',
    'create_monitoring_middleware',
    'monitor_batch_processing',
    'get_task_analytics',
    'MonitoringContext',
    'calculate_batch_cost'
] + legacy_imports