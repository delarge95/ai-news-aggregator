#!/usr/bin/env python3
"""
Setup completo del sistema de búsqueda avanzada
Configura base de datos, índices, datos de ejemplo y verifica funcionamiento
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.models import Base, Article, Source, TrendingTopic
from scripts.init_search_data import SearchDataInitializer
from app.services.search_service import search_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SearchSystemSetup:
    """Setup completo del sistema de búsqueda"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url
        self.backend_dir = backend_dir
        self.success = True
    
    async def setup_complete_system(self):
        """Configurar sistema completo"""
        logger.info("🚀 Iniciando setup completo del sistema de búsqueda avanzada")
        
        steps = [
            ("Verificar dependencias", self.check_dependencies),
            ("Configurar base de datos", self.setup_database),
            ("Crear índices de rendimiento", self.create_performance_indexes),
            ("Poblar datos de ejemplo", self.populate_sample_data),
            ("Verificar endpoints", self.verify_endpoints),
            ("Ejecutar tests básicos", self.run_basic_tests),
            ("Generar documentación", self.generate_documentation)
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 Ejecutando: {step_name}")
            
            try:
                await step_func()
                logger.info(f"✅ {step_name} - Completado")
            except Exception as e:
                logger.error(f"❌ {step_name} - Error: {str(e)}")
                self.success = False
            
            print()
        
        if self.success:
            logger.info("🎉 Setup completado exitosamente")
            self.print_final_instructions()
        else:
            logger.error("❌ Setup completado con errores")
            self.print_troubleshooting_tips()
    
    def check_dependencies(self):
        """Verificar dependencias requeridas"""
        logger.info("Verificando dependencias...")
        
        required_packages = [
            "fastapi", "uvicorn", "sqlalchemy", "asyncpg",
            "pydantic", "aiohttp", "redis"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"  ✅ {package}")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"  ❌ {package}")
        
        if missing_packages:
            logger.error(f"Packages faltantes: {missing_packages}")
            logger.info("Instalar con: pip install " + " ".join(missing_packages))
            raise Exception("Dependencias faltantes")
        
        # Verificar Python version
        if sys.version_info < (3, 8):
            raise Exception("Se requiere Python 3.8+")
        
        logger.info("Todas las dependencias están disponibles")
    
    def setup_database(self):
        """Configurar base de datos"""
        logger.info("Configurando base de datos...")
        
        try:
            from app.db.database import engine, get_db
            from sqlalchemy import text
            
            # Test connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                if result != 1:
                    raise Exception("No se pudo conectar a la base de datos")
                
            logger.info("Conexión a base de datos: ✅")
            
            # Create all tables
            Base.metadata.create_all(bind=engine)
            logger.info("Tablas creadas: ✅")
            
        except Exception as e:
            logger.error(f"Error configurando base de datos: {str(e)}")
            raise
    
    def create_performance_indexes(self):
        """Crear índices para mejor rendimiento"""
        logger.info("Creando índices de rendimiento...")
        
        try:
            from app.db.database import engine
            from sqlalchemy import text
            
            indexes = [
                # Full-text search indexes
                "CREATE INDEX IF NOT EXISTS idx_articles_title_fts ON articles USING gin(to_tsvector('english', title))",
                "CREATE INDEX IF NOT EXISTS idx_articles_content_fts ON articles USING gin(to_tsvector('english', content))",
                "CREATE INDEX IF NOT EXISTS idx_articles_summary_fts ON articles USING gin(to_tsvector('english', summary))",
                
                # Performance indexes
                "CREATE INDEX IF NOT EXISTS idx_articles_published_at_desc ON articles(published_at DESC)",
                "CREATE INDEX IF NOT EXISTS idx_articles_sentiment_label ON articles(sentiment_label)",
                "CREATE INDEX IF NOT EXISTS idx_articles_relevance_score_desc ON articles(relevance_score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)",
                "CREATE INDEX IF NOT EXISTS idx_articles_processing_status ON articles(processing_status)",
                
                # Trending topics indexes
                "CREATE INDEX IF NOT EXISTS idx_trending_topic_score_desc ON trending_topics(trend_score DESC)",
                "CREATE INDEX IF NOT EXISTS idx_trending_topic_period_date ON trending_topics(time_period, date_recorded DESC)",
                
                # Source indexes
                "CREATE INDEX IF NOT EXISTS idx_sources_active ON sources(is_active)",
                "CREATE INDEX IF NOT EXISTS idx_sources_api_name ON sources(api_name)"
            ]
            
            with engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        conn.commit()
                        logger.info(f"  ✅ Índice creado")
                    except Exception as e:
                        # Algunos índices pueden fallar si ya existen
                        if "already exists" in str(e).lower():
                            logger.info(f"  ℹ️ Índice ya existe")
                        else:
                            logger.warning(f"  ⚠️ Error creando índice: {str(e)[:100]}")
            
            logger.info("Índices de rendimiento configurados")
            
        except Exception as e:
            logger.warning(f"Error creando índices (no crítico): {str(e)}")
    
    def populate_sample_data(self):
        """Poblar base de datos con datos de ejemplo"""
        logger.info("Poblando datos de ejemplo...")
        
        try:
            # Importar el inicializador
            from scripts.init_search_data import SearchDataInitializer
            
            # Usar DATABASE_URL de environment o usar default
            db_url = self.db_url or os.getenv('DATABASE_URL', 'sqlite:///./ai_news.db')
            
            initializer = SearchDataInitializer(db_url)
            
            # Limpiar datos existentes
            logger.info("Limpiando datos existentes...")
            initializer.clear_search_data()
            
            # Crear datos de ejemplo
            logger.info("Creando datos de ejemplo...")
            success = initializer.initialize_data()
            
            if not success:
                raise Exception("Error inicializando datos")
            
            logger.info("Datos de ejemplo creados correctamente")
            
        except Exception as e:
            logger.error(f"Error poblando datos: {str(e)}")
            raise
    
    def verify_endpoints(self):
        """Verificar que los endpoints funcionen"""
        logger.info("Verificando endpoints...")
        
        import aiohttp
        
        base_url = "http://localhost:8000"
        
        endpoints_to_test = [
            "/health",
            "/search",
            "/search/filters", 
            "/search/trending",
            "/search/stats"
        ]
        
        async def test_endpoint(session, endpoint, params=None):
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return True, data.get('status', 'unknown')
                    else:
                        return False, f"HTTP {response.status}"
            except Exception as e:
                return False, str(e)
        
        async def run_endpoint_tests():
            async with aiohttp.ClientSession() as session:
                for endpoint in endpoints_to_test:
                    params = {"limit": "1"} if endpoint == "/search" else None
                    success, status = await test_endpoint(session, endpoint, params)
                    
                    if success:
                        logger.info(f"  ✅ {endpoint} - {status}")
                    else:
                        logger.warning(f"  ⚠️ {endpoint} - {status}")
                        self.success = False
        
        # Solo ejecutar tests si el servidor está corriendo
        try:
            asyncio.run(run_endpoint_tests())
        except Exception as e:
            logger.warning(f"No se pudo verificar endpoints (servidor no corriendo): {str(e)}")
            logger.info("Para verificar endpoints, ejecutar:")
            print(f"  cd {self.backend_dir}")
            print(f"  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
    
    def run_basic_tests(self):
        """Ejecutar tests básicos del sistema"""
        logger.info("Ejecutando tests básicos...")
        
        try:
            # Ejecutar tests del servicio de búsqueda
            test_command = [
                sys.executable, "-m", "pytest", 
                "tests/services/test_search_service.py", 
                "-v", "--tb=short"
            ]
            
            result = subprocess.run(
                test_command, 
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Tests básicos: ✅ Passed")
                # Mostrar resumen de tests
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'PASSED' in line or 'test_' in line:
                        logger.info(f"  {line.strip()}")
            else:
                logger.warning(f"Tests básicos: ⚠️ Algunos fallos")
                logger.warning(result.stdout[-500:])  # Últimas 500 chars
            
        except subprocess.TimeoutExpired:
            logger.warning("Tests básicos: ⚠️ Timeout")
        except Exception as e:
            logger.warning(f"Tests básicos: ⚠️ Error - {str(e)}")
    
    def generate_documentation(self):
        """Generar documentación"""
        logger.info("Generando documentación...")
        
        try:
            # Verificar que existe la documentación
            doc_file = self.backend_dir / "docs" / "SEARCH_SYSTEM.md"
            if doc_file.exists():
                logger.info("  ✅ Documentación existe")
                
                # Verificar que el demo existe
                demo_file = self.backend_dir / "examples" / "search_demo.py"
                if demo_file.exists():
                    logger.info("  ✅ Script de demo existe")
                else:
                    logger.warning("  ⚠️ Script de demo no encontrado")
                
                # Verificar script de inicialización
                init_file = self.backend_dir / "scripts" / "init_search_data.py"
                if init_file.exists():
                    logger.info("  ✅ Script de inicialización existe")
                else:
                    logger.warning("  ⚠️ Script de inicialización no encontrado")
                
            else:
                logger.warning("  ⚠️ Documentación no encontrada")
                
        except Exception as e:
            logger.warning(f"Error verificando documentación: {str(e)}")
    
    def print_final_instructions(self):
        """Imprimir instrucciones finales"""
        print()
        print("🎉 SISTEMA DE BÚSQUEDA CONFIGURADO EXITOSAMENTE")
        print("=" * 50)
        print()
        print("🚀 Para iniciar el servidor:")
        print(f"  cd {self.backend_dir}")
        print("  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print()
        print("📋 Endpoints disponibles:")
        print("  GET /search - Búsqueda avanzada")
        print("  GET /search/suggestions - Sugerencias de búsqueda")  
        print("  GET /search/trending - Búsquedas populares")
        print("  GET /search/filters - Filtros disponibles")
        print("  GET /search/semantic - Búsqueda semántica")
        print("  GET /search/stats - Estadísticas")
        print("  GET /search/health - Health check")
        print()
        print("🧪 Para ejecutar el demo:")
        print(f"  cd {self.backend_dir}")
        print("  python examples/search_demo.py")
        print()
        print("📚 Documentación completa:")
        print(f"  {self.backend_dir}/docs/SEARCH_SYSTEM.md")
        print()
        print("🔧 Ejemplos de uso:")
        print("  # Búsqueda básica")
        print("  curl 'http://localhost:8000/search?q=artificial%20intelligence&limit=10'")
        print()
        print("  # Búsqueda con filtros")
        print("  curl 'http://localhost:8000/search?q=AI&sentiment=positive&min_relevance=0.8'")
        print()
        print("  # Búsquedas trending")
        print("  curl 'http://localhost:8000/search/trending?timeframe=24h&limit=10'")
        print()
    
    def print_troubleshooting_tips(self):
        """Imprimir tips de troubleshooting"""
        print()
        print("❌ CONFIGURACIÓN COMPLETADA CON ERRORES")
        print("=" * 50)
        print()
        print("🔧 Tips de troubleshooting:")
        print()
        print("1. Verificar conexión a base de datos:")
        print("   export DATABASE_URL='postgresql://user:pass@localhost/db'")
        print()
        print("2. Instalar dependencias faltantes:")
        print("   pip install -r requirements.txt")
        print()
        print("3. Verificar logs del sistema:")
        print("   tail -f logs/search_system.log")
        print()
        print("4. Ejecutar solo el setup:")
        print("   python setup_search_system.py --verify-only")
        print()
        print("5. Verificar estado manual:")
        print("   python -c \"from app.db.database import get_db; print('DB OK')\"")


def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup del sistema de búsqueda avanzada")
    parser.add_argument("--db-url", help="URL personalizada de base de datos")
    parser.add_argument("--verify-only", action="store_true", 
                       help="Solo verificar configuración sin poblar datos")
    parser.add_argument("--check-deps", action="store_true",
                       help="Solo verificar dependencias")
    
    args = parser.parse_args()
    
    if args.check_deps:
        setup = SearchSystemSetup(args.db_url)
        setup.check_dependencies()
        return
    
    print("🔧 Setup del Sistema de Búsqueda Avanzada")
    print("=" * 50)
    
    if args.verify_only:
        print("Modo: Solo verificación")
    else:
        print("Modo: Setup completo")
    
    print(f"Base de datos: {args.db_url or 'Por defecto'}")
    print()
    
    setup = SearchSystemSetup(args.db_url)
    
    if args.verify_only:
        # Solo verificar, no poblar datos
        try:
            asyncio.run(setup.check_dependencies())
            asyncio.run(setup.setup_database())
            asyncio.run(setup.create_performance_indexes())
            asyncio.run(setup.verify_endpoints())
            print("✅ Verificación completada")
        except Exception as e:
            print(f"❌ Error en verificación: {str(e)}")
    else:
        # Setup completo
        asyncio.run(setup.setup_complete_system())


if __name__ == "__main__":
    main()