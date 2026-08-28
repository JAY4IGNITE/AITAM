from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from typing import Optional
import os
import shutil
import uuid
from ..database.connection import get_db
from ..models.dataset import Dataset, DatasetSample
from ..datasets.registry import DatasetRegistry

router = APIRouter()

@router.post("/import")
async def import_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    source: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """Uploads a dataset file (CSV/JSON), normalizes it, and saves samples."""
    # Save file temporarily
    ext = file.filename.split(".")[-1].lower()
    if ext not in ["csv", "json", "jsonl"]:
        raise HTTPException(status_code=400, detail="Only CSV, JSON, and JSONL formats are supported.")
        
    temp_path = f"/tmp/{uuid.uuid4()}.{ext}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        result = await DatasetRegistry.import_dataset(db, temp_path, name, source, description)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.get("/")
async def list_datasets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Dataset).order_by(Dataset.created_at.desc()))
    datasets = result.scalars().all()
    
    # Get sample counts
    out = []
    for d in datasets:
        count = await db.scalar(select(func.count()).where(DatasetSample.dataset_id == d.id))
        out.append({
            "id": d.id,
            "name": d.name,
            "source": d.source,
            "description": d.description,
            "created_at": d.created_at,
            "sample_count": count
        })
    return out

@router.get("/{id}/statistics")
async def get_dataset_statistics(id: str, db: AsyncSession = Depends(get_db)):
    dataset = await db.get(Dataset, id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
        
    # Get label distribution
    stats_query = await db.execute(
        select(DatasetSample.label, func.count()).where(DatasetSample.dataset_id == id).group_by(DatasetSample.label)
    )
    distribution = {row[0].value: row[1] for row in stats_query.all()}
    
    total = sum(distribution.values())
    
    return {
        "dataset_id": id,
        "total_samples": total,
        "distribution": distribution
    }

@router.get("/{id}/samples")
async def get_dataset_samples(id: str, limit: int = 50, offset: int = 0, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DatasetSample).where(DatasetSample.dataset_id == id).limit(limit).offset(offset)
    )
    samples = result.scalars().all()
    return samples
