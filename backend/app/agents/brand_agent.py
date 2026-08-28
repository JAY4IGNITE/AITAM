import re
from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult

class BrandImpersonationAgent(BaseAgent):
    agent_name = "brand_impersonation"
    agent_version = "1.0.0"
    capabilities = ["brand_detection", "typosquatting"]

    KNOWN_BRANDS = {
        "paypal": ["paypal", "pay-pal", "paypai"],
        "microsoft": ["microsoft", "micro-soft", "microsft"],
        "apple": ["apple", "appie"],
        "amazon": ["amazon", "amazn"],
        "google": ["google", "gogle", "googIe"],
        "chase": ["chase", "chasebank"],
        "bank of america": ["bofa", "bankofamerica"]
    }

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv.normalized_input:
            return AgentResult(agent_name=cls.agent_name, agent_version=cls.agent_version, status="SKIPPED", execution_time=0.0)
            
        hostname = urlparse(inv.normalized_input).hostname or ""
        
        findings = []
        evidence = []
        
        for brand, variations in cls.KNOWN_BRANDS.items():
            for var in variations:
                if var in hostname:
                    # Ignore if the domain is exactly the brand domain (e.g. paypal.com)
                    if hostname == f"{brand}.com":
                        continue
                        
                    f = Finding(
                        investigation_id=investigation_id, agent=cls.agent_name, category="impersonation",
                        title="Possible brand impersonation", 
                        description=f"Hostname '{hostname}' attempts to impersonate {brand.title()}.",
                        severity="high", confidence=0.87, risk_contribution=35
                    )
                    findings.append(f)
                    evidence.append({"type": "BRAND", "fact": f"Matched variation '{var}' for brand '{brand}'"})
                    break # Don't double count same brand

        session.add_all(findings)
        
        # Save legacy evidence
        for ev in evidence:
            session.add(Evidence(
                investigation_id=investigation_id, agent_name=cls.agent_name,
                evidence_type=ev["type"], severity="high", observed_fact=ev["fact"], confidence=0.87
            ))
            
        return AgentResult(
            agent_name=cls.agent_name, agent_version=cls.agent_version, status="RUNNING", execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence, confidence=0.87
        )
