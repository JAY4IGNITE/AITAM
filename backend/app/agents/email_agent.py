from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
import re

class EmailIntelligenceAgent(BaseAgent):
    @property
    def name(self) -> str:
        return "email_intelligence"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def capabilities(self) -> list[str]:
        return ["header_analysis", "spf_dkim_check", "impersonation_detection"]
        
    async def _execute(self, investigation_id: str, session: AsyncSession) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            return self.build_error_result("Investigation not found")
            
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
            
        return self.build_success_result(findings=findings, evidence=evidence, confidence=0.9)
