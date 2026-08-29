from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from ..models.finding import Finding
from ..models.investigation import Investigation
from ..schemas.agent_io import RiskOutput, RiskReason

class RiskEngine:
    @staticmethod
    async def calculate_risk(investigation_id: str, session: AsyncSession) -> RiskOutput:
        inv = await session.get(Investigation, investigation_id)
        
        # Get all findings from all specialized agents
        result = await session.execute(
            select(Finding).where(Finding.investigation_id == investigation_id)
        )
        findings: List[Finding] = result.scalars().all()
        
        total_score = 0.0
        reasons: List[RiskReason] = []
        
        # Deduplicate findings by title to prevent double-counting identical facts
        seen_titles = set()
        
        for f in findings:
            if f.title not in seen_titles:
                seen_titles.add(f.title)
                contribution = float(f.risk_contribution or 0.0) * float(f.confidence or 1.0)
                total_score += contribution
                if contribution > 0:
                    reasons.append(RiskReason(finding=f.title, contribution=round(contribution, 1)))
            
        final_score = min(100.0, total_score)
        
        # Determine classification according to Phase 17 requirements:
        # 0-19 SAFE, 20-39 LOW, 40-59 MEDIUM, 60-79 HIGH, 80-100 CRITICAL
        if not findings and (not inv or not inv.normalized_input):
            level = "UNKNOWN"
        elif final_score >= 80:
            level = "CRITICAL"
        elif final_score >= 60:
            level = "HIGH"
        elif final_score >= 40:
            level = "MEDIUM"
        elif final_score >= 20:
            level = "LOW"
        else:
            # Check if verified clean by at least one provider/agent
            has_clean_finding = any("clean" in f.title.lower() or f.severity == "info" for f in findings)
            level = "SAFE" if (has_clean_finding or len(findings) > 0) else "UNKNOWN"
            
        # Adaptive sandbox decision (Phase 15):
        # Trigger sandbox if score >= 40 (MEDIUM, HIGH, CRITICAL) or if suspicious heuristics present
        sandbox_req = final_score >= 40 or any(f.category in ["evasion", "quishing", "credential_harvesting"] for f in findings)
        deep_req = final_score >= 80
            
        return RiskOutput(
            score=round(final_score, 1),
            level=level,
            reasons=reasons,
            sandbox_required=sandbox_req,
            deep_analysis_required=deep_req
        )
