from sqlalchemy import Column, String, Float, ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base import BaseModel

class AgentStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class AgentRun(BaseModel):
    __tablename__ = "agent_runs"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    agent_name = Column(String, index=True)
    status = Column(Enum(AgentStatus), default=AgentStatus.QUEUED)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    error_message = Column(String, nullable=True)
    
    investigation = relationship("Investigation", back_populates="agent_runs")

class Evidence(BaseModel):
    __tablename__ = "evidence"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    agent_name = Column(String)
    
    evidence_type = Column(String)
    severity = Column(String) # low, medium, high, critical
    observed_fact = Column(String)
    confidence = Column(Float)
    
    related_ioc = Column(String, nullable=True)
    related_attack_step = Column(String, nullable=True)
    
    investigation = relationship("Investigation", back_populates="evidence")
    
class SandboxSession(BaseModel):
    __tablename__ = "sandbox_sessions"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    status = Column(String) # RUNNING, COMPLETED, FAILED
    
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    
    target_url = Column(String)
    browser_version = Column(String, nullable=True)
    
    events = Column(JSON, nullable=True)
    network_summary = Column(JSON, nullable=True)
    screenshots = Column(JSON, nullable=True)
    
    investigation = relationship("Investigation", back_populates="sandbox_sessions")
