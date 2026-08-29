from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from ..models.agent import AgentStatus

class AgentRunResponse(BaseModel):
    id: str
    agent_name: str
    status: AgentStatus
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    confidence: Optional[float] = None
    error_message: Optional[str] = None
    outputs: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class EvidenceResponse(BaseModel):
    id: str
    agent_name: str
    evidence_type: str
    severity: str
    observed_fact: str
    confidence: float
    related_ioc: Optional[str] = None
    related_attack_step: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IOCResponse(BaseModel):
    id: str
    ioc_type: str
    value: str
    source_agent: str
    confidence: float
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
