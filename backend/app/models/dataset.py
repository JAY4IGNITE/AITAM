from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from datetime import datetime
from .base import BaseModel
from .investigation import InputType

class Dataset(BaseModel):
    __tablename__ = "datasets"
    
    name = Column(String, index=True)
    source = Column(String, nullable=True)
    license = Column(String, nullable=True)
    data_type = Column(String, nullable=True)
    description = Column(String, nullable=True)
    version = Column(String, nullable=True)
    
    samples = relationship("DatasetSample", back_populates="dataset", cascade="all, delete-orphan")
    evaluations = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")

class LabelType(str, enum.Enum):
    BENIGN = "BENIGN"
    SUSPICIOUS = "SUSPICIOUS"
    PHISHING = "PHISHING"
    MALICIOUS = "MALICIOUS"
    SPAM = "SPAM"

class DatasetSample(BaseModel):
    __tablename__ = "dataset_samples"
    
    dataset_id = Column(String, ForeignKey("datasets.id"))
    input_type = Column(Enum(InputType))
    content = Column(String)
    label = Column(Enum(LabelType))
    source = Column(String, nullable=True)
    metadata_payload = Column(JSON, default=dict)
    expected_category = Column(String, nullable=True) # e.g. 'credential_harvesting'
    
    dataset = relationship("Dataset", back_populates="samples")
    evaluation_results = relationship("EvaluationResult", back_populates="sample", cascade="all, delete-orphan")
