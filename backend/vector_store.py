import os
from typing import List, Dict, Optional, Any, Union
from pathlib import Path
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection
import logging
from dataclasses import asdict
from .embedder import CodeChunk
from .config.vector_store_config import settings as vector_store_settings

logger = logging.getLogger(__name__)

class VectorStoreError(Exception):
    """Base class for vector store related errors."""
    pass

class CollectionNotFoundError(VectorStoreError):
    """Raised when trying to access a collection that doesn't exist."""
    pass

class VectorStoreManager:
    def __init__(
        self,
        persist_directory: Optional[Union[str, Path]] = None,
        collection_name: Optional[str] = None,
        distance_metric: Optional[str] = None
    ):
        """
        Initialize the vector store manager.
        
        Args:
            persist_directory: Directory to persist the vector store. If None, uses configured directory
            collection_name: Name of the default collection. If None, uses configured name
            distance_metric: Distance metric for similarity search. If None, uses configured metric
        """
        self.persist_directory = persist_directory or vector_store_settings.get_persist_directory()
        self.collection_name = collection_name or vector_store_settings.COLLECTION_NAME
        self.distance_metric = distance_metric or vector_store_settings.DISTANCE_METRIC
        
        # Initialize ChromaDB client
        self.client = chromadb.Client(Settings(
            persist_directory=str(self.persist_directory),
            anonymized_telemetry=False
        ))
        
        # Create or get the default collection
        self.collection = self._get_or_create_collection(self.collection_name)
        
        logger.info(f"Initialized vector store at {self.persist_directory}")
        
    def _get_or_create_collection(self, name: str) -> Collection:
        """Get an existing collection or create a new one."""
        try:
            return self.client.get_collection(name=name)
        except ValueError:
            return self.client.create_collection(
                name=name,
                metadata={"hnsw:space": self.distance_metric}
            )
            
    def add_chunks(self, chunks: List[CodeChunk], batch_size: int = 100) -> None:
        """
        Add code chunks to the vector store.
        
        Args:
            chunks: List of CodeChunk objects to add
            batch_size: Number of chunks to add in each batch
        """
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare batch data
            ids = [str(i + j) for j in range(len(batch))]
            embeddings = [chunk.embedding for chunk in batch if chunk.embedding is not None]
            documents = [chunk.content for chunk in batch]
            metadatas = [{
                "language": chunk.language or "unknown",
                "type": chunk.type,
                "name": chunk.name or "",
                "start_line": chunk.start_line,
                "end_line": chunk.end_line
            } for chunk in batch]
            
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception as e:
                logger.error(f"Error adding chunks to vector store: {e}")
                raise VectorStoreError(f"Failed to add chunks: {str(e)}")
                
    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar code chunks.
        
        Args:
            query_embedding: The query embedding vector
            n_results: Number of results to return
            where: Filter conditions for metadata
            where_document: Filter conditions for document content
            
        Returns:
            Dictionary containing search results with distances and metadata
        """
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            
            return {
                "ids": results["ids"][0],
                "distances": results["distances"][0],
                "documents": results["documents"][0],
                "metadatas": results["metadatas"][0]
            }
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise VectorStoreError(f"Search failed: {str(e)}")
            
    def filter_chunks(
        self,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        Filter code chunks based on metadata or content.
        
        Args:
            where: Filter conditions for metadata
            where_document: Filter conditions for document content
            limit: Maximum number of results to return
            
        Returns:
            Dictionary containing filtered chunks with metadata
        """
        try:
            results = self.collection.get(
                where=where,
                where_document=where_document,
                limit=limit
            )
            
            return {
                "ids": results["ids"],
                "documents": results["documents"],
                "metadatas": results["metadatas"]
            }
        except Exception as e:
            logger.error(f"Error filtering chunks: {e}")
            raise VectorStoreError(f"Filtering failed: {str(e)}")
            
    def delete_chunks(
        self,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Delete chunks from the vector store.
        
        Args:
            ids: List of chunk IDs to delete
            where: Filter conditions for metadata
            where_document: Filter conditions for document content
        """
        try:
            self.collection.delete(
                ids=ids,
                where=where,
                where_document=where_document
            )
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            raise VectorStoreError(f"Deletion failed: {str(e)}")
            
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the current collection."""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "distance_metric": self.distance_metric,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise VectorStoreError(f"Failed to get stats: {str(e)}")
            
    def reset_collection(self) -> None:
        """Delete all data in the current collection."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection(self.collection_name)
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise VectorStoreError(f"Reset failed: {str(e)}")
