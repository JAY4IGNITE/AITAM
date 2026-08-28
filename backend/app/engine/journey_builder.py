from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.investigation import Investigation
from ..models.journey import AttackJourneyStep, RiskAssessment
import datetime

class AttackJourneyService:
    @staticmethod
    async def build_journey(investigation_id: str, session: AsyncSession):
        # Clear old journey steps
        await session.execute(
            AttackJourneyStep.__table__.delete().where(AttackJourneyStep.investigation_id == investigation_id)
        )
        await session.commit()
        
        inv = await session.get(Investigation, investigation_id)
        if not inv: return

        risk_history_res = await session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.investigation_id == investigation_id)
            .order_by(RiskAssessment.created_at.asc())
        )
        risks = risk_history_res.scalars().all()
        
        steps = []
        seq = 1
        
        def add_step(title, desc, stage, agent=None, risk_b=None, risk_a=None):
            nonlocal seq
            steps.append(AttackJourneyStep(
                investigation_id=investigation_id,
                sequence=seq,
                title=title,
                description=desc,
                stage=stage,
                agent=agent,
                risk_before=risk_b,
                risk_after=risk_a
            ))
            seq += 1

        add_step("Investigation Started", f"Target: {inv.target}", "DISCOVERY", "System", 0.0, 0.0)
        
        # Trace risks
        last_risk = 0.0
        for r in risks:
            if r.stage == "INITIAL":
                add_step("Initial Analysis", "Parsed target structure", "ANALYSIS", risk_b=last_risk, risk_a=r.score)
            elif r.stage == "AGENTS":
                add_step("Multi-Agent Intelligence", "Executed fast intelligence agents", "ANALYSIS", risk_b=last_risk, risk_a=r.score)
            elif r.stage == "SANDBOX":
                add_step("Sandbox Dynamic Analysis", "Isolated execution observed suspicious behaviors", "SANDBOX", risk_b=last_risk, risk_a=r.score)
            elif r.stage == "FINAL":
                add_step("Final Risk Calculation", f"Classified as {r.level}", "RISK", risk_b=last_risk, risk_a=r.score)
            last_risk = r.score
            
        if inv.status.value == "COMPLETED":
            add_step("Classification Complete", f"Investigation finalized with score {last_risk}", "FINAL")
            
        if steps:
            session.add_all(steps)
            await session.commit()
