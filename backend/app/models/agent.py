from sqlalchemy import Column, String, Float, ForeignKey, JSON, Enum, DateTime, Integer
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base import BaseModel

class AgentStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    RETRY = "RETRY"
    COMPLETED = "COMPLETED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class AgentRun(BaseModel):
    __tablename__ = "agent_runs"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    agent_name = Column(String, index=True)
    agent_version = Column(String, default="1.0.0")
    status = Column(Enum(AgentStatus), default=AgentStatus.QUEUED)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=True)
    
    input_summary = Column(String, nullable=True)
    output_summary = Column(String, nullable=True)
    
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    confidence = Column(Float, nullable=True)
    
    error_message = Column(String, nullable=True)
    retry_count = Column(Integer, default=0)
    
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
    
class SandboxStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"
    FAILED = "FAILED"
    TERMINATED = "TERMINATED"

class SandboxSession(BaseModel):
    __tablename__ = "sandbox_sessions"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    status = Column(Enum(SandboxStatus), default=SandboxStatus.QUEUED)
    
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    timeout = Column(Float, default=30.0)
    
    target_url = Column(String)
    browser_type = Column(String, default="chromium")
    browser_version = Column(String, nullable=True)
    
    error = Column(String, nullable=True)
    artifact_count = Column(Integer, default=0)
    event_count = Column(Integer, default=0)
    
    events = Column(JSON, nullable=True)
    network_summary = Column(JSON, nullable=True)
    screenshots = Column(JSON, nullable=True)
    
    investigation = relationship("Investigation", back_populates="sandbox_sessions")
