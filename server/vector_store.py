"""
Vector store service for MCP server embeddings using Qdrant.

This module handles embedding generation and vector search for MCP server discovery.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple

from qdrant_client import QdrantClient
from qdrant_client.http import models
from qdrant_client.http.exceptions import UnexpectedResponse
from sentence_transformers import SentenceTransformer

from .config import settings

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Manages vector embeddings and search for MCP servers in Qdrant.
    
    Handles encoding MCP server descriptions using configurable embedding models
    and storing/searching them in Qdrant vector database.
    """

    def __init__(self) -> None:
        """Initialize the vector store with Qdrant client and embedding model."""
        # Initialize Qdrant client
        self.client = QdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            https=settings.qdrant_use_https,
            api_key=settings.qdrant_api_key,
        )
        
        self.collection_name = settings.qdrant_collection_name
        
        # Initialize embedding model
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self.encoder = SentenceTransformer(
            settings.embedding_model,
            device=settings.embedding_device,
        )
        
        # Verify/update embedding dimension
        test_embedding = self.encoder.encode("test", convert_to_tensor=False)
        actual_dimension = len(test_embedding)
        
        if actual_dimension != settings.embedding_dimension:
            logger.warning(
                f"Configured embedding dimension ({settings.embedding_dimension}) "
                f"does not match model dimension ({actual_dimension}). "
                f"Using model dimension: {actual_dimension}"
            )
            self.embedding_dimension = actual_dimension
        else:
            self.embedding_dimension = settings.embedding_dimension
        
        logger.info(f"Embedding model loaded. Dimension: {self.embedding_dimension}")
        
        # Initialize collection
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """
        Ensure the Qdrant collection exists, create if it doesn't.
        
        The collection stores vectors with metadata about MCP servers.
        """
        try:
            # Check if collection exists
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists")
        except (UnexpectedResponse, Exception):
            # Collection doesn't exist, create it
            logger.info(f"Creating collection '{self.collection_name}'")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=self.embedding_dimension,
                    distance=models.Distance.COSINE,
                ),
            )
            logger.info(f"Collection '{self.collection_name}' created successfully")

    def _create_embedding_text(self, mcp_data: Dict[str, Any]) -> str:
        """
        Create a comprehensive text representation for embedding.
        
        Combines name, description, and config fields to create a rich
        text representation for semantic search.
        
        Args:
            mcp_data: Dictionary with MCP server data (name, description, config, etc.)
            
        Returns:
            Text string for embedding
        """
        parts = [
            f"Name: {mcp_data.get('name', '')}",
            f"Description: {mcp_data.get('description', '')}",
        ]
        
        # Add config information if available
        config = mcp_data.get('config', {})
        if config:
            if 'variables' in config:
                variables = ', '.join(config['variables'].keys()) if isinstance(config['variables'], dict) else str(config['variables'])
                parts.append(f"Variables: {variables}")
            
            if 'capabilities' in config:
                capabilities = ', '.join(config['capabilities']) if isinstance(config['capabilities'], list) else str(config['capabilities'])
                parts.append(f"Capabilities: {capabilities}")
            
            if 'tags' in config:
                tags = ', '.join(config['tags']) if isinstance(config['tags'], list) else str(config['tags'])
                parts.append(f"Tags: {tags}")
        
        return ' | '.join(parts)

    def add_mcp_server(
        self,
        mcp_id: int,
        name: str,
        description: str,
        endpoint_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add an MCP server to the vector store.
        
        Args:
            mcp_id: Database ID of the MCP server
            name: Name of the MCP server
            description: Description of the server's purpose
            endpoint_url: Server endpoint URL
            config: Optional configuration dictionary
            
        Returns:
            Qdrant point ID (UUID)
        """
        # Create embedding text
        embedding_text = self._create_embedding_text({
            'name': name,
            'description': description,
            'config': config or {},
        })
        
        # Generate embedding
        logger.debug(f"Generating embedding for MCP server: {name}")
        embedding = self.encoder.encode(embedding_text, convert_to_tensor=False)
        
        # Generate UUID for this point
        point_id = str(uuid.uuid4())
        
        # Create point with payload
        point = models.PointStruct(
            id=point_id,
            vector=embedding.tolist(),
            payload={
                "mcp_id": mcp_id,
                "name": name,
                "description": description,
                "endpoint_url": endpoint_url,
                "config": config or {},
            },
        )
        
        # Insert into Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        
        logger.info(f"Added MCP server '{name}' to vector store with ID: {point_id}")
        return point_id

    def update_mcp_server(
        self,
        qdrant_id: str,
        mcp_id: int,
        name: str,
        description: str,
        endpoint_url: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Update an existing MCP server in the vector store.
        
        Args:
            qdrant_id: Qdrant point ID
            mcp_id: Database ID of the MCP server
            name: Name of the MCP server
            description: Description of the server's purpose
            endpoint_url: Server endpoint URL
            config: Optional configuration dictionary
        """
        # Create embedding text
        embedding_text = self._create_embedding_text({
            'name': name,
            'description': description,
            'config': config or {},
        })
        
        # Generate embedding
        logger.debug(f"Updating embedding for MCP server: {name}")
        embedding = self.encoder.encode(embedding_text, convert_to_tensor=False)
        
        # Update point
        point = models.PointStruct(
            id=qdrant_id,
            vector=embedding.tolist(),
            payload={
                "mcp_id": mcp_id,
                "name": name,
                "description": description,
                "endpoint_url": endpoint_url,
                "config": config or {},
            },
        )
        
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )
        
        logger.info(f"Updated MCP server '{name}' in vector store")

    def search_mcp_servers(
        self,
        query: str,
        limit: int = 5,
        score_threshold: float = 0.0,
    ) -> List[Tuple[int, float, Dict[str, Any]]]:
        """
        Search for MCP servers based on semantic similarity.
        
        Args:
            query: Search query describing the desired task/capability
            limit: Maximum number of results to return
            score_threshold: Minimum similarity score (0-1)
            
        Returns:
            List of tuples: (mcp_id, score, payload)
        """
        # Generate query embedding
        logger.debug(f"Searching for: {query}")
        query_embedding = self.encoder.encode(query, convert_to_tensor=False)
        
        # Search in Qdrant
        search_results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=limit,
            score_threshold=score_threshold,
        )
        
        # Format results
        results = []
        for hit in search_results:
            mcp_id = hit.payload.get("mcp_id")
            score = hit.score
            payload = hit.payload
            
            results.append((mcp_id, score, payload))
        
        logger.info(f"Found {len(results)} MCP servers for query: {query}")
        return results

    def delete_mcp_server(self, qdrant_id: str) -> None:
        """
        Delete an MCP server from the vector store.
        
        Args:
            qdrant_id: Qdrant point ID to delete
        """
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=models.PointIdsList(
                points=[qdrant_id],
            ),
        )
        logger.info(f"Deleted MCP server with Qdrant ID: {qdrant_id}")

    def check_connection(self) -> bool:
        """
        Check if Qdrant connection is working.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant connection check failed: {e}")
            return False


# Global vector store instance (initialized in main app)
vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    """
    Get the global vector store instance.
    
    Returns:
        VectorStore instance
        
    Raises:
        RuntimeError: If vector store not initialized
    """
    if vector_store is None:
        raise RuntimeError("Vector store not initialized")
    return vector_store
