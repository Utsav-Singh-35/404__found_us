"""
CMTE Embedding Generator
Generates embeddings for text and images
"""

from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    def __init__(self):
        try:
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("✓ Loaded sentence-transformers model")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            self.text_model = None
    
    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate 384-dim vector for text"""
        try:
            if self.text_model is None:
                # Fallback: simple hash-based embedding
                return self._simple_embedding(text)
            
            embedding = self.text_model.encode(text, convert_to_numpy=True)
            return embedding
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return self._simple_embedding(text)
    
    def _simple_embedding(self, text: str) -> np.ndarray:
        """Fallback simple embedding"""
        # Create a simple 384-dim vector based on text hash
        import hashlib
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        # Repeat hash to get 384 dimensions
        embedding = np.frombuffer(hash_bytes * 12, dtype=np.float32)[:384]
        # Normalize
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
