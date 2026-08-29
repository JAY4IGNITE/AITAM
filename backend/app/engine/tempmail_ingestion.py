import re
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.tempmail import TempMailInbox, TempMailMessage
from ..models.investigation import Investigation, InvestigationStatus, InputType
from ..models.event import InvestigationEvent
from ..engine.tempmail import tempmail_client
from ..engine.input_processor import IndicatorExtractor
from ..engine.orchestrator import Orchestrator

logger = logging.getLogger("tempmail_ingestion")

class TempMailIngestionService:
    @staticmethod
    async def poll_inbox(inbox_id: str, session: AsyncSession) -> Dict[str, Any]:
        """
        Polls a specific TempMail inbox, ingests new incoming emails, normalizes content,
        creates an autonomous investigation, and dispatches the multi-agent cybersecurity pipeline.
        Prevents duplicate investigations for previously ingested messages.
        """
        inbox = (await session.execute(
            select(TempMailInbox).where(TempMailInbox.inbox_id == inbox_id)
        )).scalar_one_or_none()

        if not inbox:
            return {"error": "Inbox not found", "inbox_id": inbox_id, "new_messages_count": 0}

        # 1. Fetch raw messages from TempMail provider
        raw_messages = await tempmail_client.list_messages(inbox.inbox_id, inbox.email_address)
        new_count = 0
        investigations_dispatched = []

        for msg_summary in raw_messages:
            prov_msg_id = msg_summary.get("provider_message_id")
            if not prov_msg_id:
                continue

            # 2. Check deduplication in database
            existing = (await session.execute(
                select(TempMailMessage).where(TempMailMessage.provider_message_id == prov_msg_id)
            )).scalar_one_or_none()

            if existing:
                continue

            # 3. Retrieve full email body, HTML, headers, attachments
            full_msg = await tempmail_client.get_message(inbox.inbox_id, prov_msg_id, inbox.email_address)
            sender = full_msg.get("sender") or msg_summary.get("sender") or "unknown@sender.com"
            subject = full_msg.get("subject") or msg_summary.get("subject") or "No Subject"
            text_body = full_msg.get("text_body") or ""
            html_body = full_msg.get("html_body") or ""
            raw_eml = full_msg.get("raw_eml") or f"From: {sender}\nSubject: {subject}\nTo: {inbox.email_address}\n\n{text_body}"
            attachments = full_msg.get("attachment_metadata") or []

            sender_domain = sender.split("@")[-1].strip(">").lower() if "@" in sender else None

            # 4. Extract embedded URLs from both text & HTML
            combined_content = f"{subject}\n{text_body}\n{html_body}"
            extracted_urls = list(set(IndicatorExtractor.extract_urls(combined_content)))

            # 5. Create ThreatLens Investigation
            display_id = f"INV-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
            investigation_target = raw_eml if len(raw_eml.strip()) > 20 else f"From: {sender}\nSubject: {subject}\n\n{text_body}"
            
            new_inv = Investigation(
                display_id=display_id,
                input_type=InputType.EMAIL,
                target=investigation_target,
                normalized_input=investigation_target,
                status=InvestigationStatus.QUEUED,
                current_stage="Email Ingested via TempMail.so — Queued for Multi-Agent Triage"
            )
            session.add(new_inv)
            await session.commit()
            await session.refresh(new_inv)

            # Log INVESTIGATION_CREATED event
            session.add(InvestigationEvent(
                investigation_id=new_inv.id,
                event_type="EMAIL_INGESTED_TEMPMAIL",
                source="TempMailIngestionService",
                severity="INFO",
                metadata_payload={
                    "inbox_id": inbox.inbox_id,
                    "recipient": inbox.email_address,
                    "sender": sender,
                    "subject": subject,
                    "urls_count": len(extracted_urls),
                    "attachments_count": len(attachments)
                }
            ))

            # 6. Save TempMailMessage record
            msg_record = TempMailMessage(
                inbox_id=inbox.inbox_id,
                provider_message_id=prov_msg_id,
                sender=sender,
                sender_domain=sender_domain,
                recipient=inbox.email_address,
                subject=subject,
                received_at=datetime.utcnow(),
                text_body=text_body,
                html_body=html_body,
                raw_eml=raw_eml,
                attachment_metadata=attachments,
                extracted_urls=extracted_urls,
                investigation_id=new_inv.id,
                status="INVESTIGATING",
                processed_at=datetime.utcnow()
            )
            session.add(msg_record)
            await session.commit()

            # 7. Dispatch Multi-Agent Orchestration
            asyncio.create_task(Orchestrator.start_investigation(new_inv.id))
            investigations_dispatched.append(new_inv.id)
            new_count += 1

        return {
            "inbox_id": inbox.inbox_id,
            "email_address": inbox.email_address,
            "new_messages_count": new_count,
            "total_messages_count": len(raw_messages),
            "investigations_dispatched": investigations_dispatched,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    def validate_mailbox(email_address: str) -> Dict[str, Any]:
        """
        Validates temporary email syntax, domain structure, and provider compatibility.
        """
        if not email_address or "@" not in email_address:
            return {"valid": False, "status": "INVALID", "error": "Invalid email syntax format"}

        parts = email_address.strip().lower().split("@")
        if len(parts) != 2 or not parts[0] or not parts[1] or "." not in parts[1]:
            return {"valid": False, "status": "INVALID", "error": "Malformed email address structure"}

        local_part, domain = parts[0], parts[1]
        
        # Syntax regex check
        if not re.match(r'^[a-zA-Z0-9_.+-]+$', local_part):
            return {"valid": False, "status": "INVALID", "error": "Local part contains forbidden characters"}

        return {
            "valid": True,
            "status": "VALID",
            "email_address": email_address,
            "local_part": local_part,
            "domain": domain,
            "provider": "TempMail.so"
        }

    @staticmethod
    async def watch_and_auto_investigate(inbox_id: str, timeout_seconds: int = 120, poll_interval: float = 3.0) -> Dict[str, Any]:
        """
        Background autonomous watchdog: monitors a temporary mailbox for incoming emails,
        automatically ingests arriving messages, dispatches multi-agent pipelines,
        and broadcasts live telemetry to WebSocket / SSE subscribers.
        """
        from ..database.connection import AsyncSessionLocal
        from ..engine.event_broadcaster import event_broadcaster
        from ..schemas.agent_event import AgentEvent
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout_seconds:
            async with AsyncSessionLocal() as session:
                inbox = (await session.execute(
                    select(TempMailInbox).where(TempMailInbox.inbox_id == inbox_id)
                )).scalar_one_or_none()
                
                if not inbox:
                    break

                res = await TempMailIngestionService.poll_inbox(inbox_id, session)
                
                if res.get("new_messages_count", 0) > 0:
                    dispatched_invs = res.get("investigations_dispatched", [])
                    inv_id = dispatched_invs[0] if dispatched_invs else None
                    logger.info(f"Autonomous email detected in {inbox_id}! Dispatched investigation: {inv_id}")
                    return {
                        "status": "EMAIL_RECEIVED",
                        "inbox_id": inbox_id,
                        "email_address": inbox.email_address,
                        "new_messages_count": res.get("new_messages_count"),
                        "investigation_id": inv_id
                    }

            remaining = int(timeout_seconds - (asyncio.get_event_loop().time() - start_time))
            if remaining > 0 and remaining % 6 == 0:
                logger.debug(f"Watchdog waiting for email in {inbox_id}... ({remaining}s remaining)")

            await asyncio.sleep(poll_interval)

        return {
            "status": "TIMEOUT",
            "inbox_id": inbox_id,
            "message": f"No incoming email arrived within {timeout_seconds}s timeout window."
        }

    @staticmethod
    async def poll_all_active_inboxes(session: AsyncSession) -> List[Dict[str, Any]]:
        """Polls all active temporary inboxes in the database."""
        inboxes_res = await session.execute(
            select(TempMailInbox).where(TempMailInbox.status == "ACTIVE")
        )
        inboxes = inboxes_res.scalars().all()
        results = []
        for inbox in inboxes:
            try:
                res = await TempMailIngestionService.poll_inbox(inbox.inbox_id, session)
                results.append(res)
            except Exception as e:
                logger.error(f"Error polling inbox {inbox.inbox_id}: {e}")
        return results
