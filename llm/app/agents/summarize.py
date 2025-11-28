"""
Agent 7: Summarize Agent
Purpose: LLM-powered analysis with confidence scoring
"""

import json
from typing import Dict, Any, List
from bson import ObjectId
from app.config import settings
from app.database import (
    claims_collection,
    fact_checks_collection,
    evidence_collection
)
from app.llm_client import llm_client

class SummarizeAgent:
    """Agent 7: LLM-powered summarization with confidence scoring"""
    
    def summarize(self, claim_id: ObjectId) -> Dict[str, Any]:
        """
        Generate summary with confidence score
        
        Returns:
            {
                "short_explanation": "...",
                "confidence": 0.87,
                "calculated_confidence": 0.85,
                "top_sources": [...],
                "hallucination_detected": False
            }
        """
        
        # Get claim
        claim = claims_collection.find_one({"_id": claim_id})
        if not claim:
            raise ValueError("Claim not found")
        
        # Get fact-checks
        fact_checks = list(fact_checks_collection.find({"claim_id": claim_id}))
        
        # Get evidence
        evidence = list(evidence_collection.find({"claim_id": claim_id}))
        
        # Build LLM prompt
        prompt = self._build_prompt(claim, fact_checks, evidence)
        
        # Call LLM
        try:
            response = llm_client.generate(
                prompt=prompt,
                system_prompt="You are a fact-checking expert. Return only valid JSON.",
                response_format="json"
            )
            llm_result = self._parse_llm_response(response)
        except Exception as e:
            print(f"⚠️  LLM call failed: {e}")
            # Fallback to rule-based summary
            llm_result = self._generate_fallback_summary(claim, fact_checks, evidence)
        
        # Calculate confidence using formula
        calculated_confidence = self._calculate_confidence(fact_checks, evidence)
        
        # Validate sources (detect hallucinations)
        validated_sources = self._validate_sources(
            llm_result.get('top_sources', []),
            fact_checks,
            evidence
        )
        
        hallucination_detected = len(validated_sources) < len(llm_result.get('top_sources', []))
        
        # Use lower of LLM confidence and calculated confidence
        final_confidence = min(
            llm_result.get('confidence', 0.5),
            calculated_confidence
        )
        
        # Penalize if hallucination detected
        if hallucination_detected:
            final_confidence *= 0.8
            print(f"⚠️  Hallucination detected, confidence reduced to {final_confidence:.2f}")
        
        return {
            "short_explanation": llm_result.get('short_explanation', ''),
            "confidence": final_confidence,
            "calculated_confidence": calculated_confidence,
            "llm_confidence": llm_result.get('confidence', 0.5),
            "top_sources": validated_sources,
            "hallucination_detected": hallucination_detected,
            "metadata": {
                "fact_checks_found": len(fact_checks),
                "evidence_collected": len(evidence),
                "model_used": llm_client.provider or "fallback"
            }
        }
    
    def _build_prompt(
        self,
        claim: Dict,
        fact_checks: List[Dict],
        evidence: List[Dict]
    ) -> str:
        """Build structured prompt for LLM"""
        
        prompt = f"""You are a fact-checking summarization expert. Analyze the claim and all evidence to provide a concise summary.

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON
- No markdown, no code blocks, just raw JSON
- ALL THREE FIELDS ARE REQUIRED
- Follow this exact schema:
{{
  "short_explanation": "1-3 sentence explanation of verdict",
  "confidence": 0.85,
  "top_sources": [
    {{"url": "exact URL from evidence", "why": "brief reason"}},
    {{"url": "exact URL from evidence", "why": "brief reason"}}
  ]
}}

CRITICAL: The "confidence" field MUST be a number between 0.0 and 1.0

CLAIM:
"{claim['normalized_claim']}"

"""
        
        # Add fact-check results
        if fact_checks:
            prompt += "\nAUTHORITATIVE FACT-CHECKS:\n"
            for fc in fact_checks:
                prompt += f"\n- {fc['api_name']}: {fc['verdict']}"
                prompt += f"\n  Summary: {fc['summary'][:200]}"
                prompt += f"\n  Source: {fc['url']}\n"
        else:
            prompt += "\nNo authoritative fact-checks found.\n"
        
        # Add web evidence
        if evidence:
            prompt += "\nWEB EVIDENCE:\n"
            for i, ev in enumerate(evidence[:15], 1):  # Limit to top 15
                prompt += f"\n{i}. [{ev['supports_claim'].upper()}] {ev['title']}"
                prompt += f"\n   Reliability: {ev['reliability_score']:.2f}"
                prompt += f"\n   URL: {ev['source_url']}"
                prompt += f"\n   Snippet: {ev['snippet'][:150]}...\n"
        else:
            prompt += "\nNo web evidence collected.\n"
        
        prompt += """
INSTRUCTIONS:
1. Analyze all evidence carefully
2. Determine if claim is TRUE, FALSE, MISLEADING, or UNVERIFIED
3. Write a clear 1-3 sentence explanation
4. Assign confidence score (0.0-1.0):
   - 0.9-1.0: Strong authoritative fact-check + supporting evidence
   - 0.7-0.9: Multiple reliable sources agree
   - 0.5-0.7: Some evidence but conflicting or limited
   - 0.3-0.5: Weak evidence or highly uncertain
   - 0.0-0.3: No reliable evidence
5. List 2-4 top sources with exact URLs from the evidence above
6. ONLY cite URLs that appear in the evidence list above

Return ONLY the JSON object, nothing else.
"""
        
        return prompt
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse and validate LLM JSON response"""
        
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            # Validate required fields
            if 'short_explanation' not in data:
                raise ValueError("Missing short_explanation")
            if 'confidence' not in data:
                print(f"⚠️  LLM response missing confidence field, using 0.5")
                data['confidence'] = 0.5
            if 'top_sources' not in data:
                data['top_sources'] = []
            
            # Validate confidence range
            data['confidence'] = max(0.0, min(1.0, float(data['confidence'])))
            
            # Validate sources structure
            if not isinstance(data['top_sources'], list):
                data['top_sources'] = []
            
            return data
        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"⚠️  Failed to parse LLM response: {e}")
            print(f"Response: {response[:200]}...")
            raise
    
    def _calculate_confidence(
        self,
        fact_checks: List[Dict],
        evidence: List[Dict]
    ) -> float:
        """
        Calculate confidence using formula:
        confidence = 0.6*fact_check + 0.25*evidence_ratio + 0.15*avg_reliability
        """
        
        # Fact-check score
        if fact_checks:
            # High confidence if authoritative source found
            high_similarity = [fc for fc in fact_checks if fc.get('similarity_score', 0) >= 0.8]
            if high_similarity:
                fc_score = 0.95
            else:
                fc_score = 0.7
        else:
            fc_score = 0.0
        
        # Evidence support ratio
        if evidence:
            supporting = len([e for e in evidence if e['supports_claim'] == 'supports'])
            refuting = len([e for e in evidence if e['supports_claim'] == 'refutes'])
            total = len(evidence)
            
            # Use the dominant direction
            if refuting > supporting:
                evidence_ratio = refuting / total
            elif supporting > refuting:
                evidence_ratio = supporting / total
            else:
                evidence_ratio = 0.5  # Mixed evidence
        else:
            evidence_ratio = 0.0
        
        # Average reliability of relevant evidence
        if evidence:
            relevant_evidence = [
                e for e in evidence
                if e['supports_claim'] in ['supports', 'refutes']
            ]
            if relevant_evidence:
                avg_reliability = sum(
                    e['reliability_score'] for e in relevant_evidence
                ) / len(relevant_evidence)
            else:
                avg_reliability = 0.5
        else:
            avg_reliability = 0.5
        
        # Calculate final confidence
        confidence = (
            0.6 * fc_score +
            0.25 * evidence_ratio +
            0.15 * avg_reliability
        )
        
        return max(0.0, min(1.0, confidence))
    
    def _validate_sources(
        self,
        llm_sources: List[Dict],
        fact_checks: List[Dict],
        evidence: List[Dict]
    ) -> List[Dict]:
        """Validate that LLM-cited sources actually exist in our data"""
        
        # Collect all valid URLs
        valid_urls = set()
        
        for fc in fact_checks:
            valid_urls.add(fc['url'])
        
        for ev in evidence:
            valid_urls.add(ev['source_url'])
        
        # Filter LLM sources
        validated = []
        for source in llm_sources:
            if 'url' in source and source['url'] in valid_urls:
                validated.append(source)
            else:
                print(f"⚠️  Hallucination detected: {source.get('url', 'unknown')}")
        
        return validated
    
    def _generate_fallback_summary(
        self,
        claim: Dict,
        fact_checks: List[Dict],
        evidence: List[Dict]
    ) -> Dict[str, Any]:
        """Generate rule-based summary if LLM fails"""
        
        if fact_checks:
            verdict = fact_checks[0]['verdict']
            explanation = f"This claim is {verdict.lower()}. {fact_checks[0]['summary'][:200]}"
            confidence = 0.85
        elif evidence:
            supporting = len([e for e in evidence if e['supports_claim'] == 'supports'])
            refuting = len([e for e in evidence if e['supports_claim'] == 'refutes'])
            
            if refuting > supporting:
                explanation = f"This claim appears to be false based on {refuting} refuting sources."
                confidence = 0.6
            elif supporting > refuting:
                explanation = f"This claim appears to be true based on {supporting} supporting sources."
                confidence = 0.6
            else:
                explanation = "Evidence is mixed or inconclusive."
                confidence = 0.4
        else:
            explanation = "Unable to verify this claim. No evidence found."
            confidence = 0.2
        
        # Get top sources
        top_sources = []
        if fact_checks:
            top_sources.append({
                "url": fact_checks[0]['url'],
                "why": f"Authoritative fact-check: {fact_checks[0]['verdict']}"
            })
        
        for ev in evidence[:3]:
            top_sources.append({
                "url": ev['source_url'],
                "why": f"{ev['supports_claim'].capitalize()} claim (reliability: {ev['reliability_score']:.0%})"
            })
        
        return {
            "short_explanation": explanation,
            "confidence": confidence,
            "top_sources": top_sources
        }

# Create singleton
summarize_agent = SummarizeAgent()
