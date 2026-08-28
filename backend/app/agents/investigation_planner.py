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
        inv = await session.get(Investigation, investigation_id)
        if not inv:
            raise ValueError("Investigation not found")
            
        text = (inv.normalized_input or inv.target).lower()
        
        await asyncio.sleep(0.5) # Simulate LLM generation time
        
        # Base agents for almost all types
        planned = ["ContentIntelligenceAgent", "PhishingDetectionAgent"]
        reason = "Standard baseline agents selected."
        
        # Simulated LLM logic:
        if inv.input_type in [InputType.URL, InputType.WEBPAGE]:
            planned.extend(["URLIntelligenceAgent", "ThreatIntelligenceAgent"])
            reason = "Detected URL/Webpage input; scheduling URL analysis and Threat Intelligence."
        elif inv.input_type == InputType.EMAIL:
            planned.extend(["EmailIntelligenceAgent", "URLIntelligenceAgent", "BrandImpersonationAgent", "ThreatIntelligenceAgent"])
            reason = "Detected Email input; scheduling Email headers, Brand impersonation, and Threat Intel."
        elif inv.input_type == InputType.SMS:
            planned.extend(["SMSIntelligenceAgent", "URLIntelligenceAgent", "BrandImpersonationAgent", "ThreatIntelligenceAgent"])
            reason = "Detected SMS smishing context; routing to SMS, Brand, and Threat Intel."
        elif inv.input_type == InputType.SOCIAL:
            planned.extend(["SocialMessageIntelligenceAgent", "URLIntelligenceAgent", "ThreatIntelligenceAgent"])
            reason = "Detected Social media context."
            
        if "crypto" in text or "wallet" in text or "payment" in text:
            if "BrandImpersonationAgent" not in planned:
                planned.append("BrandImpersonationAgent")
            reason += " Added Brand Impersonation due to financial keywords."
            
        plan = InvestigationPlan(
            investigation_id=investigation_id,
            planned_agents=planned,
            reason=reason
        )
        session.add(plan)
        
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.5,
            findings=[],
            evidence=[{"planned_agents": planned, "reason": reason}], 
            confidence=0.95
        )
