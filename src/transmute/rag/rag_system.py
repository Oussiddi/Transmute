"""
RAG (Retrieval Augmented Generation) system for code translation.

Orchestrates embeddings, vector storage, and pattern retrieval.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path  # Add this import
import uuid

from transmute.rag.embeddings import EmbeddingGenerator
from transmute.rag.vector_store import VectorStore, CodePattern
from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class RAGSystem:
    """
    RAG system for code translation.
    
    Combines embedding generation and vector search to provide relevant
    code translation patterns.
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        qdrant_url: str = "http://localhost:6333",
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "transmute-code"
    ):
        """
        Initialize RAG system.
        
        Args:
            embedding_model: Sentence transformer model name
            qdrant_url: Qdrant server URL
            qdrant_api_key: API key for Qdrant Cloud
            collection_name: Vector collection name
        """
        logger.info("Initializing RAG system")
        
        self.embedding_gen = EmbeddingGenerator(model_name=embedding_model)
        self.vector_store = VectorStore(
            url=qdrant_url,
            api_key=qdrant_api_key,
            collection_name=collection_name
        )
        
        # Initialize collection
        embedding_dim = self.embedding_gen.get_embedding_dim()
        self.vector_store.create_collection(embedding_dim)
        
        logger.info("RAG system initialized")
    
    def add_pattern(
        self,
        source_code: str,
        target_code: str,
        source_language: str,
        target_language: str,
        feature: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a code translation pattern.
        
        Args:
            source_code: Source code snippet
            target_code: Target code snippet
            source_language: Source language name
            target_language: Target language name
            feature: Feature this pattern demonstrates
            description: Human-readable description
            metadata: Additional metadata
            
        Returns:
            Pattern ID
            
        Example:
            >>> rag = RAGSystem()
            >>> pattern_id = rag.add_pattern(
            ...     source_code="for item in items:",
            ...     target_code="for (Item item : items) {",
            ...     source_language="python",
            ...     target_language="java",
            ...     feature="for_loop"
            ... )
        """
        # Create pattern
        pattern = CodePattern(
            id=str(uuid.uuid4()),
            source_code=source_code,
            target_code=target_code,
            source_language=source_language,
            target_language=target_language,
            feature=feature,
            description=description,
            metadata=metadata or {}
        )
        
        # Generate embedding from source code + description
        text = f"{source_code}\n{description}"
        embedding = self.embedding_gen.generate_embedding(text)
        
        # Store pattern
        pattern_id = self.vector_store.store_pattern(pattern, embedding.tolist())
        
        logger.info(f"Added pattern: {feature} ({source_language} -> {target_language})")
        
        return pattern_id
    
    def retrieve_context(
        self,
        query_code: str,
        source_language: str,
        target_language: str,
        top_k: int = 5,
        score_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant translation patterns for query code.
        
        Args:
            query_code: Source code to translate
            source_language: Source language
            target_language: Target language
            top_k: Number of patterns to retrieve
            score_threshold: Minimum similarity score
            
        Returns:
            List of relevant patterns with scores
            
        Example:
            >>> rag = RAGSystem()
            >>> patterns = rag.retrieve_context(
            ...     "for item in items:\n    print(item)",
            ...     "python",
            ...     "java",
            ...     top_k=3
            ... )
            >>> for pattern in patterns:
            ...     print(f"Score: {pattern['score']}")
            ...     print(f"Target: {pattern['target_code']}")
        """
        # Generate embedding for query
        embedding = self.embedding_gen.generate_embedding(query_code)
        
        # Search with filters
        filters = {
            'source_language': source_language,
            'target_language': target_language
        }
        
        results = self.vector_store.search_similar(
            query_embedding=embedding.tolist(),
            top_k=top_k,
            score_threshold=score_threshold,
            filters=filters
        )
        
        logger.info(f"Retrieved {len(results)} patterns for translation")
        
        return results
    
    def get_translation_hints(
        self,
        query_code: str,
        source_language: str,
        target_language: str
    ) -> str:
        """
        Get translation hints based on similar patterns.
        
        Args:
            query_code: Source code to translate
            source_language: Source language
            target_language: Target language
            
        Returns:
            Formatted hints string
            
        Example:
            >>> hints = rag.get_translation_hints(
            ...     "async def fetch():",
            ...     "python",
            ...     "javascript"
            ... )
            >>> print(hints)
        """
        patterns = self.retrieve_context(
            query_code, source_language, target_language, top_k=3
        )
        
        if not patterns:
            return "No similar patterns found."
        
        hints = ["Similar translation patterns:"]
        
        for i, pattern in enumerate(patterns, 1):
            hints.append(f"\n{i}. Similarity: {pattern['score']:.2f}")
            hints.append(f"   Source: {pattern['source_code'][:100]}...")
            hints.append(f"   Target: {pattern['target_code'][:100]}...")
            if pattern.get('description'):
                hints.append(f"   Note: {pattern['description']}")
        
        return "\n".join(hints)
    
    def build_pattern_index(
        self,
        patterns: List[Dict[str, Any]]
    ) -> int:
        """
        Bulk add patterns to build index.
        
        Args:
            patterns: List of pattern dictionaries
            
        Returns:
            Number of patterns added
            
        Example:
            >>> patterns = [
            ...     {
            ...         'source_code': 'for x in list:',
            ...         'target_code': 'for (var x : list) {',
            ...         'source_language': 'python',
            ...         'target_language': 'java',
            ...         'feature': 'for_loop'
            ...     },
            ...     ...
            ... ]
            >>> count = rag.build_pattern_index(patterns)
        """
        logger.info(f"Building pattern index with {len(patterns)} patterns")
        
        added = 0
        
        for pattern_data in patterns:
            try:
                self.add_pattern(**pattern_data)
                added += 1
            except Exception as e:
                logger.warning(f"Failed to add pattern: {e}")
                continue
        
        logger.info(f"Added {added}/{len(patterns)} patterns to index")
        
        return added
    
    def count_patterns(self) -> int:
        """Get total number of patterns in the system."""
        return self.vector_store.count_patterns()

    def rank_results(
        self,
        results: List[Dict[str, Any]],
        boost_recent: bool = True,
        boost_framework: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results with custom criteria.
        
        Args:
            results: Search results from retrieve_context
            boost_recent: Boost recently added patterns
            boost_framework: Boost patterns from specific framework
            
        Returns:
            Re-ranked results
            
        Example:
            >>> results = rag.retrieve_context(code, "python", "java")
            >>> ranked = rag.rank_results(results, boost_framework="spring")
        """
        if not results:
            return results
        
        scored_results = []
        
        for result in results:
            score = result['score']
            
            # Boost by framework match
            if boost_framework and boost_framework in result.get('description', '').lower():
                score *= 1.2
            
            # Boost by metadata (e.g., verified patterns)
            if result.get('verified', False):
                score *= 1.1
            
            scored_results.append({
                **result,
                'adjusted_score': min(1.0, score)
            })
        
        # Sort by adjusted score
        ranked = sorted(scored_results, key=lambda x: x['adjusted_score'], reverse=True)
        
        logger.info(f"Re-ranked {len(ranked)} results")
        
        return ranked
    
    def filter_by_language(
        self,
        source_language: str,
        target_language: str,
        feature: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter patterns by language pair and optional feature.
        
        Args:
            source_language: Source language
            target_language: Target language
            feature: Optional feature filter
            
        Returns:
            Filtered patterns
            
        Example:
            >>> patterns = rag.filter_by_language("python", "java", "async")
        """
        # Use vector store to search with filters
        filters = {
            'source_language': source_language,
            'target_language': target_language
        }
        
        if feature:
            filters['feature'] = feature
        
        # Dummy query to get all matching patterns
        dummy_embedding = [0.0] * self.embedding_gen.get_embedding_dim()
        
        results = self.vector_store.search_similar(
            query_embedding=dummy_embedding,
            top_k=100,  # Get many results
            score_threshold=0.0,  # No threshold
            filters=filters
        )
        
        logger.info(f"Found {len(results)} patterns for {source_language}->{target_language}")
        
        return results
    
    def export_patterns(self, output_file: Path) -> int:
        """
        Export all patterns to JSON file.
        
        Args:
            output_file: Path to output JSON file
            
        Returns:
            Number of patterns exported
            
        Example:
            >>> count = rag.export_patterns(Path("patterns.json"))
            >>> print(f"Exported {count} patterns")
        """
        import json
        
        logger.info(f"Exporting patterns to {output_file}")
        
        # Get all patterns (use dummy query)
        dummy_embedding = [0.0] * self.embedding_gen.get_embedding_dim()
        
        all_patterns = self.vector_store.search_similar(
            query_embedding=dummy_embedding,
            top_k=10000,  # Get all
            score_threshold=0.0
        )
        
        # Export to JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_patterns, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(all_patterns)} patterns")
        
        return len(all_patterns)
    
    def import_patterns(self, input_file: Path) -> int:
        """
        Import patterns from JSON file.
        
        Args:
            input_file: Path to JSON file with patterns
            
        Returns:
            Number of patterns imported
            
        Example:
            >>> count = rag.import_patterns(Path("patterns.json"))
            >>> print(f"Imported {count} patterns")
        """
        import json
        
        logger.info(f"Importing patterns from {input_file}")
        
        with open(input_file, 'r', encoding='utf-8') as f:
            patterns = json.load(f)
        
        imported = 0
        
        for pattern_data in patterns:
            try:
                # Remove score if present
                pattern_data.pop('score', None)
                pattern_data.pop('id', None)
                pattern_data.pop('adjusted_score', None)
                
                self.add_pattern(**pattern_data)
                imported += 1
            except Exception as e:
                logger.warning(f"Failed to import pattern: {e}")
                continue
        
        logger.info(f"Imported {imported}/{len(patterns)} patterns")
        
        return imported
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored patterns.
        
        Returns:
            Dictionary with statistics
            
        Example:
            >>> stats = rag.get_statistics()
            >>> print(f"Total patterns: {stats['total_patterns']}")
        """
        total = self.count_patterns()
        
        stats = {
            'total_patterns': total,
            'embedding_model': self.embedding_gen.model_name,
            'embedding_dim': self.embedding_gen.get_embedding_dim(),
            'collection_name': self.vector_store.collection_name,
        }
        
        logger.info(f"Statistics: {stats}")
        
        return stats
    
    def clear_collection(self) -> None:
        """
        Clear all patterns from the collection.
        
        Warning: This deletes all stored patterns!
        
        Example:
            >>> rag.clear_collection()
        """
        logger.warning("Clearing all patterns from collection")
        
        self.vector_store.delete_collection()
        
        # Recreate empty collection
        embedding_dim = self.embedding_gen.get_embedding_dim()
        self.vector_store.create_collection(embedding_dim)
        
        logger.info("Collection cleared and recreated")