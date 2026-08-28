from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal

class ThreatIntelligenceAgent(BaseAgent):
    agent_name = "threat_intel"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        
        target = inv.target
        # MOCK IMPLEMENTATION
        # In a real scenario, this would call VirusTotal, URLhaus, etc.
        # But we must not invent evidence and the backend must remain functional without APIs.
        
        # We will mock a safe response
        signals = []
        risk_score = 0.0
        
        # For demonstration purposes, if the URL contains "malware" we flag it
        if "malware" in target.lower():
            signals.append(Signal(
                type="malicious_reputation",
                severity="critical",
                evidence="Mock threat intel provider flagged domain as malicious"
            ))
            risk_score = 90.0
            
        elif "phishing" in target.lower():
            signals.append(Signal(
                type="phishing_reputation",
                severity="high",
                evidence="Mock threat intel provider flagged domain for phishing"
            ))
            risk_score = 80.0
            
        output = AgentOutput(
            agent_name=cls.agent_name,
            risk_score=risk_score,
            confidence=0.95 if risk_score > 0 else 0.5,
            signals=signals
        )
        
        run.outputs = output.dict()
        run.confidence = output.confidence
        
        # Save evidence
        for sig in signals:
            ev = Evidence(
                investigation_id=investigation_id,
                agent_name=cls.agent_name,
                evidence_type=sig.type,
                severity=sig.severity,
                observed_fact=sig.evidence,
                confidence=output.confidence
            )
            session.add(ev)
