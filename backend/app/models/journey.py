from sqlalchemy import Column, String, Float, ForeignKey, Integer, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class AttackJourneyStep(BaseModel):
    __tablename__ = "attack_journey_steps"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    sequence = Column(Integer)
    title = Column(String)
    description = Column(String)
    stage = Column(String)
    severity = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    evidence_ids = Column(JSON, nullable=True)
    agent = Column(String, nullable=True)
    risk_before = Column(Float, nullable=True)
    risk_after = Column(Float, nullable=True)
    
    investigation = relationship("Investigation")

class RiskAssessment(BaseModel):
    __tablename__ = "risk_assessments"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    stage = Column(String)
    score = Column(Float)
    level = Column(String)
    reasons = Column(JSON)
    triggered_by = Column(String, nullable=True)
    
    investigation = relationship("Investigation")
