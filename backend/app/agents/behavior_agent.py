from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .base import BaseAgent
from ..models.agent import AgentRun, SandboxSession
from ..models.investigation import Investigation
from ..models.finding import Finding
from ..schemas.agent_io import AgentResult
import json

class BehaviorAnalysisAgent(BaseAgent):
    agent_name = "behavior_analysis"
    
    @classmethod
    async def _execute(cls, investigation_id: str, session: AsyncSession, run: AgentRun):
        # Retrieve the completed SandboxSession
        result = await session.execute(
            select(SandboxSession).where(SandboxSession.investigation_id == investigation_id).order_by(SandboxSession.start_time.desc())
        )
        sb_session = result.scalars().first()
        
        if not sb_session or not sb_session.events:
            return AgentResult(
                agent_name=cls.agent_name, agent_version="1.0.0", status="COMPLETED", execution_time=0.0,
                confidence=1.0, findings=[], evidence=[], metadata={"status": "No events found"}
            )
            
        events = sb_session.events
        findings = []
        evidence = []
        
        # Analyze Events
        redirects = [e for e in events if e["event_type"] == "REDIRECT"]
        forms = [e for e in events if e["event_type"] == "FORM_DETECTED"]
        passwords = [e for e in events if e["event_type"] == "PASSWORD_FIELD_DETECTED"]
        downloads = [e for e in events if e["event_type"] == "DOWNLOAD_DETECTED"]
        
        # 1. Multiple Redirects
        if len(redirects) > 2:
            findings.append({"title": "Multiple Redirects Detected", "severity": "medium", "category": "evasion", "contribution": 15})
            evidence.append({"type": "redirect_count", "fact": f"{len(redirects)} redirects occurred"})
            
        # 2. Credential Collection via External Submission
        if passwords:
            external_forms = [f for f in forms if f["metadata"].get("external") is True]
            if external_forms:
                findings.append({"title": "External Credential Submission", "severity": "critical", "category": "credential_harvesting", "contribution": 45})
                evidence.append({"type": "external_form_action", "fact": f"Password field submits to: {external_forms[0]['metadata'].get('action')}"})
            else:
                findings.append({"title": "Credential Collection Form", "severity": "high", "category": "credential_harvesting", "contribution": 30})
                evidence.append({"type": "password_field", "fact": "Password input detected in sandbox DOM"})
                
        # 3. Suspicious Download
        if downloads:
            findings.append({"title": "Suspicious Auto-Download", "severity": "high", "category": "malware_delivery", "contribution": 40})
            evidence.append({"type": "download_triggered", "fact": f"File: {downloads[0]['metadata'].get('filename')}"})
            
        # Persist findings to DB so RiskEngine sees them
        db_findings = []
        for f in findings:
            db_findings.append(Finding(
                investigation_id=investigation_id,
                agent=cls.agent_name,
                category=f["category"],
                title=f["title"],
                description=f.get("description", "Detected dynamically via Sandbox"),
                severity=f["severity"],
                confidence=0.95,
                risk_contribution=f["contribution"]
            ))
            
        if db_findings:
            session.add_all(db_findings)
            await session.commit()
            
        return AgentResult(
            agent_name=cls.agent_name,
            agent_version="1.0.0",
            status="COMPLETED",
            execution_time=0.0,
            confidence=0.95,
            findings=findings,
            evidence=evidence,
            metadata={"processed_events": len(events)}
        )
