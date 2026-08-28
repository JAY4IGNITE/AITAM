from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List

from ..database.connection import get_db
from ..models import Investigation, InvestigationStatus
from ..schemas import InvestigationCreate, InvestigationResponse
from ..engine.orchestrator import Orchestrator

router = APIRouter()

@router.post("/", response_model=InvestigationResponse)
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
        status=InvestigationStatus.SUBMITTED
    )
    
    db.add(new_inv)
    await db.commit()
    await db.refresh(new_inv)
    
    # Start orchestrator in background
    background_tasks.add_task(Orchestrator.start_investigation, new_inv.id)
    
    return new_inv

@router.get("/", response_model=List[InvestigationResponse])
async def list_investigations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Investigation).order_by(Investigation.created_at.desc()))
    return result.scalars().all()

@router.get("/{id}", response_model=InvestigationResponse)
async def get_investigation(id: str, db: AsyncSession = Depends(get_db)):
    inv = await db.get(Investigation, id)
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return inv
