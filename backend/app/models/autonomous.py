from sqlalchemy import Column, String, Integer, ForeignKey, JSON, Float, DateTime
from datetime import datetime
import uuid

from .base import Base

class TriageResult(Base):
    __tablename__ = "triage_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    priority = Column(String) # LOW, HIGH
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class InvestigationPlan(Base):
    __tablename__ = "investigation_plans"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    planned_agents = Column(JSON) # List of agent class names
    reason = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class ResponseAction(Base):
    __tablename__ = "response_actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    action_type = Column(String) # BLOCK, REPORT, EDUCATE
    details = Column(String)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
