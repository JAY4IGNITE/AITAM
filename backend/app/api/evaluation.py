from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import uuid
import json
from typing import Optional, Dict, Any
from ..database.connection import get_db
from ..models.dataset import Dataset
from ..models.evaluation import EvaluationRun, EvaluationResult
from ..engine.evaluator import DatasetEvaluator

router = APIRouter()

class EvaluationRequest(BaseModel):
    dataset_id: str
    sample_limit: Optional[int] = None
    parallelism: Optional[int] = 2
    thresholds: Optional[Dict[str, float]] = None

@router.post("/run")
async def run_evaluation(req: EvaluationRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    dataset = await db.get(Dataset, req.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    run_id = str(uuid.uuid4())
    run = EvaluationRun(
        id=run_id,
        dataset_id=req.dataset_id,
        status="STARTING",
        configuration={
            "sample_limit": req.sample_limit,
            "parallelism": req.parallelism
        },
        thresholds=req.thresholds or {"CRITICAL": 80, "HIGH": 60, "MEDIUM": 30}
    )
    db.add(run)
    await db.commit()
    
    # We must start execution asynchronously to not block the API
    background_tasks.add_task(DatasetEvaluator.execute_run, run_id, db)
    
    return {"evaluation_id": run_id, "status": "STARTING"}

@router.get("/{id}")
async def get_evaluation(id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(EvaluationRun, id)
    if not run:
        raise HTTPException(status_code=404, detail="Evaluation run not found")
        
    return run

@router.get("/{id}/report")
async def get_evaluation_report(id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(EvaluationRun, id)
    if not run or run.status != "COMPLETED":
        raise HTTPException(status_code=404, detail="Evaluation run not found or not completed")
        
    dataset = await db.get(Dataset, run.dataset_id)
    
    report = {
        "dataset_name": dataset.name,
        "source": dataset.source,
        "sample_count": run.total_samples,
        "metrics": {
            "accuracy": run.accuracy,
            "precision": run.precision,
            "recall": run.recall,
            "f1_score": run.f1_score,
            "false_positive_rate": run.false_positive_rate,
            "false_negative_rate": run.false_negative_rate
        },
        "confusion_matrix": run.confusion_matrix,
        "configuration": run.configuration,
        "thresholds": run.thresholds
    }
    return report
