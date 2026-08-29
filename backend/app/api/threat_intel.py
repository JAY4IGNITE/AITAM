from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc, or_

from ..database.connection import get_db
from ..models.threat_intel import ThreatIndicator
from ..engine.threat_intel_provider import registry
from ..schemas.threat_intel import (
    ThreatIntelResult, ThreatIntelProviderHealth,
    ThreatIndicatorCreate, ThreatIndicatorResponse, PaginatedThreatIndicators, ThreatFeedSyncResponse
)
from ..worker import _sync_urlhaus_feed

router = APIRouter()

class LookupRequest(BaseModel):
    indicator: str
    indicator_type: str

@router.get("/providers", response_model=List[ThreatIntelProviderHealth])
async def get_providers():
    """Returns health and status of all configured threat intelligence providers."""
    return await registry.get_health()

@router.post("/lookup", response_model=List[ThreatIntelResult])
async def manual_lookup(req: LookupRequest):
    """Executes real-time multi-provider intelligence lookup on any arbitrary indicator."""
    results = await registry.lookup(req.indicator.strip(), req.indicator_type.upper())
    if not results:
        raise HTTPException(status_code=404, detail="No intelligence found for this indicator")
    return results

@router.get("/indicators", response_model=PaginatedThreatIndicators)
async def list_threat_indicators(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    indicator_type: Optional[str] = Query(None),
    classification: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns paginated threat intelligence indicators from local PostgreSQL database.
    """
    query = select(ThreatIndicator)
    count_query = select(func.count(ThreatIndicator.id))
    
    filters = []
    if indicator_type:
        filters.append(ThreatIndicator.indicator_type == indicator_type.upper())
    if classification:
        filters.append(ThreatIndicator.classification == classification.upper())
    if source:
        filters.append(ThreatIndicator.source == source.upper())
    if search:
        filters.append(or_(
            ThreatIndicator.indicator.ilike(f"%{search.strip()}%"),
            ThreatIndicator.source.ilike(f"%{search.strip()}%")
        ))
        
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
        
    total = await db.scalar(count_query) or 0
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(desc(ThreatIndicator.last_seen)).offset(offset).limit(limit))
    items = result.scalars().all()
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    return PaginatedThreatIndicators(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )

@router.post("/indicators", response_model=ThreatIndicatorResponse)
async def add_threat_indicator(
    req: ThreatIndicatorCreate,
    db: AsyncSession = Depends(get_db)
):
    """Manually add an indicator to the local threat database."""
    # Check if duplicate exists
    existing = (await db.execute(
        select(ThreatIndicator).where(
            ThreatIndicator.indicator == req.indicator.strip(),
            ThreatIndicator.source == req.source.upper()
        )
    )).scalar_one_or_none()
    
    if existing:
        existing.classification = req.classification.upper()
        existing.confidence = req.confidence
        existing.last_seen = datetime.utcnow()
        existing.status = req.status.upper()
        existing.tags = list(set(existing.tags + req.tags)) if existing.tags else req.tags
        await db.commit()
        await db.refresh(existing)
        return existing
        
    new_ind = ThreatIndicator(
        indicator=req.indicator.strip(),
        indicator_type=req.indicator_type.upper(),
        source=req.source.upper(),
        classification=req.classification.upper(),
        confidence=req.confidence,
        status=req.status.upper(),
        tags=req.tags,
        metadata_payload=req.metadata_payload
    )
    db.add(new_ind)
    await db.commit()
    await db.refresh(new_ind)
    return new_ind

@router.post("/sync", response_model=ThreatFeedSyncResponse)
async def trigger_threat_feed_sync():
    """Triggers immediate background threat feed ingestion from URLhaus."""
    res = await _sync_urlhaus_feed()
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=502, detail=f"Threat feed synchronization failed: {res.get('error')}")
        
    return ThreatFeedSyncResponse(
        status="SUCCESS",
        source="URLHAUS",
        new_indicators_count=res.get("new_count", 0),
        updated_indicators_count=res.get("updated_count", 0),
        timestamp=datetime.utcnow()
    )
