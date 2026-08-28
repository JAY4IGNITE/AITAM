from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal

class QRAgent(BaseAgent):
    agent_name = "qr_analysis"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        
        if inv.input_type.value != "QR":
            run.outputs = {"message": "QR analysis skipped for non-QR inputs."}
            run.confidence = 1.0
            return
            
        # MOCK IMPLEMENTATION
        # Normally this would read an image from storage, use pyzbar to decode,
        # and then parse the URL payload.
        # Since we are keeping it deterministic and mocked without real file upload yet:
        
        target_payload = inv.target # Assuming the target is the decoded text or a base64 string
        
        signals = []
        risk_score = 0.0
        
        if "http" in target_payload:
            signals.append(Signal(
                type="qr_url_payload",
                severity="low",
                evidence="QR code contains a URL payload. Forwarding to URL analysis."
            ))
            # In a real system, the orchestrator would see this and trigger URL analysis
            
        output = AgentOutput(
            agent_name=cls.agent_name,
            risk_score=risk_score,
            confidence=0.90,
            signals=signals
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
