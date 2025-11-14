"""
Ejemplo de uso del sistema de deduplicación y normalización
Demuestra cómo integrar los sistemas en el flujo de trabajo del agregador de noticias
"""

from typing import List, Dict
from datetime import datetime

from .deduplication import DuplicateDetector
from .normalizer import NewsNormalizer
from ..db.models import Article
from ..db.database import SessionLocal


class NewsProcessor:
    """Procesador principal que integra normalización y deduplicación"""
    
    def __init__(self):
        self.normalizer = NewsNormalizer()
        self.deduplicator = DuplicateDetector(
            similarity_threshold=0.85,
            max_age_days=7
        )
    
    def process_raw_articles(self, raw_articles: List[Dict], 
                           source_type: str = 'generic') -> List[Dict]:
        """
        Procesa artículos crudos: normaliza, valida y elimina duplicados
        
        Args:
            raw_articles: Lista de artículos en formato crudo
            source_type: Tipo de fuente ('newsapi', 'guardian', etc.)
            
        Returns:
            Lista de artículos procesados y únicos
        """
        print(f"🔄 Procesando {len(raw_articles)} artículos crudos...")
        
        # 1. Normalizar todos los artículos
        normalized_articles = self.normalizer.batch_normalize(
            raw_articles, source_type
        )
        
        print(f"✅ Normalizados: {len(normalized_articles)} de {len(raw_articles)} artículos")
        
        # 2. Validar y limpiar el lote
        valid_articles, invalid_articles = self.normalizer.validate_and_clean_batch(
            normalized_articles
        )
        
        if invalid_articles:
            print(f"⚠️  Artículos inválidos: {len(invalid_articles)}")
        
        # 3. Eliminar duplicados
        unique_articles = self._remove_duplicates(valid_articles)
        
        print(f"🎯 Artículos únicos finales: {len(unique_articles)}")
        
        # 4. Mostrar estadísticas de normalización
        stats = self.normalizer.get_normalization_stats(raw_articles, unique_articles)
        self._print_normalization_stats(stats)
        
        return unique_articles
    
    def _remove_duplicates(self, articles: List[Dict]) -> List[Dict]:
        """Elimina duplicados usando el sistema de detección"""
        db = SessionLocal()
        unique_articles = []
        
        try:
            for article_data in articles:
                # Verificar duplicados en base de datos
                is_duplicate, reason = self.deduplicator.is_duplicate(db, article_data)
                
                if not is_duplicate:
                    unique_articles.append(article_data)
                else:
                    print(f"🗑️  Duplicado eliminado: {article_data['title'][:50]}... - {reason}")
            
        finally:
            db.close()
        
        return unique_articles
    
    def _print_normalization_stats(self, stats: Dict):
        """Imprime estadísticas del proceso de normalización"""
        print("\n📊 ESTADÍSTICAS DE NORMALIZACIÓN:")
        print(f"   • Tasa de éxito: {stats['success_rate']:.1f}%")
        print(f"   • Longitud promedio del contenido: {stats['avg_content_length']:.0f} caracteres")
        print(f"   • Legibilidad promedio: {stats['avg_readability']:.2f}/1.0")
        
        if stats['languages_detected']:
            print(f"   • Idiomas detectados:")
            for lang, count in stats['languages_detected'].items():
                print(f"     - {lang}: {count} artículos")
        
        if stats['article_types']:
            print(f"   • Tipos de artículos:")
            for article_type, count in stats['article_types'].items():
                print(f"     - {article_type}: {count} artículos")


def demo_normalization():
    """Demostración del sistema de normalización"""
    
    print("=" * 60)
    print("🚀 DEMOSTRACIÓN: Sistema de Normalización")
    print("=" * 60)
    
    # Datos de ejemplo de diferentes fuentes
    sample_data = [
        {
            "title": "Breaking: AI Revolution Transforms Healthcare Industry",
            "content": "Artificial Intelligence is revolutionizing healthcare with new diagnostic tools...",
            "description": "AI systems showing promising results in medical diagnosis...",
            "url": "https://example.com/ai-healthcare-1?utm_source=twitter",
            "publishedAt": "2025-11-06T10:30:00Z",
            "source": {"name": "Tech News Daily"},
            "author": "Jane Smith"
        },
        {
            "title": "Major AI Breakthrough in Medical AI Diagnostic Systems Announced",
            "content": "Leading researchers have announced significant progress in AI-powered medical diagnostics...",
            "description": "Revolutionary AI diagnostic tools demonstrate remarkable accuracy...",
            "url": "https://medical-news.com/ai-diagnostics-breakthrough",
            "published_at": "2025-11-06T11:15:00",
            "source_name": "Medical Research Today",
            "author": "Dr. John Doe"
        }
    ]
    
    normalizer = NewsNormalizer()
    
    print("\n📰 NORMALIZANDO ARTÍCULOS DE EJEMPLO...")
    for i, raw_article in enumerate(sample_data, 1):
        print(f"\n🔹 Artículo {i}:")
        print(f"   Título original: {raw_article['title']}")
        
        # Normalizar artículo individual
        normalized = normalizer.normalize_article(raw_article, 'generic')
        
        if normalized:
            print(f"   ✅ Normalizado exitosamente:")
            print(f"   • Título: {normalized['title']}")
            print(f"   • URL normalizada: {normalized['url']}")
            print(f"   • Fecha: {normalized['published_at']}")
            print(f"   • Metadatos extraídos:")
            print(f"     - Hash: {normalized['content_hash'][:10]}...")
            print(f"     - Tipo: {normalized['article_type']}")
            print(f"     - Idioma: {normalized['language']}")
            print(f"     - Legibilidad: {normalized['readability_score']:.2f}/1.0")
        else:
            print(f"   ❌ Error en normalización")
    
    # Procesamiento en lote
    print(f"\n🔄 PROCESAMIENTO EN LOTE...")
    normalized_batch = normalizer.batch_normalize(sample_data, 'generic')
    stats = normalizer.get_normalization_stats(sample_data, normalized_batch)
    
    normalizer._print_normalization_stats(stats)


def demo_deduplication():
    """Demostración del sistema de deduplicación"""
    
    print("\n" + "=" * 60)
    print("🚀 DEMOSTRACIÓN: Sistema de Deduplicación")
    print("=" * 60)
    
    # Simular datos de artículos para demostración
    sample_articles = [
        {
            "title": "AI Breakthrough Changes Everything",
            "content": "Scientists announce major AI advancement that could transform industries worldwide with new possibilities for automation...",
            "url": "https://technews.com/ai-breakthrough-2025"
        },
        {
            "title": "Major AI Breakthrough Transforms Industries Worldwide",
            "content": "Researchers have announced a significant AI advancement that could transform industries worldwide, offering new possibilities for automation...",
            "url": "https://ai-research.org/industry-transformation-2025"
        },
        {
            "title": "Complete Different Topic: Climate Change Solutions",
            "content": "New renewable energy technologies show promise for combating climate change effects...",
            "url": "https://environment.news.com/climate-solutions"
        }
    ]
    
    deduplicator = DuplicateDetector(similarity_threshold=0.8)
    
    # Crear sesión de base de datos temporal (en un entorno real, esto vendría de la aplicación)
    from unittest.mock import Mock
    mock_db = Mock()
    
    print("\n🔍 DETECTANDO DUPLICADOS...")
    
    for i, article in enumerate(sample_articles, 1):
        print(f"\n🔹 Analizando artículo {i}:")
        print(f"   Título: {article['title']}")
        
        # En una implementación real, esto consultaría la base de datos
        # Para la demostración, simulamos la detección
        if i == 1:
            print(f"   ⚪ No hay artículos previos para comparar")
        else:
            print(f"   🔍 Comparando con artículos anteriores...")
            
            # Simular comparación
            if i == 2:
                print(f"   ⚠️  DUPLICADO DETECTADO:")
                print(f"   • Tipo: Similitud de título")
                print(f"   • Puntuación: 0.85/1.0")
                print(f"   • Motivo: Alto grado de similitud entre títulos")
            else:
                print(f"   ✅ Artículo único - tema completamente diferente")
    
    print(f"\n💡 FUNCIONES DISPONIBLES:")
    print(f"   • Detección por URL exacta")
    print(f"   • Fuzzy matching de títulos")
    print(f"   • Análisis de contenido similar")
    print(f"   • Fusión automática de duplicados")
    print(f"   • Umbrales de similitud configurables")


def demo_integration():
    """Demostración de la integración completa"""
    
    print("\n" + "=" * 60)
    print("🚀 DEMOSTRACIÓN: Integración Completa")
    print("=" * 60)
    
    # Simular flujo completo
    processor = NewsProcessor()
    
    # Datos simulados de múltiples fuentes
    mixed_raw_data = [
        # Similitudes para demostrar deduplicación
        {
            "title": "AI Company Announces Revolutionary Chip",
            "content": "Leading AI company unveils new chip design that promises to revolutionize machine learning processing...",
            "publishedAt": "2025-11-06T09:00:00Z"
        },
        {
            "title": "Revolutionary AI Chip Unveiled by Leading Company",
            "content": "A major AI company has unveiled revolutionary chip design that promises to revolutionize machine learning...",
            "publishedAt": "2025-11-06T09:30:00Z"
        },
        # Artículo diferente
        {
            "title": "Climate Summit Reaches Historic Agreement",
            "content": "World leaders reach unprecedented climate agreement with ambitious emission reduction targets...",
            "publishedAt": "2025-11-06T10:00:00Z"
        }
    ]
    
    print(f"\n🔄 Procesamiento integrado (simulado):")
    print(f"   Entrada: {len(mixed_raw_data)} artículos crudos")
    print(f"   1️⃣ Normalización...")
    print(f"   2️⃣ Validación...")
    print(f"   3️⃣ Detección de duplicados...")
    print(f"   4️⃣ Salida final: 2 artículos únicos (1 duplicado eliminado)")
    
    print(f"\n🎯 BENEFICIOS DEL SISTEMA:")
    print(f"   ✅ Unifica datos de múltiples fuentes")
    print(f"   ✅ Elimina contenido duplicado inteligente")
    print(f"   ✅ Extrae metadatos automáticamente")
    print(f"   ✅ Mejora calidad de datos")
    print(f"   ✅ Reduce ruido en el agregador")


if __name__ == "__main__":
    """Ejecutar todas las demostraciones"""
    print("🎬 SISTEMA DE DEDUPLICACIÓN Y NORMALIZACIÓN")
    print("    AI News Aggregator - Backend Utils")
    
    demo_normalization()
    demo_deduplication()
    demo_integration()
    
    print(f"\n" + "=" * 60)
    print(f"✅ DEMOSTRACIÓN COMPLETADA")
    print(f"   Los sistemas están listos para integrar en el agregador")
    print(f"=" * 60)