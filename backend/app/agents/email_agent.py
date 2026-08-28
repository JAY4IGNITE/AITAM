from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun
import re

class EmailIntelligenceAgent(BaseAgent):
    agent_name = "email_intelligence"
    agent_version = "1.0.0"
    capabilities = ["header_analysis", "spf_dkim_check", "impersonation_detection"]
        
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")
            
        content = inv.normalized_input or inv.target
        findings = []
        evidence = {"raw": content[:500]}
        
        # Simulated header analysis
        if "Reply-To:" in content and "From:" in content:
            findings.append({"title": "Reply-To mismatch", "category": "email_spoofing"})
            
        if "invoice" in content.lower() or "billing" in content.lower():
            findings.append({"title": "Financial Request", "category": "social_engineering"})
            
        # Simulated auth failure
        if "SPF: FAIL" in content or "DKIM: FAIL" in content:
            findings.append({"title": "Email Authentication Failed", "category": "spoofing"})
            
        return AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="COMPLETED",
            execution_time=0.0,
            findings=findings,
            evidence=[evidence],
            confidence=0.9
        )
