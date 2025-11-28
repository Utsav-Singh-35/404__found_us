"""
Agent 4: Fact-Check APIs
Purpose: Query authoritative fact-checking sources
"""

import asyncio
import aiohttp
from typing import Dict, List
from datetime import datetime
from app.config import settings

class FactCheckAgent:
    """Agent 4: Query fact-checking APIs"""
    
    def __init__(self):
        self.google_key = settings.google_factcheck_key
        # Load semantic similarity model lazily
        self.similarity_model = None
    
    def _load_similarity_model(self):
        """Load sentence transformer model"""
        if self.similarity_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')
                print("✓ Loaded semantic similarity model")
            except Exception as e:
                print(f"⚠️  Could not load similarity model: {e}")
                self.similarity_model = False  # Mark as failed
    
    async def check_all_sources(self, claim_text: str) -> List[Dict]:
        """
        Query all fact-checking sources in parallel
        
        Returns list of fact-check results
        """
        
        # Run all queries in parallel
        results = await asyncio.gather(
            self.query_google_factcheck(claim_text),
            return_exceptions=True
        )
        
        # Filter out None and exceptions
        valid_results = []
        for result in results:
            if result and not isinstance(result, Exception):
                valid_results.extend(result if isinstance(result, list) else [result])
        
        return valid_results
    
    async def query_google_factcheck(self, claim_text: str) -> List[Dict]:
        """Query Google Fact Check Tools API"""
        
        if not self.google_key:
            print("⚠️  Google Fact Check API key not configured")
            return []
        
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": claim_text,
            "key": self.google_key,
            "languageCode": "en"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=30) as resp:
                    if resp.status != 200:
                        print(f"⚠️  Google Fact Check API error: {resp.status}")
                        return []
                    
                    data = await resp.json()
                    
                    if 'claims' not in data:
                        return []
                    
                    # Load similarity model if needed
                    self._load_similarity_model()
                    
                    # Process results
                    results = []
                    for claim in data['claims']:
                        # Calculate semantic similarity
                        similarity = self._calculate_similarity(
                            claim_text,
                            claim['text']
                        )
                        
                        # Only include if similarity > 0.7
                        if similarity >= 0.7:
                            # Get first review
                            review = claim['claimReview'][0] if claim.get('claimReview') else {}
                            
                            results.append({
                                "api_name": "GoogleFactCheck",
                                "found": True,
                                "claim_text": claim['text'],
                                "verdict": review.get('textualRating', 'Unknown'),
                                "summary": claim.get('text', ''),
                                "url": review.get('url', ''),
                                "publisher": review.get('publisher', {}).get('name', 'Unknown'),
                                "similarity_score": similarity,
                                "retrieved_at": datetime.utcnow()
                            })
                    
                    return results
        
        except Exception as e:
            print(f"⚠️  Error querying Google Fact Check: {e}")
            return []
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity between two texts"""
        
        if not self.similarity_model or self.similarity_model is False:
            # Fallback to simple string matching
            text1_lower = text1.lower()
            text2_lower = text2.lower()
            
            # Count matching words
            words1 = set(text1_lower.split())
            words2 = set(text2_lower.split())
            
            if not words1 or not words2:
                return 0.0
            
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        
        try:
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Generate embeddings
            embeddings = self.similarity_model.encode([text1, text2])
            
            # Calculate cosine similarity
            similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            
            return float(similarity)
        except Exception as e:
            print(f"⚠️  Similarity calculation error: {e}")
            return 0.5  # Default medium similarity

# Create singleton
factcheck_agent = FactCheckAgent()
