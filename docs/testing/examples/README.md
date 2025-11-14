# Ejemplos de Writing Tests - AI News Aggregator

Esta carpeta contiene ejemplos prácticos de cómo escribir tests para diferentes tipos de componentes en el AI News Aggregator.

## Estructura de Ejemplos

```
examples/
├── backend/
│   ├── unit/
│   │   ├── test_service_examples.py
│   │   ├── test_api_client_examples.py
│   │   └── test_utility_examples.py
│   ├── integration/
│   │   ├── test_api_endpoints_examples.py
│   │   ├── test_database_examples.py
│   │   └── test_external_apis_examples.py
│   └── performance/
│       ├── test_performance_examples.py
│       └── test_load_examples.py
├── frontend/
│   ├── components/
│   │   ├── NewsCard.test.tsx
│   │   ├── SearchBar.test.tsx
│   │   └── UserProfile.test.tsx
│   ├── hooks/
│   │   ├── useNewsSearch.test.ts
│   │   └── useAuth.test.ts
│   └── utils/
│       ├── api.test.ts
│       └── dateHelpers.test.ts
└── e2e/
    ├── user-journey-examples.spec.ts
    └── search-flow-examples.spec.ts
```

## Patrones de Testing

### 1. Tests Unitarios Backend (Python/pytest)

#### Service Testing Pattern
```python
# Ejemplo: test_service_examples.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.services.news_service import NewsService
from app.models.article import Article

@pytest.mark.unit
class TestNewsService:
    """Ejemplos de testing para servicios"""
    
    @pytest.fixture
    def news_service(self):
        """Fixture para NewsService con dependencias mock"""
        mock_api_client = Mock()
        mock_db_client = Mock()
        mock_cache_client = Mock()
        
        return NewsService(
            api_client=mock_api_client,
            db_client=mock_db_client,
            cache_client=mock_cache_client
        )
    
    @pytest.fixture
    def sample_articles(self):
        """Fixture con artículos de ejemplo"""
        return [
            Article(
                title="Test Article 1",
                content="Test content 1",
                url="https://example.com/1",
                published_at="2023-01-01T00:00:00Z"
            ),
            Article(
                title="Test Article 2", 
                content="Test content 2",
                url="https://example.com/2",
                published_at="2023-01-02T00:00:00Z"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_fetch_articles_success(self, news_service, sample_articles):
        """Test: obtener artículos exitosamente"""
        # Arrange
        news_service.api_client.fetch_articles.return_value = sample_articles
        query = "technology"
        
        # Act
        result = await news_service.fetch_articles(query)
        
        # Assert
        assert len(result) == 2
        assert result[0].title == "Test Article 1"
        assert result[1].title == "Test Article 2"
        
        # Verify interactions
        news_service.api_client.fetch_articles.assert_called_once_with(query)
        news_service.cache_client.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fetch_articles_api_error(self, news_service):
        """Test: manejo de error de API"""
        # Arrange
        news_service.api_client.fetch_articles.side_effect = Exception("API Error")
        query = "technology"
        
        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await news_service.fetch_articles(query)
        
        assert str(exc_info.value) == "API Error"
        
        # Verify that cache wasn't modified on error
        news_service.cache_client.set.assert_not_called()
    
    def test_deduplicate_articles(self, news_service, sample_articles):
        """Test: deduplicación de artículos"""
        # Arrange
        duplicate_articles = sample_articles + [
            Article(
                title="Test Article 1",  # Duplicate title
                content="Test content 1", # Duplicate content
                url="https://example.com/1",
                published_at="2023-01-01T00:00:00Z"
            )
        ]
        
        # Act
        result = news_service.deduplicate_articles(duplicate_articles)
        
        # Assert
        assert len(result) == 2  # Should remove duplicate
        
    @pytest.mark.parametrize("query,expected_count", [
        ("technology", 5),
        ("sports", 3),
        ("politics", 2),
        ("", 0),
    ])
    @pytest.mark.asyncio
    async def test_fetch_articles_with_params(self, news_service, query, expected_count):
        """Test: parámetros diferentes de búsqueda"""
        # Arrange
        news_service.api_client.fetch_articles.return_value = [
            Mock() for _ in range(expected_count)
        ]
        
        # Act
        result = await news_service.fetch_articles(query)
        
        # Assert
        assert len(result) == expected_count
        news_service.api_client.fetch_articles.assert_called_with(query)

@pytest.mark.unit  
class TestDeduplicationService:
    """Ejemplos de testing de algoritmos complejos"""
    
    @pytest.fixture
    def dedup_service(self):
        return DeduplicationService(threshold=0.8)
    
    def test_find_exact_duplicates(self, dedup_service):
        """Test: encontrar duplicados exactos"""
        # Arrange
        articles = [
            Article(title="Same Title", content="Same Content", url="https://a.com"),
            Article(title="Same Title", content="Same Content", url="https://b.com"),
            Article(title="Different Title", content="Different Content", url="https://c.com")
        ]
        
        # Act
        duplicates = dedup_service.find_duplicates(articles)
        
        # Assert
        assert len(duplicates) == 1
        assert duplicates[0] == [articles[0], articles[1]]  # First two are duplicates
    
    def test_find_semantic_duplicates(self, dedup_service):
        """Test: encontrar duplicados semánticos"""
        # Arrange
        articles = [
            Article(
                title="AI Revolution in Tech",
                content="Artificial intelligence is transforming technology...",
                url="https://a.com"
            ),
            Article(
                title="Artificial Intelligence Changing Technology",
                content="AI is revolutionizing how we use tech...",
                url="https://b.com"
            ),
            Article(
                title="Weather Forecast Today",
                content="Today's weather will be sunny...",
                url="https://c.com"
            )
        ]
        
        # Act
        duplicates = dedup_service.find_duplicates(articles)
        
        # Assert
        assert len(duplicates) == 1
        # First two articles should be considered similar
        assert articles[0] in duplicates[0]
        assert articles[1] in duplicates[0]
        assert articles[2] not in duplicates[0]
    
    @pytest.mark.parametrize("threshold,expected_groups", [
        (0.9, 3),  # Very strict, no duplicates
        (0.8, 1),  # Normal threshold
        (0.5, 0),  # Too loose, everything is duplicate
    ])
    def test_deduplication_with_different_thresholds(
        self, dedup_service, threshold, expected_groups
    ):
        """Test: deduplicación con diferentes umbrales"""
        # Arrange
        dedup_service.threshold = threshold
        articles = [
            Article(title="Similar Title 1", content="Similar content 1", url="https://a.com"),
            Article(title="Similar Title 2", content="Similar content 2", url="https://b.com"),
            Article(title="Completely Different", content="Different content", url="https://c.com")
        ]
        
        # Act
        groups = dedup_service.find_duplicates(articles)
        
        # Assert
        assert len(groups) == expected_groups
```

#### API Client Testing Pattern
```python
# Ejemplo: test_api_client_examples.py
import pytest
import httpx
from unittest.mock import AsyncMock, patch, Mock
from app.clients.newsapi_client import NewsAPIClient
from app.schemas.article import ArticleResponse

@pytest.mark.unit
class TestNewsAPIClient:
    """Ejemplos de testing para clientes de APIs"""
    
    @pytest.fixture
    def client(self):
        return NewsAPIClient(api_key="test_key")
    
    @pytest.fixture
    def mock_response_data(self):
        return {
            "status": "ok",
            "totalResults": 2,
            "articles": [
                {
                    "source": {"id": "techcrunch", "name": "TechCrunch"},
                    "author": "John Doe",
                    "title": "AI Breakthrough",
                    "description": "Latest AI developments",
                    "url": "https://example.com/1",
                    "urlToImage": "https://example.com/img1.jpg",
                    "publishedAt": "2023-01-01T00:00:00Z",
                    "content": "Full article content..."
                },
                {
                    "source": {"id": "reuters", "name": "Reuters"},
                    "author": "Jane Smith",
                    title: "Tech Stocks Rise",
                    "description": "Technology sector gains",
                    "url": "https://example.com/2",
                    "urlToImage": "https://example.com/img2.jpg", 
                    "publishedAt": "2023-01-02T00:00:00Z",
                    "content": "Market analysis content..."
                }
            ]
        }
    
    @pytest.mark.asyncio
    async def test_fetch_articles_success(self, client, mock_response_data):
        """Test: fetch exitoso de artículos"""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            mock_get.return_value = mock_response
            
            query = "artificial intelligence"
            page = 1
            page_size = 20
            
            # Act
            result = await client.fetch_articles(
                query=query,
                page=page,
                page_size=page_size
            )
            
            # Assert
            assert len(result) == 2
            assert isinstance(result[0], ArticleResponse)
            assert result[0].title == "AI Breakthrough"
            assert result[0].author == "John Doe"
            assert result[0].source_name == "TechCrunch"
            
            # Verify API call
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "q=artificial+intelligence" in call_args[0][0]
            assert call_args[1]["params"]["page"] == 1
            assert call_args[1]["params"]["pageSize"] == 20
    
    @pytest.mark.asyncio
    async def test_fetch_articles_api_error(self, client):
        """Test: manejo de error de API"""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 429  # Too Many Requests
            mock_response.json.return_value = {
                "status": "error",
                "code": "rateLimited",
                "message": "API rate limit exceeded"
            }
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await client.fetch_articles("test query")
            
            assert "rate limit" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_fetch_articles_network_error(self, client):
        """Test: manejo de error de red"""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await client.fetch_articles("test query")
            
            assert "connection" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_fetch_articles_invalid_response(self, client):
        """Test: respuesta inválida de API"""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "error",  # API returned error
                "code": "invalidQuery",
                "message": "Invalid search query"
            }
            mock_get.return_value = mock_response
            
            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await client.fetch_articles("")
            
            assert "invalid" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_fetch_articles_pagination(self, client):
        """Test: manejo de paginación"""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "status": "ok",
                "totalResults": 100,
                "articles": [{"title": f"Article {i}"} for i in range(20)]
            }
            mock_get.return_value = mock_response
            
            # Act
            result = await client.fetch_articles("test", page=3, page_size=20)
            
            # Assert
            assert len(result) == 20
            call_args = mock_get.call_args
            assert call_args[1]["params"]["page"] == 3
            assert call_args[1]["params"]["pageSize"] == 20
    
    @pytest.mark.asyncio
    async def test_build_url(self, client):
        """Test: construcción de URLs"""
        # Arrange
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok", "articles": []}
            mock_get.return_value = mock_response
            
            # Act
            await client.fetch_articles("test query", from_date="2023-01-01")
            
            # Assert - Verify URL parameters
            call_args = mock_get.call_args
            params = call_args[1]["params"]
            
            assert "q=test+query" in call_args[0][0]
            assert params["from"] == "2023-01-01"
            assert "apiKey" in params
            assert params["language"] == "en"

@pytest.mark.unit
class TestRateLimiting:
    """Ejemplos de testing de rate limiting"""
    
    @pytest.fixture
    def limiter(self):
        return RateLimiter(requests_per_minute=5)
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_requests_within_limit(self, limiter):
        """Test: rate limit permite requests dentro del límite"""
        # Act & Assert
        for i in range(5):
            allowed, remaining = await limiter.check_limit("api_key")
            assert allowed is True
            assert remaining == 4 - i
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_requests_over_limit(self, limiter):
        """Test: rate limit bloquea requests excedentes"""
        # Act & Assert
        # First 5 requests should be allowed
        for i in range(5):
            allowed, remaining = await limiter.check_limit("api_key")
            assert allowed is True
        
        # 6th request should be blocked
        allowed, remaining = await limiter.check_limit("api_key")
        assert allowed is False
        assert remaining == 0
    
    @pytest.mark.asyncio
    async def test_rate_limit_resets_after_window(self, limiter):
        """Test: rate limit se resetea después de la ventana"""
        # First, consume all requests
        for i in range(5):
            await limiter.check_limit("api_key")
        
        # Should be blocked
        allowed, _ = await limiter.check_limit("api_key")
        assert allowed is False
        
        # Simulate time passing (mock the time)
        with patch('time.time', return_value=time.time() + 61):  # 61 seconds later
            # Should be allowed again
            allowed, remaining = await limiter.check_limit("api_key")
            assert allowed is True
            assert remaining == 4
```

### 2. Tests de Integración Backend

#### API Endpoint Testing Pattern
```python
# Ejemplo: test_api_endpoints_examples.py
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import get_database
from sqlalchemy.ext.asyncio import AsyncSession

@pytest.mark.integration
class TestArticlesAPI:
    """Ejemplos de testing de endpoints de API"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    async def test_db(self, setup_test_db):
        """Database fixture con datos de prueba"""
        async with setup_test_db() as db:
            # Insert test data
            await self.insert_test_articles(db)
            yield db
    
    @pytest.fixture
    def auth_headers(self):
        """Headers de autenticación"""
        # Mock authentication token
        return {"Authorization": "Bearer test_token_123"}
    
    async def insert_test_articles(self, db: AsyncSession):
        """Insert test articles into database"""
        # Implementation depends on your database setup
        pass
    
    def test_get_articles_success(self, client, auth_headers):
        """Test: obtener artículos exitosamente"""
        # Act
        response = client.get(
            "/articles",
            headers=auth_headers,
            params={"page": 1, "limit": 10}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        
        assert len(data["items"]) <= 10
        assert data["page"] == 1
        assert data["limit"] == 10
    
    def test_get_articles_with_filters(self, client, auth_headers):
        """Test: obtener artículos con filtros"""
        # Act
        response = client.get(
            "/articles",
            headers=auth_headers,
            params={
                "category": "technology",
                "source": "TechCrunch",
                "from_date": "2023-01-01",
                "to_date": "2023-01-31"
            }
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # Verify filtering logic (depends on implementation)
        for article in data["items"]:
            assert article["category"] == "technology"
            # More assertions based on your filtering logic
    
    def test_get_articles_unauthorized(self, client):
        """Test: acceso sin autorización"""
        # Act
        response = client.get("/articles")
        
        # Assert
        assert response.status_code == 401
    
    def test_get_articles_invalid_token(self, client):
        """Test: token inválido"""
        # Act
        response = client.get(
            "/articles",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Assert
        assert response.status_code == 401
    
    def test_search_articles_success(self, client, auth_headers):
        """Test: búsqueda de artículos"""
        # Act
        response = client.get(
            "/articles/search",
            headers=auth_headers,
            params={"q": "artificial intelligence", "limit": 20}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "query" in data
        assert "total_results" in data
        assert "search_time" in data
        
        assert data["query"] == "artificial intelligence"
        assert len(data["results"]) <= 20
        assert data["total_results"] >= 0
    
    def test_search_articles_empty_query(self, client, auth_headers):
        """Test: búsqueda con query vacía"""
        # Act
        response = client.get(
            "/articles/search",
            headers=auth_headers,
            params={"q": ""}
        )
        
        # Assert
        assert response.status_code == 400
        assert "query" in response.json()["detail"].lower()
    
    def test_create_article_favorite(self, client, auth_headers):
        """Test: marcar artículo como favorito"""
        # Arrange
        article_id = "test_article_123"
        
        # Act
        response = client.post(
            f"/articles/{article_id}/favorite",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 201
        assert response.json()["status"] == "favorited"
        assert response.json()["article_id"] == article_id
    
    def test_remove_article_favorite(self, client, auth_headers):
        """Test: remover artículo de favoritos"""
        # Arrange
        article_id = "test_article_123"
        
        # First, mark as favorite
        client.post(f"/articles/{article_id}/favorite", headers=auth_headers)
        
        # Act
        response = client.delete(
            f"/articles/{article_id}/favorite",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == 204
    
    @pytest.mark.parametrize("page,limit,expected_status", [
        (1, 10, 200),
        (0, 10, 422),  # page must be >= 1
        (1, 101, 422),  # limit too high
        (-1, 10, 422),  # negative page
    ])
    def test_get_articles_validation(self, client, auth_headers, page, limit, expected_status):
        """Test: validación de parámetros de paginación"""
        # Act
        response = client.get(
            "/articles",
            headers=auth_headers,
            params={"page": page, "limit": limit}
        )
        
        # Assert
        assert response.status_code == expected_status

@pytest.mark.integration
class TestUserAPI:
    """Ejemplos de testing de endpoints de usuario"""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_user_registration_success(self, client):
        """Test: registro exitoso de usuario"""
        # Arrange
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        
        # Act
        response = client.post("/users/register", json=user_data)
        
        # Assert
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "created_at" in data
        
        # Password should not be returned
        assert "password" not in data
        assert "password_hash" not in data
    
    def test_user_registration_duplicate_email(self, client, setup_test_db):
        """Test: registro con email duplicado"""
        # Arrange
        user_data = {
            "email": "existing@example.com",
            "password": "securepassword123",
            "full_name": "Existing User"
        }
        
        # Create user first
        client.post("/users/register", json=user_data)
        
        # Act - Try to create same user again
        response = client.post("/users/register", json=user_data)
        
        # Assert
        assert response.status_code == 409
        assert "email" in response.json()["detail"].lower()
    
    def test_user_login_success(self, client):
        """Test: login exitoso"""
        # Arrange - First register a user
        user_data = {
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User"
        }
        client.post("/users/register", json=user_data)
        
        # Act
        login_data = {
            "email": "test@example.com",
            "password": "securepassword123"
        }
        response = client.post("/users/login", json=login_data)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        
        # Verify token is JWT-like (basic check)
        token = data["access_token"]
        assert len(token.split(".")) == 3  # JWT format
    
    def test_user_login_invalid_credentials(self, client):
        """Test: login con credenciales inválidas"""
        # Arrange
        login_data = {
            "email": "test@example.com",
            "password": "wrongpassword"
        }
        
        # Act
        response = client.post("/users/login", json=login_data)
        
        # Assert
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()
    
    def test_get_user_profile(self, client, auth_headers):
        """Test: obtener perfil de usuario"""
        # Act
        response = client.get("/users/profile", headers=auth_headers)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "preferences" in data
        assert "created_at" in data
    
    def test_update_user_preferences(self, client, auth_headers):
        """Test: actualizar preferencias de usuario"""
        # Arrange
        preferences = {
            "categories": ["technology", "science"],
            "sources": ["TechCrunch", "Reuters"],
            "notification_frequency": "daily"
        }
        
        # Act
        response = client.put(
            "/users/preferences",
            headers=auth_headers,
            json=preferences
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        assert data["categories"] == ["technology", "science"]
        assert data["sources"] == ["TechCrunch", "Reuters"]
        assert data["notification_frequency"] == "daily"
```

### 3. Tests Frontend (React/Vitest)

#### Component Testing Pattern
```typescript
// Ejemplo: NewsCard.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NewsCard } from '../NewsCard';
import { Article } from '@/types/article';

describe('NewsCard Component', () => {
  const mockArticle: Article = {
    id: '1',
    title: 'Test Article Title',
    description: 'Test article description',
    content: 'Full test article content...',
    url: 'https://example.com/article',
    urlToImage: 'https://example.com/image.jpg',
    publishedAt: '2023-01-01T00:00:00Z',
    source: {
      id: 'test-source',
      name: 'Test Source'
    },
    author: 'Test Author',
    category: 'technology'
  };

  const mockProps = {
    article: mockArticle,
    onFavorite: vi.fn(),
    onShare: vi.fn(),
    isFavorite: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render article information correctly', () => {
    // Arrange & Act
    render(<NewsCard {...mockProps} />);
    
    // Assert
    expect(screen.getByText('Test Article Title')).toBeInTheDocument();
    expect(screen.getByText('Test article description')).toBeInTheDocument();
    expect(screen.getByText('Test Author')).toBeInTheDocument();
    expect(screen.getByText('Test Source')).toBeInTheDocument();
  });

  it('should display formatted date', () => {
    // Arrange & Act
    render(<NewsCard {...mockProps} />);
    
    // Assert
    expect(screen.getByText(/Jan 1, 2023/)).toBeInTheDocument();
  });

  it('should show favorite button when not favorited', () => {
    // Arrange & Act
    render(<NewsCard {...mockProps} isFavorite={false} />);
    
    // Assert
    const favoriteButton = screen.getByLabelText(/add to favorites/i);
    expect(favoriteButton).toBeInTheDocument();
    expect(screen.queryByLabelText(/remove from favorites/i)).not.toBeInTheDocument();
  });

  it('should show different button when favorited', () => {
    // Arrange & Act
    render(<NewsCard {...mockProps} isFavorite={true} />);
    
    // Assert
    expect(screen.getByLabelText(/remove from favorites/i)).toBeInTheDocument();
    expect(screen.queryByLabelText(/add to favorites/i)).not.toBeInTheDocument();
  });

  it('should call onFavorite when favorite button is clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    render(<NewsCard {...mockProps} />);
    
    // Act
    const favoriteButton = screen.getByLabelText(/add to favorites/i);
    await user.click(favoriteButton);
    
    // Assert
    expect(mockProps.onFavorite).toHaveBeenCalledTimes(1);
    expect(mockProps.onFavorite).toHaveBeenCalledWith(mockArticle.id);
  });

  it('should call onShare when share button is clicked', async () => {
    // Arrange
    const user = userEvent.setup();
    
    // Mock navigator.share
    Object.assign(navigator, {
      share: vi.fn()
    });
    
    render(<NewsCard {...mockProps} />);
    
    // Act
    const shareButton = screen.getByLabelText(/share article/i);
    await user.click(shareButton);
    
    // Assert
    expect(navigator.share).toHaveBeenCalledTimes(1);
    expect(navigator.share).toHaveBeenCalledWith({
      title: mockArticle.title,
      text: mockArticle.description,
      url: mockArticle.url
    });
  });

  it('should handle missing image gracefully', () => {
    // Arrange
    const articleWithoutImage = {
      ...mockArticle,
      urlToImage: undefined
    };
    
    // Act
    render(<NewsCard {...mockProps} article={articleWithoutImage} />);
    
    // Assert
    const image = screen.queryByRole('img');
    expect(image).not.toBeInTheDocument();
    
    // Should show placeholder
    expect(screen.getByText(/no image available/i)).toBeInTheDocument();
  });

  it('should truncate long content', () => {
    // Arrange
    const articleWithLongContent = {
      ...mockArticle,
      description: 'A'.repeat(200) // Very long description
    };
    
    // Act
    render(<NewsCard {...mockProps} article={articleWithLongContent} />);
    
    // Assert
    const description = screen.getByText(/^A{3}\.{3}/); // Should start with "A..." 
    expect(description).toBeInTheDocument();
  });

  it('should display loading state', () => {
    // Arrange & Act
    render(<NewsCard {...mockProps} isLoading={true} />);
    
    // Assert
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(screen.queryByText('Test Article Title')).not.toBeInTheDocument();
  });

  it('should handle click to open article', async () => {
    // Arrange
    const user = userEvent.setup();
    
    // Mock window.open
    Object.assign(window, {
      open: vi.fn()
    });
    
    render(<NewsCard {...mockProps} />);
    
    // Act
    const articleCard = screen.getByRole('article');
    await user.click(articleCard);
    
    // Assert
    expect(window.open).toHaveBeenCalledTimes(1);
    expect(window.open).toHaveBeenCalledWith(
      mockArticle.url,
      '_blank',
      'noopener,noreferrer'
    );
  });

  it('should handle external link with proper attributes', () => {
    // Arrange & Act
    render(<NewsCard {...mockProps} />);
    
    // Assert
    const externalLink = screen.getByText('Test Source');
    expect(externalLink.closest('a')).toHaveAttribute('target', '_blank');
    expect(externalLink.closest('a')).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('should apply correct CSS classes', () => {
    // Arrange & Act
    const { container } = render(<NewsCard {...mockProps} />);
    
    // Assert
    expect(container.firstChild).toHaveClass('news-card');
    expect(container.firstChild).toHaveClass('news-card--tech');
  });
});
```

#### Hook Testing Pattern
```typescript
// Ejemplo: useNewsSearch.test.ts
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { act } from 'react-dom/test-utils';
import { useNewsSearch } from '../useNewsSearch';
import * as newsApi from '@/services/newsApi';

// Mock the news API
vi.mock('@/services/newsApi', () => ({
  searchArticles: vi.fn(),
  getPopularArticles: vi.fn()
}));

describe('useNewsSearch Hook', () => {
  const mockSearchResults = {
    articles: [
      {
        id: '1',
        title: 'Test Article',
        description: 'Test description',
        url: 'https://example.com',
        publishedAt: '2023-01-01T00:00:00Z'
      }
    ],
    total: 1,
    page: 1,
    hasMore: false
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with default state', () => {
    // Arrange & Act
    const { result } = renderHook(() => useNewsSearch());
    
    // Assert
    expect(result.current.articles).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.hasMore).toBe(true);
    expect(result.current.searchQuery).toBe('');
  });

  it('should search articles successfully', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    mockSearch.mockResolvedValue(mockSearchResults);
    
    const { result } = renderHook(() => useNewsSearch());
    
    // Act
    act(() => {
      result.current.searchArticles('technology');
    });
    
    // Assert initial loading state
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBe(null);
    
    // Wait for search to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert final state
    expect(result.current.articles).toEqual(mockSearchResults.articles);
    expect(result.current.searchQuery).toBe('technology');
    expect(result.current.error).toBe(null);
    expect(result.current.hasMore).toBe(mockSearchResults.hasMore);
    
    // Verify API call
    expect(mockSearch).toHaveBeenCalledTimes(1);
    expect(mockSearch).toHaveBeenCalledWith('technology', 1, 20, {});
  });

  it('should handle search error', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    const error = new Error('Search failed');
    mockSearch.mockRejectedValue(error);
    
    const { result } = renderHook(() => useNewsSearch());
    
    // Act
    act(() => {
      result.current.searchArticles('invalid query');
    });
    
    // Wait for error
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.error).toBe('Search failed');
    expect(result.current.articles).toEqual([]);
    expect(result.current.loading).toBe(false);
  });

  it('should load more articles', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    mockSearch.mockResolvedValue(mockSearchResults);
    
    const { result } = renderHook(() => useNewsSearch());
    
    // First search
    act(() => {
      result.current.searchArticles('technology');
    });
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Reset mock to simulate different results for page 2
    mockSearch.mockResolvedValue({
      ...mockSearchResults,
      articles: [
        ...mockSearchResults.articles,
        { id: '2', title: 'Article 2', description: 'Desc 2', url: 'https://2.com', publishedAt: '2023-01-02T00:00:00Z' }
      ],
      page: 2,
      hasMore: false
    });
    
    // Act - Load more
    act(() => {
      result.current.loadMore();
    });
    
    // Wait for load more to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.articles).toHaveLength(2);
    expect(mockSearch).toHaveBeenCalledTimes(2);
    expect(mockSearch).toHaveBeenLastCalledWith('technology', 2, 20, {});
  });

  it('should not load more when already loading or no more articles', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    mockSearch.mockResolvedValue(mockSearchResults);
    
    const { result } = renderHook(() => useNewsSearch());
    
    // Perform initial search
    act(() => {
      result.current.searchArticles('technology');
    });
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Set hasMore to false
    act(() => {
      result.current.setHasMore(false);
    });
    
    // Act - Try to load more
    act(() => {
      result.current.loadMore();
    });
    
    // Assert - Should not call API again
    expect(mockSearch).toHaveBeenCalledTimes(1); // Only initial search
    
    // Test when loading
    act(() => {
      result.current.setLoading(true);
    });
    
    act(() => {
      result.current.loadMore();
    });
    
    expect(mockSearch).toHaveBeenCalledTimes(1); // Still only initial search
  });

  it('should handle filters correctly', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    mockSearch.mockResolvedValue(mockSearchResults);
    
    const { result } = renderHook(() => useNewsSearch());
    
    // Act
    act(() => {
      result.current.searchArticles('tech', {
        category: 'technology',
        source: 'TechCrunch',
        dateRange: {
          from: '2023-01-01',
          to: '2023-01-31'
        }
      });
    });
    
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(mockSearch).toHaveBeenCalledWith(
      'tech',
      1,
      20,
      {
        category: 'technology',
        source: 'TechCrunch',
        dateRange: {
          from: '2023-01-01',
          to: '2023-01-31'
        }
      }
    );
  });

  it('should cancel search when query changes', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    let resolveCount = 0;
    mockSearch.mockImplementation(() => {
      return new Promise(resolve => {
        setTimeout(() => {
          resolveCount++;
          resolve(mockSearchResults);
        }, 100);
      });
    });
    
    const { result } = renderHook(() => useNewsSearch());
    
    // Act - Start first search
    act(() => {
      result.current.searchArticles('query1');
    });
    
    // Wait a bit
    await new Promise(resolve => setTimeout(resolve, 50));
    
    // Start second search (should cancel first)
    act(() => {
      result.current.searchArticles('query2');
    });
    
    // Wait for second search to complete
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    
    // Assert
    expect(result.current.searchQuery).toBe('query2');
    // First search should be cancelled (implementation depends on your hook)
  });

  it('should debounce search queries', async () => {
    // Arrange
    const mockSearch = vi.mocked(newsApi.searchArticles);
    mockSearch.mockResolvedValue(mockSearchResults);
    
    const { result } = renderHook(() => useNewsSearch());
    
    // Act - Type multiple times quickly
    act(() => {
      result.current.setSearchQuery('t');
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    act(() => {
      result.current.setSearchQuery('te');
    });
    
    await new Promise(resolve => setTimeout(resolve, 100));
    
    act(() => {
      result.current.setSearchQuery('tech');
    });
    
    // Wait for debounce
    await new Promise(resolve => setTimeout(resolve, 300));
    
    // Assert
    expect(mockSearch).toHaveBeenCalledTimes(1);
    expect(mockSearch).toHaveBeenCalledWith('tech', 1, 20, {});
  });
});
```

Esta documentación proporciona ejemplos concretos de cómo escribir tests efectivos para diferentes tipos de componentes en el AI News Aggregator. Cada ejemplo incluye:

1. **Tests de éxito**: Casos donde todo funciona correctamente
2. **Tests de error**: Manejo de errores y casos excepcionales  
3. **Tests de validación**: Verificación de inputs y parámetros
4. **Tests de integración**: Testing de componentes trabajando juntos
5. **Tests de performance**: Cuando corresponde

Los ejemplos muestran:
- ✅ **Arrange-Act-Assert pattern**
- ✅ **Proper mocking strategies**
- ✅ **Parametrized tests**
- ✅ **Error handling testing**
- ✅ **Async testing patterns**
- ✅ **State management testing**
- ✅ **User interaction testing**

Estos patrones deben servir como referencia para escribir tests consistentes y efectivos en todo el proyecto.
