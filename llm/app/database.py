from pymongo import MongoClient
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import certifi

# SSL/TLS configuration for Python 3.13 compatibility
mongo_options = {
    'tlsAllowInvalidCertificates': False,
    'tlsCAFile': certifi.where(),
    'serverSelectionTimeoutMS': 5000,
    'connectTimeoutMS': 10000,
}

# Synchronous client (for workers)
client = MongoClient(settings.mongodb_uri, **mongo_options)
db = client[settings.mongodb_db]

# Async client (for FastAPI)
async_client = AsyncIOMotorClient(settings.mongodb_uri, **mongo_options)
async_db = async_client[settings.mongodb_db]

# Collections
submissions_collection = db.submissions
claims_collection = db.claims
fact_checks_collection = db.fact_checks
evidence_collection = db.evidence
summaries_collection = db.summaries
reports_collection = db.reports

# Async collections
async_submissions = async_db.submissions
async_claims = async_db.claims
async_fact_checks = async_db.fact_checks
async_evidence = async_db.evidence
async_summaries = async_db.summaries
async_reports = async_db.reports

def init_db():
    """Initialize database with indexes"""
    print("🔧 Creating database indexes...")
    
    # Submissions indexes
    submissions_collection.create_index("status")
    submissions_collection.create_index("created_at")
    
    # Claims indexes
    claims_collection.create_index("submission_id")
    claims_collection.create_index([("normalized_claim", "text")])
    
    # Fact checks indexes
    fact_checks_collection.create_index("claim_id")
    fact_checks_collection.create_index("api_name")
    
    # Evidence indexes
    evidence_collection.create_index("claim_id")
    evidence_collection.create_index("supports_claim")
    evidence_collection.create_index("reliability_score")
    
    # Summaries indexes
    summaries_collection.create_index("claim_id", unique=True)
    
    # Reports indexes
    reports_collection.create_index("claim_id", unique=True)
    
    print("✅ Database indexes created successfully")

def test_connection():
    """Test MongoDB connection"""
    try:
        client.admin.command('ping')
        print("✅ MongoDB connection successful")
        print(f"📊 Database: {settings.mongodb_db}")
        return True
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False
