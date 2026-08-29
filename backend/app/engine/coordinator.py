import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import Investigation, InvestigationStatus
from .orchestrator import Orchestrator

class InvestigationCoordinator:
    """
    Manages the autonomous orchestration lifecycle for investigations.
    """
    @classmethod
    async def start_investigation(cls, investigation_id: str):
        await Orchestrator.start_investigation(investigation_id)

    @classmethod
    async def run_loop(cls, investigation_id: str, db: AsyncSession = None):
        await Orchestrator.start_investigation(investigation_id)
