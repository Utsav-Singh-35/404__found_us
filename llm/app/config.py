from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str = "mongodb://localhost:27017/"
    mongodb_db: str = "factchecker"
    
    # Redis (Railway provides this automatically)
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AWS S3
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    
    # Storage
    storage_mode: str = "local"  # "s3" or "local"
    local_storage_path: str = "./storage"
    
    # API (Railway sets PORT automatically)
    api_host: str = "0.0.0.0"
    api_port: int = int(os.getenv("PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security
    secret_key: str = "change-this-in-production"
    
    # CORS - Allow Django domain
    allowed_origins: str = "https://satyamatrix.onrender.com,http://localhost:8000"
    
    # API Keys
    ocr_space_key: str = ""
    serpapi_key: str = ""
    google_factcheck_key: str = ""
    
    # LLM Configuration
    openrouter_api_key: str = ""
    openrouter_model: str = "openai/gpt-4o-mini:free"
    openrouter_site_url: str = "https://satyamatrix.onrender.com"
    openrouter_site_name: str = "SatyaMatrix-FactChecker"
    
    # Alternative LLM providers
    openai_api_key: str = ""
    gemini_api_key: str = ""
    
    # Neo4j Configuration (Phase 1 & 3)
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    
    # CMTE Settings (Phase 1)
    cmte_similarity_threshold: float = 0.85
    cmte_max_family_size: int = 100
    cmte_enable_image_tracking: bool = False
    
    # NRI Settings (Phase 2)
    nri_enable_narrative_classification: bool = True
    nri_enable_corrective_messaging: bool = True
    nri_narrative_confidence_threshold: float = 0.7
    
    # CRG Settings (Phase 3)
    crg_enable_trust_scoring: bool = True
    crg_pagerank_iterations: int = 20
    crg_min_trust_score: float = 0.3
    
    # RTR Settings (Phase 4)
    rtr_enable_realtime_tracking: bool = True
    rtr_update_interval_seconds: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()
