from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
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
