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
