import json
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentResult
from ..engine.sandbox_controller import SandboxController

class SandboxAgent(BaseAgent):
    agent_name = "sandbox_execution"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        
        if inv.input_type.value not in ["URL", "WEBPAGE"]:
            return AgentResult(
                agent_name=cls.agent_name,
                agent_version="1.0.0",
                status="COMPLETED",
                execution_time=0.0,
                confidence=1.0,
                findings=[],
                evidence=[],
                metadata={"message": "Sandbox requires a URL."}
            )
            
        # Dispatch to SandboxController
        result = await SandboxController.run_sandbox(investigation_id, inv.target, session)
        
        if result.get("status") == "FAILED":
            raise Exception(result.get("error", "Sandbox execution failed"))
            
        events = result.get("events", [])
        
        # We don't generate Findings here. The BehaviorAnalysisAgent will consume the events.
        return AgentResult(
            agent_name=cls.agent_name,
            agent_version="1.0.0",
            status="COMPLETED",
            execution_time=0.0,
            confidence=1.0,
            findings=[],
            evidence=[{"type": "sandbox_event_count", "fact": str(len(events))}],
            metadata={"event_count": len(events), "status": result.get("status")}
        )
