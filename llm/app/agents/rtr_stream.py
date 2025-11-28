"""
RTR Event Stream Manager
Manages Redis Streams for real-time events
"""

import redis
import json
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EventStreamManager:
    def __init__(self, redis_url: str):
        try:
            self.redis_client = redis.from_url(redis_url)
            self.stream_name = 'misinformation:events'
            logger.info("✓ RTR: Connected to Redis Streams")
        except Exception as e:
            logger.error(f"RTR: Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def publish_event(self, event_type: str, event_data: Dict):
        """Publish event to stream"""
        if not self.redis_client:
            return False
        
        try:
            event = {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': json.dumps(event_data)
            }
            
            self.redis_client.xadd(
                self.stream_name,
                event,
                maxlen=10000  # Keep last 10k events
            )
            
            logger.debug(f"RTR: Published event: {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"RTR: Failed to publish event: {e}")
            return False
    
    def consume_events(self, last_id: str = '0', count: int = 100) -> List[Dict]:
        """Consume events from stream"""
        if not self.redis_client:
            return []
        
        try:
            events = self.redis_client.xread(
                {self.stream_name: last_id},
                count=count,
                block=1000  # Block for 1 second
            )
            
            processed_events = []
            for stream_name, messages in events:
                for message_id, message_data in messages:
                    processed_events.append({
                        'id': message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id,
                        'type': message_data[b'type'].decode('utf-8') if isinstance(message_data[b'type'], bytes) else message_data[b'type'],
                        'timestamp': message_data[b'timestamp'].decode('utf-8') if isinstance(message_data[b'timestamp'], bytes) else message_data[b'timestamp'],
                        'data': json.loads(message_data[b'data'].decode('utf-8') if isinstance(message_data[b'data'], bytes) else message_data[b'data'])
                    })
            
            return processed_events
            
        except Exception as e:
            logger.error(f"RTR: Failed to consume events: {e}")
            return []
    
    def get_recent_events(self, count: int = 50) -> List[Dict]:
        """Get recent events"""
        if not self.redis_client:
            return []
        
        try:
            events = self.redis_client.xrevrange(
                self.stream_name,
                count=count
            )
            
            processed_events = []
            for message_id, message_data in events:
                processed_events.append({
                    'id': message_id.decode('utf-8') if isinstance(message_id, bytes) else message_id,
                    'type': message_data[b'type'].decode('utf-8') if isinstance(message_data[b'type'], bytes) else message_data[b'type'],
                    'timestamp': message_data[b'timestamp'].decode('utf-8') if isinstance(message_data[b'timestamp'], bytes) else message_data[b'timestamp'],
                    'data': json.loads(message_data[b'data'].decode('utf-8') if isinstance(message_data[b'data'], bytes) else message_data[b'data'])
                })
            
            return processed_events
            
        except Exception as e:
            logger.error(f"RTR: Failed to get recent events: {e}")
            return []
