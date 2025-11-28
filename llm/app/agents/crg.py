"""
Agent 11: CRG - Community Reliability Graph
Manages trust network and enhances confidence scores
"""

from app.agents.crg_builder import ReliabilityGraphBuilder
from app.agents.crg_trust import TrustCalculator
from app.agents.crg_analyzer import GraphAnalyzer
from app.config import settings
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class CRGAgent:
    def __init__(self):
        neo4j_uri = getattr(settings, 'neo4j_uri', '')
        
        if neo4j_uri:
            self.builder = ReliabilityGraphBuilder(
                uri=neo4j_uri,
                user=getattr(settings, 'neo4j_user', 'neo4j'),
                password=getattr(settings, 'neo4j_password', '')
            )
            self.trust_calc = TrustCalculator(
                uri=neo4j_uri,
                user=getattr(settings, 'neo4j_user', 'neo4j'),
                password=getattr(settings, 'neo4j_password', '')
            )
            self.analyzer = GraphAnalyzer(
                uri=neo4j_uri,
                user=getattr(settings, 'neo4j_user', 'neo4j'),
                password=getattr(settings, 'neo4j_password', '')
            )
        else:
            logger.warning("CRG: Neo4j not configured, using fallback")
            self.builder = None
            self.trust_calc = None
            self.analyzer = None
    
    def process_evidence(self, evidence_list: List[Dict]) -> Dict:
        """
        Process evidence through CRG pipeline
        
        Args:
            evidence_list: List of evidence sources
        
        Returns:
            Dict with trust-enhanced analysis
        """
        try:
            logger.info(f"🕸️ CRG: Processing {len(evidence_list)} sources")
            
            if not self.builder:
                # Fallback when Neo4j not available
                return self._fallback_processing(evidence_list)
            
            # Step 1: Add sources to graph
            for evidence in evidence_list:
                self.builder.add_source({
                    'url': evidence.get('source_url', ''),
                    'title': evidence.get('title', ''),
                    'domain': self._extract_domain(evidence.get('source_url', '')),
                    'base_reliability': evidence.get('reliability_score', 0.5),
                    'timestamp': evidence.get('retrieved_at', 'now()')
                })
            
            # Step 2: Calculate trust scores
            trust_scores = {}
            for evidence in evidence_list:
                url = evidence.get('source_url', '')
                if url:
                    trust_score = self.trust_calc.calculate_trust_score(url)
                    trust_scores[url] = trust_score
            
            logger.info(f"✓ CRG: Trust scores calculated")
            
            # Step 3: Get network stats
            network_stats = self.analyzer.get_trust_network_stats()
            
            # Step 4: Find most trusted sources
            top_sources = self.analyzer.find_most_trusted_sources(limit=5)
            
            # Step 5: Calculate weighted confidence
            avg_trust = sum(trust_scores.values()) / len(trust_scores) if trust_scores else 0.5
            trust_weight = 0.8 + (avg_trust * 0.4)  # 0.8 to 1.2 multiplier
            
            result = {
                'trust_scores': trust_scores,
                'average_trust': round(avg_trust, 3),
                'trust_weight': round(trust_weight, 3),
                'network_stats': network_stats,
                'top_trusted_sources': top_sources
            }
            
            logger.info(f"✅ CRG: Complete (Trust Weight: {trust_weight:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"❌ CRG Error: {e}")
            import traceback
            traceback.print_exc()
            
            return self._fallback_processing(evidence_list)
    
    def _fallback_processing(self, evidence_list: List[Dict]) -> Dict:
        """Fallback when Neo4j not available"""
        
        # Simple average of base reliability scores
        reliabilities = [e.get('reliability_score', 0.5) for e in evidence_list]
        avg_reliability = sum(reliabilities) / len(reliabilities) if reliabilities else 0.5
        
        trust_weight = 0.8 + (avg_reliability * 0.4)
        
        return {
            'trust_scores': {e.get('source_url', ''): e.get('reliability_score', 0.5) for e in evidence_list},
            'average_trust': round(avg_reliability, 3),
            'trust_weight': round(trust_weight, 3),
            'network_stats': {
                'total_sources': len(evidence_list),
                'average_reliability': round(avg_reliability, 3)
            },
            'top_trusted_sources': []
        }
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        try:
            return urlparse(url).netloc
        except:
            return 'unknown'

def run_crg_agent(evidence_list: List[Dict]) -> Dict:
    """Standalone function to run CRG agent"""
    agent = CRGAgent()
    return agent.process_evidence(evidence_list)
