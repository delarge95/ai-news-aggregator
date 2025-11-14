#!/usr/bin/env python3
"""
Demostración del AI Processor Service

Este script demuestra las capacidades del AI Processor sin necesidad de API key,
utilizando los sistemas de fallback para análisis local.
"""

import sys
import os
import time

# Add the backend directory to the Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

from app.services.ai_processor import (
    create_ai_processor,
    SentimentAnalyzer,
    TopicClassifier,
    Summarizer,
    RelevanceScorer,
    SentimentType,
    TopicCategory,
    analyze_cost_breakdown
)


def demo_basic_functionality():
    """Demuestra funcionalidad básica del sistema"""
    
    print("🤖 DEMOSTRACIÓN DEL AI PROCESSOR SERVICE")
    print("=" * 60)
    
    # Crear analizador (sin API key para usar fallbacks)
    analyzer = create_ai_processor()
    
    # Artículo de ejemplo
    article_text = """
    Nueva tecnología de inteligencia artificial desarrollada por investigadores 
    del MIT promete revolucionar el diagnóstico médico. El sistema utiliza 
    algoritmos avanzados de machine learning para detectar enfermedades raras 
    con una precisión del 95%. Según el Dr. Smith, esta tecnología permitirá 
    diagnósticos más rápidos y precisos, mejorando significativamente los 
    resultados para los pacientes. La investigación ha sido probada en más de 
    10,000 casos clínicos con resultados prometedores.
    """
    
    print("\n📰 ARTÍCULO DE EJEMPLO:")
    print(f"Texto: {article_text.strip()[:200]}...")
    
    # Demostrar análisis individual
    print("\n" + "="*60)
    print("1️⃣ ANÁLISIS INDIVIDUALES")
    print("="*60)
    
    # Análisis de sentimiento
    print("\n📊 Análisis de Sentimiento:")
    sentiment_analyzer = SentimentAnalyzer()
    sentiment_result = sentiment_analyzer.analyze_sentiment(article_text)
    print(f"   ✅ Sentimiento: {sentiment_result.sentiment.value}")
    print(f"   📈 Score: {sentiment_result.sentiment_score:.2f}")
    print(f"   🎯 Confianza: {sentiment_result.confidence:.2f}")
    print(f"   ⏱️ Tiempo: {sentiment_result.processing_time:.2f}s")
    print(f"   💰 Costo: ${sentiment_result.cost:.4f}")
    
    # Clasificación de tema
    print("\n🏷️ Clasificación de Tema:")
    topic_classifier = TopicClassifier()
    topic_result = topic_classifier.classify_topic(article_text)
    print(f"   ✅ Tema principal: {topic_result.primary_topic.value}")
    print(f"   📈 Probabilidad: {topic_result.topic_probability:.2f}")
    print(f"   🔑 Keywords: {topic_result.topic_keywords[:3]}")
    print(f"   ⏱️ Tiempo: {topic_result.processing_time:.2f}s")
    print(f"   💰 Costo: ${topic_result.cost:.4f}")
    
    # Generación de resumen
    print("\n📝 Resumen del Artículo:")
    summarizer = Summarizer()
    summary_result = summarizer.summarize(article_text, max_words=80)
    print(f"   ✅ Resumen: {summary_result.summary}")
    print(f"   📊 Palabras: {summary_result.word_count}")
    print(f"   ⏰ Tiempo lectura: {summary_result.reading_time_minutes:.1f} min")
    print(f"   ⏱️ Tiempo: {summary_result.processing_time:.2f}s")
    print(f"   💰 Costo: ${summary_result.cost:.4f}")
    
    # Scoring de relevancia
    print("\n⭐ Scoring de Relevancia:")
    relevance_scorer = RelevanceScorer()
    relevance_result = relevance_scorer.score_relevance(article_text)
    print(f"   ✅ Score: {relevance_result.relevance_score:.2f}")
    print(f"   📈 Importancia: {relevance_result.importance_score:.2f}")
    print(f"   🔥 Trending: {relevance_result.trending_score:.2f}")
    print(f"   ⏱️ Tiempo: {relevance_result.processing_time:.2f}s")
    print(f"   💰 Costo: ${relevance_result.cost:.4f}")


def demo_comprehensive_analysis():
    """Demuestra análisis comprehensivo"""
    
    print("\n" + "="*60)
    print("2️⃣ ANÁLISIS COMPREHENSIVO")
    print("="*60)
    
    analyzer = create_ai_processor()
    
    # Múltiples artículos de ejemplo
    articles = [
        {
            "id": "tech_001",
            "title": "Apple lanza iPhone con IA",
            "content": "Apple ha anunciado el nuevo iPhone 15 Pro con capacidades avanzadas de inteligencia artificial que mejoran la experiencia del usuario."
        },
        {
            "id": "pol_001",
            "title": "Elecciones 2024: Candidatos presentan propuestas",
            "content": "Los principales candidatos a la presidencia han presentado sus propuestas para el próximo mandato, enfocándose en economía y tecnología."
        },
        {
            "id": "health_001",
            "title": "Nueva vacuna COVID-19 muestra eficacia del 95%",
            "content": "Un estudio clínico reciente demuestra la alta eficacia de la nueva vacuna desarrollada por Pfizer contra las variantes actuales."
        },
        {
            "id": "sports_001",
            "title": "Barcelona gana Champions League",
            "content": "El FC Barcelona ha ganado la Champions League tras una espectacular final donde sumaron tres goles en los últimos diez minutos."
        }
    ]
    
    print(f"\n📚 Analizando {len(articles)} artículos...")
    
    # Análisis individual con comprehensivo
    results = []
    for article in articles:
        try:
            result = analyzer.analyze_article(
                article_id=article["id"],
                content=article["title"] + " " + article["content"],
                max_summary_words=50
            )
            results.append(result)
            
            print(f"\n📰 {article['id'].upper()}:")
            print(f"   🏷️ Tema: {result.topic.primary_topic.value}")
            print(f"   😊 Sentimiento: {result.sentiment.sentiment.value}")
            print(f"   ⭐ Relevancia: {result.relevance.relevance_score:.2f}")
            print(f"   📊 Score combinado: {result.combined_score:.2f}")
            print(f"   💰 Costo: ${result.total_cost:.4f}")
            
        except Exception as e:
            print(f"   ❌ Error procesando {article['id']}: {str(e)}")
    
    # Análisis de costos
    if results:
        print(f"\n💰 ANÁLISIS DE COSTOS:")
        cost_breakdown = analyze_cost_breakdown(results)
        print(f"   📊 Total artículos: {cost_breakdown['total_articles']}")
        print(f"   💵 Costo total: ${cost_breakdown['total_cost']:.4f}")
        print(f"   💳 Costo promedio: ${cost_breakdown['average_cost']:.4f}")
        print(f"   📈 Costo por artículo: ${cost_breakdown['cost_per_article']:.4f}")


def demo_rate_limiting():
    """Demuestra sistema de rate limiting"""
    
    print("\n" + "="*60)
    print("3️⃣ SISTEMA DE RATE LIMITING")
    print("="*60)
    
    # Crear analizador con límites bajos para demostrar
    analyzer = create_ai_processor(
        requests_per_minute=3,  # Límite muy bajo
        requests_per_day=10
    )
    
    print("⚙️ Configuración de rate limits:")
    print(f"   🕐 Por minuto: 3 requests")
    print(f"   📅 Por día: 10 requests")
    
    text = "Esta es una noticia de prueba para demostrar rate limiting."
    
    print("\n🚀 Ejecutando requests múltiples...")
    
    for i in range(5):
        try:
            start_time = time.time()
            result = analyzer.analyze_article(f"demo_{i}", text)
            elapsed = time.time() - start_time
            
            print(f"   ✅ Request {i+1}: {elapsed:.2f}s")
            
        except Exception as e:
            print(f"   ❌ Request {i+1}: {str(e)}")


def demo_cache_functionality():
    """Demuestra funcionalidad de cache"""
    
    print("\n" + "="*60)
    print("4️⃣ SISTEMA DE CACHE")
    print("="*60)
    
    analyzer = create_ai_processor(cache_ttl=30)  # Cache corto para demo
    
    text = "Esta es una noticia que será procesada múltiples veces para demostrar cache."
    
    print("🗃️ Probando cache con TTL de 30 segundos...")
    
    # Primera request (sin cache)
    print("\n📥 Primera request (sin cache):")
    start_time = time.time()
    result1 = analyzer.analyze_article("cache_test", text)
    time1 = time.time() - start_time
    print(f"   ⏱️ Tiempo: {time1:.3f}s")
    
    # Segunda request (con cache)
    print("\n📤 Segunda request (con cache):")
    start_time = time.time()
    result2 = analyzer.analyze_article("cache_test", text)
    time2 = time.time() - start_time
    print(f"   ⏱️ Tiempo: {time2:.3f}s")
    
    if time2 < time1:
        improvement = ((time1 - time2) / time1) * 100
        print(f"   🚀 Mejora: {improvement:.1f}% más rápido")
    else:
        print("   ℹ️ Cache no disponible (primera vez)")


def demo_error_handling():
    """Demuestra manejo de errores"""
    
    print("\n" + "="*60)
    print("5️⃣ MANEJO DE ERRORES Y FALLBACKS")
    print("="*60)
    
    print("🔄 Probando diferentes escenarios de error...")
    
    # Test con texto muy corto
    print("\n📝 Texto muy corto:")
    short_text = "Noticia corta."
    
    analyzer = create_ai_processor()
    try:
        result = analyzer.analyze_article("short_test", short_text)
        print(f"   ✅ Procesado con éxito")
        print(f"   📊 Score combinado: {result.combined_score:.2f}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test con texto largo
    print("\n📄 Texto muy largo:")
    long_text = "Noticia muy larga. " * 200  # Texto repetido
    
    try:
        result = analyzer.analyze_article("long_test", long_text)
        print(f"   ✅ Procesado con éxito")
        print(f"   📊 Palabras en resumen: {result.summary.word_count}")
        print(f"   ⚡ Tiempo: {result.processing_time:.2f}s")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
    
    # Test con texto con caracteres especiales
    print("\n🔤 Texto con caracteres especiales:")
    special_text = "Noticia con ñ, acentos áéíóú y símbolos @#$%&*"
    
    try:
        result = analyzer.analyze_article("special_test", special_text)
        print(f"   ✅ Procesado con éxito")
        print(f"   🏷️ Tema detectado: {result.topic.primary_topic.value}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


def demo_configurations():
    """Demuestra diferentes configuraciones"""
    
    print("\n" + "="*60)
    print("6️⃣ DIFERENTES CONFIGURACIONES")
    print("="*60)
    
    configs = [
        {
            "name": "Desarrollo (Económico)",
            "model": "gpt-3.5-turbo",
            "rpm": 30,
            "cache_ttl": 7200
        },
        {
            "name": "Producción (Robusto)",
            "model": "gpt-3.5-turbo", 
            "rpm": 60,
            "cache_ttl": 3600
        },
        {
            "name": "Tiempo Real (Rápido)",
            "model": "gpt-3.5-turbo",
            "rpm": 100,
            "cache_ttl": 1800
        }
    ]
    
    for config in configs:
        print(f"\n⚙️ {config['name']}:")
        analyzer = create_ai_processor(
            default_model=config['model'],
            requests_per_minute=config['rpm'],
            cache_ttl=config['cache_ttl']
        )
        print(f"   🤖 Modelo: {config['model']}")
        print(f"   🚦 Rate limit: {config['rpm']}/min")
        print(f"   🗃️ Cache TTL: {config['cache_ttl']}s")
        
        # Test rápido
        text = "Noticia de prueba para configuración."
        try:
            result = analyzer.analyze_article("config_test", text)
            print(f"   ✅ Test exitoso: {result.processing_time:.2f}s")
        except Exception as e:
            print(f"   ❌ Test falló: {str(e)}")


def main():
    """Función principal de demostración"""
    
    import time
    
    try:
        # Demostración de funcionalidad básica
        demo_basic_functionality()
        
        # Demostración de análisis comprehensivo
        demo_comprehensive_analysis()
        
        # Demostración de rate limiting
        demo_rate_limiting()
        
        # Demostración de cache
        demo_cache_functionality()
        
        # Demostración de manejo de errores
        demo_error_handling()
        
        # Demostración de configuraciones
        demo_configurations()
        
        print("\n" + "="*60)
        print("🎉 DEMOSTRACIÓN COMPLETADA")
        print("="*60)
        
        print("\n📋 RESUMEN DE FUNCIONALIDADES DEMOSTRADAS:")
        print("   ✅ Análisis de sentimiento con fallbacks")
        print("   ✅ Clasificación automática de temas")
        print("   ✅ Generación de resúmenes inteligentes")
        print("   ✅ Scoring de relevancia contextual")
        print("   ✅ Análisis comprehensivo integrado")
        print("   ✅ Sistema de rate limiting automático")
        print("   ✅ Cache inteligente con TTL")
        print("   ✅ Manejo robusto de errores")
        print("   ✅ Configuraciones flexibles")
        print("   ✅ Monitoreo de costos y performance")
        
        print("\n💡 NOTAS IMPORTANTES:")
        print("   🔑 Configure OPENAI_API_KEY para funcionalidad completa")
        print("   💰 El sistema incluye fallbacks locales para análisis básico")
        print("   📊 Todos los análisis incluyen métricas de costo y tiempo")
        print("   🔄 Rate limits y retry logic garantizan alta disponibilidad")
        print("   🗃️ Cache inteligente optimiza costos y latencia")
        
        print("\n🚀 PRÓXIMOS PASOS:")
        print("   1. Configure su OPENAI_API_KEY")
        print("   2. Ajuste las configuraciones según su caso de uso")
        print("   3. Integre en su pipeline de noticias")
        print("   4. Configure monitoreo y alertas")
        print("   5. Escale según las necesidades de carga")
        
    except Exception as e:
        print(f"\n❌ ERROR EN DEMOSTRACIÓN: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()