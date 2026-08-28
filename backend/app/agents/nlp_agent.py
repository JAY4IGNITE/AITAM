from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal

class NLPAnalysisAgent(BaseAgent):
    agent_name = "nlp_analysis"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        
        if inv.input_type.value not in ["EMAIL", "SMS", "SOCIAL"]:
            run.outputs = {"message": "NLP analysis skipped for this input type."}
            run.confidence = 1.0
            return
            
        target = inv.target.lower()
        signals = []
        risk_score = 0.0
        
        # MOCK IMPLEMENTATION (Simulates an LLM abstraction)
        # Without an API key, we fall back to deterministic keyword analysis
        urgency_keywords = ["urgent", "immediate", "suspension", "within 24 hours"]
        financial_keywords = ["payment", "invoice", "refund", "billing"]
        credential_keywords = ["password", "login", "verify your account", "otp"]
        
        has_urgency = any(kw in target for kw in urgency_keywords)
        has_financial = any(kw in target for kw in financial_keywords)
        has_credential = any(kw in target for kw in credential_keywords)
        
        if has_urgency:
            risk_score += 30
            signals.append(Signal(
                type="urgency_pressure",
                severity="medium",
                evidence="High urgency language detected"
            ))
            
        if has_credential:
            risk_score += 40
            signals.append(Signal(
                type="credential_request",
                severity="high",
                evidence="Message requests credential or account verification"
            ))
            
        if has_financial:
            risk_score += 20
            signals.append(Signal(
                type="financial_lure",
                severity="medium",
                evidence="Financial keywords detected"
            ))
            
        output = AgentOutput(
            agent_name=cls.agent_name,
            risk_score=min(100.0, risk_score),
            confidence=0.85,
            signals=signals,
            raw_data={"urgency": has_urgency, "credential": has_credential, "financial": has_financial}
        )
        
        run.outputs = output.dict()
        run.confidence = output.confidence
        
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
