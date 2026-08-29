import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from ..database.connection import get_db
from ..models.tempmail import TempMailInbox, TempMailMessage
from ..models.investigation import Investigation
from ..schemas.tempmail import (
    TempMailInboxCreate, TempMailInboxResponse, TempMailMessageSummary,
    TempMailMessageDetail, TempMailPollResponse, TempMailHealthStatus
)
from ..engine.tempmail import tempmail_client
from ..engine.tempmail_ingestion import TempMailIngestionService

router = APIRouter()

@router.post("/inbox", response_model=TempMailInboxResponse)
async def create_temporary_inbox(
    req: TempMailInboxCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Provisions a new real temporary inbox via TempMail.so API.
    Saves inbox record in PostgreSQL and prepares it for automated live threat ingestion.
    """
    inbox_data = await tempmail_client.create_inbox(prefix=req.prefix, domain=req.domain)
    
    inbox = TempMailInbox(
        inbox_id=inbox_data["inbox_id"],
        email_address=inbox_data["email_address"],
        domain=inbox_data["domain"],
        status="ACTIVE"
    )
    db.add(inbox)
    await db.commit()
    await db.refresh(inbox)

    return TempMailInboxResponse(
        id=inbox.id,
        inbox_id=inbox.inbox_id,
        email_address=inbox.email_address,
        domain=inbox.domain,
        status=inbox.status,
        created_at=inbox.created_at,
        updated_at=inbox.updated_at,
        message_count=0
    )

@router.get("/inboxes", response_model=List[TempMailInboxResponse])
async def list_temporary_inboxes(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Lists all registered temporary inboxes with live message counts."""
    query = select(TempMailInbox).order_by(desc(TempMailInbox.created_at))
    if status:
        query = query.where(TempMailInbox.status == status.upper())

    result = await db.execute(query)
    inboxes = result.scalars().all()

    out = []
    for inbox in inboxes:
        msg_count = await db.scalar(
            select(func.count(TempMailMessage.id)).where(TempMailMessage.inbox_id == inbox.inbox_id)
        ) or 0
        out.append(TempMailInboxResponse(
            id=inbox.id,
            inbox_id=inbox.inbox_id,
            email_address=inbox.email_address,
            domain=inbox.domain,
            status=inbox.status,
            created_at=inbox.created_at,
            updated_at=inbox.updated_at,
            message_count=msg_count
        ))
    return out

@router.get("/inbox/{inbox_id}/messages", response_model=List[TempMailMessageSummary])
async def list_inbox_messages(
    inbox_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Lists all messages received in a temporary inbox along with automated threat investigation status.
    """
    query = select(TempMailMessage).where(TempMailMessage.inbox_id == inbox_id).order_by(desc(TempMailMessage.received_at))
    result = await db.execute(query)
    messages = result.scalars().all()

    out = []
    for msg in messages:
        risk_score = None
        risk_level = None
        if msg.investigation_id:
            inv = await db.get(Investigation, msg.investigation_id)
            if inv:
                risk_score = inv.final_risk_score or inv.initial_risk_score
                risk_level = inv.classification

        out.append(TempMailMessageSummary(
            id=msg.id,
            inbox_id=msg.inbox_id,
            provider_message_id=msg.provider_message_id,
            sender=msg.sender,
            sender_domain=msg.sender_domain,
            recipient=msg.recipient,
            subject=msg.subject,
            received_at=msg.received_at,
            status=msg.status,
            investigation_id=msg.investigation_id,
            risk_score=risk_score,
            risk_level=risk_level,
            has_attachments=bool(msg.attachment_metadata and len(msg.attachment_metadata) > 0),
            urls_count=len(msg.extracted_urls or [])
        ))
    return out

@router.post("/inbox/{inbox_id}/sync", response_model=TempMailPollResponse)
async def sync_inbox_emails(
    inbox_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Triggers immediate real-time polling of TempMail.so for incoming emails.
    Automatically extracts URLs, normalizes content, creates investigations, and executes the multi-agent pipeline.
    """
    result = await TempMailIngestionService.poll_inbox(inbox_id, db)
    if "error" in result and result.get("error") == "Inbox not found":
        raise HTTPException(status_code=404, detail="Temporary inbox not found")

    return TempMailPollResponse(
        inbox_id=result["inbox_id"],
        email_address=result["email_address"],
        new_messages_count=result.get("new_messages_count", 0),
        total_messages_count=result.get("total_messages_count", 0),
        investigations_dispatched=result.get("investigations_dispatched", []),
        timestamp=datetime.utcnow()
    )

@router.get("/message/{message_id}", response_model=TempMailMessageDetail)
async def get_message_detail(
    message_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieves full email body, HTML, headers, and linked investigation telemetry."""
    msg = await db.get(TempMailMessage, message_id)
    if not msg:
        # Check by provider_message_id
        res = await db.execute(select(TempMailMessage).where(TempMailMessage.provider_message_id == message_id))
        msg = res.scalar_one_or_none()
        
    if not msg:
        raise HTTPException(status_code=404, detail="Email message not found")

    return TempMailMessageDetail(
        id=msg.id,
        inbox_id=msg.inbox_id,
        provider_message_id=msg.provider_message_id,
        sender=msg.sender,
        sender_domain=msg.sender_domain,
        recipient=msg.recipient,
        subject=msg.subject,
        received_at=msg.received_at,
        text_body=msg.text_body,
        html_body=msg.html_body,
        raw_eml=msg.raw_eml,
        attachment_metadata=msg.attachment_metadata or [],
        extracted_urls=msg.extracted_urls or [],
        investigation_id=msg.investigation_id,
        status=msg.status,
        processed_at=msg.processed_at,
        created_at=msg.created_at
    )

@router.delete("/inbox/{inbox_id}")
async def delete_temporary_inbox(
    inbox_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deletes or deactivates a temporary inbox."""
    inbox = (await db.execute(
        select(TempMailInbox).where(TempMailInbox.inbox_id == inbox_id)
    )).scalar_one_or_none()
    
    if not inbox:
        raise HTTPException(status_code=404, detail="Inbox not found")

    await db.delete(inbox)
    await db.commit()
    return {"status": "DELETED", "inbox_id": inbox_id}

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

class AutoInvestigateRequest(BaseModel):
    email_address: Optional[str] = None
    inbox_id: Optional[str] = None
    timeout_seconds: int = Field(default=120, ge=10, le=600)

class MailboxValidationRequest(BaseModel):
    email_address: str

@router.post("/validate-mailbox")
async def validate_mailbox_endpoint(req: MailboxValidationRequest):
    """Validates disposable mailbox syntax, domain structure, and provider support."""
    return TempMailIngestionService.validate_mailbox(req.email_address)

@router.post("/auto-investigate")
async def start_auto_investigation(
    req: AutoInvestigateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    One-Click Fully Automated Phishing Pipeline:
    1. Validates mailbox and registers in database if new.
    2. Immediately checks for any existing uninvestigated email messages.
    3. If none present, launches background watchdog monitoring mailbox up to timeout window.
    4. Automatically ingests arriving emails, extracts URLs, parses headers, runs multi-agent swarm,
       checks Safe Browsing, calculates risk, and generates forensic threat report.
    """
    email = req.email_address
    inbox_id = req.inbox_id
    
    if not email and not inbox_id:
        raise HTTPException(status_code=400, detail="Either email_address or inbox_id must be provided")

    inbox = None
    if inbox_id:
        inbox = (await db.execute(select(TempMailInbox).where(TempMailInbox.inbox_id == inbox_id))).scalar_one_or_none()
    elif email:
        inbox = (await db.execute(select(TempMailInbox).where(TempMailInbox.email_address == email))).scalar_one_or_none()

    if not inbox and email:
        val = TempMailIngestionService.validate_mailbox(email)
        if not val.get("valid"):
            raise HTTPException(status_code=400, detail=val.get("error", "Invalid mailbox format"))
        
        domain = val["domain"]
        inbox_id = inbox_id or uuid.uuid4().hex[:16]
        inbox = TempMailInbox(
            inbox_id=inbox_id,
            email_address=email.lower().strip(),
            domain=domain,
            status="ACTIVE"
        )
        db.add(inbox)
        await db.commit()
        await db.refresh(inbox)

    if not inbox:
        raise HTTPException(status_code=404, detail="Could not find or provision temporary inbox")

    # 1. Check if email is already waiting in the inbox
    res = await TempMailIngestionService.poll_inbox(inbox.inbox_id, db)
    if res.get("new_messages_count", 0) > 0:
        inv_id = res.get("investigations_dispatched", [None])[0]
        return {
            "status": "EMAIL_RECEIVED",
            "inbox_id": inbox.inbox_id,
            "email_address": inbox.email_address,
            "investigation_id": inv_id,
            "message": "Existing email detected and multi-agent investigation dispatched immediately."
        }

    # 2. Launch background watchdog
    background_tasks.add_task(
        TempMailIngestionService.watch_and_auto_investigate,
        inbox.inbox_id,
        req.timeout_seconds,
        3.0
    )

    return {
        "status": "WAITING_FOR_EMAIL",
        "inbox_id": inbox.inbox_id,
        "email_address": inbox.email_address,
        "timeout_seconds": req.timeout_seconds,
        "message": f"Autonomous watchdog active. Monitoring {inbox.email_address} for incoming phishing email..."
    }

@router.get("/health", response_model=TempMailHealthStatus)
async def get_tempmail_health(
    db: AsyncSession = Depends(get_db)
):
    """Checks live connectivity and active inboxes for TempMail integration."""
    health = await tempmail_client.health_check()
    active_cnt = await db.scalar(
        select(func.count(TempMailInbox.id)).where(TempMailInbox.status == "ACTIVE")
    ) or 0

    return TempMailHealthStatus(
        provider=health["provider"],
        configured=health["configured"],
        status=health["status"],
        active_inboxes_count=active_cnt,
        latency_ms=health.get("latency_ms"),
        last_checked=datetime.utcnow(),
        error=health.get("error")
    )

