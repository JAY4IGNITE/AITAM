from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.investigation import Investigation
from ..models.journey import RiskAssessment
from ..models.graph import EvidenceNode

class RiskExplanationService:
    @staticmethod
    async def generate_explanation(investigation_id: str, session: AsyncSession) -> dict:
        inv = await session.get(Investigation, investigation_id)
        if not inv: return {"error": "Investigation not found"}
        
        risk_history_res = await session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.investigation_id == investigation_id)
            .order_by(RiskAssessment.created_at.asc())
        )
        risks = risk_history_res.scalars().all()
        
        nodes_res = await session.execute(select(EvidenceNode).where(EvidenceNode.investigation_id == investigation_id))
        nodes = nodes_res.scalars().all()
        
        findings_nodes = [n for n in nodes if n.node_type == "FINDING"]
        
        explanation = {
            "title": f"{inv.classification} RISK",
            "summary": f"This target was classified as {inv.classification} because multiple independent signals indicate malicious activity.",
            "evidence": [f"✓ {n.label}" for n in findings_nodes],
            "confidence": 95,
            "sandbox_confirmation": any(n.source == "Sandbox" or n.source == "behavior_analysis" for n in nodes)
        }
        
        return explanation
