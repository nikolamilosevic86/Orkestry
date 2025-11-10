"""
Configuration management for Orkestry server.

Loads and validates configuration from environment variables using pydantic-settings.
"""

import json
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be configured via .env file or environment variables.
    """

    # Database Configuration
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="orkestry", alias="POSTGRES_DB")
    postgres_user: str = Field(default="orkestry_user", alias="POSTGRES_USER")
    postgres_password: str = Field(default="changeme", alias="POSTGRES_PASSWORD")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_collection_name: str = Field(default="mcp_servers", alias="QDRANT_COLLECTION_NAME")
    qdrant_use_https: bool = Field(default=False, alias="QDRANT_USE_HTTPS")
    qdrant_api_key: Optional[str] = Field(default=None, alias="QDRANT_API_KEY")

    # Embedding Model Configuration
    embedding_model: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2", alias="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, alias="EMBEDDING_DIMENSION")
    embedding_device: str = Field(default="cpu", alias="EMBEDDING_DEVICE")

    # Authentication & Security
    jwt_secret_key: str = Field(
        default="your-super-secret-jwt-key-change-this-in-production", alias="JWT_SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Admin User
    admin_username: str = Field(default="admin", alias="ADMIN_USERNAME")
    admin_password: str = Field(default="changeme", alias="ADMIN_PASSWORD")
    admin_email: str = Field(default="admin@orkestry.local", alias="ADMIN_EMAIL")

    # Server Configuration
    server_host: str = Field(default="0.0.0.0", alias="SERVER_HOST")
    server_port: int = Field(default=8000, alias="SERVER_PORT")
    server_reload: bool = Field(default=True, alias="SERVER_RELOAD")
    server_workers: int = Field(default=1, alias="SERVER_WORKERS")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    # Docker Configuration
    auto_setup_docker: bool = Field(default=True, alias="AUTO_SETUP_DOCKER")
    docker_network: str = Field(default="orkestry_network", alias="DOCKER_NETWORK")

    # CORS Configuration
    cors_allow_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"], alias="CORS_ALLOW_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], alias="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], alias="CORS_ALLOW_HEADERS")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, alias="RATE_LIMIT_PER_MINUTE")

    # MCP Proxy Configuration
    mcp_proxy_timeout: int = Field(default=30, alias="MCP_PROXY_TIMEOUT")
    mcp_proxy_max_response_size: int = Field(default=10, alias="MCP_PROXY_MAX_RESPONSE_SIZE")

    model_config = SettingsConfigDict(
        env_file="server/.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | List[str]) -> List[str]:
        """Parse CORS origins from JSON string or list."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("cors_allow_methods", mode="before")
    @classmethod
    def parse_cors_methods(cls, v: str | List[str]) -> List[str]:
        """Parse CORS methods from JSON string or list."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    @field_validator("cors_allow_headers", mode="before")
    @classmethod
    def parse_cors_headers(cls, v: str | List[str]) -> List[str]:
        """Parse CORS headers from JSON string or list."""
        if isinstance(v, str):
            return json.loads(v)
        return v

    def get_database_url(self) -> str:
        """
        Get the database URL.
        
        Returns:
            Database connection URL
        """
        if self.database_url:
            return self.database_url
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def get_postgres_config(self) -> dict:
        """
        Get PostgreSQL configuration for Docker setup.
        
        Returns:
            Dictionary with PostgreSQL configuration
        """
        return {
            "host": self.postgres_host,
            "port": self.postgres_port,
            "user": self.postgres_user,
            "password": self.postgres_password,
            "db": self.postgres_db,
        }

    def get_qdrant_config(self) -> dict:
        """
        Get Qdrant configuration for Docker setup.
        
        Returns:
            Dictionary with Qdrant configuration
        """
        return {
            "host": self.qdrant_host,
            "port": self.qdrant_port,
            "collection": self.qdrant_collection_name,
            "use_https": self.qdrant_use_https,
            "api_key": self.qdrant_api_key,
        }


# Global settings instance
settings = Settings()
