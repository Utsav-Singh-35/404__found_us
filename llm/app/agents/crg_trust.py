"""
CRG Trust Calculator
Calculates and propagates trust scores
"""

from neo4j import GraphDatabase
import logging

logger = logging.getLogger(__name__)

# Try to import networkx, but make it optional
try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logger.warning("NetworkX not available, PageRank disabled")

class TrustCalculator:
    def __init__(self, uri: str, user: str, password: str):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
        except Exception as e:
            logger.error(f"CRG: Failed to connect: {e}")
            self.driver = None
    
    def calculate_pagerank(self, iterations: int = 20, damping: float = 0.85):
        """Calculate PageRank-style trust scores"""
        
        if not self.driver or not NETWORKX_AVAILABLE:
            logger.warning("CRG: PageRank not available")
            return {}
        
        try:
            # Get graph data
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s1:Source)-[:CITES]->(s2:Source)
                    RETURN s1.url as source, s2.url as target
                """)
                
                edges = [(record['source'], record['target']) for record in result]
            
            if not edges:
                logger.warning("CRG: No citation edges found")
                return {}
            
            # Build NetworkX graph
            G = nx.DiGraph()
            G.add_edges_from(edges)
            
            # Calculate PageRank
            pagerank_scores = nx.pagerank(G, alpha=damping, max_iter=iterations)
            
            # Update Neo4j with scores
            with self.driver.session() as session:
                for url, score in pagerank_scores.items():
                    session.run("""
                        MATCH (s:Source {url: $url})
                        SET s.pagerank_score = $score
                    """, url=url, score=score)
            
            logger.info(f"✓ CRG: PageRank calculated for {len(pagerank_scores)} sources")
            return pagerank_scores
            
        except Exception as e:
            logger.error(f"CRG: PageRank calculation failed: {e}")
            return {}
    
    def calculate_trust_score(self, source_url: str) -> float:
        """Calculate comprehensive trust score"""
        
        if not self.driver:
            return 0.5
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Source {url: $url})
                    RETURN s.base_reliability as base_rel,
                           s.pagerank_score as pagerank
                """, url=source_url)
                
                record = result.single()
                if not record:
                    return 0.5
                
                base_rel = record['base_rel'] or 0.5
                pagerank = record['pagerank'] or 0.0
                
                # Weighted combination
                trust_score = (
                    0.7 * base_rel +
                    0.3 * (pagerank * 10)  # Scale pagerank
                )
                
                return min(max(trust_score, 0.0), 1.0)
                
        except Exception as e:
            logger.error(f"CRG: Trust calculation failed: {e}")
            return 0.5
    
    def update_all_trust_scores(self):
        """Recalculate trust scores for all sources"""
        
        if not self.driver:
            return
        
        try:
            # First calculate PageRank
            self.calculate_pagerank()
            
            # Then update individual trust scores
            with self.driver.session() as session:
                result = session.run("MATCH (s:Source) RETURN s.url as url")
                urls = [record['url'] for record in result]
            
            for url in urls:
                trust_score = self.calculate_trust_score(url)
                
                with self.driver.session() as session:
                    session.run("""
                        MATCH (s:Source {url: $url})
                        SET s.computed_reliability = $trust_score,
                            s.last_trust_update = datetime()
                    """, url=url, trust_score=trust_score)
            
            logger.info(f"✓ CRG: Updated trust scores for {len(urls)} sources")
            
        except Exception as e:
            logger.error(f"CRG: Trust update failed: {e}")
