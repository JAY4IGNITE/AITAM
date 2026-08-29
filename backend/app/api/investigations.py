import uuid
import os
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, asc, or_

from ..database.connection import get_db
from ..models import (
    Investigation, InvestigationStatus, InputType, Finding, Evidence,
    InvestigationEvent, SandboxSession, IOC
)
from ..models.autonomous import TriageResult, InvestigationPlan, ResponseAction
from ..schemas.investigation import (
    InvestigationCreate, InvestigationResponse, PaginatedInvestigationsResponse,
    QRUploadResponse
)
from ..engine.orchestrator import Orchestrator
from ..engine.risk import RiskEngine
from ..engine.explanation import RiskExplanationService
from ..engine.report_generator import ReportGenerator
from ..engine.sandbox_controller import SandboxController
from ..engine.threat_intel_provider import registry
from ..agents.qr_processor import decode_qr_image

router = APIRouter()

@router.post("/", response_model=dict)
@router.post("/analyze", response_model=dict)
async def create_investigation(
    req: InvestigationCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Creates a new investigation for any universal input type (URL, EMAIL, SMS, QR, WEBPAGE, SOCIAL).
    Enqueues multi-agent triage and investigation pipeline in background.
    """
    display_id = f"INV-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
    
    new_inv = Investigation(
        display_id=display_id,
        input_type=req.input_type,
        target=req.target.strip(),
        status=InvestigationStatus.QUEUED,
        current_stage="Queued for Autonomous Investigation"
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
        metadata_payload={"input_type": new_inv.input_type.value, "target_preview": new_inv.target[:100]}
    )
    db.add(event)
    await db.commit()
    
    # Dispatch Orchestrator
    background_tasks.add_task(Orchestrator.start_investigation, new_inv.id)
    
    return {
        "investigation_id": new_inv.id,
        "display_id": new_inv.display_id,
        "input_type": new_inv.input_type.value,
        "status": new_inv.status.value,
        "message": "Investigation created and queued for multi-agent analysis."
    }

@router.post("/upload-qr", response_model=QRUploadResponse)
async def upload_qr_code(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Secure file upload for QR code analysis.
    Validates MIME type, file size, extracts QR payload, and starts the investigation pipeline.
    """
    # 1. MIME and Extension validation
    allowed_content_types = ["image/png", "image/jpeg", "image/jpg", "image/webp", "image/bmp"]
    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Supported image formats: PNG, JPEG, WEBP, BMP."
        )
        
    ext = file.filename.split(".")[-1].lower() if file.filename and "." in file.filename else "png"
    if ext not in ["png", "jpg", "jpeg", "webp", "bmp"]:
        raise HTTPException(status_code=400, detail="Invalid image file extension.")
        
    # 2. Secure temporary file storage with size check
    temp_dir = os.path.join(os.getcwd(), "scratch_uploads")
    os.makedirs(temp_dir, exist_ok=True)
    temp_filepath = os.path.join(temp_dir, f"qr_{uuid.uuid4().hex}.{ext}")
    
    max_size = 10 * 1024 * 1024  # 10MB
    size = 0
    
    try:
        with open(temp_filepath, "wb") as buffer:
            while chunk := await file.read(1024 * 64):
                size += len(chunk)
                if size > max_size:
                    raise HTTPException(status_code=413, detail="File size exceeds maximum allowed limit of 10MB.")
                buffer.write(chunk)
                
        # 3. Decode QR image
        decoded_payloads = decode_qr_image(temp_filepath)
        if not decoded_payloads:
            # If no barcode found in image
            decoded_payload = "NO_QR_PAYLOAD_DETECTED"
            payload_type = "UNKNOWN"
        else:
            decoded_payload = decoded_payloads[0]
            payload_type = "URL" if decoded_payload.startswith(("http://", "https://")) else "TEXT"
            
        # 4. Create Investigation
        display_id = f"INV-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
        new_inv = Investigation(
            display_id=display_id,
            input_type=InputType.QR,
            target=decoded_payload if decoded_payload != "NO_QR_PAYLOAD_DETECTED" else f"Image Upload: {file.filename}",
            normalized_input=decoded_payload,
            status=InvestigationStatus.QUEUED,
            current_stage="QR Decoded — Enqueueing URL and Threat Intel Pipelines"
        )
        db.add(new_inv)
        await db.commit()
        await db.refresh(new_inv)
        
        # Start pipeline
        background_tasks.add_task(Orchestrator.start_investigation, new_inv.id)
        
        return QRUploadResponse(
            investigation_id=new_inv.id,
            decoded_payload=decoded_payload,
            payload_type=payload_type,
            status=new_inv.status.value
        )
        
    finally:
        # 5. Clean up temporary uploaded file safely
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except Exception:
                pass

@router.get("/", response_model=PaginatedInvestigationsResponse)
async def list_investigations(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    input_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    db: AsyncSession = Depends(get_db)
):
    """
    Paginated investigation history with filtering, sorting, and full-text keyword search.
    """
    query = select(Investigation)
    count_query = select(func.count(Investigation.id))
    
    filters = []
    if input_type:
        try:
            filters.append(Investigation.input_type == InputType(input_type.upper()))
        except ValueError:
            pass
    if status:
        try:
            filters.append(Investigation.status == InvestigationStatus(status.upper()))
        except ValueError:
            pass
    if classification:
        filters.append(Investigation.classification == classification.upper())
    if search:
        search_term = f"%{search.strip()}%"
        filters.append(or_(
            Investigation.target.ilike(search_term),
            Investigation.display_id.ilike(search_term),
            Investigation.classification.ilike(search_term)
        ))
        
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
        
    # Sorting
    sort_col = getattr(Investigation, sort_by, Investigation.created_at)
    if order.lower() == "asc":
        query = query.order_by(asc(sort_col))
    else:
        query = query.order_by(desc(sort_col))
        
    total = await db.scalar(count_query) or 0
    offset = (page - 1) * limit
    result = await db.execute(query.offset(offset).limit(limit))
    items = result.scalars().all()
    
    # Calculate finding counts
    out_items = []
    for item in items:
        f_count = await db.scalar(select(func.count(Finding.id)).where(Finding.investigation_id == item.id))
        sb_count = await db.scalar(select(func.count(SandboxSession.id)).where(SandboxSession.investigation_id == item.id))
        out_items.append(InvestigationResponse(
            id=item.id,
            display_id=item.display_id,
            input_type=item.input_type,
            target=item.target,
            status=item.status,
            current_stage=item.current_stage,
            initial_risk_score=item.initial_risk_score,
            final_risk_score=item.final_risk_score,
            classification=item.classification or "UNKNOWN",
            confidence=item.confidence or 0.95,
            findings_count=f_count or 0,
            sandbox_status="COMPLETED" if (sb_count or 0) > 0 else "NOT_REQUIRED",
            created_at=item.created_at,
            updated_at=item.updated_at,
            completed_at=item.completed_at
        ))
        
    pages = (total + limit - 1) // limit if total > 0 else 1
    return PaginatedInvestigationsResponse(
        items=out_items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )

@router.get("/{id}")
async def get_investigation(id: str, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Investigation, id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
        
    findings_count = await db.scalar(select(func.count(Finding.id)).where(Finding.investigation_id == id))
    sandbox_count = await db.scalar(select(func.count(SandboxSession.id)).where(SandboxSession.investigation_id == id))
    
    return {
        "id": inv.id,
        "display_id": inv.display_id,
        "input_type": inv.input_type.value,
        "target": inv.target,
        "normalized_input": inv.normalized_input,
        "status": inv.status.value,
        "current_stage": inv.current_stage or "Analyzing",
        "risk_score": inv.final_risk_score or inv.initial_risk_score or 0.0,
        "risk_level": inv.classification or "UNKNOWN",
        "confidence": inv.confidence or 0.95,
        "progress": 100 if inv.status in [InvestigationStatus.COMPLETED, InvestigationStatus.FAILED] else 50,
        "findings_count": findings_count or 0,
        "sandbox_status": "COMPLETED" if (sandbox_count or 0) > 0 else "NOT_REQUIRED",
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
            "status": run.status.value if hasattr(run.status, 'value') else str(run.status),
            "duration": run.duration,
            "findings_count": getattr(run, "findings_count", len((run.outputs or {}).get("findings", []))),
            "error": run.error_message
        })
    return agents

@router.get("/{id}/risk")
async def get_investigation_risk(id: str, db: AsyncSession = Depends(get_db)):
    risk_output = await RiskEngine.calculate_risk(id, db)
    return risk_output.dict()

@router.get("/{id}/explanation")
async def get_explanation(id: str, db: AsyncSession = Depends(get_db)):
    return await RiskExplanationService.generate_explanation(id, db)

@router.get("/{id}/report")
async def get_report(id: str, db: AsyncSession = Depends(get_db)):
    return await ReportGenerator.generate_report(id, db)

@router.get("/{id}/sandbox")
async def get_sandbox_session(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SandboxSession).where(SandboxSession.investigation_id == id).order_by(SandboxSession.start_time.desc()))
    session = result.scalars().first()
    if not session:
        return {"status": "NOT_STARTED"}
    return {
        "status": session.status.value,
        "start_time": session.start_time,
        "end_time": session.end_time,
        "browser": session.browser_type,
        "event_count": session.event_count or 0,
        "error": session.error
    }

@router.get("/{id}/sandbox/events")
async def get_sandbox_events(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SandboxSession).where(SandboxSession.investigation_id == id).order_by(SandboxSession.start_time.desc()))
    session = result.scalars().first()
    if not session:
        return []
    return session.events or []

@router.get("/{id}/sandbox/artifacts")
async def get_sandbox_artifacts(id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(SandboxSession).where(SandboxSession.investigation_id == id).order_by(SandboxSession.start_time.desc()))
    session = result.scalars().first()
    if not session:
        return {}
    return session.screenshots or {}

@router.get("/{id}/threat-intelligence")
async def get_investigation_threat_intel(id: str, db: AsyncSession = Depends(get_db)):
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
    triage = (await db.execute(select(TriageResult).filter_by(investigation_id=id))).scalar_one_or_none()
    plan = (await db.execute(select(InvestigationPlan).filter_by(investigation_id=id))).scalar_one_or_none()
    response = (await db.execute(select(ResponseAction).filter_by(investigation_id=id))).scalar_one_or_none()
    
    return {
        "triage": {
            "priority": triage.priority,
            "reasons": triage.reasons
        } if triage else None,
        "plan": {
            "planned_agents": plan.planned_agents if plan else [],
            "reason": plan.reason if plan else ""
        } if plan else None,
        "response": {
            "action": response.action_type if response else "MONITOR",
            "details": response.description if response else "Standard monitoring",
            "confidence": response.confidence if response else 0.95
        } if response else None
    }

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
