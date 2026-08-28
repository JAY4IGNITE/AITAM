from sqlalchemy.orm import declarative_base
from datetime import datetime
from sqlalchemy import Column, DateTime, String
import uuid

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class BaseModel(Base):
    __abstract__ = True
    id = Column(String, primary_key=True, default=generate_uuid)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
