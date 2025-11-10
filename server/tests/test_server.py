"""
Comprehensive tests for Orkestry MCP Registry Server.

Tests cover:
- Authentication and JWT tokens
- User management
- MCP server registration and management
- Vector search functionality
- Proxy functionality
- Health checks

Run with: pytest server/tests/test_server.py -v
"""

import os
from typing import Generator
from unittest.mock import Mock, patch, MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Set test environment variables before importing app
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["QDRANT_HOST"] = "localhost"
os.environ["QDRANT_PORT"] = "6333"
os.environ["AUTO_SETUP_DOCKER"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_PASSWORD"] = "testpassword123"
os.environ["ADMIN_EMAIL"] = "admin@test.com"

# Mock VectorStore before importing app
mock_vector_store = MagicMock()
mock_vector_store.add_mcp_server = MagicMock(return_value="mock-uuid")
mock_vector_store.search_mcp_servers = MagicMock(return_value=[])
mock_vector_store.update_mcp_server = MagicMock()
mock_vector_store.delete_mcp_server = MagicMock()

from server.database import Base, get_db
from server.server import app
from server.models import User, MCPServer
from server.auth import get_password_hash

# Test database setup
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test.
    
    Yields:
        Database session for testing
    """
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database override.
    
    Args:
        db_session: Test database session
        
    Returns:
        FastAPI test client
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Mock vector store initialization
    with patch('server.server.VectorStore', return_value=mock_vector_store):
        with TestClient(app) as test_client:
            yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session: Session) -> User:
    """
    Create an admin user for testing.
    
    Args:
        db_session: Test database session
        
    Returns:
        Admin user
    """
    user = User(
        username="testadmin",
        email="admin@test.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
        is_admin=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def regular_user(db_session: Session) -> User:
    """
    Create a regular user for testing.
    
    Args:
        db_session: Test database session
        
    Returns:
        Regular user
    """
    user = User(
        username="testuser",
        email="user@test.com",
        hashed_password=get_password_hash("userpassword123"),
        is_active=True,
        is_admin=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_token(client: TestClient, admin_user: User) -> str:
    """
    Get JWT token for admin user.
    
    Args:
        client: Test client
        admin_user: Admin user
        
    Returns:
        JWT access token
    """
    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "testpassword123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def regular_token(client: TestClient, regular_user: User) -> str:
    """
    Get JWT token for regular user.
    
    Args:
        client: Test client
        regular_user: Regular user
        
    Returns:
        JWT access token
    """
    response = client.post(
        "/auth/login",
        json={"username": "testuser", "password": "userpassword123"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


# ============================
# Health & Root Tests
# ============================


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint returns basic info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["name"] == "Orkestry MCP Registry"


def test_health_endpoint(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "qdrant" in data
    assert "embedding_model" in data


# ============================
# Authentication Tests
# ============================


def test_login_success(client: TestClient, admin_user: User) -> None:
    """Test successful login."""
    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "testpassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client: TestClient, admin_user: User) -> None:
    """Test login with wrong password."""
    response = client.post(
        "/auth/login",
        json={"username": "testadmin", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient) -> None:
    """Test login with nonexistent user."""
    response = client.post(
        "/auth/login",
        json={"username": "nonexistent", "password": "password123"},
    )
    assert response.status_code == 401


# ============================
# User Management Tests
# ============================


def test_get_current_user(client: TestClient, admin_user: User, admin_token: str) -> None:
    """Test getting current user information."""
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testadmin"
    assert data["email"] == "admin@test.com"
    assert data["is_admin"] is True


def test_create_user_as_admin(client: TestClient, admin_user: User, admin_token: str) -> None:
    """Test creating a new user as admin."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "newpassword123",
            "is_admin": False,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@test.com"
    assert data["is_admin"] is False


def test_create_user_as_regular_user(
    client: TestClient, regular_user: User, regular_token: str
) -> None:
    """Test that regular users cannot create users."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {regular_token}"},
        json={
            "username": "newuser2",
            "email": "newuser2@test.com",
            "password": "newpassword123",
            "is_admin": False,
        },
    )
    assert response.status_code == 403


def test_create_duplicate_username(
    client: TestClient, admin_user: User, regular_user: User, admin_token: str
) -> None:
    """Test creating user with duplicate username."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "testuser",  # Already exists
            "email": "different@test.com",
            "password": "password123",
            "is_admin": False,
        },
    )
    assert response.status_code == 400


def test_list_users(
    client: TestClient, admin_user: User, regular_user: User, admin_token: str
) -> None:
    """Test listing all users."""
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # admin and regular user
    usernames = [user["username"] for user in data]
    assert "testadmin" in usernames
    assert "testuser" in usernames


def test_update_user(
    client: TestClient, admin_user: User, regular_user: User, admin_token: str
) -> None:
    """Test updating user information."""
    response = client.put(
        f"/users/{regular_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "updated@test.com",
            "is_active": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@test.com"
    assert data["is_active"] is False


# ============================
# MCP Server Registration Tests
# ============================


@pytest.mark.skip(reason="Requires Qdrant connection - integration test")
def test_register_mcp_server(
    client: TestClient, admin_user: User, admin_token: str
) -> None:
    """Test registering a new MCP server."""
    response = client.post(
        "/mcp/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "test-mcp-server",
            "description": "A test MCP server for unit testing",
            "endpoint_url": "https://example.com/mcp",
            "config": {
                "variables": {"api_key": "secret"},
                "capabilities": ["search", "analyze"],
            },
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-mcp-server"
    assert data["is_active"] is True
    assert "qdrant_id" in data


@pytest.mark.skip(reason="Requires Qdrant connection - integration test")
def test_register_duplicate_mcp_server(
    client: TestClient, admin_user: User, admin_token: str
) -> None:
    """Test registering MCP server with duplicate name."""
    # Register first server
    client.post(
        "/mcp/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "duplicate-server",
            "description": "First server",
            "endpoint_url": "https://example.com/mcp1",
        },
    )
    
    # Try to register duplicate
    response = client.post(
        "/mcp/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "duplicate-server",
            "description": "Second server",
            "endpoint_url": "https://example.com/mcp2",
        },
    )
    assert response.status_code == 400


@pytest.mark.skip(reason="Requires Qdrant connection - integration test")
def test_list_mcp_servers(
    client: TestClient, admin_user: User, admin_token: str
) -> None:
    """Test listing MCP servers."""
    # Register a server first
    client.post(
        "/mcp/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "list-test-server",
            "description": "Server for list test",
            "endpoint_url": "https://example.com/mcp",
        },
    )
    
    # List servers
    response = client.get(
        "/mcp/servers",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(server["name"] == "list-test-server" for server in data)


@pytest.mark.skip(reason="Requires Qdrant connection - integration test")
def test_search_mcp_servers(
    client: TestClient, admin_user: User, admin_token: str
) -> None:
    """Test semantic search for MCP servers."""
    # Register servers with different descriptions
    client.post(
        "/mcp/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "weather-server",
            "description": "Provides weather forecasts and current conditions",
            "endpoint_url": "https://example.com/weather",
        },
    )
    
    # Search for weather-related servers
    response = client.post(
        "/mcp/search",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "query": "get current weather conditions",
            "limit": 5,
            "score_threshold": 0.0,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["query"] == "get current weather conditions"


# ============================
# Authorization Tests
# ============================


def test_unauthorized_access(client: TestClient) -> None:
    """Test accessing protected endpoints without token."""
    response = client.get("/users/me")
    assert response.status_code == 403  # No authorization header


def test_invalid_token(client: TestClient) -> None:
    """Test accessing endpoints with invalid token."""
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token-12345"},
    )
    assert response.status_code == 401


def test_regular_user_cannot_access_admin_endpoints(
    client: TestClient, regular_user: User, regular_token: str
) -> None:
    """Test that regular users cannot access admin-only endpoints."""
    # Try to create a user (admin only)
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {regular_token}"},
        json={
            "username": "hacker",
            "email": "hacker@test.com",
            "password": "password123",
            "is_admin": True,
        },
    )
    assert response.status_code == 403
    
    # Try to list users (admin only)
    response = client.get(
        "/users",
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert response.status_code == 403


# ============================
# Input Validation Tests
# ============================


def test_invalid_email_format(
    client: TestClient, admin_user: User, admin_token: str
) -> None:
    """Test creating user with invalid email format."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "testuser2",
            "email": "not-an-email",
            "password": "password123",
            "is_admin": False,
        },
    )
    assert response.status_code == 422  # Validation error


def test_short_password(client: TestClient, admin_user: User, admin_token: str) -> None:
    """Test creating user with too short password."""
    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "username": "testuser3",
            "email": "test3@test.com",
            "password": "short",  # Less than 8 characters
            "is_admin": False,
        },
    )
    assert response.status_code == 422  # Validation error


def test_invalid_mcp_endpoint(
    client: TestClient, admin_user: User, admin_token: str
) -> None:
    """Test registering MCP server with invalid endpoint URL."""
    response = client.post(
        "/mcp/register",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "name": "invalid-endpoint-server",
            "description": "Server with invalid endpoint",
            "endpoint_url": "not-a-url",  # Invalid URL
        },
    )
    assert response.status_code == 422  # Validation error
