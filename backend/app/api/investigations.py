from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from ..database.connection import get_db
from ..models import Investigation, InvestigationStatus, Finding, Evidence, InvestigationEvent
from ..schemas import InvestigationCreate
from ..engine.orchestrator import Orchestrator

router = APIRouter()

@router.post("/")
async def create_investigation(
    req: InvestigationCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    import uuid
    from datetime import datetime
    
    display_id = f"INV-{datetime.utcnow().year}-{str(uuid.uuid4())[:6].upper()}"
    
    new_inv = Investigation(
        display_id=display_id,
        input_type=req.input_type,
        target=req.target,
        status=InvestigationStatus.QUEUED,
        current_stage="INITIALIZING"
    )
    
    db.add(new_inv)
    await db.commit()
    await db.refresh(new_inv)
    
    # Log INVESTIGATION_CREATED event
    event = InvestigationEvent(
        investigation_id=new_inv.id,
        event_type="INVESTIGATION_CREATED",
        source="API",
        severity="INFO",
        metadata_payload={"input_type": new_inv.input_type.value, "target": new_inv.target}
    )
    db.add(event)
    await db.commit()
    
    # Start orchestrator in background
    background_tasks.add_task(Orchestrator.start_investigation, new_inv.id)
    
    return {
        "investigation_id": new_inv.id,
        "status": "queued"
    }

@router.get("/{id}")
async def get_investigation(id: str, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Investigation, id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    # Get findings count
    findings_count = await db.scalar(select(func.count(Finding.id)).where(Finding.investigation_id == id))
    
    # Get sandbox sessions count manually to avoid lazy load error
    from ..models.agent import SandboxSession
    sandbox_count = await db.scalar(select(func.count(SandboxSession.id)).where(SandboxSession.investigation_id == id))
    
    return {
        "id": inv.id,
        "display_id": inv.display_id,
        "status": inv.status.value,
        "current_stage": inv.current_stage,
        "risk_score": inv.final_risk_score or inv.initial_risk_score,
        "risk_level": inv.classification,
        "progress": 100 if inv.status in [InvestigationStatus.COMPLETED, InvestigationStatus.FAILED] else 50,
        "findings_count": findings_count or 0,
        "sandbox_status": "COMPLETED" if sandbox_count > 0 else "NOT_REQUIRED",
        "created_at": inv.created_at,
        "updated_at": inv.updated_at,
        "completed_at": inv.completed_at
    }

@router.get("/{id}/findings")
async def get_findings(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Finding).where(Finding.investigation_id == id).order_by(Finding.created_at.desc()))
    return result.scalars().all()

@router.get("/{id}/evidence")
async def get_evidence(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Evidence).where(Evidence.investigation_id == id).order_by(Evidence.created_at.desc()))
    return result.scalars().all()

@router.get("/{id}/timeline")
async def get_timeline(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InvestigationEvent).where(InvestigationEvent.investigation_id == id).order_by(InvestigationEvent.created_at.asc()))
    return result.scalars().all()

@router.get("/{id}/agents")
async def get_investigation_agents(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.agent import AgentRun
    result = await db.execute(
        select(AgentRun).where(AgentRun.investigation_id == id).order_by(AgentRun.start_time)
    )
    runs = result.scalars().all()
    
    agents = []
    for run in runs:
        agents.append({
            "agent_name": run.agent_name,
            "version": run.agent_version,
            "status": run.status.value,
            "duration": run.duration,
            "findings_count": 0,
            "error": run.error_message
        })
        
    return agents

@router.get("/{id}/risk")
async def get_investigation_risk(id: str, db: AsyncSession = Depends(get_db)):
    from ..engine.risk import RiskEngine
    risk_output = await RiskEngine.calculate_risk(id, db)
    return risk_output.dict()

@router.post("/{id}/sandbox")
async def trigger_sandbox(id: str, db: AsyncSession = Depends(get_db)):
    from ..engine.sandbox_controller import SandboxController
    inv = await db.get(Investigation, id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    result = await SandboxController.run_sandbox(id, inv.target, db)
    return result

@router.get("/{id}/sandbox")
async def get_sandbox_session(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.agent import SandboxSession
    result = await db.execute(select(SandboxSession).where(SandboxSession.investigation_id == id).order_by(SandboxSession.start_time.desc()))
    session = result.scalars().first()
    if not session:
        return {"status": "NOT_STARTED"}
    return {
        "status": session.status.value,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "browser": session.browser_type,
        "event_count": session.event_count,
        "error": session.error
    }

@router.get("/{id}/sandbox/events")
async def get_sandbox_events(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.agent import SandboxSession
    result = await db.execute(select(SandboxSession).where(SandboxSession.investigation_id == id).order_by(SandboxSession.start_time.desc()))
    session = result.scalars().first()
    if not session:
        return []
    return session.events or []

@router.get("/{id}/sandbox/artifacts")
async def get_sandbox_artifacts(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.agent import SandboxSession
    result = await db.execute(select(SandboxSession).where(SandboxSession.investigation_id == id).order_by(SandboxSession.start_time.desc()))
    session = result.scalars().first()
    if not session:
        return {}
    return session.screenshots or {}

@router.get("/{id}/behavior")
async def get_behavior(id: str, db: AsyncSession = Depends(get_db)):
    # Returns the specific findings generated by the BehaviorAnalysisAgent
    result = await db.execute(select(Finding).where(Finding.investigation_id == id, Finding.agent == "behavior_analysis"))
    return result.scalars().all()

@router.get("/{id}/report")
async def get_report(id: str, db: AsyncSession = Depends(get_db)):
    from ..engine.report_generator import ReportGenerator
    report = await ReportGenerator.generate_report(id, db)
    return report

@router.get("/reports/alerts")
async def get_active_alerts(db: AsyncSession = Depends(get_db)):
    from ..models.alert import Alert
    result = await db.execute(select(Alert).order_by(Alert.created_at.desc()).limit(20))
    alerts = result.scalars().all()
    return alerts

@router.get("/{id}/graph")
async def get_graph(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.graph import EvidenceNode, EvidenceEdge
    nodes_res = await db.execute(select(EvidenceNode).where(EvidenceNode.investigation_id == id))
    edges_res = await db.execute(select(EvidenceEdge).where(EvidenceEdge.investigation_id == id))
    return {
        "nodes": nodes_res.scalars().all(),
        "edges": edges_res.scalars().all()
    }

@router.get("/{id}/journey")
async def get_journey(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.journey import AttackJourneyStep
    res = await db.execute(select(AttackJourneyStep).where(AttackJourneyStep.investigation_id == id).order_by(AttackJourneyStep.sequence.asc()))
    return res.scalars().all()

@router.get("/{id}/risk/history")
async def get_risk_history(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.journey import RiskAssessment
    res = await db.execute(select(RiskAssessment).where(RiskAssessment.investigation_id == id).order_by(RiskAssessment.created_at.asc()))
    return res.scalars().all()

@router.get("/{id}/explanation")
async def get_explanation(id: str, db: AsyncSession = Depends(get_db)):
    from ..engine.explanation import RiskExplanationService
    return await RiskExplanationService.generate_explanation(id, db)

@router.get("/{id}/indicators")
async def get_investigation_indicators(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.iocs import IOC
    result = await db.execute(select(IOC).filter_by(investigation_id=id))
    iocs = result.scalars().all()
    return [{"type": ioc.ioc_type, "value": ioc.value, "first_seen": ioc.first_seen} for ioc in iocs]

@router.get("/{id}/threat-intelligence")
async def get_investigation_threat_intel(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.iocs import IOC
    from ..engine.threat_intel_provider import registry
    import asyncio
    
    result = await db.execute(select(IOC).filter_by(investigation_id=id))
    iocs = result.scalars().all()
    
    all_results = []
    tasks = []
    for ioc in iocs:
        tasks.append(registry.lookup(ioc.value, ioc.ioc_type.upper()))
        
    if tasks:
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        for res_list in completed:
            if isinstance(res_list, list):
                all_results.extend([r.model_dump(mode='json') for r in res_list])
                
    return all_results

@router.get("/{id}/autonomous")
async def get_investigation_autonomous(id: str, db: AsyncSession = Depends(get_db)):
    from ..models.autonomous import TriageResult, InvestigationPlan, ResponseAction
    
    triage = (await db.execute(select(TriageResult).filter_by(investigation_id=id))).scalar_one_or_none()
    plan = (await db.execute(select(InvestigationPlan).filter_by(investigation_id=id))).scalar_one_or_none()
    response = (await db.execute(select(ResponseAction).filter_by(investigation_id=id))).scalar_one_or_none()
    
    return {
        "triage": {
            "priority": triage.priority,
            "reason": triage.reason
        } if triage else None,
        "plan": {
            "planned_agents": plan.planned_agents,
            "reason": plan.reason
        } if plan else None,
        "response": {
            "action": response.action_type,
            "details": response.details,
            "confidence": response.confidence
        } if response else None
    }

class AnalyzeRequest(BaseModel):
    input_type: str
    content: str

@router.post("/analyze")
async def analyze_input(
    req: AnalyzeRequest,
    background_tasks: BackgroundTasks, 
    db: AsyncSession = Depends(get_db)
):
    from ..models.investigation import InputType, Investigation, InvestigationStatus
    from ..engine.orchestrator import Orchestrator
    try:
        input_type_enum = InputType(req.input_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail="Unsupported input type")
        
    import uuid
    inv = Investigation(
        display_id=f"INV-2026-{uuid.uuid4().hex[:6].upper()}",
        input_type=input_type_enum,
        target=req.content,
        status=InvestigationStatus.QUEUED
    )
    db.add(inv)
    await db.commit()
    await db.refresh(inv)
    
    background_tasks.add_task(Orchestrator.start_investigation, inv.id)
    return {"investigation_id": inv.id, "input_type": inv.input_type.value, "status": inv.status.value}

@router.post("/input/preview")
async def preview_input(req: AnalyzeRequest):
    from ..models.investigation import InputType
    from ..engine.input_processor import UniversalInputProcessor
    try:
        input_type_enum = InputType(req.input_type.upper())
    except ValueError:
        return {"detected_type": "UNKNOWN", "warnings": ["Unsupported input type"]}
        
    threat_obj = UniversalInputProcessor.process_input(input_type_enum, req.content)
    
    return {
        "detected_type": threat_obj.input_type.value,
        "normalized_content": threat_obj.normalized_text,
        "indicators": [i.model_dump() for i in threat_obj.extracted_indicators],
        "warnings": [] if threat_obj.urls else ["No external indicators detected."]
    }
