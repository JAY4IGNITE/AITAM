import logging
from sqlalchemy.ext.asyncio import AsyncSession
from ..models.investigation import Investigation
from ..models.alert import Alert, AlertStatus
import asyncio

logger = logging.getLogger(__name__)

class EscalationEngine:
    @staticmethod
    async def evaluate_and_escalate(investigation_id: str, session: AsyncSession) -> bool:
        """
        Evaluates the final risk score of an investigation.
        If it meets the criteria (>= 80 for CRITICAL, >= 60 for HIGH),
        it generates an Alert and simulates an escalation webhook/email.
        """
        inv = await session.get(Investigation, investigation_id)
        if not inv or inv.final_risk_score is None:
            return False
            
        score = inv.final_risk_score
        
        if score >= 80:
            severity = "CRITICAL"
        elif score >= 60:
            severity = "HIGH"
        else:
            return False # No escalation needed
            
        # Create Alert
        title = f"[{severity}] Threat Detected: {inv.target}"
        description = f"Investigation {inv.display_id} concluded with a risk score of {score}. Immediate review required."
        
        alert = Alert(
            investigation_id=investigation_id,
            severity=severity,
            title=title,
            description=description,
            status=AlertStatus.OPEN.value
        )
        session.add(alert)
        await session.commit()
        
        # Simulate webhook/email dispatch
        logger.info(f"ESCALATION TRIGGERED: {title}")
        asyncio.create_task(EscalationEngine._dispatch_webhook(alert))
        
        return True
        
    @staticmethod
    async def _dispatch_webhook(alert: Alert):
        """Simulates sending an external webhook/email to a SOAR/SIEM platform."""
        await asyncio.sleep(1.0)
        logger.info(f"Webhook dispatched successfully for Alert ID: {alert.id}")
