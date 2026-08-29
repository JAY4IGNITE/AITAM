from pydantic import BaseModel, Field, ConfigDict
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
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reputation_score: Optional[int] = None # Scale e.g., 0-100
    categories: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    lookup_timestamp: datetime = Field(default_factory=datetime.utcnow)
    provider_metadata: Dict[str, Any] = Field(default_factory=dict)

class ThreatIntelProviderHealth(BaseModel):
    provider_name: str
    enabled: bool
    status: str
    latency_ms: Optional[float] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None

class ThreatIndicatorCreate(BaseModel):
    indicator: str
    indicator_type: str  # URL, DOMAIN, IP, HASH, EMAIL
    source: str = "MANUAL"
    classification: str = "MALICIOUS"
    confidence: float = 1.0
    status: str = "ACTIVE"
    tags: List[str] = Field(default_factory=list)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)

class ThreatIndicatorResponse(BaseModel):
    id: str
    indicator: str
    indicator_type: str
    source: str
    classification: str
    confidence: float
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    status: str
    tags: List[str] = Field(default_factory=list)
    metadata_payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PaginatedThreatIndicators(BaseModel):
    items: List[ThreatIndicatorResponse]
    total: int
    page: int
    limit: int
    pages: int

class ThreatFeedSyncResponse(BaseModel):
    status: str
    source: str
    new_indicators_count: int
    updated_indicators_count: int
    timestamp: datetime
