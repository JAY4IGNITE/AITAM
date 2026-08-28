import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import time

from ..models.agent import AgentRun, AgentStatus, Evidence
from ..models.investigation import Investigation

# Configure basic structured logging for agents
logger = logging.getLogger("agent_system")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    formatter = logging.Formatter('{"time": "%(asctime)s", "level": "%(levelname)s", "agent": "%(name)s", "message": %(message)s}')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

class BaseAgent:
    agent_name = "base_agent"
    
    @classmethod
    async def analyze(cls, investigation_id: str, session: AsyncSession):
        start_ts = time.time()
        # Create run record
        run = AgentRun(
            investigation_id=investigation_id,
            agent_name=cls.agent_name,
            status=AgentStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        session.add(run)
        await session.commit()
        
        logger.info(f'{{"investigation_id": "{investigation_id}", "event": "start"}}')
        
        try:
            # Perform logic
            await cls._execute(investigation_id, session, run)
            
            run.status = AgentStatus.COMPLETED
            run.end_time = datetime.utcnow()
            await session.commit()
            
            duration = round(time.time() - start_ts, 2)
            findings_count = len(run.outputs.get("signals", [])) if run.outputs else 0
            logger.info(f'{{"investigation_id": "{investigation_id}", "event": "completed", "duration_sec": {duration}, "findings": {findings_count}}}')
            
        except Exception as e:
            run.status = AgentStatus.FAILED
            run.error_message = str(e)
            run.end_time = datetime.utcnow()
            await session.commit()
            
            duration = round(time.time() - start_ts, 2)
            logger.error(f'{{"investigation_id": "{investigation_id}", "event": "failed", "duration_sec": {duration}, "error": "{str(e)}"}}')
            raise e
            
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        raise NotImplementedError
