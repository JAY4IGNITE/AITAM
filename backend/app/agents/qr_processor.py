from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
from ..models.investigation import Investigation

class QRCodeProcessor(BaseAgent):
    @property
    def name(self) -> str:
        return "qr_processor"
        
    @property
    def version(self) -> str:
        return "1.0.0"
        
    @property
    def capabilities(self) -> list[str]:
        return ["qr_decoding"]
        
    async def _execute(self, investigation_id: str, session: AsyncSession) -> AgentResult:
        inv = await session.get(Investigation, investigation_id)
        if not inv: return self.build_error_result("Not found")
            
        # In a real system, we'd decode the image here using pyzbar.
        # We simulate that the 'target' already contains the decoded text or a dummy decoding.
        findings = [{"title": "QR Decoded", "category": "extraction"}]
        
        return self.build_success_result(findings=findings, evidence={"decoded": True}, confidence=0.99)
