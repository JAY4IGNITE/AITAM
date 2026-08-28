from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.investigation import Investigation
from ..models.autonomous import ResponseAction
from ..models.agent import AgentRun
from ..models.finding import Finding
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
import asyncio

class ResponseAgent(BaseAgent):
    agent_name = "response_agent"
    agent_version = "1.0.0"
    capabilities = ["automated_mitigation"]

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
            
        # Get all findings to make a decision
        res = await session.execute(select(Finding).where(Finding.investigation_id == investigation_id))
        findings = res.scalars().all()
        
        await asyncio.sleep(0.5) # Simulate LLM reasoning
        
        score = inv.final_risk_score or 0
        
        action_type = "REPORT"
        details = "Routine incident report generated for analyst review."
        confidence = 0.8
        
        if score > 80:
            action_type = "BLOCK"
            details = "Critical risk detected. Initiating immediate network/DNS block for associated indicators."
            confidence = 0.99
        elif score > 60:
            action_type = "BLOCK"
            details = "High risk detected. Recommending DNS sinkholing."
            confidence = 0.90
        elif score > 20 and any(f.category == "phishing" for f in findings):
            action_type = "EDUCATE"
            details = "Detected low/medium risk phishing attempt. Deploying targeted 'Why this was blocked' training to the recipient."
            confidence = 0.85
        elif score <= 20:
            action_type = "REPORT"
            details = "Low risk or clean. Logged for audit purposes."
            confidence = 0.95
            
        action = ResponseAction(
            investigation_id=investigation_id,
            action_type=action_type,
            details=details,
            confidence=confidence
        )
        session.add(action)
        
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.5,
            findings=[],
            evidence=[{"action": action_type, "details": details}], 
            confidence=confidence
        )
