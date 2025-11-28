"""
CMTE Mutation Analyzer
Analyzes mutation families and predicts viral potential
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MutationAnalyzer:
    
    def analyze_family(self, mutations: List[Dict]) -> Dict:
        """Analyze mutation family characteristics"""
        if not mutations:
            return {
                'family_size': 0,
                'time_span_days': 0,
                'spread_rate': 0,
                'viral_score': 0,
                'mutation_types': {},
                'earliest_source': None,
                'latest_mutation': None,
                'peak_period': None
            }
        
        try:
            # Sort by timestamp
            sorted_mutations = sorted(
                mutations, 
                key=lambda x: x.get('timestamp', datetime.now())
            )
            
            # Calculate metrics
            family_size = len(mutations)
            
            # Calculate time span
            if len(sorted_mutations) > 1:
                first_time = sorted_mutations[0].get('timestamp')
                last_time = sorted_mutations[-1].get('timestamp')
                
                if isinstance(first_time, str):
                    first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                if isinstance(last_time, str):
                    last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                
                time_span = (last_time - first_time).days
            else:
                time_span = 0
            
            # Calculate spread rate (mutations per day)
            spread_rate = family_size / max(time_span, 1)
            
            # Calculate viral potential (0-100)
            viral_score = min(100, (spread_rate * 10) + (family_size * 2))
            
            # Identify mutation types (simplified)
            mutation_types = self._classify_mutations(sorted_mutations)
            
            return {
                'family_size': family_size,
                'time_span_days': time_span,
                'spread_rate': round(spread_rate, 2),
                'viral_score': round(viral_score, 1),
                'mutation_types': mutation_types,
                'earliest_source': sorted_mutations[0] if sorted_mutations else None,
                'latest_mutation': sorted_mutations[-1] if sorted_mutations else None,
                'peak_period': self._find_peak_period(sorted_mutations)
            }
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                'family_size': len(mutations),
                'time_span_days': 0,
                'spread_rate': 0,
                'viral_score': 0,
                'mutation_types': {},
                'earliest_source': None,
                'latest_mutation': None,
                'peak_period': None
            }
    
    def _classify_mutations(self, mutations: List[Dict]) -> Dict[str, int]:
        """Classify types of mutations"""
        types = {
            'paraphrase': 0,
            'translation': 0,
            'platform_crossover': 0,
            'other': 0
        }
        
        for i in range(1, len(mutations)):
            prev = mutations[i-1]
            curr = mutations[i]
            
            # Simple heuristics
            prev_platform = prev.get('platform', 'unknown')
            curr_platform = curr.get('platform', 'unknown')
            
            if prev_platform != curr_platform and prev_platform != 'unknown':
                types['platform_crossover'] += 1
            else:
                types['paraphrase'] += 1
        
        return types
    
    def _find_peak_period(self, mutations: List[Dict]) -> Optional[Dict]:
        """Find period with highest mutation rate"""
        if len(mutations) < 2:
            return None
        
        try:
            # Group by day
            daily_counts = {}
            for mutation in mutations:
                timestamp = mutation.get('timestamp')
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                
                date = timestamp.date()
                daily_counts[date] = daily_counts.get(date, 0) + 1
            
            if not daily_counts:
                return None
            
            # Find peak
            peak_date = max(daily_counts, key=daily_counts.get)
            peak_count = daily_counts[peak_date]
            
            return {
                'date': peak_date.isoformat(),
                'mutation_count': peak_count
            }
        except Exception as e:
            logger.error(f"Peak period calculation failed: {e}")
            return None
    
    def predict_spread(self, mutations: List[Dict], days_ahead: int = 7) -> Dict:
        """Predict future spread trajectory"""
        if len(mutations) < 3:
            return {
                'prediction': 'insufficient_data',
                'current_count': len(mutations),
                'predicted_count': len(mutations),
                'days_ahead': days_ahead,
                'growth_rate': 0,
                'confidence': 'low'
            }
        
        try:
            # Sort by timestamp
            sorted_mutations = sorted(
                mutations,
                key=lambda x: x.get('timestamp', datetime.now())
            )
            
            # Calculate recent growth rate (last 7 days)
            recent_mutations = [
                m for m in sorted_mutations
                if self._is_recent(m.get('timestamp'), days=7)
            ]
            
            recent_rate = len(recent_mutations) / 7
            
            # Simple exponential growth prediction
            predicted_count = int(len(mutations) * (1 + recent_rate) ** days_ahead)
            
            return {
                'prediction': 'exponential_growth',
                'current_count': len(mutations),
                'predicted_count': predicted_count,
                'days_ahead': days_ahead,
                'growth_rate': round(recent_rate, 2),
                'confidence': 'medium' if len(mutations) > 10 else 'low'
            }
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                'prediction': 'error',
                'current_count': len(mutations),
                'predicted_count': len(mutations),
                'days_ahead': days_ahead,
                'growth_rate': 0,
                'confidence': 'low'
            }
    
    def _is_recent(self, timestamp, days: int = 7) -> bool:
        """Check if timestamp is within recent days"""
        try:
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            cutoff = datetime.now() - timedelta(days=days)
            return timestamp >= cutoff
        except:
            return False
