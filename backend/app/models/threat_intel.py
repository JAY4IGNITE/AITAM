from sqlalchemy import Column, String, Float, DateTime, JSON, Index, UniqueConstraint
from datetime import datetime
from .base import BaseModel

class ThreatIndicator(BaseModel):
    __tablename__ = "threat_indicators"

    indicator = Column(String, nullable=False, index=True)
    indicator_type = Column(String, nullable=False, index=True)  # URL, DOMAIN, IP, HASH, EMAIL
    source = Column(String, nullable=False, index=True)  # URLHAUS, VIRUSTOTAL, GOOGLE_SAFE_BROWSING, USER_REPORT, LOCAL_FEED
    classification = Column(String, nullable=False, default="MALICIOUS", index=True)  # MALICIOUS, SUSPICIOUS, CLEAN, UNKNOWN
    confidence = Column(Float, default=1.0)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE", index=True)  # ACTIVE, INACTIVE, RESOLVED
    tags = Column(JSON, default=list)
    metadata_payload = Column(JSON, default=dict)

    __table_args__ = (
        UniqueConstraint('indicator', 'source', name='uq_indicator_source'),
        Index('ix_threat_ind_type_val', 'indicator_type', 'indicator'),
    )
