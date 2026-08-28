from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation

class SocialMessageIntelligenceAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "social_intelligence"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def capabilities(self) -> list[str]:
        return ["social_scam_detection"]
        
    async def _execute(self, investigation_id: str, session: AsyncSession) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv: return self.build_error_result("Not found")
            
        content = (inv.normalized_input or inv.target).lower()
        findings = []
        
        if "giveaway" in content or "crypto" in content:
            findings.append({"title": "Investment/Giveaway Scam", "category": "social_scam"})
            
        if "violated policy" in content:
            findings.append({"title": "Policy Violation Threat", "category": "social_engineering"})
            
        return self.build_success_result(findings=findings, evidence={"platform": "social"}, confidence=0.85)
