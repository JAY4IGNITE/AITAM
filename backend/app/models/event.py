from sqlalchemy import Column, String, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class InvestigationEvent(BaseModel):
    __tablename__ = "investigation_events"
    
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    event_type = Column(String, index=True) # e.g. INVESTIGATION_CREATED, AGENT_STARTED
    source = Column(String) # e.g. "Orchestrator", "URLIntelligenceAgent"
    severity = Column(String, default="INFO") # INFO, WARNING, ERROR
    metadata_payload = Column(JSON, nullable=True) # structured metadata
    
    investigation = relationship("Investigation", back_populates="events")
