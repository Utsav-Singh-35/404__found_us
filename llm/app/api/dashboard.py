"""
Dashboard API Endpoints
"""

from fastapi import APIRouter
from app.agents.rtr_aggregator import DashboardAggregator
from app.agents.rtr_stream import EventStreamManager
from app.config import settings

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

aggregator = DashboardAggregator()
stream_manager = EventStreamManager(settings.redis_url)

@router.get("/stats")
async def get_dashboard_stats():
    """Get overall dashboard statistics"""
    return aggregator.get_dashboard_stats()

@router.get("/top-claims")
async def get_top_claims(limit: int = 10):
    """Get top recent claims"""
    return aggregator.get_top_claims(limit)

@router.get("/narratives")
async def get_narrative_distribution():
    """Get narrative type distribution"""
    return aggregator.get_narrative_distribution()

@router.get("/time-series")
async def get_time_series(hours: int = 24):
    """Get time series data"""
    return aggregator.get_time_series(hours)

@router.get("/threats")
async def get_emerging_threats(threshold: float = 0.7):
    """Get emerging high-risk claims"""
    return aggregator.get_emerging_threats(threshold)

@router.get("/recent-events")
async def get_recent_events(count: int = 50):
    """Get recent events from stream"""
    return stream_manager.get_recent_events(count)
