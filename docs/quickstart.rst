Quick Start Guide
=================

This guide will help you get started with Orkestry MCP Registry Server.

Prerequisites
-------------

* Python 3.11 or higher
* Docker and Docker Compose (optional, for automatic setup)
* Git

Installation
------------

1. Clone the repository::

    git clone https://github.com/nikolamilosevic86/Orkestry.git
    cd Orkestry

2. Create and activate virtual environment::

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate

3. Install dependencies::

    pip install -r requirements.txt

4. Configure the server::

    cd server
    cp .env.example .env
    # Edit .env with your configuration (or use defaults for development)

5. Start the server::

    cd ..
    python server/run.py

6. Verify installation::

    curl http://localhost:8000/health

First Steps
-----------

Login
~~~~~

Get an access token::

    curl -X POST "http://localhost:8000/auth/login" \
      -H "Content-Type: application/json" \
      -d '{"username":"admin","password":"changeme_admin_password"}'

Register an MCP Server
~~~~~~~~~~~~~~~~~~~~~~

Register your first MCP server::

    curl -X POST "http://localhost:8000/mcp/register" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "weather-service",
        "description": "Provides weather forecasts and current conditions",
        "endpoint_url": "https://api.weather.com/mcp",
        "config": {
          "capabilities": ["forecast", "current"],
          "tags": ["weather", "climate"]
        }
      }'

Search for MCP Servers
~~~~~~~~~~~~~~~~~~~~~~

Find relevant MCP servers using semantic search::

    curl -X POST "http://localhost:8000/mcp/search" \
      -H "Authorization: Bearer YOUR_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "query": "I need current weather information",
        "limit": 5
      }'

View API Documentation
~~~~~~~~~~~~~~~~~~~~~~

Access the interactive API documentation at:

* Swagger UI: http://localhost:8000/docs
* ReDoc: http://localhost:8000/redoc

Configuration
-------------

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

All configuration is managed via the ``.env`` file:

Database Configuration::

    POSTGRES_HOST=localhost
    POSTGRES_PORT=5432
    POSTGRES_DB=orkestry
    POSTGRES_USER=orkestry_user
    POSTGRES_PASSWORD=changeme_secure_password

Qdrant Configuration::

    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    QDRANT_COLLECTION_NAME=mcp_servers

Embedding Model::

    EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
    EMBEDDING_DIMENSION=384
    EMBEDDING_DEVICE=cpu

Authentication::

    JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=changeme_admin_password

Docker Auto-Setup
~~~~~~~~~~~~~~~~~

Set ``AUTO_SETUP_DOCKER=true`` to automatically install and start PostgreSQL and Qdrant via Docker.

Testing
-------

Run the test suite::

    pip install pytest pytest-asyncio pytest-cov faker
    pytest server/tests/ -v

Run with coverage::

    pytest server/tests/ -v --cov=server --cov-report=html

Security
--------

Before deploying to production:

1. Change all default passwords
2. Generate a secure JWT secret key
3. Configure HTTPS/SSL
4. Set up proper CORS origins
5. Review rate limiting settings

See the :doc:`api` section for detailed security best practices.

Next Steps
----------

* Read the full :doc:`api` documentation
* Explore the API endpoints at http://localhost:8000/docs
* Review the security checklist in server/README.md
* Join the community discussions on GitHub
