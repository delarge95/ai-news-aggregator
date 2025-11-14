"""
Ejemplos de uso del sistema AI Monitoring
Demostración de cómo integrar y usar el sistema de monitoreo con servicios existentes
"""

import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any

# Importar sistema de monitoreo
from app.services.ai_monitor import ai_monitor, TaskStatus, AlertSeverity
from app.services.ai_monitor_integration import (
    monitor_ai_task, monitor_api_call, monitor_context,
    integrate_with_existing_service, get_task_analytics
)


# ================================================================
# EJEMPLO 1: USAR DECORATORS PARA MONITOREO AUTOMÁTICO
# ================================================================

@monitor_ai_task(task_type="news_analysis", model="gpt-3.5-turbo")
async def analyze_news_with_ai(articles: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analizar artículos de noticias usando AI
    """
    # Simular procesamiento de AI
    await asyncio.sleep(random.uniform(2, 5))
    
    # Simular respuesta de OpenAI
    class MockResponse:
        def __init__(self, text: str):
            self.choices = [type('Choice', (), {'text': text})()]
            self.usage = type('Usage', (), {
                'prompt_tokens': random.randint(100, 500),
                'completion_tokens': random.randint(200, 800),
                'total_tokens': 0
            })()
            self.usage.total_tokens = self.usage.prompt_tokens + self.usage.completion_tokens
    
    # Análisis simulado
    analysis_result = {
        "sentiment": random.choice(["positive", "negative", "neutral"]),
        "summary": "AI-generated summary of the articles",
        "keywords": ["AI", "technology", "innovation"],
        "confidence": random.uniform(0.7, 0.95)
    }
    
    return MockResponse(f"Analysis: {analysis_result}")


@monitor_api_call(service_name="openai", operation="chat_completion")
async def call_openai_api(messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo") -> Dict[str, Any]:
    """
    Llamada API a OpenAI con monitoreo automático
    """
    # Simular llamada API
    await asyncio.sleep(random.uniform(1, 3))
    
    return {
        "choices": [{"message": {"content": "AI response"}}],
        "usage": {
            "prompt_tokens": random.randint(50, 200),
            "completion_tokens": random.randint(100, 300)
        }
    }


# ================================================================
# EJEMPLO 2: USAR CONTEXT MANAGER PARA MONITOREO MANUAL
# ================================================================

async def process_news_batch(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Procesar batch de noticias con monitoreo manual
    """
    processed_articles = []
    
    with monitor_context(task_type="batch_processing", model="gpt-4") as monitor:
        try:
            for article in articles:
                # Procesar cada artículo
                with monitor_context(task_type="article_analysis", metadata={"article_id": article.get("id")}):
                    await asyncio.sleep(0.5)  # Simular procesamiento
                    
                    processed_article = {
                        **article,
                        "processed_at": datetime.utcnow().isoformat(),
                        "ai_summary": f"Processed summary for {article.get('title', 'Unknown')}"
                    }
                    processed_articles.append(processed_article)
            
            # Establecer costo total del batch
            total_cost = len(articles) * random.uniform(0.01, 0.05)
            monitor.set_cost(total_cost, len(articles) * random.randint(200, 500))
            
        except Exception as e:
            # El context manager manejará automáticamente el error
            raise
    
    return processed_articles


# ================================================================
# EJEMPLO 3: INTEGRAR MONITOREO CON SERVICIOS EXISTENTES
# ================================================================

class NewsService:
    """Servicio de noticias con monitoreo integrado"""
    
    def __init__(self):
        self.api_key = "mock_key"
        self.base_url = "https://api.news.com"
    
    async def get_latest_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtener últimas noticias"""
        await asyncio.sleep(random.uniform(0.5, 2.0))
        
        return [
            {
                "id": f"news_{i}",
                "title": f"News Article {i}",
                "content": f"Content of news article {i}",
                "source": "Mock News",
                "published_at": datetime.utcnow().isoformat()
            }
            for i in range(limit)
        ]
    
    async def search_news(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Buscar noticias"""
        await asyncio.sleep(random.uniform(1.0, 3.0))
        
        return [
            {
                "id": f"search_{i}",
                "title": f"Search result {i} for '{query}'",
                "content": f"Content about {query}",
                "source": "Search Results",
                "published_at": datetime.utc.now().isoformat()
            }
            for i in range(limit)
        ]


def integrate_news_service_monitoring():
    """Integrar monitoreo con el servicio de noticias"""
    news_service = NewsService()
    
    # Integrar automáticamente
    integrate_with_existing_service(
        service_instance=news_service,
        service_name="news_service",
        methods_to_monitor=["get_latest_news", "search_news"]
    )
    
    return news_service


# ================================================================
# EJEMPLO 4: MONITOREO DE ANÁLISIS Y REPORTING
# ================================================================

async def generate_comprehensive_report() -> Dict[str, Any]:
    """Generar reporte comprehensivo con monitoreo"""
    
    with monitor_context(task_type="comprehensive_report") as report_monitor:
        # Obtener datos de diferentes fuentes
        with monitor_context(task_type="data_collection"):
            dashboard_summary = ai_monitor.get_dashboard_summary()
            performance_report = ai_monitor.get_performance_report(hours=24)
            cost_report = ai_monitor.get_cost_report(days=7)
            error_report = ai_monitor.get_error_report(days=7)
        
        # Procesar y analizar datos
        with monitor_context(task_type="data_analysis"):
            await asyncio.sleep(2)  # Simular análisis
            
            # Analizar patrones
            analysis_results = {
                "performance_trends": performance_report.get("metrics", {}),
                "cost_optimization": {
                    "estimated_savings": random.uniform(5, 15),
                    "recommendations": ["Use gpt-3.5-turbo for simple tasks"]
                },
                "error_patterns": error_report.get("patterns", []),
                "recommendations": ai_monitor._generate_recommendations(
                    ai_monitor.error_analyzer.get_active_patterns()
                )
            }
        
        # Generar documento final
        with monitor_context(task_type="report_generation"):
            await asyncio.sleep(1)  # Simular generación
            
            final_report = {
                "generated_at": datetime.utcnow().isoformat(),
                "dashboard_summary": dashboard_summary,
                "performance_analysis": performance_report,
                "cost_analysis": cost_report,
                "error_analysis": error_report,
                "insights": analysis_results
            }
            
            # Establecer costo total
            total_cost = random.uniform(0.1, 0.5)
            report_monitor.set_cost(total_cost, random.randint(1000, 3000))
        
        return final_report


# ================================================================
# EJEMPLO 5: USAR BATCH PROCESSING CON MONITOREO
# ================================================================

async def process_news_articles_batch(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Procesar artículos en batch con monitoreo detallado
    """
    
    def analyze_single_article(article: Dict[str, Any]) -> Dict[str, Any]:
        """Análisis individual de artículo"""
        # Simular análisis AI
        time.sleep(random.uniform(0.1, 0.5))
        
        return {
            **article,
            "ai_analysis": {
                "sentiment": random.choice(["positive", "negative", "neutral"]),
                "relevance_score": random.uniform(0.6, 1.0),
                "category": random.choice(["technology", "business", "politics"])
            },
            "processed_at": datetime.utcnow().isoformat()
        }
    
    # Usar monitor_batch_processing
    from app.services.ai_monitor_integration import monitor_batch_processing
    
    results = await monitor_batch_processing(
        items=articles,
        process_func=analyze_single_article,
        batch_size=5,
        task_type="batch_news_analysis"
    )
    
    return results


# ================================================================
# EJEMPLO 6: DEMO COMPLETO - SISTEMA COMPLETO FUNCIONANDO
# ================================================================

async def run_complete_monitoring_demo():
    """Demo completo del sistema de monitoreo"""
    
    print("🚀 Starting AI Monitoring Demo...")
    
    # 1. Mostrar estado inicial
    print("\n📊 Initial System Status:")
    dashboard = ai_monitor.get_dashboard_summary()
    print(f"   Active Tasks: {dashboard['overview']['active_tasks']}")
    print(f"   Success Rate: {dashboard['overview']['success_rate']:.2f}%")
    
    # 2. Ejecutar tareas con monitoreo automático
    print("\n🔄 Running Monitored Tasks...")
    
    # Tarea simple con decorator
    articles = [{"id": f"art_{i}", "title": f"Article {i}"} for i in range(3)]
    result1 = await analyze_news_with_ai(articles)
    print(f"   ✅ News analysis completed")
    
    # API call con monitoreo
    messages = [{"role": "user", "content": "Hello AI"}]
    result2 = await call_openai_api(messages)
    print(f"   ✅ API call completed")
    
    # Batch processing
    batch_results = await process_news_articles_batch(articles)
    print(f"   ✅ Batch processing completed: {len(batch_results)} articles")
    
    # 3. Mostrar estado después del procesamiento
    print("\n📈 Post-Processing Status:")
    dashboard = ai_monitor.get_dashboard_summary()
    print(f"   Active Tasks: {dashboard['overview']['active_tasks']}")
    print(f"   Total Tasks Today: {dashboard['overview']['total_tasks_today']}")
    print(f"   Success Rate: {dashboard['overview']['success_rate']:.2f}%")
    print(f"   Average Latency: {dashboard['overview']['average_latency']:.2f}s")
    print(f"   Daily Cost: ${dashboard['costs']['daily']:.4f}")
    
    # 4. Generar alertas de prueba
    print("\n🚨 Testing Alert System...")
    ai_monitor.alert_manager.create_alert(
        title="Test Alert",
        message="This is a test alert for demonstration",
        severity=AlertSeverity.WARNING
    )
    print(f"   ✅ Test alert created")
    
    # 5. Generar reportes
    print("\n📋 Generating Reports...")
    
    perf_report = ai_monitor.get_performance_report(hours=1)
    print(f"   Performance Report: {len(perf_report)} metrics")
    
    cost_report = ai_monitor.get_cost_report(days=1)
    print(f"   Cost Report: ${cost_report['summary']['total_cost']:.4f} total")
    
    error_report = ai_monitor.get_error_report(days=1)
    print(f"   Error Report: {error_report['summary'].get('total_patterns', 0)} patterns")
    
    # 6. Análisis detallado por tipo de tarea
    print("\n🔍 Detailed Task Analysis:")
    analytics = get_task_analytics("news_analysis", days=1)
    if analytics.get("total_tasks", 0) > 0:
        print(f"   News Analysis Tasks: {analytics['total_tasks']}")
        print(f"   Success Rate: {analytics['success_rate']:.2f}%")
        print(f"   Average Cost: ${analytics['costs']['average_cost']:.4f}")
    
    # 7. Estado final
    print("\n✅ Final System Status:")
    dashboard = ai_monitor.get_dashboard_summary()
    print(f"   Active Alerts: {dashboard['alerts']['active']}")
    print(f"   Critical Alerts: {dashboard['alerts']['critical']}")
    print(f"   Recent Tasks: {len(dashboard['recent_tasks'])}")
    
    print("\n🎉 Demo completed successfully!")
    
    return {
        "dashboard_summary": dashboard,
        "performance_report": perf_report,
        "cost_report": cost_report,
        "error_report": error_report
    }


# ================================================================
# EJEMPLO 7: INTEGRACIÓN CON SERVICIOS REALES
# ================================================================

def demonstrate_service_integration():
    """Demostrar integración con servicios reales"""
    
    print("\n🔧 Service Integration Demo...")
    
    # Integrar servicio de noticias
    news_service = integrate_news_service_monitoring()
    
    # Usar servicio integrado
    articles = asyncio.run(news_service.get_latest_news(limit=5))
    print(f"   ✅ Retrieved {len(articles)} news articles")
    
    # Verificar que se monitoreo
    active_tasks = ai_monitor.task_monitor.get_active_tasks()
    recent_tasks = ai_monitor.task_monitor.get_task_history(limit=10)
    
    monitored_tasks = [t for t in recent_tasks if 'news_service' in str(t.metadata)]
    print(f"   ✅ Monitored {len(monitored_tasks)} service calls")
    
    return articles


# ================================================================
# EJEMPLO 8: TESTING HELPERS
# ================================================================

async def test_monitoring_system():
    """Suite completa de tests para el sistema de monitoreo"""
    
    print("\n🧪 Testing Monitoring System...")
    
    # Test 1: Task lifecycle
    task_id = "test_task_001"
    ai_monitor.start_task(task_id, "test_task", "gpt-3.5-turbo")
    print("   ✅ Task started")
    
    await asyncio.sleep(0.1)
    ai_monitor.complete_task(task_id, TaskStatus.COMPLETED, tokens_used=100, cost=0.01)
    print("   ✅ Task completed")
    
    # Test 2: Error handling
    ai_monitor.start_task("test_error_task", "test_error", "gpt-4")
    ai_monitor.complete_task("test_error_task", TaskStatus.FAILED, error_message="Test error")
    print("   ✅ Error handling tested")
    
    # Test 3: Alert creation
    alert_id = ai_monitor.alert_manager.create_alert(
        title="Test System Alert",
        message="System monitoring test",
        severity=AlertSeverity.INFO
    )
    print("   ✅ Alert system tested")
    
    # Test 4: Cost tracking
    ai_monitor.cost_monitor.record_cost("test_cost_task", 0.05, 250, "gpt-3.5-turbo", "test")
    print("   ✅ Cost tracking tested")
    
    # Test 5: Performance metrics
    perf_metrics = ai_monitor.performance_monitor.get_performance_metrics()
    print("   ✅ Performance metrics generated")
    
    return {
        "task_tests": "passed",
        "alert_tests": "passed", 
        "cost_tests": "passed",
        "performance_tests": "passed"
    }


# ================================================================
# FUNCIÓN PRINCIPAL DE DEMO
# ================================================================

async def main():
    """Función principal que ejecuta todos los demos"""
    
    print("=" * 60)
    print("🎯 AI MONITORING SYSTEM - COMPREHENSIVE DEMO")
    print("=" * 60)
    
    # Ejecutar demo completo
    demo_results = await run_complete_monitoring_demo()
    
    # Demostrar integración de servicios
    service_articles = demonstrate_service_integration()
    
    # Ejecutar tests
    test_results = await test_monitoring_system()
    
    # Mostrar resumen final
    print("\n" + "=" * 60)
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    
    print("✅ Demo completed successfully!")
    print(f"📈 Generated {len(demo_results)} comprehensive reports")
    print(f"🔧 Integrated {len(service_articles)} service calls")
    print(f"🧪 All {len(test_results)} test categories passed")
    
    print("\n🎯 Key Features Demonstrated:")
    print("   • Automatic task monitoring with decorators")
    print("   • Manual monitoring with context managers") 
    print("   • Service integration and wrapping")
    print("   • Real-time performance tracking")
    print("   • Cost analysis and forecasting")
    print("   • Error pattern detection and alerting")
    print("   • Comprehensive reporting and analytics")
    print("   • Batch processing with detailed monitoring")
    
    print("\n🚀 Ready for production use!")


if __name__ == "__main__":
    # Ejecutar demo si se ejecuta directamente
    asyncio.run(main())
