# Orkestry

**A Model Context Protocol (MCP) Server Registry and Agent Orchestration Platform**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Orkestry is a production-ready service that enables **discovery of MCP servers** and facilitates seamless communication between tools, agents, and services through intelligent orchestration.

## 🎯 Vision

Orkestry aims to be the central nervous system for AI agent ecosystems, providing:

- **Discovery**: Find the right MCP server or agent for any task using semantic search
- **Communication**: Facilitate easy interaction between agents, tools, and services
- **Orchestration**: Coordinate complex multi-agent workflows and tool invocations
- **Registry**: Maintain a comprehensive, searchable catalog of capabilities

## ✨ Current Features

### MCP Server Registry (v0.1)

The initial release focuses on MCP server discovery and management:

- 🔍 **Semantic Search**: Vector-based search to find MCP servers by task description
- 📝 **Server Registration**: Register MCP servers with rich metadata and capabilities
- 🔐 **Authentication**: Secure JWT-based authentication with role-based access control
- 🎯 **Smart Matching**: AI-powered embedding models match queries to relevant servers
- 🔄 **Proxy Functionality**: Route requests to appropriate MCP servers transparently
- 🐳 **Easy Deployment**: Automatic Docker setup for all dependencies
- 📊 **API-First Design**: RESTful API with comprehensive OpenAPI documentation
- 🛡️ **Production-Ready**: Rate limiting, CORS, security best practices built-in

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Orkestry Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────┐         ┌──────────────────┐           │
│  │User management │ ◄─────► │  Vector Search   │           │
│  │  (PostgreSQL)  │         │    (Qdrant)      │           │
│  └────────────────┘         └──────────────────┘           │
│          ▲                           ▲                       │
│          │                           │                       │
│  ┌───────┴────────────────────────────┴────────┐           │
│  │        FastAPI Server (server.py)           │           │
│  │  ┌──────────────────────────────────────┐   │           │
│  │  │     Authentication & Authorization   │   │           │
│  │  └──────────────────────────────────────┘   │           │
│  │  ┌──────────────────────────────────────┐   │           │
│  │  │   MCP Discovery & Registration       │   │           │
│  │  └──────────────────────────────────────┘   │           │
│  │  ┌──────────────────────────────────────┐   │           │
│  │  │      Semantic Search Engine          │   │           │
│  │  └──────────────────────────────────────┘   │           │
│  │  ┌──────────────────────────────────────┐   │           │
│  │  │         Proxy & Routing              │   │           │
│  │  └──────────────────────────────────────┘   │           │
│  └─────────────────────────────────────────────┘           │
│                         ▲                                   │
└─────────────────────────┼───────────────────────────────────┘
                          │
                          │ HTTP/HTTPS + JWT
                          │
              ┌───────────┴──────────┐
              │                      │
         ┌────▼─────┐          ┌────▼─────┐
         │  Clients │          │   Agents │
         │  & Apps  │          │  & Tools │
         └──────────┘          └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (optional, for automatic setup)
- Git

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/nikolamilosevic86/Orkestry.git
   cd Orkestry
   ```

2. **Install dependencies**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install requirements
   pip install -r requirements.txt
   ```

3. **Configure the server**:
   ```bash
   cd server
   cp .env.example .env
   # Edit .env with your configuration (or use defaults for development)
   ```

4. **Start the server**:
   ```bash
   cd ..
   python server/run.py
   # Or: uvicorn server.server:app --host 0.0.0.0 --port 8000
   ```

5. **Verify installation**:
   ```bash
   # Check health
   curl http://localhost:8000/health
   
   # View API documentation
   open http://localhost:8000/docs
   ```

### First Steps

1. **Login** to get an access token:
   ```bash
   curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"username":"admin","password":"changeme_admin_password"}'
   ```

2. **Register an MCP server**:
   ```bash
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
   ```

3. **Search for MCP servers**:
   ```bash
   curl -X POST "http://localhost:8000/mcp/search" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "I need current weather information",
       "limit": 5
     }'
   ```

## 📚 Documentation

- **[Server Documentation](server/README.md)**: Detailed server setup, API reference, and deployment guide
- **[Quick Start Guide](server/QUICKSTART.md)**: Step-by-step getting started tutorial
- **[Implementation Details](server/IMPLEMENTATION.md)**: Technical architecture and design decisions
- **[Test Results](server/TEST_RESULTS.md)**: Test coverage and validation results
- **[API Documentation](http://localhost:8000/docs)**: Interactive OpenAPI/Swagger UI (when server is running)

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov faker

# Run all tests
pytest server/tests/ -v

# Run with coverage report
pytest server/tests/ -v --cov=server --cov-report=html

# View coverage report
open htmlcov/index.html
```

**Test Coverage**: 17 tests passing, covering authentication, user management, MCP registration, search, and proxy functionality.

## 🔒 Security

Orkestry follows **OWASP secure coding practices** and implements multiple security layers:

- ✅ JWT-based authentication with secure token handling
- ✅ Password hashing using bcrypt (industry standard)
- ✅ Input validation using Pydantic schemas
- ✅ SQL injection prevention via SQLAlchemy ORM
- ✅ XSS protection through proper output encoding
- ✅ Rate limiting to prevent abuse
- ✅ CORS configuration for cross-origin security
- ✅ Role-based access control (RBAC)
- ✅ Comprehensive logging and audit trails

**Production Deployment**: Before deploying to production, review the [Security Best Practices](server/README.md#security-best-practices) section.

## 🗺️ Roadmap

### Current Release (v0.1) ✅
- [x] MCP server registry with semantic search using Qdrant
- [x] JWT authentication and user management
- [x] RESTful API with OpenAPI documentation
- [x] Docker auto-setup for dependencies
- [x] Comprehensive test suite
- [x] Production-ready security features

### Planned Features (v0.2+)
- [ ] **Agent Discovery**: Register and discover AI agents
- [ ] **Agent Orchestration**: Coordinate multi-agent workflows
- [ ] **Capability Matching**: Advanced semantic matching algorithms
- [ ] **Metrics & Analytics**: Usage tracking and performance monitoring

### Future Vision
- **Multi-Agent Systems**: Facilitate complex agent interactions
- **Federated Registry**: Distributed MCP server discovery
- **Smart Routing**: Intelligent request routing based on context
- **Cost Optimization**: Route to most cost-effective providers
- **Quality of Service**: SLA monitoring and enforcement

## 🏛️ Design Philosophy

Orkestry follows the **Zen of Python** principles:

- **Beautiful is better than ugly**: Clean, readable code with comprehensive documentation
- **Explicit is better than implicit**: Clear API contracts and type hints throughout
- **Simple is better than complex**: Straightforward architecture, avoiding over-engineering
- **Readability counts**: PEP 8 compliance, Sphinx docstrings, meaningful names
- **Errors should never pass silently**: Comprehensive error handling and logging
- **In the face of ambiguity, refuse the temptation to guess**: Strong typing and validation

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

1. **Code Quality**:
   - Follow PEP 8 and PEP 20 (Zen of Python)
   - Use type hints for all functions
   - Write Sphinx-style docstrings
   - Maintain test coverage above 80%

2. **Security**:
   - Follow OWASP secure coding practices
   - Never commit secrets or credentials
   - Validate all inputs
   - Document security implications

3. **Testing**:
   - Write tests for all new features
   - Ensure existing tests pass
   - Use pytest and follow existing patterns

4. **Documentation**:
   - Update relevant documentation
   - Add docstrings to all public APIs
   - Include examples where appropriate

### Development Setup

```bash
# Clone the repository
git clone https://github.com/nikolamilosevic86/Orkestry.git
cd Orkestry

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install -r server/requirements.txt
pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Run tests
pytest server/tests/ -v

# Check code style
black server/ --check
flake8 server/
mypy server/
```

## 📦 Project Structure

```
Orkestry/
├── README.md                 # This file - project overview
├── LICENSE                   # MIT License
├── requirements.txt          # Core dependencies
├── pyproject.toml           # Project metadata
├── Makefile                 # Build automation
├── make.bat                 # Windows build automation
│
├── orc/                     # Core orchestration library (planned)
│   ├── __init__.py
│   └── orchestrator.py      # Main orchestration logic
│
├── server/                  # MCP Registry Server
│   ├── README.md            # Server documentation
│   ├── QUICKSTART.md        # Getting started guide
│   ├── IMPLEMENTATION.md    # Technical details
│   ├── requirements.txt     # Server dependencies
│   ├── .env.example         # Configuration template
│   ├── docker-compose.yml   # Docker orchestration
│   ├── Dockerfile           # Container definition
│   │
│   ├── server.py            # Main FastAPI application
│   ├── auth.py              # Authentication & authorization
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connections
│   ├── docker_setup.py      # Docker automation
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── vector_store.py      # Qdrant integration
│   └── run.py               # Server entry point
│
├── tests/                   # Core tests
│   └── test_orchestrator.py
│
└── docs/                    # Documentation
    ├── api.rst
    ├── index.rst
    └── conf.py
```

## 🔧 Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL 16
- **Vector Search**: Qdrant
- **Embeddings**: sentence-transformers (HuggingFace)
- **Authentication**: JWT with bcrypt
- **ORM**: SQLAlchemy 2.0
- **Testing**: pytest
- **Containerization**: Docker & Docker Compose
- **API Docs**: OpenAPI/Swagger

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Nikola Milosevic**

- GitHub: [@nikolamilosevic86](https://github.com/nikolamilosevic86)

## 🙏 Acknowledgments

- Built on the [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) specification
- Powered by [FastAPI](https://fastapi.tiangolo.com/)
- Vector search by [Qdrant](https://qdrant.tech/)
- Embeddings from [HuggingFace](https://huggingface.co/)

## 📞 Support

- **Documentation**: Check the [docs](docs/) folder
- **Issues**: Open an issue on [GitHub](https://github.com/nikolamilosevic86/Orkestry/issues)
- **Discussions**: Join our [GitHub Discussions](https://github.com/nikolamilosevic86/Orkestry/discussions)

---

**Note**: Orkestry is under active development. The current release (v0.1) focuses on MCP server discovery. Agent orchestration features are planned for future releases.

*Built with ❤️ following the Zen of Python*
