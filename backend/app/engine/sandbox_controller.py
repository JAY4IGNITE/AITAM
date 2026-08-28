import json
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from ..models.agent import SandboxSession, SandboxStatus
from ..models.investigation import Investigation
from ..models.event import InvestigationEvent
from ..security.ssrf import is_safe_url
import os
import logging
from celery import Celery

logger = logging.getLogger(__name__)

# Initialize Celery client
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_client = Celery("threatlens_sandbox", broker=redis_url, backend=redis_url)

class SandboxController:
    @staticmethod
    async def run_sandbox(investigation_id: str, target_url: str, session: AsyncSession) -> dict:
        """
        Manages the sandbox lifecycle: SSRF check, DB tracking, Celery dispatch, and event collection.
        """
        # 1. Pre-flight SSRF Validation
        if not is_safe_url(target_url):
            logger.warning(f"Sandbox Controller rejected URL due to SSRF risk: {target_url}")
            return {"error": "SSRF Policy Violation"}
            
        # 2. Create Sandbox Session
        sb_session = SandboxSession(
            investigation_id=investigation_id,
            status=SandboxStatus.QUEUED,
            target_url=target_url,
            timeout=30.0
        )
        session.add(sb_session)
        await session.commit()
        await session.refresh(sb_session)
        
        # 3. Queue Celery Task (Offloaded execution)
        sb_session.status = SandboxStatus.STARTING
        sb_session.start_time = datetime.utcnow()
        await session.commit()
        
        try:
            # We block this thread on Celery async result, wrapped in an asyncio thread to not block the main event loop
            async_result = celery_client.send_task("analyze_url", args=[investigation_id, target_url])
            
            def get_result():
                return async_result.get(timeout=30.0) # Matches SB timeout
                
            result = await asyncio.to_thread(get_result)
            
            if result.get("status") == "failed":
                raise Exception(result.get("error", "Unknown error in Sandbox"))
                
            # 4. Process Results
            sb_session.status = SandboxStatus.COMPLETED
            sb_session.events = result.get("events", [])
            sb_session.screenshots = {"final": result.get("screenshot_base64")}
            sb_session.event_count = len(sb_session.events)
            
            # Save raw events into the unified timeline
            new_events = []
            for ev in sb_session.events:
                new_events.append(InvestigationEvent(
                    investigation_id=investigation_id,
                    event_type=ev["event_type"],
                    source="SandboxWorker",
                    severity=ev.get("severity", "INFO"),
                    metadata_payload=ev.get("metadata", {})
                ))
            if new_events:
                session.add_all(new_events)
                
        except Exception as e:
            sb_session.status = SandboxStatus.FAILED
            sb_session.error = str(e)
            
        finally:
            sb_session.end_time = datetime.utcnow()
            await session.commit()
            
        return {
            "status": sb_session.status.value,
            "events": sb_session.events,
            "error": sb_session.error
        }
