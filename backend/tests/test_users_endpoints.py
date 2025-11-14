"""
Test suite for user management endpoints
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import get_db
from app.db.models import Base, User, UserPreference, UserBookmark

# Test database setup
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/test_ai_news_db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Override get_db dependency
async def override_get_db():
    async with TestSessionLocal() as db:
        yield db

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
async def test_user_data():
    """Test user data for registration"""
    return {
        "username": "testuser123",
        "email": "test@example.com",
        "password": "testpassword123",
        "full_name": "Test User"
    }

@pytest.fixture
async def test_user():
    """Create a test user and return user data with token"""
    # Register user
    user_data = {
        "username": "testuser456",
        "email": "testuser@example.com",
        "password": "testpassword456",
        "full_name": "Test User 456"
    }
    
    response = client.post("/api/v1/users/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "username": "testuser456",
        "password": "testpassword456"
    }
    
    login_response = client.post("/api/v1/users/login", json=login_data)
    assert login_response.status_code == 200
    
    token_data = login_response.json()
    user_data["token"] = token_data["access_token"]
    user_data["user"] = token_data["user"]
    
    return user_data

class TestUserRegistration:
    """Test user registration endpoint"""
    
    def test_register_valid_user(self, test_user_data):
        """Test registration with valid data"""
        response = client.post("/api/v1/users/register", json=test_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        
        user = data["user"]
        assert user["username"] == test_user_data["username"]
        assert user["email"] == test_user_data["email"]
        assert user["full_name"] == test_user_data["full_name"]
        assert user["is_active"] == True
        assert user["role"] == "user"
    
    def test_register_duplicate_username(self, test_user_data):
        """Test registration with duplicate username"""
        # First registration should succeed
        response1 = client.post("/api/v1/users/register", json=test_user_data)
        assert response1.status_code == 201
        
        # Second registration with same username should fail
        response2 = client.post("/api/v1/users/register", json=test_user_data)
        assert response2.status_code == 400
        assert "Username already registered" in response2.json()["detail"]
    
    def test_register_duplicate_email(self, test_user_data):
        """Test registration with duplicate email"""
        user_data1 = test_user_data.copy()
        user_data2 = test_user_data.copy()
        user_data2["username"] = "different_user"
        
        # First registration
        response1 = client.post("/api/v1/users/register", json=user_data1)
        assert response1.status_code == 201
        
        # Second registration with same email
        response2 = client.post("/api/v1/users/register", json=user_data2)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]
    
    def test_register_invalid_email(self):
        """Test registration with invalid email"""
        user_data = {
            "username": "testuser789",
            "email": "invalid-email",
            "password": "testpassword789"
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self):
        """Test registration with short password"""
        user_data = {
            "username": "testuser_short",
            "email": "short@example.com",
            "password": "123"  # Too short
        }
        
        response = client.post("/api/v1/users/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestUserLogin:
    """Test user login endpoint"""
    
    def test_login_valid_credentials(self, test_user):
        """Test login with valid credentials"""
        login_data = {
            "username": test_user["username"],
            "password": "testpassword456"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user["username"]
    
    def test_login_invalid_username(self):
        """Test login with invalid username"""
        login_data = {
            "username": "nonexistent_user",
            "password": "somepassword"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]
    
    def test_login_invalid_password(self, test_user):
        """Test login with invalid password"""
        login_data = {
            "username": test_user["username"],
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/users/login", json=login_data)
        assert response.status_code == 401
        assert "Incorrect username or password" in response.json()["detail"]


class TestUserProfile:
    """Test user profile endpoints"""
    
    def test_get_current_user_profile(self, test_user):
        """Test getting current user profile"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 200
        
        user = response.json()
        assert user["username"] == test_user["username"]
        assert user["email"] == "testuser@example.com"
    
    def test_get_profile_without_token(self):
        """Test getting profile without authentication token"""
        response = client.get("/api/v1/users/me")
        assert response.status_code == 403  # Forbidden
    
    def test_get_profile_with_invalid_token(self):
        """Test getting profile with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        
        response = client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401  # Unauthorized
    
    def test_update_profile(self, test_user):
        """Test updating user profile"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        update_data = {
            "full_name": "Updated Test User",
            "email": "updated@example.com"
        }
        
        response = client.put("/api/v1/users/me", json=update_data, headers=headers)
        assert response.status_code == 200
        
        updated_user = response.json()
        assert updated_user["full_name"] == "Updated Test User"
        assert updated_user["email"] == "updated@example.com"


class TestUserPreferences:
    """Test user preferences endpoints"""
    
    def test_get_preferences(self, test_user):
        """Test getting user preferences"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        response = client.get("/api/v1/users/preferences", headers=headers)
        assert response.status_code == 200
        
        preferences = response.json()
        assert "preferred_sources" in preferences
        assert "preferred_topics" in preferences
        assert "sentiment_preference" in preferences
        assert preferences["language"] == "es"
    
    def test_update_preferences(self, test_user):
        """Test updating user preferences"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        preferences_data = {
            "preferred_sources": ["newsapi", "guardian"],
            "preferred_topics": ["tecnologia", "ia"],
            "sentiment_preference": "positive",
            "language": "es"
        }
        
        response = client.put("/api/v1/users/preferences", json=preferences_data, headers=headers)
        assert response.status_code == 200
        
        updated_preferences = response.json()
        assert updated_preferences["preferred_sources"] == ["newsapi", "guardian"]
        assert updated_preferences["preferred_topics"] == ["tecnologia", "ia"]
        assert updated_preferences["sentiment_preference"] == "positive"


class TestUserBookmarks:
    """Test user bookmarks endpoints"""
    
    def test_get_empty_bookmarks(self, test_user):
        """Test getting empty bookmarks list"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        response = client.get("/api/v1/users/bookmarks", headers=headers)
        assert response.status_code == 200
        
        bookmarks = response.json()
        assert isinstance(bookmarks, list)
        assert len(bookmarks) == 0
    
    def test_create_bookmark(self, test_user):
        """Test creating a new bookmark"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        bookmark_data = {
            "article_id": "123e4567-e89b-12d3-a456-426614174000",
            "title": "Test Article Title",
            "url": "https://example.com/article",
            "notes": "Test note",
            "tags": ["test", "ai"]
        }
        
        response = client.post("/api/v1/users/bookmarks", json=bookmark_data, headers=headers)
        assert response.status_code == 201
        
        bookmark = response.json()
        assert bookmark["title"] == "Test Article Title"
        assert bookmark["url"] == "https://example.com/article"
        assert bookmark["notes"] == "Test note"
        assert bookmark["tags"] == ["test", "ai"]
    
    def test_get_bookmarks_after_creation(self, test_user):
        """Test getting bookmarks after creating one"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # First create a bookmark
        bookmark_data = {
            "article_id": "456e7890-e89b-12d3-a456-426614174001",
            "title": "Another Test Article",
            "url": "https://example.com/another-article"
        }
        
        client.post("/api/v1/users/bookmarks", json=bookmark_data, headers=headers)
        
        # Then get bookmarks
        response = client.get("/api/v1/users/bookmarks", headers=headers)
        assert response.status_code == 200
        
        bookmarks = response.json()
        assert len(bookmarks) == 1
        assert bookmarks[0]["title"] == "Another Test Article"
    
    def test_delete_bookmark(self, test_user):
        """Test deleting a bookmark"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # First create a bookmark
        bookmark_data = {
            "article_id": "789e0123-e89b-12d3-a456-426614174002",
            "title": "Bookmark to Delete",
            "url": "https://example.com/delete-me"
        }
        
        create_response = client.post("/api/v1/users/bookmarks", json=bookmark_data, headers=headers)
        bookmark_id = create_response.json()["id"]
        
        # Then delete it
        delete_response = client.delete(f"/api/v1/users/bookmarks/{bookmark_id}", headers=headers)
        assert delete_response.status_code == 204
        
        # Verify it's deleted
        get_response = client.get("/api/v1/users/bookmarks", headers=headers)
        bookmarks = get_response.json()
        assert len(bookmarks) == 0


class TestAuthenticationMiddleware:
    """Test authentication requirements"""
    
    def test_unauthorized_access_to_protected_endpoints(self):
        """Test that protected endpoints require authentication"""
        protected_endpoints = [
            ("GET", "/api/v1/users/me"),
            ("PUT", "/api/v1/users/me"),
            ("GET", "/api/v1/users/preferences"),
            ("PUT", "/api/v1/users/preferences"),
            ("GET", "/api/v1/users/bookmarks"),
        ]
        
        for method, endpoint in protected_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "PUT":
                response = client.put(endpoint, json={})
            
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require authentication"
            assert response.status_code != 200, f"Endpoint {endpoint} should not be accessible without token"


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"])