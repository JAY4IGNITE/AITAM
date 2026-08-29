from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class TempMailInboxCreate(BaseModel):
    prefix: Optional[str] = None
    domain: Optional[str] = None

class TempMailInboxResponse(BaseModel):
    id: str
    inbox_id: str
    email_address: str
    domain: str
    status: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)

class TempMailMessageSummary(BaseModel):
    id: str
    inbox_id: str
    provider_message_id: str
    sender: Optional[str] = None
    sender_domain: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    received_at: datetime
    status: str
    investigation_id: Optional[str] = None
    risk_score: Optional[float] = None
    risk_level: Optional[str] = None
    has_attachments: bool = False
    urls_count: int = 0

    model_config = ConfigDict(from_attributes=True)

class TempMailMessageDetail(BaseModel):
    id: str
    inbox_id: str
    provider_message_id: str
    sender: Optional[str] = None
    sender_domain: Optional[str] = None
    recipient: Optional[str] = None
    subject: Optional[str] = None
    received_at: datetime
    text_body: Optional[str] = None
    html_body: Optional[str] = None
    raw_eml: Optional[str] = None
    attachment_metadata: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_urls: List[str] = Field(default_factory=list)
    investigation_id: Optional[str] = None
    status: str
    processed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TempMailPollResponse(BaseModel):
    inbox_id: str
    email_address: str
    new_messages_count: int
    total_messages_count: int
    investigations_dispatched: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TempMailHealthStatus(BaseModel):
    provider: str
    configured: bool
    status: str
    active_inboxes_count: int
    latency_ms: Optional[float] = None
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    error: Optional[str] = None
