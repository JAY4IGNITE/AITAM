from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Float, DateTime
from datetime import datetime
import uuid

from .base import Base

class TriageResult(Base):
    __tablename__ = "triage_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    priority = Column(String) # P1_CRITICAL, P2_HIGH, P3_MEDIUM, P4_LOW
    confidence = Column(Float, default=1.0)
    reasons = Column(JSON, default=list) # List of reasons
    created_at = Column(DateTime, default=datetime.utcnow)

class InvestigationPlan(Base):
    __tablename__ = "investigation_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    priority = Column(String)
    depth = Column(String, default="LEVEL_1")
    planned_agents = Column(JSON) # Deprecated logic, keeping for backward compat
    reason = Column(String)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)

class InvestigationTask(Base):
    __tablename__ = "investigation_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    plan_id = Column(String, ForeignKey("investigation_plans.id", ondelete="CASCADE"), index=True)
    task_type = Column(String)
    status = Column(String, default="PLANNED") # PLANNED, QUEUED, RUNNING, COMPLETED, FAILED, SKIPPED, CANCELLED
    assigned_agent = Column(String)
    priority = Column(Integer, default=5)
    dependencies = Column(JSON, default=list) # List of task IDs
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)

class AgentMessage(Base):
    __tablename__ = "agent_messages"
    
    message_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    sender = Column(String)
    receiver = Column(String)
    message_type = Column(String) # REQUEST_ANALYSIS, ANALYSIS_RESULT, etc.
    payload = Column(JSON, default=dict)
    evidence_refs = Column(JSON, default=list)
    confidence = Column(Float, default=1.0)
    timestamp = Column(DateTime, default=datetime.utcnow)

class AgentToolPolicy(Base):
    __tablename__ = "agent_tool_policies"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    agent = Column(String)
    tool = Column(String)
    reason = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    action_type = Column(String) # BLOCK, REPORT, EDUCATE
    description = Column(String)
    risk = Column(Float)
    confidence = Column(Float, default=1.0)
    requested_by = Column(String)
    approved_by = Column(String, nullable=True)
    status = Column(String, default="RECOMMENDED") # RECOMMENDED, PENDING_APPROVAL, APPROVED, REJECTED, EXECUTED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, nullable=True)

class Incident(Base):
    __tablename__ = "incidents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), unique=True)
    title = Column(String)
    severity = Column(String)
    priority = Column(String)
    status = Column(String, default="OPEN") # OPEN, INVESTIGATING, CONFIRMED, CONTAINMENT_RECOMMENDED, RESOLVED, FALSE_POSITIVE
    summary = Column(String)
    attack_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class InvestigationFeedback(Base):
    __tablename__ = "investigation_feedback"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    verdict = Column(String) # FALSE_POSITIVE
    reason = Column(String)
    evidence_quality = Column(String, nullable=True)
    analyst_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
