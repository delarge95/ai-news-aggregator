"""
Frontend Performance Tests para Core Web Vitals y métricas de UX
Evalúa performance del frontend y experiencia de usuario
"""

import asyncio
import aiohttp
import time
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import re

# Configuración
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CoreWebVitals:
    """Métricas de Core Web Vitals"""
    lcp: float  # Largest Contentful Paint (ms)
    fid: float  # First Input Delay (ms)
    cls: float  # Cumulative Layout Shift
    fcp: float  # First Contentful Paint (ms)
    ttfb: float  # Time to First Byte (ms)
    speed_index: float
    fully_loaded_time: float  # Time to Complete Load (ms)

@dataclass
class PagePerformanceMetrics:
    """Métricas de performance para una página específica"""
    url: str
    page_name: str
    load_time: float  # Tiempo total de carga (ms)
    dom_ready_time: float  # Tiempo hasta DOM ready (ms)
    core_web_vitals: CoreWebVitals
    resource_count: int
    total_resource_size: float  # KB
    script_execution_time: float  # ms
    render_blocking_resources: int
    image_optimization_score: float
    accessibility_score: float
    performance_score: float
    timestamp: str

@dataclass
class FrontendTestConfig:
    """Configuración para tests de frontend"""
    name: str
    base_url: str
    pages_to_test: List[str]
    concurrent_users: int
    iterations_per_page: int
    mobile_emulation: bool = False
    capture_screenshots: bool = False

class FrontendPerformanceTester:
    """Tester de performance para frontend"""
    
    def __init__(self, config: FrontendTestConfig):
        self.config = config
        self.results: List[PagePerformanceMetrics] = []
    
    async def test_page_performance(self, page_url: str, page_name: str) -> PagePerformanceMetrics:
        """Test de performance para una página específica"""
        logger.info(f"Testing page performance: {page_name} - {page_url}")
        
        # Simular navegador con aiohttp (en un entorno real, usarías Playwright o Puppeteer)
        page_metrics = await self._simulate_page_load(page_url)
        
        # Calcular Core Web Vitals simulados
        core_web_vitals = await self._calculate_core_web_vitals(page_url)
        
        # Evaluar recursos de la página
        resource_analysis = await self._analyze_page_resources(page_url)
        
        # Calcular scores adicionales
        performance_score = self._calculate_performance_score(page_metrics)
        accessibility_score = await self._calculate_accessibility_score(page_url)
        image_optimization_score = self._calculate_image_optimization_score(resource_analysis)
        
        metrics = PagePerformanceMetrics(
            url=page_url,
            page_name=page_name,
            load_time=page_metrics.get("load_time", 0),
            dom_ready_time=page_metrics.get("dom_ready_time", 0),
            core_web_vitals=core_web_vitals,
            resource_count=resource_analysis.get("resource_count", 0),
            total_resource_size=resource_analysis.get("total_size_kb", 0),
            script_execution_time=page_metrics.get("script_time", 0),
            render_blocking_resources=resource_analysis.get("render_blocking", 0),
            image_optimization_score=image_optimization_score,
            accessibility_score=accessibility_score,
            performance_score=performance_score,
            timestamp=datetime.now().isoformat()
        )
        
        self.results.append(metrics)
        return metrics
    
    async def _simulate_page_load(self, url: str) -> Dict[str, float]:
        """Simular carga de página y medir tiempos"""
        start_time = time.time()
        
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    "User-Agent": "FrontendPerformanceTest/1.0"
                }
            ) as session:
                
                # Medir TTFB (Time to First Byte)
                ttfb_start = time.time()
                async with session.get(url) as response:
                    ttfb = (time.time() - ttfb_start) * 1000  # ms
                    content = await response.read()
                
                # Simular parsing y renderizado
                parse_start = time.time()
                content_str = content.decode('utf-8', errors='ignore')
                
                # Estimar tiempos de parsing y renderizado
                html_size = len(content_str)
                estimated_parse_time = min(html_size / 10000, 500)  # Simulado
                
                # Simular tiempo de ejecución de JavaScript
                js_execution_time = self._estimate_js_execution_time(content_str)
                
                # Estimar tiempo de DOM ready
                dom_ready_time = estimated_parse_time + js_execution_time
                
                # Tiempo total de carga
                total_load_time = (time.time() - start_time) * 1000
                
                return {
                    "ttfb": ttfb,
                    "load_time": total_load_time,
                    "dom_ready_time": dom_ready_time,
                    "script_time": js_execution_time,
                    "html_size_kb": html_size / 1024
                }
                
        except Exception as e:
            logger.error(f"Error loading page {url}: {e}")
            return {
                "ttfb": 0,
                "load_time": 0,
                "dom_ready_time": 0,
                "script_time": 0,
                "html_size_kb": 0
            }
    
    async def _calculate_core_web_vitals(self, url: str) -> CoreWebVitals:
        """Calcular Core Web Vitals para la página"""
        # En un entorno real, esto usaría APIs del navegador
        # Aquí simulamos valores basados en heurísticas
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.read()
                    content_str = content.decode('utf-8', errors='ignore')
                    
                    # Analizar contenido para estimar métricas
                    html_size = len(content_str)
                    script_count = len(re.findall(r'<script', content_str, re.IGNORECASE))
                    image_count = len(re.findall(r'<img', content_str, re.IGNORECASE))
                    css_count = len(re.findall(r'<link.*stylesheet|<style', content_str, re.IGNORECASE))
                    
                    # Estimar LCP (Largest Contentful Paint) - simulado
                    # Basado en tamaño de HTML y recursos críticos
                    base_lcp = min(html_size / 500, 4000)  # ms
                    script_penalty = script_count * 100
                    image_penalty = image_count * 50
                    lcp = base_lcp + script_penalty + image_penalty
                    
                    # Estimar FID (First Input Delay) - simulado
                    # Basado en cantidad de JavaScript
                    fid = min(script_count * 20, 300)  # ms
                    
                    # Estimar CLS (Cumulative Layout Shift) - simulado
                    # Basado en contenido dinámico y recursos
                    base_cls = 0.1
                    dynamic_content_penalty = (html_size % 1000) / 10000
                    cls = min(base_cls + dynamic_content_penalty, 0.5)
                    
                    # Estimar FCP (First Contentful Paint) - simulado
                    # Similar a LCP pero más optimista
                    fcp = lcp * 0.7
                    
                    # Estimar TTFB (Time to First Byte) - simulado
                    # Basado en tamaño de HTML
                    ttfb = min(html_size / 5000, 800)  # ms
                    
                    # Estimar Speed Index - simulado
                    # Promedio ponderado de métricas
                    speed_index = (lcp + fcp + ttfb) / 3
                    
                    # Estimar tiempo completamente cargado
                    # Basado en todos los recursos
                    total_resources = script_count + image_count + css_count
                    fully_loaded = lcp + (total_resources * 100)  # ms
                    
                    return CoreWebVitals(
                        lcp=round(lcp, 2),
                        fid=round(fid, 2),
                        cls=round(cls, 3),
                        fcp=round(fcp, 2),
                        ttfb=round(ttfb, 2),
                        speed_index=round(speed_index, 2),
                        fully_loaded_time=round(fully_loaded, 2)
                    )
                    
        except Exception as e:
            logger.error(f"Error calculating Core Web Vitals for {url}: {e}")
            return CoreWebVitals(0, 0, 0, 0, 0, 0, 0)
    
    async def _analyze_page_resources(self, url: str) -> Dict[str, Any]:
        """Analizar recursos de la página"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.read()
                    content_str = content.decode('utf-8', errors='ignore')
                    
                    # Contar y analizar diferentes tipos de recursos
                    script_tags = re.findall(r'<script[^>]*src=["\']([^"\']*)["\']', content_str, re.IGNORECASE)
                    link_tags = re.findall(r'<link[^>]*href=["\']([^"\']*)["\']', content_str, re.IGNORECASE)
                    img_tags = re.findall(r'<img[^>]*src=["\']([^"\']*)["\']', content_str, re.IGNORECASE)
                    
                    # Estimar tamaños (en un entorno real, harías HEAD requests)
                    estimated_js_size = len(script_tags) * 50  # KB por archivo promedio
                    estimated_css_size = len(link_tags) * 20   # KB por archivo promedio
                    estimated_img_size = len(img_tags) * 100   # KB por imagen promedio
                    
                    total_size_kb = estimated_js_size + estimated_css_size + estimated_img_size
                    
                    # Identificar recursos render-blocking
                    # En un entorno real, analizarías el render tree
                    render_blocking = len([tag for tag in script_tags if 'defer' not in tag.lower()])
                    
                    return {
                        "resource_count": len(script_tags) + len(link_tags) + len(img_tags),
                        "js_files": len(script_tags),
                        "css_files": len(link_tags),
                        "images": len(img_tags),
                        "total_size_kb": total_size_kb,
                        "render_blocking": render_blocking,
                        "estimated_js_size_kb": estimated_js_size,
                        "estimated_css_size_kb": estimated_css_size,
                        "estimated_img_size_kb": estimated_img_size
                    }
                    
        except Exception as e:
            logger.error(f"Error analyzing resources for {url}: {e}")
            return {
                "resource_count": 0,
                "total_size_kb": 0,
                "render_blocking": 0
            }
    
    def _estimate_js_execution_time(self, content: str) -> float:
        """Estimar tiempo de ejecución de JavaScript"""
        # Contar líneas de JavaScript
        js_lines = len(re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE))
        
        # Estimar tiempo de ejecución (simulado)
        # Cada línea de JS toma ~0.5ms en promedio
        execution_time = js_lines * 0.5
        
        # Penalizar por scripts externos (tiempo de descarga + ejecución)
        external_scripts = re.findall(r'<script[^>]*src=["\']([^"\']*)["\']', content, re.IGNORECASE)
        execution_time += len(external_scripts) * 100  # 100ms por script externo
        
        return execution_time
    
    def _calculate_performance_score(self, page_metrics: Dict[str, float]) -> float:
        """Calcular score de performance (0-100)"""
        score = 100
        
        # Penalizar por tiempos altos
        load_time = page_metrics.get("load_time", 0)
        if load_time > 3000:  # > 3 segundos
            score -= 20
        elif load_time > 2000:  # > 2 segundos
            score -= 10
        
        # Penalizar por TTFB alto
        ttfb = page_metrics.get("ttfb", 0)
        if ttfb > 800:  # > 800ms
            score -= 15
        elif ttfb > 500:  # > 500ms
            score -= 8
        
        # Penalizar por mucho JavaScript
        script_time = page_metrics.get("script_time", 0)
        if script_time > 1000:  # > 1 segundo
            score -= 15
        elif script_time > 500:  # > 500ms
            score -= 8
        
        return max(0, score)
    
    async def _calculate_accessibility_score(self, url: str) -> float:
        """Calcular score de accesibilidad"""
        # En un entorno real, usarías axe-core o similar
        # Aquí simulamos basado en heurísticas del HTML
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    content = await response.read()
                    content_str = content.decode('utf-8', errors='ignore')
                    
                    score = 100
                    
                    # Verificar alt attributes en imágenes
                    images_without_alt = len(re.findall(r'<img(?![^>]*alt=)', content_str, re.IGNORECASE))
                    score -= min(images_without_alt * 5, 20)
                    
                    # Verificar labels en formularios
                    inputs_without_label = len(re.findall(r'<input(?![^>]*id=|<label[^>]*for=)', content_str, re.IGNORECASE))
                    score -= min(inputs_without_label * 10, 30)
                    
                    # Verificar heading structure
                    h1_count = len(re.findall(r'<h1', content_str, re.IGNORECASE))
                    if h1_count == 0:
                        score -= 10
                    elif h1_count > 1:
                        score -= 5
                    
                    return max(0, score)
                    
        except Exception as e:
            logger.error(f"Error calculating accessibility score for {url}: {e}")
            return 0
    
    def _calculate_image_optimization_score(self, resource_analysis: Dict[str, Any]) -> float:
        """Calcular score de optimización de imágenes"""
        images = resource_analysis.get("images", 0)
        total_images_size = resource_analysis.get("estimated_img_size_kb", 0)
        
        if images == 0:
            return 100
        
        # Penalizar por imágenes grandes
        avg_image_size = total_images_size / images
        
        score = 100
        
        if avg_image_size > 200:  # > 200KB promedio por imagen
            score -= 30
        elif avg_image_size > 100:  # > 100KB promedio
            score -= 15
        
        # Penalizar por muchas imágenes
        if images > 10:
            score -= 20
        elif images > 5:
            score -= 10
        
        return max(0, score)
    
    async def test_user_journey(self, journey_name: str, pages: List[Tuple[str, str]]) -> Dict[str, Any]:
        """Test de journey completo del usuario"""
        logger.info(f"Testing user journey: {journey_name}")
        
        journey_start = time.time()
        page_results = []
        total_interactions = 0
        
        for page_url, page_name in pages:
            page_start = time.time()
            
            # Simular interacción del usuario
            await asyncio.sleep(0.1)  # Tiempo de navegación simulado
            
            # Test de performance de la página
            page_metrics = await self.test_page_performance(page_url, page_name)
            page_results.append(asdict(page_metrics))
            
            total_interactions += 1
            total_journey_time = time.time() - journey_start
        
        # Calcular métricas del journey completo
        avg_load_time = statistics.mean([r["load_time"] for r in page_results])
        avg_performance_score = statistics.mean([r["performance_score"] for r in page_results])
        avg_accessibility_score = statistics.mean([r["accessibility_score"] for r in page_results])
        
        journey_metrics = {
            "journey_name": journey_name,
            "total_pages": len(pages),
            "total_interactions": total_interactions,
            "total_journey_time": round(total_journey_time, 2),
            "average_load_time": round(avg_load_time, 2),
            "average_performance_score": round(avg_performance_score, 2),
            "average_accessibility_score": round(avg_accessibility_score, 2),
            "page_results": page_results,
            "user_experience_score": self._calculate_user_experience_score(page_results),
            "timestamp": datetime.now().isoformat()
        }
        
        return journey_metrics
    
    def _calculate_user_experience_score(self, page_results: List[Dict[str, Any]]) -> float:
        """Calcular score de experiencia de usuario"""
        # Combinar múltiples métricas en un score único
        
        scores = []
        
        for result in page_results:
            page_score = 0
            
            # Performance (40% del peso)
            perf_score = result["performance_score"] * 0.4
            page_score += perf_score
            
            # Accessibility (30% del peso)
            access_score = result["accessibility_score"] * 0.3
            page_score += access_score
            
            # Core Web Vitals (30% del peso)
            cwv = result["core_web_vitals"]
            
            # Penalizar por LCP alto
            if cwv["lcp"] <= 2500:
                lcp_score = 30  # Máximo
            elif cwv["lcp"] <= 4000:
                lcp_score = 20
            else:
                lcp_score = 10
            
            # Penalizar por FID alto
            if cwv["fid"] <= 100:
                fid_score = 30
            elif cwv["fid"] <= 300:
                fid_score = 20
            else:
                fid_score = 10
            
            # Penalizar por CLS alto
            if cwv["cls"] <= 0.1:
                cls_score = 30
            elif cwv["cls"] <= 0.25:
                cls_score = 20
            else:
                cls_score = 10
            
            cwv_score = (lcp_score + fid_score + cls_score) / 3
            page_score += cwv_score * 0.3
            
            scores.append(page_score)
        
        return round(statistics.mean(scores), 2)


class FrontendPerformanceTestSuite:
    """Suite completa de tests de performance de frontend"""
    
    def __init__(self, config: FrontendTestConfig):
        self.config = config
        self.tester = FrontendPerformanceTester(config)
    
    async def run_frontend_performance_tests(self) -> Dict[str, Any]:
        """Ejecutar suite completa de tests de frontend"""
        logger.info("Iniciando suite de tests de performance de frontend...")
        
        start_time = time.time()
        test_results = []
        user_journeys = []
        
        # Test de páginas individuales
        for page_url in self.config.pages_to_test:
            page_name = page_url.split("/")[-1] or "home"
            
            # Ejecutar múltiples iteraciones para promediar
            page_metrics_list = []
            for iteration in range(self.config.iterations_per_page):
                metrics = await self.tester.test_page_performance(page_url, page_name)
                page_metrics_list.append(asdict(metrics))
                
                # Pequeña pausa entre iteraciones
                await asyncio.sleep(1)
            
            # Calcular promedios
            avg_metrics = self._average_page_metrics(page_metrics_list)
            test_results.append(avg_metrics)
        
        # Test de user journeys comunes
        common_journeys = self._define_common_journeys()
        for journey_name, pages in common_journeys:
            # Verificar que las páginas existen en la configuración
            journey_pages = [(page, page.split("/")[-1] or "home") for page in pages if page in self.config.pages_to_test]
            if journey_pages:
                journey_results = await self.tester.test_user_journey(journey_name, journey_pages)
                user_journeys.append(journey_results)
        
        total_time = time.time() - start_time
        
        # Análisis de resultados
        analysis = self._analyze_frontend_results(test_results, user_journeys)
        
        return {
            "test_suite": "Frontend Performance Testing",
            "execution_time": round(total_time, 2),
            "configuration": asdict(self.config),
            "page_performance_results": test_results,
            "user_journey_results": user_journeys,
            "analysis": analysis,
            "recommendations": self._generate_frontend_recommendations(analysis),
            "timestamp": datetime.now().isoformat()
        }
    
    def _define_common_journeys(self) -> List[Tuple[str, List[str]]]:
        """Definir journeys comunes de usuario"""
        return [
            ("User Reading Journey", [
                "/",
                "/articles",
                "/articles/1",
                "/search"
            ]),
            ("User Registration Journey", [
                "/",
                "/register",
                "/profile",
                "/dashboard"
            ]),
            ("Admin Dashboard Journey", [
                "/admin",
                "/admin/articles",
                "/admin/analytics",
                "/admin/users"
            ])
        ]
    
    def _average_page_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calcular promedios de múltiples iteraciones de una página"""
        if not metrics_list:
            return {}
        
        # Métricas numéricas a promediar
        numeric_fields = [
            "load_time", "dom_ready_time", "resource_count", "total_resource_size",
            "script_execution_time", "render_blocking_resources", "image_optimization_score",
            "accessibility_score", "performance_score"
        ]
        
        averaged_metrics = {}
        
        for field in numeric_fields:
            values = [m[field] for m in metrics_list if field in m]
            if values:
                averaged_metrics[field] = round(statistics.mean(values), 2)
        
        # Promediar Core Web Vitals
        cwv_fields = ["lcp", "fid", "cls", "fcp", "ttfb", "speed_index", "fully_loaded_time"]
        averaged_cwv = {}
        
        for field in cwv_fields:
            values = [m["core_web_vitals"][field] for m in metrics_list if "core_web_vitals" in m]
            if values:
                averaged_cwv[field] = round(statistics.mean(values), 2)
        
        averaged_metrics["core_web_vitals"] = averaged_cwv
        averaged_metrics["url"] = metrics_list[0]["url"]
        averaged_metrics["page_name"] = metrics_list[0]["page_name"]
        averaged_metrics["timestamp"] = datetime.now().isoformat()
        averaged_metrics["iterations"] = len(metrics_list)
        
        return averaged_metrics
    
    def _analyze_frontend_results(self, page_results: List[Dict], user_journeys: List[Dict]) -> Dict[str, Any]:
        """Analizar resultados de tests de frontend"""
        if not page_results:
            return {"error": "No hay resultados para analizar"}
        
        # Métricas agregadas
        avg_performance_score = statistics.mean([r["performance_score"] for r in page_results])
        avg_accessibility_score = statistics.mean([r["accessibility_score"] for r in page_results])
        avg_load_time = statistics.mean([r["load_time"] for r in page_results])
        
        # Análisis de Core Web Vitals
        all_lcp = [r["core_web_vitals"]["lcp"] for r in page_results]
        all_fid = [r["core_web_vitals"]["fid"] for r in page_results]
        all_cls = [r["core_web_vitals"]["cls"] for r in page_results]
        
        # Clasificar páginas según performance
        excellent_pages = [r for r in page_results if r["performance_score"] >= 90]
        good_pages = [r for r in page_results if 70 <= r["performance_score"] < 90]
        poor_pages = [r for r in page_results if r["performance_score"] < 70]
        
        # Evaluar Core Web Vitals vs thresholds
        cwv_status = {
            "lcp": "good" if statistics.mean(all_lcp) <= 2500 else "needs_improvement",
            "fid": "good" if statistics.mean(all_fid) <= 100 else "needs_improvement",
            "cls": "good" if statistics.mean(all_cls) <= 0.1 else "needs_improvement"
        }
        
        # Análisis de user journeys
        journey_analysis = []
        for journey in user_journeys:
            journey_analysis.append({
                "journey_name": journey["journey_name"],
                "user_experience_score": journey["user_experience_score"],
                "total_time": journey["total_journey_time"]
            })
        
        return {
            "overall_performance_score": round(avg_performance_score, 2),
            "overall_accessibility_score": round(avg_accessibility_score, 2),
            "average_load_time": round(avg_load_time, 2),
            "core_web_vitals_status": cwv_status,
            "page_classification": {
                "excellent": len(excellent_pages),
                "good": len(good_pages),
                "poor": len(poor_pages)
            },
            "core_web_vitals_averages": {
                "lcp": round(statistics.mean(all_lcp), 2),
                "fid": round(statistics.mean(all_fid), 2),
                "cls": round(statistics.mean(all_cls), 3)
            },
            "user_journey_analysis": journey_analysis,
            "critical_issues": self._identify_critical_issues(page_results)
        }
    
    def _identify_critical_issues(self, page_results: List[Dict]) -> List[str]:
        """Identificar problemas críticos"""
        issues = []
        
        for page in page_results:
            # Performance issues
            if page["performance_score"] < 50:
                issues.append(f"Página '{page['page_name']}' tiene performance crítica (< 50)")
            
            # Core Web Vitals issues
            cwv = page["core_web_vitals"]
            if cwv["lcp"] > 4000:
                issues.append(f"Página '{page['page_name']}' tiene LCP crítico (> 4s)")
            
            if cwv["fid"] > 300:
                issues.append(f"Página '{page['page_name']}' tiene FID crítico (> 300ms)")
            
            if cwv["cls"] > 0.25:
                issues.append(f"Página '{page['page_name']}' tiene CLS crítico (> 0.25)")
            
            # Load time issues
            if page["load_time"] > 5000:
                issues.append(f"Página '{page['page_name']}' carga muy lentamente (> 5s)")
            
            # Accessibility issues
            if page["accessibility_score"] < 60:
                issues.append(f"Página '{page['page_name']}' tiene problemas serios de accesibilidad")
        
        return issues
    
    def _generate_frontend_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generar recomendaciones para frontend performance"""
        recommendations = []
        
        # Performance general
        if analysis["overall_performance_score"] < 70:
            recommendations.append("Optimizar performance general - score por debajo de 70")
        
        # Core Web Vitals
        cwv_status = analysis.get("core_web_vitals_status", {})
        if cwv_status.get("lcp") == "needs_improvement":
            recommendations.append("Optimizar Largest Contentful Paint (LCP): optimizar imágenes críticas y recursos de renderizado")
        
        if cwv_status.get("fid") == "needs_improvement":
            recommendations.append("Optimizar First Input Delay (FID): reducir JavaScript blocking y optimizar event handlers")
        
        if cwv_status.get("cls") == "needs_improvement":
            recommendations.append("Optimizar Cumulative Layout Shift (CLS): reservar espacio para contenido dinámico")
        
        # Accessibility
        if analysis["overall_accessibility_score"] < 80:
            recommendations.append("Mejorar accesibilidad: agregar alt texts, labels en formularios y estructura de headings")
        
        # Issues críticos
        critical_issues = analysis.get("critical_issues", [])
        if critical_issues:
            recommendations.append(f"Resolver {len(critical_issues)} problemas críticos identificados")
        
        # Optimizaciones específicas
        page_results = analysis.get("page_classification", {})
        if page_results.get("poor", 0) > 0:
            recommendations.append("Priorizar optimización de páginas con performance pobre")
        
        if not recommendations:
            recommendations.append("Performance de frontend está en buen estado - continuar monitoreo regular")
        
        return recommendations


def main():
    """Función principal para ejecutar tests de frontend"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Frontend Performance Tests for AI News Aggregator")
    parser.add_argument("--host", default="localhost:3000", help="Frontend host to test")
    parser.add_argument("--pages", nargs="+", default=[
        "/", "/articles", "/search", "/dashboard"
    ], help="Pages to test")
    parser.add_argument("--concurrent", type=int, default=5, help="Concurrent users")
    parser.add_argument("--iterations", type=int, default=3, help="Iterations per page")
    parser.add_argument("--output", default="frontend_performance_report.json", help="Output file")
    
    args = parser.parse_args()
    
    # Crear configuración de test
    base_url = f"http://{args.host}"
    config = FrontendTestConfig(
        name="Frontend Performance Test",
        base_url=base_url,
        pages_to_test=args.pages,
        concurrent_users=args.concurrent,
        iterations_per_page=args.iterations
    )
    
    # Ejecutar tests
    test_suite = FrontendPerformanceTestSuite(config)
    results = asyncio.run(test_suite.run_frontend_performance_tests())
    
    # Guardar resultados
    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Resultados guardados en {args.output}")
    
    # Mostrar resumen
    if "error" not in results:
        print(f"\n=== RESUMEN DE PERFORMANCE DE FRONTEND ===")
        print(f"Páginas testadas: {len(results['page_performance_results'])}")
        print(f"Journeys de usuario: {len(results['user_journey_results'])}")
        
        analysis = results['analysis']
        print(f"Score de performance general: {analysis['overall_performance_score']}/100")
        print(f"Score de accesibilidad general: {analysis['overall_accessibility_score']}/100")
        print(f"Tiempo de carga promedio: {analysis['average_load_time']}ms")
        
        # Core Web Vitals
        cwv_avg = analysis['core_web_vitals_averages']
        print(f"\nCore Web Vitals:")
        print(f"- LCP: {cwv_avg['lcp']}ms")
        print(f"- FID: {cwv_avg['fid']}ms")
        print(f"- CLS: {cwv_avg['cls']}")
        
        # Clasificación de páginas
        classification = analysis['page_classification']
        print(f"\nClasificación de páginas:")
        print(f"- Excelentes: {classification['excellent']}")
        print(f"- Buenas: {classification['good']}")
        print(f"- Pobres: {classification['poor']}")
        
        if results['recommendations']:
            print("\n=== RECOMENDACIONES ===")
            for i, rec in enumerate(results['recommendations'], 1):
                print(f"{i}. {rec}")
        
        if analysis['critical_issues']:
            print("\n=== PROBLEMAS CRÍTICOS ===")
            for issue in analysis['critical_issues']:
                print(f"⚠️  {issue}")
    else:
        print(f"Error en tests de frontend: {results['error']}")


if __name__ == "__main__":
    main()