from sqlalchemy import Column, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class Report(BaseModel):
    __tablename__ = "reports"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    report_type = Column(String) # CONSUMER, ANALYST
    content = Column(JSON) # Structured report content
    
    investigation = relationship("Investigation")

class AttackStep(BaseModel):
    __tablename__ = "attack_steps"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    step_order = Column(String)
    description = Column(String)
    mitre_tactic = Column(String, nullable=True)
    mitre_technique = Column(String, nullable=True)
    evidence_ids = Column(JSON) # List of evidence IDs supporting this step
    
    investigation = relationship("Investigation")
