"""
Agent 3: Format Agent
Purpose: Normalize and canonicalize claims using NLP
"""

import re
from typing import Dict, Any
from datetime import datetime

class FormatAgent:
    """
    Agent 3: Analyze and format claims
    
    - Extract named entities (requires spaCy - optional)
    - Normalize dates
    - Canonicalize text
    - Remove hedging words
    """
    
    def __init__(self):
        # Try to load spaCy model (optional)
        self.nlp = None
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("⚠️  spaCy not available - using basic NLP")
    
    def run(self, claim_text: str, reference_date: datetime = None) -> Dict[str, Any]:
        """
        Format and normalize claim
        
        Args:
            claim_text: Extracted claim text
            reference_date: Reference date for relative date parsing
            
        Returns:
            Normalized claim with entities and metadata
        """
        
        if reference_date is None:
            reference_date = datetime.utcnow()
        
        # Extract entities if spaCy is available
        entities = []
        entity_types = {}
        
        if self.nlp:
            try:
                doc = self.nlp(claim_text)
                entities = [ent.text for ent in doc.ents]
                entity_types = {ent.text: ent.label_ for ent in doc.ents}
            except:
                pass
        
        # Normalize the claim
        normalized_text = self._normalize_claim(claim_text, reference_date)
        
        return {
            "normalized_claim": normalized_text,
            "entities": entities,
            "entity_types": entity_types,
            "metadata": {
                "original_length": len(claim_text),
                "normalized_length": len(normalized_text),
                "entity_count": len(entities),
                "has_spacy": self.nlp is not None
            }
        }
    
    def _normalize_claim(self, text: str, reference_date: datetime) -> str:
        """Normalize claim text"""
        
        normalized = text
        
        # 1. Normalize common abbreviations
        entity_map = {
            r'\bgovt\b': 'Government',
            r'\bgov\b': 'Government',
            r'\bPM\b': 'Prime Minister',
            r'\bprez\b': 'President',
            r'\bUS\b': 'United States',
            r'\bUK\b': 'United Kingdom',
        }
        
        for abbr, full in entity_map.items():
            normalized = re.sub(abbr, full, normalized, flags=re.IGNORECASE)
        
        # 2. Normalize relative dates (basic)
        date_patterns = {
            r'\bnext month\b': self._get_next_month(reference_date),
            r'\bnext year\b': str(reference_date.year + 1),
            r'\bthis year\b': str(reference_date.year),
            r'\byesterday\b': 'recently',
            r'\btoday\b': 'currently',
            r'\btomorrow\b': 'soon',
        }
        
        for pattern, replacement in date_patterns.items():
            normalized = re.sub(pattern, replacement, normalized, flags=re.IGNORECASE)
        
        # 3. Remove hedging words
        hedging_words = [
            'reportedly', 'allegedly', 'supposedly',
            'apparently', 'seemingly', 'purportedly'
        ]
        
        for word in hedging_words:
            normalized = re.sub(r'\b' + word + r'\b', '', normalized, flags=re.IGNORECASE)
        
        # 4. Clean up extra spaces
        normalized = ' '.join(normalized.split())
        
        # 5. Capitalize first letter
        if normalized:
            normalized = normalized[0].upper() + normalized[1:]
        
        return normalized
    
    def _get_next_month(self, reference_date: datetime) -> str:
        """Get next month in YYYY-MM format"""
        year = reference_date.year
        month = reference_date.month + 1
        
        if month > 12:
            month = 1
            year += 1
        
        return f"{year}-{month:02d}"

# Create singleton instance
format_agent = FormatAgent()
