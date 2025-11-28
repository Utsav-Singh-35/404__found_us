"""
CMTE Graph Manager
Manages mutation graph in Neo4j
"""

from neo4j import GraphDatabase
from datetime import datetime
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class MutationGraph:
    def __init__(self, uri: str, user: str, password: str):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._initialize_graph()
            logger.info("✓ Connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def _initialize_graph(self):
        """Create indexes and constraints"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # Create indexes
                session.run("CREATE INDEX claim_id IF NOT EXISTS FOR (c:Claim) ON (c.id)")
                session.run("CREATE INDEX claim_text IF NOT EXISTS FOR (c:Claim) ON (c.normalized_text)")
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    def add_claim(self, claim_id: str, claim_data: Dict):
        """Add claim node to graph"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (c:Claim {id: $id})
                    SET c.text = $text,
                        c.normalized_text = $normalized_text,
                        c.timestamp = datetime($timestamp),
                        c.source_url = $source_url,
                        c.platform = $platform
                """, 
                    id=claim_id,
                    text=claim_data.get('text', ''),
                    normalized_text=claim_data.get('normalized_text', '').lower(),
                    timestamp=claim_data.get('timestamp', datetime.now().isoformat()),
                    source_url=claim_data.get('source_url', ''),
                    platform=claim_data.get('platform', 'unknown')
                )
            return True
        except Exception as e:
            logger.error(f"Failed to add claim: {e}")
            return False
    
    def add_mutation_edge(self, from_id: str, to_id: str, similarity: float):
        """Add mutation relationship"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (c1:Claim {id: $from_id})
                    MATCH (c2:Claim {id: $to_id})
                    MERGE (c1)-[r:MUTATES_TO]->(c2)
                    SET r.similarity = $similarity,
                        r.detected_at = datetime()
                """, from_id=from_id, to_id=to_id, similarity=similarity)
            return True
        except Exception as e:
            logger.error(f"Failed to add mutation edge: {e}")
            return False
    
    def find_mutation_family(self, claim_id: str, max_depth: int = 5) -> List[Dict]:
        """Find all related mutations"""
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (c:Claim {id: $claim_id})-[:MUTATES_TO*0..5]-(related:Claim)
                    RETURN DISTINCT related.id as id, 
                           related.text as text,
                           related.timestamp as timestamp,
                           length(path) as distance
                    ORDER BY distance, timestamp
                    LIMIT 100
                """, claim_id=claim_id)
                
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Failed to find mutation family: {e}")
            return []
    
    def find_patient_zero(self, claim_id: str) -> Optional[Dict]:
        """Find earliest claim in mutation family"""
        if not self.driver:
            return None
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH path = (c:Claim {id: $claim_id})-[:MUTATES_TO*0..10]-(related:Claim)
                    RETURN related.id as id,
                           related.text as text,
                           related.timestamp as timestamp,
                           related.source_url as source_url
                    ORDER BY timestamp ASC
                    LIMIT 1
                """, claim_id=claim_id)
                
                record = result.single()
                return dict(record) if record else None
        except Exception as e:
            logger.error(f"Failed to find patient zero: {e}")
            return None
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
