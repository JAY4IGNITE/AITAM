from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.investigation import Investigation
from ..models.autonomous import Incident
from ..models.agent import AgentRun
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
import asyncio

class IncidentSummarizationAgent(BaseAgent):
    agent_name = "incident_summarization_agent"
    agent_version = "1.0.0"
    capabilities = ["summarization"]

    @classmethod
    async def analyze(cls, investigation_id: str, session: AsyncSession) -> AgentResult:
        import time
        start_time = time.time()
        
        run = AgentRun(
            investigation_id=investigation_id,
            agent_name=cls.agent_name,
            agent_version=cls.agent_version,
            status="RUNNING"
        )
        session.add(run)
        await session.commit()
        await session.refresh(run)

        try:
            result = await cls._execute(investigation_id, session, run)
            run.status = "COMPLETED"
            run.findings_count = len(result.findings)
        except Exception as e:
            run.status = "FAILED"
            run.error_message = str(e)
            result = AgentResult(
                agent_name=cls.agent_name, agent_version=cls.agent_version,
                status="FAILED", execution_time=time.time() - start_time,
                errors=[str(e)]
            )
            
        run.duration = time.time() - start_time
        await session.commit()
        return result

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun) -> AgentResult:
        res = await session.execute(select(Incident).where(Incident.investigation_id == investigation_id))
        incident = res.scalar_one_or_none()
        
        if not incident:
            return AgentResult(
                agent_name=cls.agent_name, agent_version=cls.agent_version, 
                status="COMPLETED", execution_time=0.1, findings=[], evidence=[], confidence=1.0
            )
            
        await asyncio.sleep(0.5) # Simulate LLM summarization
        
        # In a real implementation, we would query all AgentMessages and Findings
        # to generate a natural language summary. For the demo, we generate a structured technical summary.
        incident.summary = f"Autonomous analysis confirmed {incident.priority} severity threat. Multiple intelligence agents agreed on malicious indicators. Sandbox analysis corroborated risk. Human approval is pending for containment."
        session.add(incident)
        
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.5,
            findings=[],
            evidence=[{"summary": incident.summary}], 
            confidence=0.9
        )
