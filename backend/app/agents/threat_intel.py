from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse
from typing import Dict, Any, Tuple
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult

class ThreatIntelProvider:
    async def analyze_indicator(self, indicator: str, indicator_type: str) -> Tuple[str, float, str]:
        """Returns (status: malicious/suspicious/clean/unknown, confidence: float, evidence: str)"""
        raise NotImplementedError

class MockThreatIntelProvider(ThreatIntelProvider):
    async def analyze_indicator(self, indicator: str, indicator_type: str) -> Tuple[str, float, str]:
        # Deterministic mock results based on the indicator string
        if "malicious" in indicator or "123.45" in indicator:
            return "malicious", 0.99, "Known malware distribution domain (Mock VT)"
        elif "suspicious" in indicator:
            return "suspicious", 0.75, "Recently registered domain with low reputation"
        else:
            return "clean", 0.95, "No malicious activity observed"

class ThreatIntelligenceAgent(BaseAgent):
    agent_name = "threat_intelligence"
    agent_version = "1.0.0"
    capabilities = ["domain_reputation", "ip_reputation"]
    provider = MockThreatIntelProvider()

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        from ..models.iocs import IOC
        from datetime import datetime
        
        inv = await session.get(Investigation, investigation_id)
        if not inv.normalized_input:
            return AgentResult(agent_name=cls.agent_name, agent_version=cls.agent_version, status="SKIPPED", execution_time=0.0)
            
        hostname = urlparse(inv.normalized_input).hostname or ""
        
        status, conf, evidence_str = await cls.provider.analyze_indicator(hostname, "domain")
        
        findings = []
        evidence = []
        iocs_to_save = []
        
        if status in ["malicious", "suspicious"]:
            severity = "critical" if status == "malicious" else "high"
            contribution = 60 if status == "malicious" else 30
            
            f = Finding(
                investigation_id=investigation_id, agent=cls.agent_name, category="threat_intel",
                title=f"{status.title()} indicator detected", 
                description=f"External threat intelligence marked {hostname} as {status}.",
                severity=severity, confidence=conf, risk_contribution=contribution
            )
            findings.append(f)
            evidence.append({"type": "THREAT_INTEL", "fact": evidence_str})
            
            # Save IOC
            iocs_to_save.append(IOC(
                investigation_id=investigation_id,
                ioc_type="DOMAIN",
                value=hostname,
                source_agent=cls.agent_name,
                confidence=conf,
                first_seen=datetime.utcnow().isoformat(),
                last_seen=datetime.utcnow().isoformat()
            ))
            
            session.add(f)
            session.add_all(iocs_to_save)
            session.add(Evidence(
                investigation_id=investigation_id, agent_name=cls.agent_name,
                evidence_type="THREAT_INTEL", severity=severity, observed_fact=evidence_str, confidence=conf
            ))
            
        return AgentResult(
            agent_name=cls.agent_name, agent_version=cls.agent_version, status="RUNNING", execution_time=0.0,
            findings=[{"title": f.title, "severity": f.severity, "category": f.category} for f in findings],
            evidence=evidence, confidence=conf
        )
