"""
Orkestry MCP Registry Server.

A FastAPI server for registering, discovering, and proxying Model Context Protocol (MCP) servers
using vector-based semantic search.

Features:
- JWT-based authentication with user management
- MCP server registration with metadata
- Vector-based semantic search using Qdrant
- Configurable embedding models
- Proxy functionality for MCP server calls
- Automatic Docker setup for PostgreSQL and Qdrant

Author: Nikola Milosevic
License: MIT
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from .auth import (
    authenticate_user,
    create_access_token,
    create_admin_user,
    get_current_active_user,
    get_current_admin_user,
    get_password_hash,
)
from .config import settings
from .database import check_db_connection, get_db, init_db
from .docker_setup import DockerSetup
from .models import MCPServer, User
from .schemas import (
    ErrorResponse,
    HealthResponse,
    LoginRequest,
    MCPProxyRequest,
    MCPProxyResponse,
    MCPSearchRequest,
    MCPSearchResponse,
    MCPSearchResult,
    MCPServerCreate,
    MCPServerResponse,
    MCPServerUpdate,
    Token,
    UserCreate,
    UserResponse,
    UserUpdate,
)
from .vector_store import VectorStore, get_vector_store, vector_store

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global vector store instance
vector_store: Optional["VectorStore"] = None


def get_vector_store() -> "VectorStore":
    """Get the global vector store instance."""
    if vector_store is None:
        raise RuntimeError("Vector store not initialized")
    return vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Docker setup (if enabled)
    - Database initialization
    - Vector store initialization
    - Admin user creation
    """
    # Startup
    logger.info("Starting Orkestry MCP Registry Server...")
    
    # Setup Docker containers if enabled
    if settings.auto_setup_docker:
        logger.info("Auto-setup Docker is enabled, setting up containers...")
        try:
            docker_setup = DockerSetup(
                postgres_config=settings.get_postgres_config(),
                qdrant_config=settings.get_qdrant_config(),
                network_name=settings.docker_network,
            )
            
            success, errors = docker_setup.setup_all()
            
            if not success:
                logger.error(f"Docker setup failed: {errors}")
                logger.warning("Continuing anyway - ensure services are running externally")
            else:
                logger.info("Docker containers setup successfully")
                
        except Exception as e:
            logger.error(f"Docker setup error: {e}")
            logger.warning("Continuing anyway - ensure services are running externally")
    
    # Initialize database
    try:
        init_db()
        
        # Create admin user (skip in test mode to avoid conflicts)
        if os.getenv("DATABASE_URL", "").startswith("sqlite:///./test"):
            logger.info("Test mode: skipping admin user creation")
        else:
            db = next(get_db())
            create_admin_user(db)
            db.close()
        
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
    
    # Initialize vector store
    try:
        global vector_store
        vector_store = VectorStore()
        logger.info("Vector store initialized successfully")
    except Exception as e:
        logger.error(f"Vector store initialization failed: {e}")
        raise
    
    logger.info(f"Server ready at http://{settings.server_host}:{settings.server_port}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Orkestry MCP Registry Server...")


# Create FastAPI app
app = FastAPI(
    title="Orkestry MCP Registry",
    description="MCP Server Registry with Vector-Based Discovery",
    version="0.1.0",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# ============================
# Health & Status Endpoints
# ============================


@app.get("/", response_model=Dict[str, str])
async def root() -> Dict[str, str]:
    """Root endpoint with basic API information."""
    return {
        "name": "Orkestry MCP Registry",
        "version": "0.1.0",
        "description": "MCP Server Registry with Vector-Based Discovery",
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def health_check(request: Request) -> HealthResponse:
    """
    Health check endpoint.
    
    Verifies connectivity to database and Qdrant.
    """
    db_status = "healthy" if check_db_connection() else "unhealthy"
    
    qdrant_status = "healthy"
    try:
        vs = get_vector_store()
        if not vs.check_connection():
            qdrant_status = "unhealthy"
    except Exception:
        qdrant_status = "unhealthy"
    
    return HealthResponse(
        status="healthy" if db_status == "healthy" and qdrant_status == "healthy" else "degraded",
        timestamp=datetime.utcnow(),
        database=db_status,
        qdrant=qdrant_status,
        embedding_model=settings.embedding_model,
    )


# ============================
# Authentication Endpoints
# ============================


@app.post("/auth/login", response_model=Token)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def login(request: Request, credentials: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """
    Authenticate user and return JWT token.
    
    Args:
        credentials: Username and password
        
    Returns:
        JWT access token
    """
    user = authenticate_user(db, credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user.username,
            "user_id": user.id,
            "is_admin": user.is_admin,
        }
    )
    
    logger.info(f"User '{user.username}' logged in successfully")
    
    return Token(access_token=access_token)


# ============================
# User Management Endpoints
# ============================


@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def create_user(
    request: Request,
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> UserResponse:
    """
    Create a new user (admin only).
    
    Args:
        user_data: User information
        
    Returns:
        Created user
    """
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_admin=user_data.is_admin,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"User '{new_user.username}' created by admin '{current_user.username}'")
    
    return UserResponse.model_validate(new_user)


@app.get("/users/me", response_model=UserResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_current_user_info(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Get information about the currently authenticated user."""
    return UserResponse.model_validate(current_user)


@app.get("/users", response_model=List[UserResponse])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_users(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    skip: int = 0,
    limit: int = 100,
) -> List[UserResponse]:
    """
    List all users (admin only).
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]


@app.put("/users/{user_id}", response_model=UserResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def update_user(
    request: Request,
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> UserResponse:
    """
    Update user information (admin only).
    
    Args:
        user_id: User ID to update
        user_data: Updated user data
        
    Returns:
        Updated user
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update fields
    if user_data.email is not None:
        user.email = user_data.email
    if user_data.password is not None:
        user.hashed_password = get_password_hash(user_data.password)
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.is_admin is not None:
        user.is_admin = user_data.is_admin
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"User '{user.username}' updated by admin '{current_user.username}'")
    
    return UserResponse.model_validate(user)


# ============================
# MCP Server Registry Endpoints
# ============================


@app.post("/mcp/register", response_model=MCPServerResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def register_mcp_server(
    request: Request,
    mcp_data: MCPServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MCPServerResponse:
    """
    Register a new MCP server.
    
    Creates a database entry and adds the server to the vector store for semantic search.
    
    Args:
        mcp_data: MCP server information
        
    Returns:
        Registered MCP server
    """
    # Check if name already exists
    existing = db.query(MCPServer).filter(MCPServer.name == mcp_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"MCP server with name '{mcp_data.name}' already exists",
        )
    
    # Create temporary MCP server entry (we need the ID for vector store)
    new_server = MCPServer(
        name=mcp_data.name,
        description=mcp_data.description,
        endpoint_url=mcp_data.endpoint_url,
        config=mcp_data.config,
        qdrant_id="",  # Will be updated after vector store insertion
        registered_by=current_user.id,
    )
    
    db.add(new_server)
    db.flush()  # Get the ID without committing
    
    # Add to vector store
    try:
        vs = get_vector_store()
        qdrant_id = vs.add_mcp_server(
            mcp_id=new_server.id,
            name=mcp_data.name,
            description=mcp_data.description,
            endpoint_url=mcp_data.endpoint_url,
            config=mcp_data.config,
        )
        
        # Update with Qdrant ID
        new_server.qdrant_id = qdrant_id
        db.commit()
        db.refresh(new_server)
        
        logger.info(f"MCP server '{new_server.name}' registered by user '{current_user.username}'")
        
        return MCPServerResponse.model_validate(new_server)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to register MCP server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register MCP server: {str(e)}",
        )


@app.get("/mcp/servers", response_model=List[MCPServerResponse])
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_mcp_servers(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
) -> List[MCPServerResponse]:
    """
    List all registered MCP servers.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        active_only: Only return active servers
        
    Returns:
        List of MCP servers
    """
    query = db.query(MCPServer)
    
    if active_only:
        query = query.filter(MCPServer.is_active == True)
    
    servers = query.offset(skip).limit(limit).all()
    return [MCPServerResponse.model_validate(server) for server in servers]


@app.get("/mcp/servers/{server_id}", response_model=MCPServerResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_mcp_server(
    request: Request,
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MCPServerResponse:
    """
    Get details of a specific MCP server.
    
    Args:
        server_id: MCP server ID
        
    Returns:
        MCP server details
    """
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    return MCPServerResponse.model_validate(server)


@app.put("/mcp/servers/{server_id}", response_model=MCPServerResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def update_mcp_server(
    request: Request,
    server_id: int,
    update_data: MCPServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MCPServerResponse:
    """
    Update an existing MCP server.
    
    Updates both database and vector store entries.
    
    Args:
        server_id: MCP server ID
        update_data: Updated server data
        
    Returns:
        Updated MCP server
    """
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    # Check permissions (only admin or original registrant can update)
    if not current_user.is_admin and server.registered_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges to update this server",
        )
    
    # Update fields
    updated = False
    if update_data.description is not None:
        server.description = update_data.description
        updated = True
    if update_data.endpoint_url is not None:
        server.endpoint_url = update_data.endpoint_url
        updated = True
    if update_data.config is not None:
        server.config = update_data.config
        updated = True
    if update_data.is_active is not None:
        server.is_active = update_data.is_active
        updated = True
    
    if updated:
        # Update vector store
        try:
            vs = get_vector_store()
            vs.update_mcp_server(
                qdrant_id=server.qdrant_id,
                mcp_id=server.id,
                name=server.name,
                description=server.description,
                endpoint_url=server.endpoint_url,
                config=server.config,
            )
            
            db.commit()
            db.refresh(server)
            
            logger.info(f"MCP server '{server.name}' updated by user '{current_user.username}'")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update MCP server: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update MCP server: {str(e)}",
            )
    
    return MCPServerResponse.model_validate(server)


@app.delete("/mcp/servers/{server_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def delete_mcp_server(
    request: Request,
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
) -> None:
    """
    Delete an MCP server (admin only).
    
    Removes from both database and vector store.
    
    Args:
        server_id: MCP server ID to delete
    """
    server = db.query(MCPServer).filter(MCPServer.id == server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    try:
        # Delete from vector store
        vs = get_vector_store()
        vs.delete_mcp_server(server.qdrant_id)
        
        # Delete from database
        db.delete(server)
        db.commit()
        
        logger.info(f"MCP server '{server.name}' deleted by admin '{current_user.username}'")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete MCP server: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete MCP server: {str(e)}",
        )


# ============================
# MCP Search Endpoint
# ============================


@app.post("/mcp/search", response_model=MCPSearchResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def search_mcp_servers(
    request: Request,
    search_request: MCPSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MCPSearchResponse:
    """
    Search for MCP servers using semantic similarity.
    
    Uses vector embeddings to find servers that best match the query.
    
    Args:
        search_request: Search query and parameters
        
    Returns:
        List of matching servers with similarity scores
    """
    try:
        vs = get_vector_store()
        results = vs.search_mcp_servers(
            query=search_request.query,
            limit=search_request.limit,
            score_threshold=search_request.score_threshold,
        )
        
        # Fetch full server details from database
        search_results = []
        for mcp_id, score, payload in results:
            server = db.query(MCPServer).filter(MCPServer.id == mcp_id).first()
            
            if server and server.is_active:
                search_results.append(
                    MCPSearchResult(
                        server=MCPServerResponse.model_validate(server),
                        score=score,
                    )
                )
        
        logger.info(
            f"Search query '{search_request.query}' returned {len(search_results)} results "
            f"for user '{current_user.username}'"
        )
        
        return MCPSearchResponse(
            results=search_results,
            query=search_request.query,
            total_found=len(search_results),
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}",
        )


# ============================
# MCP Proxy Endpoint
# ============================


@app.post("/mcp/proxy", response_model=MCPProxyResponse)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def proxy_mcp_request(
    request: Request,
    proxy_request: MCPProxyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MCPProxyResponse:
    """
    Proxy a request to an MCP server.
    
    Acts as a passthrough to the specified MCP server, forwarding the request
    and returning the response.
    
    Args:
        proxy_request: Proxy request details
        
    Returns:
        Response from the MCP server
    """
    # Get server details
    server = db.query(MCPServer).filter(MCPServer.id == proxy_request.server_id).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="MCP server not found",
        )
    
    if not server.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MCP server is not active",
        )
    
    # Construct full URL
    url = f"{server.endpoint_url.rstrip('/')}/{proxy_request.path.lstrip('/')}"
    
    # Prepare headers
    headers = proxy_request.headers or {}
    
    # Add query parameters
    params = proxy_request.query_params or {}
    
    try:
        async with httpx.AsyncClient(timeout=settings.mcp_proxy_timeout) as client:
            # Make the proxied request
            response = await client.request(
                method=proxy_request.method,
                url=url,
                headers=headers,
                params=params,
                json=proxy_request.body,
            )
            
            # Parse response
            try:
                response_body = response.json()
            except Exception:
                response_body = response.text
            
            logger.info(
                f"Proxied {proxy_request.method} request to '{server.name}' "
                f"for user '{current_user.username}'"
            )
            
            return MCPProxyResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                body=response_body,
                server_name=server.name,
                server_id=server.id,
            )
            
    except httpx.TimeoutException:
        logger.error(f"Proxy request to '{server.name}' timed out")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="MCP server request timed out",
        )
    except httpx.RequestError as e:
        logger.error(f"Proxy request to '{server.name}' failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to MCP server: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error during proxy request: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proxy request failed: {str(e)}",
        )


# ============================
# Error Handlers
# ============================


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions with consistent error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            detail=str(exc.detail),
        ).model_dump(mode='json'),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal server error",
            detail=str(exc) if settings.log_level.lower() == "debug" else None,
        ).model_dump(mode='json'),
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "server.server:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.server_reload,
        workers=settings.server_workers,
        log_level=settings.log_level.lower(),
    )
