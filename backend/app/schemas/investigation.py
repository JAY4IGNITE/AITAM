from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.investigation import InvestigationStatus, InputType

class InvestigationCreate(BaseModel):
    input_type: InputType
    target: Optional[str] = Field(None, description="The URL, email content, SMS text, or artifact payload")
    content: Optional[str] = Field(None, description="Alternative field name for target")

    @model_validator(mode='before')
    @classmethod
    def validate_target_or_content(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("target") and data.get("content"):
                data["target"] = data["content"]
            elif not data.get("target"):
                raise ValueError("Target or content field is required")
        return data

class InvestigationResponse(BaseModel):
    id: str
    display_id: str
    input_type: InputType
    target: str
    status: InvestigationStatus
    current_stage: Optional[str] = None
    initial_risk_score: Optional[float] = None
    final_risk_score: Optional[float] = None
    classification: Optional[str] = None
    confidence: Optional[float] = None
    findings_count: Optional[int] = 0
    sandbox_status: Optional[str] = "NOT_REQUIRED"
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class PaginatedInvestigationsResponse(BaseModel):
    items: List[InvestigationResponse]
    total: int
    page: int
    limit: int
    pages: int

class SandboxSessionResponse(BaseModel):
    id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    target_url: str
    events: Optional[List[Dict[str, Any]]] = None
    network_summary: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)

class QRUploadResponse(BaseModel):
    investigation_id: str
    decoded_payload: str
    payload_type: str
    status: str
