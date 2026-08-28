from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation

class SMSIntelligenceAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "sms_intelligence"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def capabilities(self) -> list[str]:
        return ["smishing_detection", "otp_fraud_detection"]
        
    async def _execute(self, investigation_id: str, session: AsyncSession) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv: return self.build_error_result("Investigation not found")
            
        content = inv.normalized_input or inv.target
        findings = []
        
        content_lower = content.lower()
        if "suspended" in content_lower or "verify" in content_lower:
            findings.append({"title": "Account Suspension Threat", "category": "smishing"})
            
        if "package" in content_lower or "delivery" in content_lower:
            findings.append({"title": "Delivery Scam", "category": "smishing"})
            
        if "otp" in content_lower or "code" in content_lower:
            findings.append({"title": "OTP Request", "category": "credential_harvesting"})
            
        return self.build_success_result(findings=findings, evidence={"text": content}, confidence=0.95)
