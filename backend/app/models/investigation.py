from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum
from .base import BaseModel

class InvestigationStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    INITIAL_ANALYSIS = "INITIAL_ANALYSIS"
    INITIAL_RISK_EVALUATION = "INITIAL_RISK_EVALUATION"
    SANDBOX_PENDING = "SANDBOX_PENDING"
    SANDBOX_RUNNING = "SANDBOX_RUNNING"
    SANDBOX_COMPLETED = "SANDBOX_COMPLETED"
    BEHAVIOR_ANALYSIS = "BEHAVIOR_ANALYSIS"
    RISK_REEVALUATION = "RISK_REEVALUATION"
    ESCALATION_PENDING = "ESCALATION_PENDING"
    ARTIFACT_QUARANTINE = "ARTIFACT_QUARANTINE"
    DEEP_ANALYSIS = "DEEP_ANALYSIS"
    EVIDENCE_CORRELATION = "EVIDENCE_CORRELATION"
    ATTACK_RECONSTRUCTION = "ATTACK_RECONSTRUCTION"
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
    status = Column(Enum(InvestigationStatus), default=InvestigationStatus.SUBMITTED)
    
    initial_risk_score = Column(Float, nullable=True)
    final_risk_score = Column(Float, nullable=True)
    classification = Column(String, nullable=True) # SAFE, LOW, SUSPICIOUS, HIGH, CRITICAL
    confidence = Column(Float, nullable=True)
    
    # Relationships
    agent_runs = relationship("AgentRun", back_populates="investigation", cascade="all, delete-orphan")
    evidence = relationship("Evidence", back_populates="investigation", cascade="all, delete-orphan")
    sandbox_sessions = relationship("SandboxSession", back_populates="investigation", cascade="all, delete-orphan")
