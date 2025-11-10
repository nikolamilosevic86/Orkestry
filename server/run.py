#!/usr/bin/env python3
"""
Orkestry MCP Registry Server Startup Script.

This script provides a convenient way to start the server with proper error handling.
"""

import logging
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_env_file() -> None:
    """Check if .env file exists, create from example if not."""
    env_file = Path(__file__).parent / ".env"
    env_example = Path(__file__).parent / ".env.example"
    
    if not env_file.exists():
        logger.warning(".env file not found!")
        
        if env_example.exists():
            logger.info("Creating .env from .env.example...")
            env_file.write_text(env_example.read_text())
            logger.warning(
                "⚠️  IMPORTANT: Please update .env with your configuration, "
                "especially passwords and secret keys!"
            )
        else:
            logger.error(".env.example not found. Cannot create .env file.")
            sys.exit(1)


def main() -> None:
    """Main entry point."""
    logger.info("Starting Orkestry MCP Registry Server...")
    
    # Check environment configuration
    check_env_file()
    
    try:
        import uvicorn
        from server.config import settings
        
        # Log configuration
        logger.info(f"Server will start on {settings.server_host}:{settings.server_port}")
        logger.info(f"Auto-setup Docker: {settings.auto_setup_docker}")
        logger.info(f"Embedding model: {settings.embedding_model}")
        logger.info(f"Log level: {settings.log_level}")
        
        # Start server
        uvicorn.run(
            "server.server:app",
            host=settings.server_host,
            port=settings.server_port,
            reload=settings.server_reload,
            workers=settings.server_workers,
            log_level=settings.log_level.lower(),
        )
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
