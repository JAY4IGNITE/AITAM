from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Dict, Any, List
from ..models.finding import Finding
from ..schemas.agent_io import RiskOutput, RiskReason

class RiskEngine:
    @staticmethod
    async def calculate_risk(investigation_id: str, session: AsyncSession) -> RiskOutput:
        # Get all findings
        result = await session.execute(
            select(Finding).where(Finding.investigation_id == investigation_id)
        )
        findings: List[Finding] = result.scalars().all()
        
        total_score = 0.0
        reasons = []
        
        # Deduplicate findings by title so we don't double count identical evidence
        seen_titles = set()
        
        for f in findings:
            if f.title not in seen_titles:
                seen_titles.add(f.title)
                contribution = float(f.risk_contribution) * f.confidence
                total_score += contribution
                if contribution > 0:
                    reasons.append(RiskReason(finding=f.title, contribution=round(contribution, 1)))
            
        final_score = min(100.0, total_score)
        
        level = "SAFE"
        if final_score > 79:
            level = "CRITICAL"
        elif final_score > 59:
            level = "HIGH"
        elif final_score > 29:
            level = "MEDIUM"
        else:
            level = "LOW"
            
        sandbox_req = final_score > 40
        deep_req = final_score > 80
            
        # Return structured RiskOutput directly
        return RiskOutput(
            score=round(final_score, 1),
            level=level,
            reasons=reasons,
            sandbox_required=sandbox_req,
            deep_analysis_required=deep_req
        )
