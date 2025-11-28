from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional
from datetime import datetime
from bson import ObjectId
import uuid
import redis
from rq import Queue

from app.config import settings
from app.database import (
    async_submissions, async_claims, async_summaries,
    async_reports, init_db, test_connection
)
from app.storage import storage
from app.models import SubmissionResponse, ResultResponse

# Initialize Redis and task queue
try:
    redis_conn = redis.from_url(settings.redis_url)
    task_queue = Queue('default', connection=redis_conn)
    print("✅ Redis connection established")
except Exception as e:
    print(f"⚠️  Redis connection failed: {e}")
    print("⚠️  Background processing will not work")
    task_queue = None

# Create FastAPI app
app = FastAPI(
    title="AI Fact-Checker API",
    description="8-Agent fact-checking system",
    version="1.0.0"
)

# CORS middleware - Allow Django domain
allowed_origins = settings.allowed_origins.split(",") if settings.allowed_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    print("🚀 Starting Fact-Checker API...")
    if test_connection():
        init_db()
        print("✅ API ready!")
    else:
        print("❌ Failed to connect to database")

# Include dashboard routes
try:
    from app.api.dashboard import router as dashboard_router
    app.include_router(dashboard_router)
    print("✅ Dashboard API routes loaded")
except Exception as e:
    print(f"⚠️  Dashboard routes failed to load: {e}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "AI Fact-Checker",
        "version": "1.0.0",
        "message": "Welcome to the AI Fact-Checking System"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "storage": settings.storage_mode,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/check", response_model=SubmissionResponse)
async def check_claim(
    text: Optional[str] = Form(None),
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """
    Submit a claim for fact-checking
    
    Accepts:
    - text: Plain text claim
    - url: URL to article/post
    - file: Image file (for OCR)
    """
    
    # Determine input type
    if file:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(400, "Only image files are supported")
        
        input_type = "image"
        
        # Read file
        file_bytes = await file.read()
        
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
        file_path = f"uploads/{uuid.uuid4()}.{file_ext}"
        
        # Upload to storage
        input_ref = storage.upload_file(file_bytes, file_path)
        
    elif url:
        if not url.startswith('http'):
            raise HTTPException(400, "Invalid URL format")
        input_type = "url"
        input_ref = url
        
    elif text:
        input_type = "text"
        input_ref = text
        
    else:
        raise HTTPException(400, "No input provided. Please provide text, url, or file.")
    
    # Create submission document
    submission = {
        "user_id": None,  # Add authentication later
        "input_type": input_type,
        "input_ref": input_ref,
        "created_at": datetime.utcnow(),
        "status": "queued"
    }
    
    result = await async_submissions.insert_one(submission)
    submission_id = str(result.inserted_id)
    
    # Enqueue processing job (Phase 2)
    if task_queue:
        from app.orchestrator import process_submission
        job = task_queue.enqueue(
            process_submission,
            submission_id,
            job_timeout=-1  # No timeout for Windows compatibility
        )
        print(f"📝 New submission created: {submission_id} (type: {input_type})")
        print(f"✓ Job enqueued: {job.id}")
    else:
        print(f"📝 New submission created: {submission_id} (type: {input_type})")
        print(f"⚠️  Redis not available - job not enqueued")
    
    return SubmissionResponse(
        submission_id=submission_id,
        status="queued",
        estimated_time=60
    )

@app.get("/result/{submission_id}", response_model=ResultResponse)
async def get_result(submission_id: str):
    """Get fact-check result for a submission"""
    
    # Validate ObjectId
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(400, "Invalid submission ID")
    
    # Get submission
    submission = await async_submissions.find_one(
        {"_id": ObjectId(submission_id)}
    )
    
    if not submission:
        raise HTTPException(404, "Submission not found")
    
    # If still processing
    if submission['status'] in ['queued', 'processing']:
        return ResultResponse(status=submission['status'])
    
    # If error
    if submission['status'] == 'error':
        return ResultResponse(
            status='error',
            explanation=submission.get('error_message', 'Unknown error')
        )
    
    # Get claim
    claim = await async_claims.find_one(
        {"submission_id": ObjectId(submission_id)}
    )
    
    if not claim:
        return ResultResponse(status='processing')
    
    # Get summary
    summary = await async_summaries.find_one(
        {"claim_id": claim['_id']}
    )
    
    # Get report
    report = await async_reports.find_one(
        {"claim_id": claim['_id']}
    )
    
    # Build response
    response = ResultResponse(
        status=submission['status'],
        claim=claim.get('claim_text'),
        normalized_claim=claim.get('normalized_claim')
    )
    
    if summary:
        response.confidence = summary.get('confidence')
        response.explanation = summary.get('short_explanation')
        response.sources = summary.get('top_sources', [])
    
    if report:
        response.report_url = storage.get_file_url(report['pdf_path'])
    
    return response

@app.get("/report/{submission_id}")
async def download_report(submission_id: str):
    """Download PDF report"""
    
    if not ObjectId.is_valid(submission_id):
        raise HTTPException(400, "Invalid submission ID")
    
    # Get claim
    claim = await async_claims.find_one(
        {"submission_id": ObjectId(submission_id)}
    )
    
    if not claim:
        raise HTTPException(404, "Claim not found")
    
    # Get report
    report = await async_reports.find_one(
        {"claim_id": claim['_id']}
    )
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Download file
    pdf_path = report['pdf_path']
    
    if settings.storage_mode == 'local':
        return FileResponse(
            pdf_path,
            media_type='application/pdf',
            filename=f"report_{submission_id}.pdf"
        )
    else:
        # For S3, redirect to presigned URL
        url = storage.get_file_url(pdf_path)
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
