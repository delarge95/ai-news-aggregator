"""
Test de carga usando Locust para APIs de ai-news-aggregator
Simula usuarios reales accediendo a la aplicación bajo carga
"""

import json
import random
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner
import time
import logging
from typing import Dict, Any

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NewsApiUser(HttpUser):
    """Usuario simulado que interactúa con las APIs de noticias"""
    wait_time = between(1, 3)  # Espera entre 1-3 segundos entre requests
    
    def on_start(self):
        """Inicialización al empezar la prueba"""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LoadTest-Client/1.0"
        }
        
        # Intentar autenticación si está disponible
        self.auth_token = None
        self.user_id = None
        try:
            self._authenticate()
        except Exception as e:
            logger.warning(f"Autenticación fallida: {e}")
    
    def _authenticate(self):
        """Intentar autenticación con usuario de prueba"""
        auth_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        
        response = self.client.post("/auth/login", 
                                  headers=self.headers, 
                                  data=json.dumps(auth_data))
        
        if response.status_code == 200:
            result = response.json()
            self.auth_token = result.get("access_token")
            self.user_id = result.get("user", {}).get("id")
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
            logger.info("Autenticación exitosa")
        else:
            logger.warning("Autenticación fallida, continuando sin auth")
    
    @task(3)
    def get_articles(self):
        """Test endpoint principal de artículos"""
        with self.client.get("/api/v1/articles", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                # Verificar que se recibieron datos
                data = response.json()
                if "items" in data and len(data["items"]) > 0:
                    response.success()
                else:
                    response.failure("No se recibieron artículos")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_articles_paginated(self):
        """Test paginación de artículos"""
        page = random.randint(1, 5)
        size = random.choice([10, 20, 50])
        
        with self.client.get(f"/api/v1/articles?page={page}&size={size}", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                data = response.json()
                if "items" in data and "total" in data:
                    response.success()
                else:
                    response.failure("Estructura de respuesta inválida")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(4)
    def search_articles(self):
        """Test búsqueda de artículos"""
        # Términos de búsqueda comunes
        search_terms = ["IA", "machine learning", "inteligencia artificial", 
                       "AI", "technology", "innovation"]
        query = random.choice(search_terms)
        
        params = {
            "query": query,
            "limit": 20
        }
        
        with self.client.get("/api/v1/search", 
                           headers=self.headers,
                           params=params,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def get_article_details(self):
        """Test detalles de artículo específico"""
        # Primero obtener una lista de artículos
        try:
            response = self.client.get("/api/v1/articles?size=100", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                articles = data.get("items", [])
                if articles:
                    article_id = random.choice(articles)["id"]
                    
                    with self.client.get(f"/api/v1/articles/{article_id}", 
                                       headers=self.headers,
                                       catch_response=True) as detail_response:
                        if detail_response.status_code == 200:
                            detail_response.success()
                        else:
                            detail_response.failure(f"Status code: {detail_response.status_code}")
        except Exception as e:
            logger.warning(f"Error obteniendo detalles del artículo: {e}")
    
    @task(1)
    def get_user_news(self):
        """Test feed personalizado del usuario"""
        if not self.user_id:
            self._authenticate()
            
        if self.user_id:
            with self.client.get(f"/api/v1/users/{self.user_id}/news", 
                               headers=self.headers,
                               catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def get_user_analytics(self):
        """Test analytics del usuario"""
        if not self.user_id:
            self._authenticate()
            
        if self.user_id:
            with self.client.get(f"/api/v1/users/{self.user_id}/analytics", 
                               headers=self.headers,
                               catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        with self.client.get("/health", 
                           headers=self.headers,
                           catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


class AdminUser(HttpUser):
    """Usuario administrador para tests específicos"""
    weight = 1
    wait_time = between(5, 10)
    
    def on_start(self):
        """Inicialización con credenciales de admin"""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LoadTest-Admin/1.0"
        }
        self._admin_authenticate()
    
    def _admin_authenticate(self):
        """Autenticación como administrador"""
        auth_data = {
            "email": "admin@example.com",
            "password": "adminpassword123"
        }
        
        response = self.client.post("/auth/login", 
                                  headers=self.headers, 
                                  data=json.dumps(auth_data))
        
        if response.status_code == 200:
            result = response.json()
            self.auth_token = result.get("access_token")
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
    
    @task
    def get_system_metrics(self):
        """Test métricas del sistema"""
        with self.client.get("/api/v1/admin/metrics", 
                           headers=self.headers) as response:
            if response.status_code == 200:
                logger.info("Métricas del sistema obtenidas")
            else:
                logger.warning(f"Error obteniendo métricas: {response.status_code}")


class CrawlerUser(HttpUser):
    """Usuario simulando crawler/bot"""
    weight = 2
    wait_time = between(0.5, 1.5)
    
    def on_start(self):
        """Configuración para crawler"""
        self.headers = {
            "Content-Type": "application/json",
            "User-Agent": "LoadTest-Crawler/1.0"
        }
    
    @task(5)
    def fast_article_scan(self):
        """Escaneo rápido de artículos por un bot"""
        # Solo obtener metadatos básicos
        params = {
            "fields": "id,title,published_at",
            "limit": 50
        }
        
        with self.client.get("/api/v1/articles", 
                           headers=self.headers,
                           params=params) as response:
            if response.status_code == 200:
                logger.info("Escaneo de artículos completado")


# Eventos para tracking personalizado
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Evento al iniciar la prueba"""
    logger.info("Iniciando test de carga")
    if isinstance(environment.runner, MasterRunner):
        logger.info(f"Test distribuido iniciado - {environment.runner.target_user_count} usuarios")
    elif isinstance(environment.runner, WorkerRunner):
        logger.info(f"Worker iniciado - conectado al master")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Evento al finalizar la prueba"""
    logger.info("Test de carga finalizado")
    
    # Estadísticas finales
    stats = environment.stats
    logger.info(f"Total requests: {stats.total.num_requests}")
    logger.info(f"Requests fallidas: {stats.total.num_failures}")
    logger.info(f"Response time medio: {stats.total.avg_response_time:.2f}ms")
    logger.info(f"Response time p95: {stats.total.get_response_time_percentile(0.95):.2f}ms")


if __name__ == "__main__":
    # Para ejecutar standalone
    import os
    host = os.getenv("API_HOST", "localhost:8000")
    logger.info(f"Ejecutando test contra {host}")