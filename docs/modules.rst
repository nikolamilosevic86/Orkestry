Modules Documentation
=====================

This section contains the API reference for all Orkestry modules.

Core Modules
------------

.. toctree::
   :maxdepth: 4

   generated/orc.orchestrator

Server Documentation
--------------------

For detailed server API documentation, please refer to:

* **Server README**: `server/README.md` - Complete API reference and deployment guide
* **Quick Start**: `server/QUICKSTART.md` - Getting started tutorial  
* **Implementation**: `server/IMPLEMENTATION.md` - Technical architecture details
* **Interactive API Docs**: http://localhost:8000/docs (when server is running)

The server modules include:

* ``server.server`` - Main FastAPI application with all endpoints
* ``server.auth`` - JWT authentication and authorization
* ``server.config`` - Configuration management via Pydantic
* ``server.database`` - PostgreSQL connection and ORM models
* ``server.docker_setup`` - Automatic Docker container setup
* ``server.models`` - SQLAlchemy database models
* ``server.schemas`` - Pydantic request/response schemas
* ``server.vector_store`` - Qdrant vector database integration
