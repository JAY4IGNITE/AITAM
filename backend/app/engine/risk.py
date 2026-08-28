from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.agent import Evidence

class RiskEngine:
    @staticmethod
    async def calculate_risk(investigation_id: str, session: AsyncSession) -> float:
        # Base risk
        base_risk = 0.0
        
        # Get all evidence
        result = await session.execute(
            select(Evidence).where(Evidence.investigation_id == investigation_id)
        )
        evidence_list = result.scalars().all()
        
        for ev in evidence_list:
            weight = 0
            if ev.severity == "critical":
                weight = 80
            elif ev.severity == "high":
                weight = 50
            elif ev.severity == "medium":
                weight = 30
            elif ev.severity == "low":
                weight = 10
                
            base_risk += weight * ev.confidence
            
        final_score = min(100.0, base_risk)
        return float(final_score)
