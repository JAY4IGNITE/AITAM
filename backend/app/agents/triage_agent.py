from sqlalchemy.ext.asyncio import AsyncSession
from ..models.investigation import Investigation
from ..models.autonomous import TriageResult
from ..models.agent import AgentRun, Evidence
from .base import BaseAgent
from ..schemas.agent_io import AgentResult
import asyncio

class TriageAgent(BaseAgent):
    agent_name = "triage_agent"
    agent_version = "2.0.0"
    capabilities = ["priority_evaluation", "threat_triage"]

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
                errors=str(e)
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
        
        priority = "P2_HIGH"
        reasons = ["General input requires thorough multi-agent examination."]
        
        # High-risk heuristics
        critical_terms = ["malicious", "urgent", "login", "password", "crypto", "verify", "suspended", "wire transfer", "seed phrase", "giveaway"]
        low_terms = ["newsletter", "unsubscribe", "weekly digest", "privacy policy"]

        if any(term in text for term in critical_terms):
            priority = "P1_CRITICAL"
            reasons = [
                "Critical threat indicators or credential harvesting lures detected.",
                "Elevated to maximum triage priority for full multi-agent & sandbox detonation."
            ]
        elif any(term in text for term in low_terms) and not any(term in text for term in critical_terms):
            priority = "P4_LOW"
            reasons = ["Likely benign administrative / promotional communication."]
        else:
            priority = "P2_HIGH"
            reasons = ["Input contains active link or unstructured text requiring standard intelligence correlation."]
            
        triage = TriageResult(
            investigation_id=investigation_id,
            priority=priority,
            reasons=reasons,
            confidence=0.95
        )
        session.add(triage)
        
        # Log evidence
        session.add(Evidence(
            investigation_id=investigation_id,
            agent_name=cls.agent_name,
            evidence_type="TRIAGE_ASSESSMENT",
            severity="high" if priority in ["P1_CRITICAL", "P2_HIGH"] else "low",
            observed_fact=f"Triage assigned {priority}: {'; '.join(reasons)}",
            confidence=0.95
        ))
        
        return AgentResult(
            agent_name=cls.agent_name, 
            agent_version=cls.agent_version, 
            status="COMPLETED", 
            execution_time=0.1,
            findings=[],
            evidence=[{"priority": priority, "reasons": reasons}], 
            confidence=0.95
        )
