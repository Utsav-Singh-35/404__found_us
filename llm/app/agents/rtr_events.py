"""
RTR Event Publishers
Publish events to stream from various agents
"""

from app.agents.rtr_stream import EventStreamManager
from app.config import settings
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Initialize stream manager
try:
    stream_manager = EventStreamManager(settings.redis_url)
except Exception as e:
    logger.warning(f"RTR: Stream manager initialization failed: {e}")
    stream_manager = None

def publish_submission_event(submission_id: str, submission_data: Dict):
    """Publish new submission event"""
    if not stream_manager:
        return
    
    stream_manager.publish_event('submission_created', {
        'submission_id': submission_id,
        'input_type': submission_data.get('input_type'),
        'timestamp': submission_data.get('created_at')
    })

def publish_completion_event(submission_id: str, result_data: Dict):
    """Publish completion event"""
    if not stream_manager:
        return
    
    stream_manager.publish_event('fact_check_completed', {
        'submission_id': submission_id,
        'confidence': result_data.get('confidence'),
        'claim': result_data.get('claim', '')[:100],  # Truncate
        'narrative_type': result_data.get('narrative_type'),
        'risk_level': result_data.get('risk_level')
    })

def publish_mutation_event(claim_id: str, mutation_data: Dict):
    """Publish mutation detection event"""
    if not stream_manager:
        return
    
    stream_manager.publish_event('mutation_detected', {
        'claim_id': claim_id,
        'family_size': mutation_data.get('family_size'),
        'viral_score': mutation_data.get('viral_score')
    })

def publish_alert_event(alert_type: str, alert_data: Dict):
    """Publish alert event"""
    if not stream_manager:
        return
    
    stream_manager.publish_event('alert', {
        'alert_type': alert_type,
        'severity': alert_data.get('severity', 'medium'),
        'message': alert_data.get('message'),
        'data': alert_data
    })
