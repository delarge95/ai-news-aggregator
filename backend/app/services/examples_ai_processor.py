"""
Ejemplos de uso del AI Processor Service

Este archivo muestra cómo utilizar las diferentes funcionalidades del AI Processor
para análisis de sentimientos, clasificación de temas, resumen y scoring de relevancia.
"""

import asyncio
import os
from typing import Dict, List

# Importar las clases del AI Processor
try:
    # Try relative import first (when run as module)
    from .ai_processor import (
        SentimentAnalyzer,
        TopicClassifier, 
        Summarizer,
        RelevanceScorer,
        ComprehensiveAnalyzer,
        create_ai_processor,
        analyze_cost_breakdown,
        SentimentType,
        TopicCategory
    )
except ImportError:
    # Fall back to absolute import (when run directly)
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    
    from ai_processor import (
        SentimentAnalyzer,
        TopicClassifier, 
        Summarizer,
        RelevanceScorer,
        ComprehensiveAnalyzer,
        create_ai_processor,
        analyze_cost_breakdown,
        SentimentType,
        TopicCategory
    )


def example_basic_usage():
    """Ejemplo básico de uso del analizador comprehensivo"""
    
    # Configuración
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Crear instancia del analizador
    analyzer = create_ai_processor(
        openai_api_key=openai_api_key,
        default_model="gpt-3.5-turbo",
        requests_per_minute=50,
        cache_ttl=3600
    )
    
    # Artículo de ejemplo
    article = {
        "id": "article_001",
        "title": "Nueva tecnología de IA revoluciona la industria médica",
        "content": """
        Una revolucionaria tecnología de inteligencia artificial desarrollada por investigadores 
        del MIT promete transformar el diagnóstico médico. El sistema, que utiliza algoritmos 
        avanzados de machine learning, puede detectar enfermedades raras con una precisión del 95%.
        
        Según el Dr. Smith, líder del proyecto, esta tecnología permitirá diagnósticos más 
        rápidos y precisos, mejorando significativamente los resultados para los pacientes.
        
        La investigación, publicada en la revista Nature Medicine, ha sido probada en más de 
        10,000 casos clínicos con resultados prometedores.
        """,
        "description": "Nueva IA desarrollada por MIT mejora el diagnóstico médico"
    }
    
    # Análisis comprehensivo síncrono
    result = analyzer.analyze_article(
        article_id=article["id"],
        content=article["title"] + " " + article["content"],
        user_preferences={
            "technology": 0.8,
            "health": 0.9,
            "science": 0.7
        },
        max_summary_words=100
    )
    
    print("=== RESULTADOS DEL ANÁLISIS COMPREHENSIVO ===")
    print(f"Artículo ID: {result.article_id}")
    print(f"Tiempo de procesamiento: {result.processing_time:.2f}s")
    print(f"Costo total: ${result.total_cost:.4f}")
    print(f"Score combinado: {result.combined_score:.2f}")
    
    # Mostrar resultados individuales
    if result.sentiment:
        print(f"\n📊 SENTIMIENTO:")
        print(f"  - Tipo: {result.sentiment.sentiment.value}")
        print(f"  - Score: {result.sentiment.sentiment_score:.2f}")
        print(f"  - Confianza: {result.sentiment.confidence:.2f}")
        print(f"  - Emociones: {result.sentiment.emotion_tags}")
    
    if result.topic:
        print(f"\n🏷️ TEMA:")
        print(f"  - Categoría principal: {result.topic.primary_topic.value}")
        print(f"  - Probabilidad: {result.topic.topic_probability:.2f}")
        print(f"  - Palabras clave: {result.topic.topic_keywords}")
    
    if result.summary:
        print(f"\n📝 RESUMEN:")
        print(f"  - Texto: {result.summary.summary}")
        print(f"  - Puntos clave: {result.summary.key_points}")
        print(f"  - Palabras: {result.summary.word_count}")
        print(f"  - Tiempo de lectura: {result.summary.reading_time_minutes:.1f} min")
    
    if result.relevance:
        print(f"\n⭐ RELEVANCIA:")
        print(f"  - Score: {result.relevance.relevance_score:.2f}")
        print(f"  - Importancia: {result.relevance.importance_score:.2f}")
        print(f"  - Trending: {result.relevance.trending_score:.2f}")
    
    return result


async def example_async_usage():
    """Ejemplo de uso asíncrono con múltiples artículos"""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Crear analizador
    analyzer = create_ai_processor(openai_api_key=openai_api_key)
    
    # Lista de artículos
    articles = [
        {
            "id": "tech_001",
            "title": "Apple lanza nuevo iPhone con IA integrada",
            "content": "Apple ha anunciado oficialmente el lanzamiento del iPhone 15 Pro con capacidades avanzadas de inteligencia artificial..."
        },
        {
            "id": "pol_001", 
            "title": "Elecciones 2024: Candidatos presentan propuestas",
            "content": "Los principales candidatos a la presidencia han presentado sus propuestas para el próximo mandato..."
        },
        {
            "id": "health_001",
            "title": "Nueva vacuna contra COVID-19 muestra eficacia",
            "content": "Un estudio clínico reciente demuestra la alta eficacia de la nueva vacuna desarrollada por Pfizer..."
        }
    ]
    
    # Análisis en lote asíncrono
    print("=== ANÁLISIS EN LOTE ASÍNCRONO ===")
    
    results, errors = await analyzer.batch_analyze_async(
        articles=articles,
        max_concurrent=3
    )
    
    print(f"Resultados exitosos: {len(results)}")
    print(f"Errores: {len(errors)}")
    
    # Mostrar resumen de resultados
    for result in results:
        print(f"\n📰 Artículo: {result.article_id}")
        print(f"   Tema: {result.topic.primary_topic.value if result.topic else 'N/A'}")
        print(f"   Sentimiento: {result.sentiment.sentiment.value if result.sentiment else 'N/A'}")
        print(f"   Relevancia: {result.relevance.relevance_score:.2f if result.relevance else 'N/A'}")
    
    # Análisis de costos
    if results:
        cost_breakdown = analyze_cost_breakdown(results)
        print(f"\n💰 BREAKDOWN DE COSTOS:")
        print(f"  - Costo total: ${cost_breakdown['total_cost']:.4f}")
        print(f"  - Costo promedio: ${cost_breakdown['average_cost']:.4f}")
        print(f"  - Total artículos: {cost_breakdown['total_articles']}")
    
    return results


def example_individual_analyzers():
    """Ejemplo de uso de analizadores individuales"""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    # Texto de ejemplo
    text = """
    Los mercados financieros han mostrado signos de recuperación después de semanas de volatilidad. 
    El índice S&P 500 subió un 2.5% en la última sesión, impulsado por los buenos resultados 
    de las grandes tecnológicas. Los inversores muestran optimismo cauteloso sobre las perspectivas 
    económicas para el próximo trimestre.
    """
    
    print("=== ANÁLISIS CON ANALIZADORES INDIVIDUALES ===")
    
    # Análisis de sentimiento individual
    sentiment_analyzer = SentimentAnalyzer(openai_api_key=openai_api_key)
    sentiment_result = sentiment_analyzer.analyze_sentiment(text)
    
    print(f"\n📊 ANÁLISIS DE SENTIMIENTO:")
    print(f"  - Tipo: {sentiment_result.sentiment.value}")
    print(f"  - Score: {sentiment_result.sentiment_score:.2f}")
    print(f"  - Confianza: {sentiment_result.confidence:.2f}")
    print(f"  - Tiempo: {sentiment_result.processing_time:.2f}s")
    
    # Clasificación de tema individual
    topic_classifier = TopicClassifier(openai_api_key=openai_api_key)
    topic_result = topic_classifier.classify_topic(text)
    
    print(f"\n🏷️ CLASIFICACIÓN DE TEMA:")
    print(f"  - Categoría: {topic_result.primary_topic.value}")
    print(f"  - Probabilidad: {topic_result.topic_probability:.2f}")
    print(f"  - Palabras clave: {topic_result.topic_keywords}")
    
    # Resumen individual
    summarizer = Summarizer(openai_api_key=openai_api_key)
    summary_result = summarizer.summarize(text, max_words=50)
    
    print(f"\n📝 RESUMEN:")
    print(f"  - Resumen: {summary_result.summary}")
    print(f"  - Palabras: {summary_result.word_count}")
    print(f"  - Puntos clave: {summary_result.key_points}")
    
    # Scoring de relevancia individual
    relevance_scorer = RelevanceScorer(openai_api_key=openai_api_key)
    relevance_result = relevance_scorer.score_relevance(
        text,
        user_preferences={"economy": 0.9, "finance": 0.8}
    )
    
    print(f"\n⭐ RELEVANCIA:")
    print(f"  - Score: {relevance_result.relevance_score:.2f}")
    print(f"  - Importancia: {relevance_result.importance_score:.2f}")
    print(f"  - Factores: {relevance_result.relevance_factors}")


def example_error_handling():
    """Ejemplo de manejo de errores y fallbacks"""
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    print("=== EJEMPLO DE MANEJO DE ERRORES ===")
    
    # Crear analizador con rate limits muy bajos para forzar fallbacks
    analyzer = create_ai_processor(
        openai_api_key=openai_api_key,
        requests_per_minute=1,  # Rate limit muy bajo
        cache_ttl=10  # Cache muy corto
    )
    
    text = "Artículo de prueba para demostrar fallbacks."
    
    try:
        # Este debería funcionar con cache o fallback
        result = analyzer.analyze_article("test_001", text)
        print("✅ Análisis completado (con cache o fallback)")
        print(f"   Tiempo: {result.processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error en análisis: {str(e)}")
    
    # Ejemplo con texto muy corto (debería usar fallback)
    short_text = "Noticia corta."
    
    try:
        result = analyzer.analyze_article("test_002", short_text)
        print("✅ Análisis de texto corto completado")
        
    except Exception as e:
        print(f"❌ Error con texto corto: {str(e)}")


def example_configuration():
    """Ejemplo de diferentes configuraciones"""
    
    print("=== EJEMPLOS DE CONFIGURACIÓN ===")
    
    # Configuración para desarrollo (económico)
    dev_analyzer = create_ai_processor(
        default_model="gpt-3.5-turbo",
        requests_per_minute=30,
        requests_per_day=1000,
        cache_ttl=7200  # 2 horas
    )
    print("✅ Configuración de desarrollo inicializada")
    
    # Configuración para producción (robusto)
    prod_analyzer = create_ai_processor(
        default_model="gpt-4",
        requests_per_minute=60,
        requests_per_day=10000,
        cache_ttl=3600  # 1 hora
    )
    print("✅ Configuración de producción inicializada")
    
    # Configuración para análisis en tiempo real (rápido)
    realtime_analyzer = create_ai_processor(
        default_model="gpt-3.5-turbo",
        requests_per_minute=100,
        requests_per_day=50000,
        cache_ttl=1800  # 30 minutos
    )
    print("✅ Configuración de tiempo real inicializada")


async def main():
    """Función principal para ejecutar todos los ejemplos"""
    
    print("🚀 EJEMPLOS DE AI PROCESSOR SERVICE")
    print("=" * 50)
    
    # Verificar si hay API key configurada
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  ADVERTENCIA: OPENAI_API_KEY no está configurada")
        print("   Algunas funciones usarán fallbacks locales")
        print("   Configure la variable de entorno OPENAI_API_KEY para funcionalidad completa")
        print()
    
    # Ejecutar ejemplos
    try:
        # Ejemplo básico
        print("\n1️⃣ EJEMPLO BÁSICO:")
        example_basic_usage()
        
        # Ejemplo asíncrono
        print("\n\n2️⃣ EJEMPLO ASÍNCRONO:")
        await example_async_usage()
        
        # Analizadores individuales
        print("\n\n3️⃣ ANALIZADORES INDIVIDUALES:")
        example_individual_analyzers()
        
        # Manejo de errores
        print("\n\n4️⃣ MANEJO DE ERRORES:")
        example_error_handling()
        
        # Configuraciones
        print("\n\n5️⃣ CONFIGURACIONES:")
        example_configuration()
        
        print("\n\n✅ TODOS LOS EJEMPLOS COMPLETADOS")
        
    except Exception as e:
        print(f"\n❌ ERROR EN EJEMPLOS: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Ejecutar ejemplos
    asyncio.run(main())