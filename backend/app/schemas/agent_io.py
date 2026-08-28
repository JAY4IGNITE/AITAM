from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class Signal(BaseModel):
    type: str
    severity: str # low, medium, high, critical
    evidence: str

class AgentOutput(BaseModel):
    agent_name: str
    risk_score: float
    confidence: float
    signals: List[Signal]
    raw_data: Optional[Dict[str, Any]] = None

class AgentResult(BaseModel):
    agent_name: str
    agent_version: str
    status: str
    execution_time: float
    findings: List[Dict[str, Any]] = []
    evidence: List[Dict[str, Any]] = []
    confidence: float = 0.0
    metadata: Dict[str, Any] = {}
    errors: Optional[str] = None

class RiskReason(BaseModel):
    finding: str
    contribution: float

class RiskOutput(BaseModel):
    score: float
    level: str
    reasons: List[RiskReason]
    sandbox_required: bool
    deep_analysis_required: bool
