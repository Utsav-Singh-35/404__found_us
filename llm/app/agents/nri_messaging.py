"""
NRI Corrective Messaging Generator
Creates counter-narratives and advisory templates
"""

from typing import Dict
from app.llm_client import get_llm_response
import logging
import json
import re

logger = logging.getLogger(__name__)

class CorrectiveMessagingGenerator:
    
    def generate_counter_message(self, claim_text: str, narrative_analysis: Dict, 
                                 fact_check_result: Dict) -> Dict:
        """Generate corrective messaging"""
        
        prompt = f"""Create corrective messages to counter this misinformation:

Claim: "{claim_text}"
Narrative Type: {narrative_analysis.get('narrative_type', 'unknown')}
Emotional Triggers: {', '.join(narrative_analysis.get('emotional_triggers', []))}
Fact-Check: {fact_check_result.get('explanation', 'False')}

Create THREE versions:
1. SHORT (280 chars): Direct, clear, factual
2. MEDIUM (2-3 sentences): Professional, cites authorities
3. DETAILED (1 paragraph): Comprehensive explanation

Respond in JSON:
{{
    "short_message": "...",
    "medium_message": "...",
    "detailed_message": "...",
    "communication_style": "calm|urgent|empathetic",
    "recommended_channels": ["social_media", "press_release"],
    "key_points": ["point1", "point2"]
}}"""
        
        try:
            response = get_llm_response(prompt=prompt, temperature=0.5)
            
            # Extract JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return self._generate_fallback_message(claim_text, narrative_analysis)
            
        except Exception as e:
            logger.error(f"Corrective messaging generation failed: {e}")
            return self._generate_fallback_message(claim_text, narrative_analysis)
    
    def _generate_fallback_message(self, claim_text: str, narrative_analysis: Dict) -> Dict:
        """Fallback messaging when LLM fails"""
        
        narrative_type = narrative_analysis.get('narrative_type', 'unknown')
        
        templates = {
            'fear_health': {
                'short': "This claim is false. Health authorities confirm there is no evidence to support this.",
                'medium': "Official health organizations have investigated and found no evidence for this claim. The public should rely on verified health information from trusted sources.",
                'style': 'calm'
            },
            'conspiracy_control': {
                'short': "This conspiracy theory is unfounded. No credible evidence supports these claims.",
                'medium': "Independent fact-checkers and experts have thoroughly debunked this conspiracy theory. There is no evidence of the alleged activities.",
                'style': 'authoritative'
            },
            'default': {
                'short': "This claim is false according to fact-checkers.",
                'medium': "Multiple authoritative sources have verified that this claim is false. Please refer to official fact-checking organizations for accurate information.",
                'style': 'calm'
            }
        }
        
        template = templates.get(narrative_type, templates['default'])
        
        return {
            'short_message': template['short'],
            'medium_message': template['medium'],
            'detailed_message': template['medium'] + " For more information, consult trusted sources and official health organizations.",
            'communication_style': template['style'],
            'recommended_channels': ['social_media', 'website', 'press_release'],
            'key_points': ['Claim is false', 'No credible evidence', 'Trust official sources']
        }
