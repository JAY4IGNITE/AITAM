from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun

class SMSIntelligenceAgent(BaseAgent):
    agent_name = "sms_intelligence"
    agent_version = "1.0.0"
    capabilities = ["smishing_detection", "otp_fraud_detection"]
        
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv: 
            raise ValueError("Investigation not found")
            
        content = inv.normalized_input or inv.target
        findings = []
        
        content_lower = content.lower()
        if "suspended" in content_lower or "verify" in content_lower:
            findings.append({"title": "Account Suspension Threat", "category": "smishing"})
            
        if "package" in content_lower or "delivery" in content_lower:
            findings.append({"title": "Delivery Scam", "category": "smishing"})
            
        if "otp" in content_lower or "code" in content_lower:
            findings.append({"title": "OTP Request", "category": "credential_harvesting"})
            
        return AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="COMPLETED",
            execution_time=0.0,
            findings=findings,
            evidence=[{"text": content}],
            confidence=0.95
        )
