from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base import BaseModel

class AlertStatus(str, enum.Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

class Alert(BaseModel):
    __tablename__ = "alerts"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    status = Column(String, default=AlertStatus.OPEN.value) # Using string for simplicity to avoid enum migration issues
    
    severity = Column(String) # CRITICAL, HIGH
    title = Column(String)
    description = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    
    investigation = relationship("Investigation")
