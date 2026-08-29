from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ThreatTrendPoint(BaseModel):
    timestamp: str
    count: int
    malicious: int
    suspicious: int
    safe: int

class RecentInvestigationItem(BaseModel):
    id: str
    display_id: str
    input_type: str
    target: str
    classification: Optional[str] = "UNKNOWN"
    final_risk_score: Optional[float] = None
    status: str
    created_at: datetime

class DashboardStatsResponse(BaseModel):
    total_investigations: int
    active_analysis_count: int
    safe_count: int
    low_count: int
    medium_count: int
    high_count: int
    critical_count: int
    unknown_count: int
    threat_intel_matches: int
    sandbox_executions: int
    total_reports: int
    pending_reports: int
    recent_investigations: List[RecentInvestigationItem] = Field(default_factory=list)
    threat_trend_24h: List[ThreatTrendPoint] = Field(default_factory=list)
