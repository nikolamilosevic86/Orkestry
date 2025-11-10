.. Orkestry documentation master file, created by
   sphinx-quickstart on Tue Oct  7 16:14:13 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Orkestry Documentation
======================

**A Model Context Protocol (MCP) Server Registry and Agent Orchestration Platform**

Orkestry is a production-ready service that enables discovery of MCP servers and 
facilitates seamless communication between tools, agents, and services through 
intelligent orchestration.

Vision
------

Orkestry aims to be the central nervous system for AI agent ecosystems, providing:

* **Discovery**: Find the right MCP server or agent for any task using semantic search
* **Communication**: Facilitate easy interaction between agents, tools, and services
* **Orchestration**: Coordinate complex multi-agent workflows and tool invocations
* **Registry**: Maintain a comprehensive, searchable catalog of capabilities

Quick Start
-----------

Installation::

    git clone https://github.com/nikolamilosevic86/Orkestry.git
    cd Orkestry
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd server
    cp .env.example .env
    cd ..
    python server/run.py

Access the API documentation at http://localhost:8000/docs

Current Features (v0.1)
-----------------------

* 🔍 **Semantic Search**: Vector-based search to find MCP servers by task description
* 📝 **Server Registration**: Register MCP servers with rich metadata and capabilities
* 🔐 **Authentication**: Secure JWT-based authentication with role-based access control
* 🎯 **Smart Matching**: AI-powered embedding models match queries to relevant servers
* 🔄 **Proxy Functionality**: Route requests to appropriate MCP servers transparently
* 🐳 **Easy Deployment**: Automatic Docker setup for all dependencies
* 📊 **API-First Design**: RESTful API with comprehensive OpenAPI documentation
* 🛡️ **Production-Ready**: Rate limiting, CORS, security best practices built-in

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Guide:

   quickstart
   api

.. toctree::
   :maxdepth: 2
   :caption: API Reference:

   modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

API Modules
===========

Core Orchestration
------------------

.. autosummary::
   :toctree: generated
   :recursive:

   orc.orchestrator

