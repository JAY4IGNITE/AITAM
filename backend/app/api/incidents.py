from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import List

from ..database.connection import get_db
from ..models.autonomous import Incident, ResponseAction, InvestigationFeedback

router = APIRouter()

@router.get("/")
async def get_incidents(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Incident).order_by(Incident.created_at.desc()))
    return res.scalars().all()

@router.get("/{id}")
async def get_incident(id: str, db: AsyncSession = Depends(get_db)):
    incident = await db.get(Incident, id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    # Get associated response actions
    res_actions = await db.execute(select(ResponseAction).where(ResponseAction.investigation_id == incident.investigation_id))
    actions = res_actions.scalars().all()
    
    return {
        "incident": incident,
        "recommended_actions": actions
    }

class ApprovalRequest(BaseModel):
    action_id: str
    analyst_id: str

@router.post("/{id}/approve-action")
async def approve_action(id: str, req: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    action = await db.get(ResponseAction, req.action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    action.status = "APPROVED"
    action.approved_by = req.analyst_id
    await db.commit()
    
    # In a real system, this would trigger the actual blocking integration
    action.status = "EXECUTED" 
    await db.commit()
    
    return {"status": "SUCCESS", "action": action}

@router.post("/{id}/reject-action")
async def reject_action(id: str, req: ApprovalRequest, db: AsyncSession = Depends(get_db)):
    action = await db.get(ResponseAction, req.action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
        
    action.status = "REJECTED"
    action.approved_by = req.analyst_id
    await db.commit()
    
    return {"status": "SUCCESS", "action": action}

@router.get("/{id}/timeline")
async def get_incident_timeline(id: str, db: AsyncSession = Depends(get_db)):
    incident = await db.get(Incident, id)
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    from ..models import InvestigationEvent
    result = await db.execute(select(InvestigationEvent).where(InvestigationEvent.investigation_id == incident.investigation_id).order_by(InvestigationEvent.created_at.asc()))
    return result.scalars().all()
