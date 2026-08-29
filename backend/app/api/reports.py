from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from ..database.connection import get_db
from ..models.report import ThreatReport
from ..schemas.report import (
    ThreatReportCreate, ThreatReportResponse, ThreatReportStatusUpdate, PaginatedThreatReports
)

router = APIRouter()

@router.post("/", response_model=ThreatReportResponse)
async def create_threat_report(
    req: ThreatReportCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Submits a suspicious content report for security analyst review.
    """
    report = ThreatReport(
        indicator=req.indicator.strip(),
        report_type=req.report_type.upper(),
        description=req.description.strip(),
        investigation_id=req.investigation_id,
        reporter_email=req.reporter_email,
        status="PENDING"
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report

@router.get("/", response_model=PaginatedThreatReports)
async def list_threat_reports(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    report_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Lists submitted threat reports with optional filtering by status and type.
    """
    query = select(ThreatReport)
    count_query = select(func.count(ThreatReport.id))
    
    filters = []
    if status:
        filters.append(ThreatReport.status == status.upper())
    if report_type:
        filters.append(ThreatReport.report_type == report_type.upper())
        
    if filters:
        query = query.where(*filters)
        count_query = count_query.where(*filters)
        
    total = await db.scalar(count_query) or 0
    offset = (page - 1) * limit
    result = await db.execute(query.order_by(desc(ThreatReport.created_at)).offset(offset).limit(limit))
    items = result.scalars().all()
    
    pages = (total + limit - 1) // limit if total > 0 else 1
    return PaginatedThreatReports(
        items=items,
        total=total,
        page=page,
        limit=limit,
        pages=pages
    )

@router.get("/{id}", response_model=ThreatReportResponse)
async def get_threat_report(id: str, db: AsyncSession = Depends(get_db)):
    report = await db.get(ThreatReport, id)
    if not report:
        raise HTTPException(status_code=404, detail="Threat report not found")
    return report

@router.patch("/{id}/status", response_model=ThreatReportResponse)
async def update_threat_report_status(
    id: str,
    update_req: ThreatReportStatusUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Updates threat report review status (PENDING, REVIEWED, RESOLVED).
    """
    report = await db.get(ThreatReport, id)
    if not report:
        raise HTTPException(status_code=404, detail="Threat report not found")
        
    valid_statuses = ["PENDING", "REVIEWED", "RESOLVED"]
    new_status = update_req.status.upper()
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
    report.status = new_status
    if update_req.resolution_notes:
        report.resolution_notes = update_req.resolution_notes
    report.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(report)
    return report
