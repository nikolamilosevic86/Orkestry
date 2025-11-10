"""
Docker setup utilities for PostgreSQL and Qdrant.

This module handles automatic installation and configuration of required
services using Docker.
"""

import logging
import time
from typing import Optional, Tuple

import docker
from docker.errors import APIError, DockerException, ImageNotFound, NotFound

logger = logging.getLogger(__name__)


class DockerSetup:
    """
    Manages Docker containers for Orkestry dependencies.
    
    Handles automatic setup and configuration of PostgreSQL and Qdrant
    containers based on environment configuration.
    """

    def __init__(
        self,
        postgres_config: dict,
        qdrant_config: dict,
        network_name: str = "orkestry_network",
    ) -> None:
        """
        Initialize Docker setup manager.
        
        Args:
            postgres_config: PostgreSQL configuration (host, port, user, password, db)
            qdrant_config: Qdrant configuration (host, port)
            network_name: Docker network name for container communication
        """
        self.postgres_config = postgres_config
        self.qdrant_config = qdrant_config
        self.network_name = network_name
        
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def _ensure_network(self) -> None:
        """Create Docker network if it doesn't exist."""
        try:
            self.client.networks.get(self.network_name)
            logger.info(f"Docker network '{self.network_name}' already exists")
        except NotFound:
            logger.info(f"Creating Docker network '{self.network_name}'")
            self.client.networks.create(self.network_name, driver="bridge")

    def _container_exists(self, container_name: str) -> bool:
        """
        Check if a container exists.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if container exists, False otherwise
        """
        try:
            self.client.containers.get(container_name)
            return True
        except NotFound:
            return False

    def _container_is_running(self, container_name: str) -> bool:
        """
        Check if a container is running.
        
        Args:
            container_name: Name of the container
            
        Returns:
            True if container is running, False otherwise
        """
        try:
            container = self.client.containers.get(container_name)
            return container.status == "running"
        except NotFound:
            return False

    def setup_postgres(self) -> Tuple[bool, Optional[str]]:
        """
        Setup PostgreSQL container.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        container_name = "orkestry_postgres"
        
        try:
            # Check if container already exists
            if self._container_exists(container_name):
                if self._container_is_running(container_name):
                    logger.info(f"PostgreSQL container '{container_name}' is already running")
                    return True, None
                else:
                    logger.info(f"Starting existing PostgreSQL container '{container_name}'")
                    container = self.client.containers.get(container_name)
                    container.start()
                    time.sleep(3)  # Wait for startup
                    return True, None
            
            # Create network if needed
            self._ensure_network()
            
            # Create and start new container
            logger.info(f"Creating PostgreSQL container '{container_name}'")
            container = self.client.containers.run(
                "postgres:16-alpine",
                name=container_name,
                environment={
                    "POSTGRES_USER": self.postgres_config["user"],
                    "POSTGRES_PASSWORD": self.postgres_config["password"],
                    "POSTGRES_DB": self.postgres_config["db"],
                },
                ports={f"5432/tcp": self.postgres_config["port"]},
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
            )
            
            # Wait for PostgreSQL to be ready
            logger.info("Waiting for PostgreSQL to be ready...")
            time.sleep(5)
            
            logger.info(f"PostgreSQL container '{container_name}' started successfully")
            return True, None
            
        except ImageNotFound:
            error_msg = "PostgreSQL Docker image not found. Pulling..."
            logger.warning(error_msg)
            try:
                self.client.images.pull("postgres:16-alpine")
                return self.setup_postgres()  # Retry after pulling
            except APIError as e:
                error_msg = f"Failed to pull PostgreSQL image: {e}"
                logger.error(error_msg)
                return False, error_msg
                
        except APIError as e:
            error_msg = f"Docker API error setting up PostgreSQL: {e}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error setting up PostgreSQL: {e}"
            logger.error(error_msg)
            return False, error_msg

    def setup_qdrant(self) -> Tuple[bool, Optional[str]]:
        """
        Setup Qdrant container.
        
        Returns:
            Tuple of (success: bool, error_message: Optional[str])
        """
        container_name = "orkestry_qdrant"
        
        try:
            # Check if container already exists
            if self._container_exists(container_name):
                if self._container_is_running(container_name):
                    logger.info(f"Qdrant container '{container_name}' is already running")
                    return True, None
                else:
                    logger.info(f"Starting existing Qdrant container '{container_name}'")
                    container = self.client.containers.get(container_name)
                    container.start()
                    time.sleep(2)  # Wait for startup
                    return True, None
            
            # Create network if needed
            self._ensure_network()
            
            # Create and start new container
            logger.info(f"Creating Qdrant container '{container_name}'")
            container = self.client.containers.run(
                "qdrant/qdrant:latest",
                name=container_name,
                ports={
                    f"6333/tcp": self.qdrant_config["port"],
                    f"6334/tcp": 6334,  # gRPC port
                },
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
            )
            
            # Wait for Qdrant to be ready
            logger.info("Waiting for Qdrant to be ready...")
            time.sleep(3)
            
            logger.info(f"Qdrant container '{container_name}' started successfully")
            return True, None
            
        except ImageNotFound:
            error_msg = "Qdrant Docker image not found. Pulling..."
            logger.warning(error_msg)
            try:
                self.client.images.pull("qdrant/qdrant:latest")
                return self.setup_qdrant()  # Retry after pulling
            except APIError as e:
                error_msg = f"Failed to pull Qdrant image: {e}"
                logger.error(error_msg)
                return False, error_msg
                
        except APIError as e:
            error_msg = f"Docker API error setting up Qdrant: {e}"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Unexpected error setting up Qdrant: {e}"
            logger.error(error_msg)
            return False, error_msg

    def setup_all(self) -> Tuple[bool, list[str]]:
        """
        Setup all required Docker containers.
        
        Returns:
            Tuple of (all_success: bool, error_messages: list[str])
        """
        errors = []
        
        # Setup PostgreSQL
        postgres_success, postgres_error = self.setup_postgres()
        if not postgres_success and postgres_error:
            errors.append(f"PostgreSQL: {postgres_error}")
        
        # Setup Qdrant
        qdrant_success, qdrant_error = self.setup_qdrant()
        if not qdrant_success and qdrant_error:
            errors.append(f"Qdrant: {qdrant_error}")
        
        all_success = postgres_success and qdrant_success
        
        if all_success:
            logger.info("All Docker containers setup successfully")
        else:
            logger.error(f"Docker setup completed with errors: {errors}")
        
        return all_success, errors

    def stop_all(self) -> None:
        """Stop all Orkestry Docker containers."""
        for container_name in ["orkestry_postgres", "orkestry_qdrant"]:
            try:
                if self._container_exists(container_name):
                    container = self.client.containers.get(container_name)
                    if container.status == "running":
                        logger.info(f"Stopping container '{container_name}'")
                        container.stop()
            except Exception as e:
                logger.error(f"Error stopping container '{container_name}': {e}")

    def remove_all(self) -> None:
        """Remove all Orkestry Docker containers."""
        self.stop_all()
        
        for container_name in ["orkestry_postgres", "orkestry_qdrant"]:
            try:
                if self._container_exists(container_name):
                    logger.info(f"Removing container '{container_name}'")
                    container = self.client.containers.get(container_name)
                    container.remove()
            except Exception as e:
                logger.error(f"Error removing container '{container_name}': {e}")
