"""
Ejemplo práctico de uso del sistema Celery para AI News Aggregator
Demuestra todas las funcionalidades implementadas
"""

import time
import json
from typing import List, Dict, Any
from loguru import logger

# Importar tareas de Celery
from app.tasks import (
    analyze_article_async,
    batch_analyze_articles,
    classify_topics_batch,
    generate_summaries_batch,
    fetch_latest_news,
    search_news_task,
    get_system_metrics,
    generate_article_digest
)

# Configurar logging
logger.add("logs/celery_example.log", rotation="10 MB", level="INFO")


class CeleryExampleRunner:
    """Ejecutor de ejemplos prácticos del sistema Celery"""
    
    def __init__(self):
        self.results = {}
        
    def run_all_examples(self):
        """Ejecutar todos los ejemplos de uso"""
        logger.info("🚀 Iniciando ejemplos completos del sistema Celery")
        
        # Ejemplo 1: Obtener noticias
        self.example_fetch_news()
        
        # Ejemplo 2: Analizar artículo individual
        if self.results.get('news_articles'):
            self.example_analyze_single_article()
        
        # Ejemplo 3: Procesamiento en lote
        if self.results.get('news_articles'):
            self.example_batch_analysis()
        
        # Ejemplo 4: Clasificación temática
        if self.results.get('analyzed_articles'):
            self.example_topic_classification()
        
        # Ejemplo 5: Generación de resúmenes
        if self.results.get('classified_articles'):
            self.example_generate_summaries()
        
        # Ejemplo 6: Digest consolidado
        if self.results.get('summaries'):
            self.example_generate_digest()
        
        # Ejemplo 7: Búsqueda de noticias
        self.example_search_news()
        
        # Ejemplo 8: Métricas del sistema
        self.example_system_metrics()
        
        # Mostrar resumen final
        self.show_final_summary()
    
    def example_fetch_news(self):
        """Ejemplo 1: Obtener las últimas noticias"""
        logger.info("📰 Ejemplo 1: Obteniendo últimas noticias...")
        
        try:
            # Enviar tarea para obtener noticias
            result = fetch_latest_news.delay(
                limit_per_source=10,
                client_types=['newsapi']  # Usar solo NewsAPI para el ejemplo
            )
            
            # Esperar resultado
            news_data = result.get(timeout=300)  # 5 minutos timeout
            
            if news_data['status'] == 'success':
                articles = news_data['articles']
                self.results['news_articles'] = articles[:5]  # Solo los primeros 5
                
                logger.info(f"✅ Obtenidas {len(articles)} noticias")
                logger.info(f"📊 Fuentes utilizadas: {news_data['statistics']['sources_used']}")
                logger.info(f"⏱️ Tiempo de procesamiento: {news_data['statistics']['processing_time']:.2f}s")
                
                # Mostrar primeras noticias
                for i, article in enumerate(articles[:3], 1):
                    logger.info(f"   {i}. {article.get('title', 'Sin título')[:80]}...")
                    
            else:
                logger.error(f"❌ Error obteniendo noticias: {news_data.get('error_message')}")
                self.results['news_articles'] = []
                
        except Exception as e:
            logger.error(f"💥 Excepción en ejemplo de noticias: {str(e)}")
            self.results['news_articles'] = []
    
    def example_analyze_single_article(self):
        """Ejemplo 2: Analizar un artículo individual"""
        logger.info("🔍 Ejemplo 2: Analizando artículo individual...")
        
        try:
            articles = self.results.get('news_articles', [])
            if not articles:
                logger.warning("⚠️ No hay artículos para analizar")
                return
            
            # Seleccionar primer artículo
            article = articles[0]
            
            # Enviar tarea de análisis
            result = analyze_article_async.delay(article, 'comprehensive')
            
            # Esperar resultado
            analysis = result.get(timeout=180)  # 3 minutos timeout
            
            if analysis.get('status') == 'completed':
                self.results['single_analysis'] = analysis
                
                logger.info(f"✅ Análisis completado")
                logger.info(f"📝 Categoría: {analysis.get('category', 'N/A')}")
                logger.info(f"🏷️ Temas: {analysis.get('topics', [])}")
                logger.info(f"💭 Sentimiento: {analysis.get('sentiment', 'N/A')}")
                logger.info(f"⚡ Tiempo de análisis: {analysis.get('processing_time', 0):.2f}s")
                
            else:
                logger.error(f"❌ Error en análisis: {analysis.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción en análisis individual: {str(e)}")
    
    def example_batch_analysis(self):
        """Ejemplo 3: Procesamiento en lote de artículos"""
        logger.info("📊 Ejemplo 3: Análisis en lote...")
        
        try:
            articles = self.results.get('news_articles', [])
            if len(articles) < 3:
                logger.warning("⚠️ Necesitamos al menos 3 artículos para el lote")
                return
            
            # Seleccionar 3 artículos para el ejemplo
            batch_articles = articles[:3]
            
            # Enviar tarea de análisis en lote
            result = batch_analyze_articles.delay(
                batch_articles,
                analysis_type='comprehensive',
                batch_size=2,  # Procesar de 2 en 2
                max_workers=2
            )
            
            # Esperar resultado
            batch_result = result.get(timeout=600)  # 10 minutos timeout
            
            if batch_result.get('status') == 'completed':
                self.results['batch_analysis'] = batch_result
                
                logger.info(f"✅ Análisis en lote completado")
                logger.info(f"📊 Procesados: {batch_result.get('total_processed', 0)}")
                logger.info(f"❌ Fallidos: {batch_result.get('total_failed', 0)}")
                logger.info(f"📈 Tasa de éxito: {batch_result.get('success_rate', 0):.1f}%")
                logger.info(f"⏱️ Tiempo total: {batch_result.get('processing_time', 0):.2f}s")
                
                # Mostrar resultados detallados si están disponibles
                if 'successful_results' in batch_result:
                    for i, result in enumerate(batch_result['successful_results'], 1):
                        logger.info(f"   {i}. {result.get('category', 'N/A')} - {result.get('topics', [])[:2]}")
                        
            else:
                logger.error(f"❌ Error en análisis en lote: {batch_result.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción en análisis en lote: {str(e)}")
    
    def example_topic_classification(self):
        """Ejemplo 4: Clasificación temática"""
        logger.info("🏷️ Ejemplo 4: Clasificación temática...")
        
        try:
            articles = self.results.get('news_articles', [])
            if not articles:
                logger.warning("⚠️ No hay artículos para clasificar")
                return
            
            # Enviar tarea de clasificación
            result = classify_topics_batch.delay(
                articles,
                classification_system='comprehensive',
                min_confidence=0.5,
                max_categories_per_article=3
            )
            
            # Esperar resultado
            classification = result.get(timeout=300)  # 5 minutos timeout
            
            if classification.get('status') == 'completed':
                self.results['classified_articles'] = classification.get('classification_results', [])
                
                logger.info(f"✅ Clasificación completada")
                logger.info(f"📊 Artículos clasificados: {classification.get('statistics', {}).get('classified_articles', 0)}")
                
                # Mostrar distribución de temas
                topic_dist = classification.get('topic_distribution', {})
                if topic_dist:
                    logger.info("📈 Distribución de temas:")
                    for topic, count in sorted(topic_dist.items(), key=lambda x: x[1], reverse=True):
                        logger.info(f"   {topic}: {count} artículos")
                
            else:
                logger.error(f"❌ Error en clasificación: {classification.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción en clasificación: {str(e)}")
    
    def example_generate_summaries(self):
        """Ejemplo 5: Generación de resúmenes"""
        logger.info("📝 Ejemplo 5: Generando resúmenes...")
        
        try:
            articles = self.results.get('news_articles', [])
            if not articles:
                logger.warning("⚠️ No hay artículos para resumir")
                return
            
            # Enviar tarea de generación de resúmenes
            result = generate_summaries_batch.delay(
                articles,
                summary_type='executive',
                max_summary_length=150,
                include_key_points=True
            )
            
            # Esperar resultado
            summaries = result.get(timeout=450)  # 7.5 minutos timeout
            
            if summaries.get('status') == 'completed':
                self.results['summaries'] = summaries.get('successful_summaries', [])
                
                logger.info(f"✅ Resúmenes generados")
                logger.info(f"📝 Artículos resumidos: {summaries.get('statistics', {}).get('processed_articles', 0)}")
                logger.info(f"⏱️ Tiempo promedio: {summaries.get('statistics', {}).get('avg_summary_length', 0):.1f} caracteres")
                
                # Mostrar algunos resúmenes
                if self.results['summaries']:
                    for i, summary in enumerate(self.results['summaries'][:3], 1):
                        logger.info(f"   {i}. {summary.get('summary', '')[:100]}...")
                        
            else:
                logger.error(f"❌ Error en generación de resúmenes: {summaries.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción en generación de resúmenes: {str(e)}")
    
    def example_generate_digest(self):
        """Ejemplo 6: Generar digest consolidado"""
        logger.info("📋 Ejemplo 6: Generando digest diario...")
        
        try:
            articles = self.results.get('news_articles', [])
            if not articles:
                logger.warning("⚠️ No hay artículos para el digest")
                return
            
            # Enviar tarea de digest
            result = generate_article_digest.delay(
                articles,
                digest_type='daily',
                max_articles=10
            )
            
            # Esperar resultado
            digest = result.get(timeout=300)  # 5 minutos timeout
            
            if digest.get('status') == 'success':
                self.results['digest'] = digest.get('digest', '')
                
                logger.info(f"✅ Digest generado")
                logger.info(f"📊 Artículos incluidos: {digest.get('articles_included', 0)}")
                
                # Mostrar primeras líneas del digest
                digest_lines = digest.get('digest', '').split('\n')[:10]
                logger.info("📋 Primeras líneas del digest:")
                for line in digest_lines:
                    if line.strip():
                        logger.info(f"   {line}")
                        
            else:
                logger.error(f"❌ Error generando digest: {digest.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción generando digest: {str(e)}")
    
    def example_search_news(self):
        """Ejemplo 7: Búsqueda de noticias"""
        logger.info("🔍 Ejemplo 7: Buscando noticias sobre IA...")
        
        try:
            # Enviar tarea de búsqueda
            result = search_news_task.delay(
                query='artificial intelligence',
                limit=5,
                client_types=['newsapi'],
                sort_by='relevance'
            )
            
            # Esperar resultado
            search_results = result.get(timeout=180)  # 3 minutos timeout
            
            if search_results.get('status') == 'success':
                self.results['search_results'] = search_results.get('articles', [])
                
                logger.info(f"✅ Búsqueda completada")
                logger.info(f"🔍 Query: {search_results.get('query', '')}")
                logger.info(f"📊 Resultados encontrados: {search_results.get('total_results', 0)}")
                logger.info(f"⏱️ Tiempo de búsqueda: {search_results.get('statistics', {}).get('processing_time', 0):.2f}s")
                
                # Mostrar resultados
                for i, article in enumerate(search_results.get('articles', [])[:3], 1):
                    logger.info(f"   {i}. {article.get('title', 'Sin título')[:80]}...")
                    
            else:
                logger.error(f"❌ Error en búsqueda: {search_results.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción en búsqueda: {str(e)}")
    
    def example_system_metrics(self):
        """Ejemplo 8: Métricas del sistema"""
        logger.info("📊 Ejemplo 8: Obteniendo métricas del sistema...")
        
        try:
            # Enviar tarea de métricas
            result = get_system_metrics.delay()
            
            # Esperar resultado
            metrics = result.get(timeout=60)  # 1 minuto timeout
            
            if metrics.get('status') == 'success':
                self.results['metrics'] = metrics.get('metrics', {})
                
                # Mostrar métricas principales
                celery_metrics = self.results['metrics'].get('celery_metrics', {})
                system_metrics = self.results['metrics'].get('system_metrics', {})
                redis_metrics = self.results['metrics'].get('redis_metrics', {})
                
                logger.info(f"✅ Métricas obtenidas")
                logger.info(f"👥 Workers activos: {celery_metrics.get('active_workers', 0)}")
                logger.info(f"📋 Tareas activas: {celery_metrics.get('active_tasks_count', 0)}")
                logger.info(f"💻 CPU: {system_metrics.get('cpu_percent', 0):.1f}%")
                logger.info(f"🧠 Memoria: {system_metrics.get('memory_percent', 0):.1f}%")
                logger.info(f"💾 Redis memoria: {redis_metrics.get('used_memory_human', 'N/A')}")
                
            else:
                logger.error(f"❌ Error obteniendo métricas: {metrics.get('error_message')}")
                
        except Exception as e:
            logger.error(f"💥 Excepción obteniendo métricas: {str(e)}")
    
    def show_final_summary(self):
        """Mostrar resumen final de todos los ejemplos"""
        logger.info("📊 RESUMEN FINAL DE EJEMPLOS")
        logger.info("=" * 50)
        
        # Contar resultados exitosos
        successful_examples = 0
        total_examples = 8
        
        if self.results.get('news_articles'):
            successful_examples += 1
            logger.info(f"✅ 1. Noticias obtenidas: {len(self.results['news_articles'])} artículos")
        
        if self.results.get('single_analysis'):
            successful_examples += 1
            logger.info(f"✅ 2. Análisis individual: {self.results['single_analysis'].get('category', 'N/A')}")
        
        if self.results.get('batch_analysis'):
            successful_examples += 1
            batch_stats = self.results['batch_analysis']
            logger.info(f"✅ 3. Análisis en lote: {batch_stats.get('total_processed', 0)} artículos")
        
        if self.results.get('classified_articles'):
            successful_examples += 1
            logger.info(f"✅ 4. Clasificación temática: {len(self.results['classified_articles'])} artículos")
        
        if self.results.get('summaries'):
            successful_examples += 1
            logger.info(f"✅ 5. Resúmenes generados: {len(self.results['summaries'])} resúmenes")
        
        if self.results.get('digest'):
            successful_examples += 1
            logger.info(f"✅ 6. Digest consolidado: Generado")
        
        if self.results.get('search_results'):
            successful_examples += 1
            logger.info(f"✅ 7. Búsqueda de noticias: {len(self.results['search_results'])} resultados")
        
        if self.results.get('metrics'):
            successful_examples += 1
            logger.info(f"✅ 8. Métricas del sistema: Obtenidas")
        
        logger.info(f"📈 Tasa de éxito: {successful_examples}/{total_examples} ({(successful_examples/total_examples)*100:.1f}%)")
        
        if successful_examples == total_examples:
            logger.info("🎉 ¡Todos los ejemplos ejecutados exitosamente!")
        elif successful_examples > total_examples // 2:
            logger.info("👍 La mayoría de ejemplos completados correctamente")
        else:
            logger.warning("⚠️ Varios ejemplos fallaron - revisar configuración")
        
        # Guardar resultados en archivo
        self.save_results_to_file()
    
    def save_results_to_file(self):
        """Guardar resultados en archivo JSON"""
        try:
            output_file = "logs/celery_examples_results.json"
            
            # Preparar datos serializables
            serializable_results = {}
            for key, value in self.results.items():
                if key == 'digest':
                    # Guardar solo texto del digest
                    serializable_results[key] = value
                elif isinstance(value, (str, int, float, bool, list, dict)):
                    serializable_results[key] = value
                else:
                    # Para objetos complejos, convertir a string
                    serializable_results[key] = str(value)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_results, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Resultados guardados en: {output_file}")
            
        except Exception as e:
            logger.error(f"💥 Error guardando resultados: {str(e)}")


def main():
    """Función principal para ejecutar los ejemplos"""
    print("🚀 AI News Aggregator - Ejemplos de Celery")
    print("=" * 50)
    print("Este script demuestra todas las funcionalidades del sistema Celery")
    print("Asegúrate de que Redis y los workers de Celery estén ejecutándose")
    print("=" * 50)
    
    # Crear directorio de logs si no existe
    import os
    os.makedirs("logs", exist_ok=True)
    
    # Ejecutar ejemplos
    runner = CeleryExampleRunner()
    runner.run_all_examples()
    
    print("\n🎉 Ejemplos completados. Revisa los logs para más detalles.")


if __name__ == "__main__":
    main()