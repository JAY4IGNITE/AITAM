from sqlalchemy.ext.asyncio import AsyncSession
from ..models.investigation import Investigation
from ..models.autonomous import TriageResult
from ..models.agent import AgentRun
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
import asyncio

class TriageAgent(BaseAgent):
    agent_name = "triage_agent"
    agent_version = "1.0.0"
    capabilities = ["priority_evaluation"]

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
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")
            
        text = (inv.normalized_input or inv.target).lower()
        
        # Simulated LLM decision logic for Priority
        await asyncio.sleep(0.5) # Simulate LLM generation time
        
        priority = "HIGH"
        reason = "Input requires deep investigation due to unknown artifacts."
        
        if "spam" in text or "unsubscribe" in text or "newsletter" in text:
            priority = "LOW"
            reason = "Likely promotional spam or newsletter. Does not warrant heavy multi-agent analysis."
        elif "safe" in text and "clean" in text:
            priority = "LOW"
            reason = "Input is explicitly known safe."
        elif "malicious" in text or "urgent" in text or "login" in text:
            priority = "HIGH"
            reason = "High urgency or credential harvesting keywords detected."
            
        triage = TriageResult(
            investigation_id=investigation_id,
            priority=priority,
            reason=reason
        )
        session.add(triage)
        
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.5,
            findings=[],
            evidence=[{"priority": priority, "reason": reason}], 
            confidence=0.9
        )
