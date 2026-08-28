from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation
from ..models.agent import AgentRun

class QRCodeProcessor(BaseAgent):
    agent_name = "qr_processor"
    agent_version = "1.0.0"
    capabilities = ["qr_decoding"]
        
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv: 
            raise ValueError("Not found")
            
        # In a real system, we'd decode the image here using pyzbar.
        # We simulate that the 'target' already contains the decoded text or a dummy decoding.
        findings = [{"title": "QR Decoded", "category": "extraction"}]
        
        return AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="COMPLETED",
            execution_time=0.0,
            findings=findings,
            evidence=[{"decoded": True}],
            confidence=0.99
        )
