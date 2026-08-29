from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from .qr_processor import QRCodeProcessor
from ..schemas.agent_io import AgentResult
from ..models.agent import AgentRun

class QRAgent(BaseAgent):
    agent_name = "qr_analysis"
    agent_version = "2.0.0"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        # Delegate directly to the real QRCodeProcessor
        return await QRCodeProcessor._execute(investigation_id, session, run)
