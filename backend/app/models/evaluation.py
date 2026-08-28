from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class EvaluationRun(BaseModel):
    __tablename__ = "evaluation_runs"
    
    dataset_id = Column(String, ForeignKey("datasets.id"))
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED
    configuration = Column(JSON, default=dict)
    thresholds = Column(JSON, default=dict)
    
    # Metrics
    total_samples = Column(Integer, default=0)
    completed_samples = Column(Integer, default=0)
    failed_samples = Column(Integer, default=0)
    
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    false_positive_rate = Column(Float, nullable=True)
    false_negative_rate = Column(Float, nullable=True)
    confusion_matrix = Column(JSON, default=dict)
    
    dataset = relationship("Dataset", back_populates="evaluations")
    results = relationship("EvaluationResult", back_populates="evaluation_run", cascade="all, delete-orphan")

class EvaluationResult(BaseModel):
    __tablename__ = "evaluation_results"
    
    evaluation_run_id = Column(String, ForeignKey("evaluation_runs.id"))
    sample_id = Column(String, ForeignKey("dataset_samples.id"))
    investigation_id = Column(String, ForeignKey("investigations.id"), nullable=True)
    
    predicted_label = Column(String, nullable=True) # Mapped from Risk Score
    status = Column(String, default="PENDING")
    error_message = Column(String, nullable=True)
    
    # Latency Tracking
    total_latency = Column(Float, default=0.0)
    agent_latencies = Column(JSON, default=dict) # e.g. {"url_intelligence": 1.2}
    
    evaluation_run = relationship("EvaluationRun", back_populates="results")
    sample = relationship("DatasetSample", back_populates="evaluation_results")
