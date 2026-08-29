import asyncio
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import time
from typing import List, Dict, Any

from ..models.agent import AgentRun, AgentStatus, Evidence
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult

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
    agent_version = "1.0.0"
    capabilities: List[str] = []
    
    @classmethod
    async def emit_event(cls, investigation_id: str, event_type: str, status: str, message: str, data: dict = None):
        """Emits a real-time event for this agent to live subscribers."""
        try:
            from ..engine.event_broadcaster import event_broadcaster
            from ..schemas.agent_event import AgentEvent
            
            human_name = cls.agent_name.replace("_", " ").title()
            await event_broadcaster.emit(AgentEvent(
                investigation_id=investigation_id,
                agent_id=cls.agent_name,
                agent_name=human_name,
                event_type=event_type,
                status=status,
                message=message,
                data=data or {}
            ))
        except Exception as e:
            logger.debug(f"Event emit notice: {e}")

    @classmethod
    async def analyze(cls, investigation_id: str, session: AsyncSession) -> AgentResult:
        start_ts = time.time()
        human_name = cls.agent_name.replace("_", " ").title()
        
        # Create run record
        run = AgentRun(
            investigation_id=investigation_id,
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status=AgentStatus.RUNNING,
            start_time=datetime.utcnow()
        )
        session.add(run)
        await session.commit()
        
        await cls.emit_event(
            investigation_id=investigation_id,
            event_type="agent_started",
            status="RUNNING",
            message=f"{human_name} started analysis on artifact.",
            data={"capabilities": cls.capabilities, "version": cls.agent_version}
        )
        
        logger.info(f'{{"investigation_id": "{investigation_id}", "event": "start"}}')
        
        result = AgentResult(
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="RUNNING",
            execution_time=0.0
        )
        
        try:
            # Perform logic
            agent_result = await cls._execute(investigation_id, session, run)
            
            run.status = AgentStatus.COMPLETED if not run.error_message else AgentStatus.FAILED
            run.end_time = datetime.utcnow()
            run.duration = round(time.time() - start_ts, 2)
            
            if agent_result:
                result = agent_result
                
            result.status = run.status.value
            result.execution_time = run.duration
            
            # Persist summary
            run.output_summary = f"Generated {len(result.findings)} findings and {len(result.evidence)} evidence items."
            await session.commit()
            
            await cls.emit_event(
                investigation_id=investigation_id,
                event_type="agent_completed",
                status="COMPLETED",
                message=f"{human_name} completed in {run.duration}s ({len(result.findings)} findings).",
                data={
                    "duration_seconds": run.duration,
                    "findings_count": len(result.findings),
                    "evidence_count": len(result.evidence),
                    "findings_summary": [f.get("title") for f in result.findings if isinstance(f, dict)]
                }
            )
            
            logger.info(f'{{"investigation_id": "{investigation_id}", "event": "completed", "duration_sec": {run.duration}, "findings": {len(result.findings)}}}')
            return result
            
        except Exception as e:
            run.status = AgentStatus.FAILED
            run.error_message = str(e)
            run.end_time = datetime.utcnow()
            run.duration = round(time.time() - start_ts, 2)
            await session.commit()
            
            result.status = "FAILED"
            result.execution_time = run.duration
            result.errors = str(e)
            
            await cls.emit_event(
                investigation_id=investigation_id,
                event_type="agent_failed",
                status="FAILED",
                message=f"{human_name} failed: {str(e)}",
                data={"error": str(e), "duration_seconds": run.duration}
            )
            
            logger.error(f'{{"investigation_id": "{investigation_id}", "event": "failed", "duration_sec": {run.duration}, "error": "{str(e)}"}}')
            return result
            
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        raise NotImplementedError
        
    @classmethod
    async def health_check(cls) -> bool:
        return True
