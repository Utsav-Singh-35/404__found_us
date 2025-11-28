"""
CMTE Search Engine
Fast similarity search using FAISS
"""

import faiss
import numpy as np
from typing import List, Tuple
import logging

logger = logging.getLogger(__name__)

class MutationSearchEngine:
    def __init__(self, dimension: int = 384):
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)
        self.claim_ids = []
        logger.info(f"✓ Initialized FAISS index (dim={dimension})")
    
    def add_claim(self, claim_id: str, embedding: np.ndarray):
        """Add claim embedding to index"""
        try:
            # Ensure embedding is correct shape
            if embedding.shape[0] != self.dimension:
                logger.warning(f"Embedding dimension mismatch: {embedding.shape[0]} != {self.dimension}")
                return
            
            # Add to FAISS index
            self.index.add(embedding.reshape(1, -1).astype('float32'))
            self.claim_ids.append(claim_id)
            
        except Exception as e:
            logger.error(f"Failed to add claim to index: {e}")
    
    def search_similar(self, query_embedding: np.ndarray, k: int = 20, 
                      threshold: float = 0.85) -> List[Tuple[str, float]]:
        """Search for similar claims"""
        try:
            if len(self.claim_ids) == 0:
                return []
            
            # Ensure query is correct shape
            query = query_embedding.reshape(1, -1).astype('float32')
            
            # Search
            k_actual = min(k, len(self.claim_ids))
            distances, indices = self.index.search(query, k_actual)
            
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.claim_ids) and idx >= 0:
                    # Convert L2 distance to similarity (0-1)
                    similarity = 1 / (1 + float(distance))
                    
                    if similarity >= threshold:
                        results.append((self.claim_ids[idx], similarity))
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def get_index_size(self) -> int:
        """Get number of claims in index"""
        return len(self.claim_ids)
