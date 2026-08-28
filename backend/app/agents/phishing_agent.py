from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult

class PhishingDetectionAgent(BaseAgent):
    agent_name = "phishing_detection"
    agent_version = "1.0.0"
    capabilities = ["multi_signal_correlation", "phishing_heuristics"]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        # Load all current findings for this investigation
        result = await session.execute(
            select(Finding).where(Finding.investigation_id == investigation_id)
        )
        existing_findings: List[Finding] = result.scalars().all()
        
        has_credential_req = any(f.category == "credential_harvesting" for f in existing_findings)
        has_brand_impersonation = any(f.category == "impersonation" for f in existing_findings)
        has_suspicious_url = any(f.category in ["evasion", "suspicious_infrastructure"] for f in existing_findings)
        has_urgency = any(f.category == "social_engineering" for f in existing_findings)
        
        findings = []
        evidence = []
        
        # Heuristic 1: Classic Phishing (Brand + Credential Request)
        if has_brand_impersonation and has_credential_req:
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="phishing",
                title="Targeted Brand Phishing", 
                description="High confidence phishing: Attempting to harvest credentials while impersonating a known brand.",
                severity="critical", confidence=0.98, risk_contribution=50
            )
            findings.append(f)
            evidence.append({"type": "CORRELATION", "fact": "Brand impersonation combined with credential request"})
            
        # Heuristic 2: Generic Phishing (Suspicious URL + Credential Request)
        elif has_suspicious_url and has_credential_req:
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="phishing",
                title="Generic Credential Phishing", 
                description="Suspicious URL structure combined with a credential request.",
                severity="high", confidence=0.90, risk_contribution=40
            )
            findings.append(f)
            evidence.append({"type": "CORRELATION", "fact": "Suspicious URL combined with credential request"})
            
        # Heuristic 3: Social Engineering Scam (Urgency + Suspicious URL)
        if has_urgency and has_suspicious_url and not has_credential_req:
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="scam",
                title="Urgency-Driven Scam", 
                description="Suspicious URL combined with urgent language, a common social engineering tactic.",
                severity="high", confidence=0.85, risk_contribution=35
            )
            findings.append(f)
            evidence.append({"type": "CORRELATION", "fact": "Urgency combined with suspicious URL"})

        session.add_all(findings)
        
        for ev in evidence:
            session.add(Evidence(
                investigation_id=investigation_id, agent_name=cls.agent_name,
                evidence_type=ev["type"], severity="high", observed_fact=ev["fact"], confidence=0.9
            ))
            
        return AgentResult(
            agent_name=cls.agent_name, agent_version=cls.agent_version, status="RUNNING", execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence, confidence=0.9
        )
