"""
Tests for RAG system.
"""

import pytest
import numpy as np

from transmute.rag.embeddings import EmbeddingGenerator
from transmute.rag.vector_store import CodePattern


class TestEmbeddingGenerator:
    """Tests for EmbeddingGenerator."""
    
    def test_embedding_generator_initialization(self):
        """Test embedding generator initialization."""
        gen = EmbeddingGenerator()
        
        assert gen.model is not None
        assert gen.model_name is not None
    
    def test_generate_embedding_single(self):
        """Test generating single embedding."""
        gen = EmbeddingGenerator()
        
        embedding = gen.generate_embedding("def hello(): pass")
        
        assert isinstance(embedding, np.ndarray)
        assert len(embedding.shape) == 1  # 1D array
        assert embedding.shape[0] > 0  # Has dimensions
    
    def test_generate_embeddings_multiple(self):
        """Test generating multiple embeddings."""
        gen = EmbeddingGenerator()
        
        texts = [
            "def hello(): pass",
            "class MyClass: pass",
            "for item in items: print(item)"
        ]
        
        embeddings = gen.generate_embeddings(texts)
        
        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape[0] == 3  # 3 texts
        assert embeddings.shape[1] > 0  # Has embedding dimension
    
    def test_get_embedding_dim(self):
        """Test getting embedding dimension."""
        gen = EmbeddingGenerator()
        
        dim = gen.get_embedding_dim()
        
        assert isinstance(dim, int)
        assert dim > 0
    
    def test_embeddings_are_consistent(self):
        """Test that same text produces same embedding."""
        gen = EmbeddingGenerator()
        
        text = "def test(): return 42"
        
        emb1 = gen.generate_embedding(text)
        emb2 = gen.generate_embedding(text)
        
        # Should be very similar (allowing for minor floating point differences)
        assert np.allclose(emb1, emb2, rtol=1e-5)
    
    def test_different_texts_different_embeddings(self):
        """Test that different texts produce different embeddings."""
        gen = EmbeddingGenerator()
        
        emb1 = gen.generate_embedding("def hello(): pass")
        emb2 = gen.generate_embedding("class Goodbye: pass")
        
        # Should be different
        assert not np.allclose(emb1, emb2)


class TestCodePattern:
    """Tests for CodePattern dataclass."""
    
    def test_code_pattern_creation(self):
        """Test creating a CodePattern."""
        pattern = CodePattern(
            id="test_id",
            source_code="for x in list:",
            target_code="for (var x : list) {",
            source_language="python",
            target_language="java",
            feature="for_loop"
        )
        
        assert pattern.id == "test_id"
        assert pattern.source_language == "python"
        assert pattern.target_language == "java"
        assert pattern.feature == "for_loop"
    
    def test_code_pattern_with_metadata(self):
        """Test CodePattern with metadata."""
        pattern = CodePattern(
            id="test_id",
            source_code="async def fetch():",
            target_code="async function fetch() {",
            source_language="python",
            target_language="javascript",
            feature="async",
            description="Async function translation",
            metadata={"difficulty": "medium"}
        )
        
        assert pattern.description == "Async function translation"
        assert pattern.metadata["difficulty"] == "medium"


# Note: VectorStore and RAGSystem tests require Qdrant to be running
# These are integration tests and should be run separately

"""
class TestVectorStoreIntegration:
    '''Integration tests for VectorStore (requires Qdrant).'''
    
    @pytest.fixture
    def vector_store(self):
        '''Create a test vector store.'''
        store = VectorStore(
            url="http://localhost:6333",
            collection_name="test-transmute"
        )
        yield store
        # Cleanup
        try:
            store.delete_collection()
        except:
            pass
    
    def test_create_collection(self, vector_store):
        '''Test creating a collection.'''
        vector_store.create_collection(384)
        
        count = vector_store.count_patterns()
        assert count == 0
    
    def test_store_and_retrieve_pattern(self, vector_store):
        '''Test storing and retrieving a pattern.'''
        vector_store.create_collection(384)
        
        pattern = CodePattern(
            id="test_pattern",
            source_code="for x in list:",
            target_code="for (var x : list) {",
            source_language="python",
            target_language="java",
            feature="for_loop"
        )
        
        # Create dummy embedding
        embedding = [0.1] * 384
        
        pattern_id = vector_store.store_pattern(pattern, embedding)
        
        assert pattern_id == "test_pattern"
        
        # Retrieve
        retrieved = vector_store.get_pattern(pattern_id)
        assert retrieved is not None
        assert retrieved['source_code'] == "for x in list:"
"""

class TestRAGSystemEnhanced:
    """Tests for enhanced RAG system methods."""
    
    def test_rank_results(self):
        """Test re-ranking results."""
        gen = EmbeddingGenerator()
        
        # Mock RAG system
        class MockRAG:
            def __init__(self):
                self.embedding_gen = gen
        
        rag = MockRAG()
        
        # Add rank_results method
        from transmute.rag.rag_system import RAGSystem
        rag.rank_results = RAGSystem.rank_results.__get__(rag)
        
        results = [
            {'score': 0.8, 'description': 'spring boot example'},
            {'score': 0.9, 'description': 'basic example'},
            {'score': 0.7, 'description': 'django example', 'verified': True},
        ]
        
        ranked = rag.rank_results(results, boost_framework='spring')
        
        assert len(ranked) == 3
        assert all('adjusted_score' in r for r in ranked)
        # Spring example should be boosted
        assert ranked[0]['description'] == 'spring boot example'
    
    def test_get_statistics(self):
        """Test getting statistics."""
        gen = EmbeddingGenerator()
        
        class MockVectorStore:
            collection_name = "test"
            def count_patterns(self):
                return 42
        
        class MockRAG:
            def __init__(self):
                self.embedding_gen = gen
                self.vector_store = MockVectorStore()
            
            def count_patterns(self):
                return self.vector_store.count_patterns()
        
        rag = MockRAG()
        
        from transmute.rag.rag_system import RAGSystem
        rag.get_statistics = RAGSystem.get_statistics.__get__(rag)
        
        stats = rag.get_statistics()
        
        assert stats['total_patterns'] == 42
        assert 'embedding_model' in stats
        assert 'embedding_dim' in stats
        assert stats['collection_name'] == 'test'