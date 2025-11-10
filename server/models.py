"""
Database models for Orkestry MCP Registry.

This module defines SQLAlchemy ORM models for PostgreSQL database.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
    """
    User model for authentication and authorization.
    
    Attributes:
        id: Primary key
        username: Unique username for login
        email: User's email address
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        is_admin: Whether the user has admin privileges
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}', is_admin={self.is_admin})>"


class MCPServer(Base):
    """
    MCP Server registry model.
    
    Stores metadata about registered MCP servers. The full description
    and configuration are embedded in Qdrant for vector search.
    
    Attributes:
        id: Primary key
        name: Name of the MCP server
        description: Human-readable description of the server's purpose
        endpoint_url: Base URL for the MCP server
        config: JSON configuration (variables, authentication, etc.)
        qdrant_id: UUID of the corresponding vector in Qdrant
        registered_by: ID of the user who registered this server
        is_active: Whether the server is currently active
        created_at: Timestamp when server was registered
        updated_at: Timestamp when server was last updated
    """

    __tablename__ = "mcp_servers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=False)
    endpoint_url = Column(String(512), nullable=False)
    config = Column(JSON, nullable=True)  # Store variables, auth settings, etc.
    qdrant_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID
    registered_by = Column(Integer, nullable=False)  # User ID
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<MCPServer(name='{self.name}', endpoint='{self.endpoint_url}', active={self.is_active})>"
