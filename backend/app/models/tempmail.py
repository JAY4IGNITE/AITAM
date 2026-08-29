from sqlalchemy import Column, String, Text, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel

class TempMailInbox(BaseModel):
    __tablename__ = "temp_mail_inboxes"

    inbox_id = Column(String, unique=True, index=True, nullable=False)
    email_address = Column(String, unique=True, index=True, nullable=False)
    domain = Column(String, index=True, nullable=False)
    status = Column(String, default="ACTIVE", index=True)  # ACTIVE, INACTIVE, DELETED
    expires_at = Column(DateTime, nullable=True)

    messages = relationship("TempMailMessage", back_populates="inbox", cascade="all, delete-orphan")

class TempMailMessage(BaseModel):
    __tablename__ = "temp_mail_messages"

    inbox_id = Column(String, ForeignKey("temp_mail_inboxes.inbox_id", ondelete="CASCADE"), index=True, nullable=False)
    provider_message_id = Column(String, unique=True, index=True, nullable=False)
    sender = Column(String, index=True, nullable=True)
    sender_domain = Column(String, index=True, nullable=True)
    recipient = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    text_body = Column(Text, nullable=True)
    html_body = Column(Text, nullable=True)
    raw_eml = Column(Text, nullable=True)
    attachment_metadata = Column(JSON, default=list, nullable=True)
    extracted_urls = Column(JSON, default=list, nullable=True)
    investigation_id = Column(String, ForeignKey("investigations.id", ondelete="SET NULL"), index=True, nullable=True)
    status = Column(String, default="RECEIVED", index=True)  # RECEIVED, INVESTIGATING, COMPLETED, FAILED
    processed_at = Column(DateTime, nullable=True)

    inbox = relationship("TempMailInbox", back_populates="messages")
    investigation = relationship("Investigation")

# Composite Indexes for optimal query performance
Index("idx_tempmail_msg_inbox_recv", TempMailMessage.inbox_id, TempMailMessage.received_at.desc())
Index("idx_tempmail_msg_prov_id", TempMailMessage.provider_message_id)
Index("idx_tempmail_msg_inv_id", TempMailMessage.investigation_id)
