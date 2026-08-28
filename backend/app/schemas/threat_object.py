from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from ..models.investigation import InputType

class Indicator(BaseModel):
    type: str # e.g. "URL", "DOMAIN", "EMAIL", "PHONE"
    value: str
    confidence: float = 1.0
    context: Optional[str] = None

class ThreatObject(BaseModel):
    input_type: InputType
    raw_input_reference: str
    normalized_text: str
    
    # Specific extracted entities
    urls: List[str] = Field(default_factory=list)
    domains: List[str] = Field(default_factory=list)
    email_addresses: List[str] = Field(default_factory=list)
    phone_numbers: List[str] = Field(default_factory=list)
    
    # Other indicators
    extracted_indicators: List[Indicator] = Field(default_factory=list)
    
    # Optional metadata (attachments, headers, etc)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AgentInput(BaseModel):
    investigation_id: str
    input_type: InputType
    threat_object: ThreatObject
    previous_findings: List[Dict[str, Any]] = Field(default_factory=list)
    relevant_evidence: List[Dict[str, Any]] = Field(default_factory=list)
