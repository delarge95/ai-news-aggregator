"""
Mock External APIs - Simulación de APIs externas para testing

Proporciona mocks para simular respuestas de APIs externas como NewsAPI,
The Guardian API, NYTimes API, etc., permitiendo testing sin dependencias
de servicios externos.
"""

import json
import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from unittest.mock import Mock, patch
from dataclasses import dataclass
from enum import Enum


class APIResponseStatus(Enum):
    """Estados de respuesta de API simulados"""
    SUCCESS = "success"
    RATE_LIMITED = "rate_limited"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    SERVER_ERROR = "server_error"
    TIMEOUT = "timeout"


@dataclass
class MockAPIResponse:
    """Respuesta simulada de API externa"""
    status_code: int
    json_data: Dict[str, Any]
    headers: Dict[str, str]
    success: bool


class MockNewsAPI:
    """Mock para NewsAPI.org"""
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, api_key: str = "test_api_key", simulate_errors: bool = False):
        self.api_key = api_key
        self.simulate_errors = simulate_errors
        self.request_count = 0
        self.rate_limit_count = 0
    
    def get_top_headlines(
        self,
        country: str = "es",
        category: Optional[str] = None,
        q: Optional[str] = None,
        page_size: int = 20,
        page: int = 1
    ) -> MockAPIResponse:
        """Simula endpoint de top headlines"""
        return self._make_request('top-headlines', {
            'country': country,
            'category': category,
            'q': q,
            'pageSize': page_size,
            'page': page
        })
    
    def get_everything(
        self,
        q: Optional[str] = None,
        sources: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        language: str = "es",
        sort_by: str = "publishedAt",
        page: int = 1,
        page_size: int = 20
    ) -> MockAPIResponse:
        """Simula endpoint de everything"""
        return self._make_request('everything', {
            'q': q,
            'sources': sources,
            'from': from_date,
            'to': to_date,
            'language': language,
            'sortBy': sort_by,
            'page': page,
            'pageSize': page_size
        })
    
    def get_sources(
        self,
        category: Optional[str] = None,
        language: Optional[str] = None,
        country: Optional[str] = None
    ) -> MockAPIResponse:
        """Simula endpoint de sources"""
        return self._make_request('sources', {
            'category': category,
            'language': language,
            'country': country
        })
    
    def _make_request(self, endpoint: str, params: Dict[str, Any]) -> MockAPIResponse:
        """Procesa request simulado"""
        self.request_count += 1
        
        # Simular diferentes tipos de errores
        if self.simulate_errors:
            if self.request_count % 10 == 0:
                return self._create_error_response(APIResponseStatus.RATE_LIMITED)
            elif self.request_count % 20 == 0:
                return self._create_error_response(APIResponseStatus.UNAUTHORIZED)
            elif self.request_count % 30 == 0:
                return self._create_error_response(APIResponseStatus.SERVER_ERROR)
        
        # Respuesta exitosa
        if endpoint == 'sources':
            return self._create_sources_response(params)
        else:
            return self._create_articles_response(endpoint, params)
    
    def _create_articles_response(self, endpoint: str, params: Dict[str, Any]) -> MockAPIResponse:
        """Crea respuesta de artículos simulada"""
        articles = self._generate_mock_articles(params)
        
        response_data = {
            'status': 'ok',
            'totalResults': len(articles) * 2,  # Simular más resultados de los mostrados
            'articles': articles
        }
        
        return MockAPIResponse(
            status_code=200,
            json_data=response_data,
            headers={'content-type': 'application/json'},
            success=True
        )
    
    def _create_sources_response(self, params: Dict[str, Any]) -> MockAPIResponse:
        """Crea respuesta de fuentes simulada"""
        sources = self._generate_mock_sources(params)
        
        response_data = {
            'status': 'ok',
            'sources': sources
        }
        
        return MockAPIResponse(
            status_code=200,
            json_data=response_data,
            headers={'content-type': 'application/json'},
            success=True
        )
    
    def _create_error_response(self, error_type: APIResponseStatus) -> MockAPIResponse:
        """Crea respuesta de error simulada"""
        error_responses = {
            APIResponseStatus.RATE_LIMITED: {
                'status': 'error',
                'code': 'rateLimited',
                'message': 'You have made too many requests recently. Please try again later.'
            },
            APIResponseStatus.UNAUTHORIZED: {
                'status': 'error',
                'code': 'unauthorized',
                'message': 'Your API key is invalid or you have exceeded your quota.'
            },
            APIResponseStatus.NOT_FOUND: {
                'status': 'error',
                'code': 'notFound',
                'message': 'The requested resource was not found.'
            },
            APIResponseStatus.SERVER_ERROR: {
                'status': 'error',
                'code': 'internalServerError',
                'message': 'An internal server error occurred.'
            },
            APIResponseStatus.TIMEOUT: {
                'status': 'error',
                'code': 'timeout',
                'message': 'The request timed out.'
            }
        }
        
        status_codes = {
            APIResponseStatus.RATE_LIMITED: 429,
            APIResponseStatus.UNAUTHORIZED: 401,
            APIResponseStatus.NOT_FOUND: 404,
            APIResponseStatus.SERVER_ERROR: 500,
            APIResponseStatus.TIMEOUT: 408
        }
        
        return MockAPIResponse(
            status_code=status_codes[error_type],
            json_data=error_responses[error_type],
            headers={'content-type': 'application/json'},
            success=False
        )
    
    def _generate_mock_articles(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera artículos simulados"""
        # Mapeo de categorías a contenido
        content_mapping = {
            'technology': [
                'Avance en inteligencia artificial revoluciona la industria',
                'Nueva startup tecnológica recaudó 50 millones de euros',
                'Expertos predicen el futuro de la computación cuántica'
            ],
            'business': [
                'Mercados financieros muestran signos de recuperación',
                'Gran empresa anuncia nueva estrategia de expansión',
                'Economistas advierten sobre inflación creciente'
            ],
            'health': [
                'Nuevo tratamiento médico muestra resultados prometedores',
                'Estudio revela beneficios de ejercicio regular',
                'Investigadores desarrollan vacuna más efectiva'
            ],
            'sports': [
                'Equipo local gana campeonato nacional',
                'Atleta establece nuevo récord mundial',
                'Comienzan los Juegos Olímpicos con gran expectativa'
            ]
        }
        
        # Determinar categoría
        category = params.get('category', 'general')
        q = params.get('q', '')
        
        articles = []
        num_articles = params.get('pageSize', 20)
        
        for i in range(num_articles):
            # Generar título basado en categoría
            if category in content_mapping:
                titles = content_mapping[category]
                title = random.choice(titles)
            else:
                title = f"Noticia importante del día {i+1}"
            
            # Generar artículo completo
            article = {
                'source': {
                    'id': f"source-{i+1}",
                    'name': f"Diario {chr(65+i)}"
                },
                'author': f"Autor {i+1}",
                'title': title,
                'description': f"Resumen de la noticia: {title.lower()}",
                'url': f"https://example.com/news/{uuid.uuid4()}",
                'urlToImage': f"https://example.com/images/news-{i+1}.jpg",
                'publishedAt': (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat() + 'Z',
                'content': self._generate_content_for_title(title)
            }
            
            # Filtrar por query si se proporciona
            if q and q.lower() not in title.lower():
                continue
            
            articles.append(article)
        
        return articles
    
    def _generate_content_for_title(self, title: str) -> str:
        """Genera contenido basado en el título"""
        content_templates = [
            "En una decisión histórica, las autoridades han anunciado nuevas medidas que prometen cambiar el panorama actual. Los expertos señalan que estos cambios podrían tener un impacto significativo en el futuro próximo.",
            "Los investigadores han descubierto información importante que podría revolucionar nuestra comprensión del tema. Este hallazgo podría llevar a nuevos desarrollos en el campo.",
            "La comunidad internacional ha reaccionado con gran interés a los recientes acontecimientos. Las implicaciones de esta decisión se extienden mucho más allá de lo esperado inicialmente.",
            "Los ciudadanos expresan opiniones divididas sobre las nuevas políticas implementadas. Mientras algunos apoyan la iniciativa, otros expresan sus preocupaciones sobre las consecuencias a largo plazo."
        ]
        
        return random.choice(content_templates)
    
    def _generate_mock_sources(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Genera fuentes simuladas"""
        sources = [
            {
                'id': 'el-pais',
                'name': 'El País',
                'description': 'Diario español de información general',
                'url': 'https://elpais.com',
                'category': 'general',
                'language': 'es',
                'country': 'es'
            },
            {
                'id': 'abc',
                'name': 'ABC',
                'description': 'Diario español de información general',
                'url': 'https://abc.es',
                'category': 'general',
                'language': 'es',
                'country': 'es'
            },
            {
                'id': 'techcrunch',
                'name': 'TechCrunch',
                'description': 'Tecnología e innovación',
                'url': 'https://techcrunch.com',
                'category': 'technology',
                'language': 'en',
                'country': 'us'
            },
            {
                'id': 'bbc-news',
                'name': 'BBC News',
                'description': 'Noticias internacionales',
                'url': 'https://bbc.com/news',
                'category': 'general',
                'language': 'en',
                'country': 'gb'
            }
        ]
        
        # Filtrar por parámetros
        if params.get('category'):
            sources = [s for s in sources if s['category'] == params['category']]
        
        if params.get('language'):
            sources = [s for s in sources if s['language'] == params['language']]
        
        if params.get('country'):
            sources = [s for s in sources if s['country'] == params['country']]
        
        return sources


class MockGuardianAPI:
    """Mock para The Guardian API"""
    
    BASE_URL = "https://content.guardianapis.com"
    
    def __init__(self, api_key: str = "test_guardian_key"):
        self.api_key = api_key
        self.request_count = 0
    
    def search(
        self,
        q: Optional[str] = None,
        section: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
        order_by: str = "newest"
    ) -> MockAPIResponse:
        """Simula búsqueda en The Guardian"""
        self.request_count += 1
        
        articles = self._generate_guardian_articles(q, section)
        
        response_data = {
            'response': {
                'status': 'ok',
                'total': len(articles) * 3,
                'startIndex': (page - 1) * page_size + 1,
                'pageSize': page_size,
                'pages': max(1, (len(articles) * 3) // page_size),
                'currentPage': page,
                'results': articles
            }
        }
        
        return MockAPIResponse(
            status_code=200,
            json_data=response_data,
            headers={'content-type': 'application/json'},
            success=True
        )
    
    def _generate_guardian_articles(self, q: Optional[str], section: Optional[str]) -> List[Dict[str, Any]]:
        """Genera artículos estilo The Guardian"""
        titles = [
            "Exclusive: New developments in ongoing investigation",
            "Analysis: What the latest data tells us about the future",
            "Opinion: Why we need to rethink our approach to this crisis",
            "Breaking: Major announcement expected today",
            "Investigation: Uncovering the truth behind the headlines"
        ]
        
        articles = []
        for i, title in enumerate(titles):
            if q and q.lower() not in title.lower():
                continue
                
            article = {
                'id': f"https://theguardian.com/{section or 'news'}/2024/01/{random.randint(10, 30)}/article-{i+1}",
                'type': 'article',
                'sectionId': section or 'news',
                'sectionName': section.title() if section else 'News',
                'webPublicationDate': (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'webTitle': title,
                'webUrl': f"https://theguardian.com/{section or 'news'}/2024/01/15/article-{i+1}",
                'apiUrl': f"https://content.guardianapis.com/{section or 'news'}/2024/01/15/article-{i+1}",
                'fields': {
                    'headline': title,
                    'standfirst': f"Brief summary of {title.lower()}",
                    'byline': f"By Journalist {i+1}",
                    'thumbnail': f"https://media.guim.co.uk/article-images/guardian-{i+1}.jpg",
                    'body': f"Full article content for {title}..."
                }
            }
            articles.append(article)
        
        return articles


class MockNYTimesAPI:
    """Mock para New York Times API"""
    
    BASE_URL = "https://api.nytimes.com/svc"
    
    def __init__(self, api_key: str = "test_nyt_key"):
        self.api_key = api_key
        self.request_count = 0
    
    def search_articles(
        self,
        q: Optional[str] = None,
        begin_date: Optional[str] = None,
        end_date: Optional[str] = None,
        sort: str = "newest",
        page: int = 0
    ) -> MockAPIResponse:
        """Simula búsqueda de artículos en NYTimes"""
        self.request_count += 1
        
        articles = self._generate_nyt_articles(q)
        
        response_data = {
            'status': 'OK',
            'copyright': 'Copyright (c) 2024 The New York Times Company. All Rights Reserved.',
            'response': {
                'docs': articles,
                'meta': {
                    'hits': len(articles) * 10,
                    'offset': page * 10,
                    'time': random.randint(50, 200)
                }
            }
        }
        
        return MockAPIResponse(
            status_code=200,
            json_data=response_data,
            headers={'content-type': 'application/json'},
            success=True
        )
    
    def _generate_nyt_articles(self, q: Optional[str]) -> List[Dict[str, Any]]:
        """Genera artículos estilo NYTimes"""
        articles = []
        for i in range(10):
            title = f"NY Times Article {i+1} - {random.choice(['Politics', 'Business', 'Technology', 'Health', 'Sports'])}"
            
            if q and q.lower() not in title.lower():
                continue
            
            article = {
                'web_url': f"https://nytimes.com/{random.randint(2023, 2024)}/{random.randint(1, 12)}/{random.randint(1, 28)}/article-{i+1}",
                'snippet': f"Brief description of {title.lower()}",
                'lead_paragraph': f"Lead paragraph for {title}",
                'abstract': f"Abstract of {title}",
                'pub_date': (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat(),
                'headline': {
                    'main': title,
                    'kicker': random.choice(['Breaking News', 'Analysis', 'Opinion', 'Investigation']),
                    'content_kicker': None,
                    'print_headline': title
                },
                'byline': {
                    'original': f"By Reporter {i+1}",
                    'person': [
                        {
                            'firstname': f"Reporter",
                            'lastname': f"{i+1}",
                            'rank': 1,
                            'role': 'reported'
                        }
                    ]
                },
                'multimedia': [
                    {
                        'url': f"https://nytimes.com/images/2024/01/15/arts/article-{i+1}-image.jpg",
                        'subtype': 'xlarge',
                        'caption': f"Caption for image {i+1}"
                    }
                ]
            }
            articles.append(article)
        
        return articles


class MockExternalAPIs:
    """Gestor principal de mocks de APIs externas"""
    
    def __init__(self):
        self.apis = {
            'newsapi': MockNewsAPI(),
            'guardian': MockGuardianAPI(),
            'nytimes': MockNYTimesAPI()
        }
        self.active_mocks = []
    
    def get_api(self, api_name: str) -> Union[MockNewsAPI, MockGuardianAPI, MockNYTimesAPI]:
        """Obtiene instancia mock de API"""
        if api_name not in self.apis:
            raise ValueError(f"API mock no disponible: {api_name}")
        return self.apis[api_name]
    
    def start_mock(self, api_name: str) -> None:
        """Inicia mock para una API específica"""
        if api_name not in self.apis:
            raise ValueError(f"API mock no disponible: {api_name}")
        
        api_mock = self.apis[api_name]
        
        if api_name == 'newsapi':
            patcher = patch('requests.get', side_effect=self._mock_newsapi_get)
        elif api_name == 'guardian':
            patcher = patch('requests.get', side_effect=self._mock_guardian_get)
        elif api_name == 'nytimes':
            patcher = patch('requests.get', side_effect=self._mock_nyt_get)
        else:
            raise ValueError(f"API mock no configurada: {api_name}")
        
        mock_obj = patcher.start()
        self.active_mocks.append(patcher)
    
    def stop_all_mocks(self) -> None:
        """Detiene todos los mocks activos"""
        for patcher in self.active_mocks:
            patcher.stop()
        self.active_mocks.clear()
    
    def _mock_newsapi_get(self, url: str, *args, **kwargs) -> Mock:
        """Mock para requests.get de NewsAPI"""
        response = Mock()
        
        if '/sources' in url:
            data = self.apis['newsapi'].get_sources().json_data
        else:
            data = self.apis['newsapi'].get_top_headlines().json_data
        
        response.status_code = 200
        response.json.return_value = data
        response.headers = {'content-type': 'application/json'}
        return response
    
    def _mock_guardian_get(self, url: str, *args, **kwargs) -> Mock:
        """Mock para requests.get de Guardian"""
        response = Mock()
        
        params = kwargs.get('params', {})
        data = self.apis['guardian'].search(**params).json_data
        
        response.status_code = 200
        response.json.return_value = data
        response.headers = {'content-type': 'application/json'}
        return response
    
    def _mock_nyt_get(self, url: str, *args, **kwargs) -> Mock:
        """Mock para requests.get de NYTimes"""
        response = Mock()
        
        params = kwargs.get('params', {})
        data = self.apis['nytimes'].search_articles(**params).json_data
        
        response.status_code = 200
        response.json.return_value = data
        response.headers = {'content-type': 'application/json'}
        return response
    
    def configure_api_error(self, api_name: str, error_type: str) -> None:
        """Configura API para simular errores"""
        if api_name == 'newsapi':
            self.apis['newsapi'].simulate_errors = True
            # Reset counter para controlar frecuencia de errores
            self.apis['newsapi'].request_count = 0
        else:
            raise ValueError(f"Configuración de error no disponible para: {api_name}")
    
    def reset_api_counters(self, api_name: str) -> None:
        """Resetea contadores de API"""
        if api_name in self.apis:
            self.apis[api_name].request_count = 0
    
    def get_api_stats(self, api_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de API"""
        if api_name not in self.apis:
            raise ValueError(f"API no encontrada: {api_name}")
        
        api = self.apis[api_name]
        
        return {
            'api_name': api_name,
            'request_count': getattr(api, 'request_count', 0),
            'simulate_errors': getattr(api, 'simulate_errors', False)
        }


# Context manager para manejo automático de mocks
class MockAPIContext:
    """Context manager para mocks de APIs"""
    
    def __init__(self, apis: List[str] = None):
        """
        Args:
            apis: Lista de APIs a simular. None = todas las disponibles.
        """
        self.mock_manager = MockExternalAPIs()
        self.apis_to_mock = apis or ['newsapi', 'guardian', 'nytimes']
    
    def __enter__(self):
        for api_name in self.apis_to_mock:
            self.mock_manager.start_mock(api_name)
        return self.mock_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.mock_manager.stop_all_mocks()


# Funciones de conveniencia
def mock_all_apis() -> MockExternalAPIs:
    """Inicia mocks para todas las APIs disponibles"""
    mock_manager = MockExternalAPIs()
    mock_manager.start_mock('newsapi')
    mock_manager.start_mock('guardian')
    mock_manager.start_mock('nytimes')
    return mock_manager


def mock_newsapi_only() -> MockExternalAPIs:
    """Inicia solo mock de NewsAPI"""
    mock_manager = MockExternalAPIs()
    mock_manager.start_mock('newsapi')
    return mock_manager