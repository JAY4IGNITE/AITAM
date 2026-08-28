from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from ..database.connection import get_db
from ..models import Investigation, InvestigationStatus, InputType
from ..engine.coordinator import InvestigationCoordinator
import uuid

router = APIRouter()

@router.post("/reset")
async def reset_demo(db: AsyncSession = Depends(get_db)):
    """Clear out all DEMO investigations without affecting real data."""
    try:
        await db.execute(text("DELETE FROM investigations WHERE display_id LIKE 'DEMO-%'"))
        await db.commit()
        return {"status": "success", "message": "Demo data reset successfully."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/run")
async def run_demo(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Trigger the deterministic credential harvesting demo."""
    
    # Pre-configure the investigation parameters required for the Hackathon Demo flow
    target_sms = "URGENT: Verify your crypto wallet at http://malicious.test/login before it is locked."
    display_id = f"DEMO-{str(uuid.uuid4())[:6].upper()}"
    
    new_inv = Investigation(
        display_id=display_id,
        input_type=InputType.SMS,
        target=target_sms,
        status=InvestigationStatus.QUEUED,
        current_stage="INITIALIZING"
    )
    
    db.add(new_inv)
    await db.commit()
    await db.refresh(new_inv)
    
    # Push to Celery orchestrator
    background_tasks.add_task(InvestigationCoordinator.start_investigation, new_inv.id)
    
    return {
        "status": "success",
        "investigation_id": new_inv.id,
        "display_id": display_id,
        "message": "Demo scenario initiated."
    }
