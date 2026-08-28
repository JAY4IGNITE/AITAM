from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.investigation import InvestigationStatus, InputType

class InvestigationCreate(BaseModel):
    input_type: InputType
    target: str = Field(..., description="The URL, email content, or artifact hash")

class InvestigationResponse(BaseModel):
    id: str
    display_id: str
    input_type: InputType
    target: str
    status: InvestigationStatus
    initial_risk_score: Optional[float] = None
    final_risk_score: Optional[float] = None
    classification: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class SandboxSessionResponse(BaseModel):
    id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    target_url: str
    events: Optional[List[Dict[str, Any]]] = None
    network_summary: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True
