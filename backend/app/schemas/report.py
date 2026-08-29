from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime

class ThreatReportCreate(BaseModel):
    indicator: str
    report_type: str = "URL"  # URL, EMAIL, SMS, QR, WEBPAGE, SOCIAL
    description: str
    investigation_id: Optional[str] = None
    reporter_email: Optional[str] = None

class ThreatReportStatusUpdate(BaseModel):
    status: str  # PENDING, REVIEWED, RESOLVED
    resolution_notes: Optional[str] = None

class ThreatReportResponse(BaseModel):
    id: str
    indicator: str
    report_type: str
    description: str
    investigation_id: Optional[str] = None
    reporter_email: Optional[str] = None
    status: str
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedThreatReports(BaseModel):
    items: List[ThreatReportResponse]
    total: int
    page: int
    limit: int
    pages: int
