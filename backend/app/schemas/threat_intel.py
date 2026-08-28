from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime

class Verdict(str, Enum):
    CLEAN = "CLEAN"
    SUSPICIOUS = "SUSPICIOUS"
    MALICIOUS = "MALICIOUS"
    UNKNOWN = "UNKNOWN"
    ERROR = "ERROR"

class ThreatIntelResult(BaseModel):
    provider: str
    indicator_type: str
    indicator: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    reputation_score: Optional[int] = None # Scale e.g., 0-100
    categories: List[str] = []
    evidence: List[str] = []
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    lookup_timestamp: datetime
    provider_metadata: Dict[str, Any] = {}

class ThreatIntelProviderHealth(BaseModel):
    provider_name: str
    enabled: bool
    status: str
    latency_ms: Optional[float] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
