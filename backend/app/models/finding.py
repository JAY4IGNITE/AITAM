from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import BaseModel

class Finding(BaseModel):
    __tablename__ = "findings"
    
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="CASCADE"), index=True)
    agent = Column(String, index=True)
    category = Column(String, index=True)
    title = Column(String)
    description = Column(String)
    severity = Column(String) # low, medium, high, critical
    confidence = Column(Float)
    risk_contribution = Column(Integer, default=0)
    
    investigation = relationship("Investigation", back_populates="findings")
