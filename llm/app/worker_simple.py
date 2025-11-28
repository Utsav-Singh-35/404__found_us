"""
Simple Background Worker - Robust Redis Connection
"""

import redis
import time
import json
from app.config import settings
from app.orchestrator import process_submission

def connect_redis_with_retry(max_retries=5):
    """Connect to Redis with retry logic"""
    for attempt in range(max_retries):
        try:
            conn = redis.from_url(
                settings.redis_url,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Test connection
            conn.ping()
            print(f"✅ Redis connected successfully!")
            return conn
        except Exception as e:
            print(f"⚠️  Redis connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5)
            else:
                raise

def main():
    """Main worker loop"""
    print("="*60)
    print("🚀 Starting Simple Worker")
    print("="*60)
    
    # Connect to Redis with retry
    redis_conn = connect_redis_with_retry()
    
    print(f"📡 Redis: {settings.redis_url[:50]}...")
    print(f"📋 Listening for jobs...")
    print("="*60)
    
    consecutive_errors = 0
    max_consecutive_errors = 10
    
    while True:
        try:
            # Check for jobs in default queue
            job_data = redis_conn.blpop('rq:queue:default', timeout=5)
            
            if job_data:
                queue_name, job_id = job_data
                job_id = job_id.decode('utf-8') if isinstance(job_id, bytes) else job_id
                
                print(f"\n📝 Processing job: {job_id}")
                
                # Get job details
                job_key = f'rq:job:{job_id}'
                job_info = redis_conn.hgetall(job_key)
                
                # Extract submission_id from job data
                data_field = job_info.get(b'data') or job_info.get('data')
                if data_field:
                    import pickle
                    try:
                        args, kwargs = pickle.loads(data_field)
                        if args:
                            submission_id = args[0]
                            print(f"✓ Submission ID: {submission_id}")
                            
                            # Process the submission
                            result = process_submission(submission_id)
                            
                            if result.get('success'):
                                print(f"✅ Job completed successfully!")
                            else:
                                print(f"❌ Job failed: {result.get('error')}")
                            
                            # Mark job as finished
                            redis_conn.hset(job_key, 'status', 'finished')
                            
                            consecutive_errors = 0
                    except Exception as e:
                        print(f"❌ Job execution error: {e}")
                        redis_conn.hset(job_key, 'status', 'failed')
                        consecutive_errors += 1
            else:
                # No job, reset error counter
                consecutive_errors = 0
        
        except redis.ConnectionError as e:
            consecutive_errors += 1
            print(f"⚠️  Redis connection error ({consecutive_errors}/{max_consecutive_errors}): {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                print(f"❌ Too many consecutive errors. Reconnecting...")
                try:
                    redis_conn = connect_redis_with_retry()
                    consecutive_errors = 0
                except Exception as reconnect_error:
                    print(f"❌ Reconnection failed: {reconnect_error}")
                    print(f"⏸️  Waiting 30 seconds before retry...")
                    time.sleep(30)
            else:
                time.sleep(2)
        
        except KeyboardInterrupt:
            print("\n⏹️  Worker stopped by user")
            break
        
        except Exception as e:
            consecutive_errors += 1
            print(f"⚠️  Worker error ({consecutive_errors}/{max_consecutive_errors}): {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                print(f"❌ Too many errors. Restarting worker...")
                consecutive_errors = 0
                time.sleep(10)
            else:
                time.sleep(2)

if __name__ == "__main__":
    main()
