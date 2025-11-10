"""
Pydantic schemas for request/response validation.

This module defines data transfer objects (DTOs) used by the FastAPI endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# ============================
# User Schemas
# ============================


class UserBase(BaseModel):
    """Base user schema with common fields."""

    username: str = Field(..., min_length=3, max_length=100, description="Unique username")
    email: EmailStr = Field(..., description="User email address")


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    is_admin: bool = Field(default=False, description="Admin privileges")


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user responses (excludes password)."""

    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================
# Authentication Schemas
# ============================


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data encoded in JWT token."""

    username: Optional[str] = None
    user_id: Optional[int] = None
    is_admin: bool = False


class LoginRequest(BaseModel):
    """Login credentials."""

    username: str
    password: str


# ============================
# MCP Server Schemas
# ============================


class MCPServerBase(BaseModel):
    """Base MCP server schema."""

    name: str = Field(..., min_length=1, max_length=255, description="MCP server name")
    description: str = Field(..., min_length=10, description="Detailed description of the server")
    endpoint_url: str = Field(..., description="Base URL for the MCP server")
    config: Optional[Dict[str, Any]] = Field(
        default=None, description="Configuration including variables, auth, etc."
    )

    @field_validator("endpoint_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that endpoint URL is properly formatted."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("endpoint_url must start with http:// or https://")
        return v


class MCPServerCreate(MCPServerBase):
    """Schema for registering a new MCP server."""

    pass


class MCPServerUpdate(BaseModel):
    """Schema for updating MCP server information."""

    description: Optional[str] = Field(None, min_length=10)
    endpoint_url: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

    @field_validator("endpoint_url")
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """Validate that endpoint URL is properly formatted."""
        if v is not None and not v.startswith(("http://", "https://")):
            raise ValueError("endpoint_url must start with http:// or https://")
        return v


class MCPServerResponse(MCPServerBase):
    """Schema for MCP server responses."""

    id: int
    qdrant_id: str
    registered_by: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================
# Search Schemas
# ============================


class MCPSearchRequest(BaseModel):
    """Request schema for searching MCP servers."""

    query: str = Field(..., min_length=3, description="Search query describing the task")
    limit: int = Field(default=5, ge=1, le=50, description="Maximum number of results")
    score_threshold: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Minimum similarity score (0-1)"
    )


class MCPSearchResult(BaseModel):
    """Single search result with score."""

    server: MCPServerResponse
    score: float = Field(..., description="Similarity score (0-1)")


class MCPSearchResponse(BaseModel):
    """Response containing search results."""

    results: List[MCPSearchResult]
    query: str
    total_found: int


# ============================
# MCP Proxy Schemas
# ============================


class MCPProxyRequest(BaseModel):
    """Request to proxy to an MCP server."""

    server_id: int = Field(..., description="ID of the MCP server to call")
    method: str = Field(..., description="HTTP method (GET, POST, etc.)")
    path: str = Field(..., description="Path to append to the server endpoint")
    headers: Optional[Dict[str, str]] = Field(default=None, description="Additional headers")
    body: Optional[Dict[str, Any]] = Field(default=None, description="Request body (for POST/PUT)")
    query_params: Optional[Dict[str, str]] = Field(default=None, description="Query parameters")


class MCPProxyResponse(BaseModel):
    """Response from proxied MCP server."""

    status_code: int
    headers: Dict[str, str]
    body: Any
    server_name: str
    server_id: int


# ============================
# Health & Status Schemas
# ============================


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    timestamp: datetime
    database: str
    qdrant: str
    embedding_model: str


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
