"""
NRI Risk Assessor
Calculates narrative risk and spread potential
"""

from typing import Dict
import logging

logger = logging.getLogger(__name__)

class NarrativeRiskAssessor:
    
    def assess_risk(self, narrative_analysis: Dict, claim_data: Dict) -> Dict:
        """Calculate narrative risk score"""
        
        # Base risk from narrative type
        narrative_risks = {
            'fear_health': 0.8,
            'conspiracy_control': 0.7,
            'blame_scapegoat': 0.9,
            'hope_miracle': 0.6,
            'political_partisan': 0.75,
            'unknown': 0.5
        }
        
        base_risk = narrative_risks.get(
            narrative_analysis.get('narrative_type', 'unknown'),
            0.5
        )
        
        # Adjust for emotional intensity
        emotional_triggers = narrative_analysis.get('emotional_triggers', [])
        high_intensity_emotions = ['fear', 'anger', 'panic', 'rage']
        emotional_multiplier = 1.0
        
        for emotion in emotional_triggers:
            if emotion in high_intensity_emotions:
                emotional_multiplier += 0.1
        
        # Adjust for target audience size
        audience = narrative_analysis.get('target_audience', '')
        audience_multiplier = 1.0
        if 'general' in audience.lower():
            audience_multiplier = 1.2
        
        # Calculate final risk
        risk_score = min(base_risk * emotional_multiplier * audience_multiplier, 1.0)
        
        # Determine risk level
        if risk_score >= 0.7:
            risk_level = 'HIGH'
            recommendation = 'Immediate intervention recommended'
        elif risk_score >= 0.4:
            risk_level = 'MEDIUM'
            recommendation = 'Monitor and prepare response'
        else:
            risk_level = 'LOW'
            recommendation = 'Standard fact-checking sufficient'
        
        return {
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'recommendation': recommendation,
            'factors': {
                'narrative_type': narrative_analysis.get('narrative_type'),
                'emotional_intensity': len([e for e in emotional_triggers if e in high_intensity_emotions]),
                'target_audience_breadth': audience_multiplier
            },
            'intervention_priority': 'urgent' if risk_score >= 0.7 else 'normal'
        }
