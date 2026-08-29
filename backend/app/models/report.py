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
    investigation = relationship("Investigation")

class ThreatReport(BaseModel):
    __tablename__ = "threat_reports"

    indicator = Column(String, nullable=False, index=True)
    report_type = Column(String, nullable=False, default="URL")  # URL, EMAIL, SMS, QR, WEBPAGE, SOCIAL
    description = Column(String, nullable=False)
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True, index=True)
    reporter_email = Column(String, nullable=True)
    status = Column(String, nullable=False, default="PENDING", index=True)  # PENDING, REVIEWED, RESOLVED
    resolution_notes = Column(String, nullable=True)

    investigation = relationship("Investigation")

