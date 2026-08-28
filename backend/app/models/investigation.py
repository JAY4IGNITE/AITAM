from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class InvestigationStatus(str, enum.Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    INITIAL_ANALYSIS = "INITIAL_ANALYSIS"
    AGENT_ANALYSIS = "AGENT_ANALYSIS"
    RISK_EVALUATION = "RISK_EVALUATION"
    SANDBOX_QUEUED = "SANDBOX_QUEUED"
    SANDBOX_RUNNING = "SANDBOX_RUNNING"
    BEHAVIOR_ANALYSIS = "BEHAVIOR_ANALYSIS"
    RE_EVALUATION = "RE_EVALUATION"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"
    EVIDENCE_CORRELATION = "EVIDENCE_CORRELATION"
    REPORT_GENERATION = "REPORT_GENERATION"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class InputType(str, enum.Enum):
    URL = "URL"
    EMAIL = "EMAIL"
    SMS = "SMS"
    QR = "QR"
    WEBPAGE = "WEBPAGE"
    SOCIAL = "SOCIAL"

class Investigation(BaseModel):
    __tablename__ = "investigations"
    
    # Custom display ID like INV-2026-000001
    display_id = Column(String, unique=True, index=True)
    input_type = Column(Enum(InputType))
    target = Column(String) # The URL, email content, etc.
    normalized_input = Column(String, nullable=True)
    status = Column(Enum(InvestigationStatus), default=InvestigationStatus.CREATED)
    current_stage = Column(String, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    initial_risk_score = Column(Float, nullable=True)
    final_risk_score = Column(Float, nullable=True)
    classification = Column(String, nullable=True) # SAFE, LOW, SUSPICIOUS, HIGH, CRITICAL
    confidence = Column(Float, nullable=True)
    
    # Relationships
    agent_runs = relationship("AgentRun", back_populates="investigation", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")
    sandbox_sessions = relationship("SandboxSession", back_populates="investigation", cascade="all, delete-orphan")
    events = relationship("InvestigationEvent", back_populates="investigation", cascade="all, delete-orphan")
    findings = relationship("Finding", back_populates="investigation", cascade="all, delete-orphan")
