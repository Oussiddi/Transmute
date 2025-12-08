"""
Vector store for code patterns using Qdrant.

Manages storage and retrieval of code patterns in a vector database.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from qdrant_client.models import FieldCondition, Filter, MatchValue


from transmute.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CodePattern:
    """
    Represents a code pattern for translation.
    
    Stores source code, target code, and metadata for pattern matching.
    """
    
    id: str
    source_code: str
    target_code: str
    source_language: str
    target_language: str
    feature: str
    description: str = ""
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class VectorStore:
    """
    Vector store wrapper for Qdrant.
    
    Manages collections, storage, and retrieval of code patterns.
    """
    
    def __init__(
        self,
        url: str = "http://localhost:6333",
        api_key: Optional[str] = None,
        collection_name: str = "transmute-code"
    ):
        """
        Initialize vector store.
        
        Args:
            url: Qdrant server URL
            api_key: API key for Qdrant Cloud (optional)
            collection_name: Name of the collection
        """
        self.url = url
        self.collection_name = collection_name
        
        logger.info(f"Connecting to Qdrant at {url}")
        
        try:
            self.client = QdrantClient(url=url, api_key=api_key)
            logger.info("Successfully connected to Qdrant")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            raise
    
    def create_collection(
        self,
        embedding_dim: int,
        distance: Distance = Distance.COSINE
    ) -> None:
        """
        Create a new collection in Qdrant.
        
        Args:
            embedding_dim: Dimension of embedding vectors
            distance: Distance metric (COSINE, EUCLID, DOT)
            
        Example:
            >>> store = VectorStore()
            >>> store.create_collection(384)
        """
        logger.info(f"Creating collection: {self.collection_name}")
        
        try:
            # Check if collection exists
            collections = self.client.get_collections().collections
            exists = any(c.name == self.collection_name for c in collections)
            
            if exists:
                logger.warning(f"Collection {self.collection_name} already exists")
                return
            
            # Create collection
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=embedding_dim,
                    distance=distance
                )
            )
            
            logger.info(f"Created collection: {self.collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            raise
    
    def store_pattern(
        self,
        pattern: CodePattern,
        embedding: List[float]
    ) -> str:
        """
        Store a code pattern with its embedding.
        
        Args:
            pattern: CodePattern object
            embedding: Vector embedding
            
        Returns:
            ID of stored pattern
            
        Example:
            >>> pattern = CodePattern(
            ...     id=str(uuid.uuid4()),
            ...     source_code="for item in items:",
            ...     target_code="for (Item item : items) {",
            ...     source_language="python",
            ...     target_language="java",
            ...     feature="loops"
            ... )
            >>> store.store_pattern(pattern, embedding)
        """
        logger.debug(f"Storing pattern: {pattern.id}")
        
        try:
            point = PointStruct(
                id=pattern.id,
                vector=embedding,
                payload={
                    'source_code': pattern.source_code,
                    'target_code': pattern.target_code,
                    'source_language': pattern.source_language,
                    'target_language': pattern.target_language,
                    'feature': pattern.feature,
                    'description': pattern.description,
                    **pattern.metadata
                }
            )
            
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point]
            )
            
            logger.debug(f"Stored pattern: {pattern.id}")
            
            return pattern.id
            
        except Exception as e:
            logger.error(f"Failed to store pattern: {e}")
            raise
    
    def search_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        score_threshold: float = 0.7,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar code patterns.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            score_threshold: Minimum similarity score
            filters: Optional filters (e.g., {'source_language': 'python'})
            
        Returns:
            List of similar patterns with scores
            
        Example:
            >>> results = store.search_similar(
            ...     query_embedding,
            ...     top_k=5,
            ...     filters={'source_language': 'python'}
            ... )
            >>> for result in results:
            ...     print(f"{result['score']:.2f}: {result['source_code']}")
        """
        logger.debug(f"Searching for similar patterns (top_k={top_k})")
        
        try:
            # Build filter
            query_filter = None
            if filters:
                conditions = [
                    FieldCondition(
                        key=key,
                        match=MatchValue(value=value)
                    )
                    for key, value in filters.items()
                ]
                query_filter = Filter(must=conditions)
            
            # Search
            search_result = self.client.query_points(
                collection_name=self.collection_name,
                query=query_embedding,
                limit=top_k,
                query_filter=query_filter,
                score_threshold=score_threshold
            )
            
            # Format results - handle QueryResponse object
            results = []
            
            # Check if it's a QueryResponse with points attribute
            if hasattr(search_result, 'points'):
                # New API format
                for point in search_result.points:
                    results.append({
                        'id': point.id,
                        'score': point.score,
                        **point.payload
                    })
            else:
                # Fallback for old format or list
                for hit in search_result:
                    results.append({
                        'id': hit.id,
                        'score': hit.score,
                        **hit.payload
                    })
            
            logger.info(f"Found {len(results)} similar patterns")
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific pattern by ID.
        
        Args:
            pattern_id: Pattern ID
            
        Returns:
            Pattern data or None if not found
        """
        try:
            result = self.client.retrieve(
                collection_name=self.collection_name,
                ids=[pattern_id]
            )
            
            if result:
                return result[0].payload
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve pattern: {e}")
            return None
    
    def delete_collection(self) -> None:
        """Delete the collection."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.warning(f"Failed to delete collection: {e}")
    
    def count_patterns(self) -> int:
        """
        Count total patterns in collection.
        
        Returns:
            Number of patterns
        """
        try:
            collection_info = self.client.get_collection(
                collection_name=self.collection_name
            )
            return collection_info.points_count
        except Exception as e:
            logger.error(f"Failed to count patterns: {e}")
            return 0