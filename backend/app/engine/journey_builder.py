from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from ..models.investigation import Investigation
from ..models.journey import AttackJourneyStep, RiskAssessment
from ..models.finding import Finding
from ..models.agent import AgentRun, SandboxSession

class AttackJourneyService:
    @staticmethod
    async def build_journey(investigation_id: str, session: AsyncSession):
        # Clear old journey steps
        await session.execute(
            AttackJourneyStep.__table__.delete().where(AttackJourneyStep.investigation_id == investigation_id)
        )
        await session.commit()
        
        inv = await session.get(Investigation, investigation_id)
        if not inv: 
            return

        findings_res = await session.execute(
            select(Finding).where(Finding.investigation_id == investigation_id).order_by(Finding.created_at.asc())
        )
        findings = findings_res.scalars().all()

        agent_runs_res = await session.execute(
            select(AgentRun).where(AgentRun.investigation_id == investigation_id).order_by(AgentRun.start_time.asc())
        )
        agent_runs = agent_runs_res.scalars().all()

        sb_res = await session.execute(
            select(SandboxSession).where(SandboxSession.investigation_id == investigation_id)
        )
        sandbox = sb_res.scalars().first()

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

        # Step 1: Ingestion & Normalization
        add_step(
            f"Artifact Ingested ({inv.input_type.value})",
            f"Universal Input Processor normalized target: '{inv.target[:60]}'",
            "DISCOVERY",
            "Preprocessor",
            0.0,
            0.0
        )

        # Step 2: Dynamic Multi-Agent Observations
        current_risk = 0.0
        for f in findings:
            prev_risk = current_risk
            current_risk = min(100.0, current_risk + (f.risk_contribution or 15.0))
            add_step(
                f.title,
                f.description,
                "ANALYSIS",
                f.agent,
                round(prev_risk, 1),
                round(current_risk, 1)
            )

        # Step 3: Sandbox Detonation (if executed)
        if sandbox and sandbox.status.value == "COMPLETED":
            events_count = sandbox.event_count or len(sandbox.events or [])
            add_step(
                "Zero-Trust Browser Detonation",
                f"Isolated Playwright container captured {events_count} DOM & network events with full screenshot artifact.",
                "SANDBOX",
                "SandboxAgent",
                round(current_risk, 1),
                round(inv.final_risk_score or current_risk, 1)
            )

        # Step 4: Final Classification
        final_score = inv.final_risk_score or current_risk
        classification = inv.classification or "UNKNOWN"
        add_step(
            f"Threat Classification: {classification} ({final_score}/100)",
            f"Synthesized {len(findings)} findings across {len(agent_runs)} agents into actionable forensic intelligence report.",
            "FINAL",
            "RiskEngine",
            round(current_risk, 1),
            round(final_score, 1)
        )
            
        if steps:
            session.add_all(steps)
            await session.commit()
