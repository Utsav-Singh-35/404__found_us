"""
CRG Graph Analyzer
Analyzes trust network and provides insights
"""

from neo4j import GraphDatabase
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class GraphAnalyzer:
    def __init__(self, uri: str, user: str, password: str):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            logger.error(f"CRG: Failed to connect: {e}")
            self.driver = None
    
    def get_trust_network_stats(self) -> Dict:
        """Get overall network statistics"""
        
        if not self.driver:
            return {
                'total_sources': 0,
                'cited_sources': 0,
                'total_citations': 0,
                'average_reliability': 0.5
            }
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Source)
                    OPTIONAL MATCH (s)-[:CITES]->(s2)
                    
                    WITH count(DISTINCT s) as total_sources,
                         count(DISTINCT s2) as cited_sources,
                         avg(s.computed_reliability) as avg_reliability
                    
                    MATCH ()-[c:CITES]->()
                    
                    RETURN total_sources, cited_sources, 
                           count(c) as total_citations,
                           avg_reliability
                """)
                
                record = result.single()
                if record:
                    return {
                        'total_sources': record['total_sources'] or 0,
                        'cited_sources': record['cited_sources'] or 0,
                        'total_citations': record['total_citations'] or 0,
                        'average_reliability': round(record['avg_reliability'] or 0.5, 3)
                    }
        except Exception as e:
            logger.error(f"CRG: Stats query failed: {e}")
        
        return {
            'total_sources': 0,
            'cited_sources': 0,
            'total_citations': 0,
            'average_reliability': 0.5
        }
    
    def find_most_trusted_sources(self, limit: int = 10) -> List[Dict]:
        """Find highest trust sources"""
        
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Source)
                    WHERE s.computed_reliability IS NOT NULL
                    RETURN s.url as url,
                           s.title as title,
                           s.domain as domain,
                           s.computed_reliability as trust_score
                    ORDER BY trust_score DESC
                    LIMIT $limit
                """, limit=limit)
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"CRG: Top sources query failed: {e}")
            return []
