"""
NRI Narrative Classifier
Classifies claims into narrative templates
"""

import json
import os
from typing import Dict, List
from app.llm_client import get_llm_response
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class NarrativeClassifier:
    def __init__(self):
        # Load narrative templates
        template_path = 'app/data/narrative_templates.json'
        if os.path.exists(template_path):
            with open(template_path, 'r') as f:
                self.templates = json.load(f)['templates']
            logger.info(f"✓ Loaded {len(self.templates)} narrative templates")
        else:
            logger.warning("Narrative templates not found")
            self.templates = []
    
    def classify_with_llm(self, claim_text: str) -> Dict:
        """Use LLM to classify narrative"""
        
        prompt = f"""Analyze this claim and identify its narrative structure:

Claim: "{claim_text}"

Classify it into ONE of these narrative templates:
1. fear_health: Creates fear about health risks
2. conspiracy_control: Hidden control or surveillance
3. blame_scapegoat: Blames specific groups
4. hope_miracle: Too-good-to-be-true solutions
5. political_partisan: Attacks political opponents

Respond in JSON format:
{{
    "narrative_type": "fear_health|conspiracy_control|blame_scapegoat|hope_miracle|political_partisan",
    "confidence": 0.85,
    "emotional_triggers": ["fear", "anxiety"],
    "psychological_appeal": "Brief explanation of why this narrative persuades people",
    "target_audience": "Who is most likely to believe this",
    "persuasion_tactics": ["emotional_appeal", "authority_questioning"]
}}"""
        
        try:
            response = get_llm_response(
                prompt=prompt,
                temperature=0.3
            )
            
            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                logger.warning("LLM response not in JSON format, using fallback")
                return self.classify_with_rules(claim_text)
            
        except Exception as e:
            logger.error(f"LLM classification failed: {e}")
            return self.classify_with_rules(claim_text)
    
    def classify_with_rules(self, claim_text: str) -> Dict:
        """Fallback rule-based classification"""
        
        claim_lower = claim_text.lower()
        scores = {}
        
        # Score each template
        for template in self.templates:
            score = 0
            for keyword in template['keywords']:
                if keyword in claim_lower:
                    score += 1
            scores[template['id']] = score
        
        # Get best match
        if max(scores.values()) > 0:
            best_template_id = max(scores, key=scores.get)
            best_template = next(t for t in self.templates if t['id'] == best_template_id)
            
            return {
                'narrative_type': best_template_id,
                'confidence': min(scores[best_template_id] / 5, 0.8),
                'emotional_triggers': best_template['emotional_triggers'],
                'psychological_appeal': best_template['description'],
                'target_audience': best_template['target_audience'],
                'persuasion_tactics': ['keyword_matching']
            }
        
        # Default
        return {
            'narrative_type': 'unknown',
            'confidence': 0.3,
            'emotional_triggers': ['unknown'],
            'psychological_appeal': 'Unable to determine narrative structure',
            'target_audience': 'general public',
            'persuasion_tactics': []
        }
