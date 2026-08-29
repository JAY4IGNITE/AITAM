from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc

from ..database.connection import get_db
from ..models import Investigation, InvestigationStatus, Finding, SandboxSession
from ..models.report import ThreatReport
from ..schemas.dashboard import DashboardStatsResponse, RecentInvestigationItem, ThreatTrendPoint

router = APIRouter()

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Computes real-time aggregated metrics and 24h trend data directly from PostgreSQL.
    No hardcoded statistics.
    """
    # 1. Total & Active Investigations
    total_inv = await db.scalar(select(func.count(Investigation.id))) or 0
    active_inv = await db.scalar(
        select(func.count(Investigation.id)).where(
            Investigation.status.notin_([InvestigationStatus.COMPLETED, InvestigationStatus.FAILED])
        )
    ) or 0

    # 2. Risk Level Counts
    safe_cnt = await db.scalar(select(func.count(Investigation.id)).where(Investigation.classification == "SAFE")) or 0
    low_cnt = await db.scalar(select(func.count(Investigation.id)).where(Investigation.classification == "LOW")) or 0
    med_cnt = await db.scalar(select(func.count(Investigation.id)).where(Investigation.classification.in_(["MEDIUM", "SUSPICIOUS"]))) or 0
    high_cnt = await db.scalar(select(func.count(Investigation.id)).where(Investigation.classification == "HIGH")) or 0
    crit_cnt = await db.scalar(select(func.count(Investigation.id)).where(Investigation.classification == "CRITICAL")) or 0
    unk_cnt = await db.scalar(select(func.count(Investigation.id)).where(
        (Investigation.classification == "UNKNOWN") | (Investigation.classification.is_(None))
    )) or 0

    # 3. Threat Intel Matches & Sandbox Executions
    threat_matches = await db.scalar(
        select(func.count(Finding.id)).where(Finding.category == "threat_intel")
    ) or 0
    
    sandbox_runs = await db.scalar(
        select(func.count(SandboxSession.id)).where(SandboxSession.status == "COMPLETED")
    ) or 0

    # 4. Reports Counts
    total_reports = await db.scalar(select(func.count(ThreatReport.id))) or 0
    pending_reports = await db.scalar(
        select(func.count(ThreatReport.id)).where(ThreatReport.status == "PENDING")
    ) or 0

    # 5. Recent Investigations (Top 10)
    recent_q = await db.execute(
        select(Investigation).order_by(desc(Investigation.created_at)).limit(10)
    )
    recent_rows = recent_q.scalars().all()
    recent_items = [
        RecentInvestigationItem(
            id=r.id,
            display_id=r.display_id,
            input_type=r.input_type.value,
            target=r.target,
            classification=r.classification or "UNKNOWN",
            final_risk_score=r.final_risk_score,
            status=r.status.value,
            created_at=r.created_at
        ) for r in recent_rows
    ]

    # 6. Real 24h Activity Timeline
    now = datetime.utcnow()
    threat_trend: list[ThreatTrendPoint] = []
    
    # Bucket into 6-hour windows over last 24 hours
    for i in range(4, -1, -1):
        window_start = now - timedelta(hours=(i + 1) * 6)
        window_end = now - timedelta(hours=i * 6)
        
        window_tot = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.created_at >= window_start,
                Investigation.created_at < window_end
            )
        ) or 0
        
        window_mal = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.created_at >= window_start,
                Investigation.created_at < window_end,
                Investigation.classification.in_(["HIGH", "CRITICAL"])
            )
        ) or 0
        
        window_susp = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.created_at >= window_start,
                Investigation.created_at < window_end,
                Investigation.classification.in_(["MEDIUM", "SUSPICIOUS", "LOW"])
            )
        ) or 0
        
        window_safe = await db.scalar(
            select(func.count(Investigation.id)).where(
                Investigation.created_at >= window_start,
                Investigation.created_at < window_end,
                Investigation.classification == "SAFE"
            )
        ) or 0

        label = window_end.strftime("%H:%M")
        threat_trend.append(ThreatTrendPoint(
            timestamp=label,
            count=window_tot,
            malicious=window_mal,
            suspicious=window_susp,
            safe=window_safe
        ))

    return DashboardStatsResponse(
        total_investigations=total_inv,
        active_analysis_count=active_inv,
        safe_count=safe_cnt,
        low_count=low_cnt,
        medium_count=med_cnt,
        high_count=high_cnt,
        critical_count=crit_cnt,
        unknown_count=unk_cnt,
        threat_intel_matches=threat_matches,
        sandbox_executions=sandbox_runs,
        total_reports=total_reports,
        pending_reports=pending_reports,
        recent_investigations=recent_items,
        threat_trend_24h=threat_trend
    )
