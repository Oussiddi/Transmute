"""
Embedding generation for code patterns.

Generates vector embeddings for code snippets using sentence transformers.
"""

from typing import List, Union
import numpy as np

from sentence_transformers import SentenceTransformer

from transmute.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """
    Generates embeddings for code snippets.
    
    Uses sentence transformers to create vector embeddings that capture
    semantic meaning of code.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize embedding generator.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        logger.info(f"Loading embedding model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"Successfully loaded model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load model {model_name}: {e}")
            raise
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed (code snippet, description, etc.)
            
        Returns:
            Numpy array of embedding vector
            
        Example:
            >>> gen = EmbeddingGenerator()
            >>> embedding = gen.generate_embedding("def hello(): pass")
            >>> print(embedding.shape)
            (384,)
        """
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            logger.debug(f"Generated embedding of shape {embedding.shape}")
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of embeddings (num_texts x embedding_dim)
            
        Example:
            >>> gen = EmbeddingGenerator()
            >>> embeddings = gen.generate_embeddings([
            ...     "def hello(): pass",
            ...     "class MyClass: pass"
            ... ])
            >>> print(embeddings.shape)
            (2, 384)
        """
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            logger.info(f"Generated {len(texts)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def get_embedding_dim(self) -> int:
        """
        Get dimensionality of embeddings.
        
        Returns:
            Embedding dimension
        """
        return self.model.get_sentence_embedding_dimension()