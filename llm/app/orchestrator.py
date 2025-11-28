"""
Orchestrator: Coordinates all agents in the pipeline
"""

import asyncio
from bson import ObjectId
from datetime import datetime
from app.database import (
    submissions_collection, claims_collection,
    fact_checks_collection, evidence_collection,
    summaries_collection, reports_collection
)
from app.agents.classify import classify_agent
from app.agents.extract import extraction_agent
from app.agents.format import format_agent
from app.agents.factcheck import factcheck_agent
from app.agents.identify import identify_agent
from app.agents.search import search_agent
from app.agents.summarize import summarize_agent
from app.agents.report import report_agent

def process_submission(submission_id: str):
    """
    Process a submission through the agent pipeline
    
    Phase 2: Agents 1-3 (Classify, Extract, Format) ✅
    Phase 3: Agents 4-6 (Fact-check, Identify, Search) ✅
    Phase 4: Agents 7-8 (Summarize, Report) ✅
    
    Args:
        submission_id: MongoDB ObjectId as string
        
    Returns:
        Processing result
    """
    
    # Run async agents in sync context
    return asyncio.run(process_submission_async(submission_id))

async def process_submission_async(submission_id: str):
    """Async version of process_submission"""
    
    print(f"\n{'='*60}")
    print(f"📝 Processing submission: {submission_id}")
    print(f"{'='*60}\n")
    
    try:
        # Get submission from database
        submission = submissions_collection.find_one(
            {"_id": ObjectId(submission_id)}
        )
        
        if not submission:
            raise Exception("Submission not found")
        
        # Update status to processing
        submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {"$set": {"status": "processing"}}
        )
        
        # ============================================================
        # AGENT 1: CLASSIFY
        # ============================================================
        print("🔍 Agent 1: Classify")
        print("-" * 60)
        
        classify_result = classify_agent.run(submission)
        
        input_type = classify_result['input_type']
        input_ref = classify_result['input_ref']
        
        print(f"✓ Input type: {input_type}")
        print(f"✓ Metadata: {classify_result['metadata']}")
        print()
        
        # ============================================================
        # AGENT 2: EXTRACT
        # ============================================================
        print("🔍 Agent 2: Extract Claim")
        print("-" * 60)
        
        extraction_result = extraction_agent.run(input_type, input_ref)
        
        if not extraction_result['success']:
            print(f"⚠️  Extraction failed: {extraction_result.get('error', 'Unknown error')}")
            print(f"✓ Using fallback: {extraction_result['claim_text']}")
        else:
            print(f"✓ Claim extracted: {extraction_result['claim_text'][:100]}...")
        
        print()
        
        # ============================================================
        # AGENT 3: FORMAT
        # ============================================================
        print("🔍 Agent 3: Format & Normalize")
        print("-" * 60)
        
        format_result = format_agent.run(
            extraction_result['claim_text'],
            reference_date=submission['created_at']
        )
        
        print(f"✓ Normalized: {format_result['normalized_claim'][:100]}...")
        print(f"✓ Entities found: {len(format_result['entities'])}")
        if format_result['entities']:
            print(f"  - {', '.join(format_result['entities'][:5])}")
        print()
        
        # ============================================================
        # SAVE CLAIM TO DATABASE
        # ============================================================
        print("💾 Saving to database...")
        print("-" * 60)
        
        claim = {
            "submission_id": ObjectId(submission_id),
            "claim_text": extraction_result['claim_text'],
            "normalized_claim": format_result['normalized_claim'],
            "entities": format_result['entities'],
            "entity_types": format_result['entity_types'],
            "raw_ocr": extraction_result.get('raw_content'),
            "extracted_from": extraction_result['extracted_from'],
            "extraction_success": extraction_result['success'],
            "created_at": datetime.utcnow()
        }
        
        result = claims_collection.insert_one(claim)
        claim_id = result.inserted_id
        
        print(f"✓ Claim saved with ID: {claim_id}")
        print()
        
        # ============================================================
        # AGENT 4: FACT-CHECK APIs
        # ============================================================
        print("🔍 Agent 4: Fact-Check APIs")
        print("-" * 60)
        
        fact_checks = await factcheck_agent.check_all_sources(
            format_result['normalized_claim']
        )
        
        # Save fact-checks
        if fact_checks:
            for fc in fact_checks:
                fc['claim_id'] = claim_id
                fact_checks_collection.insert_one(fc)
            print(f"✓ Found {len(fact_checks)} authoritative fact-checks")
        else:
            print(f"✓ No authoritative fact-checks found")
        print()
        
        # ============================================================
        # AGENT 5: IDENTIFY
        # ============================================================
        print("🔍 Agent 5: Identify Verification Status")
        print("-" * 60)
        
        identify_result = identify_agent.identify(claim_id)
        
        if identify_result['found']:
            print(f"✓ Status: Authoritative fact-check found")
            print(f"✓ Confidence: {identify_result['confidence']}")
            print(f"✓ Source: {identify_result['primary_factcheck'].get('publisher', 'Unknown')}")
        else:
            print(f"✓ Status: No authoritative fact-check")
            print(f"✓ Reason: {identify_result['reason']}")
        print()
        
        # ============================================================
        # AGENT 6: WEB SEARCH
        # ============================================================
        evidence_list = []
        
        if identify_result['should_search_web']:
            print("🔍 Agent 6: Web Search & Evidence Collection")
            print("-" * 60)
            
            evidence_list = await search_agent.search_and_collect(
                format_result['normalized_claim'],
                format_result['entities']
            )
            
            # Save evidence
            if evidence_list:
                for ev in evidence_list:
                    ev['claim_id'] = claim_id
                    evidence_collection.insert_one(ev)
                print(f"✓ Collected {len(evidence_list)} evidence sources")
                
                # Show reliability breakdown
                high_reliability = sum(1 for e in evidence_list if e['reliability_score'] >= 0.8)
                print(f"✓ High reliability sources: {high_reliability}/{len(evidence_list)}")
            else:
                print(f"✓ No evidence collected")
            print()
        
        # ============================================================
        # AGENT 7: SUMMARIZE
        # ============================================================
        print("🔍 Agent 7: Summarize with LLM")
        print("-" * 60)
        
        summary_result = summarize_agent.summarize(claim_id)
        
        # Save summary
        summary_result['claim_id'] = claim_id
        summary_result['created_at'] = datetime.utcnow()
        summaries_collection.insert_one(summary_result)
        
        print(f"✓ Summary generated")
        print(f"✓ Confidence: {summary_result['confidence']:.2%}")
        print(f"✓ LLM Confidence: {summary_result['llm_confidence']:.2%}")
        print(f"✓ Calculated Confidence: {summary_result['calculated_confidence']:.2%}")
        
        if summary_result['hallucination_detected']:
            print(f"⚠️  Hallucination detected and filtered")
        
        print(f"✓ Top sources: {len(summary_result['top_sources'])}")
        print()
        
        # ============================================================
        # AGENT 8: REPORT
        # ============================================================
        print("🔍 Agent 8: Generate PDF Report")
        print("-" * 60)
        
        report_result = report_agent.generate_report(claim_id)
        
        # Save report metadata
        report_result['claim_id'] = claim_id
        reports_collection.insert_one(report_result)
        
        print(f"✓ Report generated: {report_result['pdf_path']}")
        print()
        
        # ============================================================
        # UPDATE SUBMISSION STATUS
        # ============================================================
        submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "status": "completed",
                    "result_id": claim_id,
                    "completed_at": datetime.utcnow(),
                    "fact_checks_count": len(fact_checks),
                    "evidence_count": len(evidence_list),
                    "confidence": summary_result['confidence'],
                    "report_path": report_result['pdf_path']
                }
            }
        )
        
        print(f"{'='*60}")
        print(f"✅ All 8 Agents Complete!")
        print(f"{'='*60}\n")
        print(f"📊 Final Results:")
        print(f"   Claim: {extraction_result['claim_text'][:60]}...")
        print(f"   Confidence: {summary_result['confidence']:.2%}")
        print(f"   Explanation: {summary_result['short_explanation'][:80]}...")
        print(f"   Report: {report_result['pdf_path']}")
        print()
        
        return {
            "success": True,
            "claim_id": str(claim_id),
            "claim_text": extraction_result['claim_text'],
            "normalized_claim": format_result['normalized_claim'],
            "fact_checks_found": len(fact_checks),
            "evidence_collected": len(evidence_list),
            "confidence": summary_result['confidence'],
            "explanation": summary_result['short_explanation'],
            "report_path": report_result['pdf_path']
        }
    
    except Exception as e:
        print(f"\n{'='*60}")
        print(f"❌ Error processing submission: {e}")
        print(f"{'='*60}\n")
        
        # Update submission with error
        submissions_collection.update_one(
            {"_id": ObjectId(submission_id)},
            {
                "$set": {
                    "status": "error",
                    "error_message": str(e),
                    "failed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": False,
            "error": str(e)
        }
