from sqlalchemy import Column, String, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .base import BaseModel

class EvidenceNode(BaseModel):
    __tablename__ = "evidence_nodes"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    node_type = Column(String)
    label = Column(String)
    value_hash = Column(String) # For idempotency
    safe_display_value = Column(String)
    source = Column(String)
    confidence = Column(Float)
    severity = Column(String, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    
    investigation = relationship("Investigation")

class EvidenceEdge(BaseModel):
    __tablename__ = "evidence_edges"
    
    investigation_id = Column(String, ForeignKey("investigations.id"))
    source_node_id = Column(String, ForeignKey("evidence_nodes.id"))
    target_node_id = Column(String, ForeignKey("evidence_nodes.id"))
    relationship_type = Column(String)
    confidence = Column(Float)
    source = Column(String)
    metadata_json = Column(JSON, nullable=True)
    
    investigation = relationship("Investigation")
    source_node = relationship("EvidenceNode", foreign_keys=[source_node_id])
    target_node = relationship("EvidenceNode", foreign_keys=[target_node_id])
