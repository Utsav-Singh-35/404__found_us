"""
Agent 9: CMTE - Claim Mutation Tracking Engine
Tracks claim mutations and builds family trees
"""

from app.agents.cmte_embeddings import EmbeddingGenerator
from app.agents.cmte_search import MutationSearchEngine
from app.agents.cmte_graph import MutationGraph
from app.agents.cmte_analyzer import MutationAnalyzer
from app.config import settings
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

class CMTEAgent:
    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
        self.search_engine = MutationSearchEngine()
        
        # Initialize graph if Neo4j is configured
        neo4j_uri = getattr(settings, 'neo4j_uri', '')
        if neo4j_uri:
            self.graph = MutationGraph(
                uri=neo4j_uri,
                user=getattr(settings, 'neo4j_user', 'neo4j'),
                password=getattr(settings, 'neo4j_password', '')
            )
        else:
            logger.warning("Neo4j not configured, graph features disabled")
            self.graph = None
        
        self.analyzer = MutationAnalyzer()
    
    def process(self, claim_id: str, claim_text: str, claim_data: Dict) -> Dict:
        """
        Process claim through CMTE pipeline
        
        Args:
            claim_id: Unique claim identifier
            claim_text: Normalized claim text
            claim_data: Additional claim metadata
        
        Returns:
            Dict with mutation analysis results
        """
        try:
            logger.info(f"🔄 CMTE: Processing claim {claim_id}")
            
            # Step 1: Generate embedding
            embedding = self.embedding_gen.generate_text_embedding(claim_text)
            logger.info(f"✓ Generated embedding (dim={len(embedding)})")
            
            # Step 2: Search for similar claims
            similar_claims = self.search_engine.search_similar(
                embedding, 
                k=20,
                threshold=getattr(settings, 'cmte_similarity_threshold', 0.85)
            )
            logger.info(f"✓ Found {len(similar_claims)} similar claims")
            
            # Step 3: Add to search index
            self.search_engine.add_claim(claim_id, embedding)
            
            # Step 4: Add to graph (if available)
            mutation_family = []
            patient_zero = None
            
            if self.graph:
                # Add claim to graph
                self.graph.add_claim(claim_id, {
                    'text': claim_text,
                    'normalized_text': claim_text.lower(),
                    'timestamp': claim_data.get('timestamp', 'now()'),
                    'source_url': claim_data.get('source_url', ''),
                    'platform': claim_data.get('platform', 'unknown')
                })
                
                # Create mutation edges
                for similar_id, similarity in similar_claims:
                    self.graph.add_mutation_edge(similar_id, claim_id, similarity)
                
                # Find mutation family
                mutation_family = self.graph.find_mutation_family(claim_id)
                logger.info(f"✓ Mutation family size: {len(mutation_family)}")
                
                # Find patient zero
                patient_zero = self.graph.find_patient_zero(claim_id)
            
            # Step 5: Analyze family
            analysis = self.analyzer.analyze_family(mutation_family)
            
            # Step 6: Predict spread
            prediction = self.analyzer.predict_spread(mutation_family, days_ahead=7)
            
            result = {
                'claim_id': claim_id,
                'similar_claims_count': len(similar_claims),
                'similar_claims': [
                    {'claim_id': cid, 'similarity': sim}
                    for cid, sim in similar_claims[:10]  # Top 10
                ],
                'mutation_family': mutation_family[:50],  # Limit to 50
                'patient_zero': patient_zero,
                'analysis': analysis,
                'spread_prediction': prediction,
                'viral_score': analysis.get('viral_score', 0),
                'index_size': self.search_engine.get_index_size()
            }
            
            logger.info(f"✅ CMTE: Complete (Viral Score: {result['viral_score']})")
            return result
            
        except Exception as e:
            logger.error(f"❌ CMTE Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'error': str(e),
                'claim_id': claim_id,
                'similar_claims_count': 0,
                'similar_claims': [],
                'mutation_family': [],
                'patient_zero': None,
                'analysis': {
                    'family_size': 0,
                    'viral_score': 0
                },
                'spread_prediction': {},
                'viral_score': 0,
                'index_size': 0
            }

def run_cmte_agent(claim_id: str, claim_text: str, claim_data: Dict) -> Dict:
    """Standalone function to run CMTE agent"""
    agent = CMTEAgent()
    return agent.process(claim_id, claim_text, claim_data)
