#!/usr/bin/env python
"""
Start both API server and worker in a single process
"""
import os
import sys
import subprocess
import time
import signal

def start_worker():
    """Start worker in background"""
    print("🔄 Starting worker...")
    worker_process = subprocess.Popen(
        [sys.executable, "-m", "app.worker_simple"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    print(f"✅ Worker started (PID: {worker_process.pid})")
    return worker_process

def start_api():
    """Start API server in foreground"""
    print("🔄 Starting API server...")
    port = os.getenv("API_PORT", os.getenv("PORT", "8001"))
    api_process = subprocess.Popen(
        ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port],
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    print(f"✅ API server started (PID: {api_process.pid})")
    return api_process

def main():
    print("="*60)
    print("🚀 Starting SatyaMatrix Services")
    print("="*60)
    
    worker = start_worker()
    time.sleep(2)  # Give worker time to start
    
    api = start_api()
    
    def signal_handler(sig, frame):
        print("\n⏹️  Shutting down...")
        worker.terminate()
        api.terminate()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Wait for API process (it runs in foreground)
    api.wait()

if __name__ == "__main__":
    main()
