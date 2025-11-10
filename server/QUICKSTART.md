# Orkestry MCP Registry - Quick Start Guide

This guide will get you up and running with the Orkestry MCP Registry Server in under 5 minutes.

## Prerequisites

- Python 3.11 or higher
- Docker (optional, but recommended for easy setup)

## Installation Steps

### 1. Install Dependencies

```bash
cd server
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration (IMPORTANT!)
nano .env  # or your preferred editor

# At minimum, change these:
# - ADMIN_PASSWORD
# - JWT_SECRET_KEY
# - POSTGRES_PASSWORD
```

### 3. Start the Server

#### Option A: Automatic Setup (Docker)

The server will automatically set up PostgreSQL and Qdrant in Docker containers:

```bash
python run.py
```

Or:

```bash
python -m server.server
```

#### Option B: Using Docker Compose

```bash
docker-compose up -d
```

#### Option C: Manual Setup

If you have PostgreSQL and Qdrant already running:

1. Set `AUTO_SETUP_DOCKER=false` in `.env`
2. Configure database and Qdrant connection settings
3. Run: `python run.py`

### 4. Verify Installation

Open your browser and visit:
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## First Steps

### 1. Login as Admin

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "changeme_admin_password"}'
```

Save the `access_token` from the response.

### 2. Register Your First MCP Server

```bash
curl -X POST http://localhost:8000/mcp/register \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "example-weather-api",
    "description": "Provides weather forecasts and current conditions",
    "endpoint_url": "https://api.weather.example.com/mcp",
    "config": {
      "variables": {"api_key": "required"},
      "capabilities": ["forecast", "current"],
      "tags": ["weather", "forecast"]
    }
  }'
```

### 3. Search for MCP Servers

```bash
curl -X POST http://localhost:8000/mcp/search \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "get weather forecast",
    "limit": 5
  }'
```

### 4. Create Additional Users (Optional)

```bash
curl -X POST http://localhost:8000/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "developer",
    "email": "dev@example.com",
    "password": "secure_password_123",
    "is_admin": false
  }'
```

## Using the Interactive API Documentation

Visit http://localhost:8000/docs for an interactive Swagger UI where you can:
1. Click "Authorize" button
2. Enter your JWT token: `Bearer YOUR_TOKEN_HERE`
3. Try out all API endpoints directly from your browser

## Common Issues

### Docker containers fail to start

```bash
# Check Docker is running
docker ps

# View logs
docker logs orkestry_postgres
docker logs orkestry_qdrant

# Restart Docker service
# macOS: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

### Import errors

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt --upgrade
```

### Port already in use

Edit `.env` and change:
```bash
SERVER_PORT=8001  # or any available port
POSTGRES_PORT=5433
QDRANT_PORT=6334
```

### Permission denied on run.py

```bash
chmod +x run.py
./run.py
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API at http://localhost:8000/docs
- Set up production deployment with proper security
- Configure custom embedding models
- Integrate with your AI applications

## Getting Help

- Check the logs: The server logs detailed information about all operations
- Use debug mode: Set `LOG_LEVEL=debug` in `.env`
- Review test examples in `tests/test_server.py`

## Security Reminder

🔒 **Before deploying to production**:
1. Change ALL default passwords
2. Generate a secure JWT secret key
3. Use HTTPS
4. Configure firewall rules
5. Enable proper CORS settings
6. Review the Security section in README.md

---

**Congratulations!** Your Orkestry MCP Registry Server is now running. 🎉
