import json
from celery import Celery
import os
from sqlalchemy.ext.asyncio import AsyncSession
from .base import BaseAgent
from ..models.agent import AgentRun, Evidence, SandboxSession
from ..models.investigation import Investigation
from ..schemas.agent_io import AgentOutput, Signal

# Initialize Celery client (must match sandbox worker settings)
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
celery_client = Celery("threatlens_sandbox", broker=redis_url, backend=redis_url)

class SandboxAgent(BaseAgent):
    agent_name = "sandbox_execution"

    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        inv = await session.get(Investigation, investigation_id)
        
        if inv.input_type.value not in ["URL", "WEBPAGE"]:
            run.outputs = {"message": "Sandbox requires a URL."}
            run.confidence = 1.0
            return
            
        target_url = inv.target
        
        # Dispatch the task to Redis for the Sandbox container to pick up.
        # We wait for the result here, but in a true event-driven system this would be fully async.
        # For simplicity in this hackathon, we'll block the orchestrator briefly (max 20 seconds).
        async_result = celery_client.send_task("analyze_url", args=[investigation_id, target_url])
        
        try:
            # Wait for sandbox to finish (timeout after 20s to prevent hanging)
            result = async_result.get(timeout=20.0)
            
            if result.get("status") == "failed":
                raise Exception(result.get("error", "Sandbox execution failed"))
                
            # Process Sandbox results
            signals = []
            risk_score = 0.0
            
            # Save the SandboxSession record to DB
            sb_session = SandboxSession(
                investigation_id=investigation_id,
                url_visited=target_url,
                screenshot_base64=result.get("screenshot_base64"),
                dom_snapshot="DOM analysis complete",
                network_logs=json.dumps(result.get("redirect_chain", [])),
                detected_forms=result.get("has_login_form", False)
            )
            session.add(sb_session)
            
            # Convert sandbox findings into standard Signals
            for sig in result.get("signals", []):
                risk_score += 40 if sig["severity"] == "high" else (20 if sig["severity"] == "medium" else 5)
                signals.append(Signal(
                    type=sig["type"],
                    severity=sig["severity"],
                    evidence=sig["evidence"]
                ))
                
            output = AgentOutput(
                agent_name=cls.agent_name,
                risk_score=min(100.0, risk_score),
                confidence=0.95,
                signals=signals
            )
                
            run.outputs = output.dict()
            run.confidence = output.confidence
            
            # Save evidence
            for sig in signals:
                ev = Evidence(
                    investigation_id=investigation_id,
                    agent_name=cls.agent_name,
                    evidence_type=sig.type,
                    severity=sig.severity,
                    observed_fact=sig.evidence,
                    confidence=output.confidence
                )
                session.add(ev)
                
        except Exception as e:
            run.outputs = {"error": str(e)}
            run.confidence = 0.0
            raise e
