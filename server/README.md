# Orkestry MCP Registry Server

A production-ready FastAPI server for registering, discovering, and proxying Model Context Protocol (MCP) servers using vector-based semantic search.

## Features

✨ **Core Capabilities**
- 🔐 JWT-based authentication with role-based access control
- 📝 MCP server registration with rich metadata
- 🔍 Vector-based semantic search using Qdrant
- 🎯 Configurable embedding models (default: cross-encoder/ms-marco-MiniLM-L-6-v2)
- 🔄 Proxy functionality for MCP server calls
- 🐳 Automatic Docker setup for PostgreSQL and Qdrant
- 📊 Comprehensive API documentation (OpenAPI/Swagger)
- 🛡️ Rate limiting and CORS support
- 🧪 Full test coverage

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       │ HTTPS/JWT
       ▼
┌─────────────────────────────────────┐
│     FastAPI Server (server.py)      │
│  ┌──────────────────────────────┐   │
│  │  Authentication (auth.py)    │   │
│  └──────────────────────────────┘   │
│  ┌──────────────────────────────┐   │
│  │  User Management             │   │
│  │  MCP Registry                │   │
│  │  Search & Proxy              │   │
│  └──────────────────────────────┘   │
└────┬─────────────────────┬──────────┘
     │                     │
     │                     │
     ▼                     ▼
┌─────────────┐    ┌──────────────┐
│ PostgreSQL  │    │    Qdrant    │
│  (Users &   │    │  (Vectors &  │
│   MCP DB)   │    │   Embeddings)│
└─────────────┘    └──────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for automatic setup)
- OR manually installed PostgreSQL and Qdrant

### Installation

1. **Clone the repository**:
   ```bash
   cd server
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the server**:
   ```bash
   python -m server.server
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn server.server:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Alternative docs: http://localhost:8000/redoc

### Default Admin Credentials

```
Username: admin
Password: changeme_admin_password
```

**⚠️ IMPORTANT**: Change these credentials in production!

## Configuration

All configuration is managed via environment variables in the `.env` file:

### Database Configuration

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=orkestry
POSTGRES_USER=orkestry_user
POSTGRES_PASSWORD=changeme_secure_password
```

### Qdrant Configuration

```bash
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=mcp_servers
QDRANT_USE_HTTPS=false
QDRANT_API_KEY=  # Optional
```

### Embedding Model Configuration

```bash
# HuggingFace model name
EMBEDDING_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
EMBEDDING_DIMENSION=384
EMBEDDING_DEVICE=cpu  # cpu, cuda, or mps
```

### Authentication Configuration

```bash
JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme_admin_password
ADMIN_EMAIL=admin@orkestry.local
```

### Docker Auto-Setup

```bash
AUTO_SETUP_DOCKER=true  # Set to false for manual setup
DOCKER_NETWORK=orkestry_network
```

## API Endpoints

### Authentication

#### POST `/auth/login`
Authenticate and get JWT token.

**Request**:
```json
{
  "username": "admin",
  "password": "changeme_admin_password"
}
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### User Management

#### GET `/users/me`
Get current user information (authenticated).

#### POST `/users` (Admin only)
Create a new user.

**Request**:
```json
{
  "username": "newuser",
  "email": "user@example.com",
  "password": "securepassword123",
  "is_admin": false
}
```

#### GET `/users` (Admin only)
List all users.

#### PUT `/users/{user_id}` (Admin only)
Update user information.

### MCP Server Registry

#### POST `/mcp/register`
Register a new MCP server (authenticated).

**Request**:
```json
{
  "name": "weather-api",
  "description": "Provides weather forecasts and current conditions for any location",
  "endpoint_url": "https://api.weather.com/mcp",
  "config": {
    "variables": {
      "api_key": "required"
    },
    "capabilities": ["forecast", "current", "historical"],
    "tags": ["weather", "forecast", "climate"]
  }
}
```

**Response**:
```json
{
  "id": 1,
  "name": "weather-api",
  "description": "Provides weather forecasts...",
  "endpoint_url": "https://api.weather.com/mcp",
  "config": {...},
  "qdrant_id": "550e8400-e29b-41d4-a716-446655440000",
  "registered_by": 1,
  "is_active": true,
  "created_at": "2025-11-10T12:00:00Z",
  "updated_at": "2025-11-10T12:00:00Z"
}
```

#### GET `/mcp/servers`
List all registered MCP servers (authenticated).

**Query Parameters**:
- `skip`: Number of records to skip (default: 0)
- `limit`: Maximum records to return (default: 100)
- `active_only`: Only active servers (default: true)

#### GET `/mcp/servers/{server_id}`
Get details of a specific MCP server (authenticated).

#### PUT `/mcp/servers/{server_id}`
Update MCP server (owner or admin only).

#### DELETE `/mcp/servers/{server_id}`
Delete MCP server (admin only).

### MCP Search

#### POST `/mcp/search`
Search for MCP servers using semantic similarity (authenticated).

**Request**:
```json
{
  "query": "I need to get the current weather for New York",
  "limit": 5,
  "score_threshold": 0.5
}
```

**Response**:
```json
{
  "results": [
    {
      "server": {
        "id": 1,
        "name": "weather-api",
        "description": "Provides weather forecasts...",
        "endpoint_url": "https://api.weather.com/mcp",
        ...
      },
      "score": 0.87
    }
  ],
  "query": "I need to get the current weather for New York",
  "total_found": 1
}
```

### MCP Proxy

#### POST `/mcp/proxy`
Proxy a request to an MCP server (authenticated).

**Request**:
```json
{
  "server_id": 1,
  "method": "POST",
  "path": "/forecast",
  "headers": {
    "X-API-Key": "your-api-key"
  },
  "body": {
    "location": "New York",
    "days": 7
  },
  "query_params": {
    "units": "metric"
  }
}
```

**Response**:
```json
{
  "status_code": 200,
  "headers": {...},
  "body": {
    "forecast": [...]
  },
  "server_name": "weather-api",
  "server_id": 1
}
```

### Health Check

#### GET `/health`
Check server health and connectivity.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-10T12:00:00Z",
  "database": "healthy",
  "qdrant": "healthy",
  "embedding_model": "cross-encoder/ms-marco-MiniLM-L-6-v2"
}
```

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov faker

# Run all tests
pytest server/tests/ -v

# Run with coverage
pytest server/tests/ -v --cov=server --cov-report=html

# Run specific test
pytest server/tests/test_server.py::test_login_success -v
```

**Note**: Some tests require running PostgreSQL and Qdrant. Use the `@pytest.mark.skip` decorator for integration tests.

## Security Best Practices

### Before Deployment

1. **Change default credentials**:
   ```bash
   ADMIN_PASSWORD=<strong-unique-password>
   JWT_SECRET_KEY=<cryptographically-secure-random-key>
   POSTGRES_PASSWORD=<strong-database-password>
   ```

2. **Use HTTPS in production**:
   - Deploy behind a reverse proxy (nginx, Traefik)
   - Configure SSL/TLS certificates

3. **Secure database access**:
   - Use firewall rules to restrict database access
   - Use strong passwords
   - Enable SSL for database connections

4. **Enable Qdrant authentication**:
   ```bash
   QDRANT_API_KEY=<secure-api-key>
   ```

5. **Configure CORS properly**:
   ```bash
   CORS_ALLOW_ORIGINS=["https://your-frontend-domain.com"]
   ```

6. **Set up rate limiting**:
   ```bash
   RATE_LIMIT_PER_MINUTE=60  # Adjust based on your needs
   ```

### OWASP Security Compliance

This implementation follows OWASP secure coding practices:

- ✅ Input validation using Pydantic schemas
- ✅ Password hashing with bcrypt
- ✅ JWT token-based authentication
- ✅ SQL injection prevention via SQLAlchemy ORM
- ✅ XSS prevention through proper output encoding
- ✅ CSRF protection via token authentication
- ✅ Rate limiting to prevent DoS attacks
- ✅ Secure password requirements (min 8 characters)
- ✅ Role-based access control (RBAC)
- ✅ Logging and monitoring

## Deployment

### Using Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: orkestry_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: orkestry
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - orkestry_network

  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"
      - "6334:6334"
    networks:
      - orkestry_network

  orkestry:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://orkestry_user:${POSTGRES_PASSWORD}@postgres:5432/orkestry
      - QDRANT_HOST=qdrant
      - QDRANT_PORT=6333
    depends_on:
      - postgres
      - qdrant
    networks:
      - orkestry_network

networks:
  orkestry_network:
    driver: bridge

volumes:
  postgres_data:
  qdrant_data:
```

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "server.server"]
```

Deploy:

```bash
docker-compose up -d
```

### Production Checklist

- [ ] Update all default passwords
- [ ] Generate secure JWT secret key
- [ ] Configure HTTPS/SSL
- [ ] Set up database backups
- [ ] Configure monitoring and logging
- [ ] Set up firewall rules
- [ ] Enable Qdrant authentication
- [ ] Configure proper CORS origins
- [ ] Set appropriate rate limits
- [ ] Review and test security settings
- [ ] Set up CI/CD pipeline
- [ ] Configure health check monitoring

## Troubleshooting

### Docker containers not starting

```bash
# Check Docker daemon
docker ps

# View logs
docker logs orkestry_postgres
docker logs orkestry_qdrant

# Restart containers
docker-compose down
docker-compose up -d
```

### Database connection errors

1. Verify PostgreSQL is running
2. Check credentials in `.env`
3. Ensure database exists
4. Check network connectivity

### Qdrant connection errors

1. Verify Qdrant is running on correct port
2. Check firewall rules
3. Verify collection creation

### Embedding model issues

```bash
# Clear cache and reload
rm -rf ~/.cache/huggingface

# Try different device
EMBEDDING_DEVICE=cpu  # or cuda, mps
```

## Contributing

1. Follow PEP 8 and the Zen of Python
2. Write comprehensive tests
3. Use type hints
4. Document with Sphinx-style docstrings
5. Follow secure coding practices

## License

MIT License - see LICENSE file for details.

## Author

Nikola Milosevic

## Support

For issues and questions, please open an issue on GitHub.
