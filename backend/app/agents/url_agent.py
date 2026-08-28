from sqlalchemy.ext.asyncio import AsyncSession
from urllib.parse import urlparse
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal

class URLIntelligenceAgent(BaseAgent):
    agent_name = "url_intelligence"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        if inv.input_type.value != "URL" and inv.input_type.value != "WEBPAGE":
            run.outputs = {"message": "Not a URL"}
            run.confidence = 1.0
            return
            
        url = inv.target
        parsed = urlparse(url)
        
        # Very naive heuristic for demo purposes
        risk_score = 0
        signals = []
        
        if parsed.scheme != "https":
            risk_score += 30
            signals.append(Signal(type="no_https", severity="medium", evidence="URL does not use HTTPS"))
            
        # Example typosquatting check
        suspicious_keywords = ["login", "verify", "secure", "account", "update", "banking"]
        for kw in suspicious_keywords:
            if kw in parsed.netloc or kw in parsed.path:
                risk_score += 40
                signals.append(Signal(type="suspicious_keyword", severity="high", evidence=f"Suspicious keyword '{kw}' found in URL"))
                
        # Length check
        if len(url) > 100:
            risk_score += 10
            signals.append(Signal(type="long_url", severity="low", evidence="URL length is unusually long"))
            
        output = AgentOutput(
            agent_name=cls.agent_name,
            risk_score=risk_score,
            confidence=0.90,
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
