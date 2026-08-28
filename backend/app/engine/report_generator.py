from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from ..models.investigation import Investigation
from ..models.report import Report, AttackStep
from ..models.finding import Finding
from ..models.agent import AgentRun, Evidence, SandboxSession
from ..models.iocs import IOC
import json

class ReportGenerator:
    @staticmethod
    async def generate_report(investigation_id: str, session: AsyncSession) -> dict:
        """
        Compiles the investigation data into a structured report payload.
        """
        inv = await session.get(Investigation, investigation_id, options=[
            selectinload(Investigation.agent_runs),
            selectinload(Investigation.evidence),
            selectinload(Investigation.findings),
            selectinload(Investigation.sandbox_sessions),
        ])
        
        if not inv:
            return {"error": "Investigation not found"}
            
        iocs_res = await session.execute(select(IOC).where(IOC.investigation_id == investigation_id))
        iocs = iocs_res.scalars().all()
        
        # Build Summary
        report_content = {
            "display_id": inv.display_id,
            "target": inv.target,
            "status": inv.status.value,
            "final_risk_score": inv.final_risk_score,
            "classification": inv.classification,
            "completed_at": inv.completed_at.isoformat() if inv.completed_at else None,
            "agents": [{"name": a.agent_name, "status": a.status.value, "duration": a.duration} for a in inv.agent_runs],
            "findings": [{"title": f.title, "severity": f.severity, "risk_contribution": f.risk_contribution} for f in inv.findings],
            "iocs": [{"type": i.ioc_type, "value": i.value} for i in iocs],
        }
        
        # Sandbox artifact
        sandbox_img = None
        if inv.sandbox_sessions:
            sb = inv.sandbox_sessions[-1]
            if sb.screenshots and "final" in sb.screenshots:
                sandbox_img = sb.screenshots["final"]
                
        report_content["sandbox_screenshot"] = sandbox_img
        
        # Save to DB
        report = Report(
            investigation_id=investigation_id,
            report_type="ANALYST",
            content=report_content
        )
        session.add(report)
        
        # Generate generic attack steps
        if inv.final_risk_score and inv.final_risk_score > 50:
            step = AttackStep(
                investigation_id=investigation_id,
                step_order="1",
                description="Initial Access / Phishing Delivery",
                mitre_tactic="TA0001",
                mitre_technique="T1566",
                evidence_ids=[]
            )
            session.add(step)
            
        await session.commit()
        return report_content
