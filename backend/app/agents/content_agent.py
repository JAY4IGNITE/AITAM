import re
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult

class ContentIntelligenceAgent(BaseAgent):
    agent_name = "content_intelligence"
    agent_version = "1.0.0"
    capabilities = ["urgency_detection", "financial_requests", "credential_phishing"]

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        text_content = inv.target.lower()
        
        findings = []
        evidence = []
        
        # 1. Urgency Detection
        urgency_keywords = ["immediate", "urgent", "suspend", "action required", "within 24 hours", "account will be closed"]
        if any(kw in text_content for kw in urgency_keywords):
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="social_engineering",
                title="Urgency-based social engineering", description="The content creates a false sense of urgency.",
                severity="high", confidence=0.9, risk_contribution=25
            )
            findings.append(f)
            evidence.append({"type": "TEXT", "fact": "Found urgency keywords"})
            
        # 2. Credential Requests
        cred_keywords = ["password", "login", "credentials", "auth", "otp", "verify your account"]
        if any(kw in text_content for kw in cred_keywords):
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="credential_harvesting",
                title="Credential Request", description="The content asks for sensitive authentication data.",
                severity="critical", confidence=0.85, risk_contribution=40
            )
            findings.append(f)
            evidence.append({"type": "TEXT", "fact": "Found credential request patterns"})

        # 3. Financial Pressure
        fin_keywords = ["payment", "invoice", "overdue", "billing", "credit card", "transfer"]
        if any(kw in text_content for kw in fin_keywords):
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="financial_fraud",
                title="Financial Request", description="The content is related to money transfers or billing.",
                severity="high", confidence=0.8, risk_contribution=30
            )
            findings.append(f)
            evidence.append({"type": "TEXT", "fact": "Found financial keywords"})

        session.add_all(findings)
        
        # Save legacy evidence
        for ev in evidence:
            session.add(Evidence(
                investigation_id=investigation_id, agent_name=cls.agent_name,
                evidence_type=ev["type"], severity="medium", observed_fact=ev["fact"], confidence=0.9
            ))
            
        return AgentResult(
            agent_name=cls.agent_name, agent_version=cls.agent_version, status="RUNNING", execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence, confidence=0.9
        )
