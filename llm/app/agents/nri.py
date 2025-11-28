"""
Agent 10: NRI - Narrative Reasoning Index
Analyzes narrative structure and generates corrective messaging
"""

from app.agents.nri_classifier import NarrativeClassifier
from app.agents.nri_messaging import CorrectiveMessagingGenerator
from app.agents.nri_risk import NarrativeRiskAssessor
from typing import Dict
import logging

logger = logging.getLogger(__name__)

class NRIAgent:
    def __init__(self):
        self.classifier = NarrativeClassifier()
        self.messaging_gen = CorrectiveMessagingGenerator()
        self.risk_assessor = NarrativeRiskAssessor()
    
    def process(self, claim_text: str, fact_check_result: Dict) -> Dict:
        """
        Process claim through NRI pipeline
        
        Args:
            claim_text: Normalized claim text
            fact_check_result: Results from fact-checking
        
        Returns:
            Dict with narrative analysis and corrective messaging
        """
        try:
            logger.info(f"🧠 NRI: Analyzing narrative structure")
            
            # Step 1: Classify narrative
            narrative_analysis = self.classifier.classify_with_llm(claim_text)
            logger.info(f"✓ Narrative type: {narrative_analysis.get('narrative_type')}")
            
            # Step 2: Generate corrective messaging
            corrective_messages = self.messaging_gen.generate_counter_message(
                claim_text,
                narrative_analysis,
                fact_check_result
            )
            logger.info(f"✓ Corrective messages generated")
            
            # Step 3: Assess risk
            risk_assessment = self.risk_assessor.assess_risk(
                narrative_analysis,
                {'claim_text': claim_text}
            )
            logger.info(f"✓ Risk level: {risk_assessment.get('risk_level')}")
            
            result = {
                'narrative_analysis': narrative_analysis,
                'corrective_messaging': corrective_messages,
                'risk_assessment': risk_assessment
            }
            
            logger.info(f"✅ NRI: Complete")
            return result
            
        except Exception as e:
            logger.error(f"❌ NRI Error: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'error': str(e),
                'narrative_analysis': {'narrative_type': 'unknown', 'confidence': 0},
                'corrective_messaging': {},
                'risk_assessment': {'risk_level': 'UNKNOWN', 'risk_score': 0}
            }

def run_nri_agent(claim_text: str, fact_check_result: Dict) -> Dict:
    """Standalone function to run NRI agent"""
    agent = NRIAgent()
    return agent.process(claim_text, fact_check_result)
