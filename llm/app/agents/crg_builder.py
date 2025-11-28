"""
CRG Graph Builder
Constructs and maintains the reliability graph
"""

from neo4j import GraphDatabase
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ReliabilityGraphBuilder:
    def __init__(self, uri: str, user: str, password: str):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self._initialize_graph()
            logger.info("✓ CRG: Connected to Neo4j")
        except Exception as e:
            logger.error(f"CRG: Failed to connect to Neo4j: {e}")
            self.driver = None
    
    def _initialize_graph(self):
        """Create indexes and constraints"""
        if not self.driver:
            return
        
        try:
            with self.driver.session() as session:
                # Create indexes
                session.run("CREATE INDEX source_url IF NOT EXISTS FOR (s:Source) ON (s.url)")
                session.run("CREATE INDEX domain_name IF NOT EXISTS FOR (d:Domain) ON (d.name)")
        except Exception as e:
            logger.warning(f"CRG: Index creation warning: {e}")
    
    def add_source(self, source_data: Dict):
        """Add source node to graph"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (s:Source {url: $url})
                    SET s.title = $title,
                        s.domain = $domain,
                        s.base_reliability = $base_reliability,
                        s.last_updated = datetime($timestamp)
                """, **source_data)
                
                # Also create domain node
                session.run("""
                    MERGE (d:Domain {name: $domain})
                    SET d.base_reliability = $base_reliability
                    
                    WITH d
                    MATCH (s:Source {url: $url})
                    MERGE (s)-[:BELONGS_TO]->(d)
                """, **source_data)
            return True
        except Exception as e:
            logger.error(f"CRG: Failed to add source: {e}")
            return False
    
    def add_citation(self, from_url: str, to_url: str, context: str = ""):
        """Add citation relationship"""
        if not self.driver:
            return False
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MATCH (s1:Source {url: $from_url})
                    MATCH (s2:Source {url: $to_url})
                    MERGE (s1)-[c:CITES]->(s2)
                    SET c.context = $context,
                        c.created_at = datetime()
                """, from_url=from_url, to_url=to_url, context=context)
            return True
        except Exception as e:
            logger.error(f"CRG: Failed to add citation: {e}")
            return False
    
    def get_source_reliability(self, source_url: str) -> float:
        """Get current reliability score for source"""
        if not self.driver:
            return 0.5
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (s:Source {url: $url})
                    RETURN s.computed_reliability as reliability,
                           s.base_reliability as base_reliability
                """, url=source_url)
                
                record = result.single()
                if record:
                    return record['reliability'] or record['base_reliability'] or 0.5
                return 0.5
        except Exception as e:
            logger.error(f"CRG: Failed to get reliability: {e}")
            return 0.5
    
    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
