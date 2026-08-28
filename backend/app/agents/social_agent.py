from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun

class SocialMessageIntelligenceAgent(BaseAgent):
    agent_name = "social_intelligence"
    agent_version = "1.0.0"
    capabilities = ["social_scam_detection"]
        
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv: 
            raise ValueError("Not found")
            
        content = (inv.normalized_input or inv.target).lower()
        findings = []
        
        if "giveaway" in content or "crypto" in content:
            findings.append({"title": "Investment/Giveaway Scam", "category": "social_scam"})
            
        if "violated policy" in content:
            findings.append({"title": "Policy Violation Threat", "category": "social_engineering"})
            
        return AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="COMPLETED",
            execution_time=0.0,
            findings=findings,
            evidence=[{"platform": "social"}],
            confidence=0.85
        )
