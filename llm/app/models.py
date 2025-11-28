from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class SubmissionCreate(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    # file handled separately in endpoint

class SubmissionResponse(BaseModel):
    submission_id: str
    status: str
    estimated_time: int = 60

class ResultResponse(BaseModel):
    status: str
    claim: Optional[str] = None
    normalized_claim: Optional[str] = None
    verdict: Optional[str] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    sources: Optional[List[dict]] = None
    report_url: Optional[str] = None
