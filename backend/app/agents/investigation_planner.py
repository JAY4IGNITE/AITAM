from sqlalchemy.ext.asyncio import AsyncSession
from ..models.investigation import Investigation, InputType
from ..models.autonomous import InvestigationPlan
from ..models.agent import AgentRun
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
import asyncio

class InvestigationPlannerAgent(BaseAgent):
    agent_name = "investigation_planner"
    agent_version = "1.0.0"
    capabilities = ["dynamic_routing"]

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
        from sqlalchemy.future import select
        from ..models.autonomous import TriageResult
        
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")
            
        triage_res = await session.execute(select(TriageResult).filter_by(investigation_id=investigation_id))
        triage = triage_res.scalar_one_or_none()
        
        priority = triage.priority if triage else "P3_MEDIUM"
        
        text = (inv.normalized_input or inv.target).lower()
        
        await asyncio.sleep(0.5) # Simulate LLM generation time
        
        depth = "LEVEL_1"
        planned_tasks = []
        
        if priority == "P4_LOW":
            depth = "LEVEL_0"
            planned_tasks = []
            reason = "Basic validation only due to low priority."
        elif priority == "P3_MEDIUM":
            depth = "LEVEL_1"
            planned_tasks = ["ContentIntelligenceAgent", "URLIntelligenceAgent", "ThreatIntelligenceAgent"]
            reason = "Standard baseline agents selected for medium priority."
        elif priority == "P2_HIGH":
            depth = "LEVEL_2"
            planned_tasks = ["ContentIntelligenceAgent", "URLIntelligenceAgent", "ThreatIntelligenceAgent", "PhishingDetectionAgent", "BrandImpersonationAgent"]
            reason = "Deep multi-agent analysis required for high priority."
        else: # P1_CRITICAL
            depth = "LEVEL_3"
            planned_tasks = ["ContentIntelligenceAgent", "URLIntelligenceAgent", "ThreatIntelligenceAgent", "PhishingDetectionAgent", "BrandImpersonationAgent", "SANDBOX_ANALYSIS"]
            reason = "Maximum depth analysis including Sandbox requested for critical priority."
            
        if inv.input_type == InputType.EMAIL and depth != "LEVEL_0":
            planned_tasks.append("EmailIntelligenceAgent")
        elif inv.input_type == InputType.SMS and depth != "LEVEL_0":
            planned_tasks.append("SMSIntelligenceAgent")
        elif inv.input_type == InputType.SOCIAL and depth != "LEVEL_0":
            planned_tasks.append("SocialMessageIntelligenceAgent")
            
        # Deduplicate
        planned_tasks = list(set(planned_tasks))
            
        plan = InvestigationPlan(
            investigation_id=investigation_id,
            priority=priority,
            depth=depth,
            planned_agents=planned_tasks,
            reason=reason,
            status="ACTIVE"
        )
        session.add(plan)
        
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.5,
            findings=[],
            evidence=[{"planned_agents": planned_tasks, "depth": depth, "reason": reason}], 
            confidence=0.95
        )
