"""
RTR Data Aggregator
Aggregates data for dashboard display
"""

from app.database import db
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class DashboardAggregator:
    def __init__(self):
        self.db = db
    
    def get_dashboard_stats(self) -> Dict:
        """Get overall dashboard statistics"""
        try:
            # Get counts
            total_submissions = self.db.submissions.count_documents({})
            completed = self.db.submissions.count_documents({'status': 'completed'})
            processing = self.db.submissions.count_documents({'status': 'processing'})
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.now() - timedelta(hours=24)
            recent_submissions = self.db.submissions.count_documents({
                'created_at': {'$gte': yesterday}
            })
            
            # Get average confidence
            pipeline = [
                {'$match': {'status': 'completed', 'confidence': {'$exists': True}}},
                {'$group': {'_id': None, 'avg_confidence': {'$avg': '$confidence'}}}
            ]
            result = list(self.db.submissions.aggregate(pipeline))
            avg_confidence = result[0]['avg_confidence'] if result else 0.5
            
            return {
                'total_submissions': total_submissions,
                'completed': completed,
                'processing': processing,
                'recent_24h': recent_submissions,
                'average_confidence': round(avg_confidence, 3)
            }
        except Exception as e:
            logger.error(f"RTR: Stats aggregation failed: {e}")
            return {
                'total_submissions': 0,
                'completed': 0,
                'processing': 0,
                'recent_24h': 0,
                'average_confidence': 0.5
            }
    
    def get_top_claims(self, limit: int = 10) -> List[Dict]:
        """Get top claims by activity"""
        try:
            pipeline = [
                {'$match': {'status': 'completed'}},
                {'$sort': {'created_at': -1}},
                {'$limit': limit},
                {'$project': {
                    'claim': '$input_ref',
                    'confidence': 1,
                    'created_at': 1,
                    'status': 1
                }}
            ]
            
            return list(self.db.submissions.aggregate(pipeline))
        except Exception as e:
            logger.error(f"RTR: Top claims query failed: {e}")
            return []
    
    def get_narrative_distribution(self) -> Dict:
        """Get distribution of narrative types"""
        try:
            pipeline = [
                {'$lookup': {
                    'from': 'narratives',
                    'localField': '_id',
                    'foreignField': 'claim_id',
                    'as': 'narrative'
                }},
                {'$unwind': {'path': '$narrative', 'preserveNullAndEmptyArrays': False}},
                {'$group': {
                    '_id': '$narrative.narrative_analysis.narrative_type',
                    'count': {'$sum': 1}
                }},
                {'$sort': {'count': -1}}
            ]
            
            results = list(self.db.submissions.aggregate(pipeline))
            
            distribution = {}
            for result in results:
                if result['_id']:
                    distribution[result['_id']] = result['count']
            
            return distribution
        except Exception as e:
            logger.error(f"RTR: Narrative distribution query failed: {e}")
            return {}
    
    def get_time_series(self, hours: int = 24) -> List[Dict]:
        """Get time series data for charts"""
        try:
            start_time = datetime.now() - timedelta(hours=hours)
            
            pipeline = [
                {'$match': {'created_at': {'$gte': start_time}}},
                {'$group': {
                    '_id': {
                        '$dateToString': {
                            'format': '%Y-%m-%d %H:00',
                            'date': '$created_at'
                        }
                    },
                    'count': {'$sum': 1},
                    'avg_confidence': {'$avg': '$confidence'}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            return list(self.db.submissions.aggregate(pipeline))
        except Exception as e:
            logger.error(f"RTR: Time series query failed: {e}")
            return []
    
    def get_emerging_threats(self, threshold: float = 0.7) -> List[Dict]:
        """Identify emerging high-risk claims"""
        try:
            recent_time = datetime.now() - timedelta(hours=6)
            
            pipeline = [
                {'$match': {
                    'created_at': {'$gte': recent_time},
                    'status': 'completed'
                }},
                {'$lookup': {
                    'from': 'narratives',
                    'localField': '_id',
                    'foreignField': 'claim_id',
                    'as': 'narrative'
                }},
                {'$unwind': {'path': '$narrative', 'preserveNullAndEmptyArrays': False}},
                {'$match': {
                    'narrative.risk_assessment.risk_score': {'$gte': threshold}
                }},
                {'$project': {
                    'claim': '$input_ref',
                    'risk_score': '$narrative.risk_assessment.risk_score',
                    'risk_level': '$narrative.risk_assessment.risk_level',
                    'narrative_type': '$narrative.narrative_analysis.narrative_type',
                    'created_at': 1
                }},
                {'$sort': {'risk_score': -1}},
                {'$limit': 10}
            ]
            
            return list(self.db.submissions.aggregate(pipeline))
        except Exception as e:
            logger.error(f"RTR: Emerging threats query failed: {e}")
            return []
