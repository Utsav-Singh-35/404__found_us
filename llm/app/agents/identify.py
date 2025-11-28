"""
Agent 5: Identify Agent
Purpose: Determine if authoritative fact-check was found
"""

from typing import Dict, List
from bson import ObjectId
from app.database import fact_checks_collection

class IdentifyAgent:
    """Agent 5: Identify if fact-check was found"""
    
    def identify(self, claim_id: ObjectId) -> Dict:
        """
        Check if authoritative fact-check exists
        
        Returns:
            {
                "found": True/False,
                "should_search_web": True/False,
                "primary_factcheck": {...} or None,
                "confidence": 0.0-1.0
            }
        """
        
        # Query fact_checks collection
        fact_checks = list(fact_checks_collection.find({"claim_id": claim_id}))
        
        if not fact_checks:
            return {
                "found": False,
                "should_search_web": True,
                "primary_factcheck": None,
                "confidence": 0.0,
                "reason": "No authoritative fact-checks found"
            }
        
        # Find highest confidence fact-check
        high_confidence = [
            fc for fc in fact_checks
            if fc.get('similarity_score', 0) >= 0.8
        ]
        
        if high_confidence:
            # Sort by similarity score
            high_confidence.sort(
                key=lambda x: x.get('similarity_score', 0),
                reverse=True
            )
            
            primary = high_confidence[0]
            
            return {
                "found": True,
                "should_search_web": True,  # Still collect for transparency
                "primary_factcheck": primary,
                "confidence": 0.95,  # High confidence from authoritative source
                "reason": f"Found authoritative fact-check from {primary.get('publisher', 'Unknown')}"
            }
        
        # Low confidence matches
        return {
            "found": False,
            "should_search_web": True,
            "primary_factcheck": fact_checks[0] if fact_checks else None,
            "confidence": 0.3,
            "reason": "Found fact-checks but low similarity"
        }

# Create singleton
identify_agent = IdentifyAgent()
