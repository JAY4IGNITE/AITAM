from sqlalchemy import Column, String, ForeignKey, Float
from sqlalchemy.orm import relationship
from .base import BaseModel

class IOC(BaseModel):
    __tablename__ = "iocs"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    ioc_type = Column(String) # URL, DOMAIN, IP, HASH, EMAIL
    value = Column(String, index=True)
    source_agent = Column(String)
    confidence = Column(Float)
    first_seen = Column(String)
    last_seen = Column(String)
    
    investigation = relationship("Investigation")

class Artifact(BaseModel):
    __tablename__ = "artifacts"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    filename = Column(String)
    mime_type = Column(String)
    size = Column(String)
    sha256 = Column(String)
    source_url = Column(String)
    quarantine_status = Column(String) # DETECTED, QUARANTINED, ANALYZING, ANALYZED, DESTROYED
    
    investigation = relationship("Investigation")
